import os
from typing import Type, Optional, Any

from PyQt5.Qsci import QsciLexerCustom

from Cat.Serializable import RegisterContainer, Serialized
from base.gui.documentLexer import DocumentLexerBase2
from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument, TextDocument,  DocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node
from base.model.pathUtils import FilePath
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE
from corePlugins.json.core import JsonSchema


def initPlugin() -> None:
	# from corePlugins.json import jsonSchema
	PLUGIN_SERVICE.registerPlugin('JsonPlugin', JsonPlugin())


class JsonPlugin(PluginBase):

	def initPlugin(self) -> None:
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
		JSON_SCHEMA_LOADER.registerSchema('dpe:json_schema', os.path.join(resourcesDir, 'jsonSchema.json'))

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from corePlugins.json import parser
		return {
			LanguageId('JSON'): parser.JsonParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from corePlugins.json.jsonContext import JsonCtxProvider
		from corePlugins.json.core import JsonNode
		return {
			JsonNode: JsonCtxProvider
		}

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return [DocumentTypeDescription(
			type=JsonDocument,
			name='JSON',
			extensions=['.json', '.mcmeta'],
			defaultLanguage='JSON'
		)]

	def lexers(self) -> dict[LanguageId, Type[QsciLexerCustom]]:
		return {
			LanguageId('JSON'): DocumentLexerBase2
		}

	def stylers(self) -> list[Type[CatStyler]]:
		from corePlugins.json.jsonStyler import JsonStyler
		return [JsonStyler]


# @RegisterDocument('JSON', ext=['.json', '.mcmeta'], defaultLanguage='JSON')
@RegisterContainer
class JsonDocument(ParsedDocument, TextDocument):
	"""docstring for Document"""

	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(JsonDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: bytes = b''

	encoding: str = Serialized(default='utf-8')

	@property
	def schema(self) -> Optional[JsonSchema]:
		# if isinstance(self.metaInfo, JsonMeta):
		# 	schemaId = self.metaInfo.schemaId
		# 	return getSession().datapackData.jsonSchemas.get(schemaId)
		# else:
		# 	return getSession().datapackData.jsonSchemas.get('dpe:json_schema')
		return None

	@property
	def parseKwArgs(self) -> dict[str, Any]:
		return dict(allowMultilineStr=True)


# class LexerJson(DocumentLexerBase2):
# 	def language(self):
# 		return "JSON"
#
# 	def description(self, style):
# 		return "Custom lexer for the Minecrafts .json files"