from model.json.core import JsonArgType
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

DPE_FLOAT = JsonArgType(
	name='dpe:float',
	description=MDStr("a string containing a float value"),
	description2=MDStr(""),
	examples=MDStr(
		"* true\n"
		"* false"
	),
)

DPE_URL = JsonArgType(
	name='dpe:url',
	description=MDStr("a web address"),
	description2=MDStr(""),
	examples=MDStr(
		"* https://www.minecraft.net\n"
		"* https://github.com/JoachimCoenen/Datapack-Editor"
	),
)

DPE_DEF_REF = JsonArgType(
	name='dpe:def_ref',
	description=MDStr("a reference to a definition in a dpe/json/schema"),
)


DPE_TMPL_REF = JsonArgType(
	name='dpe:tmpl_ref',
	description=MDStr("a reference to a template in a dpe/json/schema"),
)

DPE_JSON_ARG_TYPE = JsonArgType(
	name='dpe:json_arg_type',
	description=MDStr("name of a JsonArgType"),
)

DPE_LIB_PATH = JsonArgType(
	name='dpe:schema_library_path',
	description=MDStr("relative path to a schema library"),
)


def init() -> None:
	pass


__all__ = [
	'MINECRAFT_CHAT_COMMAND',
	'MINECRAFT_NBT_COMPOUND_TAG',
	'MINECRAFT_NBT_TAG',
	'MINECRAFT_CHAT_COMMAND',
	'MINECRAFT_RESOURCE_LOCATION',
	'DPE_FLOAT',
	'DPE_URL',
	'DPE_DEF_REF',
	'DPE_TMPL_REF',
	'DPE_JSON_ARG_TYPE',
	'DPE_LIB_PATH',
]
