from abc import abstractmethod, ABC
from typing import Optional, Iterable, Any

from cat.utils.logging_ import logError
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID
from .argTypes import *
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, RESOURCE_LOCATION_ID, getAllKnownResourceLocationContexts
from corePlugins.json.core import *
from corePlugins.json.jsonContext import jsonStringContext, JsonStringContext
from corePlugins.nbt.tags import NBTTagSchema
from base.model.parsing.bytesUtils import strToBytes
from base.model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getDocumentation, onIndicatorClicked, getClickableRanges, parseNPrepare, CtxInfo
from base.model.parsing.tree import Schema
from base.model.utils import GeneralError, Position, Span, MDStr, LanguageId


class ParsingJsonCtx(JsonStringContext, ABC):

	@abstractmethod
	def getSchema(self, node: JsonString) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, node: JsonString) -> LanguageId:
		pass

	def getParserKwArgs(self, node: JsonString) -> dict[str, Any]:
		return {}

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		schema = self.getSchema(node)
		language = self.getLanguage(node)

		data, errors = parseNPrepare(
			strToBytes(node.data),
			filePath=info.filePath,
			language=language,
			schema=schema,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,  # not quite sure, yet...
			cursor=0,
			cursorOffset=node.indexMapper.toDecoded(node.span.start.index) + 1,  # + 1 in order to skip the quotation marks
			indexMapper=node.indexMapper,
			**self.getParserKwArgs(node)
		)
		errorsIO.extend(errors)
		node.parsedValue = data

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		validateTree(node.parsedValue, b'', errorsIO)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if node.parsedValue is not None:
			return getSuggestions(node.parsedValue, b'', pos, replaceCtx)
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		docs = []
		if propertyDoc := super().getDocumentation(node, pos):
			docs.append(propertyDoc)

		if node.parsedValue is not None:
			if valueDoc := getDocumentation(node.parsedValue, b'', pos):
				docs.append(valueDoc)

		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None:
			return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos)


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
				value=JsonStringOptionsSchema(options={val: MDStr("") for val in allResLocCtxKeys}, warningOnly=True, allowMultilineStr=False),
				optional=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='allowTags',
				value=JsonBoolSchema(allowMultilineStr=None),
				optional=True,
				default=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='onlyTags',
				value=JsonBoolSchema(allowMultilineStr=None),
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


@jsonStringContext(MINECRAFT_CHAT_COMMAND.name)
class CommandJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		if isinstance(node.schema, JsonStringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return schema or GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID)

	def getLanguage(self, node: JsonString) -> LanguageId:
		return MC_FUNCTION_ID
