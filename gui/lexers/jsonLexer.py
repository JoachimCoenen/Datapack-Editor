from __future__ import annotations

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, CodeEditorLexer
from gui.lexers.documentLexer import DocumentLexerBase2


@CodeEditorLexer('MCJson', forceOverride=True)
class LexerJson(DocumentLexerBase2):
	# defaultStyles = {style[0]: style[1] for style in styles.items()}

	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		# self._lastStylePos: int = 0

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	def language(self):
		return "JSON"

	def description(self, style):
		return "Custom lexer for the Minecrafts .json files"

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		return ['.']  # ':', '#', '.']


def init():
	pass  # Don't delete!
