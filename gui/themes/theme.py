from __future__ import annotations

import importlib
import os
import warnings
from dataclasses import dataclass, field, fields, Field, is_dataclass
from operator import attrgetter
from types import ModuleType
from typing import TypeVar, Generic, Union, Optional, Iterable

from PyQt5.QtGui import QFont, QColor

from Cat.extensions import processRecursively
from Cat.utils import getExePath
from Cat.utils.graphs import getCycles, collectAndSemiTopolSortAllNodes
from Cat.utils.logging_ import logDebug, logWarning
from model.utils import LanguageId

_TT = TypeVar('_TT')


# @dataclass
class NotSet(Generic[_TT]):
	def __init__(self, default: _TT):
		self.default: _TT = default


@dataclass
class StyleFont:
	family: Union[str, NotSet[str]] = NotSet('Consolas')  # NotSet('Courier New')
	styleHint: Union[QFont.StyleHint, NotSet[QFont.StyleHint]] = NotSet(QFont.Monospace)
	pointSize: Union[int, NotSet[int]] = NotSet(8)
	bold: Union[bool, NotSet[bool]] = NotSet(False)
	italic: Union[bool, NotSet[bool]] = NotSet(False)
	underline: Union[bool, NotSet[bool]] = NotSet(False)
	overline: Union[bool, NotSet[bool]] = NotSet(False)
	strikeOut: Union[bool, NotSet[bool]] = NotSet(False)


@dataclass
class Style:
	foreground: Optional[QColor] = None
	background: Optional[QColor] = None
	font: Optional[StyleFont] = None


DEFAULT_STYLE_STYLE = Style(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	font=StyleFont("Consolas", QFont.Monospace, 8)
)


# def mergeFont(font1: StyleFont, font2: StyleFont) -> StyleFont:
# 	aField: Field
# 	values = {}
# 	for aField in fields(StyleFont):
# 		propName: str = aField.name
# 		value = getattr(font2, propName)
# 		if isinstance(value, NotSet):
# 			value = getattr(font1, propName)
# 		values[propName] = value
#
# 	return StyleFont(**values)
#
#
# def _mergeSimpleVal(val1: _TT, val2: _TT) -> _TT:
# 	if val2 is None or isinstance(val2, NotSet):
# 		return val1
# 	return val2
#
#
# def mergeFont2(font1: Optional[StyleFont], font2: Optional[StyleFont]) -> Optional[StyleFont]:
# 	aField: Field
# 	values = {}
# 	for aField in fields(StyleFont):
# 		propName: str = aField.name
# 		value = _mergeSimpleVal(getattr(font1, propName), getattr(font2, propName))
# 		values[propName] = value
#
# 	return StyleFont(**values)


def _getWithDefaultsFilled(obj: _TT) -> _TT:
	aField: Field
	values = {}
	for aField in fields(obj):
		if not aField.init:
			continue
		propName: str = aField.name
		value = getattr(obj, propName)
		if isinstance(value, NotSet):
			value = value.default
		if is_dataclass(value):
			value = _getWithDefaultsFilled(value)
		values[propName] = value

	return type(obj)(**values)


def _mergeDataclass(val1: _TT, val2: _TT) -> _TT:
	aField: Field
	values = {}
	for aField in fields(val2):
		if not aField.init:
			continue
		propName: str = aField.name
		value = mergeVal(getattr(val1, propName), getattr(val2, propName))
		values[propName] = value

	return type(val2)(**values)


def mergeVal(val1: _TT, val2: _TT) -> _TT:
	if val2 is None or isinstance(val2, NotSet):
		return val1
	elif val1 is None or isinstance(val1, NotSet):
		return val2
	elif is_dataclass(val1):
		return _mergeDataclass(val1, val2)
	else:
		return val2


def mergeStyle(style1: Style, style2: Style) -> Style:
	mergedStyle = _mergeDataclass(style1, style2)
	return mergedStyle
	# foreground = mergeSimpleVal(style1.foreground, style2.foreground)
	# background = mergeSimpleVal(style1.background, style2.background)
	#
	# if style2.font is None:
	# 	font = style1.font
	# elif style1.font is None:
	# 	font = style2.font
	# else:
	# 	font = mergeFont(style1.font, style2.font)
	#
	# return Style(
	# 	foreground=foreground,
	# 	background=background,
	# 	font=font
	# )


@dataclass
class ColorScheme:
	name: str
	fallback: list[str]

	localFallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)
	allFallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)

	defaultStyle: Style = DEFAULT_STYLE_STYLE

	# styles: dict[LanguageId, dict[str, Style]] = field(default_factory=dict)

	def deferredInit1(self) -> None:
		"""
		Must be called *after* all ColorSchemes are loaded or reloaded to initialize the localFallbackSchemes.
		Must be used like this:
			for cs in allColorSchemes:
				cs.deferredInit1()

			_breakCycles(allColorSchemes)

			for cs in allColorSchemes:
				cs.deferredInit2()

		see: initAllColorSchemes()
		"""
		for fbName in self.fallback:
			fbScheme = getColorScheme(fbName)
			if fbScheme is not None:
				self.localFallbackSchemes.append(fbScheme)

	def deferredInit2(self) -> None:
		"""
		Must be called *after* ColorSchemes.deferredInit1() has been run for all ColorSchemes to initialize the allFallbackSchemes.
		Must be used like this:
			for cs in allColorSchemes:
				cs.deferredInit1()

			_breakCycles(allColorSchemes)

			for cs in allColorSchemes:
				cs.deferredInit2()

		see: initAllColorSchemes()
		"""
		allFbs = collectAndSemiTopolSortAllNodes(self, attrgetter('localFallbackSchemes'), attrgetter('name'))
		self.allFallbackSchemes = allFbs

	# def getLocalStyles(self, language: LanguageId) -> Optional[dict[str, Style]]:
	# 	return self.styles.get(language)
	#
	# def getStyles(self, language: LanguageId) -> Optional[dict[str, Style]]:
	# 	styles = self.getLocalStyles(language)
	# 	if styles is not None:
	# 		return styles
	#
	# 	for fbScheme in self.allFallbackSchemes:
	# 		styles = fbScheme.getLocalStyles(language)
	# 		if styles is not None:
	# 			return styles
	#
	# 	return None
	#
	# def getStyle(self, language: LanguageId, style: str) -> Optional[Style]:
	# 	styles = self.getStyles(language)
	# 	if styles is None:
	# 		return None
	# 	return styles.get(style)

	styles2: dict[LanguageId, Styles] = field(default_factory=dict)

	def getLocalStyles2(self, language: LanguageId) -> Optional[Styles]:
		return self.styles2.get(language)

	def getStyles2(self, language: LanguageId, outerStyles: Styles = ...) -> Optional[StylesProxy]:
		styles = self.getLocalStyles2(language)
		if outerStyles is ...:
			outerStyles = styles

		if styles is not None:
			return StylesProxy(self, language, styles, outerStyles)

		for fbScheme in self.allFallbackSchemes:
			styles = fbScheme.getLocalStyles2(language)
			if styles is not None:
				return StylesProxy(self, language, styles, outerStyles)

		return None

	def getStyle2(self, language: LanguageId, style: str) -> Optional[Style]:
		styles = self.getStyles2(language)
		if styles is None:
			return None
		return styles.get(style)

	# def getAllStyles(self, language: LanguageId, allStylesIds: Iterable[str]) -> dict[str, Style]:
	# 	styles = self.getStyles2(language)
	# 	styleMap = {}
	# 	if styles is None:
	# 		return {}
	#
	# 	for fullStyleName in allStylesIds:
	# 		lang, styleName = fullStyleName.partition(':')[::2]
	# 		style = self.getStyle(lang, styleName)
	# 		if style is None:
	# 			style = DEFAULT_STYLE_STYLE
	# 		style = styles.modifyStyle(lang, style)
	# 		styleMap[fullStyleName] = style
	#
	# 	return styleMap


# class StylesLike(ABC):
# 	@abstractmethod
# 	def get(self, style: str) -> Optional[Style]:
# 		raise NotImplementedError('StylesLike.get()')
#
# 	@abstractmethod
# 	def getInnerLanguageStyles(self, innerLanguage: LanguageId) -> Optional[StylesLike]:
# 		raise NotImplementedError('StylesLike.getInnerLanguageStyles()')
#
# 	@abstractmethod
# 	def getInnerLanguageStyleModifier(self, innerLanguage: LanguageId) -> Optional[Style]:
# 		raise NotImplementedError('StylesLike.getInnerLanguageStyleModifier()')


@dataclass
class Styles:
	# language: LanguageId

	_styles: dict[str, Style] = field(default_factory=dict)
	innerLanguageStyleModifiers: dict[LanguageId, Style] = field(default_factory=dict)

	def get(self, name: str) -> Optional[Style]:
		return self._styles.get(name)

	# def modifyStyle(self, language: LanguageId, style: Style) -> Style:
	# 	return mergeStyle(style, self.getInnerLanguageStyleModifier(language))

	# def getInnerLanguageStyleModifier(self, innerLanguage: LanguageId) -> Optional[Style]:
	# 	return self.innerLanguageStyleModifiers.get(innerLanguage)


@dataclass
class StylesProxy:
	scheme: ColorScheme
	language: LanguageId
	_styles: Styles
	outerStyles: Optional[Styles]
	_styleModifier: Optional[Style] = field(init=False)

	def __post_init__(self):
		if self.outerStyles is not None:
			self._styleModifier = self.outerStyles.innerLanguageStyleModifiers.get(self.language)
		else:
			self._styleModifier = None

	# @property
	# def _styleModifier(self) -> Optional[Style]:
	# 	if self.outerStyles is not None:
	# 		return self.outerStyles.innerLanguageStyleModifiers.get(self._styles.language)
	# 		# return self.outerStyles.getInnerLanguageStyleModifier(self._styles.language)

	def get(self, styleName: str) -> Optional[Style]:
		style = self._styles.get(styleName)
		if style is None:
			return None
		if self._styleModifier is not None:
			style = mergeStyle(style, self._styleModifier)
		return style

	def getInnerLanguageStyles(self, innerLanguage: LanguageId) -> Optional[StylesProxy]:
		return self.scheme.getStyles2(innerLanguage, self.outerStyles)


_ALL_COLOR_SCHEMES: dict[str, ColorScheme] = {}


def currentColorScheme() -> ColorScheme:
	from settings import applicationSettings
	csName = applicationSettings.appearance.colorScheme
	scheme = _ALL_COLOR_SCHEMES.get(csName)
	if scheme is None:
		scheme = _ALL_COLOR_SCHEMES.get('Default')
	if scheme is None:
		scheme = _ALL_COLOR_SCHEMES.get('None')
	if scheme is None:
		warnings.warn("No Color Schemes available. Not even the 'None' Color Scheme. Adding it now.", RuntimeWarning)
		scheme = addColorScheme(ColorScheme('None', []))
	return scheme


def getColorScheme(name: str) -> Optional[ColorScheme]:
	return _ALL_COLOR_SCHEMES.get(name)


def getAllColorSchemes() -> list[ColorScheme]:
	return list(_ALL_COLOR_SCHEMES.values())


def addColorScheme(cs: ColorScheme, /) -> ColorScheme:
	_ALL_COLOR_SCHEMES[cs.name] = cs
	return cs


def _breakCycles(colorSchemes: Iterable[ColorScheme]):
	cycles = getCycles(_ALL_COLOR_SCHEMES.values(), attrgetter('localFallbackSchemes'), attrgetter('name'))
	if cycles:
		cyclesStr = '\n'.join(f"[{' -> '.join(elem.name for elem in cycle)}]" for cycle in cycles)
		logWarning(
			f"ColorSchemes: {len(cycles)} fallback cycles found: \n{cyclesStr}\n"
			f"Fallbacks will be disabled for all ColorSchemes within these cycles.")

		for cycle in cycles:
			cycleNames = {elem.name for elem in cycle}
			for elem in cycle:
				fbs = list(filter(lambda fb: fb.name not in cycleNames, elem.localFallbackSchemes))
				elem.localFallbackSchemes = fbs


def initAllColorSchemes() -> None:
	"""
	Must be used like this:
		for cs in allColorSchemes:
			cs.deferredInit1()

		_breakCycles(allColorSchemes)

		for cs in allColorSchemes:
			cs.deferredInit2()
	"""
	for cs in _ALL_COLOR_SCHEMES.values():
		cs.deferredInit1()

	_breakCycles(_ALL_COLOR_SCHEMES.values())

	for cs in _ALL_COLOR_SCHEMES.values():
		cs.deferredInit2()


def getColorSchemesDir() -> str:
	colorSchemesDir = os.path.dirname(os.path.abspath(getExePath()))
	colorSchemesDir = os.path.join(colorSchemesDir, 'colorSchemes')
	return colorSchemesDir


def _allColorSchemeModules() -> list[str]:
	csDir = getColorSchemesDir()
	allModulePaths: list[str] = []

	processRecursively(csDir, '/**', allModulePaths.append)

	allModulePaths = [mp.removeprefix(csDir).removesuffix('.py') for mp in allModulePaths if mp.endswith('.py')]
	allModuleNames = ['colorSchemes' + '.'.join(mp.split('/')) for mp in allModulePaths if mp.rpartition('/')[2].startswith("scheme_")]
	return allModuleNames


def _loadColorSchemeModules(names: list[str]) -> dict[str, ModuleType]:
	colorSchemeModules: dict[str, ModuleType] = {}
	for modName in names:
		thisMod = importlib.import_module(modName)
		if getattr(thisMod, 'enabled') is True:
			colorSchemeModules[modName] = thisMod
			logDebug(f"imported colorScheme {modName}")
		else:
			logDebug(f"imported colorScheme {modName}: DISABLED")
	return colorSchemeModules


def _reloadModules(modules: Iterable[ModuleType]):
	for module in modules:
		importlib.reload(module)


def loadAllColorSchemes() -> None:
	_ALL_COLOR_SCHEMES.clear()
	addColorScheme(ColorScheme('None', []))

	colorSchemeModuleNames = _allColorSchemeModules()
	_colorSchemeModules = _loadColorSchemeModules(colorSchemeModuleNames)
	_reloadModules(_colorSchemeModules.values())

	for module in _colorSchemeModules.values():
		module.initPlugin()
	initAllColorSchemes()


def reloadAllColorSchemes() -> None:
	loadAllColorSchemes()
