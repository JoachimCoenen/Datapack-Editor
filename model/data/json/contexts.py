from abc import abstractmethod, ABC
from dataclasses import replace
from typing import Optional, Iterable, Any

from PyQt5.QtWidgets import QWidget

from Cat.utils.logging_ import logError
from model.commands.stringReader import StringReader
from model.data.json.argTypes import *
from model.datapack.datapackContents import ResourceLocationNode, ResourceLocationSchema
from model.json.core import *
from model.json.core import OPTIONS_JSON_ARG_TYPE
from model.json.jsonContext import jsonStringContext, JsonStringContext
from model.messages import *
from model.nbt.tags import NBTTagSchema
from model.parsing.bytesUtils import strToBytes
from model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getDocumentation, onIndicatorClicked, getClickableRanges, parseNPrepare
from model.parsing.tree import Schema
from model.utils import GeneralError, Position, Span, MDStr, LanguageId


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

		if not isinstance(schema, ResourceLocationSchema):
			logError(f"invalid 'schema' argument for JsonArgType '{MINECRAFT_RESOURCE_LOCATION.name}' in JsonStringSchema: {schema}. Expected an instance of ResourceLocationContext.")
			schema = ResourceLocationSchema('', 'any')
		return schema

	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
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
		start = replace(start, column=start.column + 1, index=start.index + 1)
		end = node.span.end
		offset = node.indexMapper.toEncoded(end.index - start.index) + start.index - end.index  # todo: test
		end = replace(end, column=end.column + offset, index=end.index + offset)
		if len(node.data) + 2 == node.span.length:
			end = replace(end, column=end.column - 1, index=end.index - 1)
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

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		return onIndicatorClicked(node.parsedValue, b'', pos, window)


class ParsingJsonCtx(JsonStringContext, ABC):

	@abstractmethod
	def getSchema(self, node: JsonString) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, node: JsonString) -> LanguageId:
		pass

	def getParserKwArgs(self, node: JsonString) -> dict[str, Any]:
		return {}

	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		# remainder = sr.tryReadRemaining()
		schema = self.getSchema(node)
		language = self.getLanguage(node)

		data, errors = parseNPrepare(
			strToBytes(node.data),
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

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos, window)


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
		from model.commands.command import MCFunctionSchema
		from session.session import getSession
		if isinstance(node.schema, JsonStringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return schema or MCFunctionSchema('', commands=getSession().minecraftData.commands)

	def getLanguage(self, node: JsonString) -> LanguageId:
		return LanguageId('MCCommand')


@jsonStringContext(OPTIONS_JSON_ARG_TYPE.name)
class OptionsJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			if node.data not in node.schema.args.get('values', ()):
				errorsIO.append(JsonSemanticsError(UNKNOWN_MSG.format("Option", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if isinstance(node.schema, JsonStringSchema):
			return list(node.schema.args.get('values', ()))
		return []


def init() -> None:
	pass
