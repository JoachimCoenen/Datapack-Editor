from dataclasses import dataclass
from typing import Optional

from Cat.utils.collections_ import OrderedMultiDict
from model.commands.parsedCommands import ParsedArgument, ParsedNode
from model.datapackContents import ResourceLocation
from model.nbt.tags import CompoundTag


@dataclass
class FilterArgument:
	key: ParsedNode
	value: Optional[ParsedArgument]
	isNegated: bool


class FilterArguments(OrderedMultiDict[str, FilterArgument]):
	__slots__ = ()


@dataclass
class BlockState:
	blockId: ResourceLocation
	states: FilterArguments
	nbt: Optional[CompoundTag]


@dataclass
class ItemStack:
	itemId: ResourceLocation
	nbt: Optional[CompoundTag]


@dataclass
class TargetSelector:
	variable: str
	arguments: FilterArguments
