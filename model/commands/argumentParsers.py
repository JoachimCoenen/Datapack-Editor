import re
from typing import Optional, Protocol, Any

from Cat.utils import Decorator, escapeForXml
from Cat.utils.collections import AddToDictDecorator
from Cat.utils.profiling import logError
from model.commands.argumentTypes import *
from model.commands.command import ArgumentInfo, CommandNode
from model.commands.utils import CommandSyntaxError
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader


class ArgumentParserFunc(Protocol):
	def __call__(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pass


__argumentParses: dict[str, ArgumentParserFunc] = {}
argumentParser = Decorator(AddToDictDecorator[str, ArgumentParserFunc](__argumentParses))


def getArgumentParser(type: ArgumentType) -> Optional[ArgumentParserFunc]:
	if isinstance(type, LiteralsArgumentType):
		parser = parseLiteral
	else:
		parser = __argumentParses.get(type.name, None)
	return parser


def makeCommandSyntaxError(sr: StringReader, message: str, *, style: str = 'error') -> CommandSyntaxError:
	return CommandSyntaxError(message, sr.currentSpan, style=style)


def missingArgumentParser(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	errorMsg: str = f"missing ArgumentParser for type `{escapeForXml(ai.typeName)}`"
	logError(errorMsg)

	trailingData: str = sr.readUntilEndOrWhitespace()
	errorsIO.append(makeCommandSyntaxError(sr, errorMsg, style='info'))
	sr.rollback()
	return None


def makeParsedArgument(sr: StringReader, ai: Optional[CommandNode], value: Any) -> ParsedArgument:
	span = sr.currentSpan
	argument = ParsedArgument.create(
		source=sr.fullSource,
		span=span,
		value=value,
		info=ai,
	)
	return argument


def parseLiteral(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	literal = sr.tryReadRegex(re.compile(r'\w+'))
	if literal is None:
		literal = sr.tryReadLiteral()
	if literal is None:
		return None

	options: set[str] = set(ai.type.options)
	if literal not in options:
		sr.rollback()
		return None
	return makeParsedArgument(sr, ai, value=literal)
