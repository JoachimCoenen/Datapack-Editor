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
	return {
		'Minecraft 24w04a': schema_v29,
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

