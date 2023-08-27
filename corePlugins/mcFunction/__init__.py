from typing import Type

from PyQt5.Qsci import QsciLexerCustom

from base.gui.documentLexer import DocumentLexerBase2
from base.gui.styler import CatStyler
from base.model.documents import DocumentTypeDescription, ParsedDocument
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from base.plugin import PLUGIN_SERVICE, PluginBase

MC_FUNCTION_ID = LanguageId('MCFunction')
MC_FUNCTION_DEFAULT_SCHEMA_ID = 'Minecraft'


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('McFunctionPlugin', McFunctionPlugin())


class McFunctionPlugin(PluginBase):

	def initPlugin(self) -> None:
		pass

	def dependencies(self) -> set[str]:
		return {'MinecraftPlugin', 'NbtPlugin'}

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from .parser import MCFunctionParser
		return {
			MC_FUNCTION_ID: MCFunctionParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from .commandContext import CommandCtxProvider
		from .command import CommandPart
		return {
			CommandPart: CommandCtxProvider,
			# MCFunction: CommandCtxProvider,
			# ParsedComment: CommandCtxProvider,
			# ParsedCommand: CommandCtxProvider,
			# ParsedArgument: CommandCtxProvider,
		}

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return [DocumentTypeDescription(
			type=ParsedDocument,
			name='MC Function',
			extensions=['.mcfunction'],
			defaultLanguage=MC_FUNCTION_ID,
			defaultSchemaId=MC_FUNCTION_DEFAULT_SCHEMA_ID
		)]

	def lexers(self) -> dict[LanguageId, Type[QsciLexerCustom]]:
		return {
			MC_FUNCTION_ID: DocumentLexerBase2
		}

	def stylers(self) -> list[Type[CatStyler]]:
		from .mcFunctionStyler import MCCommandStyler
		return [MCCommandStyler]
