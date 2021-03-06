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

	validator = getSchemaValidator(type(data), None)
	if validator is None:
		msg = NO_JSON_SCHEMA_VALIDATOR_MSG.format(data.typeName)
		errorsIO.append(JsonSemanticsError(msg, data.span, 'info'))
	else:
		validator(data, errorsIO=errorsIO)


class ValidatorFunc(Protocol):
	def __call__(self, data: JsonData, *, errorsIO: list[JsonSemanticsError]) -> None:
		pass


VALIDATORS_FOR_SCHEMAS: dict[Type[JsonData], ValidatorFunc] = {}
schemaValidator = AddToDictDecorator(VALIDATORS_FOR_SCHEMAS)


def getSchemaValidator(key: Type[JsonData], default):
	return getIfKeyIssubclass(VALIDATORS_FOR_SCHEMAS, key, default)


@schemaValidator(JsonInvalid)
def validateJsonInvalid(data: JsonInvalid, *, errorsIO: list[JsonSemanticsError]) -> None:
	errorsIO.append(wrongTypeError(data.schema, data))
	return


@schemaValidator(JsonNull)
def validateJsonNull(data: JsonNull, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonNullSchema):
		errorsIO.append(wrongTypeError(data.schema, data))
		return


@schemaValidator(JsonBool)
def validateJsonBool(data: JsonBool, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonBoolSchema):
		errorsIO.append(wrongTypeError(data.schema, data))
		return


@schemaValidator(JsonNumber)
def validateJsonNumber(data: JsonNumber, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonNumberSchema):
		errorsIO.append(wrongTypeError(data.schema, data))
		return

	if isinstance(data.schema, JsonIntSchema) and type(data.data) is float:
		msg = EXPECTED_BUT_GOT_MSG.format('integer', 'float')
		errorsIO.append(JsonSemanticsError(msg, data.span))

	if not data.schema.min <= data.data <= data.schema.max:
		msg = NUMBER_OUT_OF_BOUNDS_MSG.format(data.schema.min, data.schema.max)
		errorsIO.append(JsonSemanticsError(msg, data.span))


@schemaValidator(JsonString)
def validateJsonString(data: JsonString, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonStringSchema):
		errorsIO.append(wrongTypeError(data.schema, data))
		return
	# TODO: validation of JsonString using JsonStringSchema.type

	if data.schema.type is not None:
		argumentHandler = getJsonStringContext(data.schema.type.name)
		if argumentHandler is not None:
			argumentHandler.validate(data, errorsIO)
		else:
			errorsIO.append(JsonSemanticsError(INTERNAL_ERROR_MSG.format(MISSING_JSON_STRING_HANDLER_MSG, data.schema.type.name), data.span, style='info'))


@schemaValidator(JsonArray)
def validateJsonArray(data: JsonArray, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonArraySchema):
		errorsIO.append(wrongTypeError(data.schema, data))
		return

	for element in data.data:
		_validateInternal(element, errorsIO=errorsIO)


@schemaValidator(JsonObject)
def validateJsonObject(data: JsonObject, *, errorsIO: list[JsonSemanticsError]) -> None:
	if not isinstance(data.schema, JsonObjectSchema):
		errorsIO.append(wrongTypeError(data.schema, data))
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

		isUnknownProp = prop.schema is None or prop.value.schema is None
		# isUnknownProp = key not in data.schema.propertiesDict or data.schema.propertiesDict[key].valueForParent(data) is None
		if isUnknownProp:
			msg = UNKNOWN_PROPERTY_MSG.format(repr(key))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span))
			continue

		missingRequiredProp = prop.schema.requiresProp != () and all(p not in data.data for p in prop.schema.requiresProp)
		if missingRequiredProp:
			msg = REQUIRES_PROPERTY_SET_MSG.format(repr(prop.schema.requiresProp))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span, style='warning'))

		if prop.schema.deprecated:
			msg = DEPRECATED_PROPERTY_MSG.format(repr(prop.key.data))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span, style='warning'))

		_validateInternal(prop.value, errorsIO=errorsIO)

	for propSchema in data.schema.propertiesDict.values():
		if propSchema.name not in validatedProps:
			missingRequiredProp = propSchema.requiresProp != () and all(p not in data.data for p in propSchema.requiresProp)
			isMandatory = propSchema.isMandatory and not missingRequiredProp and propSchema.valueForParent(data) is not None
			if isMandatory:
				msg = MISSING_MANDATORY_PROPERTY_MSG.format(repr(propSchema.name))
				end = data.span.end
				start = replace(end, column=end.column - 1, index=end.index - 1)
				errorsIO.append(JsonSemanticsError(msg, Span(start, end)))
