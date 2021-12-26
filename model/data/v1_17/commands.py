from Cat.utils.collections_ import ChainedList
from model.commands.argumentTypes import *
from model.commands.command import CommandInfo, Keyword, ArgumentInfo, TERMINAL, COMMANDS_ROOT, Switch
from model.data.mcVersions import MCVersion


def fillCommandsFor1_17(version: MCVersion) -> None:
	_BASIC_COMMAND_INFO_LIST = [
		CommandInfo.create(
			command='?',
			description='An alias of /help. Provides help for commands.',
			opLevel=0,
		),
		CommandInfo.create(
			command='advancement',
			description='Gives, removes, or checks player advancements.',
			opLevel=2,
		),
		CommandInfo.create(
			command='attribute',
			description='Queries, adds, removes or sets an entity attribute.',
			opLevel=2,
		),
		CommandInfo.create(
			command='ban',
			description='Adds player to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='ban-ip',
			description='Adds IP address to banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='banlist',
			description='Displays banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='bossbar',
			description='Creates and modifies bossbars.',
			opLevel=2,
		),
		CommandInfo.create(
			command='clear',
			description='Clears items from player inventory.',
			opLevel=2,
		),
		CommandInfo.create(
			command='clone',
			description='Copies blocks from one place to another.',
			opLevel=2,
		),
		CommandInfo.create(
			command='data',
			description='Gets, merges, modifies and removes block entity and entity NBT data.',
			opLevel=2,
		),
		CommandInfo.create(
			command='datapack',
			description='Controls loaded data packs.',
			opLevel=2,
		),
		CommandInfo.create(
			command='debug',
			description='Starts or stops a debugging session.',
			opLevel=3,
		),
		CommandInfo.create(
			command='defaultgamemode',
			description='Sets the default game mode.',
			opLevel=2,
		),
		CommandInfo.create(
			command='deop',
			description='Revokes operator status from a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='difficulty',
			description='Sets the difficulty level.',
			opLevel=2,
		),
		CommandInfo.create(
			command='effect',
			description='Add or remove status effects.',
			opLevel=2,
		),
		CommandInfo.create(
			command='enchant',
			description="Adds an enchantment to a player's selected item.",
			opLevel=2,
		),
		CommandInfo.create(
			command='execute',
			description='Executes another command.',
			opLevel=2,
		),
		CommandInfo.create(
			command='experience',
			description='An alias of /xp. Adds or removes player experience.',
			opLevel=2,
		),
		CommandInfo.create(
			command='fill',
			description='Fills a region with a specific block.',
			opLevel=2,
		),
		CommandInfo.create(
			command='forceload',
			description='Forces chunks to constantly be loaded or not.',
			opLevel=2,
		),
		CommandInfo.create(
			command='function',
			description='Runs a function.',
			opLevel=2,
		),
		CommandInfo.create(
			command='gamemode',
			description="Sets a player's game mode.",
			opLevel=2,
		),
		CommandInfo.create(
			command='gamerule',
			description='Sets or queries a game rule value.',
			opLevel=2,
		),
		CommandInfo.create(
			command='give',
			description='Gives an item to a player.',
			opLevel=2,
		),
		CommandInfo.create(
			command='help',
			description='An alias of /?. Provides help for commands.',
			opLevel=0,
		),
		CommandInfo.create(
			command='item',
			description='Manipulates items in inventories.',
			opLevel=2,
		),
		CommandInfo.create(
			command='kick',
			description='Kicks a player off a server.',
			opLevel=3,
		),
		CommandInfo.create(
			command='kill',
			description='Kills entities (players, mobs, items, etc.).',
			opLevel=2,
		),
		CommandInfo.create(
			command='list',
			description='Lists players on the server.',
			opLevel=0,
		),
		CommandInfo.create(
			command='locate',
			description='Locates closest structure.',
			opLevel=2,
		),
		CommandInfo.create(
			command='locatebiome',
			description='Locates closest biome.',
			opLevel=2,
		),
		CommandInfo.create(
			command='loot',
			description='Drops items from an inventory slot onto the ground.',
			opLevel=2,
		),
		CommandInfo.create(
			command='me',
			description='Displays a message about the sender.',
			opLevel=0,
		),
		CommandInfo.create(
			command='msg',
			description='An alias of /tell and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo.create(
			command='op',
			description='Grants operator status to a player.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='pardon',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='pardon-ip',
			description='Removes entries from the banlist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='particle',
			description='Creates particles.',
			opLevel=2,
		),
		CommandInfo.create(
			command='perf',
			description='Captures info and metrics about the game for 10 seconds.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo.create(
			command='playsound',
			description='Plays a sound.',
			opLevel=2,
		),
		CommandInfo.create(
			command='publish',
			description='Opens single-player world to local network.',
			opLevel=4,
			availableInMP=False
		),
		CommandInfo.create(
			command='recipe',
			description='Gives or takes player recipes.',
			opLevel=2,
		),
		CommandInfo.create(
			command='reload',
			description='Reloads loot tables, advancements, and functions from disk.',
			opLevel=2,
		),
		CommandInfo.create(
			command='replaceitem',
			description='Replaces items in inventories.',
			removed=True,
			removedVersion='1.17',
			removedComment='Replaced with `/item replace`',
			opLevel=2,
		),
		CommandInfo.create(
			command='save-all',
			description='Saves the server to disk.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo.create(
			command='save-off',
			description='Disables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo.create(
			command='save-on',
			description='Enables automatic server saves.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo.create(
			command='say',
			description='Displays a message to multiple players.',
			opLevel=2,
		),
		CommandInfo.create(
			command='schedule',
			description='Delays the execution of a function.',
			opLevel=2,
		),
		CommandInfo.create(
			command='scoreboard',
			description='Manages scoreboard objectives and players.',
			opLevel=2,
		),
		CommandInfo.create(
			command='seed',
			description='Displays the world seed.',
			opLevel='0 in singleplayer, 2 in multiplayer',
		),
		CommandInfo.create(
			command='setblock',
			description='Changes a block to another block.',
			opLevel=2,
		),
		CommandInfo.create(
			command='setidletimeout',
			description='Sets the time before idle players are kicked.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='setworldspawn',
			description='Sets the world spawn.',
			opLevel=2,
		),
		CommandInfo.create(
			command='spawnpoint',
			description='Sets the spawn point for a player.',
			opLevel=2,
		),
		CommandInfo.create(
			command='spectate',
			description='Make one player in spectator mode spectate an entity.',
			opLevel=2,
		),
		CommandInfo.create(
			command='spreadplayers',
			description='Teleports entities to random locations.',
			opLevel=2,
		),
		CommandInfo.create(
			command='stop',
			description='Stops a server.',
			opLevel=4,
			availableInSP=False
		),
		CommandInfo.create(
			command='stopsound',
			description='Stops a sound.',
			opLevel=2,
		),
		CommandInfo.create(
			command='summon',
			description='Summons an entity.',
			opLevel=2,
		),
		CommandInfo.create(
			command='tag',
			description='Controls entity tags.',
			opLevel=2,
		),
		CommandInfo.create(
			command='team',
			description='Controls teams.',
			opLevel=2,
		),
		CommandInfo.create(
			command='teammsg',
			description='An alias of /tm. Specifies the message to send to team.',
			opLevel=0,
		),
		CommandInfo.create(
			command='teleport',
			description='An alias of /tp. Teleports entities.',
			opLevel=2,
		),
		CommandInfo.create(
			command='tell',
			description='An alias of /msg and /w. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo.create(
			command='tellraw',
			description='Displays a JSON message to players.',
			opLevel=2,
		),
		CommandInfo.create(
			command='testfor',
			description='Counts entities matching specified conditions.',
			removed=True,
			removedVersion='1.13',
			removedComment='',  # TODO: removedComment for '/testfor' command
			opLevel=2,
		),
		CommandInfo.create(
			command='testforblock',
			description='Tests whether a block is in a location.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead',
			opLevel=2,
		),
		CommandInfo.create(
			command='testforblocks',
			description='Tests whether the blocks in two regions match.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/execute if` instead',
			opLevel=2,
		),
		CommandInfo.create(
			command='time',
			description="Changes or queries the world's game time.",
			opLevel=2,
		),
		CommandInfo.create(
			command='title',
			description='Manages screen titles.',
			opLevel=2,
		),
		CommandInfo.create(
			command='tm',
			description='An alias of /teammsg. Specifies the message to send to team.',
			opLevel=0,
		),
		CommandInfo.create(
			command='toggledownfall',
			description='Toggles the weather.',
			removed=True,
			removedVersion='1.13',
			removedComment='Use `/weather ...` instead',
			opLevel=1,
		),
		CommandInfo.create(
			command='tp',
			description='An alias of /teleport. Teleports entities.',
			opLevel=2,
		),
		CommandInfo.create(
			command='trigger',
			description='Sets a trigger to be activated.',
			opLevel=0,
		),
		CommandInfo.create(
			command='w',
			description='An alias of /tell and /msg. Displays a private message to other players.',
			opLevel=0,
		),
		CommandInfo.create(
			command='weather',
			description='Sets the weather.',
			opLevel=2,
		),
		CommandInfo.create(
			command='whitelist',
			description='Manages server whitelist.',
			opLevel=3,
			availableInSP=False
		),
		CommandInfo.create(
			command='worldborder',
			description='Manages the world border.',
			opLevel=2,
		),
		CommandInfo.create(
			command='xp',
			description='An alias of /experience [Java Edition only]. Adds or removes player experience.',
			opLevel=2,
		)
	]

	BASIC_COMMAND_INFO: dict[str, CommandInfo] = {c.command: c for c in _BASIC_COMMAND_INFO_LIST}
	version.commands = BASIC_COMMAND_INFO

	BASIC_COMMAND_INFO['?'].argument = []

	BASIC_COMMAND_INFO['advancement'].argument = [
		ArgumentInfo.create(
			name='__action',
			type=LiteralsArgumentType(['grant', 'revoke']),
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						Keyword.create(
							name='everything',
						),
						Keyword.create(
							name='only',
							next=[
								ArgumentInfo.create(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='criterion',
											type=BRIGADIER_STRING,
										),
									]
								),
							]
						),
						Keyword.create(
							name='from',
							next=[
								ArgumentInfo.create(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
								),
							]
						),
						Keyword.create(
							name='through',
							next=[
								ArgumentInfo.create(
									name='advancement',
									type=MINECRAFT_RESOURCE_LOCATION,
								),
							]
						),
						Keyword.create(
							name='until',
							next=[
								ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['attribute'].argument = [
		ArgumentInfo.create(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='attribute',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						Keyword.create(
							name='get',
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='scale',
									type=BRIGADIER_DOUBLE,
								),
							]
						),
						Keyword.create(
							name='base',
							next=[
								Keyword.create(
									name='get',
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='scale',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
								Keyword.create(
									name='set',
									next=[
										ArgumentInfo.create(
											name='value',
											type=BRIGADIER_DOUBLE,
										),
									]
								),
							],
						),
						Keyword.create(
							name='modifier',
							next=[
								Keyword.create(
									name='add',
									next=[
										ArgumentInfo.create(
											name='uuid',
											type=MINECRAFT_UUID,
											next=[
												ArgumentInfo.create(
													name='name',
													type=BRIGADIER_STRING,
													next=[
														ArgumentInfo.create(
															name='value',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentInfo.create(
																	name='uuid',
																	type=LiteralsArgumentType(['add', 'multiply', 'multiply_base']),
																),
															]
														),
													]
												),
											]
										),
									]
								),
								Keyword.create(
									name='remove',
									next=[
										ArgumentInfo.create(
											name='uuid',
											type=MINECRAFT_UUID,
										),
									]
								),
								Keyword.create(
									name='value',
									next=[
										Keyword.create(
											name='get',
											next=[
												ArgumentInfo.create(
													name='uuid',
													type=MINECRAFT_UUID,
													next=[
														TERMINAL,
														ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['ban'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['ban-ip'].argument = [
		ArgumentInfo.create(
			name='target',
			type=BRIGADIER_STRING,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['banlist'].argument = [
		TERMINAL,
		Keyword.create(
			name='ips',
		),
		Keyword.create(
			name='players',
		),
	]

	BASIC_COMMAND_INFO['bossbar'].argument = [
		Keyword.create(
			name='add',
			next=[
				ArgumentInfo.create(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo.create(
							name='name',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			],
		),
		Keyword.create(
			name='get',
			next=[
				ArgumentInfo.create(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo.create(
							name='__setting',
							type=LiteralsArgumentType(['max', 'players', 'value', 'visible']),
						),
					]
				),
			],
		),
		Keyword.create(
			name='list',
		),
		Keyword.create(
			name='remove',
			next=[
				ArgumentInfo.create(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			],
		),
		Keyword.create(
			name='set',
			next=[
				ArgumentInfo.create(
					name='id',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						Keyword.create(
							name='color',
							next=[
								ArgumentInfo.create(
									name='color',
									type=LiteralsArgumentType(['blue', 'green', 'pink', 'purple', 'red', 'white', 'yellow']),
								),
							],
						),
						Keyword.create(
							name='max',
							next=[
								ArgumentInfo.create(
									name='max',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						Keyword.create(
							name='name',
							next=[
								ArgumentInfo.create(
									name='name',
									type=MINECRAFT_COMPONENT,
								),
							],
						),
						Keyword.create(
							name='players',
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='targets',
									type=MINECRAFT_ENTITY,
								),
							],
						),
						Keyword.create(
							name='style',
							next=[
								ArgumentInfo.create(
									name='style',
									type=LiteralsArgumentType(['notched_6', 'notched_10', 'notched_12', 'notched_20', 'progress']),
								),
							],
						),
						Keyword.create(
							name='value	',
							next=[
								ArgumentInfo.create(
									name='value',
									type=BRIGADIER_INTEGER,
								),
							],
						),
						Keyword.create(
							name='visible',
							next=[
								ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['clear'].argument = [
		TERMINAL,
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='item',
					type=MINECRAFT_ITEM_PREDICATE,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='maxCount',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			],
		),
	]

	BASIC_COMMAND_INFO['clone'].argument = [
		ArgumentInfo.create(
			name='begin',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo.create(
					name='end',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentInfo.create(
							name='destination',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='maskMode',
									type=LiteralsArgumentType(['replace', 'masked']),
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='cloneMode',
											type=LiteralsArgumentType(['force', 'move', 'normal']),
										),
									],
								),
								Keyword.create(
									name='filtered',
									next=[
										ArgumentInfo.create(
											name='filter',
											type=MINECRAFT_BLOCK_PREDICATE,
											next=[
												TERMINAL,
												ArgumentInfo.create(
													name='cloneMode',
													type=LiteralsArgumentType(['force', 'move', 'normal']),
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
		Keyword.create(
			name='block',
			next=[
				ArgumentInfo.create(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword.create(
			name='entity',
			next=[
				ArgumentInfo.create(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword.create(
			name='storage',
			next=[
				ArgumentInfo.create(
					name='target',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	DATA_MODIFICATION = [
		Keyword.create(
			name='append',
		),
		Keyword.create(
			name='insert',
			next=[
				ArgumentInfo.create(
					name='index',
					type=BRIGADIER_INTEGER,
				),
			]
		),
		Keyword.create(
			name='merge',
		),
		Keyword.create(
			name='prepend',
		),
		Keyword.create(
			name='set',
		),
	]

	DATA_SOURCE = [
		Keyword.create(
			name='block',
			next=[
				ArgumentInfo.create(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword.create(
			name='entity',
			next=[
				ArgumentInfo.create(
					name='source',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword.create(
			name='storage',
			next=[
				ArgumentInfo.create(
					name='source',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['data'].argument = [
		Keyword.create(
			name='get',
			next=[
				Switch.create(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='path',
							type=MINECRAFT_NBT_PATH,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='scale',
									type=BRIGADIER_FLOAT,
								),
							]
						),
					]
				),
			]
		),
		Keyword.create(
			name='merge',
			next=[
				Switch.create(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo.create(
							name='nbt',
							type=MINECRAFT_NBT_COMPOUND_TAG,
						),
					]
				),
			]
		),
		Keyword.create(
			name='modify',
			next=[
				Switch.create(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo.create(
							name='targetPath',
							type=MINECRAFT_NBT_PATH,
							next=[
								Switch.create(
									name='MODIFICATION',
									options=DATA_MODIFICATION,
									next=[
										Keyword.create(
											name='from',
											next=[
												Switch.create(
													name='SOURCE',
													options=DATA_SOURCE,
													next=[
														TERMINAL,
														ArgumentInfo.create(
															name='sourcePath',
															type=MINECRAFT_NBT_PATH,
														),
													]
												),
											]
										),
										Keyword.create(
											name='value',
											next=[
												ArgumentInfo.create(
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
		Keyword.create(
			name='remove',
			next=[
				Switch.create(
					name='TARGET',
					options=DATA_TARGET,
					next=[
						ArgumentInfo.create(
							name='path',
							type=MINECRAFT_NBT_PATH,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['datapack'].argument = [
		Keyword.create(
			name='disable',
			next=[
				ArgumentInfo.create(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
				),
			],
		),
		Keyword.create(
			name='enable',
			next=[
				ArgumentInfo.create(
					name='name',
					type=BRIGADIER_STRING,
					subType=ST_DPE_DATAPACK,
					next=[
						TERMINAL,
						Keyword.create(
							name='first',
						),
						Keyword.create(
							name='last',
						),
						Keyword.create(
							name='before',
							next=[
								ArgumentInfo.create(
									name='name',
									type=BRIGADIER_STRING,
									subType=ST_DPE_DATAPACK,
								),
							],
						),
						Keyword.create(
							name='after',
							next=[
								ArgumentInfo.create(
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
		Keyword.create(
			name='list',
			description="List all data packs, or list only the available/enabled ones. Hovering over the data packs in the chat output shows their description defined in their pack.mcmeta.",
			next=[
				TERMINAL,
				Keyword.create(
						name='available',
						next=[TERMINAL],
					),
				Keyword.create(
						name='enabled',
						next=[TERMINAL],
					),
			],
		),
	]

	BASIC_COMMAND_INFO['debug'].argument = [
		Keyword.create(
			name='start',
		),
		Keyword.create(
			name='stop',
		),
		Keyword.create(
			name='function',
			next=[
				ArgumentInfo.create(
					name='name',
					type=MINECRAFT_FUNCTION,
				),
			]
		),
	]


	BASIC_COMMAND_INFO['defaultgamemode'].argument = [
		ArgumentInfo.create(
			name='mode',
			type=LiteralsArgumentType(['survival', 'creative', 'adventure', 'spectator']),
		),
	]

	BASIC_COMMAND_INFO['deop'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['difficulty'].argument = [
		TERMINAL,
		ArgumentInfo.create(
			name='difficulty',
			type=LiteralsArgumentType(['peaceful', 'easy', 'normal', 'hard']),
		),
	]

	BASIC_COMMAND_INFO['effect'].argument = [
		Keyword.create(
			name='give',
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo.create(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='seconds',
									type=BRIGADIER_INTEGER,
									args={'min': 0, 'max': 1000000},
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='amplifier',
											type=BRIGADIER_INTEGER,
											args={'min': 0, 'max': 255},
											next=[
												TERMINAL,
												ArgumentInfo.create(
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
		Keyword.create(
			name='clear',
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='effect',
							type=MINECRAFT_MOB_EFFECT,
						),
					]
				),
			],
		),
	]

	BASIC_COMMAND_INFO['enchant'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='enchantment',
					type=MINECRAFT_ITEM_ENCHANTMENT,
					next=[
						TERMINAL,
						ArgumentInfo.create(
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

	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='align',
		next=[
			ArgumentInfo.create(
				name='axes',
				type=MINECRAFT_SWIZZLE,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='anchored',
		next=[
			ArgumentInfo.create(
				name='anchor',
				type=MINECRAFT_ENTITY_ANCHOR,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='as',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='at',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_ENTITY,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='facing',
		next=[
			ArgumentInfo.create(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword.create(
				name='entity',
				next=[
					ArgumentInfo.create(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentInfo.create(
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
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='in',
		next=[
			ArgumentInfo.create(
				name='dimension',
				type=MINECRAFT_DIMENSION,
				next=EXECUTE_INSTRUCTIONS
			),
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='positioned',
		next=[
			ArgumentInfo.create(
				name='pos',
				type=MINECRAFT_VEC3,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword.create(
				name='as',
				next=[
					ArgumentInfo.create(
						name='targets',
						type=MINECRAFT_ENTITY,
						next=EXECUTE_INSTRUCTIONS
					),
				],
			)
		],
	))
	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='rotated',
		next=[
			ArgumentInfo.create(
				name='rot',
				type=MINECRAFT_ROTATION,
				next=EXECUTE_INSTRUCTIONS
			),
			Keyword.create(
				name='as',
				next=[
					ArgumentInfo.create(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='block',
		next=[
			ArgumentInfo.create(
				name='pos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo.create(
						name='block',
						type=MINECRAFT_BLOCK_PREDICATE,
						next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS)
					),
				],
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='blocks',
		next=[
			ArgumentInfo.create(
				name='start',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo.create(
						name='end',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentInfo.create(
								name='destination',
								type=MINECRAFT_BLOCK_POS,
								next=[
									Keyword.create(
										name='all',
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
									Keyword.create(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='data',
		next=[
			Keyword.create(
				name='block',
				next=[
					ArgumentInfo.create(
						name='pos',
						type=MINECRAFT_BLOCK_POS,
						next=[
							ArgumentInfo.create(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			Keyword.create(
				name='entity',
				next=[
					ArgumentInfo.create(
						name='target',
						type=MINECRAFT_ENTITY,
						next=[
							ArgumentInfo.create(
								name='path',
								type=MINECRAFT_NBT_PATH,
								next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
							),
						],
					),
				],
			),
			Keyword.create(
				name='storage',
				next=[
					ArgumentInfo.create(
						name='source',
						type=MINECRAFT_RESOURCE_LOCATION,
						next=[
							ArgumentInfo.create(
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

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='entity',
		next=[
			ArgumentInfo.create(
				name='entities',
				type=MINECRAFT_ENTITY,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='predicate',
		next=[
			ArgumentInfo.create(
				name='predicate',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
			),
		],
	))

	EXECUTE_IF_UNLESS_ARGUMENTS.append(Keyword.create(name='score',
		next=[
			ArgumentInfo.create(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							Keyword.create(
								name='matches',
								next=[
									ArgumentInfo.create(
										name='range',
										type=MINECRAFT_INT_RANGE,
										next=ChainedList(TERMINAL_LIST, EXECUTE_INSTRUCTIONS),
									),
								]
							),
							ArgumentInfo.create(
								name='__compare',
								type=LiteralsArgumentType(['<=', '<', '=', '>=', '>']),
								next=[
									ArgumentInfo.create(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentInfo.create(
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

	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='if',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))

	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='unless',
		next=EXECUTE_IF_UNLESS_ARGUMENTS,
	))


	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS = []

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword.create(name='block',
		next=[
			ArgumentInfo.create(
				name='targetPos',
				type=MINECRAFT_BLOCK_POS,
				next=[
					ArgumentInfo.create(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo.create(
								name='type',
								type=LiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo.create(
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

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword.create(name='bossbar',
		next=[
			ArgumentInfo.create(
				name='id',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentInfo.create(
						name='value',
						type=LiteralsArgumentType(['value', 'max']),
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword.create(name='entity',
		next=[
			ArgumentInfo.create(
				name='target',
				type=MINECRAFT_ENTITY,
				next=[
					ArgumentInfo.create(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo.create(
								name='type',
								type=LiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo.create(
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

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword.create(name='score',
		next=[
			ArgumentInfo.create(
				name='targets',
				description='Specifies score holder(s) whose score is to be overridden',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						description='A scoreboard objective',
						type=MINECRAFT_OBJECTIVE,
						next=EXECUTE_INSTRUCTIONS,
					),
				],
			),
		]
	))

	EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS.append(Keyword.create(name='storage',
		next=[
			ArgumentInfo.create(
				name='target',
				type=MINECRAFT_RESOURCE_LOCATION,
				next=[
					ArgumentInfo.create(
						name='path',
						type=MINECRAFT_NBT_PATH,
						next=[
							ArgumentInfo.create(
								name='type',
								type=LiteralsArgumentType(['byte', 'short', 'int', 'long', 'float', 'double']),
								next=[
									ArgumentInfo.create(
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

	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='store',
		next=[
			Keyword.create(
				name='result',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
			Keyword.create(
				name='success',
				next=EXECUTE_STORE_RESULT_SUCCESS_ARGUMENTS,
			),
		]
	))

	EXECUTE_INSTRUCTIONS.append(Keyword.create(name='run',
		next=[COMMANDS_ROOT],
	))

	BASIC_COMMAND_INFO['execute'].argument = EXECUTE_INSTRUCTIONS

	BASIC_COMMAND_INFO['experience'].argument = [
		Keyword.create(
			name='add',
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo.create(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo.create(
									name='__levels',
									type=LiteralsArgumentType(['levels', 'points']),
								),
							]
						),
					]
				),
			]
		),
		Keyword.create(
			name='set',
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo.create(
							name='amount',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo.create(
									name='__levels',
									type=LiteralsArgumentType(['levels', 'points']),
								),
							]
						),
					]
				),
			],
		),
		Keyword.create(
			name='query',
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
					next=[
						ArgumentInfo.create(
							name='__levels',
							type=LiteralsArgumentType(['levels', 'points']),
						),
					]
				),
			]
		),
	]

	# fill <from> <to> <block> [destroy|hollow|keep|outline]
	# fill <from> <to> <block> replace [<filter>]
	BASIC_COMMAND_INFO['fill'].argument = [
		ArgumentInfo.create(
			name='from',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo.create(
					name='to',
					type=MINECRAFT_BLOCK_POS,
					next=[
						ArgumentInfo.create(
							name='block',
							type=MINECRAFT_BLOCK_STATE,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='option',
									type=LiteralsArgumentType(['destroy', 'hollow', 'keep', 'outline']),
								),
								Keyword.create(
									name='replace',
									next=[
										TERMINAL,
										ArgumentInfo.create(
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

	FORCELOAD_RANGE_ARG = ArgumentInfo.create(
		name='from',
		type=MINECRAFT_COLUMN_POS,
		next=[
			TERMINAL,
			ArgumentInfo.create(
				name='to',
				type=MINECRAFT_COLUMN_POS,
			),
		]
	)

	BASIC_COMMAND_INFO['forceload'].argument = [
		Keyword.create(
			name='add',
			next=[
				FORCELOAD_RANGE_ARG,
			]
		),
		Keyword.create(
			name='remove',
			next=[
				Keyword('all'),
				FORCELOAD_RANGE_ARG,
			]
		),
		Keyword.create(
			name='query',
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='pos',
					type=MINECRAFT_COLUMN_POS,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['function'].argument = [
		ArgumentInfo.create(
			name='name',
			type=MINECRAFT_FUNCTION,
		),
	]

	BASIC_COMMAND_INFO['gamemode'].argument = [
		ArgumentInfo.create(
			name='gamemode',
			type=MINECRAFT_GAME_MODE,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='target',
					type=MINECRAFT_ENTITY,
				)
			]
		),
	]

	BASIC_COMMAND_INFO['gamerule'].argument = [
		Keyword.create(
			name=gr.name,
			description=gr.description,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='value',
					type=gr.type,
				),
			]
		) for gr in version.gamerules
	]

	BASIC_COMMAND_INFO['give'].argument = [
		ArgumentInfo.create(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='count',
							type=BRIGADIER_INTEGER,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['help'].argument = []

	ITEM_TARGET = [
		Keyword.create(
			name='block',
			next=[
				ArgumentInfo.create(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword.create(
			name='entity',
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_SOURCE = [
		Keyword.create(
			name='block',
			next=[
				ArgumentInfo.create(
					name='sourcePos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
		Keyword.create(
			name='entity',
			next=[
				ArgumentInfo.create(
					name='sourceTarget',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	ITEM_MODIFIER = [
		ArgumentInfo.create(
			name='modifier',
			type=MINECRAFT_RESOURCE_LOCATION,
		),
	]

	BASIC_COMMAND_INFO['item'].argument = [
		Keyword.create(
			name='modify',
			next=[
				Switch.create(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentInfo.create(
							name='slot',
							type=MINECRAFT_NBT_PATH,
							next=[*ITEM_MODIFIER]
						),
					]
				),
			]
		),
		Keyword.create(
			name='replace',
			next=[
				Switch.create(
					name='TARGET',
					options=ITEM_TARGET,
					next=[
						ArgumentInfo.create(
							name='slot',
							type=MINECRAFT_NBT_PATH,
							next=[
								Keyword.create(
									name='with',
									next=[
										ArgumentInfo.create(
											name='item',
											type=MINECRAFT_ITEM_STACK,
											next=[
												TERMINAL,
												ArgumentInfo.create(
													name='count',
													type=BRIGADIER_INTEGER,
													args={'min': 1, 'max': 64},
												),
											]
										),
									]
								),
								Keyword.create(
									name='from',
									next=[
										Switch.create(
											name='SOURCE',
											options=ITEM_SOURCE,
											next=[
												ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['kick'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='reason',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['kill'].argument = [
		TERMINAL,  # An entity is required to run the command without args
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
		),
	]

	BASIC_COMMAND_INFO['list'].argument = [
		TERMINAL,
		Keyword('uuids'),
	]

	BASIC_COMMAND_INFO['locate'].argument = [
		ArgumentInfo.create(
			name='StructureType',
			type=LiteralsArgumentType(list(version.structures)),
		),
	]

	BASIC_COMMAND_INFO['locatebiome'].argument = [
		ArgumentInfo.create(
			name='biome',
			type=DPE_BIOME_ID,
		),
	]

	LOOT_TARGETS = [
		Keyword.create(
			name='spawn',
			next=[
				ArgumentInfo.create(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
					args={'type': float}
				),
			]
		),
		Keyword.create(
			name='replace',
			next=[
				Switch.create(
					name='REPLACE',
					options=[
						Keyword.create(
							name='entity',
							next=[
								ArgumentInfo.create(
									name='entities',
									type=MINECRAFT_ENTITY,
								),
							]
						),
						Keyword.create(
							name='block',
							next=[
								ArgumentInfo.create(
									name='targetPos',
									type=MINECRAFT_BLOCK_POS,
								),
							]
						),
					],
					next=[
						ArgumentInfo.create(
							name='slot',
							type=MINECRAFT_ITEM_SLOT,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='count',
									type=BRIGADIER_INTEGER,
								),
							]
						),

					]
				),
			]
		),
		Keyword.create(
			name='give',
			next=[
				ArgumentInfo.create(
					name='players',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword.create(
			name='insert',
			next=[
				ArgumentInfo.create(
					name='targetPos',
					type=MINECRAFT_BLOCK_POS,
				),
			]
		),
	]

	LOOT_SOURCES = [
		Keyword.create(
			name='fish',
			next=[
				ArgumentInfo.create(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
					next=[
						ArgumentInfo.create(
							name='pos',
							type=MINECRAFT_BLOCK_POS,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='hand',
									type=LiteralsArgumentType(['mainhand', 'offhand']),
								),
								ArgumentInfo.create(
									name='tool',
									type=MINECRAFT_ITEM_STACK,
								),
							]
						),
					]
				),
			]
		),
		Keyword.create(
			name='loot',
			next=[
				ArgumentInfo.create(
					name='loot_table',
					type=MINECRAFT_RESOURCE_LOCATION,
				),
			]
		),
		Keyword.create(
			name='kill',
			next=[
				ArgumentInfo.create(
					name='target',
					type=MINECRAFT_ENTITY,
				),
			]
		),
		Keyword.create(
			name='mine',
			next=[
				ArgumentInfo.create(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='hand',
							type=LiteralsArgumentType(['mainhand', 'offhand']),
						),
						ArgumentInfo.create(
							name='tool',
							type=MINECRAFT_ITEM_STACK,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['loot'].argument = [
		Switch.create(
			name='TARGET',
			options=LOOT_TARGETS,
			next=[
				Switch.create(
					name='SOURCE',
					options=LOOT_SOURCES,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['me'].argument = [
		ArgumentInfo.create(
			name='action',
			type=MINECRAFT_MESSAGE,
		)
	]

	BASIC_COMMAND_INFO['msg'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='message',
					type=MINECRAFT_MESSAGE,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['op'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['pardon'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_GAME_PROFILE,
		),
	]

	BASIC_COMMAND_INFO['pardon-ip'].argument = [
		ArgumentInfo.create(
			name='target',
			type=BRIGADIER_STRING,
		),
	]

	# particle <name> [<pos>] [<delta> <speed> <count> [force|normal] [<viewers>]]

	PARTICLE_ARGUMENTS = [
		TERMINAL,
		ArgumentInfo.create(
			name='pos',
			type=MINECRAFT_VEC3,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='delta',
					type=MINECRAFT_VEC3,
					next=[
						ArgumentInfo.create(
							name='speed',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo.create(
									name='count',
									type=BRIGADIER_INTEGER,
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='display_mode',
											type=LiteralsArgumentType(['force', 'normal']),
											next=[
												TERMINAL,
												ArgumentInfo.create(
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
		Keyword.create(
			name='dust',
			next=[
				ArgumentInfo.create(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo.create(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo.create(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentInfo.create(
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
		Keyword.create(
			name='dust_color_transition',
			next=[
				ArgumentInfo.create(
					name='red',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo.create(
							name='green',
							type=BRIGADIER_FLOAT,
							next=[
								ArgumentInfo.create(
									name='blue',
									type=BRIGADIER_FLOAT,
									next=[
										ArgumentInfo.create(
											name='size',
											type=BRIGADIER_FLOAT,
											next=[
												ArgumentInfo.create(
													name='red',
													type=BRIGADIER_FLOAT,
													next=[
														ArgumentInfo.create(
															name='green',
															type=BRIGADIER_FLOAT,
															next=[
																ArgumentInfo.create(
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
		Keyword.create(
			name='block',
			next=[
				ArgumentInfo.create(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword.create(
			name='falling_dust',
			next=[
				ArgumentInfo.create(
					name='blockState',
					type=MINECRAFT_BLOCK_STATE,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword.create(
			name='item',
			next=[
				ArgumentInfo.create(
					name='item',
					type=MINECRAFT_ITEM_STACK,
					next=PARTICLE_ARGUMENTS
				),
			]
		),
		Keyword.create(
			name='vibration',
			next=[
				ArgumentInfo.create(
					name='x_start',
					type=BRIGADIER_DOUBLE,
					next=[
						ArgumentInfo.create(
							name='y_start',
							type=BRIGADIER_DOUBLE,
							next=[
								ArgumentInfo.create(
									name='z_start',
									type=BRIGADIER_DOUBLE,
									next=[
										ArgumentInfo.create(
											name='x_end',
											type=BRIGADIER_DOUBLE,
											next=[
												ArgumentInfo.create(
													name='y_end',
													type=BRIGADIER_DOUBLE,
													next=[
														ArgumentInfo.create(
															name='z_end',
															type=BRIGADIER_DOUBLE,
															next=[
																ArgumentInfo.create(
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
		particle = particle.copy()
		particle.name = f'minecraft:{particle.name}'
		_SPECIAL_PARTICLES.append(particle)

	del _SPECIAL_PARTICLES_tmp

	BASIC_COMMAND_INFO['particle'].argument = [
		*_SPECIAL_PARTICLES,
		ArgumentInfo.create(
			name='name',
			type=MINECRAFT_PARTICLE,
			next=PARTICLE_ARGUMENTS
		),
	]

	BASIC_COMMAND_INFO['perf'].argument = [
		Keyword('start'),
		Keyword('stop'),
	]

	# playsound <sound> <source> <targets> [<pos>] [<volume>] [<pitch>] [<minVolume>]
	BASIC_COMMAND_INFO['playsound'].argument = [
		ArgumentInfo.create(
			name='sound',
			type=MINECRAFT_RESOURCE_LOCATION,
			next=[
				ArgumentInfo.create(
					name='source',
					type=LiteralsArgumentType(['master', 'music', 'record', 'weather', 'block', 'hostile', 'neutral', 'player', 'ambient', 'voice']),
					next=[
						ArgumentInfo.create(
							name='targets',
							type=MINECRAFT_ENTITY,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='pos',
									type=MINECRAFT_VEC3,
									next=[
										TERMINAL,
										ArgumentInfo.create(
											name='volume',
											type=BRIGADIER_FLOAT,
											next=[
												TERMINAL,
												ArgumentInfo.create(
													name='pitch',
													type=BRIGADIER_FLOAT,
													next=[
														TERMINAL,
														ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['publish'].argument = [
		TERMINAL,
		ArgumentInfo.create(
			name='port',
			type=BRIGADIER_INTEGER,
		),
	]

	# recipe (give|take) <targets> (*|<recipe>)
	BASIC_COMMAND_INFO['recipe'].argument = [
		ArgumentInfo.create(
			name='action',
			type=LiteralsArgumentType(['give', 'take']),
			next=[
				ArgumentInfo.create(
					name='target',
					type=MINECRAFT_ENTITY,
					next=[
						Keyword('*'),
						ArgumentInfo.create(
							name='recipe',
							type=MINECRAFT_RESOURCE_LOCATION,
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['reload'].argument = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['replaceitem'].argument = [
		ArgumentInfo.create(
			name='OUTDATED!',
			type=MINECRAFT_MESSAGE,
		),
	]  # This command was superseded by the /item command in Java Edition 1.17.

	BASIC_COMMAND_INFO['save-all'].argument = [
		TERMINAL,
		Keyword('flush'),
	]

	BASIC_COMMAND_INFO['save-off'].argument = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['save-on'].argument = [TERMINAL]  # has no arguments!

	BASIC_COMMAND_INFO['say'].argument = [
		ArgumentInfo.create(
			name='message',
			type=MINECRAFT_MESSAGE,
		),
	]

	# schedule function <function> <time> [append|replace]
	# schedule clear <function>
	BASIC_COMMAND_INFO['schedule'].argument = [
		Keyword.create(
			name='function',
			next=[
				ArgumentInfo.create(
					name='function',
					type=MINECRAFT_FUNCTION,
					next=[
						ArgumentInfo.create(
							name='time',
							type=MINECRAFT_TIME,
							next=[
								TERMINAL,
								ArgumentInfo.create(
									name='replace_behaviour',
									type=LiteralsArgumentType(['append', 'replace']),
								),
							]
						),
					]
				),
			]
		),
		Keyword.create(
			name='clear',
			next=[
				ArgumentInfo.create(
					name='function',
					type=MINECRAFT_FUNCTION,
				),
			]
		),

	]

	# scoreboard Command:
	SCOREBOARD_OBJECTIVES = []

	SCOREBOARD_OBJECTIVES.append(Keyword.create(name='list'))

	# scoreboard objectives add <objective> <criteria> [<displayName>]
	SCOREBOARD_OBJECTIVES.append(Keyword.create(name='add',
		next=[
			ArgumentInfo.create(
				name='objective',
				type=BRIGADIER_STRING,
				next=[
					ArgumentInfo.create(
						name='criteria',
						type=MINECRAFT_OBJECTIVE_CRITERIA,
						next=[
							TERMINAL,
							ArgumentInfo.create(
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
	SCOREBOARD_OBJECTIVES.append(Keyword.create(name='remove',
		next=[
			ArgumentInfo.create(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
			),
		]
	))

	# scoreboard objectives setdisplay <slot> [<objective>]
	SCOREBOARD_OBJECTIVES.append(Keyword.create(name='setdisplay',
		next=[
			ArgumentInfo.create(
				name='slot',
				type=MINECRAFT_SCOREBOARD_SLOT,
				next=[
					TERMINAL,
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard objectives modify <objective> displayname <displayName>
	# scoreboard objectives modify <objective> rendertype (hearts|integer)
	SCOREBOARD_OBJECTIVES.append(Keyword.create(name='modify',
		next=[
			ArgumentInfo.create(
				name='objective',
				type=MINECRAFT_OBJECTIVE,
				next=[
					Keyword.create(
						name='displayname',
						next=[
							ArgumentInfo.create(
								name='displayName',
								type=MINECRAFT_COMPONENT,
							),
						]
					),
					Keyword.create(
						name='rendertype',
						next=[
							ArgumentInfo.create(
								name='rendertype',
								type=LiteralsArgumentType(['hearts', 'integer']),
							),
						]
					),
				]
			),
		]
	))


	SCOREBOARD_PLAYERS = []

	# scoreboard players list [<target>]
	SCOREBOARD_PLAYERS.append(Keyword.create(name='list',
		next=[
			TERMINAL,
			ArgumentInfo.create(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
			),
		]
	))

	# scoreboard players get <target> <objective>
	SCOREBOARD_PLAYERS.append(Keyword.create(name='get',
		next=[
			ArgumentInfo.create(
				name='target',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players set <targets> <objective> <score>
	SCOREBOARD_PLAYERS.append(Keyword.create(name='set',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo.create(
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
	SCOREBOARD_PLAYERS.append(Keyword.create(name='add',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo.create(
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
	SCOREBOARD_PLAYERS.append(Keyword.create(name='remove',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo.create(
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
	SCOREBOARD_PLAYERS.append(Keyword.create(name='reset',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					TERMINAL,
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players enable <targets> <objective>
	SCOREBOARD_PLAYERS.append(Keyword.create(name='enable',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='objective',
						type=MINECRAFT_OBJECTIVE,
					),
				]
			),
		]
	))

	# scoreboard players operation <targets> <targetObjective> <operation> <source> <sourceObjective>
	SCOREBOARD_PLAYERS.append(Keyword.create(name='operation',
		next=[
			ArgumentInfo.create(
				name='targets',
				type=MINECRAFT_SCORE_HOLDER,
				next=[
					ArgumentInfo.create(
						name='targetObjective',
						type=MINECRAFT_OBJECTIVE,
						next=[
							ArgumentInfo.create(
								name='operation',
								type=MINECRAFT_OPERATION,
								next=[
									ArgumentInfo.create(
										name='source',
										type=MINECRAFT_SCORE_HOLDER,
										next=[
											ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['scoreboard'].argument = [
		Keyword.create(
			name='objectives',
			next=SCOREBOARD_OBJECTIVES
		),
		Keyword.create(
			name='players',
			next=SCOREBOARD_PLAYERS
		),
	]

	BASIC_COMMAND_INFO['seed'].argument = [TERMINAL]  # has no arguments!

	# setblock <pos> <block> [destroy|keep|replace]
	BASIC_COMMAND_INFO['setblock'].argument = [
		ArgumentInfo.create(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				ArgumentInfo.create(
					name='block',
					type=MINECRAFT_BLOCK_STATE,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='operation',
							type=LiteralsArgumentType(['destroy', 'keep', 'replace']),
						),
					]
				),
			]
		),
	]

	BASIC_COMMAND_INFO['setidletimeout'].argument = [
		ArgumentInfo.create(
			name='minutes',
			type=BRIGADIER_INTEGER,
		),
	]

	# setworldspawn [<pos>] [<angle>]
	BASIC_COMMAND_INFO['setworldspawn'].argument = [
		TERMINAL,
		ArgumentInfo.create(
			name='pos',
			type=MINECRAFT_BLOCK_POS,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='angle',
					type=MINECRAFT_ANGLE,
				),
			]
		),
	]

	# spawnpoint [<targets>] [<pos>] [<angle>]
	BASIC_COMMAND_INFO['spawnpoint'].argument = [
		TERMINAL,
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='pos',
					type=MINECRAFT_BLOCK_POS,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='angle',
							type=MINECRAFT_ANGLE,
						),
					]
				),
			]
		),
	]

	# spectate <target> [<player>]
	BASIC_COMMAND_INFO['spectate'].argument = [
		ArgumentInfo.create(
			name='target',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='player',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	# spreadplayers <center> <spreadDistance> <maxRange> <respectTeams> <targets>
	# spreadplayers <center> <spreadDistance> <maxRange> under <maxHeight> <respectTeams> <targets>
	SPREADPLAYERS_RESPECT_TEAMS = [
		ArgumentInfo.create(
			name='respectTeams',
			type=BRIGADIER_BOOL,
			next=[
				ArgumentInfo.create(
					name='targets',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['spreadplayers'].argument = [
		ArgumentInfo.create(
			name='center',
			type=MINECRAFT_VEC2,
			next=[
				ArgumentInfo.create(
					name='spreadDistance',
					type=BRIGADIER_FLOAT,
					next=[
						ArgumentInfo.create(
							name='maxRange',
							type=BRIGADIER_FLOAT,
							next=[
								Keyword.create(
									name='under',
									next=[
										ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['stop'].argument = [TERMINAL]  # has no arguments!

	# stopsound <targets> [<source>] [<sound>]
	BASIC_COMMAND_INFO['stopsound'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='source',
					type=LiteralsArgumentType(['*', 'master', 'music', 'record', 'weather', 'block', 'hostile', 'neutral', 'player', 'ambient', 'voice']),
					next=[
						TERMINAL,
						ArgumentInfo.create(
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
	BASIC_COMMAND_INFO['summon'].argument = [
		ArgumentInfo.create(
			name='entity',
			type=MINECRAFT_ENTITY_SUMMON,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='pos',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentInfo.create(
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
	BASIC_COMMAND_INFO['tag'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				Keyword.create(
					name='add',
					next=[
						ArgumentInfo.create(
							name='name',
							type=BRIGADIER_STRING,
						),
					]
				),
				Keyword('list'),
				Keyword.create(
					name='remove',
					next=[
						ArgumentInfo.create(
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
	BASIC_COMMAND_INFO['team'].argument = [
		Keyword.create(
			name='list',
			description="Lists all teams, with their display names and the amount of entities in them. The optional `<team>` can be used to specify a particular team.",
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword.create(
			name='add',
			description="Creates a team with the given name and optional display name. `<displayName>` defaults to `<objective>` when unspecified.",
			next=[
				ArgumentInfo.create(
					name='team',
					type=BRIGADIER_STRING,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='displayName',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
			]
		),
		Keyword.create(
			name='remove',
			description="Deletes the specified team.",
			next=[
				ArgumentInfo.create(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword.create(
			name='empty',
			description="Removes all members from the named team.",
			next=[
				ArgumentInfo.create(
					name='team',
					type=MINECRAFT_TEAM,
				),
			]
		),
		Keyword.create(
			name='join',
			description="Assigns the specified entities to the specified team. If no entities is specified, makes the executor join the team.",
			next=[
				ArgumentInfo.create(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='members',
							type=MINECRAFT_SCORE_HOLDER,
						),
					]
				),
			]
		),
		Keyword.create(
			name='leave',
			description="Makes the specified entities leave their teams.",
			next=[
				ArgumentInfo.create(
					name='members',
					type=MINECRAFT_SCORE_HOLDER,
				),
			]
		),
		Keyword.create(
			name='modify',
			description="Modifies the options of the specified team.",
			next=[
				ArgumentInfo.create(
					name='team',
					type=MINECRAFT_TEAM,
					next=[
						Switch.create(
							name='option',
							options=[
								Keyword.create(
									name='displayName',
									description="Set the display name of the team.",
									next=[
										ArgumentInfo.create(
											name='displayName',
											type=MINECRAFT_COMPONENT,
											description="Specifies the team name to be displayed. Must be a raw JSON text.",
										),
									]
								),
								Keyword.create(
									name='color',
									description="Decide the color of the team and players in chat, above their head, on the Tab menu, and on the sidebar. Also changes the color of the outline of the entities caused by the Glowing effect.",
									next=[
										ArgumentInfo.create(
											name='value',
											type=MINECRAFT_COLOR,
											description="Must be a color.\n\nDefaults to reset. If reset, names are shown in default color and formatting.",
										),
									]
								),
								Keyword.create(
									name='friendlyFire',
									description="Enable/Disable players inflicting damage on each other when on the same team. (Note: players can still inflict status effects on each other.) Does not affect some non-player entities in a team.",
									next=[
										ArgumentInfo.create(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Enable players inflicting damage on each other when in the same team.\n  - false - Disable players inflicting damage on each other when in the same team.",
										),
									]
								),
								Keyword.create(
									name='seeFriendlyInvisibles',
									description="Decide players can see invisible players on their team as whether semi-transparent or completely invisible.",
									next=[
										ArgumentInfo.create(
											name='allowed',
											type=BRIGADIER_BOOL,
											description="  - true - (Default) Can see invisible players on the same team semi-transparently.\n  - false - Cannot see invisible players on the same team.",
										),
									]
								),
								Keyword.create(
									name='nametagVisibility',
									description="Decide whose name tags above their heads can be seen.",
									next=[
										Keyword.create(
											name='never',
											description="Name above player's head cannot be seen by any players.",
										),
										Keyword.create(
											name='hideForOtherTeams',
											description="Name above player's head can be seen only by players in the same team.",
										),
										Keyword.create(
											name='hideForOwnTeam',
											description="Name above player's head cannot be seen by all the players in the same team.",
										),
										Keyword.create(
											name='always',
											description="(Default) Name above player's head can be seen by all the players.",
										),
									]
								),
								Keyword.create(
									name='deathMessageVisibility',
									description="Control the visibility of death messages for players.",
									next=[
										Keyword.create(
											name='never',
											description="Hide death message for all the players.",
										),
										Keyword.create(
											name='hideForOtherTeams',
											description="Hide death message to all the players who are not in the same team.",
										),
										Keyword.create(
											name='hideForOwnTeam',
											description="Hide death message to players in the same team.",
										),
										Keyword.create(
											name='always',
											description="(Default) Make death message visible to all the players.",
										),
									]
								),
								Keyword.create(
									name='collisionRule',
									description="Controls the way the entities on the team collide with other entities.",
									next=[
										Keyword.create(
											name='always',
											description="(Default) Normal collision.",
										),
										Keyword.create(
											name='never',
											description="No entities can push entities in this team.",
										),
										Keyword.create(
											name='pushOtherTeams',
											description="Entities in this team can be pushed only by other entities in the same team.",
										),
										Keyword.create(
											name='pushOwnTeam',
											description="Entities in this team cannot be pushed by another entity in this team.",
										),
									]
								),
								Keyword.create(
									name='prefix',
									description="Modifies the prefix that displays before players' names.",
									next=[
										ArgumentInfo.create(
											name='prefix',
											type=MINECRAFT_COMPONENT,
											description="Specifies the prefix to display. Must be a raw JSON text.",
										),
									]
								),
								Keyword.create(
									name='suffix',
									description="Modifies the suffix that displays before players' names.",
									next=[
										ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['teammsg'].argument = [
		ArgumentInfo.create(
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
	BASIC_COMMAND_INFO['teleport'].argument = [
		# ArgumentInfo.create(
		# 	name='destination',
		# 	type=MINECRAFT_ENTITY,
		# ),
		ArgumentInfo.create(
			name='location',
			type=MINECRAFT_VEC3,
		),
		ArgumentInfo.create(
			name='targets|destination',
			type=MINECRAFT_ENTITY,
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='location',
					type=MINECRAFT_VEC3,
					next=[
						TERMINAL,
						ArgumentInfo.create(
							name='rotation',
							type=MINECRAFT_ROTATION,
						),
						Keyword.create(
							name='facing',
							next=[
								ArgumentInfo.create(
									name='facingLocation',
									type=MINECRAFT_VEC3,
								),
								Keyword.create(
									name='entity',
									next=[
										ArgumentInfo.create(
											name='facingEntity',
											type=MINECRAFT_ENTITY,
											next=[
												TERMINAL,
												ArgumentInfo.create(
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
				ArgumentInfo.create(
					name='destination',
					type=MINECRAFT_ENTITY,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['tell'].argument = BASIC_COMMAND_INFO['msg'].argument

	# tellraw <targets> <message>
	BASIC_COMMAND_INFO['tellraw'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='message',
					type=MINECRAFT_COMPONENT,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['testfor'].argument = []  # This command has been removed

	BASIC_COMMAND_INFO['testforblock'].argument = []  # This command has been removed

	BASIC_COMMAND_INFO['testforblocks'].argument = []  # This command has been removed

	BASIC_COMMAND_INFO['time'].argument = [
		Keyword.create(
			name='add',
			description="Adds `<time>` to the in-game daytime.",
			next=[
				ArgumentInfo.create(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
		Keyword.create(
			name='query',
			description="Queries current time.",
			next=[
				ArgumentInfo.create(
					name='daytime|gametime|day',
					type=LiteralsArgumentType(['daytime', 'gametime', 'day']),
				),
			]
		),
		Keyword.create(
			name='set',
			next=[
				ArgumentInfo.create(
					name='timeSpec',
					type=LiteralsArgumentType(['day', 'night', 'noon', 'midnight']),
				),
			]
		),
		Keyword.create(
			name='set',
			next=[
				ArgumentInfo.create(
					name='time',
					type=MINECRAFT_TIME,
				),
			]
		),
	]

	# title <targets> (clear|reset)
	# title <targets> (title|subtitle|actionbar) <title>
	# title <targets> times <fadeIn> <stay> <fadeOut>
	BASIC_COMMAND_INFO['title'].argument = [
		ArgumentInfo.create(
			name='targets',
			type=MINECRAFT_ENTITY,
			next=[
				ArgumentInfo.create(
					name='clear|reset',
					type=LiteralsArgumentType(['clear', 'reset']),
				),
				ArgumentInfo.create(
					name='title|subtitle|actionbar',
					type=LiteralsArgumentType(['title', 'subtitle', 'actionbar']),
					next=[
						ArgumentInfo.create(
							name='title',
							type=MINECRAFT_COMPONENT,
						),
					]
				),
				Keyword.create(
					name='times',
					next=[
						ArgumentInfo.create(
							name='fadeIn',
							type=BRIGADIER_INTEGER,
							next=[
								ArgumentInfo.create(
									name='stay',
									type=BRIGADIER_INTEGER,
									next=[
										ArgumentInfo.create(
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

	BASIC_COMMAND_INFO['tm'].argument = BASIC_COMMAND_INFO['teammsg'].argument

	# BASIC_COMMAND_INFO['toggledownfall'].argument = []  has been removed

	BASIC_COMMAND_INFO['tp'].argument = BASIC_COMMAND_INFO['teleport'].argument

	# trigger <objective>
	# trigger <objective> add <value>
	# trigger <objective> set <value>
	BASIC_COMMAND_INFO['trigger'].argument = [
		ArgumentInfo.create(
			name='objective',
			type=MINECRAFT_OBJECTIVE,
			next=[
				TERMINAL,
				Keyword.create(
					name='add',
					next=[
						ArgumentInfo.create(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					]
				),
				Keyword.create(
					name='set',
					next=[
						ArgumentInfo.create(
							name='value',
							type=BRIGADIER_INTEGER,
						),
					],
				),
			]
		),
	]

	BASIC_COMMAND_INFO['w'].argument = BASIC_COMMAND_INFO['msg'].argument

	# weather (clear|rain|thunder) [<duration>]
	BASIC_COMMAND_INFO['weather'].argument = [
		ArgumentInfo.create(
			name='objective',
			type=LiteralsArgumentType(['clear', 'rain', 'thunder']),
			next=[
				TERMINAL,
				ArgumentInfo.create(
					name='duration',
					type=BRIGADIER_INTEGER,
				),
			]
		),
	]

	BASIC_COMMAND_INFO['whitelist'].argument = []  # TODO: BASIC_COMMAND_INFO['whitelist'].argument

	BASIC_COMMAND_INFO['worldborder'].argument = []  # TODO: BASIC_COMMAND_INFO['worldborder'].argument

	BASIC_COMMAND_INFO['xp'].argument = BASIC_COMMAND_INFO['experience'].argument
