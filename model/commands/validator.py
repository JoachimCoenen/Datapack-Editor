from dataclasses import replace
from typing import Sequence, TYPE_CHECKING, Optional

from model.commands.argumentTypes import *
from model.commands.command import formatPossibilities, CommandPartSchema, TERMINAL, KeywordSchema, SwitchSchema, ArgumentSchema, CommandSchema, getNextSchemas
from model.commands.commandContext import getArgumentContext
from model.commands.utils import CommandSemanticsError
from model.commands.command import MCFunction, CommandPart, ParsedCommand
from model.messages import *
from model.parsing.bytesUtils import bytesToStr
from model.utils import Span, Message, wrapInMarkdownCode

if TYPE_CHECKING:
	from session.session import Session

	def getSession() -> Session:
		pass
else:
	def getSession():
		pass


UNKNOWN_ARGUMENT_MSG = Message("Unknown argument: expected {0}, but got: {1}", 2)
TOO_MANY_ARGUMENTS_MSG = Message("Too many arguments: {0}", 1)
OUTDATED_COMMAND_MSG = Message("Outdated Command `{0}`. (removed in version {1}; {2}.", 3)
DEPRECATED_COMMAND_MSG = Message("Deprecated Command `{0}`. (deprecated in version {1}; {2}.", 3)
MISSING_ARGUMENTS_MSG = Message("Missing argument: `{0}`", 1)


def checkMCFunction(mcFunction: MCFunction) -> list[CommandSemanticsError]:
	errors: list[CommandSemanticsError] = []
	for command in mcFunction.commands:
		if command is None:
			continue
		validateCommand(command, errorsIO=errors)
	return errors


def validateCommand(command: ParsedCommand, *, errorsIO: list[CommandSemanticsError]) -> None:
	schema = command.schema
	if schema.removed:
		errorsIO.append(CommandSemanticsError(OUTDATED_COMMAND_MSG.format(command.name, schema.removedVersion, schema.removedComment), command.span))
	elif schema.deprecated:
		errorsIO.append(CommandSemanticsError(DEPRECATED_COMMAND_MSG.format(command.name, schema.deprecatedVersion, schema.deprecatedComment), command.span, style='warning'))

	lastCommandPart: CommandPart = command
	commandPart: Optional[CommandPart] = command.next
	possibilities: Sequence[CommandPartSchema] = command.schema.next
	while commandPart is not None:
		lastCommandPart = commandPart
		commandPart, possibilities = validateArgument(commandPart, errorsIO=errorsIO)

	if possibilities and TERMINAL not in possibilities:
		errorsIO.append(_missingArgumentError(command, lastCommandPart, possibilities))


def _unknownOrTooManyArgumentsError(commandPart: CommandPart, possibilities: Sequence[CommandPartSchema]) -> CommandSemanticsError:
	valueStr = wrapInMarkdownCode(bytesToStr(commandPart.content))
	if possibilities:
		possibilitiesStr = wrapInMarkdownCode(formatPossibilities(possibilities))
		return CommandSemanticsError(UNKNOWN_ARGUMENT_MSG.format(possibilitiesStr, valueStr), commandPart.span)
	else:
		return CommandSemanticsError(TOO_MANY_ARGUMENTS_MSG.format(valueStr), commandPart.span)


def _missingArgumentError(command: ParsedCommand, lastCommandPart: CommandPart, possibilities: Sequence[CommandPartSchema]) -> CommandSemanticsError:
	errorStart = lastCommandPart.end
	errorEnd = command.span.end
	if errorStart.index >= errorEnd.index:
		errorStart = replace(errorEnd, column=max(0, errorEnd.column - 1), index=max(0, errorEnd.index - 1))

	possibilitiesStr = formatPossibilities(possibilities)
	return CommandSemanticsError(MISSING_ARGUMENTS_MSG.format(possibilitiesStr), Span(errorStart, errorEnd))


def validateArgument(commandPart: CommandPart, *, errorsIO: list[CommandSemanticsError]) -> tuple[Optional[CommandPart], Sequence[CommandPartSchema]]:
	schema = commandPart.schema
	if schema is None:
		before = commandPart.prev
		remainingPossibilities = getNextSchemas(before) if before is not None else []
		errorsIO.append(_unknownOrTooManyArgumentsError(commandPart, remainingPossibilities))
		return commandPart.next, []

	if isinstance(schema, KeywordSchema):
		return commandPart.next, schema.next

	if isinstance(schema, SwitchSchema):
		# TODO: validateArgument for Switch?
		return commandPart.next, schema.next

	if isinstance(schema, ArgumentSchema):
		type_: ArgumentType = schema.type
		if isinstance(type_, LiteralsArgumentType):
			pass
		else:
			handler = getArgumentContext(type_)
			if handler is not None:
				handler.validate(commandPart, errorsIO)
		return commandPart.next, schema.next

	if isinstance(schema, CommandSchema):
		# TODO: validateArgument for command. (i.e. deprecated, wrongVersion, etc...)
		if isinstance(commandPart, ParsedCommand):
			validateCommand(commandPart, errorsIO=errorsIO)
			return None, []
		else:
			errorsIO.append(CommandSemanticsError(INTERNAL_ERROR_MSG.format(EXPECTED_BUT_GOT_MSG, '`ParsedCommand`', type(commandPart).__name__), commandPart.span))
			return commandPart.next, schema.next
