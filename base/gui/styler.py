from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from typing import Mapping, TYPE_CHECKING, TypeVar, NewType, Protocol, Generic, Type, Optional

from Cat.utils import CachedProperty
from Cat.utils.graphs import semiTopologicalSort
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

	def __post_init__(self):
		self.setStyling = self.ctx.setStylingUtf8

	@classmethod
	@abstractmethod
	def language(cls) -> LanguageId:
		pass

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

	# @classmethod
	# @abstractmethod
	# def localInnerStylers(cls) -> list[Type[CatStyler]]:
	# 	pass

	# @classmethod
	# def createStyler(cls, setStyling: StylingFunc):
	# 	# def collectAllInnerStylers(cls, setStyling: StylingFunc):
	# 	toHandle: deque[Type[CatStyler]] = deque()
	#
	# 	allInnerStylerTypes: list[Type[CatStyler]] = []
	# 	stylerTypesByLang: dict[str, Type[CatStyler]] = {}
	# 	innerLanguagesByLang: dict[str, list[str]] = {}
	#
	# 	toHandle.append(cls)
	# 	while toHandle:
	# 		stylerCls = toHandle.pop()
	# 		if stylerCls.language() in stylerTypesByLang:
	# 			continue
	# 		allInnerStylerTypes.append(stylerCls)
	# 		stylerTypesByLang[stylerCls.language()] = stylerCls
	# 		localInnerStylers = stylerCls.localInnerStylers()
	#
	# 		innerLanguagesByLang[stylerCls.language()] = [l.language() for l in localInnerStylers]
	# 		toHandle.extend(localInnerStylers)
	#
	# 	localInnerStylersByLang = {
	# 		lang: [stylerTypesByLang[il] for il in innerLangs]
	# 		for lang, innerLangs in innerLanguagesByLang.items()
	# 	}
	#
	# 	sortedStylerTypes: list[Type[CatStyler]] = semiTopologicalSort(
	# 		cast(Type[CatStyler], cls),
	# 		allInnerStylerTypes,
	# 		getDestinations=lambda x: localInnerStylersByLang[x.language()],
	# 		getId=lambda x: x.language()
	# 	)
	#
	# 	allStylers: OrderedDict[str, CatStyler] = OrderedDict()
	#
	# 	offset = 0
	# 	for stylerCls in sortedStylerTypes:
	# 		styler = stylerCls(
	# 			setStyling,
	# 			allStylers,
	# 			offset
	# 		)
	# 		allStylers[styler.language()] = styler
	#
	# 	return list(allStylers.values())[0]

	@classmethod
	def _getStyler(cls, language: LanguageId) -> Optional[Type[CatStyler]]:
		if language == cls.language():
			return cls
		else:
			return getStylerCls(language)

	@classmethod
	def _allInnerLanguages(cls) -> list[LanguageId]:
		# def collectAllInnerStylers(cls, setStyling: StylingFunc):
		toHandle: deque[LanguageId] = deque()

		allInnerLangs: list[LanguageId] = []
		seenLangs: set[LanguageId] = set()
		# stylerTypesByLang: dict[str, Type[CatStyler]] = {}
		innerLanguagesByLang: dict[LanguageId, list[LanguageId]] = {}

		toHandle.append(cls.language())
		while toHandle:
			language = toHandle.pop()
			if language in seenLangs:
				continue
			seenLangs.add(language)
			allInnerLangs.append(language)

			stylerCls = cls._getStyler(language)
			if stylerCls is not None:
				localInnerLangs = stylerCls.localInnerLanguages()
				innerLanguagesByLang[language] = localInnerLangs
				toHandle.extend(localInnerLangs)

		sortedLanguages: list[LanguageId] = semiTopologicalSort(
			[cls.language()],
			allInnerLangs,
			getDestinations=lambda x: innerLanguagesByLang.get(x, ()),
			getId=lambda x: x
		)

		return sortedLanguages

	@classmethod
	def createStyler(cls: Type[_TStyler], stylerCtx: StylerCtx) -> _TStyler:
		sortedLanguages = cls._allInnerLanguages()
		allStylers: OrderedDict[LanguageId, CatStyler] = OrderedDict()

		offset = 0
		for language in sortedLanguages:
			stylerCls = cls._getStyler(language)
			if stylerCls is None:
				logError(f"CatStyler: No Styler found for language {language!r} while creating inner stylers for {cls}")
			else:
				styler = stylerCls(
					stylerCtx,
					allStylers,
					offset
				)
				offset += styler.localStylesCount
				allStylers[styler.language()] = styler

		return list(allStylers.values())[0]

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

	def __enter__(self):
		self.ctx.defaultStyles.append(self.ctx.defaultStyle)
		self.ctx.defaultStyle = self.offset

	def __exit__(self, exc_type, exc_val, exc_tb):
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


def registerStyler(stylerCls: Type[CatStyler]):
	__allCatStylers[stylerCls.language()] = stylerCls
	return stylerCls


def getStylerCls(language: LanguageId) -> Optional[Type[CatStyler]]:
	return __allCatStylers.get(language)


def getStyler(language: LanguageId, stylerCtx: StylerCtx) -> Optional[CatStyler]:
	stylerCls = getStylerCls(language)
	if stylerCls is None:
		return None
	styler = stylerCls.createStyler(stylerCtx)
	return styler


def allStylers() -> Mapping[LanguageId, Type[CatStyler]]:
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
	'allStylers',
	'StylerCtx',
]
