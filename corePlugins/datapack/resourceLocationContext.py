from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Mapping, Collection, Optional

from base.model.project.project import Root
from .datapackContents import DatapackContents, RESOURCES, TAGS
from corePlugins.minecraft.resourceLocation import ResourceLocation, ResourceLocationNode, ResourceLocationContext, resourceLocationContext, MetaInfo
from base.model.utils import GeneralError
from corePlugins.minecraft_data.fullData import FullMCData


@dataclass
class SimpleResourceLocationContext1(ResourceLocationContext, ABC):
	_indexPath: Optional[str]
	_tagsIndexPath: Optional[str] = None

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		if self._tagsIndexPath is not None and (contents := dp.indexBundles.get(DatapackContents)) is not None:
			return (contents.resources.getIndex(self._tagsIndexPath),)
		else:
			return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		if self._indexPath is not None and (contents := dp.indexBundles.get(DatapackContents)) is not None:
			return (contents.resources.getIndex(self._indexPath),)
		else:
			return ()


@resourceLocationContext('advancement', _indexPath=RESOURCES.ADVANCEMENTS, _tagsIndexPath=None)
class AdvancementResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('function', _indexPath=RESOURCES.FUNCTIONS, _tagsIndexPath=TAGS.FUNCTION)
class FunctionResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('predicate', _indexPath=RESOURCES.PREDICATES, _tagsIndexPath=None)
class PredicateResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_table', _indexPath=RESOURCES.LOOT_TABLES, _tagsIndexPath=None)
class LootTableResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('recipe', _indexPath=RESOURCES.RECIPES, _tagsIndexPath=TAGS.RECIPE_TYPE)  # todo check whether TAGS.RECIPE_TYPE is correct OR RECIPE_TYPE means {coocking, shaped, shapeles, ...}
class RecipeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# others from minecraft registry:
@resourceLocationContext('attribute', _indexPath=None, _tagsIndexPath=TAGS.ATTRIBUTE)
class AttributeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('block_entity_type', _indexPath=None, _tagsIndexPath=TAGS.BLOCK_ENTITY_TYPE)
class BlockEntityTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('chunk_status', _indexPath=None, _tagsIndexPath=TAGS.CHUNK_STATUS)
class ChunkStatusResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('command_argument_type', _indexPath=None, _tagsIndexPath=TAGS.COMMAND_ARGUMENT_TYPE)
class CommandArgumentTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('dimension_type', _indexPath=RESOURCES.DIMENSION_TYPE, _tagsIndexPath=TAGS.DIMENSION_TYPE)  # todo change name to 'dimensionType'!!
class DimensionTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('position_source_type', _indexPath=None, _tagsIndexPath=TAGS.POSITION_SOURCE_TYPE)
class PositionSourceTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('menu', _indexPath=None, _tagsIndexPath=TAGS.MENU)
class MenuResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('particle_type', _indexPath=None, _tagsIndexPath=TAGS.PARTICLE_TYPE)
class ParticleTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('recipe_serializer', _indexPath=None, _tagsIndexPath=TAGS.RECIPE_SERIALIZER)
class RecipeSerializerResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('recipe_type', _indexPath=None, _tagsIndexPath=TAGS.RECIPE_TYPE)
class RecipeTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('sound_event', _indexPath=None, _tagsIndexPath=TAGS.SOUND_EVENT)
class SoundEventResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('stat_type', _indexPath=None, _tagsIndexPath=TAGS.STAT_TYPE)
class StatTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('custom_stat', _indexPath=None, _tagsIndexPath=TAGS.CUSTOM_STAT)
class CustomStatResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# Entity data registries
@resourceLocationContext('activity', _indexPath=None, _tagsIndexPath=TAGS.ACTIVITY)
class ActivityResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('memory_module_type', _indexPath=None, _tagsIndexPath=TAGS.MEMORY_MODULE_TYPE)
class MemoryModuleTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('schedule', _indexPath=None, _tagsIndexPath=TAGS.SCHEDULE)
class ScheduleResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('sensor_type', _indexPath=None, _tagsIndexPath=TAGS.SENSOR_TYPE)
class SensorTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('motive', _indexPath=None, _tagsIndexPath=TAGS.MOTIVE)
class MotiveResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('villager_profession', _indexPath=None, _tagsIndexPath=TAGS.VILLAGER_PROFESSION)
class VillagerProfessionResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('villager_type', _indexPath=None, _tagsIndexPath=TAGS.VILLAGER_TYPE)
class VillagerTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('point_of_interest_type', _indexPath=None, _tagsIndexPath=TAGS.POINT_OF_INTEREST_TYPE)
class PointOfInterestTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# Loot table serializer registries:
@resourceLocationContext('loot_condition_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_CONDITION_TYPE)
class LootConditionTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_function_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_FUNCTION_TYPE)
class LootFunctionTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_nbt_provider_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_NBT_PROVIDER_TYPE)
class LootNbtProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_number_provider_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_NUMBER_PROVIDER_TYPE)
class LootNumberProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_pool_entry_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_POOL_ENTRY_TYPE)
class LootPoolEntryTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('loot_score_provider_type', _indexPath=None, _tagsIndexPath=TAGS.LOOT_SCORE_PROVIDER_TYPE)
class LootScoreProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# Json file value provider registries:
@resourceLocationContext('float_provider_type', _indexPath=None, _tagsIndexPath=TAGS.FLOAT_PROVIDER_TYPE)
class FloatProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('int_provider_type', _indexPath=None, _tagsIndexPath=TAGS.INT_PROVIDER_TYPE)
class IntProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('height_provider_type', _indexPath=None, _tagsIndexPath=TAGS.HEIGHT_PROVIDER_TYPE)
class HeightProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# misc:
@resourceLocationContext('block_predicate_type', _indexPath=None, _tagsIndexPath=TAGS.BLOCK_PREDICATE_TYPE)
class BlockPredicateTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('rule_test', _indexPath=None, _tagsIndexPath=TAGS.RULE_TEST)
class RuleTestResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('pos_rule_test', _indexPath=None, _tagsIndexPath=TAGS.POS_RULE_TEST)
class PosRuleTestResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


# World generator registries:
@resourceLocationContext('worldgen/carver', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.CARVER)
class WorldgenCarverResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/configured_carver', _indexPath=RESOURCES.WORLDGEN.CONFIGURED_CARVER, _tagsIndexPath=TAGS.WORLDGEN.CONFIGURED_CARVER)
class WorldgenConfiguredCarverResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/feature', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.FEATURE)
class WorldgenFeatureResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/configured_feature', _indexPath=RESOURCES.WORLDGEN.CONFIGURED_FEATURE, _tagsIndexPath=TAGS.WORLDGEN.CONFIGURED_FEATURE)
class WorldgenConfiguredFeatureResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_set', _indexPath=RESOURCES.WORLDGEN.STRUCTURE_SET, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_SET)
class WorldgenStructureSetResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_processor', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_PROCESSOR)
class WorldgenStructureProcessorResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/processor_list', _indexPath=RESOURCES.WORLDGEN.PROCESSOR_LIST, _tagsIndexPath=TAGS.WORLDGEN.PROCESSOR_LIST)
class WorldgenProcessorListResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_pool_element', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_POOL_ELEMENT)
class WorldgenStructurePoolElementResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/template_pool', _indexPath=RESOURCES.WORLDGEN.TEMPLATE_POOL, _tagsIndexPath=TAGS.WORLDGEN.TEMPLATE_POOL)
class WorldgenTemplatePoolResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_piece', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_PIECE)
class WorldgenStructurePieceResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_TYPE)
class WorldgenStructureTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure', _indexPath=RESOURCES.WORLDGEN.STRUCTURE, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE)
@resourceLocationContext('structure', _indexPath=RESOURCES.WORLDGEN.STRUCTURE, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE)  # an old alias for worldgen/structure
class WorldgenStructureResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/structure_placement', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.STRUCTURE_PLACEMENT)
class WorldgenStructurePlacementResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/placement_modifier_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.PLACEMENT_MODIFIER_TYPE)
class WorldgenPlacementModifierTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/placed_feature', _indexPath=RESOURCES.WORLDGEN.PLACED_FEATURE, _tagsIndexPath=TAGS.WORLDGEN.PLACED_FEATURE)
class WorldgenPlacedFeatureResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/biome', _indexPath=RESOURCES.WORLDGEN.BIOME, _tagsIndexPath=TAGS.WORLDGEN.BIOME)
class WorldgenBiomeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/biome_source', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.BIOME_SOURCE)
class WorldgenBiomeSourceResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/noise', _indexPath=RESOURCES.WORLDGEN.NOISE, _tagsIndexPath=TAGS.WORLDGEN.NOISE)
class WorldgenNoiseResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/noise_settings', _indexPath=RESOURCES.WORLDGEN.NOISE_SETTINGS, _tagsIndexPath=TAGS.WORLDGEN.NOISE_SETTINGS)
class WorldgenNoiseSettingsResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/density_function', _indexPath=RESOURCES.WORLDGEN.DENSITY_FUNCTION, _tagsIndexPath=TAGS.WORLDGEN.DENSITY_FUNCTION)
class WorldgenDensityFunctionResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/density_function_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.DENSITY_FUNCTION_TYPE)
class WorldgenDensityFunctionTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/world_preset', _indexPath=RESOURCES.WORLDGEN.WORLD_PRESET, _tagsIndexPath=TAGS.WORLDGEN.WORLD_PRESET)
class WorldgenWorldPresetResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/flat_level_generator_preset', _indexPath=RESOURCES.WORLDGEN.FLAT_LEVEL_GENERATOR_PRESET, _tagsIndexPath=TAGS.WORLDGEN.FLAT_LEVEL_GENERATOR_PRESET)
class WorldgenFlatLevelGeneratorPresetResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/chunk_generator', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.CHUNK_GENERATOR)
class WorldgenChunkGeneratorResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/material_condition', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.MATERIAL_CONDITION)
class WorldgenMaterialConditionResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/material_rule', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.MATERIAL_RULE)
class WorldgenMaterialRuleResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/block_state_provider_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.BLOCK_STATE_PROVIDER_TYPE)
class WorldgenBlockStateProviderTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/foliage_placer_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.FOLIAGE_PLACER_TYPE)
class WorldgenFoliagePlacerTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/trunk_placer_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.TRUNK_PLACER_TYPE)
class WorldgenTrunkPlacerTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/tree_decorator_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.TREE_DECORATOR_TYPE)
class WorldgenTreeDecoratorTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('worldgen/feature_size_type', _indexPath=None, _tagsIndexPath=TAGS.WORLDGEN.FEATURE_SIZE_TYPE)
class WorldgenFeatureSizeTypeResourceLocationContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('block', _indexPath=None, _tagsIndexPath=TAGS.BLOCK)
class BlockContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.blocks


@resourceLocationContext('dimension', _indexPath=RESOURCES.DIMENSION, _tagsIndexPath=TAGS.DIMENSION)
class DimensionContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.dimensions


@resourceLocationContext('entity_type', _indexPath=None, _tagsIndexPath=TAGS.ENTITY_TYPE)
class EntityContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.entities


@resourceLocationContext('fluid', _indexPath=None, _tagsIndexPath=TAGS.FLUID)
class FluidContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.fluids


@resourceLocationContext('game_event', _indexPath=None, _tagsIndexPath=TAGS.GAME_EVENT)
class GameEventsContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.gameEvents


@resourceLocationContext('enchantment', _indexPath=None, _tagsIndexPath=TAGS.ENCHANTMENT)
class ItemEnchantmentContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.enchantments


@resourceLocationContext('item', _indexPath=None, _tagsIndexPath=TAGS.ITEM)
class ItemsContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.items


@resourceLocationContext('mob_effect', _indexPath=None, _tagsIndexPath=TAGS.MOB_EFFECT)
class MobEffectContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.effects


@resourceLocationContext('particle', _indexPath=None, _tagsIndexPath=TAGS.PARTICLE_TYPE)
class ParticleContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.particles


@resourceLocationContext('potion', _indexPath=None, _tagsIndexPath=TAGS.POTION)
class StructureContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.potions


@resourceLocationContext('condition', _indexPath=None, _tagsIndexPath=TAGS.LOOT_CONDITION_TYPE)
class ConditionIdContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.predicateConditions  # todo check if predicateConditions for LOOT_CONDITION_TYPE is correct


@resourceLocationContext('command_storage', _indexPath=None, _tagsIndexPath=None)
class CommandStorageContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


@resourceLocationContext('instrument', _indexPath=None, _tagsIndexPath=TAGS.INSTRUMENT)
class InstrumentContext(SimpleResourceLocationContext1):
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return mc.instruments


@resourceLocationContext('any', name='resource_location')
class AnyContext(ResourceLocationContext):

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)
