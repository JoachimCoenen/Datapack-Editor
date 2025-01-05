from typing import Type

from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.tree import Node
from base.plugin import PluginBase, PLUGIN_SERVICE


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('NbtJsonBasePlugin', SNBTPlugin())


class SNBTPlugin(PluginBase):

	def initPlugin(self) -> None:
		from .argTypes import init  # load standard argument types
		init()

	def dependencies(self) -> set[str]:
		return set()

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from .structureContextImpl import StructureArgTypeStrContext  # load structureContextImpl
		return {}