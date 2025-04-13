from .core import StructureDataNode, ListLikeNode, StructureProperty, ObjectNode, StructureDataSchema, ListLikeSchema, \
	KeySchema, ObjectSchema, UnionSchema, resolveCalculatedSchema, STRUCTURE_ANY_SCHEMA, STRUCTURE_ILLEGAL_SCHEMA


def enrichWithSchema(data: StructureDataNode, schema: StructureDataSchema | None) -> bool:
	# data.schema = schema
	if schema is not None:
		return _enrichWithSchemaInternal(data, schema) > 0
	else:
		_enrichWithAnySchema(data)
		data.schema = None
		return False


def _enrichWithSchemaInternal(data: StructureDataNode, schema: StructureDataSchema) -> int:
	# 2 = OK, 1 = Maybe, 0 = No
	resolvedSchema = resolveCalculatedSchema(schema, data.parent)
	if isinstance(resolvedSchema, UnionSchema):
		return _enrichWithUnionSchema(data, resolvedSchema)

	if resolvedSchema is None:
		return 0

	if resolvedSchema.typeName == 'any':
		_enrichWithAnySchema(data)
		return 2

	dataType = type(data)
	if issubclass(dataType, resolvedSchema.DATA_TYPE):
		data.schema = resolvedSchema
		if isinstance(data, ListLikeNode) and isinstance(resolvedSchema, ListLikeSchema):
			return _enrichListLikeWithSchema(data, resolvedSchema)
		elif isinstance(data, ObjectNode) and isinstance(resolvedSchema, ObjectSchema):
			return _enrichObjectWithSchema(data, resolvedSchema)
		return 2
	# elif dataType is JsonInvalid:
	# 	data.schema = resolvedSchema
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
	# todo: don't know how to properly incorporate exclusionGroups...
	needsAMandatory = False
	hasAtLeastOneMandatory = False
	allMandatory = True
	hasDefiningProp = not schema.definingProps.isdisjoint(data.data.keys())
	if not hasDefiningProp:
		for prop in schema.propertiesDict.values():
			if prop.mandatory and not prop.values:
				if any(r in data.data for r in prop.hates):
					continue
				needsAMandatory = True
				if prop.name in data.data:  # type: ignore  # mypy gets confused by `Anything`
					hasAtLeastOneMandatory = True
				if not all(r in data.data for r in prop.requires):
					continue
				if prop.name not in data.data:  # type: ignore  # mypy gets confused by `Anything`
					allMandatory = False

		hasAtLeastOneMandatory = hasAtLeastOneMandatory or not needsAMandatory  # treat hasAtLeastOneMandatory as True if nothing in the schema is mandatory.

	atLeastOneOK = False
	allOK = True
	for name, prop2 in data.data.items():
		if _enrichProperty(name, prop2, schema, data):
			atLeastOneOK = True
		else:
			allOK = False

	return 2 if hasDefiningProp or (allOK and allMandatory) else (1 if atLeastOneOK and hasAtLeastOneMandatory else 0)


def _enrichProperty(name: str, prop: StructureProperty, parentSchema: ObjectSchema, parent: ObjectNode) -> bool:
	keySchema, propSchema, valueSchema = parentSchema.getSchemaForPropAndVal(name, parent)
	if propSchema is not None:
		prop.schema = propSchema
		if keySchema is not None:
			assert isinstance(prop.key.schema, KeySchema)
			prop.key.schema.type = keySchema.type
			prop.key.schema.args = keySchema.args
			prop.key.schema.description = keySchema.description
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
