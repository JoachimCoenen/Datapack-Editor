import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Iterator, Mapping, TypeVar, Type, Optional

from Cat.utils.collections_ import AddToDictDecorator
from base.model.parsing.tree import Node, Schema, TokenLike
from base.model.pathUtils import FilePath
from base.model.utils import Message, ParsingError, Position, GeneralError, LanguageId, MDStr, Span, wrapInMarkdownCode, NULL_SPAN

_TToken = TypeVar('_TToken', bound=TokenLike)
_TNode = TypeVar('_TNode', bound=Node)
_TSchema = TypeVar('_TSchema', bound=Schema)


def mapRange(x: int, rf: tuple[int, int], rt: tuple[int, int]) -> int:
	"""
	:param x:
	:param rf: rangeFrom
	:param rt: rangeTo
	:return:
	"""
	if rf[1] == rf[0]:
		return rt[1]
	else:
		return (x - rf[0]) * (rt[1] - rt[0]) // (rf[1] - rf[0]) + rt[0]


@dataclass
class IndexMapper:
	"""
	dec: decoded = the string (& indices) used by the parser
	enc: encoded = the string (& indices) edited by the user
	(encPos, decPos)
	"""
	_markers: list[tuple[int, int]] = field(default_factory=lambda: [(0, 0)], kw_only=True)
	""" list of (encPos, decPos) pairs"""

	def _findMarker(self, pos: int, toEnc: bool) -> int:
		"""
		find the corresponding largest index i such that indices[i][D] <= pos where D = 1 if toEnc else 0
		:param pos:
		:param toEnc:
		:return:
		"""
		D = 1 if toEnc else 0
		a = self._markers
		lo = 0
		hi = len(a)
		while lo < hi:
			mid = (lo + hi) // 2
			# Use __lt__ to match the logic in list.sort() and in heapq
			if a[mid][D] < pos:
				lo = mid + 1
			else:
				hi = mid
		# now following statement is true: a[lo][D] >= pos && a[lo-1][D] < pos
		if lo == len(a) or a[lo][D] != pos:
			lo -= 1
		# now following statement is true: a[lo][D] <= pos && a[lo+1][D] > pos

		# # now following statement is true: a[lo][D] > pos && a[lo-1][D] <= pos
		# lo -= 1
		# # now following statement is true: a[lo][D] <= pos && a[lo+1][D] > pos

		# if lo == len(a):
		# 	return -1

		# if lo == -1:  can happen, but we pass it on
		# 	return -1
		return lo

	def findDecodingMap(self, encPos: int) -> int:
		""" find the corresponding largest index i such that indices[i][0] <= encPos """
		return self._findMarker(encPos, toEnc=False)

	def findEncodingMap(self, decPos: int) -> int:
		""" find the corresponding largest index i such that indices[i][1] <= decPos """
		return self._findMarker(decPos, toEnc=True)

	def _mapPos(self, pos: int, toEnc: bool) -> int:
		D = 1 if toEnc else 0
		E = 0 if toEnc else 1
		i = self._findMarker(pos, toEnc)
		le = self._markers[i] if i >= 0 else (0, 0)
		if i + 1 == len(self._markers):
			# we're at the very end
			result = pos - le[D] + le[E]
		else:
			# we're between two markers and have to interpolate:
			gt = self._markers[i + 1]
			result = mapRange(pos, (le[D], gt[D]), (le[E], gt[E]))
			# result = ((pos - le[D]) * (gt[E] - le[E])) // (gt[D] - le[D]) + le[E]
		return result

	def toDecoded(self, encPos: int) -> int:
		return self._mapPos(encPos, toEnc=False)

	def toEncoded(self, decPos: int) -> int:
		return self._mapPos(decPos, toEnc=True)

	def addMarker(self, encPos: int, decPos: int):
		marker = (encPos, decPos)
		if not self._markers or self._markers[-1] != marker:
			self._markers.append(marker)


@dataclass
class IndexMapBuilder:
	baseMap: IndexMapper
	offset: int
	_markers: list[tuple[int, int]] = field(default_factory=list, init=False)
	_lastEncPos: int = field(init=False)
	""" list of (encPos, decPos) pairs"""
	_lastBaseMapIdx: int = field(default=-1, init=False)

	def __post_init__(self):
		self._lastBaseMapIdx = self.baseMap.findEncodingMap(self.offset)
		self._lastEncPos = self.offset
		self.addMarker(0, 0)

	def _addActualMarker(self, marker: tuple[int, int]) -> None:
		if not self._markers or self._markers[-1] != marker:
			self._markers.append(marker)

	def _addBaseMarkers(self, encPos: int, decPos: int):
		""" adds the markers from the _baseMap that are come before the given marker (encPos, decPos)"""
		baseIdx = self.baseMap.findEncodingMap(encPos)
		if baseIdx <= self._lastBaseMapIdx:
			return
		lastMarker = self._markers[-1]
		lastEncPos = self._lastEncPos
		for idx in range(self._lastBaseMapIdx + 1, baseIdx + 1):
			baseMarker = self.baseMap._markers[idx]
			actualBaseDec = mapRange(baseMarker[1], (lastEncPos, encPos), (lastMarker[1], decPos))
			self._addActualMarker((baseMarker[0], actualBaseDec))
		self._lastBaseMapIdx = baseIdx

	def addMarker(self, encPos: int, decPos: int):
		encPos += self.offset
		decPos += self.offset
		actualEncPos = self.baseMap.toEncoded(encPos)
		self._addBaseMarkers(encPos, decPos)
		self._addActualMarker((actualEncPos, decPos))
		self._lastEncPos = encPos

	def completeIndexMapper(self, encPosLastChar: int, decPosLastChar: int) -> IndexMapper:
		self.addMarker(encPosLastChar, decPosLastChar)
		return IndexMapper(_markers=self._markers)


@dataclass
class _Base(ABC):
	text: bytes
	line: int
	lineStart: int
	cursor: int
	cursorOffset: int
	indexMapper: IndexMapper
	maxEncIndex: int
	errors: list[GeneralError] = field(default_factory=list, init=False)
	maxErrors: int = field(default=200, init=False)

	length: int = field(init=False)
	decodedBytesCursor: int = field(init=False)
	_lastDecodedCursorOfBytesDecodedCursor: int = field(init=False)

	def __post_init__(self):
		self.length = len(self.text)
		self.decodedBytesCursor = self.cursor
		self._lastDecodedCursorOfBytesDecodedCursor = self.cursor

	@property
	def currentPos(self) -> Position:
		actualCursor = self.indexMapper.toEncoded(self.cursor + self.cursorOffset)
		return Position(self.line, actualCursor - self.lineStart, actualCursor)

	# @property
	# def currentPos(self) -> Position:
	# 	actualCursor = self.indexMapper.toEncoded(self.cursor) + self.cursorOffset
	# 	return Position(self.line, actualCursor - self.lineStart, actualCursor)

	def advanceLine(self) -> None:
		self.lineStart = self.indexMapper.toEncoded(self.cursor + self.cursorOffset)
		self.line += 1

	def advanceLineCounter(self, newPos: int) -> None:
		start_of_line = self.text.rfind(b'\n', self.cursor, newPos)
		if start_of_line != -1:
			self.lineStart = start_of_line + self.cursorOffset + 1
			self.line += self.text.count(b'\n', self.cursor, start_of_line) + 1

	def advanceLineCounterAndUpdatePos(self, newPos: int) -> None:
		start_of_line = self.text.rfind(b'\n', self.cursor, newPos)
		if start_of_line != -1:
			self.lineStart = start_of_line + self.cursorOffset + 1
			self.line += self.text.count(b'\n', self.cursor, start_of_line) + 1
		self.cursor = newPos

	def tryConsumeLiteral(self, chars: bytes) -> bool:
		if self.text.startswith(chars, self.cursor):
			self.cursor += len(chars)
			return True
		else:
			return False

	def consumeLiteral(self, chars: bytes) -> bool:
		if self.tryConsumeLiteral(chars):
			return True
		else:
			self.error(MDStr(f"Expected {wrapInMarkdownCode(repr(chars))}"))
			return False

	def tryConsumeAnyOfLiteral(self, options: tuple[bytes, ...]) -> Optional[bytes]:
		for chars in options:
			if self.text.startswith(chars, self.cursor):
				self.cursor += len(chars)
				return chars
		return None

	def consumeAnyOfLiteral(self, options: tuple[bytes, ...]) -> Optional[str]:
		if (chars := self.tryConsumeAnyOfLiteral(options)) is not None:
			return chars
		else:
			optionsStr = ', '.join(f'`{repr(chars)}`' for chars in options)
			self.error(MDStr(f"Expected any of ({optionsStr})"))
			return None

	def tryReadRegex(self, pattern: re.Pattern[bytes]) -> Optional[bytes]:
		match = pattern.match(self.text, self.cursor)
		if match is None:
			return None
		text = match.group(0)
		self.cursor += len(text)
		return text

	def tryReadRegexMultiLine(self, pattern: re.Pattern[bytes]) -> Optional[bytes]:
		match = pattern.match(self.text, self.cursor)
		if match is None:
			return None
		text = match.group(0)
		self.advanceLineCounterAndUpdatePos(self.cursor + len(text))
		return text

	@staticmethod
	def createError(message: MDStr, span: Span, style: str) -> ParsingError:
		return ParsingError(message, span=span, style=style)

	def error(self, message: MDStr, *, span: Span = ..., style: str = 'error') -> None:
		if len(self.errors) >= self.maxErrors > 0:
			return  # don't generate too many errors!
		# Provide additional information in the errors message
		if span is ...:
			position = self.currentPos
			span = Span(position)
		error = self.createError(message, span, style)
		self.errors.append(error)

	def errorMsg(self, msg: Message, *args, span: Span, style: str = 'error') -> None:
		if len(self.errors) >= self.maxErrors > 0:
			return  # don't generate too many errors!
		msgStr = msg.format(*args)
		self.error(msgStr, span=span, style=style)


@dataclass
class TokenizerBase(_Base, Generic[_TToken], ABC):
	totalLength: int = field(default=-1, init=False)

	def __post_init__(self):
		self.totalLength = len(self.text)

	@abstractmethod
	def nextToken(self) -> Optional[_TToken]:
		pass

	def __iter__(self) -> Iterator[_TToken]:
		while (tk := self.nextToken()) is not None:
			yield tk


@dataclass
class ParserBase(_Base, Generic[_TNode, _TSchema], ABC):
	schema: Optional[_TSchema]
	filePath: FilePath

	@abstractmethod
	def parse(self) -> Optional[_TNode]:
		pass


__parsers: dict[LanguageId, Type[ParserBase]] = {}
registerParser = AddToDictDecorator(__parsers)
getParserCls = __parsers.get


def allParsers() -> Mapping[LanguageId, Type[ParserBase]]:
	return __parsers


def parse(
		text: bytes,
		*,
		filePath: FilePath,
		language: LanguageId,
		schema: Optional[Schema],
		line: int = 0,
		lineStart: int = 0,
		cursor: int = 0,
		cursorOffset: int = 0,
		indexMapper: IndexMapper = None,
		maxIndex: int = None,
		**kwargs
) -> tuple[Optional[Node], list[GeneralError]]:
	parserCls = getParserCls(language)
	if parserCls is None:
		return None, [ParsingError(MDStr(f"No Parser for language `{language}` registered."), span=NULL_SPAN, style='info')]
	if indexMapper is None:
		indexMapper = IndexMapper()
	maxEncIndex = maxIndex
	if maxEncIndex is None:
		maxEncIndex = 2**63 - 1
	parser: ParserBase = parserCls(text, line, lineStart, cursor, cursorOffset, indexMapper, maxEncIndex, schema, filePath, **kwargs)
	node = parser.parse()
	return node, parser.errors


__all__ = [
	'IndexMapper',
	'IndexMapBuilder',
	'TokenizerBase',
	'ParserBase',
	'registerParser',
	'getParserCls',
	'allParsers',
	'parse'
]
