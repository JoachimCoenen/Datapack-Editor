from __future__ import annotations
from dataclasses import dataclass
from typing import AbstractSet, Mapping, Optional, ClassVar, Sequence

from .customData import CustomMCData, Gamerule
from .mcdAdapter import MCData, BlockStateType
from .resourceLocation import ResourceLocation


@dataclass
class FullMCData:
	name: str

	datapackVersion: str
	blocks: AbstractSet[ResourceLocation]
	fluids: AbstractSet[ResourceLocation]
	items: AbstractSet[ResourceLocation]

	entities: AbstractSet[ResourceLocation]
	potions: AbstractSet[ResourceLocation]
	effects: AbstractSet[ResourceLocation]
	enchantments: AbstractSet[ResourceLocation]
	biomes: AbstractSet[ResourceLocation]
	particles: AbstractSet[ResourceLocation]
	dimensions: AbstractSet[ResourceLocation]
	predicateConditions: AbstractSet[ResourceLocation]
	gameEvents: AbstractSet[ResourceLocation]  # introduced in version 1.19
	instruments: AbstractSet[ResourceLocation]
	structures: AbstractSet[ResourceLocation]

	slots: Mapping[bytes, Optional[int]]
	blockStates: Mapping[ResourceLocation, list[BlockStateType]]
	gamerules: Sequence[Gamerule]

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
		slots=cuData.slots,
		blockStates=mcData.blockStates,
		gamerules=cuData.gamerules,
	)


FullMCData.EMPTY = buildFullMCData('EMPTY', MCData.EMPTY, CustomMCData.EMPTY)


def loadAllVersionsFullMcData() -> list[FullMCData]:
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
