from abc import ABC, abstractmethod
from typing import Optional, Iterable

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLStr
from Cat.utils.logging_ import logError
from model.commands.stringReader import StringReader
from model.datapack.json.argTypes import *
from model.datapackContents import ResourceLocation
from model.json.core import *
from model.json.jsonContext import jsonStringContext, JsonStringContext
from model.parsing.contextProvider import Suggestions
import model.resourceLocationContext as rlc
from model.utils import GeneralError, Position, Span


class ResourceLocationLikeHandler(JsonStringContext, ABC):

	@abstractmethod
	def context(self, node: JsonString) -> rlc.ResourceLocationContext:
		pass

	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		sr = StringReader(node.data, 0, 0, node.data)

		allowTag = True
		location = sr.tryReadResourceLocation(allowTag=allowTag)
		if location is None:
			node.parsedValue = node.data
			return
		if len(location) != len(node.data):
			node.parsedValue = node.data
			return
		location = ResourceLocation.fromString(location)
		node.parsedValue = location

	def validate(self, node: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		self.context(node).validate(node.parsedValue, node.span, errorsIO)

	# def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
	# 	return self.context.getSuggestions(contextStr, cursorPos, replaceCtx)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		posInContextStr = pos.index - node.span.start.index
		return self.context(node).getSuggestions(node.data, posInContextStr, replaceCtx)

	def getDocumentation(self, node: JsonString, position: Position) -> HTMLStr:
		tips = []
		valueDoc = self.context(node).getDocumentation(node.parsedValue)
		if valueDoc:
			tips.append(valueDoc)

		propertyDoc = super(ResourceLocationLikeHandler, self).getDocumentation(node, position)
		if propertyDoc:
			tips.append(propertyDoc)

			return HTMLStr('<br/>'.join(tips))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return self.context(node).getClickableRanges(node.parsedValue, node.span)

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		return self.context(node).onIndicatorClicked(node.parsedValue, window)


@jsonStringContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ResourceLocationLikeHandler):

	def context(self, node: JsonString) -> rlc.ResourceLocationContext:
		schema = node.schema
		if isinstance(schema, JsonStringSchema):
			args = schema.args
			context = (args or {}).get('context')
		else:
			context = None

		if context is None:
			context = rlc.AnyContext()

		if not isinstance(context, rlc.ResourceLocationContext):
			logError(f"invalid 'context' argument for JsonArgType '{MINECRAFT_RESOURCE_LOCATION.name}' in JsonStringSchema: {context}. Expected an instance of ResourceLocationContext.")
			context = rlc.AnyContext()
		return context


def init() -> None:
	pass
