from typing import Sequence, TYPE_CHECKING, Optional

from Cat.Serializable import replace
from Cat.utils import Maybe, escapeForXml
from model.commands.argumentHandlers import getArgumentHandler
from model.commands.argumentTypes import *
from model.commands.command import formatPossibilities, CommandNode, TERMINAL, Keyword, Switch, ArgumentInfo, COMMANDS_ROOT, CommandInfo
from model.commands.utils import CommandSemanticsError
from model.commands.parsedCommands import ParsedMCFunction, ParsedArgument, ParsedCommandPart, ParsedCommand
from model.parsingUtils import Span

if TYPE_CHECKING:
	from session.session import Session

	def getSession() -> Session:
		pass
else:
	def getSession():
		pass


def checkMCFunction(mcFunction: ParsedMCFunction) -> list[CommandSemanticsError]:
	errors: list[CommandSemanticsError] = []
	for command in mcFunction.commands:
		if command is None:
			continue
		validateCommand(command, errorsIO=errors)
	return errors


def validateCommand(command: ParsedCommand, *, errorsIO: list[CommandSemanticsError]) -> None:
	info = command.info
	if info.removed:
		errorsIO.append(CommandSemanticsError(f"Outdated Command `{command.value}`. (removed in version {info.removedVersion}; {info.removedComment}.", command.span))
	elif info.deprecated:
		errorsIO.append(CommandSemanticsError(f"Deprecated Command `{command.value}`. (deprecated in version {info.deprecatedVersion}; {info.deprecatedComment}.", command.span, style='warning'))

	lastCommandPart: ParsedCommandPart = command
	commandPart: Optional[ParsedCommandPart] = command.argument
	possibilities: Sequence[CommandNode] = command.info.next
	while commandPart is not None:
		lastCommandPart = commandPart
		commandPart, possibilities = validateArgument(commandPart, errorsIO=errorsIO)

	if possibilities and TERMINAL not in possibilities:
		errorsIO.append(_missingArgumentError(command, lastCommandPart, possibilities))


def _unknownOrTooManyArgumentsError(commandPart: ParsedCommandPart, possibilities: Sequence[CommandNode]) -> CommandSemanticsError:
	if possibilities:
		possibilitiesStr = escapeForXml(formatPossibilities(possibilities))
		valueStr = escapeForXml(commandPart.value)
		return CommandSemanticsError(f"unknown argument: expected `{possibilitiesStr}`, but got: `{valueStr}`", commandPart.span)
	else:
		valueStr = escapeForXml(commandPart.value)
		return CommandSemanticsError(f"too many arguments: `{valueStr}`", commandPart.span)


def _missingArgumentError(command: ParsedCommand, lastCommandPart: ParsedCommandPart, possibilities: Sequence[CommandNode]) -> CommandSemanticsError:
	# lastArgEnd = Maybe(command.argument).recursive(ParsedArgument.next.get).orElse(command).span.end
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


def validateArgument(commandPart: ParsedCommandPart, *, errorsIO: list[CommandSemanticsError]) -> tuple[Optional[ParsedCommandPart], Sequence[CommandNode]]:
	info = commandPart.info

	if info is None:
		remainingPossibilities = Maybe(commandPart.prev).getattr('info').getattr('next').get()
		errorsIO.append(_unknownOrTooManyArgumentsError(commandPart, remainingPossibilities))
		return commandPart.next, []

	if isinstance(info, Keyword):
		return commandPart.next, commandPart.info.next

	if isinstance(info, Switch):
		# TODO: validateArgument for Switch?
		return commandPart.next, commandPart.info.next

	if isinstance(info, ArgumentInfo):
		type_: ArgumentType = info.type
		if isinstance(type_, LiteralsArgumentType):
			pass
		else:
			handler = getArgumentHandler(type_)
			if handler is not None:
				error = handler.validate(commandPart)
				if error is not None:
					errorsIO.append(error)
		return commandPart.next, commandPart.info.next

	if isinstance(info, CommandInfo):
		# TODO: validateArgument for command. (i.e. deprecated, wrongVersion, etc...)
		if isinstance(commandPart, ParsedCommand):
			validateCommand(commandPart, errorsIO=errorsIO)
			return None, []
		else:
			errorsIO.append(CommandSemanticsError(f"Internal Error: commandPart should be a `ParsedCommand`, but it was `{type(commandPart).__name__}`", commandPart.span))
			return commandPart.next, commandPart.info.next
