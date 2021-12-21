"""
filterArgs are a list of comma separated arguments enclosed in square brackets. eg.: "[distance=3..7, team=red]"
They are either block states ot target selector arguments
"""
import re
from typing import Optional

from Cat.Serializable import RegisterContainer, Serialized
from Cat.utils.profiling import ProfiledFunction
from model.commands.argumentHandlers import getArgumentHandler, makeParsedArgument, missingArgumentParser
from model.commands.argumentTypes import *
from model.commands.argumentValues import FilterArguments
from model.commands.command import ArgumentInfo
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.nbt.snbtParser import EXPECTED_BUT_GOT_MSG
from model.parsingUtils import Span


@RegisterContainer
class FilterArgumentInfo(ArgumentInfo):
	__slots__ = ()
	multipleAllowed: bool = Serialized(default=False)
	isNegatable: bool = Serialized(default=False)
	canBeEmpty: bool = Serialized(default=False)


FALLBACK_FILTER_ARGUMENT_INFO = FilterArgumentInfo.create(
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
			prop = sr.tryReadString()
			if prop is None:
				sr.save()
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				prop = ''
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			elif prop not in argsInfo:
				errorsIO.append(CommandSyntaxError(f"Unknown argument '`{prop}`'.", sr.currentSpan, style='error'))
				tsai = FALLBACK_FILTER_ARGUMENT_INFO
			else:
				tsai = argsInfo[prop]
			# duplicate?:
			if prop in arguments and not tsai.multipleAllowed:
				errorsIO.append(CommandSyntaxError(f"Argument '`{prop}`' cannot be duplicated.", sr.currentSpan, style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))
			sr.tryConsumeWhitespace()
			isNegated = sr.tryConsumeChar('!')
			if isNegated and not tsai.isNegatable:
				errorsIO.append(CommandSyntaxError(f"Argument '`{prop}`' cannot be negated.", sr.currentSpan, style='error'))

			handler = getArgumentHandler(tsai.type)
			if handler is None:
				value = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
			# return firstArg, errors
			else:
				value = handler.parse(sr, tsai, errorsIO=errorsIO)
			if value is None:
				remaining = sr.readUntilEndOrRegex(re.compile(r'[],]'))
				value = makeParsedArgument(sr, tsai, value=remaining)
				errorsIO.append(CommandSyntaxError(f"Expected {tsai.type.name}.", sr.currentSpan, style='error'))
			sr.mergeLastSave()
			arguments.add(prop, value)

			sr.tryConsumeWhitespace()
			if sr.tryConsumeChar(']'):
				break
			if sr.tryConsumeChar(','):
				sr.tryConsumeWhitespace()
				continue
			if sr.hasReachedEnd:
				errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format(f"`]`", 'end of str'), sr.currentSpan, style='error'))
				break
		return arguments
	else:
		return None


def getBestFAMatch(fas: FilterArguments, cursorPos: int) -> Optional[ParsedArgument]:
	for fa in fas.values():
		if fa.span.start.index <= cursorPos <= fa.span.end.index:
			return fa
	return None


def getNextFAMatch(fas: FilterArguments, cursorPos: int) -> Optional[ParsedArgument]:
	for fa in fas.values():
		if fa.span.start.index >= cursorPos:
			return fa
	return None


@ProfiledFunction(enabled=False, colourNodesBySelftime=False)
def suggestionsForFilterArgs(contextStr: str, cursorPos: int, argsInfo: dict[str, FilterArgumentInfo]) -> list[str]:
	# if cursorPos == 0:
	# 	if len(contextStr) == 2:
	# 		return [contextStr + '[]']
	if contextStr.startswith('[') and not contextStr.endswith(']'):
		contextStr += ']'
	sr = StringReader(contextStr, 0, 0, contextStr)
	errors = []
	ts = parseFilterArgs(sr, argsInfo, errorsIO=errors)
	if ts is None:
		return []
	tsaMatch = getBestFAMatch(ts, cursorPos)
	if tsaMatch is None and re.search(r'= *$', contextStr[:cursorPos]) is not None:
		tsaMatch = getNextFAMatch(ts, cursorPos)

	if tsaMatch is None:
		return [t.name for t in argsInfo.values()]
	else:
		tsaInfo = tsaMatch.info
		if tsaInfo is None:
			return []

		if isinstance(tsaInfo, ArgumentInfo):
			type_: ArgumentType = tsaInfo.type
			handler = getArgumentHandler(type_)
			if handler is not None:
				return handler.getSuggestions(tsaInfo, contextStr, cursorPos)
		return []


__all__ = [
	'FilterArgumentInfo',
	'parseFilterArgs',
	'suggestionsForFilterArgs',
	# 'FALLBACK_FILTER_ARGUMENT_INFO',
]
