from dataclasses import dataclass, field, fields
from typing import Optional, Sequence, cast, NewType

from PyQt5.Qsci import QsciLexer, QsciLexerCustom, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QGuiApplication

from base.gui.styler import DEFAULT_STYLE_ID, StyleId, StylerCtx, getStyler, CommonStyleIds
from base.model import theme
from base.model.documents import TextDocument
from base.model.parsing.contextProvider import ContextProvider, getContextProvider
from base.model.parsing.tree import Node
from base.model.searchUtils import performFuzzyStrSearch
from base.model.theme import Style, StyleFont
from base.model.utils import GeneralError, LanguageId, MDStr, NULL_POSITION, Position, addStyle, formatMarkdown
from cat.GUI.components.codeEditor import AutoCompletionTree, CEPosition, CallTipInfo, CodeEditor, MyQsciAPIs, \
	IndexSpan, IndicatorStyle
from cat.utils import HTMLStr, override
from cat.utils.logging_ import logError
from cat.utils.utils import CrashReportWrapped, runLaterSafe

SciStyleId = NewType('SciStyleId', int)

_SCI_STYLE_DEFAULT: SciStyleId = SciStyleId(32)  # This style defines the attributes that all styles receive when the SCI_STYLECLEARALL message is used.
_SCI_STYLE_LINENUMBER: SciStyleId = SciStyleId(33)  # This style sets the attributes of the text used to display line numbers in a line number margin. The background colour set for this style also sets the background colour for all margins that do not have any folding mask bits set. That is, any margin for which mask & SC_MASK_FOLDERS is 0. See SCI_SETMARGINMASKN for more about masks.
_SCI_STYLE_BRACELIGHT: SciStyleId = SciStyleId(34)  # This style sets the attributes used when highlighting braces with the SCI_BRACEHIGHLIGHT message and when highlighting the corresponding indentation with SCI_SETHIGHLIGHTGUIDE.
_SCI_STYLE_BRACEBAD: SciStyleId = SciStyleId(35)  # This style sets the display attributes used when marking an unmatched brace with the SCI_BRACEBADLIGHT message.
_SCI_STYLE_CONTROLCHAR: SciStyleId = SciStyleId(36)  # This style sets the font used when drawing control characters. Only the font, size, bold, italics, and character set attributes are used and not the colour attributes. See also: SCI_SETCONTROLCHARSYMBOL.
_SCI_STYLE_INDENTGUIDE: SciStyleId = SciStyleId(37)  # This style sets the foreground and background colours used when drawing the indentation guides.
_SCI_STYLE_CALLTIP: SciStyleId = SciStyleId(38)  # Call tips normally use the font attributes defined by STYLE_DEFAULT. Use of SCI_CALLTIPUSESTYLE causes call tips to use this style instead. Only the font face name, font size, foreground and background colours and character set attributes are used.
_SCI_STYLE_FOLDDISPLAYTEXT: SciStyleId = SciStyleId(39)  # This is the style used for drawing text tags attached to folded text.
_SCI_STYLE_LASTPREDEFINED: SciStyleId = SciStyleId(39)
_SCI_STYLE_FIRST_USER_STYLE: SciStyleId = SciStyleId(_SCI_STYLE_LASTPREDEFINED + 1)


def toSciStyleId(styleId: StyleId) -> SciStyleId:
	return SciStyleId(styleId + _SCI_STYLE_FIRST_USER_STYLE)


@dataclass
class ResolvedStyle:
	foreground: QColor
	background: QColor
	font: StyleFont


def resolveStyle(style: Style, default: ResolvedStyle) -> ResolvedStyle:
	return theme._mergeDataclass(default, style)  # type: ignore


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

	def __init__(self, parent=None) -> None:
		# Initialize superclass
		super().__init__(parent)
		# Initialize all style colors
		self._document: Optional[TextDocument] = None
		self._lastStylePos: int = 0
		self._languageIndicators: dict[LanguageId, int] = {}
		self._api: DocumentQsciAPIs = DocumentQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

		self.initStyles()

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

	def editor(self) -> CodeEditor | None:  # type: ignore
		return super().editor()  # type: ignore

	def setFoldMarginStyle(self, style: ResolvedStyle):
		if (editor := self.editor()) is not None:
			editor.setFoldMarginColors(style.background, style.background)

	def setCaretLineStyle(self, style: ResolvedStyle):
		if (editor := self.editor()) is not None:
			editor.setCaretLineBackgroundColor(style.background)

	def setCaretStyle(self, style: ResolvedStyle):
		if (editor := self.editor()) is not None:
			editor.setCaretForegroundColor(style.foreground)

	def setWhitespaceStyle(self, style: ResolvedStyle):
		if (editor := self.editor()) is not None:
			editor.SendScintilla(CodeEditor.SCI_SETWHITESPACEFORE, True, _qColorToSciRGB(style.foreground))
			editor.SendScintilla(CodeEditor.SCI_SETWHITESPACEBACK, False, _qColorToSciRGB(style.background))

	def initStyle(self, style: ResolvedStyle, styleId: SciStyleId) -> None:
		self.setColor(style.foreground, styleId)
		self.setPaper(style.background, styleId)
		self.setFont(QFontFromStyleFont(style.font), styleId)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	def initStyles(self) -> None:
		fallbackStyle = ResolvedStyle(
			foreground=self.defaultColor(),
			background=self.defaultPaper(),
			font=StyleFontFromQFont(self.defaultFont()),
		)
		scheme = theme.currentColorScheme()
		globalStyles = scheme.globalStyles

		# handle default first:
		default = resolveStyle(globalStyles.defaultStyle, fallbackStyle)
		self.setDefaultColor(default.foreground)
		self.setDefaultPaper(default.background)
		super().setDefaultFont(QFontFromStyleFont(default.font))
		self.setColor(default.foreground, 0)
		self.setPaper(default.background, 0)

		self.setCaretLineStyle(resolveStyle(globalStyles.caretLineStyle, default))
		self.setCaretStyle(resolveStyle(globalStyles.caretStyle, default))
		self.setWhitespaceStyle(resolveStyle(globalStyles.whiteSpaceStyle, default))
		self.setFoldMarginStyle(resolveStyle(globalStyles.lineNumberStyle, default))

		self.initStyle(default, toSciStyleId(DEFAULT_STYLE_ID))
		self.initStyle(default, _SCI_STYLE_DEFAULT)
		self.initStyle(resolveStyle(globalStyles.lineNumberStyle, default), _SCI_STYLE_LINENUMBER)
		self.initStyle(resolveStyle(globalStyles.braceLightStyle, default), _SCI_STYLE_BRACELIGHT)
		self.initStyle(resolveStyle(globalStyles.braceBadStyle, default), _SCI_STYLE_BRACEBAD)
		self.initStyle(resolveStyle(globalStyles.controlCharStyle, default), _SCI_STYLE_CONTROLCHAR)
		self.initStyle(resolveStyle(globalStyles.indentGuideStyle, default), _SCI_STYLE_INDENTGUIDE)
		self.initStyle(resolveStyle(globalStyles.calltipStyle, default), _SCI_STYLE_CALLTIP)
		self.initStyle(resolveStyle(globalStyles.foldDisplayTextStyle, default), _SCI_STYLE_FOLDDISPLAYTEXT)

		syntaxHighlightingStyles = scheme.syntaxHighlightingCommonStyles
		for styleId in CommonStyleIds:
			if styleId.name != 'default':
				style = getattr(syntaxHighlightingStyles, styleId.name)
				sciStyleId = toSciStyleId(styleId.value)
				self.initStyle(resolveStyle(style, default), sciStyleId)

		self.initLanguageIndicators(scheme.languageIndicators)

	def initLanguageIndicators(self, indicators: dict[LanguageId, IndicatorStyle]) -> None:
		self._languageIndicators = {languageId: i for i, languageId in enumerate(indicators.keys())}
		if (editor := self.editor()) is not None:
			editor.initIndicatorStyles({
				i: indicators[languageId] for languageId, i in self._languageIndicators.items()
			})

	def setDefaultFont(self, font: QFont):
		super().setDefaultFont(font)
		self.initStyles()

	def setFont(self, font: QFont, style=-1):
		super().setFont(font, style)

	def getTree(self) -> Optional[Node]:
		doc = self.document()
		if doc is None:
			return None
		tree = doc.tree
		if isinstance(tree, Node):
			return tree
		return None

	def getText(self) -> Optional[bytes]:
		doc = self.document()
		if doc is None:
			return None
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

	@CrashReportWrapped
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
		documentText = self.getText()
		lengthOfDocumentText = len(documentText) if documentText is not None else None
		editor = self.editor()
		if editor is not None and editor.length() != lengthOfDocumentText:
			# no need to style anything if the document text does not match the current text in the editor. This avoids unnecessary parsing.
			# This also prevents this assertion failing when editing text at the very end of a document:
			# Assertion [lengthStyle == 0 || (lengthStyle > 0 && lengthStyle + position <= style.Length())] failed at ../../tmpym18yovx/QScintilla2/QScintilla_src-2.14.1/scintilla/src/CellBuffer.cpp 635
			return
		tree = self.getTree()
		if tree is None:
			return

		self.clearLanguageIndicatorRanges(start, end)

		stylerCtx = StylerCtxQScintilla(DEFAULT_STYLE_ID, start, end, self._languageIndicators, self)
		styler = getStyler(tree.language, stylerCtx)
		if styler is not None:
			self.startStyling(start)
			styler.styleNode(tree)

	def clearLanguageIndicatorRanges(self, start: int, end: int) -> None:
		editor = self.editor()
		if editor is not None:
			for indicator in self._languageIndicators.values():
				editor.clearIndicatorRangeIndex(start, end, indicator)

	# @TimedMethod(objectName=lambda self: self.document().fileName if self.document() is not None else 'None')
	# @ProfiledFunction()
	def actuallyFoldText(self, start: int, end: int):
		folder = Folder(self.editor())
		folder.add_folding(start, end - start)

	def wordCharacters(self) -> str:
		return self._api.wordCharacters()

	def autoCompletionWordSeparators(self) -> list[str]:
		return self._api.autoCompletionWordSeparators()
		#return ['.']  # ':', '#', '.']


@dataclass
class StylerCtxQScintilla(StylerCtx):
	_lastStylePos: int = field(init=False)
	languageIndicators: dict[LanguageId, int]
	lexer: DocumentLexer

	def __post_init__(self):
		self._lastStylePos = self.start

	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		index = span.start
		if index > self.end:
			return
		if index > self._lastStylePos:
			interStrLength = index - self._lastStylePos
			assert interStrLength >= 0, interStrLength
			self.lexer.setStyling(interStrLength, toSciStyleId(self.defaultStyle))  # styler.offset)
			self._lastStylePos = index
		else:
			index = self._lastStylePos
		if span.stop > self._lastStylePos:
			length = span.stop - index
			assert length >= 0, (length, style)
			self.lexer.setStyling(length, toSciStyleId(style))
			self._lastStylePos = span.stop

	def setForeignLanguage(self, span: slice, languageId: LanguageId) -> None:
		editor = self.lexer.editor()
		if editor is not None:
			if (indicator := self.languageIndicators.get(languageId)) is not None:
				editor.fillIndicatorRangeIndex(span.start, span.stop, indicator)


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
		return formatMarkdown(tip)

	@override
	def getCallTips(self, cePosition: CEPosition) -> list[CallTipInfo] | None:
		self.updateDocumentTree()
		position = self.posFromCEPos(cePosition)
		if (ctxProvider := self.contextProvider) is not None:
			return [CallTipInfo(ct, HTMLStr('')) for ct in ctxProvider.getCallTips(position)]
		return None

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

		try:
			if (ctxProvider := self.contextProvider) is not None:
				replaceCtx = context[-1] if context else ''
				position = self.currentCursorPos
				suggestions = ctxProvider.getSuggestions(position, replaceCtx)
				suggestions2 = performFuzzyStrSearch(suggestions, replaceCtx)
				return [sr.fe for sr in suggestions2.results]
		except Exception as e:
			logError(e)
			return [f"<>ERROR: {e}! see logfile<>"]

		return super().updateAutoCompletionList(context, aList)

	@override
	def getClickableRanges(self) -> list[IndexSpan]:
		editor = self._editor
		if editor is not None and (ctxProvider := self.contextProvider) is not None:
			ranges = ctxProvider.getClickableRanges()
			return [IndexSpan(r.start.index, r.end.index) for r in ranges]
		return []

	@override
	def indicatorClicked(self, cePosition: CEPosition, state: Qt.KeyboardModifiers) -> None:
		if QGuiApplication.keyboardModifiers() != Qt.ControlModifier:  # 'state' is broken on Wayland
			return

		if (ctxProvider := self.contextProvider) is not None:
			position = self.posFromCEPos(cePosition)
			ctxProvider.onIndicatorClicked(position)

	@override
	def wordCharacters(self) -> str:
		if (ctxProvider := self.contextProvider) is not None:
			wordCharacters = ctxProvider.getWordCharacters(self.currentCursorPos)
			if wordCharacters is not None:
				return wordCharacters
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"
		# return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

	@override
	def autoCompletionWordSeparators(self) -> list[str]:
		if (ctxProvider := self.contextProvider) is not None:
			return ctxProvider.getAutoCompletionWordSeparators(self.currentCursorPos)
		return []  # ['.']  # ':', '#', '.']
