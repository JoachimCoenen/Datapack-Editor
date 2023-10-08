from base.model.utils import MDStr
from .core import JsonArgType, OPTIONS_JSON_ARG_TYPE

DPE_FLOAT = JsonArgType(
	name='dpe:float',
	description=MDStr("a string containing a float value"),
)

DPE_URL = JsonArgType(
	name='dpe:url',
	description=MDStr("a web address"),
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
	'OPTIONS_JSON_ARG_TYPE',
	'DPE_FLOAT',
	'DPE_URL',
	'DPE_DEF_REF',
	'DPE_TMPL_REF',
	'DPE_JSON_ARG_TYPE',
	'DPE_LIB_PATH',
]