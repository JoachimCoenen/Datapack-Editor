from collections import Callable

from PyQt5.QtGui import QColor, QFont

from Cat.utils.collections_ import AddToDictDecorator
from model.utils import LanguageId
from gui.themes.theme import addColorScheme, ColorScheme, Style, Styles, StyleFont

enabled = True


def initPlugin():
	scheme = addColorScheme(ColorScheme('Default', []))
	# addMCCommandScheme(scheme)
	# addJsonScheme(scheme)
	for language, stylesGen in _STYLES_TO_ADD.items():
		scheme.styles2[language] = stylesGen()



StylesGenerator = Callable[[], Styles]

_STYLES_TO_ADD: dict[LanguageId, StylesGenerator] = {}

languageStyles = AddToDictDecorator(_STYLES_TO_ADD)

# def languageStyles(languageId: LanguageId) -> Callable[[StylesGenerator], StylesGenerator]:
# 	def addStyles(stylesGen: StylesGenerator) -> StylesGenerator:
# 		_STYLES_TO_ADD[]
# 	return


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

	innerLanguageStyleModifiers = {
		LanguageId('JSON'): Style(background=lighten(styles[StyleId.String.name].foreground, 0.95)),
		LanguageId('SNBT'): Style(background=lighten(styles[StyleId.Complex.name].foreground, 0.925)),
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
		LanguageId('MCCommand'): Style(background=lighten(styles[StyleId.boolean.name].foreground, 0.95)),
		LanguageId('SNBT'): Style(background=lighten(QColor(0x7f, 0x7f, 0x00), 0.925)),
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

	innerLanguageStyleModifiers = {
	}

	return Styles(styles, innerLanguageStyleModifiers)


print("math module says hi!")
