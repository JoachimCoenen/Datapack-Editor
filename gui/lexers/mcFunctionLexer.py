from typing import Optional, Iterable, cast

from PyQt5.Qsci import QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CodeEditorLexer
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override
from gui.lexers.documentLexer import DocumentLexerBase, StyleStyle, StyleFont
from model.commands.argumentHandlers import getArgumentHandler, defaultDocumentationProvider
from model.commands.command import ArgumentInfo, Keyword, Switch, CommandNode, TERMINAL, COMMANDS_ROOT
from model.commands.parsedCommands import ParsedMCFunction, ParsedCommandPart, ParsedComment, ParsedArgument
from model.commands.parser import parseMCFunction
from model.commands.tokenizer import TokenType, tokenizeMCFunction
from model.utils import Position
from session.session import getSession


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


class McFunctionQsciAPIs(MyQsciAPIs):
	def __init__(self, lexer: Optional[QsciLexer]):
		super(MyQsciAPIs, self).__init__(lexer)
		self._autoCompletionTree: AutoCompletionTree = AutoCompletionTree('', '')

	@property
	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._autoCompletionTree

	@autoCompletionTree.setter
	def autoCompletionTree(self, value: AutoCompletionTree):
		self._autoCompletionTree = value

	# def getApiContext(self, pos: int, self) -> tuple[List[str], int, int]:

	def _getBestMatch(self, tree: ParsedCommandPart, bestMatch: Optional[ParsedCommandPart], pos: Position) -> Optional[ParsedCommandPart]:
		child = tree
		while child is not None:
			if pos >= child.end:
				bestMatch = child
			elif pos >= child.start:
				bestMatch = child
			elif pos > child.start:
				break
			child = child.next
		return bestMatch

	def getBestMatch(self, tree: ParsedMCFunction, pos: Position) -> Optional[ParsedCommandPart]:
		bestMatch: Optional[ParsedCommandPart] = None
		children = tuple(tree.children)
		for child in children:
			if child.span.start < pos <= child.span.end:
				if isinstance(child, ParsedComment):
					continue
				bestMatch = self._getBestMatch(child, bestMatch, pos)
		return bestMatch

	@override
	def getHoverTip(self, cePosition: CEPosition) -> Optional[str]:
		lexer: LexerMCFunction = cast(LexerMCFunction, self.lexer())
		editor: QsciScintilla = lexer.editor()
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		doc = lexer.document()
		if doc is None:
			return None

		errors = doc.errors

		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		tips = [f'<div style="{PythonGUI.helpBoxStyles.get(e.style, "")}">{e.message}</div>' for e in matchedErrors]

		function = doc.tree
		if isinstance(function, ParsedMCFunction):
			match = self.getBestMatch(function, position)
			if match is not None:
				info = match.info
				if info is not None:
					type_ = getattr(info, 'type', None)
					handler = getArgumentHandler(type_) if type_ is not None else None
					if handler is None:
						documentationProvider = defaultDocumentationProvider
					else:
						documentationProvider = handler.getDocumentation
					tips.append(documentationProvider(match))
				else:
					pass
		if not tips:
			return None
		tip = '<br/>'.join(tips)
		return f"{tip}"

	def _getNextKeywords(self, nexts: Iterable[CommandNode], contextStr: str, cursorPos: int, replaceCtx: str) -> list[str]:
		result = []
		for nx in nexts:
			if isinstance(nx, Keyword):
				result.append(nx.name)
			elif isinstance(nx, Switch):
				result += self._getNextKeywords(nx.options, contextStr, cursorPos, replaceCtx)
				hasTerminal = TERMINAL in nx.options
				if hasTerminal:
					result += self._getNextKeywords(nx.next, contextStr, cursorPos, replaceCtx)
			elif isinstance(nx, ArgumentInfo):
				handler = getArgumentHandler(nx.type)
				if handler is not None:
					result += handler.getSuggestions(nx, contextStr, cursorPos, replaceCtx)
			elif nx is COMMANDS_ROOT:
				result += list(getSession().minecraftData.commands.keys())
		return result

	@CrashReportWrapped
	def updateAutoCompletionList(self, context: list[str], aList: list[str]) -> list[str]:
		"""
		Update the list \a list with API entries derived from \a context.  \a
		context is the list of words in the text preceding the cursor position.
		The characters that make up a word and the characters that separate
		words are defined by the lexer.  The last word is a partial word and
		may be empty if the user has just entered a word separator.
		"""
		lexer: LexerMCFunction = cast(LexerMCFunction, self.lexer())
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()
		cePosition = CEPosition(*editor.getCursorPosition())
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		doc = lexer.document()
		if doc is None:
			return super().updateAutoCompletionList(context, aList)
		function = doc.tree
		if not isinstance(function, ParsedMCFunction):
			return super().updateAutoCompletionList(context, aList)
		# function, errors = parseMCFunction(getSession().minecraftData.commands, text)
		# if function is None:
		# 	return super().updateAutoCompletionList(context, aList)

		match = self.getBestMatch(function, position)
		if match is None:
			return list(getSession().minecraftData.commands.keys())

		# if match.info is None or (0 <= idx-1 < len(text) and text[idx-1] != ' '):
		if match.span.end.index >= position.index:
			argument = match.prev
			contextStr = match.content
			posInContextStr = position.index - match.span.start.index
			if argument is None:
				argument = match
				contextStr = ''
				posInContextStr = 0
		else:
			argument = match
			contextStr = ''
			posInContextStr = 0
		info = argument.info
		if info is None:
			return super().updateAutoCompletionList(context, aList)
		# contextStr = context[-1] if context else ''

		replaceCtx = context[0] if context else ''
		result = self._getNextKeywords(info.next, contextStr, posInContextStr, replaceCtx)

		return result

	@override
	def getClickableRanges(self) -> list[tuple[CEPosition, CEPosition]]:
		lexer: LexerMCFunction = cast(LexerMCFunction, self.lexer())

		doc = lexer.document()
		if doc is None:
			return []
		function = doc.tree
		if not isinstance(function, ParsedMCFunction):
			return []

		ranges: list[tuple[Position, Position]] = []
		for command in function.commands:
			part: ParsedCommandPart = command.next
			while part is not None:
				if isinstance(part, ParsedArgument):
					info = part.info
					if isinstance(info, ArgumentInfo):
						handler = getArgumentHandler(info.type)
						if handler is not None:
							partRanges = handler.getClickableRanges(part)
							if partRanges:
								ranges.extend(r.asTuple for r in partRanges)
				part = part.next
		return ranges

	@override
	def indicatorClicked(self, cePosition: CEPosition, state: Qt.KeyboardModifiers) -> None:
		lexer: LexerMCFunction = cast(LexerMCFunction, self.lexer())
		editor: QsciScintilla = lexer.editor()
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		if state != Qt.ControlModifier:
			return

		doc = lexer.document()
		if doc is None:
			return
		function = doc.tree
		if not isinstance(function, ParsedMCFunction):
			return

		match = self.getBestMatch(function, position)
		if match is None:
			return None
		else:
			if isinstance(match, ParsedArgument):
				info = match.info
				if isinstance(info, ArgumentInfo):
					handler = getArgumentHandler(info.type)
					if handler is not None:
						window = editor.window()
						handler.onIndicatorClicked(match, position, window)


@CodeEditorLexer('MCFunction')
class LexerMCFunction(DocumentLexerBase):
	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)

		self._api = McFunctionQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

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
		if not isinstance(function, ParsedMCFunction):
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