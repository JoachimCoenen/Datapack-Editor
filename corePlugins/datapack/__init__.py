import os
from typing import Type

from base.model.project.project import ProjectAspect
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackPlugin', DatapackPlugin())


class DatapackPlugin(PluginBase):

	def initPlugin(self):
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		JSON_SCHEMA_LOADER.registerSchema('dpe:dependencies', os.path.join(resourcesDir, 'dependencies.json'))

	def projectAspects(self) -> list[Type[ProjectAspect]]:
		from corePlugins.datapack.aspect import DatapackAspect
		return [DatapackAspect]
