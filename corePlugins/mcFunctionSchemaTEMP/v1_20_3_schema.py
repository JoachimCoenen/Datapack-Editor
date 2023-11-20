"""
currently at minecraft version 1.20.2
"""

from copy import copy
from typing import Any, Callable, Optional

from cat.utils.collections_ import AddToDictDecorator, ChainedList
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import CommandPartSchema, CommandSchema, KeywordSchema, ArgumentSchema, Options, TERMINAL, COMMANDS_ROOT, SwitchSchema, MCFunctionSchema
from base.model.parsing.bytesUtils import strToBytes

from .argumentTypes import *
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData
from ..datapack.datapackContents import RESOURCES


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_20_3 = getFullMcData('1.20.3')
	schema_1_20_3 = buildMCFunctionSchemaFor_v1_20_3(version1_20_3)
	return {'Minecraft 1.20.3': schema_1_20_3}


_COMMAND_CREATORS: dict[Callable[[FullMCData], list[CommandPartSchema]], list[dict[str, Any]]] = {}


def buildMCFunctionSchemaFor_v1_20_3(version: FullMCData) -> MCFunctionSchema:
	basicCmdInfo: dict[bytes, CommandSchema] = {}
	_addCommand = AddToDictDecorator(basicCmdInfo)

	for cc, aliases in _COMMAND_CREATORS.items():
		args = cc(version)
		for cmdSchemaKwargs in aliases:
			_addCommand(strToBytes(cmdSchemaKwargs['name']))(CommandSchema(**cmdSchemaKwargs, next=Options(args)))

	return MCFunctionSchema('', commands=basicCmdInfo)


def addCommand(
		*,
		name: str = ...,
		names: tuple[str, ...] = ...,

		description: str = '',
		opLevel: int|str = 0,
		availableInSP: bool = True,
		availableInMP: bool = True,

		removed: bool = False,
		removedVersion: Optional[str] = None,
		removedComment: str = '',

		deprecated: bool = False,
		deprecatedVersion: Optional[str] = None,
		deprecatedComment: str = '',
) -> Callable[[Callable[[FullMCData], list[CommandPartSchema]]], Callable[[FullMCData], list[CommandPartSchema]]]:
	if name is not ...:
		names = (name,)
	if names is ...:
		ValueError("at least one of (name, names) must be specified")

	kwargs = dict(
		description=description,
		opLevel=opLevel,
		availableInSP=availableInSP,
		availableInMP=availableInMP,
		removed=removed,
		removedVersion=removedVersion,
		removedComment=removedComment,
		deprecated=deprecated,
		deprecatedVersion=deprecatedVersion,
		deprecatedComment=deprecatedComment,
	)

	def _addCommandFunc(func: Callable[[FullMCData], list[CommandPartSchema]]) -> Callable[[FullMCData], list[CommandPartSchema]]:
		if (aliases := _COMMAND_CREATORS.get(func)) is None:
			_COMMAND_CREATORS[func] = aliases = []
		for name2 in names:
			aliases.append(dict(kwargs, name=name2))
		return func

	return _addCommandFunc


@addCommand(
	name='?',
	description='An alias of /help. Provides help for commands.',
	opLevel=0
)
def build_help_args(_: FullMCData) -> list[CommandPartSchema]:
	return []


@addCommand(
	name='advancement',
	description='Gives, removes, or checks player advancements.',
	opLevel=2
)
def build_advancement_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='__action',
			type=makeLiteralsArgumentType([b'grant', b'revoke']),
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						KeywordSchema(
							name='everything',
						),
						KeywordSchema(
							name='only',
							next=Options([
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='criterion',
											type=BRIGADIER_STRING,
										),
									])
								),
							])
						),
						KeywordSchema(
							name='from',
							next=Options([
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							])
						),
						KeywordSchema(
							name='through',
							next=Options([
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							])
						),
						KeywordSchema(
							name='until',
							next=Options([
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							])
						),
					]),
				),
			]),
		),
	]


@addCommand(
	name='attribute',
	description='Queries, adds, removes or sets an entity attribute.',
	opLevel=2
)
def build_attribute_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='attribute',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						KeywordSchema(
							name='get',
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='scale',
									type=BRIGADIER_DOUBLE,
								),
							])
						),
						KeywordSchema(
							name='base',
							next=Options([
								KeywordSchema(
									name='get',
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='scale',
											type=BRIGADIER_DOUBLE,
										),
									])
								),
								KeywordSchema(
									name='set',
									next=Options([
										ArgumentSchema(
											name='value',
											type=BRIGADIER_DOUBLE,
										),
									])
								),
							]),
						),
						KeywordSchema(
							name='modifier',
							next=Options([
								KeywordSchema(
									name='add',
									next=Options([
										ArgumentSchema(
											name='uuid',
											type=MINECRAFT_UUID,
											next=Options([
												ArgumentSchema(
													name='name',
													type=BRIGADIER_STRING,
													next=Options([
														ArgumentSchema(
															name='value',
															type=BRIGADIER_DOUBLE,
															next=Options([
																ArgumentSchema(
																	name='uuid',
																	type=makeLiteralsArgumentType([b'add', b'multiply', b'multiply_base']),
																),
															])
														),
													])
												),
											])
										),
									])
								),
								KeywordSchema(
									name='remove',
									next=Options([
										ArgumentSchema(
											name='uuid',
											type=MINECRAFT_UUID,
										),
									])
								),
								KeywordSchema(
									name='value',
									next=Options([
										KeywordSchema(
											name='get',
											next=Options([
												ArgumentSchema(
													name='uuid',
													type=MINECRAFT_UUID,
													next=Options([
														TERMINAL,
														ArgumentSchema(
															name='scale',
															type=BRIGADIER_DOUBLE,
														),
													])
												),
											])
										),
									])
								),
							]),
						),

					]),
				),
			]),
		),
	]


@addCommand(
	name='ban',
	description='Adds player to banlist.',
	opLevel=3,
	availableInSP=False
)
def build_ban_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			])
		),
	]


@addCommand(
	name='ban-ip',
	description='Adds IP address to banlist.',
	opLevel=3,
	availableInSP=False
)
def build_ban_ip_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='target',
			type=BRIGADIER_STRING,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			])
		),
	]


@addCommand(
	name='banlist',
	description='Displays banlist.',
	opLevel=3,
	availableInSP=False
)
def build_banlist_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		KeywordSchema(
			name='ips',
		),
		KeywordSchema(
			name='players',
		),
	]


@addCommand(
	name='bossbar',
	description='Creates and modifies bossbars.',
	opLevel=2
)
def build_bossbar_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='add',
			next=Options([
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						ArgumentSchema(
							name='name',
							type=MINECRAFT_COMPONENT,
						),
					])
				),
			]),
		),
		KeywordSchema(
			name='get',
			next=Options([
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						ArgumentSchema(
							name='__setting',
							type=makeLiteralsArgumentType([b'max', b'players', b'value', b'visible']),
						),
					])
				),
			]),
		),
		KeywordSchema(
			name='list',
		),
		KeywordSchema(
			name='remove',
			next=Options([
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]),
		),
		KeywordSchema(
			name='set',
			next=Options([
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						KeywordSchema(
							name='color',
							next=Options([
								ArgumentSchema(
									name='color',
									type=makeLiteralsArgumentType([b'blue', b'green', b'pink', b'purple', b'red', b'white', b'yellow']),
								),
							]),
						),
						KeywordSchema(
							name='max',
							next=Options([
								ArgumentSchema(
									name='max',
									type=BRIGADIER_INTEGER,
								),
							]),
						),
						KeywordSchema(
							name='name',
							next=Options([
								ArgumentSchema(
									name='name',
									type=MINECRAFT_COMPONENT,
								),
							]),
						),
						KeywordSchema(
							name='players',
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='targets',
									type=MINECRAFT_ENTITY,
								),
							]),
						),
						KeywordSchema(
							name='style',
							next=Options([
								ArgumentSchema(
									name='style',
									type=makeLiteralsArgumentType([b'notched_6', b'notched_10', b'notched_12', b'notched_20', b'progress']),
								),
							]),
						),
						KeywordSchema(
							name='value	',
							next=Options([
								ArgumentSchema(
									name='value',
									type=BRIGADIER_INTEGER,
								),
							]),
						),
						KeywordSchema(
							name='visible',
							next=Options([
								ArgumentSchema(
									name='visible',
									type=BRIGADIER_BOOL,
								),
							]),
						),
					])
				),
			]),
		),
	]


@addCommand(
	name='clear',
	description='Clears items from player inventory.',
	opLevel=2
)
def build_clear_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_PREDICATE,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='maxCount',
							type=BRIGADIER_INTEGER,
						),
					]),
				),
			]),
		),
	]


@addCommand(
	name='clone',
	description='Copies blocks from one place to another.',
	opLevel=2
)
def build_clone_args(_: FullMCData) -> list[CommandPartSchema]:
	CLONE_MODE = ArgumentSchema(name='cloneMode', type=makeLiteralsArgumentType([b'force', b'move', b'normal']), )

	MASK_OR_FILTER = [
		TERMINAL,
		ArgumentSchema(
			name='maskMode',
			type=makeLiteralsArgumentType([b'replace', b'masked']),
			next=Options([
				TERMINAL,
				CLONE_MODE
			])
		),
		KeywordSchema(
			name='filtered',
			next=Options([
				ArgumentSchema(
					name='filter',
					type=MINECRAFT_BLOCK_PREDICATE,
					next=Options([
						TERMINAL,
						CLONE_MODE
					])
				)
			])
		)
	]

	TO_TARGETDIMENSION = KeywordSchema(
		name='to',
		next=Options([
			ArgumentSchema(
				name='targetDimension',
				type=MINECRAFT_RESOURCE_LOCATION,
				args=dict(schema=RESOURCES.DIMENSION)
			)
		])
	)

	TO = SwitchSchema(
		name='...',
		options=Options([
			TO_TARGETDIMENSION,
			TERMINAL
		]),
		next=Options([
			ArgumentSchema(
				name='destination',
				type=MINECRAFT_BLOCK_POS,
				next=Options(MASK_OR_FILTER),
			),
		])
	)

	FROM_TARGETDIMENSION = KeywordSchema(
		name='from',
		next=Options([
			ArgumentSchema(
				name='targetDimension',
				type=MINECRAFT_RESOURCE_LOCATION,
				args=dict(schema=RESOURCES.DIMENSION)
			)
		])
	)

	return [
		SwitchSchema(
			name='...',
			options=Options([
				FROM_TARGETDIMENSION,
				TERMINAL
			]),
			next=Options([
				ArgumentSchema(
					name='begin',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='end',
							type=MINECRAFT_BLOCK_POS,
							next=Options([
								TO
							]),
						),
					]),
				)
			])
		)
	]


@addCommand(
	name='damage',
	description='Applies damage to entities.',
	opLevel=0
)
def build_damage_args(_: FullMCData) -> list[CommandPartSchema]:
	AT_LOCATION = KeywordSchema(
		name='at',
		next=Options([
			ArgumentSchema(
				name='location',
				type=MINECRAFT_VEC3,
			),
		]),
	)

	FROM_CAUSE = KeywordSchema(
		name='from',
		next=Options([
			ArgumentSchema(
				name='cause',
				type=MINECRAFT_ENTITY,
				args=dict(single=True),  # todo: add processing of 'single' argument to class EntityHandler(ArgumentContext) and and check all places where this should be set.
				description="Specifies the cause of the damage (for example, the skeleton that shot the arrow)."
			),
		]),
	)

	BY_ENTITY = KeywordSchema(
		name='by',
		next=Options([
			ArgumentSchema(
				name='entity',
				type=MINECRAFT_ENTITY,
				args=dict(single=True),
				description="Specifies the entity who dealt the damage.",
				next=Options([
					TERMINAL,
					FROM_CAUSE
				])
			),
		]),
	)

	DAMAGE_TYPE = ArgumentSchema(
		name='damageType',
		type=MINECRAFT_RESOURCE_LOCATION,
		args=dict(schema='damage_type'),
		next=Options([
			TERMINAL,
			AT_LOCATION,
			BY_ENTITY,
			*BY_ENTITY.next.all,
		]),
	)
	return [
		# damage <target> <amount> [<damageType>] [at <location>]
		# damage <target> <amount> [<damageType>] [by <entity>] [from <cause>]
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='amount',
					type=BRIGADIER_FLOAT,
					args=dict(min=0.),
					next=Options([
						TERMINAL,
						DAMAGE_TYPE,
						*DAMAGE_TYPE.next.all,
					]),
				),
			]),
		),
	]


DATA_SOURCE = [
	KeywordSchema(
		name='block',
		next=Options([
			ArgumentSchema(
				name='sourcePos',
				type=MINECRAFT_BLOCK_POS,
			),
		])
	),
	KeywordSchema(
		name='entity',
		next=Options([
			ArgumentSchema(
				name='source',
				type=MINECRAFT_ENTITY,
			),
		])
	),
	KeywordSchema(
		name='storage',
		next=Options([
			ArgumentSchema(
				name='source',
				type=MINECRAFT_RESOURCE_LOCATION,
			),
		])
	),
]

DATA_SOURCE_AND_PATH = SwitchSchema(
	name='SOURCE',
	options=Options(DATA_SOURCE),
	next=Options([
		TERMINAL,
		ArgumentSchema(
			name='sourcePath',
			type=MINECRAFT_NBT_PATH,
		),
	])
)


@addCommand(
	name='data',
	description='Gets, merges, modifies and removes block entity and entity NBT data.',
	opLevel=2
)
def build_data_args(_: FullMCData) -> list[CommandPartSchema]:
	DATA_TARGET = [
		KeywordSchema(
			name='block',
			next=Options([
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			])
		),
		KeywordSchema(
			name='entity',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			])
		),
		KeywordSchema(
			name='storage',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			])
		),
	]
	DATA_MODIFICATION = [
		KeywordSchema(
			name='append',
		),
		KeywordSchema(
			name='insert',
			next=Options([
				ArgumentSchema(
					name='index',
					type=BRIGADIER_INTEGER,
				),
			])
		),
		KeywordSchema(
			name='merge',
		),
		KeywordSchema(
			name='prepend',
		),
		KeywordSchema(
			name='set',
		),
	]

	MODIFICATION_FROM = KeywordSchema(
		name='from',
		next=Options([DATA_SOURCE_AND_PATH])
	)
	MODIFICATION_STRING = KeywordSchema(
		name='string',
		next=Options([
			SwitchSchema(
				name='SOURCE',  # jsut like DATA_SOURCE_AND_PATH but with following arguments. :'(
				options=Options(DATA_SOURCE),
				next=Options([
					TERMINAL,
					ArgumentSchema(
						name='sourcePath',
						type=MINECRAFT_NBT_PATH,
						next=Options([
							TERMINAL,
							ArgumentSchema(
								name='start',
								type=BRIGADIER_INTEGER,
								description="Specifies the index of first character to include at the start of the string. Negative values are interpreted as index counted from the end of the string.",
								next=Options([
									TERMINAL,
									ArgumentSchema(
										name='end',
										type=BRIGADIER_INTEGER,
										description="Specifies the index of the first character to exclude at the end of the string. Negative values are interpreted as index counted from the end of the string."
									)
								])
							)
						])
					)
				])
			)
		])
	)
	MODIFICATION_VALUE = KeywordSchema(
		name='value',
		next=Options([
			ArgumentSchema(
				name='value',
				type=MINECRAFT_NBT_TAG,
			)
		])
	)

	return [
		KeywordSchema(
			name='get',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(DATA_TARGET),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='scale',
									type=BRIGADIER_FLOAT,
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='merge',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(DATA_TARGET),
					next=Options([
						ArgumentSchema(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					])
				),
			])
		),
		KeywordSchema(
			name='modify',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(DATA_TARGET),
					next=Options([
						ArgumentSchema(
							name='targetPath',
							type=MINECRAFT_NBT_PATH,
							next=Options([
								SwitchSchema(
									name='MODIFICATION',
									options=Options(DATA_MODIFICATION),
									next=Options([
										MODIFICATION_FROM,
										MODIFICATION_STRING,
										MODIFICATION_VALUE
									])
								)
							])
						)
					])
				)
			])
		),
		# remove <TARGET> <path>
		KeywordSchema(
			name='remove',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(DATA_TARGET),
					next=Options([
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='datapack',
	description='Controls loaded data packs.',
	opLevel=2
)
def build_datapack_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='disable',
			next=Options([
				ArgumentSchema(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
				),
			]),
		),
		KeywordSchema(
			name='enable',
			next=Options([
				ArgumentSchema(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
					next=Options([
						TERMINAL,
						KeywordSchema(
							name='first',
						),
						KeywordSchema(
							name='last',
						),
						KeywordSchema(
							name='before',
							next=Options([
								ArgumentSchema(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							]),
						),
						KeywordSchema(
							name='after',
							next=Options([
								ArgumentSchema(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							]),
						),
					])
				),
			]),
		),
		KeywordSchema(
			name='list',
			description="List all data packs, or list only the available/enabled ones. Hovering over the data packs in the chat output shows their description defined in their pack.mcmeta.",
			next=Options([
				TERMINAL,
				KeywordSchema(name='available'),
				KeywordSchema(name='enabled'),
			]),
		),
	]


@addCommand(
	name='debug',
	description='Starts or stops a debugging session.',
	opLevel=3
)
def build_debug_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(name='start'),
		KeywordSchema(name='stop'),
		KeywordSchema(
			name='function',
			next=Options([
				ArgumentSchema(
					name='name',
					type=MINECRAFT_FUNCTION,
				),
			])
		),
	]


@addCommand(
	name='defaultgamemode',
	description='Sets the default game mode.',
	opLevel=2
)
def build_defaultgamemode_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='mode',
			type=makeLiteralsArgumentType([b'survival', b'creative', b'adventure', b'spectator']),
		),
	]


@addCommand(
	name='deop',
	description='Revokes operator status from a player.',
	opLevel=3,
	availableInSP=False
)
def build_deop_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]


@addCommand(
	name='difficulty',
	description='Sets the difficulty level.',
	opLevel=2
)
def build_difficulty_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		ArgumentSchema(
			name='difficulty',
			type=makeLiteralsArgumentType([b'peaceful', b'easy', b'normal', b'hard']),
		),
	]


@addCommand(
	name='effect',
	description='Add or remove status effects.',
	opLevel=2
)
def build_effect_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='give',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						ArgumentSchema(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
							next=Options([
								TERMINAL,
								SwitchSchema(
									name='DURATION',
									options=Options([
										ArgumentSchema(
											name='seconds',
											type=BRIGADIER_INTEGER,
											args={'min': 0, 'max': 1000000}
										),
										KeywordSchema(
											name='infinite',
										)
									]),
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='amplifier',
											type=BRIGADIER_INTEGER,
											args={'min': 0, 'max': 255},
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='hideParticles',
													type=BRIGADIER_BOOL,
												),
											])
										),
									])
								),
							])
						),
					])
				),
			]),
		),
		KeywordSchema(
			name='clear',
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
						),
					])
				),
			]),
		),
	]


@addCommand(
	name='enchant',
	description="Adds an enchantment to a player's selected item.",
	opLevel=2
)
def build_enchant_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='enchantment',
					type=MINECRAFT_ITEM_ENCHANTMENT,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='level',
							type=BRIGADIER_INTEGER,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='execute',
	description='Executes another command.',
	opLevel=2
)
def build_execute_args(_: FullMCData) -> list[CommandPartSchema]:
	# execute Command:
	EXECUTE_INSTRUCTIONS = []
	EXECUTE_INSTRUCTION_OPTIONS = Options(EXECUTE_INSTRUCTIONS)
	EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS = Options(ChainedList([TERMINAL], EXECUTE_INSTRUCTIONS))

	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='align',
			next=Options([
				ArgumentSchema(
					name='axes',
					type=MINECRAFT_SWIZZLE,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='anchored',
			next=Options([
				ArgumentSchema(
					name='anchor',
					type=MINECRAFT_ENTITY_ANCHOR,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='as',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='at',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='facing',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_VEC3,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='entity',
					next=Options([
						ArgumentSchema(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=Options([
								ArgumentSchema(
									name='anchor',
									type=MINECRAFT_ENTITY_ANCHOR,
									next=EXECUTE_INSTRUCTION_OPTIONS
								),
							])
						),
					]),
				)
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='in',
			next=Options([
				ArgumentSchema(
					name='dimension',
					type=MINECRAFT_DIMENSION,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='on',
			description="Selects entities based on relation to the current executing entity. If the relation is not applicable to the executing entity or there are no entities matching it, selector returns zero elements.",
			next=Options([
				KeywordSchema(
					name='attacker',
					description="last entity that damaged the executing entity in the previous 5 seconds.",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='controller',
					description="entity that is controlling the executing entity (for example: first passenger in a boat).",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='leasher',
					description="entity leading the executing entity with a leash (might be a leash knot in case of being attached to a fence).",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='owner',
					description="owner of the executing entity, if it is a tameable animal (like cats, wolves or parrots).",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='passengers',
					description="all entities directly riding the executing entity (no sub-passengers).",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='target',
					description="attack target for the executing entity.",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='vehicle',
					description="entity that the executing entity is riding.",
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='origin',
					description=" - Shooter, if the executing entity is a projectile (like arrow, fireball, trident, firework, thrown potion, etc.)\n"
								" - Thrower, if the executing entity is an item.\n"
								" - Source of effects, if the executing entity is an area effect cloud.\n"
								" - Igniter, if the executing entity is a primed TNT.\n"
								" - Summoner, if the executing entity is evoker fangs or a vex.\n",
					next=EXECUTE_INSTRUCTION_OPTIONS
				)
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='positioned',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_VEC3,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='as',
					next=Options([
						ArgumentSchema(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=EXECUTE_INSTRUCTION_OPTIONS
						),
					]),
				),
				KeywordSchema(
					name='over',
					description="Finds a position on top of a heightmap. Changes the height of the execution position to be on top of the given heightmap",
					next=Options([
						ArgumentSchema(
							name='heightmap',
							type=makeLiteralsArgumentType([b'world_surface', b'motion_blocking', b'motion_blocking_no_leaves', b'ocean_floor']),
							next=EXECUTE_INSTRUCTION_OPTIONS
						),
					]),
				)
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='rotated',
			next=Options([
				ArgumentSchema(
					name='rot',
					type=MINECRAFT_ROTATION,
					next=EXECUTE_INSTRUCTION_OPTIONS
				),
				KeywordSchema(
					name='as',
					next=Options([
						ArgumentSchema(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=EXECUTE_INSTRUCTION_OPTIONS
						),
					]),
				)
			]),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='summon',
			description="Summons a new entity and binds the context (@s) to it. Meant to simplify entity setup and reduce need for raw NBT editing.",
			next=Options([
				ArgumentSchema(
					name='entity',
					type=MINECRAFT_ENTITY_SUMMON,
					next=EXECUTE_INSTRUCTION_OPTIONS
				)
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS = []
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='biome',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='biome',
							type=MINECRAFT_RESOURCE_LOCATION,
							args=dict(schema=RESOURCES.WORLDGEN.BIOME, allowTags=True),
							next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS
						),
					]),
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='block',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='block',
							type=MINECRAFT_BLOCK_PREDICATE,
							next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS
						),
					]),
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='blocks',
			next=Options([
				ArgumentSchema(
					name='start',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='end',
							type=MINECRAFT_BLOCK_POS,
							next=Options([
								ArgumentSchema(
									name='destination',
									type=MINECRAFT_BLOCK_POS,
									next=Options([
										KeywordSchema(
											name='all',
											next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
										),
										KeywordSchema(
											name='masked',
											next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
										),
									]),
								),
							]),
						),
					]),
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='data',
			next=Options([
				KeywordSchema(
					name='block',
					next=Options([
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							next=Options([
								ArgumentSchema(
									name='path',
									type=MINECRAFT_NBT_PATH,
									next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
								),
							]),
						),
					]),
				),
				KeywordSchema(
					name='entity',
					next=Options([
						ArgumentSchema(
							name='target',
							type=MINECRAFT_ENTITY,
							next=Options([
								ArgumentSchema(
									name='path',
									type=MINECRAFT_NBT_PATH,
									next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
								),
							]),
						),
					]),
				),
				KeywordSchema(
					name='storage',
					next=Options([
						ArgumentSchema(
							name='source',
							type=MINECRAFT_RESOURCE_LOCATION,
							next=Options([
								ArgumentSchema(
									name='path',
									type=MINECRAFT_NBT_PATH,
									next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
								),
							]),
						),
					]),
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='dimension',
			description="checks if the execution is in a matching dimension.",
			next=Options([
				ArgumentSchema(
					name='dimension',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.DIMENSION),  # curiously, there are no tags allowed here...
					next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='entity',
			next=Options([
				ArgumentSchema(
					name='entities',
					type=MINECRAFT_ENTITY,
					next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='loaded',
			description="Checks if the position given is fully loaded (in regard to both blocks and entities).",
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='predicate',
			next=Options([
				ArgumentSchema(
					name='predicate',
					type=MINECRAFT_PREDICATE,
					next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
				),
			]),
		)
	)
	EXECUTE_IF_UNLESS_ARGUMENTS.append(
		KeywordSchema(
			name='score',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='targetObjective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								KeywordSchema(
									name='matches',
									next=Options([
										ArgumentSchema(
											name='range',
											type=MINECRAFT_INT_RANGE,
											next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
										),
									])
								),
								ArgumentSchema(
									name='__compare',
									type=makeLiteralsArgumentType([b'<=', b'<', b'=', b'>=', b'>']),
									next=Options([
										ArgumentSchema(
											name='source',
											type=MINECRAFT_SCORE_HOLDER,
											next=Options([
												ArgumentSchema(
													name='sourceObjective',
													type=MINECRAFT_OBJECTIVE,
													next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS,
												),
											]),
										),
									]),
								),
							]),
						),
					]),
				),
			]),
		)
	)

	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='if',
			next=Options(EXECUTE_IF_UNLESS_ARGUMENTS),
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='unless',
			next=Options(EXECUTE_IF_UNLESS_ARGUMENTS),
		)
	)
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS = []
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(
		KeywordSchema(
			name='block',
			next=Options([
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=Options([
								ArgumentSchema(
									name='type',
									type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
									next=Options([
										ArgumentSchema(
											name='scale',
											description="Multiplier to apply before storing value",
											type=BRIGADIER_DOUBLE,
											next=EXECUTE_INSTRUCTION_OPTIONS
										),
									]),
								),
							]),
						),
					]),
				),
			])
		)
	)
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(
		KeywordSchema(
			name='bossbar',
			next=Options([
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						ArgumentSchema(
							name='value',
							type=makeLiteralsArgumentType([b'value', b'max']),
							next=EXECUTE_INSTRUCTION_OPTIONS,
						),
					]),
				),
			])
		)
	)
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(
		KeywordSchema(
			name='entity',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
					next=Options([
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=Options([
								ArgumentSchema(
									name='type',
									type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
									next=Options([
										ArgumentSchema(
											name='scale',
											description="Multiplier to apply before storing value",
											type=BRIGADIER_DOUBLE,
											next=EXECUTE_INSTRUCTION_OPTIONS
										),
									]),
								),
							]),
						),
					]),
				),
			])
		)
	)
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(
		KeywordSchema(
			name='score',
			next=Options([
				ArgumentSchema(
					name='targets',
					description='Specifies score holder(s) whose score is to be overridden',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							description='A scoreboard objective',
							type=MINECRAFT_OBJECTIVE,
							next=EXECUTE_INSTRUCTION_OPTIONS,
						),
					]),
				),
			])
		)
	)
	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(
		KeywordSchema(
			name='storage',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=Options([
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=Options([
								ArgumentSchema(
									name='type',
									type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
									next=Options([
										ArgumentSchema(
											name='scale',
											description="Multiplier to apply before storing value",
											type=BRIGADIER_DOUBLE,
											next=EXECUTE_INSTRUCTION_OPTIONS
										),
									]),
								),
							]),
						),
					]),
				),
			])
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='store',
			next=Options([
				KeywordSchema(
					name='result',
					next=Options(EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS),
				),
				KeywordSchema(
					name='success',
					next=Options(EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS),
				),
			])
		)
	)
	EXECUTE_INSTRUCTIONS.append(
		KeywordSchema(
			name='run',
			next=Options([COMMANDS_ROOT]),
		)
	)
	EXECUTE_INSTRUCTION_OPTIONS.finish()
	EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS.finish()
	return EXECUTE_INSTRUCTIONS


@addCommand(
	names=('experience', 'xp'),
	description='An alias of /xp. Adds or removes player experience.',
	opLevel=2
)
def build_experience_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='add',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						ArgumentSchema(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=Options([
								ArgumentSchema(
									name='__levels',
									type=makeLiteralsArgumentType([b'levels', b'points']),
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='set',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						ArgumentSchema(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=Options([
								ArgumentSchema(
									name='__levels',
									type=makeLiteralsArgumentType([b'levels', b'points']),
								),
							])
						),
					])
				),
			]),
		),
		KeywordSchema(
			name='query',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=Options([
						ArgumentSchema(
							name='__levels',
							type=makeLiteralsArgumentType([b'levels', b'points']),
						),
					])
				),
			])
		),
	]


@addCommand(
	name='fill',
	description='Fills a region with a specific block.',
	opLevel=2
)
def build_fill_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='from',
			type=MINECRAFT_BLOCK_POS,
			next=Options([
				ArgumentSchema(
					name='to',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='block',
							type=MINECRAFT_BLOCK_STATE,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='option',
									type=makeLiteralsArgumentType([b'destroy', b'hollow', b'keep', b'outline']),
								),
								KeywordSchema(
									name='replace',
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='replace',
											type=MINECRAFT_BLOCK_PREDICATE
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='fillbiome',
	description='Changes biome entries for an area.',
	opLevel=2
)
def build_fillbiome_args(_: FullMCData) -> list[CommandPartSchema]:
	# fillbiome <from> <to> <biome> [replace <filter>]
	return [
		ArgumentSchema(
			name='from',
			type=MINECRAFT_BLOCK_POS,
			next=Options([
				ArgumentSchema(
					name='to',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						ArgumentSchema(
							name='biome',
							type=MINECRAFT_RESOURCE_LOCATION,
							args=dict(schema=RESOURCES.WORLDGEN.BIOME, allowTags=False),
							description="Specifies the biome to fill the specified area with.",
							next=Options([
								TERMINAL,
								KeywordSchema(
									name='replace',
									next=Options([
										ArgumentSchema(
											name='replace',
											type=MINECRAFT_RESOURCE_LOCATION,
											args=dict(schema=RESOURCES.WORLDGEN.BIOME, allowTags=True),
											description="Specifies the biomes in the fill region to be replaced. If not specified, replaces all biomes in the fill region."
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='forceload',
	description='Forces chunks to constantly be loaded or not.',
	opLevel=2
)
def build_forceload_args(_: FullMCData) -> list[CommandPartSchema]:
	FORCELOAD_RANGE_ARG = ArgumentSchema(
		name='from',
		type=MINECRAFT_COLUMN_POS,
		next=Options([
			TERMINAL,
			ArgumentSchema(
				name='to',
				type=MINECRAFT_COLUMN_POS,
			),
		])
	)
	return [
		KeywordSchema(
			name='add',
			next=Options([
				FORCELOAD_RANGE_ARG,
			])
		),
		KeywordSchema(
			name='remove',
			next=Options([
				KeywordSchema('all'),
				FORCELOAD_RANGE_ARG,
			])
		),
		KeywordSchema(
			name='query',
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_COLUMN_POS,
				),
			])
		),
	]


@addCommand(
	name='function',
	description='Runs a function.',
	opLevel=2
)
def build_function_args(_: FullMCData) -> list[CommandPartSchema]:
	# /function <name> [<arguments>|with (block <sourcePos>|entity <source>|storage <source>) [<path>]]
	return [
		ArgumentSchema(
			name='name',
			type=MINECRAFT_FUNCTION,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='arguments',
					type=MINECRAFT_NBT_COMPOUND_TAG  # TODO: add specialized checking if parameters match the macros of the function, and if the resulting function would be valid.
				),
				KeywordSchema(
					name='with',  # TODO: add specialized checking if parameters match the macros of the function, and if the resulting function would be valid.
					description=" - The data source and path must specify a compound data entry.\n"
								" - The compound must contain one entry for each variable used in the macro.\n"
								" - More data may be present in the compound and if so is ignored.\n",
					next=Options([DATA_SOURCE_AND_PATH])
				)
			])
		)
	]


@addCommand(
	name='gamemode',
	description="Sets a player's game mode.",
	opLevel=2
)
def build_gamemode_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='gamemode',
			type=MINECRAFT_GAME_MODE,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				)
			])
		),
	]


@addCommand(
	name='gamerule',
	description='Sets or queries a game rule value.',
	opLevel=2
)
def build_gamerule_args(version: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name=gr.name,
			description=gr.description,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='value',
					type=ALL_NAMED_ARGUMENT_TYPES[gr.type],
				),
			])
		) for gr in version.gamerules.values()
	]


@addCommand(
	name='give',
	description='Gives an item to a player.',
	opLevel=2
)
def build_give_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='count',
							type=BRIGADIER_INTEGER,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='help',
	description='An alias of /?. Provides help for commands.',
	opLevel=0
)
def build_help_args(_: FullMCData) -> list[CommandPartSchema]:
	return []


@addCommand(
	name='item',
	description='Manipulates items in inventories.',
	opLevel=2
)
def build_item_args(_: FullMCData) -> list[CommandPartSchema]:
	ITEM_TARGET = [
		KeywordSchema(
			name='block',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
				),
			])
		),
		KeywordSchema(
			name='entity',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			])
		),
	]
	ITEM_SOURCE = [
		KeywordSchema(
			name='block',
			next=Options([
				ArgumentSchema(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			])
		),
		KeywordSchema(
			name='entity',
			next=Options([
				ArgumentSchema(
					name='sourceTarget',
					type=MINECRAFT_ENTITY,
				),
			])
		),
	]
	ITEM_MODIFIER = [
		ArgumentSchema(
			name='modifier',
			type=MINECRAFT_RESOURCE_LOCATION,
		),
	]
	return [
		KeywordSchema(
			name='modify',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(ITEM_TARGET),
					next=Options([
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=Options(ITEM_MODIFIER)
						),
					])
				),
			])
		),
		KeywordSchema(
			name='replace',
			next=Options([
				SwitchSchema(
					name='TARGET',
					options=Options(ITEM_TARGET),
					next=Options([
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=Options([
								KeywordSchema(
									name='with',
									next=Options([
										ArgumentSchema(
											name='item',
											type=MINECRAFT_ITEM_STACK,
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='count',
													type=BRIGADIER_INTEGER,
													args={'min': 1, 'max': 64},
												),
											])
										),
									])
								),
								KeywordSchema(
									name='from',
									next=Options([
										SwitchSchema(
											name='SOURCE',
											options=Options(ITEM_SOURCE),
											next=Options([
												ArgumentSchema(
													name='sourceSlot',
													type=MINECRAFT_ITEM_SLOT,
													next=Options([
														TERMINAL,
														*ITEM_MODIFIER,
													])
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='jfr',
	description='Starts or stops a JFR profiling.',
	opLevel=4
)
def build_jfr_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(name='start'),
		KeywordSchema(name='stop')
	]


@addCommand(
	name='kick',
	description='Kicks a player off a server.',
	opLevel=3
)
def build_kick_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			])
		),
	]


@addCommand(
	name='kill',
	description='Kills entities (players, mobs, items, etc.).',
	opLevel=2
)
def build_kill_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,  # An entity is required to run the command without args
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
		),
	]


@addCommand(
	name='list',
	description='Lists players on the server.',
	opLevel=0
)
def build_list_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		KeywordSchema('uuids'),
	]


@addCommand(
	name='locate',
	description='Locates closest structure, biome, or point of interest (poi).',
	opLevel=2
)
def build_locate_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='structure',
			next=Options([
				ArgumentSchema(
					name='structure',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.STRUCTURE, allowTags=True),
				)
			])
		),
		KeywordSchema(
			name='biome',
			next=Options([
				ArgumentSchema(
					name='biome',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.BIOME, allowTags=True),
				)
			])
		),
		KeywordSchema(
			name='poi',
			next=Options([
				ArgumentSchema(
					name='poi',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema='point_of_interest_type', allowTags=True),
				)
			])
		)
	]


@addCommand(
	name='locatebiome',
	description='Locates closest biome.',
	removed=True,
	removedVersion='1.19',
	removedComment='Replaced with `/locate biome`',
	opLevel=2
)
def build_locatebiome_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='biome',
			type=MINECRAFT_RESOURCE_LOCATION,
			args=dict(schema=RESOURCES.WORLDGEN.BIOME, allowTags=True),
		),
	]


@addCommand(
	name='loot',
	description='Drops items from an inventory slot onto the ground.',
	opLevel=2
)
def build_loot_args(_: FullMCData) -> list[CommandPartSchema]:
	LOOT_TARGETS = [
		KeywordSchema(
			name='spawn',
			next=Options([
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_VEC3,  # uses float values
				),
			])
		),
		KeywordSchema(
			name='replace',
			next=Options([
				SwitchSchema(
					name='REPLACE',
					options=Options([
						KeywordSchema(
							name='entity',
							next=Options([
								ArgumentSchema(
									name='entities',
									type=MINECRAFT_ENTITY,
								),
							])
						),
						KeywordSchema(
							name='block',
							next=Options([
								ArgumentSchema(
									name='targetPos',
									type=MINECRAFT_BLOCK_POS,
								),
							])
						),
					]),
					next=Options([
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='count',
									type=BRIGADIER_INTEGER,
								),
							])
						),

					])
				),
			])
		),
		KeywordSchema(
			name='give',
			next=Options([
				ArgumentSchema(
					name='players',
					type=MINECRAFT_ENTITY,
				),
			])
		),
		KeywordSchema(
			name='insert',
			next=Options([
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			])
		),
	]
	LOOT_SOURCES = [
		KeywordSchema(
			name='fish',
			next=Options([
				ArgumentSchema(
					name='loot_table',
					type=MINECRAFT_LOOT_TABLE,
					next=Options([
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='hand',
									type=makeLiteralsArgumentType([b'mainhand', b'offhand']),
								),
								ArgumentSchema(
									name='tool',
									type=MINECRAFT_ITEM_STACK,
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='loot',
			next=Options([
				ArgumentSchema(
					name='loot_table',
					type=MINECRAFT_LOOT_TABLE,
				),
			])
		),
		KeywordSchema(
			name='kill',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			])
		),
		KeywordSchema(
			name='mine',
			next=Options([
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='hand',
							type=makeLiteralsArgumentType([b'mainhand', b'offhand']),
						),
						ArgumentSchema(
							name='tool',
							type=MINECRAFT_ITEM_STACK,
						),
					])
				),
			])
		),
	]
	return [
		SwitchSchema(
			name='TARGET',
			options=Options(LOOT_TARGETS),
			next=Options([
				SwitchSchema(
					name='SOURCE',
					options=Options(LOOT_SOURCES),
				),
			])
		),
	]


@addCommand(
	name='me',
	description='Displays a message about the sender.',
	opLevel=0
)
def build_me_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='action',
			type=MINECRAFT_MESSAGE,
		)
	]


@addCommand(
	names=('msg', 'tell', 'w'),
	description='An alias of /tell and /w. Displays a private message to other players.',
	opLevel=0
)
def build_msg_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='message',
					type=MINECRAFT_MESSAGE,
				),
			])
		),
	]


@addCommand(
	name='op',
	description='Grants operator status to a player.',
	opLevel=3,
	availableInSP=False
)
def build_op_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]


@addCommand(
	name='pardon',
	description='Removes entries from the banlist.',
	opLevel=3,
	availableInSP=False
)
def build_pardon_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]


@addCommand(
	name='pardon-ip',
	description='Removes entries from the banlist.',
	opLevel=3,
	availableInSP=False
)
def build_pardon_ip_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='target',
			type=BRIGADIER_STRING,
		),
	]


@addCommand(
	name='particle',
	description='Creates particles.',
	opLevel=2
)
def build_particle_args(_: FullMCData) -> list[CommandPartSchema]:
	# particle <name> [<pos>] [<delta> <speed> <count> [force|normal] [<viewers>]]
	PARTICLE_ARGUMENT_OPTIONS = Options([
		TERMINAL,
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_VEC3,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='delta',
					type=MINECRAFT_VEC3,
					next=Options([
						ArgumentSchema(
							name='speed',
							type=BRIGADIER_FLOAT,
							next=Options([
								ArgumentSchema(
									name='count',
									type=BRIGADIER_INTEGER,
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='display_mode',
											type=makeLiteralsArgumentType([b'force', b'normal']),
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='viewers',
													type=MINECRAFT_ENTITY
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
	])
	_SPECIAL_PARTICLES_LIST = [
		KeywordSchema(
			name='dust',
			next=Options([
				ArgumentSchema(
					name='red',
					type=BRIGADIER_FLOAT,
					next=Options([
						ArgumentSchema(
							name='green',
							type=BRIGADIER_FLOAT,
							next=Options([
								ArgumentSchema(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=Options([
										ArgumentSchema(
											name='size',
											type=BRIGADIER_FLOAT,
											next=PARTICLE_ARGUMENT_OPTIONS
										),
									])
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='dust_color_transition',
			next=Options([
				ArgumentSchema(
					name='red',
					type=BRIGADIER_FLOAT,
					next=Options([
						ArgumentSchema(
							name='green',
							type=BRIGADIER_FLOAT,
							next=Options([
								ArgumentSchema(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=Options([
										ArgumentSchema(
											name='size',
											type=BRIGADIER_FLOAT,
											next=Options([
												ArgumentSchema(
													name='red',
													type=BRIGADIER_FLOAT,
													next=Options([
														ArgumentSchema(
															name='green',
															type=BRIGADIER_FLOAT,
															next=Options([
																ArgumentSchema(
																	name='blue',
																	type=BRIGADIER_FLOAT,
																	next=PARTICLE_ARGUMENT_OPTIONS
																),
															])
														),
													])
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='block_marker',
			next=Options([
				ArgumentSchema(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENT_OPTIONS
				),
			])
		),
		KeywordSchema(
			name='falling_dust',
			next=Options([
				ArgumentSchema(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENT_OPTIONS
				),
			])
		),
		KeywordSchema(
			name='item',
			next=Options([
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=PARTICLE_ARGUMENT_OPTIONS
				),
			])
		),
		KeywordSchema(
			name='vibration',
			next=Options([
				ArgumentSchema(
					name='x_start',
					type=BRIGADIER_DOUBLE,
					next=Options([
						ArgumentSchema(
							name='y_start',
							type=BRIGADIER_DOUBLE,
							next=Options([
								ArgumentSchema(
									name='z_start',
									type=BRIGADIER_DOUBLE,
									next=Options([
										ArgumentSchema(
											name='x_end',
											type=BRIGADIER_DOUBLE,
											next=Options([
												ArgumentSchema(
													name='y_end',
													type=BRIGADIER_DOUBLE,
													next=Options([
														ArgumentSchema(
															name='z_end',
															type=BRIGADIER_DOUBLE,
															next=Options([
																ArgumentSchema(
																	name='duration',
																	type=BRIGADIER_INTEGER,
																	next=PARTICLE_ARGUMENT_OPTIONS
																),
															])
														),
													])
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]
	_SPECIAL_PARTICLES = []
	for particle in _SPECIAL_PARTICLES_LIST:
		_SPECIAL_PARTICLES.append(particle)
		particle = copy(particle)
		particle.name = f'minecraft:{particle.name}'
		_SPECIAL_PARTICLES.append(particle)
	del _SPECIAL_PARTICLES_LIST
	return [
		*_SPECIAL_PARTICLES,
		ArgumentSchema(
			name='name',
			type=MINECRAFT_PARTICLE,
			next=PARTICLE_ARGUMENT_OPTIONS
		),
	]


@addCommand(
	name='perf',
	description='Captures info and metrics about the game for 10 seconds.',
	opLevel=4,
	availableInSP=False
)
def build_perf_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema('start'),
		KeywordSchema('stop'),
	]


@addCommand(
	name='place',
	description='Places features, jigsaws, structures, and templates at a given location.',
	opLevel=2
)
def build_place_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		# place feature <feature> [pos]
		KeywordSchema(
			name='feature',
			next=Options([
				ArgumentSchema(
					name='feature',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.CONFIGURED_FEATURE),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							description="The position to use as the origin for the feature placement (if omitted, ~ ~ ~ is used)."
						),
					])
				),
			])
		),
		# place jigsaw <pool> <start> <depth> [pos]
		KeywordSchema(
			name='jigsaw',
			next=Options([
				ArgumentSchema(
					name='pool',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.TEMPLATE_POOL),
					next=Options([
						ArgumentSchema(
							name='start',
							type=MINECRAFT_RESOURCE_LOCATION,
							args=dict(schema='any'),
							description="Specifies the jigsaw block that is connected to when generating the start structure pool.",
							next=Options([
								ArgumentSchema(
									name='max_depth',
									type=BRIGADIER_INTEGER,
									args=dict(min=1, max=7),
									description="The maximum number of jigsaw connections to traverse during placement.",
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='position',
											type=MINECRAFT_BLOCK_POS,  # todo what does this actually do? doesn't the placement of the jigsaw block already define a a location?
											description="The position to use as the origin for the feature placement (if omitted, ~ ~ ~ is used)."
										),
									])
								),
							])
						),
					])
				),
			])
		),
		# place structure <structure> [pos]
		KeywordSchema(
			name='structure',
			next=Options([
				ArgumentSchema(
					name='structure',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.STRUCTURE),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							description="The position to use as the origin for the structure placement (if omitted, ~ ~ ~ is used)."
						),
					])
				),
			])
		),
		# place template <template> [pos] [rotation] [mirror] [integrity] [seed]
		KeywordSchema(
			name='template',
			next=Options([
				ArgumentSchema(
					name='structure',
					type=MINECRAFT_RESOURCE_LOCATION,
					args=dict(schema=RESOURCES.WORLDGEN.STRUCTURE),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							description="The position to use as the origin for the template placement.",
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='rotation',
									type=MINECRAFT_TEMPLATE_ROTATION,
									description="Specifies the rotation to apply to the placed template.",
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='mirror',
											type=MINECRAFT_TEMPLATE_MIRROR,
											description="Specifies the mirroring to apply to the placed template.",
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='integrity',
													type=BRIGADIER_FLOAT,
													args=dict(min=0., max=1.),
													description="Specifies the integrity value to apply to the placed template (how complete the template that gets placed is). If omitted, defaults to 1.0.",
													next=Options([
														TERMINAL,
														ArgumentSchema(
															name='seed',
															type=BRIGADIER_INTEGER,
															description="Specifies the seed to use for randomized degradation of the placed template when integrity is less than 1. If omitted, defaults to 0."
														),
													])
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='placefeature',
	description='Places a configured feature at a given location.',
	removed=True,
	removedVersion='1.19',
	removedComment='Replaced with `/place feature`',
	opLevel=2
)
def build_placefeature_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='id',
			type=MINECRAFT_RESOURCE_LOCATION,
			args=dict(schema='feature'),
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='source',
					type=MINECRAFT_BLOCK_POS,
					description="The position to use as the origin for the feature placement (if omitted, ~ ~ ~ is used)."
				),
			])
		),
	]


@addCommand(
	name='playsound',
	description='Plays a sound.',
	opLevel=2
)
def build_playsound_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='sound',
			type=MINECRAFT_RESOURCE_LOCATION,
			next=Options([
				ArgumentSchema(
					name='source',
					type=makeLiteralsArgumentType([b'master', b'music', b'record', b'weather', b'block', b'hostile', b'neutral', b'player', b'ambient', b'voice']),
					next=Options([
						ArgumentSchema(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='pos',
									type=MINECRAFT_VEC3,
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='volume',
											type=BRIGADIER_FLOAT,
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='pitch',
													type=BRIGADIER_FLOAT,
													next=Options([
														TERMINAL,
														ArgumentSchema(
															name='minVolume',
															type=BRIGADIER_FLOAT,
														),
													])
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='publish',
	description='Opens single-player world to local network.',
	opLevel=4,
	availableInMP=False
)
def build_publish_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		ArgumentSchema(
			name='allowCommands',
			type=BRIGADIER_BOOL,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='gamemode',
					type=MINECRAFT_GAME_MODE,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='port',
							type=BRIGADIER_INTEGER,
							args=dict(min=0, max=65535)
						),
					])
				),
			])
		),
	]


@addCommand(
	name='random',
	description='Draws a random value.',
	opLevel="0 without sequence; 2 otherwise"
)
def build_random_args(_: FullMCData) -> list[CommandPartSchema]:
	# /random (value|roll) <range> [<sequenceId>]
	#     Extract random numbers.
	#
	# /random reset (*|<sequenceId>) [<seed>] [<includeWorldSeed>] [<includeSequenceId>]
	#     Reset the random number sequence.


	SEQUENCE_ID = ArgumentSchema(
		name='sequenceId',
		type=MINECRAFT_RESOURCE_LOCATION,
		args=dict(schema='random_number_sequence'),
		description="Specifies the name of a random number sequence to be used. If you specify a sequenceId that does not exist, it is created on the spot and the command is executed."
	)

	return [
		SwitchSchema(
			name='draw',
			description="Extract random numbers.",
			options=Options([
				KeywordSchema(
					name='value',
					description="Draws a new random value. The results are displayed only to the player using the command"
				),
				KeywordSchema(
					name='roll',
					description="Draws a new random value. The results are revealed to all players"
				)
			]),
			next=Options([
				ArgumentSchema(
					name='range',
					type=MINECRAFT_INT_RANGE,
					args=dict(minSize=2, maxSize=2147483647),
					next=Options([
						TERMINAL,
						SEQUENCE_ID
					])
				)
			])
		),
		KeywordSchema(
			name='reset',
			description="Reset the random number sequence.",
			next=Options([
				SwitchSchema(
					name='sequenceId',
					description="The sequence.",
					options=Options([
						KeywordSchema(
							name='*',
							description="all sequenceIds"
						),
						SEQUENCE_ID
					]),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='seed',
							type=BRIGADIER_LONG,
							description="The seed value used to reset the random number sequence. Default is `0`.",
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='includeWorldSeed',
									type=BRIGADIER_BOOL,
									description="Whether to incorporate the world seed value when seeding the random number sequence. Default is `true`. If set to `false`, the random number sequence is reset in the same way regardless of the world.",
									next=Options([
										TERMINAL,
										ArgumentSchema(
											name='includeSequenceId',
											type=BRIGADIER_BOOL,
											description="Whether to include the ID of the random number column when seeding the random number column. Default is `true`. If set to `false`, the result of resetting the random number sequence is the same regardless of the random number sequence ID."
										)
									])
								)
							])
						)
					])
				)
			])
		)
	]


@addCommand(
	name='recipe',
	description='Gives or takes player recipes.',
	opLevel=2
)
def build_recipe_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='action',
			type=makeLiteralsArgumentType([b'give', b'take']),
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
					next=Options([
						KeywordSchema('*'),
						ArgumentSchema(
							name='recipe',
							type=MINECRAFT_RESOURCE_LOCATION,
							args=dict(schema='feature', allowTags=True),
						),
					])
				),
			])
		),
	]


@addCommand(
	name='reload',
	description='Reloads loot tables, advancements, and functions from disk.',
	opLevel=2
)
def build_reload_args(_: FullMCData) -> list[CommandPartSchema]:
	return [TERMINAL]


@addCommand(
	name='replaceitem',
	description='Replaces items in inventories.',
	removed=True,
	removedVersion='1.17',
	removedComment='Replaced with `/item replace`',
	opLevel=2
)
def build_replaceitem_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='OUTDATED!',
			type=MINECRAFT_MESSAGE,
		),
	]


@addCommand(
	name='return',
	description='Can be used to control execution flow inside functions and change their return value',
	opLevel="N/A"
)
def build_replaceitem_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='value',
			type=BRIGADIER_INTEGER,
		),
	]


@addCommand(
	name='ride',
	description='Used to make entities ride other entities, stop entities from riding, make rides evict their riders, or summon rides or riders.',
	opLevel='-'
)
def build_ride_args(_: FullMCData) -> list[CommandPartSchema]:
	# ride <target> mount <vehicle>
	# ride <target> dismount
	return [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			args=dict(single=True),
			next=Options([
				KeywordSchema(
					name='mount',
					next=Options([
						ArgumentSchema(
							name='target',
							type=MINECRAFT_ENTITY,
							args=dict(single=True)
						)
					])
				),
				KeywordSchema(
					name='dismount'
				)
			])
		)
	]


@addCommand(
	name='save-all',
	description='Saves the server to disk.',
	opLevel=4,
	availableInSP=False
)
def build_save_all_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		KeywordSchema('flush'),
	]


@addCommand(
	name='save-off',
	description='Disables automatic server saves.',
	opLevel=4,
	availableInSP=False
)
def build_save_off_args(_: FullMCData) -> list[CommandPartSchema]:
	return [TERMINAL]


@addCommand(
	name='save-on',
	description='Enables automatic server saves.',
	opLevel=4,
	availableInSP=False
)
def build_save_on_args(_: FullMCData) -> list[CommandPartSchema]:
	return [TERMINAL]


@addCommand(
	name='say',
	description='Displays a message to multiple players.',
	opLevel=2
)
def build_say_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]


@addCommand(
	name='schedule',
	description='Delays the execution of a function.',
	opLevel=2
)
def build_schedule_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='function',
			next=Options([
				ArgumentSchema(
					name='function',
					type=MINECRAFT_FUNCTION,
					next=Options([
						ArgumentSchema(
							name='time',
							type=MINECRAFT_TIME,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='replace_behaviour',
									type=makeLiteralsArgumentType([b'append', b'replace']),
								),
							])
						),
					])
				),
			])
		),
		KeywordSchema(
			name='clear',
			next=Options([
				ArgumentSchema(
					name='function',
					type=MINECRAFT_FUNCTION,
				),
			])
		),

	]


@addCommand(
	name='scoreboard',
	description='Manages scoreboard objectives and players.',
	opLevel=2
)
def build_scoreboard_args(_: FullMCData) -> list[CommandPartSchema]:
	SCOREBOARD_OBJECTIVES = []
	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='list'))
	# scoreboard objectives add <objective> <criteria> [<displayName>]
	SCOREBOARD_OBJECTIVES.append(
		KeywordSchema(
			name='add',
			next=Options([
				ArgumentSchema(
					name='objective',
					type=BRIGADIER_STRING,
					next=Options([
						ArgumentSchema(
							name='criteria',
							type=MINECRAFT_OBJECTIVE_CRITERIA,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='displayName',
									type=MINECRAFT_COMPONENT,
								),
							])
						),
					])
				),
			])
		)
	)
	# scoreboard objectives remove <objective>
	SCOREBOARD_OBJECTIVES.append(
		KeywordSchema(
			name='remove',
			next=Options([
				ArgumentSchema(
					name='objective',
					type=MINECRAFT_OBJECTIVE,
				),
			])
		)
	)
	# scoreboard objectives setdisplay <slot> [<objective>]
	SCOREBOARD_OBJECTIVES.append(
		KeywordSchema(
			name='setdisplay',
			next=Options([
				ArgumentSchema(
					name='slot',
					type=MINECRAFT_SCOREBOARD_SLOT,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
						),
					])
				),
			])
		)
	)
	# scoreboard objectives modify <objective> displayname <displayName>
	# scoreboard objectives modify <objective> rendertype (hearts|integer)
	SCOREBOARD_OBJECTIVES.append(
		KeywordSchema(
			name='modify',
			next=Options([
				ArgumentSchema(
					name='objective',
					type=MINECRAFT_OBJECTIVE,
					next=Options([
						KeywordSchema(
							name='displayname',
							next=Options([
								ArgumentSchema(
									name='displayName',
									type=MINECRAFT_COMPONENT,
								),
							])
						),
						KeywordSchema(
							name='rendertype',
							next=Options([
								ArgumentSchema(
									name='rendertype',
									type=makeLiteralsArgumentType([b'hearts', b'integer']),
								),
							])
						),
					])
				),
			])
		)
	)
	SCOREBOARD_PLAYERS = []
	# scoreboard players list [<target>]
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='list',
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='target',
					type=MINECRAFT_SCORE_HOLDER,
				),
			])
		)
	)
	# scoreboard players get <target> <objective>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='get',
			next=Options([
				ArgumentSchema(
					name='target',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
						),
					])
				),
			])
		)
	)
	# scoreboard players set <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='set',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								ArgumentSchema(
									name='score',
									type=BRIGADIER_INTEGER,
								),
							])
						),
					])
				),
			])
		)
	)
	# scoreboard players add <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='add',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								ArgumentSchema(
									name='score',
									type=BRIGADIER_INTEGER,
								),
							])
						),
					])
				),
			])
		)
	)
	# scoreboard players remove <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='remove',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								ArgumentSchema(
									name='score',
									type=BRIGADIER_INTEGER,
								),
							])
						),
					])
				),
			])
		)
	)
	# scoreboard players reset <targets> [<objective>]
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='reset',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
						),
					])
				),
			])
		)
	)
	# scoreboard players enable <targets> <objective>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='enable',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
						),
					])
				),
			])
		)
	)
	# scoreboard players operation <targets> <targetObjective> <operation> <source> <sourceObjective>
	SCOREBOARD_PLAYERS.append(
		KeywordSchema(
			name='operation',
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='targetObjective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								ArgumentSchema(
									name='operation',
									type=MINECRAFT_OPERATION,
									next=Options([
										ArgumentSchema(
											name='source',
											type=MINECRAFT_SCORE_HOLDER,
											next=Options([
												ArgumentSchema(
													name='sourceObjective',
													type=MINECRAFT_OBJECTIVE,
												),
											])
										),
									])
								),
							])
						),
					])
				),
			])
		)
	)
	return [
		KeywordSchema(
			name='objectives',
			next=Options(SCOREBOARD_OBJECTIVES)
		),
		KeywordSchema(
			name='players',
			next=Options(SCOREBOARD_PLAYERS)
		),
	]


@addCommand(
	name='seed',
	description='Displays the world seed.',
	opLevel='0 in singleplayer, 2 in multiplayer'
)
def build_seed_args(_: FullMCData) -> list[CommandPartSchema]:
	return [TERMINAL]


@addCommand(
	name='setblock',
	description='Changes a block to another block.',
	opLevel=2
)
def build_setblock_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=Options([
				ArgumentSchema(
					name='block',
					type=MINECRAFT_BLOCK_STATE,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='operation',
							type=makeLiteralsArgumentType([b'destroy', b'keep', b'replace']),
						),
					])
				),
			])
		),
	]


@addCommand(
	name='setidletimeout',
	description='Sets the time before idle players are kicked.',
	opLevel=3,
	availableInSP=False
)
def build_setidletimeout_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='minutes',
			type=BRIGADIER_INTEGER,
		),
	]


@addCommand(
	name='setworldspawn',
	description='Sets the world spawn.',
	opLevel=2
)
def build_setworldspawn_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='angle',
					type=MINECRAFT_ANGLE,
				),
			])
		),
	]


@addCommand(
	name='spawnpoint',
	description='Sets the spawn point for a player.',
	opLevel=2
)
def build_spawnpoint_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		TERMINAL,
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='angle',
							type=MINECRAFT_ANGLE,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='spectate',
	description='Make one player in spectator mode spectate an entity.',
	opLevel=2
)
def build_spectate_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='player',
					type=MINECRAFT_ENTITY,
				),
			])
		),
	]


@addCommand(
	name='spreadplayers',
	description='Teleports entities to random locations.',
	opLevel=2
)
def build_spreadplayers_args(_: FullMCData) -> list[CommandPartSchema]:
	# spreadplayers <center> <spreadDistance> <maxRange> <respectTeams> <targets>
	# spreadplayers <center> <spreadDistance> <maxRange> under <maxHeight> <respectTeams> <targets>
	SPREADPLAYERS_RESPECT_TEAMS = ArgumentSchema(
		name='respectTeams',
		type=BRIGADIER_BOOL,
		next=Options([
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_ENTITY,
			),
		])
	)
	return [
		ArgumentSchema(
			name='center',
			type=MINECRAFT_VEC2,
			next=Options([
				ArgumentSchema(
					name='spreadDistance',
					type=BRIGADIER_FLOAT,
					next=Options([
						ArgumentSchema(
							name='maxRange',
							type=BRIGADIER_FLOAT,
							next=Options([
								KeywordSchema(
									name='under',
									next=Options([
										ArgumentSchema(
											name='maxHeight',
											type=BRIGADIER_INTEGER,
											next=Options([SPREADPLAYERS_RESPECT_TEAMS])
										),
									])
								),
								SPREADPLAYERS_RESPECT_TEAMS
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='stop',
	description='Stops a server.',
	opLevel=4,
	availableInSP=False
)
def build_stop_args(_: FullMCData) -> list[CommandPartSchema]:
	return [TERMINAL]


@addCommand(
	name='stopsound',
	description='Stops a sound.',
	opLevel=2
)
def build_stopsound_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='source',
					type=makeLiteralsArgumentType([b'*', b'master', b'music', b'record', b'weather', b'block', b'hostile', b'neutral', b'player', b'ambient', b'voice']),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='sound',
							type=MINECRAFT_RESOURCE_LOCATION,
							description="Specifies the sound to stop. Must be a resource location. \n\nMust be a sound event defined in `sounds.json` (for example, `entity.pig.ambient`).",
						),
					])
				),
			])
		),
	]


@addCommand(
	name='summon',
	description='Summons an entity.',
	opLevel=2
)
def build_summon_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='entity',
			type=MINECRAFT_ENTITY_SUMMON,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_VEC3,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='tag',
	description='Controls entity tags.',
	opLevel=2
)
def build_tag_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				KeywordSchema(
					name='add',
					next=Options([
						ArgumentSchema(
							name='name',
							type=BRIGADIER_STRING,
						),
					])
				),
				KeywordSchema('list'),
				KeywordSchema(
					name='remove',
					next=Options([
						ArgumentSchema(
							name='name',
							type=BRIGADIER_STRING,
						),
					])
				),
			])
		),
	]


@addCommand(
	name='team',
	description='Controls teams.',
	opLevel=2
)
def build_team_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='list',
			description="Lists all teams, with their display names and the amount of entities in them. The optional `<team>` can be used to specify a particular team.",
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			])
		),
		KeywordSchema(
			name='add',
			description="Creates a team with the given name and optional display name. `<displayName>` defaults to `<objective>` when unspecified.",
			next=Options([
				ArgumentSchema(
					name='team',
					type=BRIGADIER_STRING,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='displayName',
							type=MINECRAFT_COMPONENT,
						),
					])
				),
			])
		),
		KeywordSchema(
			name='remove',
			description="Deletes the specified team.",
			next=Options([
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			])
		),
		KeywordSchema(
			name='empty',
			description="Removes all members from the named team.",
			next=Options([
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			])
		),
		KeywordSchema(
			name='join',
			description="Assigns the specified entities to the specified team. If no entities is specified, makes the executor join the team.",
			next=Options([
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='members',
							type=MINECRAFT_SCORE_HOLDER,
						),
					])
				),
			])
		),
		KeywordSchema(
			name='leave',
			description="Makes the specified entities leave their teams.",
			next=Options([
				ArgumentSchema(
					name='members',
					type=MINECRAFT_SCORE_HOLDER,
				),
			])
		),
		KeywordSchema(
			name='modify',
			description="Modifies the options of the specified team.",
			next=Options([
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
					next=Options([
						SwitchSchema(
							name='option',
							options=Options([
								KeywordSchema(
									name='displayName',
									description="Set the display name of the team.",
									next=Options([
										ArgumentSchema(
											name='displayName',
											type=MINECRAFT_COMPONENT,
											description="Specifies the team name to be displayed. Must be a raw JSON text.",
										),
									])
								),
								KeywordSchema(
									name='color',
									description="Decide the color of the team and players in chat, above their head, on the Tab menu, and on the sidebar. Also changes the color of the outline of the entities caused by the Glowing effect.",
									next=Options([
										ArgumentSchema(
											name='value',
											type=MINECRAFT_COLOR,
											description="Must be a color.\n\nDefaults to reset. If reset, names are shown in default color and formatting.",
										),
									])
								),
								KeywordSchema(
									name='friendlyFire',
									description="Enable/Disable players inflicting damage on each other when on the same team. (Note: players can still inflict status effects on each other.) Does not affect some non-player entities in a team.",
									next=Options([
										ArgumentSchema(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Enable players inflicting damage on each other when in the same team.\n  - false - Disable players inflicting damage on each other when in the same team.",
										),
									])
								),
								KeywordSchema(
									name='seeFriendlyInvisibles',
									description="Decide players can see invisible players on their team as whether semi-transparent or completely invisible.",
									next=Options([
										ArgumentSchema(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Can see invisible players on the same team semi-transparently.\n  - false - Cannot see invisible players on the same team.",
										),
									])
								),
								KeywordSchema(
									name='nametagVisibility',
									description="Decide whose name tags above their heads can be seen.",
									next=Options([
										KeywordSchema(
											name='never',
											description="Name above player's head cannot be seen by any players.",
										),
										KeywordSchema(
											name='hideForOtherTeams',
											description="Name above player's head can be seen only by players in the same team.",
										),
										KeywordSchema(
											name='hideForOwnTeam',
											description="Name above player's head cannot be seen by all the players in the same team.",
										),
										KeywordSchema(
											name='always',
											description="(Default) Name above player's head can be seen by all the players.",
										),
									])
								),
								KeywordSchema(
									name='deathMessageVisibility',
									description="Control the visibility of death messages for players.",
									next=Options([
										KeywordSchema(
											name='never',
											description="Hide death message for all the players.",
										),
										KeywordSchema(
											name='hideForOtherTeams',
											description="Hide death message to all the players who are not in the same team.",
										),
										KeywordSchema(
											name='hideForOwnTeam',
											description="Hide death message to players in the same team.",
										),
										KeywordSchema(
											name='always',
											description="(Default) Make death message visible to all the players.",
										),
									])
								),
								KeywordSchema(
									name='collisionRule',
									description="Controls the way the entities on the team collide with other entities.",
									next=Options([
										KeywordSchema(
											name='always',
											description="(Default) Normal collision.",
										),
										KeywordSchema(
											name='never',
											description="No entities can push entities in this team.",
										),
										KeywordSchema(
											name='pushOtherTeams',
											description="Entities in this team can be pushed only by other entities in the same team.",
										),
										KeywordSchema(
											name='pushOwnTeam',
											description="Entities in this team cannot be pushed by another entity in this team.",
										),
									])
								),
								KeywordSchema(
									name='prefix',
									description="Modifies the prefix that displays before players' names.",
									next=Options([
										ArgumentSchema(
											name='prefix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the prefix to display. Must be a raw JSON text.",
										),
									])
								),
								KeywordSchema(
									name='suffix',
									description="Modifies the suffix that displays before players' names.",
									next=Options([
										ArgumentSchema(
											name='suffix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the suffix to display. Must be a raw JSON text.",
										),
									])
								),
							]),
						),
					])
				),
			])
		),
	]


@addCommand(
	names=('teammsg', 'tm'),
	description='An alias of /tm. Specifies the message to send to team.',
	opLevel=0
)
def build_teammsg_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]


@addCommand(
	names=('teleport', 'tp'),
	description='An alias of /tp. Teleports entities.',
	opLevel=2
)
def build_teleport_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		# ArgumentSchema(
		# 	name='destination',
		# 	type=MINECRAFT_ENTITY,
		# ),
		ArgumentSchema(
			name='location',
			type=MINECRAFT_VEC3,
		),
		ArgumentSchema(
			name='targets|destination',
			type=MINECRAFT_ENTITY,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='location',
					type=MINECRAFT_VEC3,
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='rotation',
							type=MINECRAFT_ROTATION,
						),
						KeywordSchema(
							name='facing',
							next=Options([
								ArgumentSchema(
									name='facingLocation',
									type=MINECRAFT_VEC3,
								),
								KeywordSchema(
									name='entity',
									next=Options([
										ArgumentSchema(
											name='facingEntity',
											type=MINECRAFT_ENTITY,
											next=Options([
												TERMINAL,
												ArgumentSchema(
													name='facingAnchor',
													type=MINECRAFT_ENTITY_ANCHOR,
												),
											])
										),
									])
								),
							])
						),
					])
				),
				ArgumentSchema(
					name='destination',
					type=MINECRAFT_ENTITY,
				),
			])
		),
	]


@addCommand(
	name='tellraw',
	description='Displays a JSON message to players.',
	opLevel=2
)
def build_tellraw_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='message',
					type=MINECRAFT_COMPONENT,
				),
			])
		),
	]


@addCommand(
	name='testfor',
	description='Counts entities matching specified conditions.',
	removed=True,
	removedVersion='1.13',
	removedComment='Use `/execute if` instead',  # TODO: removedComment for '/testfor' command
	opLevel=2
)
def build_testfor_args(_: FullMCData) -> list[CommandPartSchema]:
	return []


@addCommand(
	name='testforblock',
	description='Tests whether a block is in a location.',
	removed=True,
	removedVersion='1.13',
	removedComment='Use `/execute if block` instead',
	opLevel=2
)
def build_testforblock_args(_: FullMCData) -> list[CommandPartSchema]:
	return []


@addCommand(
	name='testforblocks',
	description='Tests whether the blocks in two regions match.',
	removed=True,
	removedVersion='1.13',
	removedComment='Use `/execute if` instead',
	opLevel=2
)
def build_testforblocks_args(_: FullMCData) -> list[CommandPartSchema]:
	return []


@addCommand(
	name='time',
	description="Changes or queries the world's game time.",
	opLevel=2
)
def build_time_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='add',
			description="Adds `<time>` to the in-game daytime.",
			next=Options([
				ArgumentSchema(
					name='time',
					type=MINECRAFT_TIME,
				),
			])
		),
		KeywordSchema(
			name='query',
			description="Queries current time.",
			next=Options([
				ArgumentSchema(
					name='daytime|gametime|day',
					type=makeLiteralsArgumentType([b'daytime', b'gametime', b'day']),
				),
			])
		),
		KeywordSchema(
			name='set',
			next=Options([
				ArgumentSchema(
					name='timeSpec',
					type=makeLiteralsArgumentType([b'day', b'night', b'noon', b'midnight']),
				),
			])
		),
		KeywordSchema(
			name='set',
			next=Options([
				ArgumentSchema(
					name='time',
					type=MINECRAFT_TIME,
				),
			])
		),
	]


@addCommand(
	name='title',
	description='Manages screen titles.',
	opLevel=2
)
def build_title_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=Options([
				ArgumentSchema(
					name='clear|reset',
					type=makeLiteralsArgumentType([b'clear', b'reset']),
				),
				ArgumentSchema(
					name='title|subtitle|actionbar',
					type=makeLiteralsArgumentType([b'title', b'subtitle', b'actionbar']),
					next=Options([
						ArgumentSchema(
							name='title',
							type=MINECRAFT_COMPONENT,
						),
					])
				),
				KeywordSchema(
					name='times',
					next=Options([
						ArgumentSchema(
							name='fadeIn',
							type=MINECRAFT_TIME,
							next=Options([
								ArgumentSchema(
									name='stay',
									type=MINECRAFT_TIME,
									next=Options([
										ArgumentSchema(
											name='fadeOut',
											type=MINECRAFT_TIME,
										),
									])
								),
							])
						),
					])
				),
			])
		),
	]


@addCommand(
	name='trigger',
	description='Sets a trigger to be activated.',
	opLevel=0
)
def build_trigger_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='objective',
			type=MINECRAFT_OBJECTIVE,
			next=Options([
				TERMINAL,
				KeywordSchema(
					name='add',
					next=Options([
						ArgumentSchema(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					])
				),
				KeywordSchema(
					name='set',
					next=Options([
						ArgumentSchema(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					]),
				),
			])
		),
	]


@addCommand(
	name='weather',
	description='Sets the weather.',
	opLevel=2
)
def build_weather_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='objective',
			type=makeLiteralsArgumentType([b'clear', b'rain', b'thunder']),
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='duration',
					type=MINECRAFT_TIME,
				),
			])
		),
	]


@addCommand(
	name='whitelist',
	description='Manages server whitelist.',
	opLevel=3,
	availableInSP=False
)
def build_whitelist_args(_: FullMCData) -> list[CommandPartSchema]:
	# TODO: BASIC_CMD_INFO[b'whitelist'].next
	return []


@addCommand(
	name='worldborder',
	description='Manages the world border.',
	opLevel=2
)
def build_worldborder_args(_: FullMCData) -> list[CommandPartSchema]:
	# TODO: BASIC_CMD_INFO[b'worldborder'].next
	return []
