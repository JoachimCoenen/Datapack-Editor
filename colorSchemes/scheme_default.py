from typing import Callable

from PyQt5.QtGui import QColor

from cat.GUI.components.catWidgetMixins import BaseColors
from cat.GUI.components.codeEditor import IndicatorStyle, QSciIndicatorStyle
from base.model.utils import LanguageId
from base.model.theme import addColorScheme, ColorScheme, Style, GlobalStyles, updateGlobalStylesToMatchUIColors, \
	StyleFont, SyntaxHighlightingStyles


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default', [])
		
	scheme.uiColors = BaseColors(
		Icon=QColor('#606060'),  # QColor('#4b4b4b')
		DisabledIcon=QColor('#b4b4b4'),

		Border=QColor('#b9b9b9'),
		DisabledBorder=QColor('#cacaca'),  # QColor('#bcbcbcbc')

		Window=QColor('#f0f0f0'),
		Panel=QColor('#ffffff'),  # =BaseColor, QColor('#f8f8f8')
		Input=QColor('#ffffff'),
		AltInput=QColor('#e9e7e3'),
		Button=QColor('#ffffff'),

		Highlight=QColor('#0072ff'),  # QColor('#0090ff')  # QColor('#0078d7')
		InactiveHighlight=QColor('#959595'),
		DisabledHighlight=QColor('#a0a0a0'),
		LightHighlight=QColor('#519fff'),  # QColor('#43acff')

		Text=QColor('#000000'),
		HighlightedText=QColor('#ffffff'),
		ButtonText=QColor('#202020'),

		ToolTip=QColor('#ffffdc'),
		ToolTipText=QColor('#000000'),

		Link=QColor('#0000ff'),
		LinkVisited=QColor('#ff00ff'),
	)
	
	lightGray = QColor('#b4b4b4')
	scheme.globalStyles = GlobalStyles(
		defaultStyle=Style(foreground=scheme.uiColors.Text, background=scheme.uiColors.Input),
		lineNumberStyle=Style(background=scheme.uiColors.Window),
		braceLightStyle=Style(),
		braceBadStyle=Style(foreground=QColor('red')),
		controlCharStyle=Style(foreground=scheme.uiColors.Icon),
		indentGuideStyle=Style(foreground=lightGray, background=QColor('orange')),
		calltipStyle=Style(foreground=scheme.uiColors.Border, background=scheme.uiColors.Window),
		foldDisplayTextStyle=Style(foreground=lightGray, background=QColor('orange')),
		caretLineStyle=Style(background=scheme.uiColors.Window),
		whiteSpaceStyle=Style(foreground=lightGray)
	)
	scheme.syntaxHighlightingCommonStyles = SyntaxHighlightingStyles(
		comment=         Style(foreground=QColor(0x7f, 0x7f, 0x7f), font=StyleFont(italic=True)),
		keyword=         Style(foreground=QColor(0xb100d0), font=StyleFont(bold=False)),  # Style(foreground=QColor(0x88, 0x0a, 0xe8), font=StyleFont(bold=False)),
		string=          Style(foreground=QColor(0x7f, 0x00, 0x00)),
		number=          Style(foreground=QColor(0x00, 0x7f, 0x7f)),
		specialConstant= Style(foreground=QColor(0x00, 0x00, 0xBf)),
		key1=            Style(foreground=QColor(0x88, 0x0a, 0xe8)),
		key2=            Style(foreground=QColor('plum')),  # to be decided later
		contentLocator=  Style(foreground=QColor(0x6f, 0x6f, 0x00)),
		type=            Style(foreground=QColor(0xbf, 0x00, 0xbf)),
		operator=        Style(foreground=QColor(0x00, 0x00, 0x00)),  # Style(foreground=QColor('limegreen')),
		special1=        Style(foreground=QColor(0x00, 0x7f, 0x7f)),
		special2=        Style(foreground=QColor('darkorange')),  # to be decided later

		error=           Style(foreground=QColor(0xff, 0x00, 0x00)),
		invalid=         Style(foreground=QColor(0xff, 0x00, 0x00)),

		xmlTag=          Style(foreground=QColor(0x00, 0x00, 0xbf)),
		xmlAttribute=    Style(foreground=QColor(0x00, 0x80, 0x80)),
	)
	updateGlobalStylesToMatchUIColors(scheme)

	colJson = lighten(scheme.syntaxHighlightingCommonStyles.string.foreground, 0.8)
	colJson.setAlphaF(1 - 0.9)

	colMCFunction = lighten(scheme.syntaxHighlightingCommonStyles.specialConstant.foreground, 0.75)
	colMCFunction.setAlphaF(1 - 0.9)

	colSNBT = lighten(QColor(0x7f, 0x7f, 0x00), 0.33)
	colSNBT.setAlphaF(1 - 0.9)

	scheme.languageIndicators = {
		LanguageId('JSON'): IndicatorStyle(
			style=QSciIndicatorStyle.StraightBoxIndicator,
			drawUnder=True,
			foreground=colJson,
		),
		LanguageId('MCFunction'): IndicatorStyle(
			style=QSciIndicatorStyle.StraightBoxIndicator,
			drawUnder=True,
			foreground=colMCFunction,
		),
		LanguageId('SNBT'): IndicatorStyle(
			style=QSciIndicatorStyle.StraightBoxIndicator,
			drawUnder=True,
			foreground=colSNBT,
		)}

	return scheme


def lighten(fg, lightness=.975):
	return QColor.fromHslF(fg.hslHueF(), fg.hslSaturationF(), lightness)
