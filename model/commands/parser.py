from typing import Optional, Sequence, Union

from Cat.utils import escapeForXml
from Cat.utils.collections_ import Stack
from Cat.utils.profiling import ProfiledFunction
from model.commands.command import CommandInfo, Keyword, ArgumentInfo, CommandNode, TERMINAL, COMMANDS_ROOT, Switch
from model.commands.utils import CommandSyntaxError, EXPECTED_ARGUMENT_SEPARATOR_MSG
from model.commands.parsedCommands import ParsedMCFunction, ParsedComment, ParsedCommand, ParsedArgument
from model.commands.stringReader import StringReader
from model.parsingUtils import Span

from . import argumentParsersImpl
from .argumentHandlers import getArgumentHandler, makeCommandSyntaxError, makeParsedArgument, missingArgumentParser


argumentParsersImpl._init()  # do not remove!


@ProfiledFunction(enabled=False, colourNodesBySelftime=False)
def parseMCFunction(commands: dict[str, CommandInfo], source: str) -> tuple[Optional[ParsedMCFunction], list[CommandSyntaxError]]:
	parser = Parser(commands, source)
	mcFunction = parser.parseMCFunction()
	return mcFunction, parser.errors


class Parser:
	def __init__(self, commands: dict[str, CommandInfo], source: str):
		self._commands: dict[str, CommandInfo] = commands
		self._lines: list[str] = source.splitlines()
		self._source: str = '\n'.join(self._lines)
		self.errors: list[CommandSyntaxError] = []

	def parseMCFunction(self) -> Optional[ParsedMCFunction]:
		result: ParsedMCFunction = ParsedMCFunction()
		lineStart: int = 0

		for lineNo, line in enumerate(self._lines):
			sr = StringReader(line, lineStart, lineNo, self._source)
			if (node := self.parseLine(sr)) is not None:
				result.children.append(node)
			lineStart += len(line) + 1

		return result

	def parseLine(self, sr: StringReader) -> Union[None, ParsedCommand, ParsedComment]:
		sr.tryConsumeWhitespace()
		if sr.tryPeek() == '#':
			return self.parseComment(sr)
		elif not sr.hasReachedEnd:
			return self.parseCommand(sr)
		else:
			return None

	def parseComment(self, sr: StringReader) -> ParsedComment:
		sr.tryReadRemaining()
		return ParsedComment(
			source=sr.fullSource,
			span=sr.currentSpan
		)

	def parseCommand(self, sr: StringReader) -> Optional[ParsedCommand]:
		commandName: Optional[str] = sr.tryReadLiteral()
		if commandName is None:
			return None
		commandSpan = sr.currentSpan

		commandInfo: Optional[CommandInfo] = self._commands.get(commandName)
		if commandInfo is None:
			if sr.tryReadRemaining():  # move cursor to end
				sr.mergeLastSave()
			self.errors.append(CommandSyntaxError(f"Unknown Command '`{escapeForXml(commandName)}`'", sr.currentSpan))
			return None

		argument: Optional[ParsedArgument] = None
		if sr.tryConsumeWhitespace():
			argument = self.parseArguments(sr, commandInfo)
		else:
			if not sr.hasReachedEnd:
				trailingData: str = escapeForXml(sr.readUntilEndOrWhitespace())
				errorMsg: str = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
				self.errors.append(makeCommandSyntaxError(sr, errorMsg))

		sr.tryReadRemaining()
		commandSpan = Span(commandSpan.start, sr.currentPos)

		command = ParsedCommand(value=commandName, info=commandInfo, span=commandSpan, source=sr.fullSource)
		command.next = argument

		return command

	def parseKeyword(self, sr: StringReader, ai: Keyword) -> Optional[ParsedArgument]:
		literal: Optional[str] = sr.tryReadLiteral()
		if literal is None:
			return None
		if ai.name == literal:
			argument = makeParsedArgument(sr, ai, value=literal)
			return argument
		else:
			sr.rollback()
			return None

	def parseKeywords(self, sr: StringReader, possibilities: Sequence[CommandNode]) -> Optional[ParsedArgument]:
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

	def parseArguments(self, sr: StringReader, commandInfo: CommandInfo) -> Optional[ParsedArgument]:
		possibilities: Sequence[CommandNode] = commandInfo.next
		firstArg: Optional[ParsedArgument] = None
		lastArg: Optional[ParsedArgument] = None

		infoStack: Stack[CommandNode] = Stack[CommandNode]()
		# try to parse Keywords & Arguments:
		while not sr.hasReachedEnd:
			argument: Optional[ParsedArgument] = self.parseKeywords(sr, possibilities)

			if argument is None:
				for possibility in possibilities:
					if False and isinstance(possibility, Keyword):
						continue
					elif isinstance(possibility, ArgumentInfo):
						possibility: ArgumentInfo  # make the type inference of pycharm happy :(
						handler = getArgumentHandler(possibility.type)
						if handler is None:
							argument = missingArgumentParser(sr, possibility, errorsIO=self.errors)
							# return firstArg, errors
						else:
							argument = handler.parse(sr, possibility, errorsIO=self.errors)
						if argument is not None:
							break
						pass  # TODO isinstance(possibility, ArgumentInfo):
					elif isinstance(possibility, Switch):
						argument = self.parseKeywords(sr, possibility.options)
						if argument is not None:
							infoStack.push(possibility)

					elif possibility is COMMANDS_ROOT:
						cursor = sr.cursor
						argument = self.parseCommand(sr)
						if argument is not None:
							break
						sr.cursor = cursor
					elif possibility is TERMINAL:
						if sr.hasReachedEnd:
							return firstArg

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
					self.errors.append(makeCommandSyntaxError(sr, errorMsg))
					sr.rollback()
					break

		remaining: Optional[str] = sr.tryReadRemaining()
		if remaining is not None:
			argument = makeParsedArgument(sr, None, value=remaining)
			if lastArg is None:
				firstArg = argument
			else:
				lastArg.next = argument

		return firstArg



