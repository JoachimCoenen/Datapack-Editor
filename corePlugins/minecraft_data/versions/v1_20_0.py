"""
for Minecraft version 1.20 - 1.20.4
"""
from dataclasses import replace

from cat.utils.collections_ import FrozenDict
from corePlugins.minecraft_data.customData import CustomMCData, Gamerule, buildGamerulesDict
from corePlugins.minecraft_data.resourceLocation import ResourceLocation
from base.model.parsing.bytesUtils import strToBytes
from . import v1_18_0


_VERSION_1_18_X = v1_18_0.ALL_VERSIONS[-1]


_VERSION_1_20_0 = replace(
	_VERSION_1_18_X, 
	name='1.20',
	datapackVersion='15',
	# compiled from the Minecraft wiki:
	predicateConditions=_VERSION_1_18_X.predicateConditions
						- {ResourceLocation.fromString('alternative')}
						| {ResourceLocation.fromString('any_of')}
						| {ResourceLocation.fromString('all_of')},
	# compiled from the 1.20.2.jar using this command "javap -constants -c  djt.class":
	gameEvents=frozenset({
		ResourceLocation.fromString("block_activate"),
		ResourceLocation.fromString("block_attach"),
		ResourceLocation.fromString("block_change"),
		ResourceLocation.fromString("block_close"),
		ResourceLocation.fromString("block_deactivate"),
		ResourceLocation.fromString("block_destroy"),
		ResourceLocation.fromString("block_detach"),
		ResourceLocation.fromString("block_open"),
		ResourceLocation.fromString("block_place"),
		ResourceLocation.fromString("container_close"),
		ResourceLocation.fromString("container_open"),
		ResourceLocation.fromString("drink"),
		ResourceLocation.fromString("eat"),
		ResourceLocation.fromString("elytra_glide"),
		ResourceLocation.fromString("entity_damage"),
		ResourceLocation.fromString("entity_die"),
		ResourceLocation.fromString("entity_dismount"),
		ResourceLocation.fromString("entity_interact"),
		ResourceLocation.fromString("entity_mount"),
		ResourceLocation.fromString("entity_place"),
		ResourceLocation.fromString("entity_action"),
		ResourceLocation.fromString("equip"),
		ResourceLocation.fromString("explode"),
		ResourceLocation.fromString("flap"),
		ResourceLocation.fromString("fluid_pickup"),
		ResourceLocation.fromString("fluid_place"),
		ResourceLocation.fromString("hit_ground"),
		ResourceLocation.fromString("instrument_play"),
		ResourceLocation.fromString("item_interact_finish"),
		ResourceLocation.fromString("item_interact_start"),
		ResourceLocation.fromString("jukebox_play"),
		ResourceLocation.fromString("jukebox_stop_play"),
		ResourceLocation.fromString("lightning_strike"),
		ResourceLocation.fromString("note_block_play"),
		ResourceLocation.fromString("prime_fuse"),
		ResourceLocation.fromString("projectile_land"),
		ResourceLocation.fromString("projectile_shoot"),
		ResourceLocation.fromString("sculk_sensor_tendrils_clicking"),
		ResourceLocation.fromString("shear"),
		ResourceLocation.fromString("shriek"),
		ResourceLocation.fromString("splash"),
		ResourceLocation.fromString("step"),
		ResourceLocation.fromString("swim"),
		ResourceLocation.fromString("teleport"),
		ResourceLocation.fromString("unequip"),
		ResourceLocation.fromString("resonate_1"),
		ResourceLocation.fromString("resonate_2"),
		ResourceLocation.fromString("resonate_3"),
		ResourceLocation.fromString("resonate_4"),
		ResourceLocation.fromString("resonate_5"),
		ResourceLocation.fromString("resonate_6"),
		ResourceLocation.fromString("resonate_7"),
		ResourceLocation.fromString("resonate_8"),
		ResourceLocation.fromString("resonate_9"),
		ResourceLocation.fromString("resonate_10"),
		ResourceLocation.fromString("resonate_11"),
		ResourceLocation.fromString("resonate_12"),
		ResourceLocation.fromString("resonate_13"),
		ResourceLocation.fromString("resonate_14"),
		ResourceLocation.fromString("resonate_15"),
	}),
	# compiled from the 1.20.2.jar using this command "javap -constants -c  dvc.class":
	structures=frozenset({
		ResourceLocation.fromString("pillager_outpost"),
		ResourceLocation.fromString("mineshaft"),
		ResourceLocation.fromString("mineshaft_mesa"),
		ResourceLocation.fromString("mansion"),
		ResourceLocation.fromString("jungle_pyramid"),
		ResourceLocation.fromString("desert_pyramid"),
		ResourceLocation.fromString("igloo"),
		ResourceLocation.fromString("shipwreck"),
		ResourceLocation.fromString("shipwreck_beached"),
		ResourceLocation.fromString("swamp_hut"),
		ResourceLocation.fromString("stronghold"),
		ResourceLocation.fromString("monument"),
		ResourceLocation.fromString("ocean_ruin_cold"),
		ResourceLocation.fromString("ocean_ruin_warm"),
		ResourceLocation.fromString("fortress"),
		ResourceLocation.fromString("nether_fossil"),
		ResourceLocation.fromString("end_city"),
		ResourceLocation.fromString("buried_treasure"),
		ResourceLocation.fromString("bastion_remnant"),
		ResourceLocation.fromString("village_plains"),
		ResourceLocation.fromString("village_desert"),
		ResourceLocation.fromString("village_savanna"),
		ResourceLocation.fromString("village_snowy"),
		ResourceLocation.fromString("village_taiga"),
		ResourceLocation.fromString("ruined_portal"),
		ResourceLocation.fromString("ruined_portal_desert"),
		ResourceLocation.fromString("ruined_portal_jungle"),
		ResourceLocation.fromString("ruined_portal_swamp"),
		ResourceLocation.fromString("ruined_portal_mountain"),
		ResourceLocation.fromString("ruined_portal_ocean"),
		ResourceLocation.fromString("ruined_portal_nether"),
		ResourceLocation.fromString("ancient_city"),
		ResourceLocation.fromString("trail_ruins"),
	}),
	# compiled from the 1.20.2.jar using this command "javap -constants -c  buj.class":
	pointOfInterestTypes=frozenset({
		ResourceLocation.fromString('armorer'),
		ResourceLocation.fromString('butcher'),
		ResourceLocation.fromString('cartographer'),
		ResourceLocation.fromString('cleric'),
		ResourceLocation.fromString('farmer'),
		ResourceLocation.fromString('fisherman'),
		ResourceLocation.fromString('fletcher'),
		ResourceLocation.fromString('leatherworker'),
		ResourceLocation.fromString('librarian'),
		ResourceLocation.fromString('mason'),
		ResourceLocation.fromString('shepherd'),
		ResourceLocation.fromString('toolsmith'),
		ResourceLocation.fromString('weaponsmith'),
		ResourceLocation.fromString('home'),
		ResourceLocation.fromString('meeting'),
		ResourceLocation.fromString('beehive'),
		ResourceLocation.fromString('bee_nest'),
		ResourceLocation.fromString('nether_portal'),
		ResourceLocation.fromString('lodestone'),
		ResourceLocation.fromString('lightning_rod'),
	}),
	# compiled from the 1.20.2.jar using this command "javap -constants -c  bhr.class":
	damageTypes=frozenset({
		ResourceLocation.fromString('in_fire'),
		ResourceLocation.fromString('lightning_bolt'),
		ResourceLocation.fromString('on_fire'),
		ResourceLocation.fromString('lava'),
		ResourceLocation.fromString('hot_floor'),
		ResourceLocation.fromString('in_wall'),
		ResourceLocation.fromString('cramming'),
		ResourceLocation.fromString('drown'),
		ResourceLocation.fromString('starve'),
		ResourceLocation.fromString('cactus'),
		ResourceLocation.fromString('fall'),
		ResourceLocation.fromString('fly_into_wall'),
		ResourceLocation.fromString('out_of_world'),
		ResourceLocation.fromString('generic'),
		ResourceLocation.fromString('magic'),
		ResourceLocation.fromString('wither'),
		ResourceLocation.fromString('dragon_breath'),
		ResourceLocation.fromString('dry_out'),
		ResourceLocation.fromString('sweet_berry_bush'),
		ResourceLocation.fromString('freeze'),
		ResourceLocation.fromString('stalagmite'),
		ResourceLocation.fromString('falling_block'),
		ResourceLocation.fromString('falling_anvil'),
		ResourceLocation.fromString('falling_stalactite'),
		ResourceLocation.fromString('sting'),
		ResourceLocation.fromString('mob_attack'),
		ResourceLocation.fromString('mob_attack_no_aggro'),
		ResourceLocation.fromString('player_attack'),
		ResourceLocation.fromString('arrow'),
		ResourceLocation.fromString('trident'),
		ResourceLocation.fromString('mob_projectile'),
		ResourceLocation.fromString('fireworks'),
		ResourceLocation.fromString('fireball'),
		ResourceLocation.fromString('unattributed_fireball'),
		ResourceLocation.fromString('wither_skull'),
		ResourceLocation.fromString('thrown'),
		ResourceLocation.fromString('indirect_magic'),
		ResourceLocation.fromString('thorns'),
		ResourceLocation.fromString('explosion'),
		ResourceLocation.fromString('player_explosion'),
		ResourceLocation.fromString('sonic_boom'),
		ResourceLocation.fromString('bad_respawn_point'),
		ResourceLocation.fromString('outside_border'),
		ResourceLocation.fromString('generic_kill'),
	}),
	# compiled from the Minecraft wiki:
	slots=FrozenDict({
		b'armor.chest':     102,
		b'armor.feet':      100,
		b'armor.head':      103,
		b'armor.legs':      101,
		b'weapon':          None, # ?????! it was 98,
		b'weapon.mainhand': None, # ?????! it was 98,
		b'weapon.offhand':  -106, # ?????! it was 99,
		**{b'container.' + strToBytes(f'{sn}'):    0 + sn for sn in range(0, 53 + 1)},  # 0-53 	0-53
		**{b'enderchest.' + strToBytes(f'{sn}'): 200 + sn for sn in range(0, 26 + 1)},  # 0-26 	200-226
		**{b'hotbar.' + strToBytes(f'{sn}'):       0 + sn for sn in range(0, 8 + 1)},   # 0-8 	0-8
		**{b'inventory.' + strToBytes(f'{sn}'):    9 + sn for sn in range(0, 26 + 1)},  # 0-26 	9-35
		b'horse.saddle':    400,
		b'horse.chest':     499,
		b'horse.armor':     401,
		**{b'horse.' + strToBytes(f'{sn}'):      500 + sn for sn in range(0, 14 + 1)},  # 0-14 	500-514
		**{b'villager.' + strToBytes(f'{sn}'):   300 + sn for sn in range(0, 7 + 1)},   # 0-7 	300-307
	}),
	# compiled from the Minecraft wiki:
	gamerules=buildGamerulesDict([
		Gamerule(
			name='announceAdvancements',
			description="Whether advancements should be announced in chat.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='blockExplosionDropDecay',
			description="Whether block loot is dropped by all blocks ({{cd|false}}) or randomly ({{cd|true}}) depending on how far the block is from the center of a block explosion (e.g. clicking a bed in dimensions other than the Overworld).",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='commandBlockOutput',
			description="Whether command blocks should notify admins when they perform commands.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='commandModificationBlockLimit',
			description="Controls the maximum number of blocks changed when using {{cmd|clone}}, {{cmd|fill}}, or {{cmd|fillbiome}}.",
			type='brigadier:integer',
			defaultValue='32768',
		),
		Gamerule(
			name='disableElytraMovementCheck',
			description="Whether the server should skip checking player speed when the player is wearing elytra. Often helps with jittering due to lag in multiplayer.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='disableRaids',
			description="Whether raids are disabled.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='doDaylightCycle',
			description="Whether the daylight cycle and moon phases progress.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doEntityDrops',
			description="Whether entities that are not mobs should have drops.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doFireTick',
			description="Whether fire should spread and naturally extinguish.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doInsomnia',
			description="Whether phantoms can spawn in the nighttime.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doImmediateRespawn',
			description="Players respawn immediately without showing the death screen.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='doLimitedCrafting',
			description="Whether players can craft only those recipes that they have unlocked.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='doMobLoot',
			description="Whether mobs should [[drops|drop items]] and experience orbs.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doMobSpawning',
			description="Whether mobs should [[Spawn#Spawn cycle|spawn naturally]], or via global spawning logic, such as for cats, phantoms, patrols, wandering traders, or zombie sieges. Does not affect special spawning attempts, like monster spawners, raids, or iron golems.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doPatrolSpawning',
			description="Whether patrols can spawn.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doTileDrops',
			description="Whether blocks should have drops.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doTraderSpawning',
			description="Whether wandering traders can spawn.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doVinesSpread',
			description="Whether vines can spread to other blocks. Cave vines, weeping vines, and twisting vines are not affected.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doWeatherCycle',
			description="Whether the weather can change naturally. The {{command|weather}} command can still change weather.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='doWardenSpawning',
			description="Whether wardens can spawn.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='drowningDamage',
			description="Whether the player should take damage when drowning.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='enderPearlsVanishOnDeath',
			description="Controls whether thrown ender pearls vanish when the player dies.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='fallDamage',
			description="Whether the player should take fall damage.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='fireDamage',
			description="Whether the player should take damage in fire, lava, campfires, or on magma blocks. ",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='forgiveDeadPlayers',
			description="Makes angered neutral mobs stop being angry when the targeted player dies nearby.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='freezeDamage',
			description="Whether the player should take damage when inside powder snow.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='globalSoundEvents',
			description="Whether certain sound events are heard by all players regardless of location.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='keepInventory',
			description="Whether the player should keep items and experience in their inventory after death.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='lavaSourceConversion',
			description="Whether new sources of lava are allowed to form.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='logAdminCommands',
			description="Whether to log admin commands to server log.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='maxCommandChainLength',
			description="The maximum length of a chain of commands that can be executed during one tick. Applies to command blocks and functions.",
			type='brigadier:integer',
			defaultValue='65536',
		),
		Gamerule(
			name='maxEntityCramming',
			description="The maximum number of pushable entities a mob or player can push, before taking {{hp|6}} entity cramming damage per half-second.  Setting to 0 or lower disables the rule.  Damage affects Survival-mode or Adventure-mode players, and all mobs but bats. Pushable entities include non-Spectator-mode players, any mob except bats, as well as boats and minecarts.",
			type='brigadier:integer',
			defaultValue='24',
		),
		Gamerule(
			name='mobExplosionDropDecay',
			description="Whether block loot is dropped by all blocks ({{cd|false}}) or randomly ({{cd|true}}) depending on how far the block is from the center of a mob explosion (e.g. Creeper explosion).",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='mobGriefing',
			description="Whether creepers, zombies, endermen, ghasts, withers, ender dragons, rabbits, sheep, villagers, silverfish, snow golems, and end crystals{{only|bedrock|short=1}} should be able to change blocks, and whether mobs can pick up items. When mobGriefing is disabled, piglins do not pick up gold ingots, but a player can still barter with them by {{ctrl|using}} the item on the mob. Similarly, villagers do not pick up food items but can still breed until they run out of any food already in their inventory. This also affects the capability of zombie-like creatures like zombified piglins and drowned to pathfind to turtle eggs.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='naturalRegeneration',
			description="Whether the player can regenerate health naturally if their hunger is full enough (doesn't affect external healing, such as golden apples, the [[Regeneration|Regeneration effect]], etc.).",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='playersSleepingPercentage',
			description="What percentage of players in the Overworld must sleep to skip the night. A percentage value of 0 or less will allow the night to be skipped by just 1 player, and a percentage value more than 100 will prevent players from ever skipping the night.",
			type='brigadier:integer',
			defaultValue='100',
		),
		Gamerule(
			name='randomTickSpeed',
			description="How often a random block tick occurs (such as plant growth, leaf decay, etc.) per chunk section per game tick. 0 and negative values disables random ticks, higher numbers increase random ticks. Setting to a high integer results in high speeds of decay and growth. Numbers over 4096 make plant growth or leaf decay instantaneous.",
			type='brigadier:integer',
			defaultValue='3',
		),
		Gamerule(
			name='reducedDebugInfo',
			description="Whether the debug screen shows all or reduced information; and whether the effects of {{key|F3+B}} (entity hitboxes) and {{key|F3+G}} (chunk boundaries) are shown.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='sendCommandFeedback',
			description="Whether the feedback from commands executed by a player should show up in chat. Also affects the default behavior of whether command blocks store their output text.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='showDeathMessages',
			description="Whether [[Health#Death messages|death messages]] are put into chat when a player dies. Also affects whether [[Health#Pet death messages|a message]] is sent to the pet's owner when the pet dies.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='snowAccumulationHeight',
			description="The maximum number of snow layers that can be accumulated on each block.",
			type='brigadier:integer',
			defaultValue='1',
		),
		Gamerule(
			name='spawnRadius',
			description="The number of blocks outward from the world spawn coordinates that a player spawns in when first joining a server or when dying without a personal spawnpoint. Has no effect on servers where the default game mode is Adventure.",
			type='brigadier:integer',
			defaultValue='10',
		),
		Gamerule(
			name='spectatorsGenerateChunks',
			description="Whether players in Spectator mode can generate chunks.",
			type='brigadier:bool',
			defaultValue='true',
		),
		Gamerule(
			name='tntExplosionDropDecay',
			description="Whether block loot is dropped by all blocks ({{cd|false}}) or randomly ({{cd|true}}) depending on how far the block is from the center of a TNT explosion.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='universalAnger',
			description="Makes angered neutral mobs attack any nearby player, not just the player that angered them. Works best if {{cd|forgiveDeadPlayers}} is disabled.",
			type='brigadier:bool',
			defaultValue='false',
		),
		Gamerule(
			name='waterSourceConversion',
			description="Whether new sources of water are allowed to form.",
			type='brigadier:bool',
			defaultValue='true',
		),
	]),
)


_VERSION_1_20_1 = replace(
	_VERSION_1_20_0,
	name='1.20.1'
)

_VERSION_1_20_2 = replace(
	_VERSION_1_20_1,
	name='1.20.2',
	datapackVersion='18'
)

_VERSION_1_20_3 = replace(
	_VERSION_1_20_2,
	name='1.20.3',
	datapackVersion='21',
	gamerules=_VERSION_1_20_2.gamerules | buildGamerulesDict([
		Gamerule(
			name='maxCommandForkCount',
			description="The maximum number of forks (contexts) that can be created during one tick. Applies to command blocks and functions.",
			type='brigadier:integer',
			defaultValue='65536',
		),
		Gamerule(
			name='playersNetherPortalCreativeDelay',
			description="Controls the time that a creative player needs to stand in a nether portal before changing dimensions.",
			type='brigadier:integer',
			defaultValue='1',
		),
		Gamerule(
			name='playersNetherPortalDefaultDelay',
			description="Controls the time that a non-creative player needs to stand in a nether portal before changing dimensions.",
			type='brigadier:integer',
			defaultValue='80',
		),
		Gamerule(
			name='projectilesCanBreakBlocks',
			description="Whether impact projectiles will destroy blocks that are destructible by them, i.e. chorus flowers, pointed dripstone and decorated pots.",
			type='brigadier:bool',
			defaultValue='True',
		),
	])
)


_VERSION_1_20_4 = replace(
	_VERSION_1_20_3,
	name='1.20.4'
)


ALL_VERSIONS: list[CustomMCData] = [_VERSION_1_20_0, _VERSION_1_20_1, _VERSION_1_20_2, _VERSION_1_20_3, _VERSION_1_20_4]
