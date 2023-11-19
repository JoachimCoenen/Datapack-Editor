from base.plugin import PLUGIN_SERVICE, PluginBase
from corePlugins.minecraft_data.fullData import registerFullMcData


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('dpe:minecraft_data-Plugin', MinecraftDataPlugin())


class MinecraftDataPlugin(PluginBase):

	def initPlugin(self):
		from . import mcdAdapter
		from corePlugins.minecraft_data.fullData import loadAllVersionsFullMcData
		allVersionsData = loadAllVersionsFullMcData()
		for data in allVersionsData:
			registerFullMcData(data)

	def dependencies(self) -> set[str]:
		return {'McFunctionPlugin'}
