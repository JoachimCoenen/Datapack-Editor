from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, Iterable, Optional, Type, final

from cat.utils import Decorator
from cat.utils.collections_ import AddToDictDecorator
from cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from cat.utils.logging_ import logWarning
from base.model.parsing.parser import ParserBase, parse, IndexMapper
from base.model.parsing.tree import Node, Schema
from base.model.pathUtils import FilePath
from base.model.utils import LanguageId, MDStr, MessageLike, SemanticsError, Span, Position, GeneralError, formatAsError

_TNode = TypeVar('_TNode', bound=Node)


def createErrorMsg(msg: MessageLike, *args: str, span: Span, style: str = 'error') -> SemanticsError:
	# if len(self.errors) >= self.maxErrors > 0:
	# 	return  # don't generate too many errors!
	msgStr = msg.format(*args)
	return SemanticsError(msgStr, span=span, style=style)


def errorMsg(msg: MessageLike, *args, span: Span, style: str = 'error', errorsIO: list[GeneralError]) -> None:
	error = createErrorMsg(msg, *args, span=span, style=style)
	errorsIO.append(error)


Suggestion = str  # for now...
Suggestions = list[Suggestion]


@dataclass
class CtxInfo(Generic[_TNode]):
	ctxProvider: ContextProvider[_TNode]
	filePath: FilePath


class Context(Generic[_TNode]):
	def prepare(self, node: _TNode, info: CtxInfo[_TNode], errorsIO: list[GeneralError]) -> None:
		pass

	@abstractmethod
	def validate(self, node: _TNode, errorsIO: list[GeneralError]) -> None:
		pass

	@abstractmethod
	def getSuggestions(self, node: _TNode, pos: Position, replaceCtx: str) -> Suggestions:
		"""
		:param node:
		:param pos: cursor position in contextStr
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		return []

	@abstractmethod
	def getDocumentation(self, node: _TNode, pos: Position) -> MDStr:
		return defaultDocumentationProvider(node)

	def getCallTips(self, node: _TNode, pos: Position) -> list[str]:
		return []

	@abstractmethod
	def getClickableRanges(self, node: _TNode) -> Optional[Iterable[Span]]:
		pass

	@abstractmethod
	def onIndicatorClicked(self, node: _TNode, pos: Position) -> None:
		pass

	# @abstractmethod
	def getWordCharacters(self, node: _TNode, pos: Position) -> Optional[str]:
		return None  #  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	# @abstractmethod
	def getAutoCompletionWordSeparators(self, node: _TNode, pos: Position) -> list[str]:
		return []  # ['.', '::', '->']

	def checkCorrectNodeType(self, node: _TNode, expectedNodeType: Type[_TNode] | tuple[Type[_TNode], ...]) -> bool:
		if not isinstance(node, expectedNodeType):
			logWarning(f"checkCorrectNodeType() failed", f"expectedNodeType={expectedNodeType}", f"received type was {type(node)}" )
			return False
		return True


def defaultDocumentationProvider(argument: Node) -> MDStr:
	schema = argument.schema
	if schema is not None:
		if schema.description:
			tip = schema.description
		else:
			tip = MDStr('')
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = formatAsError(message)
	return tip



_TContext = TypeVar('_TContext', bound=Context)


class AddContextFunc(Protocol[_TContext]):
	def __call__(self, func: Type[_TContext]) -> Type[_TContext]:
		pass


class AddContextToDictDecorator(AddToDictDecorator[str, _TContext], Generic[_TContext]):
	def __call__(self, key: str, *, forceOverride: bool = False, **kwargs) -> AddContextFunc[_TContext]:
		addContextInner = super(AddContextToDictDecorator, self).__call__(key, forceOverride=forceOverride)

		def addContext(func: Type[_TContext]) -> Type[_TContext]:
			addContextInner(func(**kwargs))
			return func
		return addContext


@dataclass
class Match(Generic[_TNode]):
	before: Optional[_TNode]
	hit: Optional[_TNode]
	after: Optional[_TNode]
	contained: list[_TNode]


class ContextProvider(Generic[_TNode], ABC):
	def __init__(self, tree: _TNode, text: bytes):
		self.tree: _TNode = tree
		self.text: bytes = text

	@abstractmethod
	def getBestMatch(self, pos: Position) -> Match[_TNode]:
		pass

	@abstractmethod
	def getContext(self, node: _TNode) -> Optional[Context]:
		pass

	def prepareTree(self, filePath: FilePath, errorsIO: list[GeneralError]) -> None:
		info = CtxInfo(self, filePath)
		self._prepareAll(self.tree, info, errorsIO)

	def _prepareAll(self, node: _TNode, info: CtxInfo, errorsIO: list[GeneralError]) -> None:
		if (ctx := self.getContext(node)) is not None:
			ctx.prepare(node, info, errorsIO)
		for innerChild in node.children:
			self._prepareAll(innerChild, info, errorsIO)

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		self._validateAll(self.tree, errorsIO)
		return

	def _validateAll(self, node: _TNode, errorsIO: list[GeneralError]) -> None:
		if (ctx := self.getContext(node)) is not None:
			ctx.validate(node, errorsIO)
		for innerChild in node.children:
			self._validateAll(innerChild, errorsIO)

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		"""
		:param pos: cursor position in contextStr
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				return ctx.getSuggestions(match.hit, pos, replaceCtx)
		return []

	def getDocumentation(self, pos: Position) -> MDStr:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				return ctx.getDocumentation(match.hit, pos)
		return MDStr('')

	@abstractmethod
	def getCallTips(self, pos: Position) -> list[str]:
		return []

	@final
	def getClickableRanges(self, span: Span = ...) -> Iterable[Span]:
		if span is ...:
			span = self.tree.span
		return self.getClickableRangesInternal(span)

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		ranges: list[Span] = []
		for node in self.tree.walkTree():
			if not node.span.overlaps(span):
				continue
			if(ctx := self.getContext(node)) is not None:
				partRanges = ctx.getClickableRanges(node)
				if partRanges:
					ranges.extend(partRanges)
		return ranges

	def onIndicatorClicked(self, pos: Position) -> None:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				ctx.onIndicatorClicked(match.hit, pos)

	@property
	def defaultWordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def getWordCharacters(self, pos: Position) -> Optional[str]:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				if (wordCharacters := ctx.getWordCharacters(match.hit, pos)) is not None:
					return wordCharacters

		return self.defaultWordCharacters

	def getAutoCompletionWordSeparators(self, pos: Position) -> list[str]:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				return ctx.getAutoCompletionWordSeparators(match.hit, pos)
		return []


__contextProviders: dict[Type[Node], Type[ContextProvider]] = {}
registerContextProvider = Decorator(AddToDictDecorator(__contextProviders))
getContextProviderCls = IfKeyIssubclassGetter(__contextProviders)


def getContextProvider(node: _TNode, text: bytes) -> Optional[ContextProvider[_TNode]]:
	if (ctxProviderCls := getContextProviderCls(type(node))) is not None:
		return ctxProviderCls(node, text)
	return None


def getContext(node: _TNode, text: bytes) -> Optional[Context[_TNode]]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getContext(node)
	return None


def prepareTree(node: Node, text: bytes, filePath: FilePath, errorsIO: list[GeneralError]) -> None:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		ctxProvider.prepareTree(filePath, errorsIO)


def parseNPrepare(
		text: bytes,
		*,
		filePath: FilePath,
		language: LanguageId,
		schema: Optional[Schema],
		line: int = 0,
		lineStart: int = 0,
		cursor: int = 0,
		cursorOffset: int = 0,
		indexMapper: IndexMapper = None,
		maxIndex: int = None,
		**kwargs
) -> tuple[Optional[Node], list[GeneralError], Optional[ParserBase]]:
	node, errors, parser = parse(
		text,
		filePath=filePath,
		language=language,
		schema=schema,
		line=line,
		lineStart=lineStart,
		cursor=cursor,
		cursorOffset=cursorOffset,
		indexMapper=indexMapper,
		maxIndex=maxIndex,
		**kwargs
	)
	if node is not None:
		prepareTree(node, text, filePath, errorsIO=errors)
	return node, errors, parser


def validateTree(node: Node, text: bytes, errorsIO: list[GeneralError]) -> None:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		ctxProvider.validateTree(errorsIO)


def getSuggestions(node: Node, text: bytes, pos: Position, replaceCtx: str) -> Suggestions:
	"""
	:param node:
	:param text:
	:param pos: cursor position in contextStr
	:param replaceCtx: the string that will be replaced
	:return:
	"""
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getSuggestions(pos, replaceCtx)
	return []


def getDocumentation(node: Node, text: bytes, pos: Position) -> MDStr:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getDocumentation(pos)
	return MDStr('')


def getCallTips(node: Node, text: bytes, pos: Position) -> list[str]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getCallTips(pos)
	return []


def getClickableRanges(node: Node, text: bytes, span: Span = ...) -> Iterable[Span]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getClickableRanges(span)
	return []


def onIndicatorClicked(node: Node, text: bytes, pos: Position) -> None:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.onIndicatorClicked(pos)


def getWordCharacters(node: Node, text: bytes, pos: Position) -> Optional[str]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getWordCharacters(pos)
	return None


def getAutoCompletionWordSeparators(node: Node, text: bytes, pos: Position) -> list[str]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getAutoCompletionWordSeparators(pos)
	return []


__all__ = [
	'createErrorMsg',
	'errorMsg',
	'Suggestion',
	'Suggestions',
	'CtxInfo',
	'Context',
	'AddContextToDictDecorator',
	'Match',
	'ContextProvider',
	'registerContextProvider',
	'getContextProviderCls',
	'getContextProvider',
	'getContextProvider',
	'getContext',
	'prepareTree',
	'parseNPrepare',
	'validateTree',
	'getSuggestions',
	'getDocumentation',
	'getCallTips',
	'getClickableRanges',
	'onIndicatorClicked',
	'getWordCharacters',
	'getAutoCompletionWordSeparators',
]