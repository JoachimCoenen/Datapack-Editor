import os

from . import providers

from base.model.parsing.tree import Schema
from base.plugin import PLUGIN_SERVICE, PluginBase


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

