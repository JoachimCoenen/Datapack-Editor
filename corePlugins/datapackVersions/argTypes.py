from corePlugins.json.core import JsonArgType
from base.model.utils import MDStr

MINECRAFT_CHAT_COMMAND = JsonArgType(
	name='minecraft:chat_command',
	description=MDStr("A minecraft command"),
	description2=MDStr(""),
	examples=MDStr(""),
)

MINECRAFT_NBT_COMPOUND_TAG = JsonArgType(
	name='minecraft:nbt_compound_tag',
	description=MDStr("Must be a compound NBT in SNBT format."),
	description2=MDStr(""""""),
	examples=MDStr("""
	* <code>{}</code>
	* <code>{foo:bar}</code>"""),
)

MINECRAFT_NBT_PATH = JsonArgType(
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

MINECRAFT_NBT_TAG = JsonArgType(
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

MINECRAFT_RESOURCE_LOCATION = JsonArgType(
	name='minecraft:resource_location',
	description=MDStr("{{Arg desc|je=resource_location}}"),
	description2=MDStr(""),
	examples=MDStr(
		"* {{cd|foo}}\n"
		"* {{cd|foo:bar}}\n"
		"* {{cd|012}}\n"
	),
)


def init() -> None:
	pass


__all__ = [
	'MINECRAFT_CHAT_COMMAND',
	'MINECRAFT_NBT_COMPOUND_TAG',
	'MINECRAFT_NBT_TAG',
	'MINECRAFT_CHAT_COMMAND',
	'MINECRAFT_RESOURCE_LOCATION',
]
