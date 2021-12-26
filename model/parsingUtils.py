from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from typing import final, Iterator

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, Computed
from Cat.utils import HTMLifyMarkDownSubSet


@final
@dataclass(order=True, unsafe_hash=True, frozen=False)
class Position:
	line: int = -1
	column: int = -1
	index: int = field(default=-1, hash=False, compare=False)

	def __iter__(self):
		yield self.line
		yield self.column

	def __len__(self):
		return 2


@final
@dataclass(frozen=False)
class Span:
	start: Position = field(default_factory=Position)
	end: Position = field(default_factory=Position)

	@property
	def slice(self) -> builtins.slice:
		return builtins.slice(self.start.index, self.end.index)

	@property
	def asTuple(self) -> tuple[Position, Position]:
		return self.start, self.end

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