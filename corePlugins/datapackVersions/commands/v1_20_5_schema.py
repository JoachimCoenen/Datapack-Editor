"""
currently at minecraft version 1.20.3 (1.20.3-rc1)
"""

import copy

from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, CommandPartSchema, MCFunctionSchema, Options, TERMINAL
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData
from . import v1_20_3_schema
from .argumentTypes import *
from .v1_20_2_schema import CommandsCreator


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_20_5 = getFullMcData('1.20.5')
	schema_v29 = COMMANDS_V29.buildSchema(version1_20_5)
	schema_v30 = COMMANDS_V30.buildSchema(version1_20_5)
	schema_v31 = COMMANDS_V31.buildSchema(version1_20_5)
	return {
		'Minecraft 24w04a': schema_v29,
		'Minecraft 24w05b': schema_v30,
		'Minecraft 24w06a': schema_v31,
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
def build_transfer_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	amplifierSchema = (
		args[0]       # give
		.next.all[0]  # targets
		.next.all[0]  # effect
		.next.all[1]  # duration
		.next.all[1]  # amplifier
	)
	# Potion effect amplifiers are now restricted between 0 and 127.
	amplifierSchema.args.update(dict(min=0, max=127))
	return args


COMMANDS_V31: CommandsCreator = copy.deepcopy(COMMANDS_V29)  # reverts changes in v30 (limiting of Potion effect amplifiers to 127)
