import re
from typing import Optional, TYPE_CHECKING, final

from Cython import final as cy_final

from Cat.utils.collections import Stack
from model.parsingUtils import Position, Span

if TYPE_CHECKING:
	def cy_final(x): x

Char = str


SYNTAX_ESCAPE = '\\'
SYNTAX_DOUBLE_QUOTE = '"'
SYNTAX_SINGLE_QUOTE = '\''


# A character is a Java whitespace character if and only if it satisfies one of the following criteria:
JAVA_WHITESPACES = {
# It is a Unicode space character (SPACE_SEPARATOR, LINE_SEPARATOR, or PARAGRAPH_SEPARATOR) but is not also a non-breaking space ('\u00A0', '\u2007', '\u202F'):
# SPACE_SEPARATORs:
	'\u0020',  # Space
	# '\u00A0', (excluded) # No-Break Space
	'\u1680',  # Ogham Space Mark
	'\u2000',  # En Quad
	'\u2001',  # Em Quad
	'\u2002',  # En Space
	'\u2003',  # Em Space
	'\u2004',  # Three-Per-Em Space
	'\u2005',  # Four-Per-Em Space
	'\u2006',  # Six-Per-Em Space
	# '\u2007', (excluded)  # Figure Space
	'\u2008',  # Punctuation Space
	'\u2009',  # Thin Space
	'\u200A',  # Hair Space
	# '\u202F',  (excluded) # Narrow No-Break Space
	'\u205F',  # Medium Mathematical Space
	'\u3000',  # Ideographic Space
# LINE_SEPARATORs:
	'\u2028',  # Line Separator
# PARAGRAPH_SEPARATORs:
	'\u2029',  # Paragraph Separator
# Explicitly named Characters:
	'\t',      # It is '\t', U+0009 HORIZONTAL TABULATION.
	'\n',      # It is '\n', U+000A LINE FEED.
	'\u000B',  # It is '\u000B', U+000B VERTICAL TABULATION.
	'\f',      # It is '\f', U+000C FORM FEED.
	'\r',      # It is '\r', U+000D CARRIAGE RETURN.
	'\u001C',  # It is '\u001C', U+001C FILE SEPARATOR.
	'\u001D',  # It is '\u001D', U+001D GROUP SEPARATOR.
	'\u001E',  # It is '\u001E', U+001E RECORD SEPARATOR.
	'\u001F',  # It is '\u001F', U+001F UNIT SEPARATOR.
}
DIGITS = set('0123456789')
DOT_OR_MINUS = set('.-')
QUOTES = set('\'"')
UNQUOTED_STRING_CHARS = set('0123456789' + 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '_-.+')
BOOLEAN_VALUES = {'true', 'false'}

NOT_JAVA_WHITESPACES_REGEX = f"[^{''.join(JAVA_WHITESPACES)}]"


@final
class StringReader:
	def __init__(self, source: str, lineStart: int, lineNo: int, fullSource: str):
		self._lineStart: int = lineStart
		self._lineNo: int = lineNo
		self.source: str = source
		self.totalLength = len(source)
		self.cursor: int = 0
		self.lastCursors: Stack[int] = Stack()
		self.fullSource: str = fullSource

	@property
	@cy_final
	def hasReachedEnd(self) -> bool:
		return self.cursor >= self.totalLength

	@cy_final
	def posFromColumn(self, cursor: int) -> Position:
		return Position.create(line=self._lineNo, column=cursor, index=self._lineStart + cursor)

	@property
	@cy_final
	def currentPos(self) -> Position:
		return self.posFromColumn(self.cursor)

	@property
	@cy_final
	def currentSpan(self) -> Span:
		start = self.lastCursors.peek()
		begin = self.posFromColumn(start)
		end = self.posFromColumn(self.cursor)
		return Span(begin, end)

	@cy_final
	def save(self) -> None:
		self.lastCursors.push(self.cursor)

	@cy_final
	def mergeLastSave(self) -> None:
		""" removes the last save, without resetting the cursor. """
		assert self.lastCursors
		self.lastCursors.pop()

	@cy_final
	def acceptLastSave(self) -> None:
		""" removes the last save, without resetting the cursor. """
		assert self.lastCursors
		self.lastCursors.pop()

	@cy_final
	def rollback(self) -> None:
		assert self.lastCursors
		self.cursor = self.lastCursors.pop()

	@cy_final
	def skip(self) -> None:
		self.cursor += 1

	@cy_final
	def skipN(self, n: int) -> None:
		self.cursor += n

	@cy_final
	def tryConsumeWhitespace(self) -> bool:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		while cursor < length and source[cursor] in JAVA_WHITESPACES:
			cursor += 1
		# do not update lastCursor!: self.lastCursors = self.cursor
		if self.cursor != cursor:
			self.cursor = cursor
			return True
		else:
			return False

	def tryConsumeChar(self, char: Char) -> bool:
		if self.cursor < self.totalLength and self.source[self.cursor] == char:
			self.cursor += 1
			return True
		return False

	@cy_final
	def tryReadRemaining(self) -> Optional[str]:
		if self.hasReachedEnd:
			return None
		start: int = self.cursor
		self.save()
		self.cursor = self.totalLength
		return self.source[start:]

	@cy_final
	def readUntilEndOr(self, sub: str, *, includeTerminator: bool = False) -> str:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength

		cursor = source.find(sub, cursor)
		if cursor == -1:
			cursor = length
		elif includeTerminator:
			cursor += len(sub)
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	@cy_final
	def readUntilEndOrRegex(self, sub: re.Pattern, *, includeTerminator: bool = False) -> str:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
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

	@cy_final
	def readUntilEndOrWhitespace(self) -> str:
		result = self.tryReadRegex(re.compile(NOT_JAVA_WHITESPACES_REGEX))
		assert result is not None
		return result

	@cy_final
	def tryReadRegex(self, pattern: re.Pattern) -> Optional[str]:  # throws CommandSyntaxException
		match = pattern.match(self.source, self.cursor)
		if match is None:
			return None
		text = match.group(0)
		self.save()
		self.cursor += len(text)
		return text

	@cy_final
	def tryReadInt(self) -> Optional[str]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength

		if cursor < length and source[cursor] == '-':
			cursor += 1
		if cursor < length and source[cursor] in DIGITS:
			cursor += 1
		else:
			return None
		while cursor < length and source[cursor] in DIGITS:
			cursor += 1
		if cursor < length and source[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	@cy_final
	def tryReadFloat(self) -> Optional[str]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		hasHadDot: bool = False

		if cursor < length and source[cursor] == '-':
			cursor += 1

		if cursor < length and source[cursor] == '.':
			hasHadDot = True
			cursor += 1

		if cursor < length and source[cursor] in DIGITS:
			cursor += 1
		else:
			return None
		while cursor < length and source[cursor] in DIGITS:
			cursor += 1
		if cursor < length and source[cursor] == '.':
			cursor += 1
			if hasHadDot:
				return None  # TODO: Lexer Errors
		while cursor < length and source[cursor] in DIGITS:
			cursor += 1
		if cursor < length and source[cursor] in DOT_OR_MINUS:
			return None  # TODO: Lexer Errors
		self.save()
		self.cursor = cursor
		return source[start:cursor]

	@cy_final
	def tryReadString(self) -> Optional[str]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		if cursor >= length:
			return None
		terminator: Char = source[cursor]
		TERMINATOR_OR_ESCAPE: set[Char] = {terminator, SYNTAX_ESCAPE}
		if terminator in QUOTES: # quoted string
			cursor += 1
			result: str = ''
			escaped: bool = False
			while cursor < length:
				c: Char = source[cursor]
				cursor += 1
				if escaped:
					if c in TERMINATOR_OR_ESCAPE:
						result += c
						escaped = False
					else:
						return None  # TODO: Lexer Errors
				elif c == SYNTAX_ESCAPE:
					escaped = True
				elif c == terminator:
					self.save()
					self.cursor = cursor
					return result
				else:
					result += c
			return None  # TODO: Lexer Errors
		else: # unquoted string
			while cursor < length and source[cursor] in UNQUOTED_STRING_CHARS:
				cursor += 1
			if start == cursor:
				return None
			self.save()
			self.cursor = cursor
			return source[start:cursor]

	@cy_final
	def tryReadBoolean(self) -> Optional[str]:  # throws CommandSyntaxException
		value: Optional[str] = self.tryReadString()
		if not value:
			return None  # TODO: Lexer Errors
		if value in BOOLEAN_VALUES:
			return value
		else:
			self.rollback()
			return None  # TODO: Lexer Errors

	@cy_final
	def tryReadLiteral(self) -> Optional[str]:  # throws CommandSyntaxException
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		if cursor >= length or source[cursor] == ' ':
			return None
		while cursor < length and source[cursor] != ' ':
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

	@cy_final
	def tryReadResourceLocation(self, *, allowTag: bool = False) -> Optional[str]:  # throws CommandSyntaxException
		# The namespace and the path of a resource location should only contain the following symbols:
		#     0123456789 Numbers
		#     abcdefghijklmnopqrstuvwxyz Lowercase letters
		#     _ Underscore
		#     - Hyphen/minus
		#     . Dot
		# The following characters are illegal in the namespace, but acceptable in the path:
		#     / Forward slash (directory separator)
		# The preferred naming convention for either namespace or path is snake_case.
		pattern = r'(?:[0-9a-z._-]+:)?[0-9a-z._/-]+'
		if allowTag:
			pattern = f'#?{pattern}'
		literal = self.tryReadRegex(re.compile(pattern))
		return literal

	@cy_final
	def tryReadTildeNotation(self) -> Optional[str]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		if cursor < length and source[cursor] == '~':
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

	@cy_final
	def tryReadCaretNotation(self) -> Optional[str]:
		start: int = self.cursor
		cursor: int = self.cursor
		source: str = self.source
		length: int = self.totalLength
		if cursor < length and source[cursor] == '^':
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




