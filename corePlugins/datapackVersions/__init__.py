from base.model.defaultSchemaProvider import SchemaMapping
from base.model.utils import LanguageId
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackVersionsPlugin', DatapackVersionsPlugin())


class DatapackVersionsPlugin(PluginBase):

	def initPlugin(self):
		from . import providers  # loads all resource location contexts
		from . import contexts  # loads all resource location contexts
		from . import version7
		version7.initVersion()

	def dependencies(self) -> set[str]:
		return {'DatapackPlugin', 'JsonPlugin', 'NbtPlugin', 'DatapackPlugin', 'MinecraftPlugin'}

	def schemaMappings(self) -> dict[LanguageId, list[SchemaMapping]]:
		mappings = [
			SchemaMapping(
				schemaId='minecraft:pack',
				pathFilter='/pack.mcmeta',
			),
			# TagInfos:
			SchemaMapping(
				schemaId='minecraft:tags/block_type',
				pathFilter='data/*/tags/blocks/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/entity_type',
				pathFilter='data/*/tags/entity_types/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/fluid_type',
				pathFilter='data/*/tags/fluids/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/function',
				pathFilter='data/*/tags/functions/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/game_event',
				pathFilter='data/*/tags/game_events/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/item_type',
				pathFilter='data/*/tags/items/**.json',
			),

			# WorldGenInfos:
			SchemaMapping(
				schemaId='minecraft:worldgen/biome',
				pathFilter='data/*/worldgen/biome/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/configured_carver',
				pathFilter='data/*/worldgen/configured_carver/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/configured_feature',
				pathFilter='data/*/worldgen/configured_feature/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/configured_structure_feature',
				pathFilter='data/*/worldgen/configured_structure_feature/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/configured_surface_builder',
				pathFilter='data/*/worldgen/configured_surface_builder/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/noise_settings',
				pathFilter='data/*/worldgen/noise_settings/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/processor_list',
				pathFilter='data/*/worldgen/processor_list/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:worldgen/template_pool',
				pathFilter='data/*/worldgen/template_pool/**.json',
			),

			# DatapackContents:
			SchemaMapping(
				schemaId='minecraft:advancement',
				pathFilter='data/*/advancements/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:item_modifier',
				pathFilter='data/*/item_modifiers/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:loot_table',
				pathFilter='data/*/loot_tables/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:predicate',
				pathFilter='data/*/predicates/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:recipe',
				pathFilter='data/*/recipes/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:dimension',
				pathFilter='data/*/dimension/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:dimension_type',
				pathFilter='data/*/dimension_type/**.json',
			),
		]

		from corePlugins.json import JSON_ID
		return {JSON_ID: mappings}
