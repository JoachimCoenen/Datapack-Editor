from typing import Optional

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from Cat.utils.collections_ import OrderedMultiDict
from model.commands.parsedCommands import ParsedArgument, ParsedNode
from model.datapackContents import ResourceLocation
from model.nbt.tags import CompoundTag


@RegisterContainer
class FilterArgument(SerializableContainer):
	__slots__ = ()
	key: ParsedNode = Serialized(default_factory=ParsedNode)
	value: Optional[ParsedArgument] = Serialized(default=None)
	isNegated: bool = Serialized(default=False)

	@classmethod
	def create(cls, *, key: ParsedNode, value: Optional[ParsedArgument], isNegated: bool):
		return super(FilterArgument, cls).create(key=key, value=value, isNegated=isNegated)


class FilterArguments(OrderedMultiDict[str, FilterArgument]):
	__slots__ = ()


@RegisterContainer
class BlockState(SerializableContainer):
	__slots__ = ()
	blockId: ResourceLocation = Serialized(default=ResourceLocation(None, 'INVALID', False))
	states: FilterArguments = Serialized(default_factory=FilterArguments)
	nbt: Optional[CompoundTag] = Serialized(default=None)

	@classmethod
	def create(cls, *, blockId: ResourceLocation, states: FilterArguments, nbt: Optional[CompoundTag]):
		return super(BlockState, cls).create(blockId=blockId, states=states, nbt=nbt)


@RegisterContainer
class ItemStack(SerializableContainer):
	__slots__ = ()
	itemId: ResourceLocation = Serialized(default=ResourceLocation(None, 'INVALID', False))
	nbt: Optional[CompoundTag] = Serialized(default=None)

	@classmethod
	def create(cls, *, itemId: ResourceLocation, nbt: Optional[CompoundTag]):
		return super(ItemStack, cls).create(itemId=itemId, nbt=nbt)


@RegisterContainer
class TargetSelector(SerializableContainer):
	__slots__ = ()
	variable: str = Serialized(default='')
	arguments: FilterArguments = Serialized(default_factory=FilterArguments)

	@classmethod
	def create(cls, *, variable: str, arguments: OrderedMultiDict[str, ParsedArgument]):
		return super(TargetSelector, cls).create(variable=variable, arguments=arguments)

