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
# from model.resourceLocationContext import getResourceLocationContext
from base.model.utils import Position


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


def _parseResourceLocation(sr: StringReader, ai: ArgumentSchema, schema: ResourceLocationSchema) -> Optional[ParsedArgument]:
	# todo: rlc = getResourceLocationContext(schema.name)
	# allowTag = rlc.allowTags
	allowTag = True  # = rlc.allowTags
	location = sr.readResourceLocation(allowTag=allowTag)
	location = ResourceLocationNode.fromString(location, sr.currentSpan, schema)
	return makeParsedArgument(sr, ai, value=location)
