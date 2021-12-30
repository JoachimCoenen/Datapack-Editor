"""Parser functions, based on www.github.com/tusharsadhwani/json_parser"""
from ast import literal_eval
from typing import Deque, List, Optional

from Cat.utils.collections_ import OrderedMultiDict
from model.json.lexer import Token, tokenizeJson, TokenizeError, TokenType
from model.json.core import *
from model.utils import GeneralParsingError, Span


class ParseErrorData(GeneralParsingError):
	pass


class ParseError(Exception):
	"""Error thrown when invalid JSON tokens are parsed"""
	def __init__(self, data: ParseErrorData):
		super(ParseError, self).__init__(str(data))
		self.data: ParseErrorData = data


def parse_object(tokens: Deque[Token], schema: Optional[JsonObjectSchema]) -> JsonObject:
	"""Parses an object out of JSON tokens"""
	objData: OrderedMultiDict[JsonString, JsonData] = OrderedMultiDict()

	start = token = tokens.popleft()
	# special case:
	if tokens[0].type == TokenType.right_brace:
		token = tokens.popleft()
	else:
		isObjectSchema = isinstance(schema, JsonObjectSchema)
		while tokens:
			token = tokens[0]

			if not token.type == TokenType.string:
				raise ParseError(ParseErrorData(
					f"Expected string key for object, found {token.value} ",
					token.span
				))

			key = parse_string(tokens, None)

			if len(tokens) == 0:
				raise ParseError(ParseErrorData(
					"Unexpected end of file while parsing ",
					token.span
				))

			token = tokens.popleft()
			if token.type != TokenType.colon:
				raise ParseError(ParseErrorData(
					f"Expected colon, found {token.value} ",
					token.span
				))

			# Missing value for key
			if len(tokens) == 0:
				raise ParseError(ParseErrorData(
					"Unexpected end of file while parsing ",
					token.span
				))

			if tokens[0].type == TokenType.right_brace:
				token = tokens[0]
				raise ParseError(ParseErrorData(
					"Expected value after colon, found } ",
					token.span
				))

			valueSchema = schema.propertiesDict.get(key.data) if isObjectSchema else None
			valueSchema = valueSchema.value if valueSchema is not None else None
			value = parseJsonTokens(tokens, valueSchema)
			objData.add(key, value)

			if len(tokens) == 0:
				raise ParseError(ParseErrorData(
					"Unexpected end of file while parsing ",
					token.span
				))

			token = tokens.popleft()
			if token.type not in (TokenType.comma, TokenType.right_brace):
				raise ParseError(ParseErrorData(
					f"Expected ',' or '}}', found {token.value}",
					token.span
				))

			if token.type == TokenType.right_brace:
				break

			# Trailing comma checks
			if len(tokens) == 0:
				raise ParseError(ParseErrorData(
					"Unexpected end of file while parsing ",
					token.span
				))

			if tokens[0].type == TokenType.right_brace:
				token = tokens[0]
				raise ParseError(ParseErrorData(
					"Expected value after comma, found } ",
					token.span
				))

	return JsonObject(objData, Span(start.span.start, token.span.end), schema)


def parse_array(tokens: Deque[Token], schema: Optional[JsonArraySchema]) -> JsonArray:
	"""Parses an array out of JSON tokens"""

	array: list[JsonData] = []

	start = token = tokens.popleft()
	# special case:
	if tokens[0].type == TokenType.right_bracket:
		token = tokens.popleft()
	else:
		elementSchema = schema.element if isinstance(schema, JsonArraySchema) else None
		while tokens:
			value = parseJsonTokens(tokens, elementSchema)
			array.append(value)

			token = tokens.popleft()
			if token.type not in (TokenType.comma, TokenType.right_bracket):
				raise ParseError(ParseErrorData(
					f"Expected ',' or ']', found {token.value} ",
					token.span
				))

			if token.type == TokenType.right_bracket:
				break

			# trailing comma check
			if len(tokens) == 0:
				raise ParseError(ParseErrorData(
					"Unexpected end of file while parsing ",
					token.span
				))

			if tokens[0].type == TokenType.right_bracket:
				token = tokens[0]
				raise ParseError(ParseErrorData(
					"Expected value after comma, found ] ",
					token.span
				))

	return JsonArray(array, Span(start.span.start, token.span.end), schema)


def parse_string(tokens: Deque[Token], schema: Optional[JsonSchema]) -> JsonString:
	"""Parses a string out of a JSON token"""
	chars: List[str] = []

	token = tokens.popleft()

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
				raise ParseError(ParseErrorData(
					f"Invalid unicode escape: \\u{hex_string} ",
					token.span
				)) from err

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
			raise ParseError(ParseErrorData(
				f"Unknown escape sequence: {token.value} ",
				token.span
			))

		index += 2

	string = ''.join(chars)
	return JsonString(string, token.span, schema)


def parse_number(tokens: Deque[Token], schema: Optional[JsonSchema]) -> JsonNumber:
	"""Parses a number out of a JSON token"""
	token = tokens.popleft()
	try:
		if token.value.isdigit():
			number = int(token.value)
		else:
			number = float(token.value)
		return JsonNumber(number, token.span, schema)

	except ValueError as err:
		raise ParseError(ParseErrorData(
			f"Invalid token: {token.value} ",
			token.span
		)) from err


BOOLEAN_TOKENS = {
	'true': True,
	'false': False,
}


def parse_boolean(tokens: Deque[Token], schema: Optional[JsonSchema]) -> JsonBool:
	"""Parses a boolean out of a JSON token"""
	token = tokens.popleft()
	value = BOOLEAN_TOKENS[token.value]
	return JsonBool(value, token.span, schema)


def parse_null(tokens: Deque[Token], schema: Optional[JsonSchema]) -> JsonNull:
	"""Parses a boolean out of a JSON token"""
	token = tokens.popleft()
	return JsonNull(None, token.span, schema)


_PARSERS = {
	TokenType.left_bracket: parse_array,
	TokenType.left_brace: parse_object,
	TokenType.string: parse_string,
	TokenType.number: parse_number,
	TokenType.boolean: parse_boolean,
	TokenType.null: parse_null,
}


def parseJsonTokens(tokens: Deque[Token], schema: Optional[JsonSchema]) -> JsonData:
	"""Recursive JSON parseJsonStr implementation"""
	token = tokens[0]
	if isinstance(schema, JsonUnionSchema):
		schema = schema.optionsDict.get(token.type, schema)
	parser = _PARSERS.get(token.type)
	if parser is not None:
		return parser(tokens, schema)
	else:
		raise ParseError(ParseErrorData(
			f"Unexpected token: {token.value} ",
			token.span
		))


def parseJsonStr(json_string: str, schema: Optional[JsonSchema]) -> tuple[Optional[JsonData], list[ParseErrorData]]:
	"""Parses a JSON string into a Python object"""
	value = None
	try:
		tokens = tokenizeJson(json_string)
		value = parseJsonTokens(tokens, schema)
		if len(tokens) != 0:
			raise ParseError(ParseErrorData(
				f"Invalid JSON at {tokens[0].value} ",
				tokens[0].span
			))
	except (ParseError, TokenizeError) as e:
		errors = [e.data]
	else:
		errors = []

	return value, errors
