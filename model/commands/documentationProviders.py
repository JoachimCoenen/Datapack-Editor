from typing import Protocol, Optional

from Cat.CatPythonGUI.GUI import PythonGUI
from Cat.utils import Decorator
from Cat.utils.collections import AddToDictDecorator
from Cat.utils.utils import HTMLStr, escapeForXml, HTMLifyMarkDownSubSet
from model.commands.argumentTypes import *
from model.commands.command import ArgumentInfo
from model.commands.parsedCommands import ParsedCommandPart
from model.datapackContents import ResourceLocation
from session import getSession


class DocumentationProviderFunc(Protocol):
	def __call__(self, argument: ParsedCommandPart) -> HTMLStr:
		pass


__documentationProviders: dict[str, DocumentationProviderFunc] = {}
documentationProvider = Decorator(AddToDictDecorator[str, DocumentationProviderFunc](__documentationProviders))


def getDocumentationProvider(type_: ArgumentType) -> Optional[DocumentationProviderFunc]:
	if isinstance(type_, ArgumentType):
		return __documentationProviders.get(type_.name)
	else:
		return None


def defaultDocumentationProvider(argument: ParsedCommandPart) -> HTMLStr:
	info = argument.info
	if info is not None:
		name = (info.name)
		description = info.description
		if isinstance(info, ArgumentInfo):
			typeStr = escapeForXml(info.type.name)
			typeDescription = [
				(info.type.description),
				(info.type.description2),
			]
		else:
			typeStr = escapeForXml(info.asCodeString())
			typeDescription = []
		tip = f"{name}\n\n`{typeStr}`\n\n{description}"
		if typeDescription:
			tip += '\n\n'.join(typeDescription)
		tip = HTMLifyMarkDownSubSet(tip)
	else:
		message = 'no documentation available (most likely due to parsing errors)'
		tip = f'<div style="{PythonGUI.helpBoxStyles["error"]}">{message}</div>'
	return tip


@documentationProvider(BRIGADIER_BOOL.name)
def getDocForBRIGADIER_BOOL(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(BRIGADIER_DOUBLE.name)
def getDocForBRIGADIER_DOUBLE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(BRIGADIER_FLOAT.name)
def getDocForBRIGADIER_FLOAT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(BRIGADIER_INTEGER.name)
def getDocForBRIGADIER_INTEGER(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(BRIGADIER_LONG.name)
def getDocForBRIGADIER_LONG(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(BRIGADIER_STRING.name)
def getDocForBRIGADIER_STRING(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ANGLE.name)
def getDocForMINECRAFT_ANGLE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_BLOCK_POS.name)
def getDocForMINECRAFT_BLOCK_POS(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_BLOCK_PREDICATE.name)
def getDocForMINECRAFT_BLOCK_PREDICATE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_BLOCK_STATE.name)
def getDocForMINECRAFT_BLOCK_STATE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_COLUMN_POS.name)
def getDocForMINECRAFT_COLUMN_POS(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_COMPONENT.name)
def getDocForMINECRAFT_COMPONENT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_DIMENSION.name)
def getDocForMINECRAFT_DIMENSION(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ENTITY.name)
def getDocForMINECRAFT_ENTITY(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ENTITY_SUMMON.name)
def getDocForMINECRAFT_ENTITY_SUMMON(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_FLOAT_RANGE.name)
def getDocForMINECRAFT_FLOAT_RANGE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_FUNCTION.name)
def getDocForMINECRAFT_FUNCTION(argument: ParsedCommandPart) -> HTMLStr:
	value: ResourceLocation = argument.value
	if not isinstance(value, ResourceLocation):
		return defaultDocumentationProvider(argument)

	if not value.isTag:
		for dp in getSession().world.datapacks:
			if (func := dp.contents.functions.get(value))is not None:
				return func.documentation

	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_GAME_PROFILE.name)
def getDocForMINECRAFT_GAME_PROFILE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_INT_RANGE.name)
def getDocForMINECRAFT_INT_RANGE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ITEM_ENCHANTMENT.name)
def getDocForMINECRAFT_ITEM_ENCHANTMENT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ITEM_PREDICATE.name)
def getDocForMINECRAFT_ITEM_PREDICATE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ITEM_SLOT.name)
def getDocForMINECRAFT_ITEM_SLOT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ITEM_STACK.name)
def getDocForMINECRAFT_ITEM_STACK(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_MESSAGE.name)
def getDocForMINECRAFT_MESSAGE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_MOB_EFFECT.name)
def getDocForMINECRAFT_MOB_EFFECT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_NBT_COMPOUND_TAG.name)
def getDocForMINECRAFT_NBT_COMPOUND_TAG(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_NBT_PATH.name)
def getDocForMINECRAFT_NBT_PATH(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_NBT_TAG.name)
def getDocForMINECRAFT_NBT_TAG(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_OBJECTIVE.name)
def getDocForMINECRAFT_OBJECTIVE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_OBJECTIVE_CRITERIA.name)
def getDocForMINECRAFT_OBJECTIVE_CRITERIA(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_PARTICLE.name)
def getDocForMINECRAFT_PARTICLE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_RESOURCE_LOCATION.name)
def getDocForMINECRAFT_RESOURCE_LOCATION(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_ROTATION.name)
def getDocForMINECRAFT_ROTATION(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_SCORE_HOLDER.name)
def getDocForMINECRAFT_SCORE_HOLDER(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_SCOREBOARD_SLOT.name)
def getDocForMINECRAFT_SCOREBOARD_SLOT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_SWIZZLE.name)
def getDocForMINECRAFT_SWIZZLE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_TEAM.name)
def getDocForMINECRAFT_TEAM(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_TIME.name)
def getDocForMINECRAFT_TIME(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_UUID.name)
def getDocForMINECRAFT_UUID(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_VEC2.name)
def getDocForMINECRAFT_VEC2(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(MINECRAFT_VEC3.name)
def getDocForMINECRAFT_VEC3(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(ST_DPE_COMMAND.name)
def getDocForST_DPE_COMMAND(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(ST_DPE_DATAPACK.name)
def getDocForST_DPE_DATAPACK(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(ST_DPE_GAME_RULE.name)
def getDocForST_DPE_GAME_RULE(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)


@documentationProvider(ST_DPE_RAW_JSON_TEXT.name)
def getDocForST_DPE_RAW_JSON_TEXT(argument: ParsedCommandPart) -> HTMLStr:
	return defaultDocumentationProvider(argument)

