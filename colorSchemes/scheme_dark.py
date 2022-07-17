from dataclasses import replace, fields

from PyQt5.QtGui import QColor, qGray

from Cat.CatPythonGUI.GUI.catWidgetMixins import BaseColors
from gui.themes.theme import addColorScheme, ColorScheme, Style, StylesModifier

enabled = True


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default Dark', [])
	from .scheme_default import buildColorScheme
	lightScheme = buildColorScheme()
	for language, styles in lightScheme.styles2.items():
		styles._styles = {name: invertStyle(style) for name, style in styles._styles.items()}
		styles.innerLanguageStyleModifiers = {name: invertStylesModifier(stylesMode) for name, stylesMode in styles.innerLanguageStyleModifiers.items()}
		scheme.styles2[language] = styles

	scheme.defaultStyle = invertStyle(lightScheme.defaultStyle)
	scheme.lineNumberStyle = invertStyle(lightScheme.lineNumberStyle)
	scheme.braceLightStyle = invertStyle(lightScheme.braceLightStyle)
	scheme.braceBadStyle = invertStyle(lightScheme.braceBadStyle)
	scheme.controlCharStyle = invertStyle(lightScheme.controlCharStyle)
	scheme.indentGuideStyle = invertStyle(lightScheme.indentGuideStyle)
	scheme.calltipStyle = invertStyle(lightScheme.calltipStyle)
	scheme.foldDisplayTextStyle = invertStyle(lightScheme.foldDisplayTextStyle)

	scheme.caretLineStyle = invertStyle(lightScheme.caretLineStyle)

	scheme.uiColors = invertUIColors(lightScheme.uiColors)
	return scheme


def invertUIColors(uiColors: BaseColors) -> BaseColors:
	inverted = {}
	for f in fields(uiColors):
		inverted[f.name] = invert(getattr(uiColors, f.name))
	return BaseColors(**inverted)


def invertStylesModifier(stylesMod: StylesModifier) -> StylesModifier:
	modifier = invertStyle(stylesMod.modifier) if stylesMod.modifier is not None else None
	default = invertStyle(stylesMod.default) if stylesMod.default is not None else None
	return replace(stylesMod, modifier=modifier, default=default)


def invertStyle(style: Style) -> Style:
	foreground = invert(style.foreground) if style.foreground is not None else None
	background = invert(style.background) if style.background is not None else None
	return replace(style, foreground=foreground, background=background)


def invert(c1: QColor):
	value = 1 - (qGray(c1.rgb()) / 255)
	# print(f"value = {value}")
	c2 = QColor.fromRgbF(value, value, value, c1.alphaF())
	cr3 = matchValue(c1, matchTo=c2)
	cr4 = matchValue2(c1, matchTo=c2)

	power = 1.2

	lightness = c1.lightnessF()
	lightness2 = lightness**power
	darkness2 = 1.0 - lightness2
	darkness = darkness2**(1 / power)
	cr1 = QColor.fromHslF(c1.hueF(), c1.hslSaturationF(), darkness)
	cr2 = QColor.fromHsvF(c1.hsvHueF(), c1.hsvSaturationF(), 1.0-c1.valueF())
	return cr1


def matchValue(c1: QColor, *, matchTo: QColor) -> QColor:
	br2 = qGray(matchTo.rgb())
	br1 = qGray(c1.rgb())
	val3 = c1.valueF() * br2 / br1 if br1 != 0 else matchTo.valueF()
	val3 = min(1., val3)
	c3 = QColor.fromHsvF(c1.hsvHueF(), c1.hsvSaturationF(), val3, matchTo.alphaF())
	return c3


def matchValue2(c1: QColor, *, matchTo: QColor) -> QColor:
	br2 = qGray(matchTo.rgb())
	br1 = qGray(c1.rgb())
	val3 = c1.lightnessF() * br2 / br1 if br1 != 0 else matchTo.lightnessF()
	val3 = min(1., val3)
	c3 = QColor.fromHsvF(c1.hslHueF(), c1.hslSaturationF(), val3, matchTo.alphaF())
	return c3


def colorToStr(c: QColor):
	return c.name()
