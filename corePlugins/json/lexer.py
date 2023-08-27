"""Lexer functions, loosely based on www.github.com/tusharsadhwani/json_parser"""
from dataclasses import dataclass, field
from typing import Optional, Callable

from Cat.utils import CachedProperty
from base.model.parsing.bytesUtils import CR_LF, DIGITS_RANGE, WHITESPACE, ASCII_LOWERCASE_RANGE, ASCII_UPPERCASE_RANGE, bytesToStr, ASCII_LETTERS, WHITESPACE_NO_LF
from .core import TokenType, Token
from base.model.parsing.parser import TokenizerBase
from base.model.utils import Span, Position, Message

INCOMPLETE_ESCAPE_MSG = Message("Incomplete escape at end of string", 0)
SINGLE_QUOTED_STRING_MSG = Message("JSON standard does not allow single quoted strings", 0)
EXPECTED_END_OF_STRING_MSG = Message("Expected end of string", 0)
MISSING_CLOSING_QUOTE_MSG = Message("Missing closing quote", 0)
INVALID_NUMBER_MSG = Message("Invalid number `{0}`", 1)
UNKNOWN_LITERAL_MSG = Message("Unknown literal `{0}`", 1)
ILLEGAL_CHARS_MSG = Message("Illegal characters `{0}`", 1)
EMPTY_STRING_MSG = Message("Cannot parse empty string", 0)


Char = int


_TOKEN_TYPE_FOR_SPECIAL = {
	b'true': TokenType.boolean,
	b'false': TokenType.boolean,
	b'null': TokenType.null,
}

_TOKEN_TYPE_FOR_OPERATOR = {
	b'[': TokenType.left_bracket,
	b']': TokenType.right_bracket,
	b'{': TokenType.left_brace,
	b'}': TokenType.right_brace,
	b',': TokenType.comma,
	b':': TokenType.colon,
}


@dataclass
class JsonTokenizer(TokenizerBase[Token]):
	allowMultilineStr: bool
	_errorsNextToken: list[tuple[Message, tuple, str]] = field(default_factory=list, init=False)

	def __post_init__(self):
		super(JsonTokenizer, self).__post_init__()

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
				self.errorMsg(msg, *args, span=token.span, style=style)
			self._errorsNextToken.clear()
		return token

	def addToken2(self, start: Position, value: bytes, tokenType: TokenType) -> Token:
		end = self.currentPos
		span = Span(start, end)
		token = Token(value, tokenType, span)
		# add errors:
		if self._errorsNextToken:
			for msg, args, style in self._errorsNextToken:
				self.errorMsg(msg, *args, span=token.span, style=style)
			self._errorsNextToken.clear()
		return token

	def errorNextToken(self, msg: Message, *args, style: str = 'error') -> None:
		self._errorsNextToken.append((msg, args, style))

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
		self.cursor += 1  # opening "

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
		"""Extracts a single number token (e.g. 42, -12.3) from JSON string"""
		start = self.currentPos

		non_exp_digit_found = False
		decimal_point_found = False
		exponent_found = False
		exponent_digit_found = False
		isValid = True

		if self.cursor < self.totalLength and self.text[self.cursor] in b'-+':
			self.cursor += 1

		while self.cursor < self.totalLength:
			char = self.text[self.cursor]
			self.cursor += 1

			if char in DIGITS_RANGE:
				non_exp_digit_found = True
			elif char == 46:  # 46 == ord('.')!
				isValid = isValid and not decimal_point_found
				decimal_point_found = True
			elif char in b'eE':
				exponent_found = True
				break
			elif char in b',' + WHITESPACE + b'}]"\':=[{\\':
				self.cursor -= 1
				break
			else:  # includes b'+-'
				isValid = False

		if exponent_found:
			if self.cursor < self.totalLength and self.text[self.cursor] in b'-+':
				self.cursor += 1

			while self.cursor < self.totalLength:
				char = self.text[self.cursor]
				self.cursor += 1
				if char in DIGITS_RANGE:
					exponent_digit_found = True
				elif char in b',' + WHITESPACE + b'}]"\':=[{\\':
					self.cursor -= 1
					break
				else:  # includes b'.+-eE'
					isValid = False

		isValid = isValid and non_exp_digit_found
		isValid = isValid and (not exponent_found or exponent_digit_found)

		token = self.addToken(start, TokenType.number)
		if not isValid:
			self.errorMsg(INVALID_NUMBER_MSG, token.value, span=token.span)
		return token

	def extract_special(self) -> Token:
		"""Extracts true, false and null from JSON string"""
		start = self.currentPos
		self.cursor += 1  # first letter
		while self.cursor < self.totalLength and (self.text[self.cursor] in ASCII_LOWERCASE_RANGE or self.text[self.cursor] in ASCII_UPPERCASE_RANGE):
			self.cursor += 1

		word = self.text[start.index - self.cursorOffset:self.cursor]
		tkType = _TOKEN_TYPE_FOR_SPECIAL.get(word, TokenType.invalid)
		if tkType is TokenType.invalid:
			if self.cursor < self.totalLength and self.text[self.cursor] == ord(b'"'):
				self.cursor += 1
				word += self.text[self.cursor:self.cursor + 1]
		token = self.addToken2(start, word, tkType)
		if token.type is TokenType.invalid:
			self.errorMsg(UNKNOWN_LITERAL_MSG, bytesToStr(token.value), span=token.span)
		return token

	def extract_illegal(self) -> Token:
		"""Extracts illegal characters from JSON string"""
		start = self.currentPos
		self.cursor += 1  # first character
		while self.cursor < self.totalLength:
			char = self.text[self.cursor]
			if char in DIGITS_RANGE or char in ASCII_LOWERCASE_RANGE or char in ASCII_UPPERCASE_RANGE:
				break
			if char in WHITESPACE:
				break
			if char in b'[]{},:+-.':
				break
			self.cursor += 1

		token = self.addToken(start, TokenType.invalid)
		if token.type is TokenType.invalid:
			self.errorMsg(ILLEGAL_CHARS_MSG, repr(bytesToStr(token.value)), span=token.span)
		return token

	def extract_operator(self) -> Token:
		start = self.currentPos
		char = self.text[self.cursor:self.cursor+1]
		self.cursor += 1
		return self.addToken2(start, char, _TOKEN_TYPE_FOR_OPERATOR[char])

	@CachedProperty
	def _TOKEN_EXTRACTORS_BY_CHAR(self) -> dict[str, Callable[[], Token]]:
		return {
			**{c: self.extract_string for c in b'"\''},
			**{c: self.extract_special for c in ASCII_LETTERS},  # 'e' & 'E' will be replaced again with 'e': extract_number,
			**{c: self.extract_number for c in b'0123456789+-.eE'},
		}

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


__all__ = [
	'JsonTokenizer',
]
