from itertools import chain
from typing import Protocol, Optional

from Cat.utils import Decorator
from Cat.utils.collections import AddToDictDecorator
from model.commands.argumentTypes import *
from model.commands.parsedCommands import ParsedCommandPart
from session import getSession


class SuggestionProviderFunc(Protocol):
	def __call__(self, argument: ParsedCommandPart) -> list[str]:
		pass


__suggestionProviders: dict[str, SuggestionProviderFunc] = {}
suggestionProvider = Decorator(AddToDictDecorator[str, SuggestionProviderFunc](__suggestionProviders))


def getSuggestionProvider(type_: ArgumentType) -> Optional[SuggestionProviderFunc]:
	if isinstance(type_, ArgumentType):
		return __suggestionProviders.get(type_.name)
	else:
		return None


@suggestionProvider(BRIGADIER_BOOL.name)
def suggestBRIGADIER_BOOL(argument: ParsedCommandPart) -> list[str]:
	return ['true', 'false']


@suggestionProvider(BRIGADIER_DOUBLE.name)
def suggestBRIGADIER_DOUBLE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(BRIGADIER_FLOAT.name)
def suggestBRIGADIER_FLOAT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(BRIGADIER_INTEGER.name)
def suggestBRIGADIER_INTEGER(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(BRIGADIER_LONG.name)
def suggestBRIGADIER_LONG(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(BRIGADIER_STRING.name)
def suggestBRIGADIER_STRING(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_ANGLE.name)
def suggestMINECRAFT_ANGLE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_BLOCK_POS.name)
def suggestMINECRAFT_BLOCK_POS(argument: ParsedCommandPart) -> list[str]:
	return ['^ ^ ^', '~ ~ ~']


@suggestionProvider(MINECRAFT_BLOCK_PREDICATE.name)
def suggestMINECRAFT_BLOCK_PREDICATE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_BLOCK_STATE.name)
def suggestMINECRAFT_BLOCK_STATE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_COLUMN_POS.name)
def suggestMINECRAFT_COLUMN_POS(argument: ParsedCommandPart) -> list[str]:
	return ['~ ~']


@suggestionProvider(MINECRAFT_COMPONENT.name)
def suggestMINECRAFT_COMPONENT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_DIMENSION.name)
def suggestMINECRAFT_DIMENSION(argument: ParsedCommandPart) -> list[str]:
	return ['minecraft:overworld', 'minecraft:nether', 'minecraft:end']


@suggestionProvider(MINECRAFT_ENTITY.name)
def suggestMINECRAFT_ENTITY(argument: ParsedCommandPart) -> list[str]:
	return ['@a', '@e', '@s', '@p', '@r', ]


@suggestionProvider(MINECRAFT_ENTITY_SUMMON.name)
def suggestMINECRAFT_ENTITY_SUMMON(argument: ParsedCommandPart) -> list[str]:
	return ['minecraft:']


@suggestionProvider(MINECRAFT_FLOAT_RANGE.name)
def suggestMINECRAFT_FLOAT_RANGE(argument: ParsedCommandPart) -> list[str]:
	return ['0...']


@suggestionProvider(MINECRAFT_FUNCTION.name)
def suggestMINECRAFT_FUNCTION(argument: ParsedCommandPart) -> list[str]:
	result = [f.asString for dp in getSession().world.datapacks for f in chain(dp.contents.functions, dp.contents.tags.functions)]
	return result


@suggestionProvider(MINECRAFT_GAME_PROFILE.name)
def suggestMINECRAFT_GAME_PROFILE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_INT_RANGE.name)
def suggestMINECRAFT_INT_RANGE(argument: ParsedCommandPart) -> list[str]:
	return ['0...']


@suggestionProvider(MINECRAFT_ITEM_ENCHANTMENT.name)
def suggestMINECRAFT_ITEM_ENCHANTMENT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_ITEM_PREDICATE.name)
def suggestMINECRAFT_ITEM_PREDICATE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_ITEM_SLOT.name)
def suggestMINECRAFT_ITEM_SLOT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_ITEM_STACK.name)
def suggestMINECRAFT_ITEM_STACK(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_MESSAGE.name)
def suggestMINECRAFT_MESSAGE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_MOB_EFFECT.name)
def suggestMINECRAFT_MOB_EFFECT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_NBT_COMPOUND_TAG.name)
def suggestMINECRAFT_NBT_COMPOUND_TAG(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_NBT_PATH.name)
def suggestMINECRAFT_NBT_PATH(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_NBT_TAG.name)
def suggestMINECRAFT_NBT_TAG(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_OBJECTIVE.name)
def suggestMINECRAFT_OBJECTIVE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_OBJECTIVE_CRITERIA.name)
def suggestMINECRAFT_OBJECTIVE_CRITERIA(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_PARTICLE.name)
def suggestMINECRAFT_PARTICLE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_RESOURCE_LOCATION.name)
def suggestMINECRAFT_RESOURCE_LOCATION(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_ROTATION.name)
def suggestMINECRAFT_ROTATION(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_SCORE_HOLDER.name)
def suggestMINECRAFT_SCORE_HOLDER(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_SCOREBOARD_SLOT.name)
def suggestMINECRAFT_SCOREBOARD_SLOT(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_SWIZZLE.name)
def suggestMINECRAFT_SWIZZLE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_TEAM.name)
def suggestMINECRAFT_TEAM(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_TIME.name)
def suggestMINECRAFT_TIME(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_UUID.name)
def suggestMINECRAFT_UUID(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_VEC2.name)
def suggestMINECRAFT_VEC2(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(MINECRAFT_VEC3.name)
def suggestMINECRAFT_VEC3(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(ST_DPE_COMMAND.name)
def suggestST_DPE_COMMAND(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(ST_DPE_DATAPACK.name)
def suggestST_DPE_DATAPACK(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(ST_DPE_GAME_RULE.name)
def suggestST_DPE_GAME_RULE(argument: ParsedCommandPart) -> list[str]:
	return []


@suggestionProvider(ST_DPE_RAW_JSON_TEXT.name)
def suggestST_DPE_RAW_JSON_TEXT(argument: ParsedCommandPart) -> list[str]:
	return []

