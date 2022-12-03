import os
from typing import Type

from PyQt5.Qsci import QsciLexerCustom

from base.gui.documentLexer import DocumentLexerBase2
from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument, DocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE


JSON_ID = LanguageId('JSON')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('JsonPlugin', JsonPlugin())


class JsonPlugin(PluginBase):

	def initPlugin(self) -> None:
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		JSON_SCHEMA_LOADER.registerSchema('dpe:json_schema', os.path.join(resourcesDir, 'jsonSchema.json'))
		from corePlugins.json.argTypes import init  # load standard argument types
		init()

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from corePlugins.json.parser import JsonParser
		return {
			JSON_ID: JsonParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from corePlugins.json.jsonContext import JsonCtxProvider
		from corePlugins.json.core import JsonNode
		return {
			JsonNode: JsonCtxProvider
		}

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return [DocumentTypeDescription(
			type=ParsedDocument,
			name='JSON',
			extensions=['.json', '.mcmeta'],
			defaultLanguage=JSON_ID
		)]

	def lexers(self) -> dict[LanguageId, Type[QsciLexerCustom]]:
		return {
			JSON_ID: DocumentLexerBase2
		}

	def stylers(self) -> list[Type[CatStyler]]:
		from corePlugins.json.jsonStyler import JsonStyler
		return [JsonStyler]
