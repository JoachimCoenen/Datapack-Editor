"""
for Minecraft version 1.18
"""
from typing import AbstractSet, Mapping

from corePlugins.minecraft_data.customData import Gamerule
from corePlugins.minecraft_data.resourceLocation import ResourceLocation

from . import v1_17_0

NAMES: list[str] = ['1.18', '1.18.1']


DATAPACK_VERSION: str = '8'


# compiled from the Minecraft wiki:
FLUIDS: AbstractSet[ResourceLocation] = v1_17_0.FLUIDS


# compiled from the Minecraft wiki:
POTIONS: AbstractSet[ResourceLocation] = v1_17_0.POTIONS


# compiled from the Minecraft wiki:
DIMENSIONS: AbstractSet[ResourceLocation] = v1_17_0.DIMENSIONS


# compiled from the Minecraft wiki:
PREDICATE_CONDITIONS: AbstractSet[ResourceLocation] = v1_17_0.PREDICATE_CONDITIONS


# compiled from the Minecraft wiki:
GAME_EVENTS: AbstractSet[ResourceLocation] = v1_17_0.GAME_EVENTS  # only added in 1.19, so there's nothing here in 1.18


# compiled from the Minecraft wiki:
STRUCTURES: AbstractSet[ResourceLocation] = v1_17_0.STRUCTURES

# compiled from the Minecraft wiki:
SLOTS: Mapping[bytes, int] = v1_17_0.SLOTS

GAMERULES: list[Gamerule] = v1_17_0.GAMERULES
