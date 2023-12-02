from abc import ABC
from typing import Any, Optional, cast

from base.model.messages import EXPECTED_MSG, TRAILING_NOT_ALLOWED_MSG
from base.model.parsing.contextProvider import CtxInfo, errorMsg
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.utils import GeneralError, LanguageId, MDStr, Span
from cat.utils.logging_ import logError
from corePlugins.json.core import *
from corePlugins.json.jsonContext import JsonStringContext, ParsingJsonCtx, jsonStringContext, orRefSchema
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID
from corePlugins.mcFunction.argumentTypes import ALL_NAMED_ARGUMENT_TYPES, ArgumentType
from corePlugins.mcFunction.command import ArgumentSchema
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import RESOURCE_LOCATION_ID, ResourceLocationSchema, getAllKnownResourceLocationContexts
from corePlugins.nbt.tags import NBTTagSchema
from .argTypes import *
from .commands.argumentTypes import *
from ..mcFunction.commandContext import getArgumentContext


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


@jsonStringContext(MINECRAFT_SCORE_HOLDER.name, argType=MINECRAFT_SCORE_HOLDER)
@jsonStringContext(MINECRAFT_OBJECTIVE.name, argType=MINECRAFT_OBJECTIVE)
@jsonStringContext('minecraft:target_selector', argType=MINECRAFT_ENTITY)  # for now
@jsonStringContext(MINECRAFT_BLOCK_POS.name, argType=MINECRAFT_BLOCK_POS)
@jsonStringContext(MINECRAFT_COLOR.name, argType=MINECRAFT_COLOR)
@jsonStringContext(MINECRAFT_UUID.name, argType=MINECRAFT_UUID)
class McFunctionArgumentContextAdaptor(ParsingJsonCtx, ABC):

	def __init__(self, *, argType: ArgumentType):
		self.argType: ArgumentType = argType

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		raise NotImplemented()  # we don't need this

	def getLanguage(self, node: JsonString) -> LanguageId:
		raise NotImplemented()  # we don't need this

	def getParserKwArgs(self, node: JsonString) -> dict[str, Any]:
		raise NotImplemented()  # we don't need this

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		sr = StringReader(
			node.rawData,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,  # not quite sure, yet...
			cursor=0,
			cursorOffset=node.indexMapper.toDecoded(node.span.start.index) + 1,  # + 1 in order to skip the quotation marks
			indexMapper=node.indexMapper,
			fullSource=info.ctxProvider.text
		)

		ai = ArgumentSchema(
			"value",
			type=self.argType,
			args=cast(JsonStringSchema, node.schema).args
		)

		if (context := getArgumentContext(self.argType)) is not None:
			parsedArg = context.parse(sr, ai, info.filePath, errorsIO=errorsIO)
			if parsedArg is None:
				errorMsg(EXPECTED_MSG, ai.asString, span=node.span, errorsIO=errorsIO)
			elif not sr.hasReachedEnd:
				p1 = sr.currentPos
				sr.tryReadRemaining()
				p2 = sr.currentPos
				errorMsg(TRAILING_NOT_ALLOWED_MSG, "characters", span=Span(p1, p2), errorsIO=errorsIO)
			node.parsedValue = parsedArg

			if parsedArg is not None:
				context.prepare(parsedArg, info, errorsIO=errorsIO)

