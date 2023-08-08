import os

from base.model.defaultSchemaProvider import SchemaMapping
from base.model.utils import LanguageId
from . import providers

from base.model.parsing.tree import Schema
from base.plugin import PLUGIN_SERVICE, PluginBase
from ..json import JSON_ID


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackSchemasPlugin', DatapackSchemasPlugin())


class DatapackSchemasPlugin(PluginBase):

	def initPlugin(self):
		from . import contexts

	def schemas(self) -> dict[str, Schema]:
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		return {
			**JSON_SCHEMA_LOADER.loadSchemaLibrary('minecraft:tags', os.path.join(resourcesDir, 'tags.json')),
			'minecraft:raw_json_text': JSON_SCHEMA_LOADER.loadSchema('minecraft:raw_json_text', os.path.join(resourcesDir, 'rawJsonText.json')),
			'minecraft:predicate': JSON_SCHEMA_LOADER.loadSchema('minecraft:predicate', os.path.join(resourcesDir, 'predicate.json')),
			'minecraft:recipe': JSON_SCHEMA_LOADER.loadSchema('minecraft:recipe', os.path.join(resourcesDir, 'recipe.json')),
			'minecraft:pack': JSON_SCHEMA_LOADER.loadSchema('minecraft:pack', os.path.join(resourcesDir, 'pack.json')),
		}

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
				schemaId='minecraft:advancements',
				pathFilter='data/*/advancements/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:item_modifiers',
				pathFilter='data/*/item_modifiers/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:loot_tables',
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

		return {JSON_ID: mappings}

