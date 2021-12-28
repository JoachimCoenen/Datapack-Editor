from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Iterator

from model.utils import Position, Span


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


STRING_OR_NUMBER_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+-"
NUMBER_PAT = re.compile(r"[+-]?(?:[0-9]*?\.[0-9]+|[0-9]+\.[0-9]*?|[1-9][0-9]*|0)([eE][+-]?[0-9]+)?[bslfdBSLFD]?(?![a-zA-Z0-9._+-])")
STRING_PAT = re.compile(r"[a-zA-Z0-9._+-]+")


class SNBTTokenizer:
	def __init__(self, source: str, ignoreTrailingChars: bool = False):
		self._source: str = source
		self._ignoreTrailingChars: bool = ignoreTrailingChars

		self._length: int = len(source)
		self._index: int = 0
		self._line: int = 0
		self._lineStart: int = 0

		self._tokenStart = self._position

	@property
	def _position(self) -> Position:
		return Position(self._line, self._index - self._lineStart, self._index)

	@property
	def _tokenSpan(self) -> Span:
		return Span(self._tokenStart, self._position)

	def _consumeWhitespace(self) -> None:
		src = self._source
		length = self._length
		i = self._index
		while i < length and src[i].isspace():
			if src[i] == '\n':
				self._line += 1
				self._lineStart = i + 1
			i += 1
		self._index = i

	def handleQuotedString(self) -> Optional[Token]:
		src = self._source
		i = self._index
		length = self._length

		quote = src[i]

		i += 1
		while i < length:
			i2 = src.find(quote, i)
			if i2 == -1:
				i = self._length
				self._index = i
				return Token(TokenType.Invalid, self._tokenSpan)
			else:
				# is it an escaped quote?:
				i3: int = i2 - 1
				while i3 >= i and src[i3] == '\\':
					i3 -= 1
				escapesCnt = i2 - i3 - 1

				i = i2 + 1
				if escapesCnt % 2 == 1:
					continue  # it's escaped
				else:  # it's not escaped!
					self._index = i
					return Token(TokenType.QuotedString, self._tokenSpan)
		# string isn't closed:
		self._index = i
		return Token(TokenType.Invalid, self._tokenSpan)

	def handleNumberOrString(self) -> Optional[Token]:
		numberMatch = NUMBER_PAT.match(self._source, self._index)
		if numberMatch is not None:
			self._index = numberMatch.end()
			return Token(TokenType.Number, self._tokenSpan)
		stringMatch = STRING_PAT.match(self._source, self._index)
		if stringMatch is not None:
			self._index = stringMatch.end()
			return Token(TokenType.String, self._tokenSpan)
		else:
			self._index += 1
			return Token(TokenType.Invalid, self._tokenSpan)

	def handleCompound(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.Compound, self._tokenSpan)

	def handleCloseCompound(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.CloseCompound, self._tokenSpan)

	_tokenTypeByPrefix: dict[str, TokenType] = {
		'B': TokenType.ByteArray,
		'I': TokenType.IntArray,
		'L': TokenType.LongArray,
	}

	def handleArrayOrList(self) -> Optional[Token]:
		self._index += 1
		if self._index >= self._length:
			# List:
			return Token(TokenType.List, self._tokenSpan)
		c = self._source[self._index]

		# Array:
		if (tokenType := self._tokenTypeByPrefix.get(c)) is not None:
			self._index += 1
			if self._index < self._length:
				c2 = self._source[self._index]
				if c2 == ';':
					self._index += 1
					return Token(tokenType, self._tokenSpan)
			self._index -= 1
		# List:
		return Token(TokenType.List, self._tokenSpan)

	def handleCloseList(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.CloseList, self._tokenSpan)

	def handleColon(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.Colon, self._tokenSpan)

	def handleComma(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.Comma, self._tokenSpan)

	def handleInvalid(self) -> Optional[Token]:
		self._index += 1
		return Token(TokenType.Invalid, self._tokenSpan)

	_tokenHandlers_1: dict[str, Callable[[SNBTTokenizer], Token]] = {
		'"': handleQuotedString,
		"'": handleQuotedString,
		**{
			c: lambda s: SNBTTokenizer.handleNumberOrString(s)
			for c in STRING_OR_NUMBER_CHARS
		},
		'{': handleCompound,
		'}': handleCloseCompound,
		'[': handleArrayOrList,
		']': handleCloseList,
		# ';': handleColon,
		':': handleColon,
		',': handleComma,
	}

	def nextToken(self) -> Optional[Token]:
		self._consumeWhitespace()
		self._tokenStart = self._position
		if self._index >= self._length:
			return None

		c = self._source[self._index]
		handler = self._tokenHandlers_1.get(c, lambda s: s.handleInvalid())
		return handler(self)

	def __iter__(self) -> Iterator[Token]:
		while (tk := self.nextToken()) is not None:
			yield tk


__all__ = [
	'TokenType',
	'Token',
	'SNBTTokenizer',
]
