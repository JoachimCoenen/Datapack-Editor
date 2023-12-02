import re
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from .command import *
from .stringReader import StringReader
from base.model.utils import ParsingError, Span, Message, wrapInMarkdownCode

from .commandContext import makeParsedArgument, getArgumentContext, missingArgumentContext
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import IndexMapBuilder, ParserBase


UNKNOWN_COMMAND_MSG = Message("Unknown Command '{0}'", 1)
EXPECTED_ARGUMENT_SEPARATOR_MSG: Message = Message("Expected whitespace to end one argument, but found trailing data: {0}", 1)

_LINE_CONTINUE_PATTERN = re.compile(br'\\ *\r?\n$')


@dataclass
class MCFunctionParser(ParserBase[MCFunction, MCFunctionSchema]):

	def parseMCFunction(self) -> Optional[MCFunction]:
		p1 = self.currentPos
		children = self._parseMcFunctionContents()
		p2 = self.currentPos
		result: MCFunction = MCFunction(
			Span(p1, p2),
			self.schema,
			self.text,
			self.text,
			children
		)
		return result

	def _parseMcFunctionContents(self) -> list[ParsedCommand | ParsedComment]:
		children = []
		actualLines = self.text.splitlines(keepends=True)
		linesCount = len(actualLines)
		lineNo = 0
		cursorOffset = self.cursorOffset
		cursor = self.cursor
		mergedLinesCount = 1
		lasWasEscaped: bool = False
		virtualLine = b''
		while lineNo < linesCount:
			line = actualLines[lineNo]
			if lasWasEscaped:
				strippedLine = line.lstrip()
				lenDiff = len(line) - len(strippedLine)
				idxMapBldr.addMarker(self.cursor + lenDiff, len(virtualLine) + cursorOffset)
			else:
				strippedLine = line
				lenDiff = 0

			lineContMatch = _LINE_CONTINUE_PATTERN.search(strippedLine)
			if lineContMatch is not None:
				if not lasWasEscaped:
					# we need a new IndexMapBuilder
					idxMapBldr = IndexMapBuilder(self.indexMapper, self.cursorOffset)  # - self.cursorOffset)  # + 1 because of opening quotation marks?

				lineContpos = lineContMatch.start(0)
				virtualLine += strippedLine[:lineContpos]
				idxMapBldr.addMarker(self.cursor + lineContpos + lenDiff - 1, len(virtualLine) + cursorOffset - 1)
				lasWasEscaped = True

			if lineContMatch is None or lineNo == linesCount - 1:  # also parse for last line, even if we have an escape!
				if strippedLine.endswith(b'\r\n'):
					nlLen = 2
				elif strippedLine.endswith(b'\n'):
					nlLen = 1
				else:
					nlLen = 0
				strippedLine = strippedLine[:len(strippedLine) - nlLen]
				virtualLine += strippedLine
				if lasWasEscaped:
					# we have an IndexMapBuilder we must use:
					idxMap = idxMapBldr.completeIndexMapper(self.cursor + len(line) - nlLen, len(virtualLine) + cursorOffset)
				else:
					idxMap = self.indexMapper
				reader = StringReader(virtualLine, self.line, self.lineStart, cursor, cursorOffset, idxMap, self.text)
				if (node := self.parseVirtualLine(reader)) is not None:
					children.append(node)
				cursor = 0
				virtualLine = b''
				lasWasEscaped = False
				self.cursor += len(line)
				cursorOffset = self.cursorOffset + self.cursor
				for _ in range(mergedLinesCount):
					self.advanceLine()
				mergedLinesCount = 1

			else:
				self.cursor += len(line)
				mergedLinesCount += 1
			lineNo += 1

		return children

	def parseVirtualLine(self, sr: StringReader) -> Optional[ParsedCommand | ParsedComment]:
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
		isTemplateCommand =  sr.tryConsumeByte(ord(b'$'))
		startCursor = sr.cursor
		startPos = sr.currentPos
		sr.tryConsumeByte(ord(b'/'))

		if isTemplateCommand:
			oldErrors = self.errors.copy()
			didMatch, commandArg, hasErrors, lastArg = self._parseSimpleCommand(sr)
			self.errors = oldErrors
		else:
			didMatch, commandArg, hasErrors, lastArg = self._parseSimpleCommand(sr)

		if commandArg is None:
			return None

		commandSpan = Span(startPos, sr.currentPos)
		endCursor = sr.cursor
		content = sr.text[startCursor:endCursor]

		command = ParsedCommand(name=commandArg.content, schema=commandArg.schema, span=commandSpan, source=self.text, content=content, isTemplateCommand=isTemplateCommand)
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
		commandArg.potentialNextSchemas += commandSchema.next.flattened

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
		self.errorMsg(EXPECTED_ARGUMENT_SEPARATOR_MSG, trailingData, span=sr.currentSpan)

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
	def parseKeywords(sr: StringReader, keywords: Mapping[bytes, KeywordSchema]) -> Optional[ParsedArgument]:
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

	def parseArguments(self, sr: StringReader, possibilities: Options) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument]]:
		"""
		:return:(didMatch, firstArg, hasError, lastArg)
		"""
		lastArg = None
		firstArg = None

		# try to parse Keywords & Arguments:
		while True:  # not sr.hasReachedEnd:
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
				# finally consume whitespace:
				if not hasConsumedWhitespace and not sr.tryConsumeWhitespace() and not sr.hasReachedEnd:
					self._addExpectedArgumentError(sr)
					sr.rollback()
					break

			if not possibilities:
				break

		return didMatch, firstArg, hasError, lastArg

	def parseArgument(self, sr: StringReader, possibilities: Options) -> tuple[bool, Optional[ParsedArgument], bool, Optional[ParsedArgument], bool, Sequence[CommandPartSchema]]:
		hasError = False
		hasConsumedWhitespace = False

		argument: Optional[ParsedArgument] = self.parseKeywords(sr, possibilities.keywords)
		argument2: Optional[ParsedArgument] = argument
		if argument is not None:
			nextPossibilities = argument.schema.next
			argument2.potentialNextSchemas += argument.schema.next.flattened
			didMatch = True
		else:
			nextPossibilities = ()
			didMatch = possibilities.hasTerminal  # a TERMINAL always matches
			for possibility in possibilities.nonKeywords:
				# cursor = sr.cursor
				if possibility is COMMANDS_ROOT:
					argumentDidMatch, argument, hasError, argument2 = self._parseSimpleCommand(sr)
				elif isinstance(possibility, SwitchSchema):
					argumentDidMatch, argument, hasError, argument2 = self.parseArguments(sr, possibility.options)
					hasConsumedWhitespace = argumentDidMatch
				else:
					argumentDidMatch, argument, hasError, argument2 = self._parseSimpleArgument(sr, possibility)

				if hasError:
					break
				elif argumentDidMatch:
					nextPossibilities = possibility.next  # get possibilities for next argument
					if argument2 is not None:  # we successfully parsed an argument!
						argument2.potentialNextSchemas += possibility.next.flattened
					didMatch = True
					break

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

	def parse(self) -> Optional[MCFunction]:
		return self.parseMCFunction()


def init():
	pass
