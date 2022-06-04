"""Parser functions, based on www.github.com/tusharsadhwani/json_parser"""
from ast import literal_eval
from dataclasses import dataclass, field
from typing import Optional, AbstractSet

from Cat.utils.collections_ import OrderedMultiDict
from Cat.utils.profiling import ProfiledFunction
from model.json.core import *
from model.json.lexer_v2 import Token, TokenType, JsonTokenizer
from model.json.schema import enrichWithSchema
from model.messages import *
from model.parsing.bytesUtils import bytesToStr, strToBytes
from model.parsing.parser import ParserBase, registerParser, IndexMapper
from model.utils import Span, MDStr, LanguageId


_ESCAPE_CHAR_MAP = {
	ord('"'): b'"',
	ord('/'): b'/',
	ord('\\'): b'\\',
	ord('b'): b'\b',
	ord('f'): b'\f',
	ord('n'): b'\n',
	ord('r'): b'\r',
	ord('t'): b'\t',
}

_BOOLEAN_TOKENS = {
	b'true': True,
	b'false': False,
}


@registerParser(LanguageId('MCJson'))
@registerParser(LanguageId('JSON'))
@dataclass
class JsonParser(ParserBase[JsonData, JsonSchema]):
	allowMultilineStr: bool = False

	# tokens: deque[Token] = field(init=False)
	_tokenizer: JsonTokenizer = field(init=False)
	_current: Optional[Token] = field(init=False)
	_last: Optional[Token] = field(init=False, default=None)

	def __post_init__(self):
		self._tokenizer = JsonTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
			self.allowMultilineStr,
		)
		self.errors = self._tokenizer.errors  # sync errors
		self._current = self._tokenizer.nextToken()
		self._last = None

	def _error(self, message: MDStr, span: Span, style: str = 'error') -> None:
		self.errors.append(JsonParseError(message, span, style=style))

	@property
	def hasTokens(self) -> bool:
		return self._current is not None

	def _next(self) -> None:
		self._last = self._current
		self._current = self._tokenizer.nextToken()

	def accept(self, tokenType: TokenType) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else Span()
			self._error(UNEXPECTED_EOF_MSG.format(), span)
			return self._last  # TODO: WTF ?????

		if current.type is not tokenType:
			msg = EXPECTED_BUT_GOT_MSG.format(tokenType.asString, current.value)
			self._error(msg, current.span)
		self._next()
		return current

	def acceptAnyOf(self, tokenTypes: AbstractSet[TokenType], name: str = None) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else Span()
			self._error(UNEXPECTED_EOF_MSG.format(), span)
			return self._last  # TODO: WTF ?????

		if current.type not in tokenTypes:
			if name is None:
				name = ' | '.join(tk.asString for tk in tokenTypes)
			msg = EXPECTED_BUT_GOT_MSG.format(name, current.value)
			self._error(msg, current.span)
		self._next()
		return current

	def acceptAny(self) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else Span()
			self._error(UNEXPECTED_EOF_MSG.format(), span)
			return self._last  # TODO: WTF ?????
		self._next()
		return current

	def parse_object(self) -> JsonObject:
		"""Parses an object out of JSON tokens"""
		objData: OrderedMultiDict[str, JsonProperty] = OrderedMultiDict()

		start = self._last

		token = self.acceptAnyOf({TokenType.right_brace, TokenType.string})
		if token.type is TokenType.eof:
			return JsonObject(Span(start.span.start, token.span.end), None, objData)
		# special case:
		if token.type is TokenType.right_brace:
			return JsonObject(Span(start.span.start, token.span.end), None, objData)

		while token is not None:
			if token.type == TokenType.string:
				key = self.parse_string()
			else:
				if token.type == TokenType.comma:
					token = self.accept(TokenType.string)
					continue
				if token.type == TokenType.right_brace:
					break
				key = JsonString(token.span, JSON_KEY_SCHEMA, '', IndexMapper())

			if token.type != TokenType.colon:
				token = self.accept(TokenType.colon)
			if token.type is TokenType.eof:
				value = JsonInvalid(Span(self._last.span.end, token.span.end), None, '')
				objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
				break
			elif token.type != TokenType.colon:
				if token.type == TokenType.comma:
					value = JsonInvalid(self._last.span, None, '')
					objData.add(key.data, JsonProperty(Span(key.span.start, token.span.start), None, key, value))
					token = self.accept(TokenType.string)
					continue
				if token.type == TokenType.right_brace:
					value = JsonInvalid(self._last.span, None, '')
					objData.add(key.data, JsonProperty(Span(key.span.start, token.span.start), None, key, value))
					break
				pass
			self.acceptAnyOf(self._PARSERS.keys())
			value = self._internalParseTokens()

			token = self.acceptAnyOf({TokenType.comma, TokenType.right_brace})
			if token.type is TokenType.eof:
				objData.add(key.data, JsonProperty(Span(key.span.start, token.span.end), None, key, value))
				break
			objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
			if token.type is TokenType.comma:
				token = self.accept(TokenType.string)
				continue
			if token.type == TokenType.right_brace:
				break

		if token.type is TokenType.eof:
			token = self._last
		return JsonObject(Span(start.span.start, token.span.end), None, objData)

	def parse_array(self) -> JsonArray:
		"""Parses an array out of JSON tokens"""

		arrayData: list[JsonData] = []

		start = self._last

		token = self.acceptAnyOf({TokenType.right_bracket, *self._PARSERS.keys()})
		if token.type is TokenType.eof:
			return JsonArray(Span(start.span.start, token.span.end), None, arrayData)
		# special case:
		if token.type is TokenType.right_bracket:
			return JsonArray(Span(start.span.start, token.span.end), None, arrayData)

		while token is not None:

			value = self._internalParseTokens()
			arrayData.append(value)

			token = self.acceptAnyOf({TokenType.comma, TokenType.right_bracket})
			if token.type is TokenType.eof:
				break
			if token.type is TokenType.comma:
				token = self.acceptAnyOf(self._PARSERS.keys())
				continue
			if token.type == TokenType.right_bracket:
				break

		if token.type is TokenType.eof:
			token = self._last
		return JsonArray(Span(start.span.start, token.span.end), None, arrayData)

	def parse_string(self) -> JsonString:
		"""Parses a string out of a JSON token"""

		token = self._last
		string = token.value

		idxMap = []

		if b'\\' in string:
			chars: bytes = b''  # list[str] = []
			index = 1
			strStreakStart = index
			end = len(string) - 1
			while index < end:
				char = string[index]

				if char != ord(b'\\'):
					# chars.append(char)
					index += 1
					continue

				chars += (string[strStreakStart:index])
				decIdx = len(chars)
				next_char = string[index + 1]
				if next_char == ord(b'u'):
					hex_string = string[index + 2:index + 6]
					try:
						unicode_char = literal_eval(f'"\\u{bytesToStr(hex_string)}"')
					except SyntaxError:
						self._error(MDStr(f"Invalid unicode escape: `\\u{bytesToStr(hex_string)}`"), token.span)
						unicode_char = b'\\u' + hex_string
						encIdx = index
					else:
						unicode_char = strToBytes(unicode_char)
						encIdx = index - 1 + 5

					chars += unicode_char
					idxMap.append((encIdx, decIdx))
					index += 6
					strStreakStart = index
					continue
				else:
					next_char_str = _ESCAPE_CHAR_MAP.get(next_char)
					if next_char_str is not None:
						encIdx = index - 1 + 1
						chars += next_char_str
						idxMap.append((encIdx, decIdx))
					else:
						self._error(MDStr(f"Unknown escape sequence: `{bytesToStr(string)}`"), token.span)
						chars += string[index:index+2]

					index += 2
					strStreakStart = index

			chars += (string[strStreakStart:index])
			value = bytesToStr(chars)
		elif string:
			if string[0] == ord('"'):
				string = string[1:].removesuffix(b'"')
			elif string[0] == ord("'"):
				string = string[1:].removesuffix(b"'")
			value = bytesToStr(string)
		else:
			value = ''
		return JsonString(token.span, None, value, IndexMapper(idxMap))

	def parse_number(self) -> JsonNumber:
		"""Parses a number out of a JSON token"""
		token = self._last
		try:

			if token.value and token.value[0] == ord('-'):
				valToCHeck = token.value[1:]
			else:
				valToCHeck = token.value
			if valToCHeck.isdigit():
				number = int(token.value)
			else:
				number = float(token.value)
			return JsonNumber(token.span, None, number)

		except ValueError:
			self._error(MDStr(f"Invalid number: `{token.value}`"), token.span)
		return JsonNumber(token.span, None, 0)

	def parse_boolean(self) -> JsonBool:
		"""Parses a boolean out of a JSON token"""
		token = self._last
		value = _BOOLEAN_TOKENS[token.value]
		return JsonBool(token.span, None, value)

	def parse_null(self) -> JsonNull:
		"""Parses a boolean out of a JSON token"""
		token = self._last
		return JsonNull(token.span, None)

	_PARSERS = {
		TokenType.left_bracket: parse_array,
		TokenType.left_brace: parse_object,
		TokenType.string: parse_string,
		TokenType.number: parse_number,
		TokenType.boolean: parse_boolean,
		TokenType.null: parse_null,
	}

	def _internalParseTokens(self) -> JsonData:
		"""Recursive JSON parse implementation"""
		token = self._last
		parser = self._PARSERS.get(token.type)
		if parser is not None:
			value = parser(self)
			return value
		else:
			return JsonInvalid(token.span, None, bytesToStr(token.value))

	def parseJsonTokens(self) -> Optional[JsonData]:
		"""Recursive JSON parse implementation"""
		token = self.acceptAnyOf(self._PARSERS.keys())
		if token is not None:
			data = self._internalParseTokens()
			enrichWithSchema(data, self.schema)
		else:
			data = None
		return data

	@ProfiledFunction(enabled=False)
	def parse(self) -> Optional[JsonData]:
		"""Parses a JSON string into a Python object"""
		value = self.parseJsonTokens()

		if self._current is not None:
			self._error(
				MDStr(f"Invalid JSON at `{self._current.value}`"),
				self._current.span
			)

		return value


def init():
	pass
