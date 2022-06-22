"""
filterArgs are a list of comma separated arguments enclosed in square brackets. eg.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
import re
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import QWidget

from model.commands.argumentTypes import *
from model.commands.argumentValues import FilterArguments, FilterArgument
from model.commands.command import ArgumentSchema, ParsedArgument, CommandPart
from model.commands.commandContext import getArgumentContext, missingArgumentParser, makeParsedArgument
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.messages import *
from model.parsing.bytesUtils import bytesToStr
from model.parsing.contextProvider import Suggestions
from model.utils import Span, Position, GeneralError


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


def parseFilterArgs(sr: StringReader, argsInfo: dict[bytes, FilterArgumentInfo], *, errorsIO: list[CommandSyntaxError]) -> Optional[FilterArguments]:
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
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				key = b''
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			elif key not in argsInfo:
				errorsIO.append(CommandSyntaxError(f"Unknown argument '`{bytesToStr(key)}`'.", sr.currentSpan, style='error'))
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			else:
				tsai = argsInfo[key]

			keyNode = makeCommandPart(sr, key)
			assert keyNode.content == key, f"keyNode.content = {keyNode.content!r}, key = {bytesToStr(key)!r}"

			# duplicate?:
			if key in arguments and not tsai.multipleAllowed:
				errorsIO.append(CommandSyntaxError(f"Argument '`{bytesToStr(key)}`' cannot be duplicated.", sr.currentSpan, style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeByte(ord('=')):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))
				isNegated = False
				sr.readUntilEndOrRegex(re.compile(rb'[],]'))
				valueNode = None
			else:
				sr.tryConsumeWhitespace()
				isNegated = sr.tryConsumeByte(ord('!'))
				if isNegated and not tsai.isNegatable:
					errorsIO.append(CommandSyntaxError(f"Argument '`{bytesToStr(key)}`' cannot be negated.", sr.currentSpan, style='error'))

				handler = getArgumentContext(tsai.type)
				if handler is None:
					valueNode = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
				else:
					valueNode = handler.parse(sr, tsai, errorsIO=errorsIO)
				if valueNode is None:
					remaining = sr.readUntilEndOrRegex(re.compile(rb'[],]'))
					valueNode = makeParsedArgument(sr, tsai, value=remaining)
					errorsIO.append(CommandSyntaxError(f"Expected {tsai.type.name}.", sr.currentSpan, style='error'))
			sr.mergeLastSave()
			arguments.add(key, FilterArgument(keyNode, valueNode, isNegated))

			sr.tryConsumeWhitespace()
			if sr.tryConsumeByte(ord(']')):
				break
			if sr.tryConsumeByte(ord(',')):
				sr.tryConsumeWhitespace()
				continue
			if sr.hasReachedEnd:
				errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format(f"`]`", 'end of str'), Span(sr.currentPos), style='error'))
				break
			errorsIO.append(CommandSyntaxError(f"Expected `,` or `]`", Span(sr.currentPos), style='error'))
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

	context = getCursorContext(contextStr, cursorPos, pos, argsInfo, node)
	if context.fa is None:
		return [cursorTouchesWord + ']'] + _getKeySuggestions(argsInfo)

	suggestions: Suggestions = []
	if context.isValue:
		if context.inside:
			if (value := context.fa.value) is not None:
				tsaInfo = value.schema
				if isinstance(tsaInfo, ArgumentSchema):
					handler = getArgumentContext(tsaInfo.type)
					if handler is not None:
						suggestions += handler.getSuggestions2(tsaInfo, value, pos, replaceCtx)
						# TODO: maybe log if no handler has been found...
		if context.after:
			suggestions.append(cursorTouchesWord + ', ')
			suggestions.append(cursorTouchesWord + ']')
	else:
		if context.after:
			suggestions.append(cursorTouchesWord + '=')
		if context.inside:
			# context.fa is not None, so we already have an '=' after the key, so don't add one here.
			suggestions += _getKeySuggestions(argsInfo)

	return suggestions


def _getKeySuggestions(argsInfo: dict[bytes, FilterArgumentInfo]):
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


def onIndicatorClickedForFilterArgs(filterArgs: FilterArguments, position: Position, window: QWidget) -> None:
	if (match := getBestFAMatch(filterArgs, position.index)) is not None:
		argInfo = match.schema
		if isinstance(argInfo, ArgumentSchema):
			if (handler := getArgumentContext(argInfo.type)) is not None:
				handler.onIndicatorClicked(match, position, window)


__all__ = [
	'FilterArgumentInfo',
	'parseFilterArgs',
	'validateFilterArgs',
	'suggestionsForFilterArgs',
	'clickableRangesForFilterArgs',
	'onIndicatorClickedForFilterArgs',
	# 'FALLBACK_FILTER_ARGUMENT_INFO',
]
