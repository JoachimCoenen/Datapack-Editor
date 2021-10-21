from typing import Protocol, Sequence, TYPE_CHECKING, Optional

from Cat.utils import Maybe, escapeForXml, Decorator
from Cat.utils.collections import AddToDictDecorator
from model.commands.argumentTypes import *
from model.commands.command import formatPossibilities, CommandNode, TERMINAL, Keyword, Switch, ArgumentInfo, COMMANDS_ROOT
from model.commands.utils import CommandSemanticsError
from model.commands.parsedCommands import ParsedMCFunction, ParsedArgument, ParsedCommandPart
from model.Model import ResourceLocation
from model.parsingUtils import Span

if TYPE_CHECKING:
	from session import Session

	def getSession() -> Session:
		pass
else:
	def getSession():
		pass


def checkMCFunction(mcFunction: ParsedMCFunction) -> list[CommandSemanticsError]:
	errors: list[CommandSemanticsError] = []
	for command in mcFunction.commands:
		if command is None:
			continue

		possibilities: Sequence[CommandNode] = command.info.next
		argument = command.argument

		while argument is not None:
			if argument.info is None:
				if possibilities:
					possibilitiesStr = escapeForXml(formatPossibilities(possibilities))
					valueStr = escapeForXml(argument.value)
					errors.append(CommandSemanticsError(f"unknown argument: expected `{possibilitiesStr}`, but got: `{valueStr}`", argument.span))
					possibilities = []
				else:
					valueStr = escapeForXml(argument.value)
					errors.append(CommandSemanticsError(f"too many arguments: `{valueStr}`", argument.span))
			else:
				validateArgument(argument, errorsIO=errors)
				possibilities = argument.info.next
			argument = argument.next

		if possibilities and TERMINAL not in possibilities:
			lastArgEnd = Maybe(command.argument).recursive(ParsedArgument.next.get).orElse(command).span.end
			if lastArgEnd.index >= command.span.end.index:
				lastArgEnd = lastArgEnd.copy()
				lastArgEnd.column -= 1
				lastArgEnd.index -= 1
				if lastArgEnd.column < 0:
					lastArgEnd = command.span.start
			possibilitiesStr = escapeForXml(formatPossibilities(possibilities))
			errors.append(CommandSemanticsError(f"missing argument: `{possibilitiesStr}`", Span(lastArgEnd, command.span.end)))

	return errors


def validateArgument(argument: ParsedCommandPart, *, errorsIO: list[CommandSemanticsError]) -> None:
	info = argument.info
	if isinstance(info, Keyword):
		pass
	elif isinstance(info, Switch):
		# TODO: validateArgument for Switch?
		pass
	elif isinstance(info, ArgumentInfo):
		type_: ArgumentType = info.type
		if isinstance(type_, LiteralsArgumentType):
			pass
		else:
			validator = getValidator(type_)
			if validator is not None:
				error = validator(argument)
				if error is not None:
					errorsIO.append(error)
	elif info is COMMANDS_ROOT:
		# TODO: validateArgument for command. (i.e. deprecated, wrongVersion, etc...)
		pass


class ValidatorFunc(Protocol):
	def __call__(self, argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
		pass


__validators: dict[str, ValidatorFunc] = {}
validator = Decorator(AddToDictDecorator[str, ValidatorFunc](__validators))


def getValidator(type_: ArgumentType) -> Optional[ValidatorFunc]:
	if isinstance(type_, ArgumentType):
		return __validators.get(type_.name)
	else:
		return None


@validator(BRIGADIER_BOOL.name)
def validateBRIGADIER_BOOL(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(BRIGADIER_DOUBLE.name)
def validateBRIGADIER_DOUBLE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(BRIGADIER_FLOAT.name)
def validateBRIGADIER_FLOAT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(BRIGADIER_INTEGER.name)
def validateBRIGADIER_INTEGER(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(BRIGADIER_LONG.name)
def validateBRIGADIER_LONG(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(BRIGADIER_STRING.name)
def validateBRIGADIER_STRING(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ANGLE.name)
def validateMINECRAFT_ANGLE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_BLOCK_POS.name)
def validateMINECRAFT_BLOCK_POS(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_BLOCK_PREDICATE.name)
def validateMINECRAFT_BLOCK_PREDICATE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_BLOCK_STATE.name)
def validateMINECRAFT_BLOCK_STATE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_COLUMN_POS.name)
def validateMINECRAFT_COLUMN_POS(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_COMPONENT.name)
def validateMINECRAFT_COMPONENT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_DIMENSION.name)
def validateMINECRAFT_DIMENSION(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	if argument.value not in ['minecraft:overworld', 'minecraft:nether', 'minecraft:end']:
		return CommandSemanticsError(f"Unknown dimension '{argument.value}'.", argument.span)
	else:
		return None


@validator(MINECRAFT_ENTITY.name)
def validateMINECRAFT_ENTITY(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ENTITY_SUMMON.name)
def validateMINECRAFT_ENTITY_SUMMON(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_FLOAT_RANGE.name)
def validateMINECRAFT_FLOAT_RANGE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_FUNCTION.name)
def validateMINECRAFT_FUNCTION(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	value: ResourceLocation = argument.value
	if value.isTag:
		isValid = any(value in dp.contents.tags.functions for dp in getSession().world.datapacks)
	else:
		isValid = any(value in dp.contents.functions for dp in getSession().world.datapacks)
	if isValid:
		return None
	else:
		if value.isTag:
			return CommandSemanticsError(f"function tag '{value.asString}' is never defined.", argument.span, style='warning')
		else:
			return CommandSemanticsError(f"Unknown function '{value.asString}'.", argument.span)


@validator(MINECRAFT_GAME_PROFILE.name)
def validateMINECRAFT_GAME_PROFILE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_INT_RANGE.name)
def validateMINECRAFT_INT_RANGE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ITEM_ENCHANTMENT.name)
def validateMINECRAFT_ITEM_ENCHANTMENT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ITEM_PREDICATE.name)
def validateMINECRAFT_ITEM_PREDICATE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ITEM_SLOT.name)
def validateMINECRAFT_ITEM_SLOT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ITEM_STACK.name)
def validateMINECRAFT_ITEM_STACK(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_MESSAGE.name)
def validateMINECRAFT_MESSAGE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_MOB_EFFECT.name)
def validateMINECRAFT_MOB_EFFECT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_NBT_COMPOUND_TAG.name)
def validateMINECRAFT_NBT_COMPOUND_TAG(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_NBT_PATH.name)
def validateMINECRAFT_NBT_PATH(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_NBT_TAG.name)
def validateMINECRAFT_NBT_TAG(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_OBJECTIVE.name)
def validateMINECRAFT_OBJECTIVE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_OBJECTIVE_CRITERIA.name)
def validateMINECRAFT_OBJECTIVE_CRITERIA(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_PARTICLE.name)
def validateMINECRAFT_PARTICLE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_RESOURCE_LOCATION.name)
def validateMINECRAFT_RESOURCE_LOCATION(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_ROTATION.name)
def validateMINECRAFT_ROTATION(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_SCORE_HOLDER.name)
def validateMINECRAFT_SCORE_HOLDER(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_SCOREBOARD_SLOT.name)
def validateMINECRAFT_SCOREBOARD_SLOT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_SWIZZLE.name)
def validateMINECRAFT_SWIZZLE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_TEAM.name)
def validateMINECRAFT_TEAM(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_TIME.name)
def validateMINECRAFT_TIME(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_UUID.name)
def validateMINECRAFT_UUID(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_VEC2.name)
def validateMINECRAFT_VEC2(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(MINECRAFT_VEC3.name)
def validateMINECRAFT_VEC3(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(ST_DPE_COMMAND.name)
def validateST_DPE_COMMAND(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(ST_DPE_DATAPACK.name)
def validateST_DPE_DATAPACK(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(ST_DPE_GAME_RULE.name)
def validateST_DPE_GAME_RULE(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None


@validator(ST_DPE_RAW_JSON_TEXT.name)
def validateST_DPE_RAW_JSON_TEXT(argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
	return None
