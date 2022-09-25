from math import inf
from typing import Optional

from model.commands.argumentTypes import LiteralsArgumentType, BRIGADIER_BOOL, BRIGADIER_INTEGER
from model.datapack.datapackContents import ResourceLocation
from model.json.core import *
from model.parsing.bytesUtils import bytesToStr
from model.utils import MDStr


def _propertiesFromBlockStates(blockId: ResourceLocation) -> Optional[JsonObjectSchema]:
	from session.session import getSession
	states = getSession().minecraftData.blockStates.get(blockId)
	if states is None:
		return None

	properties = []
	for state in states:
		valueDescr: MDStr = state.type.description
		if isinstance(state.type, LiteralsArgumentType):
			value = JsonStringOptionsSchema(options={bytesToStr(opt): MDStr("") for opt in state.type.options}, description=valueDescr)
		elif state.type.name == BRIGADIER_BOOL.name:
			value = JsonBoolSchema(description=valueDescr)
		elif state.type.name == BRIGADIER_INTEGER.name:
			args = state.args or {}
			value = JsonIntSchema(minVal=args.get('min', -inf), maxVal=args.get('max', inf), description=valueDescr)
		else:
			value = JsonStringSchema(type=state.type, description=valueDescr)
		properties.append(PropertySchema(name=state.name, value=value, optional=True, description=state.description))

	return JsonObjectSchema(properties=properties)


def propertiesFor_block_state_property(parent: JsonObject) -> Optional[JsonObjectSchema]:
	blockVal = parent.data.get('block', None)
	if blockVal is None or not isinstance(blockVal.value, JsonString):
		return JsonObjectSchema(properties=[])
	else:
		block = blockVal.value.data
		block = ResourceLocation.fromString(block)
		return _propertiesFromBlockStates(block)


def _getTemplate(library: JsonObject, name: str) -> Optional[JsonObject]:
	templatesProp = library.data.get('$templates')

	if templatesProp is None or not isinstance(templatesProp.value, JsonObject):
		return None
	templateProp = templatesProp.value.data.get(name)
	if templateProp is None or not isinstance(templateProp.value, JsonObject):
		return None
	return templateProp.value


# def propertiesFor_ref(stack: list[JsonData]) -> Optional[JsonObjectSchema]:
#
# 	library = stack[-1]
# 	if isinstance(stack[-1], JsonObject):
# 		if isinstance(library, JsonObject):
#
# 			template = _getTemplate(library, name)
#
# 	blockVal = parent.data.get('block', None)
# 	if blockVal is None or not isinstance(blockVal.value, JsonString):
# 		return JsonObjectSchema(properties=[])
# 	else:
# 		block = blockVal.value.data
# 		block = ResourceLocation.fromString(block)
# 		return _propertiesFromBlockStates(block)


def init() -> None:
	pass