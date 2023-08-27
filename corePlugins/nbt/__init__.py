from typing import Type

from PyQt5.Qsci import QsciLexerCustom

from base.gui.documentLexer import DocumentLexerBase2
from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument,  DocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE


SNBT_ID = LanguageId('SNBT')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('NbtPlugin', SNBTPlugin())


class SNBTPlugin(PluginBase):

	def initPlugin(self) -> None:
		pass

	def dependencies(self) -> set[str]:
		return set()

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from corePlugins.nbt.snbtParser import SNBTParser
		return {
			SNBT_ID: SNBTParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		pass

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return [DocumentTypeDescription(
			type=ParsedDocument,
			name='SNBT',
			extensions=['.snbt'],
			defaultLanguage=SNBT_ID
		)]

	def lexers(self) -> dict[LanguageId, Type[QsciLexerCustom]]:
		return {
			SNBT_ID: DocumentLexerBase2
		}

	def stylers(self) -> list[Type[CatStyler]]:
		from corePlugins.nbt.snbtStyler import SNBTStyler
		return [SNBTStyler]
