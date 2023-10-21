import re
from typing import Optional, final

from cat.utils.collections_ import Stack
from base.model.parsing.bytesUtils import DIGITS, ASCII_LETTERS, JAVA_WHITESPACES, JAVA_WHITESPACES_SINGLE_BYTE, JAVA_WHITESPACES_THREE_BYTES, DIGITS_RANGE
from base.model.utils import Position, Span

Char = bytes
Byte = int


SYNTAX_ESCAPE = '\\'
SYNTAX_DOUBLE_QUOTE = '"'
SYNTAX_SINGLE_QUOTE = '\''


DOT_OR_MINUS = set(b'.-')
QUOTES = set(b'\'"')
UNQUOTED_STRING_CHARS = set(DIGITS + ASCII_LETTERS + b'_-.+')
BOOLEAN_VALUES = {b'true', b'false'}

NOT_JAVA_WHITESPACES_REGEX: bytes = b"(?:" + b'|'.join(JAVA_WHITESPACES) + b")*"


@final
class StringReader:
	def __init__(self, source: bytes, lineStart: int, lineNo: int, cursorOffset: int, fullSource: bytes):
		self._lineStart: int = lineStart
		self._lineNo: int = lineNo
		self.source: bytes = source
		self.totalLength = len(source)
		self.cursor: int = 0
		self.cursorOffset: int = cursorOffset
		self.lastCursors: Stack[int] = Stack()
		self.fullSource: bytes = fullSource

	@property
	def hasReachedEnd(self) -> bool:
		return self.cursor >= self.totalLength

	def posFromColumn(self, cursor: int) -> Position:
		actualCursor = (cursor + self._lineStart) + self.cursorOffset
		return Position(self._lineNo, actualCursor - self._lineStart, actualCursor)
		# return Position(self._lineNo, cursor, self._lineStart + cursor)

	@property
	def currentPos(self) -> Position:
		return self.posFromColumn(self.cursor)

	@property
	def currentSpan(self) -> Span:
		start = self.lastCursors.peek()
		begin = self.posFromColumn(start)
		end = self.posFromColumn(self.cursor)
		return Span(begin, end)

	def save(self) -> None:
		self.lastCursors.push(self.cursor)

	def mergeLastSave(self) -> None:
		""" removes the last save, without resetting the cursor. """
		assert self.lastCursors
		self.lastCursors.pop()

	def acceptLastSave(self) -> None:
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
		source: bytes = self.source
		length: int = self.totalLength
		# beware of unicode utf-8:
		while cursor < length:
			if source[cursor] in JAVA_WHITESPACES_SINGLE_BYTE:
				cursor += 1
			elif cursor + 3 <= length and source[cursor:cursor + 3] in JAVA_WHITESPACES_THREE_BYTES:
				cursor += 3
			else:
				break
		# do not update lastCursor!: self.lastCursors = self.cursor
		if self.cursor != cursor:
			self.cursor = cursor
			return True
		else:
			return False

	# @cy_final
	# def tryConsumeChar(self, char: Char) -> bool:
	# 	if self.cursor < self.totalLength and self.source[self.cursor] == char:
	# 		self.cursor += 1
	# 		return True
	# 	return False

	def tryConsumeByte(self, byte: Byte) -> bool:
		if self.cursor < self.totalLength and self.source[self.cursor] == byte:
			self.cursor += 1
			return True
		return False

	def tryPeek(self) -> Optional[Byte]:
		if self.cursor < self.totalLength:
			return self.source[self.cursor]
		else:
			return None

	def tryReadRemaining(self) -> Optional[bytes]:
		if self.hasReachedEnd:
			return None
		start: int = self.cursor
		self.save()
		self.cursor = self.totalLength
		return self.source[start:]

	def readUntilEndOr(self, sub: bytes, *, includeTerminator: bool = False) -> bytes:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength

		cursor = source.find(sub, cursor)
		if cursor == -1:
			cursor = length
		elif includeTerminator:
			cursor += len(sub)
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	def readUntilEndOrRegex(self, sub: re.Pattern[bytes], *, includeTerminator: bool = False) -> bytes:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength

		findIter = sub.finditer(source, cursor)
		match = next(findIter, None)
		if match is None:
			cursor = length
		elif includeTerminator:
			cursor = match.end()
		else:
			cursor = match.start()

		self.save()
		self.cursor = cursor
		return source[start:cursor]

	def readUntilEndOrWhitespace(self) -> bytes:
		result = self.tryReadRegex(re.compile(NOT_JAVA_WHITESPACES_REGEX))
		assert result is not None
		return result

	def tryReadRegex(self, pattern: re.Pattern[bytes]) -> Optional[bytes]:  # throws CommandSyntaxException
		match = pattern.match(self.source, self.cursor)
		if match is None:
			return None
		text = match.group(0)
		self.save()
		self.cursor += len(text)
		return text

	def tryReadInt(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength

		if cursor < length and source[cursor] == ord('-'):
			cursor += 1
		if cursor < length and source[cursor] in DIGITS_RANGE:
			cursor += 1
		else:
			return None
		while cursor < length and source[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and source[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	def tryReadFloat(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength
		hasHadDot: bool = False

		if cursor < length and source[cursor] == ord('-'):
			cursor += 1

		if cursor < length and source[cursor] == ord('.'):
			hasHadDot = True
			cursor += 1

		if cursor < length and source[cursor] in DIGITS_RANGE:
			cursor += 1
		else:
			return None
		while cursor < length and source[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and source[cursor] == ord('.'):
			cursor += 1
			if hasHadDot:
				return None  # TODO: Lexer Errors
		while cursor < length and source[cursor] in DIGITS_RANGE:
			cursor += 1
		if cursor < length and source[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	def tryReadString(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength
		if cursor >= length:
			return None
		terminator: Byte = source[cursor]
		TERMINATOR_OR_ESCAPE: set[Byte] = {terminator, ord(SYNTAX_ESCAPE)}

		if terminator in QUOTES:  # quoted string
			cursor += 1
			strStreakStart = cursor
			result: bytes = b''
			while cursor < length:
				c: Byte = source[cursor]

				if c == ord(SYNTAX_ESCAPE):
					result += source[strStreakStart:cursor]
					cursor += 1
					if not cursor < length:
						return None
					c2 = source[cursor]
					if c2 in TERMINATOR_OR_ESCAPE:
						strStreakStart = cursor
						cursor += 1
					else:
						return None  # TODO: Lexer Errors
				elif c == terminator:
					result += source[strStreakStart:cursor]
					cursor += 1
					self.save()
					self.cursor = cursor
					return result
				else:
					cursor += 1

			return None  # TODO: Lexer Errors
		else:  # unquoted string
			while cursor < length and source[cursor] in UNQUOTED_STRING_CHARS:
				cursor += 1
			if start == cursor:
				return None
			self.save()
			self.cursor = cursor
			return source[start:cursor]

	# @cy_final
	# def tryReadString(self) -> Optional[bytes]:
	# 	start: int = self.cursor
	# 	cursor: int = self.cursor
	# 	source: bytes = self.source
	# 	length: int = self.totalLength
	# 	if cursor >= length:
	# 		return None
	# 	terminator: Byte = source[cursor]
	# 	TERMINATOR_OR_ESCAPE: set[Byte] = {terminator, ord(SYNTAX_ESCAPE)}
	# 	if terminator in QUOTES:  # quoted string
	# 		cursor += 1
	# 		result: bytes = b''
	# 		escaped: bool = False
	# 		while cursor < length:
	# 			c: Byte = source[cursor]
	# 			cursor += 1
	# 			if escaped:
	# 				if c in TERMINATOR_OR_ESCAPE:
	# 					result += c
	# 					escaped = False
	# 				else:
	# 					return None  # TODO: Lexer Errors
	# 			elif c == ord(SYNTAX_ESCAPE):
	# 				escaped = True
	# 			elif c == terminator:
	# 				self.save()
	# 				self.cursor = cursor
	# 				return result
	# 			else:
	# 				result += c
	# 		return None  # TODO: Lexer Errors
	# 	else: # unquoted string
	# 		while cursor < length and source[cursor] in UNQUOTED_STRING_CHARS:
	# 			cursor += 1
	# 		if start == cursor:
	# 			return None
	# 		self.save()
	# 		self.cursor = cursor
	# 		return source[start:cursor]

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
		source: bytes = self.source
		length: int = self.totalLength
		if cursor >= length or source[cursor] == ord(' '):
			return None
		while cursor < length and source[cursor] != ord(' '):
			cursor += 1
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	# @cy_final
	# def tryReadEntityLocator(self) -> Optional[str]:
	# 	# Must be a player name, a target selector or a UUID.
	# 	start: int = self.cursor
	# 	cursor: int = self.cursor
	# 	source: str = self.source
	# 	length: int = self.totalLength
	#
	# 	string = self.tryReadString()
	# 	if string is None:
	# 		# tryParse Target selector:
	# 		if cursor + 1 < length and source[cursor:cursor + 2] in {'@p', '@r', '@a', '@e', '@s'}:
	# 			cursor += 2
	# 			if cursor < length and source[cursor] == '[':  # No spaces before '['!!
	# 				cursor2: int = source.find(']', cursor + 1)
	# 				if cursor2 != -1:
	# 					cursor = cursor2 + 1
	# 			self.save()
	# 			self.cursor = cursor
	# 			return source[start:cursor]
	# 		else:
	# 			return None
	# 	else:
	# 		return string

	def readResourceLocation(self, *, allowTag: bool = False) -> bytes:
		# The namespace and the path of a resource location should only contain the following symbols:
		#     0123456789 Numbers
		#     abcdefghijklmnopqrstuvwxyz Lowercase letters
		#     _ Underscore
		#     - Hyphen/minus
		#     . Dot
		# The following characters are illegal in the namespace, but acceptable in the path:
		#     / Forward slash (directory separator)
		# The preferred naming convention for either namespace or path is snake_case.
		pattern = rb'(?:[0-9a-zA-Z._-]+:)?[0-9a-zA-Z._/-]*'
		if allowTag:
			pattern = b'#?' + pattern
		literal = self.tryReadRegex(re.compile(pattern))
		return literal

	def tryReadTildeNotation(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength
		if cursor < length and source[cursor] == ord('~'):
			cursor += 1
			self.save()
			self.cursor = cursor
			if self.tryReadFloat() is not None:
				self.mergeLastSave()
			return source[start:self.cursor]
			# if cursor == length or source[cursor] == ' ':
			# 	return source[start:self.cursor]
			# else:
			# 	self.rollback()
			# 	return None
		else:
			return None

	def tryReadCaretNotation(self) -> Optional[bytes]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: bytes = self.source
		length: int = self.totalLength
		if cursor < length and source[cursor] == ord('^'):
			cursor += 1
			self.save()
			self.cursor = cursor
			if self.tryReadFloat() is not None:
				self.mergeLastSave()
			return source[start:self.cursor]
			# if cursor == length or source[cursor] == ' ':
			# 	return source[start:self.cursor]
			# else:
			# 	self.rollback()
			# 	return None
		else:
			return None


__all__ = [
	'StringReader'
]
