"""
predicateArgs are a list of comma separated arguments enclosed in square brackets. e.g.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Callable, ClassVar, Sequence, Iterable, Type

from base.gui.styler import StyleIdEnum, DEFAULT_STYLE_ID, CatStyler
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesOptToStr
from base.model.parsing.contextProvider import Suggestions, Match, getSuggestions, ContextProvider, Context, \
	parseNPrepare, getContext, getDocumentation, getCallTips, getClickableRanges, CtxInfo, prepareTree, validateTree
from base.model.parsing.parser import ParserBase
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema, Node
from base.model.utils import Span, Position, GeneralError, MDStr, LanguageId
from cat.utils import first
from .. import PREDICATE_ARGS_ID
from corePlugins.mcFunction.command import CommandPartSchema, ParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import ResourceLocationNode, ResourceLocationSchema, RESOURCE_LOCATION_ID
from corePlugins.minecraft_data.resourceLocation import ResourceLocation
from corePlugins.nbt import SNBT_ID
from corePlugins.nbt.tags import InvalidTag
from corePlugins.nbtJsonBase.core import StructureDataSchema, STRUCTURE_ANY_SCHEMA, STRUCTURE_ILLEGAL_SCHEMA


def makeArgument(sr: StringReader, schema: CommandPartSchema, key: bytes, value: Any) -> ParsedArgument:
	return ParsedArgument(
		sr.currentSpan,
		schema,
		sr.fullSource,
		key,
		value=value
	)


_INT_MAX = int(2**31) - 1


class PredicateArgSchemaBase(Schema):
	language: ClassVar[LanguageId] = PREDICATE_ARGS_ID

	@property
	def asString(self) -> str:
		return 'PredicateArgSchemaBase'


@dataclass
class PredicateArgNode[TSchema: PredicateArgSchemaBase](Node['PredicateArgNode', TSchema]):
	typeName: ClassVar[str] = 'PredicateArgNode'
	language: ClassVar[LanguageId] = PREDICATE_ARGS_ID


@dataclass
class PredicateArgInfo(PredicateArgSchemaBase):
	name: str = field(default=None, kw_only=True)
	valueSchema: Optional[str] = field(default=None, kw_only=True)
	subPredicateSchema: Optional[str] = field(default=None, kw_only=True)

	def __post_init__(self):
		if self.valueSchema is None and self.subPredicateSchema is None:
			raise ValueError("At least one of (valueSchema, subPredicateSchema) must be set.")

	@property
	def asString(self) -> str:
		return 'PredicateArgInfo'


@dataclass
class PredicateArgOptions(PredicateArgSchemaBase):
	keySchema: ResourceLocationSchema
	getArgsInfo: Callable[[ResourceLocation], PredicateArgInfo]

	@property
	def asString(self) -> str:
		return 'PredicateArgOptions'


@dataclass
class PredicateArg(PredicateArgNode[PredicateArgInfo]):
	typeName: ClassVar[str] = 'PredicateArg'
	key: ResourceLocationNode
	isNegated: bool
	operator: str  # usually '='
	value: StructureDataSchema | None

	@property
	def children(self) -> Sequence[PredicateArgNode]:
		return ()

	@property
	def foreignNodes(self) -> Sequence[Node | None]:
		return self.key, self.value


@dataclass
class PredicateArgUnion(PredicateArgNode[PredicateArgInfo]):
	typeName: ClassVar[str] = 'PredicateArgUnion'
	predicates: list[PredicateArg]

	@property
	def children(self) -> Sequence[PredicateArgNode]:
		return self.predicates


@dataclass
class PredicateArgs(PredicateArgNode[PredicateArgOptions]):
	typeName: ClassVar[str] = 'PredicateArgs'
	arguments: list[PredicateArgUnion]

	@property
	def children(self) -> Sequence[PredicateArgNode]:
		return self.arguments


FALLBACK_FILTER_ARGUMENT_INFO = PredicateArgInfo(
	name='_fallback',
	valueSchema='any',
	subPredicateSchema='any',
	description=''
)


@dataclass
class PredicateArgsParser(ParserBase[PredicateArgs, PredicateArgOptions]):

	def parse(self) -> Optional[PredicateArgs]:
		"""Parses a JSON string into a Python object"""
		value = self._parsePredicateArgs()
		# trailing characters?
		return value

	def _parsePredicateArg(self) -> PredicateArg:
		self.consumeWhitespace()
		p1 = self.currentPos
		isNegated = self.tryConsumeLiteral(b'!')
		self.consumeWhitespace()
		key = self._parseForeignNode(self.schema.keySchema, RESOURCE_LOCATION_ID, ignoreTrailingChars=True)
		if key is None:
			self.error(EXPECTED_MSG.format(self.schema.keySchema.asString()))
			key = ResourceLocationNode(None, '', False, Span(self.currentPos), self.schema.keySchema)
		self.consumeWhitespace()

		p_op1 = self.currentPos
		operator = bytesOptToStr(self.tryConsumeAnyOfLiteral((b'=', b'~')))

		schema = self.schema.getArgsInfo(key)

		if operator is not None:
			p_op2 = self.currentPos
			# parse value / predicate
			if operator == '=':
				nbtSchemaName = schema.valueSchema
				if nbtSchemaName is None:
					self.error(MDStr(f"Predicate Argument '{key.asString}' does not support exact-value matching."), span=Span(p_op1, p_op2))
			else:
				nbtSchemaName = schema.subPredicateSchema
				if nbtSchemaName is None:
					self.error(MDStr(f"Predicate Argument '{key.asString}' does not support sub-predicate matching."), span=Span(p_op1, p_op2))

			nbtSchema = GLOBAL_SCHEMA_STORE.get(nbtSchemaName, SNBT_ID)
			if nbtSchema is None:
				nbtSchema = STRUCTURE_ANY_SCHEMA

			self.consumeWhitespace()
			if self.text.startswith((b'|', b',', b']'), self.cursor):
				self.error(EXPECTED_MSG.format("snbt"))
				value = InvalidTag(Span(self.currentPos), STRUCTURE_ILLEGAL_SCHEMA, '')
			else:
				value = self._parseForeignNode(nbtSchema, SNBT_ID)
		else:
			value = None

		p2 = self.currentPos
		return PredicateArg(Span(p1, p2), schema, key, isNegated, operator, value)

	def _parsePredicateArgsUnion(self) -> PredicateArgUnion:
		predicates = []
		p1 = self.currentPos
		predicates.append(self._parsePredicateArg())

		self.consumeWhitespace()
		while self.tryConsumeLiteral(b'|'):
			self.consumeWhitespace()
			predicates.append(self._parsePredicateArg())
			self.consumeWhitespace()

		p2 = self.currentPos
		return PredicateArgUnion(Span(p1, p2), None, predicates)

	def _parsePredicateArgs(self) -> PredicateArgs:
		arguments = []

		p1 = self.currentPos
		if not self.tryConsumeLiteral(b'['):
			return PredicateArgs(Span(p1), self.schema, arguments)
		self.consumeWhitespace()

		if self.tryConsumeLiteral(b']'):
			p2 = self.currentPos
			return PredicateArgs(Span(p1, p2), self.schema, arguments)

		arguments.append(self._parsePredicateArgsUnion())

		self.consumeWhitespace()
		while self.tryConsumeLiteral(b','):
			self.consumeWhitespace()
			arguments.append(self._parsePredicateArg())
			self.consumeWhitespace()

		self.consumeLiteral(b']')
		p2 = self.currentPos
		return PredicateArgs(Span(p1, p2), self.schema, arguments)

	def _parseForeignNode(self, schema: Schema, language: LanguageId, **kwargs) -> Node | None:
		node, errors, parser = parseNPrepare(
			self.text,
			filePath=self.filePath,
			language=language,
			schema=schema,
			line=self.line,
			lineStart=self.lineStart,
			cursor=self.cursor,
			cursorOffset=self.cursorOffset,
			indexMapper=self.indexMapper,
			**kwargs
		)
		self.errors.extend(errors)
		self.cursor = parser.cursor
		self.line = parser.line
		self.lineStart = parser.lineStart
		return node


@dataclass
class Match2[T: Node]:
	before: list[T]
	hit: list[T]
	after: list[T]


def _getAnyChildNodes(node: Node) -> Sequence[Node]:
	return node.children or node.foreignNodes


def _collectBeforeMatches(node: Node, match: Match2) -> None:
	while (child := first(filter(None, reversed(_getAnyChildNodes(node))), None)) is not None and (child.span.end == node.span.end):
		match.before.append(child)
		node = child


def _collectAfterMatches(node: Node, match: Match2) -> None:
	while (child := first(filter(None, _getAnyChildNodes(node)), None)) is not None and (child.span.start == node.span.start):
		match.after.append(child)
		node = child


def _getBestMatchInChildren2(children: Sequence[Node | None], pos: Position, match: Match2) -> None:
	# it's only a hit if pos is actually INSIDE; pos just touching the start or end is not considered a hit.
	before = None
	for child in children:
		if child is None:
			continue
		if child.span.end <= pos:
			before = child
		elif child.span.start < pos:
			# maybe keep match.before if start == pos?
			before = None
			_getBestMatchInNode2(child, pos, match)
			break
		else:
			match.after.append(child)
			break

	if before is not None:
		match.before.append(before)


def _getBestMatchInNode2(node: Node, pos: Position, match: Match2) -> None:
	match.hit.append(node)
	if (children := node.children) or (children := node.foreignNodes):
		_getBestMatchInChildren2(children, pos, match)
	else:
		match.hit.append(node)


def _getBestMatch2(node: Node, pos: Position) -> Match2[Node]:
	match = Match2([], [], [])
	if node.span.__contains__(pos):
		_getBestMatchInChildren2((node,), pos, match)
		if match.before:
			_collectBeforeMatches(match.before[-1], match)
		if match.after:
			_collectAfterMatches(match.after[-1], match)
	return match


class PredicateArgNodeCtxProvider(ContextProvider[PredicateArgNode]):

	def getBestMatch2(self, pos: Position) -> Match2[Node]:
		return _getBestMatch2(self.tree, pos)

	def getBestMatch(self, pos: Position) -> Match[Node]:
		match2 = _getBestMatch2(self.tree, pos)
		hit = None
		if hit is None:
			hit = match2.after[-1] if match2.after and match2.after[-1].span.start == pos else None
		if hit is None:
			hit = match2.before[-1] if match2.before and match2.before[-1].span.end == pos else None
		if hit is None:
			hit = match2.hit[-1] if match2.hit else None
		return Match(None, hit, None, [])

	def getContext(self, node: PredicateArgNode) -> Optional[Context]:
		if isinstance(node, PredicateArgNode):
			return PREDICATE_ARGUMENTS_CONTEXT
		else:
			return getContext(node, self.text)

	def _prepareAll(self, node: PredicateArgNode, info: CtxInfo, errorsIO: list[GeneralError]) -> None:
		super()._prepareAll(node, info, errorsIO)
		for foreignNode in node.foreignNodes:
			prepareTree(foreignNode, self.text, info.filePath, errorsIO)

	def _validateAll(self, node: Node, errorsIO: list[GeneralError]) -> None:
		super()._validateAll(node, errorsIO)
		for foreignNode in node.foreignNodes:
			validateTree(foreignNode, self.text, errorsIO)

	def getSuggestionsForPredicateArgKey(self, pos: Position, schema: PredicateArgOptions, replaceCtx: str) -> Suggestions:
		key = ResourceLocationNode(None, '', False, Span(pos), schema.keySchema)
		return getSuggestions(key, self.text, pos, replaceCtx)

	def _getSuggestionsForBefore(self, pos: Position, befores: list[Node], hits: list[Node], replaceCtx: str) -> Suggestions:
		before = befores[-1]
		suggestions = []

		if isinstance(before, PredicateArgs):
			if before.span.length == 0:
				suggestions.append(replaceCtx + '[')
			elif not before.arguments:
				suggestions.append('!')
				suggestions.extend(self.getSuggestionsForPredicateArgKey(pos, self.tree.schema, replaceCtx))
				suggestions.append(replaceCtx + ']')
			else:
				return suggestions  # we must be after a properly closed PredicateArgs

		elif isinstance(before, PredicateArgUnion):
			raise ValueError(f"Unexpected type of before {type(before)}.")

		elif isinstance(before, PredicateArg):  # we must be at the end of (or after) operator
			if before.value is not None:
				suggestions.extend(getSuggestions(before.value, self.text, pos, replaceCtx))
			else:
				suggestions.extend([])  # todo suggestions for empty nbt!

		elif isinstance(before, PredicateArgNode):
			raise ValueError(f"Unexpected type of before {type(before)}.")

		else:  # we must be at the end of (or after) the key or value
			suggestions = getSuggestions(before, self.text, pos, replaceCtx)
			before2 = befores[-2] if len(befores) >= 2 else hits[-1]
			if not isinstance(before2, PredicateArg):
				raise ValueError(f"Unexpected type of before2 {type(before2)}.")
			if before2.value is not None:  # we must be at the end of value
				suggestions.extend([replaceCtx + '|', replaceCtx + ',', replaceCtx + ']'])
			elif before2.operator is None and before2.key.isValid:  # we must be at the end of key
				if before2.schema.valueSchema:
					suggestions.append(replaceCtx + '=')
				if before2.schema.subPredicateSchema:
					suggestions.append(replaceCtx + '~')
				suggestions.extend([replaceCtx + '|', replaceCtx + ',', replaceCtx + ']'])

		return suggestions

	def _getSuggestionsForAfter(self, pos: Position, afters: list[Node], hits: list[Node], replaceCtx: str) -> Suggestions:
		after = afters[-1]
		suggestions = []

		if isinstance(after, PredicateArgs):
			suggestions.append(replaceCtx + '[')
		elif isinstance(after, PredicateArgUnion):
			raise ValueError(f"Unexpected type of after {type(after)}.")
		elif isinstance(after, PredicateArg):  # we must be at the beginning of key
			suggestions.append('!')
			suggestions.extend(self.getSuggestionsForPredicateArgKey(pos, self.tree.schema, replaceCtx))
		elif isinstance(after, PredicateArgNode):
			raise ValueError(f"Unexpected type of after {type(after)}.")
		else:
			after2 = afters[-2] if len(afters) >= 2 else hits[-1]
			if not isinstance(after2, PredicateArg):
				raise ValueError(f"Unexpected type of after2 {type(after2)}.")
			if after2.key is after:
				if not after2.isNegated:
					suggestions.append('!')
				suggestions.extend(self.getSuggestionsForPredicateArgKey(pos, self.tree.schema, replaceCtx))
			suggestions.extend(getSuggestions(after, self.text, pos, replaceCtx))

		return suggestions

	def _getSuggestionsForHit(self, pos: Position, hits: list[Node], replaceCtx: str) -> Suggestions:
		hit = hits[-1]
		if isinstance(hit, PredicateArgs):  # PredicateArgs can be a hit if it is empty and pos is between the brackets.
			return self.getSuggestionsForPredicateArgKey(pos, hit.schema, replaceCtx) + [']']
		elif isinstance(hit, PredicateArgNode):
			raise ValueError(f"Unexpected type of hit {type(hit)}.")
		else:
			return getSuggestions(hit, self.text, pos, replaceCtx)

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		match = self.getBestMatch2(pos)

		if match.before:
			return self._getSuggestionsForBefore(pos, match.before, match.hit, replaceCtx)
		elif match.after:
			return self._getSuggestionsForAfter(pos, match.after, match.hit, replaceCtx)
		elif match.hit:
			return self._getSuggestionsForHit(pos, match.hit, replaceCtx)
		else:
			return []

	def getDocumentation(self, pos: Position) -> MDStr:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if isinstance(match.hit, PredicateArgNode):
				if (ctx := self.getContext(match.hit)) is not None:
					return ctx.getDocumentation(match.hit, pos)
			else:
				return getDocumentation(match.hit, self.text, pos)
		return MDStr('')

	def getCallTips(self, pos: Position) -> list[str]:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if isinstance(match.hit, PredicateArgNode):
				if (ctx := self.getContext(match.hit)) is not None:
					return ctx.getCallTips(match.hit, pos)
			else:
				return getCallTips(match.hit, self.text, pos)
		return []

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		ranges: list[Span] = []
		for node in self.tree.walkTree():
			if not node.span.overlaps(span):
				continue
			if isinstance(node, PredicateArg):

				if keyRanges := getClickableRanges(node.key, self.text, span):
					ranges.extend(keyRanges)
				if (value := node.value) is not None:
					if valueRanges := getClickableRanges(value, self.text, span):
						ranges.extend(valueRanges)
		return ranges


class PredicateArgsContext(Context[PredicateArgNode]):
	def validate(self, node: PredicateArgNode, errorsIO: list[GeneralError]) -> None:
		pass

	def getDocumentation(self, node: PredicateArgNode, pos: Position) -> MDStr:
		return MDStr("")

	def getClickableRanges(self, node: PredicateArgNode) -> Optional[Iterable[Span]]:
		pass

	def onIndicatorClicked(self, node: PredicateArgNode, pos: Position) -> None:
		pass

	def getSuggestions(self, node: PredicateArgs, pos: Position, replaceCtx: str, info: CtxInfo[PredicateArgNode]) -> Suggestions:
		return []


PREDICATE_ARGUMENTS_CONTEXT = PredicateArgsContext()


class PredicateArgumentsStyleIds(StyleIdEnum):
	Default = DEFAULT_STYLE_ID


@dataclass
class PredicateArgumentsStyler(CatStyler[PredicateArgNode]):

	@property
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		return PredicateArgumentsStyleIds

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return [SNBT_ID]

	def styleNode(self, node: PredicateArgNode) -> int:
		if node.typeName == PredicateArg.typeName:
			return self.styleStructuredNodeForeignNodes(node, DEFAULT_STYLE_ID)
		else:
			return self.styleStructuredNodeChildNodes(node, DEFAULT_STYLE_ID)


__all__ = [
	'PredicateArgInfo',
	'PredicateArg',
	'PredicateArgOptions',
	'PredicateArgNode',
	'PredicateArgs',
	'FALLBACK_FILTER_ARGUMENT_INFO',
	'PredicateArgsParser',
	'PredicateArgNodeCtxProvider',
	'PredicateArgumentsStyler',
]
