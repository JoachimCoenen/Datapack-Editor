import re
from json import JSONDecodeError
from typing import Optional, Union

from Cat.utils.collections import OrderedDict
from model.commands.argumentParsers import argumentParser, makeParsedArgument, missingArgumentParser
from model.commands.argumentTypes import *
from model.commands.argumentValues import BlockState, TargetSelector
from model.commands.command import ArgumentInfo
from model.commands.snbt import parseNBTTag, parseNBTPath
from model.commands.targetSelector import parseTargetSelector
from model.commands.utils import CommandSyntaxError
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.Model import ResourceLocation
from model.nbt.tags import NBTTag, CompoundTag
from model.parsingUtils import Span


def _init():
	pass  # do not remove!


def _parse2dPos(sr: StringReader, ai: ArgumentInfo, *, useFloat: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	if useFloat:
		numberReader = sr.tryReadFloat
	else:
		numberReader = sr.tryReadInt
	sr.save()
	blockPos1: Optional[str] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos1 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeChar(' '):
		sr.rollback()
		return None

	blockPos2: Optional[str] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos2 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	blockPos = (blockPos1, blockPos2)
	return makeParsedArgument(sr, ai, value=blockPos)


def _parse3dPos(sr: StringReader, ai: ArgumentInfo, *, useFloat: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	if useFloat:
		numberReader = sr.tryReadFloat
	else:
		numberReader = sr.tryReadInt
	sr.save()
	blockPos1: Optional[str] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos1 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeChar(' '):
		sr.rollback()
		return None

	blockPos2: Optional[str] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos2 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeChar(' '):
		sr.rollback()
		return None

	blockPos3: Optional[str] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos3 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	blockPos = (blockPos1, blockPos2, blockPos3)
	return makeParsedArgument(sr, ai, value=blockPos)


def tryReadNBTCompoundTag(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[NBTTag]:
	tag = parseNBTTag(sr, errorsIO=errorsIO)
	if tag is None:
		return None

	if type(tag) is CompoundTag:
		return tag
	else:
		sr.rollback()
		return None


def _parseBlockStates(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[OrderedDict[str, str]]:
	if sr.tryConsumeChar('['):
		# block states:
		states = OrderedDict[str, str]()
		sr.tryConsumeWhitespace()
		while not sr.tryConsumeChar(']'):
			prop = sr.tryReadString()
			if prop is None:
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				prop = ''
			elif prop in states:
				errorsIO.append(CommandSyntaxError(f"Property '{prop}' already defined.", Span(sr.currentPos), style='error'))

			sr.tryConsumeWhitespace()
			if not sr.tryConsumeChar('='):
				errorsIO.append(CommandSyntaxError(f"Expected '`=`'.", Span(sr.currentPos), style='error'))

			value = sr.tryReadString()
			if value is None:
				errorsIO.append(CommandSyntaxError(f"Expected a String.", Span(sr.currentPos), style='error'))
				value = ''
			else:
				sr.mergeLastSave()
			states[prop] = value

			sr.tryConsumeWhitespace()
			if sr.tryConsumeChar(']'):
				break
			if sr.tryConsumeChar(','):
				sr.tryConsumeWhitespace()
				continue
		return states
	else:
		return None


def _parseEntityLocator(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[Union[str, TargetSelector]]:
	# Must be a player name, a target selector or a UUID.
	string = sr.tryReadString()
	if string is None:
		# tryParse Target selector:
		string = parseTargetSelector(sr, ai, errorsIO=errorsIO)
	return string


def _parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, allowTag: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	location = sr.tryReadResourceLocation(allowTag=allowTag)
	if location is None:
		return None
	location = ResourceLocation.fromString(location)
	return makeParsedArgument(sr, ai, value=location)


@argumentParser(BRIGADIER_BOOL.name)
def parseBool(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadBoolean()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(BRIGADIER_FLOAT.name)
def parseFloat(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadFloat()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(BRIGADIER_DOUBLE.name)
def parseDouble(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadFloat()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(BRIGADIER_INTEGER.name)
def parseInteger(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadInt()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(BRIGADIER_LONG.name)
def parseLong(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadInt()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(BRIGADIER_STRING.name)
def parseString(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	string = sr.tryReadString()
	if string is None:
		return None
	return makeParsedArgument(sr, ai, value=string)


@argumentParser(MINECRAFT_ANGLE.name)
def parseAngle(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	angle = sr.tryReadTildeNotation()
	if angle is None:
		angle = sr.tryReadFloat()
	if angle is None:
		return None
	return makeParsedArgument(sr, ai, value=angle)


@argumentParser(MINECRAFT_BLOCK_POS.name)
def parseBlockPos(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	useFloat = ai.args is not None and ai.args.get('type', None) is float
	return _parse3dPos(sr, ai, useFloat=useFloat, errorsIO=errorsIO)


@argumentParser(MINECRAFT_BLOCK_PREDICATE.name)
def parseBlockPredicate(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return parseBlockState(sr, ai, errorsIO=errorsIO, allowTag=True)


@argumentParser(MINECRAFT_BLOCK_STATE.name)
def parseBlockState(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError], allowTag: bool = False) -> Optional[ParsedArgument]:
	# block_id[block_states]{data_tags}
	blockID = sr.tryReadResourceLocation(allowTag=allowTag)
	if blockID is None:
		return None
	blockID = ResourceLocation.fromString(blockID)
	# block states:
	states = _parseBlockStates(sr, ai, errorsIO=errorsIO)
	if states is not None:
		sr.mergeLastSave()
	else:
		states = OrderedDict()
	# data tags:
	if sr.tryConsumeChar('{'):
		sr.cursor -= 1
		nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
	else:
		nbt = None
	if nbt is not None:
		sr.mergeLastSave()

	blockPredicate = BlockState.create(blockId=blockID, states=states, nbt=nbt)
	return makeParsedArgument(sr, ai, value=blockPredicate)


@argumentParser(MINECRAFT_COLUMN_POS.name)
def parseColumnPos(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	sr.save()
	columnPos1: Optional[str] = sr.tryReadInt() or sr.tryReadTildeNotation()
	if columnPos1 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeChar(' '):
		sr.rollback()
		return None

	columnPos2: Optional[str] = sr.tryReadInt() or sr.tryReadTildeNotation()
	if columnPos2 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	blockPos = f'{columnPos1} {columnPos2}'
	return makeParsedArgument(sr, ai, value=blockPos)


@argumentParser(MINECRAFT_COMPONENT.name)
def parseComponent(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# TODO: parseComponent(...): Must be a raw JSON text.
	import json
	remainder = sr.tryReadRemaining()
	if remainder is None:
		return None
	try:
		json = json.loads(remainder)
	except JSONDecodeError as e:
		position = sr.posFromColumn(sr.lastCursors.peek() + e.colno)
		end = sr.currentPos
		errorsIO.append(CommandSyntaxError(e.msg, Span(position, end), style='error'))
		return None
	else:
		return makeParsedArgument(sr, ai, value=json)


@argumentParser(MINECRAFT_DIMENSION.name)
def parseDimension(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_ENTITY.name)
def parseEntity(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# Must be a player name, a target selector or a UUID.
	locator = _parseEntityLocator(sr, ai, errorsIO=errorsIO)
	if locator is None:
		return None
	return makeParsedArgument(sr, ai, value=locator)


@argumentParser(MINECRAFT_ENTITY_SUMMON.name)
def parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_FLOAT_RANGE.name)
def parseFloatRange(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	float1Regex = r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)'
	float2Regex = r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
	separatorRegex = r'\.\.'
	pattern = re.compile(f"{float1Regex}(?:{separatorRegex}(?:{float2Regex})?)?|{separatorRegex}{float2Regex}")
	range_ = sr.tryReadRegex(pattern)
	if range_ is None:
		return None
	return makeParsedArgument(sr, ai, value=range_)


@argumentParser(MINECRAFT_FUNCTION.name)
def parseFunction(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, allowTag=True, errorsIO=errorsIO)


@argumentParser(MINECRAFT_GAME_PROFILE.name)
def parseGameProfile(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# TODO: parseGameProfile(...)
	return parseEntity(sr, ai, errorsIO=errorsIO)


@argumentParser(MINECRAFT_INT_RANGE.name)
def parseIntRange(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	intRegex = r'-?[0-9]+'
	separatorRegex = r'\.\.'
	pattern = re.compile(f"{intRegex}(?:{separatorRegex}(?:{intRegex})?)?|{separatorRegex}{intRegex}")
	range_ = sr.tryReadRegex(pattern)
	if range_ is None:
		return None
	return makeParsedArgument(sr, ai, value=range_)


@argumentParser(MINECRAFT_ITEM_ENCHANTMENT.name)
def parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_ITEM_PREDICATE.name)
def parseItemPredicate(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return parseItemStack(sr, ai, errorsIO=errorsIO, allowTag=True)


@argumentParser(MINECRAFT_ITEM_SLOT.name)
def parseItemSlot(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	slot = sr.tryReadRegex(re.compile(r'\w+(?:\.\w+)?'))
	if slot is None:
		return None
	return makeParsedArgument(sr, ai, value=slot)


@argumentParser(MINECRAFT_ITEM_STACK.name)
def parseItemStack(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError], allowTag: bool = False) -> Optional[ParsedArgument]:
	# block_id[block_states]{data_tags}
	itemID = sr.tryReadResourceLocation(allowTag=allowTag)
	if itemID is None:
		return None
	itemStack = itemID

	# data tags:
	if sr.tryConsumeChar('{'):
		sr.cursor -= 1
		nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
	else:
		nbt = None
	if nbt is not None:
		sr.mergeLastSave()
		itemStack = (itemStack, nbt)
	else:
		itemStack = (itemStack, None)
	return makeParsedArgument(sr, ai, value=itemStack)


@argumentParser(MINECRAFT_MESSAGE.name)
def parseMessage(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	message = sr.tryReadRemaining()
	if message is None:
		return None
	return makeParsedArgument(sr, ai, value=message)


@argumentParser(MINECRAFT_MOB_EFFECT.name)
def parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_NBT_COMPOUND_TAG.name)
def parseNbtCompoundTag(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
	if nbt is None:
		return None
	return makeParsedArgument(sr, ai, value=nbt)


@argumentParser(MINECRAFT_NBT_PATH.name)
def parseNbtPath(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	path = parseNBTPath(sr, errorsIO=errorsIO)
	if path is None:
		return None
	return makeParsedArgument(sr, ai, value=path)


@argumentParser(MINECRAFT_NBT_TAG.name)
def parseNbtTag(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	nbt = parseNBTTag(sr, errorsIO=errorsIO)
	if nbt is None:
		return None
	return makeParsedArgument(sr, ai, value=nbt)


@argumentParser(MINECRAFT_OBJECTIVE.name)
def parseObjective(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	pattern = re.compile(r"[a-zA-Z0-9_.+-]{0,16}")
	objective = sr.tryReadRegex(pattern)
	if objective is None:
		return None
	return makeParsedArgument(sr, ai, value=objective)


@argumentParser(MINECRAFT_OBJECTIVE_CRITERIA.name)
def parseObjectiveCriteria(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, allowTag=False, errorsIO=errorsIO)


@argumentParser(MINECRAFT_PARTICLE.name)
def parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_RESOURCE_LOCATION.name)
def parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentParser(MINECRAFT_ROTATION.name)
def parseRotation(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	numberReader = sr.tryReadFloat
	sr.save()
	yaw: Optional[str] = numberReader() or sr.tryReadTildeNotation()
	if yaw is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeChar(' '):
		sr.rollback()
		return None

	pitch: Optional[str] = numberReader() or sr.tryReadTildeNotation()
	if pitch is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	rotation = f'{yaw} {pitch}'
	return makeParsedArgument(sr, ai, value=rotation)


@argumentParser(MINECRAFT_SCORE_HOLDER.name)
def parseScoreHolder(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# Must be a player name, a target selector or a UUID, or *.
	locator = _parseEntityLocator(sr, ai, errorsIO=errorsIO)
	if locator is None:
		sr.save()
		if sr.tryConsumeChar('*'):
			locator = '*'
		else:
			locator = sr.tryReadLiteral()
			if locator is None:
				sr.rollback()
				return None
	return makeParsedArgument(sr, ai, value=locator)


@argumentParser(MINECRAFT_SCOREBOARD_SLOT.name)
def parseScoreboardSlot(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	literal = sr.tryReadLiteral()
	if literal is None:
		return None
	return makeParsedArgument(sr, ai, value=literal)


@argumentParser(MINECRAFT_SWIZZLE.name)
def parseSwizzle(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	swizzle = sr.tryReadLiteral()
	if swizzle is None:
		return None
	if re.fullmatch(r'[xyz]{1,3}', swizzle) is None:
		sr.rollback()
		return None
	if swizzle.count('x') > 1 or swizzle.count('y') > 1 or swizzle.count('z') > 1:
		sr.rollback()
		return None
	return makeParsedArgument(sr, ai, value=swizzle)


@argumentParser(MINECRAFT_TEAM.name)
def parseTeam(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# -, +, ., _, A-Z, a-z, and 0-9
	literal = sr.tryReadRegex(re.compile(r'[-+._A-Za-z0-9]+'))
	if literal is None:
		return None
	return makeParsedArgument(sr, ai, value=literal)


@argumentParser(MINECRAFT_TIME.name)
def parseTime(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	number = sr.tryReadFloat()
	if number is None:
		return None
	unit = sr.tryReadLiteral()
	if unit is None:
		sr.rollback()
		return None

	if unit not in ('d', 's', 't'):
		sr.rollback()
		sr.rollback()
		return None
	sr.mergeLastSave()
	return makeParsedArgument(sr, ai, value=(number, unit))


@argumentParser(MINECRAFT_UUID.name)
def parseUuid(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentParser(MINECRAFT_VEC2.name)
def parseVec2(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parse2dPos(sr, ai, useFloat=True, errorsIO=errorsIO)


@argumentParser(MINECRAFT_VEC3.name)
def parseVec3(sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	return _parse3dPos(sr, ai, useFloat=True, errorsIO=errorsIO)
