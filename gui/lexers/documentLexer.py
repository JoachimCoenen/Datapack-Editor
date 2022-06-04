from __future__ import annotations

from abc import abstractmethod
from dataclasses import fields, dataclass
from typing import TypeVar, Optional, cast, Sequence

from PyQt5.Qsci import QsciLexerCustom, QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CallTipInfo
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override, HTMLStr
from Cat.utils.logging_ import logWarning
from Cat.utils.profiling import TimedMethod, ProfiledFunction, TimedAction
from gui.lexers.styler import getStyler, StyleId, DEFAULT_STYLE_ID, StylerCtx
from gui.themes import theme
from gui.themes.theme import StyleFont, Style, DEFAULT_STYLE_STYLE, mergeVal, _getWithDefaultsFilled
from model.parsing.contextProvider import ContextProvider, getContextProvider
from model.parsing.tree import Node
from model.utils import GeneralError, Position, addStyle, MDStr, formatMarkdown, LanguageId
from session.documents import TextDocument

TT = TypeVar('TT')
TokenType = int


_SCI_STYLE_LASTPREDEFINED = 39


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


DEFAULT_STYLE: TokenType = 0


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

	def initStyles(self, styles: dict[TokenType, Style], overwriteDefaultStyle: bool = False):
		# handle default first:
		if overwriteDefaultStyle:
			defaultStyle = styles[DEFAULT_STYLE]
			defaultFont = _getWithDefaultsFilled(defaultStyle.font)
			defaultQFont = QFontFromStyleFont(defaultFont)
			defaultQFont.setPointSize(self.defaultFont().pointSize())

			self.setDefaultColor(defaultStyle.foreground)
			self.setDefaultPaper(defaultStyle.background)
			super(DocumentLexerBase, self).setDefaultFont(defaultQFont)

		defaultForeground: QColor = self.defaultColor()
		defaultBackground: QColor = self.defaultPaper()
		defaultFont: StyleFont = StyleFontFromQFont(self.defaultFont())

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
				font = mergeVal(defaultFont, style.font)

			font = _getWithDefaultsFilled(font)
			qFont = QFontFromStyleFont(font)

			self.setColor(foreground, tokenType + _SCI_STYLE_LASTPREDEFINED + 1)
			self.setPaper(background, tokenType + _SCI_STYLE_LASTPREDEFINED + 1)
			self.setFont(qFont, tokenType + _SCI_STYLE_LASTPREDEFINED + 1)

	def setDefaultFont(self, font: QFont):
		super().setDefaultFont(font)
		self.initStyles(self.getStyles(), overwriteDefaultStyle=True)

	def setFont(self, font: QFont, style=-1):
		if style == -1:
			self.setDefaultFont(font)
		else:
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

		return styleMap

	# @override
	# def getStyles(self) -> dict[StyleId, Style]:
	# 	styleMap = {DEFAULT_STYLE_ID: DEFAULT_STYLE_STYLE}
	# 	languageId = self.languageId
	# 	if languageId is not None:
	# 		styler = getStyler(languageId, lambda x, y: None)
	# 		if styler is not None:
	# 			scheme = theme.currentColorScheme()
	# 			styles = scheme.getStyles2(languageId)
	#
	# 			styleIds = styler.allStylesIds
	# 			for name, styleId in styleIds.items():
	# 				lang, styleName = name.partition(':')[::2]
	# 				style = scheme.getStyle(lang, styleName)
	# 				if style is None:
	# 					style = DEFAULT_STYLE_STYLE
	# 				style = styles.modifyStyle(lang, style)
	# 				styleMap[styleId] = style
	#
	# 	return styleMap

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

		# def setStyling(span: slice, style: StyleId) -> None:
		# 	index = span.start
		# 	if index > self._lastStylePos:
		# 		interStr = text[self._lastStylePos:index]
		# 		interStrLength = len(bytearray(interStr, "utf-8"))
		# 		self.setStyling(interStrLength, 0)  # styler.offset)
		#
		# 	token = text[index:span.stop]
		# 	self._lastStylePos = span.stop
		# 	length = len(bytearray(token, "utf-8"))
		#
		# 	self.setStyling(length, style)

		stylerCtx = StylerCtxQScintilla(DEFAULT_STYLE_ID, start, self)
		styler = getStyler(tree.language, stylerCtx)
		if styler is not None:
			self.startStyling(start)
			styler.styleNode(tree)


@dataclass
class StylerCtxQScintilla(StylerCtx):
	_lastStylePos: int
	lexer: QsciLexerCustom

	def setStylingUtf8(self, span: slice, style: StyleId) -> None:
		index = span.start
		if index > self._lastStylePos:
			interStrLength = index - self._lastStylePos
			assert interStrLength >= 0
			self.lexer.setStyling(interStrLength, _SCI_STYLE_LASTPREDEFINED + 1 + self.defaultStyle)  # styler.offset)

		length = span.stop - index
		assert length >= 0
		self.lexer.setStyling(length, _SCI_STYLE_LASTPREDEFINED + 1 + style)

		self._lastStylePos = span.stop


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


# _TNode = TypeVar('_TNode', bound=Node)
#
#
# class StylingFunc(Protocol):
# 	def __call__(self, length: int, style: int) -> None:
# 		...
#
#
# StyleId = NewType('StyleId', int)
#
# DEFAULT_STYLE_ID: StyleId = StyleId(0)
#

# @dataclass
# class Styler:
# 	pos: int
# 	styleOffset: int
#
# 	_encoding: Optional[str]
# 	_text: str
# 	_lexer: QsciLexerCustom
#
# 	def setStyling(self, length: int, style: StyleId) -> None:
# 		actualLength = length if self._encoding is None else len(bytearray(self._text[self.pos:length], self._encoding))
# 		self._lexer.setStyling(actualLength, style + self.styleOffset)
# 		self.pos += length


# @dataclass
# class CatLexerBase(Generic[_TNode], ABC):
#
# 	styleIdOffsets: dict[str, int] = field(default_factory=dict)
#
# 	@property
# 	@abstractmethod
# 	def language(self) -> str:
# 		pass
#
# 	@property
# 	@abstractmethod
# 	def styles(self) -> list[Style]:
# 		pass
#
# 	@property
# 	def totalStylesCount(self) -> int:
# 		return sum(map(lambda x: x.totalStylesCount, self.innerLexers), len(self.styles))
#
# 	@property
# 	@abstractmethod
# 	def innerStyler(self) -> list[CatLexerBase]:
# 		pass
#
# 	def initStyleOffsets(self) -> None:
# 		offset = len(self.styles)
# 		for styler in self.innerStyler:
# 			if styler.language in self.styleIdOffsets:
# 				raise ValueError(f"innerLexer for language '{styler.language}' defined twice in lexer '{self.language}'")
# 			self.styleIdOffsets[styler.language] = offset
# 			styler.initStyleOffsets()
#
# 	@abstractmethod
# 	def styleText(self, start: int, end: int, startStyling: Callable[[int], None], setStyle: StylingFunc):
# 		pass
#
# 	def setStyling(self, length: int, style: int) -> None:
# 		assert (length >= 0)
# 		doc = self.document()
# 		if doc is not None:
# 			text = doc.content[self._lastStylePos:self._lastStylePos + length]
# 			self._lastStylePos += length
# 			length = len(bytearray(text, "utf-8"))
#
# 		super(LexerJson, self).setStyling(length, style)
