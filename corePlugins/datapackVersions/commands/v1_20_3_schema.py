"""
currently at minecraft version 1.20.3 (23w42a)
"""

import copy

from cat.utils import first
from cat.utils.collections_ import ChainedList
from corePlugins.datapack.datapackContents import RESOURCES
from corePlugins.mcFunction.command import ArgumentSchema, COMMANDS_ROOT, CommandPartSchema, KeywordSchema, MCFunctionSchema, Options, TERMINAL
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData
from . import v1_20_2_schema
from .argumentTypes import MINECRAFT_RESOURCE_LOCATION


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_20_3 = getFullMcData('1.20.3')
	schema_1_20_3 = COMMANDS_V20.buildSchema(version1_20_3)
	return {'Minecraft 1.20.3': schema_1_20_3}


COMMANDS_V20: v1_20_2_schema.CommandsCreator = copy.deepcopy(v1_20_2_schema.COMMANDS)


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
