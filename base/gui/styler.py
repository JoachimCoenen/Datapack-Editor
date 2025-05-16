from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, TYPE_CHECKING, NewType, Protocol, Type, Optional, Callable, Collection

from cat.utils.collections_ import AddToDictDecorator
from cat.utils.logging_ import logError
from base.model.parsing.tree import Node
from base.model.utils import LanguageId


ENABLE_LOGGING_STYLER_NOT_FOUND: bool = False

StyleId = NewType('StyleId', int)

DEFAULT_STYLE_ID: StyleId = StyleId(0)


if TYPE_CHECKING:
	class StyleIdEnum(StyleId, enum.Enum):
		"""Enum where members are also (and must be) StyleIds"""
else:
	class StyleIdEnum(StyleId.__supertype__, enum.Enum):
		"""Enum where members are also (and must be) StyleIds"""


class CommonStyleIds(StyleIdEnum):
	default = DEFAULT_STYLE_ID
	comment =          enum.auto()
	keyword =          enum.auto()  # if | else | return
	string =           enum.auto()
	string2 =          enum.auto()
	number =           enum.auto()
	special_constant = enum.auto()  # e.g. true, false, null, ...
	key1 =             enum.auto()  # in key-value pairs. e.g. JSON
	key2 =             enum.auto()
	content_locator =  enum.auto()  # e.g. ResourceLocation, TLTypeLiteral, ...

	variable =         enum.auto()  # a variable or function argument
	function =         enum.auto()  # a function or method
	parameter =        enum.auto()  # a function parameter
	type =             enum.auto()  # e.g. int, string, dict, bool, ...
	operator =         enum.auto()
	special1 =         enum.auto()
	special2 =         enum.auto()

	error =            enum.auto()
	invalid =          enum.auto()

	xml_tag =          enum.auto()
	xml_attribute =    enum.auto()


class StylingFunc(Protocol):
	def __call__(self, span: slice, style: StyleId) -> None:
		...


@dataclass
class CatStyler[N: Node](ABC):
	ctx: StylerCtx
	stylersCache: dict[LanguageId, CatStyler | None] = field(default_factory=dict, init=False)

	setStyling: StylingFunc = field(init=False)

	def __post_init__(self) -> None:
		self.setStyling = self.ctx.setStylingUtf8

	@classmethod
	def create[_TStyler: CatStyler](cls: Type[_TStyler], ctx: StylerCtx) -> _TStyler:
		return cls(ctx)

	def _getStyler(self, language: LanguageId) -> CatStyler | None:
		if (styler := self.stylersCache.get(language)) is not None:
			return styler

		if language in self.stylersCache:
			return styler  # we already looked for a styler previously and were unsuccessful

		self.stylersCache[language] = styler = getStyler(language, self.ctx)
		if styler is not None:
			styler.stylersCache = self.stylersCache
		return styler

	@abstractmethod
	def styleNode(self, node: N) -> int:
		pass

	def styleForeignNode(self, node: Node) -> int:
		self.ctx.setForeignLanguage(node.span.slice, node.language)
		styler = self._getStyler(type(node).language)
		if styler is not None:
			self.setStyling(slice(node.span.start.index, node.span.start.index), DEFAULT_STYLE_ID)
			with styler:
				result = styler.styleNode(node)
				self.setStyling(slice(result, node.span.end.index), DEFAULT_STYLE_ID)
			return node.span.end.index
		return node.span.start.index

	def styleStructuredNodeChildNodes(self, node: Node, baseStyle: StyleId) -> int:
		return self.styleStructuredNode(node, node.children, baseStyle, self.styleNode)

	def styleStructuredNodeForeignNodes(self, node: Node, baseStyle: StyleId) -> int:
		return self.styleStructuredNode(node, node.foreignNodes, baseStyle, self.styleForeignNode)

	def styleStructuredNode[N2: Node](self, node: Node, children: Collection[N2 | None], baseStyle: StyleId, styleChildFunc: Callable[[N2], int]) -> int:
		if not children:
			self.setStyling(node.span.slice, baseStyle)
		else:
			lastIdx = node.span.start.index
			for child in children:
				if child is not None:
					self.setStyling(slice(lastIdx, child.span.start.index), baseStyle)
					lastIdx = styleChildFunc(child)
			self.setStyling(slice(lastIdx, node.span.end.index), baseStyle)
		return node.span.end.index

	def __enter__(self) -> None:
		self.ctx.defaultStyles.append(self.ctx.defaultStyle)
		self.ctx.defaultStyle = DEFAULT_STYLE_ID

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self.ctx.defaultStyle = self.ctx.defaultStyles.pop()

	# def setStyling(self, length: int, style: int) -> None:
	# 	assert (length >= 0)
	# 	doc = self.document()
	# 	if doc is not None:
	# 		text = doc.content[self._lastStylePos:self._lastStylePos + length]
	# 		self._lastStylePos += length
	# 		length = len(bytearray(text, "utf-8"))
	#
	# 	super(LexerJson, self).setStyling(length, style)


__allCatStylers: dict[LanguageId, Type[CatStyler]] = {}

registerStyler: AddToDictDecorator[LanguageId, Type[CatStyler]] = AddToDictDecorator(__allCatStylers)


def getStylerCls(language: LanguageId) -> Optional[Type[CatStyler]]:
	return __allCatStylers.get(language)


def getStyler(language: LanguageId, stylerCtx: StylerCtx) -> Optional[CatStyler]:
	stylerCls = getStylerCls(language)
	if stylerCls is None:
		if ENABLE_LOGGING_STYLER_NOT_FOUND:
			logError(f"CatStyler: No Styler found for language {language!r}")
		return None
	else:
		return stylerCls.create(stylerCtx)


def getAllStylers() -> Mapping[LanguageId, Type[CatStyler]]:
	return __allCatStylers


@dataclass
class StylerCtx(ABC):
	defaultStyle: StyleId
	defaultStyles: list[StyleId] = field(init=False, default_factory=list)
	start: int
	"start index of the range to be styled."
	end: int
	"end index of the range to be styled."

	@abstractmethod
	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		pass

	@abstractmethod
	def setForeignLanguage(self, span: slice, languageId: LanguageId) -> None:
		pass


__all__ = [
	'StyleId',
	'DEFAULT_STYLE_ID',
	'StyleIdEnum',
	'CommonStyleIds',
	'CatStyler',
	'registerStyler',
	'getStylerCls',
	'getStyler',
	'getAllStylers',
	'StylerCtx',
]
