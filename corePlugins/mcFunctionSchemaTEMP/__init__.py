from typing import Type

from base.model.applicationSettings import SettingsAspect
from base.model.parsing.tree import Schema
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('McFunctionSchemasTEMPPlugin', McFunctionSchemasTEMPPlugin())


class McFunctionSchemasTEMPPlugin(PluginBase):

	def initPlugin(self):

		from .argumentContextsImpl import initPlugin as initArgumentContexts
		initArgumentContexts()

		from .argumentStylers import initPlugin as initArgumentStylers
		initArgumentStylers()

	def dependencies(self) -> set[str]:
		return {'McFunctionPlugin', 'MinecraftPlugin', 'NbtPlugin'}

	def schemas(self) -> dict[str, Schema]:
		schemas = {}

		from .v1_17_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_17
		from .v1_18_schema import buildMCFunctionSchemas as buildMCFunctionSchemas_1_18

		schemas |= buildMCFunctionSchemas_1_17()
		schemas |= buildMCFunctionSchemas_1_18()
		return schemas
