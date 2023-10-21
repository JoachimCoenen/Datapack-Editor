"""
for Minecraft version 1.17
"""
from typing import AbstractSet, Mapping

from cat.utils.collections_ import FrozenDict
from corePlugins.minecraft_data.customData import Gamerule
from corePlugins.minecraft_data.resourceLocation import ResourceLocation
from base.model.parsing.bytesUtils import strToBytes


NAMES: list[str] = ['1.17', '1.17.1']


DATAPACK_VERSION: str = '7'


# compiled from the Minecraft wiki:
FLUIDS: AbstractSet[ResourceLocation] = {
	ResourceLocation.fromString('empty'),
	ResourceLocation.fromString('flowing_lava'),
	ResourceLocation.fromString('flowing_water'),
	ResourceLocation.fromString('lava'),
	ResourceLocation.fromString('water'),
}


# compiled from the Minecraft wiki:
POTIONS: AbstractSet[ResourceLocation] = frozenset({
	ResourceLocation.fromString('water'),
	ResourceLocation.fromString('mundane'),
	ResourceLocation.fromString('thick'),
	ResourceLocation.fromString('awkward'),
	ResourceLocation.fromString('night_vision'),
	ResourceLocation.fromString('long_night_vision'),
	ResourceLocation.fromString('invisibility'),
	ResourceLocation.fromString('long_invisibility'),
	ResourceLocation.fromString('leaping'),
	ResourceLocation.fromString('strong_leaping'),
	ResourceLocation.fromString('long_leaping'),
	ResourceLocation.fromString('fire_resistance'),
	ResourceLocation.fromString('long_fire_resistance'),
	ResourceLocation.fromString('swiftness'),
	ResourceLocation.fromString('strong_swiftness'),
	ResourceLocation.fromString('long_swiftness'),
	ResourceLocation.fromString('slowness'),
	ResourceLocation.fromString('strong_slowness'),
	ResourceLocation.fromString('long_slowness'),
	ResourceLocation.fromString('water_breathing'),
	ResourceLocation.fromString('long_water_breathing'),
	ResourceLocation.fromString('healing'),
	ResourceLocation.fromString('strong_healing'),
	ResourceLocation.fromString('harming'),
	ResourceLocation.fromString('strong_harming'),
	ResourceLocation.fromString('poison'),
	ResourceLocation.fromString('strong_poison'),
	ResourceLocation.fromString('long_poison'),
	ResourceLocation.fromString('regeneration'),
	ResourceLocation.fromString('strong_regeneration'),
	ResourceLocation.fromString('long_regeneration'),
	ResourceLocation.fromString('strength'),
	ResourceLocation.fromString('strong_strength'),
	ResourceLocation.fromString('long_strength'),
	ResourceLocation.fromString('weakness'),
	ResourceLocation.fromString('long_weakness'),
	ResourceLocation.fromString('luck'),
	ResourceLocation.fromString('turtle_master'),
	ResourceLocation.fromString('strong_turtle_master'),
	ResourceLocation.fromString('long_turtle_master'),
	ResourceLocation.fromString('slow_falling'),
	ResourceLocation.fromString('long_slow_falling'),
})


# compiled from the Minecraft wiki:
DIMENSIONS: AbstractSet[ResourceLocation] = frozenset({
	ResourceLocation.fromString('overworld'),
	ResourceLocation.fromString('the_nether'),
	ResourceLocation.fromString('the_end'),
})


# compiled from the Minecraft wiki:
PREDICATE_CONDITIONS: AbstractSet[ResourceLocation] = frozenset({
	ResourceLocation.fromString('inverted'),
	ResourceLocation.fromString('alternative'),
	ResourceLocation.fromString('random_chance'),
	ResourceLocation.fromString('random_chance_with_looting'),
	ResourceLocation.fromString('entity_properties'),
	ResourceLocation.fromString('killed_by_player'),
	ResourceLocation.fromString('entity_scores'),
	ResourceLocation.fromString('block_state_property'),
	ResourceLocation.fromString('match_tool'),
	ResourceLocation.fromString('table_bonus'),
	ResourceLocation.fromString('survives_explosion'),
	ResourceLocation.fromString('damage_source_properties'),
	ResourceLocation.fromString('location_check'),
	ResourceLocation.fromString('weather_check'),
	ResourceLocation.fromString('reference'),
	ResourceLocation.fromString('time_check'),
	ResourceLocation.fromString('value_check'),
})


# compiled from the Minecraft wiki:
GAME_EVENTS: AbstractSet[ResourceLocation] = frozenset()  # only added in 1.19, so there's nothing here in 1.17


# compiled from the Minecraft wiki:
STRUCTURES: AbstractSet[ResourceLocation] = frozenset({
	ResourceLocation.fromString('jungle_pyramid'),
	ResourceLocation.fromString('village'),
	ResourceLocation.fromString('endcity'),
	ResourceLocation.fromString('ruined_portal'),
	ResourceLocation.fromString('igloo'),
	ResourceLocation.fromString('stronghold'),
	ResourceLocation.fromString('bastion_remnant'),
	ResourceLocation.fromString('desert_pyramid'),
	ResourceLocation.fromString('nether_fossil'),
	ResourceLocation.fromString('buried_treasure'),
	ResourceLocation.fromString('mansion'),
	ResourceLocation.fromString('shipwreck'),
	ResourceLocation.fromString('monument'),
	ResourceLocation.fromString('swamp_hut'),
	ResourceLocation.fromString('fortress'),
	ResourceLocation.fromString('pillager_outpost'),
	ResourceLocation.fromString('ocean_ruin'),
	ResourceLocation.fromString('mineshaft'),
})

# compiled from the Minecraft wiki:
SLOTS: Mapping[bytes, int] = FrozenDict({
	b'armor.chest':     102,
	b'armor.feet':      100,
	b'armor.head':      103,
	b'armor.legs':      101,
	b'weapon':           98,
	b'weapon.mainhand':  98,
	b'weapon.offhand':   99,
	**{b'container.' + strToBytes(f'{sn}'):    0 + sn for sn in range(0, 53 + 1)},  # 0-53 	0-53
	**{b'enderchest.' + strToBytes(f'{sn}'): 200 + sn for sn in range(0, 26 + 1)},  # 0-26 	200-226
	**{b'hotbar.' + strToBytes(f'{sn}'):       0 + sn for sn in range(0, 8 + 1)},   # 0-8 	0-8
	**{b'inventory.' + strToBytes(f'{sn}'):    9 + sn for sn in range(0, 26 + 1)},  # 0-26 	9-35
	b'horse.saddle':    400,
	b'horse.chest':     499,
	b'horse.armor':     401,
	**{b'horse.' + strToBytes(f'{sn}'):      500 + sn for sn in range(0, 14 + 1)},  # 0-14 	500-514
	**{b'villager.' + strToBytes(f'{sn}'):   300 + sn for sn in range(0, 7 + 1)},   # 0-7 	300-307
})


GAMERULES = [
	Gamerule(
		name='announceAdvancements',
		description="Whether advancements should be announced in chat",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='commandBlockOutput',
		description="Whether command blocks should notify admins when they perform commands",
		type='brigadier:bool',
		defaultValue='true',
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
		description="Whether the daylight cycle and moon phases progress",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doEntityDrops',
		description="Whether entities that are not mobs should have drops",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doFireTick',
		description="Whether fire should spread and naturally extinguish",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doInsomnia',
		description="Whether phantoms can spawn in the nighttime",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doImmediateRespawn',
		description="Players respawn immediately without showing the death screen",
		type='brigadier:bool',
		defaultValue='false',
	),
	Gamerule(
		name='doLimitedCrafting',
		description="Whether players should be able to craft only those recipes that they've unlocked first",
		type='brigadier:bool',
		defaultValue='false',
	),
	Gamerule(
		name='doMobLoot',
		description="Whether mobs should drop items and experience orbs",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doMobSpawning',
		description="Whether mobs should naturally spawn. Does not affect monster spawners.",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doPatrolSpawning',
		description="Whether patrols can spawn",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doTileDrops',
		description="Whether blocks should have drops",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doTraderSpawning',
		description="Whether wandering traders can spawn",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='doWeatherCycle',
		description="Whether the weather can change naturally. The /weather command can still change weather.",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='drowningDamage',
		description="Whether the player should take damage when drowning",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='fallDamage',
		description="Whether the player should take fall damage",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='fireDamage',
		description="Whether the player should take damage in fire, lava, campfires, or on magma blocks‌[Java Edition only][1].",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='forgiveDeadPlayers',
		description="Makes angered neutral mobs stop being angry when the targeted player dies nearby",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='freezeDamage',
		description="Whether the player should take damage when inside powder snow",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='keepInventory',
		description="Whether the player should keep items and experience in their inventory after death",
		type='brigadier:bool',
		defaultValue='false',
	),
	Gamerule(
		name='logAdminCommands',
		description="Whether to log admin commands to server log",
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
		description="The maximum number of pushable entities a mob or player can push, before taking 3♥♥ suffocation damage per half-second. Setting to 0 or lower disables the rule. Damage affects survival-mode or adventure-mode players, and all mobs but bats. Pushable entities include non-spectator-mode players, any mob except bats, as well as boats and minecarts.",
		type='brigadier:integer',
		defaultValue='24',
	),
	Gamerule(
		name='mobGriefing',
		description="Whether creepers, zombies, endermen, ghasts, withers, ender dragons, rabbits, sheep, villagers, silverfish, snow golems, and end crystals should be able to change blocks and whether mobs can pick up items, which also disables bartering. This also affects the capability of zombie-like creatures like zombified piglins and drowned to pathfind to turtle eggs.",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='naturalRegeneration',
		description="Whether the player can regenerate health naturally if their hunger is full enough (doesn't affect external healing, such as golden apples, the Regeneration effect, etc.)",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='playersSleepingPercentage',
		description="What percentage of players must sleep to skip the night.",
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
		description="Whether the debug screen shows all or reduced information; and whether the effects of F3 + B (entity hitboxes) and F3 + G (chunk boundaries) are shown.",
		type='brigadier:bool',
		defaultValue='false',
	),
	Gamerule(
		name='sendCommandFeedback',
		description="Whether the feedback from commands executed by a player should show up in chat. Also affects the default behavior of whether command blocks store their output text",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='showDeathMessages',
		description="Whether death messages are put into chat when a player dies. Also affects whether a message is sent to the pet's owner when the pet dies.",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='spawnRadius',
		description="The number of blocks outward from the world spawn coordinates that a player spawns in when first joining a server or when dying without a personal spawnpoint.",
		type='brigadier:integer',
		defaultValue='10',
	),
	Gamerule(
		name='spectatorsGenerateChunks',
		description="Whether players in spectator mode can generate chunks",
		type='brigadier:bool',
		defaultValue='true',
	),
	Gamerule(
		name='universalAnger',
		description="Makes angered neutral mobs attack any nearby player, not just the player that angered them. Works best if forgiveDeadPlayers is disabled.",
		type='brigadier:bool',
		defaultValue='false',
	),

]
