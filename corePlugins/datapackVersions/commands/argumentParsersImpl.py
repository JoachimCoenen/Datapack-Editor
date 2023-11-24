from typing import Optional, cast

from base.model.parsing.bytesUtils import ORD_SPACE
from corePlugins.mcFunction.argumentContextsImpl import parseFromStringReader
from corePlugins.mcFunction.command import ArgumentSchema, ParsedArgument
from corePlugins.mcFunction.commandContext import makeParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.nbt import SNBT_ID
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, ResourceLocationNode
from corePlugins.nbt.tags import NBTTag, CompoundTag, NBTTagSchema
from base.model.pathUtils import FilePath
from base.model.utils import GeneralError


def _parseVec(sr: StringReader, ai: ArgumentSchema, *, count: int, useFloat: bool, notation: bytes) -> Optional[ParsedArgument]:
	if useFloat:
		numberReader = sr.tryReadFloat
	else:
		numberReader = sr.tryReadInt
	sr.save()

	vec = [None] * count
	blockPos1: Optional[bytes] = numberReader() or sr.tryReadNotation2(notation)
	if blockPos1 is None:
		sr.rollback()
		return None
	vec[0] = blockPos1

	for i in range(1, count):

		if not sr.tryConsumeByte(ORD_SPACE):
			sr.rollback()
			return None

		blockPos2: Optional[bytes] = numberReader() or sr.tryReadNotation2(notation)
		if blockPos2 is None:
			sr.rollback()
			return None
		vec[i] = blockPos2

	return makeParsedArgument(sr, ai, value=tuple(vec))


def tryReadNBTCompoundTag(sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[NBTTag]:
	tag = cast(NBTTag, parseFromStringReader(
		sr,
		filePath=filePath,
		language=SNBT_ID,
		schema=NBTTagSchema(''),
		errorsIO=errorsIO,
		ignoreTrailingChars=True
	))
	if tag is None:
		return None

	if type(tag) is CompoundTag:
		return tag
	else:
		sr.rollback()
		return None


def _readResourceLocation(sr: StringReader, filePath: FilePath, schema: ResourceLocationSchema, *, errorsIO: list[GeneralError]) -> Optional[ResourceLocationNode]:
	return parseFromStringReader(sr, filePath, schema.language, schema, errorsIO=errorsIO, ignoreTrailingChars=True)
