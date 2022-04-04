import re
from abc import abstractmethod, ABC
from typing import Iterable, Optional, Type, Any

from PyQt5.QtWidgets import QWidget

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.utils import HTMLStr, escapeForXml, HTMLifyMarkDownSubSet, Decorator
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.profiling import logError
from model.commands.argumentTypes import LiteralsArgumentType, ArgumentType
from model.commands.command import CommandPart, MCFunction, ParsedComment, ParsedArgument, ArgumentSchema, CommandPartSchema, TERMINAL, COMMANDS_ROOT, KeywordSchema, \
	SwitchSchema, formatPossibilities
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.parsing.contextProvider import ContextProvider, Suggestions, Context, Match, registerContextProvider
from model.utils import Position, Span, GeneralError


@registerContextProvider(CommandPart)
class CommandCtxProvider(ContextProvider[CommandPart]):
	@staticmethod
	def _getBestMatch(tree: CommandPart, pos: Position, match: Match) -> None:
		child = tree
		while child is not None:
			if child.end < pos:
				match.before = child
			elif child.start <= pos:
				match.hit = child
			elif pos < child.start:
				match.after = child
				break
			child = child.next

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
					self._getBestMatch(child, pos, match)
					# correct some special cases:
					# if match.before is match.hit:
					# 	match.before = None
					if match.before is not None and match.hit is not None:
						if match.before.span.end > match.hit.span.start:
							match.contained.append(match.hit)
							match.hit = None
		else:
			self._getBestMatch(tree, pos, match)
		return match

	def getContext(self, node: CommandPart) -> Optional[Context]:
		if isinstance(node, ParsedArgument):
			schema = node.schema
			if isinstance(schema, ArgumentSchema):
				return getArgumentContext(schema.type)
		return None

	def prepareTree(self) -> list[GeneralError]:
		pass

	def validateTree(self) -> list[GeneralError]:
		pass

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		match = self.getBestMatch(pos)
		hit = match.hit
		before = match.before
		contextStr = ''
		posInContextStr = 0
		# if match.info is None or (0 <= idx-1 < len(text) and text[idx-1] != ' '):
		if hit is not None:
			if not hit.span.end.index >= pos.index:
				before = hit
			elif before is not None:
				contextStr = hit.content
				posInContextStr = pos.index - hit.span.start.index
		if before is not None:
			if (schema := before.schema) is not None:
				result = self._getNextKeywords(schema.next, contextStr, posInContextStr, replaceCtx)
				return result
			# contextStr = context[-1] if context else ''
			return []

		from session.session import getSession
		return [cmd + ' ' for cmd in getSession().minecraftData.commands.keys()]

	def _getNextKeywords(self, nexts: Iterable[CommandPartSchema], contextStr: str, cursorPos: int, replaceCtx: str) -> list[str]:
		result = []
		for nx in nexts:
			if isinstance(nx, KeywordSchema):
				result.append(nx.name + ' ')
			elif isinstance(nx, SwitchSchema):
				result += self._getNextKeywords(nx.options, contextStr, cursorPos, replaceCtx)
				hasTerminal = TERMINAL in nx.options
				if hasTerminal:
					result += self._getNextKeywords(nx.next, contextStr, cursorPos, replaceCtx)
			elif isinstance(nx, ArgumentSchema):
				handler = getArgumentContext(nx.type)
				if handler is not None:
					result += handler.getSuggestions2(nx, contextStr, cursorPos, replaceCtx)
			elif nx is COMMANDS_ROOT:
				from session.session import getSession
				result += [cmd + ' ' for cmd in getSession().minecraftData.commands.keys()]
		return result

	# def getDocumentation(self, pos: Position) -> HTMLStr:
	# 	pass

	@staticmethod
	def _getPossibilitiesFromHit(hit: CommandPart) -> Optional[list[CommandPartSchema]]:
		if (prev := hit.prev) is not None:
			if (schema := prev.schema) is not None:
				if (next_ := schema.next) is not None:
					return next_
		if (schema := hit.schema) is not None:
			return [schema]
		return None

	@staticmethod
	def _getPossibilitiesFromBefore(before: CommandPart) -> Optional[list[CommandPartSchema]]:
		if (schema := before.schema) is not None:
			return schema.next
		return None

	def getCallTips(self, pos: Position) -> list[str]:
		match = self.getBestMatch(pos)
		possibilities: Optional[list[CommandPartSchema]] = None
		if (hit := match.hit) is not None:
			# if (ctx := self.getContext(hit)) is not None:
			# 	return ctx.getDocumentation(hit, pos)
			possibilities = self._getPossibilitiesFromHit(hit)

		if possibilities is None:
			if (before := match.before) is not None:
				possibilities = self._getPossibilitiesFromBefore(before)

		if possibilities is not None:
			return [formatPossibilities((p,)) for p in possibilities]
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


class ArgumentContext(Context[ParsedArgument], ABC):
	@abstractmethod
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		pass

	def getSuggestions(self, node: ParsedArgument, pos: Position, replaceCtx: str) -> Suggestions:
		posInContextStr = pos.index - node.span.start.index
		contextStr = node.content
		return self.getSuggestions2(node.schema, contextStr, posInContextStr, replaceCtx)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		"""
		:param ai:
		:param contextStr:
		:param cursorPos: cursor position in contextStr
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		return []

	def getDocumentation(self, node: ParsedArgument, pos: Position) -> HTMLStr:
		return defaultDocumentationProvider(node)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		pass

	def onIndicatorClicked(self, node: ParsedArgument, pos: Position, window: QWidget) -> None:
		pass


class AddContextToDictDecorator(AddToDictDecorator[str, ArgumentContext]):
	def __call__(self, key: str, forceOverride: bool = False):
		addFormatterInner = super(AddContextToDictDecorator, self).__call__(key, forceOverride)

		def addFormatter(func: Type[ArgumentContext]) -> Type[ArgumentContext]:
			addFormatterInner(func())
			return func
		return addFormatter


__argumentContexts: dict[str, ArgumentContext] = {}
argumentContext = Decorator(AddContextToDictDecorator(__argumentContexts))


def getArgumentContext(aType: ArgumentType) -> Optional[ArgumentContext]:
	if isinstance(aType, LiteralsArgumentType):
		handler = LiteralArgumentHandler()
	else:
		handler = __argumentContexts.get(aType.name, None)

	return handler


def defaultDocumentationProvider(argument: CommandPart) -> HTMLStr:
	schema = argument.schema
	if schema is not None:
		name = schema.name
		description = schema.description
		if isinstance(schema, ArgumentSchema):
			typeStr = escapeForXml(schema.type.name)
			typeDescription = [
				schema.type.description,
				schema.type.description2,
			]
		else:
			typeStr = escapeForXml(schema.asString)
			typeDescription = []
		tip = f"{name}\n\n`{typeStr}`\n\n{description}"
		if typeDescription:
			tip += '\n\n'.join(typeDescription)
		tip = HTMLifyMarkDownSubSet(tip)
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = f'<div style="{PythonGUI.helpBoxStyles["error"]}">{message}</div>'
	return tip


def makeCommandSyntaxError(sr: StringReader, message: str, *, style: str = 'error') -> CommandSyntaxError:
	return CommandSyntaxError(message, sr.currentSpan, style=style)


def missingArgumentContext(sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	errorMsg: str = f"missing ArgumentContext for type `{escapeForXml(ai.typeName)}`"
	logError(errorMsg)

	sr.readUntilEndOrWhitespace()
	errorsIO.append(makeCommandSyntaxError(sr, errorMsg, style='info'))
	sr.rollback()
	return None


def missingArgumentParser(sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	errorMsg: str = f"missing parse(...) implementation in ArgumentContext for type `{escapeForXml(ai.typeName)}`"
	logError(errorMsg)

	sr.readUntilEndOrWhitespace()
	errorsIO.append(makeCommandSyntaxError(sr, errorMsg, style='info'))
	sr.rollback()
	return None


def makeParsedArgument(sr: StringReader, schema: Optional[CommandPartSchema], value: Any) -> ParsedArgument:
	return ParsedArgument(
		sr.currentSpan,
		schema,
		sr.fullSource,
		value
	)


def parseLiteral(sr: StringReader, ai: ArgumentSchema) -> Optional[ParsedArgument]:
	literal = sr.tryReadRegex(re.compile(r'\w+'))
	if literal is None:
		literal = sr.tryReadLiteral()
	if literal is None:
		return None
	assert isinstance(ai.type, LiteralsArgumentType)
	options: set[str] = set(ai.type.options)
	if literal not in options:
		sr.rollback()
		return None
	return makeParsedArgument(sr, ai, value=literal)


class LiteralArgumentHandler(ArgumentContext):

	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return parseLiteral(sr, ai)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		if isinstance(ai.type, LiteralsArgumentType):
			return [option + ' ' for option in ai.type.options]
		else:
			return []
