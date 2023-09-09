from typing import Type

from base.model.applicationSettings import SettingsAspect
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.tree import Node
from base.plugin import PLUGIN_SERVICE, PluginBase


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('MinecraftPlugin', MinecraftPlugin())


class MinecraftPlugin(PluginBase):

	def initPlugin(self):
		pass

	def dependencies(self) -> set[str]:
		return set()

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from .resourceLocation import ResourceLocationCtxProvider, ResourceLocationNode
		return {
			ResourceLocationNode: ResourceLocationCtxProvider
		}

	def settingsAspects(self) -> list[Type[SettingsAspect]]:
		from corePlugins.minecraft.settings import MinecraftSettings
		return [MinecraftSettings]
