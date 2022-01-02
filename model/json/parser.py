"""Parser functions, based on www.github.com/tusharsadhwani/json_parser"""
from ast import literal_eval
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, AbstractSet

from Cat.utils.collections_ import OrderedMultiDict
from Cat.utils.profiling import ProfiledFunction
from model.json.lexer import Token, tokenizeJson, TokenType
from model.json.core import *
from model.json.schema import enrichWithSchema
from model.utils import GeneralParsingError, Span, Message

EOF_MSG = Message("Unexpected end of file while parsing", 0)
EXPECTED_BUT_GOT_MSG = Message("Expected `{0}` but got `{1}`", 2)


class JsonParseError(GeneralParsingError):
	pass


# class ParseError(Exception):
# 	"""Error thrown when invalid JSON tokens are parsed"""
# 	def __init__(self, data: JsonParseError):
# 		super(ParseError, self).__init__(str(data))
# 		self.data: JsonParseError = data


@dataclass
class ParserData:
	tokens: deque[Token]
	lastToken: Optional[Token] = None
	errors: list[JsonParseError] = field(default_factory=list)

	@property
	def hasTokens(self) -> bool:
		return bool(self.tokens)

	def accept(self, tokenType: TokenType) -> Optional[Token]:
		if len(self.tokens) == 0:
			span = self.lastToken.span if self.lastToken is not None else Span()
			self.errors.append(JsonParseError(EOF_MSG.format(), span))
			return None

		token = self.tokens.popleft()
		self.lastToken = token
		if token.type is not tokenType:
			msg = EXPECTED_BUT_GOT_MSG.format(tokenType.name, token.value)
			self.errors.append(JsonParseError(msg, token.span))
		return token

	def acceptAnyOf(self, tokenTypes: AbstractSet[TokenType]) -> Optional[Token]:
		if len(self.tokens) == 0:
			span = self.lastToken.span if self.lastToken is not None else Span()
			self.errors.append(JsonParseError(EOF_MSG.format(), span))
			return None

		token = self.tokens.popleft()
		self.lastToken = token
		if token.type not in tokenTypes:
			msg = EXPECTED_BUT_GOT_MSG.format('|'.join(tk.name for tk in tokenTypes), token.value)
			self.errors.append(JsonParseError(msg, token.span))
		return token

	def acceptAny(self) -> Optional[Token]:
		if len(self.tokens) == 0:
			span = self.lastToken.span if self.lastToken is not None else Span()
			self.errors.append(JsonParseError(EOF_MSG.format(), span))
			return None
		token = self.tokens.popleft()
		self.lastToken = token
		return token

	def pop(self) -> Token:
		token = self.tokens.popleft()
		self.lastToken = token
		return token


def parse_object(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonObject:
	"""Parses an object out of JSON tokens"""
	objData: OrderedMultiDict[str, JsonProperty] = OrderedMultiDict()
	isObjectSchema = isinstance(schema, JsonObjectSchema)

	start = psr.lastToken

	token = psr.acceptAnyOf({TokenType.right_brace, TokenType.string})
	if token is None:
		return JsonObject(objData, start.span, schema)
	# special case:
	if token.type is TokenType.right_brace:
		return JsonObject(objData, Span(start.span.start, token.span.end), schema)

	while token is not None:
		if token.type == TokenType.string:
			key = parse_string(psr, None)
		else:
			if token.type == TokenType.comma:
				token = psr.accept(TokenType.string)
				continue
			if token.type == TokenType.right_brace:
				break
			key = JsonString('', token.span, None)

		propertySchema = schema.propertiesDict.get(key.data) if isObjectSchema else None
		valueSchema = propertySchema.value if propertySchema is not None else None

		if token.type != TokenType.colon:
			token = psr.accept(TokenType.colon)
		if token is None:
			value = JsonNull(None, Span(psr.lastToken.span.end), valueSchema)
			objData.add(key.data, JsonProperty(key, value, propertySchema))
			break
		elif token.type != TokenType.colon:
			if token.type == TokenType.comma:
				value = JsonNull(None, psr.lastToken.span, valueSchema)
				objData.add(key.data, JsonProperty(key, value, propertySchema))
				token = psr.accept(TokenType.string)
				continue
			if token.type == TokenType.right_brace:
				value = JsonNull(None, psr.lastToken.span, valueSchema)
				objData.add(key.data, JsonProperty(key, value, propertySchema))
				break
			pass
		psr.acceptAnyOf(_PARSERS.keys())
		value = _internalParseTokens(psr, valueSchema)
		objData.add(key.data, JsonProperty(key, value, propertySchema))

		token = psr.acceptAnyOf({TokenType.comma, TokenType.right_brace})
		if token is None:
			break
		if token.type is TokenType.comma:
			token = psr.accept(TokenType.string)
			continue
		if token.type == TokenType.right_brace:
			break

	if token is None:
		token = psr.lastToken
	return JsonObject(objData, Span(start.span.start, token.span.end), schema)


def parse_array(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonArray:
	"""Parses an array out of JSON tokens"""

	arrayData: list[JsonData] = []
	elementSchema = schema.element if isinstance(schema, JsonArraySchema) else None

	start = psr.lastToken

	token = psr.acceptAnyOf({TokenType.right_bracket, *_PARSERS.keys()})
	if token is None:
		return JsonArray(arrayData, start.span, schema)
	# special case:
	if token.type is TokenType.right_bracket:
		return JsonArray(arrayData, Span(start.span.start, token.span.end), schema)

	while token is not None:

		value = _internalParseTokens(psr, elementSchema)
		arrayData.append(value)

		token = psr.acceptAnyOf({TokenType.comma, TokenType.right_bracket})
		if token is None:
			break
		if token.type is TokenType.comma:
			token = psr.acceptAnyOf(_PARSERS.keys())
			continue
		if token.type == TokenType.right_bracket:
			break

	if token is None:
		token = psr.lastToken
	return JsonArray(arrayData, Span(start.span.start, token.span.end), schema)


def parse_string(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonString:
	"""Parses a string out of a JSON token"""

	token = psr.lastToken
	string = token.value

	if '\\' in string:
		chars: list[str] = []
		index = 1
		end = len(token.value) - 1
		while index < end:
			char = token.value[index]

			if char != '\\':
				chars.append(char)
				index += 1
				if char == '\n':
					pass
				else:
					pass
				continue

			next_char = token.value[index+1]
			if next_char == 'u':
				hex_string = token.value[index+2:index+6]
				try:
					unicode_char = literal_eval(f'"\\u{hex_string}"')
				except SyntaxError as err:
					psr.errors.append(JsonParseError(f"Invalid unicode escape: `\\u{hex_string}`", token.span))
					unicode_char = '\\u{hex_string}'

				chars.append(unicode_char)
				index += 6
				continue

			if next_char in ('"', '/', '\\'):
				chars.append(next_char)
			elif next_char == 'b':
				chars.append('\b')
			elif next_char == 'f':
				chars.append('\f')
			elif next_char == 'n':
				chars.append('\n')
			elif next_char == 'r':
				chars.append('\r')
			elif next_char == 't':
				chars.append('\t')
			else:
				psr.errors.append(JsonParseError(f"Unknown escape sequence: `{token.value}`", token.span))

			index += 2

		string = ''.join(chars)
	elif string:
		if string[0] == '"':
			string = string[1:].removesuffix('"')
		elif string[0] == "'":
			string = string[1:].removesuffix("'")
	return JsonString(string, token.span, schema)


def parse_number(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonNumber:
	"""Parses a number out of a JSON token"""
	token = psr.lastToken
	try:
		if token.value.isdigit():
			number = int(token.value)
		else:
			number = float(token.value)
		return JsonNumber(number, token.span, schema)

	except ValueError as err:
		psr.errors.append(JsonParseError(f"Invalid number: `{token.value} ", token.span))
	return JsonNumber(0, token.span, schema)


BOOLEAN_TOKENS = {
	'true': True,
	'false': False,
}


def parse_boolean(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonBool:
	"""Parses a boolean out of a JSON token"""
	token = psr.lastToken
	value = BOOLEAN_TOKENS[token.value]
	return JsonBool(value, token.span, schema)


def parse_null(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonNull:
	"""Parses a boolean out of a JSON token"""
	token = psr.lastToken
	return JsonNull(None, token.span, schema)


_PARSERS = {
	TokenType.left_bracket: parse_array,
	TokenType.left_brace: parse_object,
	TokenType.string: parse_string,
	TokenType.number: parse_number,
	TokenType.boolean: parse_boolean,
	TokenType.null: parse_null,
}


def _internalParseTokens(psr: ParserData, schema: Optional[JsonArraySchema]) -> JsonData:
	"""Recursive JSON parse implementation"""
	token = psr.lastToken
	if isinstance(schema, JsonUnionSchema):
		schema = schema.optionsDict.get(token.type, schema)
	parser = _PARSERS.get(token.type)
	if parser is not None:
		value = parser(psr, schema)
		return value
	else:
		return JsonNull(None, token.span, schema)


def parseJsonTokens(tokens: deque[Token], schema: Optional[JsonSchema]) -> tuple[Optional[JsonData], list[GeneralParsingError]]:
	"""Recursive JSON parse implementation"""
	psr = ParserData(tokens)
	token = psr.acceptAnyOf(_PARSERS.keys())
	if token is not None:
		data = _internalParseTokens(psr, schema)
		enrichWithSchema(data, schema)
	else:
		data = None
	return data, psr.errors


@ProfiledFunction(enabled=False)
def parseJsonStr(json_string: str, allowMultilineStr: bool, schema: Optional[JsonSchema]) -> tuple[Optional[JsonData], list[GeneralParsingError]]:
	"""Parses a JSON string into a Python object"""
	tokens, errors = tokenizeJson(json_string, allowMultilineStr)
	value, errors2 = parseJsonTokens(tokens, schema)
	errors += errors2
	if len(tokens) != 0:
		errors.append(JsonParseError(
			f"Invalid JSON at {tokens[0].value} ",
			tokens[0].span
		))

	return value, errors
