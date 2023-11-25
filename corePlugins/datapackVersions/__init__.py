from base.model.defaultSchemaProvider import SchemaMapping
from base.model.parsing.tree import Schema
from base.model.utils import LanguageId
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackVersionsPlugin', DatapackVersionsPlugin())


class DatapackVersionsPlugin(PluginBase):

	def initPlugin(self):
		from . import providers
		from . import contexts
		from . import version23
		version23.initVersion()
		from .commands import argumentContextsImpl
		from .commands import argumentStylers

	def dependencies(self) -> set[str]:
		return {'DatapackPlugin', 'JsonPlugin', 'NbtPlugin', 'DatapackPlugin', 'MinecraftPlugin', 'McFunctionPlugin'}

	def schemaMappings(self) -> dict[LanguageId, list[SchemaMapping]]:
		from corePlugins.datapackVersions.allVersions import REGISTRY_TAGS, WORLDGEN
		mappings = [
			SchemaMapping(
				schemaId='minecraft:pack',
				pathFilter='/pack.mcmeta',
			),
			# TagInfos:
			*[
				SchemaMapping(
					schemaId=f'minecraft:{indexPath}',
					pathFilter=f'data/*/{folder}/**.json',
				)
				for indexPath, folder in REGISTRY_TAGS.items()
			],
			SchemaMapping(
				schemaId='minecraft:tags/function',
				pathFilter='data/*/tags/functions/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/chat_type',
				pathFilter='data/*/tags/chat_type/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/damage_type',
				pathFilter='data/*/tags/damage_type/**.json',
			),
			SchemaMapping(
				schemaId='minecraft:tags/instrument',
				pathFilter='data/*/tags/instrument/**.json',
			),

			# WorldGenInfos:
			*[
				SchemaMapping(
					schemaId=f'minecraft:{indexPath}',
					pathFilter=f'data/*/{folder}/**.json',
				)
				for indexPath, folder in WORLDGEN.items()
			],

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

	def schemas(self) -> dict[str, Schema]:
		schemas = {}

		from corePlugins.datapackVersions.commands.v1_20_2_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_20_2
		from corePlugins.datapackVersions.commands.v1_20_3_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_20_3

		schemas |= buildMCFunctionSchemas_1_20_2()  # legacy way of doing it.
		schemas |= buildMCFunctionSchemas_1_20_3()  # legacy way of doing it.
		return schemas

