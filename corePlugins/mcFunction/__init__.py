from typing import Type

from base.gui.styler import CatStyler
from base.model.documents import DocumentTypeDescription, ParsedDocument
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from base.plugin import PLUGIN_SERVICE, PluginBase

MC_FUNCTION_ID = LanguageId('MCFunction')
MC_FUNCTION_DEFAULT_SCHEMA_ID = 'Minecraft'

FILTER_ARGS_ID = LanguageId('FilterArg')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('McFunctionPlugin', McFunctionPlugin())


class McFunctionPlugin(PluginBase):

	def initPlugin(self) -> None:
		from .argumentContextsImpl import initPlugin as initArgumentContexts
		initArgumentContexts()

	def dependencies(self) -> set[str]:
		return set()

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from .parser import MCFunctionParser
		from .filterArgs import FilterArgumentsParser
		return {
			MC_FUNCTION_ID: MCFunctionParser,
			FILTER_ARGS_ID: FilterArgumentsParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from .commandContext import CommandCtxProvider
		from .command import CommandPart
		from .filterArgs import FilterArgNode, FilterArgNodeCtxProvider
		return {
			CommandPart: CommandCtxProvider,
			FilterArgNode: FilterArgNodeCtxProvider,
		}

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return [DocumentTypeDescription(
			type=ParsedDocument,
			name='MC Function',
			extensions=['.mcfunction'],
			defaultLanguage=MC_FUNCTION_ID,
			defaultSchemaId=MC_FUNCTION_DEFAULT_SCHEMA_ID
		)]

	def stylers(self) -> dict[LanguageId, Type[CatStyler]]:
		from .mcFunctionStyler import MCCommandStyler, FilterArgumentsStyler
		return {
			MC_FUNCTION_ID: MCCommandStyler,
			FILTER_ARGS_ID: FilterArgumentsStyler,
		}
