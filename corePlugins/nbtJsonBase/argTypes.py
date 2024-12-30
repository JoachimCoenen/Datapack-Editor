from base.model.utils import MDStr
from .core import StructureArgType, OPTIONS_STRUCTURE_ARG_TYPE

DPE_FLOAT = StructureArgType(
	name='dpe:float',
	description=MDStr("a string containing a float value"),
)

DPE_URL = StructureArgType(
	name='dpe:url',
	description=MDStr("a web address"),
	examples=MDStr(
		"* https://www.minecraft.net\n"
		"* https://github.com/JoachimCoenen/Datapack-Editor"
	),
)

DPE_DEF_REF = StructureArgType(
	name='dpe:def_ref',
	description=MDStr("a reference to a definition in a dpe/json/schema"),
)


DPE_TMPL_REF = StructureArgType(
	name='dpe:tmpl_ref',
	description=MDStr("a reference to a template in a dpe/json/schema"),
)

DPE_TMPL_REF_ARG_KEYS = StructureArgType(
	name='dpe:tmpl_ref_arg_keys',
	description=MDStr("a the arguments of a template in a dpe/json/schema"),
)

DPE_STRUCTURE_ARG_TYPE = StructureArgType(
	name='dpe:json_arg_type',
	description=MDStr("name of a StructureArgType"),
)

DPE_LIB_PATH = StructureArgType(
	name='dpe:schema_library_path',
	description=MDStr("relative path to a schema library"),
)


def init() -> None:
	pass


__all__ = [
	'OPTIONS_STRUCTURE_ARG_TYPE',
	'DPE_FLOAT',
	'DPE_URL',
	'DPE_DEF_REF',
	'DPE_TMPL_REF',
	'DPE_TMPL_REF_ARG_KEYS',
	'DPE_STRUCTURE_ARG_TYPE',
	'DPE_LIB_PATH',
]
