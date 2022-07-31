from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Callable, Type

from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.styler import DEFAULT_STYLE_ID, CatStyler, registerStyler, StyleIdEnum
from model.nbt.tags import *
from model.parsing.tree import Node
from model.utils import LanguageId


class StyleId(StyleIdEnum):
	default   = DEFAULT_STYLE_ID
	boolean   = DEFAULT_STYLE_ID + 1
	intLike   = DEFAULT_STYLE_ID + 2
	floatLike = DEFAULT_STYLE_ID + 3
	string    = DEFAULT_STYLE_ID + 4
	key       = DEFAULT_STYLE_ID + 5
	invalid   = DEFAULT_STYLE_ID + 6


@registerStyler
@dataclass
class SNBTStyler(CatStyler[NBTTag]):

	@property
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		return StyleId

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return []

	@classmethod
	def language(cls) -> LanguageId:
		return LanguageId('SNBT')

	_STYLERS: ClassVar[dict[str, Callable[[SNBTStyler, NBTTag], int]]] = {}
	_Styler: ClassVar = AddToDictDecorator(_STYLERS)

	def __post_init__(self):
		super(SNBTStyler, self).__post_init__()
		self.DEFAULT_STYLE:    StyleId = self.offset + StyleId.default.value
		self.BOOLEAN_STYLE:    StyleId = self.offset + StyleId.boolean.value
		self.INT_LIKE_STYLE:   StyleId = self.offset + StyleId.intLike.value
		self.FLOAT_LIKE_STYLE: StyleId = self.offset + StyleId.floatLike.value
		self.STRING_STYLE:     StyleId = self.offset + StyleId.string.value
		self.KEY_STYLE:        StyleId = self.offset + StyleId.key.value
		self.INVALID_STYLE:    StyleId = self.offset + StyleId.invalid.value

	def styleNode(self, data: NBTTag) -> int:
		return self._STYLERS[data.typeName](self, data)

	@_Styler(InvalidTag.typeName)
	def styleInvalid(self, data: InvalidTag) -> int:
		self.setStyling(data.span.slice, self.INVALID_STYLE)
		return data.span.end.index

	@_Styler(BooleanTag.typeName)
	def styleBool(self, data: BooleanTag) -> int:
		self.setStyling(data.span.slice, self.BOOLEAN_STYLE)
		return data.span.end.index

	@_Styler(ByteTag.typeName)
	@_Styler(ShortTag.typeName)
	@_Styler(IntTag.typeName)
	@_Styler(LongTag.typeName)
	def styleIntLike(self, data: NumberTag) -> int:
		self.setStyling(data.span.slice, self.INT_LIKE_STYLE)
		return data.span.end.index

	@_Styler(FloatTag.typeName)
	@_Styler(DoubleTag.typeName)
	def styleFloatLike(self, data: NumberTag) -> int:
		self.setStyling(data.span.slice, self.FLOAT_LIKE_STYLE)
		return data.span.end.index

	@_Styler(StringTag.typeName)
	def styleString(self, data: StringTag) -> int:
		if data.parsedValue is not None and isinstance(data.parsedValue, Node):
			beforeLen = slice(data.span.start.index, data.parsedValue.span.start.index)
			self.setStyling(beforeLen, self.STRING_STYLE)
			after = self.styleForeignNode(data.parsedValue)
			afterLen = slice(after, data.parsedValue.span.end.index)
			self.setStyling(afterLen, self.STRING_STYLE)
		else:
			self.setStyling(data.span.slice, self.STRING_STYLE)
		return data.span.end.index

	@_Styler(ListTag.typeName)
	def styleList(self, data: ListTag) -> int:
		lastPos = data.span.start.index
		for element in data.data:
			self.setStyling(slice(lastPos, element.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleNode(element)
		self.setStyling(slice(lastPos, data.span.end.index), self.DEFAULT_STYLE)
		return data.span.end.index

	@_Styler(ByteArrayTag.typeName)
	@_Styler(IntArrayTag.typeName)
	@_Styler(LongArrayTag.typeName)
	# @_Styler(ArrayTag.typeName)
	def styleArray(self, data: ArrayTag) -> int:
		for element in data.data:
			self.styleNode(element)
		return data.span.end.index

	def styleKey(self, data: StringTag) -> int:
		self.setStyling(data.span.slice, self.KEY_STYLE)
		return data.span.end.index

	def styleProperty(self, data: NBTProperty) -> int:
		self.styleKey(data.key)
		self.styleNode(data.value)
		return data.span.end.index

	@_Styler(CompoundTag.typeName)
	def styleCompound(self, data: CompoundTag) -> int:
		for prop in data.data.values():
			self.styleProperty(prop)
		return data.span.end.index


# def run():
# 	from Cat.utils.formatters import formatVal
# 	styler = SNBTStyler(lambda x, y: None, {}, 5)
# 	print(f"styler.localStylesCount = {styler.localStylesCount}")
# 	print(f"styler.localStyles = {formatVal(styler.localStyles)}")
#
#
# if __name__ == '__main__':
# 	run()
