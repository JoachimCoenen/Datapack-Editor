from model.commands.argumentTypes import *
from model.datapackContents import ResourceLocationSchema
from ..argTypes import *
from model.json.core import *
from model.utils import MDStr

# see: https://minecraft.fandom.com/wiki/Raw_JSON_text_format#Plain_Text

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
		JsonStringSchema(description=MDStr("A string containing plain text to display directly. This is the same as an object that only has a  text tag. For example, `\"A\"` and `{\"text\": \"A\"}` are equivalent.")),
		JsonBoolSchema(description=MDStr("A boolean is converted to a string (`\"true\"` or `\"false\"`) to display directly. This is the same as an object that only has a  text tag. For example, true, `\"true\"`, and `{\"text\": \"true\"}` are equivalent.")),
		JsonFloatSchema(description=MDStr("A number is converted to a string to display directly. This is the same as an object that only has a  text tag. For example, 1.9E10, `\"1.9E10\"`, and `{\"text\": \"1.9E10\"}` are equivalent.")),
	]
)

RAW_JSON_TEXT_SCHEMA = JsonUnionSchema(options=[])
RAW_JSON_TEXT_SCHEMA.options = [
	_STR_NUM_BOOL,
	JsonArraySchema(
		description=MDStr(" A list of raw JSON text components. Same as having all components after the first one appended to the first's `extra` array. For example,  `[\"A\", \"B\", \"C\"]` is equivalent to `{\"text\": \"A\", \"extra\": [\"B\", \"C\"]}`."),
		element=RAW_JSON_TEXT_SCHEMA
	),
	JsonObjectSchema(
		description=MDStr("A text component object. All non-content tags are optional.\nTo be valid, an object must contain the tags for one content type. The different content types and their tags are described below. Having more than one is allowed, but only one is used."),
		properties=[
			# Content:
			PropertySchema(
				name="text",
				description=MDStr("A string containing plain text to display directly. Can also be a number or boolean that is displayed directly."),
				value=_STR_NUM_BOOL,
				optional=True,
			),
			PropertySchema(
				name="translate",
				description=MDStr("A translation identifier, corresponding to the identifiers found in loaded language files. Displayed as the corresponding text in the player's selected language. If no corresponding translation can be found, the identifier itself is used as the translated text."),
				value=JsonStringSchema(),
				optional=True,
			),
			PropertySchema(
				name="with",
				description=MDStr(" A list of raw JSON text components to be inserted into slots in the translation text. Ignored if `translate` is not present. "),
				value=JsonArraySchema(
					description=MDStr("A raw JSON text component. If no component is provided for a slot, the slot is displayed as no text."),
					element=RAW_JSON_TEXT_SCHEMA
				),
				optional=True
			),
			PropertySchema(
				name="score",
				description=MDStr("This component is resolved into a  text component containing the scoreboard value. "),
				value=JsonObjectSchema(
					description=MDStr("Displays a score holder's current score in an objective. Displays nothing if the given score holder or the given objective do not exist, or if the score holder is not tracked in the objective. "),
					properties=[
						PropertySchema(
							name="name",
							description=MDStr("The name of the score holder whose score should be displayed. This can be a selector like `@p` or an explicit name. If the text is a selector, the selector must be guaranteed to never select more than one entity, possibly by adding `limit=1`. If the text is `\"*\"`, it shows the reader's own score (for example, `/tellraw @a {\"score\":{\"name\":\"*\",\"objective\":\"obj\"}}` shows every online player their own score in the \"obj\" objective)"),
							value=JsonStringSchema(type=MINECRAFT_SCORE_HOLDER)
						),
						PropertySchema(
							name="objective",
							description=MDStr("The internal name of the objective to display the player's score in."),
							value=JsonStringSchema(type=MINECRAFT_OBJECTIVE)
						),
						PropertySchema(
							name="value",
							description=MDStr("If present, this value is displayed regardless of what the score would have been."),
							value=JsonStringSchema(),
							optional=True,
						),
					]
				),
				optional=True
			),
			PropertySchema(
				name="selector",
				description=MDStr("Displays the name of one or more entities found by a selector. "),
				value=JsonStringSchema(type=MINECRAFT_ENTITY),  # TODO fix: replace MINECRAFT_ENTITY with target selector
				optional=True
			),
			PropertySchema(
				name="separator",
				description=MDStr("Defaults to `{\"color\": \"gray\", \"text\": \", \"}`. A raw JSON text component. Used as the separator between different names, if the component selects multiple entities."),
				value=RAW_JSON_TEXT_SCHEMA,
				optional=True
			),
			PropertySchema(
				name="keybind",
				description=MDStr("A keybind identifier, to be displayed as the name of the button that is currently bound to that action. For example, `{\"keybind\": \"key.inventory\"}` displays `\"e\"` if the player is using the default control scheme."),
				value=JsonStringSchema(),  # TODO fix: use DPE_KEYBIND_IDENTIFIER
				optional=True
			),
			PropertySchema(
				name="nbt",
				description=MDStr("TO BE DONE"),  # TODO description for nbt in raw JSON text
				value=JsonStringSchema(type=MINECRAFT_NBT_COMPOUND_TAG),
				optional=True
			),


			# Children:
			PropertySchema(
				name="extra",
				description=MDStr("A list of additional raw JSON text components to be displayed after this one. \nChild text components inherit all formatting and interactivity from the parent component, unless they explicitly override them."),
				value=JsonArraySchema(element=RAW_JSON_TEXT_SCHEMA),
				optional=True
			),


			# Formatting:
			PropertySchema(
				name="color",
				description=MDStr("The color to render the content in. Valid values are `\"black\"`, `\"dark_blue\"`, `\"dark_green\"`, `\"dark_aqua\"`, `\"dark_red\"`, `\"dark_purple\"`, `\"gold\"`, `\"gray\"`, `\"dark_gray\"`, `\"blue\"`, `\"green\"`, `\"aqua\"`, `\"red\"`, `\"light_purple\"`, `\"yellow\"`, `\"white\"`, and `\"reset\"` (cancels out the effects of colors used by parent objects). \nSet to `\"#<hex>\"` to insert any color in the hexadecimal color format. Example: Using `\"#FF0000\"` makes the component red. Must be a full 6-digit value, not 3-digit."),
				value=JsonStringSchema(),
				optional=True
			),
			PropertySchema(
				name="font",
				description=MDStr("The resource location of the font for this component in the resource pack within `assets/<namespace>/font`. Defaults to `\"minecraft:default\"`."),
				value=JsonStringSchema(),
				optional=True,
				default='minecraft:default'
			),
			PropertySchema(
				name="bold",
				description=MDStr("Whether to render the content in bold."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),
			PropertySchema(
				name="italic",
				description=MDStr("Whether to render the content in italics. Note that text that is italicized by default, such as custom item names, can be unitalicized by setting this to false."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),
			PropertySchema(
				name="underlined",
				description=MDStr("Whether to underline the content."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),
			PropertySchema(
				name="strikethrough",
				description=MDStr("Whether to strikethrough the content."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),
			PropertySchema(
				name="obfuscated",
				description=MDStr("Whether to render the content obfuscated."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),


			# Interactivity:
			PropertySchema(
				name="insertion",
				description=MDStr("When the text is shift-clicked by a player, this string is inserted in their chat input. It does not overwrite any existing text the player was writing. This only works in chat messages."),
				value=BOOL_STR_SCHEMA,
				optional=True,
				default=False
			),
			PropertySchema(
				name="clickEvent",
				description=MDStr("Allows for events to occur when the player clicks on text. Only work in chat messages and written books, unless specified otherwise. "),
				value=JsonObjectSchema(
					properties=[
						PropertySchema(
							name="action",
							description=MDStr("The action to perform when clicked."),
							value=JsonStringOptionsSchema(
								options={
									"open_url": MDStr("Opens  value as a URL in the user's default web browser."),
									# ... and cannot be used by players for security reasons. "open_file": MDStr("Opens the file at  value on the user's computer. This is used in messages automatically generated by the game (e.g., on taking a screenshot) and cannot be used by players for security reasons."),
									"run_command": MDStr("Works in signs, but only on the root text component, not on any children. Activated by using the sign. In chat and written books, this has  value entered in chat as though the player typed it themselves and pressed enter. This can be used to run commands, provided the player has the required permissions. Since they are being run from chat, commands must be prefixed with the usual \"/\" slash. In signs, the command is run by the server at the sign's location, with the player who used the sign as @s. Since they are run by the server, sign commands have the same permission level as a command block instead of using the player's permission level, are not restricted by chat length limits, and do not need to be prefixed with a \"/\" slash."),
									"suggest_command": MDStr("Opens chat and fills in the command given in value. If a chat message was already being composed, it is overwritten. This does not work in books."),
									"change_page": MDStr("Can only be used in written books. Changes to page  value if that page exists."),
									"copy_to_clipboard": MDStr("Copies  value to the clipboard."),
								}
							)
						),
						PropertySchema(
							name="value",
							description=MDStr("The URL, file path, chat, command or book page used by the specified action."),
							decidingProp='action',
							values={
								'open_url': JsonStringSchema(type=DPE_URL),
								'run_command': JsonStringSchema(type=MINECRAFT_CHAT_COMMAND),
								'suggest_command': JsonStringSchema(type=MINECRAFT_CHAT_COMMAND, args=dict(incomplete=True)),
								'change_page': NUMBER_STR_SCHEMA,
								'copy_to_clipboard': JsonStringSchema(),
							},
							value=None,
						),
					]
				),
				optional=True
			),
			PropertySchema(
				name="hoverEvent",
				description=MDStr(" Allows for a tooltip to be displayed when the player hovers their mouse over text."),
				value=JsonObjectSchema(
					properties=[
						PropertySchema(
							name="action",
							description=MDStr("The type of tooltip to show."),
							value=JsonStringOptionsSchema(
								options={
									"show_text": MDStr("Shows a raw JSON text component."),
									"show_item": MDStr("Shows the tooltip of an item as if it was being hovering over it in an inventory."),
									"show_entity": MDStr("Shows an entity's name, type, and UUID. Used by  selector."),
								}

							)
						),
						PropertySchema(  # DEPRECATED!
							name="value",
							description=MDStr("The formatting and type of this tag varies depending on the action. Deprecated, use  contents instead."),
							decidingProp='action',
							values={
								'show_text': RAW_JSON_TEXT_SCHEMA,
								'show_item': JsonStringSchema(
									type=MINECRAFT_NBT_COMPOUND_TAG,
									description=MDStr("A string containing the SNBT for an item stack. See Player.dat format#Item structure."),
								),
								'show_entity': JsonStringSchema(
									type=MINECRAFT_NBT_COMPOUND_TAG,
									description=MDStr("A string containing SNBT. The SNBT does not represent the full entity data, but only stores the name, type, and UUID of the entity. "),
								),
							},
							value=None,
							optional=True,
							deprecated=True
						),
						PropertySchema(
							name="contents",
							description=MDStr("The URL, file path, chat, command or book page used by the specified action."),
							decidingProp='action',
							values={
								'show_text': RAW_JSON_TEXT_SCHEMA,
								'show_item': JsonObjectSchema(
									description=MDStr("The item that should be displayed."),
									properties=[
										PropertySchema(
											name='id',
											description=MDStr("The namespaced item ID. Preset `minecraft:air` if invalid."),
											value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema('', 'item')))
										),
										PropertySchema(
											name='count',
											description=MDStr("Size of the item stack."),
											value=NUMBER_STR_SCHEMA,
											optional=True,
											default=1
										),
										PropertySchema(
											name='tag',
											description=MDStr("A string containing the serialized NBT of the additional information about the item, discussed more in the subsections of the player format page."),
											value=JsonStringSchema(type=MINECRAFT_NBT_TAG),
											optional=True,
										),
									]
								),
								'show_entity': JsonObjectSchema(
									description=MDStr("The entity that should be displayed."),
									properties=[
										PropertySchema(name='id', description=MDStr("A string containing the UUID of the entity in the hyphenated hexadecimal format. Should be a valid UUID."), value=JsonStringSchema(type=MINECRAFT_UUID)),
										PropertySchema(name='type', description=MDStr("A string containing the type of the entity. Should be a namespaced entity ID. Present `minecraft:pig` if invalid."), value=JsonStringSchema()),
										PropertySchema(name='name', description=MDStr("Hidden if not present. A raw JSON text that is displayed as the name of the entity."), value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION), optional=True),  # TODO: type=ENTITY_ID)),
									]
								),
							},
							value=None,
						),
					]
				),
				optional=True
			),
			# TBD!

		]
	)
]
