from typing import TypeVar, Generic, Type, overload

from Cat.Serializable import RegisterContainer, Serialized, SerializableContainer, Computed
from Cat.utils.collections import OrderedDict
from model.parsingUtils import Position, Span

TS = TypeVar('TS')
TT = TypeVar('TT')
TT2 = TypeVar('TT2')


@RegisterContainer
class NBTTag(SerializableContainer, Generic[TT]):
	__slots__ = ()
	span: Span = Serialized(default_factory=Span)
	data: TT = Computed(abstract=True)

	@overload
	def __init__(self):
		...

	@overload
	def __init__(self, data: TT, /):
		...

	@overload
	def __init__(self, data: TT, /, span: Span):
		...

	def __init__(self, data: TT = None, /, span: Span = None):
		super(NBTTag, self).__init__()
		if data is not None:
			self.data = data
		if span is not None:
			self.span = span

	@classmethod
	def create(cls: Type[TS], *, data: TT, **kwargs) -> TS:
		return super(NBTTag, cls).create(data=data, **kwargs)


TTag = TypeVar('TTag', bound=NBTTag)


@RegisterContainer
class BooleanTag(NBTTag[bool]):
	__slots__ = ()
	data: bool = Serialized(default=False)


@RegisterContainer
class NumberTag(NBTTag[TT], Generic[TT]):
	__slots__ = ()
	data: TT = Computed(abstract=True)


@RegisterContainer
class ByteTag(NBTTag[int]):
	__slots__ = ()
	data: int = Serialized(default=0)


@RegisterContainer
class ShortTag(NBTTag[int]):
	__slots__ = ()
	data: int = Serialized(default=0)


@RegisterContainer
class IntTag(NBTTag[int]):
	__slots__ = ()
	data: int = Serialized(default=0)


@RegisterContainer
class LongTag(NBTTag[int]):
	__slots__ = ()
	data: int = Serialized(default=0)


@RegisterContainer
class FloatTag(NBTTag[float]):
	__slots__ = ()
	data: float = Serialized(default=0.)


@RegisterContainer
class DoubleTag(NBTTag[float]):
	__slots__ = ()
	data: float = Serialized(default=0.)


@RegisterContainer
class StringTag(NBTTag[str]):
	__slots__ = ()
	data: str = Serialized(default='')


@RegisterContainer
class ListTag(NBTTag[list[NBTTag]]):
	__slots__ = ()
	data: list[NBTTag] = Serialized(default_factory=list[NBTTag])


@RegisterContainer
class CompoundTag(NBTTag[OrderedDict[str, NBTTag]]):
	__slots__ = ()
	data: OrderedDict[str, NBTTag] = Serialized(default_factory=OrderedDict[str, NBTTag])


@RegisterContainer
class ArrayTag(NBTTag[list[TT2]], Generic[TT2]):
	__slots__ = ()
	data: list[TT2] = Serialized(abstract=True)


@RegisterContainer
class ByteArrayTag(ArrayTag[ByteTag]):
	__slots__ = ()
	data: list[ByteTag] = Serialized(default_factory=list[ByteTag])


@RegisterContainer
class IntArrayTag(ArrayTag[IntTag]):
	__slots__ = ()
	data: list[IntTag] = Serialized(default_factory=list[IntTag])


@RegisterContainer
class LongArrayTag(ArrayTag[LongTag]):
	__slots__ = ()
	data: list[LongTag] = Serialized(default_factory=list[LongTag])


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