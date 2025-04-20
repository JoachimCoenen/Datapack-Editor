from typing import Optional, cast

from base.model.parsing.bytesUtils import ORD_SPACE
from corePlugins.datapackVersions import PREDICATE_ARGS_ID
from corePlugins.datapackVersions.commands.predicateArgs import PredicateArgOptions, PredicateArgs
from corePlugins.mcFunction.argumentContextsImpl import parseFromStringReader
from corePlugins.mcFunction.command import ArgumentSchema, ParsedArgument
from corePlugins.mcFunction.commandContext import makeParsedArgument
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.nbt import SNBT_ID
from corePlugins.minecraft.resourceLocation import ResourceLocationSchema, ResourceLocationNode
from base.model.pathUtils import FilePath
from base.model.utils import GeneralError
from corePlugins.nbtJsonBase.core import StructureDataSchema, StructureNode, ObjectNode


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
	sr.mergeLastSave()

	for i in range(1, count):

		if not sr.tryConsumeByte(ORD_SPACE):
			sr.rollback()
			return None

		blockPos2: Optional[bytes] = numberReader() or sr.tryReadNotation2(notation)
		if blockPos2 is None:
			sr.rollback()
			return None
		vec[i] = blockPos2
		sr.mergeLastSave()

	return makeParsedArgument(sr, ai, value=tuple(vec))


def tryReadNBTTag(sr: StringReader, schema: StructureDataSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[StructureNode]:
	return cast(StructureNode, parseFromStringReader(
		sr,
		filePath=filePath,
		language=SNBT_ID,
		schema=schema,
		errorsIO=errorsIO,
		ignoreTrailingChars=True
	))


def tryReadNBTCompoundTag(sr: StringReader, schema: StructureDataSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[StructureNode]:
	tag = tryReadNBTTag(sr, schema, filePath, errorsIO=errorsIO)
	if tag is None:
		return None

	if isinstance(tag, ObjectNode):
		return tag
	else:
		sr.rollback()
		return None


def readPredicateArgs(sr: StringReader, schema: PredicateArgOptions, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[PredicateArgs]:
	return cast(PredicateArgs, parseFromStringReader(
		sr,
		filePath=filePath,
		language=PREDICATE_ARGS_ID,
		schema=schema,
		errorsIO=errorsIO,
	))


def _readResourceLocation(sr: StringReader, filePath: FilePath, schema: ResourceLocationSchema, *, errorsIO: list[GeneralError]) -> Optional[ResourceLocationNode]:
	return parseFromStringReader(sr, filePath, schema.language, schema, errorsIO=errorsIO, ignoreTrailingChars=True)
