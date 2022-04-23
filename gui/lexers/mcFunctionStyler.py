from __future__ import annotations

import enum
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Type, Optional, ClassVar

from Cat.utils import Decorator
from Cat.utils.collections_ import AddToDictDecorator
from gui.lexers.styler import DEFAULT_STYLE_ID, StyleId, CatStyler, registerStyler
from model.commands.argumentTypes import *
from model.commands.command import MCFunction, ParsedComment, ParsedCommand, KeywordSchema, ArgumentSchema, CommandPart, ParsedArgument
from model.utils import LanguageId


class Style(enum.Enum):
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


_allArgumentTypeStyles: dict[str, Optional[Style]] = {
	BRIGADIER_BOOL.name:               Style.Constant,
	BRIGADIER_DOUBLE.name:             Style.Number,
	BRIGADIER_FLOAT.name:              Style.Number,
	BRIGADIER_INTEGER.name:            Style.Number,
	BRIGADIER_LONG.name:               Style.Number,
	BRIGADIER_STRING.name:             Style.String,
	MINECRAFT_ANGLE.name:              Style.Number,
	MINECRAFT_BLOCK_POS.name:          Style.Number,
	MINECRAFT_BLOCK_PREDICATE.name:    Style.Complex,
	MINECRAFT_BLOCK_STATE.name:        Style.Complex,
	MINECRAFT_COLOR.name:              Style.Constant,
	MINECRAFT_COLUMN_POS.name:         Style.Number,
	MINECRAFT_COMPONENT.name:          Style.Complex,
	MINECRAFT_DIMENSION.name:          Style.String,
	MINECRAFT_ENTITY.name:             Style.TargetSelector,
	MINECRAFT_ENTITY_ANCHOR.name:      Style.Constant,
	MINECRAFT_ENTITY_SUMMON.name:      Style.String,
	MINECRAFT_FLOAT_RANGE.name:        Style.Number,
	MINECRAFT_FUNCTION.name:           Style.String,
	MINECRAFT_GAME_PROFILE.name:       Style.TargetSelector,
	MINECRAFT_INT_RANGE.name:          Style.Number,
	MINECRAFT_ITEM_ENCHANTMENT.name:   Style.String,
	MINECRAFT_ITEM_PREDICATE.name:     Style.Complex,
	MINECRAFT_ITEM_SLOT.name:          Style.Constant,
	MINECRAFT_ITEM_STACK.name:         Style.Complex,
	MINECRAFT_MESSAGE.name:            Style.String,
	MINECRAFT_MOB_EFFECT.name:         Style.String,
	MINECRAFT_NBT_COMPOUND_TAG.name:   Style.Complex,
	MINECRAFT_NBT_PATH.name:           Style.Complex,
	MINECRAFT_NBT_TAG.name:            Style.Complex,
	MINECRAFT_OBJECTIVE.name:          Style.String,
	MINECRAFT_OBJECTIVE_CRITERIA.name: Style.String,
	MINECRAFT_OPERATION.name:          Style.Operator,
	MINECRAFT_PARTICLE.name:           Style.Complex,
	MINECRAFT_PREDICATE.name:          Style.String,
	MINECRAFT_RESOURCE_LOCATION.name:  Style.String,
	MINECRAFT_ROTATION.name:           Style.Number,
	MINECRAFT_SCORE_HOLDER.name:       Style.TargetSelector,
	MINECRAFT_SCOREBOARD_SLOT.name:    Style.Constant,
	MINECRAFT_SWIZZLE.name:            Style.Constant,
	MINECRAFT_TEAM.name:               Style.Constant,
	MINECRAFT_TIME.name:               Style.Number,
	MINECRAFT_UUID.name:               Style.String,
	MINECRAFT_VEC2.name:               Style.Number,
	MINECRAFT_VEC3.name:               Style.Number,
	DPE_ADVANCEMENT.name:              Style.String,
	DPE_COMPARE_OPERATION.name:        Style.Operator,
	DPE_BIOME_ID.name:                 Style.String,
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
			Style.Default.name:  self.offset + Style.Default.value,
			Style.Command.name:  self.offset + Style.Command.value,
			Style.String.name:   self.offset + Style.String.value,
			Style.Number.name:   self.offset + Style.Number.value,
			Style.Constant.name: self.offset + Style.Constant.value,
			Style.TargetSelector.name: self.offset + Style.TargetSelector.value,
			Style.Operator.name: self.offset + Style.Operator.value,
			Style.Keyword.name:  self.offset + Style.Keyword.value,

			Style.Complex.name:  self.offset + Style.Complex.value,

			Style.Comment.name:  self.offset + Style.Comment.value,
			Style.Error.name:    self.offset + Style.Error.value,
		}
		return styles

	argumentStylers: dict[str, ArgumentStyler] = field(init=False, repr=False, compare=False)

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return [LanguageId('JSON')]

	@property
	def localStylesCount(self) -> int:
		return self._localStylesCount

	@classmethod
	def language(cls) -> LanguageId:
		return LanguageId('MCCommand')

	def __post_init__(self):
		self.DEFAULT_STYLE: StyleId = self.offset + Style.Default.value
		# self.NULL_STYLE:    StyleId = self.offset + Style.sabotage.null.value
		# self.BOOLEAN_STYLE: StyleId = self.offset + Style.boolean.value
		# self.NUMBER_STYLE:  StyleId = self.offset + Style.number.value
		# self.STRING_STYLE:  StyleId = self.offset + Style.string.value
		# self.KEY_STYLE:     StyleId = self.offset + Style.key.value
		# self.INVALID_STYLE: StyleId = self.offset + Style.invalid.value
		self._localStylesCount = 11

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
		end = function.span.start
		for child in function.children:
			if child is None:
				continue
			elif isinstance(child, ParsedComment):
				end = self.styleComment(child)
			else:
				end = self.styleCommand(child)
		return end

	def styleComment(self, comment: ParsedComment) -> int:
		self.setStyling(comment.span.slice, Style.Comment.value)
		return comment.span.end.index

	def styleCommand(self, command: ParsedCommand) -> int:
		argument: CommandPart = command
		span = command.span.slice
		while argument is not None:
			if isinstance(argument, ParsedCommand):
				style = Style.Command
				span = slice(argument.start.index, argument.start.index + len(argument.name))
			else:
				argument: ParsedArgument
				span = argument.span.slice
				schema = argument.schema
				if isinstance(schema, KeywordSchema):
					style = Style.Keyword
				elif isinstance(schema, ArgumentSchema):
					if isinstance(schema.type, LiteralsArgumentType):
						style = Style.Constant
					else:
						typeName = schema.typeName
						# style = _allArgumentTypeStyles.get(typeName, Style.Error)
						styler = self.argumentStylers.get(typeName, None)
						if styler is None:
							style = Style.Error
						else:
							styler.style(argument)
							argument = argument.next
							continue
				else:
					style = Style.Error
			self.setStyling(span, style.value)

			argument = argument.next
		return span.stop


def addSimpleArgumentStyler(style: Style, *, forArgTypes: list[ArgumentType]) -> None:
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


addSimpleArgumentStyler(Style.Complex, forArgTypes=[
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

addSimpleArgumentStyler(Style.Constant, forArgTypes=[
	BRIGADIER_BOOL,
	MINECRAFT_COLOR,
	MINECRAFT_ENTITY_ANCHOR,
	MINECRAFT_ITEM_SLOT,
	MINECRAFT_SCOREBOARD_SLOT,
	MINECRAFT_SWIZZLE,
	MINECRAFT_TEAM,
])

addSimpleArgumentStyler(Style.Number, forArgTypes=[
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

addSimpleArgumentStyler(Style.Operator, forArgTypes=[
	MINECRAFT_OPERATION,
	DPE_COMPARE_OPERATION,
])

addSimpleArgumentStyler(Style.String, forArgTypes=[
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

addSimpleArgumentStyler(Style.TargetSelector, forArgTypes=[
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
		if idx == argument.value.span.start:
			self.commandStyler.setStyling(argument.span.slice, Style.Complex.value)