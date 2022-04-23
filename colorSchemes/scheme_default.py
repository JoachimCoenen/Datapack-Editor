from PyQt5.QtGui import QColor

from model.utils import LanguageId
from gui.themes.theme import addColorScheme, ColorScheme, DEFAULT_STYLE_STYLE, StyleStyle

enabled = True


def initPlugin():
	scheme = addColorScheme(ColorScheme('default', []))
	addMCCommandScheme(scheme)
	addJsonScheme(scheme)


def addMCCommandScheme(scheme: ColorScheme):
	from gui.lexers.mcFunctionStyler import Style
	styles = {
		Style.Default.name:        DEFAULT_STYLE_STYLE,
		Style.Command.name:        StyleStyle(foreground=QColor(0x7f, 0x00, 0x7f)),
		Style.String.name:         StyleStyle(foreground=QColor(0x7f, 0x00, 0x00)),
		Style.Number.name:         StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
		Style.Constant.name:       StyleStyle(foreground=QColor(0x00, 0x00, 0xBf)),
		Style.TargetSelector.name: StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
		Style.Operator.name:       StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),
		Style.Keyword.name:        StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),

		Style.Complex.name:        StyleStyle(foreground=QColor(0x7f, 0x7f, 0x00)),

		Style.Comment.name:        StyleStyle(foreground=QColor(0x7f, 0x7f, 0x7f)),
		Style.Error.name:          StyleStyle(foreground=QColor(0xff, 0x00, 0x00)),
	}
	scheme.styles[LanguageId('MCCommand')] = styles
	return styles


def lighter(fg):
	return QColor.fromHslF(fg.hueF(), fg.saturationF(), 0.975)


def addJsonScheme(scheme: ColorScheme):
	from gui.lexers.jsonStyler import Style
	styles = {
		Style.default.name: DEFAULT_STYLE_STYLE,
		Style.null.name:      StyleStyle(foreground=QColor(0x00, 0x00, 0xBf), background=lighter(QColor(0x00, 0x00, 0xBf))),
		Style.boolean.name:   StyleStyle(foreground=QColor(0x00, 0x00, 0xBf), background=lighter(QColor(0x00, 0x00, 0xBf))),
		Style.number.name:    StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f), background=lighter(QColor(0x00, 0x7f, 0x7f))),
		Style.string.name:    StyleStyle(foreground=QColor(0x7f, 0x00, 0x00), background=lighter(QColor(0x7f, 0x00, 0x00))),
		Style.key.name:       StyleStyle(foreground=QColor(0x88, 0x0A, 0xE8), background=lighter(QColor(0x88, 0x0A, 0xE8))),  # .lighter(209)),
		Style.invalid.name:   StyleStyle(foreground=QColor(0xff, 0x00, 0x00), background=lighter(QColor(0xff, 0x00, 0x00))),  # .lighter(209)),
	}
	scheme.styles[LanguageId('JSON')] = styles
	return styles


print("math module says hi!")
