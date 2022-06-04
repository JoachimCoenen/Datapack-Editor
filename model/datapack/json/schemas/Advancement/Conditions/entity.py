from Cat.utils import Anything
from model.json.core import *
from model.utils import MDStr

ADVANCEMENT_CONDITIONS_ENTITY = JsonObjectSchema(properties=[
	PropertySchema(
		name="catType",
		description=MDStr(" {{until|java 1.19}}: Check the variant of this cat. Accepts a resource location for the texture of the cat's variant. To be moved under <code>type_specific</code> in 1.19."),
		value=JsonStringSchema()
	),
	PropertySchema(
		name="distance",
		description=MDStr('To test the distance to the entity this predicate is invoked upon. Passes if the calculated distance is between the entered <code>min</code> and <code>max</code>, inclusive.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="absolute",
				description=MDStr('Test the distance between the two points in 3D space.'),
				value=JsonObjectSchema(properties=[
					PropertySchema(
						name="max",
						description=MDStr(''),
						value=JsonFloatSchema()
					),
					PropertySchema(
						name="min",
						description=MDStr(' '),
						value=JsonFloatSchema()
					)
				])
			),
			PropertySchema(
				name="horizontal",
				description=MDStr('Test the distance between the two points, ignoring the Y value.'),
				value=JsonObjectSchema(properties=[
					PropertySchema(
						name="max",
						description=MDStr(''),
						value=JsonFloatSchema()
					),
					PropertySchema(
						name="min",
						description=MDStr(''),
						value=JsonFloatSchema()
					)
				])
			),
			PropertySchema(
				name="x",
				description=MDStr('Test the absolute difference between the X-coordinates of the two points.'),
				value=JsonObjectSchema(properties=[
					PropertySchema(
						name="max",
						description=MDStr(''),
						value=JsonFloatSchema()
					),
					PropertySchema(
						name="min",
						description=MDStr(''),
						value=JsonFloatSchema()
					)
				])
			),
			PropertySchema(
				name="y",
				description=MDStr('Test the absolute difference between the Y-coordinates of the two points.'),
				value=JsonObjectSchema(properties=[
					PropertySchema(
						name="max",
						description=MDStr(''),
						value=JsonFloatSchema()
					),
					PropertySchema(
						name="min",
						description=MDStr(''),
						value=JsonFloatSchema()
					)
				])
			),
			PropertySchema(
				name="z",
				description=MDStr('Test the absolute difference between the Z-coordinates of the two points.'),
				value=JsonObjectSchema(properties=[
					PropertySchema(
						name="max",
						description=MDStr(''),
						value=JsonFloatSchema()
					),
					PropertySchema(
						name="min",
						description=MDStr(''),
						value=JsonFloatSchema()
					)
				])
			)
		])
	),
	PropertySchema(
		name="effects",
		description=MDStr('For testing the active [[Effect|status effects]] on the entity.'),
		value=JsonObjectSchema(
			description=MDStr('<minecraft:effect_name>: None'),
			properties=[
				PropertySchema(
					name=Anything,
					description=MDStr('A status effect that must be present.'),
					value=JsonObjectSchema(properties=[
						PropertySchema(
							name="ambient",
							description=MDStr('Test whether the effect is from a beacon.'),
							value=JsonBoolSchema()
						),
						PropertySchema(
							name="amplifier",
							description=MDStr("Test if the effect's amplifier matches an exact value. Level I is represented by 0."),
							value=JsonUnionSchema(options=[
								JsonIntSchema(),
								JsonObjectSchema(properties=[
									PropertySchema(
										name="max",
										description=MDStr(''),
										value=JsonIntSchema()
									),
									PropertySchema(
										name="min",
										description=MDStr(''),
										value=JsonIntSchema()
									)
								])
							])
						),
						PropertySchema(
							name="duration",
							description=MDStr("Test if the effect's remaining time (in ticks) matches an exact value."),
							value=JsonUnionSchema(options=[
								JsonIntSchema(),
								JsonObjectSchema(properties=[
									PropertySchema(
										name="max",
										description=MDStr(''),
										value=JsonIntSchema()
									),
									PropertySchema(
										name="min",
										description=MDStr(''),
										value=JsonIntSchema()
									)
								])
							])
						),
						PropertySchema(
							name="visible",
							description=MDStr('Test if the effect has visible particles.'),
							value=JsonBoolSchema()
						)
					])
				)
			]
		)
	),
	PropertySchema(
		name="equipment",
		description=MDStr('For testing the items that this entity holds in its equipment slots.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="mainhand",
				description=MDStr("Test the item in the entity's main hand."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			),
			PropertySchema(
				name="offhand",
				description=MDStr("Test the item in the entity's offhand."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			),
			PropertySchema(
				name="head",
				description=MDStr("Test the item in the entity's head armour slot."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			),
			PropertySchema(
				name="chest",
				description=MDStr("Test the item in the entity's chest  armour slot."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			),
			PropertySchema(
				name="legs",
				description=MDStr("Test the item in the entity's legs armour slot."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			),
			PropertySchema(
				name="feet",
				description=MDStr("Test the item in the entity's feet armour slot."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ITEM.properties
				])
			)
		])
	),
	PropertySchema(
		name="fishing_hook",
		description=MDStr(' {{until|java 1.19}}: Test properties of the fishing hook that just got reeled in by this entity. To be moved under <code>type_specific</code> in 1.19.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="in_open_water",
				description=MDStr('Whether the fishing hook was in [[Fishing#Junk_and_treasure|open water]].'),
				value=JsonBoolSchema()
			)
		])
	),
	PropertySchema(
		name="flags",
		description=MDStr('To test flags of the entity.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="is_baby",
				description=MDStr('Test whether the entity is or is not a baby variant.'),
				value=JsonBoolSchema()
			),
			PropertySchema(
				name="is_on_fire",
				description=MDStr('Test whether the entity is or is not on fire.'),
				value=JsonBoolSchema()
			),
			PropertySchema(
				name="is_sneaking",
				description=MDStr('Test whether the entity is or is not sneaking.'),
				value=JsonBoolSchema()
			),
			PropertySchema(
				name="is_sprinting",
				description=MDStr('Test whether the entity is or is not sprinting.'),
				value=JsonBoolSchema()
			),
			PropertySchema(
				name="is_swimming",
				description=MDStr('Test whether the entity is or is not swimming.'),
				value=JsonBoolSchema()
			)
		])
	),
	PropertySchema(
		name="lightning_bolt",
		description=MDStr('{{until|java 1.19}}: To check information about this lightning bolt; fails when entity is not a lightning bolt. To be moved under <code>type_specific</code> in 1.19.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="blocks_set_on_fire",
				description=MDStr('Test if the number of blocks set on fire by this lightning bolt matches an exact value.'),
				value=JsonUnionSchema(options=[
					JsonIntSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr(''),
							value=JsonIntSchema()
						),
						PropertySchema(
							name="min",
							description=MDStr(''),
							value=JsonIntSchema()
						)
					])
				])
			),
			PropertySchema(
				name="entity_struck",
				description=MDStr('Test the properties of entities struck by this lightning bolt. Passes if at least one of the struck entities matches the entered conditions.'),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ENTITY.properties
				])
			)
		])
	),
	PropertySchema(
		name="location",
		description=MDStr("Test properties of this entity's location."),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_LOCATION.properties
		])
	),
	PropertySchema(
		name="nbt",
		description=MDStr('An NBT string.'),
		value=JsonStringSchema()
	),
	PropertySchema(
		name="passenger",
		description=MDStr('Test the entity directly riding this entity.'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_ENTITY.properties
		])
	),
	PropertySchema(
		name="player",
		description=MDStr('{{until|java 1.19}}: Tests properties unique to players; fails when this entity is not a player. To be moved under <code>type_specific</code> in 1.19.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="looking_at",
				description=MDStr("Test properties of the entity that this player is looking at, as long as it is visible and within a radius of 100 blocks. Visibility is defined through the line from the player's eyes to the entity's eyes, rather than the direction that the player is looking in."),
				value=JsonObjectSchema(properties=[
					# *ADVANCEMENT_CONDITIONS_ENTITY.properties
				])
			),
			PropertySchema(
				name="advancements",
				description=MDStr("To test the player's [[advancements]]."),
				value=JsonObjectSchema(
					description=MDStr('<advancement id>: None'),
					properties=[
						PropertySchema(
							name=Anything,
							description=MDStr('Test whether an advancement is granted or not granted. Key is an advancement ID, value is <code>true</code> or <code>false</code> to test for granted/not granted respectively.'),
							value=JsonUnionSchema(options=[
								JsonBoolSchema(),
								JsonObjectSchema(
									description=MDStr('<criterion id>: None'),
									properties=[
										PropertySchema(
											name=Anything,
											description=MDStr('Key is one of the criteria of the advancement, value is <code>true</code> or <code>false</code> to test for completed/not completed respectively.'),
											value=JsonBoolSchema()
										)
									]
								)
							])
						)
					]
				)
			),
			PropertySchema(
				name="gamemode",
				description=MDStr('Test the [[Game modes|game mode]] of this player. Valid values are <code>survival</code>, <code>creative</code>, <code>adventure</code> and <code>spectator</code>.'),
				value=JsonStringSchema()
			),
			PropertySchema(
				name="level",
				description=MDStr('Test if the experience level of this player matches an exact value.'),
				value=JsonUnionSchema(options=[
					JsonIntSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr(''),
							value=JsonIntSchema()
						),
						PropertySchema(
							name="min",
							description=MDStr(''),
							value=JsonIntSchema()
						)
					])
				])
			),
			PropertySchema(
				name="recipes",
				description=MDStr('To test if [[recipe]]s are known or unknown to this player.'),
				value=JsonObjectSchema(
					description=MDStr('<recipe id>: None'),
					properties=[
						PropertySchema(
							name=Anything,
							description=MDStr('Key is the recipe ID; value is <code>true</code> or <code>false</code> to test for known/unknown respectively.'),
							value=JsonBoolSchema()
						)
					]
				)
			),
			PropertySchema(
				name="stats",
				description=MDStr("To test the player's [[statistics]]."),
				value=JsonArraySchema(element=JsonObjectSchema(
					description=MDStr(' A statistic to test.'),
					properties=[
						PropertySchema(
							name="type",
							description=MDStr('The statistic type. Valid values are <code>minecraft:custom</code>, <code>minecraft:crafted</code>, <code>minecraft:used</code>, <code>minecraft:broken</code>, <code>minecraft:mined</code>, <code>minecraft:killed</code>, <code>minecraft:picked_up</code>, <code>minecraft:dropped</code> and <code>minecraft:killed_by</code>.'),
							value=JsonStringSchema()
						),
						PropertySchema(
							name="stat",
							description=MDStr('The statistic ID to test.'),
							value=JsonStringSchema()
						),
						PropertySchema(
							name="value",
							description=MDStr('Test if the value of the statistic matches an exact number.'),
							value=JsonUnionSchema(options=[
								JsonIntSchema(),
								JsonObjectSchema(properties=[
									PropertySchema(
										name="max",
										description=MDStr(''),
										value=JsonIntSchema()
									),
									PropertySchema(
										name="min",
										description=MDStr(''),
										value=JsonIntSchema()
									)
								])
							])
						)
					]
				))
			)
		])
	),
	PropertySchema(
		name="stepping_on",
		description=MDStr('Test properties of the block the entity is standing on, using a location predicate.'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_LOCATION.properties
		])
	),
	PropertySchema(
		name="team",
		description=MDStr('Passes if the [[Scoreboard#Teams|team]] of this entity matches this string.'),
		value=JsonStringSchema()
	),
	PropertySchema(
		name="type",
		description=MDStr("Test this entity's type. Accepts an [[Data values/Entity IDs|entity ID]]."),
		value=JsonStringSchema()
	),
	PropertySchema(
		name="targeted_entity",
		description=MDStr('Test properties of the entity which this entity is targeting for attacks.'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_ENTITY.properties
		])
	),
	PropertySchema(
		name="vehicle",
		description=MDStr('Test properties of the vehicle entity that this entity is riding upon.'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_ENTITY.properties
		])
	),
	PropertySchema(
		name="type_specific",
		description=MDStr('{{upcoming|java 1.19}}: To test entity properties that can only be applied to certain entity types.  Supersedes <code>lightning_bolt</code>, <code>player</code>, <code>fishing_hook</code> and <code>catType</code>.'),
		value=JsonObjectSchema(properties=[
			# **** No other fields.,
			PropertySchema(
				name="type",
				description=MDStr('Dictates which type-specific properties to test for.<p style="padding-block-end: 1em; margin: 0 0 0 0;">The possible values for {{nbt|string|type}} and associated extra contents:</p>'),
				value=JsonStringSchema()
			),
			PropertySchema(
				name="variant",
				decidingProp='type',
				values={
					'cat': JsonUnionSchema(options=[
						JsonStringSchema(description=MDStr('A resource location specifying a cat variant. Valid values are <code>minecraft:all_black</code>, <code>minecraft:black</code>, <code>minecraft:british</code>, <code>minecraft:calico</code>, <code>minecraft:jellie</code>, <code>minecraft:persian</code>, <code>minecraft:ragdoll</code>, <code>minecraft:red</code>, <code>minecraft:siamese</code>, <code>minecraft:tabby</code>, or <code>minecraft:white</code>.')),
						JsonStringSchema(description=MDStr('A resource location specifying a frog variant. Valid values are <code>minecraft:cold</code>, <code>minecraft:temperate</code>, or <code>minecraft:warm</code>.'))
					]),
					'frog': JsonUnionSchema(options=[
						JsonStringSchema(description=MDStr('A resource location specifying a cat variant. Valid values are <code>minecraft:all_black</code>, <code>minecraft:black</code>, <code>minecraft:british</code>, <code>minecraft:calico</code>, <code>minecraft:jellie</code>, <code>minecraft:persian</code>, <code>minecraft:ragdoll</code>, <code>minecraft:red</code>, <code>minecraft:siamese</code>, <code>minecraft:tabby</code>, or <code>minecraft:white</code>.')),
						JsonStringSchema(description=MDStr('A resource location specifying a frog variant. Valid values are <code>minecraft:cold</code>, <code>minecraft:temperate</code>, or <code>minecraft:warm</code>.'))
					])
				},
				value=None
			),
			PropertySchema(
				name="in_open_water",
				decidingProp='type',
				values={
					'fishing_hook': JsonBoolSchema(description=MDStr('Whether the fishing hook was in [[Fishing#Junk_and_treasure|open water]].'))
				},
				value=None
			),
			PropertySchema(
				name="blocks_set_on_fire",
				decidingProp='type',
				values={
					'lightning': JsonUnionSchema(options=[
						JsonIntSchema(description=MDStr('Test if the number of blocks set on fire by this lightning bolt matches an exact value.')),
						JsonObjectSchema(
							description=MDStr('Test the number of blocks set on fire by this lightning bolt is between a minimum and maximum value.'),
							properties=[
								PropertySchema(
									name="max",
									description=MDStr(''),
									value=JsonIntSchema()
								),
								PropertySchema(
									name="min",
									description=MDStr(''),
									value=JsonIntSchema()
								)
							]
						)
					])
				},
				value=None
			),
			PropertySchema(
				name="entity_struck",
				decidingProp='type',
				values={
					'lightning': JsonObjectSchema(
						description=MDStr('Test the properties of entities struck by this lightning bolt. Passes if at least one of the struck entities matches the entered conditions.'),
						properties=[
					
						]
					)
				},
				value=None
			),
			PropertySchema(
				name="looking_at",
				decidingProp='type',
				values={
					'player': JsonObjectSchema(
						description=MDStr("Test properties of the entity that this player is looking at, as long as it is visible and within a radius of 100 blocks. Visibility is defined through the line from the player's eyes to the entity's eyes, rather than the direction that the player is looking in."),
						properties=[
							# *ADVANCEMENT_CONDITIONS_ENTITY.properties
						]
					)
				},
				value=None
			),
			PropertySchema(
				name="advancements",
				decidingProp='type',
				values={
					'player': JsonObjectSchema(
						description=MDStr("<advancement id>: To test the player's [[advancements]]."),
						properties=[
							PropertySchema(
								name=Anything,
								description=MDStr('Test whether an advancement is granted or not granted. Key is an advancement ID, value is <code>true</code> or <code>false</code> to test for granted/not granted respectively.'),
								value=JsonUnionSchema(options=[
									JsonBoolSchema(),
									JsonObjectSchema(
										description=MDStr('<criterion id>: None'),
										properties=[
											PropertySchema(
												name=Anything,
												description=MDStr('Key is one of the criteria of the advancement, value is <code>true</code> or <code>false</code> to test for completed/not completed respectively.'),
												value=JsonBoolSchema()
											)
										]
									)
								])
							)
						]
					)
				},
				value=None
			),
			PropertySchema(
				name="gamemode",
				decidingProp='type',
				values={
					'player': JsonStringSchema(description=MDStr('Test the [[Game modes|game mode]] of this player. Valid values are <code>survival</code>, <code>creative</code>, <code>adventure</code> and <code>spectator</code>.'))
				},
				value=None
			),
			PropertySchema(
				name="level",
				decidingProp='type',
				values={
					'player': JsonUnionSchema(options=[
						JsonIntSchema(description=MDStr('Test if the experience level of this player matches an exact value.')),
						JsonObjectSchema(
							description=MDStr('Test if the experience level of this player is between <code>min</code> and <code>max</code> values, inclusive.'),
							properties=[
								PropertySchema(
									name="max",
									description=MDStr(''),
									value=JsonIntSchema()
								),
								PropertySchema(
									name="min",
									description=MDStr(''),
									value=JsonIntSchema()
								)
							]
						)
					])
				},
				value=None
			),
			PropertySchema(
				name="recipes",
				decidingProp='type',
				values={
					'player': JsonObjectSchema(
						description=MDStr('<recipe id>: To test if [[recipe]]s are known or unknown to this player.'),
						properties=[
							PropertySchema(
								name=Anything,
								description=MDStr('Key is the recipe ID; value is <code>true</code> or <code>false</code> to test for known/unknown respectively.'),
								value=JsonBoolSchema()
							)
						]
					)
				},
				value=None
			),
			PropertySchema(
				name="stats",
				decidingProp='type',
				values={
					'player': JsonArraySchema(element=JsonObjectSchema(
						description=MDStr(' A statistic to test.'),
						properties=[
							PropertySchema(
								name="type",
								description=MDStr('The statistic type. Valid values are <code>minecraft:custom</code>, <code>minecraft:crafted</code>, <code>minecraft:used</code>, <code>minecraft:broken</code>, <code>minecraft:mined</code>, <code>minecraft:killed</code>, <code>minecraft:picked_up</code>, <code>minecraft:dropped</code> and <code>minecraft:killed_by</code>.'),
								value=JsonStringSchema()
							),
							PropertySchema(
								name="stat",
								description=MDStr('The statistic ID to test.'),
								value=JsonStringSchema()
							),
							PropertySchema(
								name="value",
								description=MDStr('Test if the value of the statistic matches an exact number.'),
								value=JsonUnionSchema(options=[
									JsonIntSchema(),
									JsonObjectSchema(properties=[
										PropertySchema(
											name="max",
											description=MDStr(''),
											value=JsonIntSchema()
										),
										PropertySchema(
											name="min",
											description=MDStr(''),
											value=JsonIntSchema()
										)
									])
								])
							)
						]
					))
				},
				value=None
			),
			PropertySchema(
				name="size",
				decidingProp='type',
				values={
					'slime': JsonUnionSchema(options=[
						JsonIntSchema(description=MDStr('Test if the size of this slime matches an exact value.')),
						JsonObjectSchema(
							description=MDStr('Test if the size of this slime is between <code>min</code> and <code>max</code> values, inclusive.'),
							properties=[
								PropertySchema(
									name="max",
									description=MDStr(''),
									value=JsonIntSchema()
								),
								PropertySchema(
									name="min",
									description=MDStr(''),
									value=JsonIntSchema()
								)
							]
						)
					])
				},
				value=None
			)
		])
	)
])

