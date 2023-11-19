from __future__ import annotations

from typing import Optional

from base.model.parsing.tree import Node
from cat.utils import first
from base.gui.styler import StyleId
from base.model.utils import LanguageId, Span
from corePlugins.mcFunction.command import ParsedArgument
from corePlugins.mcFunction.mcFunctionStyler import addSimpleArgumentStyler, argumentStyler, ArgumentStyler, StyleIds
from .argumentTypes import *
from .argumentValues import ItemStack, BlockState, TargetSelector


def initPlugin() -> None:
	pass


_allArgumentTypeStyles: dict[str, Optional[StyleId]] = {
	# BRIGADIER_BOOL.name:               StyleIds.Constant,
	# BRIGADIER_DOUBLE.name:             StyleIds.Number,
	# BRIGADIER_FLOAT.name:              StyleIds.Number,
	# BRIGADIER_INTEGER.name:            StyleIds.Number,
	# BRIGADIER_LONG.name:               StyleIds.Number,
	# BRIGADIER_STRING.name:             StyleIds.String,
	MINECRAFT_ANGLE.name:              StyleIds.Number,
	MINECRAFT_BLOCK_POS.name:          StyleIds.Number,
	MINECRAFT_BLOCK_PREDICATE.name:    StyleIds.Complex,
	MINECRAFT_BLOCK_STATE.name:        StyleIds.Complex,
	MINECRAFT_COLOR.name:              StyleIds.Constant,
	MINECRAFT_COLUMN_POS.name:         StyleIds.Number,
	MINECRAFT_COMPONENT.name:          StyleIds.Complex,
	MINECRAFT_DIMENSION.name:          StyleIds.String,
	MINECRAFT_ENTITY.name:             StyleIds.TargetSelector,
	MINECRAFT_ENTITY_ANCHOR.name:      StyleIds.Constant,
	MINECRAFT_ENTITY_SUMMON.name:      StyleIds.String,
	MINECRAFT_FLOAT_RANGE.name:        StyleIds.Number,
	MINECRAFT_FUNCTION.name:           StyleIds.String,
	MINECRAFT_GAME_PROFILE.name:       StyleIds.TargetSelector,
	MINECRAFT_INT_RANGE.name:          StyleIds.Number,
	MINECRAFT_ITEM_ENCHANTMENT.name:   StyleIds.String,
	MINECRAFT_ITEM_PREDICATE.name:     StyleIds.Complex,
	MINECRAFT_ITEM_SLOT.name:          StyleIds.Constant,
	MINECRAFT_ITEM_STACK.name:         StyleIds.Complex,
	MINECRAFT_MESSAGE.name:            StyleIds.String,
	MINECRAFT_MOB_EFFECT.name:         StyleIds.String,
	MINECRAFT_NBT_COMPOUND_TAG.name:   StyleIds.Complex,
	MINECRAFT_NBT_PATH.name:           StyleIds.Complex,
	MINECRAFT_NBT_TAG.name:            StyleIds.Complex,
	MINECRAFT_OBJECTIVE.name:          StyleIds.String,
	MINECRAFT_OBJECTIVE_CRITERIA.name: StyleIds.String,
	MINECRAFT_OPERATION.name:          StyleIds.Operator,
	MINECRAFT_PARTICLE.name:           StyleIds.Complex,
	MINECRAFT_PREDICATE.name:          StyleIds.String,
	MINECRAFT_RESOURCE_LOCATION.name:  StyleIds.String,
	MINECRAFT_ROTATION.name:           StyleIds.Number,
	MINECRAFT_SCORE_HOLDER.name:       StyleIds.TargetSelector,
	MINECRAFT_SCOREBOARD_SLOT.name:    StyleIds.Constant,
	MINECRAFT_SWIZZLE.name:            StyleIds.Constant,
	MINECRAFT_TEAM.name:               StyleIds.Constant,
	MINECRAFT_TIME.name:               StyleIds.Number,
	MINECRAFT_UUID.name:               StyleIds.String,
	MINECRAFT_VEC2.name:               StyleIds.Number,
	MINECRAFT_VEC3.name:               StyleIds.Number,
	DPE_ADVANCEMENT.name:              StyleIds.String,
	DPE_COMPARE_OPERATION.name:        StyleIds.Operator,
	DPE_BIOME_ID.name:                 StyleIds.String,
}

addSimpleArgumentStyler(StyleIds.Complex, forArgTypes=[
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

addSimpleArgumentStyler(StyleIds.Constant, forArgTypes=[
	# BRIGADIER_BOOL,
	MINECRAFT_COLOR,
	MINECRAFT_ENTITY_ANCHOR,
	MINECRAFT_ITEM_SLOT,
	MINECRAFT_SCOREBOARD_SLOT,
	MINECRAFT_SWIZZLE,
	MINECRAFT_TEAM,
])

addSimpleArgumentStyler(StyleIds.Number, forArgTypes=[
	# BRIGADIER_DOUBLE,
	# BRIGADIER_FLOAT,
	# BRIGADIER_INTEGER,
	# BRIGADIER_LONG,
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

addSimpleArgumentStyler(StyleIds.Operator, forArgTypes=[
	MINECRAFT_OPERATION,
	DPE_COMPARE_OPERATION,
])

addSimpleArgumentStyler(StyleIds.String, forArgTypes=[
	# BRIGADIER_STRING,
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

addSimpleArgumentStyler(StyleIds.TargetSelector, forArgTypes=[
	MINECRAFT_ENTITY,
	MINECRAFT_GAME_PROFILE,
	MINECRAFT_SCORE_HOLDER,
])


def styleForeignNode2(self: ArgumentStyler, value: Optional[Node], span: Span) -> None:
	if value is not None:
		idx = self.commandStyler.styleForeignNode(value)
		if idx != value.span.start.index:
			return
	self.setStyling(span.slice, StyleIds.Complex)


@argumentStyler(MINECRAFT_COMPONENT.name, forceOverride=True)
class ComponentStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('JSON')]

	def style(self, argument: ParsedArgument) -> None:
		styleForeignNode2(self, argument.value, argument.span)


@argumentStyler(MINECRAFT_NBT_COMPOUND_TAG.name, forceOverride=True)
@argumentStyler(MINECRAFT_NBT_TAG.name, forceOverride=True)
class SNBTStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		styleForeignNode2(self, argument.value, argument.span)


@argumentStyler(MINECRAFT_ITEM_STACK.name, forceOverride=True)
@argumentStyler(MINECRAFT_ITEM_PREDICATE.name, forceOverride=True)
class ItemStackStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: ItemStack = argument.value
		if not isinstance(value, ItemStack):
			self.setStyling(argument.span.slice, StyleIds.Complex)
			return

		styleForeignNode2(self, value.itemId, value.itemId.span)
		if value.nbt is not None:
			styleForeignNode2(self, value.nbt, value.nbt.span)


@argumentStyler(MINECRAFT_BLOCK_STATE.name, forceOverride=True)
@argumentStyler(MINECRAFT_BLOCK_PREDICATE.name, forceOverride=True)
class BlockStateStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('SNBT')]

	def style(self, argument: ParsedArgument) -> None:
		value: BlockState = argument.value
		if not isinstance(value, BlockState):
			self.setStyling(argument.span.slice, StyleIds.Complex)
			return

		styleForeignNode2(self, value.blockId, value.blockId.span)
		if value.states:
			for name, state in value.states.items():
				self.setStyling(state.key.span.slice, StyleIds.Complex)
				if state.value is not None:
					self.commandStyler.styleArguments(state.value)
		if value.nbt is not None:
			styleForeignNode2(self, value.nbt, value.nbt.span)


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
			self.setStyling(argument.span.slice, StyleIds.TargetSelector)
		else:
			slice1 = slice(argument.span.start.index, first(value.arguments.values()).key.span.start.index)
			self.setStyling(slice1, StyleIds.TargetSelector)
			for name, state in value.arguments.items():
				self.setStyling(state.key.span.slice, StyleIds.TargetSelector)
				if state.value is not None:
					self.commandStyler.styleArguments(state.value)
			self.setStyling(argument.span.slice, StyleIds.TargetSelector)  # style all remaining characters
