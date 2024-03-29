"""
currently at minecraft version 1.20.3 (1.20.3-rc1)
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
	schema_v23 = COMMANDS_V23.buildSchema(version1_20_3)
	schema_v25 = COMMANDS_V25.buildSchema(version1_20_3)
	schema_v26 = COMMANDS_V26.buildSchema(version1_20_3)
	return {
		'Minecraft 23w44a': schema_v23,
		'Minecraft 23w46a': schema_v25,
		'Minecraft 1.20.3-rc1': schema_v26,
		'Minecraft 1.20.3': schema_v26
	}


def getArgOptions(args: list[CommandPartSchema], name1: str, *names: str) -> CommandPartSchema:
	keywordArg = first(arg for arg in args if arg.name == name1)
	for name in names:
		keywordArg = first(arg for arg in keywordArg.next.all if arg.name == name)
	return keywordArg


COMMANDS_V23: CommandsCreator = copy.deepcopy(v1_20_2_schema.COMMANDS)


@COMMANDS_V23.modify(name='execute')
def modify_execute_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	EXECUTE_INSTRUCTIONS: list[CommandPartSchema] = args
	EXECUTE_INSTRUCTION_OR_TERMINAL_OPTIONS = Options(ChainedList([TERMINAL], EXECUTE_INSTRUCTIONS))
	ifArg = getArgOptions(args, 'if')
	ifArg.next.all.append(KeywordSchema(
		name='function',
		description="Runs a function or function tag and matches the return value(s). If a tag is given, all functions run regardless of the results of prior functions.\n"
					" - The function call evaluates to `true` if at least one function returned a non-zero value using the return command\n"
					" - If no functions exited with return, it evaluates to `false`",
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


@COMMANDS_V23.modify(name='return')
def modify_return_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	args.extend([
		KeywordSchema(
			name='run',
			description="Takes the `result` value from running the specified `command` and returns that as the return value of the function.\n"
						" - If there are no valid results from returned command, function containing `/return run` will fail (i.e. `success=0` and `result=0`)."
						" - If the given command fails, the return will fail (i.e. `success=0` and `result=0`)."
						" - In all other aspects, it works like `return` with a specified return value\n"
						" - In case of fork (for example `return run execute as @e run some_command`) the first execution of the command will return\n"
						"   - If there are no executions (for example in `return run execute if @e[something_impossible] run some_command`) function will fail (i.e. `success=0` and `result=0`).",
			next=Options([COMMANDS_ROOT])
		),
		KeywordSchema(
			name='fail',
			description="Makes whole function fail (i.e. return `success=0` and `result=0`)."
		)
	])
	return args


@COMMANDS_V23.add(
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
			name='rate',
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
				TERMINAL,
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


COMMANDS_V25: CommandsCreator = copy.deepcopy(COMMANDS_V23)


@COMMANDS_V25.modify(name='scoreboard')
def modify_scoreboard_args(_: FullMCData, args: list[CommandPartSchema]) -> list[CommandPartSchema]:
	NUMBER_FORMAT_OPTIONS = Options([
		TERMINAL,
		KeywordSchema(
			name='styled',
			description="The score will be displayed with the selected style (e.g. `{\"bold\":true}`).",
			next=Options([
				ArgumentSchema(
					name='format',
					type=MINECRAFT_STYLE,
				)
			])
		),
		KeywordSchema(
			name='fixed',
			description="The score is replaced by the given text component.",
			next=Options([
				ArgumentSchema(
					name='text component',
					type=MINECRAFT_COMPONENT,
				)
			])
		),
		KeywordSchema(
			name='blank',
			description="The score is not shown."
		)
	])

	objectivesModifyObjectiveArg = getArgOptions(args, 'objectives', 'modify', 'objective')
	objectivesModifyObjectiveArg.next.all.extend([
		KeywordSchema(
			name='displayautoupdate',
			description="Determines whether the objective should automatically update on every score update (disabled by default).",
			next=Options([
				ArgumentSchema(
					name='displayautoupdate',
					type=BRIGADIER_BOOL,
				),
			])
		),
		KeywordSchema(
			name='numberformat',
			description="Changes (or resets, if no format is given) the default number format of the given objective.",
			next=NUMBER_FORMAT_OPTIONS
		)
	])

	playersArg = getArgOptions(args, 'players', )
	playersArg.next.all.extend([
		KeywordSchema(
			name='name',
			description="Changes (or resets, if no name is given) the display name of the targets' scores.",
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
							next=Options([
								TERMINAL,
								ArgumentSchema(
									name='text',
									description="Changes the display name of the targets' scores.",
									type=MINECRAFT_COMPONENT
								)
							])
						)
					])
				)
			])
		),
		KeywordSchema(
			name='numberformat',
			description="Changes (or resets, if no format is given) the default number format of the given objective.",
			next=Options([
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_SCORE_HOLDER,
					next=Options([
						ArgumentSchema(
							name='objective',
							type=MINECRAFT_OBJECTIVE,
							next=NUMBER_FORMAT_OPTIONS
						)
					])
				)
			])
		)
	])

	return args


COMMANDS_V26: CommandsCreator = copy.deepcopy(COMMANDS_V25)
