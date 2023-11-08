from typing import Protocol

from cat.utils.collections_ import AddToDictDecorator
from .core import *
from base.model.messages import *
from base.model.utils import Message, SemanticsError, Span, GeneralError, Position

EXPECTED_ARGUMENT_SEPARATOR_MSG = Message("Expected whitespace to end one argument, but found trailing data: `{0}`", 1)
NO_JSON_SCHEMA_MSG = Message("No JSON Schema for {0}", 1)
NO_JSON_SCHEMA_VALIDATOR_MSG = Message("No JSON Schema validator for {0}", 1)
MISSING_JSON_STRING_HANDLER_MSG = Message("Missing JsonStringHandler for type `{0}`", 1)
DUPLICATE_PROPERTY_MSG = Message("Duplicate property `'{0}'`", 1)
UNKNOWN_PROPERTY_MSG = Message("Unknown property `'{0}'`", 1)
DEPRECATED_PROPERTY_MSG = Message("Deprecated property `'{0}'`", 1)
REQUIRES_PROPERTY_TO_BE_SET_MSG = Message("Requires property `'{0}'`. Will be ignored if  `'{0}'` is not present", 1)
INCOMPATIBLE_PROPERTY_MSG = Message("Is incompatible with properties `'{0}'`", 1)
MISSING_MANDATORY_PROPERTY_MSG = Message("Missing mandatory property `'{0}'`", 1)


def wrongTypeError(expected: JsonSchema, got: JsonData):
	msg = EXPECTED_BUT_GOT_MSG.format(expected.asString, got.typeName)
	return SemanticsError(msg, got.span)


def validateJson(data: JsonData, errorsIO: list[GeneralError]) -> None:
	if data.schema is not None:
		validator = getSchemaValidator(data.schema.typeName, None)
		validator(data, data.schema, errorsIO=errorsIO)
	else:
		# error has already been logged, because no schema means this node (or one of its parents) was unexpected.
		# msg = NO_JSON_SCHEMA_MSG.format(data.typeName)
		# errorsIO.append(JsonSemanticsError(msg, Span(data.span.start)))
		pass


class ValidatorFunc(Protocol):
	def __call__(self, data: JsonData, schema: JsonSchema, *, errorsIO: list[GeneralError]) -> None:
		pass


VALIDATORS_FOR_SCHEMAS: dict[str, ValidatorFunc] = {}
schemaValidator = AddToDictDecorator(VALIDATORS_FOR_SCHEMAS)


getSchemaValidator = VALIDATORS_FOR_SCHEMAS.get


@schemaValidator(PropertySchema.typeName)
def validateJsonProperty(data: JsonData, schema: PropertySchema, *, errorsIO: list[GeneralError]) -> None:
	return


@schemaValidator(JsonAnySchema.typeName)
def validateJsonAny(data: JsonData, schema: JsonAnySchema, *, errorsIO: list[GeneralError]) -> None:
	pass  # no error for invalid, because it's already invalid.


@schemaValidator(JsonNullSchema.typeName)
def validateJsonNull(data: JsonData, schema: JsonNullSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonNull):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(JsonBoolSchema.typeName)
def validateJsonBool(data: JsonData, schema: JsonBoolSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonBool):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(JsonFloatSchema.typeName)
@schemaValidator(JsonIntSchema.typeName)
def validateJsonNumber(data: JsonData, schema: JsonNumberSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonNumber):
		errorsIO.append(wrongTypeError(schema, data))
		return

	if schema.typeName == JsonIntSchema.typeName and type(data.data) is float and int(data.data) != data.data:
		msg = EXPECTED_BUT_GOT_MSG.format('integer', 'float')
		errorsIO.append(SemanticsError(msg, data.span))

	if not schema.min <= data.data <= schema.max:
		msg = NUMBER_OUT_OF_BOUNDS_MSG.format(schema.min, schema.max)
		errorsIO.append(SemanticsError(msg, data.span))


@schemaValidator(JsonStringSchema.typeName)
def validateJsonString(data: JsonData, schema: JsonStringSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonString):
		errorsIO.append(wrongTypeError(schema, data))
		return
	if schema.type is not None:  # specialized StringHandlers validate string on their own.
		# if we end up here, no specialized string handler hs been found.
		errorsIO.append(SemanticsError(INTERNAL_ERROR_MSG.format(MISSING_JSON_STRING_HANDLER_MSG, schema.type), data.span, style='info'))


@schemaValidator(JsonArraySchema.typeName)
def validateJsonArray(data: JsonData, schema: JsonArraySchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonArray):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(JsonObjectSchema.typeName)
def validateJsonObject(data: JsonData, schema: JsonObjectSchema, *, errorsIO: list[GeneralError]) -> None:
	if not isinstance(data, JsonObject):
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


@schemaValidator(JsonUnionSchema.typeName)
def validateJsonUnion(data: JsonData, schema: JsonUnionSchema, *, errorsIO: list[GeneralError]) -> None:
	# we could not decide on a schema previously, so show errors for option with the least errors:

	optionsToValidate = []
	for opt in schema.allOptions:
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
	def __call__(self, data: JsonData, schema: JsonSchema) -> bool:
		pass


SIMPLE_TYPE_CHECKERS: dict[str, TypeCheckerFunc] = {}
simpleSchemaTypeChecker = AddToDictDecorator(SIMPLE_TYPE_CHECKERS)
getSimpleSchemaTypeChecker = SIMPLE_TYPE_CHECKERS.get


@simpleSchemaTypeChecker(JsonAnySchema.typeName)
def checkJsonAnyType(data: JsonData, schema: JsonAnySchema) -> bool:
	return not isinstance(data, JsonInvalid)


@simpleSchemaTypeChecker(JsonFloatSchema.typeName)
@simpleSchemaTypeChecker(JsonIntSchema.typeName)
def checkJsonNumberType(data: JsonData, schema: JsonNumberSchema) -> bool:
	if not isinstance(data, JsonNumber):
		return False
	if schema.typeName == JsonIntSchema.typeName and type(data.data) is float:
		return False
	return True


@simpleSchemaTypeChecker(JsonNullSchema.typeName)
@simpleSchemaTypeChecker(JsonBoolSchema.typeName)
@simpleSchemaTypeChecker(JsonStringSchema.typeName)
@simpleSchemaTypeChecker(JsonArraySchema.typeName)
@simpleSchemaTypeChecker(JsonObjectSchema.typeName)
def checkJsonDefaultType(data: JsonData, schema: JsonBoolSchema) -> bool:
	return isinstance(data, schema.DATA_TYPE)


@simpleSchemaTypeChecker(JsonUnionSchema.typeName)
def checkJsonUnionType(data: JsonData, schema: JsonUnionSchema) -> bool:
	return any(getSimpleSchemaTypeChecker(opt.typeName, None)(data, opt) for opt in schema.allOptions)
