from __future__ import annotations

from copy import copy
from dataclasses import dataclass, Field, fields, is_dataclass
from typing import Optional

from model.commands.command import CommandInfo
from model.commands.filterArgs import FilterArgumentInfo
from model.data.gamerules import Gamerule
from model.datapackContents import ResourceLocation


@dataclass
class Entities:

	mobs: set[ResourceLocation]
	misc: set[ResourceLocation]
	projectiles: set[ResourceLocation]
	vehicles: set[ResourceLocation]
	blocks: set[ResourceLocation]
	items: set[ResourceLocation]

	@property
	def all(self) -> set[ResourceLocation]:
		return {
			*self.mobs,
			*self.misc,
			*self.projectiles,
			*self.vehicles,
			*self.blocks,
			*self.items,
		}


@dataclass
class MCVersion:
	name: str

	blocks: set[ResourceLocation]
	fluids: set[ResourceLocation]
	items: set[ResourceLocation]

	entities: set[ResourceLocation]

	effects: set[ResourceLocation]
	enchantments: set[ResourceLocation]
	biomes: set[ResourceLocation]
	particles: set[ResourceLocation]
	dimensions: set[ResourceLocation]
	structures: set[str]
	slots: dict[str, int]

	blockStates: dict[ResourceLocation, list[FilterArgumentInfo]]
	gamerules: list[Gamerule]

	commands: dict[str, CommandInfo]


def _copyRecursive(data):
	newData = copy(data)
	field: Field
	for field in fields(data):
		value = getattr(data, field.name)
		if is_dataclass(field.type):
			value = _copyRecursive(value)
		else:
			value = copy(value)
		setattr(newData, field.name, value)
	return newData


def newVersionFrom(version: MCVersion, *, name: str) -> MCVersion:
	newVersion = _copyRecursive(version)
	newVersion.name = name
	return newVersion


ALL_MC_VERSIONS: dict[str, MCVersion] = {}


def registerMCVersion(version: MCVersion, forceOverwrite: bool = False) -> None:
	ALL_MC_VERSIONS[version.name] = version


def getMCVersion(name: str) -> Optional[MCVersion]:
	return ALL_MC_VERSIONS.get(name)
