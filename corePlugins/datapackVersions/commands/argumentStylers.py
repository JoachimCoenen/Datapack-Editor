from __future__ import annotations

from typing import Optional

from base.model.parsing.tree import Node
from base.gui.styler import CommonStyleIds
from base.model.utils import LanguageId, Span
from corePlugins.mcFunction.command import ParsedArgument
from corePlugins.mcFunction.mcFunctionStyler import addSimpleArgumentStyler, argumentStyler, ArgumentStyler
from .argumentTypes import *
from .targetSelector import DPE_TARGET_SELECTOR_ADVANCEMENTS, DPE_TARGET_SELECTOR_ADVANCEMENTS_CRITERION, DPE_TARGET_SELECTOR_SCORES


addSimpleArgumentStyler(CommonStyleIds.special2, forArgTypes=[
	MINECRAFT_BLOCK_PREDICATE,
	MINECRAFT_BLOCK_STATE,
	MINECRAFT_COMPONENT,
	MINECRAFT_ITEM_PREDICATE,
	MINECRAFT_ITEM_STACK,
	MINECRAFT_NBT_COMPOUND_TAG,
	MINECRAFT_NBT_TAG,
	MINECRAFT_PARTICLE,
])

addSimpleArgumentStyler(CommonStyleIds.special_constant, forArgTypes=[
	# BRIGADIER_BOOL,
	MINECRAFT_COLOR,
	MINECRAFT_ENTITY_ANCHOR,
	MINECRAFT_ITEM_SLOT,
	MINECRAFT_ITEM_SLOTS,
	MINECRAFT_SCOREBOARD_SLOT,
	MINECRAFT_SWIZZLE,
	MINECRAFT_TEAM,
])

addSimpleArgumentStyler(CommonStyleIds.number, forArgTypes=[
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

addSimpleArgumentStyler(CommonStyleIds.operator, forArgTypes=[
	MINECRAFT_OPERATION,
	DPE_COMPARE_OPERATION,
])

addSimpleArgumentStyler(CommonStyleIds.string, forArgTypes=[
	# BRIGADIER_STRING,
	MINECRAFT_MESSAGE,
	MINECRAFT_NBT_PATH,
	MINECRAFT_UUID,
])

addSimpleArgumentStyler(CommonStyleIds.content_locator, forArgTypes=[
	MINECRAFT_DIMENSION,
	MINECRAFT_ENTITY_SUMMON,
	MINECRAFT_FUNCTION,
	MINECRAFT_ITEM_ENCHANTMENT,
	MINECRAFT_MOB_EFFECT,
	MINECRAFT_OBJECTIVE,
	MINECRAFT_OBJECTIVE_CRITERIA,
	MINECRAFT_RESOURCE_LOCATION,
	DPE_ADVANCEMENT,
	DPE_BIOME_ID,
])

addSimpleArgumentStyler(CommonStyleIds.special1, forArgTypes=[
	MINECRAFT_ENTITY,
	MINECRAFT_GAME_PROFILE,
	MINECRAFT_SCORE_HOLDER,
])


def styleForeignNode2(self: ArgumentStyler, value: Optional[Node], span: Span) -> None:
	if value is not None:
		idx = self.commandStyler.styleForeignNode(value)
		if idx != value.span.start.index:
			return
	self.setStyling(span.slice, CommonStyleIds.special2)


@argumentStyler(MINECRAFT_COMPONENT.name, forceOverride=True)
@argumentStyler(MINECRAFT_STYLE.name, forceOverride=True)
class ComponentStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('Structure')]

	def style(self, argument: ParsedArgument) -> None:
		styleForeignNode2(self, argument.value, argument.span)


@argumentStyler(MINECRAFT_NBT_COMPOUND_TAG.name, forceOverride=True)
@argumentStyler(MINECRAFT_NBT_TAG.name, forceOverride=True)
class SNBTStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('Structure')]

	def style(self, argument: ParsedArgument) -> None:
		styleForeignNode2(self, argument.value, argument.span)


@argumentStyler(MINECRAFT_ITEM_STACK.name, forceOverride=True)
@argumentStyler(MINECRAFT_ITEM_PREDICATE.name, forceOverride=True)
class ItemStackStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('Structure'), LanguageId('PredicateArgs')]

	def style(self, argument: ParsedArgument) -> None:
		self.commandStyler.styleStructuredNodeForeignNodes(argument, CommonStyleIds.content_locator)


@argumentStyler(MINECRAFT_BLOCK_STATE.name, forceOverride=True)
@argumentStyler(MINECRAFT_BLOCK_PREDICATE.name, forceOverride=True)
class BlockStateStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('Structure'), LanguageId('FilterArg')]

	def style(self, argument: ParsedArgument) -> None:
		self.commandStyler.styleStructuredNodeForeignNodes(argument, CommonStyleIds.content_locator)


@argumentStyler(MINECRAFT_ENTITY.name, forceOverride=True)
@argumentStyler(MINECRAFT_GAME_PROFILE.name, forceOverride=True)
@argumentStyler(MINECRAFT_SCORE_HOLDER.name, forceOverride=True)
class EntityStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('Structure'), LanguageId('FilterArg')]

	def style(self, argument: ParsedArgument) -> None:
		self.commandStyler.styleStructuredNodeForeignNodes(argument, CommonStyleIds.special1)


@argumentStyler(DPE_TARGET_SELECTOR_SCORES.name, forceOverride=True)
@argumentStyler(DPE_TARGET_SELECTOR_ADVANCEMENTS.name, forceOverride=True)
@argumentStyler(DPE_TARGET_SELECTOR_ADVANCEMENTS_CRITERION.name, forceOverride=True)
class TargetSelectorScoresStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return [LanguageId('FilterArg')]

	def style(self, argument: ParsedArgument) -> None:
		styleForeignNode2(self, argument.value, argument.span)


@argumentStyler(MINECRAFT_LOOT_TABLE.name, forceOverride=True)
@argumentStyler(MINECRAFT_LOOT_MODIFIER.name, forceOverride=True)
@argumentStyler(MINECRAFT_PARTICLE.name, forceOverride=True)
@argumentStyler(MINECRAFT_PREDICATE.name, forceOverride=True)
class StructuredNodeStyler(ArgumentStyler):
	@classmethod
	def localLanguages(cls) -> list[LanguageId]:
		return []

	def style(self, argument: ParsedArgument) -> None:
		self.commandStyler.styleStructuredNodeForeignNodes(argument, CommonStyleIds.content_locator)
