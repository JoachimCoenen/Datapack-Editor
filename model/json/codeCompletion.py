from dataclasses import dataclass
from typing import Optional, Callable, Sequence, cast

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLifyMarkDownSubSet, flatmap
from model.json.core import JsonArray, JsonData, JsonObject, JsonProperty, PropertySchema, JsonSchema, JsonNull, JsonBool, JsonNumber, JsonString, JsonUnionSchema, JsonArraySchema, \
	JsonStringSchema
from model.json.stringHandlers import getStringHandler
from model.utils import Position, GeneralError, Span


@dataclass
class Match:
	before: Optional[JsonData]
	contained: list[JsonData]
	after: Optional[JsonData]


def _getBestMatchInArray(tree: JsonArray, pos: Position, matches: Match) -> None:
	matches.before = None
	matches.after = None
	for elem in tree.data:
		if pos > elem.span.end:
			matches.before = elem
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
	matches.after = None
	for elem in tree.data.values():
		if pos > elem.span.end:
			matches.before = elem
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
	matches.contained.append(tree)
	if (matcher := _BEST_MATCHERS.get(tree.typeName)) is not None:
		matcher(tree, pos, matches)
	# if tree.typeName == JsonObject.typeName:
	# 	_getBestMatchInObject(cast(JsonObject, tree), pos, matches)
	# elif tree.typeName == JsonArray.typeName:
	# 	_getBestMatchInArray(cast(JsonArray, tree), pos, matches)
	# elif tree.typeName == JsonProperty.typeName:
	# 	_getBestMatchInProperty(cast(JsonProperty, tree), pos, matches)


def getBestMatch(tree: JsonData, pos: Position) -> Match:
	matches: Match = Match(None, [], None)
	if pos in tree.span:
		_getBestMatch(tree, pos, matches)
	return matches


def getHoverTip(position: Position, jsonData: JsonData, errors: Optional[Sequence[GeneralError]]) -> Optional[str]:
	tips = []
	if errors is not None:
		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		from Cat.CatPythonGUI.GUI import PythonGUI
		tips += [f'<div style="{PythonGUI.helpBoxStyles.get(e.style, "")}">{e.message}</div>' for e in matchedErrors]

	if jsonData is not None:
		matches: Match = getBestMatch(jsonData, position)
		for match in reversed(matches.contained):
			if (schema := match.schema) is not None:
				if schema.description:
					tips.append(HTMLifyMarkDownSubSet(schema.description))
				if schema.typeName == PropertySchema.typeName:
					break
				if isinstance(schema, JsonStringSchema) and schema.type is not None:
					if isinstance(jsonData, JsonString):
						if (strHandler := getStringHandler(schema.type.name)) is not None:
							tips.append(strHandler.getDocumentation(jsonData, position))

	if tips is not None:
		tip = '<br/>'.join(tips)
		return f"{tip}"


def getAutoCompletionForSchema(schema: JsonSchema) -> list[str]:
	values = {
		JsonNull.typeName: lambda: ['null'],
		JsonBool.typeName: lambda: ['true', 'false'],
		JsonNumber.typeName: lambda: ['0'],
		JsonString.typeName: lambda: ['"'],
		JsonArray.typeName: lambda: ['['],
		JsonObject.typeName: lambda: ['{'],
		JsonUnionSchema.typeName: lambda: list(flatmap(getAutoCompletionForSchema, (s for s in schema.options))),
	}
	return values[schema.typeName]()


def getAutoCompletionList(position: Position, jsonData: JsonData, text: str) -> list[str]:
	matches: Match = getBestMatch(jsonData, position)
	if not matches.contained:
		return []

	matchesC = list(reversed(matches.contained))

	match = matchesC[0]

	if match.typeName == JsonProperty.typeName:
		if position > match.value.span.end:
			return [', ', '}']
		if match.schema is not None:
			return getAutoCompletionForSchema(match.schema.value)

	if match.typeName == JsonArray.typeName:
		if matches.before is None:
			result = [']']
			if isinstance(match.schema, JsonArraySchema):
				result += getAutoCompletionForSchema(match.schema.element)
		elif ',' in text[matches.before.span.end.index:position.index]:
			if isinstance(match.schema, JsonArraySchema):
				result = getAutoCompletionForSchema(match.schema.element)
			else:
				result = [', ', ']']
		else:
			result = [', ', ']']
		return result

	if match.typeName == JsonString.typeName:
		if match.schema is None:
			if len(matchesC) >= 3:
				match = matchesC[2]  # if matches[0] was a key, matches[2] is the object.
		else:
			if isinstance(match.schema, JsonStringSchema) and match.schema.type is not None:
				if (strHandler := getStringHandler(match.schema.type.name)) is not None:
					suggestions = strHandler.getSuggestions(cast(JsonString, match), position.index, replaceCtx='')  # TODO: set correct replaceCtx
					return suggestions + ['"']
			return ['"']  # TODO: respect correct replaceCtx

	if match.typeName == JsonObject.typeName:
		if match.schema is not None:
			return [f'"{p.name}": ' for p in match.schema.properties] + ['}']

	if match.schema is not None:
		return getAutoCompletionForSchema(match.schema)

	return []


def getClickableRanges(root: JsonData) -> list[Span]:
	ranges: list[Span] = []
	for node in root.walkTree():
		if node.typeName == JsonString.typeName and (schema := node.schema) is not None:
			if schema.typeName == JsonStringSchema.typeName and schema.type is not None:
				if(strHandler := getStringHandler(schema.type.name)) is not None:
					partRanges = strHandler.getClickableRanges(cast(JsonString, node))
					if partRanges:
						ranges.extend(partRanges)
	return ranges


def indicatorClicked(jsonData: JsonData, position: Position, window: QWidget) -> None:
	matches = getBestMatch(jsonData, position)
	if not matches.contained:
		return

	match = matches.contained[0]
	if match.typeName == JsonString.typeName and (schema := match.schema) is not None:
		if schema.typeName == JsonStringSchema.typeName and schema.type is not None:
			if(strHandler := getStringHandler(schema.type.name)) is not None:
				strHandler.onIndicatorClicked(cast(JsonString, match), position, window)


