from typing import Optional

from cat.utils.logging_ import logError
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID
from .argTypes import *
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, RESOURCE_LOCATION_ID, getAllKnownResourceLocationContexts
from corePlugins.json.core import *
from corePlugins.json.jsonContext import ParsingJsonCtx, jsonStringContext, orRefSchema
from corePlugins.nbt.tags import NBTTagSchema
from base.model.parsing.tree import Schema
from base.model.utils import MDStr, LanguageId


@jsonStringContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ParsingJsonCtx):
	def getSchema(self, node: JsonString) -> ResourceLocationSchema:
		schema = node.schema
		if isinstance(schema, JsonStringSchema):
			args = (schema.args or {})
			schema = args.get('schema')
			allowTags = args.get('allowTags', False) is True
			onlyTags = args.get('onlyTags', False) is True
		else:
			schema = 'any'
			allowTags = False
			onlyTags = False

		if isinstance(schema, str):
			schema = ResourceLocationSchema('', schema, allowTags=allowTags, onlyTags=onlyTags)
		elif not isinstance(schema, ResourceLocationSchema):
			schemaPos = f"{node.schema.filePath!r} {node.schema.span.start}"
			logError(f"invalid 'schema' argument for JsonArgType '{MINECRAFT_RESOURCE_LOCATION.name}': '{schema}' here: {schemaPos}.")
			schema = ResourceLocationSchema('', 'any', allowTags=False, onlyTags=False)
		return schema

	def getLanguage(self, node: JsonString) -> LanguageId:
		return RESOURCE_LOCATION_ID

	def getArgsSchema(self) -> tuple[JsonObjectSchema | JsonUnionSchema | JsonIllegalSchema, bool]:
		allResLocCtxKeys = getAllKnownResourceLocationContexts().keys()
		properties: list[PropertySchema] = [
			PropertySchema(
				name='schema',
				value=orRefSchema(JsonStringOptionsSchema(options={val: MDStr("") for val in allResLocCtxKeys}, warningOnly=True, allowMultilineStr=False)),
				optional=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='allowTags',
				value=orRefSchema(JsonBoolSchema(allowMultilineStr=None)),
				optional=True,
				default=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='onlyTags',
				value=orRefSchema(JsonBoolSchema(allowMultilineStr=None)),
				optional=True,
				default=False,
				allowMultilineStr=None
			),
		]
		return JsonObjectSchema(properties=properties, allowMultilineStr=None).finish(), True


@jsonStringContext(MINECRAFT_NBT_COMPOUND_TAG.name)
@jsonStringContext(MINECRAFT_NBT_TAG.name)
class NBTJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		if isinstance(node.schema, JsonStringSchema):
			return node.schema.args.get('schema') or NBTTagSchema('')

	def getLanguage(self, node: JsonString) -> LanguageId:
		return LanguageId('SNBT')


@jsonStringContext(MINECRAFT_NBT_PATH.name)
class NBTPathJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		return None

	def getLanguage(self, node: JsonString) -> LanguageId:
		return LanguageId('SNBTPath')  # todo implement proper nbt path parsing


@jsonStringContext(MINECRAFT_CHAT_COMMAND.name)
class CommandJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		if isinstance(node.schema, JsonStringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return schema or GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID)

	def getLanguage(self, node: JsonString) -> LanguageId:
		return MC_FUNCTION_ID
