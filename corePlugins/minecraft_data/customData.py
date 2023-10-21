from __future__ import annotations
import os
from dataclasses import dataclass
from types import ModuleType
from typing import Mapping, ClassVar, Sequence

from cat.utils.collections_ import FrozenDict
from base.modules import loadAllModules, FolderAndFileFilter
from .resourceLocation import ResourceLocation


@dataclass
class Gamerule:
	name: str
	description: str
	type: str
	defaultValue: str


@dataclass
class CustomMCData:
	name: str

	datapackVersion: str
	fluids: AbstractSet[ResourceLocation]
	potions: AbstractSet[ResourceLocation]
	dimensions: AbstractSet[ResourceLocation]
	predicateConditions: AbstractSet[ResourceLocation]
	gameEvents: AbstractSet[ResourceLocation]  # introduced in version 1.19
	structures: AbstractSet[ResourceLocation]

	slots: Mapping[bytes, int]
	gamerules: Sequence[Gamerule]

	EMPTY: ClassVar[CustomMCData]


CustomMCData.EMPTY = CustomMCData(
	name='EMPTY',
	datapackVersion='-1',
	fluids=frozenset(),
	potions=frozenset(),
	dimensions=frozenset(),
	predicateConditions=frozenset(),
	gameEvents=frozenset(),
	structures=frozenset(),
	slots=FrozenDict(),
	gamerules=(),
)


def _loadAllVersions() -> dict[str, ModuleType]:
	versionsDir = os.path.join(
		os.path.dirname(__file__), "versions/"
	)

	modules = loadAllModules(
		'minecraft_data.versions',
		versionsDir,
		[
			# all single-file plugins
			FolderAndFileFilter('/', r'v\d_\d+_\d\.py'),
		],
		initMethodName=None
	)
	return modules


def createCustomDatas(module: ModuleType) -> list[CustomMCData]:
	try:
		names = module.NAMES
	except AttributeError:
		names = module.NAME

	if isinstance(names, str):
		names = [names]

	return [
		CustomMCData(
			name=name,
			datapackVersion=module.DATAPACK_VERSION,
			fluids=module.FLUIDS,
			potions=module.POTIONS,
			dimensions=module.DIMENSIONS,
			predicateConditions=module.PREDICATE_CONDITIONS,
			gameEvents=module.GAME_EVENTS,
			structures=module.STRUCTURES,
			slots=module.SLOTS,
			gamerules=module.GAMERULES,
		)
		for name in names
	]


def loadAllVersions() -> dict[str, CustomMCData]:
	versionModules = _loadAllVersions()
	versionsList = [customData for module in versionModules.values() for customData in createCustomDatas(module)]
	versionsDict = {data.name: data for data in versionsList}
	return versionsDict


ALL_SUPPORTED_VERSIONS = loadAllVersions()
