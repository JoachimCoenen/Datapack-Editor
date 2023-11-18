from typing import Sequence, Optional

from .argumentTypes import *
from .command import *
from .commandContext import getArgumentContext
from base.model.parsing.bytesUtils import bytesToStr
from base.model.utils import SemanticsError, Span, Message, wrapInMarkdownCode

UNKNOWN_ARGUMENT_MSG = Message("Unknown argument: expected {0}, but got: {1}", 2)
TOO_MANY_ARGUMENTS_MSG = Message("Too many arguments: {0}", 1)
OUTDATED_COMMAND_MSG = Message("Outdated Command `{0}`. (removed in version {1}; {2}.", 3)
DEPRECATED_COMMAND_MSG = Message("Deprecated Command `{0}`. (deprecated in version {1}; {2}.", 3)
MISSING_ARGUMENTS_MSG = Message("Missing argument: `{0}`", 1)


def checkMCFunction(mcFunction: MCFunction) -> list[SemanticsError]:
	errors: list[SemanticsError] = []
	for command in mcFunction.commands:
		if command is None:
			continue
		validateCommand(command.next, command.schema, errorsIO=errors)
	return errors


def validateCommand(command: CommandPart, schema: CommandSchema, *, errorsIO: list[SemanticsError]) -> None:
	assert isinstance(command, ParsedArgument)
	if schema.removed:
		errorsIO.append(SemanticsError(OUTDATED_COMMAND_MSG.format(bytesToStr(command.value), schema.removedVersion, schema.removedComment), command.span))
	elif schema.deprecated:
		errorsIO.append(SemanticsError(DEPRECATED_COMMAND_MSG.format(bytesToStr(command.value), schema.deprecatedVersion, schema.deprecatedComment), command.span, style='warning'))

	lastCommandPart: CommandPart = command
	commandPart: Optional[CommandPart] = command.next
	possibilities: Sequence[CommandPartSchema] = command.schema.next.flattened
	while commandPart is not None:
		lastCommandPart = commandPart
		commandPart, possibilities = validateArgument(commandPart, errorsIO=errorsIO)

	if possibilities and TERMINAL not in possibilities:
		errorsIO.append(_missingArgumentError(lastCommandPart))


def _unknownOrTooManyArgumentsError(commandPart: CommandPart, possibilities: Sequence[CommandPartSchema]) -> SemanticsError:
	valueStr = wrapInMarkdownCode(bytesToStr(commandPart.content))
	if possibilities:
		possibilitiesStr = wrapInMarkdownCode(formatPossibilities(possibilities))
		return SemanticsError(UNKNOWN_ARGUMENT_MSG.format(possibilitiesStr, valueStr), commandPart.span)
	else:
		return SemanticsError(TOO_MANY_ARGUMENTS_MSG.format(valueStr), commandPart.span)


def _missingArgumentError(lastCommandPart: CommandPart) -> SemanticsError:
	errorEnd = lastCommandPart.end
	errorStart = errorEnd - 1

	possibilitiesStr = formatPossibilities(lastCommandPart.potentialNextSchemas)
	return SemanticsError(MISSING_ARGUMENTS_MSG.format(possibilitiesStr), Span(errorStart, errorEnd))


def validateArgument(commandPart: CommandPart, *, errorsIO: list[SemanticsError]) -> tuple[Optional[CommandPart], Sequence[CommandPartSchema]]:
	schema = commandPart.schema
	if schema is None:
		before = commandPart.prev
		remainingPossibilities = before.potentialNextSchemas if before is not None else []
		errorsIO.append(_unknownOrTooManyArgumentsError(commandPart, remainingPossibilities))
		return commandPart.next, commandPart.potentialNextSchemas

	if isinstance(schema, ArgumentSchema):
		type_: ArgumentType = schema.type
		if isinstance(type_, LiteralsArgumentType):
			pass
		else:
			handler = getArgumentContext(type_)
			if handler is not None:
				handler.validate(commandPart, errorsIO)

	return commandPart.next, commandPart.potentialNextSchemas
