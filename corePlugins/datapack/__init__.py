import os
from typing import Type

from base.model.applicationSettings import SettingsAspect
from base.model.defaultSchemaProvider import SchemaMapping
from base.model.parsing.tree import Schema
from base.model.project.project import ProjectAspect
from base.model.utils import LanguageId
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackPlugin', DatapackPlugin())


class DatapackPlugin(PluginBase):

	def initPlugin(self):
		from . import resourceLocationContext  # loads all resource location contexts

	def projectAspects(self) -> list[Type[ProjectAspect]]:
		from corePlugins.datapack.aspect import DatapackAspect
		return [DatapackAspect]

	def settingsAspects(self) -> list[Type[SettingsAspect]]:
		from corePlugins.datapack.aspect import DatapackSettings
		return [DatapackSettings]

	def schemas(self) -> dict[str, Schema]:
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		schemaPath = os.path.join(resourcesDir, 'dependencies.json')
		return {'dpe:dependencies': JSON_SCHEMA_LOADER.loadSchema('dpe:dependencies', schemaPath)}

	def schemaMappings(self) -> dict[LanguageId, list[SchemaMapping]]:
		mappings = [
			SchemaMapping(
				schemaId='dpe:dependencies',
				pathFilter='/dependencies.json',
			),
		]

		from corePlugins.json import JSON_ID
		return {JSON_ID: mappings}

