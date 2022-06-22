from abc import abstractmethod, ABC
from itertools import chain
from typing import Iterable, Optional, Callable, cast

from PyQt5.QtWidgets import QWidget

from Cat.utils import Decorator, flatmap
from model.json.core import *
from model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, registerContextProvider, AddContextToDictDecorator
from model.utils import Position, Span, GeneralError, MDStr, formatAsError


def _getBestMatchInArray(tree: JsonArray, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	for elem in tree.data:
		if elem.span.end < pos:
			matches.before = elem
		# elif elem.span.start <= pos:
		# 	matches.hit = elem
		elif elem.span.start < pos:
			_getBestMatch(elem, pos, matches)
			break
		else:
			matches.after = elem
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
		elif elem.span.start < pos:
			_getBestMatch(elem, pos, matches)
			break
		else:
			matches.after = elem
			break
		# if pos in prop.span:
		# 	_getBestMatch(prop, pos, matches)
		# 	return


def _getBestMatchInProperty(tree: JsonProperty, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	valueSpan = tree.value.span
	keySpan = tree.key.span
	if valueSpan.end < pos:
		matches.before = tree.value
	elif valueSpan.start < pos:
		matches.before = tree.key
		_getBestMatch(tree.value, pos, matches)
	elif keySpan.end < pos:
		matches.before = tree.key
		matches.after = tree.value
	elif keySpan.start < pos:
		_getBestMatch(tree.key, pos, matches)
		# matches.after = tree.value
	else:
		matches.after = tree.key
	# if pos in tree.key.span:
	# 	_getBestMatch(tree.key, pos, matches)
	# 	return
	# if pos in tree.value.span:
	# 	_getBestMatch(tree.value, pos, matches)
	# 	return


_BEST_MATCHERS: dict[str, Callable[[JsonData, Position, Match], None]] = {
	JsonObject.typeName: cast(Callable[[JsonData, Position, Match], None], _getBestMatchInObject),
	JsonArray.typeName: cast(Callable[[JsonData, Position, Match], None], _getBestMatchInArray),
	JsonProperty.typeName: cast(Callable[[JsonData, Position, Match], None], _getBestMatchInProperty),
}


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


def _suggestionsForUnionSchema(schema: JsonUnionSchema):
	return list(flatmap(getSuggestionsForSchema, (s for s in schema.options)))


_SCHEMA_SUGGESTIONS_PROVIDERS = {
	JsonNullSchema.typeName: lambda schema: ['null'],
	JsonBoolSchema.typeName: lambda schema: ['true', 'false'],
	JsonNumberSchema.typeName: lambda schema: ['0'],
	JsonFloatSchema.typeName: lambda schema: ['0'],
	JsonIntSchema.typeName: lambda schema: ['0'],
	JsonStringSchema.typeName: lambda schema: ['"'],
	JsonArraySchema.typeName: lambda schema: ['['],
	JsonObjectSchema.typeName: lambda schema: ['{'],
	JsonUnionSchema.typeName: lambda schema: _suggestionsForUnionSchema(schema),
}


def getSuggestionsForSchema(schema: JsonSchema) -> list[str]:
	return _SCHEMA_SUGGESTIONS_PROVIDERS[schema.typeName](schema)


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
		errorsIO = []
		for node in self.tree.walkTree():
			if (ctx := self.getContext(node)) is not None:
				ctx.prepare(node, errorsIO)
		return errorsIO

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		from model.json.validator import validateJson
		errorsIO += validateJson(self.tree)
		pass  # TODO: validateTree for json

	@staticmethod
	def _getSuggestionsForSchema(schema: JsonSchema) -> list[str]:
		return getSuggestionsForSchema(schema)

	# def getSuggestionsOLD(self, pos: Position, replaceCtx: str) -> Suggestions:
	# 	matches: Match = self.getBestMatch(pos)
	# 	if not matches.contained:
	# 		return []
	#
	# 	matchesC = list(reversed(matches.contained))
	#
	# 	match = matchesC[0]
	#
	# 	if isinstance(match, JsonProperty):
	# 		if pos > match.value.span.end:
	# 			return [', ', '}']
	# 		if match.schema is not None:
	# 			return self._getSuggestionsForSchema(match.schema.value)
	#
	# 	if isinstance(match, JsonArray):
	# 		if matches.before is None:
	# 			result = [']']
	# 			if isinstance(match.schema, JsonArraySchema):
	# 				result += self._getSuggestionsForSchema(match.schema.element)
	# 		elif ',' in self.text[matches.before.span.end.index:pos.index]:
	# 			if isinstance(match.schema, JsonArraySchema):
	# 				result = self._getSuggestionsForSchema(match.schema.element)
	# 			else:
	# 				result = [', ', ']']
	# 		else:
	# 			result = [', ', ']']
	# 		return result
	#
	# 	if isinstance(match, JsonString):
	#
	# 		if match.schema is None:
	# 			if len(matchesC) >= 3:
	# 				match = matchesC[2]  # if matches[0] was a key, matches[2] is the object.
	# 		else:
	# 			if isinstance(match.schema, JsonStringSchema) and match.schema.type is not None:
	# 				if (strHandler := self.getContext(match)) is not None:
	# 					suggestions = strHandler.getSuggestions(match, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
	# 					return suggestions + ['"']
	# 			return ['"']
	#
	# 	if isinstance(match, JsonObject):
	# 		if isinstance(match.schema, JsonObjectSchema):
	# 			return [f'"{p.name}": ' for p in match.schema.properties] + ['}']
	#
	# 	if match.schema is not None:
	# 		return self._getSuggestionsForSchema(match.schema)
	#
	# 	return []

	def _getSuggestionsForBefore(self, pos: Position, before: JsonData, contained: list[JsonData], replaceCtx: str) -> Suggestions:
		if before.schema is JSON_KEY_SCHEMA:
			needsColon = b':' not in self.text[before.span.end.index:pos.index]
			if len(contained) >= 2:
				prop = contained[-1]
				if isinstance(prop, JsonProperty) and prop.schema is not None and contained:
					parent = contained[-2]
					if isinstance(parent, JsonObject):
						valueSchema = prop.schema.valueForParent(parent)
						if valueSchema is not None:
							suggestions = self._getSuggestionsForSchema(valueSchema)
							return [f': {sg}' for sg in suggestions] if needsColon else suggestions
			return [': '] if needsColon else []
		elif not contained:
			return []
		else:
			needsComma = b',' not in self.text[before.span.end.index:pos.index]
			return self._getSuggestionsForContained(pos, contained, replaceCtx, needsComma=needsComma)
		# 	container = contained[-1]
		# 	if isinstance(container, JsonArray):
		# 		if needsComma:
		# 			return [', ', ']']
		# 		elif isinstance(container.schema, JsonArraySchema):
		# 			return self._getSuggestionsForSchema(container.schema.element)
		# 		return []
		#
		# 	elif isinstance(container, JsonObject):
		# 		if needsComma:
		# 			return [', ', '}']
		# 		elif isinstance(container.schema, JsonObjectSchema):
		# 			return [f'"{p.name}": ' for p in container.schema.properties if p.name not in container.data]
		# 		return []
		# return []

	def _getPropsForObject(self, container: JsonObject, schema: JsonObjectSchema) -> list[str]:
		return [p.name for p in schema.propertiesDict.values() if p.name not in container.data and p.valueForParent(container) is not None]

	def _getSuggestionsForContained(self, pos: Position, contained: list[JsonData], replaceCtx: str, *, needsComma: bool) -> Suggestions:
		if not contained:
			return []
		container = contained[-1]

		if isinstance(container, JsonProperty):
			if len(contained) >= 2:
				container = contained[-2]
			else:
				return []
		if isinstance(container, JsonArray):
			if needsComma:
				return [f'{replaceCtx}, ', f'{replaceCtx}]']
			if isinstance(container.schema, JsonArraySchema):
				return self._getSuggestionsForSchema(container.schema.element) + ([']'] if not container.data else [])
		elif isinstance(container, JsonObject):
			if needsComma:
				return [f'{replaceCtx}, ', f'{replaceCtx}}}']
			if isinstance(container.schema, JsonObjectSchema):
				return [f'"{p}": ' for p in self._getPropsForObject(container, container.schema)] + (['}'] if not container.data else [])

		return []

	def _getSuggestionsForHit(self, pos: Position, hit: JsonData, contained: list[JsonData], replaceCtx: str) -> Suggestions:

		if isinstance(hit, JsonString):
			data = self.text[hit.span.slice]
			if hit.span.end == pos and len(data) >= 2 and data.endswith(b'"') and data.startswith(b'"'):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)

			elif hit.schema is JSON_KEY_SCHEMA:
				if len(contained) >= 2:
					container = contained[-2]  # if hit was a key, matches.contained[-2] is the object.
					if isinstance(container, JsonObject) and isinstance(container.schema, JsonObjectSchema):
						return [f'{p}": ' for p in self._getPropsForObject(container, container.schema)]
			else:
				if isinstance(hit.schema, JsonStringSchema) and hit.schema.type is not None:
					if (strHandler := self.getContext(hit)) is not None:
						suggestions = strHandler.getSuggestions(hit, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
						return suggestions + [f'{replaceCtx}"']
				return [f'{replaceCtx}"']
		elif hit.schema is not None:
			if hit.span.end == pos and not isinstance(hit, JsonInvalid):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)

			return self._getSuggestionsForSchema(hit.schema)
		return []

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		matches = self.getBestMatch(pos)
		if not matches.contained:
			return []

		hit = matches.hit
		if hit is not None:
			return self._getSuggestionsForHit(pos, matches.hit, matches.contained, replaceCtx)
		if matches.before is not None:
			return self._getSuggestionsForBefore(pos, matches.before, matches.contained, replaceCtx)
		else:
			return self._getSuggestionsForContained(pos, matches.contained, replaceCtx, needsComma=False)

	# def getSuggestions2(self, pos: Position, replaceCtx: str) -> Suggestions:
	# 	matches = self.getBestMatch(pos)
	# 	if not matches.contained:
	# 		return []
	#
	# 	hit = matches.hit
	# 	if hit is not None:
	# 		if isinstance(hit, JsonString):
	# 			if hit.schema is JSON_KEY_SCHEMA:
	# 				if len(matches.contained) >= 2:
	# 					contained = matches.contained[-2]  # if hit was a key, matches.contained[-2] is the object.
	# 					if isinstance(contained, JsonObject) and isinstance(contained.schema, JsonObjectSchema):
	# 						return [f'{p.name}": ' for p in contained.schema.properties if p.name not in contained.data]
	# 			else:
	# 				if isinstance(hit.schema, JsonStringSchema) and hit.schema.type is not None:
	# 					if (strHandler := self.getContext(hit)) is not None:
	# 						suggestions = strHandler.getSuggestions(hit, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
	# 						return suggestions + ['"']
	# 				return ['"']
	# 		elif hit.schema is not None:
	# 			return self._getSuggestionsForSchema(hit.schema)
	#
	# 	elif matches.before is not None:
	# 		before = matches.before
	# 		if before.schema is JSON_KEY_SCHEMA:
	# 			needsColon = ':' not in self.text[before.span.end.index:pos.index]
	# 			if len(matches.contained) >= 2:
	# 				prop = matches.contained[-1]
	# 				if isinstance(prop, JsonProperty) and prop.schema is not None and matches.contained:
	# 					parent = matches.contained[-2]
	# 					if isinstance(parent, JsonObject):
	# 						valueSchema = prop.schema.valueForParent(parent)
	# 						suggestions = self._getSuggestionsForSchema(valueSchema)
	# 						return [f': {sg}' for sg in suggestions] if needsColon else suggestions
	# 			return [': '] if needsColon else []
	# 		elif not matches.contained:
	# 			return []
	# 		else:
	# 			contained = matches.contained[-1]
	#
	# 			needsComma = ',' not in self.text[before.span.end.index:pos.index]
	# 			if isinstance(contained, JsonArray):
	# 				if needsComma:
	# 					return [', ', ']']
	# 				elif isinstance(contained.schema, JsonArraySchema):
	# 					return self._getSuggestionsForSchema(contained.schema.element)
	# 				return []
	#
	# 			elif isinstance(contained, JsonObject):
	# 				if needsComma:
	# 					return [', ', '}']
	# 				elif isinstance(contained.schema, JsonObjectSchema):
	# 					return [f'"{p.name}": ' for p in contained.schema.properties if p.name not in contained.data]
	# 				return []
	#
	# 	else:
	# 		if not matches.contained:
	# 			return []
	# 		contained = matches.contained[-1]
	#
	# 		if isinstance(contained, JsonArray):
	# 			if isinstance(contained.schema, JsonArraySchema):
	# 				return self._getSuggestionsForSchema(contained.schema.element) + [']']
	# 			return []
	#
	# 		if isinstance(contained, JsonObject):
	# 			if isinstance(contained.schema, JsonObjectSchema):
	# 				return [f'"{p.name}": ' for p in contained.schema.properties] + ['}']
	# 			return []
	#
	# 	return []

	def getDocumentation(self, pos: Position) -> MDStr:
		tips = []
		matches = self.getBestMatch(pos)

		if matches.hit is None and matches.after is not None and matches.after.span.start == pos:
			matches.hit = matches.after
			matches.after = None

		for match in chain((matches.hit,), reversed(matches.contained)):
			if match is None:
				continue
			if (schema := match.schema) is not None:
				if schema.typeName == PropertySchema.typeName:
					match: JsonProperty
					tips.append(f"###Property '{match.key.data}':")
				else:
					tips.append(f'###{schema.asString}:')
				hasSeenDescription = False
				if isinstance(schema, JsonStringSchema) and schema.type is not None:
					if isinstance(match, JsonString):
						if (strHandler := self.getContext(match)) is not None:
							if (doc := strHandler.getDocumentation(match, pos)):
								tips.append(doc)
								hasSeenDescription = True
				elif schema.description:
					tips.append(schema.description)
					hasSeenDescription = True
				if not hasSeenDescription:
					# remove heading:
					tips.pop()
				if schema.typeName == PropertySchema.typeName:
					break

		return MDStr('\n\n'.join(tips))  # '\n<br/>\n'.join(tips)

	def getCallTips(self, pos: Position) -> list[str]:
		matches = self.getBestMatch(pos)

		if matches.hit is None and matches.after is not None and matches.after.span.start == pos:
			matches.hit = matches.after
			matches.after = None

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

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		return defaultDocumentationProvider(node)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		pass


__jsonStringContexts: dict[str, JsonStringContext] = {}
jsonStringContext = Decorator(AddContextToDictDecorator[JsonStringContext](__jsonStringContexts))


def getJsonStringContext(aType: str) -> Optional[JsonStringContext]:
	return __jsonStringContexts.get(aType, None)


def defaultDocumentationProvider(argument: JsonData) -> MDStr:
	schema = argument.schema
	if schema is not None:
		if schema.description:
			tip = schema.description
		else:
			tip = MDStr('')
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = formatAsError(message)
	return tip


def defaultDocumentationProvider2(data: JsonData) -> MDStr:
	if (schema := data.schema) is not None:
		if schema.description:
			return schema.description
	return MDStr('')
