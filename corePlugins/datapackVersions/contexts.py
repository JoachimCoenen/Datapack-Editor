import re
from abc import ABC
from typing import Any, Optional, cast, ClassVar

from base.model.messages import EXPECTED_MSG, TRAILING_NOT_ALLOWED_MSG
from base.model.parsing.contextProvider import CtxInfo, errorMsg, Suggestions
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.utils import GeneralError, LanguageId, MDStr, Span, SemanticsError, Position
from cat.utils.logging_ import logError
from corePlugins.nbtJsonBase.context import ParsingStructureCtx, structureStringContext, orRefSchema, StringNodeContext
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID
from corePlugins.mcFunction.argumentTypes import ArgumentType
from corePlugins.mcFunction.command import ArgumentSchema
from corePlugins.mcFunction.commandContext import getArgumentContext
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import RESOURCE_LOCATION_ID, ResourceLocationSchema, getAllKnownResourceLocationContexts
from .argTypes import *
from corePlugins.nbtJsonBase.core import StringNode, ObjectSchema, UnionSchema, IllegalSchema, StringOptionsSchema, \
	PropertySchema, BooleanSchema, StringSchema, STRUCTURE_ANY_SCHEMA, StructureNode, StructureArgType


@structureStringContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ParsingStructureCtx):
	def getSchema(self, node: StringNode) -> ResourceLocationSchema:
		schema = node.schema
		if hasattr(schema, 'args'):  # isinstance(schema, JsonStringSchema):
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

	def getLanguage(self, node: StringNode) -> LanguageId:
		return RESOURCE_LOCATION_ID

	def getArgsSchema(self) -> tuple[ObjectSchema | UnionSchema | IllegalSchema, bool]:
		allResLocCtxKeys = getAllKnownResourceLocationContexts().keys()
		properties: list[PropertySchema] = [
			PropertySchema(
				name='schema',
				value=orRefSchema(StringOptionsSchema(options={val: MDStr("") for val in allResLocCtxKeys}, warningOnly=True, allowMultilineStr=False)),
				optional=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='allowTags',
				value=orRefSchema(BooleanSchema(allowMultilineStr=None)),
				optional=True,
				default=False,
				allowMultilineStr=None
			),
			PropertySchema(
				name='onlyTags',
				value=orRefSchema(BooleanSchema(allowMultilineStr=None)),
				optional=True,
				default=False,
				allowMultilineStr=None
			),
		]
		return ObjectSchema(properties=properties, allowMultilineStr=None).finish(), True


@structureStringContext(DPE_STRINGIFIED_JSON_TAG.name)
class StringifiedJsonStrContext(ParsingStructureCtx):

	def getSchema(self, node: StringNode) -> Optional[Schema]:
		if isinstance(node.schema, StringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return GLOBAL_SCHEMA_STORE.get(schema, LanguageId('JSON')) or STRUCTURE_ANY_SCHEMA

	def getLanguage(self, node: StringNode) -> LanguageId:
		return LanguageId('JSON')

	def getArgsSchema(self) -> tuple[ObjectSchema | UnionSchema | IllegalSchema, bool]:
		return ObjectSchema(properties=[PropertySchema(name='schema', value=StringSchema(allowMultilineStr=False), allowMultilineStr=False)], allowMultilineStr=False).finish(), False


@structureStringContext(MINECRAFT_NBT_COMPOUND_TAG.name)
@structureStringContext(MINECRAFT_NBT_TAG.name)
class NBTJsonStrContext(ParsingStructureCtx):

	def getSchema(self, node: StringNode) -> Optional[Schema]:
		if isinstance(node.schema, StringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return GLOBAL_SCHEMA_STORE.get(schema, LanguageId('SNBT')) or STRUCTURE_ANY_SCHEMA

	def getLanguage(self, node: StringNode) -> LanguageId:
		return LanguageId('SNBT')

	def getArgsSchema(self) -> tuple[ObjectSchema | UnionSchema | IllegalSchema, bool]:
		return ObjectSchema(properties=[PropertySchema(name='schema', value=StringSchema(allowMultilineStr=False), allowMultilineStr=False)], allowMultilineStr=False).finish(), False


@structureStringContext(MINECRAFT_NBT_PATH.name)
class NBTPathJsonStrContext(ParsingStructureCtx):

	def getSchema(self, node: StringNode) -> Optional[Schema]:
		return None

	def getLanguage(self, node: StringNode) -> LanguageId:
		return LanguageId('SNBTPath')  # todo implement proper nbt path parsing


@structureStringContext(MINECRAFT_CHAT_COMMAND.name)
class CommandJsonStrContext(ParsingStructureCtx):

	def getSchema(self, node: StringNode) -> Optional[Schema]:
		if isinstance(node.schema, StringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return schema or GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID)  # todo 'schema' might be a string??

	def getLanguage(self, node: StringNode) -> LanguageId:
		return MC_FUNCTION_ID


@structureStringContext(MINECRAFT_COLOR.name)
class ColorStructureCtx(StringNodeContext):
	named_colors: ClassVar[set[str]] = {
		'black',
		'dark_blue',
		'dark_green',
		'dark_aqua',
		'dark_red',
		'dark_purple',
		'gold',
		'gray',
		'dark_gray',
		'blue',
		'green',
		'aqua',
		'red',
		'light_purple',
		'yellow',
		'white',
	}

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, StringSchema):
			if node.data in self.named_colors:
				return  # good.
			else:
				v = node.data
				if not v.startswith('#'):
					errorsIO.append(SemanticsError(MDStr(f"Invalid color value '{v}'. Colors must be a named color or have to start with a '#'."), node.span))
				elif len(v) != 7:
					errorsIO.append(SemanticsError(MDStr(f"Hexadecimal colors must have 6 digits (3 pairs)."), node.span))
				elif not re.fullmatch(r'#[0-9a-fA-F]{6}', v):
					errorsIO.append(SemanticsError(MDStr(f"'{v[1:]}' is not a valid hexadecimal color."), node.span))

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		return list(self.named_colors)


@structureStringContext(MINECRAFT_SCORE_HOLDER.name, argType=MINECRAFT_SCORE_HOLDER)
@structureStringContext(MINECRAFT_OBJECTIVE.name, argType=MINECRAFT_OBJECTIVE)
@structureStringContext(MINECRAFT_TARGET_SELECTOR.name, argType=MINECRAFT_TARGET_SELECTOR)  # for now
@structureStringContext(MINECRAFT_BLOCK_POS.name, argType=MINECRAFT_BLOCK_POS)
@structureStringContext(MINECRAFT_GAME_MODE.name, argType=MINECRAFT_GAME_MODE)
@structureStringContext(MINECRAFT_ITEM_SLOTS.name, argType=MINECRAFT_ITEM_SLOTS)
@structureStringContext(MINECRAFT_UUID.name, argType=MINECRAFT_UUID)
class McFunctionArgumentContextAdaptor(ParsingStructureCtx, ABC):

	def __init__(self, *, argType: StructureArgType):
		self.argType: ArgumentType = argType.commandArgumentType

	def getSchema(self, node: StringNode) -> Optional[Schema]:
		raise NotImplemented()  # we don't need this

	def getLanguage(self, node: StringNode) -> LanguageId:
		raise NotImplemented()  # we don't need this

	def getParserKwArgs(self, node: StringNode) -> dict[str, Any]:
		raise NotImplemented()  # we don't need this

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		sr = StringReader(
			node.rawData,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,  # not quite sure, yet...
			cursor=0,
			cursorOffset=node.indexMapper.toDecoded(node.innerSlice.start),
			indexMapper=node.indexMapper,
			fullSource=info.ctxProvider.text
		)

		ai = ArgumentSchema(
			"value",
			type=self.argType,
			args=cast(StringSchema, node.schema).args
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
				context.prepare(parsedArg, cast(CtxInfo, info), errorsIO=errorsIO)
