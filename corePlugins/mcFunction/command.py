from __future__ import annotations

from abc import ABC
from collections import deque
from dataclasses import dataclass, field
from typing import Mapping, TypeVar, Union, Optional, Sequence, Any, Generic, ClassVar, Collection
from warnings import warn

from cat.utils import Nothing, Singleton
from . import MC_FUNCTION_ID
from .argumentTypes import ArgumentType, BRIGADIER_STRING, LiteralsArgumentType
from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.tree import Schema, Node
from base.model.utils import Position, LanguageId, Span


@dataclass
class Named(ABC):
	name: str

	def __post_init__(self):
		assert isinstance(self.name, str)


@dataclass
class Options:
	all: Sequence[CommandPartSchema]
	flattened: Sequence[CommandPartSchema] = field(init=False)
	keywords: Mapping[bytes, KeywordSchema] = field(init=False)
	nonKeywords: Sequence[SwitchSchema | ArgumentSchema | CommandsRoot] = field(init=False)
	switchSchemas: Sequence[SwitchSchema] = field(init=False)
	arguments: Sequence[ArgumentSchema] = field(init=False)
	hasCommand: bool = field(init=False)
	hasTerminal: bool = field(init=False)

	def __post_init__(self):
		self.finish()

	def finish(self):
		if not self.all:
			self.keywords = {}
			self.flattened = self.nonKeywords = self.switchSchemas = self.arguments = ()
			self.hasCommand = False
			self.hasTerminal = True
		else:
			self.flattened = _getAllPossibilities(self.all)
			self.keywords = {strToBytes(kw.name): kw for kw in self.all if isinstance(kw, KeywordSchema)}
			self.nonKeywords = [kw for kw in self.all if isinstance(kw, SwitchSchema | ArgumentSchema | CommandsRoot)]
			self.switchSchemas = [kw for kw in self.all if isinstance(kw, SwitchSchema)]
			self.arguments = [kw for kw in self.all if isinstance(kw, ArgumentSchema)]
			self.hasCommand = any(isinstance(kw, CommandsRoot) for kw in self.all)
			self.hasTerminal = not self.all or TERMINAL in self.all

	def deepFinish(self):
		alreadySeen: set[int] = set()
		toBeFinished: deque[Options] = deque()

		def queueOptions(options: Options):
			if id(options) not in alreadySeen:
				toBeFinished.append(options)
				alreadySeen.add(id(options))

		queueOptions(self)

		while toBeFinished:
			options = toBeFinished.popleft()
			options.finish()
			for arg in options.all:
				queueOptions(arg.next)
				if isinstance(arg, SwitchSchema):
					queueOptions(arg.options)


@dataclass
class CommandPartSchema(Schema, Named, ABC):
	description: str = field(default='')
	next: Options = field(default_factory=list)

	language: ClassVar[LanguageId] = MC_FUNCTION_ID

	def __post_init__(self):
		self.finish()

	def finish(self):
		if hasattr(self.next, '__iter__'):
			self.next = Options(self.next)
		else:
			self.next.finish()


def _getAllPossibilities(possibilities: Sequence[CommandPartSchema]) -> list[CommandPartSchema]:
	result = {}
	_addAllPossibilities(possibilities, result)
	return list(result.values())


def _addAllPossibilities(possibilities: Sequence[CommandPartSchema], allIO: dict[int, CommandPartSchema]) -> None:
	for possibility in possibilities:
		if isinstance(possibility, SwitchSchema):
			_addAllPossibilities(possibility.options.all, allIO)
			if possibility.options.hasTerminal:
				_addAllPossibilities(possibility.next.all, allIO)
		else:
			allIO[id(possibility)] = possibility


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
	next: Options = field(default_factory=list)

	@property
	def asString(self) -> str:
		if isinstance(self.type, LiteralsArgumentType):
			return f"({bytesToStr(b'|'.join(opt for opt in self.type.options))})"
		return f'<{self.name}: {self.typeName}>'


@dataclass
class FilterArgumentInfo(ArgumentSchema):
	multipleAllowed: bool = field(default=False, kw_only=True) # overrides multipleAllowedIfNegated field
	multipleAllowedIfNegated: bool = field(default=False, kw_only=True)
	isNegatable: bool = field(default=False, kw_only=True)
	canBeEmpty: bool = field(default=False, kw_only=True)
	defaultValue: Any = field(default=Nothing, kw_only=True)
	keySchema: CommandPartSchema = field(default=None, kw_only=True)

	def __post_init__(self):
		if self.keySchema is None:
			self.keySchema = KeywordSchema(self.name)
		if self.multipleAllowed and self.multipleAllowedIfNegated:
			warn("Both `multipleAllowed` and `multipleAllowedIfNegated` are set to True. This is probably not intentional.", RuntimeWarning, 3)
		if self.multipleAllowedIfNegated and not self.isNegatable:
			warn("`multipleAllowedIfNegated` is set to True, but `isNegatable` is False. This is probably not intentional.", RuntimeWarning, 3)


FALLBACK_FILTER_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
	description=''
)


@dataclass
class SwitchSchema(CommandPartSchema):
	options: Options = field(default_factory=list)
	next: Options = field(default_factory=list)
	isPotentiallyEmpty: bool = field(init=False)

	def finish(self):
		super().finish()
		if hasattr(self.options, '__iter__'):
			self.options = Options(self.options)
		else:
			self.options.finish()
		self.isPotentiallyEmpty = self.options.hasTerminal and isPotentiallyEmpty(self.next)

	@property
	def asString(self) -> str:
		options = '|'.join(opt.asString for opt in self.options.all)
		return f"({options})"


def isPotentiallyEmpty(options: Options) -> bool:
	if options.hasTerminal:
		return True
	for option in options.all:
		if option is TERMINAL:
			return True
		if isinstance(option, SwitchSchema) and option.isPotentiallyEmpty:
			return True


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
	opLevel: Union[int, str] = field(default=0)
	availableInSP: bool = field(default=True)
	availableInMP: bool = field(default=True)

	removed: bool = field(default=False)
	removedVersion: str = field(default=None)
	removedComment: str = field(default='')

	deprecated: bool = field(default=False)
	deprecatedVersion: Optional[str] = field(default=None)
	deprecatedComment: str = field(default='')

	next: Options = field(default_factory=list)

	@property
	def asString(self) -> str:
		return f"{self.name} {formatPossibilities(self.next.flattened)}"


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

	potentialNextSchemas: list[CommandPartSchema] = field(default_factory=list, init=False)

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
	span: Span = field(hash=False, compare=False)
	isTemplateCommand: bool

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


def getNextSchemas(before: CommandPart) -> Sequence[CommandPartSchema]:
	return before.potentialNextSchemas


__all__ = [
	'Options',
	'CommandPartSchema',
	'KeywordSchema',
	'ArgumentSchema',
	'FilterArgumentInfo',
	'FALLBACK_FILTER_ARGUMENT_INFO',
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
