from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import ModuleType
from typing import ClassVar, Any

from base.model.parsing.bytesUtils import strToBytes
from base.modules import loadAllModules, FolderAndFileFilter
from cat.utils.collections_ import FrozenDict
from .resourceLocation import ResourceLocation


@dataclass
class Gamerule:
	name: str
	description: str
	type: str
	defaultValue: str
	args: None | dict[str, Any | None] = field(default=None)


def buildGamerulesDict(gamerules: list[Gamerule]) -> FrozenDict[bytes, Gamerule]:
	return FrozenDict({strToBytes(gr.name): gr for gr in gamerules})


@dataclass
class CustomMCData:
	name: str

	datapackVersion: str
	fluids: frozenset[ResourceLocation]
	potions: frozenset[ResourceLocation]
	dimensions: frozenset[ResourceLocation]
	predicateConditions: frozenset[ResourceLocation]
	gameEvents: frozenset[ResourceLocation]  # introduced in version 1.19
	structures: frozenset[ResourceLocation]
	pointOfInterestTypes: frozenset[ResourceLocation]
	damageTypes: frozenset[ResourceLocation]
	itemComponents: frozenset[ResourceLocation]
	itemSubPredicates: frozenset[ResourceLocation]

	slots: FrozenDict[bytes, frozenset[bytes | None]]
	gamerules: FrozenDict[bytes, Gamerule]

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
	pointOfInterestTypes=frozenset(),
	damageTypes=frozenset(),
	itemComponents=frozenset(),
	itemSubPredicates=frozenset(),
	slots=FrozenDict(),
	gamerules=FrozenDict(),
)


def _loadAllVersionModules() -> dict[str, ModuleType]:
	versionsDir = os.path.join(
		os.path.dirname(__file__), "versions/"
	)

	modules = loadAllModules(
		'corePlugins.minecraft_data.versions',
		versionsDir,
		[
			# all single-file plugins
			FolderAndFileFilter('/', r'v\d_\d+_\d\.py'),
		],
		initMethodName=None
	)
	return modules


def loadAllVersions() -> None:
	global ALL_SUPPORTED_VERSIONS
	versionModules = _loadAllVersionModules()

	versionsList = [customData for module in versionModules.values() for customData in module.ALL_VERSIONS]
	ALL_SUPPORTED_VERSIONS = {data.name: data for data in versionsList}


ALL_SUPPORTED_VERSIONS: dict[str, CustomMCData] = {}
