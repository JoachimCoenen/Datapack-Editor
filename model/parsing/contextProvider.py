from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Generic, TypeVar, Iterable, Optional, Type, final

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLStr, Decorator
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from model.parsing.tree import Node
from model.utils import Span, Position, GeneralError

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
	def getDocumentation(self, node: _TNode, pos: Position) -> HTMLStr:
		pass  # return defaultDocumentationProvider(node)

	@abstractmethod
	def getClickableRanges(self, node: _TNode) -> Optional[Iterable[Span]]:
		pass

	@abstractmethod
	def onIndicatorClicked(self, node: _TNode, pos: Position, window: QWidget) -> None:
		pass


@dataclass
class Match(Generic[_TNode]):
	before: Optional[_TNode]
	hit: Optional[_TNode]
	after: Optional[_TNode]
	contained: list[_TNode]


class ContextProvider(Generic[_TNode], ABC):
	def __init__(self, tree: _TNode, text: str):
		self.tree: _TNode = tree
		self.text: str = text

	@abstractmethod
	def getBestMatch(self, pos: Position) -> Match[_TNode]:
		pass

	@abstractmethod
	def getContext(self, node: _TNode) -> Optional[Context]:
		pass

	@abstractmethod
	def prepareTree(self) -> list[GeneralError]:
		pass

	@abstractmethod
	def validateTree(self) -> list[GeneralError]:
		pass

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
		return []

	def getDocumentation(self, pos: Position) -> HTMLStr:
		match = self.getBestMatch(pos)
		if match.hit is not None:
			if (ctx := self.getContext(match.hit)) is not None:
				return ctx.getDocumentation(match.hit, pos)
		return HTMLStr('')

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


def getContextProvider(node: _TNode, text: str) -> Optional[ContextProvider[_TNode]]:
	if (ctxProviderCls := getContextProviderCls(type(node))) is not None:
		return ctxProviderCls(node, text)
	return None

# def defaultDocumentationProvider(node: Node) -> HTMLStr:
# 	if doc := node.documentation:
# 		return HTMLifyMarkDownSubSet(doc)
# 	return HTMLStr('')

__all__ = [
	'Suggestion',
	'Suggestions',
	'Context',
	'ContextProvider',
	'registerContextProvider',
	'getContextProviderCls',
	'getContextProvider',
]