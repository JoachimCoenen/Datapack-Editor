from __future__ import annotations

import enum
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Type, Optional, ClassVar

from Cat.utils import Decorator
from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.styler import DEFAULT_STYLE_ID, CatStyler, registerStyler
from model.commands.argumentTypes import *
from model.commands.argumentValues import ItemStack
from model.commands.command import MCFunction, ParsedComment, ParsedCommand, KeywordSchema, ArgumentSchema, CommandPart, ParsedArgument
from model.utils import LanguageId


class StyleId(enum.IntEnum):
	Default = DEFAULT_STYLE_ID
	Command = DEFAULT_STYLE_ID + 1
	String = DEFAULT_STYLE_ID + 2
	Number = DEFAULT_STYLE_ID + 3
	Constant = DEFAULT_STYLE_ID + 4
	TargetSelector = DEFAULT_STYLE_ID + 5
	Operator = DEFAULT_STYLE_ID + 6
	Keyword = DEFAULT_STYLE_ID + 7

	Complex = DEFAULT_STYLE_ID + 8
	Comment = DEFAULT_STYLE_ID + 9
	Error = DEFAULT_STYLE_ID + 10

	# KeyWord = 14
	# Variable = 11
	# BuiltinFunction = 17


_allArgumentTypeStyles: dict[str, Optional[StyleId]] = {
	BRIGADIER_BOOL.name:               StyleId.Constant,
	BRIGADIER_DOUBLE.name:             StyleId.Number,
	BRIGADIER_FLOAT.name:              StyleId.Number,
	BRIGADIER_INTEGER.name:            StyleId.Number,
	BRIGADIER_LONG.name:               StyleId.Number,
	BRIGADIER_STRING.name:             StyleId.String,
	MINECRAFT_ANGLE.name:              StyleId.Number,
	MINECRAFT_BLOCK_POS.name:          StyleId.Number,
	MINECRAFT_BLOCK_PREDICATE.name:    StyleId.Complex,
	MINECRAFT_BLOCK_STATE.name:        StyleId.Complex,
	MINECRAFT_COLOR.name:              StyleId.Constant,
	MINECRAFT_COLUMN_POS.name:         StyleId.Number,
	MINECRAFT_COMPONENT.name:          StyleId.Complex,
	MINECRAFT_DIMENSION.name:          StyleId.String,
	MINECRAFT_ENTITY.name:             StyleId.TargetSelector,
	MINECRAFT_ENTITY_ANCHOR.name:      StyleId.Constant,
	MINECRAFT_ENTITY_SUMMON.name:      StyleId.String,
	MINECRAFT_FLOAT_RANGE.name:        StyleId.Number,
	MINECRAFT_FUNCTION.name:           StyleId.String,
	MINECRAFT_GAME_PROFILE.name:       StyleId.TargetSelector,
	MINECRAFT_INT_RANGE.name:          StyleId.Number,
	MINECRAFT_ITEM_ENCHANTMENT.name:   StyleId.String,
	MINECRAFT_ITEM_PREDICATE.name:     StyleId.Complex,
	MINECRAFT_ITEM_SLOT.name:          StyleId.Constant,
	MINECRAFT_ITEM_STACK.name:         StyleId.Complex,
	MINECRAFT_MESSAGE.name:            StyleId.String,
	MINECRAFT_MOB_EFFECT.name:         StyleId.String,
	MINECRAFT_NBT_COMPOUND_TAG.name:   StyleId.Complex,
	MINECRAFT_NBT_PATH.name:           StyleId.Complex,
	MINECRAFT_NBT_TAG.name:            StyleId.Complex,
	MINECRAFT_OBJECTIVE.name:          StyleId.String,
	MINECRAFT_OBJECTIVE_CRITERIA.name: StyleId.String,
	MINECRAFT_OPERATION.name:          StyleId.Operator,
	MINECRAFT_PARTICLE.name:           StyleId.Complex,
	MINECRAFT_PREDICATE.name:          StyleId.String,
	MINECRAFT_RESOURCE_LOCATION.name:  StyleId.String,
	MINECRAFT_ROTATION.name:           StyleId.Number,
	MINECRAFT_SCORE_HOLDER.name:       StyleId.TargetSelector,
	MINECRAFT_SCOREBOARD_SLOT.name:    StyleId.Constant,
	MINECRAFT_SWIZZLE.name:            StyleId.Constant,
	MINECRAFT_TEAM.name:               StyleId.Constant,
	MINECRAFT_TIME.name:               StyleId.Number,
	MINECRAFT_UUID.name:               StyleId.String,
	MINECRAFT_VEC2.name:               StyleId.Number,
	MINECRAFT_VEC3.name:               StyleId.Number,
	DPE_ADVANCEMENT.name:              StyleId.String,
	DPE_COMPARE_OPERATION.name:        StyleId.Operator,
	DPE_BIOME_ID.name:                 StyleId.String,
}


@dataclass
class ArgumentStyler(ABC):
	# setStyling: StylingFunc
	# innerStylers: dict[Type[Node], CatStyler]
	commandStyler: MCCommandStyler
	# offset: int

	@classmethod
	@abstractmethod
	def localLanguages(cls) -> list[LanguageId]:
		pass

	@abstractmethod
	def style(self, argument: ParsedArgument) -> None:
		pass


_argumentStylers: dict[str, Type[ArgumentStyler]] = {}
argumentStyler = Decorator(AddToDictDecorator(_argumentStylers))


@registerStyler
@dataclass
class MCCommandStyler(CatStyler[CommandPart]):

	@property
	def localStyles(self) -> dict[str, StyleId]:
		styles = {
			StyleId.Default.name:  self.offset + StyleId.Default.value,
			StyleId.Command.name:  self.offset + StyleId.Command.value,
			StyleId.String.name:   self.offset + StyleId.String.value,
			StyleId.Number.name:   self.offset + StyleId.Number.value,
			StyleId.Constant.name: self.offset + StyleId.Constant.value,
			StyleId.TargetSelector.name: self.offset + StyleId.TargetSelector.value,
			StyleId.Operator.name: self.offset + StyleId.Operator.value,
			StyleId.Keyword.name:  self.offset + StyleId.Keyword.value,

			StyleId.Complex.name:  self.offset + StyleId.Complex.value,

			StyleId.Comment.name:  self.offset + StyleId.Comment.value,
			StyleId.Error.name:    self.offset + StyleId.Error.value,
		}
		return styles

	argumentStylers: dict[str, ArgumentStyler] = field(init=False, repr=False, compare=False)

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		localInnerLanguages = []
		for argS in _argumentStylers.values():
			localInnerLanguages.extend(argS.localLanguages())
		return list(set(localInnerLanguages))
		# return [LanguageId('JSON')]

	@property
	def localStylesCount(self) -> int:
		return len(StyleId)

	@classmethod
	def language(cls) -> LanguageId:
		return LanguageId('MCCommand')

	def __post_init__(self):
		super(MCCommandStyler, self).__post_init__()
		self.argumentStylers = {
			name: argStylerCls(self) for name, argStylerCls in _argumentStylers.items()
		}

	def styleNode(self, data: CommandPart) -> int:
		if isinstance(data, MCFunction):
			return self.styleMCFunction(data)
		elif isinstance(data, ParsedComment):
			return self.styleComment(data)
		else:
			return self.styleCommand(data)

	def styleMCFunction(self, function: MCFunction) -> int:
		end = function.span.start.index
		for child in function.children:
			if child is None:
				continue
			elif isinstance(child, ParsedComment):
				end = self.styleComment(child)
			else:
				end = self.styleCommand(child)
		return end

	def styleComment(self, comment: ParsedComment) -> int:
		self.setStyling(comment.span.slice, StyleId.Comment.value)
		return comment.span.end.index

	def styleCommand(self, command: ParsedCommand) -> int:
		argument: CommandPart = command
		span = command.span.slice
		while argument is not None:
			if isinstance(argument, ParsedCommand):
				style = StyleId.Command
				span = slice(argument.start.index, argument.start.index + len(argument.name))
			else:
				argument: ParsedArgument
				span = argument.span.slice
				schema = argument.schema
				if isinstance(schema, KeywordSchema):
					style = StyleId.Keyword
				elif isinstance(schema, ArgumentSchema):
					if isinstance(schema.type, LiteralsArgumentType):
						style = StyleId.Constant
					else:
						typeName = schema.typeName
						# style = _allArgumentTypeStyles.get(typeName, StyleId.Error)
						styler = self.argumentStylers.get(typeName, None)
						if styler is None:
							style = StyleId.Error
						else:
							styler.style(argument)
							argument = argument.next
							continue
				else:
					style = StyleId.Error
			self.setStyling(span, style.value)

			argument = argument.next
		return span.stop


def addSimpleArgumentStyler(style: StyleId, *, forArgTypes: list[ArgumentType]) -> None:
	styleId = style.value

	class SimpleArgumentStyler(ArgumentStyler):
		STYLE: ClassVar[StyleId] = styleId

		@classmethod
		def localLanguages(cls) -> list[LanguageId]:
			return []

		def style(self, argument: ParsedArgument) -> None:
			self.commandStyler.setStyling(argument.span.slice, styleId)

	for argType in forArgTypes:
		argumentStyler(argType.name)(SimpleArgumentStyler)


addSimpleArgumentStyler(StyleId.Complex, forArgTypes=[
	MINECRAFT_BLOCK_PREDICATE,
	MINECRAFT_BLOCK_STATE,
	MINECRAFT_COMPONENT,
	MINECRAFT_ITEM_PREDICATE,
	MINECRAFT_ITEM_STACK,
	MINECRAFT_NBT_COMPOUND_TAG,
	MINECRAFT_NBT_PATH,
	MINECRAFT_NBT_TAG,
	MINECRAFT_PARTICLE,
])

addSimpleArgumentStyler(StyleId.Constant, forArgTypes=[
	BRIGADIER_BOOL,
	MINECRAFT_COLOR,
	MINECRAFT_ENTITY_ANCHOR,
	MINECRAFT_ITEM_SLOT,
	MINECRAFT_SCOREBOARD_SLOT,
	MINECRAFT_SWIZZLE,
	MINECRAFT_TEAM,
])

addSimpleArgumentStyler(StyleId.Number, forArgTypes=[
	BRIGADIER_DOUBLE,
	BRIGADIER_FLOAT,
	BRIGADIER_INTEGER,
	BRIGADIER_LONG,
	MINECRAFT_ANGLE,
	MINECRAFT_BLOCK_POS,
	MINECRAFT_COLUMN_POS,
	MINECRAFT_FLOAT_RANGE,
	MINECRAFT_INT_RANGE,
	MINECRAFT_ROTATION,
	MINECRAFT_TIME,
	MINECRAFT_VEC2,
	MINECRAFT_VEC3,
])

addSimpleArgumentStyler(StyleId.Operator, forArgTypes=[
	MINECRAFT_OPERATION,
	DPE_COMPARE_OPERATION,
])

addSimpleArgumentStyler(StyleId.String, forArgTypes=[
	BRIGADIER_STRING,
	MINECRAFT_DIMENSION,
	MINECRAFT_ENTITY_SUMMON,
	MINECRAFT_FUNCTION,
	MINECRAFT_ITEM_ENCHANTMENT,
	MINECRAFT_MESSAGE,
	MINECRAFT_MOB_EFFECT,
	MINECRAFT_OBJECTIVE,
	MINECRAFT_OBJECTIVE_CRITERIA,
	MINECRAFT_PREDICATE,
	MINECRAFT_RESOURCE_LOCATION,
	MINECRAFT_UUID,
	DPE_ADVANCEMENT,
	DPE_BIOME_ID,
])

addSimpleArgumentStyler(StyleId.TargetSelector, forArgTypes=[
	MINECRAFT_ENTITY,
	MINECRAFT_GAME_PROFILE,
	MINECRAFT_SCORE_HOLDER,
])


@argumentStyler(MINECRAFT_COMPONENT.name, forceOverride=True)
class ComponentStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('JSON')]

	def style(self, argument: ParsedArgument) -> None:
		idx = self.commandStyler.styleForeignNode(argument.value)
		if idx == argument.value.span.start.index:
			self.commandStyler.setStyling(argument.span.slice, StyleId.Complex.value)


@argumentStyler(MINECRAFT_NBT_COMPOUND_TAG.name, forceOverride=True)
@argumentStyler(MINECRAFT_NBT_TAG.name, forceOverride=True)
class SNBTStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		idx = self.commandStyler.styleForeignNode(argument.value)
		if idx == argument.value.span.start.index:
			self.commandStyler.setStyling(argument.span.slice, StyleId.Complex.value)


@argumentStyler(MINECRAFT_ITEM_STACK.name, forceOverride=True)
class ItemStackStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: ItemStack = argument.value
		if not isinstance(value, ItemStack):
			self.commandStyler.setStyling(argument.span.slice, StyleId.Complex)
			return

		idx = self.commandStyler.styleForeignNode(value.itemId)
		if idx == value.itemId.span.start.index:
			self.commandStyler.setStyling(value.itemId.span.slice, StyleId.Complex.value)
		if value.nbt is not None:
			idx = self.commandStyler.styleForeignNode(value.nbt)
			if idx == value.nbt.span.start.index:
				self.commandStyler.setStyling(value.nbt.span.slice, StyleId.Complex.value)





