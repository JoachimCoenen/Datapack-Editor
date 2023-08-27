from abc import abstractmethod, ABC
from typing import Optional, Iterable, Any

from Cat.utils.logging_ import logError
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID, MC_FUNCTION_ID
from corePlugins.mcFunction.stringReader import StringReader
from .argTypes import *
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, ResourceLocationNode
from corePlugins.json.core import *
from corePlugins.json.jsonContext import jsonStringContext, JsonStringContext
from corePlugins.nbt.tags import NBTTagSchema
from base.model.parsing.bytesUtils import strToBytes
from base.model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getDocumentation, onIndicatorClicked, getClickableRanges, parseNPrepare, CtxInfo
from base.model.parsing.tree import Schema
from base.model.utils import GeneralError, Position, Span, MDStr, LanguageId
from model.messages import EXPECTED_BUT_GOT_MSG


@jsonStringContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(JsonStringContext):
	def schema(self, node: JsonString) -> ResourceLocationSchema:
		schema = node.schema
		if isinstance(schema, JsonStringSchema):
			args = schema.args
			schema = (args or {}).get('schema')
		else:
			schema = None

		if schema is None:
			schema = ResourceLocationSchema('', 'any')

		if isinstance(schema, str):
			schema = ResourceLocationSchema('', schema)
		if not isinstance(schema, ResourceLocationSchema):
			logError(f"invalid 'schema' argument for JsonArgType '{MINECRAFT_RESOURCE_LOCATION.name}' in JsonStringSchema: {schema}. Expected an instance of ResourceLocationContext.")
			schema = ResourceLocationSchema('', 'any')
		return schema

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		data = strToBytes(node.data)
		sr = StringReader(data, 0, 0, 0, data)

		allowTag = True
		location = sr.readResourceLocation(allowTag=allowTag)
		if len(location) != len(node.data):
			errorsIO.append(JsonSemanticsError(EXPECTED_BUT_GOT_MSG.format(MINECRAFT_RESOURCE_LOCATION.name, node.data), node.span))
			# node.parsedValue = node.data
			# return
		schema = self.schema(node)
		start = node.span.start
		start = Position(start.line, start.column + 1, start.index + 1)
		end = node.span.end
		if node.typeName == 'string':
			offset = node.indexMapper.toEncoded(end.index - start.index) + start.index - end.index  # todo: test
		else:
			offset = 0
		end = Position(end.line, end.column + offset, end.index + offset)
		if len(node.data) + 2 == node.span.length:
			end = Position(end.line, end.column - 1, end.index - 1)
		span = Span(start, end)
		location = ResourceLocationNode.fromString(location, span, schema)
		node.parsedValue = location

	def validate(self, node: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		if isinstance(node.parsedValue, ResourceLocationNode):
			validateTree(node.parsedValue, b'', errorsIO)

	# def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
	# 	return self.context.getSuggestions(contextStr, cursorPos, replaceCtx)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		posInContextStr = pos.index - node.span.start.index
		return getSuggestions(node.parsedValue, b'', pos, replaceCtx)

	def getDocumentation(self, node: JsonString, position: Position) -> MDStr:
		tips = []
		valueDoc = getDocumentation(node.parsedValue, b'', position)
		if valueDoc:
			tips.append(valueDoc)

		propertyDoc = super(ResourceLocationHandler, self).getDocumentation(node, position)
		if propertyDoc:
			tips.append(propertyDoc)

		return MDStr('\n\n'.join(tips))  # '\n<br>\n'.join(tips)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		return onIndicatorClicked(node.parsedValue, b'', pos)


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
		# remainder = sr.tryReadRemaining()
		schema = self.getSchema(node)
		language = self.getLanguage(node)

		data, errors = parseNPrepare(
			strToBytes(node.data),
			filePath=info.filePath,
			language=language,
			schema=schema,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,
			cursor=0,
			cursorOffset=node.span.start.index + 1,
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
		docs = [
			super(ParsingJsonCtx, self).getDocumentation(node, pos),
			getDocumentation(node.parsedValue, b'', pos)
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None:
			return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos)


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


def init() -> None:
	pass
