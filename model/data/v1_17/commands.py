from copy import copy

from Cat.utils.collections_ import ChainedList
from model.commands.argumentTypes import *
from model.commands.command import CommandInfo, Keyword, ArgumentInfo, TERMINAL, COMMANDS_ROOT, Switch
from model.data.mcVersions import MCVersion


def fillCommandsFor1_17(version: MCVersion) -> None:
	_BASIC_COMMAND_INFO_LIST = [
		CommandInfo(
			name='?',
			description='An alias of /help. Provides help for commands.',
			opLevel=0,
		),
		CommandInfo(
			name='advancement',
			description='Gives, removes, or checks player advancements.',
			opLevel=2,
		),
		CommandInfo(
			name='attribute',
			description='Queries, adds, removes or sets an entity attribute.',
			opLevel=2,
		),
		CommandInfo(
			name='ban',
			description='Adds player to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='ban-ip',
			description='Adds IP address to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='banlist',
			description='Displays banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='bossbar',
			description='Creates and modifies bossbars.',
			opLevel=2,
		),
		CommandInfo(
			name='clear',
			description='Clears items from player inventory.',
			opLevel=2,
		),
		CommandInfo(
			name='clone',
			description='Copies blocks from one place to another.',
			opLevel=2,
		),
		CommandInfo(
			name='data',
			description='Gets, merges, modifies and removes block entity and entity NBT data.',
			opLevel=2,
		),
		CommandInfo(
			name='datapack',
			description='Controls loaded data packs.',
			opLevel=2,
		),
		CommandInfo(
			name='debug',
			description='Starts or stops a debugging session.',
			opLevel=3,
		),
		CommandInfo(
			name='defaultgamemode',
			description='Sets the default game mode.',
			opLevel=2,
		),
		CommandInfo(
			name='deop',
			description='Revokes operator status from a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='difficulty',
			description='Sets the difficulty level.',
			opLevel=2,
		),
		CommandInfo(
			name='effect',
			description='Add or remove status effects.',
			opLevel=2,
		),
		CommandInfo(
			name='enchant',
			description="Adds an enchantment to a player's selected item.",
			opLevel=2,
		),
		CommandInfo(
			name='execute',
			description='Executes another command.',
			opLevel=2,
		),
		CommandInfo(
			name='experience',
			description='An alias of /xp. Adds or removes player experience.',
			opLevel=2,
		),
		CommandInfo(
			name='fill',
			description='Fills a region with a specific block.',
			opLevel=2,
		),
		CommandInfo(
			name='forceload',
			description='Forces chunks to constantly be loaded or not.',
			opLevel=2,
		),
		CommandInfo(
			name='function',
			description='Runs a function.',
			opLevel=2,
		),
		CommandInfo(
			name='gamemode',
			description="Sets a player's game mode.",
			opLevel=2,
		),
		CommandInfo(
			name='gamerule',
			description='Sets or queries a game rule value.',
			opLevel=2,
		),
		CommandInfo(
			name='give',
			description='Gives an item to a player.',
			opLevel=2,
		),
		CommandInfo(
			name='help',
			description='An alias of /?. Provides help for commands.',
			opLevel=0,
		),
		CommandInfo(
			name='item',
			description='Manipulates items in inventories.',
			opLevel=2,
		),
		CommandInfo(
			name='kick',
			description='Kicks a player off a server.',
			opLevel=3,
		),
		CommandInfo(
			name='kill',
			description='Kills entities (players, mobs, items, etc.).',
			opLevel=2,
		),
		CommandInfo(
			name='list',
			description='Lists players on the server.',
			opLevel=0,
		),
		CommandInfo(
			name='locate',
			description='Locates closest structure.',
			opLevel=2,
		),
		CommandInfo(
			name='locatebiome',
			description='Locates closest biome.',
			opLevel=2,
		),
		CommandInfo(
			name='loot',
			description='Drops items from an inventory slot onto the ground.',
			opLevel=2,
		),
		CommandInfo(
			name='me',
			description='Displays a message about the sender.',
			opLevel=0,
		),
		CommandInfo(
			name='msg',
			description='An alias of /tell and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo(
			name='op',
			description='Grants operator status to a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='pardon',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='pardon-ip',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='particle',
			description='Creates particles.',
			opLevel=2,
		),
		CommandInfo(
			name='perf',
			description='Captures info and metrics about the game for 10 seconds.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo(
			name='playsound',
			description='Plays a sound.',
			opLevel=2,
		),
		CommandInfo(
			name='publish',
			description='Opens single-player world to local network.',
			opLevel=4,
			availableInMP=False
		),
		CommandInfo(
			name='recipe',
			description='Gives or takes player recipes.',
			opLevel=2,
		),
		CommandInfo(
			name='reload',
			description='Reloads loot tables, advancements, and functions from disk.',
			opLevel=2,
		),
		CommandInfo(
			name='replaceitem',
			description='Replaces items in inventories.',
			removed=True,
			removedVersion='1.17',
			removedComment='Replaced with `/item replace`',
			opLevel=2,
		),
		CommandInfo(
			name='save-all',
			description='Saves the server to disk.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo(
			name='save-off',
			description='Disables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo(
			name='save-on',
			description='Enables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo(
			name='say',
			description='Displays a message to multiple players.',
			opLevel=2,
		),
		CommandInfo(
			name='schedule',
			description='Delays the execution of a function.',
			opLevel=2,
		),
		CommandInfo(
			name='scoreboard',
			description='Manages scoreboard objectives and players.',
			opLevel=2,
		),
		CommandInfo(
			name='seed',
			description='Displays the world seed.',
			opLevel='0 in singleplayer, 2 in multiplayer',
		),
		CommandInfo(
			name='setblock',
			description='Changes a block to another block.',
			opLevel=2,
		),
		CommandInfo(
			name='setidletimeout',
			description='Sets the time before idle players are kicked.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='setworldspawn',
			description='Sets the world spawn.',
			opLevel=2,
		),
		CommandInfo(
			name='spawnpoint',
			description='Sets the spawn point for a player.',
			opLevel=2,
		),
		CommandInfo(
			name='spectate',
			description='Make one player in spectator mode spectate an entity.',
			opLevel=2,
		),
		CommandInfo(
			name='spreadplayers',
			description='Teleports entities to random locations.',
			opLevel=2,
		),
		CommandInfo(
			name='stop',
			description='Stops a server.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo(
			name='stopsound',
			description='Stops a sound.',
			opLevel=2,
		),
		CommandInfo(
			name='summon',
			description='Summons an entity.',
			opLevel=2,
		),
		CommandInfo(
			name='tag',
			description='Controls entity tags.',
			opLevel=2,
		),
		CommandInfo(
			name='team',
			description='Controls teams.',
			opLevel=2,
		),
		CommandInfo(
			name='teammsg',
			description='An alias of /tm. Specifies the message to send to team.',
			opLevel=0,
		),
		CommandInfo(
			name='teleport',
			description='An alias of /tp. Teleports entities.',
			opLevel=2,
		),
		CommandInfo(
			name='tell',
			description='An alias of /msg and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo(
			name='tellraw',
			description='Displays a JSON message to players.',
			opLevel=2,
		),
		CommandInfo(
			name='testfor',
			description='Counts entities matching specified conditions.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead', # TODO: removedComment for '/testfor' command
			opLevel=2,
		),
		CommandInfo(
			name='testforblock',
			description='Tests whether a block is in a location.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if block` instead',
			opLevel=2,
		),
		CommandInfo(
			name='testforblocks',
			description='Tests whether the blocks in two regions match.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead',
			opLevel=2,
		),
		CommandInfo(
			name='time',
			description="Changes or queries the world's game time.",
			opLevel=2,
		),
		CommandInfo(
			name='title',
			description='Manages screen titles.',
			opLevel=2,
		),
		CommandInfo(
			name='tm',
			description='An alias of /teammsg. Specifies the message to send to team.',
			opLevel=0,
		),
		# CommandInfo(
		# 	name='toggledownfall',
		# 	description='Toggles the weather.',
		# 	removed=True,
		# 	removedVersion='1.13',
		# 	removedComment='Use `/weather ...` instead',
		# 	opLevel=1,
		# ),
		CommandInfo(
			name='tp',
			description='An alias of /teleport. Teleports entities.',
			opLevel=2,
		),
		CommandInfo(
			name='trigger',
			description='Sets a trigger to be activated.',
			opLevel=0,
		),
		CommandInfo(
			name='w',
			description='An alias of /tell and /msg. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo(
			name='weather',
			description='Sets the weather.',
			opLevel=2,
		),
		CommandInfo(
			name='whitelist',
			description='Manages server whitelist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo(
			name='worldborder',
			description='Manages the world border.',
			opLevel=2,
		),
		CommandInfo(
			name='xp',
			description='An alias of /experience [Java Edition only]. Adds or removes player experience.',
			opLevel=2,
		)
	]

	BASIC_COMMAND_INFO: dict[str, CommandInfo] = {c.name: c for c in _BASIC_COMMAND_INFO_LIST}
	version.commands = BASIC_COMMAND_INFO

	BASIC_COMMAND_INFO['?'].next = []

	BASIC_COMMAND_INFO['advancement'].next = [
		ArgumentInfo(
			name='__action',
			type=makeLiteralsArgumentType(['grant', 'revoke']),
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						Keyword(
							name='everything',
						),
						Keyword(
							name='only',
							next=[
								ArgumentInfo(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
									next=[
										TERMINAL,
										ArgumentInfo(
											name='criterion',
											type=BRIGADIER_STRING,
										),
									]
								),
							]
						),
						Keyword(
							name='from',
							next=[
								ArgumentInfo(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
								),
							]
						),
						Keyword(
							name='through',
							next=[
								ArgumentInfo(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
								),
							]
						),
						Keyword(
							name='until',
							next=[
								ArgumentInfo(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
								),
							]
						),
					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO['attribute'].next = [
		ArgumentInfo(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='attribute',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						Keyword(
							name='get',
							next=[
								TERMINAL,
								ArgumentInfo(
									name='scale',
									type=BRIGADIER_DOUBLE,
								),
							]
						),
						Keyword(
							name='base',
							next=[
								Keyword(
									name='get',
									next=[
										TERMINAL,
										ArgumentInfo(
											name='scale',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
								Keyword(
									name='set',
									next=[
										ArgumentInfo(
											name='value',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
							],
						),
						Keyword(
							name='modifier',
							next=[
								Keyword(
									name='add',
									next=[
										ArgumentInfo(
											name='uuid',
											type=MINECRAFT_UUID,
											next=[
												ArgumentInfo(
													name='name',
													type=BRIGADIER_STRING,
													next=[
														ArgumentInfo(
															name='value',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentInfo(
																	name='uuid',
																	type=makeLiteralsArgumentType(['add', 'multiply', 'multiply_base']),
																),
															]
														),
													]
												),
											]
										),
									]
								),
								Keyword(
									name='remove',
									next=[
										ArgumentInfo(
											name='uuid',
											type=MINECRAFT_UUID,
										),
									]
								),
								Keyword(
									name='value',
									next=[
										Keyword(
											name='get',
											next=[
												ArgumentInfo(
													name='uuid',
													type=MINECRAFT_UUID,
													next=[
														TERMINAL,
														ArgumentInfo(
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

	BASIC_COMMAND_INFO['ban'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['ban-ip'].next = [
		ArgumentInfo(
			name='target',
			type=BRIGADIER_STRING,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['banlist'].next = [
		TERMINAL,
		Keyword(
			name='ips',
		),
		Keyword(
			name='players',
		),
	]

	BASIC_COMMAND_INFO['bossbar'].next = [
		Keyword(
			name='add',
			next=[
				ArgumentInfo(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo(
							name='name',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			],
		),
		Keyword(
			name='get',
			next=[
				ArgumentInfo(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo(
							name='__setting',
							type=makeLiteralsArgumentType(['max', 'players', 'value', 'visible']),
						),
					]
				),
			],
		),
		Keyword(
			name='list',
		),
		Keyword(
			name='remove',
			next=[
				ArgumentInfo(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			],
		),
		Keyword(
			name='set',
			next=[
				ArgumentInfo(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						Keyword(
							name='color',
							next=[
								ArgumentInfo(
									name='color',
									type=makeLiteralsArgumentType(['blue', 'green', 'pink', 'purple', 'red', 'white', 'yellow']),
								),
							],
						),
						Keyword(
							name='max',
							next=[
								ArgumentInfo(
									name='max',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						Keyword(
							name='name',
							next=[
								ArgumentInfo(
									name='name',
									type=MINECRAFT_COMPONENT,
								),
							],
						),
						Keyword(
							name='players',
							next=[
								TERMINAL,
								ArgumentInfo(
									name='targets',
									type=MINECRAFT_ENTITY,
								),
							],
						),
						Keyword(
							name='style',
							next=[
								ArgumentInfo(
									name='style',
									type=makeLiteralsArgumentType(['notched_6', 'notched_10', 'notched_12', 'notched_20', 'progress']),
								),
							],
						),
						Keyword(
							name='value	',
							next=[
								ArgumentInfo(
									name='value',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						Keyword(
							name='visible',
							next=[
								ArgumentInfo(
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

	BASIC_COMMAND_INFO['clear'].next = [
		TERMINAL,
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='item',
					type=MINECRAFT_ITEM_PREDICATE,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='maxCount',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO['clone'].next = [
		ArgumentInfo(
			name='begin',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo(
					name='end',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentInfo(
							name='destination',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='maskMode',
									type=makeLiteralsArgumentType(['replace', 'masked']),
									next=[
										TERMINAL,
										ArgumentInfo(
											name='cloneMode',
											type=makeLiteralsArgumentType(['force', 'move', 'normal']),
										),
									],
								),
								Keyword(
									name='filtered',
									next=[
										ArgumentInfo(
											name='filter',
											type=MINECRAFT_BLOCK_PREDICATE,
											next=[
												TERMINAL,
												ArgumentInfo(
													name='cloneMode',
													type=makeLiteralsArgumentType(['force', 'move', 'normal']),
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
		Keyword(
			name='block',
			next=[
				ArgumentInfo(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword(
			name='entity',
			next=[
				ArgumentInfo(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword(
			name='storage',
			next=[
				ArgumentInfo(
					name='target',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	DATA_MODIFICATION = [
		Keyword(
			name='append',
		),
		Keyword(
			name='insert',
			next=[
				ArgumentInfo(
					name='index',
					type=BRIGADIER_INTEGER,
				),
			]
		),
		Keyword(
			name='merge',
		),
		Keyword(
			name='prepend',
		),
		Keyword(
			name='set',
		),
	]

	DATA_SOURCE = [
		Keyword(
			name='block',
			next=[
				ArgumentInfo(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword(
			name='entity',
			next=[
				ArgumentInfo(
					name='source',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword(
			name='storage',
			next=[
				ArgumentInfo(
					name='source',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['data'].next = [
		Keyword(
			name='get',
			next=[
				Switch(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='scale',
									type=BRIGADIER_FLOAT,
								),
							]
						),
					]
				),
			]
		),
		Keyword(
			name='merge',
			next=[
				Switch(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					]
				),
			]
		),
		Keyword(
			name='modify',
			next=[
				Switch(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo(
							name='targetPath',
							type=MINECRAFT_NBT_PATH,
							next=[
								Switch(
									name='MODIFICATION',
									options=DATA_MODIFICATION,
									next=[
										Keyword(
											name='from',
											next=[
												Switch(
													name='SOURCE',
													options=DATA_SOURCE,
													next=[
														TERMINAL,
														ArgumentInfo(
															name='sourcePath',
															type=MINECRAFT_NBT_PATH,
														),
													]
												),
											]
										),
										Keyword(
											name='value',
											next=[
												ArgumentInfo(
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
		Keyword(
			name='remove',
			next=[
				Switch(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo(
							name='path',
							type=MINECRAFT_NBT_PATH,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['datapack'].next = [
		Keyword(
			name='disable',
			next=[
				ArgumentInfo(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
				),
			],
		),
		Keyword(
			name='enable',
			next=[
				ArgumentInfo(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
					next=[
						TERMINAL,
						Keyword(
							name='first',
						),
						Keyword(
							name='last',
						),
						Keyword(
							name='before',
							next=[
								ArgumentInfo(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							],
						),
						Keyword(
							name='after',
							next=[
								ArgumentInfo(
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
		Keyword(
			name='list',
			description="List all data packs, or list only the available/enabled ones. Hovering over the data packs in the chat output shows their description defined in their pack.mcmeta.",
			next=[
				TERMINAL,
				Keyword(
						name='available',
						next=[TERMINAL],
					),
				Keyword(
						name='enabled',
						next=[TERMINAL],
					),
			],
		),
	]

	BASIC_COMMAND_INFO['debug'].next = [
		Keyword(
			name='start',
		),
		Keyword(
			name='stop',
		),
		Keyword(
			name='function',
			next=[
				ArgumentInfo(
					name='name',
					type=MINECRAFT_FUNCTION,
				),
			]
		),
	]


	BASIC_COMMAND_INFO['defaultgamemode'].next = [
		ArgumentInfo(
			name='mode',
			type=makeLiteralsArgumentType(['survival', 'creative', 'adventure', 'spectator']),
		),
	]

	BASIC_COMMAND_INFO['deop'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['difficulty'].next = [
		TERMINAL,
		ArgumentInfo(
			name='difficulty',
			type=makeLiteralsArgumentType(['peaceful', 'easy', 'normal', 'hard']),
		),
	]

	BASIC_COMMAND_INFO['effect'].next = [
		Keyword(
			name='give',
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='seconds',
									type=BRIGADIER_INTEGER,
									args={'min': 0, 'max': 1000000},
									next=[
										TERMINAL,
										ArgumentInfo(
											name='amplifier',
											type=BRIGADIER_INTEGER,
											args={'min': 0, 'max': 255},
											next=[
												TERMINAL,
												ArgumentInfo(
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
		Keyword(
			name='clear',
			next=[
				TERMINAL,
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
						),
					]
				),
			],
		),
	]

	BASIC_COMMAND_INFO['enchant'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='enchantment',
					type=MINECRAFT_ITEM_ENCHANTMENT,
					next=[
						TERMINAL,
						ArgumentInfo(
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

	EXECUTE_INSTRUCTIONS.append(Keyword(name='align',
		next=[
			ArgumentInfo(
				name='axes',
				type=MINECRAFT_SWIZZLE,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='anchored',
		next=[
			ArgumentInfo(
				name='anchor',
				type=MINECRAFT_ENTITY_ANCHOR,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='as',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='at',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='facing',
		next=[
			ArgumentInfo(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword(
				name='entity',
				next=[
					ArgumentInfo(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentInfo(
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
	EXECUTE_INSTRUCTIONS.append(Keyword(name='in',
		next=[
			ArgumentInfo(
				name='dimension',
				type=MINECRAFT_DIMENSION,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='positioned',
		next=[
			ArgumentInfo(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword(
				name='as',
				next=[
					ArgumentInfo(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=EXECUTE_INSTRUCTIONS
					),
				],
			)
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword(name='rotated',
		next=[
			ArgumentInfo(
				name='rot',
				type=MINECRAFT_ROTATION,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword(
				name='as',
				next=[
					ArgumentInfo(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='block',
		next=[
			ArgumentInfo(
				name='pos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo(
						name='block',
						type=MINECRAFT_BLOCK_PREDICATE,
						next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS)
					),
				],
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='blocks',
		next=[
			ArgumentInfo(
				name='start',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo(
						name='end',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentInfo(
								name='destination',
								type=MINECRAFT_BLOCK_POS,
								next=[
									Keyword(
										name='all',
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
									Keyword(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='data',
		next=[
			Keyword(
				name='block',
				next=[
					ArgumentInfo(
						name='pos',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentInfo(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			Keyword(
				name='entity',
				next=[
					ArgumentInfo(
						name='target',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentInfo(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			Keyword(
				name='storage',
				next=[
					ArgumentInfo(
						name='source',
						type=MINECRAFT_RESOURCE_LOCATION,
						next=[
							ArgumentInfo(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='entity',
		next=[
			ArgumentInfo(
				name='entities',
				type=MINECRAFT_ENTITY,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='predicate',
		next=[
			ArgumentInfo(
				name='predicate',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword(name='score',
		next=[
			ArgumentInfo(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							Keyword(
								name='matches',
								next=[
									ArgumentInfo(
										name='range',
										type=MINECRAFT_INT_RANGE,
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
								]
							),
							ArgumentInfo(
								name='__compare',
								type=makeLiteralsArgumentType(['<=', '<', '=', '>=', '>']),
								next=[
									ArgumentInfo(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentInfo(
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

	EXECUTE_INSTRUCTIONS.append(Keyword(name='if',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))

	EXECUTE_INSTRUCTIONS.append(Keyword(name='unless',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))


	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS = []

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword(name='block',
		next=[
			ArgumentInfo(
				name='targetPos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo(
								name='type',
								type=makeLiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo(
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

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword(name='bossbar',
		next=[
			ArgumentInfo(
				name='id',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentInfo(
						name='value',
						type=makeLiteralsArgumentType(['value', 'max']),
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword(name='entity',
		next=[
			ArgumentInfo(
				name='target',
				type=MINECRAFT_ENTITY,
				next=[
					ArgumentInfo(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo(
								name='type',
								type=makeLiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo(
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

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword(name='score',
		next=[
			ArgumentInfo(
				name='targets',
				description='Specifies score holder(s) whose score is to be overridden',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						description='A scoreboard objective',
						type=MINECRAFT_OBJECTIVE,
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword(name='storage',
		next=[
			ArgumentInfo(
				name='target',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentInfo(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo(
								name='type',
								type=makeLiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo(
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

	EXECUTE_INSTRUCTIONS.append(Keyword(name='store',
		next=[
			Keyword(
				name='result',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
			Keyword(
				name='success',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
		]
	))

	EXECUTE_INSTRUCTIONS.append(Keyword(name='run',
		next=[COMMANDS_ROOT],
	))

	BASIC_COMMAND_INFO['execute'].next = EXECUTE_INSTRUCTIONS

	BASIC_COMMAND_INFO['experience'].next = [
		Keyword(
			name='add',
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo(
									name='__levels',
									type=makeLiteralsArgumentType(['levels', 'points']),
								),
							]
						),
					]
				),
			]
		),
		Keyword(
			name='set',
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo(
									name='__levels',
									type=makeLiteralsArgumentType(['levels', 'points']),
								),
							]
						),
					]
				),
			],
		),
		Keyword(
			name='query',
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo(
							name='__levels',
							type=makeLiteralsArgumentType(['levels', 'points']),
						),
					]
				),
			]
		),
	]

	# fill <from> <to> <block> [destroy|hollow|keep|outline]
	# fill <from> <to> <block> replace [<filter>]
	BASIC_COMMAND_INFO['fill'].next = [
		ArgumentInfo(
			name='from',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo(
					name='to',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentInfo(
							name='block',
							type=MINECRAFT_BLOCK_STATE,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='option',
									type=makeLiteralsArgumentType(['destroy', 'hollow', 'keep', 'outline']),
								),
								Keyword(
									name='replace',
									next=[
										TERMINAL,
										ArgumentInfo(
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

	FORCELOAD_RANGE_ARG = ArgumentInfo(
		name='from',
		type=MINECRAFT_COLUMN_POS,
		next=[
			TERMINAL,
			ArgumentInfo(
				name='to',
				type=MINECRAFT_COLUMN_POS,
			),
		]
	)

	BASIC_COMMAND_INFO['forceload'].next = [
		Keyword(
			name='add',
			next=[
				FORCELOAD_RANGE_ARG,
			]
		),
		Keyword(
			name='remove',
			next=[
				Keyword('all'),
				FORCELOAD_RANGE_ARG,
			]
		),
		Keyword(
			name='query',
			next=[
				TERMINAL,
				ArgumentInfo(
					name='pos',
					type=MINECRAFT_COLUMN_POS,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['function'].next = [
		ArgumentInfo(
			name='name',
			type=MINECRAFT_FUNCTION,
		),
	]

	BASIC_COMMAND_INFO['gamemode'].next = [
		ArgumentInfo(
			name='gamemode',
			type=MINECRAFT_GAME_MODE,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='target',
					type=MINECRAFT_ENTITY,
				)
			]
		),
	]

	BASIC_COMMAND_INFO['gamerule'].next = [
		Keyword(
			name=gr.name,
			description=gr.description,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='value',
					type=gr.type,
				),
			]
		) for gr in version.gamerules
	]

	BASIC_COMMAND_INFO['give'].next = [
		ArgumentInfo(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='count',
							type=BRIGADIER_INTEGER,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['help'].next = []

	ITEM_TARGET = [
		Keyword(
			name='block',
			next=[
				ArgumentInfo(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword(
			name='entity',
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_SOURCE = [
		Keyword(
			name='block',
			next=[
				ArgumentInfo(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword(
			name='entity',
			next=[
				ArgumentInfo(
					name='sourceTarget',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_MODIFIER = [
		ArgumentInfo(
			name='modifier',
			type=MINECRAFT_RESOURCE_LOCATION,
		),
	]

	BASIC_COMMAND_INFO['item'].next = [
		Keyword(
			name='modify',
			next=[
				Switch(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentInfo(
							name='slot',
							type=MINECRAFT_NBT_PATH,
							next=[*ITEM_MODIFIER]
						),
					]
				),
			]
		),
		Keyword(
			name='replace',
			next=[
				Switch(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentInfo(
							name='slot',
							type=MINECRAFT_NBT_PATH,
							next=[
								Keyword(
									name='with',
									next=[
										ArgumentInfo(
											name='item',
											type=MINECRAFT_ITEM_STACK,
											next=[
												TERMINAL,
												ArgumentInfo(
													name='count',
													type=BRIGADIER_INTEGER,
													args={'min': 1, 'max': 64},
												),
											]
										),
									]
								),
								Keyword(
									name='from',
									next=[
										Switch(
											name='SOURCE',
											options=ITEM_SOURCE,
											next=[
												ArgumentInfo(
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

	BASIC_COMMAND_INFO['kick'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['kill'].next = [
		TERMINAL,  # An entity is required to run the command without args
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
		),
	]

	BASIC_COMMAND_INFO['list'].next = [
		TERMINAL,
		Keyword('uuids'),
	]

	BASIC_COMMAND_INFO['locate'].next = [
		ArgumentInfo(
			name='StructureType',
			type=makeLiteralsArgumentType(list(version.structures)),
		),
	]

	BASIC_COMMAND_INFO['locatebiome'].next = [
		ArgumentInfo(
			name='biome',
			type=DPE_BIOME_ID,
		),
	]

	LOOT_TARGETS = [
		Keyword(
			name='spawn',
			next=[
				ArgumentInfo(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
					args={'type': float}
				),
			]
		),
		Keyword(
			name='replace',
			next=[
				Switch(
					name='REPLACE',
					options=[
						Keyword(
							name='entity',
							next=[
								ArgumentInfo(
									name='entities',
									type=MINECRAFT_ENTITY,
								),
							]
						),
						Keyword(
							name='block',
							next=[
								ArgumentInfo(
									name='targetPos',
									type=MINECRAFT_BLOCK_POS,
								),
							]
						),
					],
					next=[
						ArgumentInfo(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='count',
									type=BRIGADIER_INTEGER,
								),
							]
						),

					]
				),
			]
		),
		Keyword(
			name='give',
			next=[
				ArgumentInfo(
					name='players',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword(
			name='insert',
			next=[
				ArgumentInfo(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
	]

	LOOT_SOURCES = [
		Keyword(
			name='fish',
			next=[
				ArgumentInfo(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='hand',
									type=makeLiteralsArgumentType(['mainhand', 'offhand']),
								),
								ArgumentInfo(
									name='tool',
									type=MINECRAFT_ITEM_STACK,
								),
							]
						),
					]
				),
			]
		),
		Keyword(
			name='loot',
			next=[
				ArgumentInfo(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
		Keyword(
			name='kill',
			next=[
				ArgumentInfo(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword(
			name='mine',
			next=[
				ArgumentInfo(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='hand',
							type=makeLiteralsArgumentType(['mainhand', 'offhand']),
						),
						ArgumentInfo(
							name='tool',
							type=MINECRAFT_ITEM_STACK,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['loot'].next = [
		Switch(
			name='TARGET',
			options=LOOT_TARGETS,
			next=[
				Switch(
					name='SOURCE',
					options=LOOT_SOURCES,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['me'].next = [
		ArgumentInfo(
			name='action',
			type=MINECRAFT_MESSAGE,
		)
	]

	BASIC_COMMAND_INFO['msg'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='message',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['op'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['pardon'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['pardon-ip'].next = [
		ArgumentInfo(
			name='target',
			type=BRIGADIER_STRING,
		),
	]

	# particle <name> [<pos>] [<delta> <speed> <count> [force|normal] [<viewers>]]

	PARTICLE_ARGUMENTS = [
		TERMINAL,
		ArgumentInfo(
			name='pos',
			type=MINECRAFT_VEC3,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='delta',
					type=MINECRAFT_VEC3,
					next=[
						ArgumentInfo(
							name='speed',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo(
									name='count',
									type=BRIGADIER_INTEGER,
									next=[
										TERMINAL,
										ArgumentInfo(
											name='display_mode',
											type=makeLiteralsArgumentType(['force', 'normal']),
											next=[
												TERMINAL,
												ArgumentInfo(
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
		Keyword(
			name='dust',
			next=[
				ArgumentInfo(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentInfo(
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
		Keyword(
			name='dust_color_transition',
			next=[
				ArgumentInfo(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentInfo(
											name='size',
											type=BRIGADIER_FLOAT,
											next=[
												ArgumentInfo(
													name='red',
													type=BRIGADIER_FLOAT,
													next=[
														ArgumentInfo(
															name='green',
															type=BRIGADIER_FLOAT,
															next=[
																ArgumentInfo(
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
		Keyword(
			name='block',
			next=[
				ArgumentInfo(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword(
			name='falling_dust',
			next=[
				ArgumentInfo(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword(
			name='item',
			next=[
				ArgumentInfo(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword(
			name='vibration',
			next=[
				ArgumentInfo(
					name='x_start',
					type=BRIGADIER_DOUBLE,
					next=[
						ArgumentInfo(
							name='y_start',
							type=BRIGADIER_DOUBLE,
							next=[
								ArgumentInfo(
									name='z_start',
									type=BRIGADIER_DOUBLE,
									next=[
										ArgumentInfo(
											name='x_end',
											type=BRIGADIER_DOUBLE,
											next=[
												ArgumentInfo(
													name='y_end',
													type=BRIGADIER_DOUBLE,
													next=[
														ArgumentInfo(
															name='z_end',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentInfo(
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

	BASIC_COMMAND_INFO['particle'].next = [
		*_SPECIAL_PARTICLES,
		ArgumentInfo(
			name='name',
			type=MINECRAFT_PARTICLE,
			next=PARTICLE_ARGUMENTS
		),
	]

	BASIC_COMMAND_INFO['perf'].next = [
		Keyword('start'),
		Keyword('stop'),
	]

	# playsound <sound> <source> <targets> [<pos>] [<volume>] [<pitch>] [<minVolume>]
	BASIC_COMMAND_INFO['playsound'].next = [
		ArgumentInfo(
			name='sound',
			type=MINECRAFT_RESOURCE_LOCATION,
			next=[
				ArgumentInfo(
					name='source',
					type=makeLiteralsArgumentType(['master', 'music', 'record', 'weather', 'block', 'hostile', 'neutral', 'player', 'ambient', 'voice']),
					next=[
						ArgumentInfo(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='pos',
									type=MINECRAFT_VEC3,
									next=[
										TERMINAL,
										ArgumentInfo(
											name='volume',
											type=BRIGADIER_FLOAT,
											next=[
												TERMINAL,
												ArgumentInfo(
													name='pitch',
													type=BRIGADIER_FLOAT,
													next=[
														TERMINAL,
														ArgumentInfo(
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

	BASIC_COMMAND_INFO['publish'].next = [
		TERMINAL,
		ArgumentInfo(
			name='port',
			type=BRIGADIER_INTEGER,
		),
	]

	# recipe (give|take) <targets> (*|<recipe>)
	BASIC_COMMAND_INFO['recipe'].next = [
		ArgumentInfo(
			name='action',
			type=makeLiteralsArgumentType(['give', 'take']),
			next=[
				ArgumentInfo(
					name='target',
					type=MINECRAFT_ENTITY,
					next=[
						Keyword('*'),
						ArgumentInfo(
							name='recipe',
							type=MINECRAFT_RESOURCE_LOCATION,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['reload'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['replaceitem'].next = [
		ArgumentInfo(
			name='OUTDATED!',
			type=MINECRAFT_MESSAGE,
		),
	]  # This command was superseded by the /item command in Java Edition 1.17.

	BASIC_COMMAND_INFO['save-all'].next = [
		TERMINAL,
		Keyword('flush'),
	]

	BASIC_COMMAND_INFO['save-off'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['save-on'].next = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['say'].next = [
		ArgumentInfo(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]

	# schedule function <function> <time> [append|replace]
	# schedule clear <function>
	BASIC_COMMAND_INFO['schedule'].next = [
		Keyword(
			name='function',
			next=[
				ArgumentInfo(
					name='function',
					type=MINECRAFT_FUNCTION,
					next=[
						ArgumentInfo(
							name='time',
							type=MINECRAFT_TIME,
							next=[
								TERMINAL,
								ArgumentInfo(
									name='replace_behaviour',
									type=makeLiteralsArgumentType(['append', 'replace']),
								),
							]
						),
					]
				),
			]
		),
		Keyword(
			name='clear',
			next=[
				ArgumentInfo(
					name='function',
					type=MINECRAFT_FUNCTION,
				),
			]
		),

	]

	# scoreboard Command:
	SCOREBOARD_OBJECTIVES = []

	SCOREBOARD_OBJECTIVES.append(Keyword(name='list'))

	# scoreboard objectives add <objective> <criteria> [<displayName>]
	SCOREBOARD_OBJECTIVES.append(Keyword(name='add',
		next=[
			ArgumentInfo(
				name='objective',
				type=BRIGADIER_STRING,
				next=[
					ArgumentInfo(
						name='criteria',
						type=MINECRAFT_OBJECTIVE_CRITERIA,
						next=[
							TERMINAL,
							ArgumentInfo(
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
	SCOREBOARD_OBJECTIVES.append(Keyword(name='remove',
		next=[
			ArgumentInfo(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
			),
		]
	))

	# scoreboard objectives setdisplay <slot> [<objective>]
	SCOREBOARD_OBJECTIVES.append(Keyword(name='setdisplay',
		next=[
			ArgumentInfo(
				name='slot',
				type=MINECRAFT_SCOREBOARD_SLOT,
				next=[
					TERMINAL,
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard objectives modify <objective> displayname <displayName>
	# scoreboard objectives modify <objective> rendertype (hearts|integer)
	SCOREBOARD_OBJECTIVES.append(Keyword(name='modify',
		next=[
			ArgumentInfo(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
				next=[
					Keyword(
						name='displayname',
						next=[
							ArgumentInfo(
								name='displayName',
								type=MINECRAFT_COMPONENT,
							),
						]
					),
					Keyword(
						name='rendertype',
						next=[
							ArgumentInfo(
								name='rendertype',
								type=makeLiteralsArgumentType(['hearts', 'integer']),
							),
						]
					),
				]
			),
		]
	))


	SCOREBOARD_PLAYERS = []

	# scoreboard players list [<target>]
	SCOREBOARD_PLAYERS.append(Keyword(name='list',
		next=[
			TERMINAL,
			ArgumentInfo(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
			),
		]
	))

	# scoreboard players get <target> <objective>
	SCOREBOARD_PLAYERS.append(Keyword(name='get',
		next=[
			ArgumentInfo(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players set <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(Keyword(name='set',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo(
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
	SCOREBOARD_PLAYERS.append(Keyword(name='add',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo(
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
	SCOREBOARD_PLAYERS.append(Keyword(name='remove',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo(
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
	SCOREBOARD_PLAYERS.append(Keyword(name='reset',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					TERMINAL,
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players enable <targets> <objective>
	SCOREBOARD_PLAYERS.append(Keyword(name='enable',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players operation <targets> <targetObjective> <operation> <source> <sourceObjective>
	SCOREBOARD_PLAYERS.append(Keyword(name='operation',
		next=[
			ArgumentInfo(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo(
								name='operation',
								type=MINECRAFT_OPERATION,
								next=[
									ArgumentInfo(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentInfo(
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

	BASIC_COMMAND_INFO['scoreboard'].next = [
		Keyword(
			name='objectives',
			next=SCOREBOARD_OBJECTIVES
		),
		Keyword(
			name='players',
			next=SCOREBOARD_PLAYERS
		),
	]

	BASIC_COMMAND_INFO['seed'].next = [TERMINAL]  # has no arguments!

	# setblock <pos> <block> [destroy|keep|replace]
	BASIC_COMMAND_INFO['setblock'].next = [
		ArgumentInfo(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo(
					name='block',
					type=MINECRAFT_BLOCK_STATE,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='operation',
							type=makeLiteralsArgumentType(['destroy', 'keep', 'replace']),
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['setidletimeout'].next = [
		ArgumentInfo(
			name='minutes',
			type=BRIGADIER_INTEGER,
		),
	]

	# setworldspawn [<pos>] [<angle>]
	BASIC_COMMAND_INFO['setworldspawn'].next = [
		TERMINAL,
		ArgumentInfo(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='angle',
					type=MINECRAFT_ANGLE,
				),
			]
		),
	]

	# spawnpoint [<targets>] [<pos>] [<angle>]
	BASIC_COMMAND_INFO['spawnpoint'].next = [
		TERMINAL,
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='angle',
							type=MINECRAFT_ANGLE,
						),
					]
				),
			]
		),
	]

	# spectate <target> [<player>]
	BASIC_COMMAND_INFO['spectate'].next = [
		ArgumentInfo(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='player',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	# spreadplayers <center> <spreadDistance> <maxRange> <respectTeams> <targets>
	# spreadplayers <center> <spreadDistance> <maxRange> under <maxHeight> <respectTeams> <targets>
	SPREADPLAYERS_RESPECT_TEAMS = [
		ArgumentInfo(
			name='respectTeams',
			type=BRIGADIER_BOOL,
			next=[
				ArgumentInfo(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['spreadplayers'].next = [
		ArgumentInfo(
			name='center',
			type=MINECRAFT_VEC2,
			next=[
				ArgumentInfo(
					name='spreadDistance',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo(
							name='maxRange',
							type=BRIGADIER_FLOAT,
							next=[
								Keyword(
									name='under',
									next=[
										ArgumentInfo(
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

	BASIC_COMMAND_INFO['stop'].next = [TERMINAL]  # has no arguments!

	# stopsound <targets> [<source>] [<sound>]
	BASIC_COMMAND_INFO['stopsound'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='source',
					type=makeLiteralsArgumentType(['*', 'master', 'music', 'record', 'weather', 'block', 'hostile', 'neutral', 'player', 'ambient', 'voice']),
					next=[
						TERMINAL,
						ArgumentInfo(
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
	BASIC_COMMAND_INFO['summon'].next = [
		ArgumentInfo(
			name='entity',
			type=MINECRAFT_ENTITY_SUMMON,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='pos',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentInfo(
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
	BASIC_COMMAND_INFO['tag'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				Keyword(
					name='add',
					next=[
						ArgumentInfo(
							name='name',
							type=BRIGADIER_STRING,
						),
					]
				),
				Keyword('list'),
				Keyword(
					name='remove',
					next=[
						ArgumentInfo(
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
	BASIC_COMMAND_INFO['team'].next = [
		Keyword(
			name='list',
			description="Lists all teams, with their display names and the amount of entities in them. The optional `<team>` can be used to specify a particular team.",
			next=[
				TERMINAL,
				ArgumentInfo(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword(
			name='add',
			description="Creates a team with the given name and optional display name. `<displayName>` defaults to `<objective>` when unspecified.",
			next=[
				ArgumentInfo(
					name='team',
					type=BRIGADIER_STRING,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='displayName',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			]
		),
		Keyword(
			name='remove',
			description="Deletes the specified team.",
			next=[
				ArgumentInfo(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword(
			name='empty',
			description="Removes all members from the named team.",
			next=[
				ArgumentInfo(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword(
			name='join',
			description="Assigns the specified entities to the specified team. If no entities is specified, makes the executor join the team.",
			next=[
				ArgumentInfo(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='members',
							type=MINECRAFT_SCORE_HOLDER,
						),
					]
				),
			]
		),
		Keyword(
			name='leave',
			description="Makes the specified entities leave their teams.",
			next=[
				ArgumentInfo(
					name='members',
					type=MINECRAFT_SCORE_HOLDER,
				),
			]
		),
		Keyword(
			name='modify',
			description="Modifies the options of the specified team.",
			next=[
				ArgumentInfo(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						Switch(
							name='option',
							options=[
								Keyword(
									name='displayName',
									description="Set the display name of the team.",
									next=[
										ArgumentInfo(
											name='displayName',
											type=MINECRAFT_COMPONENT,
											description="Specifies the team name to be displayed. Must be a raw JSON text.",
										),
									]
								),
								Keyword(
									name='color',
									description="Decide the color of the team and players in chat, above their head, on the Tab menu, and on the sidebar. Also changes the color of the outline of the entities caused by the Glowing effect.",
									next=[
										ArgumentInfo(
											name='value',
											type=MINECRAFT_COLOR,
											description="Must be a color.\n\nDefaults to reset. If reset, names are shown in default color and formatting.",
										),
									]
								),
								Keyword(
									name='friendlyFire',
									description="Enable/Disable players inflicting damage on each other when on the same team. (Note: players can still inflict status effects on each other.) Does not affect some non-player entities in a team.",
									next=[
										ArgumentInfo(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Enable players inflicting damage on each other when in the same team.\n  - false - Disable players inflicting damage on each other when in the same team.",
										),
									]
								),
								Keyword(
									name='seeFriendlyInvisibles',
									description="Decide players can see invisible players on their team as whether semi-transparent or completely invisible.",
									next=[
										ArgumentInfo(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Can see invisible players on the same team semi-transparently.\n  - false - Cannot see invisible players on the same team.",
										),
									]
								),
								Keyword(
									name='nametagVisibility',
									description="Decide whose name tags above their heads can be seen.",
									next=[
										Keyword(
											name='never',
											description="Name above player's head cannot be seen by any players.",
										),
										Keyword(
											name='hideForOtherTeams',
											description="Name above player's head can be seen only by players in the same team.",
										),
										Keyword(
											name='hideForOwnTeam',
											description="Name above player's head cannot be seen by all the players in the same team.",
										),
										Keyword(
											name='always',
											description="(Default) Name above player's head can be seen by all the players.",
										),
									]
								),
								Keyword(
									name='deathMessageVisibility',
									description="Control the visibility of death messages for players.",
									next=[
										Keyword(
											name='never',
											description="Hide death message for all the players.",
										),
										Keyword(
											name='hideForOtherTeams',
											description="Hide death message to all the players who are not in the same team.",
										),
										Keyword(
											name='hideForOwnTeam',
											description="Hide death message to players in the same team.",
										),
										Keyword(
											name='always',
											description="(Default) Make death message visible to all the players.",
										),
									]
								),
								Keyword(
									name='collisionRule',
									description="Controls the way the entities on the team collide with other entities.",
									next=[
										Keyword(
											name='always',
											description="(Default) Normal collision.",
										),
										Keyword(
											name='never',
											description="No entities can push entities in this team.",
										),
										Keyword(
											name='pushOtherTeams',
											description="Entities in this team can be pushed only by other entities in the same team.",
										),
										Keyword(
											name='pushOwnTeam',
											description="Entities in this team cannot be pushed by another entity in this team.",
										),
									]
								),
								Keyword(
									name='prefix',
									description="Modifies the prefix that displays before players' names.",
									next=[
										ArgumentInfo(
											name='prefix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the prefix to display. Must be a raw JSON text.",
										),
									]
								),
								Keyword(
									name='suffix',
									description="Modifies the suffix that displays before players' names.",
									next=[
										ArgumentInfo(
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

	BASIC_COMMAND_INFO['teammsg'].next = [
		ArgumentInfo(
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
	BASIC_COMMAND_INFO['teleport'].next = [
		# ArgumentInfo(
		# 	name='destination',
		# 	type=MINECRAFT_ENTITY,
		# ),
		ArgumentInfo(
			name='location',
			type=MINECRAFT_VEC3,
		),
		ArgumentInfo(
			name='targets|destination',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo(
					name='location',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentInfo(
							name='rotation',
							type=MINECRAFT_ROTATION,
						),
						Keyword(
							name='facing',
							next=[
								ArgumentInfo(
									name='facingLocation',
									type=MINECRAFT_VEC3,
								),
								Keyword(
									name='entity',
									next=[
										ArgumentInfo(
											name='facingEntity',
											type=MINECRAFT_ENTITY,
											next=[
												TERMINAL,
												ArgumentInfo(
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
				ArgumentInfo(
					name='destination',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['tell'].next = BASIC_COMMAND_INFO['msg'].next

	# tellraw <targets> <message>
	BASIC_COMMAND_INFO['tellraw'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='message',
					type=MINECRAFT_COMPONENT,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['testfor'].next = []  # This command has been removed

	BASIC_COMMAND_INFO['testforblock'].next = []  # This command has been removed

	BASIC_COMMAND_INFO['testforblocks'].next = []  # This command has been removed

	BASIC_COMMAND_INFO['time'].next = [
		Keyword(
			name='add',
			description="Adds `<time>` to the in-game daytime.",
			next=[
				ArgumentInfo(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
		Keyword(
			name='query',
			description="Queries current time.",
			next=[
				ArgumentInfo(
					name='daytime|gametime|day',
					type=makeLiteralsArgumentType(['daytime', 'gametime', 'day']),
				),
			]
		),
		Keyword(
			name='set',
			next=[
				ArgumentInfo(
					name='timeSpec',
					type=makeLiteralsArgumentType(['day', 'night', 'noon', 'midnight']),
				),
			]
		),
		Keyword(
			name='set',
			next=[
				ArgumentInfo(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
	]

	# title <targets> (clear|reset)
	# title <targets> (title|subtitle|actionbar) <title>
	# title <targets> times <fadeIn> <stay> <fadeOut>
	BASIC_COMMAND_INFO['title'].next = [
		ArgumentInfo(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo(
					name='clear|reset',
					type=makeLiteralsArgumentType(['clear', 'reset']),
				),
				ArgumentInfo(
					name='title|subtitle|actionbar',
					type=makeLiteralsArgumentType(['title', 'subtitle', 'actionbar']),
					next=[
						ArgumentInfo(
							name='title',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
				Keyword(
					name='times',
					next=[
						ArgumentInfo(
							name='fadeIn',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo(
									name='stay',
									type=BRIGADIER_INTEGER,
									next=[
										ArgumentInfo(
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

	BASIC_COMMAND_INFO['tm'].next = BASIC_COMMAND_INFO['teammsg'].next

	# BASIC_COMMAND_INFO['toggledownfall'].next = []  has been removed

	BASIC_COMMAND_INFO['tp'].next = BASIC_COMMAND_INFO['teleport'].next

	# trigger <objective>
	# trigger <objective> add <value>
	# trigger <objective> set <value>
	BASIC_COMMAND_INFO['trigger'].next = [
		ArgumentInfo(
			name='objective',
			type=MINECRAFT_OBJECTIVE,
			next=[
				TERMINAL,
				Keyword(
					name='add',
					next=[
						ArgumentInfo(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					]
				),
				Keyword(
					name='set',
					next=[
						ArgumentInfo(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			]
		),
	]

	BASIC_COMMAND_INFO['w'].next = BASIC_COMMAND_INFO['msg'].next

	# weather (clear|rain|thunder) [<duration>]
	BASIC_COMMAND_INFO['weather'].next = [
		ArgumentInfo(
			name='objective',
			type=makeLiteralsArgumentType(['clear', 'rain', 'thunder']),
			next=[
				TERMINAL,
				ArgumentInfo(
					name='duration',
					type=BRIGADIER_INTEGER,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['whitelist'].next = []  # TODO: BASIC_COMMAND_INFO['whitelist'].next

	BASIC_COMMAND_INFO['worldborder'].next = []  # TODO: BASIC_COMMAND_INFO['worldborder'].next

	BASIC_COMMAND_INFO['xp'].next = BASIC_COMMAND_INFO['experience'].next
