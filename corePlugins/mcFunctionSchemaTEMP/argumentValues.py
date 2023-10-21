from dataclasses import dataclass
from typing import Optional

from cat.utils.collections_ import OrderedMultiDict
from corePlugins.minecraft.resourceLocation import ResourceLocationNode
from corePlugins.mcFunction.command import ParsedArgument, CommandPart
from corePlugins.nbt.tags import CompoundTag


@dataclass
class FilterArgument:
	key: CommandPart
	value: Optional[ParsedArgument]
	isNegated: bool


class FilterArguments(OrderedMultiDict[bytes, FilterArgument]):
	__slots__ = ()


@dataclass
class BlockState:
	blockId: ResourceLocationNode
	states: FilterArguments
	nbt: Optional[CompoundTag]


@dataclass
class ItemStack:
	itemId: ResourceLocationNode
	nbt: Optional[CompoundTag]


@dataclass
class TargetSelector:
	variable: str
	arguments: FilterArguments
