from .core import *


def enrichWithSchema(data: StructureDataNode, schema: StructureDataSchema) -> bool:
	# data.schema = schema
	if schema is not None:
		return _enrichWithSchemaInternal(data, schema) > 0
	else:
		_enrichWithAnySchema(data)
		data.schema = None
		return False


def _enrichWithSchemaInternal(data: StructureDataNode, schema: StructureDataSchema) -> int:
	# 2 = OK, 1 = Maybe, 0 = No
	schema = resolveCalculatedSchema(schema, data.parent)
	if isinstance(schema, UnionSchema):
		return _enrichWithUnionSchema(data, schema)

	if schema.typeName == 'any':
		_enrichWithAnySchema(data)
		return 2

	dataType = type(data)
	if issubclass(dataType, schema.DATA_TYPE):
		data.schema = schema
		if isinstance(data, ListLikeNode) and isinstance(schema, ListLikeSchema):
			return _enrichListLikeWithSchema(data, schema)
		elif isinstance(data, ObjectNode) and isinstance(schema, ObjectSchema):
			return _enrichObjectWithSchema(data, schema)
		return 2
	# elif dataType is JsonInvalid:
	# 	data.schema = schema
	return 0


def _enrichWithUnionSchema(data: StructureDataNode, schema: UnionSchema) -> int:
	result = 0
	for opt in schema.allOptions:
		internal = _enrichWithSchemaInternal(data, opt)
		if internal == 2:
			return 2
		if internal == 1:
			result = 1
	if result == 0:
		data.schema = schema
	return result


def _enrichListLikeWithSchema(data: ListLikeNode, schema: ListLikeSchema) -> int:
	atLeastOneOK = False
	allOK = True
	for v in data.data:
		if enrichWithSchema(v, schema.element):
			atLeastOneOK = True
		else:
			allOK = False
	return 2 if allOK else (1 if atLeastOneOK else 0)


def _enrichObjectWithSchema(data: ObjectNode, schema: ObjectSchema) -> int:
	# 2 = OK, 1 = Maybe, 0 = No
	needsAMandatory = False
	atLeastOneMandatory = False
	allMandatory = True
	hasDefiningProp = not schema.definingProps.isdisjoint(data.data.keys())
	if not hasDefiningProp:
		for prop in schema.propertiesDict.values():
			if prop.mandatory and not prop.values:
				if any(r in data.data for r in prop.hates):
					continue
				needsAMandatory = True
				if prop.name in data.data:
					atLeastOneMandatory = True
				if not all(r in data.data for r in prop.requires):
					continue
				if prop.name not in data.data:
					allMandatory = False

		atLeastOneMandatory = atLeastOneMandatory or not needsAMandatory  # treat atLeastOneMandatory as True if nothing in the schema is mandatory.

	atLeastOneOK = False
	allOK = True
	for name, prop in data.data.items():
		if _enrichProperty(name, prop, schema, data):
			atLeastOneOK = True
		else:
			allOK = False

	return 2 if hasDefiningProp or (allOK and allMandatory) else (1 if atLeastOneOK and atLeastOneMandatory else 0)


def _enrichProperty(name: str, prop: StructureProperty, parentSchema: ObjectSchema, parent: ObjectNode) -> bool:
	propSchema, valueSchema = parentSchema.getSchemaForPropAndVal(name, parent)
	if propSchema is not None:
		prop.schema = propSchema
		if valueSchema is not None:
			return enrichWithSchema(prop.value, valueSchema)
	return False


def _enrichWithAnySchema(data: StructureDataNode):
	if data.schema is None:
		data.schema = STRUCTURE_ANY_SCHEMA
		if isinstance(data, ListLikeNode):
			for v in data.data:
				_enrichWithAnySchema(v)
		# elif isinstance(data, ObjectNode):
		# 	for key, prop in data.data.items():
		# 		if prop.schema is None:
		# 			prop.schema = PropertySchema(name=key, value=JSON_ANY_SCHEMA, allowMultilineStr=None)
		# 			_enrichWithAnySchema(prop.value)


def _enrichWithIllegalSchema(data: StructureDataNode):
	data.schema = STRUCTURE_ILLEGAL_SCHEMA


def pathify(data: StructureDataNode, path: str) -> None:
	data.path = path
	if isinstance(data, ListLikeNode):
		for i, element in enumerate(data.data):
			pathify(element, f'{path}[{i}]')
	elif isinstance(data, ObjectNode):
		for key, prop in data.data.items():
			ppath = f'{path}/{key}'
			pathify(prop.value, ppath)
