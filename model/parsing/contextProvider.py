from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, Iterable, Optional, Type, final

from PyQt5.QtWidgets import QWidget

from Cat.utils import Decorator
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from model.parsing.parser import parse, IndexMapper
from model.parsing.tree import Node, Schema
from model.utils import LanguageId, MDStr, Span, Position, GeneralError

_TNode = TypeVar('_TNode', bound=Node)


Suggestion = str  # for now...
Suggestions = list[Suggestion]


class Context(Generic[_TNode]):
	def prepare(self, node: _TNode, errorsIO: list[GeneralError]) -> None:
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
		pass

	@abstractmethod
	def getDocumentation(self, node: _TNode, pos: Position) -> MDStr:
		pass  # return defaultDocumentationProvider(node)

	def getCallTips(self, node: _TNode, pos: Position) -> list[str]:
		return []

	@abstractmethod
	def getClickableRanges(self, node: _TNode) -> Optional[Iterable[Span]]:
		pass

	@abstractmethod
	def onIndicatorClicked(self, node: _TNode, pos: Position, window: QWidget) -> None:
		pass

	# @abstractmethod
	def getWordCharacters(self, node: _TNode, pos: Position) -> Optional[str]:
		return None  #  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	# @abstractmethod
	def getAutoCompletionWordSeparators(self, node: _TNode, pos: Position) -> list[str]:
		return []  # ['.', '::', '->']


_TContext = TypeVar('_TContext', bound=Context)


class AddContextFunc(Protocol[_TContext]):
	def __call__(self, func: Type[_TContext]) -> Type[_TContext]:
		pass


class AddContextToDictDecorator(AddToDictDecorator[str, _TContext], Generic[_TContext]):
	def __call__(self, key: str, *, forceOverride: bool = False, **kwargs) -> AddContextFunc[_TContext]:
		addContextInner = super(AddContextToDictDecorator, self).__call__(key, forceOverride)

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

	def prepareTree(self) -> list[GeneralError]:
		errorsIO = []
		for node in self.tree.walkTree():
			if (ctx := self.getContext(node)) is not None:
				ctx.prepare(node, errorsIO)
		return errorsIO

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		for node in self.tree.walkTree():
			if (ctx := self.getContext(node)) is not None:
				ctx.validate(node, errorsIO)

	# @abstractmethod
	# def validate(self, data: _TNode, errorsIO: list[GeneralError]) -> None:
	# 	return None

	@abstractmethod
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

	@abstractmethod
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

	def onIndicatorClicked(self, pos: Position, window: QWidget) -> None:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				ctx.onIndicatorClicked(match.hit, pos, window)

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


def prepareTree(node: Node, text: bytes) -> list[GeneralError]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.prepareTree()
	return []


def parseNPrepare(
		text: bytes,
		*,
		language: LanguageId,
		schema: Optional[Schema],
		line: int = 0,
		lineStart: int = 0,
		cursor: int = 0,
		cursorOffset: int = 0,
		indexMapper: IndexMapper = None,
		**kwargs
) -> tuple[Optional[Node], list[GeneralError]]:
	node, errors = parse(
		text,
		language=language,
		schema=schema,
		line=line,
		lineStart=lineStart,
		cursor=cursor,
		cursorOffset=cursorOffset,
		indexMapper=indexMapper,
		**kwargs
	)
	if node is not None:
		errors += prepareTree(node, text)
	return node, errors


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


def onIndicatorClicked(node: Node, text: bytes, pos: Position, window: QWidget) -> None:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.onIndicatorClicked(pos, window)


def getWordCharacters(node: Node, text: bytes, pos: Position) -> Optional[str]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getWordCharacters(pos)
	return None


def getAutoCompletionWordSeparators(node: Node, text: bytes, pos: Position) -> list[str]:
	if (ctxProvider := getContextProvider(node, text)) is not None:
		return ctxProvider.getAutoCompletionWordSeparators(pos)
	return []


__all__ = [
	'Suggestion',
	'Suggestions',
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