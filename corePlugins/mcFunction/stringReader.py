import re
from dataclasses import dataclass, field
from typing import Optional, final

from base.model.parsing.parser import _Base
from cat.utils.collections_ import Stack
from base.model.parsing.bytesUtils import DIGITS, ASCII_LETTERS, JAVA_WHITESPACES, JAVA_WHITESPACES_SINGLE_BYTE, JAVA_WHITESPACES_THREE_BYTES, DIGITS_RANGE, ORD_BACKSLASH, \
	ORD_DOT, ORD_MINUS, ORD_ROOF, ORD_SPACE, ORD_TILDE
from base.model.utils import Position, Span

Char = bytes
Byte = int


DOT_OR_MINUS = set(b'.-')
QUOTES = set(b'\'"')
UNQUOTED_STRING_CHARS = set(DIGITS + ASCII_LETTERS + b'_-.+')
BOOLEAN_VALUES = {b'true', b'false'}

NOT_JAVA_WHITESPACES_REGEX: bytes = b"(?:" + b'|'.join(JAVA_WHITESPACES) + b")*"


@final
@dataclass
class StringReader(_Base):
	fullSource: bytes
	lastCursors: Stack[int] = field(default_factory=Stack, init=False)

	@property
	def hasReachedEnd(self) -> bool:
		return self.cursor >= self.length

	def posFromColumn(self, cursor: int) -> Position:
		# ugh. Definitely not threadsafe, but it gets the job done.
		currentCursor = self.cursor
		self.cursor = cursor
		pos = self.currentPos
		self.cursor = currentCursor
		return pos

	@property
	def currentSpan(self) -> Span:
		start = self.lastCursors.peek()
		begin = self.posFromColumn(start)
		end = self.currentPos
		return Span(begin, end)

	def save(self) -> None:
		self.lastCursors.push(self.cursor)

	def mergeLastSave(self) -> None:
		""" removes the last save, without resetting the cursor. """
		assert self.lastCursors
		self.lastCursors.pop()

	def rollback(self) -> None:
		assert self.lastCursors
		self.cursor = self.lastCursors.pop()

	def skip(self) -> None:
		self.cursor += 1

	def skipN(self, n: int) -> None:
		self.cursor += n

	def tryConsumeWhitespace(self) -> bool:
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		# beware of unicode utf-8:
		while cursor < length:
			if text[cursor] in JAVA_WHITESPACES_SINGLE_BYTE:
				cursor += 1
			elif cursor + 3 <= length and text[cursor:cursor + 3] in JAVA_WHITESPACES_THREE_BYTES:
				cursor += 3
			else:
				break
		# do not update lastCursor!: self.lastCursors = self.cursor
		if self.cursor != cursor:
			self.cursor = cursor
			return True
		else:
			return False

	def tryConsumeByte(self, byte: Byte) -> bool:
		if self.cursor < self.length and self.text[self.cursor] == byte:
			self.cursor += 1
			return True
		return False

	def tryPeek(self) -> Optional[Byte]:
		if self.cursor < self.length:
			return self.text[self.cursor]
		else:
			return None

	def tryReadRemaining(self) -> Optional[bytes]:
		if self.hasReachedEnd:
			return None
		start: int = self.cursor
		self.save()
		self.cursor = self.length
		return self.text[start:]

	def readUntilEndOr(self, sub: bytes, *, includeTerminator: bool = False) -> bytes:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length

		cursor = text.find(sub, cursor)
		if cursor == -1:
			cursor = length
		elif includeTerminator:
			cursor += len(sub)
		self.save()
		self.cursor = cursor
		return text[start:cursor]

	def readUntilEndOrRegex(self, sub: re.Pattern[bytes], *, includeTerminator: bool = False) -> bytes:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length

		findIter = sub.finditer(text, cursor)
		match = next(findIter, None)
		if match is None:
			cursor = length
		elif includeTerminator:
			cursor = match.end()
		else:
			cursor = match.start()

		self.save()
		self.cursor = cursor
		return text[start:cursor]

	def readUntilEndOrWhitespace(self) -> bytes:
		result = self.tryReadRegex(re.compile(NOT_JAVA_WHITESPACES_REGEX))
		assert result is not None
		return result

	def tryReadRegex(self, pattern: re.Pattern[bytes]) -> Optional[bytes]:  # throws CommandSyntaxException
		match = pattern.match(self.text, self.cursor)
		if match is None:
			return None
		text = match.group(0)
		self.save()
		self.cursor += len(text)
		return text

	def tryReadRegexGroups(self, pattern: re.Pattern[bytes]) -> Optional[tuple[bytes, ...]]:  # throws CommandSyntaxException
		match = pattern.match(self.text, self.cursor)
		if match is None:
			return None
		self.save()
		self.cursor += len(match.group(0))
		return match.groups()

	def tryReadInt(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length

		if cursor < length and text[cursor] == ORD_MINUS:
			cursor += 1
		if cursor < length and text[cursor] in DIGITS_RANGE:
			cursor += 1
		else:
			return None
		while cursor < length and text[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and text[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return text[start:cursor]

	def tryReadFloat(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		hasHadDot: bool = False

		if cursor < length and text[cursor] == ORD_MINUS:
			cursor += 1

		if cursor < length and text[cursor] == ORD_DOT:
			hasHadDot = True
			cursor += 1

		if cursor < length and text[cursor] in DIGITS_RANGE:
			cursor += 1
		else:
			return None
		while cursor < length and text[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and text[cursor] == ORD_DOT:
			cursor += 1
			if hasHadDot:
				return None  # TODO: Lexer Errors
		while cursor < length and text[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and text[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return text[start:cursor]

	def tryReadString(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		if cursor >= length:
			return None
		terminator: Byte = text[cursor]
		TERMINATOR_OR_ESCAPE: set[Byte] = {terminator, ORD_BACKSLASH}

		if terminator in QUOTES:  # quoted string
			cursor += 1
			strStreakStart = cursor
			result: bytes = b''
			while cursor < length:
				c: Byte = text[cursor]

				if c == ORD_BACKSLASH:
					result += text[strStreakStart:cursor]
					cursor += 1
					if not cursor < length:
						return None
					c2 = text[cursor]
					if c2 in TERMINATOR_OR_ESCAPE:
						strStreakStart = cursor
						cursor += 1
					else:
						return None  # TODO: Lexer Errors
				elif c == terminator:
					result += text[strStreakStart:cursor]
					cursor += 1
					self.save()
					self.cursor = cursor
					return result
				else:
					cursor += 1

			return None  # TODO: Lexer Errors
		else:  # unquoted string
			while cursor < length and text[cursor] in UNQUOTED_STRING_CHARS:
				cursor += 1
			if start == cursor:
				return None
			self.save()
			self.cursor = cursor
			return text[start:cursor]

	def tryReadBoolean(self) -> Optional[bytes]:  # throws CommandSyntaxException
		value: Optional[bytes] = self.tryReadString()
		if not value:
			return None  # TODO: Lexer Errors
		if value in BOOLEAN_VALUES:
			return value
		else:
			self.rollback()
			return None  # TODO: Lexer Errors

	def tryReadLiteral(self) -> Optional[bytes]:  # throws CommandSyntaxException
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		if cursor >= length or text[cursor] == ORD_SPACE:
			return None
		while cursor < length and text[cursor] != ORD_SPACE:
			cursor += 1
		self.save()
		self.cursor = cursor
		return text[start:cursor]

	def tryReadTildeNotation(self) -> Optional[bytes]:
		return self._tryReadNotation(ORD_TILDE)

	def tryReadCaretNotation(self) -> Optional[bytes]:
		return self._tryReadNotation(ORD_ROOF)

	def _tryReadNotation(self, notation: int) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		if cursor < length and text[cursor] == notation:
			cursor += 1
			self.save()
			self.cursor = cursor
			if self.tryReadFloat() is not None:
				self.mergeLastSave()
			return text[start:self.cursor]
			# if cursor == length or text[cursor] == ' ':
			# 	return text[start:self.cursor]
			# else:
			# 	self.rollback()
			# 	return None
		else:
			return None

	def tryReadNotation2(self, notation: bytes) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		text: bytes = self.text
		length: int = self.length
		if cursor < length and text[cursor] in notation:
			cursor += 1
			self.cursor = cursor
			if self.tryReadFloat() is not None:
				self.mergeLastSave()
			return text[start:self.cursor]
		else:
			return None


__all__ = [
	'StringReader'
]
