from cat.utils import Anything
from .core import *


def enrichWithSchema(data: JsonData, schema: JsonSchema) -> bool:
	# data.schema = schema
	if schema is not None:
		return _enrichWithSchemaInternal(data, schema)
	else:
		_enrichWithAnySchema(data)
		data.schema = None
		return False


def _enrichWithSchemaInternal(data: JsonData, schema: JsonSchema) -> bool:
	dataType = type(data)
	if isinstance(schema, JsonUnionSchema):
		return _enrichWithUnionSchema(data, schema)

	if schema.typeName == 'any':
		_enrichWithAnySchema(data)
		return True

	if schema.DATA_TYPE == dataType:
		data.schema = schema
		if dataType is JsonArray and isinstance(schema, JsonArraySchema):
			return _enrichArrayWithSchema(data, schema)
		elif dataType is JsonObject and isinstance(schema, JsonObjectSchema):
			return _enrichObjectWithSchema(data, schema)
		return True
	return False


def _enrichWithUnionSchema(data: JsonData, schema: JsonUnionSchema) -> bool:
	for opt in schema.allOptions:
		if _enrichWithSchemaInternal(data, opt):
			return True
	data.schema = schema
	return False


def _enrichArrayWithSchema(data: JsonArray, schema: JsonArraySchema) -> bool:
	result = True  # todo: check, use false here, if array contains any values.
	for v in data.data:
		result |= enrichWithSchema(v, schema.element)
	return result


def _enrichObjectWithSchema(data: JsonObject, schema: JsonObjectSchema) -> bool:
	result = True  # 2 = OK, 1 = Maybe, 0 = No

	for prop in schema.properties:
		if prop.mandatory and not prop.values and prop.name is not Anything:
			if not all(r in data.data for r in prop.requires):
				continue
			if any(r in data.data for r in prop.hates):
				continue
			if prop.name not in data.data:
				result = False

	for name, prop in data.data.items():
		result = _enrichProperty(name, prop, schema, data) and result

	return result


def _enrichProperty(name: str, prop: JsonProperty, parentSchema: JsonObjectSchema, parent: JsonObject) -> bool:
	propSchema, valueSchema = parentSchema.getSchemaForPropAndVal(name, parent)
	if propSchema is not None:
		prop.schema = propSchema
		if valueSchema is not None:
			return enrichWithSchema(prop.value, valueSchema)
	return False


def _enrichWithAnySchema(data: JsonData):
	if data.schema is None:
		data.schema = JSON_ANY_SCHEMA
		dataType = type(data)
		if dataType is JsonArray:
			for v in data.data:
				_enrichWithAnySchema(v)
		# elif dataType is JsonObject:
		# 	for key, prop in data.data.items():
		# 		if prop.schema is None:
		# 			prop.schema = PropertySchema(name=key, value=JSON_ANY_SCHEMA, allowMultilineStr=None)
		# 			_enrichWithAnySchema(prop.value)


def _enrichWithIllegalSchema(data: JsonData):
	data.schema = JSON_ILLEGAL_SCHEMA


def pathify(data: JsonData, path: str) -> None:
	data.path = path
	if isinstance(data, JsonArray):
		for i, element in enumerate(data.data):
			pathify(element, f'{path}[{i}]')
	elif isinstance(data, JsonObject):
		for key, prop in data.data.items():
			ppath = f'{path}/{key}'
			pathify(prop.value, ppath)
