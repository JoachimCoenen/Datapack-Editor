import re
from typing import Protocol, Optional, Iterable, MutableSequence, Type, Any

from PyQt5.QtWidgets import QWidget

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.utils import Decorator, HTMLStr, escapeForXml, HTMLifyMarkDownSubSet
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.profiling import logError
from model.commands.argumentTypes import ArgumentType, LiteralsArgumentType
from model.commands.command import ArgumentInfo, CommandNode
from model.commands.parsedCommands import ParsedArgument, ParsedCommandPart, ParsedNode
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError, CommandSemanticsError
from model.parsingUtils import Span, Position


class ArgumentParserFunc(Protocol):
	def __call__(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: MutableSequence[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pass


class ValidatorFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		pass


Suggestion = str  # for now...
Suggestions = list[Suggestion]


class SuggestionProviderFunc(Protocol):
	def __call__(self, argument: ParsedArgument) -> Suggestions:
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

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		"""
		:param ai:
		:param contextStr:
		:param cursorPos: cursor position in contextStr
		:param replaceCtx: the string that will be replaced
		:return:
		"""
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


def getArgumentHandlerForNode(node: CommandNode) -> Optional[ArgumentHandler]:
	if isinstance(node, ArgumentInfo):
		type_: ArgumentType = node.type
		return getArgumentHandler(type_)
	return None


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


def makeParsedNode(sr: StringReader) -> ParsedNode:
	argument = ParsedNode(
		sr.fullSource,
		sr.currentSpan,
	)
	return argument


def makeParsedArgument(sr: StringReader, ai: Optional[CommandNode], value: Any) -> ParsedArgument:
	argument = ParsedArgument(
		sr.fullSource,
		sr.currentSpan,
		value,
		ai,
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

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		if isinstance(ai.type, LiteralsArgumentType):
			return ai.type.options
		else:
			return []

