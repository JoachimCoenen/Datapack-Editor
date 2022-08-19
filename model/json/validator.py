from dataclasses import replace
from typing import Protocol, Type

from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclass
from model.json.core import *
from model.json.core import JsonInvalid, JsonSemanticsError
from model.json.jsonContext import getJsonStringContext
from model.messages import *
from model.utils import Message, Span

EXPECTED_ARGUMENT_SEPARATOR_MSG = Message("Expected whitespace to end one argument, but found trailing data: `{0}`", 1)
NO_JSON_SCHEMA_MSG = Message("No JSON Schema for {0}", 1)
NO_JSON_SCHEMA_VALIDATOR_MSG = Message("No JSON Schema validator for {0}", 1)
MISSING_JSON_STRING_HANDLER_MSG = Message("Missing JsonStringHandler for type `{0}`", 1)
DUPLICATE_PROPERTY_MSG = Message("Duplicate property `{0}`", 1)
UNKNOWN_PROPERTY_MSG = Message("Unknown property `{0}`", 1)
DEPRECATED_PROPERTY_MSG = Message("Deprecated property `{0}`", 1)
REQUIRES_PROPERTY_SET_MSG = Message("Requires property `{0}`. Will be ignored if  `{0}` is not present", 1)
INCOMPATIBLE_PROPERTY_MSG = Message("Is incompatible with properties `{0}`", 1)
MISSING_MANDATORY_PROPERTY_MSG = Message("Missing mandatory property `{0}`", 1)


def wrongTypeError(expected: JsonSchema, got: JsonData):
	msg = EXPECTED_BUT_GOT_MSG.format(expected.asString, got.typeName)
	return JsonSemanticsError(msg, got.span)


def validateJson(data: JsonData) -> list[JsonSemanticsError]:
	errors: list[JsonSemanticsError] = list[JsonSemanticsError]()
	if data.schema is not None:
		_validateInternal(data, errorsIO=errors)
	else:
		msg = NO_JSON_SCHEMA_MSG.format(data.typeName)
		errors.append(JsonSemanticsError(msg, Span(data.span.start)))
	return errors


def _validateInternal(data: JsonData, *, errorsIO: list[JsonSemanticsError]) -> None:
	if data.schema is None:
		msg = NO_JSON_SCHEMA_MSG.format(data.typeName)
		errorsIO.append(JsonSemanticsError(msg, data.span))
		return

	if data.schema.typeName == 'any':
		return

	validator = getSchemaValidator(type(data), None)
	if validator is None:
		msg = NO_JSON_SCHEMA_VALIDATOR_MSG.format(data.typeName)
		errorsIO.append(JsonSemanticsError(msg, data.span, 'info'))
	else:
		if isinstance(data.schema, JsonUnionSchema):
			# we could not decide on a schema previously, so show errors for all:
			for opt in data.schema.allOptions:
				if opt.typeName != 'any':
					validator(data, opt, errorsIO=errorsIO)
		else:
			validator(data, data.schema, errorsIO=errorsIO)


class ValidatorFunc(Protocol):
	def __call__(self, data: JsonData, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
		pass


VALIDATORS_FOR_SCHEMAS: dict[Type[JsonData], ValidatorFunc] = {}
schemaValidator = AddToDictDecorator(VALIDATORS_FOR_SCHEMAS)


def getSchemaValidator(key: Type[JsonData], default):
	return getIfKeyIssubclass(VALIDATORS_FOR_SCHEMAS, key, default)


@schemaValidator(JsonInvalid)
def validateJsonInvalid(data: JsonInvalid, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	errorsIO.append(wrongTypeError(schema, data))
	return


@schemaValidator(JsonNull)
def validateJsonNull(data: JsonNull, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonNullSchema):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(JsonBool)
def validateJsonBool(data: JsonBool, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonBoolSchema):
		errorsIO.append(wrongTypeError(schema, data))
		return


@schemaValidator(JsonNumber)
def validateJsonNumber(data: JsonNumber, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonNumberSchema):
		errorsIO.append(wrongTypeError(schema, data))
		return

	if isinstance(schema, JsonIntSchema) and type(data.data) is float:
		msg = EXPECTED_BUT_GOT_MSG.format('integer', 'float')
		errorsIO.append(JsonSemanticsError(msg, data.span))

	if not schema.min <= data.data <= schema.max:
		msg = NUMBER_OUT_OF_BOUNDS_MSG.format(schema.min, schema.max)
		errorsIO.append(JsonSemanticsError(msg, data.span))


@schemaValidator(JsonString)
def validateJsonString(data: JsonString, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonStringSchema):
		errorsIO.append(wrongTypeError(schema, data))
		return
	# TODO: validation of JsonString using JsonStringSchema.type

	if (argumentHandler := getJsonStringContext(schema.type)) is not None:
		argumentHandler.validate(data, errorsIO)
	elif schema.type is not None:
		errorsIO.append(JsonSemanticsError(INTERNAL_ERROR_MSG.format(MISSING_JSON_STRING_HANDLER_MSG, schema.type), data.span, style='info'))


@schemaValidator(JsonArray)
def validateJsonArray(data: JsonArray, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonArraySchema):
		errorsIO.append(wrongTypeError(schema, data))
		return

	for element in data.data:
		_validateInternal(element, errorsIO=errorsIO)


@schemaValidator(JsonObject)
def validateJsonObject(data: JsonObject, schema: JsonSchema, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(schema, JsonObjectSchema):
		errorsIO.append(wrongTypeError(schema, data))
		return

	validatedProps: set[str] = set()
	key: str
	prop: JsonProperty
	for key, prop in data.data.items():
		if key in validatedProps:
			msg = DUPLICATE_PROPERTY_MSG.format(repr(key))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span))
		else:
			validatedProps.add(key)

		prop_schema = prop.schema
		isUnknownProp = prop_schema is None or prop.value.schema is None
		# isUnknownProp = key not in schema.propertiesDict or schema.propertiesDict[key].valueForParent(data) is None
		if isUnknownProp:
			msg = UNKNOWN_PROPERTY_MSG.format(repr(key))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span))
			continue

		missingRequiredProp = prop_schema.requires != () and any(p not in data.data for p in prop_schema.requires)
		if missingRequiredProp:
			msg = REQUIRES_PROPERTY_SET_MSG.format(repr(prop_schema.requires))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span, style='warning'))

		hasHatedProp = prop_schema.hates != () and any(p in data.data for p in prop_schema.hates)
		if hasHatedProp:
			msg = INCOMPATIBLE_PROPERTY_MSG.format(repr(prop_schema.hates))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span, style='warning'))

		if prop_schema.deprecated:
			msg = DEPRECATED_PROPERTY_MSG.format(repr(prop.key.data))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span, style='warning'))

		_validateInternal(prop.value, errorsIO=errorsIO)

	for propSchema in schema.propertiesDict.values():
		if propSchema.name not in validatedProps:
			missingRequiredProp = propSchema.requires != () and all(p not in data.data for p in propSchema.requires)
			hasIncompatibleProp = propSchema.hates != () and any(p in data.data for p in propSchema.hates)
			isMandatory = propSchema.mandatory and not missingRequiredProp and not hasIncompatibleProp and propSchema.valueForParent(data) is not None
			if isMandatory:
				msg = MISSING_MANDATORY_PROPERTY_MSG.format(repr(propSchema.name))
				end = data.span.end
				start = replace(end, column=end.column - 1, index=end.index - 1)
				errorsIO.append(JsonSemanticsError(msg, Span(start, end)))
