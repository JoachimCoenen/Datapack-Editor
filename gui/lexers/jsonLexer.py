from __future__ import annotations

from enum import Enum
from typing import Callable

from PyQt5.QtGui import QFont, QColor

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, CodeEditorLexer
from Cat.utils import override
from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.documentLexer import DocumentLexerBase, StyleStyle, StyleFont, TokenType
from model.json.core import *
from model.json.core import JsonInvalid


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
	Style.key           : StyleStyle(foreground=QColor(0x88, 0x0A, 0xE8), background=QColor(0x88, 0x0A, 0xE8).lighter(209)),
	Style.invalid       : StyleStyle(foreground=QColor(0xff, 0x00, 0x00)),
}


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

	def styleText(self, start: int, end: int):
		start = 0

		doc = self.document()
		if doc is None:
			return
		jsonData = doc.tree
		if not isinstance(jsonData, JsonData):
			return

		self.startStyling(start)
		self.styleData(jsonData)

	_STYLERS: dict[str, Callable[[LexerJson, JsonData], int]] = {}
	_Styler = AddToDictDecorator(_STYLERS)

	def styleData(self, data: JsonData) -> int:
		return self._STYLERS[data.typeName](self, data)
		pass  # TODO: styleData(...)

	@_Styler(JsonInvalid.typeName)
	def styleNull(self, data: JsonInvalid) -> int:
		self.setStyling(data.span.length, Style.invalid.value)
		return data.span.end.index

	@_Styler(JsonNull.typeName)
	def styleNull(self, data: JsonNull) -> int:
		self.setStyling(data.span.length, Style.null.value)
		return data.span.end.index

	@_Styler(JsonBool.typeName)
	def styleBool(self, data: JsonBool) -> int:
		self.setStyling(data.span.length, Style.boolean.value)
		return data.span.end.index

	@_Styler(JsonNumber.typeName)
	def styleNumber(self, data: JsonNumber) -> int:
		self.setStyling(data.span.length, Style.number.value)
		return data.span.end.index

	@_Styler(JsonString.typeName)
	def styleString(self, data: JsonString) -> int:
		self.setStyling(data.span.length, Style.string.value)
		return data.span.end.index

	@_Styler(JsonArray.typeName)
	def styleArray(self, data: JsonArray) -> int:
		lastPos = data.span.start.index
		for element in data.data:
			self.setStyling(element.span.start.index - lastPos, Style.default.value)
			lastPos = self.styleData(element)
		self.setStyling(data.span.end.index - lastPos, Style.default.value)
		return data.span.end.index

	def styleKey(self, data: JsonString) -> int:
		self.setStyling(data.span.length, Style.key.value)
		return data.span.end.index

	@_Styler(JsonObject.typeName)
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
