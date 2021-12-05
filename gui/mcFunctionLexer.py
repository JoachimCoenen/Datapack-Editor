from dataclasses import dataclass, fields
from typing import Optional, TypeVar, Union, Iterable

from PyQt5.Qsci import QsciLexer, QsciLexerCustom, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position, CodeEditorLexer
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override
from model.commands.argumentHandlers import getArgumentHandler, defaultDocumentationProvider
from model.commands.argumentTypes import LiteralsArgumentType, ArgumentType, MINECRAFT_FUNCTION
from model.commands.command import ArgumentInfo, Keyword, Switch, CommandNode, TERMINAL, COMMANDS_ROOT
from model.commands.commands import BASIC_COMMAND_INFO
from model.commands.parsedCommands import ParsedMCFunction, ParsedCommandPart, ParsedComment, ParsedArgument
from model.commands.parser import parseMCFunction
from model.commands.tokenizer import TokenType, tokenizeCommand, tokenizeComment, Token2
from model.commands.validator import checkMCFunction
from model.parsingUtils import GeneralParsingError, Span

TT = TypeVar('TT')


#@dataclass
class NotSet:
	def __init__(self, default):
		self.default: TT = default


@dataclass
class StyleFont:
	family: Union[str, NotSet] = NotSet('Courier New')
	styleHint: Union[QFont.StyleHint, NotSet] = NotSet(QFont.Monospace)
	pointSize: Union[int, NotSet] = NotSet(8)
	bold: Union[bool, NotSet] = NotSet(False)
	italic: Union[bool, NotSet] = NotSet(False)
	underline: Union[bool, NotSet] = NotSet(False)
	overline: Union[bool, NotSet] = NotSet(False)
	strikeOut: Union[bool, NotSet] = NotSet(False)

	# family: Union[str, NotSet[str]] = NotSet('Courier New')
	# styleHint: Union[QFont.StyleHint, NotSet[QFont.StyleHint]] = NotSet(QFont.Monospace)
	# pointSize: Union[int, NotSet[int]] = NotSet(8)
	# bold: Union[bool, NotSet[bool]] = NotSet(False)
	# italic: Union[bool, NotSet[bool]] = NotSet(False)
	# underline: Union[bool, NotSet[bool]] = NotSet(False)
	# overline: Union[bool, NotSet[bool]] = NotSet(False)
	# strikeOut: Union[bool, NotSet[bool]] = NotSet(False)


def QFontFromStyleFont(styleFont: StyleFont, parentFont: Optional[QFont] = None):
	qfont: QFont = QFont()
	for filed in fields(styleFont):
		propName: str = filed.name
		setterName = f'set{propName[0].upper()}{propName[1:]}'

		value = getattr(styleFont, propName)
		if isinstance(value, NotSet):
			if parentFont is not None:
				value = getattr(parentFont, propName)()
			else:
				value = value.default
		getattr(qfont, setterName)(value)

	return qfont


#@dataclass
class StyleStyle:
	def __init__(self, foreground: Optional[QColor] = None, background: Optional[QColor] = None, font: Optional[StyleFont] = None):
		self.foreground: Optional[QColor] = foreground
		self.background: Optional[QColor] = background
		self.font: Optional[StyleFont] = font


styles = {
	TokenType.Default: StyleStyle(
		foreground=QColor(0x00, 0x00, 0x00),
		background=QColor(0xff, 0xff, 0xff),
		font=StyleFont("Consolas", QFont.Monospace, 8)
	),
	TokenType.Command       : StyleStyle(foreground=QColor(0x7f, 0x00, 0x7f)),
	TokenType.String        : StyleStyle(foreground=QColor(0x7f, 0x7f, 0x00)),
	TokenType.Number        : StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
	TokenType.Constant      : StyleStyle(foreground=QColor(0x00, 0x00, 0xBf)),
	TokenType.TargetSelector: StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
	TokenType.Operator      : StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),
	TokenType.Keyword       : StyleStyle(foreground=QColor(0x00, 0x00, 0x00)),

	TokenType.Complex       : StyleStyle(foreground=QColor(0x7f, 0x00, 0x00)),

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
			if child.span.start < pos < child.span.end:
				if isinstance(child, ParsedComment):
					continue
				bestMatch = self._getBestMatch(child, bestMatch, pos)
		return bestMatch

	def getHoverTip(self, position: Position) -> Optional[str]:
		lexer: LexerMCFunction = self.lexer()
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()

		function, errors = lexer._function, lexer._errors
		if function is None:
			return None
		errors = errors + checkMCFunction(function)

		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		tips = [f'<div style="{PythonGUI.helpBoxStyles.get(e.style, "")}">{e.message}</div>' for e in matchedErrors]

		match = self.getBestMatch(function, position)
		if match is None:
			return None
		else:
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

			tip = '<br/>'.join(tips)
			return f"{tip}"

	def _getNextKeywords(self, nexts: Iterable[CommandNode]) -> list[str]:
		result = []
		for nx in nexts:
			if isinstance(nx, Keyword):
				result.append(nx.name)
			elif isinstance(nx, Switch):
				result += self._getNextKeywords(nx.options)
				hasTerminal = TERMINAL in nx.options
				if hasTerminal:
					result += self._getNextKeywords(nx.next)
			elif isinstance(nx, ArgumentInfo):
				type_: ArgumentType = nx.type
				handler = getArgumentHandler(type_)
				if handler is not None:
					result += handler.getSuggestions(nx)
			elif nx is COMMANDS_ROOT:
				result += list(BASIC_COMMAND_INFO.keys())
		return result

	@CrashReportWrapped
	def updateAutoCompletionList(self, context: Iterable[str], aList: Iterable[str]) -> list[str]:
		"""
		Update the list \a list with API entries derived from \a context.  \a
		context is the list of words in the text preceding the cursor position.
		The characters that make up a word and the characters that separate
		words are defined by the lexer.  The last word is a partial word and
		may be empty if the user has just entered a word separator.
		"""
		lexer: LexerMCFunction = self.lexer()
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()
		position = Position(*editor.getCursorPosition())

		function, errors = parseMCFunction(text)
		if function is None:
			return super().updateAutoCompletionList(context, aList)

		match = self.getBestMatch(function, position)
		if match is None:
			return list(BASIC_COMMAND_INFO.keys())

		argument = match.prev
		if argument is None:
			return super().updateAutoCompletionList(context, aList)

		info = argument.info
		if info is None:
			return super().updateAutoCompletionList(context, aList)
		result = self._getNextKeywords(info.next)
		return result

	@override
	def getClickableRanges(self) -> list[tuple[Position, Position]]:
		lexer: LexerMCFunction = self.lexer()
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()

		function, errors = parseMCFunction(text)
		if function is None:
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
								ranges.extend(map(Span.asTuple.get, partRanges))
				part = part.next
		return ranges

	@override
	def indicatorClicked(self, position: Position, state: Qt.KeyboardModifiers) -> None:
		from session.session import getSession
		lexer: LexerMCFunction = self.lexer()
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()

		if state != Qt.ControlModifier:
			return

		function, errors = lexer._function, lexer._errors
		if function is None:
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
class LexerMCFunction(QsciLexerCustom):
	defaultStyles = {style[0]: style[1] for style in styles.items()}

	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		self._errorPos: Optional[tuple[int, int, int, int]] = None
		# self.__errors: tuple[TLScriptSyntaxError, ...] = tuple( )
		# self.errorsChanged: Optional[Callable[[tuple[TLScriptSyntaxError, ...]], None]] = None
		self._function: Optional[ParsedMCFunction] = None
		self._errors: list[GeneralParsingError] = []
		# Initialize all style colors
		self.initStyles(self.defaultStyles)

		self._api = McFunctionQsciAPIs(self)
		self._api.prepare()
		self.setAPIs(self._api)

	def autoCompletionTree(self) -> AutoCompletionTree:
		return self._api.autoCompletionTree

	def setAutoCompletionTree(self, value: AutoCompletionTree):
		self._api.autoCompletionTree = value

	def initStyles(self, styles: dict[TokenType, StyleStyle], overwriteDefaultStyle: bool = False):
		# handle default first:
		if overwriteDefaultStyle:
			defaultStyle = styles[TokenType.Default]
			defaultFont = QFontFromStyleFont(defaultStyle.font)

			self.setDefaultColor(defaultStyle.foreground)
			self.setDefaultPaper(defaultStyle.background)
			super(LexerMCFunction, self).setDefaultFont(defaultFont)

		defaultForeground: QColor = self.defaultColor()
		defaultBackground: QColor = self.defaultPaper()
		defaultFont: QFont = self.defaultFont()

		for tokenType, style in styles.items():

			foreground = style.foreground
			if foreground is None or tokenType == TokenType.Default:
				foreground = defaultForeground

			background = style.background
			if background is None or tokenType == TokenType.Default:
				background = defaultBackground

			if style.font is None or tokenType == TokenType.Default:
				font = defaultFont
			else:
				font = QFontFromStyleFont(style.font, defaultFont)

			self.setColor(foreground, tokenType.value)
			self.setPaper(background, tokenType.value)
			self.setFont(font, tokenType.value)

	def setDefaultFont(self, font: QFont):
		super().setDefaultFont(font)
		self.initStyles(self.defaultStyles)

	def setFont(self, font: QFont, style=-1):
		if style == -1:
			self.setDefaultFont(font)
		else:
			super().setFont(font, style)

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

	# def wseps(self) -> list[str]:
	# 	editor: QsciScintilla = self.editor()
	# 	pos: int = editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
	# 	return ['.']

	def autoCompletionWordSeparators(self) -> list[str]:
		# editor: QsciScintilla = self.editor()
		# pos: int = editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
		return ['.']  # ':', '#', '.']

	def styleText(self, start: int, end: int):
		origStart, origEnd = start, end
		start = 0
		text: str = self.parent().text()

		function, errors = parseMCFunction(text)
		if function is None:
			self._function = None
			self._errors = []
			return

		self._function = function
		self._errors = errors

		tokens: list[Token2] = []
		for child in function.children:
			if child is None:
				continue
			elif isinstance(child, ParsedComment):
				tokens.extend(tokenizeComment(child))
			else:
				tokens.extend(tokenizeCommand(child))

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