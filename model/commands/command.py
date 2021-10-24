from __future__ import annotations
from typing import TypeVar, Type, Union, Optional, Sequence

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, Computed, SerializedPropertyBaseBase
from Cat.Serializable.utils import parseSimpleValue
from Cat.utils import Singleton, abstract
from model.commands.argumentTypes import ArgumentType, BRIGADIER_STRING, LiteralsArgumentType

TS = TypeVar('TS')
TT = TypeVar('TT')


@RegisterContainer
class CommandNode(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	description: str = Serialized(default='')
	next: Sequence[CommandNode] = Serialized(default_factory=lambda: list[CommandNode]())

	@abstract
	def asCodeString(self) -> str:
		...


@RegisterContainer
class Keyword(CommandNode):
	__slots__ = ()

	def __init__(self, name: Optional[str] = None):
		if name is not None:
			self.name: str = name

	def asCodeString(self) -> str:
		return f'{self.name}'


@RegisterContainer
class LiteralsInfo(CommandNode):
	__slots__ = ()
	options: list[str] = Serialized(default_factory=list[str])
	next: Sequence[CommandNode] = Serialized(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		options = '|'.join(self.options)
		return f"({options})"


@RegisterContainer
class ArgumentInfo(CommandNode):
	__slots__ = ()
	type: ArgumentType = Serialized(default=BRIGADIER_STRING)
	typeName: str = Computed(getInitValue=type.name)
	subType: Optional[ArgumentType] = Serialized(default=None)
	args: Optional[dict[str, Union[str, int, float, None]]] = Serialized(default=None)
	next: Sequence[CommandNode] = Serialized(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		if isinstance(self.type, LiteralsArgumentType):
			return f"({'|'.join(opt for opt in self.type.options)})"
		return f'<{self.name}: {self.typeName}>'


@RegisterContainer
class Switch(CommandNode):
	__slots__ = ()
	options: list[Union[Keyword, Terminal]] = Serialized(default_factory=list[Keyword])
	next: Sequence[CommandNode] = Serialized(default_factory=lambda: list[CommandNode]())

	def asCodeString(self) -> str:
		options = '|'.join(opt.asCodeString() for opt in self.options)
		return f"({options})"


@RegisterContainer
class Terminal(Singleton, CommandNode):
	__slots__ = ()


TERMINAL = Terminal()


@RegisterContainer
class CommandsRoot(Singleton, CommandNode):
	__slots__ = ()

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

@RegisterContainer
class CommandInfo(CommandNode):
	__slots__ = ()
	command: str = Serialized(default='')
	name: str = Computed(getInitValue=command)
	description: str = Serialized(default='')
	opLevel: Union[int, str] = Serialized(default=0)
	availableInSP: bool = Serialized(default=True)
	availableInMP: bool = Serialized(default=True)

	removed: bool = Serialized(default=False)
	removedVersion: str = Serialized(default=None, doc="""the version this command was removed, if it has been removed else""")
	removedComment: str = Serialized(default='')

	deprecated: bool = Serialized(default=False)
	deprecatedVersion: str = Serialized(default=None, doc="""the version this command was deprecated, if it has been deprecated""")
	deprecatedComment: str = Serialized(default='')

	argument: list[CommandNode] = Serialized(default_factory=list[CommandNode])
	next: Sequence[CommandNode] = Computed(getInitValue=argument)

	def asCodeString(self) -> str:
		return f"{self.name} {formatPossibilities(self.argument)}"




TContainer = TypeVar('TContainer', bound=SerializableContainer)


def getSerializedPropertiesDict(cls) -> dict[str, SerializedPropertyBaseBase]:
	properties = cls._SerializableContainerBase__serializedPropertiesDictCache.get(cls, None)
	if properties is None:
		properties = dict((p.__name__, p) for p in cls.getSerializedProperties())
		cls._SerializableContainerBase__serializedPropertiesDictCache[cls] = properties
	return properties


def loadFromCSV(cls: Type[TContainer], data: str, separator: str = ';') -> list[TContainer]:
	splitLines = data.splitlines(keepends=False)
	rows = iter(splitLines)
	header = next(rows)
	columnNames = [name.strip() for name in header.split(separator)]
	props: dict[str, SerializedPropertyBaseBase] = getSerializedPropertiesDict(cls)
	result = []
	for i, row in enumerate(rows):
		if not row.strip():
			continue

		bo = cls()

		values = row.split(separator)
		#assert len(values) == len(columnNames)

		for columnName, value in zip(columnNames, values):
			if columnName not in props:
				continue
			value = value.strip()
			value = value.replace('unKnown', 'None')
			value = parseSimpleValue(value, props[columnName].typeHint_)
			setattr(bo, columnName, value)
		result.append(bo)

	return result








