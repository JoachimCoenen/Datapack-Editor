import re
from typing import Optional

from Cat.utils.collections_ import OrderedMultiDict
from model.commands.argumentHandlers import getArgumentHandler, makeParsedArgument, argumentHandler, ArgumentHandler
from model.commands.argumentTypes import *
from model.commands.command import ArgumentInfo
from model.commands.filterArgs import FilterArgumentInfo
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.nbt.snbtParser import EXPECTED_BUT_GOT_MSG


DPE_TARGET_SELECTOR_SCORES = ArgumentType.create(
	name='dpe:target_selector_scores',
	description="`[scores={<objective>=<value>,...}]` — Filter target selection based on their scores in the specified objectives. All tested objectives are in a single object, with a list of individual score arguments between braces afterward. The values inside the braces support integer ranges. Cannot duplicate this argument.",
	description2="""""",
	examples="""
	* `@e[scores={foo=10,bar=1..5}]`""",
)

targetSelectorArguments: list[FilterArgumentInfo] = [
	# Selection by Position:
	FilterArgumentInfo(
		name='x',
		type=BRIGADIER_DOUBLE,
	),
	FilterArgumentInfo(
		name='y',
		type=BRIGADIER_DOUBLE,
	),
	FilterArgumentInfo(
		name='z',
		type=BRIGADIER_DOUBLE,
	),
	FilterArgumentInfo(  # TODO: only unsigned values are allowed
		name='distance',
		type=MINECRAFT_FLOAT_RANGE,
	),
	FilterArgumentInfo(
		name='dx',
		type=BRIGADIER_DOUBLE,
	),
	FilterArgumentInfo(
		name='dy',
		type=BRIGADIER_DOUBLE,
	),
	FilterArgumentInfo(
		name='dz',
		type=BRIGADIER_DOUBLE,
	),
	# Selection by Scoreboard Values:
	FilterArgumentInfo(  # TODO: scores: @e[scores={foo=10,bar=1..5}]
		name='scores',
		type=DPE_TARGET_SELECTOR_SCORES,
	),
	FilterArgumentInfo(
		name='tag',
		type=BRIGADIER_STRING,
		multipleAllowed=True,
		isNegatable=True,
		canBeEmpty=True,
	),
	FilterArgumentInfo(
		name='team',
		type=MINECRAFT_TEAM,
		multipleAllowed=True,
		isNegatable=True,
		canBeEmpty=True,
	),
	# Selection by Traits:
	FilterArgumentInfo(
		name='limit',
		type=BRIGADIER_INTEGER,
	),
	FilterArgumentInfo(
		name='sort',
		type=LiteralsArgumentType(['nearest', 'furthest', 'random', 'arbitrary']),
	),
	FilterArgumentInfo(
		name='level',
		type=MINECRAFT_INT_RANGE,
	),
	FilterArgumentInfo(
		name='gamemode',
		type=MINECRAFT_GAME_MODE,
		isNegatable=True,
	),
	FilterArgumentInfo(
		name='name',
		type=BRIGADIER_STRING,
		multipleAllowed=True,  # TODO: Arguments testing for equality cannot be duplicated, while arguments testing for inequality can.
		isNegatable=True,
	),
	FilterArgumentInfo(  # TODO: apply bound check (-90 ... +90)
		name='x_rotation',
		type=MINECRAFT_FLOAT_RANGE,
	),
	FilterArgumentInfo(  # TODO: apply bound check (-90 ... +180)
		name='y_rotation',
		type=MINECRAFT_FLOAT_RANGE,
	),
	FilterArgumentInfo(
		name='type',
		type=MINECRAFT_ENTITY_TYPE,
		multipleAllowed=True,  # TODO: Arguments testing for equality cannot be duplicated, while arguments testing for inequality can.
		isNegatable=True,
	),
	FilterArgumentInfo(
		name='nbt',
		type=MINECRAFT_NBT_COMPOUND_TAG,
		multipleAllowed=True,
		isNegatable=True,
	),
	# FilterArgumentInfo(  # TODO: Selecting targets by advancements
	# 	name='advancements',
	# 	type=advancements,
	# 	multipleAllowed=False,
	# 	isNegatable=False,
	# 	canBeEmpty=False,
	# ),
	FilterArgumentInfo(
		name='predicate',
		type=MINECRAFT_RESOURCE_LOCATION,  # TODO: actually, the type is predicates.
		multipleAllowed=True,
		isNegatable=True,
	),
]

TARGET_SELECTOR_ARGUMENTS_DICT: dict[str, FilterArgumentInfo] = {
	tsa.name: tsa
	for tsa in targetSelectorArguments
}

FALLBACK_TS_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
)


_GOTO_NEXT_ARG_PATTERN = re.compile(r'[,}=]')


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
				objective = sr.readUntilEndOrRegex(_GOTO_NEXT_ARG_PATTERN)
				errorsIO.append(CommandSyntaxError(f"Expected an objective.", sr.currentSpan, style='error'))
			else:
				objective = objective.value

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				sr.readUntilEndOrRegex(_GOTO_NEXT_ARG_PATTERN)
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", sr.currentSpan, style='error'))
				sr.mergeLastSave()
			else:
				sr.tryConsumeWhitespace()

				handler = getArgumentHandler(MINECRAFT_INT_RANGE)
				value = handler.parse(sr, None, errorsIO=errorsIO)
				if value is None:
					remainig = sr.readUntilEndOrRegex(_GOTO_NEXT_ARG_PATTERN)
					value = makeParsedArgument(sr, None, value=remainig)
					errorsIO.append(CommandSyntaxError(f"Expected {MINECRAFT_INT_RANGE.name}.", sr.currentSpan, style='error'))
				sr.mergeLastSave()
				scores.add(objective, value)

			sr.tryConsumeWhitespace()
			if sr.tryConsumeChar('}'):
				break
			elif sr.tryConsumeChar(','):
				sr.tryConsumeWhitespace()
				continue
			else:
				if sr.hasReachedEnd:
					errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format("`}`", 'end of str'), sr.currentSpan, style='error'))
					break
				else:
					remainig = sr.readUntilEndOrRegex(_GOTO_NEXT_ARG_PATTERN)
					errorsIO.append(CommandSyntaxError(EXPECTED_BUT_GOT_MSG.format("`}` or `,`", f"'{remainig}'"), sr.currentSpan, style='error'))
					if sr.tryConsumeChar('}'):
						break
		return makeParsedArgument(sr, ai, value=scores)


__all__ = [
	'TARGET_SELECTOR_ARGUMENTS_DICT',
	'FALLBACK_TS_ARGUMENT_INFO',
]
