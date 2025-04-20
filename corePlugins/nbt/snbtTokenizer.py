from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, ClassVar

from base.model.parsing.bytesConstants import ASCII_LETTERS_SET
from base.model.parsing.parser import TokenizerBase
from base.model.utils import Position, Span
from corePlugins.nbtJsonBase.core import Token, TokenType

STRING_OR_NUMBER_CHARS = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+-"
NUMBER_PAT = re.compile(rb"[+-]?(?:[0-9]*?\.[0-9]+|[0-9]+\.[0-9]*?|[1-9][0-9]*|0)([eE][+-]?[0-9]+)?[bslfdBSLFD]?(?![a-zA-Z0-9._+-])")
STRING_PAT = re.compile(rb"[a-zA-Z0-9._+-]+")


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
	def _tokenValue(self) -> bytes:
		return self.text[self._tokenStart[1]:self.cursor]

	def handleQuotedString(self) -> Token:
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
				return Token(TokenType.invalid, self._tokenSpan, self._tokenValue)
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
					return Token(TokenType.quoted_string, self._tokenSpan, self._tokenValue)
		# string isn't closed:
		self.cursor = i
		return Token(TokenType.invalid, self._tokenSpan, self._tokenValue)

	def handleNumberOrString(self) -> Token | None:
		numberMatch = NUMBER_PAT.match(self.text, self.cursor)
		if numberMatch is not None:
			self.cursor = numberMatch.end()
			return Token(TokenType.number, self._tokenSpan, self._tokenValue)
		stringMatch = STRING_PAT.match(self.text, self.cursor)
		if stringMatch is not None:
			self.cursor = stringMatch.end()
			return Token(TokenType.unquoted_string, self._tokenSpan, self._tokenValue)
		else:
			self.cursor += 1
			return Token(TokenType.invalid, self._tokenSpan, self._tokenValue)

	def handleCompound(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.object_start, self._tokenSpan, self._tokenValue)

	def handleCloseCompound(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.object_end, self._tokenSpan, self._tokenValue)

	def handleArrayOrList(self) -> Token | None:
		self.cursor += 1
		if self.cursor >= self.length:
			# List:
			return Token(TokenType.list_start, self._tokenSpan, self._tokenValue)
		c = self.text[self.cursor]

		# Array:
		if c in ASCII_LETTERS_SET:
			self.cursor += 1
			if self.cursor < self.length:
				c2 = self.text[self.cursor]
				if c2 == ord(';'):
					self.cursor += 1
					return Token(TokenType.array_start, self._tokenSpan, self._tokenValue)
			self.cursor -= 1
		# List:
		return Token(TokenType.list_start, self._tokenSpan, self._tokenValue)

	def handleCloseList(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.list_end, self._tokenSpan, self._tokenValue)

	def handleColon(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.colon, self._tokenSpan, self._tokenValue)

	def handleComma(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.comma, self._tokenSpan, self._tokenValue)

	def handleInvalid(self) -> Token | None:
		self.cursor += 1
		return Token(TokenType.invalid, self._tokenSpan, self._tokenValue)

	_TOKEN_HANDLERS_1: ClassVar[dict[int, Callable[[SNBTTokenizer], Token | None]]] = {
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

	def nextToken(self) -> Token:
		self.lastCursor = self.cursor
		self.lastLine = self.line
		self.lastLineStart = self.lineStart
		self.consumeWhitespace()
		self._tokenStart = self.currentPos, self.cursor
		if self.cursor >= self.length:
			# self.cursor = self.lastCursor
			# self.line = self.lastLine
			# self.lineStart = self.lastLineStart
			return Token(TokenType.eof, Span(self.currentPos), self._tokenValue)

		c = self.text[self.cursor]
		handler = self._TOKEN_HANDLERS_1.get(c, lambda s: s.handleInvalid())
		return handler(self)


__all__ = [
	'SNBTTokenizer',
]
