from typing import Optional

from base.model.utils import MDStr
from corePlugins.mcFunction.argumentTypes import BRIGADIER_BOOL, BRIGADIER_INTEGER
from corePlugins.minecraft.resourceLocation import ResourceLocation
from corePlugins.json.core import *
from corePlugins.minecraft_data.fullData import getCurrentFullMcData


def _propertiesFromBlockStates(blockId: ResourceLocation) -> Optional[JsonObjectSchema]:
	states = getCurrentFullMcData().blockStates.get(blockId)
	if states is None:
		return None

	properties = []
	for state in states:
		valueDescr: MDStr = MDStr("")
		if state.values:
			values = state.values
		elif state.type == BRIGADIER_BOOL.name:
			values = ['true', 'false']
		elif state.type == BRIGADIER_INTEGER.name and state.range is not None:
			values = [str(i) for i in range(state.range[0], state.range[1] + 1)]
		else:
			values = None

		if values is not None:
			value = JsonStringOptionsSchema(options={val: MDStr("") for val in values}, description=valueDescr, allowMultilineStr=False)
		else:
			value = JsonStringSchema(type=state.type, description=valueDescr, allowMultilineStr=False)

		properties.append(PropertySchema(name=state.name, value=value, optional=True, description=state.description, allowMultilineStr=None))

	return JsonObjectSchema(properties=properties, allowMultilineStr=None)


def propertiesFor_block_state_property(parent: JsonObject) -> Optional[JsonObjectSchema]:
	blockVal = parent.data.get('block', None)
	if blockVal is None or not isinstance(blockVal.value, JsonString):
		return JsonObjectSchema(properties=[], allowMultilineStr=None)
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
