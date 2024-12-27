from typing import Optional

from base.model.utils import MDStr
from corePlugins.mcFunction.argumentTypes import BRIGADIER_BOOL, BRIGADIER_INTEGER
from corePlugins.minecraft.resourceLocation import ResourceLocation
from corePlugins.nbtJsonBase.core import *
from corePlugins.minecraft_data.fullData import getCurrentFullMcData


def _propertiesFromBlockStates(blockId: ResourceLocation) -> Optional[ObjectSchema]:
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
			value = StringOptionsSchema(options={val: MDStr("") for val in values}, description=valueDescr, allowMultilineStr=False)
		else:
			value = StringSchema(type=state.type, description=valueDescr, allowMultilineStr=False)

		properties.append(PropertySchema(name=state.name, value=value, optional=True, description=state.description, allowMultilineStr=None))

	return ObjectSchema(properties=properties, allowMultilineStr=None).finish()


def propertiesFor_block_state_property(parent: ObjectNode) -> Optional[ObjectSchema]:
	blockVal = parent.data.get('block', None)
	if blockVal is None or not isinstance(blockVal.value, StringNode):
		return ObjectSchema(properties=[], allowMultilineStr=None).finish()
	else:
		block = blockVal.value.data
		block = ResourceLocation.fromString(block)
		return _propertiesFromBlockStates(block)


def _getTemplate(library: ObjectNode, name: str) -> Optional[ObjectNode]:
	templatesProp = library.data.get('$templates')

	if templatesProp is None or not isinstance(templatesProp.value, ObjectNode):
		return None
	templateProp = templatesProp.value.data.get(name)
	if templateProp is None or not isinstance(templateProp.value, ObjectNode):
		return None
	return templateProp.value


# def propertiesFor_ref(stack: list[JsonData]) -> Optional[ObjectSchema]:
#
# 	library = stack[-1]
# 	if isinstance(stack[-1], ObjectNode):
# 		if isinstance(library, ObjectNode):
#
# 			template = _getTemplate(library, name)
#
# 	blockVal = parent.data.get('block', None)
# 	if blockVal is None or not isinstance(blockVal.value, JsonString):
# 		return ObjectSchema(properties=[])
# 	else:
# 		block = blockVal.value.data
# 		block = ResourceLocation.fromString(block)
# 		return _propertiesFromBlockStates(block)


def init() -> None:
	pass
