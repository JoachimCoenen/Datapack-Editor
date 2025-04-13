from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from corePlugins.nbtJsonBase.core import StructureDataNode, InvalidNode, BooleanNode, NumberNode, StringNode, \
	ListLikeNode, StructureProperty, ObjectNode, StructureSchema


@dataclass
class NBTNode(Node['NBTNode', StructureSchema], ABC):
	language: ClassVar[LanguageId] = LanguageId('SNBT')


@dataclass
class InvalidTag(NBTNode, InvalidNode):
	pass


@dataclass
class BooleanTag(NBTNode, BooleanNode):
	pass


@dataclass
class NumberTag[T: int | float](NBTNode, NumberNode[T]):
	# typeName: ClassVar[str] = 'number_tag'
	pass  # data: T


@dataclass
class ByteTag(NumberTag[int]):
	data: int


@dataclass
class ShortTag(NumberTag[int]):
	data: int


@dataclass
class IntTag(NumberTag[int]):
	data: int


@dataclass
class LongTag(NumberTag[int]):
	data: int


@dataclass
class FloatTag(NumberTag[float]):
	data: float


@dataclass
class DoubleTag(NumberTag[float]):
	data: float


@dataclass
class StringTag(NBTNode, StringNode):
	pass


@dataclass
class ListTag(NBTNode, ListLikeNode[StructureDataNode]):
	pass


@dataclass
class NBTProperty(NBTNode, StructureProperty):
	pass


@dataclass
class CompoundTag(NBTNode, ObjectNode):
	pass


@dataclass
class ArrayTag[T2: StructureDataNode](NBTNode, ListLikeNode[T2]):
	data: list[T2]


@dataclass
class ByteArrayTag(ArrayTag[ByteTag]):
	arrayTypeTag: ClassVar[bytes] = b'B'
	data: list[ByteTag]


@dataclass
class IntArrayTag(ArrayTag[IntTag]):
	arrayTypeTag: ClassVar[bytes] = b'I'
	data: list[IntTag]


@dataclass
class LongArrayTag(ArrayTag[LongTag]):
	arrayTypeTag: ClassVar[bytes] = b'L'
	data: list[LongTag]


__all__ = [
	'NBTNode',
	'InvalidTag',
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
