from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, TYPE_CHECKING, TypeVar, NewType, Protocol, Generic, Type, Optional, Callable, Collection

from cat.utils import CachedProperty
from cat.utils.collections_ import AddToDictDecorator
from cat.utils.graphs import collectAndSemiTopolSortAllNodes3
from cat.utils.logging_ import logError
from base.model.parsing.tree import Node
from base.model.utils import LanguageId

_TNode = TypeVar('_TNode', bound=Node)
_TStyler = TypeVar('_TStyler', bound='CatStyler')

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
	number =           enum.auto()
	special_constant = enum.auto()  # e.g. true, false, null, ...
	key1 =             enum.auto()  # in key-value pairs. e.g. JSON
	key2 =             enum.auto()
	content_locator =  enum.auto()  # e.g. ResourceLocation, TLTypeLiteral, ...
	type =             enum.auto()  # e.g. int, string, dict, bool, ...
	operator =         enum.auto()
	special1 =         enum.auto()
	special2 =         enum.auto()
	error =            enum.auto()
	invalid =          enum.auto()

	xml_tag =          enum.auto()
	xml_attribute =    enum.auto()


class _CommonStyleIdsPlaceHolder(StyleIdEnum):
	pass  # intentionally empty


class StylingFunc(Protocol):
	def __call__(self, span: slice, style: StyleId) -> None:
		...


@dataclass
class CatStyler(Generic[_TNode], ABC):
	ctx: StylerCtx
	innerStylers: dict[LanguageId, CatStyler]
	offset: StyleId

	setStyling: StylingFunc = field(init=False)

	def __post_init__(self) -> None:
		self.setStyling = self.ctx.setStylingUtf8
		if self.usesCommonStyleIds():
			self.offset = DEFAULT_STYLE_ID

	@classmethod
	def create(cls: Type[_TStyler], ctx: StylerCtx, innerStylers: dict[LanguageId, CatStyler], offset: StyleId) -> _TStyler:
		return cls(ctx, innerStylers, offset)

	@classmethod
	def usesCommonStyleIds(cls) -> bool:
		""" override when CommonStyleIds are used"""
		return False

	@classmethod
	@abstractmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		pass

	@property
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		if self.usesCommonStyleIds():
			return _CommonStyleIdsPlaceHolder
		else:
			raise NotImplementedError("styleIdEnum")

	@property
	def localStylesCount(self) -> int:
		return len(self.styleIdEnum)

	@abstractmethod
	def styleNode(self, node: _TNode) -> int:
		pass

	def styleForeignNode(self, node: Node) -> int:
		self.ctx.setForeignLanguage(node.span.slice, node.language)
		styler = self.innerStylers.get(type(node).language)
		if styler is not None:
			self.setStyling(slice(node.span.start.index, node.span.start.index), self.offset)
			with styler:
				result = styler.styleNode(node)
				self.setStyling(slice(result, node.span.end.index), styler.offset)
			return node.span.end.index
		return node.span.start.index

	def styleStructuredNodeChildNodes(self, node: Node, baseStyle: StyleId) -> int:
		return self.styleStructuredNode(node, node.children, baseStyle, self.styleNode)

	def styleStructuredNodeForeignNodes(self, node: Node, baseStyle: StyleId) -> int:
		return self.styleStructuredNode(node, node.foreignNodes, baseStyle, self.styleForeignNode)

	def styleStructuredNode(self, node: Node, children: Collection[Node], baseStyle: StyleId, styleChildFunc: Callable[[Node], int]) -> int:
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

	@CachedProperty
	def localStyles(self) -> dict[str, StyleId]:
		styles = {
			styleId.name: self.offset + styleId.value
			for styleId in self.styleIdEnum
		}
		return styles

	@property
	def allStylesIds(self) -> dict[str, StyleId]:
		allStylesIds = {}
		for language, styler in self.innerStylers.items():
			innerStyles = styler.localStyles
			for name, styleId in innerStyles.items():
				allStylesIds[f'{language}:{name}'] = styleId
		return allStylesIds

	def __enter__(self) -> None:
		self.ctx.defaultStyles.append(self.ctx.defaultStyle)
		self.ctx.defaultStyle = self.offset

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


def createStyler(cls: Type[_TStyler], language: LanguageId, stylerCtx: StylerCtx) -> _TStyler:
	def getDirectInnerLanguages(base: tuple[LanguageId, Optional[Type[CatStyler]]]) -> list[tuple[LanguageId, Optional[Type[CatStyler]]]]:
		return () if base[1] is None else [(iLang, getStylerCls(iLang)) for iLang in base[1].localInnerLanguages()]

	sortedLanguageStylers = collectAndSemiTopolSortAllNodes3([(language, cls)], getDirectInnerLanguages)

	allStylers: dict[LanguageId, CatStyler] = {}

	offset = len(CommonStyleIds)
	for innerLanguage, stylerCls in sortedLanguageStylers:
		if stylerCls is None:
			logError(f"CatStyler: No Styler found for language {innerLanguage!r} while creating inner stylers for {cls}")
		else:
			allStylers[innerLanguage] = styler = stylerCls.create(stylerCtx, allStylers, StyleId(offset))
			offset += styler.localStylesCount

	return allStylers[language]


__allCatStylers: dict[LanguageId, Type[CatStyler]] = {}

registerStyler: AddToDictDecorator[LanguageId, Type[CatStyler]] = AddToDictDecorator(__allCatStylers)


def getStylerCls(language: LanguageId) -> Optional[Type[CatStyler]]:
	return __allCatStylers.get(language)


def getStyler(language: LanguageId, stylerCtx: StylerCtx) -> Optional[CatStyler]:
	stylerCls = getStylerCls(language)
	if stylerCls is None:
		return None
	styler = createStyler(stylerCls, language, stylerCtx)
	return styler


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
