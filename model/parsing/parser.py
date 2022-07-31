from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Type, Optional, Iterator, Mapping

from Cat.utils import Decorator
from Cat.utils.collections_ import AddToDictDecorator
from model.parsing.tree import Node, Schema, TokenLike
from model.utils import Position, GeneralError, LanguageId, MDStr, Span, ParsingError

_TToken = TypeVar('_TToken', bound=TokenLike)
_TNode = TypeVar('_TNode', bound=Node)
_TSchema = TypeVar('_TSchema', bound=Schema)


@dataclass
class IndexMapper:
	indices: list[tuple[int, int]] = field(default_factory=list)

	def _findEncodingMap(self, dec: int):
		a = self.indices
		lo = 0
		hi = len(a)
		while lo < hi:
			mid = (lo + hi) // 2
			# Use __lt__ to match the logic in list.sort() and in heapq
			if a[mid][1] < dec:
				lo = mid + 1
			else:
				hi = mid

		lo -= 1
		if 0 > lo or lo >= len(a):
			return 0, 0
		return a[lo]

	# def toDecoded(self, enc: int) -> int:
	# 	mapp = self._findEncoded(enc)
	# 	mapp

	def toEncoded(self, dec: int) -> int:
		mapp = self._findEncodingMap(dec)
		return dec - mapp[1] + mapp[0]


@dataclass
class _Base(ABC):
	text: bytes
	line: int
	lineStart: int
	cursor: int
	cursorOffset: int
	indexMapper: IndexMapper
	errors: list[GeneralError] = field(default_factory=list, init=False)

	@property
	def currentPos(self) -> Position:
		actualCursor = self.indexMapper.toEncoded(self.cursor) + self.cursorOffset
		return Position(self.line, actualCursor - self.lineStart, actualCursor)

	@staticmethod
	def createError(message: MDStr, span: Span, style: str) -> ParsingError:
		return ParsingError(message, span=span, style=style)

	def error(self, message: MDStr, *, span: Span = ..., style: str = 'error') -> None:
		# Provide additional information in the errors message
		if span is ...:
			position = self.currentPos
			span = Span(position)
		error = self.createError(message, span, style)
		self.errors.append(error)


@dataclass
class TokenizerBase(_Base, Generic[_TToken], ABC):
	totalLength: int = field(default=-1, init=False)

	def __post_init__(self):
		self.totalLength = len(self.text)

	def advanceLine(self) -> None:
		self.lineStart = self.indexMapper.toEncoded(self.cursor) + self.cursorOffset
		self.line += 1

	@abstractmethod
	def nextToken(self) -> Optional[_TToken]:
		pass

	def __iter__(self) -> Iterator[_TToken]:
		while (tk := self.nextToken()) is not None:
			yield tk


@dataclass
class ParserBase(_Base, Generic[_TNode, _TSchema], ABC):
	schema: Optional[_TSchema]

	@abstractmethod
	def parse(self) -> Optional[_TNode]:
		pass


__parsers: dict[LanguageId, Type[ParserBase]] = {}
registerParser = Decorator(AddToDictDecorator(__parsers))

getParserCls = __parsers.get


def allParsers() -> Mapping[LanguageId, Type[ParserBase]]:
	return __parsers


def parse(
		text: bytes,
		*,
		language: LanguageId,
		schema: Optional[Schema],
		line: int = 0,
		lineStart: int = 0,
		cursor: int = 0,
		cursorOffset: int = 0,
		indexMapper: IndexMapper = None,
		**kwargs
) -> tuple[Optional[Node], list[GeneralError]]:
	parserCls = getParserCls(language)
	if parserCls is None:
		return None, [GeneralError(MDStr(f"No Parser for language `{language}` registered."), Span(), style='info')]
	if indexMapper is None:
		indexMapper = IndexMapper()
	parser: ParserBase = parserCls(text, line, lineStart, cursor, cursorOffset, indexMapper, schema, **kwargs)
	node = parser.parse()
	return node, parser.errors


__all__ = [
	'IndexMapper',
	'TokenizerBase',
	'ParserBase',
	'registerParser',
	'getParserCls',
	'parse'
]
