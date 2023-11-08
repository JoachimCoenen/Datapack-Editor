"""
filterArgs are a list of comma separated arguments enclosed in square brackets. eg.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
import re
from dataclasses import dataclass
from typing import Optional

from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, ParsedArgument, CommandPart
from corePlugins.mcFunction.commandContext import getArgumentContext, missingArgumentParser, makeParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from .argumentValues import FilterArguments, FilterArgument
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import Suggestions, Match
from base.model.pathUtils import FilePath
from base.model.utils import ParsingError, Span, Position, GeneralError, MDStr


@dataclass
class FilterArgumentInfo(ArgumentSchema):
	multipleAllowed: bool = False
	isNegatable: bool = False
	canBeEmpty: bool = False


FALLBACK_FILTER_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
	description=''
)


def makeCommandPart(sr: StringReader, key: bytes) -> CommandPart:
	argument = CommandPart(
		sr.currentSpan,
		None,
		sr.fullSource,
		key,
	)
	return argument


def parseFilterArgs(sr: StringReader, argsInfo: dict[bytes, FilterArgumentInfo], filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[FilterArguments]:
	if sr.tryConsumeByte(ord('[')):
		# block states:
		arguments: FilterArguments = FilterArguments()
		sr.tryConsumeWhitespace()
		sr.save()
		while not sr.tryConsumeByte(ord(']')):
			sr.mergeLastSave()

			key: bytes = sr.tryReadString()
			if key is None:
				sr.save()
				errorsIO.append(ParsingError(MDStr(f"Expected a String."), Span(sr.currentPos), style='error'))
				key = b''
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			elif key not in argsInfo:
				errorsIO.append(ParsingError(MDStr(f"Unknown argument '`{bytesToStr(key)}`'."), sr.currentSpan, style='error'))
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			else:
				tsai = argsInfo[key]

			keyNode = makeCommandPart(sr, key)
			assert keyNode.content == key, f"keyNode.content = {keyNode.content!r}, key = {bytesToStr(key)!r}"

			# duplicate?:
			if key in arguments and not tsai.multipleAllowed:
				errorsIO.append(ParsingError(MDStr(f"Argument '`{bytesToStr(key)}`' cannot be duplicated."), sr.currentSpan, style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeByte(ord('=')):
				errorsIO.append(ParsingError(MDStr(f"Expected '`=`'."), Span(sr.currentPos), style='error'))
				isNegated = False
				sr.readUntilEndOrRegex(re.compile(rb'[],]'))
				valueNode = None
			else:
				sr.tryConsumeWhitespace()
				isNegated = sr.tryConsumeByte(ord('!'))
				if isNegated and not tsai.isNegatable:
					errorsIO.append(ParsingError(MDStr(f"Argument '`{bytesToStr(key)}`' cannot be negated."), sr.currentSpan, style='error'))

				handler = getArgumentContext(tsai.type)
				if handler is None:
					valueNode = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
				else:
					valueNode = handler.parse(sr, tsai, filePath, errorsIO=errorsIO)
				if valueNode is None:
					remaining = sr.readUntilEndOrRegex(re.compile(rb'[],]'))
					valueNode = makeParsedArgument(sr, tsai, value=remaining)
					errorsIO.append(ParsingError(MDStr(f"Expected {tsai.type.name}."), sr.currentSpan, style='error'))
			sr.mergeLastSave()
			arguments.add(key, FilterArgument(keyNode, valueNode, isNegated))

			sr.tryConsumeWhitespace()
			if sr.tryConsumeByte(ord(']')):
				break
			if sr.tryConsumeByte(ord(',')):
				sr.tryConsumeWhitespace()
				continue
			if sr.hasReachedEnd:
				errorsIO.append(ParsingError(EXPECTED_BUT_GOT_MSG.format(f"`]`", 'end of str'), Span(sr.currentPos), style='error'))
				break
			errorsIO.append(ParsingError(MDStr(f"Expected `,` or `]`"), Span(sr.currentPos), style='error'))
		return arguments
	else:
		return None


def validateFilterArgs(fas: FilterArguments, argsInfo: dict[bytes, FilterArgumentInfo], errorsIO: list[GeneralError]) -> None:
	pass  # TODO: implement validateFilterArgs(...)


def getBestFAMatch(fas: FilterArguments, cursorPos: int) -> Optional[ParsedArgument]:
	for fa in fas.values():
		if (value := fa.value) is not None and value.span.start.index <= cursorPos <= value.span.end.index:
			return value
	return None


@dataclass
class CursorCtx:
	fa: Optional[FilterArgument]
	isValue: bool
	inside: bool = False
	after: bool = False


def getCursorContext(contextStr: bytes, cursorPos: int, pos: Position, argsInfo: dict[bytes, FilterArgumentInfo], fas: FilterArguments) -> CursorCtx:
	assert contextStr
	assert contextStr[0] == ord('[')
	if cursorPos == 1:
		return CursorCtx(None, isValue=False, inside=False, after=False)

	for fa in reversed(fas.values()):
		keySpan = fa.key.span
		if (value := fa.value) is not None:
			valSpan = value.span
			if valSpan.end < pos:
				if re.search(rb', *$', contextStr[:cursorPos]) is not None:
					return CursorCtx(fa, isValue=False, inside=True)
				else:
					return CursorCtx(fa, isValue=True, after=True)
			elif valSpan.start <= pos and not pos <= keySpan.end:
				# TODO: check if value is parsable: if not: set after=False
				return CursorCtx(fa, isValue=True, inside=True, after=False)

		if keySpan.end < pos:
			if re.search(rb'= *$', contextStr[:cursorPos]) is not None:
				return CursorCtx(fa, isValue=True, inside=True)
			else:
				return CursorCtx(fa, isValue=False, after=True)
		elif keySpan.start <= pos:
			if (keyMatch := re.search(rb'\w+$', contextStr[:cursorPos])) is not None:
				keyStr = keyMatch.group(0)
				return CursorCtx(fa, isValue=False, inside=True, after=keyStr in argsInfo)
			return CursorCtx(fa, isValue=False, inside=True)

	return CursorCtx(None, isValue=False, inside=False, after=False)


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


def getCursorContext2(contextStr: bytes, cursorPos: int, pos: Position, argsInfo: dict[bytes, FilterArgumentInfo], fas: FilterArguments) -> CursorCtx2:
	assert contextStr
	assert contextStr[0] == ord('[')
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


def suggestionsForFilterArgs(node: Optional[FilterArguments], contextStr: bytes, cursorPos: int, pos: Position, replaceCtx: str, argsInfo: dict[bytes, FilterArgumentInfo]) -> Suggestions:
	if node is None or cursorPos == 0:
		# if len(contextStr) == 0:
		if not argsInfo:
			return [replaceCtx + '[]']
		else:
			return [replaceCtx + '[']
	# elif cursorPos == 1:
	# 	if len(contextStr) >= 1:
	# 		if contextStr[0] == '[':
	#
	if contextStr.startswith(b'[') and not contextStr.endswith(b']'):
		contextStr += b']'

	if node is None:
		return []

	cursorTouchesWord = re.search(rb'\w*$', contextStr[:cursorPos]).group()
	cursorTouchesWord = bytesToStr(cursorTouchesWord)

	context = getCursorContext2(contextStr, cursorPos, pos, argsInfo, node)
	# context = getCursorContext(contextStr, cursorPos, pos, argsInfo, node)
	if context.value is None and context.after is False and context.inside is False:  # and re.search(rb'\[\s*$', contextStr[:cursorPos]) is not None:
		return [cursorTouchesWord + ']'] + _getKeySuggestions(argsInfo, False)

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
			suggestions.append(cursorTouchesWord + ']')
	else:
		if context.after and not context.inside:
			suggestions.append(cursorTouchesWord + '=')
		if context.inside:
			# context.fa is not None, so we already have an '=' after the key, so don't add one here.
			suggestions += _getKeySuggestions(argsInfo, False)

	return suggestions


def _getKeySuggestions(argsInfo: dict[bytes, FilterArgumentInfo], addComma: bool):
	if addComma:
		return [f', {bytesToStr(key)}=' for key in argsInfo.keys()]
	else:
		return [f'{bytesToStr(key)}=' for key in argsInfo.keys()]


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
	'FilterArgumentInfo',
	'parseFilterArgs',
	'validateFilterArgs',
	'suggestionsForFilterArgs',
	'clickableRangesForFilterArgs',
	'onIndicatorClickedForFilterArgs',
	# 'FALLBACK_FILTER_ARGUMENT_INFO',
]
