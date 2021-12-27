from dataclasses import dataclass, field
from typing import TypeVar, Generic

from Cat.utils.collections_ import OrderedDict
from model.parsingUtils import Span

TS = TypeVar('TS')
TT = TypeVar('TT')
TT2 = TypeVar('TT2')


@dataclass
class NBTTag(Generic[TT]):
	data: TT
	span: Span = field(default_factory=Span)


TTag = TypeVar('TTag', bound=NBTTag)


class BooleanTag(NBTTag[bool]):
	pass  # data: bool


class NumberTag(NBTTag[TT], Generic[TT]):
	pass  # data: TT


class ByteTag(NumberTag[int]):
	pass  # data: int


class ShortTag(NumberTag[int]):
	pass  # data: int


class IntTag(NumberTag[int]):
	pass  # data: int


class LongTag(NumberTag[int]):
	pass  # data: int


class FloatTag(NumberTag[float]):
	pass  # data: float


class DoubleTag(NumberTag[float]):
	pass  # data: float


class StringTag(NBTTag[str]):
	pass  # data: str


class ListTag(NBTTag[list[NBTTag]]):
	pass  # data: list[NBTTag]


class CompoundTag(NBTTag[OrderedDict[str, NBTTag]]):
	pass  # data: OrderedDict[str, NBTTag]


class ArrayTag(NBTTag[list[TT2]], Generic[TT2]):
	pass  # data: list[TT2]


class ByteArrayTag(ArrayTag[ByteTag]):
	pass  # data: list[ByteTag]


class IntArrayTag(ArrayTag[IntTag]):
	pass  # data: list[IntTag]


class LongArrayTag(ArrayTag[LongTag]):
	pass  # data: list[LongTag]


__all__ = [
	'NBTTag',
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
	'CompoundTag',
	'ArrayTag',
	'ByteArrayTag',
	'IntArrayTag',
	'LongArrayTag',
]