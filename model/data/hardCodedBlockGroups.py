from model.datapackContents import ResourceLocation

_LOG_TYPES = [
	'oak',
	'spruce',
	'birch',
	'jungle',
	'acacia',
	'dark_oak',
]

_STEM_TYPES = [
	'crimson',
	'warped',
]

_COPPER_WAX = [
	'',
	'waxed_',
]

_COPPER_STATES = [
	'',
	'exposed_',
	'oxidized_',
	'weathered_',
]

_STONE_LIKE = [  # yikes...
	'cobblestone',
	'mossy_cobblestone',
	'stone_brick',
	'mossy_stone_brick',
	'andesite',
	'diorite',
	'granite',
	'sandstone',
	'red_sandstone',
	'brick',
	'prismarine',
	'nether_brick',
	'red_nether_brick',
	'end_stone_brick',
	'blackstone',
	'polished_blackstone',
	'polished_blackstone_brick',
	'cobbled_deepslate',
	'polished_deepslate',
	'deepslate_brick',
	'deepslate_tile',
]

_CUTTABLE_STAIRS = [  # these have stairs: (yikes...)
	*_LOG_TYPES,
	*_STEM_TYPES,
	*_STONE_LIKE,
	*(f'{c}cut_copper' for c in _COPPER_STATES),
	*(f'waxed_{c}cut_copper' for c in _COPPER_STATES),

	'dark_prismarine',
	'prismarine_brick',

	'polished_andesite',
	'polished_diorite',
	'polished_granite',
	'purpur',

	'quartz',
	'smooth_quartz',

	'smooth_red_sandstone',
	'smooth_sandstone',
	'stone',
]

_CUTTABLE_SLAB = [  # these have slabs: (yikes...)
	*_CUTTABLE_STAIRS,
	'smooth_stone',
	'cut_red_sandstone',
	'cut_sandstone',
]

_COLOR_PREFIXES = [
	'white',
	'orange',
	'magenta',
	'light_blue',
	'yellow',
	'lime',
	'pink',
	'gray',
	'light_gray',
	'cyan',
	'purple',
	'blue',
	'brown',
	'green',
	'red',
	'black',
]


ALL_LOGS = [  # (including all variants, wood, and stripped versions of both logs and wood)
	*(ResourceLocation.fromString(f'{c}_log') for c in _LOG_TYPES),
	*(ResourceLocation.fromString(f'stripped_{c}_log') for c in _LOG_TYPES),
	*(ResourceLocation.fromString(f'{c}_wood') for c in _LOG_TYPES),
	*(ResourceLocation.fromString(f'stripped_{c}_wood') for c in _LOG_TYPES),
]

ALL_STEMS = [  # (including all variants, hyphae, and stripped versions of both stems and hyphae)
	*(ResourceLocation.fromString(f'{c}_stem') for c in _STEM_TYPES),
	*(ResourceLocation.fromString(f'stripped_{c}_stem') for c in _STEM_TYPES),
	*(ResourceLocation.fromString(f'{c}_hyphae') for c in _STEM_TYPES),
	*(ResourceLocation.fromString(f'stripped_{c}_hyphae') for c in _STEM_TYPES),
]

ALL_FENCES = [  # (any, including nether brick)
	*(ResourceLocation.fromString(f'{c}_fence') for c in _LOG_TYPES + _STEM_TYPES),
	ResourceLocation.fromString('nether_brick_fence'),
]

ALL_GLASS_PANES = [  # (including all stained colors)
	ResourceLocation.fromString('glass_pane'),
	*(ResourceLocation.fromString(f'{c}_stained_glass_pane') for c in _COLOR_PREFIXES),
]

ALL_WALLS = [  # (any)
	*(ResourceLocation.fromString(f'{c}_wall') for c in _STONE_LIKE),
]

ALL_BUTTONS = [  # (any)
	ResourceLocation.fromString('stone_button'),
	ResourceLocation.fromString('polished_blackstone_button'),
	*(ResourceLocation.fromString(f'{c}_button') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_AMETHYST_CLUSTERS = [  # (any stage)
	ResourceLocation.fromString('small_amethyst_bud'),
	ResourceLocation.fromString('medium_amethyst_bud'),
	ResourceLocation.fromString('large_amethyst_bud'),
	ResourceLocation.fromString('amethyst_cluster'),
]

ALL_COMMAND_BLOCKS = [  # (any variant)
	ResourceLocation.fromString('command_block'),
	ResourceLocation.fromString('chain_command_block'),
	ResourceLocation.fromString('repeating_command_block'),
]

ALL_SHULKER_BOXES = [  # (any color)
	ResourceLocation.fromString('shulker_box'),
	*(ResourceLocation.fromString(f'{c}_shulker_box') for c in _COLOR_PREFIXES),
]

ALL_ANVILS = [  # (any durability)
	ResourceLocation.fromString('anvil'),
	ResourceLocation.fromString('chipped_anvil'),
	ResourceLocation.fromString('damaged_anvil'),
]

ALL_BANNERS = [  # (any wall variant)
	*(ResourceLocation.fromString(f'{c}_banner') for c in _COLOR_PREFIXES),
	*(ResourceLocation.fromString(f'{c}_wall_banner') for c in _COLOR_PREFIXES),
]

ALL_BEDS = [  # (any)
	*(ResourceLocation.fromString(f'{c}_bed') for c in _COLOR_PREFIXES),
]

_CORAL_TYPES = [
	'tube',
	'brain',
	'bubble',
	'fire',
	'horn',
]

ALL_CORAL_WALL_FANS = [  # (any variant, including dead)
	*(ResourceLocation.fromString(f'{c}_coral_wall_fan') for c in _CORAL_TYPES),
	*(ResourceLocation.fromString(f'dead_{c}_coral_wall_fan') for c in _CORAL_TYPES),
]

ALL_DOORS = [  # (any)
	ResourceLocation.fromString('iron_door'),
	*(ResourceLocation.fromString(f'{c}_door') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_FENCE_GATES = [  # (any)
	*(ResourceLocation.fromString(f'{c}_fence_gate') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_GLAZED_TERRACOTTAS = [  # (any color)
	*(ResourceLocation.fromString(f'{c}_glazed_terracotta') for c in _COLOR_PREFIXES),
]

ALL_MOB_HEADS = [  # (any)
	ResourceLocation.fromString('skeleton_skull'),
	ResourceLocation.fromString('wither_skeleton_skull'),
	ResourceLocation.fromString('zombie_head'),
	ResourceLocation.fromString('player_head'),
	ResourceLocation.fromString('creeper_head'),
	ResourceLocation.fromString('dragon_head'),
	ResourceLocation.fromString('skeleton_wall_skull'),
	ResourceLocation.fromString('wither_skeleton_wall_skull'),
	ResourceLocation.fromString('zombie_wall_head'),
	ResourceLocation.fromString('player_wall_head'),
	ResourceLocation.fromString('creeper_wall_head'),
	ResourceLocation.fromString('dragon_wall_head'),
]

ALL_SIGNS = [  # (any wall variant)
	*(ResourceLocation.fromString(f'{c}_sign') for c in _LOG_TYPES + _STEM_TYPES),
	*(ResourceLocation.fromString(f'{c}_wall_sign') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_STAIRS = [  # (any)
	# TODO: fix ALL_STAIRS!
	# *(ResourceLocation.fromString(f'{c}_stairs') for c in _LOG_TYPES + _STEM_TYPES),
	# *(ResourceLocation.fromString(f'{c}_stairs') for c in _STONE_LIKE),
	*(ResourceLocation.fromString(f'{c}_stairs') for c in _CUTTABLE_STAIRS),
]

ALL_TRAPDOORS = [  # (any, including iron)
	ResourceLocation.fromString('iron_trapdoor'),
	*(ResourceLocation.fromString(f'{c}_trapdoor') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_WEIGHTED_PRESSURE_PLATES = [  # (any non-weighted)
	ResourceLocation.fromString('light_weighted_pressure_plate'),
	ResourceLocation.fromString('heavy_weighted_pressure_plate'),
]

ALL_NON_WEIGHTED_PRESSURE_PLATES = [  # (any non-weighted)
	ResourceLocation.fromString('stone_pressure_plate'),
	ResourceLocation.fromString('polished_blackstone_pressure_plate'),
	*(ResourceLocation.fromString(f'{c}_pressure_plate') for c in _LOG_TYPES + _STEM_TYPES),
]

ALL_SAPLINGS = [  # (any, including bamboo sapling)
	*(ResourceLocation.fromString(f'{c}_sapling') for c in _LOG_TYPES),
	ResourceLocation.fromString('bamboo_sapling'),
	ResourceLocation.fromString('bamboo'),
]

ALL_SLABS = [  # (any)
	*(ResourceLocation.fromString(f'{c}_slab') for c in _CUTTABLE_SLAB),
]

ALL_CORALS = [  # (all non-block variants, including dead variants)
	*ALL_CORAL_WALL_FANS,
	*(ResourceLocation.fromString(f'{c}_coral_fan') for c in _CORAL_TYPES),
	*(ResourceLocation.fromString(f'dead_{c}_coral_fan') for c in _CORAL_TYPES),
	*(ResourceLocation.fromString(f'{c}_coral') for c in _CORAL_TYPES),
	*(ResourceLocation.fromString(f'dead_{c}_coral') for c in _CORAL_TYPES),
]

ALL_LEAVES = [
	*(ResourceLocation.fromString(f'{c}_leaves') for c in _LOG_TYPES),
	ResourceLocation.fromString('azalea_leaves'),
	ResourceLocation.fromString('flowering_azalea_leaves'),
]


__all__ = [
	'ALL_LOGS',
	'ALL_STEMS',
	'ALL_FENCES',
	'ALL_GLASS_PANES',
	'ALL_WALLS',
	'ALL_BUTTONS',
	'ALL_AMETHYST_CLUSTERS',
	'ALL_COMMAND_BLOCKS',
	'ALL_SHULKER_BOXES',
	'ALL_ANVILS',
	'ALL_BANNERS',
	'ALL_BEDS',
	'ALL_CORAL_WALL_FANS',
	'ALL_DOORS',
	'ALL_FENCE_GATES',
	'ALL_GLAZED_TERRACOTTAS',
	'ALL_MOB_HEADS',
	'ALL_SIGNS',
	'ALL_STAIRS',
	'ALL_TRAPDOORS',
	'ALL_WEIGHTED_PRESSURE_PLATES',
	'ALL_NON_WEIGHTED_PRESSURE_PLATES',
	'ALL_SAPLINGS',
	'ALL_SLABS',
	'ALL_CORALS',
	'ALL_LEAVES',
]