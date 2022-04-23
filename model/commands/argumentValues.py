from dataclasses import dataclass
from typing import Optional

from Cat.utils.collections_ import OrderedMultiDict
from model.commands.command import ParsedArgument, CommandPart
from model.datapackContents import ResourceLocationNode
from model.nbt.tags import CompoundTag


@dataclass
class FilterArgument:
	key: CommandPart
	value: Optional[ParsedArgument]
	isNegated: bool


class FilterArguments(OrderedMultiDict[str, FilterArgument]):
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
