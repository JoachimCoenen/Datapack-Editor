"""
currently at minecraft version 1.20.6
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
	schema_v41 = COMMANDS_V41.buildSchema(version1_20_5)
	return {
		'Minecraft 1.20.5': schema_v41,
		'Minecraft 1.20.6': schema_v41
	}


COMMANDS_V41: CommandsCreator = copy.deepcopy(v1_20_3_schema.COMMANDS_V26)


@COMMANDS_V41.add(name='transfer', description="Triggers a transfer of a player to another server. Only exists on dedicated servers.")
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


@COMMANDS_V41.modify(name='playsound')
def modify_playsound_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	getArgOptions(args, 'sound', 'source').next.all.insert(0, TERMINAL)
	getArgOptions(args, 'sound').next.all.insert(0, TERMINAL)
	return args


@COMMANDS_V41.modify(name='attribute')
def modify_attribute_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	operationSchema = getArgOptions(args, 'target', 'attribute', 'modifier', 'add', 'uuid', 'name', 'value', 'operation')
	operationSchema.type = makeLiteralsArgumentType([b'add_value', b'add_multiplied_total', b'add_multiplied_base'])
	return args


@COMMANDS_V41.modify(name='execute')
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


@COMMANDS_V41.modify(name='particle')
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
