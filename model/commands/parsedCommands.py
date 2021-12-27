from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union, Any

from model.commands.command import CommandInfo, CommandNode
from model.parsingUtils import Position, Span


@dataclass
class ParsedNode:
	source: str = field(repr=False)
	span: Span

	@property
	def start(self) -> Position:
		return self.span.start

	@property
	def end(self) -> Position:
		return self.span.end

	@property
	def content(self) -> str:
		return self.source[self.span.slice]


@dataclass
class ParsedComment(ParsedNode):
	pass


@dataclass
class ParsedCommandPart(ParsedNode):
	value: Any
	info: Optional[CommandNode]
	_next: Optional[ParsedCommandPart] = field(default=None, init=False)
	_prev: Optional[ParsedCommandPart] = field(default=None, init=False, repr=False)

	@property
	def next(self) -> Optional[ParsedCommandPart]:
		return self._next

	@next.setter
	def next(self, value: Optional[ParsedCommandPart]):
		oldVal = self._next
		if oldVal is not None:
			oldVal._prev = None
		if value is not None:
			value._prev = self
		self._next = value

	@property
	def prev(self) -> Optional[ParsedCommandPart]:
		return self._prev


@dataclass
class ParsedCommand(ParsedCommandPart):
	info: Optional[CommandInfo]

	@property
	def name(self) -> str:
		return self.value


@dataclass
class ParsedArgument(ParsedCommandPart):
	pass


@dataclass
class ParsedMCFunction:
	children: list[Union[ParsedCommand, ParsedComment]] = field(default_factory=list[Union[ParsedCommand, ParsedComment]])

	@property
	def commands(self) -> list[ParsedCommand]:
		return [c for c in self.children if isinstance(c, ParsedCommand)]

	@property
	def comments(self) -> list[ParsedComment]:
		return [c for c in self.children if isinstance(c, ParsedComment)]
