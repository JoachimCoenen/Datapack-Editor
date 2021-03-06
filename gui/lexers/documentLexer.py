from abc import abstractmethod
from dataclasses import dataclass, fields
from typing import TypeVar, Optional, cast, Sequence

from PyQt5.Qsci import QsciLexerCustom, QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from Cat.CatPythonGUI.GUI.codeEditor import CodeEditor, MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CallTipInfo
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override, HTMLStr
from Cat.utils.logging_ import logWarning
from gui.lexers.styler import DEFAULT_STYLE_ID, getStyler, StyleId, StylerCtx
from gui.themes import theme
from gui.themes.theme import DEFAULT_STYLE_STYLE, StyleFont, Style
from model.parsing.contextProvider import ContextProvider, getContextProvider
from model.parsing.tree import Node
from model.utils import addStyle, formatMarkdown, GeneralError, LanguageId, MDStr, Position
from session.documents import TextDocument

TT = TypeVar('TT')
TokenType = int


_SCI_STYLE_DEFAULT = 32  # This style defines the attributes that all styles receive when the SCI_STYLECLEARALL message is used.
_SCI_STYLE_LINENUMBER = 33  # This style sets the attributes of the text used to display line numbers in a line number margin. The background colour set for this style also sets the background colour for all margins that do not have any folding mask bits set. That is, any margin for which mask & SC_MASK_FOLDERS is 0. See SCI_SETMARGINMASKN for more about masks.
_SCI_STYLE_BRACELIGHT = 34  # This style sets the attributes used when highlighting braces with the SCI_BRACEHIGHLIGHT message and when highlighting the corresponding indentation with SCI_SETHIGHLIGHTGUIDE.
_SCI_STYLE_BRACEBAD = 35  # This style sets the display attributes used when marking an unmatched brace with the SCI_BRACEBADLIGHT message.
_SCI_STYLE_CONTROLCHAR = 36  # This style sets the font used when drawing control characters. Only the font, size, bold, italics, and character set attributes are used and not the colour attributes. See also: SCI_SETCONTROLCHARSYMBOL.
_SCI_STYLE_INDENTGUIDE = 37  # This style sets the foreground and background colours used when drawing the indentation guides.
_SCI_STYLE_CALLTIP = 38  # Call tips normally use the font attributes defined by STYLE_DEFAULT. Use of SCI_CALLTIPUSESTYLE causes call tips to use this style instead. Only the font face name, font size, foreground and background colours and character set attributes are used.
_SCI_STYLE_FOLDDISPLAYTEXT = 39  # This is the style used for drawing text tags attached to folded text.
_SCI_STYLE_LASTPREDEFINED = 39
_CAT_STYLE_CARETLINE = -257


def QFontFromStyleFont(styleFont: StyleFont) -> QFont:
	qFont: QFont = QFont()
	for field in fields(styleFont):
		propName: str = field.name
		setterName = f'set{propName[0].upper()}{propName[1:]}'
		value = getattr(styleFont, propName)
		getattr(qFont, setterName)(value)

	return qFont


def StyleFontFromQFont(qFont: QFont) -> StyleFont:
	values = {}
	for filed in fields(StyleFont):
		propName: str = filed.name
		value = getattr(qFont, propName)()
		values[propName] = value

	return StyleFont(**values)


class DocumentLexerBase(QsciLexerCustom):  # this is an ABC, but there would be a metaclass conflict.

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		# Initialize all style colors
		self._document: Optional[TextDocument] = None
		self.initStyles(self.getStyles(), overwriteDefaultStyle=True)

		self._api = DocumentQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	@abstractmethod
	def getStyles(self) -> dict[TokenType, Style]:
		pass

	def setCaretLineStyle(self, style: Style):
		editor: CodeEditor = self.editor()
		if editor is None:
			return
		editor.setCaretLineBackgroundColor(style.background)

	def initStyle(self, style: Style, id: int) -> None:
		actualId = id + _SCI_STYLE_LASTPREDEFINED + 1
		self.setColor(style.foreground, actualId)
		self.setPaper(style.background, actualId)
		self.setFont(QFontFromStyleFont(style.font), actualId)

	def initStyles(self, styles: dict[TokenType, Style], overwriteDefaultStyle: bool = False):
		defaultStyle = Style(
			foreground=self.defaultColor(),
			background=self.defaultPaper(),
			font=StyleFontFromQFont(self.defaultFont()),
		)
		# handle default first:
		if overwriteDefaultStyle:
			defaultStyle = defaultStyle | styles[DEFAULT_STYLE_ID]
			defaultQFont = QFontFromStyleFont(defaultStyle.font)
			# defaultQFont.setPointSize(self.defaultFont().pointSize())

			self.setDefaultColor(defaultStyle.foreground)
			self.setColor(defaultStyle.foreground, 0)
			self.setDefaultPaper(defaultStyle.background)
			self.setPaper(defaultStyle.background, 0)
			super().setDefaultFont(defaultQFont)

		for tokenType, style in styles.items():
			actualStyle = defaultStyle
			if tokenType != DEFAULT_STYLE_ID:
				actualStyle |= style

			if tokenType == _CAT_STYLE_CARETLINE:
				self.setCaretLineStyle(actualStyle)
			else:
				self.initStyle(actualStyle, tokenType)

	def setDefaultFont(self, font: QFont):
		super().setDefaultFont(font)
		self.initStyles(self.getStyles(), overwriteDefaultStyle=True)

	def setFont(self, font: QFont, style=-1):
		super().setFont(font, style)

	def getTree(self) -> Optional[Node]:
		doc = self.document()
		if doc is None:
			return
		tree = doc.tree
		if isinstance(tree, Node):
			return tree
		return None

	def getText(self) -> Optional[bytes]:
		doc = self.document()
		if doc is None:
			return
		return doc.content

	def document(self) -> Optional[TextDocument]:
		return self._document

	def setDocument(self, document: Optional[TextDocument]) -> None:
		self._document = document

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		return ['.']  # ':', '#', '.']


class DocumentLexerBase2(DocumentLexerBase):  # this is an ABC, but there would be a metaclass conflict.
	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		self._lastStylePos: int = 0

	# @override
	# def setDocument(self, document: Optional[TextDocument]) -> None:
	# 	super(LexerMCFunction, self).setDocument(document)
	# 	self.initStyles(self.getStyles())

	@property
	def languageId(self) -> Optional[LanguageId]:
		if (doc := self.document()) is not None:
			# TODO: return doc.language
			pass
		if (tree := self.getTree()) is not None:
			return tree.language
		return None

	@override
	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	def getStyles(self) -> dict[StyleId, Style]:
		scheme = theme.currentColorScheme()

		styleMap = {DEFAULT_STYLE_ID: scheme.defaultStyle}

		languageId = self.languageId
		if languageId is None:
			return styleMap

		styles = scheme.getStyles2(languageId)
		if styles is None:
			return styleMap

		styler = getStyler(languageId, StylerCtxQScintilla(DEFAULT_STYLE_ID, 0, self))
		if styler is None:
			return styleMap

		for innerLanguage, styler in styler.innerStylers.items():
			innerStyles = styles.getInnerLanguageStyles(innerLanguage)
			for name, styleId in styler.localStyles.items():
				style = innerStyles.get(name)
				if style is None:
					logWarning(f"Theme '{scheme.name}' is missing style '{name}' for language '{innerLanguage}'")
					style = DEFAULT_STYLE_STYLE
				styleMap[styleId] = style

		revOffset = -_SCI_STYLE_LASTPREDEFINED - 1
		styleMap[_SCI_STYLE_LINENUMBER + revOffset] = scheme.lineNumberStyle
		styleMap[_SCI_STYLE_BRACELIGHT + revOffset] = scheme.braceLightStyle
		styleMap[_SCI_STYLE_BRACEBAD + revOffset] = scheme.braceBadStyle
		styleMap[_SCI_STYLE_CONTROLCHAR + revOffset] = scheme.controlCharStyle
		styleMap[_SCI_STYLE_INDENTGUIDE + revOffset] = scheme.indentGuideStyle
		styleMap[_SCI_STYLE_CALLTIP + revOffset] = scheme.calltipStyle
		styleMap[_SCI_STYLE_FOLDDISPLAYTEXT + revOffset] = scheme.foldDisplayTextStyle

		styleMap[_CAT_STYLE_CARETLINE] = scheme.caretLineStyle

		return styleMap

	def startStyling(self, pos: int, styleBits: int = ...) -> None:
		self._lastStylePos = pos
		super(DocumentLexerBase2, self).startStyling(pos)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	# @ProfiledFunction()
	def styleText(self, start: int, end: int):
		start = 0
		text: bytes = self.getText()
		tree = self.getTree()
		if tree is None or text is None:
			return

		stylerCtx = StylerCtxQScintilla(DEFAULT_STYLE_ID, start, self)
		styler = getStyler(tree.language, stylerCtx)
		if styler is not None:
			self.startStyling(start)
			styler.styleNode(tree)

		folder = Folder(self.editor())
		folder.add_folding(start, len(text) - start)


@dataclass
class StylerCtxQScintilla(StylerCtx):
	_lastStylePos: int
	lexer: QsciLexerCustom

	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		index = span.start
		if index > self._lastStylePos:
			interStrLength = index - self._lastStylePos
			assert interStrLength >= 0, interStrLength
			self.lexer.setStyling(interStrLength, _SCI_STYLE_LASTPREDEFINED + 1 + self.defaultStyle)  # styler.offset)

		if span.stop > self._lastStylePos:
			length = span.stop - index
			assert length >= 0, (length, style)
			self.lexer.setStyling(length, _SCI_STYLE_LASTPREDEFINED + 1 + style)
			self._lastStylePos = span.stop


@dataclass
class Folder:
	view: QsciScintilla

	def set_fold(self, prev, line, fold, full):
		view = self.view
		if (prev[0] >= 0):
			fmax = max(fold, prev[1])
			for iter in range(prev[0], line + 1):
				view.SendScintilla(view.SCI_SETFOLDLEVEL, iter,
					fmax | (0, view.SC_FOLDLEVELHEADERFLAG)[iter + 1 < full])

	def line_empty(self, line):
		view = self.view
		return view.SendScintilla(view.SCI_GETLINEENDPOSITION, line) \
			<= view.SendScintilla(view.SCI_GETLINEINDENTPOSITION, line)

	def modify(self, position: int, modificationType, text, length: int, linesAdded, line, foldLevelNow, foldLevelPrev, token, annotationLinesAdded):
		view = self.view
		full = view.SC_MOD_INSERTTEXT | view.SC_MOD_DELETETEXT
		if (~modificationType & full == full):
			return
		self.add_folding(position, length)

	def add_folding(self, position: int, length: int):
		view = self.view
		prev = [-1, 0]
		full = view.SendScintilla(view.SCI_GETLINECOUNT)
		lbgn = view.SendScintilla(view.SCI_LINEFROMPOSITION, position)
		lend = view.SendScintilla(view.SCI_LINEFROMPOSITION, position + length)
		for iter in range(max(lbgn - 1, 0), -1, -1):
			if ((iter == 0) or not self.line_empty(iter)):
				lbgn = iter
				break
		for iter in range(min(lend + 1, full), full + 1):
			if ((iter == full) or not self.line_empty(iter)):
				lend = min(iter + 1, full)
				break
		for iter in range(lbgn, lend):
			if (self.line_empty(iter)):
				if (prev[0] == -1):
					prev[0] = iter
			else:
				fold = view.SendScintilla(view.SCI_GETLINEINDENTATION, iter)
				fold //= view.SendScintilla(view.SCI_GETTABWIDTH)
				self.set_fold(prev, iter - 1, fold, full)
				self.set_fold([iter, fold], iter, fold, full)
				prev = [-1, fold]
		self.set_fold(prev, lend - 1, 0, full)


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
	def _editor(self) -> CodeEditor:
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
			return getContextProvider(doc.tree, doc.content)
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
			if doc.asyncValidate.isPending:
				doc.asyncValidate.callNow()

	@override
	def getHoverTip(self, cePosition: CEPosition) -> Optional[HTMLStr]:
		position = self.posFromCEPos(cePosition)
		errors = self._errors
		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		tips = [addStyle(e.htmlMessage, style=e.style) for e in matchedErrors]

		if (ctxProvider := self.contextProvider) is not None:
			tips.append(ctxProvider.getDocumentation(position))

		if not tips:
			return None
		tip = MDStr('\n\n'.join(tips))  # '\n<br/>\n'.join(tips)
		tip = formatMarkdown(tip)
		return tip

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
		editor = self._editor
		if (ctxProvider := self.contextProvider) is not None:
			ranges = ctxProvider.getClickableRanges()
			# return [r.asTuple for r in ranges]
			return [
				(
					editor.lineIndexFromPosition(r.start.index),
					editor.lineIndexFromPosition(r.end.index)
				)
				for r in ranges
			]
		return []

	@override
	def indicatorClicked(self, cePosition: CEPosition, state: Qt.KeyboardModifiers) -> None:
		editor = self._editor
		position = self.posFromCEPos(cePosition)

		if state != Qt.ControlModifier:
			return

		if (ctxProvider := self.contextProvider) is not None:
			ctxProvider.onIndicatorClicked(position, editor.window())
