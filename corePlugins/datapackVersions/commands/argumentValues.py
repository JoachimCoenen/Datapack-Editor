from dataclasses import dataclass
from typing import Optional, Collection

from base.model.parsing.tree import Node
from corePlugins.mcFunction.filterArgs import FilterArguments
from corePlugins.minecraft.resourceLocation import ResourceLocationNode
from corePlugins.nbt.tags import CompoundTag


@dataclass
class BlockState:
	blockId: ResourceLocationNode
	states: FilterArguments
	nbt: Optional[CompoundTag]

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.blockId, self.states, self.nbt


@dataclass
class ItemStack:
	itemId: ResourceLocationNode
	nbt: Optional[CompoundTag]
	components: FilterArguments

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.itemId, self.nbt, self.components


@dataclass
class ItemSlot:
	slotType: str
	slotNumber: Optional[str]


@dataclass
class TargetSelector:
	variable: str
	arguments: FilterArguments

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.arguments,
