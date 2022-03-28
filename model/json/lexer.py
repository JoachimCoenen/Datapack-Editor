"""Lexer functions, based on www.github.com/tusharsadhwani/json_parser"""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple
from string import whitespace as WHITESPACE, ascii_letters

from model.utils import Span, GeneralError, Position, Message


INCOMPLETE_ESCAPE_MSG = Message("Incomplete escape at end of string", 0)
SINGLE_QUOTED_STRING_MSG = Message("JSON standard does not allow single quoted strings", 0)
EXPECTED_END_OF_STRING_MSG = Message("Expected end of string", 0)
MISSING_CLOSING_QUOTE_MSG = Message("Missing closing quote", 0)
# TOO_MANY_DECIMAL_POINTS_MSG = Message("Too many decimal points in number", 0)
# MINUS_SIGN_INSIDE_NUMBER_MSG = Message("Minus sign in between number", 0)
INVALID_NUMBER_MSG = Message("Minus sign in between number `{0}`", 1)
UNKNOWN_LITERAL_MSG = Message("Unknown literal `{0}`", 1)
ILLEGAL_CHARS_MSG = Message("Illegal characters `{0}`", 1)
EMPTY_STRING_MSG = Message("Cannot parse empty string", 0)


Char = str


class TokenType(Enum):
	default = 0
	null = 1
	boolean = 2
	number = 3
	string = 4
	left_bracket = 5
	left_brace = 6
	right_bracket = 7
	right_brace = 8
	comma = 9
	colon = 10
	invalid = 11
	eof = 12

	@property
	def asString(self) -> str:
		return _TOKEN_TYPE_STR_REP[self]


_TOKEN_TYPE_STR_REP = {
	TokenType.default: "default",
	TokenType.null: "null",
	TokenType.boolean: "boolean",
	TokenType.number: "number",
	TokenType.string: "string",
	TokenType.left_bracket: "'['",
	TokenType.left_brace: "'{'",
	TokenType.right_bracket: "']'",
	TokenType.right_brace: "'}'",
	TokenType.comma: "','",
	TokenType.colon: "':'",
	TokenType.invalid: "invalid",
	TokenType.eof: "end of file",
}


class Token(NamedTuple):
	"""Represents a Token extracted by the parser"""
	value: str
	type: TokenType
	span: Span
	# isValid: bool = True


class JsonTokenizeError(GeneralError):
	pass


WHITESPACE_NO_LF = ' \t\r\v\f'
"""without the line feed character (\\n)"""


CR_LF = '\r\n'
"""carriage return & line feed (\\r\\n)"""


@dataclass
class JsonTokenizer:
	source: str
	allowMultilineStr: bool
	cursor: int = 0
	line: int = 0
	lineStart: int = 0
	totalLength: int = field(init=False)
	tokens: deque[Token] = field(default_factory=deque)
	errors: list[JsonTokenizeError] = field(default_factory=list)
	_errorsNextToken: list[tuple[Message, tuple, str]] = field(default_factory=list, init=False)

	def __post_init__(self):
		self.totalLength = len(self.source)

	@property
	def position(self) -> Position:
		return Position(self.line, self.cursor-self.lineStart, self.cursor)

	@property
	def char(self) -> Char:
		return self.source[self.cursor]

	def advanceLine(self) -> None:
		self.lineStart = self.cursor
		self.line += 1

	def addToken(self, start: Position, tokenType: TokenType) -> Token:
		end = self.position
		span = Span(start, end)
		token = Token(self.source[start.index:end.index], tokenType, span)
		self.tokens.append(token)
		# add errors:
		if self._errorsNextToken:
			for msg, args, style in self._errorsNextToken:
				self.errorLastToken(msg, *args, style=style)
			self._errorsNextToken.clear()
		return token

	def addToken2(self, start: Position, value: str, tokenType: TokenType) -> Token:
		end = self.position
		span = Span(start, end)
		token = Token(value, tokenType, span)
		self.tokens.append(token)
		# add errors:
		if self._errorsNextToken:
			for msg, args, style in self._errorsNextToken:
				self.errorLastToken(msg, *args, style=style)
			self._errorsNextToken.clear()
		return token

	def errorNextToken(self, msg: Message, *args, style: str = 'error') -> None:
		self._errorsNextToken.append((msg, args, style))

	def errorLastToken(self, msg: Message, *args, style: str = 'error') -> None:
		msgStr = msg.format(*args)
		if self.tokens:
			span = self.tokens[-1].span  # maybe self.tokens[0] ?
		else:
			span = Span()
		self.errors.append(JsonTokenizeError(msgStr, span, style=style))

	def consumeWhitespace(self) -> None:
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		while cursor < length:
			if source[cursor] in WHITESPACE_NO_LF:
				cursor += 1
			elif source[cursor] == '\n':
				cursor += 1
				self.lineStart = cursor
				self.line += 1
			else:
				break
		self.cursor = cursor


def extract_string(tkz: JsonTokenizer) -> None:
	"""Extracts a single string token from JSON string"""
	start = tkz.position
	quote = tkz.source[tkz.cursor]
	if quote == "'":
		tkz.errorNextToken(SINGLE_QUOTED_STRING_MSG)
	tkz.cursor += 1  # opening '"'

	while tkz.cursor < tkz.totalLength:
		char = tkz.source[tkz.cursor]
		tkz.cursor += 1

		if char == '\\':
			if tkz.cursor == tkz.totalLength or tkz.source[tkz.cursor] in CR_LF:
				tkz.addToken(start, TokenType.string)
				tkz.errorLastToken(INCOMPLETE_ESCAPE_MSG)
				return
			else:
				tkz.cursor += 1
				continue

		elif char == quote:
			tkz.addToken(start, TokenType.string)
			return

		elif char == '\n':
			if tkz.allowMultilineStr:
				tkz.advanceLine()
			else:
				tkz.cursor -= 1  # '\n' is not part of the string
				break

	tkz.addToken(start, TokenType.string)
	tkz.errorLastToken(MISSING_CLOSING_QUOTE_MSG)


def extract_number(tkz: JsonTokenizer) -> None:
	"""Extracts a single number token (eg. 42, -12.3) from JSON string"""
	start = tkz.position

	decimal_point_found = False
	exponent_found = False
	isValid = True

	if tkz.cursor < tkz.totalLength and tkz.source[tkz.cursor] in '-+':
		tkz.cursor += 1

	while tkz.cursor < tkz.totalLength:
		char = tkz.source[tkz.cursor]
		tkz.cursor += 1

		if char.isdigit():
			continue
		elif char == '.':
			if decimal_point_found:
				isValid = False
			decimal_point_found = True
			continue
		elif char in '+-':
			if not tkz.source[tkz.cursor] in 'eE':
				isValid = False
			continue
		elif char in 'eE':
			if exponent_found:
				isValid = False
			exponent_found = True
			continue
		elif char in ',' + WHITESPACE + '}]"\':=[{\\':
			tkz.cursor -= 1
			break
		else:
			continue

	token = tkz.addToken(start, TokenType.number)

	if not isValid:
		tkz.errorLastToken(INVALID_NUMBER_MSG, token.value)


_TOKEN_TYPE_FOR_SPECIAL = {
	'true': TokenType.boolean,
	'false': TokenType.boolean,
	'null': TokenType.null,
}


def extract_special(tkz: JsonTokenizer) -> None:
	"""Extracts true, false and null from JSON string"""
	start = tkz.position
	tkz.cursor += 1  # first letter
	while tkz.cursor < tkz.totalLength and tkz.source[tkz.cursor].isalpha():
		tkz.cursor += 1

	word = tkz.source[start.index:tkz.cursor]
	tkType = _TOKEN_TYPE_FOR_SPECIAL.get(word, TokenType.invalid)
	token = tkz.addToken2(start, word, tkType)
	if token.type is TokenType.invalid:
		tkz.errorLastToken(UNKNOWN_LITERAL_MSG, token.value)


def extract_illegal(tkz: JsonTokenizer) -> None:
	"""Extracts illegal characters from JSON string"""
	start = tkz.position
	tkz.cursor += 1  # first character
	while tkz.cursor < tkz.totalLength:
		char = tkz.source[tkz.cursor]
		if char.isalnum():
			break
		if char in WHITESPACE:
			break
		if char in '[]{},:+-.':
			break
		tkz.cursor += 1

	token = tkz.addToken(start, TokenType.invalid)
	if token.type is TokenType.invalid:
		tkz.errorLastToken(ILLEGAL_CHARS_MSG, repr(token.value))


def extract_operator(tkz: JsonTokenizer) -> None:
	start = tkz.position
	char = tkz.source[tkz.cursor]
	tkz.cursor += 1
	tkz.addToken2(start, char, _TOKEN_TYPE_FOR_OPERATOR[char])


_TOKEN_TYPE_FOR_OPERATOR = {
	'[': TokenType.left_bracket,
	']': TokenType.right_bracket,
	'{': TokenType.left_brace,
	'}': TokenType.right_brace,
	',': TokenType.comma,
	':': TokenType.colon,
}


_OPERATOR_FOR_TOKEN_TYPE = {v: k for k, v in _TOKEN_TYPE_FOR_OPERATOR.items()}


_TOKEN_EXTRACTORS_BY_CHAR = {
	# **{c: extract_operator for c in '[]{},:'},
	**{c: extract_string for c in '"\''},
	**{c: extract_special for c in ascii_letters},  # 'e' & 'E' will be replaced again with 'e': extract_number,
	**{c: extract_number for c in '0123456789+-.eE'},
}


def tokenizeJson(source: str, allowMultilineStr: bool) -> tuple[deque[Token], list[GeneralError]]:
	"""Converts a JSON string into a queue of tokens"""
	tkz = JsonTokenizer(source, allowMultilineStr)

	tkz.consumeWhitespace()
	while tkz.cursor < tkz.totalLength:
		char = tkz.source[tkz.cursor]
		if char == '"':
			extract_string(tkz)
		elif char in '[]{},:':
			extract_operator(tkz)
		# elif char in '0123456789+-.eE':
		# 	extract_number(tkz)
		elif char in 'tfn':
			extract_special(tkz)
		# elif char == "'":
		# 	extract_string(tkz)
		else:
			extractor = _TOKEN_EXTRACTORS_BY_CHAR.get(char, extract_illegal)
			extractor(tkz)
		tkz.consumeWhitespace()
	tkz.addToken2(tkz.position, '', TokenType.eof)

		# if char in '[]{},:':
		# 	start = tkz.position
		# 	tkz.cursor += 1
		# 	tkz.addToken(start, _TOKEN_TYPE_FOR_OPERATOR[char])
		# elif char == '"':
		# 	extract_string(tkz)
		# elif char.isdigit() or char in '+-':
		# 	extract_number(tkz)
		# elif char.isalpha():
		# 	extract_special(tkz)
		# else:
		# 	extract_illegal(tkz)
		#
		# tkz.consumeWhitespace()

	if len(tkz.tokens) == 0:
		tkz.errorLastToken(EMPTY_STRING_MSG)

	return tkz.tokens, tkz.errors
