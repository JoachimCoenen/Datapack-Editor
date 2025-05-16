from __future__ import annotations

import os
import shutil
import warnings
from dataclasses import dataclass, field, fields, Field, is_dataclass, replace
from typing import Union, Optional

from PyQt5.QtGui import QFont, QColor

from cat.GUI.components.catWidgetMixins import BaseColors
from cat.GUI.components.codeEditor import IndicatorStyle
from cat.processFiles import processRecursively
from cat.utils import getExePath
from cat.utils.logging_ import logDebug, logError
from cat.utils.profiling import TimedFunction
from base.model.utils import LanguageId
from base.modules import loadAllModules, FolderAndFileFilter


class NotSet[TT]:
	def __init__(self, default: TT):
		self.default: TT = default


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

	def __str__(self):
		contents = []
		if self.foreground is not None:
			contents.append(f"foreground={self.foreground.name()}")
		if self.background is not None:
			contents.append(f"background={self.background.name()}")
		if self.font is not None:
			contents.append(f"font={self.font}")
		return f"Style({', '.join(contents)})"


EMPTY_STYLE_STYLE = Style()


DEFAULT_STYLE_STYLE = Style(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	font=StyleFont("Consolas", QFont.Monospace, 8)
)


def _getWithDefaultsFilled[TT](obj: TT) -> TT:
	aField: Field
	values = {}
	for aField in fields(obj):  # type: ignore
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


def mergeVal[TT](val: TT, overridingVal: TT) -> TT:
	if overridingVal is None or isinstance(overridingVal, NotSet):
		return val
	elif val is None or isinstance(val, NotSet):
		return overridingVal
	elif is_dataclass(val):
		return _mergeDataclass(val, overridingVal)
	else:
		return overridingVal


def _mergeDataclass[TT](val: TT, overridingVal: TT) -> TT:
	aField: Field
	values = {}
	for aField in fields(overridingVal):  # type: ignore
		if not aField.init:
			continue
		propName: str = aField.name
		value = mergeVal(getattr(val, propName), getattr(overridingVal, propName))
		values[propName] = value

	return type(val)(**values)


def mergeStyle(style: Style, overridingStyle: Style) -> Style:
	return style | overridingStyle


@dataclass
class IndicatorStyles:
	error: IndicatorStyle | None = field(default=None)
	warning: IndicatorStyle | None = field(default=None)
	info: IndicatorStyle | None = field(default=None)
	fallback: IndicatorStyle | None = field(default=None)
	search_result: IndicatorStyle | None = field(default=None)
	matched_brace: IndicatorStyle | None = field(default=None)
	# link: IndicatorStyle | None = field(default=None)


@dataclass
class GlobalStyles:
	defaultStyle: Style = field(default_factory=lambda: replace(DEFAULT_STYLE_STYLE))
	lineNumberStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	braceLightStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	braceBadStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	controlCharStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	indentGuideStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	calltipStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	foldDisplayTextStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	caretLineStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	caretStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	whiteSpaceStyle: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))


def updateGlobalStylesToMatchUIColors(scheme: ColorScheme):
	if (uic := scheme.uiColors) is not None:
		gls = scheme.globalStyles
		scheme.globalStyles = GlobalStyles(
			defaultStyle         = gls.defaultStyle         | Style(foreground=uic.Text, background=uic.Input),
			lineNumberStyle      = gls.lineNumberStyle      | Style(background=uic.Window),
			braceLightStyle      = gls.braceLightStyle      | Style(),
			braceBadStyle        = gls.braceBadStyle        | Style(),
			controlCharStyle     = gls.controlCharStyle     | Style(foreground=uic.Icon),
			indentGuideStyle     = gls.indentGuideStyle     | Style(),
			calltipStyle         = gls.calltipStyle         | Style(foreground=uic.Border, background=uic.Window),
			foldDisplayTextStyle = gls.foldDisplayTextStyle | Style(),
			caretLineStyle       = gls.caretLineStyle       | Style(background=uic.Window),
			caretStyle           = gls.caretStyle           | Style(background=uic.Text),
			whiteSpaceStyle      = gls.whiteSpaceStyle      | Style(),
		)


@dataclass
class SyntaxHighlightingStyles:
	# default: Style see GlobalStyles.defaultStyle
	comment: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	keyword: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # if | else | return
	string: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	string2: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	number: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	special_constant: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # e.g. true, false, null, ...
	key1: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # in key-value pairs. e.g. JSON
	key2: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	content_locator: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # e.g. ResourceLocation, TLTypeLiteral, ...

	variable: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # a variable
	function: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # a function or method
	parameter: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # a function parameter
	type: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))  # e.g. int, string, dict, bool, ...
	operator: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	special1: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	special2: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))

	error: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	invalid: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))

	xml_tag: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))
	xml_attribute: Style = field(default_factory=lambda: replace(EMPTY_STYLE_STYLE))


@dataclass
class ColorScheme:
	name: str

	uiColors: Optional[BaseColors] = None
	indicatorStyles: IndicatorStyles = field(default_factory=IndicatorStyles)
	globalStyles: GlobalStyles = field(default_factory=GlobalStyles)
	syntaxHighlightingCommonStyles: SyntaxHighlightingStyles = field(default_factory=SyntaxHighlightingStyles)
	languageIndicators: dict[LanguageId, IndicatorStyle] = field(default_factory=dict)


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
		scheme = addColorScheme(ColorScheme('None'))
	return scheme


def currentColorSchemeUpdated() -> None:
	from cat.GUI.components import catWidgetMixins, codeEditor
	uiColors = currentColorScheme().uiColors
	catWidgetMixins.setGUIColors(uiColors)
	indicatorStyles = currentColorScheme().indicatorStyles
	indicatorStyles2 = {
		codeEditor.CatIndicatorIds.CAT_ERROR:         indicatorStyles.error,
		codeEditor.CatIndicatorIds.CAT_WARNING:       indicatorStyles.warning,
		codeEditor.CatIndicatorIds.CAT_INFO:          indicatorStyles.info,
		codeEditor.CatIndicatorIds.CAT_FALLBACK:      indicatorStyles.fallback,
		codeEditor.CatIndicatorIds.CAT_SEARCH_RESULT: indicatorStyles.search_result,
		codeEditor.CatIndicatorIds.CAT_MATCHED_BRACE: indicatorStyles.matched_brace,
		# codeEditor.CatIndicatorIds.CAT_LINK:          indicatorStyles.link,
	}
	codeEditor.setIndicatorStyles({styleId: style for styleId, style in indicatorStyles2.items() if style is not None})


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


def getColorSchemesDir() -> str:
	colorSchemesDir = os.path.dirname(os.path.abspath(getExePath()))
	colorSchemesDir = os.path.join(colorSchemesDir, 'colorSchemes')
	return colorSchemesDir


def _copyDefaultColorSchemes(csDir: str) -> None:
	defaultSchemesDir = os.path.join(os.path.dirname(__file__), "colorSchemes/")
	logDebug(f"defaultSchemesDir = {defaultSchemesDir}")

	allFilePaths: list[str] = []
	processRecursively(defaultSchemesDir, '/**', allFilePaths.append)

	for srcPath in allFilePaths:
		relPath = srcPath.removeprefix(defaultSchemesDir)
		dstPath = os.path.join(csDir, relPath)
		try:
			shutil.copy2(srcPath, dstPath)
		except OSError as e:
			logError(e, f"Failed to copy default color scheme from '{srcPath}' to '{dstPath}'")


@TimedFunction()
def loadAllColorSchemes() -> None:
	_ALL_COLOR_SCHEMES.clear()
	addColorScheme(ColorScheme('None'))

	colorSchemesDir = getColorSchemesDir()
	loadAllModules(
		'colorSchemes',
		colorSchemesDir,
		[FolderAndFileFilter('/**', r'scheme_.+\.py')],
		setDefaultFilesFunc=_copyDefaultColorSchemes,
		initMethodName='initPlugin'
	)

	currentColorSchemeUpdated()


def reloadAllColorSchemes() -> None:
	loadAllColorSchemes()
