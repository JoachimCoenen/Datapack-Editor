import builtins
from dataclasses import dataclass, field
from typing import final, Iterator, Optional

from Cat.utils import HTMLifyMarkDownSubSet


@dataclass(frozen=True)
class Message:
	rawMessage: str
	argsCount: int

	def format(self, *args) -> str:
		if len(args) > self.argsCount:
			raise ValueError(f"too many arguments supplied. expected {self.argsCount}, but got {len(args)}")
		elif len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected {self.argsCount}, but got {len(args)}")

		return self.rawMessage.format(*args)


@final
@dataclass(order=True, unsafe_hash=True)
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
@dataclass(init=False)
class Span:
	start: Position
	end: Position

	def __init__(self, start: Position = None, end: Position = None):
		self.start = Position() if start is None else start
		self.end = self.start if end is None else end

	@property
	def slice(self) -> builtins.slice:
		return builtins.slice(self.start.index, self.end.index)

	@property
	def asTuple(self) -> tuple[Position, Position]:
		return self.start, self.end

	@property
	def length(self) -> int:
		return self.end.index - self.start.index

	def __iter__(self) -> Iterator[Position]:
		yield self.start
		yield self.end

	def __repr__(self):
		return f' Span({self.start!r}, {self.end!r})'


class GeneralParsingError:
	def __init__(self, message: str, span: Span, style: str = 'error'):
		super(GeneralParsingError, self).__init__()
		if self.__class__ is GeneralParsingError:
			raise RuntimeError("GeneralParsingError should not be instantiated directly")
		self.message: str = f"<font>{HTMLifyMarkDownSubSet(message)}</font>"
		self.span: Span = span
		self.style: str = style

	def __str__(self):
		return f"{self.message} at pos {self.span.start.column}, line {self.span.start.line + 1}"

	@property
	def position(self) -> Position:
		return self.span.start

	@property
	def end(self) -> Position:
		return self.span.end


class WrappedError:
	"""
	just a wrapper for any Exception
	satisfies protocol `Error`
	"""
	def __init__(self, exception: Exception):
		super(WrappedError, self).__init__()
		self.wrappedEx = exception
		self.message: str = str(exception)
		self.position: Optional[Position] = None
		self.end: Optional[Position] = None
		self.style: str = 'error'


__all__ = [
	'Message',
	'Position',
	'Span',
	'GeneralParsingError',
	'WrappedError',
]
