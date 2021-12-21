from typing import Optional

from model.commands.argumentHandlers import makeParsedArgument
from model.commands.command import ArgumentInfo
from model.commands.snbt import parseNBTTag
from model.commands.utils import CommandSyntaxError
from model.commands.parsedCommands import ParsedArgument
from model.commands.stringReader import StringReader
from model.Model import ResourceLocation
from model.nbt.tags import NBTTag, CompoundTag


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


def _parseResourceLocation(sr: StringReader, ai: ArgumentInfo, *, allowTag: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	location = sr.tryReadResourceLocation(allowTag=allowTag)
	if location is None:
		return None
	location = ResourceLocation.fromString(location)
	return makeParsedArgument(sr, ai, value=location)
