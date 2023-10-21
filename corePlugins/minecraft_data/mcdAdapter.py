from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass, replace
from typing import AbstractSet, Mapping, ClassVar, Optional

import minecraft_data

from cat.utils.collections_ import FrozenDict
from base.model.utils import MDStr
from .resourceLocation import ResourceLocation


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


def fillFromMinecraftData(version: str) -> MCData:
	EMPTY_LIST = []
	mcd = minecraft_data(version)
	data = MCData(
		name=version,
		blocks=rlsFromData(mcd.blocks_list) if hasattr(mcd, 'blocks_list') else set(),
		items=rlsFromData(mcd.items_list, [dict(name='air')]) if hasattr(mcd, 'items_list') else set(),
		entities=rlsFromData(mcd.entities_list) if hasattr(mcd, 'entities_list') else set(),
		effects=fixCapitalizations(rlsFromData(mcd.effects_list)) if hasattr(mcd, 'effects_list') else set(),
		enchantments=rlsFromData(mcd.enchantments_list) if hasattr(mcd, 'enchantments_list') else set(),
		biomes=rlsFromData(mcd.biomes_list) if hasattr(mcd, 'biomes_list') else set(),
		particles=rlsFromData(mcd.particles_list) if hasattr(mcd, 'particles_list') else set(),
		instruments=rlsFromData(mcd.instruments_list) if hasattr(mcd, 'instruments_list') else set(),
		blockStates={ResourceLocation.fromString(block['name']): buildBlockStates(block.get('states', EMPTY_LIST)) for block in mcd.blocks_list} if hasattr(mcd, 'blocks_list') else {},

	)
	return data


def rlsFromData(*mcdLists: list[dict]) -> set[ResourceLocation]:
	return {ResourceLocation.fromString(f"minecraft:{d['name']}") for mcdList in mcdLists for d in mcdList}


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


def _getAllVersions() -> list[str]:
	_dir = os.path.join(
		os.path.dirname(minecraft_data.__file__), "data/data/"
	)
	with open(os.path.join(_dir, 'dataPaths.json')) as f:
		dataPaths = json.load(f)
	edition = 'pc'
	return [name for name in dataPaths[edition].keys() if name not in FORBIDDEN_VERSIONS]


FORBIDDEN_VERSIONS = {
	'2.0',
}


def loadAllMcDataVersions() -> list[MCData]:
	versionNames = _getAllVersions()
	versions = [fillFromMinecraftData(name) for name in versionNames]
	return versions


def loadAllVersions() -> dict[str, MCData]:
	versionNames = _getAllVersions()
	versionsDict = {name: fillFromMinecraftData(name) for name in versionNames}
	return versionsDict


ALL_SUPPORTED_VERSIONS = loadAllVersions()
