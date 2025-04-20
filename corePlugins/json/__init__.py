import os
from typing import Type

from base.gui.styler import CatStyler
from base.model.documents import ParsedDocument, DocumentTypeDescription
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Schema
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
