from typing import Optional

from corePlugins.mcFunction.command import ArgumentSchema
from corePlugins.mcFunction.commandContext import makeParsedArgument
from corePlugins.mcFunction.utils import CommandSyntaxError
from corePlugins.mcFunction.command import ParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, ResourceLocationNode
from corePlugins.nbt.tags import NBTTag, CompoundTag
from .snbt import parseNBTTag
from base.model.parsing.contextProvider import Suggestions
from base.model.pathUtils import FilePath
from base.model.utils import Position
from ..mcFunction.argumentContextsImpl import parseFromStringReader


def _parse2dPos(sr: StringReader, ai: ArgumentSchema, *, useFloat: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	if useFloat:
		numberReader = sr.tryReadFloat
	else:
		numberReader = sr.tryReadInt
	sr.save()
	blockPos1: Optional[bytes] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos1 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeByte(ord(' ')):
		sr.rollback()
		return None

	blockPos2: Optional[bytes] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos2 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	blockPos = (blockPos1, blockPos2)
	return makeParsedArgument(sr, ai, value=blockPos)


def _get2dPosSuggestions(ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str, *, useFloat: bool) -> Suggestions:
	return ['~ ~', '0 0']


def _parse3dPos(sr: StringReader, ai: ArgumentSchema, *, useFloat: bool, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	if useFloat:
		numberReader = sr.tryReadFloat
	else:
		numberReader = sr.tryReadInt
	sr.save()
	blockPos1: Optional[bytes] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos1 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeByte(ord(' ')):
		sr.rollback()
		return None

	blockPos2: Optional[bytes] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos2 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()
	if not sr.tryConsumeByte(ord(' ')):
		sr.rollback()
		return None

	blockPos3: Optional[bytes] = numberReader() or sr.tryReadTildeNotation() or sr.tryReadCaretNotation()
	if blockPos3 is None:
		sr.rollback()
		return None
	sr.mergeLastSave()

	blockPos = (blockPos1, blockPos2, blockPos3)
	return makeParsedArgument(sr, ai, value=blockPos)


def _get3dPosSuggestions(ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str, *, useFloat: bool) -> Suggestions:
	return ['~ ~ ~', '^ ^ ^', '0 0 0']


def tryReadNBTCompoundTag(sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[NBTTag]:
	tag = parseNBTTag(sr, filePath, errorsIO=errorsIO)
	if tag is None:
		return None

	if type(tag) is CompoundTag:
		return tag
	else:
		sr.rollback()
		return None


def _readResourceLocation(sr: StringReader, filePath: FilePath, schema: ResourceLocationSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ResourceLocationNode]:
	return parseFromStringReader(sr, filePath, schema.language, schema, errorsIO=errorsIO, ignoreTrailingChars=True)


def _parseResourceLocation(sr: StringReader, filePath: FilePath, ai: ArgumentSchema, schema: ResourceLocationSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	location = _readResourceLocation(sr, filePath, schema, errorsIO=errorsIO)
	return makeParsedArgument(sr, ai, value=location)
