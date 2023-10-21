from __future__ import annotations
from typing import Mapping, Collection

from base.model.project.project import Root
from .datapackContents import DatapackContents
from corePlugins.minecraft.resourceLocation import ResourceLocation, ResourceLocationNode, ResourceLocationContext, resourceLocationContext, MetaInfo
from base.model.utils import GeneralError
from corePlugins.minecraft_data.fullData import FullMCData


@resourceLocationContext('advancement', allowTags=False)
class AdvancementContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'advancement'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.advancements,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('block', allowTags=False)
@resourceLocationContext('block_type', allowTags=True)
@resourceLocationContext('block_tag', allowTags=True, onlyTags=True)
class BlockContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'block'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.blocks,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.blocks


@resourceLocationContext('dimension', allowTags=False)
class DimensionContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'dimension'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.dimension,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.dimensions


@resourceLocationContext('entity_summon', allowTags=False)
@resourceLocationContext('entity_type', allowTags=True)
class EntityContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'entity'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.entity_types,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.entities


# EntitySummonContext, EntityTypeContext, EntityTypeLikeContext


@resourceLocationContext('fluid', allowTags=False)
@resourceLocationContext('fluid_type', allowTags=True)
class FluidContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'fluid'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.fluids,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.fluids


@resourceLocationContext('function', allowTags=False)
@resourceLocationContext('function_type', allowTags=True)
@resourceLocationContext('function_tag', allowTags=True, onlyTags=True)
class FunctionContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'function'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.functions,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.functions,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('game_event', allowTags=True)
class GameEventsContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'game_event'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.game_events,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.gameEvents


@resourceLocationContext('enchantment', allowTags=False)
class ItemEnchantmentContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'enchantment'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.enchantments


@resourceLocationContext('item', allowTags=False)
@resourceLocationContext('item_type', allowTags=True)
@resourceLocationContext('item_tag', allowTags=True, onlyTags=True)
class ItemsContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'item'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.items,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.items


@resourceLocationContext('mob_effect', allowTags=False)
class MobEffectContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'mob_effect'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.effects


@resourceLocationContext('particle', allowTags=False)
class ParticleContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'particle'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.particles


@resourceLocationContext('predicate', allowTags=False)
class PredicateContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'predicate'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.predicates,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('potion', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'potion'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.potions


@resourceLocationContext('biome', allowTags=False)
class BiomeIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'biome'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.biomes


@resourceLocationContext('structure', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'structure'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.structures


@resourceLocationContext('condition', allowTags=False)
class ConditionIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'condition'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.predicateConditions


@resourceLocationContext('command_storage', allowTags=False)
class CommandStorageContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'command_storage'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


@resourceLocationContext('loot_table', allowTags=False)
class LootTableContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'loot_table'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.loot_tables,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('instrument', allowTags=False)
class InstrumentContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'instrument'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.instruments,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.instruments


@resourceLocationContext('recipe', allowTags=False)
class InstrumentContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'recipe'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.recipes,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.recipes,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('any_no_tag', allowTags=False)
@resourceLocationContext('any', allowTags=True)
class AnyContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'resource_location'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


__all__ = [
	'BlockContext',
	'DimensionContext',
	'EntityContext',
	'FluidContext',
	'FunctionContext',
	'ItemEnchantmentContext',
	'ItemsContext',
	'MobEffectContext',
	'ParticleContext',
	'PredicateContext',
	'BiomeIdContext',
	'AnyContext',
]
