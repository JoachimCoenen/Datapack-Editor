from __future__ import annotations

import enum
from collections import Callable
from dataclasses import dataclass
from typing import ClassVar

from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.styler import DEFAULT_STYLE_ID, StyleId, CatStyler, registerStyler
from model.json.core import *
from model.parsing.tree import Node
from model.utils import LanguageId


class Style(enum.Enum):
	default = DEFAULT_STYLE_ID
	null    = DEFAULT_STYLE_ID + 1
	boolean = DEFAULT_STYLE_ID + 2
	number  = DEFAULT_STYLE_ID + 3
	string  = DEFAULT_STYLE_ID + 4
	key     = DEFAULT_STYLE_ID + 5
	invalid = DEFAULT_STYLE_ID + 6


@registerStyler
@dataclass
class JsonStyler(CatStyler[JsonData]):

	@property
	def localStyles(self) -> dict[str, StyleId]:
		styles = {
			Style.default.name: self.offset + Style.default.value,
			Style.null.name:    self.offset + Style.null.value,
			Style.boolean.name: self.offset + Style.boolean.value,
			Style.number.name:  self.offset + Style.number.value,
			Style.string.name:  self.offset + Style.string.value,
			Style.key.name:     self.offset + Style.key.value,
			Style.invalid.name: self.offset + Style.invalid.value,
		}
		return styles

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return []

	@property
	def localStylesCount(self) -> int:
		return self._localStylesCount

	@classmethod
	def language(cls) -> str:
		return 'JSON'

	_STYLERS: ClassVar[dict[str, Callable[[JsonStyler, JsonData], int]]] = {}
	_Styler: ClassVar = AddToDictDecorator(_STYLERS)

	def __post_init__(self):
		self.DEFAULT_STYLE: StyleId = self.offset + Style.default.value
		self.NULL_STYLE:    StyleId = self.offset + Style.null.value
		self.BOOLEAN_STYLE: StyleId = self.offset + Style.boolean.value
		self.NUMBER_STYLE:  StyleId = self.offset + Style.number.value
		self.STRING_STYLE:  StyleId = self.offset + Style.string.value
		self.KEY_STYLE:     StyleId = self.offset + Style.key.value
		self.INVALID_STYLE: StyleId = self.offset + Style.invalid.value
		self._localStylesCount = 7

	def styleNode(self, data: JsonData) -> int:
		return self._STYLERS[data.typeName](self, data)

	@_Styler(JsonInvalid.typeName)
	def styleNull(self, data: JsonInvalid) -> int:
		self.setStyling(data.span.slice, self.INVALID_STYLE)
		return data.span.end.index

	@_Styler(JsonNull.typeName)
	def styleNull(self, data: JsonNull) -> int:
		self.setStyling(data.span.slice, self.NULL_STYLE)
		return data.span.end.index

	@_Styler(JsonBool.typeName)
	def styleBool(self, data: JsonBool) -> int:
		self.setStyling(data.span.slice, self.BOOLEAN_STYLE)
		return data.span.end.index

	@_Styler(JsonNumber.typeName)
	def styleNumber(self, data: JsonNumber) -> int:
		self.setStyling(data.span.slice, self.NUMBER_STYLE)
		return data.span.end.index

	@_Styler(JsonString.typeName)
	def styleString(self, data: JsonString) -> int:
		if data.parsedValue is not None and isinstance(data.parsedValue, Node):
			beforeLen = slice(data.span.start.index, data.parsedValue.span.start.index)
			self.setStyling(beforeLen, self.STRING_STYLE)
			after = self.styleForeignNode(data.parsedValue)
			afterLen = slice(after, data.parsedValue.span.end.index)
			self.setStyling(afterLen, self.STRING_STYLE)
		else:
			self.setStyling(data.span.slice, self.STRING_STYLE)
		return data.span.end.index

	@_Styler(JsonArray.typeName)
	def styleArray(self, data: JsonArray) -> int:
		lastPos = data.span.start.index
		for element in data.data:
			self.setStyling(slice(lastPos, element.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleNode(element)
		self.setStyling(slice(lastPos, data.span.end.index), self.DEFAULT_STYLE)
		return data.span.end.index

	def styleKey(self, data: JsonString) -> int:
		self.setStyling(data.span.slice, self.KEY_STYLE)
		return data.span.end.index

	@_Styler(JsonObject.typeName)
	def styleObject(self, data: JsonObject) -> int:
		lastPos = data.span.start.index
		for prop in data.data.values():
			self.setStyling(slice(lastPos, prop.key.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleKey(prop.key)
			self.setStyling(slice(lastPos, prop.value.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleNode(prop.value)
		self.setStyling(slice(lastPos, data.span.end.index), self.DEFAULT_STYLE)
		return data.span.end.index
