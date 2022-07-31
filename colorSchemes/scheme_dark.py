import copy
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
	inverted = BaseColors(**inverted)
	inverted2 = copy.copy(inverted)
	inverted2.Window = lerpColor(inverted.Panel, inverted.Window, 0.5)
	inverted2.Panel = inverted.Window
	inverted2.Input = inverted.Window
	inverted2.Button = inverted.Window

	inverted2.Highlight = inverted.LightHighlight
	inverted2.LightHighlight = inverted.Highlight

	invHiBkg = qGrayF(inverted2.Highlight)
	invHiTxt = qGrayF(inverted2.HighlightedText)
	orgHiTxt = qGrayF(uiColors.HighlightedText)

	invHiOpposite = (invHiBkg < 0.5) != (invHiTxt < 0.5)
	invOrgHiOpposite = (invHiBkg < 0.5) != (orgHiTxt < 0.5)

	if not invHiOpposite and invOrgHiOpposite:
		inverted2.HighlightedText = uiColors.HighlightedText

	return inverted2


def invertStylesModifier(stylesMod: StylesModifier) -> StylesModifier:
	modifier = invertStyle(stylesMod.modifier) if stylesMod.modifier is not None else None
	default = invertStyle(stylesMod.default) if stylesMod.default is not None else None
	return replace(stylesMod, modifier=modifier, default=default)


def invertStyle(style: Style) -> Style:
	foreground = invert(style.foreground) if style.foreground is not None else None
	background = invert(style.background) if style.background is not None else None
	return replace(style, foreground=foreground, background=background)


GAMMA_FOR_INVERT = 1.2  # 1.2
INV_GAMMA_FOR_INVERT = 1 / GAMMA_FOR_INVERT


def invert(c1: QColor):
	lightness = c1.lightnessF()
	darkness = (1.0 - lightness ** GAMMA_FOR_INVERT) ** INV_GAMMA_FOR_INVERT
	cr1 = QColor.fromHslF(c1.hueF(), c1.hslSaturationF(), darkness)
	# cr2 = QColor.fromHsvF(c1.hsvHueF(), c1.hsvSaturationF(), 1.0-c1.valueF())
	return cr1


def invert2(c1: QColor):
	br1 = qGray(c1.rgb())
	cr1 = QColor(br1, br1, br1)
	lightness1 = c1.lightnessF()
	lightness2 = cr1.lightnessF()

	darkness = (1.0 - lightness2 ** GAMMA_FOR_INVERT) ** INV_GAMMA_FOR_INVERT
	cr2 = QColor.fromHslF(c1.hueF(), c1.hslSaturationF(), darkness)

	# cr2 = QColor.fromHsvF(c1.hsvHueF(), c1.hsvSaturationF(), 1.0-c1.valueF())
	return cr2


def invert3(c1: QColor):

	hue = c1.hueF()
	saturation = c1.hsvSaturationF()
	value = c1.valueF()
	value2 = value**GAMMA_FOR_INVERT
	c2 = QColor.fromHsvF(hue, saturation, value2)

	cGray = qGrayF(c2)

	# cGray **= GAMMA_FOR_INVERT
	cGray = 1 - cGray
	# cGray **= INV_GAMMA_FOR_INVERT

	hue = c2.hueF()
	saturation = c2.hslSaturationF()
	buildColor = QColor.fromHslF
	calcGray = lambda cc: lerp(qGrayF(cc), (cc.redF() + cc.greenF() + cc.blueF()) / 3, 1)

	cr2 = findGrayGoal(hue, saturation, cGray, calcGray, buildColor)

	valueR1 = cr2.valueF()**INV_GAMMA_FOR_INVERT
	saturationR1 = cr2.saturationF()
	cr1 = QColor.fromHsvF(hue, saturationR1, valueR1)
	return cr1


def findGrayGoal(hueF: float, saturation: float, grayGoal: float, calcGray, buildColor) -> QColor:
	lu = 2.0
	ll = 0.0
	lightness = ll  # lightness

	adjustSaturation = False

	# lightness:
	i = 0
	for i in range(7):
		c = buildColor(hueF, saturation, lightness)
		cGray = calcGray(c)
		if cGray > grayGoal:
			lu = lightness
		elif cGray < grayGoal:
			ll = lightness
			if lightness >= 0.999:
				lightness = 1.0
				adjustSaturation = True
				break
		else:
			return c
		lightness = (ll + lu) * 0.5

	# # saturation:
	# if adjustSaturation:
	# 	su = saturation
	# 	sl = 0.0
	# 	for j in range(0, 8):
	# 		c = buildColor(hueF, saturation, lightness)
	# 		cGray = qGrayF(c)
	# 		if cGray > grayGoal:
	# 			sl = saturation
	# 		elif cGray < grayGoal:
	# 			su = saturation
	# 		else:
	# 			return c
	# 		saturation = (sl + su) * 0.5

	return buildColor(hueF, saturation, lightness)


def qGrayF(color: QColor) -> float:
	return qGray(color.rgb()) / 255


def lerpColor(c1: QColor, c2: QColor, x: float) -> QColor:
	return QColor.fromRgbF(
		lerp(c1.redF(), c2.redF(), x),
		lerp(c1.greenF(), c2.greenF(), x),
		lerp(c1.blueF(), c2.blueF(), x),
		lerp(c1.alphaF(), c2.alphaF(), x),
	)


def lerp(c1: float, c2: float, x: float) -> float:
	return c1 + (c2 - c1) * x


def matchValue(c1: QColor, *, matchTo: QColor) -> QColor:
	br2 = qGrayF(matchTo)
	br1 = qGrayF(c1)
	val3 = c1.valueF() * br2 / br1 if br1 != 0 else matchTo.valueF()
	val3 = min(1., val3)
	c3 = QColor.fromHsvF(c1.hsvHueF(), c1.hsvSaturationF(), val3, matchTo.alphaF())
	return c3


def matchValue2(c1: QColor, *, matchTo: QColor) -> QColor:
	br2 = qGrayF(matchTo)
	br1 = qGrayF(c1)
	val3 = c1.lightnessF() * br2 / br1 if br1 != 0 else matchTo.lightnessF()
	val3 = min(1., val3)
	c3 = QColor.fromHsvF(c1.hslHueF(), c1.hslSaturationF(), val3, matchTo.alphaF())
	return c3
