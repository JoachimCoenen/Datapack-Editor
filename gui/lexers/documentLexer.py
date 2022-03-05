from abc import abstractmethod
from dataclasses import dataclass, fields
from typing import TypeVar, Optional, Union, cast, Sequence

from PyQt5.Qsci import QsciLexerCustom, QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CallTipInfo
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override, HTMLStr
from model.parsing.contextProvider import ContextProvider, getContextProvider
from model.parsing.tree import Node
from model.utils import GeneralError, Position
from session.documents import TextDocument

TT = TypeVar('TT')
TokenType = int


# @dataclass
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
	qFont: QFont = QFont()
	for filed in fields(styleFont):
		propName: str = filed.name
		setterName = f'set{propName[0].upper()}{propName[1:]}'

		value = getattr(styleFont, propName)
		if isinstance(value, NotSet):
			if parentFont is not None:
				value = getattr(parentFont, propName)()
			else:
				value = value.default
		getattr(qFont, setterName)(value)

	return qFont


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

		self._api = DocumentQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

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
			# if background is None:
			# 	fg = foreground
			# 	background = QColor.fromHslF(fg.hueF(), fg.saturationF(), 0.975)

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


class DocumentQsciAPIs(MyQsciAPIs):
	def __init__(self, lexer: Optional[QsciLexer]):
		super(MyQsciAPIs, self).__init__(lexer)
		self._autoCompletionTree: AutoCompletionTree = AutoCompletionTree('', '')

	@override
	def postAutoCompletionSelected(self, selection: str) -> None:
		QTimer.singleShot(0, lambda: self._editor.showCallTips() or self._editor.myStartAutoCompletion())

	@property
	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._autoCompletionTree

	@autoCompletionTree.setter
	def autoCompletionTree(self, value: AutoCompletionTree):
		self._autoCompletionTree = value

	# def getApiContext(self, pos: int, self) -> tuple[List[str], int, int]:

	@property
	def _editor(self) -> QsciScintilla:
		return self.lexer().editor()

	@property
	def _document(self) -> Optional[TextDocument]:
		lexer: DocumentLexerBase = cast(DocumentLexerBase, self.lexer())
		assert isinstance(lexer, DocumentLexerBase)
		return lexer.document()

	@property
	def contextProvider(self) -> Optional[ContextProvider]:
		doc = self._document
		if doc is not None and isinstance(doc.tree, Node):
			return getContextProvider(doc.tree)
		return None

	@property
	def _errors(self) -> Sequence[GeneralError]:
		doc = self._document
		if doc is not None:
			return doc.errors
		return ()

	def posFromCEPos(self, cePosition: CEPosition) -> Position:
		editor = self._editor
		return Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

	@property
	def currentCursorPos(self) -> Position:
		editor = self._editor
		cePosition = CEPosition(*editor.getCursorPosition())
		return self.posFromCEPos(cePosition)

	def updateDocumentTree(self) -> None:
		if (doc := self._document) is not None:
			if doc.asyncValidate.pending:
				doc.asyncValidate.callNow()

	@override
	def getHoverTip(self, cePosition: CEPosition) -> Optional[str]:
		position = self.posFromCEPos(cePosition)
		errors = self._errors
		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		from Cat.CatPythonGUI.GUI import PythonGUI
		tips = [f'<div style="{PythonGUI.helpBoxStyles.get(e.style, "")}">{e.message}</div>' for e in matchedErrors]

		if (ctxProvider := self.contextProvider) is not None:
			tips.append(ctxProvider.getDocumentation(position))

		if not tips:
			return None
		tip = '<br/>'.join(tips)
		return f"{tip}"

	@override
	def getCallTips(self, cePosition: CEPosition) -> list[CallTipInfo]:
		self.updateDocumentTree()
		position = self.posFromCEPos(cePosition)
		if (ctxProvider := self.contextProvider) is not None:
			return [CallTipInfo(ct, HTMLStr('')) for ct in ctxProvider.getCallTips(position)]

	@CrashReportWrapped
	def updateAutoCompletionList(self, context: list[str], aList: list[str]) -> list[str]:
		"""
		Update the list \a list with API entries derived from \a context.  \a
		context is the list of words in the text preceding the cursor position.
		The characters that make up a word and the characters that separate
		words are defined by the lexer.  The last word is a partial word and
		may be empty if the user has just entered a word separator.
		"""
		self.updateDocumentTree()
		if (ctxProvider := self.contextProvider) is not None:
			replaceCtx = context[0] if context else ''
			position = self.currentCursorPos
			suggestions = ctxProvider.getSuggestions(position, replaceCtx)
			return suggestions
		return super().updateAutoCompletionList(context, aList)

	@override
	def getClickableRanges(self) -> list[tuple[CEPosition, CEPosition]]:
		if (ctxProvider := self.contextProvider) is not None:
			ranges = ctxProvider.getClickableRanges()
			return [r.asTuple for r in ranges]
		return []

	@override
	def indicatorClicked(self, cePosition: CEPosition, state: Qt.KeyboardModifiers) -> None:
		editor = self._editor
		position = self.posFromCEPos(cePosition)

		if state != Qt.ControlModifier:
			return

		if (ctxProvider := self.contextProvider) is not None:
			ctxProvider.onIndicatorClicked(position, editor.window())
