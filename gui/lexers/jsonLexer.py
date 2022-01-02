from enum import Enum
from typing import Optional, cast, Sequence

from PyQt5.Qsci import QsciLexer, QsciScintilla
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.CatPythonGUI.GUI.codeEditor import MyQsciAPIs, AutoCompletionTree, Position as CEPosition, CodeEditorLexer, Error
from Cat.CatPythonGUI.utilities import CrashReportWrapped
from Cat.utils import override, HTMLifyMarkDownSubSet
from gui.lexers.documentLexer import DocumentLexerBase, StyleStyle, StyleFont, TokenType
from model.data.v1_17.tags import TAGS_BLOCKS
from model.json.core import *
from model.json.parser import parseJsonStr
from model.json.validator import validateJson
from model.utils import GeneralParsingError, Position
from session.session import getSession


class Style(Enum):
	default = 0
	null    = 1
	boolean = 2
	number  = 3
	string  = 5
	key     = 6
	invalid = 7


styles = {
	Style.default: StyleStyle(
		foreground=QColor(0x00, 0x00, 0x00),
		background=QColor(0xff, 0xff, 0xff),
		font=StyleFont("Consolas", QFont.Monospace, 8)
	),
	# TokenType.Command       : StyleStyle(foreground=QColor(0x7f, 0x00, 0x7f)),
	Style.null          : StyleStyle(foreground=QColor(0x00, 0x00, 0xBf)),
	Style.boolean       : StyleStyle(foreground=QColor(0x00, 0x00, 0xBf)),
	Style.number        : StyleStyle(foreground=QColor(0x00, 0x7f, 0x7f)),
	Style.string        : StyleStyle(foreground=QColor(0x7f, 0x00, 0x00)),
	Style.key           : StyleStyle(foreground=QColor(0x88, 0x0A, 0xE8)),
	Style.invalid       : StyleStyle(foreground=QColor(0xff, 0x00, 0x00)),
}


class JsonQsciAPIs(MyQsciAPIs):
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

	def _getBestMatch(self, tree: JsonData, bestMatch: Optional[JsonData], pos: Position) -> Optional[JsonData]:
		return None
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

	def getBestMatch(self, tree: JsonData, pos: Position) -> Optional[JsonData]:
		return None
		bestMatch: Optional[JsonData] = None
		children = tuple(tree.children)
		for child in children:
			if child.span.start < pos <= child.span.end:
				if isinstance(child, ParsedComment):
					continue
				bestMatch = self._getBestMatch(child, bestMatch, pos)
		return bestMatch

	def getHoverTip(self, cePosition: CEPosition) -> Optional[str]:
		lexer: LexerJson = cast(LexerJson, self.lexer())
		editor: QsciScintilla = lexer.editor()
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		jsonData = lexer.jsonData
		errors = lexer.errors
		if jsonData is None or errors is None:
			return None

		matchedErrors = [e for e in errors if e.position <= position <= e.end]
		tips = [f'<div style="{PythonGUI.helpBoxStyles.get(e.style, "")}">{e.message}</div>' for e in matchedErrors]

		match = self.getBestMatch(jsonData, position)
		if match is not None:
			schema = match.schema
			if schema is not None:
				tips.append(HTMLifyMarkDownSubSet(schema.description))
			else:
				pass

		if tips is not None:
			tip = '<br/>'.join(tips)
			return f"{tip}"

	@CrashReportWrapped
	def updateAutoCompletionList(self, context: list[str], aList: list[str]) -> list[str]:
		"""
		Update the list \a list with API entries derived from \a context.  \a
		context is the list of words in the text preceding the cursor position.
		The characters that make up a word and the characters that separate
		words are defined by the lexer.  The last word is a partial word and
		may be empty if the user has just entered a word separator.
		"""
		return super(JsonQsciAPIs, self).updateAutoCompletionList(context, aList)
		lexer: LexerJson = cast(LexerJson, self.lexer())
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()
		cePosition = CEPosition(*editor.getCursorPosition())
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		function, errors = parseMCFunction(getSession().minecraftData.commands, text)
		if function is None:
			return super().updateAutoCompletionList(context, aList)

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
		return []
		lexer: LexerJson = cast(LexerJson, self.lexer())
		editor: QsciScintilla = lexer.editor()
		text: str = editor.text()

		function, errors = parseMCFunction(getSession().minecraftData.commands, text)
		if function is None:
			return []

		ranges: list[tuple[Position, Position]] = []
		for command in function.commands:
			part: JsonData = command.next
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
		return
		lexer: LexerJson = cast(LexerJson, self.lexer())
		editor: QsciScintilla = lexer.editor()
		position = Position(cePosition.line, cePosition.column, editor.positionFromLineIndex(*cePosition))

		if state != Qt.ControlModifier:
			return

		jsonData, errors = lexer.jsonData, lexer.errors
		if jsonData is None:
			return

		match = self.getBestMatch(jsonData, position)
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


def bytesLen(text: str) -> int:
	return len(bytearray(text, "utf-8"))


@CodeEditorLexer('MCJson', forceOverride=True)
class LexerJson(DocumentLexerBase):
	defaultStyles = {style[0]: style[1] for style in styles.items()}

	# styleIndices: dict[str, int] = {name: i for i, name in enumerate(styles.keys())}

	def __init__(self, parent=None):
		# Initialize superclass
		super().__init__(parent)
		self._lastStylePos: int = 0
		self._api = JsonQsciAPIs(self)
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
		return "JSON"

	def description(self, style):
		if style < len(styles):
			description = "Custom lexer for the Minecrafts .json files"
		else:
			description = ""
		return description

	def wordCharacters(self) -> str:
		return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~^@#$%&:/"

	def autoCompletionWordSeparators(self) -> list[str]:
		return ['.']  # ':', '#', '.']

	@property
	def jsonData(self) -> Optional[JsonData]:
		doc = self.document()
		if doc is None:
			return None
		jsonData = doc.tree
		if not isinstance(jsonData, JsonData):
			return None
		return jsonData

	@property
	def errors(self) -> Optional[Sequence[Error]]:
		doc = self.document()
		if doc is None:
			return None
		return doc.errors

	def styleText(self, start: int, end: int):
		start = 0
		jsonData = self.jsonData
		if jsonData is None:
			return

		if jsonData is not None:
			self.startStyling(start)
			self.styleData(jsonData)

	def setStyling2(self, length: int, style: Style) -> None:
		# interStr = text[lastPos:index]
		# interStrLength = bytesLen(interStr)
		self.setStyling(length, style.value)

	def styleData(self, data: JsonData) -> int:
		stylers = {
			JsonNull: self.styleNull,
			JsonBool: self.styleBool,
			JsonNumber: self.styleNumber,
			JsonString: self.styleString,
			JsonArray: self.styleArray,
			JsonObject: self.styleObject,
		}
		return stylers[type(data)](data)
		pass  # TODO: styleData(...)

	def styleNull(self, data: JsonNull) -> int:
		self.setStyling(data.span.length, Style.null.value)
		return data.span.end.index

	def styleBool(self, data: JsonBool) -> int:
		self.setStyling(data.span.length, Style.boolean.value)
		return data.span.end.index

	def styleNumber(self, data: JsonNumber) -> int:
		self.setStyling(data.span.length, Style.number.value)
		return data.span.end.index

	def styleString(self, data: JsonString) -> int:
		self.setStyling(data.span.length, Style.string.value)
		return data.span.end.index

	def styleKey(self, data: JsonString) -> int:
		self.setStyling(data.span.length, Style.key.value)
		return data.span.end.index

	def styleArray(self, data: JsonArray) -> int:
		lastPos = data.span.start.index
		for element in data.data:
			self.setStyling(element.span.start.index - lastPos, Style.default.value)
			lastPos = self.styleData(element)
		self.setStyling(data.span.end.index - lastPos, Style.default.value)
		return data.span.end.index

	def styleObject(self, data: JsonObject) -> int:
		lastPos = data.span.start.index
		for prop in data.data.values():
			self.setStyling(prop.key.span.start.index - lastPos, Style.default.value)
			lastPos = self.styleKey(prop.key)
			self.setStyling(prop.value.span.start.index - lastPos, Style.default.value)
			lastPos = self.styleData(prop.value)
		self.setStyling(data.span.end.index - lastPos, Style.default.value)
		return data.span.end.index

	def startStyling(self, pos: int) -> None:
		self._lastStylePos = pos
		super(LexerJson, self).startStyling(pos)

	def setStyling(self, length: int, style: int) -> None:
		assert(length >= 0)
		doc = self.document()
		if doc is not None:
			text = doc.content[self._lastStylePos:self._lastStylePos + length]
			self._lastStylePos += length
			length = len(bytearray(text, "utf-8"))
		
		super(LexerJson, self).setStyling(length, style)


def init():
	pass  # Don't delete!
