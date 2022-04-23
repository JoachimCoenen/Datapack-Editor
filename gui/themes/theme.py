from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from operator import attrgetter
from types import ModuleType
from typing import TypeVar, Generic, Union, Optional, Iterable

from PyQt5.QtGui import QFont, QColor

from Cat.extensions import processRecursively
from Cat.utils import getExePath
from Cat.utils.graphs import getCycles, semiTopologicalSort, collectAllNodes
from Cat.utils.logging_ import logError, logDebug
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
class StyleStyle:
	foreground: Optional[QColor] = None
	background: Optional[QColor] = None
	font: Optional[StyleFont] = None


DEFAULT_STYLE_STYLE = StyleStyle(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	font=StyleFont("Consolas", QFont.Monospace, 8)
)


@dataclass
class ColorScheme:
	name: str
	fallback: list[str]

	fallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)
	allFallbackSchemes: list[ColorScheme] = field(init=False, default_factory=list)

	styles: dict[LanguageId, dict[str, StyleStyle]] = field(default_factory=dict)

	def deferredInit(self) -> None:
		for fbName in self.fallback:
			fbScheme = getColorScheme(fbName)
			if fbScheme is not None:
				self.fallbackSchemes.append(fbScheme)

	def getLocalStyles(self, language: LanguageId) -> Optional[dict[str, StyleStyle]]:
		return self.styles.get(language)

	def getStyles(self, language: LanguageId) -> Optional[dict[str, StyleStyle]]:
		styles = self.getLocalStyles(language)
		if styles is not None:
			return styles

		for fbScheme in self.allFallbackSchemes:
			styles = fbScheme.getLocalStyles(language)
			if styles is not None:
				return styles

		return None

	def getStyle(self, language: LanguageId, style: str) -> Optional[StyleStyle]:
		styles = self.getStyles(language)
		if styles is None:
			return None
		return styles.get(style)


_ALL_COLOR_SCHEMES: dict[str, ColorScheme] = {}


def currentColorScheme() -> ColorScheme:
	return _ALL_COLOR_SCHEMES['default']


def getColorScheme(name: str) -> Optional[ColorScheme]:
	return _ALL_COLOR_SCHEMES.get(name)


def addColorScheme(cs: ColorScheme, /) -> ColorScheme:
	_ALL_COLOR_SCHEMES[cs.name] = cs
	return cs


def initAllColorSchemes() -> None:
	for cs in _ALL_COLOR_SCHEMES.values():
		cs.deferredInit()

	cycles = getCycles(_ALL_COLOR_SCHEMES.values(), attrgetter('fallbackSchemes'), attrgetter('name'))
	if cycles:
		cyclesStr = '\n'.join(f"[{' -> '.join(elem.name for elem in cycle)}]" for cycle in cycles)
		logError(f"ColorSchemes: {len(cycles)} fallback cycles found: \n{cyclesStr}\n"
				 "Fallbacks will be disabled for all ColorSchemes within these cycles.")

		for cycle in cycles:
			cycleNames = {elem.name for elem in cycle}
			for elem in cycle:
				fbs = list(filter(lambda fb: fb.name not in cycleNames, elem.fallbackSchemes))
				elem.fallbackSchemes = fbs

	for cs in _ALL_COLOR_SCHEMES.values():
		allFbs = collectAllNodes(cs, attrgetter('fallbackSchemes'), attrgetter('name'))
		allFbs = semiTopologicalSort(cs, allFbs, attrgetter('fallbackSchemes'), attrgetter('name'))
		cs.allFallbackSchemes = allFbs


def _allColorSchemeModules() -> list[str]:
	colorSchemesDir = os.path.dirname(os.path.abspath(getExePath()))
	colorSchemesDir = os.path.join(colorSchemesDir, 'colorSchemes')

	allModulePaths: list[str] = []

	processRecursively(colorSchemesDir, '/**', allModulePaths.append)

	allModulePaths = [mp.removeprefix(colorSchemesDir).removesuffix('.py') for mp in allModulePaths if mp.endswith('.py')]
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
	colorSchemeModuleNames = _allColorSchemeModules()
	_colorSchemeModules = _loadColorSchemeModules(colorSchemeModuleNames)
	_reloadModules(_colorSchemeModules.values())

	for module in _colorSchemeModules.values():
		module.initPlugin()
	initAllColorSchemes()
