from math import inf
from typing import Optional

from Cat.utils import Anything
from model.commands.argumentTypes import *
from model.datapackContents import ResourceLocationSchema, ResourceLocation
from model.parsing.bytesUtils import bytesToStr
from .Advancement.Conditions.damage_type import ADVANCEMENT_CONDITIONS_DAMAGE_TYPE
from .Advancement.Conditions.entity import ADVANCEMENT_CONDITIONS_ENTITY
from .Advancement.Conditions.item import ADVANCEMENT_CONDITIONS_ITEM
from .Advancement.Conditions.location import ADVANCEMENT_CONDITIONS_LOCATION
from ..argTypes import *
from model.json.core import *
from model.utils import MDStr

# see: https://minecraft.fandom.com/wiki/Predicate#Predicate_condition_JSON_format


def _propertiesFromBlockStates(blockId: ResourceLocation) -> Optional[JsonObjectSchema]:
	from session.session import getSession
	states = getSession().minecraftData.blockStates.get(blockId)
	if states is None:
		return None

	properties = []
	for state in states:
		valueDescr: MDStr = state.type.description
		if isinstance(state.type, LiteralsArgumentType):
			value = JsonStringOptionsSchema(options={bytesToStr(opt): MDStr("") for opt in state.type.options}, description=valueDescr)
		elif state.type.name == BRIGADIER_BOOL.name:
			value = JsonBoolSchema(description=valueDescr)
		elif state.type.name == BRIGADIER_INTEGER.name:
			args = state.args or {}
			value = JsonIntSchema(minVal=args.get('min', -inf), maxVal=args.get('max', inf), description=valueDescr)
		else:
			value = JsonStringSchema(type=state.type, description=valueDescr)
		properties.append(PropertySchema(name=state.name, value=value, optional=True, description=state.description))

	return JsonObjectSchema(properties=properties)


def propertiesFor_block_state_property(parent: JsonObject) -> Optional[JsonObjectSchema]:
	blockVal = parent.data.get('block', None)
	if blockVal is None or not isinstance(blockVal.value, JsonString):
		return JsonObjectSchema(properties=[])
	else:
		block = blockVal.value.data
		block = ResourceLocation.fromString(block)
		return _propertiesFromBlockStates(block)

def _apdMC(val: str) -> tuple[str, str]:
	return val, f'minecraft:{val}'


def _apdMCs(options: dict[str, MDStr]) -> dict[str, MDStr]:
	result = {}
	for val, descr in options.items():
		result[val] = descr
		result[f'minecraft:{val}'] = descr
	return result


_TARGET_TARGET = JsonStringOptionsSchema(
	options=_apdMCs({
		'this': MDStr("the invoking entity"),
		'killer': MDStr("the entity that killed the invoking entity"),
		'direct_killer': MDStr("the entity that *directly* killed the invoking entity"),
		'killer_player': MDStr("only select the killer if they are a player"),
	})
)

NUMBER_PROVIDER = JsonUnionSchema(options=[
	JsonIntSchema(description=MDStr("Constant number provider.")),
	JsonFloatSchema(description=MDStr("Constant number provider.")),
])

NUMBER_PROVIDER.options.append(
	JsonObjectSchema(
		description=MDStr(""),
		properties=[
			PropertySchema(
				name='type',
				description=MDStr("The number provider type."),
				value=JsonStringOptionsSchema(options=_apdMCs({
					'constant': MDStr("A constant value."),
					'uniform': MDStr("A random number following a uniform distribution between two values (inclusive)."),
					'binomial': MDStr("A random number following a binomial distribution."),
					'score': MDStr("To query and use a scoreboard value."),
					'': MDStr(""),
				}))
			),

			PropertySchema(
				name='value',
				description=MDStr("The exact value."),
				decidingProp='type',
				values={_apdMC('constant'): JsonUnionSchema(options=[JsonIntSchema(), JsonFloatSchema()])},
				value=None
			),

			PropertySchema(
				name='min',
				description=MDStr("The minimum value."),
				decidingProp='type',
				values={_apdMC('uniform'): NUMBER_PROVIDER},
				value=None
			),

			PropertySchema(
				name='max',
				description=MDStr("The maximum value."),
				decidingProp='type',
				values={_apdMC('uniform'): NUMBER_PROVIDER},
				value=None
			),

			PropertySchema(
				name='n',
				description=MDStr("The amount of trials."),
				decidingProp='type',
				values={_apdMC('binomial'): NUMBER_PROVIDER},  # int number provider
				value=None
			),

			PropertySchema(
				name='p',
				description=MDStr("The probability of success on an individual trial."),
				decidingProp='type',
				values={_apdMC('binomial'): NUMBER_PROVIDER},  # float number provider
				value=None
			),

			PropertySchema(
				name='target',
				description=MDStr(""),
				decidingProp='type',
				values={_apdMC('score'): JsonUnionSchema(
					options=[JsonObjectSchema(
						properties=[
							PropertySchema(
								name='type',
								description=MDStr("Set to `fixed` to manually specify a player name or UUID. Set to `context` to use an entity from loot context."),
								value=JsonStringOptionsSchema(options=_apdMCs({
									'fixed': MDStr("manually specify a player name or UUID"),
									'context': MDStr("use an entity from loot context"),
								}))
							),
							PropertySchema(
								name='name',
								description=MDStr("Included only if type is set to `fixed`. Specifies the name of the player, or the entity's UUID (in hyphenated hexadecimal format) whose score to query."),
								decidingProp='type',
								values={_apdMC('fixed'): JsonStringSchema(type=MINECRAFT_UUID)},
								value=None
							),
							PropertySchema(
								name='target',
								description=MDStr("Included only if type is set to context. Specifies an entity from loot context to query the score of. Use `this` for the invoking entity, `killer` for the entity that killed the invoking entity, `direct_killer` for the entity that *directly* killed the invoking entity, or `player_killer` to select the killer only if they are a player."),
								decidingProp='type',
								values={_apdMC('context'): _TARGET_TARGET},
								value=None
							),
						]
					), _TARGET_TARGET]
				)},
				value=None,
				optional=True,
				default='score'
			),

			PropertySchema(
				name='score',
				description=MDStr("The scoreboard objective to query on the selected player name or UUID."),
				decidingProp='type',
				values={_apdMC('score'): JsonStringSchema(type=MINECRAFT_OBJECTIVE)},
				value=None,
				optional=True,
				default='target'
			),

			PropertySchema(
				name='scale',
				description=MDStr("The scoreboard objective to query on the selected player name or UUID."),
				decidingProp='type',
				values={_apdMC('score'): JsonFloatSchema()},
				value=None,
				optional=True,
				default=1.0
			),

		]
	)
)


PREDICATE_SCHEMA = JsonUnionSchema(options=[])


SINGLE_PREDICATE_SCHEMA = JsonObjectSchema(description=MDStr("The root element of the condition."), properties=[])
SINGLE_PREDICATE_SCHEMA.properties = (
	PropertySchema(
		name="condition",
		description=MDStr("The resource location of the condition type to check."),
		value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema('', 'condition'))),  # todo: add args for condition
	),

	PropertySchema(
		name="terms",
		description=MDStr("Evaluates a list of conditions and passes if any one of them passes. Invokable from any context."),
		decidingProp='condition',
		values={_apdMC('alternative'): PREDICATE_SCHEMA},
		value=None,
	),

	PropertySchema(
		name="term",
		description=MDStr("The condition to be negated, following the same structure as outlined here, recursively."),
		decidingProp='condition',
		values={_apdMC('inverted'): SINGLE_PREDICATE_SCHEMA},
		value=None,
	),

	PropertySchema(
		name="block",
		description=MDStr("A block ID. The test fails if the block doesn't match."),
		decidingProp='condition',
		values={_apdMC('block_state_property'): JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema('', 'block_type')))},
		value=None,
	),

	PropertySchema(
		name="properties",
		description=MDStr("(Optional) A map of block property names to values. All values are strings. The test fails if the block doesn't match."),
		decidingProp='condition',
		values={_apdMC('block_state_property'): JsonCalculatedValueSchema(func=propertiesFor_block_state_property)},
		value=None,
		optional=True
	),

	PropertySchema(
		name="predicate",
		description=MDStr(""),
		decidingProp='condition',
		values={_apdMC('damage_source_properties'): JsonObjectSchema(
			description=MDStr("Predicate applied to the damage source. Checks properties of damage source. Invokable from loot tables, and fails when invoked from anything else."),
			properties=[
				*ADVANCEMENT_CONDITIONS_DAMAGE_TYPE.properties
			]
		), _apdMC('entity_properties'): JsonObjectSchema(
			description=MDStr("Predicate applied to entity, uses same structure as advancements."),
			properties=[
				*ADVANCEMENT_CONDITIONS_ENTITY.properties
			]
		), _apdMC('location_check'): JsonObjectSchema(
			description=MDStr("Predicate applied to location, uses same structure as advancements."),
			properties=[
				*ADVANCEMENT_CONDITIONS_LOCATION.properties,
				# TODO: PropertySchema(
				# 	name='block',
				# 	value=JsonObjectSchema(
				# 		properties=[
				# 			PropertySchema(
				# 				name='nbt',
				# 				value=JsonStringSchema(type=MINECRAFT_NBT_COMPOUND_TAG),
				# 				optional=True
				# 			)
				# 		]
				# 	),
				# 	optional=True
				# )
			]
		), _apdMC('match_tool'): JsonObjectSchema(
			description=MDStr("Predicate applied to item, uses same structure as advancements. "),
			properties=[
				*ADVANCEMENT_CONDITIONS_ITEM.properties
			]
		)},
		value=None,
	),

	PropertySchema(
		name="entity",
		description=MDStr("The entity to check. Set to `this` to use the entity that invoked this condition, `killer` for the killer of the `this` entity, or `killer_player` to only select the killer if they are a player."),
		decidingProp='condition',
		values={(*_apdMC('entity_properties'), *_apdMC('entity_scores')): JsonStringOptionsSchema(options=_apdMCs({
			'this': MDStr("the entity that invoked this condition"),
			'killer': MDStr("the killer of the `this` entity"),
			'killer_player': MDStr("only select the killer if they are a player"),
		}))},
		value=None,
	),

	PropertySchema(
		name="scores",
		description=MDStr("Scores to check. All specified scores must pass for the condition to pass."),
		decidingProp='condition',
		values={_apdMC('entity_scores'): JsonObjectSchema(
			properties=[
				PropertySchema(
					name=Anything(),  # todo: Key name is the objective while the value specifies a range of score values required for the condition to pass.
					value=JsonUnionSchema(options=[
						JsonObjectSchema(
							description=MDStr("Predicate applied to the damage source. Checks properties of damage source. Invokable from loot tables, and fails when invoked from anything else."),
							properties=[
								PropertySchema(
									name="min",
									description=MDStr("Minimum score."),
									value=NUMBER_PROVIDER,
								),
								PropertySchema(
									name="max",
									description=MDStr("Maximum score."),
									value=NUMBER_PROVIDER,
								)
							]
						),
						JsonIntSchema(description=MDStr("Exact score")),
					])
				),
			]
		)},
		value=None
	),

	PropertySchema(
		name="inverse",
		description=MDStr("If true, the condition passes if killer_player is not available."),
		decidingProp='condition',
		values={_apdMC('killed_by_player'): JsonBoolSchema()},
		value=None,
	),

	PropertySchema(
		name="offsetX",
		description=MDStr("optional offsets to location"),
		decidingProp='condition',
		values={_apdMC('location_check'): JsonIntSchema()},
		value=None,
		optional=True
	),
	PropertySchema(
		name="offsetY",
		description=MDStr("optional offsets to location"),
		decidingProp='condition',
		values={_apdMC('location_check'): JsonIntSchema()},
		value=None,
		optional=True
	),
	PropertySchema(
		name="offsetZ",
		description=MDStr("optional offsets to location"),
		decidingProp='condition',
		values={_apdMC('location_check'): JsonIntSchema()},
		value=None,
		optional=True
	),

	PropertySchema(
		name="chance",
		description=MDStr("(Base-)Success rate as a number `0.0-1.0`."),
		decidingProp='condition',
		values={(*_apdMC('random_chance'), *_apdMC('random_chance_with_looting')): JsonFloatSchema(minVal=0, maxVal=1)},
		value=None,
	),

	PropertySchema(
		name="looting_multiplier",
		description=MDStr("Looting adjustment to the base success rate. Formula is `chance + (looting_level * looting_multiplier)`."),
		decidingProp='condition',
		values={_apdMC('random_chance_with_looting'): JsonFloatSchema(minVal=0, maxVal=1)},
		value=None,
	),

	PropertySchema(
		name="name",
		description=MDStr("The resource location of the predicate to invoke. A cyclic reference causes a parsing failure."),
		decidingProp='condition',
		values={_apdMC('reference'): JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema('', 'predicate')))},
		value=None,
	),

	PropertySchema(
		name="enchantment",
		description=MDStr("Resource location of enchantment."),
		decidingProp='condition',
		values={_apdMC('table_bonus'): JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema('', 'enchantment')))},
		value=None,
	),

	PropertySchema(
		name="chances",
		description=MDStr("List of probabilities for enchantment level, indexed from 0."),
		decidingProp='condition',
		values={_apdMC('table_bonus'): JsonArraySchema(element=JsonFloatSchema())},
		value=None,
	),

	PropertySchema(
		name="value",
		decidingProp='condition',
		values={_apdMC('time_check'): JsonUnionSchema(options=[
			JsonObjectSchema(
				description=MDStr("The time to compare the game time against."),
				properties=[
					PropertySchema(
						name="min",
						description=MDStr("Minimum value."),
						value=NUMBER_PROVIDER,
					),
					PropertySchema(
						name="max",
						description=MDStr("Maximum value."),
						value=NUMBER_PROVIDER,
					)
				]
			),
			JsonIntSchema(description=MDStr("The time to compare the game time against.")),
		]), _apdMC('value_check'): JsonUnionSchema(options=[NUMBER_PROVIDER], description=MDStr("The number to test."))},
		value=None,
	),

	PropertySchema(
		name="period",
		description=MDStr("If present, the game time is first reduced modulo the given number before being checked against value. For example, setting this to 24000 causes the checked time to be equal to the current daytime."),
		decidingProp='condition',
		values={_apdMC('time_check'): JsonIntSchema()},
		value=None,
		optional=True
	),

	PropertySchema(
		name="range",
		description=MDStr("The number or range of numbers to compare  value against."),
		decidingProp='condition',
		values={_apdMC('value_check'): JsonUnionSchema(
			options=[
				JsonObjectSchema(
					properties=[
						PropertySchema(
							name="min",
							description=MDStr("Minimum value."),
							value=NUMBER_PROVIDER,
						),
						PropertySchema(
							name="max",
							description=MDStr("Maximum value."),
							value=NUMBER_PROVIDER,
						)
					]
				),
				JsonIntSchema(),
			]
		)},
		value=None,
	),

	PropertySchema(
		name="raining",
		description=MDStr("If true, the condition passes only if it is raining or thundering."),
		decidingProp='condition',
		values={_apdMC('weather_check'): JsonBoolSchema()},
		value=None,
		optional=True  # overcoming a limitation of the current JsonSchema implementation: One and exactly one of (raining, thundering)
	),

	PropertySchema(
		name="thundering",
		description=MDStr("If true, the condition passes only if it is thundering."),
		decidingProp='condition',
		values={_apdMC('weather_check'): JsonBoolSchema()},
		value=None,
		optional=True  # overcoming a limitation of the current JsonSchema implementation: One and exactly one of (raining, thundering)
	),
)

SINGLE_PREDICATE_SCHEMA.buildPropertiesDict()


PREDICATE_SCHEMA.options = [
	SINGLE_PREDICATE_SCHEMA,
	JsonArraySchema(
		description=MDStr("Multiple conditions may be entered into a single predicate by placing them into a JSON array."),
		element=SINGLE_PREDICATE_SCHEMA
	),
]
