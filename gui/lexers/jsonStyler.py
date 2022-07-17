from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Callable, Type

from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.styler import DEFAULT_STYLE_ID, CatStyler, registerStyler, StyleIdEnum
from model.json.core import *
from model.parsing.tree import Node
from model.utils import LanguageId


class StyleId(StyleIdEnum):
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
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		return StyleId

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT'), LanguageId('MCCommand')]

	@classmethod
	def language(cls) -> LanguageId:
		return LanguageId('JSON')

	_STYLERS: ClassVar[dict[str, Callable[[JsonStyler, JsonData], int]]] = {}
	_Styler: ClassVar = AddToDictDecorator(_STYLERS)

	def __post_init__(self):
		super(JsonStyler, self).__post_init__()
		self.DEFAULT_STYLE: StyleId = self.offset + StyleId.default.value
		self.NULL_STYLE:    StyleId = self.offset + StyleId.null.value
		self.BOOLEAN_STYLE: StyleId = self.offset + StyleId.boolean.value
		self.NUMBER_STYLE:  StyleId = self.offset + StyleId.number.value
		self.STRING_STYLE:  StyleId = self.offset + StyleId.string.value
		self.KEY_STYLE:     StyleId = self.offset + StyleId.key.value
		self.INVALID_STYLE: StyleId = self.offset + StyleId.invalid.value

	def styleNode(self, data: JsonData) -> int:
		return self._STYLERS[data.typeName](self, data)

	@_Styler(JsonInvalid.typeName)
	def styleInvalid(self, data: JsonInvalid) -> int:
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
			afterLen = slice(after, data.span.end.index)
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
