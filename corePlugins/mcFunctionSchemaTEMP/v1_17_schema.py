from copy import copy

from Cat.utils.collections_ import ChainedList
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import CommandSchema, KeywordSchema, ArgumentSchema, TERMINAL, COMMANDS_ROOT, SwitchSchema, MCFunctionSchema
from base.model.parsing.bytesUtils import strToBytes

from corePlugins.mcFunctionSchemaTEMP.mcVersions import MCVersion, getMCVersion


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_17 = getMCVersion('1.17')
	schema_1_17 = buildMCFunctionSchemaFor_v1_17(version1_17)
	return {'Minecraft 1.17': schema_1_17}


def buildMCFunctionSchemaFor_v1_17(version: MCVersion) -> MCFunctionSchema:

	_BASIC_COMMAND_INFO_LIST = [
		CommandSchema(
			name='?',
			description='An alias of /help. Provides help for commands.',
			opLevel=0,
		),
		CommandSchema(
			name='advancement',
			description='Gives, removes, or checks player advancements.',
			opLevel=2,
		),
		CommandSchema(
			name='attribute',
			description='Queries, adds, removes or sets an entity attribute.',
			opLevel=2,
		),
		CommandSchema(
			name='ban',
			description='Adds player to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='ban-ip',
			description='Adds IP address to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='banlist',
			description='Displays banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='bossbar',
			description='Creates and modifies bossbars.',
			opLevel=2,
		),
		CommandSchema(
			name='clear',
			description='Clears items from player inventory.',
			opLevel=2,
		),
		CommandSchema(
			name='clone',
			description='Copies blocks from one place to another.',
			opLevel=2,
		),
		CommandSchema(
			name='data',
			description='Gets, merges, modifies and removes block entity and entity NBT data.',
			opLevel=2,
		),
		CommandSchema(
			name='datapack',
			description='Controls loaded data packs.',
			opLevel=2,
		),
		CommandSchema(
			name='debug',
			description='Starts or stops a debugging session.',
			opLevel=3,
		),
		CommandSchema(
			name='defaultgamemode',
			description='Sets the default game mode.',
			opLevel=2,
		),
		CommandSchema(
			name='deop',
			description='Revokes operator status from a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='difficulty',
			description='Sets the difficulty level.',
			opLevel=2,
		),
		CommandSchema(
			name='effect',
			description='Add or remove status effects.',
			opLevel=2,
		),
		CommandSchema(
			name='enchant',
			description="Adds an enchantment to a player's selected item.",
			opLevel=2,
		),
		CommandSchema(
			name='execute',
			description='Executes another command.',
			opLevel=2,
		),
		CommandSchema(
			name='experience',
			description='An alias of /xp. Adds or removes player experience.',
			opLevel=2,
		),
		CommandSchema(
			name='fill',
			description='Fills a region with a specific block.',
			opLevel=2,
		),
		CommandSchema(
			name='forceload',
			description='Forces chunks to constantly be loaded or not.',
			opLevel=2,
		),
		CommandSchema(
			name='function',
			description='Runs a function.',
			opLevel=2,
		),
		CommandSchema(
			name='gamemode',
			description="Sets a player's game mode.",
			opLevel=2,
		),
		CommandSchema(
			name='gamerule',
			description='Sets or queries a game rule value.',
			opLevel=2,
		),
		CommandSchema(
			name='give',
			description='Gives an item to a player.',
			opLevel=2,
		),
		CommandSchema(
			name='help',
			description='An alias of /?. Provides help for commands.',
			opLevel=0,
		),
		CommandSchema(
			name='item',
			description='Manipulates items in inventories.',
			opLevel=2,
		),
		CommandSchema(
			name='kick',
			description='Kicks a player off a server.',
			opLevel=3,
		),
		CommandSchema(
			name='kill',
			description='Kills entities (players, mobs, items, etc.).',
			opLevel=2,
		),
		CommandSchema(
			name='list',
			description='Lists players on the server.',
			opLevel=0,
		),
		CommandSchema(
			name='locate',
			description='Locates closest structure.',
			opLevel=2,
		),
		CommandSchema(
			name='locatebiome',
			description='Locates closest biome.',
			opLevel=2,
		),
		CommandSchema(
			name='loot',
			description='Drops items from an inventory slot onto the ground.',
			opLevel=2,
		),
		CommandSchema(
			name='me',
			description='Displays a message about the sender.',
			opLevel=0,
		),
		CommandSchema(
			name='msg',
			description='An alias of /tell and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandSchema(
			name='op',
			description='Grants operator status to a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='pardon',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='pardon-ip',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='particle',
			description='Creates particles.',
			opLevel=2,
		),
		CommandSchema(
			name='perf',
			description='Captures info and metrics about the game for 10 seconds.',
			opLevel=4,
			availableInSP=False
		),
		CommandSchema(
			name='playsound',
			description='Plays a sound.',
			opLevel=2,
		),
		CommandSchema(
			name='publish',
			description='Opens single-player world to local network.',
			opLevel=4,
			availableInMP=False
		),
		CommandSchema(
			name='recipe',
			description='Gives or takes player recipes.',
			opLevel=2,
		),
		CommandSchema(
			name='reload',
			description='Reloads loot tables, advancements, and functions from disk.',
			opLevel=2,
		),
		CommandSchema(
			name='replaceitem',
			description='Replaces items in inventories.',
			removed=True,
			removedVersion='1.17',
			removedComment='Replaced with `/item replace`',
			opLevel=2,
		),
		CommandSchema(
			name='save-all',
			description='Saves the server to disk.',
			opLevel=4,
			availableInSP=False
		),
		CommandSchema(
			name='save-off',
			description='Disables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandSchema(
			name='save-on',
			description='Enables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandSchema(
			name='say',
			description='Displays a message to multiple players.',
			opLevel=2,
		),
		CommandSchema(
			name='schedule',
			description='Delays the execution of a function.',
			opLevel=2,
		),
		CommandSchema(
			name='scoreboard',
			description='Manages scoreboard objectives and players.',
			opLevel=2,
		),
		CommandSchema(
			name='seed',
			description='Displays the world seed.',
			opLevel='0 in singleplayer, 2 in multiplayer',
		),
		CommandSchema(
			name='setblock',
			description='Changes a block to another block.',
			opLevel=2,
		),
		CommandSchema(
			name='setidletimeout',
			description='Sets the time before idle players are kicked.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='setworldspawn',
			description='Sets the world spawn.',
			opLevel=2,
		),
		CommandSchema(
			name='spawnpoint',
			description='Sets the spawn point for a player.',
			opLevel=2,
		),
		CommandSchema(
			name='spectate',
			description='Make one player in spectator mode spectate an entity.',
			opLevel=2,
		),
		CommandSchema(
			name='spreadplayers',
			description='Teleports entities to random locations.',
			opLevel=2,
		),
		CommandSchema(
			name='stop',
			description='Stops a server.',
			opLevel=4,
			availableInSP=False
		),
		CommandSchema(
			name='stopsound',
			description='Stops a sound.',
			opLevel=2,
		),
		CommandSchema(
			name='summon',
			description='Summons an entity.',
			opLevel=2,
		),
		CommandSchema(
			name='tag',
			description='Controls entity tags.',
			opLevel=2,
		),
		CommandSchema(
			name='team',
			description='Controls teams.',
			opLevel=2,
		),
		CommandSchema(
			name='teammsg',
			description='An alias of /tm. Specifies the message to send to team.',
			opLevel=0,
		),
		CommandSchema(
			name='teleport',
			description='An alias of /tp. Teleports entities.',
			opLevel=2,
		),
		CommandSchema(
			name='tell',
			description='An alias of /msg and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandSchema(
			name='tellraw',
			description='Displays a JSON message to players.',
			opLevel=2,
		),
		CommandSchema(
			name='testfor',
			description='Counts entities matching specified conditions.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead', # TODO: removedComment for '/testfor' command
			opLevel=2,
		),
		CommandSchema(
			name='testforblock',
			description='Tests whether a block is in a location.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if block` instead',
			opLevel=2,
		),
		CommandSchema(
			name='testforblocks',
			description='Tests whether the blocks in two regions match.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead',
			opLevel=2,
		),
		CommandSchema(
			name='time',
			description="Changes or queries the world's game time.",
			opLevel=2,
		),
		CommandSchema(
			name='title',
			description='Manages screen titles.',
			opLevel=2,
		),
		CommandSchema(
			name='tm',
			description='An alias of /teammsg. Specifies the message to send to team.',
			opLevel=0,
		),
		# CommandSchema(
		# 	name='toggledownfall',
		# 	description='Toggles the weather.',
		# 	removed=True,
		# 	removedVersion='1.13',
		# 	removedComment='Use `/weather ...` instead',
		# 	opLevel=1,
		# ),
		CommandSchema(
			name='tp',
			description='An alias of /teleport. Teleports entities.',
			opLevel=2,
		),
		CommandSchema(
			name='trigger',
			description='Sets a trigger to be activated.',
			opLevel=0,
		),
		CommandSchema(
			name='w',
			description='An alias of /tell and /msg. Displays a private message to other players.',
			opLevel=0,
		),
		CommandSchema(
			name='weather',
			description='Sets the weather.',
			opLevel=2,
		),
		CommandSchema(
			name='whitelist',
			description='Manages server whitelist.',
			opLevel=3,
			availableInSP=False
		),
		CommandSchema(
			name='worldborder',
			description='Manages the world border.',
			opLevel=2,
		),
		CommandSchema(
			name='xp',
			description='An alias of /experience [Java Edition only]. Adds or removes player experience.',
			opLevel=2,
		)
	]

	BASIC_COMMAND_INFO: dict[bytes, CommandSchema] = {strToBytes(c.name): c for c in _BASIC_COMMAND_INFO_LIST}

	BASIC_COMMAND_INFO[b'?'].next = []

	BASIC_COMMAND_INFO[b'advancement'].next = [
		ArgumentSchema(
			name='__action',
			type=makeLiteralsArgumentType([b'grant', b'revoke']),
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						KeywordSchema(
							name='everything',
						),
						KeywordSchema(
							name='only',
							next=[
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
									next=[
										TERMINAL,
										ArgumentSchema(
											name='criterion',
											type=BRIGADIER_STRING,
										),
									]
								),
							]
						),
						KeywordSchema(
							name='from',
							next=[
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							]
						),
						KeywordSchema(
							name='through',
							next=[
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							]
						),
						KeywordSchema(
							name='until',
							next=[
								ArgumentSchema(
									name='advancement',
									type=DPE_ADVANCEMENT,
								),
							]
						),
					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO[b'attribute'].next = [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='attribute',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						KeywordSchema(
							name='get',
							next=[
								TERMINAL,
								ArgumentSchema(
									name='scale',
									type=BRIGADIER_DOUBLE,
								),
							]
						),
						KeywordSchema(
							name='base',
							next=[
								KeywordSchema(
									name='get',
									next=[
										TERMINAL,
										ArgumentSchema(
											name='scale',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
								KeywordSchema(
									name='set',
									next=[
										ArgumentSchema(
											name='value',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
							],
						),
						KeywordSchema(
							name='modifier',
							next=[
								KeywordSchema(
									name='add',
									next=[
										ArgumentSchema(
											name='uuid',
											type=MINECRAFT_UUID,
											next=[
												ArgumentSchema(
													name='name',
													type=BRIGADIER_STRING,
													next=[
														ArgumentSchema(
															name='value',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentSchema(
																	name='uuid',
																	type=makeLiteralsArgumentType([b'add', b'multiply', b'multiply_base']),
																),
															]
														),
													]
												),
											]
										),
									]
								),
								KeywordSchema(
									name='remove',
									next=[
										ArgumentSchema(
											name='uuid',
											type=MINECRAFT_UUID,
										),
									]
								),
								KeywordSchema(
									name='value',
									next=[
										KeywordSchema(
											name='get',
											next=[
												ArgumentSchema(
													name='uuid',
													type=MINECRAFT_UUID,
													next=[
														TERMINAL,
														ArgumentSchema(
															name='scale',
															type=BRIGADIER_DOUBLE,
														),
													]
												),
											]
										),
									]
								),
							],
						),

					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO[b'ban'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'ban-ip'].next = [
		ArgumentSchema(
			name='target',
			type=BRIGADIER_STRING,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'banlist'].next = [
		TERMINAL,
		KeywordSchema(
			name='ips',
		),
		KeywordSchema(
			name='players',
		),
	]

	BASIC_COMMAND_INFO[b'bossbar'].next = [
		KeywordSchema(
			name='add',
			next=[
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentSchema(
							name='name',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			],
		),
		KeywordSchema(
			name='get',
			next=[
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentSchema(
							name='__setting',
							type=makeLiteralsArgumentType([b'max', b'players', b'value', b'visible']),
						),
					]
				),
			],
		),
		KeywordSchema(
			name='list',
		),
		KeywordSchema(
			name='remove',
			next=[
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			],
		),
		KeywordSchema(
			name='set',
			next=[
				ArgumentSchema(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						KeywordSchema(
							name='color',
							next=[
								ArgumentSchema(
									name='color',
									type=makeLiteralsArgumentType([b'blue', b'green', b'pink', b'purple', b'red', b'white', b'yellow']),
								),
							],
						),
						KeywordSchema(
							name='max',
							next=[
								ArgumentSchema(
									name='max',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						KeywordSchema(
							name='name',
							next=[
								ArgumentSchema(
									name='name',
									type=MINECRAFT_COMPONENT,
								),
							],
						),
						KeywordSchema(
							name='players',
							next=[
								TERMINAL,
								ArgumentSchema(
									name='targets',
									type=MINECRAFT_ENTITY,
								),
							],
						),
						KeywordSchema(
							name='style',
							next=[
								ArgumentSchema(
									name='style',
									type=makeLiteralsArgumentType([b'notched_6', b'notched_10', b'notched_12', b'notched_20', b'progress']),
								),
							],
						),
						KeywordSchema(
							name='value	',
							next=[
								ArgumentSchema(
									name='value',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						KeywordSchema(
							name='visible',
							next=[
								ArgumentSchema(
									name='visible',
									type=BRIGADIER_BOOL,
								),
							],
						),
					]
				),
			],
		),
	]

	BASIC_COMMAND_INFO[b'clear'].next = [
		TERMINAL,
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_PREDICATE,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='maxCount',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO[b'clone'].next = [
		ArgumentSchema(
			name='begin',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentSchema(
					name='end',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentSchema(
							name='destination',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='maskMode',
									type=makeLiteralsArgumentType([b'replace', b'masked']),
									next=[
										TERMINAL,
										ArgumentSchema(
											name='cloneMode',
											type=makeLiteralsArgumentType([b'force', b'move', b'normal']),
										),
									],
								),
								KeywordSchema(
									name='filtered',
									next=[
										ArgumentSchema(
											name='filter',
											type=MINECRAFT_BLOCK_PREDICATE,
											next=[
												TERMINAL,
												ArgumentSchema(
													name='cloneMode',
													type=makeLiteralsArgumentType([b'force', b'move', b'normal']),
												),
											],
										),
									],
								),
							],
						),
					],
				),
			],
		),
	]

	# data command:

	DATA_TARGET = [
		KeywordSchema(
			name='block',
			next=[
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		KeywordSchema(
			name='entity',
			next=[
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		KeywordSchema(
			name='storage',
			next=[
				ArgumentSchema(
					name='target',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	DATA_MODIFICATION = [
		KeywordSchema(
			name='append',
		),
		KeywordSchema(
			name='insert',
			next=[
				ArgumentSchema(
					name='index',
					type=BRIGADIER_INTEGER,
				),
			]
		),
		KeywordSchema(
			name='merge',
		),
		KeywordSchema(
			name='prepend',
		),
		KeywordSchema(
			name='set',
		),
	]

	DATA_SOURCE = [
		KeywordSchema(
			name='block',
			next=[
				ArgumentSchema(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		KeywordSchema(
			name='entity',
			next=[
				ArgumentSchema(
					name='source',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		KeywordSchema(
			name='storage',
			next=[
				ArgumentSchema(
					name='source',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'data'].next = [
		KeywordSchema(
			name='get',
			next=[
				SwitchSchema(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='scale',
									type=BRIGADIER_FLOAT,
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='merge',
			next=[
				SwitchSchema(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentSchema(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					]
				),
			]
		),
		KeywordSchema(
			name='modify',
			next=[
				SwitchSchema(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentSchema(
							name='targetPath',
							type=MINECRAFT_NBT_PATH,
							next=[
								SwitchSchema(
									name='MODIFICATION',
									options=DATA_MODIFICATION,
									next=[
										KeywordSchema(
											name='from',
											next=[
												SwitchSchema(
													name='SOURCE',
													options=DATA_SOURCE,
													next=[
														TERMINAL,
														ArgumentSchema(
															name='sourcePath',
															type=MINECRAFT_NBT_PATH,
														),
													]
												),
											]
										),
										KeywordSchema(
											name='value',
											next=[
												ArgumentSchema(
													name='value',
													type=MINECRAFT_NBT_TAG,
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
		# remove <TARGET> <path>
		KeywordSchema(
			name='remove',
			next=[
				SwitchSchema(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentSchema(
							name='path',
							type=MINECRAFT_NBT_PATH,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'datapack'].next = [
		KeywordSchema(
			name='disable',
			next=[
				ArgumentSchema(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
				),
			],
		),
		KeywordSchema(
			name='enable',
			next=[
				ArgumentSchema(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
					next=[
						TERMINAL,
						KeywordSchema(
							name='first',
						),
						KeywordSchema(
							name='last',
						),
						KeywordSchema(
							name='before',
							next=[
								ArgumentSchema(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							],
						),
						KeywordSchema(
							name='after',
							next=[
								ArgumentSchema(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							],
						),
					]
				),
			],
		),
		KeywordSchema(
			name='list',
			description="List all data packs, or list only the available/enabled ones. Hovering over the data packs in the chat output shows their description defined in their pack.mcmeta.",
			next=[
				TERMINAL,
				KeywordSchema(
						name='available',
						next=[TERMINAL],
					),
				KeywordSchema(
						name='enabled',
						next=[TERMINAL],
					),
			],
		),
	]

	BASIC_COMMAND_INFO[b'debug'].next = [
		KeywordSchema(
			name='start',
		),
		KeywordSchema(
			name='stop',
		),
		KeywordSchema(
			name='function',
			next=[
				ArgumentSchema(
					name='name',
					type=MINECRAFT_FUNCTION,
				),
			]
		),
	]


	BASIC_COMMAND_INFO[b'defaultgamemode'].next = [
		ArgumentSchema(
			name='mode',
			type=makeLiteralsArgumentType([b'survival', b'creative', b'adventure', b'spectator']),
		),
	]

	BASIC_COMMAND_INFO[b'deop'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO[b'difficulty'].next = [
		TERMINAL,
		ArgumentSchema(
			name='difficulty',
			type=makeLiteralsArgumentType([b'peaceful', b'easy', b'normal', b'hard']),
		),
	]

	BASIC_COMMAND_INFO[b'effect'].next = [
		KeywordSchema(
			name='give',
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentSchema(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='seconds',
									type=BRIGADIER_INTEGER,
									args={'min': 0, 'max': 1000000},
									next=[
										TERMINAL,
										ArgumentSchema(
											name='amplifier',
											type=BRIGADIER_INTEGER,
											args={'min': 0, 'max': 255},
											next=[
												TERMINAL,
												ArgumentSchema(
													name='hideParticles',
													type=BRIGADIER_BOOL,
												),
											]
										),
									]
								),
							]
						),
					]
				),
			],
		),
		KeywordSchema(
			name='clear',
			next=[
				TERMINAL,
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
						),
					]
				),
			],
		),
	]

	BASIC_COMMAND_INFO[b'enchant'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='enchantment',
					type=MINECRAFT_ITEM_ENCHANTMENT,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='level',
							type=BRIGADIER_INTEGER,
						),
					]
				),
			]
		),
	]

	# execute Command:
	EXECUTE_INSTRUCTIONS = []

	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='align',
		next=[
			ArgumentSchema(
				name='axes',
				type=MINECRAFT_SWIZZLE,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='anchored',
		next=[
			ArgumentSchema(
				name='anchor',
				type=MINECRAFT_ENTITY_ANCHOR,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='as',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='at',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='facing',
		next=[
			ArgumentSchema(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			KeywordSchema(
				name='entity',
				next=[
					ArgumentSchema(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentSchema(
								name='anchor',
								type=MINECRAFT_ENTITY_ANCHOR,
								next=EXECUTE_INSTRUCTIONS
							),
						]
					),
				],
			)
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='in',
		next=[
			ArgumentSchema(
				name='dimension',
				type=MINECRAFT_DIMENSION,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='positioned',
		next=[
			ArgumentSchema(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			KeywordSchema(
				name='as',
				next=[
					ArgumentSchema(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=EXECUTE_INSTRUCTIONS
					),
				],
			)
		],
	))
	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='rotated',
		next=[
			ArgumentSchema(
				name='rot',
				type=MINECRAFT_ROTATION,
				next=EXECUTE_INSTRUCTIONS
			),
			KeywordSchema(
				name='as',
				next=[
					ArgumentSchema(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=EXECUTE_INSTRUCTIONS
					),
				],
			)
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS = []

	TERMINAL_LIST = [TERMINAL]

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='block',
		next=[
			ArgumentSchema(
				name='pos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentSchema(
						name='block',
						type=MINECRAFT_BLOCK_PREDICATE,
						next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS)
					),
				],
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='blocks',
		next=[
			ArgumentSchema(
				name='start',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentSchema(
						name='end',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentSchema(
								name='destination',
								type=MINECRAFT_BLOCK_POS,
								next=[
									KeywordSchema(
										name='all',
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
									KeywordSchema(
										name='masked',
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
								],
							),
						],
					),
				],
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='data',
		next=[
			KeywordSchema(
				name='block',
				next=[
					ArgumentSchema(
						name='pos',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentSchema(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			KeywordSchema(
				name='entity',
				next=[
					ArgumentSchema(
						name='target',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentSchema(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			KeywordSchema(
				name='storage',
				next=[
					ArgumentSchema(
						name='source',
						type=MINECRAFT_RESOURCE_LOCATION,
						next=[
							ArgumentSchema(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='entity',
		next=[
			ArgumentSchema(
				name='entities',
				type=MINECRAFT_ENTITY,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='predicate',
		next=[
			ArgumentSchema(
				name='predicate',
				type=MINECRAFT_PREDICATE,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(KeywordSchema(name='score',
		next=[
			ArgumentSchema(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							KeywordSchema(
								name='matches',
								next=[
									ArgumentSchema(
										name='range',
										type=MINECRAFT_INT_RANGE,
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
								]
							),
							ArgumentSchema(
								name='__compare',
								type=makeLiteralsArgumentType([b'<=', b'<', b'=', b'>=', b'>']),
								next=[
									ArgumentSchema(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentSchema(
												name='sourceObjective',
												type=MINECRAFT_OBJECTIVE,
												next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
											),
										],
									),
								],
							),
						],
					),
				],
			),
		],
	))

	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='if',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))

	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='unless',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))


	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS = []

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(KeywordSchema(name='block',
		next=[
			ArgumentSchema(
				name='targetPos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentSchema(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentSchema(
								name='type',
								type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
								next=[
									ArgumentSchema(
										name='scale',
										description="Multiplier to apply before storing value",
										type=BRIGADIER_DOUBLE,
										next=EXECUTE_INSTRUCTIONS
									),
								],
							),
						],
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(KeywordSchema(name='bossbar',
		next=[
			ArgumentSchema(
				name='id',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentSchema(
						name='value',
						type=makeLiteralsArgumentType([b'value', b'max']),
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(KeywordSchema(name='entity',
		next=[
			ArgumentSchema(
				name='target',
				type=MINECRAFT_ENTITY,
				next=[
					ArgumentSchema(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentSchema(
								name='type',
								type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
								next=[
									ArgumentSchema(
										name='scale',
										description="Multiplier to apply before storing value",
										type=BRIGADIER_DOUBLE,
										next=EXECUTE_INSTRUCTIONS
									),
								],
							),
						],
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(KeywordSchema(name='score',
		next=[
			ArgumentSchema(
				name='targets',
				description='Specifies score holder(s) whose score is to be overridden',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						description='A scoreboard objective',
						type=MINECRAFT_OBJECTIVE,
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(KeywordSchema(name='storage',
		next=[
			ArgumentSchema(
				name='target',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentSchema(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentSchema(
								name='type',
								type=makeLiteralsArgumentType([b'byte', b'short', b'int', b'long', b'float', b'double']),
								next=[
									ArgumentSchema(
										name='scale',
										description="Multiplier to apply before storing value",
										type=BRIGADIER_DOUBLE,
										next=EXECUTE_INSTRUCTIONS
									),
								],
							),
						],
					),
				],
			),
		]
	))

	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='store',
		next=[
			KeywordSchema(
				name='result',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
			KeywordSchema(
				name='success',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
		]
	))

	EXECUTE_INSTRUCTIONS.append(KeywordSchema(name='run',
		next=[COMMANDS_ROOT],
	))

	BASIC_COMMAND_INFO[b'execute'].next = EXECUTE_INSTRUCTIONS

	BASIC_COMMAND_INFO[b'experience'].next = [
		KeywordSchema(
			name='add',
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentSchema(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentSchema(
									name='__levels',
									type=makeLiteralsArgumentType([b'levels', b'points']),
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='set',
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentSchema(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentSchema(
									name='__levels',
									type=makeLiteralsArgumentType([b'levels', b'points']),
								),
							]
						),
					]
				),
			],
		),
		KeywordSchema(
			name='query',
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentSchema(
							name='__levels',
							type=makeLiteralsArgumentType([b'levels', b'points']),
						),
					]
				),
			]
		),
	]

	# fill <from> <to> <block> [destroy|hollow|keep|outline]
	# fill <from> <to> <block> replace [<filter>]
	BASIC_COMMAND_INFO[b'fill'].next = [
		ArgumentSchema(
			name='from',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentSchema(
					name='to',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentSchema(
							name='block',
							type=MINECRAFT_BLOCK_STATE,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='option',
									type=makeLiteralsArgumentType([b'destroy', b'hollow', b'keep', b'outline']),
								),
								KeywordSchema(
									name='replace',
									next=[
										TERMINAL,
										ArgumentSchema(
											name='replace',
											type=MINECRAFT_BLOCK_PREDICATE
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]

	FORCELOAD_RANGE_ARG = ArgumentSchema(
		name='from',
		type=MINECRAFT_COLUMN_POS,
		next=[
			TERMINAL,
			ArgumentSchema(
				name='to',
				type=MINECRAFT_COLUMN_POS,
			),
		]
	)

	BASIC_COMMAND_INFO[b'forceload'].next = [
		KeywordSchema(
			name='add',
			next=[
				FORCELOAD_RANGE_ARG,
			]
		),
		KeywordSchema(
			name='remove',
			next=[
				KeywordSchema('all'),
				FORCELOAD_RANGE_ARG,
			]
		),
		KeywordSchema(
			name='query',
			next=[
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_COLUMN_POS,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'function'].next = [
		ArgumentSchema(
			name='name',
			type=MINECRAFT_FUNCTION,
		),
	]

	BASIC_COMMAND_INFO[b'gamemode'].next = [
		ArgumentSchema(
			name='gamemode',
			type=MINECRAFT_GAME_MODE,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				)
			]
		),
	]

	BASIC_COMMAND_INFO[b'gamerule'].next = [
		KeywordSchema(
			name=gr.name,
			description=gr.description,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='value',
					type=gr.type,
				),
			]
		) for gr in version.gamerules
	]

	BASIC_COMMAND_INFO[b'give'].next = [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='count',
							type=BRIGADIER_INTEGER,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'help'].next = []

	ITEM_TARGET = [
		KeywordSchema(
			name='block',
			next=[
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		KeywordSchema(
			name='entity',
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_SOURCE = [
		KeywordSchema(
			name='block',
			next=[
				ArgumentSchema(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		KeywordSchema(
			name='entity',
			next=[
				ArgumentSchema(
					name='sourceTarget',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_MODIFIER = [
		ArgumentSchema(
			name='modifier',
			type=MINECRAFT_RESOURCE_LOCATION,
		),
	]

	BASIC_COMMAND_INFO[b'item'].next = [
		KeywordSchema(
			name='modify',
			next=[
				SwitchSchema(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=[*ITEM_MODIFIER]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='replace',
			next=[
				SwitchSchema(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=[
								KeywordSchema(
									name='with',
									next=[
										ArgumentSchema(
											name='item',
											type=MINECRAFT_ITEM_STACK,
											next=[
												TERMINAL,
												ArgumentSchema(
													name='count',
													type=BRIGADIER_INTEGER,
													args={'min': 1, 'max': 64},
												),
											]
										),
									]
								),
								KeywordSchema(
									name='from',
									next=[
										SwitchSchema(
											name='SOURCE',
											options=ITEM_SOURCE,
											next=[
												ArgumentSchema(
													name='sourceSlot',
													type=MINECRAFT_ITEM_SLOT,
													next=[
														TERMINAL,
														*ITEM_MODIFIER,
													]
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'kick'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'kill'].next = [
		TERMINAL,  # An entity is required to run the command without args
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
		),
	]

	BASIC_COMMAND_INFO[b'list'].next = [
		TERMINAL,
		KeywordSchema('uuids'),
	]

	BASIC_COMMAND_INFO[b'locate'].next = [
		ArgumentSchema(
			name='StructureType',
			type=makeLiteralsArgumentType([strToBytes(s.path) for s in version.structures]),
		),
	]

	BASIC_COMMAND_INFO[b'locatebiome'].next = [
		ArgumentSchema(
			name='biome',
			type=DPE_BIOME_ID,
		),
	]

	LOOT_TARGETS = [
		KeywordSchema(
			name='spawn',
			next=[
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
					args={'type': float}
				),
			]
		),
		KeywordSchema(
			name='replace',
			next=[
				SwitchSchema(
					name='REPLACE',
					options=[
						KeywordSchema(
							name='entity',
							next=[
								ArgumentSchema(
									name='entities',
									type=MINECRAFT_ENTITY,
								),
							]
						),
						KeywordSchema(
							name='block',
							next=[
								ArgumentSchema(
									name='targetPos',
									type=MINECRAFT_BLOCK_POS,
								),
							]
						),
					],
					next=[
						ArgumentSchema(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='count',
									type=BRIGADIER_INTEGER,
								),
							]
						),

					]
				),
			]
		),
		KeywordSchema(
			name='give',
			next=[
				ArgumentSchema(
					name='players',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		KeywordSchema(
			name='insert',
			next=[
				ArgumentSchema(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
	]

	LOOT_SOURCES = [
		KeywordSchema(
			name='fish',
			next=[
				ArgumentSchema(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentSchema(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='hand',
									type=makeLiteralsArgumentType([b'mainhand', b'offhand']),
								),
								ArgumentSchema(
									name='tool',
									type=MINECRAFT_ITEM_STACK,
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='loot',
			next=[
				ArgumentSchema(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
		KeywordSchema(
			name='kill',
			next=[
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		KeywordSchema(
			name='mine',
			next=[
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='hand',
							type=makeLiteralsArgumentType([b'mainhand', b'offhand']),
						),
						ArgumentSchema(
							name='tool',
							type=MINECRAFT_ITEM_STACK,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'loot'].next = [
		SwitchSchema(
			name='TARGET',
			options=LOOT_TARGETS,
			next=[
				SwitchSchema(
					name='SOURCE',
					options=LOOT_SOURCES,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'me'].next = [
		ArgumentSchema(
			name='action',
			type=MINECRAFT_MESSAGE,
		)
	]

	BASIC_COMMAND_INFO[b'msg'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='message',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'op'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO[b'pardon'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO[b'pardon-ip'].next = [
		ArgumentSchema(
			name='target',
			type=BRIGADIER_STRING,
		),
	]

	# particle <name> [<pos>] [<delta> <speed> <count> [force|normal] [<viewers>]]

	PARTICLE_ARGUMENTS = [
		TERMINAL,
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_VEC3,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='delta',
					type=MINECRAFT_VEC3,
					next=[
						ArgumentSchema(
							name='speed',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentSchema(
									name='count',
									type=BRIGADIER_INTEGER,
									next=[
										TERMINAL,
										ArgumentSchema(
											name='display_mode',
											type=makeLiteralsArgumentType([b'force', b'normal']),
											next=[
												TERMINAL,
												ArgumentSchema(
													name='viewers',
													type=MINECRAFT_ENTITY,
													next=[]
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]


	_SPECIAL_PARTICLES_tmp = [
		KeywordSchema(
			name='dust',
			next=[
				ArgumentSchema(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentSchema(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentSchema(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentSchema(
											name='size',
											type=BRIGADIER_FLOAT,
											next=PARTICLE_ARGUMENTS
										),
									]
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='dust_color_transition',
			next=[
				ArgumentSchema(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentSchema(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentSchema(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentSchema(
											name='size',
											type=BRIGADIER_FLOAT,
											next=[
												ArgumentSchema(
													name='red',
													type=BRIGADIER_FLOAT,
													next=[
														ArgumentSchema(
															name='green',
															type=BRIGADIER_FLOAT,
															next=[
																ArgumentSchema(
																	name='blue',
																	type=BRIGADIER_FLOAT,
																	next=PARTICLE_ARGUMENTS
																),
															]
														),
													]
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='block',
			next=[
				ArgumentSchema(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		KeywordSchema(
			name='falling_dust',
			next=[
				ArgumentSchema(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		KeywordSchema(
			name='item',
			next=[
				ArgumentSchema(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		KeywordSchema(
			name='vibration',
			next=[
				ArgumentSchema(
					name='x_start',
					type=BRIGADIER_DOUBLE,
					next=[
						ArgumentSchema(
							name='y_start',
							type=BRIGADIER_DOUBLE,
							next=[
								ArgumentSchema(
									name='z_start',
									type=BRIGADIER_DOUBLE,
									next=[
										ArgumentSchema(
											name='x_end',
											type=BRIGADIER_DOUBLE,
											next=[
												ArgumentSchema(
													name='y_end',
													type=BRIGADIER_DOUBLE,
													next=[
														ArgumentSchema(
															name='z_end',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentSchema(
																	name='duration',
																	type=BRIGADIER_INTEGER,
																	next=PARTICLE_ARGUMENTS
																),
															]
														),
													]
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]

	_SPECIAL_PARTICLES = []
	for particle in _SPECIAL_PARTICLES_tmp:
		_SPECIAL_PARTICLES.append(particle)
		particle = copy(particle)
		particle.name = f'minecraft:{particle.name}'
		_SPECIAL_PARTICLES.append(particle)

	del _SPECIAL_PARTICLES_tmp

	BASIC_COMMAND_INFO[b'particle'].next = [
		*_SPECIAL_PARTICLES,
		ArgumentSchema(
			name='name',
			type=MINECRAFT_PARTICLE,
			next=PARTICLE_ARGUMENTS
		),
	]

	BASIC_COMMAND_INFO[b'perf'].next = [
		KeywordSchema('start'),
		KeywordSchema('stop'),
	]

	# playsound <sound> <source> <targets> [<pos>] [<volume>] [<pitch>] [<minVolume>]
	BASIC_COMMAND_INFO[b'playsound'].next = [
		ArgumentSchema(
			name='sound',
			type=MINECRAFT_RESOURCE_LOCATION,
			next=[
				ArgumentSchema(
					name='source',
					type=makeLiteralsArgumentType([b'master', b'music', b'record', b'weather', b'block', b'hostile', b'neutral', b'player', b'ambient', b'voice']),
					next=[
						ArgumentSchema(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='pos',
									type=MINECRAFT_VEC3,
									next=[
										TERMINAL,
										ArgumentSchema(
											name='volume',
											type=BRIGADIER_FLOAT,
											next=[
												TERMINAL,
												ArgumentSchema(
													name='pitch',
													type=BRIGADIER_FLOAT,
													next=[
														TERMINAL,
														ArgumentSchema(
															name='minVolume',
															type=BRIGADIER_FLOAT,
														),
													]
												),
											]
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'publish'].next = [
		TERMINAL,
		ArgumentSchema(
			name='port',
			type=BRIGADIER_INTEGER,
		),
	]

	# recipe (give|take) <targets> (*|<recipe>)
	BASIC_COMMAND_INFO[b'recipe'].next = [
		ArgumentSchema(
			name='action',
			type=makeLiteralsArgumentType([b'give', b'take']),
			next=[
				ArgumentSchema(
					name='target',
					type=MINECRAFT_ENTITY,
					next=[
						KeywordSchema('*'),
						ArgumentSchema(
							name='recipe',
							type=MINECRAFT_RESOURCE_LOCATION,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'reload'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO[b'replaceitem'].next = [
		ArgumentSchema(
			name='OUTDATED!',
			type=MINECRAFT_MESSAGE,
		),
	]  # This command was superseded by the /item command in Java Edition 1.17.

	BASIC_COMMAND_INFO[b'save-all'].next = [
		TERMINAL,
		KeywordSchema('flush'),
	]

	BASIC_COMMAND_INFO[b'save-off'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO[b'save-on'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO[b'say'].next = [
		ArgumentSchema(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]

	# schedule function <function> <time> [append|replace]
	# schedule clear <function>
	BASIC_COMMAND_INFO[b'schedule'].next = [
		KeywordSchema(
			name='function',
			next=[
				ArgumentSchema(
					name='function',
					type=MINECRAFT_FUNCTION,
					next=[
						ArgumentSchema(
							name='time',
							type=MINECRAFT_TIME,
							next=[
								TERMINAL,
								ArgumentSchema(
									name='replace_behaviour',
									type=makeLiteralsArgumentType([b'append', b'replace']),
								),
							]
						),
					]
				),
			]
		),
		KeywordSchema(
			name='clear',
			next=[
				ArgumentSchema(
					name='function',
					type=MINECRAFT_FUNCTION,
				),
			]
		),

	]

	# scoreboard Command:
	SCOREBOARD_OBJECTIVES = []

	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='list'))

	# scoreboard objectives add <objective> <criteria> [<displayName>]
	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='add',
		next=[
			ArgumentSchema(
				name='objective',
				type=BRIGADIER_STRING,
				next=[
					ArgumentSchema(
						name='criteria',
						type=MINECRAFT_OBJECTIVE_CRITERIA,
						next=[
							TERMINAL,
							ArgumentSchema(
								name='displayName',
								type=MINECRAFT_COMPONENT,
							),
						]
					),
				]
			),
		]
	))

	# scoreboard objectives remove <objective>
	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='remove',
		next=[
			ArgumentSchema(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
			),
		]
	))

	# scoreboard objectives setdisplay <slot> [<objective>]
	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='setdisplay',
		next=[
			ArgumentSchema(
				name='slot',
				type=MINECRAFT_SCOREBOARD_SLOT,
				next=[
					TERMINAL,
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard objectives modify <objective> displayname <displayName>
	# scoreboard objectives modify <objective> rendertype (hearts|integer)
	SCOREBOARD_OBJECTIVES.append(KeywordSchema(name='modify',
		next=[
			ArgumentSchema(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
				next=[
					KeywordSchema(
						name='displayname',
						next=[
							ArgumentSchema(
								name='displayName',
								type=MINECRAFT_COMPONENT,
							),
						]
					),
					KeywordSchema(
						name='rendertype',
						next=[
							ArgumentSchema(
								name='rendertype',
								type=makeLiteralsArgumentType([b'hearts', b'integer']),
							),
						]
					),
				]
			),
		]
	))


	SCOREBOARD_PLAYERS = []

	# scoreboard players list [<target>]
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='list',
		next=[
			TERMINAL,
			ArgumentSchema(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
			),
		]
	))

	# scoreboard players get <target> <objective>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='get',
		next=[
			ArgumentSchema(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players set <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='set',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentSchema(
								name='score',
								type=BRIGADIER_INTEGER,
							),
						]
					),
				]
			),
		]
	))

	# scoreboard players add <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='add',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentSchema(
								name='score',
								type=BRIGADIER_INTEGER,
							),
						]
					),
				]
			),
		]
	))

	# scoreboard players remove <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='remove',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentSchema(
								name='score',
								type=BRIGADIER_INTEGER,
							),
						]
					),
				]
			),
		]
	))

	# scoreboard players reset <targets> [<objective>]
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='reset',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					TERMINAL,
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players enable <targets> <objective>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='enable',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players operation <targets> <targetObjective> <operation> <source> <sourceObjective>
	SCOREBOARD_PLAYERS.append(KeywordSchema(name='operation',
		next=[
			ArgumentSchema(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentSchema(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentSchema(
								name='operation',
								type=MINECRAFT_OPERATION,
								next=[
									ArgumentSchema(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentSchema(
												name='sourceObjective',
												type=MINECRAFT_OBJECTIVE,
											),
										]
									),
								]
							),
						]
					),
				]
			),
		]
	))

	BASIC_COMMAND_INFO[b'scoreboard'].next = [
		KeywordSchema(
			name='objectives',
			next=SCOREBOARD_OBJECTIVES
		),
		KeywordSchema(
			name='players',
			next=SCOREBOARD_PLAYERS
		),
	]

	BASIC_COMMAND_INFO[b'seed'].next = [TERMINAL]  # has no arguments!

	# setblock <pos> <block> [destroy|keep|replace]
	BASIC_COMMAND_INFO[b'setblock'].next = [
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentSchema(
					name='block',
					type=MINECRAFT_BLOCK_STATE,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='operation',
							type=makeLiteralsArgumentType([b'destroy', b'keep', b'replace']),
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'setidletimeout'].next = [
		ArgumentSchema(
			name='minutes',
			type=BRIGADIER_INTEGER,
		),
	]

	# setworldspawn [<pos>] [<angle>]
	BASIC_COMMAND_INFO[b'setworldspawn'].next = [
		TERMINAL,
		ArgumentSchema(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='angle',
					type=MINECRAFT_ANGLE,
				),
			]
		),
	]

	# spawnpoint [<targets>] [<pos>] [<angle>]
	BASIC_COMMAND_INFO[b'spawnpoint'].next = [
		TERMINAL,
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='angle',
							type=MINECRAFT_ANGLE,
						),
					]
				),
			]
		),
	]

	# spectate <target> [<player>]
	BASIC_COMMAND_INFO[b'spectate'].next = [
		ArgumentSchema(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='player',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	# spreadplayers <center> <spreadDistance> <maxRange> <respectTeams> <targets>
	# spreadplayers <center> <spreadDistance> <maxRange> under <maxHeight> <respectTeams> <targets>
	SPREADPLAYERS_RESPECT_TEAMS = [
		ArgumentSchema(
			name='respectTeams',
			type=BRIGADIER_BOOL,
			next=[
				ArgumentSchema(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'spreadplayers'].next = [
		ArgumentSchema(
			name='center',
			type=MINECRAFT_VEC2,
			next=[
				ArgumentSchema(
					name='spreadDistance',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentSchema(
							name='maxRange',
							type=BRIGADIER_FLOAT,
							next=[
								KeywordSchema(
									name='under',
									next=[
										ArgumentSchema(
											name='maxHeight',
											type=BRIGADIER_INTEGER,
											next=SPREADPLAYERS_RESPECT_TEAMS
										),
									]
								),
								*SPREADPLAYERS_RESPECT_TEAMS
							]
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'stop'].next = [TERMINAL]  # has no arguments!

	# stopsound <targets> [<source>] [<sound>]
	BASIC_COMMAND_INFO[b'stopsound'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='source',
					type=makeLiteralsArgumentType([b'*', b'master', b'music', b'record', b'weather', b'block', b'hostile', b'neutral', b'player', b'ambient', b'voice']),
					next=[
						TERMINAL,
						ArgumentSchema(
							name='sound',
							type=MINECRAFT_RESOURCE_LOCATION,
							description="Specifies the sound to stop. Must be a resource location. \n\nMust be a sound event defined in `sounds.json` (for example, `entity.pig.ambient`).",
						),
					]
				),
			]
		),
	]

	#  summon <entity> [<pos>] [<nbt>]
	BASIC_COMMAND_INFO[b'summon'].next = [
		ArgumentSchema(
			name='entity',
			type=MINECRAFT_ENTITY_SUMMON,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='pos',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					]
				),
			]
		),
	]

	# tag <targets> add <name>
	# tag <targets> list
	# tag <targets> remove <name>
	BASIC_COMMAND_INFO[b'tag'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				KeywordSchema(
					name='add',
					next=[
						ArgumentSchema(
							name='name',
							type=BRIGADIER_STRING,
						),
					]
				),
				KeywordSchema('list'),
				KeywordSchema(
					name='remove',
					next=[
						ArgumentSchema(
							name='name',
							type=BRIGADIER_STRING,
						),
					]
				),
			]
		),
	]

	# team list [<team>]
	# 	Lists all teams, with their display names and the amount of entities in them. The optional <team> can be used to specify a particular team.
	#
	# team add <team> [<displayName>]
	# 	Creates a team with the given name and optional display name. <displayName> defaults to <objective> when unspecified.
	#
	# team remove <team>
	# 	Deletes the specified team.
	#
	# team empty <team>
	# 	Removes all members from the named team.
	#
	# team join <team> [<members>]
	# 	Assigns the specified entities to the specified team. If no entities is specified, makes the executor join the team.
	#
	# team leave <members>
	# 	Makes the specified entities leave their teams.
	#
	# team modify <team> <option> <value>
	# 	Modifies the options of the specified team.
	BASIC_COMMAND_INFO[b'team'].next = [
		KeywordSchema(
			name='list',
			description="Lists all teams, with their display names and the amount of entities in them. The optional `<team>` can be used to specify a particular team.",
			next=[
				TERMINAL,
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		KeywordSchema(
			name='add',
			description="Creates a team with the given name and optional display name. `<displayName>` defaults to `<objective>` when unspecified.",
			next=[
				ArgumentSchema(
					name='team',
					type=BRIGADIER_STRING,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='displayName',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			]
		),
		KeywordSchema(
			name='remove',
			description="Deletes the specified team.",
			next=[
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		KeywordSchema(
			name='empty',
			description="Removes all members from the named team.",
			next=[
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		KeywordSchema(
			name='join',
			description="Assigns the specified entities to the specified team. If no entities is specified, makes the executor join the team.",
			next=[
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='members',
							type=MINECRAFT_SCORE_HOLDER,
						),
					]
				),
			]
		),
		KeywordSchema(
			name='leave',
			description="Makes the specified entities leave their teams.",
			next=[
				ArgumentSchema(
					name='members',
					type=MINECRAFT_SCORE_HOLDER,
				),
			]
		),
		KeywordSchema(
			name='modify',
			description="Modifies the options of the specified team.",
			next=[
				ArgumentSchema(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						SwitchSchema(
							name='option',
							options=[
								KeywordSchema(
									name='displayName',
									description="Set the display name of the team.",
									next=[
										ArgumentSchema(
											name='displayName',
											type=MINECRAFT_COMPONENT,
											description="Specifies the team name to be displayed. Must be a raw JSON text.",
										),
									]
								),
								KeywordSchema(
									name='color',
									description="Decide the color of the team and players in chat, above their head, on the Tab menu, and on the sidebar. Also changes the color of the outline of the entities caused by the Glowing effect.",
									next=[
										ArgumentSchema(
											name='value',
											type=MINECRAFT_COLOR,
											description="Must be a color.\n\nDefaults to reset. If reset, names are shown in default color and formatting.",
										),
									]
								),
								KeywordSchema(
									name='friendlyFire',
									description="Enable/Disable players inflicting damage on each other when on the same team. (Note: players can still inflict status effects on each other.) Does not affect some non-player entities in a team.",
									next=[
										ArgumentSchema(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Enable players inflicting damage on each other when in the same team.\n  - false - Disable players inflicting damage on each other when in the same team.",
										),
									]
								),
								KeywordSchema(
									name='seeFriendlyInvisibles',
									description="Decide players can see invisible players on their team as whether semi-transparent or completely invisible.",
									next=[
										ArgumentSchema(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Can see invisible players on the same team semi-transparently.\n  - false - Cannot see invisible players on the same team.",
										),
									]
								),
								KeywordSchema(
									name='nametagVisibility',
									description="Decide whose name tags above their heads can be seen.",
									next=[
										KeywordSchema(
											name='never',
											description="Name above player's head cannot be seen by any players.",
										),
										KeywordSchema(
											name='hideForOtherTeams',
											description="Name above player's head can be seen only by players in the same team.",
										),
										KeywordSchema(
											name='hideForOwnTeam',
											description="Name above player's head cannot be seen by all the players in the same team.",
										),
										KeywordSchema(
											name='always',
											description="(Default) Name above player's head can be seen by all the players.",
										),
									]
								),
								KeywordSchema(
									name='deathMessageVisibility',
									description="Control the visibility of death messages for players.",
									next=[
										KeywordSchema(
											name='never',
											description="Hide death message for all the players.",
										),
										KeywordSchema(
											name='hideForOtherTeams',
											description="Hide death message to all the players who are not in the same team.",
										),
										KeywordSchema(
											name='hideForOwnTeam',
											description="Hide death message to players in the same team.",
										),
										KeywordSchema(
											name='always',
											description="(Default) Make death message visible to all the players.",
										),
									]
								),
								KeywordSchema(
									name='collisionRule',
									description="Controls the way the entities on the team collide with other entities.",
									next=[
										KeywordSchema(
											name='always',
											description="(Default) Normal collision.",
										),
										KeywordSchema(
											name='never',
											description="No entities can push entities in this team.",
										),
										KeywordSchema(
											name='pushOtherTeams',
											description="Entities in this team can be pushed only by other entities in the same team.",
										),
										KeywordSchema(
											name='pushOwnTeam',
											description="Entities in this team cannot be pushed by another entity in this team.",
										),
									]
								),
								KeywordSchema(
									name='prefix',
									description="Modifies the prefix that displays before players' names.",
									next=[
										ArgumentSchema(
											name='prefix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the prefix to display. Must be a raw JSON text.",
										),
									]
								),
								KeywordSchema(
									name='suffix',
									description="Modifies the suffix that displays before players' names.",
									next=[
										ArgumentSchema(
											name='suffix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the suffix to display. Must be a raw JSON text.",
										),
									]
								),
							],
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'teammsg'].next = [
		ArgumentSchema(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]

	# teleport <destination>
	# teleport <location>
	#
	# teleport <targets> <destination>
	# teleport <targets> <location>
	# teleport <targets> <location> <rotation>
	# teleport <targets> <location> facing <facingLocation>
	# teleport <targets> <location> facing entity <facingEntity> [<facingAnchor>]
	BASIC_COMMAND_INFO[b'teleport'].next = [
		# ArgumentSchema(
		# 	name='destination',
		# 	type=MINECRAFT_ENTITY,
		# ),
		ArgumentSchema(
			name='location',
			type=MINECRAFT_VEC3,
		),
		ArgumentSchema(
			name='targets|destination',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentSchema(
					name='location',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentSchema(
							name='rotation',
							type=MINECRAFT_ROTATION,
						),
						KeywordSchema(
							name='facing',
							next=[
								ArgumentSchema(
									name='facingLocation',
									type=MINECRAFT_VEC3,
								),
								KeywordSchema(
									name='entity',
									next=[
										ArgumentSchema(
											name='facingEntity',
											type=MINECRAFT_ENTITY,
											next=[
												TERMINAL,
												ArgumentSchema(
													name='facingAnchor',
													type=MINECRAFT_ENTITY_ANCHOR,
												),
											]
										),
									]
								),
							]
						),
					]
				),
				ArgumentSchema(
					name='destination',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'tell'].next = BASIC_COMMAND_INFO[b'msg'].next

	# tellraw <targets> <message>
	BASIC_COMMAND_INFO[b'tellraw'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='message',
					type=MINECRAFT_COMPONENT,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'testfor'].next = []  # This command has been removed

	BASIC_COMMAND_INFO[b'testforblock'].next = []  # This command has been removed

	BASIC_COMMAND_INFO[b'testforblocks'].next = []  # This command has been removed

	BASIC_COMMAND_INFO[b'time'].next = [
		KeywordSchema(
			name='add',
			description="Adds `<time>` to the in-game daytime.",
			next=[
				ArgumentSchema(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
		KeywordSchema(
			name='query',
			description="Queries current time.",
			next=[
				ArgumentSchema(
					name='daytime|gametime|day',
					type=makeLiteralsArgumentType([b'daytime', b'gametime', b'day']),
				),
			]
		),
		KeywordSchema(
			name='set',
			next=[
				ArgumentSchema(
					name='timeSpec',
					type=makeLiteralsArgumentType([b'day', b'night', b'noon', b'midnight']),
				),
			]
		),
		KeywordSchema(
			name='set',
			next=[
				ArgumentSchema(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
	]

	# title <targets> (clear|reset)
	# title <targets> (title|subtitle|actionbar) <title>
	# title <targets> times <fadeIn> <stay> <fadeOut>
	BASIC_COMMAND_INFO[b'title'].next = [
		ArgumentSchema(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentSchema(
					name='clear|reset',
					type=makeLiteralsArgumentType([b'clear', b'reset']),
				),
				ArgumentSchema(
					name='title|subtitle|actionbar',
					type=makeLiteralsArgumentType([b'title', b'subtitle', b'actionbar']),
					next=[
						ArgumentSchema(
							name='title',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
				KeywordSchema(
					name='times',
					next=[
						ArgumentSchema(
							name='fadeIn',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentSchema(
									name='stay',
									type=BRIGADIER_INTEGER,
									next=[
										ArgumentSchema(
											name='fadeOut',
											type=BRIGADIER_INTEGER,
										),
									]
								),
							]
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'tm'].next = BASIC_COMMAND_INFO[b'teammsg'].next

	# BASIC_COMMAND_INFO[b'toggledownfall'].next = []  has been removed

	BASIC_COMMAND_INFO[b'tp'].next = BASIC_COMMAND_INFO[b'teleport'].next

	# trigger <objective>
	# trigger <objective> add <value>
	# trigger <objective> set <value>
	BASIC_COMMAND_INFO[b'trigger'].next = [
		ArgumentSchema(
			name='objective',
			type=MINECRAFT_OBJECTIVE,
			next=[
				TERMINAL,
				KeywordSchema(
					name='add',
					next=[
						ArgumentSchema(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					]
				),
				KeywordSchema(
					name='set',
					next=[
						ArgumentSchema(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'w'].next = BASIC_COMMAND_INFO[b'msg'].next

	# weather (clear|rain|thunder) [<duration>]
	BASIC_COMMAND_INFO[b'weather'].next = [
		ArgumentSchema(
			name='objective',
			type=makeLiteralsArgumentType([b'clear', b'rain', b'thunder']),
			next=[
				TERMINAL,
				ArgumentSchema(
					name='duration',
					type=BRIGADIER_INTEGER,
				),
			]
		),
	]

	BASIC_COMMAND_INFO[b'whitelist'].next = []  # TODO: BASIC_COMMAND_INFO[b'whitelist'].next

	BASIC_COMMAND_INFO[b'worldborder'].next = []  # TODO: BASIC_COMMAND_INFO[b'worldborder'].next

	BASIC_COMMAND_INFO[b'xp'].next = BASIC_COMMAND_INFO[b'experience'].next

	return MCFunctionSchema('', commands=BASIC_COMMAND_INFO)
