from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Callable

from cat.utils.collections_ import AddToDictDecorator
from base.gui.styler import CatStyler, CommonStyleIds, StyleId
from .core import *
from base.model.parsing.tree import Node
from base.model.utils import LanguageId


@dataclass
class StructureStyler(CatStyler[StructureNode]):

	@classmethod
	def usesCommonStyleIds(cls) -> bool:
		""" override when CommonStyleIds are used"""
		return True

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT'), LanguageId('MCFunction')]

	_STYLERS: ClassVar[dict[str, Callable[[StructureStyler, StructureDataNode], int]]] = {}
	_Styler: ClassVar = AddToDictDecorator(_STYLERS)

	def __post_init__(self):
		super().__post_init__()
		self.DEFAULT_STYLE: StyleId = CommonStyleIds.default
		self.NULL_STYLE:    StyleId = CommonStyleIds.special_constant
		self.BOOLEAN_STYLE: StyleId = CommonStyleIds.special_constant
		self.NUMBER_STYLE:  StyleId = CommonStyleIds.number
		self.STRING_STYLE:  StyleId = CommonStyleIds.string
		self.KEY_STYLE:     StyleId = CommonStyleIds.key1
		self.INVALID_STYLE: StyleId = CommonStyleIds.invalid

	def styleNode(self, data: StructureDataNode) -> int:
		return self._STYLERS[data.typeName](self, data)

	@_Styler(InvalidNode.typeName)
	def styleInvalid(self, data: InvalidNode) -> int:
		self.setStyling(data.span.slice, self.INVALID_STYLE)
		return data.span.end.index

	@_Styler(NullNode.typeName)
	def styleNull(self, data: NullNode) -> int:
		self.setStyling(data.span.slice, self.NULL_STYLE)
		return data.span.end.index

	@_Styler(BooleanNode.typeName)
	def styleBool(self, data: BooleanNode) -> int:
		self.setStyling(data.span.slice, self.BOOLEAN_STYLE)
		return data.span.end.index

	@_Styler(NumberNode.typeName)
	def styleNumber(self, data: NumberNode) -> int:
		self.setStyling(data.span.slice, self.NUMBER_STYLE)
		return data.span.end.index

	@_Styler(StringNode.typeName)
	def styleString(self, data: StringNode) -> int:
		if data.parsedValue is not None and isinstance(data.parsedValue, Node):
			beforeLen = slice(data.span.start.index, data.parsedValue.span.start.index)
			self.setStyling(beforeLen, self.STRING_STYLE)
			after = self.styleForeignNode(data.parsedValue)
			afterLen = slice(after, data.span.end.index)
			self.setStyling(afterLen, self.STRING_STYLE)
		else:
			self.setStyling(data.span.slice, self.STRING_STYLE)
		return data.span.end.index

	@_Styler(ListLikeNode.typeName)
	def styleArray(self, data: ListLikeNode) -> int:
		return self.styleStructuredNodeChildNodes(data, self.DEFAULT_STYLE)

	def styleKey(self, data: StringNode) -> int:
		self.setStyling(data.span.slice, self.KEY_STYLE)
		return data.span.end.index

	@_Styler(ObjectNode.typeName)
	def styleObject(self, data: ObjectNode) -> int:
		lastPos = data.span.start.index
		for prop in data.data.values():
			self.setStyling(slice(lastPos, prop.key.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleKey(prop.key)
			self.setStyling(slice(lastPos, prop.value.span.start.index), self.DEFAULT_STYLE)
			lastPos = self.styleNode(prop.value)
		self.setStyling(slice(lastPos, data.span.end.index), self.DEFAULT_STYLE)
		return data.span.end.index
