import re
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional, Sequence, cast

from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import AddContextToDictDecorator, Context, ContextProvider, Match, Suggestions
from base.model.pathUtils import FilePath
from base.model.utils import GeneralError, MDStr, ParsingError, Position, Span, formatAsError
from cat.utils import Decorator, escapeForXml
from cat.utils.profiling import logError
from .argumentTypes import ArgumentType, LiteralsArgumentType
from .command import *
from .stringReader import StringReader


class CommandCtxProvider(ContextProvider[CommandPart]):

	def getBestMatch(self, pos: Position) -> Match[CommandPart]:
		tree = self.tree
		match = Match(None, None, None, [])
		if isinstance(tree, MCFunction):
			children = tuple(tree.children)
			for child in children:
				if child.span.start < pos <= child.span.end:
					if isinstance(child, ParsedComment):
						continue
					match.before = child
					_getBestMatch(child, pos, match)
		else:
			_getBestMatch(tree, pos, match)
		return match

	def getContext(self, node: CommandPart) -> Optional[Context]:
		if isinstance(node, ParsedArgument):
			schema = node.schema
			if isinstance(schema, ArgumentSchema):
				return getArgumentContext(schema.type)
			elif isinstance(schema, KeywordSchema):
				return KEYWORD_CONTEXT
		return None

	def prepareTree(self, filePath: FilePath, errorsIO: list[GeneralError]) -> None:
		pass

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		if isinstance(self.tree, MCFunction):
			from .validator import checkMCFunction
			errorsIO += checkMCFunction(self.tree)
		elif isinstance(self.tree, ParsedCommand):
			from .validator import validateCommand
			validateCommand(self.tree.next, self.tree.schema, errorsIO=cast(list, errorsIO))
		elif isinstance(self.tree, CommandPart):
			from .validator import validateArgument
			validateArgument(self.tree, errorsIO=cast(list, errorsIO))

	def _getCommandSuggestions(self) -> Suggestions:
		schema = self.tree.schema
		if isinstance(schema, MCFunctionSchema):
			return [cmd.name + ' ' for cmd in schema.commands.values()]

		tree = self.tree
		while (prev := tree.prev) is not None:
			tree = prev

		schema = self.tree.schema
		if isinstance(schema, MCFunctionSchema):
			return [cmd.name + ' ' for cmd in schema.commands.values()]
		return []

	def _getNextKeywords(self, nexts: Iterable[CommandPartSchema], node: Optional[CommandPart], pos: Position, replaceCtx: str) -> list[str]:
		result = []
		for nx in nexts:
			if isinstance(nx, KeywordSchema):
				result.append(nx.name + ' ')
			elif isinstance(nx, ArgumentSchema):
				if (ctx := getArgumentContext(nx.type)) is not None:
					result += ctx.getSuggestions2(nx, node, pos, replaceCtx)
			elif nx is COMMANDS_ROOT:
				result += self._getCommandSuggestions()
		return result

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		match = self.getBestMatch(pos)
		hit = match.hit
		before = match.before
		if hit is not None:
			before = hit.prev
		if before is not None:
			return self._getNextKeywords(getNextSchemas(before), hit, pos, replaceCtx)
		elif hit is not None and isinstance(hit, ParsedArgument) and isinstance(hit.schema, ArgumentSchema):
			if (ctx := getArgumentContext(hit.schema.type)) is not None:
				return ctx.getSuggestions2(hit.schema, hit, pos, replaceCtx)

		return self._getCommandSuggestions()

	def getCallTips(self, pos: Position) -> list[str]:
		match = self.getBestMatch(pos)
		hit = match.hit
		before = match.before
		possibilities: Optional[Sequence[CommandPartSchema]] = None
		if hit is not None:
			if (ctx := self.getContext(hit)) is not None:
				if tips := ctx.getCallTips(hit, pos):
					return tips
			before = hit.prev

		if before is not None:
			possibilities = getNextSchemas(before)
		elif hit is not None and hit.schema is not None:
			possibilities = [hit.schema]

		if possibilities is not None:
			return [p.asString for p in possibilities] or [TERMINAL.asString]
		return ['?']

	def _getClickableRangesInternal(self, span: Span, tree: CommandPart, rangesIO: list[Span]) -> None:
		child = tree
		while child is not None:
			if child.span.overlaps(span):
				if (ctx := self.getContext(child)) is not None:
					if partRanges := ctx.getClickableRanges(child):
						rangesIO.extend(partRanges)
			child = child.next

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		tree = self.tree
		ranges: list[Span] = list()
		if isinstance(tree, MCFunction):
			children = tuple(tree.children)
			for child in children:
				if child.span.overlaps(span):
					self._getClickableRangesInternal(span, child, ranges)
		else:
			self._getClickableRangesInternal(span, tree, ranges)
		return ranges


def _getBestMatch(tree: CommandPart, pos: Position, match: Match) -> None:
	if isinstance(tree, ParsedCommand):
		child = tree.next
	else:
		child = tree

	while child is not None:
		span = child.span
		if span.end < pos:
			match.before = child
		elif span.start <= pos:
			match.hit = child
			match.before = None
			break
		elif pos < span.start:
			match.after = child
			break

		child = child.next


class ArgumentContext(Context[ParsedArgument], ABC):
	@abstractmethod
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		pass

	def getSuggestions(self, node: ParsedArgument, pos: Position, replaceCtx: str) -> Suggestions:
		return self.getSuggestions2(node.schema, node, pos, replaceCtx)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		"""
		:param ai:
		:param node:
		:param pos: cursor position
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		return []

	def getDocumentation(self, node: ParsedArgument, pos: Position) -> MDStr:
		return defaultDocumentationProvider(node)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		pass

	def onIndicatorClicked(self, node: ParsedArgument, pos: Position) -> None:
		pass


class KeywordContext(ArgumentContext, ABC):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)  # parsing is KeywordArguments is handled by the parser itself.


KEYWORD_CONTEXT: KeywordContext = KeywordContext()


__argumentContexts: dict[str, ArgumentContext] = {}
argumentContext = Decorator(AddContextToDictDecorator[ArgumentContext](__argumentContexts))


def getArgumentContext(aType: ArgumentType) -> Optional[ArgumentContext]:
	if isinstance(aType, LiteralsArgumentType):
		handler = LiteralArgumentHandler()
	else:
		handler = __argumentContexts.get(aType.name, None)

	return handler


def defaultDocumentationProvider(argument: CommandPart) -> MDStr:
	schema = argument.schema
	if schema is not None:
		name = schema.name
		description = schema.description
		if isinstance(schema, ArgumentSchema):
			typeStr = escapeForXml(schema.type.name)
			typeDescription = [
				name,
				f'`{typeStr}`',
				description,
				schema.type.description,
				schema.type.description2,
			]
			tip = '\n\n'.join(typeDescription)
		else:
			tip = description
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = formatAsError(message)
	return tip


def missingArgumentContext(sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
	errorMsg = MDStr(f"missing ArgumentContext for type `{escapeForXml(ai.typeName)}`")
	logError(errorMsg)

	sr.readUntilEndOrWhitespace()
	errorsIO.append(ParsingError(errorMsg, sr.currentSpan, style='info'))
	sr.rollback()
	return None


def missingArgumentParser(sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
	errorMsg = MDStr(f"missing parse(...) implementation in ArgumentContext for type `{escapeForXml(ai.typeName)}`")
	logError(errorMsg)

	sr.readUntilEndOrWhitespace()
	errorsIO.append(ParsingError(errorMsg, sr.currentSpan, style='info'))
	sr.rollback()
	return None


def makeParsedArgument(sr: StringReader, schema: Optional[CommandPartSchema], value: Any) -> ParsedArgument:
	content = sr.text[sr.lastCursors.peek():sr.cursor]
	return ParsedArgument(
		sr.currentSpan,
		schema,
		sr.fullSource,
		content,
		value
	)


def parseLiteral(sr: StringReader, ai: ArgumentSchema) -> Optional[ParsedArgument]:
	assert isinstance(ai.type, LiteralsArgumentType)
	literal = sr.tryReadRegex(re.compile(rb'\w+'))
	if literal is None:
		literal = sr.tryReadLiteral()
	if literal is None:
		return None
	options: set[bytes] = set(ai.type.options)
	if literal not in options:
		sr.rollback()
		return None
	return makeParsedArgument(sr, ai, value=literal)


class LiteralArgumentHandler(ArgumentContext):

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return parseLiteral(sr, ai)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[CommandPart], pos: Position, replaceCtx: str) -> Suggestions:
		if isinstance(ai.type, LiteralsArgumentType):
			return [bytesToStr(option) + ' ' for option in ai.type.options]
		else:
			return []
