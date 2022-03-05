from abc import abstractmethod
from dataclasses import dataclass, fields
from typing import TypeVar, Optional, Union

from PyQt5.Qsci import QsciLexerCustom
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree
from session.documents import TextDocument

TT = TypeVar('TT')
TokenType = int

#@dataclass
class NotSet:
	def __init__(self, default):
		self.default: TT = default


@dataclass
class StyleFont:
	family: Union[str, NotSet] = NotSet('Courier New')
	styleHint: Union[QFont.StyleHint, NotSet] = NotSet(QFont.Monospace)
	pointSize: Union[int, NotSet] = NotSet(8)
	bold: Union[bool, NotSet] = NotSet(False)
	italic: Union[bool, NotSet] = NotSet(False)
	underline: Union[bool, NotSet] = NotSet(False)
	overline: Union[bool, NotSet] = NotSet(False)
	strikeOut: Union[bool, NotSet] = NotSet(False)

	# family: Union[str, NotSet[str]] = NotSet('Courier New')
	# styleHint: Union[QFont.StyleHint, NotSet[QFont.StyleHint]] = NotSet(QFont.Monospace)
	# pointSize: Union[int, NotSet[int]] = NotSet(8)
	# bold: Union[bool, NotSet[bool]] = NotSet(False)
	# italic: Union[bool, NotSet[bool]] = NotSet(False)
	# underline: Union[bool, NotSet[bool]] = NotSet(False)
	# overline: Union[bool, NotSet[bool]] = NotSet(False)
	# strikeOut: Union[bool, NotSet[bool]] = NotSet(False)


def QFontFromStyleFont(styleFont: StyleFont, parentFont: Optional[QFont] = None):
	qfont: QFont = QFont()
	for filed in fields(styleFont):
		propName: str = filed.name
		setterName = f'set{propName[0].upper()}{propName[1:]}'

		value = getattr(styleFont, propName)
		if isinstance(value, NotSet):
			if parentFont is not None:
				value = getattr(parentFont, propName)()
			else:
				value = value.default
		getattr(qfont, setterName)(value)

	return qfont


@dataclass
class StyleStyle:
	foreground: Optional[QColor] = None
	background: Optional[QColor] = None
	font: Optional[StyleFont] = None


DEFAULT_STYLE: TokenType = 0


class DocumentLexerBase(QsciLexerCustom):

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		# Initialize all style colors
		self.initStyles(self.getStyles())
		self._document: Optional[TextDocument] = None

	@abstractmethod
	def getStyles(self) -> dict[TokenType, StyleStyle]:
		pass

	def initStyles(self, styles: dict[TokenType, StyleStyle], overwriteDefaultStyle: bool = False):
		# handle default first:
		if overwriteDefaultStyle:
			defaultStyle = styles[DEFAULT_STYLE]
			defaultFont = QFontFromStyleFont(defaultStyle.font)

			self.setDefaultColor(defaultStyle.foreground)
			self.setDefaultPaper(defaultStyle.background)
			super(DocumentLexerBase, self).setDefaultFont(defaultFont)

		defaultForeground: QColor = self.defaultColor()
		defaultBackground: QColor = self.defaultPaper()
		defaultFont: QFont = self.defaultFont()

		for tokenType, style in styles.items():

			foreground = style.foreground
			if foreground is None or tokenType == DEFAULT_STYLE:
				foreground = defaultForeground

			background = style.background
			if background is None or tokenType == DEFAULT_STYLE:
				background = defaultBackground

			if style.font is None or tokenType == DEFAULT_STYLE:
				font = defaultFont
			else:
				font = QFontFromStyleFont(style.font, defaultFont)

			self.setColor(foreground, tokenType)
			self.setPaper(background, tokenType)
			self.setFont(font, tokenType)

	def setDefaultFont(self, font: QFont):
		super().setDefaultFont(font)
		self.initStyles(self.getStyles())

	def setFont(self, font: QFont, style=-1):
		if style == -1:
			self.setDefaultFont(font)
		else:
			super().setFont(font, style)

	def document(self) -> Optional[TextDocument]:
		return self._document

	def setDocument(self, document: Optional[TextDocument]) -> None:
		self._document = document