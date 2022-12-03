from typing import Callable

from PyQt5.QtGui import QColor

from Cat.CatPythonGUI.GUI.catWidgetMixins import BaseColors
from Cat.utils.collections_ import AddToDictDecorator
from base.gui.styler import DEFAULT_STYLE_ID, StyleIdEnum
from base.model.utils import LanguageId
from gui.themes.theme import addColorScheme, ColorScheme, Style, Styles, StylesModifier, GlobalStyles, updateGlobalStylesToMatchUIColors

enabled = True


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default', [])
	for language, stylesGen in _STYLES_TO_ADD.items():
		scheme.styles2[language] = stylesGen()
		
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
	
	lightGray = QColor(0xe0, 0xe0, 0xe0)
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
	)
	updateGlobalStylesToMatchUIColors(scheme)

	return scheme


StylesGenerator = Callable[[], Styles]

_STYLES_TO_ADD: dict[LanguageId, StylesGenerator] = {}

languageStyles = AddToDictDecorator(_STYLES_TO_ADD)


DEFAULT_STYLE_STYLE = Style(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	# font=StyleFont("Consolas", QFont.Monospace, 8)
)


def lighten(fg, lightness=.975):
	return QColor.fromHslF(fg.hueF(), fg.saturationF(), lightness)


# @languageStyles(LanguageId('MCCommand'))
# def addMCCommandScheme():
# 	from gui.lexers.mcFunctionStyler import StyleId
# 	styles = {
# 		StyleId.Default.name:        Style(),
# 		StyleId.Command.name:        Style(foreground=QColor(0x88, 0x0a, 0xe8)),
# 		StyleId.String.name:         Style(foreground=QColor(0x7f, 0x00, 0x00)),
# 		StyleId.Number.name:         Style(foreground=QColor(0x00, 0x7f, 0x7f)),
# 		StyleId.Constant.name:       Style(foreground=QColor(0x00, 0x00, 0xBf)),
# 		StyleId.TargetSelector.name: Style(foreground=QColor(0x00, 0x7f, 0x7f)),
# 		StyleId.Operator.name:       Style(foreground=QColor(0x00, 0x00, 0x00)),
# 		StyleId.Keyword.name:        Style(foreground=QColor(0x00, 0x00, 0x00)),
#
# 		StyleId.Complex.name:        Style(foreground=QColor(0x7f, 0x7f, 0x00)),
#
# 		StyleId.Comment.name:        Style(foreground=QColor(0x7f, 0x7f, 0x7f), font=StyleFont(italic=True)),
# 		StyleId.Error.name:          Style(foreground=QColor(0xff, 0x00, 0x00)),
# 	}
#
# 	assert len(styles) == len(StyleId)
#
# 	innerLanguageStyleModifiers = {
# 		LanguageId('JSON'): StylesModifier(
# 			modifier=Style(background=lighten(styles[StyleId.String.name].foreground, 0.95)),
# 			# default=styles[StyleId.String.name],
# 		),
# 		LanguageId('SNBT'): StylesModifier(
# 			modifier=Style(background=lighten(styles[StyleId.Complex.name].foreground, 0.925)),
# 			# default=styles[StyleId.String.name],
# 		),
# 	}
#
# 	return Styles(styles, innerLanguageStyleModifiers)


@languageStyles(LanguageId('JSON'))
def addJsonScheme():
	# from gui.lexers.jsonStyler import StyleId
	class StyleId(StyleIdEnum):
		default = DEFAULT_STYLE_ID
		null = DEFAULT_STYLE_ID + 1
		boolean = DEFAULT_STYLE_ID + 2
		number = DEFAULT_STYLE_ID + 3
		string = DEFAULT_STYLE_ID + 4
		key = DEFAULT_STYLE_ID + 5
		invalid = DEFAULT_STYLE_ID + 6
	styles = {
		StyleId.default.name: Style(),
		StyleId.null.name:    Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.boolean.name: Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.number.name:  Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.string.name:  Style(foreground=QColor(0x7f, 0x00, 0x00)),  # , background=lighten(QColor(0x7f, 0x00, 0x00))),
		StyleId.key.name:     Style(foreground=QColor(0x88, 0x0a, 0xe8)),  # , background=lighten(QColor(0x88, 0x0a, 0xe8))),  # .lighten(209)),
		StyleId.invalid.name: Style(foreground=QColor(0xff, 0x00, 0x00)),  # , background=lighten(QColor(0xff, 0x00, 0x00))),  # .lighten(209)),
	}

	innerLanguageStyleModifiers = {
		LanguageId('MCCommand'): StylesModifier(
			modifier=Style(background=lighten(styles[StyleId.boolean.name].foreground, 0.95)),
			default=styles[StyleId.string.name],
		),
		LanguageId('SNBT'): StylesModifier(
			modifier=Style(background=lighten(QColor(0x7f, 0x7f, 0x00), 0.925)),
			default=styles[StyleId.string.name],
		),
	}

	return Styles(styles, innerLanguageStyleModifiers)


@languageStyles(LanguageId('SNBT'))
def addSNBTScheme():
	class StyleId(StyleIdEnum):
		default = DEFAULT_STYLE_ID
		boolean = DEFAULT_STYLE_ID + 1
		intLike = DEFAULT_STYLE_ID + 2
		floatLike = DEFAULT_STYLE_ID + 3
		string = DEFAULT_STYLE_ID + 4
		key = DEFAULT_STYLE_ID + 5
		invalid = DEFAULT_STYLE_ID + 6
	styles = {
		StyleId.default.name: Style(),
		StyleId.boolean.name:   Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.intLike.name:   Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.floatLike.name: Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.string.name:    Style(foreground=QColor(0x7f, 0x00, 0x00)),  # , background=lighten(QColor(0x7f, 0x00, 0x00))),
		StyleId.key.name:       Style(foreground=QColor(0x88, 0x0a, 0xe8)),  # , background=lighten(QColor(0x88, 0x0a, 0xe8))),  # .lighten(209)),
		StyleId.invalid.name:   Style(foreground=QColor(0xff, 0x00, 0x00)),  # , background=lighten(QColor(0xff, 0x00, 0x00))),  # .lighten(209)),
	}

	assert len(styles) == len(StyleId)

	innerLanguageStyleModifiers = {
	}

	return Styles(styles, innerLanguageStyleModifiers)


print("scheme_default.py module says hi!")
