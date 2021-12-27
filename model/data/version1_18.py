from dataclasses import replace

from model.commands.command import Keyword
from model.data.mcVersions import MCVersion, registerMCVersion, getMCVersion, newVersionFrom
from model.data.mcd import fillFromMinecraftData
from model.data.v1_17.commands import fillCommandsFor1_17
from model.datapackContents import ResourceLocation


def initPlugin() -> None:
	registerMCVersion(version1_18)


def fillCommandsFor1_18(version: MCVersion) -> None:
	fillCommandsFor1_17(version)

	# add 'block_marker' particle:
	particles = version.commands['particle'].next
	block_marker = replace(next(p for p in particles if p.name == 'block' and isinstance(p, Keyword)), name='block_marker')
	version.commands['particle'].next.insert(-1, block_marker)


version1_18: MCVersion = newVersionFrom(getMCVersion('1.17'), name='1.18')

version1_18.items.add(ResourceLocation.fromString('music_disc_otherside'))

version1_18.particles -= {
	ResourceLocation.fromString('light'),
	ResourceLocation.fromString('barrier'),
}
version1_18.particles |= {
	ResourceLocation.fromString('block_marker')
}

version1_18.biomes = {
	ResourceLocation.fromString('badlands'),
	ResourceLocation.fromString('bamboo_jungle'),
	ResourceLocation.fromString('basalt_deltas'),
	ResourceLocation.fromString('beach'),
	ResourceLocation.fromString('birch_forest'),
	ResourceLocation.fromString('cold_ocean'),
	ResourceLocation.fromString('crimson_forest'),
	ResourceLocation.fromString('dark_forest'),
	ResourceLocation.fromString('deep_cold_ocean'),
	ResourceLocation.fromString('deep_frozen_ocean'),
	ResourceLocation.fromString('deep_lukewarm_ocean'),
	ResourceLocation.fromString('deep_ocean'),
	ResourceLocation.fromString('desert'),
	ResourceLocation.fromString('dripstone_caves'),
	ResourceLocation.fromString('end_barrens'),
	ResourceLocation.fromString('end_highlands'),
	ResourceLocation.fromString('end_midlands'),
	ResourceLocation.fromString('eroded_badlands'),
	ResourceLocation.fromString('flower_forest'),
	ResourceLocation.fromString('forest'),
	ResourceLocation.fromString('frozen_ocean'),
	ResourceLocation.fromString('frozen_peaks'),
	ResourceLocation.fromString('frozen_river'),
	ResourceLocation.fromString('grove'),
	ResourceLocation.fromString('ice_spikes'),
	ResourceLocation.fromString('jagged_peaks'),
	ResourceLocation.fromString('jungle'),
	ResourceLocation.fromString('lukewarm_ocean'),
	ResourceLocation.fromString('lush_caves'),
	ResourceLocation.fromString('meadow'),
	ResourceLocation.fromString('mushroom_fields'),
	ResourceLocation.fromString('nether_wastes'),
	ResourceLocation.fromString('ocean'),
	ResourceLocation.fromString('old_growth_birch_forest'),
	ResourceLocation.fromString('old_growth_pine_taiga'),
	ResourceLocation.fromString('old_growth_spruce_taiga'),
	ResourceLocation.fromString('plains'),
	ResourceLocation.fromString('river'),
	ResourceLocation.fromString('savanna'),
	ResourceLocation.fromString('savanna_plateau'),
	ResourceLocation.fromString('small_end_islands'),
	ResourceLocation.fromString('snowy_beach'),
	ResourceLocation.fromString('snowy_plains'),
	ResourceLocation.fromString('snowy_slopes'),
	ResourceLocation.fromString('snowy_taiga'),
	ResourceLocation.fromString('soul_sand_valley'),
	ResourceLocation.fromString('sparse_jungle'),
	ResourceLocation.fromString('stony_peaks'),
	ResourceLocation.fromString('stony_shore'),
	ResourceLocation.fromString('sunflower_plains'),
	ResourceLocation.fromString('swamp'),
	ResourceLocation.fromString('taiga'),
	ResourceLocation.fromString('the_end'),
	ResourceLocation.fromString('the_void'),
	ResourceLocation.fromString('warm_ocean'),
	ResourceLocation.fromString('warped_forest'),
	ResourceLocation.fromString('windswept_forest'),
	ResourceLocation.fromString('windswept_gravelly_hills'),
	ResourceLocation.fromString('windswept_hills'),
	ResourceLocation.fromString('windswept_savanna'),
	ResourceLocation.fromString('wooded_badlands'),
}

fillCommandsFor1_18(version1_18)
fillFromMinecraftData(version1_18)

