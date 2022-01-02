from typing import Protocol, Type

from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclass
from model.json.core import *
from model.utils import GeneralParsingError, Message, Span

EXPECTED_ARGUMENT_SEPARATOR_MSG = Message("Expected whitespace to end one argument, but found trailing data: `{0}`", 1)
NO_JSON_SCHEMA_MSG = Message("No JSON Schema for {0}", 1)
NO_JSON_SCHEMA_VALIDATOR_MSG = Message("No JSON Schema validator for {0}", 1)
EXPECTED_BUT_GOT_MSG = Message("Expected `{0}`, but got `{1}`", 2)
NUMBER_OUT_OF_BOUNDS_MSG = Message("Number out of bounds (min = {0}, max = {1})", 2)
DUPLICATE_PROPERTY_MSG = Message("Duplicate property `{0}`", 1)
UNKNOWN_PROPERTY_MSG = Message("Unknown property `{0}`", 1)
MISSING_MANDATORY_PROPERTY_MSG = Message("Missing mandatory property `{0}`", 1)


class JsonSemanticsError(GeneralParsingError):
	pass


def wrongTypeError(expected: JsonSchema, got: JsonData):
	msg = EXPECTED_BUT_GOT_MSG.format(expected.typeName, got.typeName)
	return JsonSemanticsError(msg, got.span)


def validateJson(data: JsonData) -> list[JsonSemanticsError]:
	errors: list[JsonSemanticsError] = list[JsonSemanticsError]()
	_validateInternal(data, errorsIO=errors)
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
	# start = data.span.start
	# sr = StringReader(data.data, start.index, start.line, data.data)
	#
	# if data.schema.type is not None:
	# 	argumentHandler = getArgumentHandler(data.schema.type)
	# 	if argumentHandler is None:
	# 		pa = missingArgumentHandler(sr, data.schema.type, errorsIO=)


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

		if key not in data.schema.propertiesDict:
			msg = UNKNOWN_PROPERTY_MSG.format(repr(key))
			errorsIO.append(JsonSemanticsError(msg, prop.key.span))
			continue

		_validateInternal(prop.value, errorsIO=errorsIO)

	for propSchema in data.schema.properties:
		if propSchema.name not in validatedProps and propSchema.mandatory:
			msg = MISSING_MANDATORY_PROPERTY_MSG.format(repr(propSchema.name))
			errorsIO.append(JsonSemanticsError(msg, Span(data.span.end)))



