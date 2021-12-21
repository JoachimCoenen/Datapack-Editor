from typing import Optional

from model.commands.argumentTypes import *
from model.commands.argumentValues import FilterArguments
from model.commands.filterArgs import parseFilterArgs, FilterArgumentInfo
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.data.dataValues import BLOCKS
from model.datapackContents import ResourceLocation

# Argument types:

AGE_1 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|1}})',
)

AGE_2 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|2}})',
)

AGE_3 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|3}})',
)

AGE_4 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|5}})',
)

AGE_5 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|7}})',
)

AGE_6 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|15}})',
)

AGE_7 = FilterArgumentInfo.create(
	name='age',
	description='Tracks the age of plants to handle growth and of fire to handle spread.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|25}})',
)

ATTACHED_1 = FilterArgumentInfo.create(
	name='attached',
	description='Whether the tripwire hook is connected to a valid tripwire circuit or not.',
	type=BRIGADIER_BOOL,
)

ATTACHMENT_1 = FilterArgumentInfo.create(
	name='attachment',
	description='How this block is attached to the block it is on.',
	type=LiteralsArgumentType(['ceiling', 'double_wall', 'floor', 'single_wall']),
)

AXIS_1 = FilterArgumentInfo.create(
	name='axis',
	description='What axis the block is oriented to.',
	type=LiteralsArgumentType(['x', 'y', 'z']),
)

AXIS_2 = FilterArgumentInfo.create(
	name='axis',
	description='What axis the block is oriented to.',
	type=LiteralsArgumentType(['x', 'z']),
)

BITES_1 = FilterArgumentInfo.create(
	name='bites',
	description='The number of bites taken from the cake.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|6}})',
)

BOTTOM_1 = FilterArgumentInfo.create(
	name='bottom',
	description='Whether this scaffolding is floating (shows the bottom).',
	type=BRIGADIER_BOOL,
)

CHARGES_1 = FilterArgumentInfo.create(
	name='charges',
	description='Tracks the remaining uses of respawn anchors.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|4}})',
)

CONDITIONAL_1 = FilterArgumentInfo.create(
	name='conditional',
	description='Whether or not the command block is conditional.',
	type=BRIGADIER_BOOL,
)

DELAY_1 = FilterArgumentInfo.create(
	name='delay',
	description='The amount of time between receiving a signal and responding.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|1}} to {{code|4}})',
)

DISARMED_1 = FilterArgumentInfo.create(
	name='disarmed',
	description='Whether the tripwire is broken using shears or not.',
	type=BRIGADIER_BOOL,
)

DISTANCE_1 = FilterArgumentInfo.create(
	name='distance',
	description='The distance from a base block.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|7}})',
)

DISTANCE_2 = FilterArgumentInfo.create(
	name='distance',
	description='The distance from a base block.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|1}} to {{code|7}})',
)

DOWN_1 = FilterArgumentInfo.create(
	name='down',
	description='Determines whether something is below the block.',
	type=BRIGADIER_BOOL,
)

DRAG_1 = FilterArgumentInfo.create(
	name='drag',
	description='Determines whether the bubble column is a whirlpool or upwards.',
	type=BRIGADIER_BOOL,
)

EAST_1 = FilterArgumentInfo.create(
	name='east',
	description='Determines whether something is on the east side of the block.',
	type=BRIGADIER_BOOL,
)

EAST_2 = FilterArgumentInfo.create(
	name='east',
	description='Determines whether something is on the east side of the block.',
	type=LiteralsArgumentType(['none', 'side', 'up']),
)

EGGS_1 = FilterArgumentInfo.create(
	name='eggs',
	description='The amount of eggs in this block.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|1}} to {{code|4}})',
)

ENABLED_1 = FilterArgumentInfo.create(
	name='enabled',
	description='Whether or not the hopper can collect and transfer items.',
	type=BRIGADIER_BOOL,
)

EXTENDED_1 = FilterArgumentInfo.create(
	name='extended',
	description='Whether or not the piston is extended.',
	type=BRIGADIER_BOOL,
)

EYE_1 = FilterArgumentInfo.create(
	name='eye',
	description='Whether the frame contains an eye of ender.',
	type=BRIGADIER_BOOL,
)

FACE_1 = FilterArgumentInfo.create(
	name='face',
	description='What side of a block the attached block is on.',
	type=LiteralsArgumentType(['ceiling', 'floor', 'wall']),
)

FACING_1 = FilterArgumentInfo.create(
	name='facing',
	description='For most blocks, what direction the block faces.\nFor wall-attached [[bell]]s as well as [[cocoa]], the opposite is true.<ref>{{bug|MC-193943}}</ref>',
	type=LiteralsArgumentType(['down', 'east', 'north', 'south', 'west', 'up']),
)

FACING_2 = FilterArgumentInfo.create(
	name='facing',
	description='For most blocks, what direction the block faces.\nFor wall-attached [[bell]]s as well as [[cocoa]], the opposite is true.<ref>{{bug|MC-193943}}</ref>',
	type=LiteralsArgumentType(['east', 'north', 'south', 'west']),
)

FACING_3 = FilterArgumentInfo.create(
	name='facing',
	description='For most blocks, what direction the block faces.\nFor wall-attached [[bell]]s as well as [[cocoa]], the opposite is true.<ref>{{bug|MC-193943}}</ref>',
	type=LiteralsArgumentType(['down', 'east', 'north', 'south', 'west']),
)

HALF_1 = FilterArgumentInfo.create(
	name='half',
	description='For tall plants and doors, which half of the door or plant occupies the block space. For trapdoors and stairs, what part of the block space they are in.',
	type=LiteralsArgumentType(['lower', 'upper']),
)

HALF_2 = FilterArgumentInfo.create(
	name='half',
	description='For tall plants and doors, which half of the door or plant occupies the block space. For trapdoors and stairs, what part of the block space they are in.',
	type=LiteralsArgumentType(['bottom', 'top']),
)

HANGING_1 = FilterArgumentInfo.create(
	name='hanging',
	description='Whether or not the lantern hangs on the ceiling.',
	type=BRIGADIER_BOOL,
)

HAS_BOOK_1 = FilterArgumentInfo.create(
	name='has_book',
	description='Whether or not this lectern holds a book.',
	type=BRIGADIER_BOOL,
)

HAS_BOTTLE_0_1 = FilterArgumentInfo.create(
	name='has_bottle_0',
	description='Whether or not a bottle is in slot 1 of the brewing stand.',
	type=BRIGADIER_BOOL,
)

HAS_BOTTLE_1_1 = FilterArgumentInfo.create(
	name='has_bottle_1',
	description='Whether or not a bottle is in slot 2 of the brewing stand.',
	type=BRIGADIER_BOOL,
)

HAS_BOTTLE_2_1 = FilterArgumentInfo.create(
	name='has_bottle_2',
	description='Whether or not a bottle is in slot 3 of the brewing stand.',
	type=BRIGADIER_BOOL,
)

HAS_RECORD_1 = FilterArgumentInfo.create(
	name='has_record',
	description='True when the jukebox contains a music disc.',
	type=BRIGADIER_BOOL,
)

HATCH_1 = FilterArgumentInfo.create(
	name='hatch',
	description='Determines how close an egg is to hatching; starts at 0 and is randomly incremented.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|2}})',
)

HINGE_1 = FilterArgumentInfo.create(
	name='hinge',
	description="Identifies the side the hinge is on (when facing the same direction as the door's inside).",
	type=LiteralsArgumentType(['left', 'right']),
)

IN_WALL_1 = FilterArgumentInfo.create(
	name='in_wall',
	description='If true, the gate is lowered by three pixels, to accommodate attaching more cleanly with walls.',
	type=BRIGADIER_BOOL,
)

INSTRUMENT_1 = FilterArgumentInfo.create(
	name='instrument',
	description='The instrument sound the note block makes when it gets powered or used.',
	type=LiteralsArgumentType(['banjo', 'basedrum', 'bass', 'bell', 'bit', 'chime', 'cow_bell', 'digeridoo', 'flute', 'guitar', 'harp', 'hat', 'iron_xylophone', 'snare', 'xylophone']),
)

INVERTED_1 = FilterArgumentInfo.create(
	name='inverted',
	description='Whether the daylight detector detects light (false) or darkness (true).',
	type=BRIGADIER_BOOL,
)

LAYERS_1 = FilterArgumentInfo.create(
	name='layers',
	description='How many layers of snow are on top of each other.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|1}} to {{code|8}})',
)

LEAVES_1 = FilterArgumentInfo.create(
	name='leaves',
	description='How big the leaves are on this bamboo.',
	type=LiteralsArgumentType(['large', 'none', 'small']),
)

LEVEL_1 = FilterArgumentInfo.create(
	name='level',
	description='How much water or lava is in this block or cauldron.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|3}})',
)

LEVEL_2 = FilterArgumentInfo.create(
	name='level',
	description='How much water or lava is in this block or cauldron.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|8}})',
)

LEVEL_3 = FilterArgumentInfo.create(
	name='level',
	description='How much water or lava is in this block or cauldron.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|15}})',
)

LIT_1 = FilterArgumentInfo.create(
	name='lit',
	description='Whether the block is turned on or off.',
	type=BRIGADIER_BOOL,
)

LOCKED_1 = FilterArgumentInfo.create(
	name='locked',
	description='Whether the repeater can change it is powered state (false) or not (true).',
	type=BRIGADIER_BOOL,
)

MODE_1 = FilterArgumentInfo.create(
	name='mode',
	description='The mode the comparator or structure block is in.',
	type=LiteralsArgumentType(['compare', 'subtract']),
)

MODE_2 = FilterArgumentInfo.create(
	name='mode',
	description='The mode the comparator or structure block is in.',
	type=LiteralsArgumentType(['corner', 'data', 'load', 'save']),
)

MOISTURE_1 = FilterArgumentInfo.create(
	name='moisture',
	description='How wet the farmland is.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|7}})',
)

NORTH_1 = FilterArgumentInfo.create(
	name='north',
	description='Determines whether something is on the north side of the block.',
	type=BRIGADIER_BOOL,
)

NORTH_2 = FilterArgumentInfo.create(
	name='north',
	description='Determines whether something is on the north side of the block.',
	type=LiteralsArgumentType(['up', 'side', 'none']),
)

NOTE_1 = FilterArgumentInfo.create(
	name='note',
	description='The note the note block plays when it gets powered.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|24}})',
)

OCCUPIED_1 = FilterArgumentInfo.create(
	name='occupied',
	description="If there's already a player in this bed.",
	type=BRIGADIER_BOOL,
)

OPEN_1 = FilterArgumentInfo.create(
	name='open',
	description='Whether the door is open or closed.',
	type=BRIGADIER_BOOL,
)

ORIENTATION_1 = FilterArgumentInfo.create(
	name='orientation',
	description='Direction the arrows point, followed by the position of the line face.',
	type=LiteralsArgumentType(['down_east', 'down_north', 'down_south', 'down_west', 'east_up', 'north_up', 'south_up', 'up_east', 'up_north', 'up_south', 'up_west', 'west_up']),
)

PART_1 = FilterArgumentInfo.create(
	name='part',
	description='Whether this is the foot or head end of the bed.',
	type=LiteralsArgumentType(['foot', 'head']),
)

PERSISTENT_1 = FilterArgumentInfo.create(
	name='persistent',
	description='Whether leaves decay (false) or not (true)',
	type=BRIGADIER_BOOL,
)

PICKLES_1 = FilterArgumentInfo.create(
	name='pickles',
	description='The amount of pickles in this block.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|1}} to {{code|4}})',
)

POWER_1 = FilterArgumentInfo.create(
	name='power',
	description='The power level of Redstone emission.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|15}})',
)

POWERED_1 = FilterArgumentInfo.create(
	name='powered',
	description='Whether the block is powered.',
	type=BRIGADIER_BOOL,
)

ROTATION_1 = FilterArgumentInfo.create(
	name='rotation',
	description='The rotation of standing heads, signs and banners.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|15}})',
)

SHAPE_1 = FilterArgumentInfo.create(
	name='shape',
	description='The way this block connects to its neighbors.',
	type=LiteralsArgumentType(['ascending_east', 'ascending_north', 'ascending_south', 'ascending_west', 'east_west', 'north_south']),
)

SHAPE_2 = FilterArgumentInfo.create(
	name='shape',
	description='The way this block connects to its neighbors.',
	type=LiteralsArgumentType(['inner_left', 'inner_right', 'outer_left', 'outer_right', 'straight']),
)

SHAPE_3 = FilterArgumentInfo.create(
	name='shape',
	description='The way this block connects to its neighbors.',
	type=LiteralsArgumentType(['ascending_east', 'ascending_north', 'ascending_south', 'ascending_west', 'east_west', 'north_south', 'north_east', 'north_west', 'south_east', 'south_west']),
)

SHORT_1 = FilterArgumentInfo.create(
	name='short',
	description="Whether this piston head's arm is 4/16th of a block shorter",
	type=BRIGADIER_BOOL,
)

SIGNAL_FIRE_1 = FilterArgumentInfo.create(
	name='signal_fire',
	description='Whether this campfire has higher smoke or not.',
	type=BRIGADIER_BOOL,
)

SNOWY_1 = FilterArgumentInfo.create(
	name='snowy',
	description='Whether this block uses the snowy side texture.',
	type=BRIGADIER_BOOL,
)

SOUTH_1 = FilterArgumentInfo.create(
	name='south',
	description='Determines whether something is on the south side of the block.',
	type=BRIGADIER_BOOL,
)

SOUTH_2 = FilterArgumentInfo.create(
	name='south',
	description='Determines whether something is on the south side of the block.',
	type=LiteralsArgumentType(['none', 'side', 'up']),
)

STAGE_1 = FilterArgumentInfo.create(
	name='stage',
	description='Whether this sapling is ready to grow.',
	type=BRIGADIER_INTEGER,
	# TODO: type='Integer ({{code|0}} to {{code|1}})',
)

TRIGGERED_1 = FilterArgumentInfo.create(
	name='triggered',
	description='Whether this block has been activated.',
	type=BRIGADIER_BOOL,
)

TYPE_1 = FilterArgumentInfo.create(
	name='type',
	description='Determines the variant of this block.',
	type=LiteralsArgumentType(['normal', 'sticky']),
)

TYPE_2 = FilterArgumentInfo.create(
	name='type',
	description='Determines the variant of this block.',
	type=LiteralsArgumentType(['left', 'right', 'single']),
)

TYPE_3 = FilterArgumentInfo.create(
	name='type',
	description='Determines the variant of this block.',
	type=LiteralsArgumentType(['bottom', 'double', 'top']),
)

UNSTABLE_1 = FilterArgumentInfo.create(
	name='unstable',
	description='Whether the TNT explodes when punched or not.',
	type=BRIGADIER_BOOL,
)

UP_1 = FilterArgumentInfo.create(
	name='up',
	description='Determines whether something is above the block.',
	type=BRIGADIER_BOOL,
)

WATERLOGGED_1 = FilterArgumentInfo.create(
	name='waterlogged',
	description='Whether the block has water in it.',
	type=BRIGADIER_BOOL,
)

WEST_1 = FilterArgumentInfo.create(
	name='west',
	description='Determines whether something is on the west side of the block.',
	type=BRIGADIER_BOOL,
)

WEST_2 = FilterArgumentInfo.create(
	name='west',
	description='Determines whether something is on the west side of the block.',
	type=LiteralsArgumentType(['none', 'side', 'up']),
)


# Arguments by block:

BLOCK_STATES_BY_BLOCK = {
	ResourceLocation.fromString('bamboo'): [
		AGE_1, 
		LEAVES_1, 
		STAGE_1, 
	], ResourceLocation.fromString('cocoa'): [
		AGE_2, 
		FACING_2, 
	], ResourceLocation.fromString('frosted_ice'): [
		AGE_3, 
	], ResourceLocation.fromString('sweet_berry_bush'): [
		AGE_3, 
	], ResourceLocation.fromString('beetroots'): [
		AGE_3, 
	], ResourceLocation.fromString('nether_wart'): [
		AGE_3, 
	], ResourceLocation.fromString('chorus_flower'): [
		AGE_4, 
	], ResourceLocation.fromString('potatoes'): [
		AGE_5, 
	], ResourceLocation.fromString('wheat'): [
		AGE_5, 
	], ResourceLocation.fromString('pumpkin_stem'): [
		AGE_5, 
	], ResourceLocation.fromString('melon_stem'): [
		AGE_5, 
	], ResourceLocation.fromString('carrots'): [
		AGE_5, 
	], ResourceLocation.fromString('soul_fire'): [
		AGE_6, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('sugar_cane'): [
		AGE_6, 
	], ResourceLocation.fromString('cactus'): [
		AGE_6, 
	], ResourceLocation.fromString('fire'): [
		AGE_6, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('kelp'): [
		AGE_7, 
	], ResourceLocation.fromString('tripwire'): [
		ATTACHED_1, 
		DISARMED_1, 
		EAST_1, 
		NORTH_1, 
		POWERED_1, 
		SOUTH_1, 
		WEST_1, 
	], ResourceLocation.fromString('tripwire_hook'): [
		ATTACHED_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('bell'): [
		ATTACHMENT_1, 
		FACING_2, 
	], ResourceLocation.fromString('spruce_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('dark_oak_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_birch_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('chain'): [
		AXIS_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('stripped_warped_stem'): [
		AXIS_1, 
	], ResourceLocation.fromString('deepslate'): [
		AXIS_1, 
	], ResourceLocation.fromString('warped_stem'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_dark_oak_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('hay_block'): [
		AXIS_1, 
	], ResourceLocation.fromString('quartz_pillar'): [
		AXIS_1, 
	], ResourceLocation.fromString('purpur_pillar'): [
		AXIS_1, 
	], ResourceLocation.fromString('crimson_stem'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_acacia_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('polished_basalt'): [
		AXIS_1, 
	], ResourceLocation.fromString('acacia_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('birch_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_oak_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_crimson_stem'): [
		AXIS_1, 
	], ResourceLocation.fromString('bone_block'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_jungle_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('basalt'): [
		AXIS_1, 
	], ResourceLocation.fromString('jungle_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('oak_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('stripped_spruce_log'): [
		AXIS_1, 
	], ResourceLocation.fromString('nether_portal'): [
		AXIS_2, 
	], ResourceLocation.fromString('cake'): [
		BITES_1, 
	], ResourceLocation.fromString('scaffolding'): [
		BOTTOM_1, 
		DISTANCE_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('respawn_anchor'): [
		CHARGES_1, 
	], ResourceLocation.fromString('chain_command_block'): [
		CONDITIONAL_1, 
		FACING_1, 
	], ResourceLocation.fromString('command_block'): [
		CONDITIONAL_1, 
		FACING_1, 
	], ResourceLocation.fromString('repeating_command_block'): [
		CONDITIONAL_1, 
		FACING_1, 
	], ResourceLocation.fromString('repeater'): [
		DELAY_1, 
		FACING_2, 
		LOCKED_1, 
		POWERED_1, 
	], ResourceLocation.fromString('acacia_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('oak_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('jungle_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('birch_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('spruce_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('dark_oak_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('flowering_azalea_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('azalea_leaves'): [
		DISTANCE_2, 
		PERSISTENT_1, 
	], ResourceLocation.fromString('mushroom_stem'): [
		DOWN_1, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('chorus_plant'): [
		DOWN_1, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('red_mushroom_block'): [
		DOWN_1, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('brown_mushroom_block'): [
		DOWN_1, 
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('bubble_column'): [
		DRAG_1, 
	], ResourceLocation.fromString('brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('jungle_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('polished_deepslate_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('oak_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('mossy_stone_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('diorite_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('cobbled_deepslate_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('red_sandstone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('red_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('birch_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('pink_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('nether_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('end_stone_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('light_blue_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('light_gray_stained_glass_pane'): [
		EAST_1,
		NORTH_1,
		SOUTH_1,
		WATERLOGGED_1,
		WEST_1,
	], ResourceLocation.fromString('spruce_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('cobblestone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('nether_brick_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('polished_blackstone_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('sandstone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('red_nether_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('lime_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('blue_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('green_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('brown_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('iron_bars'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('acacia_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('gray_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('blackstone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('deepslate_tile_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('vine'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WEST_1, 
	], ResourceLocation.fromString('deepslate_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('purple_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('warped_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('mossy_cobblestone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('crimson_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('orange_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('dark_oak_fence'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('stone_brick_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('cyan_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('andesite_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('black_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('polished_blackstone_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('prismarine_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('yellow_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('white_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('granite_wall'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		UP_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('magenta_stained_glass_pane'): [
		EAST_1, 
		NORTH_1, 
		SOUTH_1, 
		WATERLOGGED_1, 
		WEST_1, 
	], ResourceLocation.fromString('redstone_wire'): [
		EAST_2, 
		NORTH_2, 
		POWER_1, 
		SOUTH_2, 
		WEST_2, 
	], ResourceLocation.fromString('turtle_egg'): [
		EGGS_1, 
		HATCH_1, 
	], ResourceLocation.fromString('hopper'): [
		ENABLED_1, 
		FACING_3, 
	], ResourceLocation.fromString('piston'): [
		EXTENDED_1, 
		FACING_1, 
	], ResourceLocation.fromString('sticky_piston'): [
		EXTENDED_1, 
		FACING_1, 
	], ResourceLocation.fromString('end_portal_frame'): [
		EYE_1, 
		FACING_2, 
	], ResourceLocation.fromString('spruce_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('stone_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('birch_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('lever'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('jungle_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('acacia_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('oak_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('grindstone'): [
		FACE_1, 
		FACING_2, 
	], ResourceLocation.fromString('warped_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('polished_blackstone_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('crimson_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('dark_oak_button'): [
		FACE_1, 
		FACING_2, 
		POWERED_1, 
	], ResourceLocation.fromString('brown_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('dispenser'): [
		FACING_1, 
		TRIGGERED_1, 
	], ResourceLocation.fromString('shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('blue_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('end_rod'): [
		FACING_1, 
	], ResourceLocation.fromString('pink_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('green_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('light_blue_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('light_gray_shulker_box'): [
		FACING_1,
	], ResourceLocation.fromString('white_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('orange_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('dropper'): [
		FACING_1, 
		TRIGGERED_1, 
	], ResourceLocation.fromString('moving_piston'): [
		FACING_1, 
		TYPE_1, 
	], ResourceLocation.fromString('magenta_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('gray_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('red_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('observer'): [
		FACING_1, 
		POWERED_1, 
	], ResourceLocation.fromString('lime_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('amethyst_cluster'): [
		FACING_1, 
	], ResourceLocation.fromString('purple_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('black_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('cyan_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('barrel'): [
		FACING_1, 
		OPEN_1, 
	], ResourceLocation.fromString('yellow_shulker_box'): [
		FACING_1, 
	], ResourceLocation.fromString('piston_head'): [
		FACING_1, 
		SHORT_1, 
		TYPE_1, 
	], ResourceLocation.fromString('red_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('magenta_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('chipped_anvil'): [
		FACING_2, 
	], ResourceLocation.fromString('acacia_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('oak_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('blue_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('crimson_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('loom'): [
		FACING_2, 
	], ResourceLocation.fromString('smooth_red_sandstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('warped_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('lime_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('stone_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('fire_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('iron_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('acacia_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('iron_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('player_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('white_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('campfire'): [
		FACING_2, 
		LIT_1, 
		SIGNAL_FIRE_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('yellow_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('brain_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('ladder'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('sandstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('blue_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('waxed_weathered_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('spruce_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cobbled_deepslate_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('purpur_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('blast_furnace'): [
		FACING_2, 
		LIT_1, 
	], ResourceLocation.fromString('birch_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('pink_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('diorite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('andesite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('prismarine_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('gray_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('birch_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('crimson_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('zombie_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('jungle_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('redstone_wall_torch'): [
		FACING_2, 
		LIT_1, 
	], ResourceLocation.fromString('white_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('orange_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('light_blue_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('light_gray_glazed_terracotta'): [
		FACING_2,
	], ResourceLocation.fromString('pink_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('waxed_oxidized_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('warped_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('green_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('deepslate_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('skeleton_skull'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('oak_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('yellow_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('black_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('deepslate_tile_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('white_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('dark_oak_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('magenta_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('mossy_cobblestone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('horn_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('soul_wall_torch'): [
		FACING_2, 
	], ResourceLocation.fromString('polished_blackstone_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cyan_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('light_blue_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('light_gray_bed'): [
		FACING_2,
		OCCUPIED_1,
		PART_1,
	], ResourceLocation.fromString('polished_blackstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('red_nether_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('soul_campfire'): [
		FACING_2, 
		LIT_1, 
		SIGNAL_FIRE_1, 
	], ResourceLocation.fromString('chest'): [
		FACING_2, 
		TYPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('purple_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('lime_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('wither_skeleton_skull'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('attached_melon_stem'): [
		FACING_2, 
	], ResourceLocation.fromString('lime_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('dark_oak_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('orange_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('waxed_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_tube_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('oak_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('warped_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('dead_brain_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('gray_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('zombie_wall_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('polished_diorite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('gray_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('white_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('mossy_stone_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('pink_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('cyan_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('attached_pumpkin_stem'): [
		FACING_2, 
	], ResourceLocation.fromString('polished_deepslate_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cyan_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('polished_granite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('acacia_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('waxed_exposed_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('stone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('oak_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('smoker'): [
		FACING_2, 
		LIT_1, 
	], ResourceLocation.fromString('smooth_sandstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('stonecutter'): [
		FACING_2, 
	], ResourceLocation.fromString('light_blue_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('light_gray_banner'): [
		FACING_2,
		ROTATION_1,
	], ResourceLocation.fromString('carved_pumpkin'): [
		FACING_2, 
	], ResourceLocation.fromString('brown_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('orange_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('black_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('blue_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('oak_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brown_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('nether_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('light_blue_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('light_gray_wall_banner'): [
		FACING_2,
		ROTATION_1,
	], ResourceLocation.fromString('gray_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('crimson_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('dark_oak_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('blue_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('comparator'): [
		FACING_2, 
		MODE_1, 
		POWERED_1, 
	], ResourceLocation.fromString('dead_bubble_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('warped_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('bubble_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_andesite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('lectern'): [
		FACING_2, 
		HAS_BOOK_1, 
		POWERED_1, 
	], ResourceLocation.fromString('pink_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('black_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('red_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('damaged_anvil'): [
		FACING_2, 
	], ResourceLocation.fromString('dark_prismarine_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('black_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('yellow_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('player_wall_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('spruce_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('acacia_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('end_stone_brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('blackstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('green_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('dead_horn_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dark_oak_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('crimson_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('creeper_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('prismarine_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('spruce_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('dead_fire_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('birch_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('yellow_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('dark_oak_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('acacia_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('green_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('trapped_chest'): [
		FACING_2, 
		TYPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('exposed_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brown_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('green_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('orange_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('ender_chest'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('furnace'): [
		FACING_2, 
		LIT_1, 
	], ResourceLocation.fromString('magenta_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('skeleton_wall_skull'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('brick_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('birch_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('cyan_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('dragon_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('granite_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('wither_skeleton_wall_skull'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('magenta_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('red_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('warped_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('crimson_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('spruce_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('acacia_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jack_o_lantern'): [
		FACING_2, 
	], ResourceLocation.fromString('tube_coral_wall_fan'): [
		FACING_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dragon_wall_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('spruce_fence_gate'): [
		FACING_2, 
		IN_WALL_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('birch_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cobblestone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dark_oak_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('lime_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('oak_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('oxidized_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('quartz_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('spruce_door'): [
		FACING_2, 
		HALF_1, 
		HINGE_1, 
		OPEN_1, 
		POWERED_1, 
	], ResourceLocation.fromString('brown_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('anvil'): [
		FACING_2, 
	], ResourceLocation.fromString('purple_bed'): [
		FACING_2, 
		OCCUPIED_1, 
		PART_1, 
	], ResourceLocation.fromString('birch_trapdoor'): [
		FACING_2, 
		HALF_2, 
		OPEN_1, 
		POWERED_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_wall_sign'): [
		FACING_2, 
		ROTATION_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('beehive'): [
		FACING_2, 
	], ResourceLocation.fromString('weathered_cut_copper_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('purple_wall_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('red_banner'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('red_sandstone_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('purple_glazed_terracotta'): [
		FACING_2, 
	], ResourceLocation.fromString('creeper_wall_head'): [
		FACING_2, 
		ROTATION_1, 
	], ResourceLocation.fromString('smooth_quartz_stairs'): [
		FACING_2, 
		HALF_2, 
		SHAPE_2, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('wall_torch'): [
		FACING_2, 
	], ResourceLocation.fromString('large_fern'): [
		HALF_1, 
	], ResourceLocation.fromString('tall_grass'): [
		HALF_1, 
	], ResourceLocation.fromString('peony'): [
		HALF_1, 
	], ResourceLocation.fromString('sunflower'): [
		HALF_1, 
	], ResourceLocation.fromString('lilac'): [
		HALF_1, 
	], ResourceLocation.fromString('tall_seagrass'): [
		HALF_1, 
	], ResourceLocation.fromString('rose_bush'): [
		HALF_1, 
	], ResourceLocation.fromString('soul_lantern'): [
		HANGING_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('lantern'): [
		HANGING_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brewing_stand'): [
		HAS_BOTTLE_0_1, 
		HAS_BOTTLE_1_1, 
		HAS_BOTTLE_2_1, 
	], ResourceLocation.fromString('jukebox'): [
		HAS_RECORD_1, 
	], ResourceLocation.fromString('note_block'): [
		INSTRUMENT_1, 
		NOTE_1, 
		POWERED_1, 
	], ResourceLocation.fromString('daylight_detector'): [
		INVERTED_1, 
		POWER_1, 
	], ResourceLocation.fromString('snow'): [
		LAYERS_1, 
	], ResourceLocation.fromString('cauldron'): [
		LEVEL_1, 
	], ResourceLocation.fromString('composter'): [
		LEVEL_2, 
	], ResourceLocation.fromString('lava'): [
		LEVEL_3, 
	], ResourceLocation.fromString('water'): [
		LEVEL_3, 
	], ResourceLocation.fromString('redstone_ore'): [
		LIT_1, 
	], ResourceLocation.fromString('redstone_torch'): [
		LIT_1, 
	], ResourceLocation.fromString('redstone_lamp'): [
		LIT_1, 
	], ResourceLocation.fromString('structure_block'): [
		MODE_2, 
	], ResourceLocation.fromString('farmland'): [
		MOISTURE_1, 
	], ResourceLocation.fromString('jigsaw'): [
		ORIENTATION_1, 
	], ResourceLocation.fromString('sea_pickle'): [
		PICKLES_1, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('heavy_weighted_pressure_plate'): [
		POWER_1, 
	], ResourceLocation.fromString('light_weighted_pressure_plate'): [
		POWER_1, 
	], ResourceLocation.fromString('stone_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('spruce_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('jungle_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('warped_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('activator_rail'): [
		POWERED_1, 
		SHAPE_1, 
	], ResourceLocation.fromString('acacia_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('polished_blackstone_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('detector_rail'): [
		POWERED_1, 
		SHAPE_1, 
	], ResourceLocation.fromString('powered_rail'): [
		POWERED_1, 
		SHAPE_1, 
	], ResourceLocation.fromString('oak_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('birch_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('dark_oak_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('crimson_pressure_plate'): [
		POWERED_1, 
	], ResourceLocation.fromString('rail'): [
		SHAPE_3, 
	], ResourceLocation.fromString('mycelium'): [
		SNOWY_1, 
	], ResourceLocation.fromString('grass_block'): [
		SNOWY_1, 
	], ResourceLocation.fromString('podzol'): [
		SNOWY_1, 
	], ResourceLocation.fromString('bamboo_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('dark_oak_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('birch_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('oak_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('acacia_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('spruce_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('jungle_sapling'): [
		STAGE_1, 
	], ResourceLocation.fromString('mossy_cobblestone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cut_red_sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('purpur_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dark_oak_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('stone_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('mossy_stone_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('exposed_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('red_nether_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('blackstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cobblestone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('deepslate_tile_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('smooth_red_sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('smooth_stone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('granite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('deepslate_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('waxed_weathered_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('diorite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('nether_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('prismarine_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('acacia_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('smooth_sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_blackstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('smooth_quartz_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('weathered_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('waxed_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('red_sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cut_sandstone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('quartz_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_andesite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dark_prismarine_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('waxed_oxidized_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('cobbled_deepslate_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('andesite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('waxed_exposed_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_blackstone_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('oxidized_cut_copper_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('prismarine_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('oak_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('stone_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('birch_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('jungle_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_deepslate_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('spruce_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_diorite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('polished_granite_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('end_stone_brick_slab'): [
		TYPE_3, 
		WATERLOGGED_1, 
	], ResourceLocation.fromString('tnt'): [
		UNSTABLE_1, 
	], ResourceLocation.fromString('tube_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_horn_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_bubble_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('bubble_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('horn_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_fire_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_tube_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_horn_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('fire_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_fire_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_tube_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('horn_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brain_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('conduit'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_bubble_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('fire_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('bubble_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_brain_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('tube_coral'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('brain_coral_fan'): [
		WATERLOGGED_1, 
	], ResourceLocation.fromString('dead_brain_coral_fan'): [
		WATERLOGGED_1, 
	],
}


BLOCK_STATES_DICT_BY_BLOCK: dict[ResourceLocation, dict[str, FilterArgumentInfo]] = {
	block: {
		fai.name: fai
		for fai in fais
	}
	for block, fais in BLOCK_STATES_BY_BLOCK.items()
}


def getBlockStatesDict(blockID: ResourceLocation) -> dict:
	arguments = BLOCK_STATES_DICT_BY_BLOCK.get(blockID)
	if arguments is None:
		arguments = {}
	return arguments


def parseBlockStates(sr: StringReader, blockID: ResourceLocation, *, errorsIO: list[CommandSyntaxError]) -> Optional[FilterArguments]:
	arguments = getBlockStatesDict(blockID)
	return parseFilterArgs(sr, arguments, errorsIO=errorsIO)


if __name__ == '__main__':
	print("checking blockstes for invalid block IDs:")
	allGood = True
	for block in BLOCK_STATES_BY_BLOCK:
		if block not in BLOCKS:
			allGood = False
			print(f"  unknown block: {block.asString}")
	if allGood:
		print("  all good.")
