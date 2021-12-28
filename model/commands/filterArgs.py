"""
filterArgs are a list of comma separated arguments enclosed in square brackets. eg.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
import re
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import QWidget

from model.commands.argumentHandlers import getArgumentHandler, makeParsedArgument, missingArgumentParser, Suggestions, makeParsedNode
from model.commands.argumentTypes import *
from model.commands.argumentValues import FilterArguments, FilterArgument
from model.commands.command import ArgumentInfo
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.nbt.snbtParser import EXPECTED_BUT_GOT_MSG
from model.parsingUtils import Span, Position


@dataclass
class FilterArgumentInfo(ArgumentInfo):
	multipleAllowed: bool = False
	isNegatable: bool = False
	canBeEmpty: bool = False


FALLBACK_FILTER_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
)


def parseFilterArgs(sr: StringReader, argsInfo: dict[str, FilterArgumentInfo], *, errorsIO: list[CommandSyntaxError]) -> Optional[FilterArguments]:
	if sr.tryConsumeChar('['):
		# block states:
		arguments: FilterArguments = FilterArguments()
		sr.tryConsumeWhitespace()
		sr.save()
		while not sr.tryConsumeChar(']'):
			sr.mergeLastSave()

			key = sr.tryReadString()
			if key is None:
				sr.save()
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				key = ''
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			elif key not in argsInfo:
				errorsIO.append(CommandSyntaxError(f"Unknown argument '`{key}`'.", sr.currentSpan, style='error'))
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			else:
				tsai = argsInfo[key]

			keyNode = makeParsedNode(sr)
			assert keyNode.content == key, f"keyNode.content = {keyNode.content!r}, key = {key!r}"

			# duplicate?:
			if key in arguments and not tsai.multipleAllowed:
				errorsIO.append(CommandSyntaxError(f"Argument '`{key}`' cannot be duplicated.", sr.currentSpan, style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))
				isNegated = False
				sr.readUntilEndOrRegex(re.compile(r'[],]'))
				valueNode = None
			else:
				sr.tryConsumeWhitespace()
				isNegated = sr.tryConsumeChar('!')
				if isNegated and not tsai.isNegatable:
					errorsIO.append(CommandSyntaxError(f"Argument '`{key}`' cannot be negated.", sr.currentSpan, style='error'))

				handler = getArgumentHandler(tsai.type)
				if handler is None:
					valueNode = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
				else:
					valueNode = handler.parse(sr, tsai, errorsIO=errorsIO)
				if valueNode is None:
					remaining = sr.readUntilEndOrRegex(re.compile(r'[],]'))
					valueNode = makeParsedArgument(sr, tsai, value=remaining)
					errorsIO.append(CommandSyntaxError(f"Expected {tsai.type.name}.", sr.currentSpan, style='error'))
			sr.mergeLastSave()
			arguments.add(key, FilterArgument(keyNode, valueNode, isNegated))

			sr.tryConsumeWhitespace()
			if sr.tryConsumeChar(']'):
				break
			if sr.tryConsumeChar(','):
				sr.tryConsumeWhitespace()
				continue
			if sr.hasReachedEnd:
				errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format(f"`]`", 'end of str'), Span(sr.currentPos), style='error'))
				break
			errorsIO.append(CommandSyntaxError(f"Expected `,` or `]`", Span(sr.currentPos), style='error'))
		return arguments
	else:
		return None


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


def getCursorContext(contextStr: str, cursorPos: int, argsInfo: dict[str, FilterArgumentInfo], fas: FilterArguments) -> CursorCtx:
	assert contextStr
	assert contextStr[0] == '['
	if cursorPos == 1:
		return CursorCtx(None, isValue=False, inside=False, after=False)

	for fa in reversed(fas.values()):
		keySpan = fa.key.span
		if (value := fa.value) is not None:
			valSpan = value.span
			if valSpan.end.index < cursorPos:
				if re.search(r', *$', contextStr[:cursorPos]) is not None:
					return CursorCtx(fa, isValue=False, inside=True)
				else:
					return CursorCtx(fa, isValue=True, after=True)
			elif valSpan.start.index <= cursorPos and not cursorPos <= keySpan.end.index:
				# TODO: check if value is parsable: if not: set after=False
				return CursorCtx(fa, isValue=True, inside=True, after=False)

		if keySpan.end.index < cursorPos:
			if re.search(r'= *$', contextStr[:cursorPos]) is not None:
				return CursorCtx(fa, isValue=True, inside=True)
			else:
				return CursorCtx(fa, isValue=False, after=True)
		elif keySpan.start.index <= cursorPos:
			if (keyMatch := re.search(r'\w+$', contextStr[:cursorPos])) is not None:
				keyStr = keyMatch.group(0)
				return CursorCtx(fa, isValue=False, inside=True, after=keyStr in argsInfo)
			return CursorCtx(fa, isValue=False, inside=True)

	return CursorCtx(None, isValue=False, inside=False, after=False)


def suggestionsForFilterArgs(contextStr: str, cursorPos: int, argsInfo: dict[str, FilterArgumentInfo]) -> Suggestions:
	if cursorPos == 0:
		# if len(contextStr) == 0:
		if not argsInfo:
			return [contextStr + '[]']
		else:
			return [contextStr + '[']
	# elif cursorPos == 1:
	# 	if len(contextStr) >= 1:
	# 		if contextStr[0] == '[':
	#

	if contextStr.startswith('[') and not contextStr.endswith(']'):
		contextStr += ']'
	sr = StringReader(contextStr, 0, 0, contextStr)
	errors = []
	ts = parseFilterArgs(sr, argsInfo, errorsIO=errors)
	if ts is None:
		return []

	cursorTouchesWord = re.search(r'\w*$', contextStr[:cursorPos]).group()

	context = getCursorContext(contextStr, cursorPos, argsInfo, ts)
	if context.fa is None:
		return [cursorTouchesWord + ']'] + [f'{key}=' for key in argsInfo.keys()]

	suggestions: Suggestions = []
	if context.isValue:
		if context.inside:
			if (value := context.fa.value) is not None:
				tsaInfo = value.info
				if isinstance(tsaInfo, ArgumentInfo):
					handler = getArgumentHandler(tsaInfo.type)
					if handler is not None:
						suggestions += handler.getSuggestions(tsaInfo, contextStr, cursorPos)
						# TODO: maybe log if no handler has been found...
		if context.after:
			suggestions.append(cursorTouchesWord + ', ')
			suggestions.append(cursorTouchesWord + ']')
	else:
		if context.after:
			suggestions.append(cursorTouchesWord + '=')
		if context.inside:
			# context.fa is not None, so we already have an '=' after the key, so don't add one here.
			suggestions += [f'{key}' for key in argsInfo.keys()]

	return suggestions


def clickableRangesForFilterArgs(filterArgs: FilterArguments) -> list[Span]:
	ranges = []
	for fa in filterArgs.values():
		if (value := fa.value) is not None:
			argInfo = value.info
			if isinstance(argInfo, ArgumentInfo):
				if (handler := getArgumentHandler(argInfo.type)) is not None:
					if (rng := handler.getClickableRanges(value)) is not None:
						ranges += rng
					# TODO: maybe log if no handler has been found...
	return ranges


def onIndicatorClickedForFilterArgs(filterArgs: FilterArguments, position: Position, window: QWidget) -> None:
	if (match := getBestFAMatch(filterArgs, position.index)) is not None:
		argInfo = match.info
		if isinstance(argInfo, ArgumentInfo):
			if (handler := getArgumentHandler(argInfo.type)) is not None:
				handler.onIndicatorClicked(match, position, window)


__all__ = [
	'FilterArgumentInfo',
	'parseFilterArgs',
	'suggestionsForFilterArgs',
	'clickableRangesForFilterArgs',
	'onIndicatorClickedForFilterArgs',
	# 'FALLBACK_FILTER_ARGUMENT_INFO',
]
