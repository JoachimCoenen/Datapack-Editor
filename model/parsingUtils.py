from __future__ import annotations

import builtins
from typing import overload, Optional, final, Iterator

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, Computed
from Cat.utils import HTMLifyMarkDownSubSet
from Cat.utils.formatters import formatVal


@final
@RegisterContainer
class Position(SerializableContainer):
	__slots__ = ()
	line: int = Serialized(default=-1)
	column: int = Serialized(default=-1)
	index: int = Serialized(default=-1)

	@overload
	def __init__(self):
		...

	@overload
	def __init__(self, line: int, column: int, index: int):
		...

	def __init__(self, line: int = -1, column: int = -1, index: int = -1):
		super(Position, self).__init__()
		self.line = line
		self.column = column
		self.index = index

	def __iter__(self):
		yield self.line
		yield self.column

	def __len__(self):
		return 2

	def __eq__(self, other) -> bool:
		return isinstance(other, Position) and self.line == other.line and self.column == other.column

	def __ne__(self, other) -> bool:
		return not (isinstance(other, Position) and self.line == other.line and self.column == other.column)

	def __lt__(self, other: Position) -> bool:
		return (self.line < other.line) \
			or (self.line == other.line and self.column < other.column)

	def __le__(self, other: Position) -> bool:
		return (self.line < other.line) \
			or (self.line == other.line and self.column <= other.column)

	def __gt__(self, other: Position) -> bool:
		return (self.line > other.line) \
			or (self.line == other.line and self.column > other.column)

	def __ge__(self, other: Position) -> bool:
		return (self.line > other.line) \
			or (self.line == other.line and self.column >= other.column)

	def __hash__(self) -> int:
		return hash((self.line, self.column))

	def __repr__(self):
		return f' Position({self.line}, {self.column}, {self.index})'


@final
@RegisterContainer
class Span(SerializableContainer):
	__slots__ = ()
	start: Position = Serialized(default_factory=Position, customPrintFunc=lambda s, v: formatVal(v, singleIndent='', newLine='').s)
	end: Position = Serialized(getInitValue=start, customPrintFunc=lambda s, v: formatVal(v, singleIndent='', newLine='').s)

	slice: builtins.slice = Computed(getInitValue=lambda s: builtins.slice(s.start.index, s.end.index))
	asTuple: tuple[Position, Position] = Computed(getInitValue=lambda s: (s.start, s.end))


	@overload
	def __init__(self):
		...

	@overload
	def __init__(self, start: Position, /):
		...

	@overload
	def __init__(self, start: Position, end: Position, /):
		...

	def __init__(self, start: Position = None, end: Position = None, /):
		super(Span, self).__init__()
		if start is not None:
			self.start: Position = start
		if end is not None:
			self.end: Position = end

	def __iter__(self) -> Iterator[Position]:
		yield self.start
		yield self.end

	def __repr__(self):
		return f' Span({self.start!r}, {self.end!r})'


@RegisterContainer
class GeneralParsingError(SerializableContainer):
	__slots__ = ()
	message: str = Serialized(default='')
	span: Span = Serialized(default_factory=Span)
	style: str = Serialized(default='error')

	position: Position = Computed(getInitValue=span.start)
	end: Position = Serialized(getInitValue=span.end)

	def __init__(self, message: str, span: Span, style: str = 'error'):
		super(GeneralParsingError, self).__init__()
		if self.__class__ is GeneralParsingError:
			raise RuntimeError("GeneralParsingError should not be instantiated directly")
		self.message: str = f"<font>{HTMLifyMarkDownSubSet(message)}</font>"
		self.span: Span = span
		self.style: str = style

	def __str__(self):
		return f"{self.message} at pos {self.span.start.column}, line {self.span.start.line + 1}"


__all__ = [
	'Position',
	'Span',
	'GeneralParsingError',
]