from typing import Type

from base.model.applicationSettings import SettingsAspect
from base.model.parsing.tree import Schema
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('McFunctionSchemasTEMPPlugin', McFunctionSchemasTEMPPlugin())


class McFunctionSchemasTEMPPlugin(PluginBase):

	def initPlugin(self):
		from corePlugins.mcFunctionSchemaTEMP.mcVersions import getMCVersion
		from .version1_17 import initPlugin as initPlugin_1_17
		from .version1_16 import initPlugin as initPlugin_1_16
		from .version1_18 import initPlugin as initPlugin_1_18
		initPlugin_1_17()
		initPlugin_1_16()
		initPlugin_1_18()

		from .argumentContextsImpl import initPlugin as initArgumentContexts
		initArgumentContexts()

	def settingsAspects(self) -> list[Type[SettingsAspect]]:
		from corePlugins.mcFunctionSchemaTEMP.settings import MinecraftSettings
		return [MinecraftSettings]

	def schemas(self) -> dict[str, Schema]:
		schemas = {}

		from .v1_17_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_17
		from .v1_18_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_18

		schemas |= buildMCFunctionSchemas_1_17()
		schemas |= buildMCFunctionSchemas_1_18()
		return schemas
