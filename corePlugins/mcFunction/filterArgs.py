"""
filterArgs are a list of comma separated arguments enclosed in square brackets. e.g.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
from __future__ import annotations

import re
from _warnings import warn
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Collection, ClassVar

from better_orderedmultidict import OrderedMultiDict

from base.model.parsing.parser import ParserBase
from cat.utils import Nothing
from . import FILTER_ARGS_ID
from .argumentTypes import BRIGADIER_STRING
from .command import ArgumentSchema, CommandPartSchema, ParsedArgument, CommandPart
from .commandContext import getArgumentContext, missingArgumentParser, makeParsedArgument, CommandCtxProvider
from .stringReader import StringReader
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import Suggestions, Match, getSuggestions, ContextProvider, Context, \
	StructuredContext, CtxInfo
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePath
from base.model.utils import ParsingError, Span, Position, GeneralError, MDStr, LanguageId


def makeArgument(sr: StringReader, schema: CommandPartSchema, key: bytes, value: Any) -> ParsedArgument:
	return ParsedArgument(
		sr.currentSpan,
		schema,
		sr.fullSource,
		key,
		value=value
	)


_INT_MAX = int(2**31) - 1


class FilterArgSchemaBase(Schema):
	language: ClassVar[LanguageId] = FILTER_ARGS_ID

	@property
	def asString(self) -> str:
		return 'FilterArgSchemaBase'


@dataclass
class FilterArgNode[TSchema: FilterArgSchemaBase](Node['FilterArgNode', TSchema]):
	typeName: ClassVar[str] = 'FilterArgNode'
	language: ClassVar[LanguageId] = FILTER_ARGS_ID


@dataclass
class FilterArgumentInfo(FilterArgSchemaBase):
	name: str = field(default=None, kw_only=True)
	valueSchema: ArgumentSchema = field(default=None, kw_only=True)
	multipleAllowed: bool = field(default=False, kw_only=True)  # overrides multipleAllowedIfNegated field
	multipleAllowedIfNegated: bool = field(default=False, kw_only=True)
	isNegatable: bool = field(default=False, kw_only=True)  # '!' after the '='.
	canBeEmpty: bool = field(default=False, kw_only=True)
	defaultValue: Any = field(default=Nothing, kw_only=True)

	def __post_init__(self) -> None:
		if self.multipleAllowed and self.multipleAllowedIfNegated:
			warn("Both `multipleAllowed` and `multipleAllowedIfNegated` are set to True. This is probably not intentional.", RuntimeWarning, 3)
		if self.multipleAllowedIfNegated and not self.isNegatable:
			warn("`multipleAllowedIfNegated` is set to True, but `isNegatable` is False. This is probably not intentional.", RuntimeWarning, 3)

	@property
	def asString(self) -> str:
		return 'FilterArgumentInfo'


@dataclass
class FilterArgument(FilterArgNode[FilterArgumentInfo]):
	typeName: ClassVar[str] = 'FilterArgument'
	key: CommandPart
	value: Optional[ParsedArgument]
	isNegated: bool

	@property
	def children(self) -> Collection[FilterArgNode]:
		return ()

	@property
	def foreignNodes(self) -> Collection[Node | None]:
		return self.key, self.value


@dataclass
class FilterArgOptions(FilterArgSchemaBase):
	opening: bytes
	closing: bytes
	keySchema: ArgumentSchema
	getArgsInfo: Callable[[ParsedArgument], FilterArgumentInfo]
	maxCount: int = _INT_MAX
	minCount: int = 0
	gotoNextArgPattern: re.Pattern[bytes] = field(default=None, kw_only=True)
	openingOrd: int = field(init=False, repr=False)
	closingOrd: int = field(init=False, repr=False)
	openingStr: str = field(init=False, repr=False)
	closingStr: str = field(init=False, repr=False)

	def __post_init__(self) -> None:
		if self.gotoNextArgPattern is None:
			self.gotoNextArgPattern = re.compile(rb'[' + self.closing + b',=]')  # somehow works, even if self.closing == b']'
		self.openingOrd = ord(self.opening)
		self.closingOrd = ord(self.closing)
		self.openingStr = bytesToStr(self.opening)
		self.closingStr = bytesToStr(self.closing)

	@property
	def asString(self) -> str:
		return 'FilterArgOptions'


@dataclass
class FilterArguments(FilterArgNode[FilterArgOptions]):
	typeName: ClassVar[str] = 'FilterArguments'
	source: bytes = field(repr=False)
	arguments: OrderedMultiDict[bytes, FilterArgument]

	@property
	def children(self) -> Collection[FilterArgument]:
		return self.arguments.values()


FALLBACK_FILTER_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	valueSchema=ArgumentSchema(
		name='_fallback',
		type=BRIGADIER_STRING,
		description=''
	),
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
	description=''
)


def parseFilterArgsLike(
		sr: StringReader,
		options: FilterArgOptions,
		filePath: FilePath,
		*, errorsIO: list[GeneralError]
) -> FilterArguments:
	arguments: OrderedMultiDict[bytes, FilterArgument] = OrderedMultiDict()
	sr.save()
	if sr.tryConsumeByte(options.openingOrd):
		sr.tryConsumeWhitespace()
		if sr.hasReachedEnd:
			errorsIO.append(ParsingError(EXPECTED_MSG_RAW.format(f"key or `{options.closingStr}`"), Span(sr.currentPos), style='error'))

		while not sr.tryConsumeByte(options.closingOrd) and not sr.hasReachedEnd:
			sr.save()
			# key, keyNode, tsai = options.keyParser(sr, argsInfo, filePath, errorsIO)
			keyNode, tsai = parseKey(sr, options, filePath, errorsIO)
			key = keyNode.content

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeByte(ord('=')):
				errorsIO.append(ParsingError(MDStr(f"Expected '`=`'."), Span(sr.currentPos), style='error'))
				sr.readUntilEndOrRegex(options.gotoNextArgPattern)
				sr.mergeLastSave()
				valueNode = None
				isNegated = False
			else:
				sr.tryConsumeWhitespace()
				isNegated, valueNode = parseValue(sr, filePath, tsai, key, options, errorsIO)

			# duplicate?:
			checkDuplicate(arguments, isNegated, key, tsai, sr, errorsIO)

			arguments.add(key, FilterArgument(sr.currentSpan, tsai, keyNode, valueNode, isNegated))

			sr.tryConsumeWhitespace()
			checkAndConsumeComma(options, sr, errorsIO)
			sr.mergeLastSave()
			continue

		checkMaxArgumentCount(arguments, options, sr, errorsIO)

	checkMinArgumentCount(arguments, options, sr, errorsIO)

	argsSpan = sr.currentSpan
	startC = argsSpan.start.column
	endC = argsSpan.end.column
	if startC != endC:  # if we have filter args specified:
		assert sr.text[startC] == options.openingOrd, f"start mismatch: {sr.text[startC:endC]=!r}, {chr(options.openingOrd)=!r}"

	return FilterArguments(argsSpan, options, sr.fullSource, arguments)


def checkAndConsumeComma(options: FilterArgOptions, sr: StringReader, errorsIO: list[GeneralError]):
	if sr.tryConsumeByte(ord(',')):  # allow trailing comma.
		p1 = sr.currentPos
		whitespaceAfterComma = sr.tryConsumeWhitespace()
		isTrailingComma = sr.tryPeek() == options.closingOrd
		if isTrailingComma:
			if whitespaceAfterComma:
				msg = MDStr(f"No space after trailing comma allowed.")
				p2 = sr.currentPos
				errorsIO.append(ParsingError(msg, Span(p1, p2), style='error'))

	elif sr.tryPeek() != options.closingOrd:
		errorsIO.append(
			ParsingError(EXPECTED_MSG_RAW.format(f"`,` or `{options.closingStr}`"), Span(sr.currentPos), style='error'))


def checkDuplicate(arguments: OrderedMultiDict[bytes, FilterArgument], isNegated: bool, key: bytes, tsai: FilterArgumentInfo, sr: StringReader, errorsIO: list[GeneralError]) -> None:
	multipleAllowed = tsai.multipleAllowed or (tsai.multipleAllowedIfNegated and isNegated)
	if key in arguments and not multipleAllowed:
		if tsai.multipleAllowedIfNegated:
			msg = MDStr(f"Testing argument '`{bytesToStr(key)}`' for equality cannot be duplicated. (but testing for inequality can be.)")
		else:
			msg = MDStr(f"Argument '`{bytesToStr(key)}`' cannot be duplicated.")
		errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))


def checkMaxArgumentCount(arguments: OrderedMultiDict[bytes, FilterArgument], options: FilterArgOptions, sr: StringReader, errorsIO: list[GeneralError]) -> None:
	if len(arguments) == options.maxCount:
		if options.maxCount == 1:
			msg = MDStr(f"Too many arguments. At most one is allowed.")
		else:
			msg = MDStr(f"Too many arguments. At most {options.maxCount} are allowed.")
		errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))


def checkMinArgumentCount(arguments: OrderedMultiDict[bytes, FilterArgument], options: FilterArgOptions, sr: StringReader, errorsIO: list[GeneralError]) -> None:
	if len(arguments) < options.minCount:
		if options.minCount == 1:
			msg = MDStr(f"Too few arguments. At least one is required.")
		else:
			msg = MDStr(f"Too few arguments. At least {options.minCount} are required.")
		errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))


def parseValue(sr: StringReader, filePath, tsai: FilterArgumentInfo, key: bytes, options: FilterArgOptions, errorsIO: list[GeneralError]) -> tuple[bool, ParsedArgument | None]:
	isNegated = sr.tryConsumeByte(ord('!'))
	if not tsai.isNegatable and isNegated:
		errorsIO.append(ParsingError(MDStr(f"Argument '`{bytesToStr(key)}`' cannot be negated."), sr.currentSpan, style='error'))

	valueSchema = tsai.valueSchema
	handler = getArgumentContext(valueSchema.type)
	if handler is None:
		valueNode = missingArgumentParser(sr, valueSchema, errorsIO=errorsIO)
	else:
		valueNode = handler.parse(sr, valueSchema, filePath, errorsIO=errorsIO)
		if valueNode is not None:
			sr.mergeLastSave()

	if valueNode is None and not tsai.canBeEmpty:
		sr.readUntilEndOrRegex(options.gotoNextArgPattern)
		valueNode = makeParsedArgument(sr, valueSchema, value=None)
		errorsIO.append(ParsingError(MDStr(f"Expected {valueSchema.type.name}."), sr.currentSpan, style='error'))
		sr.mergeLastSave()
	else:
		pass

	return isNegated, valueNode


def parseKey(sr: StringReader, options: FilterArgOptions, filePath: FilePath, errorsIO: list[GeneralError]) -> tuple[CommandPart, FilterArgumentInfo]:
	keySchema = options.keySchema
	handler = getArgumentContext(keySchema.type)

	if (keyNode := handler.parse(sr, keySchema, filePath, errorsIO=errorsIO)) is not None:
		if (tsai := options.getArgsInfo(keyNode)) is None:
			errorsIO.append(ParsingError(MDStr(f"Unknown argument '`{bytesToStr(keyNode.content)}`'."), sr.currentSpan, style='error'))
			tsai = FALLBACK_FILTER_ARGUMENT_INFO
	else:
		key = sr.readUntilEndOrRegex(options.gotoNextArgPattern)
		keyNode = makeArgument(sr, keySchema, key, key)  # or maybe makeArgument(sr, keySchema, key, None). not really sure...
		tsai = FALLBACK_FILTER_ARGUMENT_INFO
		errorsIO.append(ParsingError(MDStr(f"Unknown argument '`{bytesToStr(key)}`'."), sr.currentSpan, style='error'))

	sr.mergeLastSave()
	return keyNode, tsai


@dataclass
class FilterArgumentsParser(ParserBase[FilterArguments, FilterArgOptions]):
	def parse(self) -> Optional[FilterArguments]:
		virtualLine = self.text
		cursorOffset = self.cursorOffset
		cursor = self.cursor
		reader = StringReader(virtualLine, self.line, self.lineStart, cursor, cursorOffset, self.indexMapper, self.fullSource)
		result = parseFilterArgsLike(reader, self.schema, self.filePath, errorsIO=self.errors)
		self.cursor = reader.cursor
		return result


class FilterArgNodeCtxProvider(ContextProvider[FilterArgNode]):

	def getBestMatch(self, pos: Position) -> Match[FilterArgNode]:
		return Match(None, self.tree, None, [])

	def getContext(self, node: FilterArgNode) -> Optional[Context]:
		return FILTER_ARGUMENTS_CONTEXT


class FilterArgumentsContext(StructuredContext[FilterArguments]):
	def getSuggestions(self, node: FilterArguments, pos: Position, replaceCtx: str, info: CtxInfo[FilterArguments]) -> Suggestions:
		argsStart = node.span.start
		contextStr = node.source[argsStart.index:node.span.end.index]
		cursorPos = pos.index - argsStart.index

		options: FilterArgOptions = node.schema

		if cursorPos == 0:
			return [replaceCtx + options.openingStr]

		if contextStr.startswith(options.opening) and not contextStr.endswith(options.closing):
			contextStr += options.closing

		if node is None:
			return []

		cursorTouchesWord = re.search(rb'\w*$', contextStr[:cursorPos]).group()
		cursorTouchesWord = bytesToStr(cursorTouchesWord)

		assert contextStr
		assert contextStr[0] == options.openingOrd, f"{contextStr=!r}, {options.openingOrd=!r}"
		context = getCursorContext2(contextStr, cursorPos, pos, node)
		if context.value is None and context.after is False and context.inside is False:  # and re.search(rb'\[\s*$', contextStr[:cursorPos]) is not None:
			return [cursorTouchesWord + options.closingStr] + _getKeySuggestions(options, context.key, pos, replaceCtx, False, info)

		suggestions: Suggestions = []
		if context.isValue:
			if context.inside:
				if (value := context.value) is not None:
					tsaInfo = value.schema
					if isinstance(tsaInfo, ArgumentSchema):
						handler = getArgumentContext(tsaInfo.type)
						if handler is not None:
							suggestions += [sg.rstrip() for sg in handler.getSuggestions2(tsaInfo, value, pos, replaceCtx, info)]
							# TODO: maybe log if no handler has been found...
			if context.after:
				suggestions.append(cursorTouchesWord + ', ')
				suggestions.append(cursorTouchesWord + options.closingStr)
		else:
			if context.after:
				suggestions.append(cursorTouchesWord + '=')
			if context.inside:
				# context.fa is not None, so we already have an '=' after the key, so don't add one here.
				suggestions += _getKeySuggestions(options, context.key, pos, replaceCtx, False, info)

		return suggestions


FILTER_ARGUMENTS_CONTEXT = FilterArgumentsContext()


def _getBestMatchInFilterArgument(tree: FilterArgument, pos: Position, match: Match) -> None:
	match.contained.append(tree)
	match.before = None
	match.hit = tree
	match.after = None
	if tree.value is not None:
		valueSpan = tree.value.span
		if valueSpan.end <= pos:
			match.before = tree.value
			if valueSpan.end == pos:
				match.hit = tree.value
			return
		elif valueSpan.start < pos:
			# matches.before = tree.key  # TODO this seems to be wrong?
			match.hit = tree.value
			return
	keySpan = tree.key.span
	if keySpan.end <= pos:
		match.before = tree.key
		match.after = tree.value
		if keySpan.end == pos:
			match.hit = tree.key
	elif keySpan.start < pos:
		match.hit = tree.key
	# matches.after = tree.value
	else:
		match.after = tree.key


def _getBestMatchInFilterArguments(tree: FilterArguments, pos: Position, match: Match) -> None:
	match.contained.append(tree)
	for arg in tree.arguments.values():
		if arg.span.__contains__(pos):
			_getBestMatchInFilterArgument(arg, pos, match)
			break


@dataclass
class CursorCtx2:
	value: Optional[ParsedArgument]
	key: Optional[ParsedArgument]
	inside: bool = False
	after: bool = False

	@property
	def isValue(self) -> bool:
		return self.value is not None


def getCursorContext2(contextStr: bytes, cursorPos: int, pos: Position, fas: FilterArguments) -> CursorCtx2:
	if cursorPos == 1:
		return CursorCtx2(None, None, inside=False, after=False)

	idxOffset = pos.index - cursorPos

	match = Match(None, None, None, [])
	_getBestMatchInFilterArguments(fas, pos, match)

	if (before := match.before) is not None:
		isKey = match.contained and isinstance(match.contained[-1], FilterArgument) and match.contained[-1].key is match.before

		if b',' in contextStr[before.span.end.index - idxOffset:cursorPos]:
			return CursorCtx2(None, None, inside=False, after=False)
		elif b'=' in contextStr[before.span.end.index - idxOffset:cursorPos]:
			# assert match.after
			return CursorCtx2(match.after, None, inside=True, after=False)
		else:
			if not isKey and isinstance(before, ParsedArgument):
				return CursorCtx2(before, None, inside=match.hit is before, after=True)  # , True, True)  # missing ','
			else:
				return CursorCtx2(None, before if isKey else None, inside=match.hit is before, after=True)  # , True, True)  # missing '='
	elif (hit := match.hit) is not None:
		isKey = match.contained and isinstance(match.contained[-1], FilterArgument) and match.contained[-1].key is match.hit
		if not isKey and isinstance(hit, ParsedArgument):
			return CursorCtx2(hit, None, inside=True, after=False)
		else:
			return CursorCtx2(None, hit if isKey else None, inside=True, after=False)
	else:
		return CursorCtx2(None, None, inside=False, after=False)


def _getKeySuggestions(options: FilterArgOptions, node: Optional[ParsedArgument], pos: Position, replaceCtx: str, addComma: bool, info: CtxInfo[FilterArguments]):
	if node is None:
		ctxProvider = CommandCtxProvider(ParsedArgument(Span(pos), options.keySchema, info.ctxProvider.text, b'', b''), info.ctxProvider.text)
		suggestions = ctxProvider.getSuggestionsForNext((options.keySchema,), None, pos, replaceCtx)
	else:
		suggestions = getSuggestions(node, info.ctxProvider.text, pos, replaceCtx)

	if addComma:
		return [f', {suggestion.strip()}' for suggestion in suggestions]
	else:
		return [suggestion.strip() for suggestion in suggestions]


__all__ = [
	'FilterArgumentInfo',
	'FilterArgument',
	'FilterArgOptions',
	'FilterArgNode',
	'FilterArguments',
	'FALLBACK_FILTER_ARGUMENT_INFO',
	'parseFilterArgsLike',
	'FilterArgumentsParser',
	'FilterArgNodeCtxProvider',
]
