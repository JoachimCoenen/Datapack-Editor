"""
currently at minecraft version 1.20.3 (23w43a)
"""

import copy

from cat.utils import first
from cat.utils.collections_ import ChainedList
from corePlugins.datapack.datapackContents import RESOURCES
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, COMMANDS_ROOT, CommandPartSchema, KeywordSchema, MCFunctionSchema, Options, TERMINAL
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData
from . import v1_20_2_schema
from .argumentTypes import *
from .v1_20_2_schema import CommandsCreator


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_20_3 = getFullMcData('1.20.3')
	schema_1_20_3 = COMMANDS_V22.buildSchema(version1_20_3)
	return {'Minecraft 1.20.3': schema_1_20_3}


COMMANDS_V20: CommandsCreator = copy.deepcopy(v1_20_2_schema.COMMANDS)


@COMMANDS_V20.modify(name='execute')
def modify_execute_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	EXECUTE_INSTRUCTIONS: list[CommandPartSchema] = args
	EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS = Options(ChainedList([TERMINAL], EXECUTE_INSTRUCTIONS))
	ifArg = first(arg for arg in args if isinstance(arg, KeywordSchema) and arg.name == 'if')
	ifArg.next.all.append(KeywordSchema(
		name='function',
		description="Runs a function or function tag and matches the return value(s). If a tag is given, all functions run regardless of the results of prior functions.\n"
					" - The function call evaluates to `true` if at least one function returned a non-zero value using the return command\n"
					" - If no functions exited with return, neither if or unless will run",
					# from mojang https://www.minecraft.net/en-us/article/minecraft-snapshot-23w41a:
					# "<b>The matching of the result value of the function(s) that run:</b>\n"
					# "	At least one of the function call(s) must succeed for the match to succeed\n"
					# "	A successful call is defined as a function that:\n"
					# "		Uses the return command to return a value\n"
					# "		The return value is not 0\n"
					# "	If no functions exited with return, neither if or unless will run\n"
		next=Options([
			ArgumentSchema(
				name='function',
				type=MINECRAFT_RESOURCE_LOCATION,
				args=dict(schema=RESOURCES.FUNCTIONS, allowTags=True),
				next=EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS

			)
		])
	))
	return args


@COMMANDS_V20.modify(name='return')
def modify_return_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	args.append(KeywordSchema(
		name='run',
		description="Takes the `result` value from running the specified `command` and returns that as the return value of the function.\n"
					" - If command did not return any value (like, for example, call to a `function` without `return`), return will not execute and function will continue execution\n"
					" - If the given command fails, the return value is `0`\n"
					" - In all other aspects, it works like `return` with a specified return value\n"
					" - In case of fork (for example `return run execute as @e run some_command`) the first execution of the command will return\n"
					"   - If there are no executions (for example in `return run execute if @e[something_impossible] run some_command`) function will not return and will continue execution",
		next=Options([COMMANDS_ROOT])
	))
	return args


COMMANDS_V22: CommandsCreator = copy.deepcopy(COMMANDS_V20)


@COMMANDS_V20.add(
	name='tick',
	description="Control the ticking flow and measure the performance of the game. \nRequires elevated permissions (admins and above), and so it is not by default available in command blocks and data packs.",
	opLevel=3
)
def build_tick_args(_: FullMCData) -> list[CommandPartSchema]:
	return [
		KeywordSchema(
			name='query',
			description="Outputs the current target ticking rate, with information about the tick times performance."
		),
		KeywordSchema(
			name='rate ',
			description="Sets a custom target ticking rate to the specified value. The value `rate` must be greater than `1.0` and lower than `10000.0`.",
			next=Options([
				ArgumentSchema(
					name='rate',
					type=BRIGADIER_FLOAT,
					args=dict(min=1.0, max=10000.0)
				)
			])
		),
		KeywordSchema(
			name='freeze',
			description="Freezes all gameplay elements, except for players and any entity a player is riding."
		),
		KeywordSchema(
			name='step',
			description="",
			next=Options([
				ArgumentSchema(
					name='time',
					description="Runs the game for the specified number of ticks and then freezes the game again.This allows to step through the game a set amount of ticks at a time. Only works when the game is frozen.",
					type=MINECRAFT_TIME,
					args=dict(min=1, suggestions=[20])
				),
				KeywordSchema(
					name='stop',
					description="Stops the current stepping process, and re-freezes the game."
				),
			])
		),
		KeywordSchema(
			name='unfreeze',
			description="Unfreezes the game and resumes all gameplay elements."
		),
		KeywordSchema(
			name='sprint',
			description="",
			next=Options([
				ArgumentSchema(
					name='time',
					description="Runs the game while ignoring the set ticking target rate for the specified number of ticks. At the end of the sprint, the game will resume the previous ticking target and display performance information about the tick times while sprinting.",
					type=MINECRAFT_TIME,
					args=dict(min=1, suggestions=[20])
				),
				KeywordSchema(
					name='stop',
					description="Stops the current `/tick sprint`, and resumes the previous ticking target."
				),
			])
		)
	]

