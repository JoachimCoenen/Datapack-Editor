"""
for Minecraft version 1.18
"""
from dataclasses import replace
from corePlugins.minecraft_data.customData import CustomMCData
from . import v1_17_0


_VERSION_1_17_X = v1_17_0.ALL_VERSIONS[-1]


_VERSION_1_18_0 = replace(_VERSION_1_17_X, name='1.18', datapackVersion='8')
_VERSION_1_18_1 = replace(_VERSION_1_18_0, name='1.18.1')


ALL_VERSIONS: list[CustomMCData] = [_VERSION_1_18_0, _VERSION_1_18_1]
