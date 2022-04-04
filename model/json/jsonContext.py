from abc import abstractmethod, ABC
from typing import Iterable, Optional, Type, Callable, cast

from PyQt5.QtWidgets import QWidget

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.utils import HTMLStr, HTMLifyMarkDownSubSet, Decorator, flatmap, override
from Cat.utils.collections_ import AddToDictDecorator
from model.commands.stringReader import StringReader
from model.datapackContents import ResourceLocation
from model.json.core import *
from model.json.core import JsonSemanticsError
from model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, registerContextProvider
from model.utils import Position, Span, GeneralError


def _getBestMatchInArray(tree: JsonArray, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	for elem in tree.data:
		if elem.span.end < pos:
			matches.before = elem
		# elif elem.span.start <= pos:
		# 	matches.hit = elem
		elif pos < elem.span.start:
			matches.after = elem
			break
		else:
			_getBestMatch(elem, pos, matches)
			break

		# if pos in elem.span:
		# 	_getBestMatch(elem, pos, matches)
		# 	return
		# if pos <= elem.span.start and elem.typeName == JsonInvalid.typeName:
		# 	_getBestMatch(elem, pos, matches)


def _getBestMatchInObject(tree: JsonObject, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	for elem in tree.data.values():
		if elem.span.end < pos:
			matches.before = elem
		# elif elem.span.start <= pos:
		# 	matches.hit = elem
		elif pos < elem.span.start:
			matches.after = elem
			break
		else:
			_getBestMatch(elem, pos, matches)
			break
		# if pos in prop.span:
		# 	_getBestMatch(prop, pos, matches)
		# 	return


def _getBestMatchInProperty(tree: JsonProperty, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	if pos > tree.value.span.end:
		matches.before = tree.value
	elif pos > tree.value.span.start:
		matches.before = tree.key
		_getBestMatch(tree.value, pos, matches)
	elif pos > tree.key.span.end:
		matches.before = tree.key
		matches.after = tree.value
	elif pos > tree.key.span.start:
		_getBestMatch(tree.key, pos, matches)
		matches.after = tree.value
	else:
		matches.after = tree.key
	# if pos in tree.key.span:
	# 	_getBestMatch(tree.key, pos, matches)
	# 	return
	# if pos in tree.value.span:
	# 	_getBestMatch(tree.value, pos, matches)
	# 	return


_BEST_MATCHERS: dict[str, Callable[[JsonData, Position, Match], None]] = {}
_BEST_MATCHERS.update({
	JsonObject.typeName: _getBestMatchInObject,
	JsonArray.typeName: _getBestMatchInArray,
	JsonProperty.typeName: _getBestMatchInProperty,
})


def _getBestMatch(tree: JsonData, pos: Position, matches: Match) -> None:
	if (matcher := _BEST_MATCHERS.get(tree.typeName)) is not None:
		matches.contained.append(tree)
		matcher(tree, pos, matches)
	else:
		matches.hit = tree
	# if tree.typeName == JsonObject.typeName:
	# 	_getBestMatchInObject(cast(JsonObject, tree), pos, matches)
	# elif tree.typeName == JsonArray.typeName:
	# 	_getBestMatchInArray(cast(JsonArray, tree), pos, matches)
	# elif tree.typeName == JsonProperty.typeName:
	# 	_getBestMatchInProperty(cast(JsonProperty, tree), pos, matches)


@registerContextProvider(JsonData)
class JsonCtxProvider(ContextProvider[JsonData]):

	def getBestMatch(self, pos: Position) -> Match[JsonData]:
		tree = self.tree
		matches = Match(None, None, None, [])
		if pos in tree.span:
			_getBestMatch(tree, pos, matches)
			if matches.before is not None and matches.hit is not None:
				if matches.before.span.end > matches.hit.span.start:
					matches.contained.append(matches.hit)
					matches.hit = None
		return matches

	def getContext(self, node: JsonData) -> Optional[Context]:
		if isinstance(node, JsonString):
			schema = node.schema
			if isinstance(schema, JsonStringSchema) and schema.type is not None:
				return getJsonStringContext(schema.type.name)
		return None

	def prepareTree(self) -> list[GeneralError]:
		pass

	def validateTree(self) -> list[GeneralError]:
		pass

	@classmethod
	def _getSuggestionsForSchema(cls, schema: JsonSchema) -> list[str]:
		values = {
			JsonNull.typeName: lambda: ['null'],
			JsonBool.typeName: lambda: ['true', 'false'],
			JsonNumber.typeName: lambda: ['0'],
			JsonString.typeName: lambda: ['"'],
			JsonArray.typeName: lambda: ['['],
			JsonObject.typeName: lambda: ['{'],
			JsonUnionSchema.typeName: lambda: list(flatmap(cls._getSuggestionsForSchema, (s for s in schema.options))),
		}
		return values[schema.typeName]()

	def getSuggestionsOLD(self, pos: Position, replaceCtx: str) -> Suggestions:
		matches: Match = self.getBestMatch(pos)
		if not matches.contained:
			return []

		matchesC = list(reversed(matches.contained))

		match = matchesC[0]

		if isinstance(match, JsonProperty):
			if pos > match.value.span.end:
				return [', ', '}']
			if match.schema is not None:
				return self._getSuggestionsForSchema(match.schema.value)

		if isinstance(match, JsonArray):
			if matches.before is None:
				result = [']']
				if isinstance(match.schema, JsonArraySchema):
					result += self._getSuggestionsForSchema(match.schema.element)
			elif ',' in self.text[matches.before.span.end.index:pos.index]:
				if isinstance(match.schema, JsonArraySchema):
					result = self._getSuggestionsForSchema(match.schema.element)
				else:
					result = [', ', ']']
			else:
				result = [', ', ']']
			return result

		if isinstance(match, JsonString):
			print(f"hello!")
			if match.schema is None:
				if len(matchesC) >= 3:
					match = matchesC[2]  # if matches[0] was a key, matches[2] is the object.
			else:
				if isinstance(match.schema, JsonStringSchema) and match.schema.type is not None:
					if (strHandler := self.getContext(match)) is not None:
						suggestions = strHandler.getSuggestions(match, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
						return suggestions + ['"']
				return ['"']

		if isinstance(match, JsonObject):
			if isinstance(match.schema, JsonObjectSchema):
				return [f'"{p.name}": ' for p in match.schema.properties] + ['}']

		if match.schema is not None:
			return self._getSuggestionsForSchema(match.schema)

		return []

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		matches = self.getBestMatch(pos)
		if not matches.contained:
			return []

		hit = matches.hit
		if hit is not None:
			if isinstance(hit, JsonString):
				if hit.schema is JSON_KEY_SCHEMA:
					if len(matches.contained) >= 2:
						contained = matches.contained[-2]  # if hit was a key, matches.contained[-2] is the object.
						if isinstance(contained, JsonObject) and isinstance(contained.schema, JsonObjectSchema):
							return [f'{p.name}": ' for p in contained.schema.properties if p.name not in contained.data]
				else:
					if isinstance(hit.schema, JsonStringSchema) and hit.schema.type is not None:
						if (strHandler := self.getContext(hit)) is not None:
							suggestions = strHandler.getSuggestions(hit, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
							return suggestions + ['"']
					return ['"']
			elif hit.schema is not None:
				return self._getSuggestionsForSchema(hit.schema)

		elif matches.before is not None:
			before = matches.before
			if before.schema is JSON_KEY_SCHEMA:
				needsColon = ':' not in self.text[before.span.end.index:pos.index]
				if matches.contained:
					prop = matches.contained[-1]
					if isinstance(prop, JsonProperty) and prop.schema is not None:
						suggestions = self._getSuggestionsForSchema(prop.schema.value)
						return [f': {sg}' for sg in suggestions] if needsColon else suggestions
				return [': '] if needsColon else []

			if not matches.contained:
				return []
			contained = matches.contained[-1]

			needsComma = ',' not in self.text[before.span.end.index:pos.index]
			if isinstance(contained, JsonArray):
				if needsComma:
					return [', ', ']']
				elif isinstance(contained.schema, JsonArraySchema):
					return self._getSuggestionsForSchema(contained.schema.element)
				return []

			if isinstance(contained, JsonObject):
				if needsComma:
					return [', ', '}']
				elif isinstance(contained.schema, JsonObjectSchema):
					return [f'"{p.name}": ' for p in contained.schema.properties if p.name not in contained.data]
				return []

		else:
			if not matches.contained:
				return []
			contained = matches.contained[-1]

			if isinstance(contained, JsonArray):
				if isinstance(contained.schema, JsonArraySchema):
					return self._getSuggestionsForSchema(contained.schema.element) + [']']
				return []

			if isinstance(contained, JsonObject):
				if isinstance(contained.schema, JsonObjectSchema):
					return [f'"{p.name}": ' for p in contained.schema.properties] + ['}']
				return []

		return []

	def getDocumentation(self, pos: Position) -> HTMLStr:
		tips = []
		matches = self.getBestMatch(pos)
		for match in reversed(matches.contained):
			if (schema := match.schema) is not None:
				if schema.description:
					tips.append(HTMLifyMarkDownSubSet(schema.description))
				if schema.typeName == PropertySchema.typeName:
					break
				if isinstance(schema, JsonStringSchema) and schema.type is not None:
					if isinstance(match, JsonString):
						if (strHandler := self.getContext(match)) is not None:
							tips.append(strHandler.getDocumentation(match, pos))

		if tips is not None:
			tip = '<br/>'.join(tips)
			return HTMLStr(f"{tip}")

	def getCallTips(self, pos: Position) -> list[str]:
		match = self.getBestMatch(pos)
		return ['?']

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		ranges: list[Span] = []
		for node in self.tree.walkTree():
			if not node.span.overlaps(span):
				continue
			if(strHandler := self.getContext(node)) is not None:
				partRanges = strHandler.getClickableRanges(node)
				if partRanges:
					ranges.extend(partRanges)
		return ranges


class JsonStringContext(Context[JsonString], ABC):

	@abstractmethod
	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		pass

	@abstractmethod
	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		pass

	@abstractmethod
	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		pass

	def getDocumentation(self, node: JsonString, pos: Position) -> HTMLStr:
		return defaultDocumentationProvider(node)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		pass


class AddContextToDictDecorator(AddToDictDecorator[str, JsonStringContext]):
	def __call__(self, key: str, forceOverride: bool = False):
		addFormatterInner = super(AddContextToDictDecorator, self).__call__(key, forceOverride)

		def addFormatter(func: Type[JsonStringContext]) -> Type[JsonStringContext]:
			addFormatterInner(func())
			return func
		return addFormatter


__jsonStringContexts: dict[str, JsonStringContext] = {}
jsonStringContext = Decorator(AddContextToDictDecorator(__jsonStringContexts))


def getJsonStringContext(aType: str) -> Optional[JsonStringContext]:
	return __jsonStringContexts.get(aType, None)


def defaultDocumentationProvider(argument: JsonData) -> HTMLStr:
	schema = argument.schema
	if schema is not None:
		if schema.description:
			tip = HTMLifyMarkDownSubSet(schema.description)
		else:
			tip = ''
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = f'<div style="{PythonGUI.helpBoxStyles["error"]}">{message}</div>'
	return tip


def defaultDocumentationProvider2(data: JsonData) -> HTMLStr:
	if (schema := data.schema) is not None:
		if schema.description:
			return HTMLifyMarkDownSubSet(schema.description)
	return HTMLStr('')







@jsonStringContext('minecraft:resource_location')
class ResourceLocationHandler(JsonStringContext):
	@override
	def prepare(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		sr = StringReader(node.data, 0, 0, node.data)

		allowTag = True
		location = sr.tryReadResourceLocation(allowTag=allowTag)
		if location is None:
			return
		if len(location) != len(node.data):
			return
		location = ResourceLocation.fromString(location)
		node.parsedValue = location

	@override
	def validate(self, data: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		if data.parsedValue is None:
			errorsIO.append(JsonSemanticsError(f"Expected a resource location, but got: \"`{data.data}`\"", data.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		pass

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		pass
