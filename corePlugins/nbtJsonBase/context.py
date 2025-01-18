from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from itertools import chain
from typing import Generator, Iterable, Optional, Callable, cast, Any

from base.model.messages import UNKNOWN_MSG
from base.model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, AddContextToDictDecorator, \
	CtxInfo, getCallTips, parseNPrepare, validateTree, getSuggestions, getDocumentation, getClickableRanges, \
	onIndicatorClicked, prepareTree
from base.model.parsing.tree import Schema
from base.model.pathUtils import FilePath
from base.model.session import getSession
from base.model.utils import Position, SemanticsError, Span, GeneralError, MDStr, LanguageId
from cat.utils import Decorator, flatmap, Anything
from .core import *
from .schema import enrichWithSchema
from .schemaBuilder import SchemaBuilder
from .structureReader import JObject


def _getBestMatchInListLike[N: StructureNode](tree: ListLikeNode[N, StructureDataNode[N]], pos: Position, matches: Match[N]) -> None:
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


def _getBestMatchInObject[N: StructureNode](tree: ObjectNode[N], pos: Position, matches: Match[N]) -> None:
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


def _getBestMatchInProperty[N: StructureNode](tree: StructureProperty[N], pos: Position, matches: Match[N]) -> None:
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


_BEST_MATCHERS: dict[str, Callable[[StructureNode, Position, Match[StructureNode]], None]] = {
	ObjectNode.typeName: cast(Callable[[StructureNode, Position, Match[StructureNode]], None], _getBestMatchInObject),
	ListLikeNode.typeName: cast(Callable[[StructureNode, Position, Match[StructureNode]], None], _getBestMatchInListLike),
	StructureProperty.typeName: cast(Callable[[StructureNode, Position, Match[StructureNode]], None], _getBestMatchInProperty),
}


def _getBestMatch[N: StructureNode](tree: N, pos: Position, matches: Match[N]) -> None:
	if (matcher := _BEST_MATCHERS.get(tree.typeName)) is not None:
		matches.contained.append(tree)
		matcher(tree, pos, matches)
	else:
		matches.hit = tree


def _flattenOptions(schema: UnionSchema, parent: ObjectNode) -> Generator[StructureDataSchema]:
	for opt in schema.allOptions:
		actualOpt = resolveCalculatedSchema(opt, parent)
		if actualOpt is None:
			continue
		elif isinstance(actualOpt, UnionSchema):
			yield from _flattenOptions(actualOpt, parent)
		else:
			yield actualOpt


class StructureCtxProvider[N: StructureNode[N]](ContextProvider[N]):

	def __init__(self, tree: N, text: bytes, requiresStringQuotation: bool):
		super().__init__(tree, text)
		self.requiresStringQuotation: bool = requiresStringQuotation

	def getBestMatch(self, pos: Position) -> Match[N]:
		tree = self.tree
		matches = Match(None, None, None, [])
		if tree.span.__contains__(pos):
			_getBestMatch(tree, pos, matches)
			if matches.before is not None and matches.hit is not None:
				if matches.before.span.end > matches.hit.span.start:
					matches.contained.append(matches.hit)
					matches.hit = None
		return matches

	def getContext(self, node: N) -> Optional[StructureContext]:
		schema = node.schema
		if schema is not None and isinstance(schema, StringSchema) and schema.type is not None:
			return getStringNodeContext(schema.type)
		return STRUCTURE_DEFAULT_CONTEXT
	
	def prepareTree(self, filePath: FilePath, errorsIO: list[GeneralError]) -> None:
		super().prepareTree(filePath, errorsIO)

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		from . import validator2
		validator2.validateStructure(self.tree, errorsIO)

	def _getKeySuggestionsForObject(self, container: ObjectNode, schema: ObjectSchema | UnionSchema, data: bytes) -> list[str]:
		if isinstance(schema, UnionSchema):
			allOptions = list(_flattenOptions(schema, container.parent))
		elif isinstance(schema, ObjectSchema):
			allOptions = (schema,)
		else:
			return []

		if self.requiresStringQuotation:
			prefix = '' if data.startswith(b'"') else '"'
			suffix = '": '
		else:
			prefix = ''
			suffix = chr(data[0]) + ': ' if data.startswith((b'"', b"'")) else ': '

		return [
			f'{prefix}{p.name}{suffix}'
			for opt in allOptions
			if isinstance(opt, ObjectSchema)
			for p in opt.propertiesDict.values()
			if p.name not in container.data and p.getValueSchemaForParent(container) is not None
		]

	def _suggestionsForUnionSchema(self, schema: UnionSchema, contained: list[StructureNode], data: bytes):
		gsfs = functools.partial(self.getSuggestionsForSchema, contained=contained, data=data)
		if contained:
			return list(flatmap(gsfs, _flattenOptions(schema, contained[-1])))  # maybe contained[-2]??
		else:
			return list(flatmap(gsfs, schema.options))

	def _suggestionsForKeySchema(self, schema: KeySchema | None, contained: list[StructureNode], data: bytes):
		if len(contained) >= 2:
			container = contained[-2]  # if hit was a key, matches.contained[-2] is the object.
			if isinstance(container, ObjectNode) and isinstance(container.schema, (ObjectSchema, UnionSchema)):
				return self._getKeySuggestionsForObject(container, container.schema, data)
		return []

	_SCHEMA_SUGGESTIONS_PROVIDERS = {
		AnySchema.typeName: lambda self, schema, contained, data: [],
		NullSchema.typeName: lambda self, schema, contained, data: ['null'],
		BooleanSchema.typeName: lambda self, schema, contained, data: ['true', 'false'],
		NumberSchema.typeName: lambda self, schema, contained, data: ['0'],
		FloatSchema.typeName: lambda self, schema, contained, data: ['0'],
		IntSchema.typeName: lambda self, schema, contained, data: ['0'],
		StringSchema.typeName: lambda self, schema, contained, data: ['"'],
		ListLikeSchema.typeName: lambda self, schema, contained, data: ['['],
		ObjectSchema.typeName: lambda self, schema, contained, data: ['{'],
		UnionSchema.typeName: _suggestionsForUnionSchema,
		KeySchema.typeName: _suggestionsForKeySchema,
	}

	def getSuggestionsForSchema(self, schema: StructureSchema, contained: list[StructureNode], data: bytes) -> list[str]:
		return self._SCHEMA_SUGGESTIONS_PROVIDERS[schema.typeName](self, schema, contained, data)

	def _getSuggestionsForBefore(self, pos: Position, before: N, contained: list[N], replaceCtx: str) -> Suggestions:
		if isinstance(before.schema, KeySchema):
			needsColon = b':' not in self.text[before.span.end.index:pos.index]
			if len(contained) >= 2:
				prop = contained[-1]
				if isinstance(prop, StructureProperty) and prop.schema is not None and contained:
					parent = contained[-2]
					if isinstance(parent, ObjectNode):
						valueSchema = prop.schema.getValueSchemaForParent(parent)
						if valueSchema is not None:
							data = self.text[prop.value.span.slice]
							suggestions = self.getSuggestionsForSchema(valueSchema, contained, data)
							return [f': {sg}' for sg in suggestions] if needsColon else suggestions
			return [': '] if needsColon else []
		elif not contained:
			return []
		else:
			needsComma = b',' not in self.text[before.span.end.index:pos.index]
			return self._getSuggestionsForContained(pos, contained, replaceCtx, needsComma=needsComma)

	def _getSuggestionsForContained(self, pos: Position, contained: list[N], replaceCtx: str, *, needsComma: bool) -> Suggestions:
		if not contained:
			return []
		container = contained[-1]

		if isinstance(container, StructureProperty):
			if len(contained) >= 2:
				container = contained[-2]
			else:
				return []
		if isinstance(container, ListLikeNode):
			if needsComma:
				return [f'{replaceCtx}, ', f'{replaceCtx}]']
			if isinstance(container.schema, ListLikeSchema):
				return self.getSuggestionsForSchema(container.schema.element, contained, b'') + ([']'] if not container.data else [])
		elif isinstance(container, ObjectNode):
			if needsComma:
				return [f'{replaceCtx}, ', f'{replaceCtx}}}']
			if isinstance(container.schema, (ObjectSchema, UnionSchema)):
				return self._getKeySuggestionsForObject(container, container.schema, b'') + (['}'] if not container.data else [])

		return []

	def _getSuggestionsForHit(self, pos: Position, hit: N, contained: list[N], replaceCtx: str) -> Suggestions:
		data = self.text[hit.span.slice]
		if isinstance(hit, StringNode):
			if hit.span.end == pos and len(data) >= 2 and data.endswith(b'"') and data.startswith(b'"'):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)

			elif isinstance(hit.schema, KeySchema):
				suggestions = self._suggestionsForKeySchema(hit.schema, contained, data)
				suggestions.extend(self._getSuggestionsForString(pos, hit, replaceCtx))
				return suggestions
			else:
				return self._getSuggestionsForString(pos, hit, replaceCtx)
		elif hit.schema is not None:
			if hit.span.end == pos and not isinstance(hit, InvalidNode):
				return self._getSuggestionsForBefore(pos, hit, contained, replaceCtx)
			return self.getSuggestionsForSchema(hit.schema, contained, data)
		return []

	def _getSuggestionsForString(self, pos: Position, hit: N, replaceCtx: str):
		if (strHandler := self.getContext(hit)) is not None:
			return strHandler.getSuggestions(hit, pos, replaceCtx=replaceCtx, info=CtxInfo(self, ''))  # TODO: set correct replaceCtx
		else:
			return []

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		matches = self.getBestMatch(pos)
		if not matches.contained:
			return []

		hit = matches.hit
		if hit is not None and hit.typeName is not InvalidNode.typeName:
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
					match: StructureProperty
					if schema.description:
						tips.append(f"###Property '{match.key.data}':")
						tips.append(schema.description)
					break
				else:
					if (strHandler := self.getContext(match)) is not None:
						if doc := strHandler.getDocumentation(match, pos):
							tips.append(doc)

		return MDStr('\n\n'.join(tips))  # '\n<br/>\n'.join(tips)

	def getCallTips(self, pos: Position) -> list[str]:
		return super().getCallTips(pos)

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		ranges: list[Span] = []
		for node in self.tree.walkTree():
			if not node.span.overlaps(span):
				continue
			if (strHandler := self.getContext(node)) is not None:
				partRanges = strHandler.getClickableRanges(node)
				if partRanges:
					ranges.extend(partRanges)
		return ranges


class StructureContext(Context[StructureDataNode]):

	def prepare(self, node: StringNode, info: CtxInfo[StructureNode], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		raise ValueError("StructureContext.validate() should never be called. use validator2.validateStructure(...) instead!")

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		return []

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		return super(StructureContext, self).getDocumentation(node, pos)

	def getClickableRanges(self, node: StringNode) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		pass


STRUCTURE_DEFAULT_CONTEXT = StructureContext()


class StringNodeContext(StructureContext, ABC):
	def validateSchemaArgs(
			self,
			schemaBuilder: SchemaBuilder,
			type_: StructureArgType,
			argsNode: Optional[JObject],
			typeDefNode: JObject,
	):
		expectedArgs, requireArgs = self.getArgsSchema()
		errors = validateSimpleSchemaArgs(type_, argsNode, typeDefNode.span, expectedArgs, requireArgs, typeDefNode.ctx.filePath)
		if errors:
			schemaBuilder.reader.addErrors(errors, ctx=typeDefNode.ctx)

	def getArgsSchema(self) -> tuple[ObjectSchema | UnionSchema | IllegalSchema, bool]:
		"""
		Override this Function if args are required.
		:return: (The schema for args or IllegalSchema if there are no args.; whether the 'args' property is mandatory or not.)
		"""
		return STRUCTURE_ILLEGAL_SCHEMA, False


def orRefSchema(schema: StructureSchema) -> UnionSchema:
	refProperties: list[PropertySchema] = [
		PropertySchema(
			name='$ref',
			value=StringSchema(allowMultilineStr=False),
			optional=False,
			allowMultilineStr=False
		),
		PropertySchema(
			name=Anything,
			value=STRUCTURE_ANY_SCHEMA,
			optional=False,
			allowMultilineStr=None
		),
	]
	schema2 = ObjectSchema(properties=refProperties, allowMultilineStr=None).finish()

	return UnionSchema(options=[schema, schema2], allowMultilineStr=None)


def validateSimpleSchemaArgs(
		type_: StructureArgType,
		argsNode: Optional[JObject],
		parentSpan: Span,
		expectedArgs: ObjectSchema | UnionSchema | IllegalSchema,
		requireArgs: bool,
		filePath: str,
) -> list[GeneralError]:
	from .validator2 import MISSING_MANDATORY_PROPERTY_MSG

	if argsNode is None and requireArgs:
		return [SemanticsError(MISSING_MANDATORY_PROPERTY_MSG.format('args'), parentSpan, style='error')]
	elif isinstance(expectedArgs, IllegalSchema):
		if argsNode is not None and argsNode.data:
			return [SemanticsError(MDStr(f"Unexpected arguments for type '{type_.name}'."), argsNode.span, style='warning')]
	else:
		enrichWithSchema(argsNode.n, expectedArgs)
		errors = []
		prepareTree(argsNode.n, b'', filePath, errorsIO=errors)
		validateTree(argsNode.n, b'', errorsIO=errors)
		return errors


__structureStringContexts: dict[str, StringNodeContext] = {}
structureStringContext = Decorator(AddContextToDictDecorator[StringNodeContext](__structureStringContexts))


def getStringNodeContext(aType: str) -> Optional[StringNodeContext]:
	return __structureStringContexts.get(aType, None)


class ParsingStructureCtx(StringNodeContext, ABC):

	@abstractmethod
	def getSchema(self, node: StringNode) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, node: StringNode) -> LanguageId:
		pass

	def getParserKwArgs(self, node: StringNode) -> dict[str, Any]:
		return {}

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
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
			cursorOffset=node.indexMapper.toDecoded(node.innerSlice.start),
			indexMapper=node.indexMapper,
			fullSource=info.ctxProvider.text,
			**self.getParserKwArgs(node)
		)
		errorsIO.extend(errors)
		node.parsedValue = data

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if node.parsedValue is not None:
			validateTree(node.parsedValue, b'', errorsIO)

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		if node.parsedValue is not None:
			return getSuggestions(node.parsedValue, info.ctxProvider.text, pos, replaceCtx)
		return []

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		docs = []
		if propertyDoc := super().getDocumentation(node, pos):
			docs.append(propertyDoc)

		if node.parsedValue is not None:
			if valueDoc := getDocumentation(node.parsedValue, b'', pos):
				docs.append(valueDoc)

		return MDStr('\n\n'.join(docs))

	def getCallTips(self, node: StringNode, pos: Position) -> list[str]:
		if node.parsedValue is not None:
			return getCallTips(node.parsedValue, b'', pos)
		return []

	def getClickableRanges(self, node: StringNode) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None:
			return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos)


@structureStringContext('dpe:structure/key_schema')
class KeyContext(StringNodeContext):

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		pass

	def getClickableRanges(self, node: StringNode) -> Optional[Iterable[Span]]:
		if isinstance(node.schema, KeySchema) and node.schema.forProp.schema is not None and node.schema.forProp.schema.filePath:
			return (node.span,)

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		if isinstance(node.schema, KeySchema) and node.schema.forProp.schema is not None and node.schema.forProp.schema.filePath:
			getSession().tryOpenOrSelectDocument(node.schema.forProp.schema.filePath, Span(node.schema.forProp.schema.span.start))


@structureStringContext(OPTIONS_STRUCTURE_ARG_TYPE.name)
class OptionsStrContext(StringNodeContext):

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, StringSchema):
			warningOnly = node.schema.args.get('warningOnly', False)
			style = 'warning' if warningOnly else 'error'
			if node.data not in node.schema.args.get('values', ()):
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format("Option", node.data), node.span, style=style))

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		if isinstance(node.schema, StringSchema):
			return list(node.schema.args.get('values', ()))
		return []
