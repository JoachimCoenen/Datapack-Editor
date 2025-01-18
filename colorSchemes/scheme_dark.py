import copy
from dataclasses import replace, fields
from typing import Callable

from PyQt5.QtGui import QColor, qGray

from base.model.theme import addColorScheme, ColorScheme, Style, StylesModifier, updateGlobalStylesToMatchUIColors, \
	GlobalStyles, SyntaxHighlightingStyles
from base.model.utils import LanguageId
from cat.GUI.components.catWidgetMixins import BaseColors
from cat.GUI.components.codeEditor import IndicatorStyle
from . import minimizer

_DO_PRINT = False


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default Dark', [])
	from .scheme_default import buildColorScheme
	lightScheme = buildColorScheme()

	blackColor = QColor('#1e1e1e')
	# blackColor = QColor('#000000')

	scheme.uiColors = invertUIColors(lightScheme.uiColors, blackColor)

	scheme.globalStyles = invertGlobalStyles(lightScheme.globalStyles, blackColor)
	updateGlobalStylesToMatchUIColors(scheme)
	scheme.globalStyles.defaultStyle |= Style(background=scheme.uiColors.Window)

	scheme.syntaxHighlightingCommonStyles = invertCommonStyles(lightScheme.syntaxHighlightingCommonStyles, blackColor)

	scheme.languageIndicators = invertLanguageIndicators(lightScheme.languageIndicators, blackColor)

	for language, styles in lightScheme.styles2.items():
		if _DO_PRINT:
			print(f"STYLES:")
		styles._styles = {name: invertStyle(style, blackColor, f'{language}:{name}') for name, style in styles._styles.items()}
		if _DO_PRINT:
			print(f"MODIFIERS:")
		styles.innerLanguageStyleModifiers = {name: invertStylesModifier(stylesMode, blackColor, f'{language}:{name}') for name, stylesMode in styles.innerLanguageStyleModifiers.items()}
		scheme.styles2[language] = styles

	return scheme


def invertUIColors(uiColors: BaseColors, blackColor: QColor) -> BaseColors:
	inverted = {}
	for f in fields(uiColors):
		inverted[f.name] = invert(getattr(uiColors, f.name), blackColor=blackColor, name=f'uiColors:{f.name}')
	inverted = BaseColors(**inverted)
	inverted2 = copy.copy(inverted)

	darker = inverted.Panel
	lighter = lerpColor(inverted.Panel, inverted.Window, 0.5)

	inverted2.Window = darker
	inverted2.Panel = lighter
	inverted2.Input = lighter
	inverted2.Button = lighter

	highlight = applyGamma(uiColors.Highlight, toPhysicalValue)
	lightHighlight = applyGamma(uiColors.LightHighlight, toPhysicalValue)
	highlightInv = applyGamma(inverted2.Highlight, toPhysicalValue)
	lightHighlightInv = applyGamma(inverted2.Highlight, toPhysicalValue)
	deltaGray = qGrayF(lightHighlight) - qGrayF(highlight)
	lightGray = qGrayF(highlightInv) + deltaGray
	lightHighlightInv2 = findColorForGrayGoal2(lightHighlightInv.hueF(), lightHighlightInv.hsvSaturationF(), lightGray)
	inverted2.LightHighlight = lightHighlightInv2
	# inverted2.Highlight = inverted.LightHighlight
	# inverted2.LightHighlight = inverted.Highlight

	gHighlight = qGrayF(inverted2.Highlight) >= 0.5
	gHighlightText = qGrayF(inverted2.HighlightedText) >= 0.5
	gText = qGrayF(inverted2.Text) >= 0.5
	if gHighlightText == gHighlight and gText != gHighlight:
		inverted2.HighlightedText = inverted2.Text

	return inverted2


def invertStylesModifier(stylesMod: StylesModifier, blackColor: QColor, name: str) -> StylesModifier:
	modifier = invertStyle(stylesMod.modifier, blackColor, f'{name}.modifier') if stylesMod.modifier is not None else None
	default = invertStyle(stylesMod.default, blackColor, f'{name}.default') if stylesMod.default is not None else None
	return replace(stylesMod, modifier=modifier, default=default)


def invertGlobalStyles(gs: GlobalStyles, blackColor: QColor) -> GlobalStyles:
	inverted = {
		f.name: invertStyle(getattr(gs, f.name), blackColor, f'globalStyles:{f.name}')
		for f in fields(GlobalStyles)
	}
	return replace(gs, **inverted)


def invertCommonStyles(gs: SyntaxHighlightingStyles, blackColor: QColor) -> SyntaxHighlightingStyles:
	inverted = {
		f.name: invertStyle(getattr(gs, f.name), blackColor, f'CommonStyles:{f.name}')
		for f in fields(SyntaxHighlightingStyles)
	}
	return replace(gs, **inverted)


def invertLanguageIndicators(gs: dict[LanguageId, IndicatorStyle], blackColor: QColor) -> dict[LanguageId, IndicatorStyle]:
	return {
		languageId: invertIndicatorStyle(style, blackColor, f'LanguageIndicator:{languageId}')
		for languageId, style in gs.items()
	}


def invertIndicatorStyle(style: IndicatorStyle, blackColor: QColor, name: str) -> IndicatorStyle:
	foreground = invert(style.foreground, blackColor=blackColor, name=f'{name}.foreground')
	hoverForeground = style.hoverForeground#invert(style.hoverForeground, name=f'{name}.hoverForeground')
	outline = invert(style.outline, blackColor=blackColor, name=f'{name}.outline') if style.outline is not None else None
	if _DO_PRINT: print("----------------")
	return replace(style, foreground=foreground, hoverForeground=hoverForeground, outline=outline)


def invertStyle(style: Style, blackColor: QColor, name: str) -> Style:
	foreground = invert(style.foreground, blackColor=blackColor, name=f'{name}.foreground') if style.foreground is not None else None
	background = invert(style.background, blackColor=blackColor, name=f'{name}.background') if style.background is not None else None
	if _DO_PRINT: print("----------------")
	return replace(style, foreground=foreground, background=background)


def toPhysicalValue(u: float) -> float:
	""" used with applyGamma(..., toPhysicalValue) """
	return u**1.2


def fromPhysicalValue(v: float) -> float:
	""" used with applyGamma(..., fromPhysicalValue) """
	return v**(1/1.2)


def applyGamma(c: QColor, func: Callable[[float], float]) -> QColor:
	return QColor.fromHsvF(c.hsvHueF(), c.hsvSaturationF(), func(c.valueF()))


def invert(c1: QColor, *, blackColor: QColor = QColor('black'), name: str):
	if _DO_PRINT:
		print(f"\n: {name} :")
	c2 = applyGamma(c1, toPhysicalValue)
	bc2 = applyGamma(blackColor, toPhysicalValue)

	lightnessF = c2.lightnessF()
	c3 = QColor.fromHslF(c2.hueF(), c2.hslSaturationF(), lightnessF)

	satFactor = 1.0 - (1 - lightnessF)**2 + 3 * lightnessF**6
	hsvSaturationGoal = c3.hsvSaturationF() * satFactor

	blackLevel = bc2.lightnessF()
	if _DO_PRINT: print(f"blackLevel = {round(blackLevel, 5)}")
	grayGoal = lerp(1, blackLevel * (1 + hsvSaturationGoal * 0.5), qGrayF(c3))
	if _DO_PRINT:
		print(f"c1 = {c1.name()}")
		print(f"g1 (gray) = {round(grayGoal, 5)}")
		print(f"g1 (sat)  = {round(hsvSaturationGoal, 5)}")
	c4 = findColorForGrayGoal2(c3.hueF(), hsvSaturationGoal, grayGoal)
	if _DO_PRINT: print(f"c4 (gray) = {round(qGrayF(c4), 5)}, {c4.name()}")
	c5 = applyGamma(c4, fromPhysicalValue)
	if _DO_PRINT: print(f"c5 (gray) = {round(qGrayF(c5), 5)}, {c5.name()}")
	c5.setAlphaF(c1.alphaF())
	return c5


def lerpColor(c1: QColor, c2: QColor, x: float) -> QColor:
	return QColor.fromRgbF(
		lerp(c1.redF(), c2.redF(), x),
		lerp(c1.greenF(), c2.greenF(), x),
		lerp(c1.blueF(), c2.blueF(), x),
		lerp(c1.alphaF(), c2.alphaF(), x),
	)


def lerp(c1: float, c2: float, x: float) -> float:
	return c1 + (c2 - c1) * x


def findColorForGrayGoal2(hueF: float, hsvSaturationGoal: float, grayGoal: float) -> QColor:

	def func(x: minimizer.Array) -> float:
		x2 = minimizer.clipa(x, 0, 1)
		c = QColor.fromHslF(hueF, x2[1], x2[0])
		p1 = qGrayF(c) - grayGoal
		p2 = c.hsvSaturationF() - hsvSaturationGoal
		return p1*p1 + p2*p2*2

	x0 = minimizer.array(0.5, hsvSaturationGoal)
	res = minimizer.minimize(func, x0)  # , bounds=(0, 1))
	if _DO_PRINT:
		print(f"res = {res}")
	x2 = minimizer.clipa(res, 0, 1)
	c = QColor.fromHslF(hueF, x2[1], x2[0])
	if _DO_PRINT:
		print(f"p2 (gray) = {round(qGrayF(c) - grayGoal, 5)}")
		print(f"p2 (sat)  = {round(c.saturationF() - hsvSaturationGoal, 5)}")
	return c


def qGrayF(color: QColor) -> float:
	return qGray(color.rgb()) / 255
