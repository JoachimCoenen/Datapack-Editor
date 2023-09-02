from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Type, Optional, ClassVar

from Cat.utils import Decorator, first
from Cat.utils.collections_ import AddToDictDecorator
from base.gui.styler import DEFAULT_STYLE_ID, CatStyler, StyleIdEnum, StylingFunc
from .argumentTypes import *
from .argumentValues import ItemStack, BlockState, TargetSelector
from .command import MCFunction, ParsedComment, ParsedCommand, KeywordSchema, ArgumentSchema, CommandPart, ParsedArgument
from base.model.utils import LanguageId


class StyleId(StyleIdEnum):
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
	# innerStylers: dict[Type[Node], CatStyler]
	commandStyler: MCCommandStyler
	offset: int = field(init=False)
	setStyling: StylingFunc = field(init=False)

	def __post_init__(self):
		self.offset = self.commandStyler.offset
		self.setStyling = self.commandStyler.setStyling

	@classmethod
	@abstractmethod
	def localLanguages(cls) -> list[LanguageId]:
		pass

	@abstractmethod
	def style(self, argument: ParsedArgument) -> None:
		pass


_argumentStylers: dict[str, Type[ArgumentStyler]] = {}
argumentStyler = Decorator(AddToDictDecorator(_argumentStylers))


@dataclass
class MCCommandStyler(CatStyler[CommandPart]):

	@property
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		return StyleId

	argumentStylers: dict[str, ArgumentStyler] = field(init=False, repr=False, compare=False)

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		localInnerLanguages = []
		for argS in _argumentStylers.values():
			localInnerLanguages.extend(argS.localLanguages())
		return list(set(localInnerLanguages))
		# return [LanguageId('JSON')]

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
		self.setStyling(comment.span.slice, StyleId.Comment.value + self.offset)
		return comment.span.end.index

	def styleCommand(self, command: ParsedCommand) -> int:
		return self.styleArguments(command)

	def styleArguments(self, argument: CommandPart) -> int:
		span = argument.span.slice
		while argument is not None:
			span = self.styleArgument(argument)
			argument = argument.next
		return span.stop

	def styleArgument(self, argument: CommandPart) -> slice:
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
						return span
			else:
				style = StyleId.Error
		self.setStyling(span, style.value + self.offset)
		return span


def addSimpleArgumentStyler(style: StyleId, *, forArgTypes: list[ArgumentType]) -> None:
	styleId = style.value

	class SimpleArgumentStyler(ArgumentStyler):
		STYLE: ClassVar[StyleId] = styleId

		@classmethod
		def localLanguages(cls) -> list[LanguageId]:
			return []

		def style(self, argument: ParsedArgument) -> None:
			self.setStyling(argument.span.slice, styleId + self.offset)

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
			self.setStyling(argument.span.slice, StyleId.Complex.value + self.offset)


@argumentStyler(MINECRAFT_NBT_COMPOUND_TAG.name, forceOverride=True)
@argumentStyler(MINECRAFT_NBT_TAG.name, forceOverride=True)
class SNBTStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		idx = self.commandStyler.styleForeignNode(argument.value)
		if idx == argument.value.span.start.index:
			self.setStyling(argument.span.slice, StyleId.Complex.value + self.offset)


@argumentStyler(MINECRAFT_ITEM_STACK.name, forceOverride=True)
@argumentStyler(MINECRAFT_ITEM_PREDICATE.name, forceOverride=True)
class ItemStackStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: ItemStack = argument.value
		if not isinstance(value, ItemStack):
			self.setStyling(argument.span.slice, StyleId.Complex.value + self.offset)
			return

		idx = self.commandStyler.styleForeignNode(value.itemId)
		if idx == value.itemId.span.start.index:
			self.setStyling(value.itemId.span.slice, StyleId.Complex.value + self.offset)
		if value.nbt is not None:
			idx = self.commandStyler.styleForeignNode(value.nbt)
			if idx == value.nbt.span.start.index:
				self.setStyling(value.nbt.span.slice, StyleId.Complex.value + self.offset)


@argumentStyler(MINECRAFT_BLOCK_STATE.name, forceOverride=True)
@argumentStyler(MINECRAFT_BLOCK_PREDICATE.name, forceOverride=True)
class BlockStateStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: BlockState = argument.value
		if not isinstance(value, BlockState):
			self.setStyling(argument.span.slice, StyleId.Complex.value + self.offset)
			return

		idx = self.commandStyler.styleForeignNode(value.blockId)
		if idx == value.blockId.span.start.index:
			self.setStyling(value.blockId.span.slice, StyleId.Complex.value + self.offset)
		if value.states:
			for name, state in value.states.items():
				self.setStyling(state.key.span.slice, StyleId.Complex.value + self.offset)
				if state.value is not None:
					self.commandStyler.styleArguments(state.value)
		if value.nbt is not None:
			idx = self.commandStyler.styleForeignNode(value.nbt)
			if idx == value.nbt.span.start.index:
				self.setStyling(value.nbt.span.slice, StyleId.Complex.value + self.offset)


@argumentStyler(MINECRAFT_ENTITY.name, forceOverride=True)
@argumentStyler(MINECRAFT_GAME_PROFILE.name, forceOverride=True)
@argumentStyler(MINECRAFT_SCORE_HOLDER.name, forceOverride=True)
class EntityStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: TargetSelector = argument.value
		if not isinstance(value, TargetSelector) or not value.arguments:
			self.setStyling(argument.span.slice, StyleId.TargetSelector.value + self.offset)
		else:
			slice1 = slice(argument.span.start.index, first(value.arguments.values()).key.span.start.index)
			self.setStyling(slice1, StyleId.TargetSelector.value + self.offset)
			for name, state in value.arguments.items():
				self.setStyling(state.key.span.slice, StyleId.TargetSelector.value + self.offset)
				if state.value is not None:
					self.commandStyler.styleArguments(state.value)





