from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from model.commands.argumentTypes import BRIGADIER_BOOL, ArgumentType, BRIGADIER_INTEGER


@RegisterContainer
class Gamerule(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	description: str = Serialized(default='')
	type: ArgumentType = Serialized(default=BRIGADIER_BOOL)
	defaultValue: str = Serialized(default='')


GAMERULES = [
	Gamerule.create(
		name='announceAdvancements',
		description="Whether advancements should be announced in chat",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='commandBlockOutput',
		description="Whether command blocks should notify admins when they perform commands",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='disableElytraMovementCheck',
		description="Whether the server should skip checking player speed when the player is wearing elytra. Often helps with jittering due to lag in multiplayer.",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='disableRaids',
		description="Whether raids are disabled.",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='doDaylightCycle',
		description="Whether the daylight cycle and moon phases progress",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doEntityDrops',
		description="Whether entities that are not mobs should have drops",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doFireTick',
		description="Whether fire should spread and naturally extinguish",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doInsomnia',
		description="Whether phantoms can spawn in the nighttime",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doImmediateRespawn',
		description="Players respawn immediately without showing the death screen",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='doLimitedCrafting',
		description="Whether players should be able to craft only those recipes that they've unlocked first",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='doMobLoot',
		description="Whether mobs should drop items and experience orbs",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doMobSpawning',
		description="Whether mobs should naturally spawn. Does not affect monster spawners.",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doPatrolSpawning',
		description="Whether patrols can spawn",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doTileDrops',
		description="Whether blocks should have drops",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doTraderSpawning',
		description="Whether wandering traders can spawn",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='doWeatherCycle',
		description="Whether the weather can change naturally. The /weather command can still change weather.",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='drowningDamage',
		description="Whether the player should take damage when drowning",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='fallDamage',
		description="Whether the player should take fall damage",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='fireDamage',
		description="Whether the player should take damage in fire, lava, campfires, or on magma blocks‌[Java Edition only][1].",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='forgiveDeadPlayers',
		description="Makes angered neutral mobs stop being angry when the targeted player dies nearby",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='freezeDamage',
		description="Whether the player should take damage when inside powder snow",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='keepInventory',
		description="Whether the player should keep items and experience in their inventory after death",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='logAdminCommands',
		description="Whether to log admin commands to server log",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='maxCommandChainLength',
		description="The maximum length of a chain of commands that can be executed during one tick. Applies to command blocks and functions.",
		type=BRIGADIER_INTEGER,
		defaultValue='65536',
	),
	Gamerule.create(
		name='maxEntityCramming',
		description="The maximum number of pushable entities a mob or player can push, before taking 3♥♥ suffocation damage per half-second. Setting to 0 or lower disables the rule. Damage affects survival-mode or adventure-mode players, and all mobs but bats. Pushable entities include non-spectator-mode players, any mob except bats, as well as boats and minecarts.",
		type=BRIGADIER_INTEGER,
		defaultValue='24',
	),
	Gamerule.create(
		name='mobGriefing',
		description="Whether creepers, zombies, endermen, ghasts, withers, ender dragons, rabbits, sheep, villagers, silverfish, snow golems, and end crystals should be able to change blocks and whether mobs can pick up items, which also disables bartering. This also affects the capability of zombie-like creatures like zombified piglins and drowned to pathfind to turtle eggs.",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='naturalRegeneration',
		description="Whether the player can regenerate health naturally if their hunger is full enough (doesn't affect external healing, such as golden apples, the Regeneration effect, etc.)",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='playersSleepingPercentage',
		description="What percentage of players must sleep to skip the night.",
		type=BRIGADIER_INTEGER,
		defaultValue='100',
	),
	Gamerule.create(
		name='randomTickSpeed',
		description="How often a random block tick occurs (such as plant growth, leaf decay, etc.) per chunk section per game tick. 0 and negative values disables random ticks, higher numbers increase random ticks. Setting to a high integer results in high speeds of decay and growth. Numbers over 4096 make plant growth or leaf decay instantaneous.",
		type=BRIGADIER_INTEGER,
		defaultValue='3',
	),
	Gamerule.create(
		name='reducedDebugInfo',
		description="Whether the debug screen shows all or reduced information; and whether the effects of F3 + B (entity hitboxes) and F3 + G (chunk boundaries) are shown.",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),
	Gamerule.create(
		name='sendCommandFeedback',
		description="Whether the feedback from commands executed by a player should show up in chat. Also affects the default behavior of whether command blocks store their output text",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='showDeathMessages',
		description="Whether death messages are put into chat when a player dies. Also affects whether a message is sent to the pet's owner when the pet dies.",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='spawnRadius',
		description="The number of blocks outward from the world spawn coordinates that a player spawns in when first joining a server or when dying without a personal spawnpoint.",
		type=BRIGADIER_INTEGER,
		defaultValue='10',
	),
	Gamerule.create(
		name='spectatorsGenerateChunks',
		description="Whether players in spectator mode can generate chunks",
		type=BRIGADIER_BOOL,
		defaultValue='true',
	),
	Gamerule.create(
		name='universalAnger',
		description="Makes angered neutral mobs attack any nearby player, not just the player that angered them. Works best if forgiveDeadPlayers is disabled.",
		type=BRIGADIER_BOOL,
		defaultValue='false',
	),

]



