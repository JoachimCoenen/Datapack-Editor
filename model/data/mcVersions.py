from __future__ import annotations

from copy import copy
from dataclasses import dataclass, Field, fields, is_dataclass
from typing import Optional

from model.commands.argumentTypes import ArgumentType
from model.commands.command import CommandSchema
from model.commands.filterArgs import FilterArgumentInfo
from model.datapack.datapackContents import ResourceLocation
from model.parsing.bytesUtils import strToBytes


@dataclass
class Gamerule:
	name: str
	description: str
	type: ArgumentType
	defaultValue: str


@dataclass
class MCVersion:
	name: str

	blocks: set[ResourceLocation]
	fluids: set[ResourceLocation]
	items: set[ResourceLocation]

	entities: set[ResourceLocation]
	potions: set[ResourceLocation]
	effects: set[ResourceLocation]
	enchantments: set[ResourceLocation]
	biomes: set[ResourceLocation]
	particles: set[ResourceLocation]
	dimensions: set[ResourceLocation]
	predicateConditions: set[ResourceLocation]
	gameEvents: set[ResourceLocation]  # introduced in version 1.19

	structures: set[ResourceLocation]
	slots: dict[bytes, int]

	blockStates: dict[ResourceLocation, list[FilterArgumentInfo]]
	gamerules: list[Gamerule]

	commands: dict[bytes, CommandSchema]

	def getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		arguments = self.blockStates.get(blockID)
		if arguments is None:
			return {}
		else:
			return {strToBytes(argument.name): argument for argument in arguments}


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
