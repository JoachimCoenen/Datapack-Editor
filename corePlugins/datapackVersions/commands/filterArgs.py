"""
filterArgs are a list of comma separated arguments enclosed in square brackets. eg.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from corePlugins.mcFunction.command import ArgumentSchema, CommandPartSchema, FALLBACK_FILTER_ARGUMENT_INFO, FilterArgumentInfo, ParsedArgument, CommandPart
from corePlugins.mcFunction.commandContext import getArgumentContext, missingArgumentParser, makeParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from .argumentValues import FilterArguments, FilterArgument
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import Suggestions, Match, getSuggestions, validateTree
from base.model.pathUtils import FilePath
from base.model.utils import ParsingError, Span, Position, GeneralError, MDStr


def makeCommandPart(sr: StringReader, key: bytes, schema: CommandPartSchema) -> CommandPart:
	argument = CommandPart(
		sr.currentSpan,
		schema,
		sr.fullSource,
		key,
	)
	return argument


def makeArgument(sr: StringReader, schema: CommandPartSchema, key: bytes, value: Any) -> ParsedArgument:
	argument = ParsedArgument(
		sr.currentSpan,
		schema,
		sr.fullSource,
		key,
		value=value
	)
	return argument


_INT_MAX = int(2**31) - 1


@dataclass
class FilterArgOptions:
	opening: bytes
	closing: bytes
	keySchema: ArgumentSchema
	getArgsInfo: Callable[[ParsedArgument], FilterArgumentInfo]
	maxCount: int = _INT_MAX
	minCount: int = 0
	gotoNextArgPattern: re.Pattern[bytes] = field(default=None, kw_only=True)
	openingOrd: int = field(init=False)
	closingOrd: int = field(init=False)
	openingStr: str = field(init=False)
	closingStr: str = field(init=False)

	def __post_init__(self):
		if self.gotoNextArgPattern is None:
			self.gotoNextArgPattern = re.compile(rb'[' + self.closing + b',=]')
		self.openingOrd = ord(self.opening)
		self.closingOrd = ord(self.closing)
		self.openingStr = bytesToStr(self.opening)
		self.closingStr = bytesToStr(self.closing)


def parseFilterArgsLike(
		sr: StringReader,
		options: FilterArgOptions,
		filePath: FilePath,
		*, errorsIO: list[GeneralError]) -> Optional[FilterArguments]:
	sr.save()
	if sr.tryConsumeByte(options.openingOrd):
		# block states:
		count = 0
		arguments = FilterArguments()
		sr.tryConsumeWhitespace()
		sr.save()
		while not sr.tryConsumeByte(options.closingOrd):
			sr.mergeLastSave()

			# key, keyNode, tsai = options.keyParser(sr, argsInfo, filePath, errorsIO)
			keyNode, tsai = parseKey(sr, options, filePath, errorsIO)
			key = keyNode.content

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeByte(ord('=')):
				errorsIO.append(ParsingError(MDStr(f"Expected '`=`'."), Span(sr.currentPos), style='error'))
				isNegated = False
				sr.readUntilEndOrRegex(options.gotoNextArgPattern)
				valueNode = None
			else:
				sr.tryConsumeWhitespace()
				isNegated, valueNode = parseValue(sr, filePath, tsai, key, options.gotoNextArgPattern, errorsIO)
			sr.mergeLastSave()

			# duplicate?:
			multipleAllowed = tsai.multipleAllowed or (tsai.multipleAllowedIfNegated and isNegated)
			if key in arguments and not multipleAllowed:
				if tsai.multipleAllowedIfNegated:
					msg = MDStr(f"Argument '`{bytesToStr(key)}`' testing for equality cannot be duplicated, while argument '`{bytesToStr(key)}`' testing for inequality can.")
				else:
					msg = MDStr(f"Argument '`{bytesToStr(key)}`' cannot be duplicated.")
				errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))

			count += 1
			arguments.add(key, FilterArgument(keyNode, valueNode, isNegated))

			sr.tryConsumeWhitespace()
			if sr.tryConsumeByte(options.closingOrd):
				break

			if sr.tryConsumeByte(ord(',')):
				sr.tryConsumeWhitespace()
				if count == options.maxCount:
					if options.maxCount == 1:
						msg = MDStr(f"Too many arguments. At most one is allowed.")
					else:
						msg = MDStr(f"Too many arguments. At most {options.maxCount} are allowed.")
					errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))
				continue
			if sr.hasReachedEnd:
				errorsIO.append(ParsingError(EXPECTED_BUT_GOT_MSG.format(options.closingStr, 'end of str'), Span(sr.currentPos), style='error'))
				break
			errorsIO.append(ParsingError(EXPECTED_MSG_RAW.format(f"`,` or `{options.closingStr}`"), Span(sr.currentPos), style='error'))

		if count < options.minCount:
			if options.minCount == 1:
				msg = MDStr(f"Too few arguments. At least one is required.")
			else:
				msg = MDStr(f"Too few arguments. At least {options.maxCount} are required.")
			errorsIO.append(ParsingError(msg, sr.currentSpan, style='error'))
	else:
		arguments = None
	sr.mergeLastSave()
	return arguments


def parseValue(sr: StringReader, filePath, tsai: FilterArgumentInfo, key: bytes, gotoNextArgPattern: re.Pattern[bytes], errorsIO: list[GeneralError]) -> tuple[bool, ParsedArgument]:
	isNegated = sr.tryConsumeByte(ord('!'))
	if isNegated and not tsai.isNegatable:
		errorsIO.append(ParsingError(MDStr(f"Argument '`{bytesToStr(key)}`' cannot be negated."), sr.currentSpan, style='error'))
	handler = getArgumentContext(tsai.type)
	if handler is None:
		valueNode = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
	else:
		valueNode = handler.parse(sr, tsai, filePath, errorsIO=errorsIO)
	if valueNode is None:
		remaining = sr.readUntilEndOrRegex(gotoNextArgPattern)
		valueNode = makeParsedArgument(sr, tsai, value=None)
		errorsIO.append(ParsingError(MDStr(f"Expected {tsai.type.name}."), sr.currentSpan, style='error'))
	return isNegated, valueNode


def parseKey(sr: StringReader, options: FilterArgOptions, filePath: FilePath, errorsIO: list[GeneralError]) -> tuple[CommandPart, FilterArgumentInfo]:
	keySchema = options.keySchema
	handler = getArgumentContext(keySchema.type)

	if (keyNode := handler.parse(sr, keySchema, filePath, errorsIO=errorsIO)) is not None:
		if (tsai := options.getArgsInfo(keyNode)) is None:
			errorsIO.append(ParsingError(MDStr(f"Unknown argument '`{bytesToStr(keyNode.content)}`'."), sr.currentSpan, style='error'))
			tsai = FALLBACK_FILTER_ARGUMENT_INFO
	else:
		# errorsIO.append(ParsingError(EXPECTED_MSG.format(keySchema.type.name), Span(sr.currentPos), style='error'))
		key = sr.readUntilEndOrRegex(options.gotoNextArgPattern)
		keyNode = makeArgument(sr, keySchema, key, key)  # or maybe makeArgument(sr, keySchema, key, None). not really sure...
		tsai = FALLBACK_FILTER_ARGUMENT_INFO
		errorsIO.append(ParsingError(MDStr(f"Unknown argument '`{bytesToStr(key)}`'."), sr.currentSpan, style='error'))

	return keyNode, tsai


def validateFilterArgs(fas: FilterArguments, errorsIO: list[GeneralError]) -> None:
	for fa in fas.values():
		validateTree(fa.key, b'', errorsIO)
		validateTree(fa.value, b'', errorsIO)


def getBestFAMatch(fas: FilterArguments, cursorPos: int) -> Optional[ParsedArgument]:
	for fa in fas.values():
		if (value := fa.value) is not None and value.span.start.index <= cursorPos <= value.span.end.index:
			return value
	return None


def _getBestMatch(tree: FilterArguments, pos: Position, matches: Match[CommandPart]) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	for arg in tree.values():
		keySpan = arg.key.span
		if arg.value is not None:
			valueSpan = arg.value.span
			if valueSpan.end < pos:
				matches.before = arg.value
				continue
			elif valueSpan.start < pos:
				if valueSpan.end == pos:
					matches.before = arg.value  # ?
				else:
					matches.before = None
				matches.hit = arg.value
				continue
		if keySpan.end < pos:
			matches.before = arg.key
			matches.after = arg.value
			return
		elif keySpan.start < pos:
			if keySpan.end == pos:
				matches.before = arg.key  # ?
			else:
				matches.before = None
			matches.hit = arg.key
		else:
			matches.after = arg.key
			return


def _getBestMatch2(tree: FilterArguments, pos: Position, matches: Match[CommandPart]) -> None:
	matches.before = None
	matches.hit = None
	matches.after = None
	for arg in tree.values():
		keySpan = arg.key.span
		if arg.value is not None:
			valueSpan = arg.value.span
			if valueSpan.end < pos:
				matches.before = arg.value
				continue
			elif valueSpan.start < pos:
				if valueSpan.end == pos:
					matches.before = arg.value  # ?
				matches.hit = arg.value
				continue
		if keySpan.end < pos:
			matches.before = arg.key
			matches.after = arg.value
			return
		elif keySpan.start < pos:
			if keySpan.end == pos:
				matches.before = arg.key  # ?
			matches.hit = arg.key
		else:
			matches.after = arg.key
			return


@dataclass
class CursorCtx2:
	value: Optional[ParsedArgument]
	inside: bool = False
	after: bool = False

	@property
	def isValue(self) -> bool:
		return self.value is not None


def getCursorContext2(contextStr: bytes, cursorPos: int, pos: Position, fas: FilterArguments) -> CursorCtx2:
	if cursorPos == 1:
		return CursorCtx2(None, inside=False, after=False)

	idxOffset = pos.index - cursorPos

	match = Match(None, None, None, [])
	_getBestMatch(fas, pos, match)

	if (before := match.before) is not None:
		if b',' in contextStr[before.span.end.index - idxOffset:cursorPos]:
			return CursorCtx2(None, inside=False, after=False)
		elif b'=' in contextStr[before.span.end.index - idxOffset:cursorPos]:
			# assert match.after
			return CursorCtx2(match.after, inside=True, after=False)
		else:
			if isinstance(before, ParsedArgument):
				return CursorCtx2(before, inside=match.hit is before, after=True)  # , True, True)  # missing ','
			else:
				return CursorCtx2(None, inside=match.hit is before, after=True)  # , True, True)  # missing '='
	elif (hit := match.hit) is not None:
		if isinstance(hit, ParsedArgument):
			return CursorCtx2(hit, inside=True, after=False)
		else:
			return CursorCtx2(None, inside=True, after=False)
	else:
		return CursorCtx2(None, inside=False, after=False)


def suggestionsForFilterArgs(node: Optional[FilterArguments], contextStr: bytes, cursorPos: int, pos: Position, replaceCtx: str, options: FilterArgOptions) -> Suggestions:
	if node is None or cursorPos == 0:
		return [replaceCtx + options.openingStr]

	if contextStr.startswith(options.opening) and not contextStr.endswith(options.closing):
		contextStr += options.closing

	if node is None:
		return []

	cursorTouchesWord = re.search(rb'\w*$', contextStr[:cursorPos]).group()
	cursorTouchesWord = bytesToStr(cursorTouchesWord)

	assert contextStr
	assert contextStr[0] == options.openingOrd, contextStr
	context = getCursorContext2(contextStr, cursorPos, pos, node)
	if context.value is None and context.after is False and context.inside is False:  # and re.search(rb'\[\s*$', contextStr[:cursorPos]) is not None:
		return [cursorTouchesWord + options.closingStr] + _getKeySuggestions(options, context.value, False)

	suggestions: Suggestions = []
	if context.isValue:
		if context.inside:
			if (value := context.value) is not None:
				tsaInfo = value.schema
				if isinstance(tsaInfo, ArgumentSchema):
					handler = getArgumentContext(tsaInfo.type)
					if handler is not None:
						suggestions += [sg.rstrip() for sg in handler.getSuggestions2(tsaInfo, value, pos, replaceCtx)]
						# TODO: maybe log if no handler has been found...
		if context.after:
			suggestions.append(cursorTouchesWord + ', ')
			suggestions.append(cursorTouchesWord + options.closingStr)
	else:
		if context.after and not context.inside:
			suggestions.append(cursorTouchesWord + '=')
		if context.inside:
			# context.fa is not None, so we already have an '=' after the key, so don't add one here.
			suggestions += _getKeySuggestions(options, context.value, False)

	return suggestions


def _getKeySuggestions(options: FilterArgOptions, node: Optional[ParsedArgument], addComma: bool):
	if node is None:
		node = ParsedArgument(Span(Position(0, 0, 0)), options.keySchema, b'', b'', b'')
	suggestions = getSuggestions(node, b'', Position(0, 0, 0), '')

	if addComma:
		return [f', {suggestion}' for suggestion in suggestions]
	else:
		return suggestions


def clickableRangesForFilterArgs(filterArgs: FilterArguments) -> list[Span]:
	ranges = []
	for fa in filterArgs.values():
		if (value := fa.value) is not None:
			argInfo = value.schema
			if isinstance(argInfo, ArgumentSchema):
				if (handler := getArgumentContext(argInfo.type)) is not None:
					if (rng := handler.getClickableRanges(value)) is not None:
						ranges += rng
					# TODO: maybe log if no handler has been found...
	return ranges


def onIndicatorClickedForFilterArgs(filterArgs: FilterArguments, position: Position) -> None:
	if (match := getBestFAMatch(filterArgs, position.index)) is not None:
		argInfo = match.schema
		if isinstance(argInfo, ArgumentSchema):
			if (handler := getArgumentContext(argInfo.type)) is not None:
				handler.onIndicatorClicked(match, position)


__all__ = [
	'FilterArgOptions',
	'parseFilterArgsLike',
	'validateFilterArgs',
	'suggestionsForFilterArgs',
	'clickableRangesForFilterArgs',
	'onIndicatorClickedForFilterArgs',
	# 'FALLBACK_FILTER_ARGUMENT_INFO',
]
