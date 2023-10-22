from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass, replace
from typing import AbstractSet, Mapping, ClassVar, Optional, Any

from base.model.pathUtils import normalizeDirSeparatorsStr
from cat.utils.logging_ import logWarning, logError, loggingIndentInfo

from cat.utils.collections_ import FrozenDict
from base.model.utils import MDStr
from .resourceLocation import ResourceLocation


_MINECRAFT_DATA_REL_PATH: str = 'data/data/'
_FILE_ABS_PATH: str = normalizeDirSeparatorsStr(os.path.dirname(__file__)).removesuffix('/') + '/'
_MINECRAFT_DATA_ABS_PATH: str = f'{_FILE_ABS_PATH}{_MINECRAFT_DATA_REL_PATH}'


@dataclass
class BlockStateType:
	name: str
	description: MDStr
	type: str
	values: list[str]
	range: Optional[tuple[int, int]]


@dataclass
class MCData:
	name: str

	blocks: AbstractSet[ResourceLocation]
	items: AbstractSet[ResourceLocation]
	entities: AbstractSet[ResourceLocation]
	effects: AbstractSet[ResourceLocation]
	enchantments: AbstractSet[ResourceLocation]
	biomes: AbstractSet[ResourceLocation]
	particles: AbstractSet[ResourceLocation]
	instruments: AbstractSet[ResourceLocation]

	blockStates: Mapping[ResourceLocation, list[BlockStateType]]

	EMPTY: ClassVar[MCData]


MCData.EMPTY = MCData(
	name='EMPTY',
	blocks=frozenset(),
	items=frozenset(),
	entities=frozenset(),
	effects=frozenset(),
	enchantments=frozenset(),
	biomes=frozenset(),
	particles=frozenset(),
	instruments=frozenset(),
	blockStates=FrozenDict(),
)


def fillFromVersion(version: str) -> Optional[MCData]:
	with loggingIndentInfo(f"Loading data for Minecraft version '{version}'."):
		minecraftData = _loadRawDataForVersion(version)
		return minecraftData and _getMinecraftDataFromRaw(version, minecraftData)


def _getMinecraftDataFromRaw(version: str, mcd: dict[str, Any]) -> MCData:
	EMPTY_LIST = []
	data = MCData(
		name=version,
		blocks=rlsFromData(mcd.get('blocks', EMPTY_LIST)),
		items=rlsFromData([dict(name='air')], mcd.get('items', EMPTY_LIST)),  # put air default first, so that, if mcd contains an entry for air, it will overwrite our default.
		entities=rlsFromData(mcd.get('entities', EMPTY_LIST)),
		effects=fixCapitalizations(rlsFromData(mcd.get('effects', EMPTY_LIST))),
		enchantments=rlsFromData(mcd.get('enchantments', EMPTY_LIST)),
		biomes=rlsFromData(mcd.get('biomes', EMPTY_LIST)),
		particles=rlsFromData(mcd.get('particles', EMPTY_LIST)),
		instruments=rlsFromData(mcd.get('instruments', EMPTY_LIST)),
		blockStates=rlsBlockStatesFromData(mcd.get('blocks', EMPTY_LIST)),
	)
	return data


def rlsFromData(*mcdLists: list[dict]) -> set[ResourceLocation]:
	# return {ResourceLocation.fromString(f"minecraft:{d['name']}") for mcdList in mcdLists for d in mcdList}
	return {
		ResourceLocation.fromString(d['name'])
		for mcdList in mcdLists
		for d in mcdList
	}


def rlsBlockStatesFromData(*mcdLists: list[dict]) -> dict[ResourceLocation, list[BlockStateType]]:
	EMPTY_LIST = []
	return {
		ResourceLocation.fromString(block['name']): buildBlockStates(block.get('states', EMPTY_LIST))
		for mcdList in mcdLists
		for block in mcdList
	}


def fixCapitalization(origResLoc: ResourceLocation) -> ResourceLocation:
	fixedPath = '_'.join(re.compile(r'\w[a-z]+').findall(origResLoc.path)).lower()
	return replace(origResLoc, path=fixedPath)


def fixCapitalizations(origResLocs: set[ResourceLocation]) -> set[ResourceLocation]:
	return {fixCapitalization(rl) for rl in origResLocs}


def buildBlockStates(states: list[dict]) -> list[BlockStateType]:
	return [buildBlockState(state) for state in states]


_BLOCK_STATE_TYPE_MAPPING = {
	'int': 'brigadier:integer',
	'bool': 'brigadier:bool',
	'enum': 'brigadier:string',
}


def buildBlockState(state: dict) -> BlockStateType:
	bs = BlockStateType(
		name=(state['name']),
		description=MDStr(""),
		type=_BLOCK_STATE_TYPE_MAPPING[state['type']],
		values=(state.get('values', [])),
		range=((0, state['num_values']) if state['type'] == 'int' else None)
	)
	return bs


def getMCDataForVersion(version: str) -> Optional[MCData]:
	if version not in _ALL_LOADED_VERSIONS:
		_ALL_LOADED_VERSIONS[version] = fillFromVersion(version)
	return _ALL_LOADED_VERSIONS[version]


_ALL_LOADED_VERSIONS: dict[str, Optional[MCData]] = {}


def _getAllDataPaths() -> dict[str, dict[str, dict[str, str]]]:
	global _ALL_DATA_PATHS
	if _ALL_DATA_PATHS is None:
		dataPathsPath = os.path.join(_MINECRAFT_DATA_ABS_PATH, 'dataPaths.json')
		with open(dataPathsPath, encoding='utf-8') as f:
			_ALL_DATA_PATHS = json.load(f)
	return _ALL_DATA_PATHS


_ALL_DATA_PATHS = None


def _getDataPaths(version: str) -> Optional[dict[str, str]]:
	allDataPaths = _getAllDataPaths()
	result = allDataPaths['pc'].get(version)
	if not isinstance(result, (dict, type(None))):
		logError(f"while loading data for Minecraft version '{version}'.")
	return result


def _loadRawDataForVersion(version: str) -> Optional[dict[str, Any]]:
	dataPaths = _getDataPaths(version)
	if dataPaths is None:
		return None
	return _loadRawData(dataPaths, version)


def _loadRawData(dataPaths: dict[str, str], version: str) -> dict[str, Any]:
	data = {}
	for filename, folder in dataPaths.items():
		path = os.path.join(_MINECRAFT_DATA_ABS_PATH, folder, f'{filename}.json')
		try:
			with open(path, encoding='utf-8') as fp:
				data[filename] = json.load(fp)
		except OSError as ex:
			logWarning(ex, f"while loading data for Minecraft version '{version}'.")
	return data