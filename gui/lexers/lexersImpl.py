from Cat.CatPythonGUI.GUI.codeEditor import CodeEditorLexer
from base.gui.documentLexer import DocumentLexerBase2


@CodeEditorLexer('JSON', forceOverride=True)
class LexerJson(DocumentLexerBase2):
	def language(self):
		return "JSON"

	def description(self, style):
		return "Custom lexer for the Minecrafts .json files"


@CodeEditorLexer('MCFunction')
class LexerMCFunction(DocumentLexerBase2):
	def language(self):
		return "MCFunction"

	def description(self, style):
		return "Custom lexer for the Minecrafts .mcfunction files"


@CodeEditorLexer('SNBT')
class LexerSNBT(DocumentLexerBase2):
	def language(self):
		return "SNBT"

	def description(self, style):
		return "Custom lexer for the Minecrafts SNBT format"


def init():
	pass  # Don't delete!
