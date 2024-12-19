from typing import Optional

from base.model.parsing.tree import Schema
from base.model.utils import LanguageId
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, KeywordSchema
from corePlugins.mcFunction.commandContext import argumentContext
from .argumentTypes import *
from base.model.parsing.bytesUtils import strToBytes
from corePlugins.mcFunction.filterArgs import FilterArgOptions, FALLBACK_FILTER_ARGUMENT_INFO, FilterArgumentInfo, \
	NegationStyle
from corePlugins.mcFunction import FILTER_ARGS_ID
from corePlugins.mcFunction.argumentContextsImpl import ParsingHandler

DPE_TARGET_SELECTOR_SCORES = ArgumentType(
	name='dpe:target_selector_scores',
	description="`[scores={<objective>=<value>,...}]` — Filter target selection based on their scores in the specified objectives. All tested objectives are in a single object, with a list of individual score arguments between braces afterward. The values inside the braces support integer ranges. Cannot duplicate this argument.",
	description2="""""",
	examples="""
	* `@e[scores={foo=10,bar=1..5}]`""",
)

DPE_TARGET_SELECTOR_ADVANCEMENTS = ArgumentType(
	name='dpe:target_selector_advancements',
	description="`[scores={<resource location>=<bool>, <resource location>={<criteria>=<bool>, ...}, ...}]` — Filter target selection based on the entity's advancements. This naturally filters out all non-player targets. All advancements are in a single object, with a list of individual advancement IDs between the braces afterward. The values are true or false. For advancements with one criterion, testing for that criterion always gives the same results as testing for the advancement.",
	description2="""""",
	examples="""
	* `@a[advancements={adventure/kill_all_mobs={witch=true}}]`""",
)

DPE_TARGET_SELECTOR_ADVANCEMENTS_CRITERION = ArgumentType(
	name='dpe:target_selector_advancements_criterion',
	description="`[scores={<resource location>=<bool>, <resource location>={<criteria>=<bool>, ...}, ...}]` — Filter target selection based on the entity's advancements. This naturally filters out all non-player targets. All advancements are in a single object, with a list of individual advancement IDs between the braces afterward. The values are true or false. For advancements with one criterion, testing for that criterion always gives the same results as testing for the advancement.",
	description2="""""",
	examples="""
	* `@a[advancements={adventure/kill_all_mobs={witch=true}}]`""",
)

targetSelectorArguments: list[FilterArgumentInfo] = [
	# Selection by Position:
	FilterArgumentInfo(
		keySchema=KeywordSchema('x'),
		valueSchema=ArgumentSchema(
			name='x',
			type=BRIGADIER_DOUBLE,
		),
		description="Define a position in the world the selector starts at, for use with the distance argument, the volume arguments, or the limit argument. Using these arguments alone does not restrict the entities found, and affects only the sorting of targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('y'),
		valueSchema=ArgumentSchema(
			name='y',
			type=BRIGADIER_DOUBLE,
		),
		description="Define a position in the world the selector starts at, for use with the distance argument, the volume arguments, or the limit argument. Using these arguments alone does not restrict the entities found, and affects only the sorting of targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('z'),
		valueSchema=ArgumentSchema(
			name='z',
			type=BRIGADIER_DOUBLE,
		),
		description="Define a position in the world the selector starts at, for use with the distance argument, the volume arguments, or the limit argument. Using these arguments alone does not restrict the entities found, and affects only the sorting of targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('distance'),
		valueSchema=ArgumentSchema(
			name='distance',
			type=MINECRAFT_FLOAT_RANGE,
			args=dict(minVal=0),
		),
		description="Filter target selection based on their Euclidean distances from some point, searching for the target's feet (a point at the bottom of the center of their hitbox). If the positional arguments are left undefined, radius is calculated relative to the position of the command's execution. This argument limits the search of entities to the current dimension."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('dx'),
		valueSchema=ArgumentSchema(
			name='dx',
			type=BRIGADIER_DOUBLE,
		),
		defaultValue=0,
		description="Filter target selection based on their x-difference from some point, as measured by the entities' hitboxes."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('dy'),
		valueSchema=ArgumentSchema(
			name='dy',
			type=BRIGADIER_DOUBLE,
		),
		defaultValue=0,
		description="Filter target selection based on their y-difference from some point, as measured by the entities' hitboxes."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('dz'),
		valueSchema=ArgumentSchema(
			name='dz',
			type=BRIGADIER_DOUBLE,
		),
		defaultValue=0,
		description="Filter target selection based on their z-difference from some point, as measured by the entities' hitboxes."
	),
	# Selection by Scoreboard Values:
	FilterArgumentInfo(
		keySchema=KeywordSchema('scores'),
		valueSchema=ArgumentSchema(
			name='scores',
			type=DPE_TARGET_SELECTOR_SCORES,
		),
		description="Filter target selection based on their scores in the specified objectives. All tested objectives are in a single object, separated by commas. Each objective and score value pair is separated by an equals sign. The score values support integer ranges."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('tag'),
		valueSchema=ArgumentSchema(
			name='tag',
			type=BRIGADIER_STRING,
		),
		multipleAllowed=True,
		isNegatable=True,
		canBeEmpty=True,
		description="Filter target selection based on the entity's scoreboard tags. Multiple tag arguments are allowed, and all arguments must be fulfilled for an entity to be selected."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('team'),
		valueSchema=ArgumentSchema(
			name='team',
			type=MINECRAFT_TEAM,
		),
		multipleAllowedIfNegated=True,
		isNegatable=True,
		canBeEmpty=True,
		description="Filter target selection based on teams."
	),
	# Selection by Traits:
	FilterArgumentInfo(
		keySchema=KeywordSchema('limit'),
		valueSchema=ArgumentSchema(
			name='limit',
			type=BRIGADIER_INTEGER,
			args=dict(min=1),
		),
		description="Limit the number of selectable targets for a target selector.\n"
					" - For `@p` and `@r`, this argument defaults to `1`. Applying the limiting argument to them may increase the number of nearest or random targets selected. \n"
					" - For `@a` or `@e`, this argument returns only a limited number of targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('sort'),
		valueSchema=ArgumentSchema(
			name='limit',
			type=makeLiteralsArgumentType([b'nearest', b'furthest', b'random', b'arbitrary']),
		),
		description="How targets are sorted.\n"
					" - `sort=nearest`: Sort by increasing distance. (Default for `@p`)\n"
					" - `sort=furthest`: Sort by decreasing distance.\n"
					" - `sort=random`: Sort randomly. (Default for `@r`)\n"
					" - `sort=arbitrary`: Do not sort. This often returns the oldest entities first due to how the game stores entities internally, but no order is guaranteed. (Default for `@e`, `@a`)"
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('level'),
		valueSchema=ArgumentSchema(
			name='level',
			type=MINECRAFT_INT_RANGE,
			args=dict(minVal=0),
		),
		description="Filter target selection based on the entity's experience levels. This naturally filters out all non-player targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('gamemode'),
		valueSchema=ArgumentSchema(
			name='gamemode',
			type=MINECRAFT_GAME_MODE,
		),
		multipleAllowedIfNegated=True,
		isNegatable=True,
		description="Filter target selection by game mode. This naturally filters out all non-player targets."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('name'),
		valueSchema=ArgumentSchema(
			name='name',
			type=BRIGADIER_STRING,
		),
		multipleAllowedIfNegated=True,
		isNegatable=True,
		description="Filter target selection by name. Values are strings, so spaces are allowed only if quotes are applied. This <i>cannot<i> be a JSON text compound."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('x_rotation'),
		valueSchema=ArgumentSchema(
			name='x_rotation',
			type=MINECRAFT_FLOAT_RANGE,
			args=dict(minVal=-90, maxVal=+90),
		),
		description="Filter target selection based on the entity's rotation along the pitch axis, measured in degrees. Values range from -90 (straight up) to 0 (at the horizon) to +90 (straight down)."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('y_rotation'),
		valueSchema=ArgumentSchema(
			name='y_rotation',
			type=MINECRAFT_FLOAT_RANGE,
			args=dict(minVal=-180, maxVal=+180),
		),
		description="Filter target selection based on the entity's rotation along the yaw axis, measured clockwise in degrees from due south (or the positive Z direction). Values vary from -180 (facing due north) to -90 (facing due east) to 0 (facing due south) to +90 (facing due west) to +180 (facing due north again)."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('type'),
		valueSchema=ArgumentSchema(
			name='type',
			type=MINECRAFT_RESOURCE_LOCATION,
			args=dict(schema='entity_type', allowTags=True),
		),
		multipleAllowedIfNegated=True,
		isNegatable=True,
		description="Filter target selection based on the entity's identifier. The given entity type must be a valid entity ID or entity type tag used to identify different types of entities internally."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('nbt'),
		valueSchema=ArgumentSchema(
			name='nbt',
			type=MINECRAFT_NBT_COMPOUND_TAG,
		),
		multipleAllowed=True,
		isNegatable=True,
		description="Filter target selection based on the entity's NBT data. The NBT data is written in its SNBT format. Duplicate nbt arguments are allowed, and all arguments must be fulfilled for an entity to be selected.\n\n"
					"<b>Note:</b> This selector argument should be used with care, as accessing NBT data is a heavy process for the CPU."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('advancements'),
		valueSchema=ArgumentSchema(
			name='advancements',
			type=DPE_TARGET_SELECTOR_ADVANCEMENTS,
		),
		multipleAllowed=False,
		isNegatable=False,
		canBeEmpty=False,
		description="Filter target selection based on the entity's advancements. This naturally filters out all non-player targets. All advancements are in a single object, with a list of individual advancement IDs between the braces afterward. The values are true or false. For advancements with one criterion, testing for that criterion always gives the same results as testing for the advancement."
	),
	FilterArgumentInfo(
		keySchema=KeywordSchema('predicate'),
		valueSchema=ArgumentSchema(
			name='predicate',
			type=MINECRAFT_PREDICATE,
		),
		multipleAllowed=True,
		isNegatable=True,
		description="Filter target selection by predicates. The given values must be a valid predicate represented by a resource location. Duplicate predicate arguments are allowed, and all arguments must be fulfilled for an entity to be selected."
	),
]

TARGET_SELECTOR_ARGUMENTS_DICT: dict[bytes, FilterArgumentInfo] = {
	strToBytes(tsa.keySchema.name): tsa
	for tsa in targetSelectorArguments
}

FALLBACK_TS_ARGUMENT_INFO = FilterArgumentInfo(
	keySchema=KeywordSchema('_fallback'),
	valueSchema=ArgumentSchema(
		name='_fallback',
		type=BRIGADIER_STRING,
	),
	multipleAllowed=True,
	isNegatable=True,
	canBeEmpty=True,
	description=""
)

OBJECTIVE_RANGE_KEY_SCHEMA = ArgumentSchema(
	name='_scores',
	type=MINECRAFT_OBJECTIVE
)

OBJECTIVE_RANGE_INFO = FilterArgumentInfo(
	keySchema=OBJECTIVE_RANGE_KEY_SCHEMA,
	valueSchema=ArgumentSchema(
		name='_objective',
		type=MINECRAFT_INT_RANGE,
	),
	multipleAllowed=True,
	isNegatable=False,
	canBeEmpty=False,
	description=""
)


TARGET_SELECTOR_ARG_OPTIONS: FilterArgOptions = FilterArgOptions(
	opening=b'[',
	closing=b']',
	allowTrailingComma=True,
	negationStyle=NegationStyle.VALUE_NEGATION,
	keySchema=ArgumentSchema(
		name='key',
		type=makeLiteralsArgumentType(list(TARGET_SELECTOR_ARGUMENTS_DICT.keys())),
	),
	getArgsInfo=lambda key: TARGET_SELECTOR_ARGUMENTS_DICT.get(key.content, FALLBACK_FILTER_ARGUMENT_INFO),
	description=""
)


# ========================================================================================


_TARGET_SELECTOR_SCORES_OPTIONS = FilterArgOptions(
	opening=b'{',
	closing=b'}',
	allowTrailingComma=True,
	negationStyle=NegationStyle.VALUE_NEGATION,
	keySchema=OBJECTIVE_RANGE_KEY_SCHEMA,
	getArgsInfo=lambda key: OBJECTIVE_RANGE_INFO,
	description=""
)

# ===================================================================

ADVANCEMENTS_CRITERION_KEY_SCHEMA = ArgumentSchema(
	name='_criterion',
	type=BRIGADIER_STRING,
)  # TODO check advancement criterion

ADVANCEMENTS_CRITERION_VALUE_INFO = FilterArgumentInfo(
	keySchema=ADVANCEMENTS_CRITERION_KEY_SCHEMA,
	valueSchema=ArgumentSchema(
		name='_criteria',
		type=BRIGADIER_BOOL,
	),
	multipleAllowed=True,
	isNegatable=False,
	canBeEmpty=False,
	description=""
)

_TARGET_SELECTOR_ADVANCEMENTS_CRITERION_OPTIONS = FilterArgOptions(
	opening=b'{',
	closing=b'}',
	allowTrailingComma=True,
	negationStyle=NegationStyle.VALUE_NEGATION,
	keySchema=ADVANCEMENTS_CRITERION_KEY_SCHEMA,
	getArgsInfo=lambda key: ADVANCEMENTS_CRITERION_VALUE_INFO,
	minCount=1,
	description=""
)  # todo test if minCount=1 is correct for _TARGET_SELECTOR_ADVANCEMENTS_OPTIONS


# ===================================================================


ADVANCEMENTS_KEY_SCHEMA = ArgumentSchema(
	name='_advancement',
	type=MINECRAFT_RESOURCE_LOCATION,
	args=dict(schema='advancement')
)

ADVANCEMENTS_VALUE_INFO = FilterArgumentInfo(
	keySchema=ADVANCEMENTS_KEY_SCHEMA,
	valueSchema=ArgumentSchema(
		name='_criteria',
		type=DPE_TARGET_SELECTOR_ADVANCEMENTS_CRITERION,  # TODO: or BRIGADIER_BOOL
	),
	multipleAllowed=True,
	isNegatable=False,
	canBeEmpty=False,
	description=""
)


_TARGET_SELECTOR_ADVANCEMENTS_OPTIONS = FilterArgOptions(
	opening=b'{',
	closing=b'}',
	allowTrailingComma=True,
	negationStyle=NegationStyle.VALUE_NEGATION,
	keySchema=ADVANCEMENTS_KEY_SCHEMA,
	getArgsInfo=lambda key: ADVANCEMENTS_VALUE_INFO,
	minCount=1,
	description=""
)  # todo test if minCount=1 is correct for _TARGET_SELECTOR_ADVANCEMENTS_OPTIONS


@argumentContext(DPE_TARGET_SELECTOR_SCORES.name, options=_TARGET_SELECTOR_SCORES_OPTIONS)
@argumentContext(DPE_TARGET_SELECTOR_ADVANCEMENTS.name, options=_TARGET_SELECTOR_ADVANCEMENTS_OPTIONS)
@argumentContext(DPE_TARGET_SELECTOR_ADVANCEMENTS_CRITERION.name, options=_TARGET_SELECTOR_ADVANCEMENTS_CRITERION_OPTIONS)
class TargetSelectorFilterArgArgumentHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return self.options

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return FILTER_ARGS_ID

	def __init__(self, options: FilterArgOptions):
		self.options: FilterArgOptions = options


__all__ = [
	'TARGET_SELECTOR_ARGUMENTS_DICT',
	'TARGET_SELECTOR_ARG_OPTIONS',
	'FALLBACK_TS_ARGUMENT_INFO',
]
