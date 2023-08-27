from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('DatapackVersionsPlugin', DatapackVersionsPlugin())


class DatapackVersionsPlugin(PluginBase):

	def initPlugin(self):
		from . import version6  # loads all resource location contexts
		version6.initVersion()

	def dependencies(self) -> set[str]:
		return {'DatapackPlugin'}
