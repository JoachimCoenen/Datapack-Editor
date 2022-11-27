import os
from typing import Type

from base.model.project.project import ProjectAspect
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackPlugin', DatapackPlugin())


class DatapackPlugin(PluginBase):

	def initPlugin(self):
		from corePlugins.json.schemaStore import GLOBAL_SCHEMA_STORE
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		GLOBAL_SCHEMA_STORE.registerSchema('dpe:dependencies', os.path.join(resourcesDir, 'dependencies.json'))

	def projectAspects(self) -> list[Type[ProjectAspect]]:
		from corePlugins.datapack.aspect import DatapackAspect
		return [DatapackAspect]
