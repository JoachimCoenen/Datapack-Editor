from dataclasses import replace
from typing import Optional, Iterable

from PyQt5.QtWidgets import QWidget

from Cat.utils.logging_ import logError
from model.commands.stringReader import StringReader
from model.datapack.json.argTypes import *
from model.datapackContents import ResourceLocationNode, ResourceLocationSchema
from model.json.core import *
from model.json.jsonContext import jsonStringContext, JsonStringContext
from model.messages import *
from model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getDocumentation, onIndicatorClicked, getClickableRanges
from model.utils import GeneralError, Position, Span, MDStr


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
		sr = StringReader(node.data, 0, 0, node.data)

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
		if len(node.data) + 2 == node.span.length:
			end = replace(end, column=end.column - 1, index=end.index - 1)
		span = Span(start, end)
		location = ResourceLocationNode.fromString(location, span, schema)
		node.parsedValue = location

	def validate(self, node: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		if isinstance(node.parsedValue, ResourceLocationNode):
			validateTree(node.parsedValue, '', errorsIO)

	# def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
	# 	return self.context.getSuggestions(contextStr, cursorPos, replaceCtx)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		posInContextStr = pos.index - node.span.start.index
		return getSuggestions(node.parsedValue, '', pos, replaceCtx)

	def getDocumentation(self, node: JsonString, position: Position) -> MDStr:
		tips = []
		valueDoc = getDocumentation(node.parsedValue, '', position)
		if valueDoc:
			tips.append(valueDoc)

		propertyDoc = super(ResourceLocationHandler, self).getDocumentation(node, position)
		if propertyDoc:
			tips.append(propertyDoc)

		return MDStr('\n\n'.join(tips))  # '\n<br>\n'.join(tips)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.parsedValue, '')

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		return onIndicatorClicked(node.parsedValue, '', pos, window)


def init() -> None:
	pass
