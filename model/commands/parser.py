from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

from Cat.utils import escapeForXml
from Cat.utils.collections_ import Stack
from model.commands.command import CommandSchema, KeywordSchema, ArgumentSchema, CommandPartSchema, TERMINAL, COMMANDS_ROOT, SwitchSchema, MCFunctionSchema
from model.commands.utils import CommandSyntaxError, EXPECTED_ARGUMENT_SEPARATOR_MSG
from model.commands.command import MCFunction, ParsedComment, ParsedCommand, ParsedArgument
from model.commands.stringReader import StringReader
from model.utils import Span, Position, Message, LanguageId

from . import argumentParsersImpl
from .commandContext import makeCommandSyntaxError, makeParsedArgument, getArgumentContext, missingArgumentContext
from ..parsing.bytesUtils import bytesToStr, strToBytes
from ..parsing.parser import ParserBase, registerParser

argumentParsersImpl._init()  # do not remove!


UNKNOWN_COMMAND_MSG = Message("Unknown Command '`{0}`'", 1)


# @ProfiledFunction(enabled=False, colourNodesBySelftime=False)
# def parseMCFunction(commands: dict[str, CommandSchema], source: str) -> tuple[Optional[MCFunction], list[CommandSyntaxError]]:
# 	parser = MCFunctionParser(commands, source)
# 	mcFunction = parser.parseMCFunction()
# 	return mcFunction, parser.errors


@registerParser(LanguageId('MCCommand'))
@registerParser(LanguageId('MCFunction'))
@dataclass
class MCFunctionParser(ParserBase[MCFunction, MCFunctionSchema]):
	# def __init__(self, commands: dict[str, CommandSchema], source: str):
	# 	self._commands: dict[str, CommandSchema] = commands
	# 	self._lines: list[str] = source.splitlines()
	# 	self._source: str = '\n'.join(self._lines)
	# 	self.errors: list[CommandSyntaxError] = []

	_lines: list[bytes] = field(init=False)

	def __post_init__(self):
		self._lines = self.text.splitlines()

	def parseMCFunction(self) -> Optional[MCFunction]:
		children = []

		lineStart: int = self.lineStart
		cursorOffset = self.cursorOffset - self.lineStart
		for lineNo, line in enumerate(self._lines, self.line):
			sr = StringReader(line, lineStart, lineNo, cursorOffset, self.text)
			if (node := self.parseLine(sr)) is not None:
				children.append(node)
			lineStart += len(line)
			if self.text[lineStart:lineStart+2] == b'\r\n':
				lineStart += 2
			else:
				lineStart += 1
			cursorOffset = 0

		actualCursor = self.cursor + self.cursorOffset
		self.line += max(0, len(self._lines) - 1)
		result: MCFunction = MCFunction(
			Span(
				Position(self.line, actualCursor - self.lineStart, actualCursor),
				Position(
					len(self._lines)-1 + self.line,
					len(self._lines[-1])-1 if self._lines else self.cursorOffset,
					len(self.text) + self.cursorOffset
				)
				if len(self._lines) != 1 else
				Position(
					len(self._lines)-1 + self.line,
					len(self._lines[-1]) + (self.cursorOffset - self.lineStart),
					len(self.text) + self.cursorOffset
				)
			),
			self.schema,
			self.text,
			self.text,
			children
		)

		return result

	def parseLine(self, sr: StringReader) -> Union[None, ParsedCommand, ParsedComment]:
		sr.tryConsumeWhitespace()
		if sr.tryPeek() == ord('#'):
			return self.parseComment(sr)
		elif not sr.hasReachedEnd:
			return self.parseCommand(sr)
		else:
			return None

	def parseComment(self, sr: StringReader) -> ParsedComment:
		content = sr.tryReadRemaining() or b''
		return ParsedComment(
			span=sr.currentSpan,
			schema=None,
			source=self.text,
			content=content
		)

	def parseCommand(self, sr: StringReader) -> Optional[ParsedCommand]:
		startCursor = sr.cursor
		sr.tryConsumeByte(ord(b'/'))
		commandName: Optional[bytes] = sr.tryReadLiteral()
		if commandName is None:
			return None
		commandSpan = sr.currentSpan
		if self.schema is not None:
			commandSchema = self.schema.commands.get(commandName)
		else:
			commandSchema = None
		if commandSchema is None:
			if sr.tryReadRemaining():  # move cursor to end
				sr.mergeLastSave()
			self.errors.append(CommandSyntaxError(UNKNOWN_COMMAND_MSG.format(escapeForXml(bytesToStr(commandName))), sr.currentSpan))
			return None

		argument: Optional[ParsedArgument] = None
		if sr.tryConsumeWhitespace():
			argument = self.parseArguments(sr, commandSchema)
		else:
			if not sr.hasReachedEnd:
				trailingData: str = escapeForXml(bytesToStr(sr.readUntilEndOrWhitespace()))
				errorMsg = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
				self.errors.append(makeCommandSyntaxError(sr, errorMsg))

		sr.tryReadRemaining()
		commandSpan = Span(commandSpan.start, sr.currentPos)
		endCursor = sr.cursor
		content = sr.source[startCursor:endCursor]

		command = ParsedCommand(name=commandName, schema=commandSchema, span=commandSpan, source=self.text, content=content)
		command.next = argument

		return command

	@staticmethod
	def parseKeyword(sr: StringReader, ai: KeywordSchema) -> Optional[ParsedArgument]:
		literal: Optional[bytes] = sr.tryReadLiteral()
		if literal is None:
			return None
		if ai.name == literal:
			argument = makeParsedArgument(sr, ai, value=literal)
			return argument
		else:
			sr.rollback()
			return None

	@staticmethod
	def parseKeywords(sr: StringReader, possibilities: Sequence[CommandPartSchema]) -> Optional[ParsedArgument]:
		keywords = {strToBytes(kw.name): kw for kw in possibilities if isinstance(kw, KeywordSchema)}
		if not keywords:
			return None

		literal: Optional[bytes] = sr.tryReadLiteral()
		if literal is None:
			return None
		if literal not in keywords:
			sr.rollback()
			return None

		argument = makeParsedArgument(sr, keywords[literal], value=literal)
		return argument

	def parseArguments(self, sr: StringReader, commandInfo: CommandSchema) -> Optional[ParsedArgument]:
		possibilities: Sequence[CommandPartSchema] = commandInfo.next
		firstArg: Optional[ParsedArgument] = None
		lastArg: Optional[ParsedArgument] = None

		infoStack: Stack[CommandPartSchema] = Stack()
		# try to parse Keywords & Arguments:
		while not sr.hasReachedEnd:
			argument: Optional[ParsedArgument] = self.parseKeywords(sr, possibilities)

			if argument is None:
				for possibility in possibilities:
					if False and isinstance(possibility, KeywordSchema):
						continue
					elif isinstance(possibility, ArgumentSchema):
						possibility: ArgumentSchema  # make the type inference of pycharm happy :(
						ctx = getArgumentContext(possibility.type)
						if ctx is None:
							argument = missingArgumentContext(sr, possibility, errorsIO=self.errors)
							# return firstArg, errors
						else:
							argument = ctx.parse(sr, possibility, self.filePath, errorsIO=self.errors)
						if argument is not None:
							break
						pass  # TODO isinstance(possibility, ArgumentSchema):
					elif isinstance(possibility, SwitchSchema):
						argument = self.parseKeywords(sr, possibility.options)
						if argument is not None:
							argument.switchSchema = possibility
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
				if argument.schema is None:
					possibilities = []
				else:
					possibilities = argument.schema.next
				# finally consume whitespace:
				if sr.tryConsumeWhitespace() or sr.hasReachedEnd:
					continue
				else:
					trailingData = sr.readUntilEndOrWhitespace()
					trailingData = bytesToStr(trailingData)
					errorMsg = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
					self.errors.append(makeCommandSyntaxError(sr, errorMsg))
					sr.rollback()
					break

		remaining: Optional[bytes] = sr.tryReadRemaining()
		if remaining is not None:
			argument = makeParsedArgument(sr, None, value=remaining)
			if lastArg is None:
				firstArg = argument
			else:
				lastArg.next = argument

		return firstArg

	def parse(self) -> Optional[MCFunction]:
		return self.parseMCFunction()


def init():
	pass
