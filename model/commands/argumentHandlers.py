import re
from typing import Protocol, Optional, Iterable, MutableSequence, Type, Any

from PyQt5.QtWidgets import QWidget

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.utils import Decorator, HTMLStr, escapeForXml, HTMLifyMarkDownSubSet
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.profiling import logError
from model.commands.argumentTypes import ArgumentType, LiteralsArgumentType
from model.commands.command import ArgumentInfo, CommandNode
from model.commands.parsedCommands import ParsedArgument, ParsedCommandPart
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError, CommandSemanticsError
from model.parsingUtils import Span, Position


class ArgumentParserFunc(Protocol):
	def __call__(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: MutableSequence[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pass


class ValidatorFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		pass


class SuggestionProviderFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> list[str]:
		pass


class DocumentationProviderFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> HTMLStr:
		pass


class ClickabilityProviderFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		pass


class OnIndicatorClickedFunc(Protocol):
	def __call__(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		pass


class ArgumentHandler:
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		return None

	def getSuggestions(self, ai: ArgumentInfo) -> list[str]:
		return []

	def getDocumentation(self, argument: ParsedArgument) -> HTMLStr:
		return defaultDocumentationProvider(argument)

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		return None

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		pass


class AddHandlerToDictDecorator(AddToDictDecorator[str, ArgumentHandler]):
	def __call__(self, key: str, forceOverride: bool = False):
		addFormatterInner = super(AddHandlerToDictDecorator, self).__call__(key, forceOverride)

		def addFormatter(func: Type[ArgumentHandler]) -> Type[ArgumentHandler]:
			addFormatterInner(func())
			return func
		return addFormatter


__argumentHandlers: dict[str, ArgumentHandler] = {}
argumentHandler = Decorator(AddHandlerToDictDecorator(__argumentHandlers))


def getArgumentHandler(type: ArgumentType) -> Optional[ArgumentHandler]:
	if isinstance(type, LiteralsArgumentType):
		handler = LiteralArgumentHandler()
	else:
		handler = __argumentHandlers.get(type.name, None)

	return handler


def makeCommandSyntaxError(sr: StringReader, message: str, *, style: str = 'error') -> CommandSyntaxError:
	return CommandSyntaxError(message, sr.currentSpan, style=style)


def missingArgumentHandler(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	errorMsg: str = f"missing ArgumentHandler for type `{escapeForXml(ai.typeName)}`"
	logError(errorMsg)

	trailingData: str = sr.readUntilEndOrWhitespace()
	errorsIO.append(makeCommandSyntaxError(sr, errorMsg, style='info'))
	sr.rollback()
	return None


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


def defaultDocumentationProvider(argument: ParsedCommandPart) -> HTMLStr:
	info = argument.info
	if info is not None:
		name = info.name
		description = info.description
		if isinstance(info, ArgumentInfo):
			typeStr = escapeForXml(info.type.name)
			typeDescription = [
				info.type.description,
				info.type.description2,
			]
		else:
			typeStr = escapeForXml(info.asCodeString())
			typeDescription = []
		tip = f"{name}\n\n`{typeStr}`\n\n{description}"
		if typeDescription:
			tip += '\n\n'.join(typeDescription)
		tip = HTMLifyMarkDownSubSet(tip)
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = f'<div style="{PythonGUI.helpBoxStyles["error"]}">{message}</div>'
	return tip


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


class LiteralArgumentHandler(ArgumentHandler):

	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return parseLiteral(sr, ai, errorsIO=errorsIO)

	def getSuggestions(self, ai: ArgumentInfo) -> list[str]:
		if isinstance(ai.type, LiteralsArgumentType):
			return ai.type.options
		else:
			return []
