from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TypeVar, Union, Optional, Sequence, Any, Generic, ClassVar, Collection

from cat.utils import Singleton
from . import MC_FUNCTION_ID
from .argumentTypes import ArgumentType, BRIGADIER_STRING, LiteralsArgumentType
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.tree import Schema, Node
from base.model.utils import Position, LanguageId, Span


@dataclass
class Named(ABC):
	name: str

	def __post_init__(self):
		assert isinstance(self.name, str)


@dataclass
class CommandPartSchema(Schema, Named, ABC):
	description: str = field(default='')
	next: Sequence[CommandPartSchema] = field(default_factory=list)

	language: ClassVar[LanguageId] = MC_FUNCTION_ID


@dataclass
class KeywordSchema(CommandPartSchema):
	@property
	def asString(self) -> str:
		return f'{self.name}'


@dataclass
class ArgumentSchema(CommandPartSchema):
	type: ArgumentType = field(default=BRIGADIER_STRING)

	@property
	def typeName(self) -> str:
		return self.type.name

	subType: Optional[ArgumentType] = field(default=None)
	args: Optional[dict[str, Union[Any, None]]] = field(default=None)
	next: Sequence[CommandPartSchema] = field(default_factory=list)

	@property
	def asString(self) -> str:
		if isinstance(self.type, LiteralsArgumentType):
			return f"({bytesToStr(b'|'.join(opt for opt in self.type.options))})"
		return f'<{self.name}: {self.typeName}>'


@dataclass
class SwitchSchema(CommandPartSchema):
	options: list[Union[KeywordSchema, TerminalSchema]] = field(default_factory=list)
	next: Sequence[CommandPartSchema] = field(default_factory=list)

	@property
	def asString(self) -> str:
		options = '|'.join(opt.asString for opt in self.options)
		return f"({options})"


@dataclass
class TerminalSchema(Singleton, CommandPartSchema):
	@property
	def asString(self) -> str:
		return 'END'


TERMINAL = TerminalSchema(name='Terminal')


@dataclass
class CommandsRoot(Singleton, CommandPartSchema):

	@property
	def asString(self) -> str:
		return f'<execute: Command>'


COMMANDS_ROOT = CommandsRoot(name='Command')


def formatPossibilities(possibilities: Sequence[CommandPartSchema]) -> str:
	isOptional = TERMINAL in possibilities
	possibilities2 = [p for p in possibilities if p is not TERMINAL]
	isMany = len(possibilities2) > 1

	result = '|'.join(p.asString.strip('()') for p in possibilities2)

	if isOptional:
		return f"[{result}]"
	elif isMany:
		return f"({result})"
	else:
		return result


@dataclass
class CommandSchema(CommandPartSchema):
	# name: str = field(default='')
	# description: str = field(default='')
	opLevel: Union[int, str] = field(default=0)
	availableInSP: bool = field(default=True)
	availableInMP: bool = field(default=True)

	removed: bool = field(default=False)
	removedVersion: str = field(default=None)  # , doc="""the version this command was removed, if it has been removed else""")
	removedComment: str = field(default='')

	deprecated: bool = field(default=False)
	deprecatedVersion: Optional[str] = field(default=None)  # , doc="""the version this command was deprecated, if it has been deprecated""")
	deprecatedComment: str = field(default='')

	next: list[CommandPartSchema] = field(default_factory=list[CommandPartSchema])

	@property
	def asString(self) -> str:
		return f"{self.name} {formatPossibilities(self.next)}"


@dataclass
class CommentSchema(CommandPartSchema):

	@property
	def asString(self) -> str:
		return f"<Comment>"


@dataclass
class MCFunctionSchema(CommandPartSchema):
	commands: dict[bytes, CommandSchema] = field(default_factory=dict)

	@property
	def asString(self) -> str:
		return f'<MCFunction>'


_TCommandPartSchema = TypeVar('_TCommandPartSchema', bound=CommandPartSchema)


@dataclass
class CommandPart(Node['CommandPart', _TCommandPartSchema], Generic[_TCommandPartSchema], ABC):
	source: bytes = field(repr=False)
	content: bytes = field(repr=False)
	# @property
	# def content(self) -> bytes:
	# 	return self.source[self.span.slice]

	switchSchema: Optional[SwitchSchema] = field(default=None, init=False)

	_next: Optional[CommandPart] = field(default=None, init=False)
	_prev: Optional[CommandPart] = field(default=None, init=False, repr=False)

	language: ClassVar[LanguageId] = MC_FUNCTION_ID

	@property
	def next(self) -> Optional[CommandPart]:
		return self._next

	@next.setter
	def next(self, value: Optional[CommandPart]):
		oldVal = self._next
		if oldVal is not None:
			oldVal._prev = None
		if value is not None:
			value._prev = self
		self._next = value

	@property
	def prev(self) -> Optional[CommandPart]:
		return self._prev

	@property
	def start(self) -> Position:
		return self.span.start

	@property
	def end(self) -> Position:
		return self.span.end

	@property
	def children(self) -> Collection[CommandPart]:
		return ()



@dataclass
class ParsedComment(CommandPart[CommentSchema]):

	@property
	def children(self) -> Collection[CommandPart]:
		return ()


@dataclass
class ParsedCommand(CommandPart[CommandSchema]):
	name: bytes
	nameSpan: Span = field(hash=False, compare=False)

	@property
	def children(self) -> Collection[CommandPart]:
		result = []
		arg = self.next
		while arg is not None:
			result.append(arg)
			if type(arg) is ParsedCommand:
				break
			arg = arg._next
		return result


@dataclass
class ParsedArgument(CommandPart[ArgumentSchema]):
	value: Any

	@property
	def children(self) -> Collection[CommandPart]:
		return ()


@dataclass
class MCFunction(CommandPart[MCFunctionSchema]):
	_children: list[Union[ParsedCommand, ParsedComment]] = field(default_factory=list)

	@property
	def commands(self) -> list[ParsedCommand]:
		return [c for c in self.children if isinstance(c, ParsedCommand)]

	@property
	def comments(self) -> list[ParsedComment]:
		return [c for c in self.children if isinstance(c, ParsedComment)]

	@property
	def children(self) -> Collection[CommandPart]:
		return self._children


def _addSchemas(schemas: Sequence[CommandPartSchema], allSchemasIO: list[CommandPartSchema]) -> bool:
	"""returns True if TERMINAL was found in schemas, or schemas was empty"""
	hasTerminal = False
	wasEmpty = True
	for n in schemas:
		if n is TERMINAL:
			hasTerminal = True
		elif isinstance(n, SwitchSchema):
			wasEmpty = False
			if _addSchemas(n.options, allSchemasIO):
				hasTerminal = _addSchemas(n.next, allSchemasIO) or hasTerminal
		else:
			wasEmpty = False
			allSchemasIO.append(n)
	return hasTerminal or wasEmpty


def getNextSchemas(before: CommandPart) -> Sequence[CommandPartSchema]:
	allSchemas = []
	if (schema := before.schema) is not None:
		if not _addSchemas(schema.next, allSchemas):
			return allSchemas
	else:
		return allSchemas

	prev = before
	while (prev := prev.prev) is not None:
		if (schema := prev.switchSchema) is not None:
			if not _addSchemas(schema.next, allSchemas):
				return allSchemas
	return allSchemas


__all__ = [
	'CommandPartSchema',
	'KeywordSchema',
	'ArgumentSchema',
	'SwitchSchema',
	'TerminalSchema',
	'TERMINAL',
	'CommandsRoot',
	'COMMANDS_ROOT',
	'formatPossibilities',
	'CommandSchema',
	'CommentSchema',
	'MCFunctionSchema',
	'CommandPart',
	'ParsedComment',
	'ParsedCommand',
	'ParsedArgument',
	'MCFunction',
	'getNextSchemas',
]
