from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Generic, TypeVar, Iterable, Optional, Type, final, Protocol

from PyQt5.QtWidgets import QWidget

from Cat.utils import Decorator
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from model.parsing.parser import parse, IndexMapper
from model.parsing.tree import Node, Schema
from model.utils import Span, Position, GeneralError, MDStr, LanguageId

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


class StylingFunc(Protocol):
	def call(self, length: int, style: int) -> None:
		...


class ContextProvider(Generic[_TNode], ABC):
	def __init__(self, tree: _TNode, text: bytes):
		self.tree: _TNode = tree
		self.text: bytes = text

	# @classmethod
	# @abstractmethod
	# def parse(cls, text: str, errorsIO: list[GeneralError]) -> _TNode:
	# 	pass
	#
	# @abstractmethod
	# def getStyles(self) -> dict[str, int]:
	# 	pass
	#
	# @abstractmethod
	# def styleText(self, start: int, end: int, startStyling: Callable[[int], None], setStyle: StylingFunc):
	# 	pass

	@abstractmethod
	def getBestMatch(self, pos: Position) -> Match[_TNode]:
		pass

	@abstractmethod
	def getContext(self, node: _TNode) -> Optional[Context]:
		pass

	@abstractmethod
	def prepareTree(self) -> list[GeneralError]:
		pass

	def validateTree(self, errorsIO: list[GeneralError]) -> None:
		if (ctx := self.getContext(self.tree)) is not None:
			ctx.validate(self.tree, errorsIO)

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
		pass

	@final
	def getClickableRanges(self, span: Span = ...) -> Iterable[Span]:
		if span is ...:
			span = self.tree.span
		return self.getClickableRangesInternal(span)

	@abstractmethod
	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		return ()

	def onIndicatorClicked(self, pos: Position, window: QWidget) -> None:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				ctx.onIndicatorClicked(match.hit, pos, window)


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
	if node is not None and (ctxProvider := getContextProvider(node, text)) is not None:
		errors2 = ctxProvider.prepareTree()
		errors.extend(errors2)
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
]
