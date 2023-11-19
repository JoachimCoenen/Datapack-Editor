from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, ClassVar

from base.model.parsing.bytesUtils import WHITESPACE_CHARS
from base.model.parsing.parser import TokenizerBase
from base.model.utils import Position, Span


class TokenType(Enum):
	Invalid = 0
	QuotedString = 1
	Number = 2
	String = 3
	Compound = 4
	CloseCompound = 5
	ByteArray = 6
	IntArray = 7
	LongArray = 8
	List = 9
	CloseList = 10
	Colon = 11
	Comma = 12


@dataclass
class Token:
	type: TokenType
	span: Span
	startEnd: tuple[int, int]


STRING_OR_NUMBER_CHARS = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+-"
NUMBER_PAT = re.compile(rb"[+-]?(?:[0-9]*?\.[0-9]+|[0-9]+\.[0-9]*?|[1-9][0-9]*|0)([eE][+-]?[0-9]+)?[bslfdBSLFD]?(?![a-zA-Z0-9._+-])")
STRING_PAT = re.compile(rb"[a-zA-Z0-9._+-]+")


_TOKEN_TYPE_BY_PREFIX: dict[int, TokenType] = {
	ord('B'): TokenType.ByteArray,
	ord('I'): TokenType.IntArray,
	ord('L'): TokenType.LongArray,
}


@dataclass
class SNBTTokenizer(TokenizerBase[Token]):
	ignoreTrailingChars: bool
	_tokenStart: tuple[Position, int] = field(init=False)

	lastCursor: int = field(default=-1, init=False)
	lastLine: int = field(default=-1, init=False)
	lastLineStart: int = field(default=-1, init=False)

	@property
	def _tokenSpan(self) -> Span:
		return Span(self._tokenStart[0], self.currentPos)

	@property
	def _tokenStartEnd(self) -> tuple[int, int]:
		return self._tokenStart[1], self.cursor

	def _consumeWhitespace(self) -> None:
		src = self.text
		length = self.length
		i = self.cursor
		while i < length and src[i] in WHITESPACE_CHARS:
			if src[i] == ord('\n'):
				self.cursor = i + 1  # needed for self.advanceLine()
				self.advanceLine()
			i += 1
		self.cursor = i

	def handleQuotedString(self) -> Optional[Token]:
		src = self.text
		i = self.cursor
		length = self.length

		quote = src[i]

		i += 1
		while i < length:
			i2 = src.find(quote, i)
			if i2 == -1:
				i = self.length
				self.cursor = i
				return Token(TokenType.Invalid, self._tokenSpan, self._tokenStartEnd)
			else:
				# is it an escaped quote?:
				i3: int = i2 - 1
				while i3 >= i and src[i3] == ord('\\'):
					i3 -= 1
				escapesCnt = i2 - i3 - 1

				i = i2 + 1
				if escapesCnt % 2 == 1:
					continue  # it's escaped
				else:  # it's not escaped!
					self.cursor = i
					return Token(TokenType.QuotedString, self._tokenSpan, self._tokenStartEnd)
		# string isn't closed:
		self.cursor = i
		return Token(TokenType.Invalid, self._tokenSpan, self._tokenStartEnd)

	def handleNumberOrString(self) -> Optional[Token]:
		numberMatch = NUMBER_PAT.match(self.text, self.cursor)
		if numberMatch is not None:
			self.cursor = numberMatch.end()
			return Token(TokenType.Number, self._tokenSpan, self._tokenStartEnd)
		stringMatch = STRING_PAT.match(self.text, self.cursor)
		if stringMatch is not None:
			self.cursor = stringMatch.end()
			return Token(TokenType.String, self._tokenSpan, self._tokenStartEnd)
		else:
			self.cursor += 1
			return Token(TokenType.Invalid, self._tokenSpan, self._tokenStartEnd)

	def handleCompound(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.Compound, self._tokenSpan, self._tokenStartEnd)

	def handleCloseCompound(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.CloseCompound, self._tokenSpan, self._tokenStartEnd)

	def handleArrayOrList(self) -> Optional[Token]:
		self.cursor += 1
		if self.cursor >= self.length:
			# List:
			return Token(TokenType.List, self._tokenSpan, self._tokenStartEnd)
		c = self.text[self.cursor]

		# Array:
		if (tokenType := _TOKEN_TYPE_BY_PREFIX.get(c)) is not None:
			self.cursor += 1
			if self.cursor < self.length:
				c2 = self.text[self.cursor]
				if c2 == ord(';'):
					self.cursor += 1
					return Token(tokenType, self._tokenSpan, self._tokenStartEnd)
			self.cursor -= 1
		# List:
		return Token(TokenType.List, self._tokenSpan, self._tokenStartEnd)

	def handleCloseList(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.CloseList, self._tokenSpan, self._tokenStartEnd)

	def handleColon(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.Colon, self._tokenSpan, self._tokenStartEnd)

	def handleComma(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.Comma, self._tokenSpan, self._tokenStartEnd)

	def handleInvalid(self) -> Optional[Token]:
		self.cursor += 1
		return Token(TokenType.Invalid, self._tokenSpan, self._tokenStartEnd)

	_TOKEN_HANDLERS_1: ClassVar[dict[int, Callable[[SNBTTokenizer], Token]]] = {
		ord('"'): handleQuotedString,
		ord("'"): handleQuotedString,
		**{
			c: lambda s: SNBTTokenizer.handleNumberOrString(s)
			for c in STRING_OR_NUMBER_CHARS
		},
		ord('{'): handleCompound,
		ord('}'): handleCloseCompound,
		ord('['): handleArrayOrList,
		ord(']'): handleCloseList,
		# ';': handleColon,
		ord(':'): handleColon,
		ord(','): handleComma,
	}

	def nextToken(self) -> Optional[Token]:
		self.lastCursor = self.cursor
		self.lastLine = self.line
		self.lastLineStart = self.lineStart
		self._consumeWhitespace()
		self._tokenStart = self.currentPos, self.cursor
		if self.cursor >= self.length:
			self.cursor = self.lastCursor
			self.line = self.lastLine
			self.lineStart = self.lastLineStart
			return None

		c = self.text[self.cursor]
		handler = self._TOKEN_HANDLERS_1.get(c, lambda s: s.handleInvalid())
		return handler(self)


__all__ = [
	'TokenType',
	'Token',
	'SNBTTokenizer',
]
