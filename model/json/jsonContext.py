from __future__ import annotations
import functools
from abc import ABC
from itertools import chain
from typing import Iterable, Optional, Callable, cast

from PyQt5.QtWidgets import QWidget

from Cat.utils import Decorator, flatmap
from model.json import validator2
from model.json.core import *
from model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, registerContextProvider, AddContextToDictDecorator, CtxInfo
from model.utils import Position, Span, GeneralError, MDStr


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
		matches.before = tree.key  # TODO this seems to be wrong?
		_getBestMatch(tree.value, pos, matches)
	elif keySpan.end < pos:
		matches.before = tree.key
		matches.after = tree.value
	elif keySpan.start < pos:
		_getBestMatch(tree.key, pos, matches)
		# matches.after = tree.value
	else:
		matches.after = tree.key


_BEST_MATCHERS: dict[str, Callable[[JsonNode, Position, Match], None]] = {
	JsonObject.typeName: cast(Callable[[JsonNode, Position, Match], None], _getBestMatchInObject),
	JsonArray.typeName: cast(Callable[[JsonNode, Position, Match], None], _getBestMatchInArray),
	JsonProperty.typeName: cast(Callable[[JsonNode, Position, Match], None], _getBestMatchInProperty),
}


def _getBestMatch(tree: JsonNode, pos: Position, matches: Match) -> None:
	if (matcher := _BEST_MATCHERS.get(tree.typeName)) is not None:
		matches.contained.append(tree)
		matcher(tree, pos, matches)
	else:
		matches.hit = tree


def _suggestionsForUnionSchema(schema: JsonUnionSchema, contained: list[JsonNode], data: bytes):
	gsfs = functools.partial(getSuggestionsForSchema, contained=contained, data=data)
	return list(flatmap(gsfs, (s for s in schema.options)))


def _getPropsForObject(container: JsonObject, schema: JsonObjectSchema | JsonUnionSchema, prefix: str, suffix: str) -> list[str]:
	if isinstance(schema, JsonUnionSchema):
		return [n for opt in schema.allOptions for n in _getPropsForObject(container, opt, prefix, suffix)]
	else:
		return [f'{prefix}{p.name}{suffix}' for p in schema.propertiesDict.values() if p.name not in container.data and p.valueForParent(container) is not None]


def _suggestionsForKeySchema(schema: JsonKeySchema, contained: list[JsonNode], data: bytes):
	if len(contained) >= 2:
		container = contained[-2]  # if hit was a key, matches.contained[-2] is the object.
		if isinstance(container, JsonObject) and isinstance(container.schema, (JsonObjectSchema, JsonUnionSchema)):
			prefix = '' if data.startswith(b'"') else '"'
			return _getPropsForObject(container, container.schema, prefix, '": ')
	return []


_SCHEMA_SUGGESTIONS_PROVIDERS = {
	JsonAnySchema.typeName: lambda schema, contained, data: [],
	JsonNullSchema.typeName: lambda schema, contained, data: ['null'],
	JsonBoolSchema.typeName: lambda schema, contained, data: ['true', 'false'],
	JsonNumberSchema.typeName: lambda schema, contained, data: ['0'],
	JsonFloatSchema.typeName: lambda schema, contained, data: ['0'],
	JsonIntSchema.typeName: lambda schema, contained, data: ['0'],
	JsonStringSchema.typeName: lambda schema, contained, data: ['"'],
	JsonArraySchema.typeName: lambda schema, contained, data: ['['],
	JsonObjectSchema.typeName: lambda schema, contained, data: ['{'],
	JsonUnionSchema.typeName: _suggestionsForUnionSchema,
	JsonKeySchema.typeName: _suggestionsForKeySchema,
}


def getSuggestionsForSchema(schema: JsonSchema, contained: list[JsonNode], data: bytes) -> list[str]:
	return _SCHEMA_SUGGESTIONS_PROVIDERS[schema.typeName](schema, contained, data)


@registerContextProvider(JsonNode)
class JsonCtxProvider(ContextProvider[JsonNode]):

	def getBestMatch(self, pos: Position) -> Match[JsonNode]:
		tree = self.tree
		matches = Match(None, None, None, [])
		if pos in tree.span:
			_getBestMatch(tree, pos, matches)
			if matches.before is not None and matches.hit is not None:
				if matches.before.span.end > matches.hit.span.start:
					matches.contained.append(matches.hit)
					matches.hit = None
		return matches

	def getContext(self, node: JsonNode) -> Optional[JsonContext]:
		schema = node.schema
		if schema is not None and schema.typeName in {'string', 'key'} and schema.type is not None:
			return getJsonStringContext(schema.type)
		return JSON_DEFAULT_CONTEXT

	# def validateTree(self, errorsIO: list[GeneralError]) -> None:
	# 	from model.json.validator import validateJson
	# 	errorsIO += validateJson(self.tree)
	# 	pass  # TODO: validateTree for json

	def _getSuggestionsForBefore(self, pos: Position, before: JsonNode, contained: list[JsonNode], replaceCtx: str) -> Suggestions:
		if isinstance(before.schema, JsonKeySchema):
			needsColon = b':' not in self.text[before.span.end.index:pos.index]
			if len(contained) >= 2:
				prop = contained[-1]
				if isinstance(prop, JsonProperty) and prop.schema is not None and contained:
					parent = contained[-2]
					if isinstance(parent, JsonObject):
						valueSchema = prop.schema.valueForParent(parent)
						if valueSchema is not None:
							data = self.text[prop.value.span.slice]
							suggestions = getSuggestionsForSchema(valueSchema, contained, data)
							return [f': {sg}' for sg in suggestions] if needsColon else suggestions
			return [': '] if needsColon else []
		elif not contained:
			return []
		else:
			needsComma = b',' not in self.text[before.span.end.index:pos.index]
			return self._getSuggestionsForContained(pos, contained, replaceCtx, needsComma=needsComma)

	def _getSuggestionsForContained(self, pos: Position, contained: list[JsonNode], replaceCtx: str, *, needsComma: bool) -> Suggestions:
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
				data = b''
				return getSuggestionsForSchema(container.schema.element, contained, data) + ([']'] if not container.data else [])
		elif isinstance(container, JsonObject):
			if needsComma:
				return [f'{replaceCtx}, ', f'{replaceCtx}}}']
			if isinstance(container.schema, (JsonObjectSchema, JsonUnionSchema)):
				return _getPropsForObject(container, container.schema, '"', '": ') + (['}'] if not container.data else [])

		return []

	def _getSuggestionsForHit(self, pos: Position, hit: JsonNode, contained: list[JsonNode], replaceCtx: str) -> Suggestions:
		data = self.text[hit.span.slice]
		if isinstance(hit, JsonString):
			if hit.span.end == pos and len(data) >= 2 and data.endswith(b'"') and data.startswith(b'"'):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)

			elif isinstance(hit.schema, JsonKeySchema):
				if len(contained) >= 2:
					container = contained[-2]  # if hit was a key, matches.contained[-2] is the object.
					if isinstance(container, JsonObject) and isinstance(container.schema, (JsonObjectSchema, JsonUnionSchema)):
						prefix = '' if data.startswith(b'"') else '"'
						return _getPropsForObject(container, container.schema, prefix, '": ')
			elif (strHandler := self.getContext(hit)) is not None:
				return strHandler.getSuggestions(hit, pos, replaceCtx=replaceCtx)  # TODO: set correct replaceCtx
		elif hit.schema is not None:
			if hit.span.end == pos and not isinstance(hit, JsonInvalid):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)
			return getSuggestionsForSchema(hit.schema, contained, data)
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
				if (strHandler := self.getContext(match)) is not None:
					if doc := strHandler.getDocumentation(match, pos):
						tips.append(doc)
						hasSeenDescription = True
				if schema.description:
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


class JsonContext(Context[JsonNode]):

	def prepare(self, node: JsonString, info: CtxInfo[JsonData], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		validator2.validateJson(node, errorsIO)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		return super(JsonContext, self).getDocumentation(node, pos)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		pass


JSON_DEFAULT_CONTEXT = JsonContext()


class JsonStringContext(JsonContext, ABC):
	pass


__jsonStringContexts: dict[str, JsonStringContext] = {}
jsonStringContext = Decorator(AddContextToDictDecorator[JsonStringContext](__jsonStringContexts))


def getJsonStringContext(aType: str) -> Optional[JsonStringContext]:
	return __jsonStringContexts.get(aType, None)


def defaultDocumentationProvider2(data: JsonNode) -> MDStr:
	if (schema := data.schema) is not None:
		if schema.description:
			return schema.description
	return MDStr('')


@jsonStringContext('dpe:json/key_schema')
class JsonKeyContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonData], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		pass

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		pass

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		return super(JsonKeyContext, self).getDocumentation(node, pos)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if isinstance(node.schema, JsonKeySchema) and node.schema.forProp.schema is not None and node.schema.forProp.schema.filePath:
			return (node.span,)

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		if isinstance(node.schema, JsonKeySchema) and node.schema.forProp.schema is not None and node.schema.forProp.schema.filePath:
			window._tryOpenOrSelectDocument(node.schema.forProp.schema.filePath, Span(node.schema.forProp.schema.span.start))

