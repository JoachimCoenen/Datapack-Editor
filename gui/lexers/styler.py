from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque, OrderedDict
from dataclasses import dataclass
from typing import TypeVar, NewType, Protocol, Generic, Type, Optional

from Cat.utils.graphs import semiTopologicalSort
from Cat.utils.logging_ import logError
from model.parsing.tree import Node
from model.utils import LanguageId

_TNode = TypeVar('_TNode', bound=Node)
_TStyler = TypeVar('_TStyler', bound='CatStyler')

StyleId = NewType('StyleId', int)

DEFAULT_STYLE_ID: StyleId = StyleId(0)


class StylingFunc(Protocol):
	def __call__(self, span: slice, style: StyleId) -> None:
		...


@dataclass
class CatStyler(Generic[_TNode], ABC):
	setStyling: StylingFunc
	# innerStylers: dict[Type[Node], CatStyler]
	innerStylers: dict[str, CatStyler]
	offset: int

	@classmethod
	@abstractmethod
	def language(cls) -> LanguageId:
		pass

	@property
	@abstractmethod
	def localStylesCount(self) -> int:
		pass

	# @classmethod
	# @abstractmethod
	# def localInnerStylers(cls) -> list[Type[CatStyler]]:
	# 	pass

	@classmethod
	@abstractmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		pass

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
			cls.language(),
			allInnerLangs,
			getDestinations=innerLanguagesByLang.get,
			getId=lambda x: x
		)

		return sortedLanguages

	@classmethod
	def createStyler(cls: Type[_TStyler], setStyling: StylingFunc) -> _TStyler:
		sortedLanguages = cls._allInnerLanguages()
		allStylers: OrderedDict[LanguageId, CatStyler] = OrderedDict()

		offset = 0
		for language in sortedLanguages:
			stylerCls = cls._getStyler(language)
			if stylerCls is None:
				logError(f"CatStyler: No Styler found for language {language!r} while creating inner stylers for {cls}")
			styler = stylerCls(
				setStyling,
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
			return styler.styleNode(node)
		else:
			return node.span.start.index

	@property
	@abstractmethod
	def localStyles(self) -> dict[str, StyleId]:
		pass

	@property
	def allStyles(self) -> dict[str, StyleId]:
		allStyles = {}
		for language, styler in self.innerStylers.items():
			innerStyles = styler.localStyles
			for name, styleId in innerStyles.items():
				allStyles[f'{language}:{name}'] = styleId
		return allStyles


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


def getStyler(language: LanguageId, setStyling: StylingFunc) -> Optional[CatStyler]:
	stylerCls = getStylerCls(language)
	if stylerCls is None:
		return None
	styler = stylerCls.createStyler(setStyling)
	return styler

