from base.model.utils import MDStr
from corePlugins.datapackVersions.commands import argumentTypes as commandArgumentTypes
from corePlugins.mcFunction.argumentTypes import ArgumentType
from corePlugins.nbtJsonBase.core import StructureArgType


def fromCommandArgumentType(commandArgumentType: ArgumentType, **kwargs) -> StructureArgType:
	argumentType = StructureArgType(
		name=kwargs.get('name', commandArgumentType.name),
		description=kwargs.get('description', MDStr(commandArgumentType.description)),
		description2=kwargs.get('description2', MDStr(commandArgumentType.description2)),
		example=kwargs.get('example', MDStr(commandArgumentType.example)),
		examples=kwargs.get('examples', MDStr(commandArgumentType.examples)),
		NBTProperties=kwargs.get('NBTProperties', commandArgumentType.jsonProperties),
	)
	argumentType.commandArgumentType = commandArgumentType
	return argumentType


MINECRAFT_CHAT_COMMAND = StructureArgType(
	name='minecraft:chat_command',
	description=MDStr("A minecraft command"),
	description2=MDStr(""),
	examples=MDStr(""),
)

DPE_STRINGIFIED_JSON_TAG = StructureArgType(
	name='dpe:stringified_json',
	description=MDStr("Must be JSON within a string."),
	description2=MDStr(""""""),
	examples=MDStr(""""""),
)

MINECRAFT_NBT_COMPOUND_TAG = StructureArgType(
	name='minecraft:nbt_compound_tag',
	description=MDStr("Must be a compound NBT in SNBT format."),
	description2=MDStr(""""""),
	examples=MDStr("""
	* <code>{}</code>
	* <code>{foo:bar}</code>"""),
)

MINECRAFT_NBT_PATH = StructureArgType(
	name='minecraft:nbt_path',
	description=MDStr("Must be an NBT path."),
	description2=MDStr(""""""),
	examples=MDStr("""
	* {{cd|foo}}
	* {{cd|foo.bar}}
	* {{cd|foo[0]}}
	* {{cd|[0]}}
	* <code>[]</code>
	* <code>{foo:bar}</code>"""),
)

MINECRAFT_NBT_TAG = StructureArgType(
	name='minecraft:nbt_tag',
	description=MDStr("Must be an NBT tag of any type in SNBT format."),
	description2=MDStr(""""""),
	examples=MDStr("""
	* {{cd|0}}
	* {{cd|0b}}
	* {{cd|0l}}
	* {{cd|0.0}}
	* {{cd|"foo"}}
	* <code>{foo:bar}</code>"""),
)

MINECRAFT_RESOURCE_LOCATION = StructureArgType(
	name='minecraft:resource_location',
	description=MDStr("{{Arg desc|je=resource_location}}"),
	description2=MDStr(""),
	examples=MDStr(
		"* {{cd|foo}}\n"
		"* {{cd|foo:bar}}\n"
		"* {{cd|012}}\n"
	),
)

MINECRAFT_BLOCK_POS = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_BLOCK_POS)
MINECRAFT_COLOR = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_COLOR)
MINECRAFT_GAME_MODE = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_GAME_MODE)
MINECRAFT_OBJECTIVE = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_OBJECTIVE)
MINECRAFT_SCORE_HOLDER = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_SCORE_HOLDER)
MINECRAFT_TARGET_SELECTOR = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_ENTITY, name='minecraft:target_selector')  # for now
MINECRAFT_ITEM_SLOTS = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_ITEM_SLOTS)
MINECRAFT_UUID = fromCommandArgumentType(commandArgumentTypes.MINECRAFT_UUID)


def init() -> None:
	pass


__all__ = [
	'MINECRAFT_CHAT_COMMAND',
	'DPE_STRINGIFIED_JSON_TAG',
	'MINECRAFT_NBT_COMPOUND_TAG',
	'MINECRAFT_NBT_PATH',
	'MINECRAFT_NBT_TAG',
	'MINECRAFT_RESOURCE_LOCATION',
	'MINECRAFT_SCORE_HOLDER',
	'MINECRAFT_OBJECTIVE',
	'MINECRAFT_TARGET_SELECTOR',
	'MINECRAFT_BLOCK_POS',
	'MINECRAFT_COLOR',
	'MINECRAFT_GAME_MODE',
	'MINECRAFT_ITEM_SLOTS',
	'MINECRAFT_UUID',
]
