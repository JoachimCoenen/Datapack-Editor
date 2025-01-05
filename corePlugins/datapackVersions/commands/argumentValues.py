from dataclasses import dataclass
from typing import Optional, Collection, Literal

from base.model.parsing.tree import Node
from corePlugins.datapackVersions.commands.predicateArgs import PredicateArgs
from corePlugins.mcFunction.filterArgs import FilterArguments
from corePlugins.minecraft.resourceLocation import ResourceLocationNode
from corePlugins.nbt.tags import CompoundTag, NBTNode


@dataclass
class BlockState:
	blockId: ResourceLocationNode
	states: FilterArguments
	nbt: Optional[CompoundTag]

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.blockId, self.states, self.nbt


@dataclass
class ItemStack:
	itemId: ResourceLocationNode | Literal['*']
	nbt: Optional[CompoundTag]
	components: PredicateArgs

	def getForeignNodes(self) -> Collection[Node | None]:
		if self.itemId == '*':
			return self.nbt, self.components
		else:
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


@dataclass
class Particle:
	particleId: ResourceLocationNode
	configurationTags: Optional[CompoundTag]

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.particleId, self.configurationTags


@dataclass
class ResourceLocationOrInlineNBT:
	resLoc: Optional[ResourceLocationNode]
	nbt: Optional[NBTNode]

	def getForeignNodes(self) -> Collection[Node | None]:
		return self.resLoc, self.nbt
