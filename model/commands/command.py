from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Union, Optional, Sequence

from Cat.utils import Singleton, abstract
from model.commands.argumentTypes import ArgumentType, BRIGADIER_STRING, LiteralsArgumentType

TS = TypeVar('TS')
TT = TypeVar('TT')


@abstract
@dataclass
class CommandNode:
	name: str = field(default='')
	description: str = field(default='')
	next: Sequence[CommandNode] = field(default_factory=lambda: list[CommandNode]())

	@abstract
	def asCodeString(self) -> str:
		...


@dataclass
class Keyword(CommandNode):
	def asCodeString(self) -> str:
		return f'{self.name}'


@dataclass
class LiteralsInfo(CommandNode):
	options: list[str] = field(default_factory=list[str])
	next: Sequence[CommandNode] = field(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		options = '|'.join(self.options)
		return f"({options})"


@dataclass
class ArgumentInfo(CommandNode):
	type: ArgumentType = field(default=BRIGADIER_STRING)

	@property
	def typeName(self) -> str:
		return self.type.name

	subType: Optional[ArgumentType] = field(default=None)
	args: Optional[dict[str, Union[Any, None]]] = field(default=None)
	next: Sequence[CommandNode] = field(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		if isinstance(self.type, LiteralsArgumentType):
			return f"({'|'.join(opt for opt in self.type.options)})"
		return f'<{self.name}: {self.typeName}>'


@dataclass
class Switch(CommandNode):
	options: list[Union[Keyword, Terminal]] = field(default_factory=list[Keyword])
	next: Sequence[CommandNode] = field(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		options = '|'.join(opt.asCodeString() for opt in self.options)
		return f"({options})"


@dataclass
class Terminal(Singleton, CommandNode):
	pass


TERMINAL = Terminal()


@dataclass
class CommandsRoot(Singleton, CommandNode):

	def asCodeString(self) -> str:
		return f'<execute: Command>'


COMMANDS_ROOT = CommandsRoot()


def asCodeString(part) -> str:
	return part.asCodeString()


def formatPossibilities(possibilities: Sequence[CommandNode]) -> str:
	isOptional = TERMINAL in possibilities
	possibilities2 = [p for p in possibilities if p is not TERMINAL]
	isMany = len(possibilities2) > 1

	result = '|'.join(asCodeString(p).strip('()') for p in possibilities2)

	if isOptional:
		return f"[{result}]"
	elif isMany:
		return f"({result})"
	else:
		return result


@dataclass
class CommandInfo(CommandNode):
	name: str = field(default='')
	description: str = field(default='')
	opLevel: Union[int, str] = field(default=0)
	availableInSP: bool = field(default=True)
	availableInMP: bool = field(default=True)

	removed: bool = field(default=False)
	removedVersion: str = field(default=None)  # , doc="""the version this command was removed, if it has been removed else""")
	removedComment: str = field(default='')

	deprecated: bool = field(default=False)
	deprecatedVersion: Optional[str] = field(default=None) #, doc="""the version this command was deprecated, if it has been deprecated""")
	deprecatedComment: str = field(default='')

	next: list[CommandNode] = field(default_factory=list[CommandNode])

	def asCodeString(self) -> str:
		return f"{self.name} {formatPossibilities(self.next)}"
