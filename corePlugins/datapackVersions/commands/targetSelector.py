import re
from typing import Optional

from base.model.utils import GeneralError, ParsingError
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, CommandPart, FilterArgumentInfo, ParsedArgument
from corePlugins.mcFunction.commandContext import argumentContext, ArgumentContext, getArgumentContext, makeParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from .argumentTypes import *
from base.model.messages import *
from base.model.parsing.bytesUtils import strToBytes
from base.model.pathUtils import FilePath
from .filterArgs import makeCommandPart, parseFilterArgsLike

DPE_TARGET_SELECTOR_SCORES = ArgumentType(
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
		type=makeLiteralsArgumentType([b'nearest', b'furthest', b'random', b'arbitrary']),
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
		type=MINECRAFT_PREDICATE,
		multipleAllowed=True,
		isNegatable=True,
	),
]

TARGET_SELECTOR_ARGUMENTS_DICT: dict[bytes, FilterArgumentInfo] = {
	strToBytes(tsa.name): tsa
	for tsa in targetSelectorArguments
}

FALLBACK_TS_ARGUMENT_INFO = FilterArgumentInfo(
	name='_fallback',
	type=BRIGADIER_STRING,
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
)

OBJECTIVE_RANGE_INFO = FilterArgumentInfo(
	name='_objective',
	type=MINECRAFT_INT_RANGE,
	multipleAllowed=True,
	isNegatable=False,
	canBeEmpty=False,
)


_GOTO_NEXT_ARG_PATTERN = re.compile(rb'[,}=]')


@argumentContext(DPE_TARGET_SELECTOR_SCORES.name)
class TargetSelectorScoresArgumentHandler(ArgumentContext):

	def parseObjective(self, sr: StringReader, argsInfo: dict[bytes, FilterArgumentInfo], filePath: FilePath, errorsIO: list[GeneralError]) -> tuple[bytes, CommandPart, FilterArgumentInfo]:
		handler = getArgumentContext(MINECRAFT_OBJECTIVE)
		objectiveNode = handler.parse(sr, None, filePath, errorsIO=errorsIO)
		if objectiveNode is None:
			objective = sr.readUntilEndOrRegex(_GOTO_NEXT_ARG_PATTERN)
			objectiveNode = makeCommandPart(sr, objective)
			errorsIO.append(ParsingError(EXPECTED_MSG.format("an objective"), sr.currentSpan, style='error'))
		else:
			objective = objectiveNode.value
		return objective, objectiveNode, OBJECTIVE_RANGE_INFO

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		scores = parseFilterArgsLike(sr, {}, b'{', b'}', self.parseObjective, filePath, errorsIO=errorsIO)
		return makeParsedArgument(sr, ai, value=scores)


__all__ = [
	'TARGET_SELECTOR_ARGUMENTS_DICT',
	'FALLBACK_TS_ARGUMENT_INFO',
]
