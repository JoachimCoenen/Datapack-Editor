from __future__ import annotations

import importlib
import importlib.util
import os
import shutil
import sys
import warnings
from dataclasses import dataclass, field, fields, Field, is_dataclass
from operator import attrgetter
from types import ModuleType
from typing import TypeVar, Generic, Union, Optional, Iterable

from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.catWidgetMixins import BaseColors
from Cat.extensions import processRecursively
from Cat.utils import getExePath, openOrCreate
from Cat.utils.graphs import getCycles, collectAndSemiTopolSortAllNodes
from Cat.utils.logging_ import logDebug, logWarning, logInfo
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

	def __or__(self, other: StyleFont) -> StyleFont:
		if not isinstance(other, StyleFont):
			return NotImplemented
		return _mergeDataclass(self, other)

	# def __ior__(self, other: StyleFont) -> StyleFont:
	# 	return self | other


@dataclass
class Style:
	foreground: Optional[QColor] = None
	background: Optional[QColor] = None
	font: Optional[StyleFont] = None

	def __or__(self, other: Style) -> Style:
		if not isinstance(other, Style):
			return NotImplemented
		return _mergeDataclass(self, other)

	# def __ior__(self, other: Style) -> Style:
	# 	return self | other


EMPTY_STYLE_STYLE = Style()


DEFAULT_STYLE_STYLE = Style(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	font=StyleFont("Consolas", QFont.Monospace, 8)
)


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


def mergeVal(val: _TT, overridingVal: _TT) -> _TT:
	if overridingVal is None or isinstance(overridingVal, NotSet):
		return val
	elif val is None or isinstance(val, NotSet):
		return overridingVal
	elif is_dataclass(val):
		return _mergeDataclass(val, overridingVal)
	else:
		return overridingVal


def _mergeDataclass(val: _TT, overridingVal: _TT) -> _TT:
	aField: Field
	values = {}
	for aField in fields(overridingVal):
		if not aField.init:
			continue
		propName: str = aField.name
		value = mergeVal(getattr(val, propName), getattr(overridingVal, propName))
		values[propName] = value

	return type(overridingVal)(**values)


def mergeStyle(style: Style, overridingStyle: Style) -> Style:
	return style | overridingStyle


@dataclass
class ColorScheme:
	name: str
	fallback: list[str]

	localFallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)
	allFallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)

	defaultStyle: Style = DEFAULT_STYLE_STYLE
	lineNumberStyle: Style = EMPTY_STYLE_STYLE
	braceLightStyle: Style = EMPTY_STYLE_STYLE
	braceBadStyle: Style = EMPTY_STYLE_STYLE
	controlCharStyle: Style = EMPTY_STYLE_STYLE
	indentGuideStyle: Style = EMPTY_STYLE_STYLE
	calltipStyle: Style = EMPTY_STYLE_STYLE
	foldDisplayTextStyle: Style = EMPTY_STYLE_STYLE
	caretLineStyle: Style = EMPTY_STYLE_STYLE

	uiColors: Optional[BaseColors] = None

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


@dataclass
class StylesModifier:
	modifier: Optional[Style] = None
	default: Optional[Style] = None


@dataclass
class Styles:
	# language: LanguageId

	_styles: dict[str, Style] = field(default_factory=dict)
	innerLanguageStyleModifiers: dict[LanguageId, StylesModifier] = field(default_factory=dict)

	def get(self, name: str) -> Optional[Style]:
		return self._styles.get(name)


@dataclass
class StylesProxy:
	scheme: ColorScheme
	language: LanguageId
	_styles: Styles
	outerStyles: Optional[Styles]
	_styleModifier: StylesModifier = field(init=False)

	def __post_init__(self):
		if self.outerStyles is not None:
			self._styleModifier = self.outerStyles.innerLanguageStyleModifiers.get(self.language, StylesModifier())
		else:
			self._styleModifier = StylesModifier()

	def get(self, styleName: str) -> Optional[Style]:
		style = self._styles.get(styleName)
		if style is None:
			return None

		if (default2 := self._styleModifier.default) is not None:
			if styleName == 'default':
				style = mergeStyle(style, default2)
			else:
				style = mergeStyle(default2, style)

		if (default1 := self._styles.get('default')) is not None:
			style = mergeStyle(default1, style)

		if (modifier := self._styleModifier.modifier) is not None:
			style = mergeStyle(style, modifier)
		return style

	def getInnerLanguageStyles(self, innerLanguage: LanguageId) -> Optional[StylesProxy]:
		return self.scheme.getStyles2(innerLanguage, self.outerStyles)


_ALL_COLOR_SCHEMES: dict[str, ColorScheme] = {}
_currentColorScheme: str = "Default"


def currentColorScheme() -> ColorScheme:
	csName = _currentColorScheme
	scheme = _ALL_COLOR_SCHEMES.get(csName)
	if scheme is None:
		scheme = _ALL_COLOR_SCHEMES.get('Default')
	if scheme is None:
		scheme = _ALL_COLOR_SCHEMES.get('None')
	if scheme is None:
		warnings.warn("No Color Schemes available. Not even the 'None' Color Scheme. Adding it now.", RuntimeWarning)
		scheme = addColorScheme(ColorScheme('None', []))
		scheme.uiColors
	return scheme


def currentColorSchemeUpdated() -> None:
	from Cat.CatPythonGUI.GUI import catWidgetMixins
	uiColors = currentColorScheme().uiColors
	catWidgetMixins.setGUIColors(uiColors)


def setCurrentColorScheme(name: str) -> None:
	global _currentColorScheme
	_currentColorScheme = name
	currentColorSchemeUpdated()


def getColorScheme(name: str) -> Optional[ColorScheme]:
	return _ALL_COLOR_SCHEMES.get(name)


def getAllColorSchemes() -> list[ColorScheme]:
	return list(_ALL_COLOR_SCHEMES.values())


def addColorScheme(cs: ColorScheme, /) -> ColorScheme:
	_ALL_COLOR_SCHEMES[cs.name] = cs
	return cs


def _breakCycles(colorSchemes: Iterable[ColorScheme]):
	cycles = getCycles(colorSchemes, attrgetter('localFallbackSchemes'), attrgetter('name'))
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


def _createColorSchemesDir(csDir: str) -> None:
	# os.makedirs(csDir)

	with openOrCreate(os.path.join(csDir, '__init__.py'), 'w') as f:
		pass

	defaultSchemesDir = os.path.join(
		os.path.dirname(__file__), "colorSchemes/"
	)
	logDebug(f"defaultSchemesDir = {defaultSchemesDir}")
	allModulePaths: list[str] = []
	processRecursively(defaultSchemesDir, '/**', allModulePaths.append)
	for absPath in allModulePaths:
		relPath = absPath.removeprefix(defaultSchemesDir)
		logDebug(f"absPath = {absPath}")
		logDebug(f"relPath = {relPath}")
		dest = os.path.join(csDir, relPath)
		logDebug(f"dest = {dest}")
		shutil.copy2(absPath, dest)


def _allColorSchemeModules() -> list[tuple[str, str]]:
	csDir = getColorSchemesDir()
	logInfo(f"ColorSchemesDir = {csDir}")
	allModulePaths: list[str] = []

	if not os.path.exists(csDir):
		_createColorSchemesDir(csDir)

	processRecursively(csDir, '/**', allModulePaths.append)

	allModuleNames = [(mp.removeprefix(csDir).removesuffix('.py'), mp) for mp in allModulePaths if mp.endswith('.py')]
	allModuleNames = [('colorSchemes' + '.'.join(mn.split('/')), mp) for mn, mp in allModuleNames if mn.rpartition('/')[2].startswith("scheme_")]
	return allModuleNames


def _importModuleFromFile(moduleName: str, path: str):
	spec = importlib.util.spec_from_file_location(moduleName, path)
	foo = importlib.util.module_from_spec(spec)
	sys.modules[moduleName] = foo
	spec.loader.exec_module(foo)
	return foo


def _loadColorSchemeModules(names: list[tuple[str, str]]) -> dict[str, ModuleType]:
	colorSchemeMod = _importModuleFromFile('colorSchemes', os.path.join(getColorSchemesDir(), '__init__.py'))
	colorSchemeModules: dict[str, ModuleType] = {}
	for modName, modPath in names:
		#thisMod = importlib.import_module(modName)
		thisMod = _importModuleFromFile(modName, modPath)
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
	currentColorSchemeUpdated()


def reloadAllColorSchemes() -> None:
	loadAllColorSchemes()
