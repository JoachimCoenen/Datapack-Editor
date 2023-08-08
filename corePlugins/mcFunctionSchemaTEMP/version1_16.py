from corePlugins.mcFunctionSchemaTEMP.mcVersions import MCVersion, registerMCVersion, getMCVersion, newVersionFrom
from corePlugins.mcFunctionSchemaTEMP.mcd import fillFromMinecraftData
from corePlugins.minecraft.resourceLocation import ResourceLocation


def initPlugin() -> None:
	version1_16, version1_15 = buildVersions()
	registerMCVersion(version1_16)
	registerMCVersion(version1_15)


def buildVersions() -> tuple[MCVersion, MCVersion]:
	# def fillCommandsFor1_16(version: MCVersion) -> None:
	# 	fillCommandsFor1_17(version)
	#
	# def fillCommandsFor1_15(version: MCVersion) -> None:
	# 	fillCommandsFor1_16(version)

	version1_16: MCVersion = newVersionFrom(getMCVersion('1.17'), name='1.16')

	version1_16.particles -= {
		ResourceLocation.fromString('light'),
	}

	# fillCommandsFor1_16(version1_16)
	fillFromMinecraftData(version1_16)


	version1_15: MCVersion = newVersionFrom(version1_16, name='1.15')

	# fillCommandsFor1_15(version1_15)
	fillFromMinecraftData(version1_15)

	return version1_16, version1_15
