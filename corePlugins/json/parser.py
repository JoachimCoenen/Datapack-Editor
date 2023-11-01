"""Parser functions, based on www.github.com/tusharsadhwani/json_parser"""
from ast import literal_eval
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, AbstractSet, Callable

from cat.utils import CachedProperty
from cat.utils.collections_ import OrderedMultiDict
from cat.utils.profiling import ProfiledFunction
from .core import *
from .lexer import JsonTokenizer
from .schema import enrichWithSchema, pathify
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr, strToBytes, ORD_BACKSLASH, ORD_u, ORD_DOUBLE_QUOTE, ORD_SINGLE_QUOTE, ORD_MINUS
from base.model.parsing.parser import ParserBase, IndexMapBuilder, IndexMapper
from base.model.utils import Span, MDStr, Message, NULL_SPAN

ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG = Message("JSON standard allows only double quoted string as property key", 0)
MISSING_VALUE_MSG = Message("Missing value for property", 0)

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


@dataclass
class JsonParser(ParserBase[JsonNode, JsonSchema]):

	_waitingForClosing: dict[TokenType, int] = field(default_factory=lambda: defaultdict(int), init=False)
	# tokens: deque[Token] = field(init=False)
	_tokenizer: JsonTokenizer = field(init=False)
	_current: Optional[Token] = field(init=False)
	_last: Optional[Token] = field(init=False, default=None)

	def __post_init__(self):
		super().__post_init__()
		allowMultilineStr = True or self.schema is not None and self.schema.allowMultilineStr
		self._tokenizer = JsonTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
			self.maxEncIndex,
			allowMultilineStr
		)
		self._tokens = tokens = self.tokenize()
		self._tokensIter = iter(tokens)
		self.errors = self._tokenizer.errors  # sync errors
		self._current = None
		self._last = None
		self._next()

	def tokenize(self):
		tokens = []
		while (tkn := self._tokenizer.nextToken()).type is not TokenType.eof:
			tokens.append(tkn)
		return tokens

	@property
	def allowMultilineStr(self) -> bool:
		return self._tokenizer.allowMultilineStr

	@allowMultilineStr.setter
	def allowMultilineStr(self, value: bool):
		self._tokenizer.allowMultilineStr = value

	@property
	def hasTokens(self) -> bool:
		return self._current is not None

	def _next(self) -> None:
		self._last = self._current
		# self._current = self._tokenizer.nextToken()
		self._current = next(self._tokensIter, None)

	def tryAccept(self, tokenType: TokenType) -> Optional[Token]:
		if self._current is None or self._current.type is not tokenType:
			return None
		self._next()
		return self._last  # current == self._last

	def tryAcceptAnyOf(self, tokenTypes: AbstractSet[TokenType]) -> Optional[Token]:
		if self._current is None or self._current.type not in tokenTypes:
			return None
		self._next()
		return self._last  # current == self._last

	def accept(self, tokenType: TokenType, advanceIfBad: bool = True) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else NULL_SPAN
			self.errorMsg(UNEXPECTED_EOF_MSG, span=span)
			return self._last  # TODO: WTF ?????

		if current.type is not tokenType:
			self.errorMsg(EXPECTED_BUT_GOT_MSG, tokenType.asString, bytesToStr(current.value), span=current.span)
			if advanceIfBad:
				self._next()
		else:
			self._next()
		return current  # current == (self._last if _next() was called, else self._current)

	def acceptAnyOf(self, tokenTypes: AbstractSet[TokenType], advanceIfBad: bool = True) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else NULL_SPAN
			self.errorMsg(UNEXPECTED_EOF_MSG, span=span)
			return self._last  # TODO: WTF ?????

		if current.type not in tokenTypes:
			name = ' | '.join(tk.asString for tk in tokenTypes)
			self.errorMsg(EXPECTED_BUT_GOT_MSG, name, bytesToStr(current.value), span=current.span)
			if advanceIfBad:
				self._next()
		else:
			self._next()
		return current  # current == (self._last if _next() was called, else self._current)

	def acceptAny(self) -> Optional[Token]:
		current = self._current
		if current is None:
			span = self._last.span if self._last is not None else NULL_SPAN
			self.errorMsg(UNEXPECTED_EOF_MSG, span=span)
			return self._last  # TODO: WTF ?????
		self._next()
		return current

	# def parse_object(self) -> JsonObject:
	# 	"""Parses an object out of JSON tokens"""
	# 	objData: OrderedMultiDict[str, JsonProperty] = OrderedMultiDict()
	#
	# 	start = self._last
	#
	# 	token = self.acceptAnyOf({TokenType.right_brace, TokenType.string})
	# 	if token.type is TokenType.eof:
	# 		return JsonObject(Span(start.span.start, token.span.end), None, objData)
	# 	# special case:
	# 	if token.type is TokenType.right_brace:
	# 		return JsonObject(Span(start.span.start, token.span.end), None, objData)
	#
	# 	token = self.parse_properties(objData, token)
	#
	# 	if token.type is TokenType.eof:
	# 		token = self._last
	# 	return JsonObject(Span(start.span.start, token.span.end), None, objData)
	#
	# def parse_properties(self, objData: OrderedMultiDict[str, JsonProperty], token: Token):
	# 	while token is not None:
	# 		# parse KEY:
	# 		if token.type == TokenType.string:
	# 			key = self.parse_string()
	# 			key.schema = JSON_KEY_SCHEMA
	# 		else:
	# 			if token.type == TokenType.comma:
	# 				token = self.accept(TokenType.string)
	# 				continue
	# 			if token.type == TokenType.right_brace:
	# 				break
	# 			key = JsonString(token.span, JSON_KEY_SCHEMA, '', IndexMapper())
	#
	# 		if token.type != TokenType.colon:
	# 			token = self.accept(TokenType.colon)
	# 		if token.type is TokenType.eof:
	# 			value = JsonInvalid(Span(self._last.span.end, token.span.end), None, '')
	# 			objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
	# 			break
	# 		elif token.type != TokenType.colon:
	# 			if token.type == TokenType.comma:
	# 				value = JsonInvalid(self._last.span, None, '')
	# 				objData.add(key.data, JsonProperty(Span(key.span.start, token.span.start), None, key, value))
	# 				token = self.accept(TokenType.string)
	# 				continue
	# 			if token.type == TokenType.right_brace:
	# 				value = JsonInvalid(self._last.span, None, '')
	# 				objData.add(key.data, JsonProperty(Span(key.span.start, token.span.start), None, key, value))
	# 				break
	# 			pass
	# 		self.acceptAnyOf(self._PARSERS.keys())
	# 		value = self._internalParseTokens()
	#
	# 		token = self.acceptAnyOf({TokenType.comma, TokenType.right_brace})
	# 		if token.type is TokenType.eof:
	# 			objData.add(key.data, JsonProperty(Span(key.span.start, token.span.end), None, key, value))
	# 			break
	# 		objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
	# 		if token.type is TokenType.comma:
	# 			token = self.accept(TokenType.string)
	# 			continue
	# 		if token.type == TokenType.right_brace:
	# 			break
	# 	return token

	def parse_object2(self) -> JsonObject:
		"""Parses an object out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.invalid, TokenType.colon}
		goodValueTokens = {TokenType.string}
		objData: OrderedMultiDict[str, JsonProperty] = OrderedMultiDict()

		def parse_property() -> None:
			nonlocal objData
			colonAlreadySeen = False
			token = self._last
			# parse KEY:
			if token.type == TokenType.string:
				key = self.parse_string()
			elif token.type in self._PARSERS.keys():
				key = self._internalParseTokens()
				if key.typeName != JsonString.typeName:
					self.errorMsg(ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG, span=key.span)
					key = JsonInvalid(key.span, None, bytesToStr(self.text[key.span.slice]))
			elif token.type == TokenType.invalid:
				key = self.parse_invalid()
			elif token.type == TokenType.colon:
				key = JsonInvalid(Span(token.span.start), None, '')
				colonAlreadySeen = True
			else:
				assert False, f"invalid state: invalid TokenType {token.type} for property"
			key.schema = JsonKeySchema()

			if not colonAlreadySeen:
				token = self.accept(TokenType.colon, advanceIfBad=False)

			if token.type is not TokenType.colon:
				value = JsonInvalid(Span(self._last.span.end, token.span.end), None, '')
				objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
				return

			# duplicate colons:
			while (tkn2 := self.tryAccept(TokenType.colon)) is not None:
				self.errorMsg(DUPLICATE_NOT_ALLOWED_MSG, TokenType.colon.asString, span=tkn2.span)

			if token is not None and token.type is TokenType.eof:
				value = JsonInvalid(Span(self._last.span.end, token.span.end), None, '')
				objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			elif self._waitingForClosing[self._current.type] > 0:
				self.errorMsg(MISSING_VALUE_MSG, span=self._last.span)
				value = JsonInvalid(Span(self._last.span.end, self._current.span.start), None, '')
				objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			elif self.tryAcceptAnyOf(self._PARSERS.keys()) is not None:
				value = self._internalParseTokens()
				objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			else:
				# force error, but don't consume:
				self.acceptAnyOf(self._PARSERS.keys(), advanceIfBad=False)
				if self.tryAccept(TokenType.invalid) is not None:
					value = self.parse_invalid()
					objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
					return
				elif (token := self.tryAccept(TokenType.eof)) is not None:
					value = JsonInvalid(Span(self._last.span.end, token.span.end), None, '')
					objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
					return
				else:
					value = JsonInvalid(Span(self._last.span.end, self._current.span.start), None, '')
					objData.add(key.data, JsonProperty(Span(key.span.start, value.span.end), None, key, value))
					return

		start = self._last
		self._parse_list_like(TokenType.comma, TokenType.right_brace, valueTokens, goodValueTokens, parse_property)
		return JsonObject(Span(start.span.start, self._last.span.end), None, objData)

	def _parse_list_like(self, delimiter: TokenType, closing: TokenType, valueTokens: AbstractSet[TokenType], goodValueTokens: AbstractSet[TokenType], parseItem: Callable[[], None]) -> None:
		delimiterOrClosing = {delimiter, closing}

		def tryParseItem(goodTokens):
			if self.tryAcceptAnyOf(valueTokens) is not None:
				parseItem()
			else:  # force error but don't consume:
				self.acceptAnyOf(goodTokens, advanceIfBad=False)

		if self.tryAccept(closing) is not None:
			return
		self._waitingForClosing[closing] += 1
		tryParseItem(goodValueTokens | {closing})

		while True:
			# delimiter or closing:
			if (tkn := self.tryAcceptAnyOf(delimiterOrClosing)) is not None:
				if tkn.type is closing:
					self._waitingForClosing[closing] -= 1
					return
				else:  # now: tkn.type is delimiter:
					while (tkn2 := self.tryAccept(delimiter)) is not None:
						self.errorMsg(DUPLICATE_NOT_ALLOWED_MSG, delimiter.asString, span=tkn2.span)
						tkn = tkn2
					if self.tryAccept(closing) is not None:
						self.errorMsg(TRAILING_NOT_ALLOWED_MSG, delimiter.asString, span=tkn.span)
						self._waitingForClosing[closing] -= 1
						return
					tryParseItem(goodValueTokens)
					continue
			else:
				if self._current.type in valueTokens:
					self.errorMsg(MISSING_DELIMITER_MSG, delimiter.asString, span=self._current.span)
					tryParseItem(goodValueTokens)
					continue
				elif self._waitingForClosing[self._current.type] > 0:
					self.errorMsg(MISSING_CLOSING_MSG, closing.asString, span=self._current.span)
					return
				else:
					# force an error and consume the unknown token, so we don't end up
					# in an infinite loop of trying to parse that token:
					tkn = self.acceptAnyOf(delimiterOrClosing)
					if tkn.type is TokenType.eof:
						return
					# tryParseItem(goodValueTokens)
					continue
			return

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

	def parse_array2(self) -> JsonArray:
		"""Parses an array out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.invalid}
		goodValueTokens = {*self._PARSERS.keys()}
		arrayData: list[JsonData] = []

		def parse_element() -> None:
			nonlocal arrayData
			value = self._internalParseTokens()
			arrayData.append(value)

		start = self._last
		self._parse_list_like(TokenType.comma, TokenType.right_bracket, valueTokens, goodValueTokens, parse_element)
		return JsonArray(Span(start.span.start, self._last.span.end), None, arrayData)

	def parse_string(self) -> JsonString:
		"""Parses a string out of a JSON token"""
		# TODO: usage of IndexMapBuilder needs a thorough testing. It is completely untested. [23-7-2023]
		token = self._last
		string = token.value
		hasEscapeSequence = b'\\' in string

		if hasEscapeSequence:
			idxMapBldr = self.makeIndexMapBuilderForStr(token)

			chars: bytes = b''  # list[str] = []
			index = 1
			strStreakStart = index
			end = len(string) - 1
			while index < end:
				char = string[index]

				if char != ORD_BACKSLASH:
					# chars.append(char)
					index += 1
					continue

				chars += (string[strStreakStart:index])
				decIdx = len(chars)
				next_char = string[index + 1]
				if next_char == ORD_u:  # 'růže' -> "r\u016f\u017ee"
					hex_string = string[index + 2:index + 6]
					try:
						unicode_char = literal_eval(f'"\\u{bytesToStr(hex_string)}"')
					except SyntaxError:
						self.error(MDStr(f"Invalid unicode escape: `\\u{bytesToStr(hex_string)}`"), span=token.span)
						unicode_char = b'\\u' + hex_string
					else:
						unicode_char = strToBytes(unicode_char)
						idxMapBldr.addMarker(index - 1,     decIdx)  # just before (=start of) escape sequence
						idxMapBldr.addMarker(index - 1 + 6, decIdx + 1)  # just after (=end of) escape sequence

					chars += unicode_char
					index += 6
					strStreakStart = index
					continue
				else:
					next_char_str = _ESCAPE_CHAR_MAP.get(next_char)
					if next_char_str is not None:
						chars += next_char_str
						idxMapBldr.addMarker(index - 1,     decIdx)  # just before (=start of) escape sequence
						idxMapBldr.addMarker(index - 1 + 2, decIdx + 1)  # just after (=end of) escape sequence
					else:
						self.error(MDStr(f"Unknown escape sequence: `{bytesToStr(string)}`"), span=token.span)
						chars += string[index:index+2]

					index += 2
					strStreakStart = index

			chars += (string[strStreakStart:index])
			value = bytesToStr(chars)
			decPosLastChar = len(chars)  # = index
			encPosLastChar = len(string) - 2  # we have to account for the quotation marks at start and end of string
			idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
		else:
			if string:
				if string[0] == ORD_DOUBLE_QUOTE:
					string = string[1:].removesuffix(b'"')  # todo probably to be removed. INVESTIGATE
				elif string[0] == ORD_SINGLE_QUOTE:
					string = string[1:].removesuffix(b"'")  # todo probably to be removed. INVESTIGATE
				value = bytesToStr(string)
			else:
				value = ''

			if not self._idxMprIsIdentity:
				idxMapBldr = self.makeIndexMapBuilderForStr(token)
				decPosLastChar = len(string)
				encPosLastChar = decPosLastChar
				idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
			else:
				idxMap = IndexMapper.IDENTITY_MAPPER

		return JsonString(token.span, None, value, idxMap)

	def makeIndexMapBuilderForStr(self, token: Token) -> IndexMapBuilder:
		return IndexMapBuilder(self.indexMapper, self.indexMapper.toDecoded(token.span.start.index) + 1)  # - self.cursorOffset)  # + 1 because of opening quotation marks?

	def parse_number(self) -> JsonNumber:
		"""Parses a number out of a JSON token"""
		token = self._last
		try:

			if token.value and token.value[0] == ORD_MINUS:
				valToCHeck = token.value[1:]
			else:
				valToCHeck = token.value
			if valToCHeck.isdigit():
				number = int(token.value)
			else:
				number = float(token.value)
			return JsonNumber(token.span, None, number)

		except ValueError:
			pass # numbers are checked by lexer already.
		return JsonNumber(token.span, None, 0)

	def parse_boolean(self) -> JsonBool:
		"""Parses a boolean out of a JSON token"""
		token = self._last
		value = _BOOLEAN_TOKENS[token.value]
		return JsonBool(token.span, None, value)

	def parse_null(self) -> JsonNull:
		"""Parses a null value out of a JSON token"""
		token = self._last
		return JsonNull(token.span, None)

	def parse_invalid(self) -> JsonInvalid:
		"""Parses a invalid token out of a JSON token"""
		token = self._last
		return JsonInvalid(token.span, None, bytesToStr(token.value))

	@CachedProperty
	def _PARSERS(self) -> dict[TokenType, Callable[[], JsonData]]:
		return {
			TokenType.left_bracket: self.parse_array2,
			TokenType.left_brace: self.parse_object2,
			TokenType.string: self.parse_string,
			TokenType.number: self.parse_number,
			TokenType.boolean: self.parse_boolean,
			TokenType.null: self.parse_null,
		}

	def _internalParseTokens(self) -> JsonData:
		"""Recursive JSON parse implementation"""
		token = self._last
		parser = self._PARSERS.get(token.type)
		if parser is not None:
			value = parser()
			return value
		else:
			return JsonInvalid(token.span, None, bytesToStr(token.value))

	def parseJsonTokens(self) -> Optional[JsonData]:
		"""Recursive JSON parse implementation"""
		token = self.acceptAnyOf(self._PARSERS.keys())
		if token is not None:
			data = self._internalParseTokens()
			pathify(data, '')
			enrichWithSchema(data, self.schema)
		else:
			data = None
		return data

	@ProfiledFunction(enabled=False)
	def parse(self) -> Optional[JsonData]:
		"""Parses a JSON string into a Python object"""
		value = self.parseJsonTokens()

		if self._current is not None and self._current.type is not TokenType.eof:
			self.error(
				MDStr(f"Invalid JSON at `{bytesToStr(self._current.value)}`"),
				span=self._current.span
			)

		return value


def init():
	pass
