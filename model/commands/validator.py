from dataclasses import replace
from typing import Sequence, TYPE_CHECKING, Optional

from Cat.utils import Maybe, escapeForXml
from model.commands.argumentTypes import *
from model.commands.command import formatPossibilities, CommandPartSchema, TERMINAL, KeywordSchema, SwitchSchema, ArgumentSchema, CommandSchema
from model.commands.commandContext import getArgumentContext
from model.commands.utils import CommandSemanticsError
from model.commands.command import MCFunction, CommandPart, ParsedCommand
from model.messages import *
from model.parsing.bytesUtils import bytesToStr
from model.utils import Span

if TYPE_CHECKING:
	from session.session import Session

	def getSession() -> Session:
		pass
else:
	def getSession():
		pass


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
		errorsIO.append(CommandSemanticsError(f"Outdated Command `{command.name}`. (removed in version {schema.removedVersion}; {schema.removedComment}.", command.span))
	elif schema.deprecated:
		errorsIO.append(CommandSemanticsError(f"Deprecated Command `{command.name}`. (deprecated in version {schema.deprecatedVersion}; {schema.deprecatedComment}.", command.span, style='warning'))

	lastCommandPart: CommandPart = command
	commandPart: Optional[CommandPart] = command.next
	possibilities: Sequence[CommandPartSchema] = command.schema.next
	while commandPart is not None:
		lastCommandPart = commandPart
		commandPart, possibilities = validateArgument(commandPart, errorsIO=errorsIO)

	if possibilities and TERMINAL not in possibilities:
		errorsIO.append(_missingArgumentError(command, lastCommandPart, possibilities))


def _unknownOrTooManyArgumentsError(commandPart: CommandPart, possibilities: Sequence[CommandPartSchema]) -> CommandSemanticsError:
	if possibilities:
		possibilitiesStr = escapeForXml(formatPossibilities(possibilities))
		valueStr = escapeForXml(bytesToStr(commandPart.content))
		return CommandSemanticsError(f"unknown argument: expected `{possibilitiesStr}`, but got: `{valueStr}`", commandPart.span)
	else:
		valueStr = escapeForXml(bytesToStr(commandPart.content))
		return CommandSemanticsError(f"too many arguments: `{valueStr}`", commandPart.span)


def _missingArgumentError(command: ParsedCommand, lastCommandPart: CommandPart, possibilities: Sequence[CommandPartSchema]) -> CommandSemanticsError:
	# lastArgEnd = Maybe(command.next).recursive(ParsedArgument.next.get).orElse(command).span.end
	# if lastArgEnd.index >= command.span.end.index:
	# 	lastArgEnd = lastArgEnd.copy()
	# 	lastArgEnd.column -= 1
	# 	lastArgEnd.index -= 1
	# 	if lastArgEnd.column < 0:
	# 		lastArgEnd = command.span.start
	# errorStart = lastArgEnd
	# errorEnd = command.span.end

	errorStart = lastCommandPart.end
	errorEnd = command.span.end
	if errorStart.index >= errorEnd.index:
		errorStart = replace(errorEnd, column=max(0, errorEnd.column - 1), index=max(0, errorEnd.index - 1))

	possibilitiesStr = escapeForXml(formatPossibilities(possibilities))
	return CommandSemanticsError(f"Missing argument: `{possibilitiesStr}`", Span(errorStart, errorEnd))


def validateArgument(commandPart: CommandPart, *, errorsIO: list[CommandSemanticsError]) -> tuple[Optional[CommandPart], Sequence[CommandPartSchema]]:
	schema = commandPart.schema

	if schema is None:
		remainingPossibilities = Maybe(commandPart.prev).getattr('schema').getattr('next').get()
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
