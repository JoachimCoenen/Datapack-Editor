from dataclasses import dataclass, field, fields
from typing import Optional, Sequence, cast

from PyQt5.Qsci import QsciLexer, QsciLexerCustom, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from base.gui.styler import DEFAULT_STYLE_ID, StyleId, StylerCtx, getStyler
from base.model import theme
from base.model.documents import TextDocument
from base.model.parsing.contextProvider import ContextProvider, getContextProvider
from base.model.parsing.tree import Node
from base.model.searchUtils import performFuzzyStrSearch
from base.model.theme import GlobalStyles, Style, StyleFont
from base.model.utils import GeneralError, LanguageId, MDStr, NULL_POSITION, Position, addStyle, formatMarkdown
from cat.GUI.components.codeEditor import AutoCompletionTree, CEPosition, CallTipInfo, CodeEditor, MyQsciAPIs
from cat.utils import HTMLStr, override
from cat.utils.logging_ import logWarning
from cat.utils.utils import CrashReportWrapped, runLaterSafe

_SCI_STYLE_DEFAULT = StyleId(32)  # This style defines the attributes that all styles receive when the SCI_STYLECLEARALL message is used.
_SCI_STYLE_LINENUMBER = StyleId(33)  # This style sets the attributes of the text used to display line numbers in a line number margin. The background colour set for this style also sets the background colour for all margins that do not have any folding mask bits set. That is, any margin for which mask & SC_MASK_FOLDERS is 0. See SCI_SETMARGINMASKN for more about masks.
_SCI_STYLE_BRACELIGHT = StyleId(34)  # This style sets the attributes used when highlighting braces with the SCI_BRACEHIGHLIGHT message and when highlighting the corresponding indentation with SCI_SETHIGHLIGHTGUIDE.
_SCI_STYLE_BRACEBAD = StyleId(35)  # This style sets the display attributes used when marking an unmatched brace with the SCI_BRACEBADLIGHT message.
_SCI_STYLE_CONTROLCHAR = StyleId(36)  # This style sets the font used when drawing control characters. Only the font, size, bold, italics, and character set attributes are used and not the colour attributes. See also: SCI_SETCONTROLCHARSYMBOL.
_SCI_STYLE_INDENTGUIDE = StyleId(37)  # This style sets the foreground and background colours used when drawing the indentation guides.
_SCI_STYLE_CALLTIP = StyleId(38)  # Call tips normally use the font attributes defined by STYLE_DEFAULT. Use of SCI_CALLTIPUSESTYLE causes call tips to use this style instead. Only the font face name, font size, foreground and background colours and character set attributes are used.
_SCI_STYLE_FOLDDISPLAYTEXT = StyleId(39)  # This is the style used for drawing text tags attached to folded text.
_SCI_STYLE_LASTPREDEFINED = StyleId(39)
_SCI_STYLE_FIRST_USER_STYLE = _SCI_STYLE_LASTPREDEFINED + 1
_CAT_STYLE_CARETLINE = StyleId(-257)
_CAT_STYLE_CARET = StyleId(-258)
_CAT_STYLE_WHITE_SPACE = StyleId(-300)

_SC_ELEMENT_WHITE_SPACE = 60
_SC_ELEMENT_WHITE_SPACE_BACK = 61

_CAT_SCI_ELEMENT_COLOR_IDS = {
	_CAT_STYLE_WHITE_SPACE: (_SC_ELEMENT_WHITE_SPACE, _SC_ELEMENT_WHITE_SPACE_BACK)
}


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


def _twosComp32(n: int) -> int:
	# Thanks c, that we have to do this. :/
	return n - 0x100000000 if n & 0x80000000 else n


def _qColorToSciRGB(c: QColor) -> int:
	return _twosComp32(c.red() + (c.green() << 8) + (c.blue() << 16))


def _qColorToSciRGBA(c: QColor) -> int:
	return _twosComp32(c.red() + (c.green() << 8) + (c.blue() << 16) + (c.alpha() << 24))


class DocumentLexer(QsciLexerCustom):  # this is an ABC, but there would be a metaclass conflict.

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		# Initialize all style colors
		self._document: Optional[TextDocument] = None
		self._lastStylePos: int = 0
		self._api: DocumentQsciAPIs = DocumentQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

		self.initStyles(self.getStyles(), overwriteDefaultStyle=True)

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	@property
	def languageId(self) -> Optional[LanguageId]:
		if (doc := self.document()) is not None:
			return doc.language
		# if (tree := self.getTree()) is not None:
		# 	# TODO: remove properly: return tree.language
		return None

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	def getStyles(self) -> dict[StyleId, Style]:
		scheme = theme.currentColorScheme()

		styleMap = {}  # {DEFAULT_STYLE_ID: scheme.defaultStyle}
		self.addGlobalStyles(scheme.globalStyles, styleMap)

		languageId = self.languageId
		if languageId is None:
			return styleMap

		styles = scheme.getStyles2(languageId)
		if styles is None:
			return styleMap

		styler = getStyler(languageId, StylerCtxQScintilla(DEFAULT_STYLE_ID, 0, 0, self))
		if styler is None:
			return styleMap

		for innerLanguage, styler in styler.innerStylers.items():
			innerStyles = styles.getInnerLanguageStyles(innerLanguage)
			if innerStyles is None:
				continue
			for name, styleId in styler.localStyles.items():
				style = innerStyles.get(name)
				if style is None:
					logWarning(f"Theme '{scheme.name}' is missing style '{name}' for language '{innerLanguage}'")
					style = styleMap[_SCI_STYLE_DEFAULT - _SCI_STYLE_FIRST_USER_STYLE]
				# elif styleId == DEFAULT_STYLE_ID:
				# 	style = scheme.globalStyles.defaultStyle | style
				styleMap[styleId] = style
		return styleMap

	def addGlobalStyles(self, globalStyles: GlobalStyles, styleMap: dict[int, Style]):
		revOffset = -_SCI_STYLE_FIRST_USER_STYLE
		styleMap[DEFAULT_STYLE_ID] = globalStyles.defaultStyle
		styleMap[_SCI_STYLE_DEFAULT + revOffset] = globalStyles.defaultStyle

		styleMap[_SCI_STYLE_LINENUMBER + revOffset] = globalStyles.lineNumberStyle
		styleMap[_SCI_STYLE_BRACELIGHT + revOffset] = globalStyles.braceLightStyle
		styleMap[_SCI_STYLE_BRACEBAD + revOffset] = globalStyles.braceBadStyle
		styleMap[_SCI_STYLE_CONTROLCHAR + revOffset] = globalStyles.controlCharStyle
		styleMap[_SCI_STYLE_INDENTGUIDE + revOffset] = globalStyles.indentGuideStyle
		styleMap[_SCI_STYLE_CALLTIP + revOffset] = globalStyles.calltipStyle
		styleMap[_SCI_STYLE_FOLDDISPLAYTEXT + revOffset] = globalStyles.foldDisplayTextStyle
		styleMap[_CAT_STYLE_CARETLINE] = globalStyles.caretLineStyle
		styleMap[_CAT_STYLE_CARET] = globalStyles.caretStyle
		styleMap[_CAT_STYLE_WHITE_SPACE] = globalStyles.whiteSpaceStyle

	def setCaretLineStyle(self, style: Style):
		editor: CodeEditor = self.editor()
		if editor is not None:
			editor.setCaretLineBackgroundColor(style.background)

	def setCaretStyle(self, style: Style):
		editor: CodeEditor = self.editor()
		if editor is not None:
			editor.setCaretForegroundColor(style.foreground)

	def setElementStyle(self, styleId: StyleId, style: Style):
		editor: CodeEditor = self.editor()
		if editor is not None:
			if styleId == _CAT_STYLE_WHITE_SPACE:
				editor.SendScintilla(CodeEditor.SCI_SETWHITESPACEFORE, True, _qColorToSciRGB(style.foreground))
				editor.SendScintilla(CodeEditor.SCI_SETWHITESPACEBACK, False, _qColorToSciRGB(style.background))
			else:
				elementIds = _CAT_SCI_ELEMENT_COLOR_IDS[styleId]
				if elementIds[0] is not None:
					editor.SendScintilla(CodeEditor.SCI_SETELEMENTCOLOUR, elementIds[0], _qColorToSciRGBA(style.foreground))
				if elementIds[1] is not None:
					editor.SendScintilla(CodeEditor.SCI_SETELEMENTCOLOUR, elementIds[1], _qColorToSciRGBA(style.background))

	def initStyle(self, style: Style, styleId: int) -> None:
		actualId = styleId + _SCI_STYLE_FIRST_USER_STYLE
		self.setColor(style.foreground, actualId)
		self.setPaper(style.background, actualId)
		self.setFont(QFontFromStyleFont(style.font), actualId)

	def initStyles(self, styles: dict[StyleId, Style], overwriteDefaultStyle: bool = False):
		defaultStyle = Style(
			foreground=self.defaultColor(),
			background=self.defaultPaper(),
			font=StyleFontFromQFont(self.defaultFont()),
		)
		# handle default first:
		if overwriteDefaultStyle:
			defStyle = styles[cast(StyleId, _SCI_STYLE_DEFAULT - _SCI_STYLE_FIRST_USER_STYLE)]
			defaultStyle = defaultStyle | defStyle
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
			elif tokenType == _CAT_STYLE_CARET:
				self.setCaretStyle(actualStyle)
			elif tokenType in _CAT_SCI_ELEMENT_COLOR_IDS:
				self.setElementStyle(tokenType, actualStyle)
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
		# self.initStyles(self.getStyles())

	def description(self, p_int):
		return ''

	def startStyling(self, pos: int, styleBits: int = ...) -> None:
		self._lastStylePos = pos
		super(DocumentLexer, self).startStyling(pos)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	# @ProfiledFunction()
	def styleText(self, start: int, end: int):
		# text: bytes = self.getText()
		# start = 0
		# end = len(text)

		self.actuallyStyleText(start, end)
		self.actuallyFoldText(start, end)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	# @ProfiledFunction()
	def actuallyStyleText(self, start: int, end: int):
		tree = self.getTree()
		if tree is None:
			return

		stylerCtx = StylerCtxQScintilla(DEFAULT_STYLE_ID, start, end, self)
		styler = getStyler(tree.language, stylerCtx)
		if styler is not None:
			self.startStyling(start)
			styler.styleNode(tree)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	# @ProfiledFunction()
	def actuallyFoldText(self, start: int, end: int):
		folder = Folder(self.editor())
		folder.add_folding(start, end - start)

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		return ['.']  # ':', '#', '.']


@dataclass
class StylerCtxQScintilla(StylerCtx):
	_lastStylePos: int = field(init=False)
	lexer: QsciLexerCustom

	def __post_init__(self):
		self._lastStylePos = self.start

	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		index = span.start
		if index > self.end:
			return
		if index > self._lastStylePos:
			interStrLength = index - self._lastStylePos
			assert interStrLength >= 0, interStrLength
			self.lexer.setStyling(interStrLength, _SCI_STYLE_FIRST_USER_STYLE + self.defaultStyle)  # styler.offset)
			self._lastStylePos = index
		else:
			index = self._lastStylePos
		if span.stop > self._lastStylePos:
			length = span.stop - index
			assert length >= 0, (length, style)
			self.lexer.setStyling(length, _SCI_STYLE_FIRST_USER_STYLE + style)
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
		runLaterSafe(0, lambda: (self._editor is not None) and (self._editor.showCallTips() or self._editor.myStartAutoCompletion()))

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
		lexer: DocumentLexer = cast(DocumentLexer, self.lexer())
		assert isinstance(lexer, DocumentLexer)
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
		index = editor.positionFromLineIndex(*cePosition) if editor is not None else -1
		return Position(cePosition.line, cePosition.column, index)

	@property
	def currentCursorPos(self) -> Position:
		editor = self._editor
		if editor is not None:
			return self.posFromCEPos(CEPosition(*editor.getCursorPosition()))
		return NULL_POSITION

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
			replaceCtx = context[-1] if context else ''
			position = self.currentCursorPos
			suggestions = ctxProvider.getSuggestions(position, replaceCtx)
			suggestions2 = performFuzzyStrSearch(suggestions, replaceCtx)
			return [sr.fe for sr in suggestions2.results]

		return super().updateAutoCompletionList(context, aList)

	@override
	def getClickableRanges(self) -> list[tuple[CEPosition, CEPosition]]:
		editor = self._editor
		if editor is not None and (ctxProvider := self.contextProvider) is not None:
			ranges = ctxProvider.getClickableRanges()
			return [
				(
					editor.cePositionFromIndex(r.start.index),
					editor.cePositionFromIndex(r.end.index)
				)
				for r in ranges
			]
		return []

	@override
	def indicatorClicked(self, cePosition: CEPosition, state: Qt.KeyboardModifiers) -> None:
		if state != Qt.ControlModifier:
			return

		if (ctxProvider := self.contextProvider) is not None:
			position = self.posFromCEPos(cePosition)
			ctxProvider.onIndicatorClicked(position)
