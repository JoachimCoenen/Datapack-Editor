from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, fields
from typing import TypeVar, Optional, cast, Sequence, Protocol, NewType

from PyQt5.Qsci import QsciLexerCustom, QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CallTipInfo
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override, HTMLStr
from gui.lexers.styler import getStyler
from gui.themes import theme
from gui.themes.theme import StyleFont, NotSet, StyleStyle, DEFAULT_STYLE_STYLE
from model.parsing.contextProvider import ContextProvider, getContextProvider
from model.parsing.tree import Node
from model.utils import GeneralError, Position, addStyle, MDStr, formatMarkdown
from session.documents import TextDocument

TT = TypeVar('TT')
TokenType = int


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


DEFAULT_STYLE: TokenType = 0


class DocumentLexerBase(QsciLexerCustom):

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		# Initialize all style colors
		self._document: Optional[TextDocument] = None
		self.initStyles(self.getStyles())

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

	def getTree(self) -> Optional[Node]:
		doc = self.document()
		if doc is None:
			return
		tree = doc.tree
		if isinstance(tree, Node):
			return tree
		return None

	def getText(self) -> Optional[str]:
		doc = self.document()
		if doc is None:
			return
		return doc.content

	def document(self) -> Optional[TextDocument]:
		return self._document

	def setDocument(self, document: Optional[TextDocument]) -> None:
		self._document = document


class DocumentLexerBase2(DocumentLexerBase):
	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		self._lastStylePos: int = 0

	# @override
	# def setDocument(self, document: Optional[TextDocument]) -> None:
	# 	super(LexerMCFunction, self).setDocument(document)
	# 	self.initStyles(self.getStyles())

	@override
	def getStyles(self) -> dict[StyleId, StyleStyle]:
		styles = {DEFAULT_STYLE_ID: DEFAULT_STYLE_STYLE}
		tree = self.getTree()
		if tree is not None:
			styler = getStyler(tree.language, lambda x, y: None)
			if styler is not None:
				styleIds = styler.allStyles
				scheme = theme.currentColorScheme()

				for name, styleId in styleIds.items():
					style = scheme.getStyle(*name.partition(':')[::2])
					if style is None:
						style = DEFAULT_STYLE_STYLE
					styles[styleId] = style

		return styles

	def startStyling(self, pos: int, styleBits: int = ...) -> None:
		self._lastStylePos = pos
		super(DocumentLexerBase2, self).startStyling(pos)

	def styleText(self, start: int, end: int):
		start = 0
		text: str = self.getText()
		tree = self.getTree()
		if tree is None or text is None:
			return

		def setStyling(span: slice, style: StyleId) -> None:
			index = span.start
			if index > self._lastStylePos:
				interStr = text[self._lastStylePos:index]
				interStrLength = len(bytearray(interStr, "utf-8"))
				self.setStyling(interStrLength, 0)  # styler.offset)

			token = text[index:span.stop]
			self._lastStylePos = span.stop
			length = len(bytearray(token, "utf-8"))

			self.setStyling(length, style)

		styler = getStyler(tree.language, setStyling)
		if styler is not None:
			self.startStyling(0)
			styler.styleNode(tree)


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


_TNode = TypeVar('_TNode', bound=Node)


class StylingFunc(Protocol):
	def __call__(self, length: int, style: int) -> None:
		...


StyleId = NewType('StyleId', int)

DEFAULT_STYLE_ID: StyleId = StyleId(0)


@dataclass
class Styler:
	pos: int
	styleOffset: int

	_encoding: Optional[str]
	_text: str
	_lexer: QsciLexerCustom

	def setStyling(self, length: int, style: StyleId) -> None:
		actualLength = length if self._encoding is None else len(bytearray(self._text[self.pos:length], self._encoding))
		self._lexer.setStyling(actualLength, style + self.styleOffset)
		self.pos += length


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
# 	def styles(self) -> list[StyleStyle]:
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
