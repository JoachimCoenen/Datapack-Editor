from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

from .command import *
from .stringReader import StringReader
from base.model.utils import ParsingError, Span, Message, wrapInMarkdownCode

from .commandContext import makeParsedArgument, getArgumentContext, missingArgumentContext
from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.parser import ParserBase


UNKNOWN_COMMAND_MSG = Message("Unknown Command '{0}'", 1)
EXPECTED_ARGUMENT_SEPARATOR_MSG: Message = Message("Expected whitespace to end one argument, but found trailing data: {0}", 1)


@dataclass
class MCFunctionParser(ParserBase[MCFunction, MCFunctionSchema]):

	_lines: list[bytes] = field(init=False)

	def __post_init__(self):
		super().__post_init__()
		self._lines = self.text.splitlines()

	def parseMCFunction(self) -> Optional[MCFunction]:
		children = []

		p1 = self.currentPos
		cursorOffset = self.cursorOffset
		cursor = self.cursor
		for lineNo, line in enumerate(self._lines, self.line):
			sr = StringReader(line, self.line, self.lineStart, cursor, cursorOffset, self.indexMapper, -1, self.text)
			if (node := self.parseLine(sr)) is not None:
				children.append(node)
			self.cursor += len(line)
			if self.text[self.cursor:self.cursor+2] == b'\r\n':
				self.cursor += 2
			else:
				self.cursor += 1
			self.advanceLine()

			cursorOffset = self.cursorOffset + self.cursor
			cursor = 0

		p2 = self.currentPos
		result: MCFunction = MCFunction(
			Span(p1, p2),
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
		startPos = sr.currentPos
		sr.tryConsumeByte(ord(b'/'))
		# commandArg is the first argument of a ParsedCommand
		didMatch, commandArg, hasErrors, lastArg = self._parseSimpleCommand(sr)
		if commandArg is None:
			return None

		commandSpan = Span(startPos, sr.currentPos)
		endCursor = sr.cursor
		content = sr.text[startCursor:endCursor]

		command = ParsedCommand(name=commandArg.content, schema=commandArg.schema, span=commandSpan, source=self.text, content=content)
		command.next = commandArg
		return command

	def _parseSimpleCommand(self, sr: StringReader) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument]]:
		"""
		:return:(didMatch, firstArg, hasError, lastArg)
		"""
		commandName: Optional[bytes] = sr.tryReadLiteral()
		if commandName is None:
			return False, None, False, None

		commandSchema = self.schema.commands.get(commandName) if self.schema is not None else None

		if commandSchema is None:
			if sr.tryReadRemaining():  # move cursor to end
				sr.mergeLastSave()
			self.errors.append(ParsingError(UNKNOWN_COMMAND_MSG.format(wrapInMarkdownCode(bytesToStr(commandName))), sr.currentSpan))
			return True, None, True, None

		# commandArg is the first argument of a ParsedCommand
		commandArg = makeParsedArgument(sr, commandSchema, commandName)
		commandArg.potentialNextSchemas = self._getAllPossibilities(commandSchema.next)

		if sr.tryConsumeWhitespace():
			didMatch, firstArg, hasErrors, lastArg = self.parseArguments(sr, commandSchema.next)
			if firstArg is not None:
				commandArg.next = firstArg
			lastArg = lastArg or commandArg
			remaining: Optional[bytes] = sr.tryReadRemaining()
			if remaining is not None:
				lastArg.next = makeParsedArgument(sr, None, value=remaining)
				lastArg = lastArg.next
		else:
			lastArg = commandArg
			hasErrors = False  # ? is this right?
			if not sr.hasReachedEnd:
				self._addExpectedArgumentError(sr)
				hasErrors = True

		sr.tryReadRemaining()

		return True, commandArg, hasErrors, lastArg

	def _addExpectedArgumentError(self, sr: StringReader) -> None:
		trailingData: str = wrapInMarkdownCode(bytesToStr(sr.readUntilEndOrWhitespace()))
		errorMsg = EXPECTED_ARGUMENT_SEPARATOR_MSG.format(trailingData)
		self.errors.append(ParsingError(errorMsg, sr.currentSpan))

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

	def parseArguments(self, sr: StringReader, possibilities: Sequence[CommandPartSchema]) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument]]:
		"""
		:return:(didMatch, firstArg, hasError, lastArg)
		"""
		hasError = False
		didMatch = False
		lastArg = None
		firstArg = None

		# try to parse Keywords & Arguments:
		while True: #not sr.hasReachedEnd:
			didMatch, argument, hasError, argument2, hasConsumedWhitespace, possibilities = self.parseArgument(sr, possibilities)

			if argument is not None:
				if firstArg is None:
					firstArg = argument
				if lastArg is not None:
					lastArg.next = argument
				lastArg = argument2

			# if it's the first argument which did not match, there might be other possibilities, we do not know about here.
			hasError |= firstArg is not None and not didMatch

			if hasError or not didMatch:
				break

			if argument is not None:  # we successfully parsed an argument!
				if possibilities:
					argument2.potentialNextSchemas += self._getAllPossibilities(possibilities)
				# finally consume whitespace:
				if not hasConsumedWhitespace and not sr.tryConsumeWhitespace() and not sr.hasReachedEnd:
					self._addExpectedArgumentError(sr)
					sr.rollback()
					break

			if not possibilities:
				break

		return didMatch, firstArg, hasError, lastArg

	def parseArgument(self, sr: StringReader, possibilities: Sequence[CommandPartSchema]) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument], bool, Sequence[CommandPartSchema]]:
		hasError = False
		hasConsumedWhitespace = False
		argument: Optional[ParsedArgument] = self.parseKeywords(sr, possibilities)
		argument2: Optional[ParsedArgument] = argument
		if argument is not None:
			nextPossibilities = argument.schema.next
			didMatch = True
		else:
			nextPossibilities = ()
			didMatch = not possibilities  # a TERMINAL always matches
			for possibility in possibilities:

				if False and isinstance(possibility, KeywordSchema):
					continue

				elif isinstance(possibility, (ArgumentSchema, CommandsRoot, SwitchSchema)):
					# cursor = sr.cursor
					if possibility is COMMANDS_ROOT:
						argumentDidMatch, argument, hasError, argument2 = self._parseSimpleCommand(sr)
					elif isinstance(possibility, SwitchSchema):
						argumentDidMatch, argument, hasError, argument2 = self.parseArguments(sr, possibility.options)
						hasConsumedWhitespace = argumentDidMatch
					else:
						argumentDidMatch, argument, hasError, argument2 = self._parseSimpleArgument(sr, possibility)

					if hasError:
						nextPossibilities = ()
						break
					elif argumentDidMatch:
						# get possibilities for next argument:
						nextPossibilities = possibility.next
						didMatch = True
						break
					else:
						# sr.cursor = cursor  # not necessarily needed for _parseSimpleArgument(), but required for parseCommand()
						continue

				elif possibility is TERMINAL:
					didMatch = True  # a TERMINAL always matches
				# if sr.hasReachedEnd:
				# 	return True, firstArg, False, lastArg
				elif isinstance(possibility, KeywordSchema):
					continue
				else:
					raise ValueError(f"Cannot handle possibility of type ({type(possibility).__qualname__})")

		return didMatch, argument, hasError, argument2, hasConsumedWhitespace, nextPossibilities

	def _parseSimpleArgument(self, sr: StringReader, possibility: ArgumentSchema) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument]]:
		"""
		:return:(didMatch, firstArg, hasError, lastArg)
		"""
		ctx = getArgumentContext(possibility.type)
		if ctx is None:
			argument = missingArgumentContext(sr, possibility, errorsIO=self.errors)
		else:
			argument = ctx.parse(sr, possibility, self.filePath, errorsIO=self.errors)
		return argument is not None, argument, False, argument

	def _getAllPossibilities(self, possibilities: Sequence[CommandPartSchema]) -> list[CommandPartSchema]:
		result = {}
		self._addAllPossibilities(possibilities, result)
		return list(result.values())

	def _addAllPossibilities(self, possibilities: Sequence[CommandPartSchema], allIO: dict[int, CommandPartSchema]) -> None:
		for possibility in possibilities:
			if isinstance(possibility, SwitchSchema):
				self._addAllPossibilities(possibility.options, allIO)
				if possibility.hasTerminalOption:
					self._addAllPossibilities(possibility.next, allIO)
			else:
				allIO[id(possibility)] = possibility

	def parse(self) -> Optional[MCFunction]:
		return self.parseMCFunction()


def init():
	pass
