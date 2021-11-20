from typing import Optional, Sequence

from Cat.utils import escapeForXml
from Cat.utils.collections_ import Stack
from Cat.utils.profiling import ProfiledFunction
from model.commands.command import CommandInfo, Keyword, ArgumentInfo, CommandNode, TERMINAL, COMMANDS_ROOT, Switch
from model.commands.commands import getCommandInfo
from model.commands.utils import CommandSyntaxError, EXPECTED_ARGUMENT_SEPARATOR_MSG
from model.commands.parsedCommands import ParsedMCFunction, ParsedComment, ParsedCommand, ParsedArgument
from model.commands.stringReader import StringReader
from model.parsingUtils import Position, Span

from . import argumentParsersImpl
from .argumentHandlers import getArgumentHandler, makeCommandSyntaxError, makeParsedArgument, missingArgumentParser

argumentParsersImpl._init()  # do not remove!


@ProfiledFunction(enabled=False, colourNodesBySelftime=False)
def parseMCFunction(source: str) -> tuple[Optional[ParsedMCFunction], list[CommandSyntaxError]]:
	lines = source.splitlines()
	result: ParsedMCFunction = ParsedMCFunction()
	errors: list[CommandSyntaxError] = []
	lineStart: int = 0

	for lineNo, line in enumerate(lines):
		if line.startswith('#'):
			comment = ParsedComment.create(
				source=source,
				span=Span(
					Position(lineNo, 0, lineStart),
					Position(lineNo, len(line), lineStart + len(line))
				)
			)
			result.children.append(comment)
		elif line.strip():
			sr = StringReader(line, lineStart, lineNo, source)
			sr.tryConsumeWhitespace()
			command, cmdErrors = parseCommand(sr, lineStart, lineNo, source)
			errors += cmdErrors
			if command is not None:
				result.children.append(command)
		lineStart += len(line) + 1

	return result, errors


def parseCommand(sr: StringReader, lineStart: int, lineNo: int, source: str) -> tuple[Optional[ParsedCommand], list[CommandSyntaxError]]:
	start: int = sr.cursor
	commandName: Optional[str] = sr.tryReadLiteral()
	if commandName is None:
		return None, []
	commandSpan = sr.currentSpan

	# position = sr.posFromColumn(start)
	# end = sr.currentPos

	commandInfo: Optional[CommandInfo] = getCommandInfo(commandName)
	if commandInfo is None:
		if sr.tryReadRemaining():  # move cursor to end
			sr.mergeLastSave()
		return None, [
			CommandSyntaxError(f"Unknown Command '`{escapeForXml(commandName)}`'", sr.currentSpan)
		]

	argument: Optional[ParsedArgument] = None
	if sr.tryConsumeWhitespace():
		argument, errors = parseArguments(sr, lineStart, lineNo, source, commandInfo)
	else:
		errors = []
		if not sr.hasReachedEnd:
			trailingData: str = escapeForXml(sr.readUntilEndOrWhitespace())
			errorMsg: str = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
			errors.append(makeCommandSyntaxError(sr, errorMsg))

	sr.tryReadRemaining()
	commandSpan = Span(commandSpan.start, sr.currentPos)

	command = ParsedCommand.create(name=commandName, info=commandInfo, span=commandSpan, source=source)
	command.argument = argument

	return command, errors


def parseKeyword(sr: StringReader, ai: Keyword, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	literal: Optional[str] = sr.tryReadLiteral()
	if literal is None:
		return None
	if ai.name == literal:
		argument = makeParsedArgument(sr, ai, value=literal)
		return argument
	else:
		sr.rollback()
		return None


def parseKeywords(sr: StringReader, possibilities: Sequence[CommandNode], *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	keywords = {kw.name: kw for kw in possibilities if isinstance(kw, Keyword)}
	if not keywords:
		return None

	literal: Optional[str] = sr.tryReadLiteral()
	if literal is None:
		return None
	if literal not in keywords:
		sr.rollback()
		return None

	argument = makeParsedArgument(sr, keywords[literal], value=literal)
	return argument


def parseArguments(sr: StringReader, lineStart: int, lineNo: int, source: str, commandInfo: CommandInfo) -> tuple[Optional[ParsedArgument], list[CommandSyntaxError]]:
	errors: list[CommandSyntaxError] = []

	possibilities: Sequence[CommandNode] = commandInfo.argument
	firstArg: Optional[ParsedArgument] = None
	lastArg: Optional[ParsedArgument] = None

	infoStack: Stack[CommandNode] = Stack[CommandNode]()
	# try to parse Keywords & Arguments:
	while not sr.hasReachedEnd:
		argument: Optional[ParsedArgument] = parseKeywords(sr, possibilities, errorsIO=errors)

		if argument is None:
			for possibility in possibilities:
				if False and isinstance(possibility, Keyword):
					continue
				elif isinstance(possibility, ArgumentInfo):
					possibility: ArgumentInfo  # make the type inference of pycharm happy :(
					handler = getArgumentHandler(possibility.type)
					if handler is None:
						argument = missingArgumentParser(sr, possibility, errorsIO=errors)
						# return firstArg, errors
					else:
						argument = handler.parse(sr, possibility, errorsIO=errors)
					if argument is not None:
						break
					pass  # TODO isinstance(possibility, ArgumentInfo):
				elif isinstance(possibility, Switch):
					argument = parseKeywords(sr, possibility.options, errorsIO=errors)
					if argument is not None:
						infoStack.push(possibility)

				elif possibility is COMMANDS_ROOT:
					cursor = sr.cursor
					argument, cmdErrors = parseCommand(sr, lineStart, lineNo, source)
					errors += cmdErrors
					del cmdErrors
					if argument is not None:
						break
					sr.cursor = cursor
				elif possibility is TERMINAL:
					if sr.hasReachedEnd:
						return firstArg, errors

		if argument is None:
			if infoStack:
				possibilities = infoStack.pop().next
				continue
			else:
				break
		else:  # we successfully parsed an argument!
			# add argument:
			if lastArg is None:
				firstArg = argument
			else:
				lastArg.next = argument
			lastArg = argument
			# get possibilities for next argument:
			if argument.info is None:
				possibilities = []
			else:
				possibilities = argument.info.next
			# finally consume whitespace:
			if sr.tryConsumeWhitespace() or sr.hasReachedEnd:
				continue
			else:
				trailingData: str = sr.readUntilEndOrWhitespace()
				errorMsg: str = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
				errors.append(makeCommandSyntaxError(sr, errorMsg))
				sr.rollback()
				break

	remainig: Optional[str] = sr.tryReadRemaining()
	if remainig is not None:
		argument = makeParsedArgument(sr, None, value=remainig)
		if lastArg is None:
			firstArg = argument
		else:
			lastArg.next = argument

	return firstArg, errors



