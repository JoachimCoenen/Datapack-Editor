from typing import Callable

from PyQt5.QtGui import QColor, QFont

from Cat.CatPythonGUI.GUI.catWidgetMixins import BaseColors
from Cat.utils.collections_ import AddToDictDecorator
from model.utils import LanguageId
from gui.themes.theme import addColorScheme, ColorScheme, Style, Styles, StyleFont, StylesModifier

enabled = True


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default', [])
	for language, stylesGen in _STYLES_TO_ADD.items():
		scheme.styles2[language] = stylesGen()

	# scheme.defaultStyle = invertStyle(scheme.defaultStyle)
	lightGray = QColor(0xe0, 0xe0, 0xe0)
	scheme.lineNumberStyle = Style(background=lightGray)
	# scheme.braceLightStyle = invertStyle(scheme.braceLightStyle)
	# scheme.braceBadStyle = invertStyle(scheme.braceBadStyle)
	# scheme.controlCharStyle = invertStyle(scheme.controlCharStyle)
	scheme.indentGuideStyle = Style(foreground=lightGray, background=QColor('orange'))
	# scheme.calltipStyle = invertStyle(scheme.calltipStyle)
	scheme.foldDisplayTextStyle = Style(foreground=lightGray, background=QColor('orange'))
	scheme.caretLineStyle = Style(background=lightGray)

	scheme.uiColors = BaseColors(
		Icon=QColor('#606060'),  # QColor('#4b4b4b')
		DisabledIcon=QColor('#b4b4b4'),
		DisabledBorder=QColor('#cacaca'),  # QColor('#bcbcbcbc')
		Base=QColor('#FFFFFF'),
		Window=QColor('#F0F0F0'),
		Panel=QColor('#FFFFFF'),  # =BaseColor, QColor('#F8F8F8')
		Highlight=QColor('#0072FF'),  # QColor('#0090ff')  # QColor('#0078d7')
		InactiveHighlight=QColor('#959595'),
		DisabledHighlight=QColor('#a0a0a0'),
		LightHighlight=QColor('#519FFF'),  # QColor('#43acff')
		Border=QColor('#b9b9b9'),
		Text=QColor('#000000'),
		HighlightedText=QColor('#FFFFFF'),
		ButtonText=QColor('#202020'),
		ToolTip=QColor('#ffffdc'),
		ToolTipText=QColor('#000000'),
	)

	return scheme


StylesGenerator = Callable[[], Styles]

_STYLES_TO_ADD: dict[LanguageId, StylesGenerator] = {}

languageStyles = AddToDictDecorator(_STYLES_TO_ADD)


DEFAULT_STYLE_STYLE = Style(
	foreground=QColor(0x00, 0x00, 0x00),
	background=QColor(0xff, 0xff, 0xff),
	font=StyleFont("Consolas", QFont.Monospace, 8)
)


def lighten(fg, lightness=.975):
	return QColor.fromHslF(fg.hueF(), fg.saturationF(), lightness)


@languageStyles(LanguageId('MCCommand'))
def addMCCommandScheme():
	from gui.lexers.mcFunctionStyler import StyleId
	styles = {
		StyleId.Default.name:        DEFAULT_STYLE_STYLE,
		StyleId.Command.name:        Style(foreground=QColor(0x88, 0x0A, 0xE8)),
		StyleId.String.name:         Style(foreground=QColor(0x7f, 0x00, 0x00)),
		StyleId.Number.name:         Style(foreground=QColor(0x00, 0x7f, 0x7f)),
		StyleId.Constant.name:       Style(foreground=QColor(0x00, 0x00, 0xBf)),
		StyleId.TargetSelector.name: Style(foreground=QColor(0x00, 0x7f, 0x7f)),
		StyleId.Operator.name:       Style(foreground=QColor(0x00, 0x00, 0x00)),
		StyleId.Keyword.name:        Style(foreground=QColor(0x00, 0x00, 0x00)),

		StyleId.Complex.name:        Style(foreground=QColor(0x7f, 0x7f, 0x00)),

		StyleId.Comment.name:        Style(foreground=QColor(0x7f, 0x7f, 0x7f), font=StyleFont(italic=True)),
		StyleId.Error.name:          Style(foreground=QColor(0xff, 0x00, 0x00)),
	}

	assert len(styles) == len(StyleId)

	innerLanguageStyleModifiers = {
		LanguageId('JSON'): StylesModifier(
			modifier=Style(background=lighten(styles[StyleId.String.name].foreground, 0.95)),
			# default=styles[StyleId.String.name],
		),
		LanguageId('SNBT'): StylesModifier(
			modifier=Style(background=lighten(styles[StyleId.Complex.name].foreground, 0.925)),
			# default=styles[StyleId.String.name],
		),
	}

	return Styles(styles, innerLanguageStyleModifiers)


@languageStyles(LanguageId('JSON'))
def addJsonScheme():
	from gui.lexers.jsonStyler import StyleId
	styles = {
		StyleId.default.name: DEFAULT_STYLE_STYLE,
		StyleId.null.name:    Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.boolean.name: Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.number.name:  Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.string.name:  Style(foreground=QColor(0x7f, 0x00, 0x00)),  # , background=lighten(QColor(0x7f, 0x00, 0x00))),
		StyleId.key.name:     Style(foreground=QColor(0x88, 0x0A, 0xE8)),  # , background=lighten(QColor(0x88, 0x0A, 0xE8))),  # .lighten(209)),
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
	from gui.lexers.snbtStyler import StyleId
	styles = {
		StyleId.default.name: DEFAULT_STYLE_STYLE,
		StyleId.boolean.name:   Style(foreground=QColor(0x00, 0x00, 0xBf)),  # , background=lighten(QColor(0x00, 0x00, 0xBf))),
		StyleId.intLike.name:   Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.floatLike.name: Style(foreground=QColor(0x00, 0x7f, 0x7f)),  # , background=lighten(QColor(0x00, 0x7f, 0x7f))),
		StyleId.string.name:    Style(foreground=QColor(0x7f, 0x00, 0x00)),  # , background=lighten(QColor(0x7f, 0x00, 0x00))),
		StyleId.key.name:       Style(foreground=QColor(0x88, 0x0A, 0xE8)),  # , background=lighten(QColor(0x88, 0x0A, 0xE8))),  # .lighten(209)),
		StyleId.invalid.name:   Style(foreground=QColor(0xff, 0x00, 0x00)),  # , background=lighten(QColor(0xff, 0x00, 0x00))),  # .lighten(209)),
	}

	assert len(styles) == len(StyleId)

	innerLanguageStyleModifiers = {
	}

	return Styles(styles, innerLanguageStyleModifiers)


print("scheme_default.py module says hi!")
