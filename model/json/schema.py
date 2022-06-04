from model.json.core import *


def enrichWithSchema(data: JsonData, schema: JsonSchema) -> None:
	dataType = type(data)
	if isinstance(schema, JsonUnionSchema):
		schema = schema.optionsDict2.get(dataType, schema)
	data.schema = schema
	if dataType is JsonArray and isinstance(schema, JsonArraySchema):
		for v in data.data:
			enrichWithSchema(v, schema.element)
	elif dataType is JsonObject and isinstance(schema, JsonObjectSchema):
		anythingProp = schema.anythingProp
		for name, prop in data.data.items():
			prop.key.schema = JSON_KEY_SCHEMA
			propSchema = schema.propertiesDict.get(name, anythingProp)
			if propSchema is not None:
				_enrichProperty(prop, propSchema, data)


def _enrichProperty(prop: JsonProperty, schema: SwitchingPropertySchema, parent: JsonObject):
	prop.schema = schema
	selectedSchema = schema.valueForParent(parent)
	# decidingProp = schema.decidingProp
	# if decidingProp is not None:
	# 	dp = parent.data.get(decidingProp)
	# 	if dp is not None:
	# 		dVal = dp.value.data
	# 	else:
	# 		dVal = None
	# 	selectedSchema = schema.values.get(dVal, schema.value)
	# else:
	# 	selectedSchema = schema.value
	enrichWithSchema(prop.value, selectedSchema)
