from typing import Optional

from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.utils import MDStr, LanguageId
from corePlugins.mcFunction.argumentTypes import BRIGADIER_BOOL, BRIGADIER_INTEGER
from corePlugins.minecraft.resourceLocation import ResourceLocation
from corePlugins.nbt import SNBT_ID
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
	if blockVal is None:
		blockVal = parent.data.get('Name', None)  # for utils-library.json/block_state
	if blockVal is None or not isinstance(blockVal.value, StringNode):
		return ObjectSchema(properties=[], allowMultilineStr=None).finish()
	else:
		block = blockVal.value.data
		block = ResourceLocation.fromString(block)
		return _propertiesFromBlockStates(block)


def _getStructureSchema(name: str, language: LanguageId) -> StructureDataSchema:
	schema = GLOBAL_SCHEMA_STORE.get(name, language)
	if schema is None:
		schema = STRUCTURE_ANY_SCHEMA
	return schema


def _propertiesForItemComponents(itemId: ResourceLocation | None, removable: bool) -> Optional[ObjectSchema]:
	# todo: which items have which components?
	allItemComponents = getCurrentFullMcData().itemComponents

	properties = []
	for itemComponent in allItemComponents:
		name = f'{itemComponent.actualNamespace}:item_components/{itemComponent.path}'
		value = _getStructureSchema(name, SNBT_ID)

		properties.append(PropertySchema(name=itemComponent.asQualifiedString, value=value, optional=True, description=MDStr(''), allowMultilineStr=None))
		if itemComponent.isMCNamespace:
			properties.append(PropertySchema(name=itemComponent.asCompactString, value=value, optional=True, description=MDStr(''), allowMultilineStr=None))

		if removable:
			valueDescr: MDStr = MDStr("")
			value2 = ObjectSchema(description=valueDescr, properties=[], allowMultilineStr=None)
			properties.append(PropertySchema(name='!' + itemComponent.asQualifiedString, value=value2, optional=True, description=MDStr(''), allowMultilineStr=None))
			if itemComponent.isMCNamespace:
				properties.append(PropertySchema(name='!' + itemComponent.asCompactString, value=value2, optional=True, description=MDStr(''), allowMultilineStr=None))

	return ObjectSchema(properties=properties, allowMultilineStr=None).finish()


def _propertiesFor_item_stack_components(parent: ObjectNode, removable: bool) -> Optional[ObjectSchema]:
	itemIdNode = parent.data.get('id', None)
	if itemIdNode is None or not isinstance(itemIdNode.value, StringNode):
		itemId = None
	else:
		itemId = ResourceLocation.fromString(itemIdNode.value.data)
	return _propertiesForItemComponents(itemId, removable=removable)


def propertiesFor_item_stack_components(parent: ObjectNode) -> Optional[ObjectSchema]:
	return _propertiesFor_item_stack_components(parent, removable=False)


def propertiesFor_removable_item_stack_components(parent: ObjectNode) -> Optional[ObjectSchema]:
	return _propertiesFor_item_stack_components(parent, removable=True)


def propertiesFor_item_sub_predicates(parent: ObjectNode) -> Optional[ObjectSchema]:
	allItemSubPredicates = getCurrentFullMcData().itemSubPredicates

	properties = []
	for itemSubPredicate in allItemSubPredicates:
		name = f'{itemSubPredicate.actualNamespace}:item_sub_predicates/{itemSubPredicate.path}'
		value = _getStructureSchema(name, SNBT_ID)

		properties.append(PropertySchema(name=itemSubPredicate.asQualifiedString, value=value, optional=True, description=MDStr(''), allowMultilineStr=None))
		if itemSubPredicate.isMCNamespace:
			properties.append(PropertySchema(name=itemSubPredicate.asCompactString, value=value, optional=True, description=MDStr(''), allowMultilineStr=None))

	return ObjectSchema(properties=properties, allowMultilineStr=None).finish()


def init() -> None:
	pass
