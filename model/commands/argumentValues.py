from dataclasses import dataclass
from typing import NamedTuple, Optional, Any

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from Cat.utils.collections import OrderedDict, OrderedMultiDict
from model.commands.parsedCommands import ParsedArgument
from model.datapackContents import ResourceLocation
from model.nbt.tags import CompoundTag


@RegisterContainer
class BlockState(SerializableContainer):
	__slots__ = ()
	blockId: ResourceLocation = Serialized(default=ResourceLocation(None, 'INVALID', False))
	states: OrderedDict[str, str] = Serialized(default_factory=OrderedDict[str, str])
	nbt: Optional[CompoundTag] = Serialized(default=None)

	@classmethod
	def create(cls, *, blockId: ResourceLocation, states: OrderedDict[str, str], nbt: Optional[CompoundTag]):
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
	arguments: OrderedMultiDict[str, ParsedArgument] = Serialized(default_factory=OrderedMultiDict[str, ParsedArgument])

	@classmethod
	def create(cls, *, variable: ResourceLocation, arguments: OrderedMultiDict[str, Any]):
		return super(TargetSelector, cls).create(variable=variable, arguments=arguments)
