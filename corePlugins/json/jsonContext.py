from __future__ import annotations
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import Generator, Iterable, Optional, Callable, cast, Any

from cat.utils import Anything, Decorator, flatmap
from base.model.parsing.tree import Schema
from base.model.pathUtils import joinFilePath, dirFromFilePath
from base.model.session import getSession
from .core import *
from base.model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, AddContextToDictDecorator, CtxInfo, getCallTips, parseNPrepare, prepareTree, \
	validateTree, getSuggestions, getDocumentation, getClickableRanges, onIndicatorClicked
from base.model.utils import Position, SemanticsError, Span, GeneralError, MDStr, LanguageId
from .argTypes import *
from .jsonSchema import JObject, SchemaBuilder
from .lexer import INVALID_NUMBER_MSG
from .schema import enrichWithSchema
from .schemaStore import JSON_SCHEMA_LOADER
from base.model.messages import UNKNOWN_MSG


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
		# if prop.span.__contains__(pos):
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


def _flattenOptions(schema: JsonUnionSchema, parent: JsonObject) -> Generator[JsonSchema]:
	for opt in schema.allOptions:
		actualOpt = resolveCalculatedSchema(opt, parent)
		if actualOpt is None:
			continue
		elif isinstance(actualOpt, JsonUnionSchema):
			yield from _flattenOptions(actualOpt, parent)
		else:
			yield actualOpt


def _suggestionsForUnionSchema(schema: JsonUnionSchema, contained: list[JsonNode], data: bytes):
	gsfs = functools.partial(getSuggestionsForSchema, contained=contained, data=data)
	if contained:
		return list(flatmap(gsfs, _flattenOptions(schema, contained[-1])))  # maybe contained[-2]??
	else:
		return list(flatmap(gsfs, schema.options))


def _getPropsForObject(container: JsonObject, schema: JsonObjectSchema | JsonUnionSchema, prefix: str, suffix: str) -> list[str]:
	if isinstance(schema, JsonUnionSchema):
		allOptions = list(_flattenOptions(schema, container.parent))
	elif isinstance(schema, JsonObjectSchema):
		allOptions = (schema,)
	else:
		return []

	return [
		f'{prefix}{p.name}{suffix}'
		for opt in allOptions
		if isinstance(opt, JsonObjectSchema)
		for p in opt.propertiesDict.values()
		if p.name not in container.data and p.getValueSchemaForParent(container) is not None
	]


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


class JsonCtxProvider(ContextProvider[JsonNode]):

	def getBestMatch(self, pos: Position) -> Match[JsonNode]:
		tree = self.tree
		matches = Match(None, None, None, [])
		if tree.span.__contains__(pos):
			_getBestMatch(tree, pos, matches)
			if matches.before is not None and matches.hit is not None:
				if matches.before.span.end > matches.hit.span.start:
					matches.contained.append(matches.hit)
					matches.hit = None
		return matches

	def getContext(self, node: JsonNode) -> Optional[JsonContext]:
		schema = node.schema
		if schema is not None and isinstance(schema, JsonStringSchema) and schema.type is not None:
			return getJsonStringContext(schema.type)
		return JSON_DEFAULT_CONTEXT

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		from . import validator2
		validator2.validateJson(self.tree, errorsIO)

	def _getSuggestionsForBefore(self, pos: Position, before: JsonNode, contained: list[JsonNode], replaceCtx: str) -> Suggestions:
		if isinstance(before.schema, JsonKeySchema):
			needsColon = b':' not in self.text[before.span.end.index:pos.index]
			if len(contained) >= 2:
				prop = contained[-1]
				if isinstance(prop, JsonProperty) and prop.schema is not None and contained:
					parent = contained[-2]
					if isinstance(parent, JsonObject):
						valueSchema = prop.schema.getValueSchemaForParent(parent)
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
		return super().getCallTips(pos)

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
		raise ValueError("JsonContext.validate() should never be called. use validator2.validateJson(...) instead!")

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		return super(JsonContext, self).getDocumentation(node, pos)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		pass


JSON_DEFAULT_CONTEXT = JsonContext()


class JsonStringContext(JsonContext, ABC):

	def validateSchemaArgs(
			self,
			schemaBuilder: SchemaBuilder,
			type_: JsonArgType,
			argsNode: Optional[JObject],
			typeDefNode: JObject,
	):
		expectedArgs, requireArgs = self.getArgsSchema()
		errors = validateSimpleSchemaArgs(type_, argsNode, typeDefNode.span, expectedArgs, requireArgs, typeDefNode.ctx.filePath)
		if errors:
			schemaBuilder.reader.addErrors(errors, ctx=typeDefNode.ctx)

	def getArgsSchema(self) -> tuple[JsonObjectSchema | JsonUnionSchema | JsonIllegalSchema, bool]:
		"""
		Override this Function if args are required.
		:return: (The schema for args or JsonIllegalSchema if there are no args.; whether the 'args' property is mandatory or not.)
		"""
		return JSON_ILLEGAL_SCHEMA, False


def orRefSchema(schema: JsonSchema) -> JsonUnionSchema:
	refProperties: list[PropertySchema] = [
		PropertySchema(
			name='$ref',
			value=JsonStringSchema(allowMultilineStr=False),
			optional=False,
			allowMultilineStr=False
		),
		PropertySchema(
			name=Anything(),
			value=JSON_ANY_SCHEMA,
			optional=False,
			allowMultilineStr=None
		),
	]
	schema2 = JsonObjectSchema(properties=refProperties, allowMultilineStr=None).finish()

	return JsonUnionSchema(options=[schema, schema2], allowMultilineStr=None)


def validateSimpleSchemaArgs(
		type_: JsonArgType,
		argsNode: Optional[JObject],
		parentSpan: Span,
		expectedArgs: JsonObjectSchema | JsonUnionSchema | JsonIllegalSchema,
		requireArgs: bool,
		filePath: str,
) -> list[GeneralError]:
	from .validator2 import MISSING_MANDATORY_PROPERTY_MSG

	if argsNode is None and requireArgs:
		return [SemanticsError(MISSING_MANDATORY_PROPERTY_MSG.format('args'), parentSpan, style='error')]
	elif isinstance(expectedArgs, JsonIllegalSchema):
		if argsNode is not None and argsNode.data:
			return [SemanticsError(MDStr(f"Unexpected arguments for type '{type_.name}'."), argsNode.span, style='warning')]
	else:
		enrichWithSchema(argsNode.n, expectedArgs)
		errors = []
		prepareTree(argsNode.n, b'', filePath, errorsIO=errors)
		validateTree(argsNode.n, b'', errorsIO=errors)
		return errors



__jsonStringContexts: dict[str, JsonStringContext] = {}
jsonStringContext = Decorator(AddContextToDictDecorator[JsonStringContext](__jsonStringContexts))


def getJsonStringContext(aType: str) -> Optional[JsonStringContext]:
	return __jsonStringContexts.get(aType, None)


def defaultDocumentationProvider2(data: JsonNode) -> MDStr:
	if (schema := data.schema) is not None:
		if schema.description:
			return schema.description
	return MDStr('')


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
		schema = self.getSchema(node)
		language = self.getLanguage(node)

		data, errors, _ = parseNPrepare(
			node.rawData,
			filePath=info.filePath,
			language=language,
			schema=schema,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,  # not quite sure, yet...
			cursor=0,
			cursorOffset=node.indexMapper.toDecoded(node.span.start.index) + 1,  # + 1 in order to skip the quotation marks
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
		docs = []
		if propertyDoc := super().getDocumentation(node, pos):
			docs.append(propertyDoc)

		if node.parsedValue is not None:
			if valueDoc := getDocumentation(node.parsedValue, b'', pos):
				docs.append(valueDoc)

		return MDStr('\n\n'.join(docs))

	def getCallTips(self, node: JsonString, pos: Position) -> list[str]:
		if node.parsedValue is not None:
			return getCallTips(node.parsedValue, b'', pos)
		return []

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None:
			return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos)


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

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if isinstance(node.schema, JsonKeySchema) and node.schema.forProp.schema is not None and node.schema.forProp.schema.filePath:
			getSession().tryOpenOrSelectDocument(node.schema.forProp.schema.filePath, Span(node.schema.forProp.schema.span.start))


@jsonStringContext(OPTIONS_JSON_ARG_TYPE.name)
class OptionsJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			warningOnly = node.schema.args.get('warningOnly', False)
			style = 'warning' if warningOnly else 'error'
			if node.data not in node.schema.args.get('values', ()):
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format("Option", node.data), node.span, style=style))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if isinstance(node.schema, JsonStringSchema):
			return list(node.schema.args.get('values', ()))
		return []


@jsonStringContext(DPE_FLOAT.name)
class FloatJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		data = node.data
		try:
			if data and data[0] == '-':
				valToCHeck = data[1:]
			else:
				valToCHeck = data
			if valToCHeck.isdigit():
				number = int(data)
			else:
				number = float(data)
			node.parsedValue = number

		except ValueError:
			errorsIO.append(SemanticsError(INVALID_NUMBER_MSG.format(data), span=node.span))

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass  # todo test min max

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []


@jsonStringContext(DPE_JSON_ARG_TYPE.name)
class JsonArgTypeJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass
		if node.data not in ALL_NAMED_JSON_ARG_TYPES:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format("JsonArgType", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return list(ALL_NAMED_JSON_ARG_TYPES.keys())

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		argType = ALL_NAMED_JSON_ARG_TYPES.get(node.data)
		if argType is not None:
			description = argType.description
		else:
			description = MDStr('')

		docs = [
			super(JsonArgTypeJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))


def _getLibrary(dirPath, libraryPath):
	libraryFilePath = joinFilePath(dirPath, libraryPath)
	library = JSON_SCHEMA_LOADER.orchestrator.getSchemaLibrary(path=libraryFilePath)
	return library


@jsonStringContext(DPE_LIB_PATH.name)
class LibPathJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		libraryPath = node
		if isinstance(libraryPath, JsonString):
			library = _getLibrary(dirPath, libraryPath.data)
			libraryFilePath = library.filePath
		else:
			libraryFilePath = None
		node.parsedValue = tree, libraryFilePath, dirPath

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass
		if node.parsedValue is None or node.parsedValue[1] is None:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format("library", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		if node.parsedValue is None or node.parsedValue[1] is None:
			description = MDStr('')
		else:
			description = MDStr(node.parsedValue[1])

		docs = [
			super(LibPathJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			getSession().tryOpenOrSelectDocument(node.parsedValue[1])


@jsonStringContext(DPE_DEF_REF.name, propKey='$definitions', libraryAttr='definitions', unknownMsg="definition")
@jsonStringContext(DPE_TMPL_REF.name, propKey='$templates', libraryAttr='templates', unknownMsg="template")
@dataclass
class TmplRefJsonStrContext(JsonStringContext):
	propKey: str
	libraryAttr: str
	unknownMsg: str

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		if ':' in data:
			ns, _, ref = data.rpartition(':')
			libraryPath = resolvePath(tree, ("$libraries", ns))
			if isinstance(libraryPath, JsonString):
				library = _getLibrary(dirPath, libraryPath.data)
				definition = getattr(library, self.libraryAttr).get(ref)
				libraryFilePath = library.filePath
			else:
				definition = None
				libraryFilePath = None
		else:
			definition = resolvePath(tree, (self.propKey, data))
			libraryFilePath = info.filePath
		node.parsedValue = definition, tree, libraryFilePath, dirPath

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if node.parsedValue is None or node.parsedValue[0] is None:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format(self.unknownMsg, node.data), node.span))
		else:
			pass

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if node.parsedValue is None:
			return []
		tree = node.parsedValue[1]
		definitions = resolvePath(tree, (self.propKey,))
		if not isinstance(definitions, JsonObject):
			definitions = []
		else:
			definitions = list(definitions.data.keys())

		libraries = resolvePath(tree, ("$libraries",))
		if not isinstance(libraries, JsonObject):
			return definitions
		dirPath = node.parsedValue[3]
		for ns, prop in libraries.data.items():
			if isinstance(prop.value.data, str):
				# definition, tree, libraryFilePath, dirPath
				libraryPath = prop.value.data
				library = _getLibrary(dirPath, libraryPath)
				definitions.extend(f'{ns}:{d}' for d in getattr(library, self.libraryAttr).keys())
		return definitions

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		if node.parsedValue is None or node.parsedValue[0] is None:
			return MDStr('')

		description = resolvePath(node.parsedValue[0], ("description",))
		if isinstance(description, JsonString):
			description = MDStr(description.data)
		else:
			description = MDStr('')

		docs = [
			super(TmplRefJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None and node.parsedValue[0] is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: JsonString, pos: Position) -> None:
		if node.parsedValue is not None and node.parsedValue[0] is not None:
			getSession().tryOpenOrSelectDocument(node.parsedValue[2], Span(node.parsedValue[0].span.start))


##########################################################################################
################## Providers for calculated schemas in jsonSchema.json ###################
##########################################################################################


def getStringSchemaArgTypeArgsSchema(parent: JsonObject) -> Optional[JsonObjectSchema]:

	typeProp_ = parent.data.get('type', None)
	type_ = typeProp_.value.data if typeProp_ is not None else None

	jsonArgType = ALL_NAMED_JSON_ARG_TYPES.get(type_) if isinstance(type_, str) else None

	# validate args:
	if jsonArgType is not None:
		if (ctx := getJsonStringContext(jsonArgType.name)) is not None:
			argsSchema, requireArgs = ctx.getArgsSchema()
			return argsSchema
	return None



