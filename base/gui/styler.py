from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, TYPE_CHECKING, TypeVar, NewType, Protocol, Generic, Type, Optional

from Cat.utils import CachedProperty
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.graphs import collectAndSemiTopolSortAllNodes3
from Cat.utils.logging_ import logError
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

	@classmethod
	def create(cls: Type[_TStyler], ctx: StylerCtx, innerStylers: dict[LanguageId, CatStyler], offset: StyleId) -> _TStyler:
		return cls(ctx, innerStylers, offset)

	@classmethod
	@abstractmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		pass

	@property
	@abstractmethod
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		raise NotImplementedError("styleIdEnum")

	@property
	def localStylesCount(self) -> int:
		return len(self.styleIdEnum)

	@abstractmethod
	def styleNode(self, node: _TNode) -> int:
		pass

	def styleForeignNode(self, node: Node) -> int:
		styler = self.innerStylers.get(type(node).language)
		if styler is not None:
			self.setStyling(slice(node.span.start.index, node.span.start.index), self.offset)
			with styler:
				result = styler.styleNode(node)
				self.setStyling(slice(result, node.span.end.index), styler.offset)
				return node.span.end.index
		else:
			return node.span.start.index

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

	offset = 0
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

	@abstractmethod
	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		pass


__all__ = [
	'StyleId',
	'DEFAULT_STYLE_ID',
	'StyleIdEnum',
	'CatStyler',
	'registerStyler',
	'getStylerCls',
	'getStyler',
	'getAllStylers',
	'StylerCtx',
]
