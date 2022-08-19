from dataclasses import dataclass
from typing import TypeVar, Generic, ClassVar, Optional, Collection

from Cat.utils.collections_ import OrderedDict
from model.parsing.tree import Node, Schema
from model.utils import LanguageId

_TS = TypeVar('_TS')
_TT = TypeVar('_TT')
_TT2 = TypeVar('_TT2')


class NBTTagSchema(Schema):
	def asString(self) -> str:
		return 'NBTTagSchema'
	language: ClassVar[LanguageId] = 'SNBT'


@dataclass
class NBTTag(Node['NBTTag', NBTTagSchema], Generic[_TT]):
	typeName: ClassVar[str] = 'nbt_tag'
	data: _TT

	language: ClassVar[LanguageId] = 'SNBT'


@dataclass
class InvalidTag(NBTTag[bytes]):
	typeName: ClassVar[str] = 'invalid_tag'
	data: bytes

	@property
	def children(self) -> Collection[NBTTag]:
		return ()


TTag = TypeVar('TTag', bound=NBTTag)


@dataclass
class BasicDataTag(NBTTag[_TT], Generic[_TT]):
	typeName: ClassVar[str] = 'basic_data_tag'
	data: _TT
	raw: bytes
	"""The raw value as read from the bytes, without any parsing, etc"""

	@property
	def children(self) -> Collection[NBTTag]:
		return ()


@dataclass
class BooleanTag(BasicDataTag[bool]):
	typeName: ClassVar[str] = 'boolean_tag'
	data: bool


@dataclass
class NumberTag(BasicDataTag[_TT], Generic[_TT]):
	# typeName: ClassVar[str] = 'number_tag'
	pass  # data: _TT


@dataclass
class ByteTag(NumberTag[int]):
	typeName: ClassVar[str] = 'byte_tag'
	data: int


@dataclass
class ShortTag(NumberTag[int]):
	typeName: ClassVar[str] = 'short_tag'
	data: int


@dataclass
class IntTag(NumberTag[int]):
	typeName: ClassVar[str] = 'int_tag'
	data: int


@dataclass
class LongTag(NumberTag[int]):
	typeName: ClassVar[str] = 'long_tag'
	data: int


@dataclass
class FloatTag(NumberTag[float]):
	typeName: ClassVar[str] = 'float_tag'
	data: float


@dataclass
class DoubleTag(NumberTag[float]):
	typeName: ClassVar[str] = 'double_tag'
	data: float


@dataclass
class StringTag(BasicDataTag[str]):
	typeName: ClassVar[str] = 'string_tag'
	data: str
	parsedValue: Optional[Node] = None


@dataclass
class ListTag(NBTTag[list[NBTTag]]):
	typeName: ClassVar[str] = 'list_tag'
	data: list[NBTTag]

	@property
	def children(self) -> Collection[NBTTag]:
		return self.data


@dataclass
class NBTProperty(NBTTag[tuple[StringTag, NBTTag]]):
	typeName: ClassVar[str] = 'property'
	data: tuple[StringTag, NBTTag]

	@property
	def key(self) -> StringTag:
		return self.data[0]

	@property
	def value(self) -> NBTTag:
		return self.data[1]

	@property
	def children(self) -> Collection[NBTTag]:
		return self.data


@dataclass
class CompoundTag(NBTTag[OrderedDict[bytes, NBTProperty]]):
	typeName: ClassVar[str] = 'compound_tag'
	data: OrderedDict[bytes, NBTTag]

	@property
	def children(self) -> Collection[NBTTag]:
		return self.data.values()


@dataclass
class ArrayTag(NBTTag[list[_TT2]], Generic[_TT2]):
	# typeName: ClassVar[str] = 'array_tag'
	data: list[_TT2]

	@property
	def children(self) -> Collection[NBTTag]:
		return self.data


@dataclass
class ByteArrayTag(ArrayTag[ByteTag]):
	typeName: ClassVar[str] = 'byte_array_tag'
	data: list[ByteTag]


@dataclass
class IntArrayTag(ArrayTag[IntTag]):
	typeName: ClassVar[str] = 'int_array_tag'
	data: list[IntTag]


@dataclass
class LongArrayTag(ArrayTag[LongTag]):
	typeName: ClassVar[str] = 'long_array_tag'
	data: list[LongTag]


__all__ = [
	'NBTTagSchema',
	'NBTTag',
	'InvalidTag',
	'BasicDataTag',
	'BooleanTag',
	'NumberTag',
	'ByteTag',
	'ShortTag',
	'IntTag',
	'LongTag',
	'FloatTag',
	'DoubleTag',
	'StringTag',
	'ListTag',
	'NBTProperty',
	'CompoundTag',
	'ArrayTag',
	'ByteArrayTag',
	'IntArrayTag',
	'LongArrayTag',
]
