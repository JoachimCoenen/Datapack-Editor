import minecraft_data

from model.commands.argumentTypes import *
from model.commands.filterArgs import FilterArgumentInfo
from model.data.mcVersions import MCVersion
from model.datapackContents import ResourceLocation


def rlsFromData(mcdList: list) -> set[ResourceLocation]:
	return {ResourceLocation.fromString(d['name']) for d in mcdList}


def fillFromMinecraftData(version: MCVersion) -> None:
	mcd = minecraft_data(version.name)
	version.biomes = rlsFromData(mcd.biomes_list)
	version.blocks = rlsFromData(mcd.blocks_list)
	version.blockStates = {ResourceLocation.fromString(block['name']): buildBlockStates(block['states']) for block in mcd.blocks_list}

	version.effects = rlsFromData(mcd.effects_list)
	version.enchantments = rlsFromData(mcd.enchantments_list)
	version.entities = rlsFromData(mcd.entities_list)

	version.items = rlsFromData(mcd.items_list)
	version.particles = rlsFromData(mcd.particles_list)
	# version.windows = rlsFromData(mcd.windows_list)


def buildBlockStates(states: list[dict]) -> list[FilterArgumentInfo]:
	return [buildBlockState(state) for state in states]


DESCRIPTIONS: dict[str, str] = {}


def buildBlockState(state: dict) -> FilterArgumentInfo:
	if state['type'] == 'int':
		type_ = BRIGADIER_INTEGER
	elif state['type'] == 'bool':
		type_ = BRIGADIER_BOOL
	elif state['type'] == 'enum':
		type_ = LiteralsArgumentType(state['values'])
	else:
		assert False

	fai = FilterArgumentInfo(
		name=state['name'],
		description=DESCRIPTIONS.get(state['name'], ''),
		type=type_,
	)

	return fai