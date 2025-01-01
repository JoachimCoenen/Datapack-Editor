"""
for Minecraft version 1.17
"""
from dataclasses import replace

from base.model.parsing.bytesUtils import strToBytes
from cat.utils.collections_ import FrozenDict
from corePlugins.minecraft_data.customData import CustomMCData, Gamerule, buildGamerulesDict, EntityVariants
from corePlugins.minecraft_data.resourceLocation import ResourceLocation

_VERSION_1_17_0 = CustomMCData(
	name='1.17',
	datapackVersion='7',
	# compiled from the Minecraft wiki:
	fluids=frozenset({
		ResourceLocation.fromString('empty'),
		ResourceLocation.fromString('flowing_lava'),
		ResourceLocation.fromString('flowing_water'),
		ResourceLocation.fromString('lava'),
		ResourceLocation.fromString('water'),
	}),
	# compiled from the Minecraft wiki:
	potions=frozenset({
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
	}),
	# compiled from the Minecraft wiki:
	dimensions=frozenset({
		ResourceLocation.fromString('overworld'),
		ResourceLocation.fromString('the_nether'),
		ResourceLocation.fromString('the_end'),
	}),
	# compiled from the Minecraft wiki:
	predicateConditions=frozenset({
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
	}),
	# compiled from the Minecraft wiki:
	gameEvents=frozenset(),  # only added in 1.19, so there's nothing here in 1.17
	# compiled from the Minecraft wiki:
	structures=frozenset({
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
	}),
	pointOfInterestTypes=frozenset(),  # empty. because support for 1.18 will be dropped soon.
	damageTypes=frozenset(),  # empty. because support for 1.18 will be dropped soon.
	# compiled from the 1.20.2.jar using this command "javap -constants -c  buj.class":
	itemComponents=frozenset(),  # empty. because introduced in 1.20.5.
	itemSubPredicates=frozenset(),  # empty. because introduced in 1.20.5.
	statisticTypes=frozenset({
		ResourceLocation.fromString('custom'),
		ResourceLocation.fromString('crafted'),
		ResourceLocation.fromString('used'),
		ResourceLocation.fromString('broken'),
		ResourceLocation.fromString('mined'),
		ResourceLocation.fromString('killed'),
		ResourceLocation.fromString('picked_up'),
		ResourceLocation.fromString('dropped'),
		ResourceLocation.fromString('killed_by'),
	}),
	entityVariants=EntityVariants(
		axolotl=frozenset({
			ResourceLocation.fromString('lucy'),
			ResourceLocation.fromString('wild'),
			ResourceLocation.fromString('gold'),
			ResourceLocation.fromString('cyan'),
			ResourceLocation.fromString('blue'),
		}),
		boat=frozenset({
			ResourceLocation.fromString('oak'),
			ResourceLocation.fromString('spruce'),
			ResourceLocation.fromString('birch'),
			ResourceLocation.fromString('jungle'),
			ResourceLocation.fromString('acacia'),
			ResourceLocation.fromString('dark_oak'),
			# ResourceLocation.fromString('mangrove'),  # 1.19
			# ResourceLocation.fromString('bamboo'),  # 1.20
			# ResourceLocation.fromString('cherry'),  # 1.20
		}),
		cat=frozenset({
			ResourceLocation.fromString('white'),
			ResourceLocation.fromString('black'),
			ResourceLocation.fromString('red'),
			ResourceLocation.fromString('siamese'),
			ResourceLocation.fromString('british_shorthair'),
			ResourceLocation.fromString('calico'),
			ResourceLocation.fromString('persian'),
			ResourceLocation.fromString('ragdoll'),
			ResourceLocation.fromString('tabby'),
			ResourceLocation.fromString('all_black'),
			ResourceLocation.fromString('jellie'),
		}),
		fox=frozenset({
			ResourceLocation.fromString('red'),
			ResourceLocation.fromString('snow'),
		}),
		frog=frozenset({
			ResourceLocation.fromString('temperate'),
			ResourceLocation.fromString('warm'),
			ResourceLocation.fromString('cold'),
		}),
		horse=frozenset({
			ResourceLocation.fromString('white'),
			ResourceLocation.fromString('creamy'),
			ResourceLocation.fromString('chestnut'),
			ResourceLocation.fromString('brown'),
			ResourceLocation.fromString('black'),
			ResourceLocation.fromString('gray'),
			ResourceLocation.fromString('darkbrown'),
		}),
		llama=frozenset({
			ResourceLocation.fromString('creamy'),
			ResourceLocation.fromString('white'),
			ResourceLocation.fromString('brown'),
			ResourceLocation.fromString('gray'),
		}),
		mooshroom=frozenset({
			ResourceLocation.fromString('red'),
			ResourceLocation.fromString('brown'),
		}),
		painting=frozenset({
			ResourceLocation.fromString('kebab'),
			ResourceLocation.fromString('aztec'),
			ResourceLocation.fromString('alban'),
			ResourceLocation.fromString('aztec2'),
			ResourceLocation.fromString('bomb'),
			ResourceLocation.fromString('plant'),
			ResourceLocation.fromString('wasteland'),
			ResourceLocation.fromString('meditative'),
			ResourceLocation.fromString('wanderer'),
			ResourceLocation.fromString('graham'),
			ResourceLocation.fromString('prairie_ride'),
			ResourceLocation.fromString('pool'),
			ResourceLocation.fromString('courbet'),
			ResourceLocation.fromString('sunset'),
			ResourceLocation.fromString('sea'),
			ResourceLocation.fromString('creebet'),
			ResourceLocation.fromString('match'),
			ResourceLocation.fromString('bust'),
			ResourceLocation.fromString('stage'),
			ResourceLocation.fromString('void'),
			ResourceLocation.fromString('skull_and_roses'),
			ResourceLocation.fromString('wither'),
			ResourceLocation.fromString('baroque'),
			ResourceLocation.fromString('humble'),
			ResourceLocation.fromString('bouquet'),
			ResourceLocation.fromString('cavebird'),
			ResourceLocation.fromString('cotan'),
			ResourceLocation.fromString('endboss'),
			ResourceLocation.fromString('fern'),
			ResourceLocation.fromString('owlemons'),
			ResourceLocation.fromString('sunflowers'),
			ResourceLocation.fromString('tides'),
			ResourceLocation.fromString('backyard'),
			ResourceLocation.fromString('pond'),
			ResourceLocation.fromString('fighters'),
			ResourceLocation.fromString('changing'),
			ResourceLocation.fromString('finding'),
			ResourceLocation.fromString('lowmist'),
			ResourceLocation.fromString('passage'),
			ResourceLocation.fromString('skeleton'),
			ResourceLocation.fromString('donkey_kong'),
			ResourceLocation.fromString('pointer'),
			ResourceLocation.fromString('pigscene'),
			ResourceLocation.fromString('burning_skull'),
			ResourceLocation.fromString('orb'),
			ResourceLocation.fromString('unpacked'),

			# ResourceLocation.fromString('earth'),  # 1.19
			# ResourceLocation.fromString('wind'),  # 1.19
			# ResourceLocation.fromString('fire'),  # 1.19
			# ResourceLocation.fromString('water'),  # 1.19
		}),
		parrot=frozenset({
			ResourceLocation.fromString('red_blue'),
			ResourceLocation.fromString('blue'),
			ResourceLocation.fromString('green'),
			ResourceLocation.fromString('yellow_blue'),
			ResourceLocation.fromString('gray'),
		}),
		rabbit=frozenset({
			ResourceLocation.fromString('brown'),
			ResourceLocation.fromString('white'),
			ResourceLocation.fromString('black'),
			ResourceLocation.fromString('white_splotched'),
			ResourceLocation.fromString('gold'),
			ResourceLocation.fromString('salt'),
			ResourceLocation.fromString('evil'),
		}),
		salmon=frozenset({
			ResourceLocation.fromString('small'),
			ResourceLocation.fromString('medium'),
			ResourceLocation.fromString('large'),
		}),
		tropical_fish=frozenset({
			ResourceLocation.fromString('flopper'),
			ResourceLocation.fromString('glitter'),
			ResourceLocation.fromString('betty'),
			ResourceLocation.fromString('stripey'),
			ResourceLocation.fromString('blockfish'),
			ResourceLocation.fromString('clayfish'),
			ResourceLocation.fromString('kob'),
			ResourceLocation.fromString('snooper'),
			ResourceLocation.fromString('brinely'),
			ResourceLocation.fromString('sunstreak'),
			ResourceLocation.fromString('dasher'),
			ResourceLocation.fromString('spotty'),
		}),
		villager=frozenset({
			ResourceLocation.fromString('desert'),
			ResourceLocation.fromString('jungle'),
			ResourceLocation.fromString('plains'),
			ResourceLocation.fromString('savanna'),
			ResourceLocation.fromString('snow'),
			ResourceLocation.fromString('swamp'),
			ResourceLocation.fromString('taiga'),
		}),
	),
	# compiled from the Minecraft wiki:
	slots=FrozenDict({
		b'armor': frozenset({b'chest', b'feet', b'head', b'legs'}),
		b'weapon': frozenset({None, b'mainhand', b'offhand'}),
		b'container': frozenset({strToBytes(f'{sn}')  for sn in range(0, 53 + 1)}),  # 0-53 	0-53
		b'enderchest': frozenset({strToBytes(f'{sn}') for sn in range(0, 26 + 1)}),  # 0-26 	200-226
		b'hotbar': frozenset({strToBytes(f'{sn}')     for sn in range(0, 8 + 1)}),   # 0-8 	    0-8
		b'inventory': frozenset({strToBytes(f'{sn}')  for sn in range(0, 26 + 1)}),  # 0-26 	9-35
		b'horse': frozenset({b'saddle', b'chest', b'armor'} | {strToBytes(f'{sn}') for sn in range(0, 14 + 1)}),  # 0-14 	500-514
		b'villager': frozenset({strToBytes(f'{sn}') for sn in range(0, 7 + 1)}),   # 0-7 	300-307
	}),
	gamerules=buildGamerulesDict([
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
	]),
)


_VERSION_1_17_1 = replace(_VERSION_1_17_0, name='1.17.1')


ALL_VERSIONS: list[CustomMCData] = [_VERSION_1_17_0, _VERSION_1_17_1]