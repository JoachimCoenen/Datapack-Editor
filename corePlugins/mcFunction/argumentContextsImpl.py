from abc import abstractmethod, ABC
from math import inf
from typing import Callable, Optional, Iterable, Any

from base.model.messages import NUMBER_OUT_OF_BOUNDS_MSG
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import Suggestions, errorMsg, validateTree, getSuggestions, getClickableRanges, onIndicatorClicked, getDocumentation, parseNPrepare
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePath
from base.model.utils import Span, Position, GeneralError, MDStr, LanguageId
from cat.utils.collections_ import FrozenDict
from .argumentTypes import *
from .command import ArgumentSchema, ParsedArgument, CommandPart
from .commandContext import ArgumentContext, argumentContext, makeParsedArgument, getArgumentContext
from .stringReader import StringReader


def initPlugin() -> None:
	pass


def parseFromStringReader(sr: StringReader, filePath: FilePath, language: LanguageId, schema: Optional[Schema], *, errorsIO: list[GeneralError], **kwargs) -> Optional[Node]:
	if sr.hasReachedEnd:
		return None

	data, errors, parser = parseNPrepare(
		sr.text,
		filePath=filePath,
		language=language,
		schema=schema,
		line=sr.line,
		lineStart=sr.lineStart,
		cursor=sr.cursor,
		cursorOffset=sr.cursorOffset,
		indexMapper=sr.indexMapper,
		**kwargs
	)

	errorsIO.extend(errors)
	if data is not None:
		sr.save()
		sr.cursor = parser.cursor
		sr.line = parser.line
		sr.lineStart = parser.lineStart
	return data


class ParsingHandler(ArgumentContext, ABC):

	@abstractmethod
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		pass

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return {}

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		schema = self.getSchema(ai)
		language = self.getLanguage(ai)
		data = parseFromStringReader(sr, filePath, language, schema, errorsIO=errorsIO, **self.getParserKwArgs(ai))
		if data is not None:
			return makeParsedArgument(sr, ai, value=data)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		validateTree(node.value, node.source, errorsIO)

	def getErsatzNodeForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[Node]:
		"""override in subclasses if you wnt to provide an ersatz node."""
		return None

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		"""
		:param ai:
		:param node:
		:param pos: cursor position
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		if node is not None:
			value = node.value
			source = node.source
		else:
			value = self.getErsatzNodeForSuggestions(ai, pos, replaceCtx)
			source = b''

		return getSuggestions(value, source, pos, replaceCtx)

	def getDocumentation(self, node: ParsedArgument, pos: Position) -> MDStr:
		docs = [
			super(ParsingHandler, self).getDocumentation(node, pos),
			getDocumentation(node.value, node.source, pos)
		]
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.value, node.source)

	def onIndicatorClicked(self, node: ParsedArgument, pos: Position) -> None:
		onIndicatorClicked(node.value, node.source, pos)


@argumentContext(BRIGADIER_BOOL.name)
class BoolHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadBoolean()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[CommandPart], pos: Position, replaceCtx: str) -> Suggestions:
		return ['true', 'false']


@argumentContext(BRIGADIER_DOUBLE.name, numberReader=StringReader.tryReadFloat, numberParser=float)
@argumentContext(BRIGADIER_FLOAT.name, numberReader=StringReader.tryReadFloat, numberParser=float)
@argumentContext(BRIGADIER_INTEGER.name, numberReader=StringReader.tryReadInt, numberParser=int)
@argumentContext(BRIGADIER_LONG.name, numberReader=StringReader.tryReadInt, numberParser=int)
class NumberHandler(ArgumentContext):
	def __init__(self, numberReader: Callable[[StringReader], Optional[bytes]], numberParser: Callable[[str], int | float]):
		super().__init__()
		self.numberReader: Callable[[StringReader], Optional[bytes]] = numberReader
		self.numberParser: Callable[[str], int | float] = numberParser

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = self.numberReader(sr)
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=self.numberParser(bytesToStr(string)))

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		if not isinstance(node.value, (int | float)):
			return

		args = node.schema.args or FrozenDict.EMPTY

		minVal = args.get('min', -inf)
		maxVal = args.get('max', +inf)

		if not minVal <= node.value <= maxVal:
			errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, minVal, maxVal, span=node.span, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		args = ai.args or FrozenDict.EMPTY
		minVal = args.get('min', -inf)
		maxVal = args.get('max', +inf)
		additionalSuggestions = args.get('suggestions', ())

		suggestions = [str(suggestion) for suggestion in additionalSuggestions]

		if minVal > -inf:
			suggestions.append(str(minVal))

		if minVal < 0 < maxVal:
			suggestions.append('0')

		if minVal < maxVal < +inf:
			suggestions.append(str(maxVal))

		return suggestions


@argumentContext(BRIGADIER_STRING.name)
class StringHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadString()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


def checkArgumentContextsForRegisteredArgumentTypes():
	"""makes sure there's an ArgumentContext for every registered named ArgumentType"""
	for name, argType in ALL_NAMED_ARGUMENT_TYPES.items():
		if name != argType.name:
			raise ValueError(f"argumentType {argType.name!r} registered under wrong name {name!r}.")
		if getArgumentContext(argType) is None:
			raise ValueError(f"missing argumentContext for argumentType {argType.name!r}.")


# make sure there's an ArgumentContext for every registered named ArgumentType:
checkArgumentContextsForRegisteredArgumentTypes()
