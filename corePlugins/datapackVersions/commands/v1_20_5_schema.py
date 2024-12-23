"""
currently at minecraft version 1.20.3 (1.20.3-rc1)
"""

import copy

from cat.utils.collections_ import ChainedList
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, CommandPartSchema, MCFunctionSchema, Options, TERMINAL, \
	KeywordSchema, SwitchSchema
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData
from . import v1_20_3_schema
from .argumentTypes import *
from .v1_20_2_schema import CommandsCreator, getArgOptions


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_20_5 = getFullMcData('1.20.5')
	schema_v29 = COMMANDS_V29.buildSchema(version1_20_5)
	schema_v30 = COMMANDS_V30.buildSchema(version1_20_5)
	schema_v31 = COMMANDS_V31.buildSchema(version1_20_5)
	schema_v33 = COMMANDS_V33.buildSchema(version1_20_5)
	schema_v34 = COMMANDS_V34.buildSchema(version1_20_5)
	schema_v36 = COMMANDS_V36.buildSchema(version1_20_5)
	schema_v39 = COMMANDS_V39.buildSchema(version1_20_5)
	schema_v41 = COMMANDS_V41.buildSchema(version1_20_5)
	return {
		'Minecraft 24w04a': schema_v29,
		'Minecraft 24w05b': schema_v30,
		'Minecraft 24w06a': schema_v31,
		'Minecraft 24w09a': schema_v33,
		'Minecraft 24w10a': schema_v34,
		'Minecraft 24w12a': schema_v36,
		'Minecraft 1.20.5-pre1': schema_v39,
		'Minecraft 1.20.5': schema_v41,
		'Minecraft 1.20.6': schema_v41
	}


COMMANDS_V27: CommandsCreator = copy.deepcopy(v1_20_3_schema.COMMANDS_V26)


COMMANDS_V28: CommandsCreator = copy.deepcopy(COMMANDS_V27)


COMMANDS_V29: CommandsCreator = copy.deepcopy(COMMANDS_V28)


@COMMANDS_V29.add(name='transfer', description="Triggers a transfer of a player to another server. Only exists on dedicated servers.")
def build_transfer_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		ArgumentSchema(
			name='hostname',
			description="String describing the hostname of the server to connect to.",
			type=BRIGADIER_STRING,
			subType=ST_DPE_HOSTNAME,
			next=Options([
				TERMINAL,
				ArgumentSchema(
					name='port',
					description="Denotes the port number of the server to connect to. In Java Edition, if not specified, defaults to `25565`.\n" +
								"It must be between `1` and `65535` (inclusive).",
					type=BRIGADIER_INTEGER,
					args=dict(min=1, max=65535, suggestions=[25565]),
					next=Options([
						TERMINAL,
						ArgumentSchema(
							name='players',
							description="The player(s) to transfer. If omitted, `@s` is used. The target selector must be of player type.",
							type=MINECRAFT_ENTITY,
						),
					])
				),
			])
		),
	]


COMMANDS_V30: CommandsCreator = copy.deepcopy(COMMANDS_V29)


@COMMANDS_V30.modify(name='effect')
def modify_effect_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	amplifierSchema = getArgOptions(args, 'give', 'targets', 'effect', 'DURATION', 'amplifier')
	# Potion effect amplifiers are now restricted between 0 and 127.
	amplifierSchema.args.update(dict(min=0, max=127))
	return args


COMMANDS_V31: CommandsCreator = copy.deepcopy(COMMANDS_V29)  # reverts changes in v30 (limiting of Potion effect amplifiers to 127)


COMMANDS_V33: CommandsCreator = copy.deepcopy(COMMANDS_V31)


@COMMANDS_V33.modify(name='playsound')
def modify_playsound_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	getArgOptions(args, 'sound', 'source').next.all.insert(0, TERMINAL)
	getArgOptions(args, 'sound').next.all.insert(0, TERMINAL)
	return args


@COMMANDS_V33.modify(name='attribute')
def modify_attribute_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	operationSchema = getArgOptions(args, 'target', 'attribute', 'modifier', 'add', 'uuid', 'name', 'value', 'operation')
	operationSchema.type = makeLiteralsArgumentType([b'add_value', b'add_multiplied_total', b'add_multiplied_base'])
	return args


COMMANDS_V34: CommandsCreator = copy.deepcopy(COMMANDS_V33)


@COMMANDS_V34.modify(name='execute')
def modify_execute_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	EXECUTE_INSTRUCTIONS: list[CommandPartSchema] = args
	EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS = Options(ChainedList([TERMINAL], EXECUTE_INSTRUCTIONS))
	ifArg = getArgOptions(args, 'if')
	# items <source> <slots> <item_predicate>

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
					name='source',
					type=MINECRAFT_ENTITY,
				),
			])
		),
	]
	ifArg.next.all.append(KeywordSchema(
		name='items',
		description="Checks for a matching item in the provided inventory slots.",
		next=Options([
			SwitchSchema(
				name='TARGET',
				options=Options(ITEM_SOURCE),
				next=Options([
					ArgumentSchema(
						name='slots',
						type=MINECRAFT_ITEM_SLOTS,
						next=Options([
							ArgumentSchema(
								name='item_predicate',
								type=MINECRAFT_ITEM_PREDICATE,
								next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS

							)
						])

					)
				])
			)

		])
	))
	return args


COMMANDS_V36: CommandsCreator = copy.deepcopy(COMMANDS_V34)


@COMMANDS_V36.modify(name='particle')
def modify_particle_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
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
			name='entity_effect',
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
											name='alpha',
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
	]
	_SPECIAL_PARTICLES = []
	for particle in _SPECIAL_PARTICLES_LIST:
		_SPECIAL_PARTICLES.append(particle)
		particle = copy.copy(particle)
		particle.name = f'minecraft:{particle.name}'
		_SPECIAL_PARTICLES.append(particle)
	del _SPECIAL_PARTICLES_LIST

	return _SPECIAL_PARTICLES + args


COMMANDS_V39: CommandsCreator = copy.deepcopy(COMMANDS_V36)


@COMMANDS_V39.modify(name='particle')
def modify_particle_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	# particle <name> [<pos>] [<delta> <speed> <count> [force|normal] [<viewers>]]
	# no special cases for some particles anymore.
	return [
		ArgumentSchema(
			name='particle',
			type=MINECRAFT_PARTICLE,
			next=Options([
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
									args=dict(min=0),
									next=Options([
										ArgumentSchema(
											name='count',
											type=BRIGADIER_INTEGER,
											args=dict(min=0),
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
		),
	]


COMMANDS_V41: CommandsCreator = copy.deepcopy(COMMANDS_V39)
