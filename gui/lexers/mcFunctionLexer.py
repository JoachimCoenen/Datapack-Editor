from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, CodeEditorLexer
from Cat.utils import override
from gui.lexers.documentLexer import DocumentLexerBase, StyleStyle, StyleFont
from model.commands.command import MCFunction
from model.commands.tokenizer import TokenType, tokenizeMCFunction


styles = {
	TokenType.Default: StyleStyle(
		foreground=QColor(0x00, 0x00, 0x00),
		background=QColor(0xff, 0xff, 0xff),
		font=StyleFont("Consolas", QFont.Monospace, 8)
	),
	TokenType.Command       : StyleStyle(foreground=QColor(0x7f, 0x00, 0x7f)),
	TokenType.String        : StyleStyle(foreground=QColor(0x7f, 0x00, 0x00)),
	TokenType.Number        : StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
	TokenType.Constant      : StyleStyle(foreground=QColor(0x00, 0x00, 0xBf)),
	TokenType.TargetSelector: StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
	TokenType.Operator      : StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),
	TokenType.Keyword       : StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),

	TokenType.Complex       : StyleStyle(foreground=QColor(0x7f, 0x7f, 0x00)),

	TokenType.Comment       : StyleStyle(foreground=QColor(0x7f, 0x7f, 0x7f)),
	TokenType.Error         : StyleStyle(foreground=QColor(0xff, 0x00, 0x00)),
}


@CodeEditorLexer('MCFunction')
class LexerMCFunction(DocumentLexerBase):
	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)

	@override
	def getStyles(self) -> dict[TokenType, StyleStyle]:
		return {tk.value: s for tk, s in styles.items()}

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	def language(self):
		return "MCFunction"

	def description(self, style):
		if style < len(styles):
			description = "Custom lexer for the Minecrafts .mcfunction files"
		else:
			description = ""
		return description

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		# editor: QsciScintilla = self.editor()
		# pos: int = editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
		return ['.']  # ':', '#', '.']

	def styleText(self, start: int, end: int):
		start = 0

		doc = self.document()
		if doc is None:
			return
		text: str = self.document().content
		function = doc.tree
		if not isinstance(function, MCFunction):
			return

		tokens = tokenizeMCFunction(function)

		self.startStyling(start)
		lastPos: int = 0
		for token in tokens:
			index = token.span.start.index
			if index > lastPos:
				interStr = text[lastPos:index]
				interStrLength = len(bytearray(interStr, "utf-8"))
				self.setStyling(interStrLength, TokenType.Default.value)
			tokenLength = len(bytearray(token.text, "utf-8"))
			lastPos = index + len(token.text)
			self.setStyling(tokenLength, token.style.value)


def init():
	pass  # Don't delete!
