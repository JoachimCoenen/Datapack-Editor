from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Optional, ClassVar

from cat.utils.collections_ import FrozenDict
from .customData import CustomMCData, Gamerule
from .mcdAdapter import MCData, BlockStateType
from .resourceLocation import ResourceLocation


@dataclass
class FullMCData:
	name: str

	datapackVersion: str
	blocks: frozenset[ResourceLocation]
	fluids: frozenset[ResourceLocation]
	items: frozenset[ResourceLocation]

	entities: frozenset[ResourceLocation]
	potions: frozenset[ResourceLocation]
	effects: frozenset[ResourceLocation]
	enchantments: frozenset[ResourceLocation]
	biomes: frozenset[ResourceLocation]
	particles: frozenset[ResourceLocation]
	dimensions: frozenset[ResourceLocation]
	predicateConditions: frozenset[ResourceLocation]
	gameEvents: frozenset[ResourceLocation]  # introduced in version 1.19
	instruments: frozenset[ResourceLocation]
	structures: frozenset[ResourceLocation]
	pointOfInterestTypes: frozenset[ResourceLocation]
	damageTypes: frozenset[ResourceLocation]

	slots: FrozenDict[bytes, Optional[int]]
	blockStates: FrozenDict[ResourceLocation, list[BlockStateType]]
	gamerules: FrozenDict[bytes, Gamerule]

	def getBlockStates(self, blockID: ResourceLocation) -> list[BlockStateType]:
		arguments = self.blockStates.get(blockID)
		if arguments is None:
			return []
		else:
			return arguments

	def activate(self) -> None:
		global _CURRENT_MC_VERSION
		_CURRENT_MC_VERSION = self

	def deactivate(self) -> None:
		global _CURRENT_MC_VERSION
		if _CURRENT_MC_VERSION is self:
			_CURRENT_MC_VERSION = FullMCData.EMPTY

	EMPTY: ClassVar[FullMCData]


def buildFullMCData(name: str, mcData: Optional[MCData], cuData: Optional[CustomMCData]) -> FullMCData:
	mcData = mcData or MCData.EMPTY
	cuData = cuData or CustomMCData.EMPTY
	return FullMCData(
		name=name,
		datapackVersion=cuData.datapackVersion,
		blocks=mcData.blocks,
		fluids=cuData.fluids,
		items=mcData.items,
		entities=mcData.entities,
		potions=cuData.potions,
		effects=mcData.effects,
		enchantments=mcData.enchantments,
		biomes=mcData.biomes,
		particles=mcData.particles,
		dimensions=cuData.dimensions,
		predicateConditions=cuData.predicateConditions,
		gameEvents=cuData.gameEvents,
		instruments=mcData.instruments,
		structures=cuData.structures,
		pointOfInterestTypes=cuData.pointOfInterestTypes,
		damageTypes=cuData.damageTypes,
		slots=cuData.slots,
		blockStates=mcData.blockStates,
		gamerules=cuData.gamerules,
	)


FullMCData.EMPTY = buildFullMCData('EMPTY', MCData.EMPTY, CustomMCData.EMPTY)


def loadAllVersionsFullMcData() -> list[FullMCData]:
	from .customData import loadAllVersions as loadAllCustomDataVersions
	loadAllCustomDataVersions()
	from .customData import ALL_SUPPORTED_VERSIONS as CUSTOM_DATA_VERSIONS
	from .mcdAdapter import getMCDataForVersion
	allVersionNames = sorted(CUSTOM_DATA_VERSIONS.keys())

	return [
		buildFullMCData(name, getMCDataForVersion(name), CUSTOM_DATA_VERSIONS.get(name))
		for name in allVersionNames
	]


_ALL_MC_VERSIONS: dict[str, FullMCData] = {}

_CURRENT_MC_VERSION: FullMCData = FullMCData.EMPTY


def registerFullMcData(version: FullMCData) -> None:
	_ALL_MC_VERSIONS[version.name] = version


def getFullMcData(name: str) -> FullMCData:
	return _ALL_MC_VERSIONS.get(name, FullMCData.EMPTY)


def getAllFullMcDatas() -> Mapping[str, FullMCData]:
	return _ALL_MC_VERSIONS


def getCurrentFullMcData() -> FullMCData:
	return _CURRENT_MC_VERSION
