from __future__ import annotations

from abc import ABC
from copy import copy
from dataclasses import dataclass, Field, fields, is_dataclass
from types import MappingProxyType
from typing import Optional, Mapping, Sequence

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

	structures: AbstractSet[ResourceLocation]
	slots: Mapping[bytes, int]

	blockStates: Mapping[ResourceLocation, list[FilterArgumentInfo]]
	gamerules: Sequence[Gamerule]

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


MC_EMPTY_VERSION = MCVersion(
	name='No Version',
	blocks=frozenset(),
	fluids=frozenset(),
	items=frozenset(),

	entities=frozenset(),
	# Entities(
	# 	mobs=ENTITIES_MOBS,
	# 	misc=ENTITIES_MISC,
	# 	projectiles=ENTITIES_PROJECTILES,
	# 	vehicles=ENTITIES_VEHICLES,
	# 	blocks=ENTITIES_BLOCKS,
	# 	items=ENTITIES_ITEMS,
	# ),
	potions=frozenset(),
	effects=frozenset(),
	enchantments=frozenset(),
	biomes=frozenset(),
	particles=frozenset(),
	dimensions=frozenset(),
	structures=frozenset(),
	predicateConditions=frozenset(),
	gameEvents=frozenset(),  # introduced in version 1.19

	slots=MappingProxyType({}),

	blockStates=MappingProxyType({}),
	gamerules=(),

	# commands={},
)


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
	from .settings import MinecraftSettingsTemp
	version = getApplicationSettings().aspects.get(MinecraftSettingsTemp).minecraftVersion
	return getMCVersion(version)


# def activateMCVersion(name: str) -> None:
# 	GLOBAL_SCHEMA_STORE.registerSchema('Minecraft 1.17', schema_1_17)

