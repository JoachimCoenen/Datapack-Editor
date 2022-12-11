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

		from .v1_17_schema import initPlugin as initPluginSchema_1_17
		from .v1_18_schema import initPlugin as initPluginSchema_1_18
		initPluginSchema_1_17()
		initPluginSchema_1_18()

		from .argumentContextsImpl import initPlugin as initArgumentContexts
		initArgumentContexts()
