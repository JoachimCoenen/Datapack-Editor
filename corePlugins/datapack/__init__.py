import os
from typing import Type

from base.model.applicationSettings import SettingsAspect
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.tree import Schema, Node
from base.model.project.project import ProjectAspect
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackPlugin', DatapackPlugin())


class DatapackPlugin(PluginBase):

	def initPlugin(self):
		pass

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from corePlugins.datapack.resourceLocationContext import ResourceLocationCtxProvider
		from corePlugins.datapack.datapackContents import ResourceLocationNode
		return {
			ResourceLocationNode: ResourceLocationCtxProvider
		}

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

