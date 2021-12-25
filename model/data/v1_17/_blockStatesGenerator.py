from dataclasses import dataclass, replace
from operator import itemgetter
from typing import TextIO

from Cat.utils.collections_ import OrderedDict, OrderedMultiDict
from model.data.hardCodedBlockGroups import *
from model.datapackContents import ResourceLocation

@dataclass
class BlockStateInfo:
	name: str
	description: str
	types: OrderedMultiDict[str, set[ResourceLocation]]


RAW_BSAs_1: list[BlockStateInfo] = [
	BlockStateInfo(
		name="age",
		description="Tracks the age of plants to handle growth and of fire to handle spread.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|1}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('bamboo'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|2}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('cocoa'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|3}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('nether_wart'),
				ResourceLocation.fromString('beetroots'),
				ResourceLocation.fromString('frosted_ice'),
				ResourceLocation.fromString('sweet_berry_bush'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|5}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('chorus_flower'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|7}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('wheat'),
				ResourceLocation.fromString('pumpkin_stem'),
				ResourceLocation.fromString('melon_stem'),
				ResourceLocation.fromString('carrots'),
				ResourceLocation.fromString('potatoes'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|15}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('cactus'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('sugar_cane'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|25}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('kelp'),
			}),
		]),
	),
	BlockStateInfo(
		name="attached",
		description="Whether the tripwire hook is connected to a valid tripwire circuit or not.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('tripwire_hook'),
				ResourceLocation.fromString('tripwire'),
			}),
		]),
	),
	BlockStateInfo(
		name="attachment",
		description="How this block is attached to the block it is on.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['ceiling', 'double_wall', 'floor', 'single_wall'])", {
				ResourceLocation.fromString('bell'),
			}),
		]),
	),
	BlockStateInfo(
		name="axis",
		description="What axis the block is oriented to.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['x', 'y', 'z'])", {
				*ALL_LOGS,
				*ALL_STEMS,
				ResourceLocation.fromString('basalt'),
				ResourceLocation.fromString('polished_basalt'),
				ResourceLocation.fromString('bone_block'),
				ResourceLocation.fromString('chain'),
				ResourceLocation.fromString('hay_block'),
				ResourceLocation.fromString('purpur_pillar'),
				ResourceLocation.fromString('quartz_pillar'),
				ResourceLocation.fromString('deepslate'),
			}), (
			"LiteralsArgumentType(['x', 'z'])", {
				ResourceLocation.fromString('nether_portal')
			}),
		]),
	),
	BlockStateInfo(
		name="bites",
		description="The number of bites taken from the cake.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|6}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('cake'),
			}),
		]),
	),
	BlockStateInfo(
		name="bottom",
		description="Whether this scaffolding is floating (shows the bottom).",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('scaffolding'),
			}),
		]),
	),
	BlockStateInfo(
		name="charges",
		description="Tracks the remaining uses of respawn anchors.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|4}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('respawn_anchor'),
			}),
		]),
	),
	BlockStateInfo(
		name="conditional",
		description="Whether or not the command block is conditional.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_COMMAND_BLOCKS,
			}),
		]),
	),
	BlockStateInfo(
		name="delay",
		description="The amount of time between receiving a signal and responding.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|1}} to {{code|4}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('repeater'),
			}),
		]),
	),
	BlockStateInfo(
		name="disarmed",
		description="Whether the tripwire is broken using shears or not.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('tripwire'),
			}),
		]),
	),
]

RAW_BSAs_2: list[BlockStateInfo] = [
	BlockStateInfo(
		name="distance",
		description="The distance from a base block.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|7}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('scaffolding'),
			}), (
			# TODO: 'Integer ({{code|1}} to {{code|7}})'
			"BRIGADIER_INTEGER", {
				*ALL_LEAVES,
			}),
		]),
	),
	BlockStateInfo(
		name="down",
		description="Determines whether something is below the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
			}),
		]),
	),
	BlockStateInfo(
		name="drag",
		description="Determines whether the bubble column is a whirlpool or upwards.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('bubble_column'),
			}),
		]),
	),
	BlockStateInfo(
		name="east",
		description="Determines whether something is on the east side of the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_FENCES,
				*ALL_GLASS_PANES,
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('iron_bars'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('tripwire'),
				ResourceLocation.fromString('vine'),
			}), (
			"LiteralsArgumentType(['low', 'none', 'tall'])", {
				*ALL_WALLS,
			}), (
			"LiteralsArgumentType(['none', 'side', 'up'])", {
				ResourceLocation.fromString('redstone_wire'),
			}),
		]),
	),
	BlockStateInfo(
		name="eggs",
		description="The amount of eggs in this block.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|1}} to {{code|4}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('turtle_egg'),
			}),
		]),
	),
	BlockStateInfo(
		name="enabled",
		description="Whether or not the hopper can collect and transfer items.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('hopper'),
			}),
		]),
	),
	BlockStateInfo(
		name="extended",
		description="Whether or not the piston is extended.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('sticky_piston'),
				ResourceLocation.fromString('piston'),
			}),
		]),
	),
	BlockStateInfo(
		name="eye",
		description="Whether the frame contains an eye of ender.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('end_portal_frame'),
			}),
		]),
	),
	BlockStateInfo(
		name="face",
		description="What side of a block the attached block is on.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['ceiling', 'floor', 'wall'])", {
				*ALL_BUTTONS,
				ResourceLocation.fromString('grindstone'),
				ResourceLocation.fromString('lever'),
			}),
		]),
	),
	BlockStateInfo(
		name="facing",
		description="For most blocks, what direction the block faces.\nFor wall-attached [[bell]]s as well as [[cocoa]], the opposite is true.<ref>{{bug|MC-193943}}</ref>",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['down', 'east', 'north', 'south', 'west', 'up'])", {
				ResourceLocation.fromString('amethyst_cluster'),
				*ALL_COMMAND_BLOCKS,
				*ALL_SHULKER_BOXES,
				ResourceLocation.fromString('barrel'),
				ResourceLocation.fromString('dispenser'),
				ResourceLocation.fromString('dropper'),
				ResourceLocation.fromString('end_rod'),
				ResourceLocation.fromString('moving_piston'),
				ResourceLocation.fromString('observer'),
				ResourceLocation.fromString('piston'),
				ResourceLocation.fromString('piston_head'),
				ResourceLocation.fromString('sticky_piston'),
			}), (
			"LiteralsArgumentType(['east', 'north', 'south', 'west'])", {
				*ALL_ANVILS,
				*ALL_BANNERS,
				*ALL_BEDS,
				*ALL_CORAL_WALL_FANS,
				*ALL_BUTTONS,
				*ALL_DOORS,
				*ALL_FENCE_GATES,
				*ALL_GLAZED_TERRACOTTAS,
				*ALL_MOB_HEADS,
				*ALL_SIGNS,
				*ALL_STAIRS,
				*ALL_TRAPDOORS,
				ResourceLocation.fromString('attached_melon_stem'),
				ResourceLocation.fromString('attached_pumpkin_stem'),
				ResourceLocation.fromString('bell'),
				ResourceLocation.fromString('beehive'),
				ResourceLocation.fromString('bee_nest'),
				ResourceLocation.fromString('blast_furnace'),
				ResourceLocation.fromString('campfire'),
				ResourceLocation.fromString('carved_pumpkin'),
				ResourceLocation.fromString('chest'),
				ResourceLocation.fromString('cocoa'),
				ResourceLocation.fromString('end_portal_frame'),
				ResourceLocation.fromString('ender_chest'),
				ResourceLocation.fromString('furnace'),
				ResourceLocation.fromString('grindstone'),
				ResourceLocation.fromString('jack_o_lantern'),
				ResourceLocation.fromString('ladder'),
				ResourceLocation.fromString('lectern'),
				ResourceLocation.fromString('lever'),
				ResourceLocation.fromString('loom'),
				ResourceLocation.fromString('comparator'),
				ResourceLocation.fromString('repeater'),
				ResourceLocation.fromString('redstone_wall_torch'),
				ResourceLocation.fromString('smoker'),
				ResourceLocation.fromString('soul_campfire'),
				ResourceLocation.fromString('soul_wall_torch'),
				ResourceLocation.fromString('stonecutter'),
				ResourceLocation.fromString('trapped_chest'),
				ResourceLocation.fromString('tripwire_hook'),
				ResourceLocation.fromString('wall_torch'),
			}), (
			"LiteralsArgumentType(['down', 'east', 'north', 'south', 'west'])", {
				ResourceLocation.fromString('hopper'),
			}),
		]),
	),
]

RAW_BSAs_3: list[BlockStateInfo] = [
	BlockStateInfo(
		name="half",
		description="For tall plants and doors, which half of the door or plant occupies the block space. For trapdoors and stairs, what part of the block space they are in.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['lower', 'upper'])", {
				*ALL_DOORS,
				ResourceLocation.fromString('tall_seagrass'),
				ResourceLocation.fromString('sunflower'),
				ResourceLocation.fromString('lilac'),
				ResourceLocation.fromString('rose_bush'),
				ResourceLocation.fromString('peony'),
				ResourceLocation.fromString('tall_grass'),
				ResourceLocation.fromString('large_fern'),
			}), (
			"LiteralsArgumentType(['bottom', 'top'])", {
				*ALL_STAIRS,
				*ALL_TRAPDOORS,
			}),
		]),
	),
	BlockStateInfo(
		name="hanging",
		description="Whether or not the lantern hangs on the ceiling.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('lantern'),
				ResourceLocation.fromString('soul_lantern'),
			}),
		]),
	),
	BlockStateInfo(
		name="has_book",
		description="Whether or not this lectern holds a book.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('lectern'),
			}),
		]),
	),
	BlockStateInfo(
		name="has_bottle_0",
		description="Whether or not a bottle is in slot 1 of the brewing stand.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('brewing_stand'),
			}),
		]),
	),
	BlockStateInfo(
		name="has_bottle_1",
		description="Whether or not a bottle is in slot 2 of the brewing stand.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('brewing_stand'),
			}),
		]),
	),
	BlockStateInfo(
		name="has_bottle_2",
		description="Whether or not a bottle is in slot 3 of the brewing stand.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('brewing_stand'),
			}),
		]),
	),
	BlockStateInfo(
		name="has_record",
		description="True when the jukebox contains a music disc.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('jukebox'),
			}),
		]),
	),
	BlockStateInfo(
		name="hatch",
		description="Determines how close an egg is to hatching; starts at 0 and is randomly incremented.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|2}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('turtle_egg'),
			}),
		]),
	),
	BlockStateInfo(
		name="honey_level",
		description="Every pollinated bee that leaves the hive after working increases the honey level by one. When at level 5, honey can be bottled or honeycombs can be harvested.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|5}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('beehive'),
				ResourceLocation.fromString('bee_nest'),
			}),
		]),
	),
	BlockStateInfo(
		name="hinge",
		description="Identifies the side the hinge is on (when facing the same direction as the door's inside).",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['left', 'right'])", {
				*ALL_DOORS,
			}),
		]),
	),
	BlockStateInfo(
		name="in_wall",
		description="If true, the gate is lowered by three pixels, to accommodate attaching more cleanly with walls.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_FENCE_GATES,
			}),
		]),
	),
]

RAW_BSAs_4: list[BlockStateInfo] = [
	BlockStateInfo(
		name="instrument",
		description="The instrument sound the note block makes when it gets powered or used.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['banjo', 'basedrum', 'bass', 'bell', 'bit', 'chime', 'cow_bell', 'digeridoo', 'flute', 'guitar', 'harp', 'hat', 'iron_xylophone', 'snare', 'xylophone'])", {
				ResourceLocation.fromString('note_block'),
			}),
		]),
	),
	BlockStateInfo(
		name="inverted",
		description="Whether the daylight detector detects light (false) or darkness (true).",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('daylight_detector'),
			}),
		]),
	),
	BlockStateInfo(
		name="layers",
		description="How many layers of snow are on top of each other.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|1}} to {{code|8}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('snow'),
			}),
		]),
	),
	BlockStateInfo(
		name="leaves",
		description="How big the leaves are on this bamboo.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['large', 'none', 'small'])", {
				ResourceLocation.fromString('bamboo'),
			}),
		]),
	),
	BlockStateInfo(
		name="level",
		description="How much water or lava is in this block or cauldron.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|3}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('powder_snow_cauldron'),
				ResourceLocation.fromString('water_cauldron'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|8}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('composter'),
			}), (
			# TODO: 'Integer ({{code|0}} to {{code|15}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('lava'),
				ResourceLocation.fromString('light'),
				ResourceLocation.fromString('water'),
			}),
		]),
	),
	BlockStateInfo(
		name="lit",
		description="Whether the block is turned on or off.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('blast_furnace'),
				ResourceLocation.fromString('campfire'),
				ResourceLocation.fromString('furnace'),
				ResourceLocation.fromString('redstone_ore'),
				ResourceLocation.fromString('redstone_torch'),
				ResourceLocation.fromString('redstone_wall_torch'),
				ResourceLocation.fromString('redstone_lamp'),
				ResourceLocation.fromString('smoker'),
				ResourceLocation.fromString('soul_campfire'),
			}),
		]),
	),
	BlockStateInfo(
		name="locked",
		description="Whether the repeater can change it is powered state (false) or not (true).",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('repeater'),
			}),
		]),
	),
	BlockStateInfo(
		name="mode",
		description="The mode the comparator or structure block is in.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['compare', 'subtract'])", {
				ResourceLocation.fromString('comparator'),
			}), (
			"LiteralsArgumentType(['corner', 'data', 'load', 'save'])", {
				ResourceLocation.fromString('structure_block'),
			}),
		]),
	),
	BlockStateInfo(
		name="moisture",
		description="How wet the farmland is.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|7}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('farmland'),
			}),
		]),
	),
	BlockStateInfo(
		name="north",
		description="Determines whether something is on the north side of the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_FENCES,
				*ALL_GLASS_PANES,
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('iron_bars'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('tripwire'),
				ResourceLocation.fromString('vine'),
			}), (
			"LiteralsArgumentType(['low', 'none', 'tall'])", {
				*ALL_WALLS,
			}), (
			"LiteralsArgumentType(['up', 'side', 'none'])", {
				ResourceLocation.fromString('redstone_wire'),
			}),
		]),
	),
]

RAW_BSAs_5: list[BlockStateInfo] = [
	BlockStateInfo(
		name="note",
		description="The note the note block plays when it gets powered.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|24}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('note_block'),
			}),
		]),
	),
	BlockStateInfo(
		name="occupied",
		description="If there's already a player in this bed.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_BEDS,
			}),
		]),
	),
	BlockStateInfo(
		name="open",
		description="Whether the door is open or closed.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_DOORS,
				*ALL_FENCE_GATES,
				*ALL_TRAPDOORS,
				ResourceLocation.fromString('barrel'),
			}),
		]),
	),
	BlockStateInfo(
		name="orientation",
		description="Direction the arrows point, followed by the position of the line face.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['down_east', 'down_north', 'down_south', 'down_west', 'east_up', 'north_up', 'south_up', 'up_east', 'up_north', 'up_south', 'up_west', 'west_up'])", {
				ResourceLocation.fromString('jigsaw'),
			}),
		]),
	),
	BlockStateInfo(
		name="part",
		description="Whether this is the foot or head end of the bed.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['foot', 'head'])", {
				*ALL_BEDS,
			}),
		]),
	),
	BlockStateInfo(
		name="persistent",
		description="Whether leaves decay (false) or not (true)",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_LEAVES,
			}),
		]),
	),
	BlockStateInfo(
		name="pickles",
		description="The amount of pickles in this block.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|1}} to {{code|4}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('sea_pickle'),
			}),
		]),
	),
	BlockStateInfo(
		name="power",
		description="The power level of Redstone emission.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|15}})'
			"BRIGADIER_INTEGER", {
				ResourceLocation.fromString('redstone_wire'),
				ResourceLocation.fromString('light_weighted_pressure_plate'),
				ResourceLocation.fromString('heavy_weighted_pressure_plate'),
				ResourceLocation.fromString('daylight_detector'),
			}),
		]),
	),
	BlockStateInfo(
		name="powered",
		description="Whether the block is powered.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_BUTTONS,
				*ALL_DOORS,
				*ALL_FENCE_GATES,
				*ALL_NON_WEIGHTED_PRESSURE_PLATES,
				*ALL_TRAPDOORS,
				ResourceLocation.fromString('activator_rail'),
				ResourceLocation.fromString('detector_rail'),
				ResourceLocation.fromString('lectern'),
				ResourceLocation.fromString('lever'),
				ResourceLocation.fromString('note_block'),
				ResourceLocation.fromString('observer'),
				ResourceLocation.fromString('powered_rail'),
				ResourceLocation.fromString('comparator'),
				ResourceLocation.fromString('repeater'),
				ResourceLocation.fromString('tripwire'),
				ResourceLocation.fromString('tripwire_hook'),
			}),
		]),
	),
	BlockStateInfo(
		name="rotation",
		description="The rotation of standing heads, signs and banners.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|15}})'
			"BRIGADIER_INTEGER", {
				*ALL_BANNERS,
				*ALL_MOB_HEADS,
				*ALL_SIGNS,
			}),
		]),
	),
]

RAW_BSAs_6: list[BlockStateInfo] = [
	BlockStateInfo(
		name="shape",
		description="The way this block connects to its neighbors.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['ascending_east', 'ascending_north', 'ascending_south', 'ascending_west', 'east_west', 'north_south'])", {
				ResourceLocation.fromString('powered_rail'),
				ResourceLocation.fromString('detector_rail'),
				ResourceLocation.fromString('activator_rail'),
			}), (
			"LiteralsArgumentType(['inner_left', 'inner_right', 'outer_left', 'outer_right', 'straight'])", {
				*ALL_STAIRS,
			}), (
			"LiteralsArgumentType(['ascending_east', 'ascending_north', 'ascending_south', 'ascending_west', 'east_west', 'north_south', 'north_east', 'north_west', 'south_east', 'south_west'])", {
				ResourceLocation.fromString('rail'),
			}),
		]),
	),
	BlockStateInfo(
		name="short",
		description="Whether this piston head's arm is 4/16th of a block shorter",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('piston_head'),
			}),
		]),
	),
	BlockStateInfo(
		name="signal_fire",
		description="Whether this campfire has higher smoke or not.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('campfire'),
				ResourceLocation.fromString('soul_campfire'),
			}),
		]),
	),
	BlockStateInfo(
		name="snowy",
		description="Whether this block uses the snowy side texture.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('grass_block'),
				ResourceLocation.fromString('podzol'),
				ResourceLocation.fromString('mycelium'),
			}),
		]),
	),
	BlockStateInfo(
		name="south",
		description="Determines whether something is on the south side of the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_FENCES,
				*ALL_GLASS_PANES,
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('iron_bars'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('tripwire'),
				ResourceLocation.fromString('vine'),
			}), (
			"LiteralsArgumentType(['low', 'none', 'tall'])", {
				*ALL_WALLS,
			}), (
			"LiteralsArgumentType(['none', 'side', 'up'])", {
				ResourceLocation.fromString('redstone_wire'),
			}),
		]),
	),
	BlockStateInfo(
		name="stage",
		description="Whether this sapling is ready to grow.",
		types=OrderedMultiDict([(
			# TODO: 'Integer ({{code|0}} to {{code|1}})'
			"BRIGADIER_INTEGER", {
				*ALL_SAPLINGS,
				ResourceLocation.fromString('bamboo'),
			}),
		]),
	),
	BlockStateInfo(
		name="triggered",
		description="Whether this block has been activated.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('dispenser'),
				ResourceLocation.fromString('dropper'),
			}),
		]),
	),
	BlockStateInfo(
		name="type",
		description="Determines the variant of this block.",
		types=OrderedMultiDict([(
			"LiteralsArgumentType(['normal', 'sticky'])", {
				ResourceLocation.fromString('piston_head'),
				ResourceLocation.fromString('moving_piston'),
			}), (
			"LiteralsArgumentType(['left', 'right', 'single'])", {
				ResourceLocation.fromString('chest'),
				ResourceLocation.fromString('trapped_chest'),
			}), (
			"LiteralsArgumentType(['bottom', 'double', 'top'])", {
				*ALL_SLABS,
			}),
		]),
	),
	BlockStateInfo(
		name="unstable",
		description="Whether the TNT explodes when punched or not.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				ResourceLocation.fromString('tnt'),
			}),
		]),
	),
	BlockStateInfo(
		name="up",
		description="Determines whether something is above the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_WALLS,
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('vine'),
			}),
		]),
	),
]

RAW_BSAs_7: list[BlockStateInfo] = [
	BlockStateInfo(
		name="waterlogged",
		description="Whether the block has water in it.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_CORALS,
				*ALL_FENCES,
				*ALL_GLASS_PANES,
				*ALL_SIGNS,
				*ALL_SLABS,
				*ALL_STAIRS,
				*ALL_TRAPDOORS,
				*ALL_WALLS,
				ResourceLocation.fromString('campfire'),
				ResourceLocation.fromString('chain'),
				ResourceLocation.fromString('chest'),
				ResourceLocation.fromString('conduit'),
				ResourceLocation.fromString('ender_chest'),
				ResourceLocation.fromString('iron_bars'),
				ResourceLocation.fromString('ladder'),
				ResourceLocation.fromString('lantern'),
				ResourceLocation.fromString('light'),
				ResourceLocation.fromString('scaffolding'),
				ResourceLocation.fromString('sea_pickle'),
				ResourceLocation.fromString('soul_lantern'),
				ResourceLocation.fromString('trapped_chest'),
			}),
		]),
	),
	BlockStateInfo(
		name="west",
		description="Determines whether something is on the west side of the block.",
		types=OrderedMultiDict([(
			"BRIGADIER_BOOL", {
				*ALL_FENCES,
				*ALL_GLASS_PANES,
				ResourceLocation.fromString('brown_mushroom_block'),
				ResourceLocation.fromString('chorus_plant'),
				ResourceLocation.fromString('fire'),
				ResourceLocation.fromString('iron_bars'),
				ResourceLocation.fromString('mushroom_stem'),
				ResourceLocation.fromString('red_mushroom_block'),
				ResourceLocation.fromString('soul_fire'),
				ResourceLocation.fromString('tripwire'),
				ResourceLocation.fromString('vine'),
			}), (
			"LiteralsArgumentType(['low', 'none', 'tall'])", {
				*ALL_WALLS,
			}), (
			"LiteralsArgumentType(['none', 'side', 'up'])", {
				ResourceLocation.fromString('redstone_wire'),
			}),
		]),
	)
]

ALL_RAW_BSAs: list[BlockStateInfo] = [
	*RAW_BSAs_1,
	*RAW_BSAs_2,
	*RAW_BSAs_3,
	*RAW_BSAs_4,
	*RAW_BSAs_5,
	*RAW_BSAs_6,
	*RAW_BSAs_7,
]


@dataclass
class BlockStateInfo2:
	name: str
	description: str
	types: OrderedMultiDict[str, set[ResourceLocation]]


@dataclass
class FilterArgData:
	name: str
	description: str
	type: str


if __name__ == '__main__':
	print("generating block states file (generatedBlockStates.py)...")

	print(f"len(RAW_BSAs_1) = {len(RAW_BSAs_1)}")
	print(f"len(RAW_BSAs_2) = {len(RAW_BSAs_2)}")
	print(f"len(RAW_BSAs_3) = {len(RAW_BSAs_3)}")
	print(f"len(RAW_BSAs_4) = {len(RAW_BSAs_4)}")
	print(f"len(RAW_BSAs_5) = {len(RAW_BSAs_5)}")
	print(f"len(RAW_BSAs_6) = {len(RAW_BSAs_6)}")
	print(f"len(RAW_BSAs_7) = {len(RAW_BSAs_7)}")

	allArguments: OrderedDict[str, FilterArgData] = OrderedDict()
	argsByBlocks: OrderedDict[ResourceLocation, list[str]] = OrderedDict()

	for bsa in ALL_RAW_BSAs:
		faTemplate = FilterArgData(bsa.name, bsa.description, type='')
		argName = bsa.name

		blocks: set[ResourceLocation]
		for i, (type, blocks) in enumerate(bsa.types.items()):
			argVarName = f"{argName.upper()}_{i + 1}"
			arg = replace(faTemplate, type=type)
			allArguments[argVarName] = arg

			for block in sorted(blocks):
				argsByBlocks.setdefault(block, []).append(argVarName)

	blocksByArgs: OrderedDict[tuple[str, ...], list[ResourceLocation]] = OrderedDict()
	for block, bsais in argsByBlocks.items():
		bsais = tuple(sorted(bsais))
		blocksByArgs.setdefault(bsais, []).append(block)

	def printPreamble(file: TextIO):
		file.write('"""\n')
		file.write("	This file is generated by _blockStatesGenerator.py!\n")
		file.write("					DO NOT EDIT!\n")
		file.write('"""\n')
		file.write("from model.commands.argumentTypes import *\n")
		file.write("from model.commands.filterArgs import FilterArgumentInfo\n")
		file.write("from model.datapackContents import ResourceLocation\n")


	def printArgInfos(file: TextIO):
		file.write("# Argument types:\n")
		file.write("\n")
		for varName, arg in allArguments.items():
			file.write(f"{varName} = FilterArgumentInfo.create(\n")
			file.write(f"	name={arg.name!r},\n")
			file.write(f"	description={arg.description!r},\n")
			file.write(f"	type={arg.type},\n")
			file.write(f")\n")
			file.write(f"\n")

	def printARGS_BYBLOCKS(file: TextIO):
		file.write("# Arguments by block:\n")
		file.write("\n")
		file.write("BLOCK_STATES_BY_BLOCK = {\n")
		for block, bsais in argsByBlocks.items():
			file.write(f"\tResourceLocation.fromString('{block.asCompactString}'): [{', '.join(bsais)}],\n")
		file.write("}\n\n")

	with open('./generatedBlockStates.py', 'w') as file:
		printPreamble(file)
		printArgInfos(file)
		printARGS_BYBLOCKS(file)
		file.write("__all__ = ['BLOCK_STATES_BY_BLOCK']\n")

	print("checking block states for invalid block IDs:")
	import generatedBlockStates
	from model.data.dataValues import BLOCKS

	allGood = True
	for block in generatedBlockStates.BLOCK_STATES_BY_BLOCK:
		if block not in BLOCKS:
			allGood = False
			print(f"  unknown block: {block.asString}")
	if allGood:
		print("  SUCCESS.")
