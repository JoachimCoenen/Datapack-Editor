"""Lexer functions, loosely based on www.github.com/tusharsadhwani/json_parser"""
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple, Optional

from Cat.utils import CachedProperty
from model.parsing.bytesUtils import *
from model.parsing.parser import TokenizerBase
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


Char = int


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
	value: bytes
	type: TokenType
	span: Span
	# isValid: bool = True


class JsonTokenizeError(GeneralError):
	pass


_TOKEN_TYPE_FOR_SPECIAL = {
	b'true': TokenType.boolean,
	b'false': TokenType.boolean,
	b'null': TokenType.null,
}

_TOKEN_TYPE_FOR_OPERATOR = {
	ord('['): TokenType.left_bracket,
	ord(']'): TokenType.right_bracket,
	ord('{'): TokenType.left_brace,
	ord('}'): TokenType.right_brace,
	ord(','): TokenType.comma,
	ord(':'): TokenType.colon,
}


_OPERATOR_FOR_TOKEN_TYPE = {v: k for k, v in _TOKEN_TYPE_FOR_OPERATOR.items()}


@dataclass
class JsonTokenizer(TokenizerBase[Token]):
	allowMultilineStr: bool
	_errorsNextToken: list[tuple[Message, tuple, str]] = field(default_factory=list, init=False)

	@property
	def char(self) -> Char:
		return self.text[self.cursor]

	def addToken(self, start: Position, tokenType: TokenType) -> Token:
		end = self.currentPos
		span = Span(start, end)
		token = Token(self.text[start.index-self.cursorOffset:end.index-self.cursorOffset], tokenType, span)
		# add errors:
		if self._errorsNextToken:
			for msg, args, style in self._errorsNextToken:
				self.error(msg, *args, span=token.span, style=style)
			self._errorsNextToken.clear()
		return token

	def addToken2(self, start: Position, value: bytes, tokenType: TokenType) -> Token:
		end = self.currentPos
		span = Span(start, end)
		token = Token(value, tokenType, span)
		# add errors:
		if self._errorsNextToken:
			for msg, args, style in self._errorsNextToken:
				self.error(msg, *args, span=token.span, style=style)
			self._errorsNextToken.clear()
		return token

	def errorNextToken(self, msg: Message, *args, style: str = 'error') -> None:
		self._errorsNextToken.append((msg, args, style))

	def error(self, msg: Message, *args, span: Span, style: str = 'error') -> None:
		msgStr = msg.format(*args)
		self.errors.append(JsonTokenizeError(msgStr, span, style=style))

	def consumeWhitespace(self) -> None:
		cursor: int = self.cursor
		source: bytes = self.text
		length: int = self.totalLength
		while cursor < length:
			if source[cursor] in WHITESPACE_NO_LF:
				cursor += 1
			elif source[cursor] == ord('\n'):
				cursor += 1
				self.lineStart = cursor
				self.line += 1
			else:
				break
		self.cursor = cursor

	def extract_string(self) -> Token:
		"""Extracts a single string token from JSON string"""
		start = self.currentPos
		quote = self.text[self.cursor]
		if quote == ord("'"):
			self.errorNextToken(SINGLE_QUOTED_STRING_MSG)
		self.cursor += 1  # opening '"'

		while self.cursor < self.totalLength:
			char = self.text[self.cursor]
			self.cursor += 1

			if char == ord('\\'):
				if self.cursor == self.totalLength or self.text[self.cursor] in CR_LF:
					self.errorNextToken(INCOMPLETE_ESCAPE_MSG)
					return self.addToken(start, TokenType.string)
				else:
					self.cursor += 1
					continue

			elif char == quote:
				return self.addToken(start, TokenType.string)

			elif char == ord('\n'):
				if self.allowMultilineStr:
					self.advanceLine()
				else:
					self.cursor -= 1  # '\n' is not part of the string
					break

		self.errorNextToken(MISSING_CLOSING_QUOTE_MSG)
		return self.addToken(start, TokenType.string)

	def extract_number(self) -> Token:
		"""Extracts a single number token (eg. 42, -12.3) from JSON string"""
		start = self.currentPos

		decimal_point_found = False
		exponent_found = False
		isValid = True

		if self.cursor < self.totalLength and self.text[self.cursor] in b'-+':
			self.cursor += 1

		while self.cursor < self.totalLength:
			char = self.text[self.cursor]
			self.cursor += 1

			if char in DIGITS_RANGE:
				continue
			elif char == '.':
				if decimal_point_found:
					isValid = False
				decimal_point_found = True
				continue
			elif char in b'+-':
				if not self.text[self.cursor] in b'eE':
					isValid = False
				continue
			elif char in b'eE':
				if exponent_found:
					isValid = False
				exponent_found = True
				continue
			elif char in b',' + WHITESPACE + b'}]"\':=[{\\':
				self.cursor -= 1
				break
			else:
				continue

		token = self.addToken(start, TokenType.number)
		if not isValid:
			self.error(INVALID_NUMBER_MSG, token.value, span=token.span)
		return token

	def extract_special(self) -> Token:
		"""Extracts true, false and null from JSON string"""
		start = self.currentPos
		self.cursor += 1  # first letter
		while self.cursor < self.totalLength and (self.text[self.cursor] in ASCII_LOWERCASE_RANGE or self.text[self.cursor] in ASCII_UPPERCASE_RANGE):
			self.cursor += 1

		word = self.text[start.index - self.cursorOffset:self.cursor]
		tkType = _TOKEN_TYPE_FOR_SPECIAL.get(word, TokenType.invalid)
		token = self.addToken2(start, word, tkType)
		if token.type is TokenType.invalid:
			self.error(UNKNOWN_LITERAL_MSG, token.value, span=token.span)
		return token

	def extract_illegal(self) -> Token:
		"""Extracts illegal characters from JSON string"""
		start = self.currentPos
		self.cursor += 1  # first character
		while self.cursor < self.totalLength:
			char = self.text[self.cursor]
			# if chr(char).isalnum():
			if char in DIGITS_RANGE or char in ASCII_LOWERCASE_RANGE or char in ASCII_UPPERCASE_RANGE:
				break
			if char in WHITESPACE:
				break
			if char in b'[]{},:+-.':
				break
			self.cursor += 1

		token = self.addToken(start, TokenType.invalid)
		if token.type is TokenType.invalid:
			self.error(ILLEGAL_CHARS_MSG, repr(bytesToStr(token.value)), span=token.span)
		return token

	def extract_operator(self) -> Token:
		start = self.currentPos
		char = self.text[self.cursor]
		self.cursor += 1
		return self.addToken2(start, char.to_bytes(1, 'big'), _TOKEN_TYPE_FOR_OPERATOR[char])

	@CachedProperty
	def _TOKEN_EXTRACTORS_BY_CHAR(self):
		return {
			# **{c: extract_operator for c in '[]{},:'},
			**{c: self.extract_string for c in b'"\''},
			**{c: self.extract_special for c in ASCII_LETTERS},  # 'e' & 'E' will be replaced again with 'e': extract_number,
			**{c: self.extract_number for c in b'0123456789+-.eE'},
		}

	# def tokenize(self) -> tuple[deque[Token], list[GeneralError]]:
	# 	"""Converts a JSON string into a queue of tokens"""
	# 	self.consumeWhitespace()
	# 	while self.cursor < self.totalLength:
	# 		char = self.text[self.cursor]
	# 		if char == ord('"'):
	# 			self.extract_string()
	# 		elif char in b'[]{},:':
	# 			self.extract_operator()
	# 		# elif char in '0123456789+-.eE':
	# 		# 	extract_number(self)
	# 		elif char in b'tfn':
	# 			self.extract_special()
	# 		# elif char == "'":
	# 		# 	extract_string(self)
	# 		else:
	# 			extractor = self._TOKEN_EXTRACTORS_BY_CHAR.get(char, self.extract_illegal)
	# 			extractor()
	# 		self.consumeWhitespace()
	# 	self.addToken2(self.currentPos, b'', TokenType.eof)
	#
	# 	# if char in '[]{},:':
	# 	# 	start = self.currentPos
	# 	# 	self.cursor += 1
	# 	# 	self.addToken(start, _TOKEN_TYPE_FOR_OPERATOR[char])
	# 	# elif char == '"':
	# 	# 	extract_string(self)
	# 	# elif char.isdigit() or char in '+-':
	# 	# 	extract_number(self)
	# 	# elif char.isalpha():
	# 	# 	extract_special(self)
	# 	# else:
	# 	# 	extract_illegal(self)
	# 	#
	# 	# self.consumeWhitespace()
	#
	# 	if len(self.tokens) == 0:
	# 		self.error(EMPTY_STRING_MSG, span=Span())
	#
	# 	return self.tokens, self.errors

	def nextToken(self) -> Optional[Token]:
		self.consumeWhitespace()
		if not self.cursor < self.totalLength:
			return self.addToken2(self.currentPos, b'', TokenType.eof)

		char = self.text[self.cursor]
		if char == ord('"'):
			return self.extract_string()
		elif char in b'[]{},:':
			return self.extract_operator()
		# elif char in '0123456789+-.eE':
		# 	extract_number(self)
		elif char in b'tfn':
			return self.extract_special()
		# elif char == "'":
		# 	extract_string(self)
		else:
			extractor = self._TOKEN_EXTRACTORS_BY_CHAR.get(char, self.extract_illegal)
			return extractor()
		# self.addToken2(self.currentPos, b'', TokenType.eof)
		#
		#
		# if len(self.tokens) == 0:
		# 	self.errorLastToken(EMPTY_STRING_MSG)
		#
		# return self.tokens, self.errors
