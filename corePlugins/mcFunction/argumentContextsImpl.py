from abc import abstractmethod, ABC
from typing import Optional, Iterable, Any

from base.model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getClickableRanges, onIndicatorClicked, getDocumentation, parseNPrepare
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePath
from base.model.utils import Span, Position, GeneralError, MDStr, LanguageId
from .argumentTypes import *
from .command import ArgumentSchema, ParsedArgument, CommandPart
from .commandContext import ArgumentContext, argumentContext, makeParsedArgument, getArgumentContext
from .stringReader import StringReader


def initPlugin() -> None:
	pass


def parseFromStringReader(sr: StringReader, filePath: FilePath, language: LanguageId, schema: Optional[Schema], *, errorsIO: list[GeneralError], **kwargs) -> Optional[Node]:
	if sr.hasReachedEnd:
		return None

	data, errors = parseNPrepare(
		# sr.text[sr.cursor:],  #todo why copy the text?
		sr.text,
		filePath=filePath,
		language=language,
		schema=schema,
		line=sr.line,
		lineStart=sr.lineStart,
		cursor=sr.cursor,
		cursorOffset=sr.cursorOffset,
		**kwargs
	)

	errorsIO.extend(errors)
	if data is not None:
		sr.save()
		sr.cursor += data.span.length  # TODO: use parser.cursor, etc. instead
		sr.line = data.span.end.line
		sr.lineStart = data.span.end.index - data.span.end.column
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


@argumentContext(BRIGADIER_DOUBLE.name)
class DoubleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_FLOAT.name)
class FloatHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_INTEGER.name)
class IntegerHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_LONG.name)
class LongHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


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
