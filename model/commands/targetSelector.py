import re
from typing import Optional

from Cat.Serializable import RegisterContainer, Serialized
from Cat.utils.collections_ import OrderedMultiDict
from Cat.utils.profiling import ProfiledFunction
from model.commands.argumentHandlers import getArgumentHandler, makeParsedArgument, missingArgumentParser, argumentHandler, ArgumentHandler
from model.commands.argumentTypes import *
from model.commands.argumentValues import TargetSelector
from model.commands.command import ArgumentInfo
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.nbt.snbtParser import EXPECTED_BUT_GOT_MSG
from model.parsingUtils import Span


@RegisterContainer
class TSArgumentInfo(ArgumentInfo):
	__slots__ = ()
	multipleAllowed: bool = Serialized(default=False)
	isNegatable: bool = Serialized(default=False)
	canBeEmpty: bool = Serialized(default=False)


DPE_TARGET_SELECTOR_SCORES = ArgumentType.create(
	name='dpe:target_selector_scores',
	description="`[scores={<objective>=<value>,...}]` — Filter target selection based on their scores in the specified objectives. All tested objectives are in a single object, with a list of individual score arguments between braces afterward. The values inside the braces support integer ranges. Cannot duplicate this argument.",
	description2="""""",
	examples="""
	* `@e[scores={foo=10,bar=1..5}]`""",
)

targetSelectorArguments: list[TSArgumentInfo] = [
	# Selection by Position:
	TSArgumentInfo.create(
		name='x',
		type=BRIGADIER_DOUBLE,
	),
	TSArgumentInfo.create(
		name='y',
		type=BRIGADIER_DOUBLE,
	),
	TSArgumentInfo.create(
		name='z',
		type=BRIGADIER_DOUBLE,
	),
	TSArgumentInfo.create(  # TODO: only unsigned values are allowed
		name='distance',
		type=MINECRAFT_FLOAT_RANGE,
	),
	TSArgumentInfo.create(
		name='dx',
		type=BRIGADIER_DOUBLE,
	),
	TSArgumentInfo.create(
		name='dy',
		type=BRIGADIER_DOUBLE,
	),
	TSArgumentInfo.create(
		name='dz',
		type=BRIGADIER_DOUBLE,
	),
	# Selection by Scoreboard Values:
	TSArgumentInfo.create(  # TODO: scores: @e[scores={foo=10,bar=1..5}]
		name='scores',
		type=DPE_TARGET_SELECTOR_SCORES,
	),
	TSArgumentInfo.create(
		name='tag',
		type=BRIGADIER_STRING,
		multipleAllowed=True,
		isNegatable=True,
		canBeEmpty=True,
	),
	TSArgumentInfo.create(
		name='team',
		type=MINECRAFT_TEAM,
		multipleAllowed=True,
		isNegatable=True,
		canBeEmpty=True,
	),
	# Selection by Traits:
	TSArgumentInfo.create(
		name='limit',
		type=BRIGADIER_INTEGER,
	),
	TSArgumentInfo.create(
		name='sort',
		type=LiteralsArgumentType(['nearest', 'furthest', 'random', 'arbitrary']),
	),
	TSArgumentInfo.create(
		name='level',
		type=MINECRAFT_INT_RANGE,
	),
	TSArgumentInfo.create(
		name='gamemode',
		type=MINECRAFT_GAME_MODE,
		isNegatable=True,
	),
	TSArgumentInfo.create(
		name='name',
		type=BRIGADIER_STRING,
		multipleAllowed=True,  # TODO: Arguments testing for equality cannot be duplicated, while arguments testing for inequality can.
		isNegatable=True,
	),
	TSArgumentInfo.create(  # TODO: apply bound check (-90 ... +90)
		name='x_rotation',
		type=MINECRAFT_FLOAT_RANGE,
	),
	TSArgumentInfo.create(  # TODO: apply bound check (-90 ... +180)
		name='y_rotation',
		type=MINECRAFT_FLOAT_RANGE,
	),
	TSArgumentInfo.create(
		name='type',
		type=MINECRAFT_ENTITY_SUMMON,
		multipleAllowed=True,  # TODO: Arguments testing for equality cannot be duplicated, while arguments testing for inequality can.
		isNegatable=True,
	),
	TSArgumentInfo.create(
		name='nbt',
		type=MINECRAFT_NBT_COMPOUND_TAG,
		multipleAllowed=True,
		isNegatable=True,
	),
	# TSArgumentInfo.create(  # TODO: Selecting targets by advancements
	# 	name='advancements',
	# 	type=advancements,
	# 	multipleAllowed=False,
	# 	isNegatable=False,
	# 	canBeEmpty=False,
	# ),
	TSArgumentInfo.create(
		name='predicate',
		type=MINECRAFT_RESOURCE_LOCATION,  # TODO: actually, the type is predicates.
		multipleAllowed=True,
		isNegatable=True,
	),
]

targetSelectorArgumentsDict: dict[str, TSArgumentInfo] = {
	tsa.name: tsa
	for tsa in targetSelectorArguments
}

FALLBACK_TS_ARGUMENT_INFO = TSArgumentInfo.create(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
)


@argumentHandler(DPE_TARGET_SELECTOR_SCORES.name)
class TargetSelectorScoresArgumentHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		if not sr.tryConsumeChar('{'):
			return None

		scores: OrderedMultiDict[str, ParsedArgument] = OrderedMultiDict[str, ParsedArgument]()
		sr.tryConsumeWhitespace()
		sr.save()
		while not sr.tryConsumeChar('}'):
			sr.mergeLastSave()

			handler = getArgumentHandler(MINECRAFT_OBJECTIVE)
			objective = handler.parse(sr, None, errorsIO=errorsIO)
			if objective is None:
				errorsIO.append(CommandSyntaxError(f"Expected an objective.", Span(sr.currentPos), style='error'))
				objective = ''
			else:
				objective = objective.value

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))
			sr.tryConsumeWhitespace()

			handler = getArgumentHandler(MINECRAFT_INT_RANGE)
			value = handler.parse(sr, None, errorsIO=errorsIO)
			if value is None:
				remainig = sr.readUntilEndOrRegex(re.compile(r'[],]'))
				value = makeParsedArgument(sr, None, value=remainig)
				errorsIO.append(CommandSyntaxError(f"Expected {MINECRAFT_INT_RANGE.name}.", sr.currentSpan, style='error'))
			sr.mergeLastSave()
			scores.add(objective, value)

			sr.tryConsumeWhitespace()
			if sr.tryConsumeChar('}'):
				break
			if sr.tryConsumeChar(','):
				sr.tryConsumeWhitespace()
				continue
			if sr.hasReachedEnd:
				errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format("`}`", 'end of str'), sr.currentSpan, style='error'))
				break
		return makeParsedArgument(sr, ai, value=scores)


def _parseTargetSelectorArgs(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[OrderedMultiDict[str, ParsedArgument]]:
	if sr.tryConsumeChar('['):
		# block states:
		arguments: OrderedMultiDict[str, ParsedArgument] = OrderedMultiDict[str, ParsedArgument]()
		sr.tryConsumeWhitespace()
		sr.save()
		while not sr.tryConsumeChar(']'):
			sr.mergeLastSave()
			prop = sr.tryReadString()
			if prop is None:
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				prop = ''
				tsai = FALLBACK_TS_ARGUMENT_INFO
			elif prop not in targetSelectorArgumentsDict:
				errorsIO.append(CommandSyntaxError(f"Unknown target selector argument '`{prop}`'.", sr.currentSpan, style='error'))
				tsai = FALLBACK_TS_ARGUMENT_INFO
			else:
				tsai = targetSelectorArgumentsDict[prop]
			# duplicate?:
			if prop in arguments and not tsai.multipleAllowed:
				errorsIO.append(CommandSyntaxError(f"Target selector argument '`{prop}`' cannot be duplicated.", sr.currentSpan, style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))
			sr.tryConsumeWhitespace()
			isNegated = sr.tryConsumeChar('!')
			if isNegated and not tsai.isNegatable:
				errorsIO.append(CommandSyntaxError(f"Target selector argument '`{prop}`' cannot be negated.", sr.currentSpan, style='error'))

			handler = getArgumentHandler(tsai.type)
			if handler is None:
				value = missingArgumentParser(sr, tsai, errorsIO=errorsIO)
			# return firstArg, errors
			else:
				value = handler.parse(sr, tsai, errorsIO=errorsIO)
			if value is None:
				remainig = sr.readUntilEndOrRegex(re.compile(r'[],]'))
				value = makeParsedArgument(sr, None, value=remainig)
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


@ProfiledFunction(enabled=False, colourNodesBySelftime=False)
def parseTargetSelector(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[TargetSelector]:
	# Must be a player name, a target selector or a UUID.
	variable = sr.tryReadRegex(re.compile(r'@[praes]\b'))
	if variable is None:
		return None

	arguments = _parseTargetSelectorArgs(sr, ai, errorsIO=errorsIO)
	if arguments is None:
		arguments = OrderedMultiDict()
	else:
		sr.mergeLastSave()

	return TargetSelector.create(variable=variable, arguments=arguments)


__all__ = [
	'TSArgumentInfo',
	'targetSelectorArguments',
	'targetSelectorArgumentsDict',
	'FALLBACK_TS_ARGUMENT_INFO',
]
