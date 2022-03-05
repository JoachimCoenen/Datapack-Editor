
from typing import Optional, Iterable, Type

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLStr, HTMLifyMarkDownSubSet, Decorator, override
from Cat.utils.collections_ import AddToDictDecorator
from model.commandsV2.stringReader import StringReader
from model.datapackContents import ResourceLocation
from model.json.core import JsonString, JsonData, JsonSemanticsError
from model.parsing.contextProvider import ContextProvider
from model.utils import Span, Position

Suggestion = str  # for now...
Suggestions = list[Suggestion]


JsonContextProvider = ContextProvider[JsonData]
JsonStringProvider = ContextProvider[JsonString]


__jsonContextProviders: dict[str, JsonContextProvider] = {}


def getJsonContextProvider(node: JsonData) -> Optional[JsonContextProvider]:
	pass


class JsonStringHandler:
	def parse(self, data: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		pass

	def validate(self, data: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		return None

	def getSuggestions(self, data: JsonString, cursorPos: int, replaceCtx: str) -> Suggestions:
		"""
		:param data:
		:param cursorPos: cursor position in contextStr
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		return []

	def getDocumentation(self, data: JsonString, position: Position) -> HTMLStr:
		return defaultDocumentationProvider(data)

	def getClickableRanges(self, data: JsonString) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, data: JsonString, position: Position, window: QWidget) -> None:
		pass


class AddHandlerToDictDecorator(AddToDictDecorator[str, JsonStringHandler]):
	def __call__(self, key: str, forceOverride: bool = False):
		addFormatterInner = super(AddHandlerToDictDecorator, self).__call__(key, forceOverride)

		def addFormatter(func: Type[JsonStringHandler]) -> Type[JsonStringHandler]:
			addFormatterInner(func())
			return func
		return addFormatter


__jsonStringHandlers: dict[str, JsonStringHandler] = {}
jsonStringHandler = Decorator(AddHandlerToDictDecorator(__jsonStringHandlers))


def getStringHandler(type: str) -> Optional[JsonStringHandler]:
	return __jsonStringHandlers.get(type, None)


def defaultDocumentationProvider(data: JsonData) -> HTMLStr:
	if (schema := data.schema) is not None:
		if schema.description:
			return HTMLifyMarkDownSubSet(schema.description)
	return HTMLStr('')



@jsonStringHandler('minecraft:resource_location')
class ResourceLocationHandler(JsonStringHandler):
	@override
	def parse(self, data: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		sr = StringReader(data.data, 0, 0, data.data)

		allowTag = True
		location = sr.tryReadResourceLocation(allowTag=allowTag)
		if location is None:
			return
		if len(location) != len(data.data):
			return
		location = ResourceLocation.fromString(location)
		data.parsedValue = location

	@override
	def validate(self, data: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		if data.parsedValue is None:
			errorsIO.append(JsonSemanticsError(f"Expected a resource location, but got: \"`{data.data}`\"", data.span))


