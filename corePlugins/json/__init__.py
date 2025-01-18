import os
from typing import Type

from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument, DocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node, Schema
from base.model.utils import LanguageId
from base.plugin import PluginBase, PLUGIN_SERVICE
from corePlugins.nbt import SNBT_ID

JSON_ID = LanguageId('JSON')


def initPlugin() -> None:
	PLUGIN_SERVICE.registerPlugin('JsonPlugin', JsonPlugin())


class JsonPlugin(PluginBase):

	def initPlugin(self) -> None:
		pass

	def dependencies(self) -> set[str]:
		return {'NbtJsonBasePlugin'}

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		from .parser import JsonParser
		return {
			JSON_ID: JsonParser,
		}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		from corePlugins.nbtJsonBase.context import StructureCtxProvider
		from corePlugins.nbtJsonBase.core import StructureNode
		from .core import JsonNode

		class JsonCtxProvider(StructureCtxProvider):
			def __init__(self, tree: StructureNode, text: bytes):
				super().__init__(tree, text, requiresStringQuotation=True)

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

	def stylers(self) -> dict[LanguageId, Type[CatStyler]]:
		from corePlugins.nbtJsonBase.structureStyler import StructureStyler
		return {JSON_ID: StructureStyler}

	def schemas(self) -> dict[LanguageId, dict[str, Schema]]:
		from corePlugins.nbtJsonBase.schemaStore import STRUCTURE_SCHEMA_LOADER
		resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
		schemaPath = os.path.join(resourcesDir, 'jsonSchema.json')
		schema = STRUCTURE_SCHEMA_LOADER.loadSchema('dpe:json_schema', schemaPath)
		return {
			JSON_ID: {'dpe:json_schema': schema},
			SNBT_ID: {'dpe:json_schema': schema}
		}
