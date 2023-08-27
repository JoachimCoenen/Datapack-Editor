import os
from typing import Type

from PyQt5.Qsci import QsciLexerCustom

from base.gui.documentLexer import DocumentLexerBase2
from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument, DocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node, Schema
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE


JSON_ID = LanguageId('JSON')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('JsonPlugin', JsonPlugin())


class JsonPlugin(PluginBase):

	def initPlugin(self) -> None:
		from corePlugins.json.argTypes import init  # load standard argument types
		init()

	def dependencies(self) -> set[str]:
		return set()

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

	def schemas(self) -> dict[str, Schema]:
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		schemaPath = os.path.join(resourcesDir, 'jsonSchema.json')
		return {'dpe:json_schema': JSON_SCHEMA_LOADER.loadSchema('dpe:json_schema', schemaPath)}
