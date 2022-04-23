from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, CodeEditorLexer
from gui.lexers.documentLexer import DocumentLexerBase2


@CodeEditorLexer('MCFunction')
class LexerMCFunction(DocumentLexerBase2):
	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	def language(self):
		return "MCFunction"

	def description(self, style):
		return "Custom lexer for the Minecrafts .mcfunction files"

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		# editor: QsciScintilla = self.editor()
		# pos: int = editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
		return ['.']  # ':', '#', '.']


def init():
	pass  # Don't delete!
