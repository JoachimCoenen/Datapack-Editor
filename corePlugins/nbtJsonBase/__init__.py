from base.gui.styler import CatStyler
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE

STRUCTURE_ID = LanguageId('Structure')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('NbtJsonBasePlugin', SNBTPlugin())


class SNBTPlugin(PluginBase):

	def initPlugin(self) -> None:
		from .argTypes import init  # load standard argument types  # noqa: F401
		init()

	def dependencies(self) -> set[str]:
		return set()

	def contextProviders(self) -> dict[type[Node], type[ContextProvider]]:
		from .core import StructureNode
		from .context import StructureCtxProvider
		from .structureContextImpl import StructureArgTypeStrContext  # load structureContextImpl  # noqa: F401
		return {StructureNode: StructureCtxProvider}

	def stylers(self) -> dict[LanguageId, type[CatStyler]]:
		from corePlugins.nbtJsonBase.structureStyler import StructureStyler
		return {LanguageId('Structure'): StructureStyler}
