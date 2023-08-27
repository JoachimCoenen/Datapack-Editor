from __future__ import annotations

from abc import ABC
from copy import copy
from dataclasses import dataclass, Field, fields, is_dataclass
from typing import Optional

from base.model.applicationSettings import getApplicationSettings
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID
from corePlugins.mcFunction.argumentTypes import ArgumentType
from corePlugins.mcFunction.command import MCFunctionSchema
from .filterArgs import FilterArgumentInfo
from corePlugins.minecraft.resourceLocation import ResourceLocation
from base.model.parsing.bytesUtils import strToBytes


@dataclass
class Gamerule:
	name: str
	description: str
	type: ArgumentType
	defaultValue: str


@dataclass
class MCVersion(ABC):
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

	# commands: dict[bytes, CommandSchema]

	@property
	def mcFunctionSchema(self) -> Optional[MCFunctionSchema]:
		return GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID + ' ' + self.name, MCFunctionSchema)

	def getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		arguments = self.blockStates.get(blockID)
		if arguments is None:
			return {}
		else:
			return {strToBytes(argument.name): argument for argument in arguments}

	def activate(self) -> None:
		schema = self.mcFunctionSchema
		if schema is not None:
			GLOBAL_SCHEMA_STORE.registerSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, schema)

	def deactivate(self) -> None:
		schema = self.mcFunctionSchema
		if schema is not None:
			if GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema) is schema:
				GLOBAL_SCHEMA_STORE.unregisterSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema.language)


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


def getCurrentMCVersion() -> Optional[MCVersion]:
	"""Returns the MCVersion currently selected in settings."""
	from .settings import MinecraftSettings
	version = getApplicationSettings().aspects.get(MinecraftSettings).minecraftVersion
	return getMCVersion(version)


# def activateMCVersion(name: str) -> None:
# 	GLOBAL_SCHEMA_STORE.registerSchema('Minecraft 1.17', schema_1_17)

