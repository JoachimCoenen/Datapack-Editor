from typing import Optional

from model.commands.argumentValues import FilterArguments
from model.commands.filterArgs import parseFilterArgs, FilterArgumentInfo
from model.commands.generatedBlockStates import BLOCK_STATES_BY_BLOCK
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.datapackContents import ResourceLocation


BLOCK_STATES_DICT_BY_BLOCK: dict[ResourceLocation, dict[str, FilterArgumentInfo]] = {
	block: {
		fai.name: fai
		for fai in fais
	}
	for block, fais in BLOCK_STATES_BY_BLOCK.items()
}


def getBlockStatesDict(blockID: ResourceLocation) -> dict:
	arguments = BLOCK_STATES_DICT_BY_BLOCK.get(blockID)
	if arguments is None:
		arguments = {}
	return arguments


def parseBlockStates(sr: StringReader, blockID: ResourceLocation, *, errorsIO: list[CommandSyntaxError]) -> Optional[FilterArguments]:
	arguments = getBlockStatesDict(blockID)
	return parseFilterArgs(sr, arguments, errorsIO=errorsIO)
