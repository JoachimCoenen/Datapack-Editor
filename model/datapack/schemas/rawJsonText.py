from model.commands.argumentTypes import *
from model.json.core import *

BOOL_STR_SCHEMA = JsonUnionSchema(
	options=[
		JsonBoolSchema(),
		JsonStringSchema(),
	]
)

NUMBER_STR_SCHEMA = JsonUnionSchema(
	options=[
		JsonStringSchema(),
		JsonFloatSchema(),
	]
)


_STR_NUM_BOOL = JsonUnionSchema(
	options=[
		JsonStringSchema(description="A string containing plain text to display directly. This is the same as an object that only has a  text tag. For example, `\"A\"`` and `{\"text\": \"A\"}` are equivalent."),
		JsonBoolSchema(description="A boolean is converted to a string (`\"true\"` or `\"false\"`) to display directly. This is the same as an object that only has a  text tag. For example, true, `\"true\"`, and `{\"text\": \"true\"}` are equivalent."),
		JsonFloatSchema(description="A number is converted to a string to display directly. This is the same as an object that only has a  text tag. For example, 1.9E10, `\"1.9E10\"`, and `{\"text\": \"1.9E10\"}` are equivalent."),
	]
)

RAW_JSON_TEXT_SCHEMA = JsonUnionSchema(options=[])
RAW_JSON_TEXT_SCHEMA.options = [
	_STR_NUM_BOOL,
	JsonArraySchema(
		description=" A list of raw JSON text components. Same as having all components after the first one appended to the first's `extra` array. For example,  `[\"A\", \"B\", \"C\"]` is equivalent to `{\"text\": \"A\", \"extra\": [\"B\", \"C\"]}`.",
		element=RAW_JSON_TEXT_SCHEMA
	),
	JsonObjectSchema(
		description="A text component object. All non-content tags are optional.\nTo be valid, an object must contain the tags for one content type. The different content types and their tags are described below. Having more than one is allowed, but only one is used.",
		properties=[
			# Content:
			PropertySchema(
				name="text",
				description="A string containing plain text to display directly. Can also be a number or boolean that is displayed directly.",
				value=_STR_NUM_BOOL,
				default=''
			),
			PropertySchema(
				name="translate",
				description="A translation identifier, corresponding to the identifiers found in loaded language files. Displayed as the corresponding text in the player's selected language. If no corresponding translation can be found, the identifier itself is used as the translated text.",
				value=JsonStringSchema(),
				default=''
			),
			PropertySchema(
				name="with",
				description=" A list of raw JSON text components to be inserted into slots in the translation text. Ignored if `translate` is not present. ",
				value=JsonArraySchema(
					description="A raw JSON text component. If no component is provided for a slot, the slot is displayed as no text.",
					element=RAW_JSON_TEXT_SCHEMA
				),
				default=[]
			),
			PropertySchema(
				name="score",
				description="This component is resolved into a  text component containing the scoreboard value. ",
				value=JsonObjectSchema(
					description="Displays a score holder's current score in an objective. Displays nothing if the given score holder or the given objective do not exist, or if the score holder is not tracked in the objective. ",
					properties=[
						PropertySchema(
							name="name",
							description="The name of the score holder whose score should be displayed. This can be a selector like `@p` or an explicit name. If the text is a selector, the selector must be guaranteed to never select more than one entity, possibly by adding `limit=1`. If the text is `\"*\"`, it shows the reader's own score (for example, `/tellraw @a {\"score\":{\"name\":\"*\",\"objective\":\"obj\"}}` shows every online player their own score in the \"obj\" objective)",
							value=JsonStringSchema(type=MINECRAFT_SCORE_HOLDER)
						),
						PropertySchema(
							name="objective",
							description="The internal name of the objective to display the player's score in.",
							value=JsonStringSchema(type=MINECRAFT_OBJECTIVE)
						),
						PropertySchema(
							name="value",
							description="If present, this value is displayed regardless of what the score would have been.",
							value=JsonStringSchema(),
							default=''  # this property is optional
						),
					]
				),
				default=''
			),
			PropertySchema(
				name="selector",
				description="Displays the name of one or more entities found by a selector. ",
				value=JsonStringSchema(type=MINECRAFT_ENTITY),  # TODO fix: replace MINECRAFT_ENTITY with target selector
				default=''
			),
			PropertySchema(
				name="separator",
				description="Defaults to `{\"color\": \"gray\", \"text\": \", \"}`. A raw JSON text component. Used as the separator between different names, if the component selects multiple entities.",
				value=RAW_JSON_TEXT_SCHEMA,
				default=''  # this property is optional
			),
			PropertySchema(
				name="keybind",
				description="A keybind identifier, to be displayed as the name of the button that is currently bound to that action. For example, `{\"keybind\": \"key.inventory\"}` displays `\"e\"` if the player is using the default control scheme.",
				value=JsonStringSchema(),  # TODO fix: use DPE_KEYBIND_IDENTIFIER
				default=''
			),
			PropertySchema(
				name="nbt",
				description="TO BE DONE",
				value=JsonNullSchema(),  # TODO nbt in raw JSON text
				default=''
			),


			# Children:
			PropertySchema(
				name="extra",
				description="A list of additional raw JSON text components to be displayed after this one. \nChild text components inherit all formatting and interactivity from the parent component, unless they explicitly override them.",
				value=JsonArraySchema(element=RAW_JSON_TEXT_SCHEMA),
				default=[]
			),


			# Formatting:
			PropertySchema(
				name="color",
				description="The color to render the content in. Valid values are `\"black\"`, `\"dark_blue\"`, `\"dark_green\"`, `\"dark_aqua\"`, `\"dark_red\"`, `\"dark_purple\"`, `\"gold\"`, `\"gray\"`, `\"dark_gray\"`, `\"blue\"`, `\"green\"`, `\"aqua\"`, `\"red\"`, `\"light_purple\"`, `\"yellow\"`, `\"white\"`, and `\"reset\"` (cancels out the effects of colors used by parent objects). \nSet to `\"#<hex>\"` to insert any color in the hexadecimal color format. Example: Using `\"#FF0000\"` makes the component red. Must be a full 6-digit value, not 3-digit.",
				value=JsonStringSchema(),
				default=''  # this property is optional
			),
			PropertySchema(
				name="font",
				description="The resource location of the font for this component in the resource pack within `assets/<namespace>/font`. Defaults to `\"minecraft:default\"`.",
				value=JsonStringSchema(),
				default='minecraft:default'
			),
			PropertySchema(
				name="bold",
				description="Whether to render the content in bold.",
				value=BOOL_STR_SCHEMA,
				default=False
			),
			PropertySchema(
				name="italic",
				description="Whether to render the content in italics. Note that text that is italicized by default, such as custom item names, can be unitalicized by setting this to false.",
				value=BOOL_STR_SCHEMA,
				default=False
			),
			PropertySchema(
				name="underlined",
				description="Whether to underline the content.",
				value=BOOL_STR_SCHEMA,
				default=False
			),
			PropertySchema(
				name="strikethrough",
				description="Whether to strikethrough the content.",
				value=BOOL_STR_SCHEMA,
				default=False
			),
			PropertySchema(
				name="obfuscated",
				description="Whether to render the content obfuscated.",
				value=BOOL_STR_SCHEMA,
				default=False
			),


			# Interactivity:
			PropertySchema(
				name="insertion",
				description="When the text is shift-clicked by a player, this string is inserted in their chat input. It does not overwrite any existing text the player was writing. This only works in chat messages.",
				value=BOOL_STR_SCHEMA,
				default=False
			),
			PropertySchema(
				name="clickEvent",
				description="Allows for events to occur when the player clicks on text. Only work in chat messages and written books, unless specified otherwise. ",
				value=JsonObjectSchema(
					properties=[
						PropertySchema(
							name="action",
							description="The action to perform when clicked. Valid values are: TBD...",  # TODO: add list of valid values!
							value=JsonStringSchema(type=None)  # TODO: add type for clickEvent->action!
						),
						PropertySchema(
							name="value",
							description="The URL, file path, chat, command or book page used by the specified action.",
							value=JsonStringSchema()
						),
					]
				),
				default=''  # this property is optional
			),
			PropertySchema(
				name="hoverEvent",
				description=" Allows for a tooltip to be displayed when the player hovers their mouse over text.",
				value=JsonObjectSchema(
					properties=[
						PropertySchema(
							name="action",
							description="The type of tooltip to show. Valid values are: TBD...",  # TODO: add list of valid values!
							value=JsonStringSchema(type=None)  # TODO: add type for hoverEvent->action!
						),
						PropertySchema(
							name="value",
							description="The formatting and type of this tag varies depending on the action. Deprecated, use  contents instead. ",
							decidingProp='action',
							values={
								'show_text': RAW_JSON_TEXT_SCHEMA,
								'show_item': JsonStringSchema(description="A string containing the SNBT for an item stack. See Player.dat format#Item structure."),
								'show_entity': JsonStringSchema(description="A string containing SNBT. The SNBT does not represent the full entity data, but only stores the name, type, and UUID of the entity. "),
								# TODO: add name, type, and id SNBT subelements for 'show_entity'
							},
							value=None,
							default='',
							deprecated=True
						),
						PropertySchema(
							name="contents",
							description="The URL, file path, chat, command or book page used by the specified action.",
							decidingProp='action',
							values={
								'show_text': RAW_JSON_TEXT_SCHEMA,
								'show_item': JsonObjectSchema(
									description="The item that should be displayed.",
									properties=[
										PropertySchema(name='id', description="The namespaced item ID. Preset `minecraft:air` if invalid.", value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION)),  # TODO: type=ITEM_ID)),
										PropertySchema(name='count', description="Size of the item stack.", value=NUMBER_STR_SCHEMA, default=1),
										PropertySchema(name='tag', description="A string containing the serialized NBT of the additional information about the item, discussed more in the subsections of the player format page.", value=JsonStringSchema(type=MINECRAFT_NBT_TAG), default=''),
									]
								),
								'show_entity': JsonObjectSchema(
									description="The entity that should be displayed.",
									properties=[
										PropertySchema(name='id', description="A string containing the UUID of the entity in the hyphenated hexadecimal format. Should be a valid UUID.", value=JsonStringSchema(type=MINECRAFT_UUID)),
										PropertySchema(name='type', description="A string containing the type of the entity. Should be a namespaced entity ID. Present `minecraft:pig` if invalid.", value=JsonStringSchema()),
										PropertySchema(name='name', description="Hidden if not present. A raw JSON text that is displayed as the name of the entity.", value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION), default=''),  # TODO: type=ENTITY_ID)),
									]
								),
							},
							value=None,
						),
					]
				),
				default=''  # this property is optional
			),
			# TBD!

		]
	)
]
























