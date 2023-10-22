"""
for Minecraft version 1.17
"""
from typing import AbstractSet, Mapping, Optional

from corePlugins.minecraft_data.resourceLocation import ResourceLocation

from . import v1_20_0

NAMES: list[str] = ['1.20.2']


DATAPACK_VERSION: str = '18'


# compiled from the Minecraft wiki:
FLUIDS: AbstractSet[ResourceLocation] = v1_20_0.FLUIDS


# compiled from the Minecraft wiki:
POTIONS: AbstractSet[ResourceLocation] = v1_20_0.POTIONS


# compiled from the Minecraft wiki:
DIMENSIONS: AbstractSet[ResourceLocation] = v1_20_0.DIMENSIONS


# compiled from the Minecraft wiki:
PREDICATE_CONDITIONS: AbstractSet[ResourceLocation] = v1_20_0.PREDICATE_CONDITIONS


# compiled from the 1.20.2.jar using this command "javap -constants -c  djt.class":
GAME_EVENTS: AbstractSet[ResourceLocation] = v1_20_0.GAME_EVENTS


# compiled from the 1.20.2.jar using this command "javap -constants -c  dvc.class":
STRUCTURES: AbstractSet[ResourceLocation] = v1_20_0.STRUCTURES


# compiled from the Minecraft wiki:
SLOTS: Mapping[bytes, Optional[int]] = v1_20_0.SLOTS


GAMERULES = v1_20_0.GAMERULES
