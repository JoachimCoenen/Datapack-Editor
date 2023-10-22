"""
for Minecraft version 1.17
"""
from typing import AbstractSet, Mapping, Optional

from corePlugins.minecraft_data.customData import Gamerule
from corePlugins.minecraft_data.resourceLocation import ResourceLocation

from . import v1_20_2

NAMES: list[str] = ['1.20.3']


DATAPACK_VERSION: str = '21'


# compiled from the Minecraft wiki:
FLUIDS: AbstractSet[ResourceLocation] = v1_20_2.FLUIDS


# compiled from the Minecraft wiki:
POTIONS: AbstractSet[ResourceLocation] = v1_20_2.POTIONS


# compiled from the Minecraft wiki:
DIMENSIONS: AbstractSet[ResourceLocation] = v1_20_2.DIMENSIONS


# compiled from the Minecraft wiki:
PREDICATE_CONDITIONS: AbstractSet[ResourceLocation] = v1_20_2.PREDICATE_CONDITIONS


# compiled from the 1.20.2.jar using this command "javap -constants -c  djt.class":
GAME_EVENTS: AbstractSet[ResourceLocation] = v1_20_2.GAME_EVENTS


# compiled from the 1.20.2.jar using this command "javap -constants -c  dvc.class":
STRUCTURES: AbstractSet[ResourceLocation] = v1_20_2.STRUCTURES


# compiled from the Minecraft wiki:
SLOTS: Mapping[bytes, Optional[int]] = v1_20_2.SLOTS


# compiled from the Minecraft wiki:
GAMERULES = [
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
		name='maxCommandForkCount',
		description="The maximum number of forks (contexts) that can be created during one tick. Applies to command blocks and functions.",
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
		name='playersSleepingPercentage',
		description="What percentage of players in the Overworld must sleep to skip the night. A percentage value of 0 or less will allow the night to be skipped by just 1 player, and a percentage value more than 100 will prevent players from ever skipping the night.",
		type='brigadier:integer',
		defaultValue='100',
	),
	Gamerule(
		name='projectilesCanBreakBlocks',
		description="Whether impact projectiles will destroy blocks that are destructible by them, i.e. chorus flowers, pointed dripstone and decorated pots.",
		type='brigadier:bool',
		defaultValue='True',
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
]