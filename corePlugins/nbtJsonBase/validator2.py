from typing import Protocol

from cat.utils.collections_ import AddToDictDecorator
from .core import *
from base.model.messages import *
from base.model.utils import Message, SemanticsError, Span, GeneralError, Position
from .context import getStringNodeContext

EXPECTED_ARGUMENT_SEPARATOR_MSG = Message("Expected whitespace to end one argument, but found trailing data: `{0}`", 1)
NO_SCHEMA_MSG = Message("No Schema for {0}", 1)
NO_SCHEMA_VALIDATOR_MSG = Message("No Schema validator for {0}", 1)
MISSING_STRING_HANDLER_MSG = Message("Missing StringHandler for type `{0}`", 1)
DUPLICATE_PROPERTY_MSG = Message("Duplicate property `'{0}'`", 1)
UNKNOWN_PROPERTY_MSG = Message("Unknown property `'{0}'`", 1)
DEPRECATED_PROPERTY_MSG = Message("Deprecated property `'{0}'`", 1)
REQUIRES_PROPERTY_TO_BE_SET_MSG = Message("Requires property `'{0}'`. Will be ignored if  `'{0}'` is not present", 1)
INCOMPATIBLE_PROPERTY_MSG = Message("Is incompatible with properties `'{0}'`", 1)
MISSING_MANDATORY_PROPERTY_MSG = Message("Missing mandatory property `'{0}'`", 1)
TOO_MANY_ELEMENTS_MSG = Message("Too many elements. At most {0} are allowed.", 1)
TOO_FEW_ELEMENTS_MSG = Message("Too few elements. At least {0} are required.", 1)


def wrongTypeError(expected: StructureDataSchema, got: StructureDataNode):
	msg = EXPECTED_BUT_GOT_MSG.format(expected.asString, got.typeName)
	return SemanticsError(msg, got.span)


def validateStructure(data: StructureDataNode, errorsIO: list[GeneralError]) -> None:
	if data.schema is not None:
		validator = getSchemaValidator(data.schema.typeName, None)
		validator(data, data.schema, errorsIO=errorsIO)
	else:
		msg = NO_SCHEMA_MSG.format(data.typeName)
		errorsIO.append(SemanticsError(msg, Span(data.span.start)))


class ValidatorFunc(Protocol):
	def __call__(self, data: StructureDataNode, schema: StructureSchema, *, errorsIO: list[GeneralError]) -> None:
		pass


VALIDATORS_FOR_SCHEMAS: dict[str, ValidatorFunc] = {}
schemaValidator = AddToDictDecorator(VALIDATORS_FOR_SCHEMAS)


getSchemaValidator = VALIDATORS_FOR_SCHEMAS.get


# @schemaValidator(PropertySchema.typeName)
# def validateJsonProperty(data: StructureDataNode, schema: PropertySchema, *, errorsIO: list[GeneralError]) -> None:
# 	return


@schemaValidator(AnySchema.typeName)
def validateJsonAny(data: StructureDataNode, schema: AnySchema, *, errorsIO: list[GeneralError]) -> None:
	pass  # no error for invalid, because it's already invalid.


@schemaValidator(NullSchema.typeName)
def validateNullNode(data: StructureDataNode, schema: NullSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, NullNode):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(IllegalSchema.typeName)
def validateInvalidNode(data: StructureDataNode, schema: IllegalSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, InvalidNode):
		errorsIO.append(wrongTypeError(schema, data))  # hmmm
		return


@schemaValidator(BooleanSchema.typeName)
def validateBooleanNode(data: StructureDataNode, schema: BooleanSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, BooleanNode):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(FloatSchema.typeName)
@schemaValidator(IntSchema.typeName)
def validateNumberNode(data: StructureDataNode, schema: NumberSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, NumberNode):
		errorsIO.append(wrongTypeError(schema, data))
		return

	if schema.typeName == IntSchema.typeName and type(data.data) is float and int(data.data) != data.data:
		msg = EXPECTED_BUT_GOT_MSG.format('integer', 'float')
		errorsIO.append(SemanticsError(msg, data.span))

	if not schema.min <= data.data <= schema.max:
		msg = NUMBER_OUT_OF_BOUNDS_MSG.format(schema.min, schema.max)
		errorsIO.append(SemanticsError(msg, data.span))


@schemaValidator(StringSchema.typeName)
def validateStringNode(data: StructureDataNode, schema: StringSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, StringNode):
		errorsIO.append(wrongTypeError(schema, data))
		return
	if (ctx := getStringNodeContext(schema.type)) is not None:
		ctx.validate(data, errorsIO)
	elif schema.type is not None:  # specialized StringHandlers validate string on their own.
		# if we end up here, no specialized string handler hs been found.
		errorsIO.append(SemanticsError(INTERNAL_ERROR_MSG.format(MISSING_STRING_HANDLER_MSG, schema.type), data.span, style='info'))


@schemaValidator(ListLikeSchema.typeName)
def validateListLikeNode(data: StructureDataNode, schema: ListLikeSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, schema.DATA_TYPE):
		errorsIO.append(wrongTypeError(schema, data))
		return
	for element in data.data:
		validateStructure(element, errorsIO)

	if schema.minElemCount is not None and schema.minElemCount > len(data.data):
		msg = TOO_FEW_ELEMENTS_MSG.format(str(schema.minElemCount))
		end = data.span.end
		start = end - 1
		errorsIO.append(SemanticsError(msg, Span(start, end)))

	if schema.maxElemCount is not None and schema.maxElemCount < len(data.data):
		msg = TOO_MANY_ELEMENTS_MSG.format(str(schema.maxElemCount))
		firstViolator = data.data[schema.maxElemCount]
		end = data.span.end
		start = firstViolator.span.start
		errorsIO.append(SemanticsError(msg, Span(start, end)))


@schemaValidator(ObjectSchema.typeName)
def validateObjectNode(data: StructureDataNode, schema: ObjectSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, ObjectNode):
		errorsIO.append(wrongTypeError(schema, data))
		return

	validatedProps: set[str] = set()
	for name, prop in data.data.items():
		if name in validatedProps:
			msg = DUPLICATE_PROPERTY_MSG.format(name)
			errorsIO.append(SemanticsError(msg, prop.key.span))
		else:
			validatedProps.add(name)

		prop_schema, value_schema = schema.getSchemaForPropAndVal(name, data)
		isUnknownProp = prop_schema is None or value_schema is None
		if isUnknownProp:
			msg = UNKNOWN_PROPERTY_MSG.format(name)
			errorsIO.append(SemanticsError(msg, prop.key.span))
			continue

		missingRequiredProp = prop_schema.requires != () and any(p not in data.data for p in prop_schema.requires)
		if missingRequiredProp:
			msg = REQUIRES_PROPERTY_TO_BE_SET_MSG.format(str(prop_schema.requires))
			errorsIO.append(SemanticsError(msg, prop.key.span, style='warning'))

		hasIncompatibleProp = prop_schema.hates != () and any(p in data.data for p in prop_schema.hates)
		if hasIncompatibleProp:
			msg = INCOMPATIBLE_PROPERTY_MSG.format(str(prop_schema.hates))
			errorsIO.append(SemanticsError(msg, prop.key.span, style='warning'))

		if prop_schema.deprecated:
			msg = DEPRECATED_PROPERTY_MSG.format(prop.key.data)
			errorsIO.append(SemanticsError(msg, prop.key.span, style='warning'))

		validateStructure(prop.value, errorsIO)

	for propSchema in schema.propertiesDict.values():
		if propSchema.name not in validatedProps:
			missingRequiredProp = propSchema.requires and all(p not in data.data for p in propSchema.requires)
			hasIncompatibleProp = propSchema.hates and any(p in data.data for p in propSchema.hates)
			isMandatory = propSchema.mandatory and not missingRequiredProp and not hasIncompatibleProp and propSchema.getValueSchemaForParent(data) is not None
			if isMandatory:
				msg = MISSING_MANDATORY_PROPERTY_MSG.format(propSchema.name)
				end = data.span.end
				start = Position(end.line, end.column - 1, end.index - 1)
				errorsIO.append(SemanticsError(msg, Span(start, end)))


def _flattenOptions(schema: UnionSchema, parent: ObjectNode, allOptionsIO: list[StructureDataSchema]) -> None:
	for opt in schema.allOptions:
		actualOpt = resolveCalculatedSchema(opt, parent)
		if actualOpt is None:
			continue
		elif isinstance(actualOpt, UnionSchema):
			_flattenOptions(actualOpt, parent, allOptionsIO)
		else:
			allOptionsIO.append(actualOpt)


@schemaValidator(UnionSchema.typeName)
def validateJsonUnion(data: StructureDataNode, schema: UnionSchema, *, errorsIO: list[GeneralError]) -> None:
	# we could not decide on a schema previously, so show errors for option with the least errors:
	allOptions = []
	_flattenOptions(schema, data.parent, allOptionsIO=allOptions)

	optionsToValidate = []
	for opt in allOptions:
		validator = getSimpleSchemaTypeChecker(opt.typeName)
		isOk = validator(data, opt)
		if isOk:
			optionsToValidate.append(opt)

	if not optionsToValidate:
		errorsIO.append(wrongTypeError(schema, data))
		return

	optionsErrors: list[list[GeneralError]] = []
	for opt in optionsToValidate:
		validator = getSchemaValidator(opt.typeName, None)
		errors = []
		validator(data, opt, errorsIO=errors)
		optionsErrors.append(errors)

	minErrors = []
	minErrorsLen = float('inf')
	for errors in optionsErrors:
		errorsLen = len([e for e in errors if e.style == 'error'])
		if errorsLen < minErrorsLen:
			minErrorsLen = errorsLen
			minErrors = [errors]
		elif errorsLen == minErrorsLen:
			minErrors.append(errors)

	for errors in minErrors:
		errorsIO.extend(errors)


class TypeCheckerFunc(Protocol):
	def __call__(self, data: StructureDataNode, schema: StructureDataSchema) -> bool:
		pass


SIMPLE_TYPE_CHECKERS: dict[str, TypeCheckerFunc] = {}
simpleSchemaTypeChecker = AddToDictDecorator(SIMPLE_TYPE_CHECKERS)
getSimpleSchemaTypeChecker = SIMPLE_TYPE_CHECKERS.get


@simpleSchemaTypeChecker(IllegalSchema.typeName)
def checkJsonAnyType(data: StructureDataNode, schema: IllegalSchema) -> bool:
	return False


@simpleSchemaTypeChecker(AnySchema.typeName)
def checkJsonAnyType(data: StructureDataNode, schema: AnySchema) -> bool:
	return not isinstance(data, InvalidNode)


@simpleSchemaTypeChecker(FloatSchema.typeName)
@simpleSchemaTypeChecker(IntSchema.typeName)
def checkNumberType(data: StructureDataNode, schema: NumberSchema) -> bool:
	if not isinstance(data, NumberNode):
		return False
	if schema.typeName == IntSchema.typeName and type(data.data) is float:
		return False
	return True


@simpleSchemaTypeChecker(NullSchema.typeName)
@simpleSchemaTypeChecker(BooleanSchema.typeName)
@simpleSchemaTypeChecker(StringSchema.typeName)
@simpleSchemaTypeChecker(ListLikeSchema.typeName)
@simpleSchemaTypeChecker(ObjectSchema.typeName)
def checkJsonDefaultType(data: StructureDataNode, schema: BooleanSchema) -> bool:
	return isinstance(data, schema.DATA_TYPE)


@simpleSchemaTypeChecker(UnionSchema.typeName)
def checkJsonUnionType(data: StructureDataNode, schema: UnionSchema) -> bool:
	return any(getSimpleSchemaTypeChecker(opt.typeName, None)(data, opt) for opt in schema.allOptions)
