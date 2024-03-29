from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import inf
from types import EllipsisType
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar, Type, Any, Collection, Iterator, \
	Callable, overload, TypeAlias
from weakref import ref, ReferenceType

from recordclass import as_dataclass

from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from cat.utils import CachedProperty, Anything, Nothing, NoneType
from cat.utils.collections_ import OrderedMultiDict, AddToDictDecorator, FrozenDict
from cat.utils.logging_ import logWarning
from base.model.parsing.parser import IndexMapper
from base.model.parsing.tree import LanguageId2, Node, Schema
from base.model.utils import MDStr, LanguageId, Span, NULL_SPAN


class TokenType(enum.Enum):
	default = 0
	null = 1
	boolean = 2
	number = 3
	string = 4
	left_bracket = 5
	left_brace = 6
	right_bracket = 7
	right_brace = 8
	comma = 9
	colon = 10
	invalid = 11
	eof = 12

	@property
	def asString(self) -> str:
		return _TOKEN_TYPE_STR_REP[self]


_TOKEN_TYPE_STR_REP = {
	TokenType.default: "default",
	TokenType.null: "null",
	TokenType.boolean: "boolean",
	TokenType.number: "number",
	TokenType.string: "string",
	TokenType.left_bracket: "'['",
	TokenType.left_brace: "'{'",
	TokenType.right_bracket: "']'",
	TokenType.right_brace: "'}'",
	TokenType.comma: "','",
	TokenType.colon: "':'",
	TokenType.invalid: "invalid",
	TokenType.eof: "end of file",
}

VALUE_TOKENS = {
	# TokenType.default,
	TokenType.null,
	TokenType.boolean,
	TokenType.number,
	TokenType.string,
	TokenType.left_bracket,
	TokenType.left_brace,
	# TokenType.right_bracket,
	# TokenType.right_brace,
	# TokenType.comma,
	# TokenType.colon,
	TokenType.invalid,
	# TokenType.eof,
}


@as_dataclass()
class Token:
	"""Represents a Token extracted by the parser"""
	value: bytes
	type: TokenType
	span: Span
	# isValid: bool = True


Array = list['JsonData']
Object = OrderedMultiDict[str, 'JsonProperty']
JsonValue = NoneType | bool | int | float | str | Array | Object


PyJsonArray = list['PyJsonValue']
PyJsonObject = dict[str, 'PyJsonValue']
PyJsonSimpleValue = NoneType | bool | int | float | str
PyJsonValue = PyJsonSimpleValue | PyJsonArray | PyJsonObject


_TT = TypeVar('_TT')  # , NoneType, bool, int, float, str, Array, Object)
_TT2 = TypeVar('_TT2')  # , NoneType, bool, int, float, str, Array, Object)
_TJN = TypeVar('_TJN', bound='JsonNode')
_TJD = TypeVar('_TJD', type(None), bool, int, float, str, Array, Object)
_TN = TypeVar('_TN', int, float)


@dataclass
class JsonNode(Node['JsonNode', 'JsonSchema'], ABC):
	typeName: ClassVar[str] = 'JsonNode'
	language: ClassVar[LanguageId] = 'JSON'

	schema: Optional[JsonSchema] = field(hash=False, compare=False)

	@property
	@abstractmethod
	def children(self) -> Collection[JsonNode]:
		return ()

	def walkTree(self) -> Iterator[JsonNode]:
		yield self
		yield from _walkChildren(self.children)

	@abstractmethod
	def asString(self) -> bytes:
		raise NotImplementedError()

	def __str__(self) -> str:
		return bytesToStr(self.asString())


def _walkChildren(children: Collection[JsonNode]) -> Iterator[JsonNode]:
	for child in children:
		yield child
		if child.typeName in {'property', 'object', 'array'}:
			if innerChildren := child.children:
				yield from _walkChildren(innerChildren)


@dataclass
class JsonData(JsonNode, Generic[_TJD], ABC):
	typeName: ClassVar[str] = 'JsonData'
	data: _TJD
	path: str = field(default='', init=False)
	_parent: Optional[ReferenceType[JsonObject | JsonArray]] = field(default=None, init=False)

	@property
	def parent(self) -> Optional[JsonObject | JsonArray]:
		return self._parent and self._parent()


@dataclass
class JsonInvalid(JsonData):
	typeName: ClassVar[str] = 'invalid'
	data: str

	@property
	def children(self) -> Collection[JsonNode]:
		return ()

	def asString(self) -> bytes:
		return b'invalid'


@dataclass
class JsonNull(JsonData[None]):
	typeName: ClassVar[str] = 'null'
	data: None = None

	@property
	def children(self) -> Collection[JsonNode]:
		return ()

	def asString(self) -> bytes:
		return b'null'


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData[bool]):
	data: bool
	typeName: ClassVar[str] = 'boolean'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()

	def asString(self) -> bytes:
		return b'true' if self.data else b'false'


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData[Union[int, float]]):
	data: Union[int, float]
	typeName: ClassVar[str] = 'number'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()

	def asString(self) -> bytes:
		return strToBytes(str(self.data))


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData[str]):
	data: str
	rawData: bytes
	indexMapper: IndexMapper
	parsedValue: Optional[Any] = None
	typeName: ClassVar[str] = 'string'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()

	def asString(self) -> bytes:
		rawData = self.rawData
		rawDataStr = str(rawData)
		if rawDataStr.endswith("'"):
			rawDataStr = rawDataStr[2:-1].replace("\\'", "'").replace('"', '\\"')
			rawDataStr = f'"{rawDataStr}"'
		else:
			rawDataStr = rawDataStr[1:]
		return strToBytes(rawDataStr)


@dataclass
class JsonArray(JsonData[Array]):
	data: Array
	typeName: ClassVar[str] = 'array'

	def __post_init__(self):
		selfRef = ref(self)
		for d in self.data:
			d._parent = selfRef

	@property
	def children(self) -> Collection[JsonData]:
		return self.data

	def asString(self) -> bytes:
		return b'[' + b', '.join(d.asString() for d in self.data) + b']'


@dataclass
class JsonProperty(JsonNode):
	key: JsonString
	value: JsonData
	schema: Optional[PropertySchema] = field(hash=False, compare=False)

	typeName: ClassVar[str] = 'property'

	def __post_init__(self):
		if isinstance(self.key.schema, JsonKeySchema):
			self.key.schema.forProp = self

	@property
	def children(self) -> Collection[JsonData]:
		return self.key, self.value

	def asString(self) -> bytes:
		return self.key.asString() + b': ' + self.value.asString()


@dataclass
class JsonObject(JsonData[Object]):
	data: Object
	typeName: ClassVar[str] = 'object'

	def __post_init__(self):
		selfRef = ref(self)
		for prop in self.data.values():
			prop.key._parent = selfRef
			prop.value._parent = selfRef

	@property
	def children(self) -> Collection[JsonProperty]:
		return self.data.values()

	def getValue(self, key: str, default: _TT = None) -> JsonData | _TT:
		prop = self.data.get(key)
		return prop.value if prop is not None else default

	def asString(self) -> bytes:
		return b'{' + b', '.join(d.asString() for d in self.data.values()) + b'}'


JSON_ID2: LanguageId2[JsonNode] = LanguageId2('JSON', JsonNode)


# ## SCHEMAS: #############################################################################

FieldsMeta: TypeAlias = dict[str, tuple[str | EllipsisType, Any]]


class JsonSchema(Schema, ABC):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	DATA_TYPE: ClassVar[Type[JsonNode]] = JsonData
	typeName: ClassVar[str] = 'JsonNode'
	language: ClassVar[LanguageId] = 'JSON'
	_fields: ClassVar[FieldsMeta] = dict(description=(..., ''), deprecated=(..., False))

	def __init__(self, *, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool] = None):
		self.description: MDStr = description
		self.deprecated: bool = deprecated
		self.span: Span = NULL_SPAN
		self.filePath: str = ''
		self.allowMultilineStr: Optional[bool] = allowMultilineStr

	@property
	def asString(self) -> str:
		return self.typeName

	def setSpan(self, newSpan: Span, filePath: str):
		self.span = newSpan
		self.filePath = filePath
		return self

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		pass


class JsonDataSchema(JsonSchema, ABC):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonData
	typeName: ClassVar[str] = 'JsonData'
	_fields: ClassVar[FieldsMeta] = dict(typeName=('$type', ''))


class JsonNullSchema(JsonDataSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNull
	typeName: ClassVar[str] = 'null'


class JsonBoolSchema(JsonDataSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonBool
	typeName: ClassVar[str] = 'boolean'


class JsonNumberSchema(JsonDataSchema, ABC):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNumber
	typeName: ClassVar[str] = 'number'
	_fields: ClassVar[FieldsMeta] = dict(min=(..., -inf), max=(..., inf))

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool] = None):
		super(JsonNumberSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'integer'


class JsonFloatSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'float'


class JsonStringSchema(JsonDataSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'string'
	_fields: ClassVar[FieldsMeta] = dict(type=(..., None), args=(..., FrozenDict.EMPTY))

	def __init__(
			self,
			*,
			type: Optional[str | JsonArgType] = None,
			args: Optional[dict[str, Union[Any, None]]] = None,
			description: MDStr = '',
			deprecated: bool = False,
			allowMultilineStr: Optional[bool]
	):
		super(JsonStringSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.type: Optional[str] = getattr(type, 'name', type)
		self.args: Optional[dict[str, Union[Any, None]]] = args or {}


class JsonStringOptionsSchema(JsonStringSchema):
	def __init__(
			self,
			*,
			options: dict[str, MDStr],
			description: MDStr = '',
			deprecated: bool = False,
			warningOnly: bool = False,
			allowMultilineStr: Optional[bool]
	):
		super(JsonStringOptionsSchema, self).__init__(
			type=OPTIONS_JSON_ARG_TYPE,
			args=dict(values=options, warningOnly=warningOnly),
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		structure['$type'] = 'enum'
		structure['options'] = structure.pop('args')['values']
		structure['warningOnly'] = structure.pop('args')['warningOnly']
		del structure['type']


class JsonArraySchema(JsonDataSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonArray
	typeName: ClassVar[str] = 'array'
	_fields: ClassVar[FieldsMeta] = dict(element=(..., Nothing))

	def __init__(self, *, description: MDStr = '', element: JsonSchema, deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(JsonArraySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.element: JsonSchema = element


class JsonKeySchema(JsonStringSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'key'

	def __init__(
			self,
			*,
			type: Optional[str] = 'dpe:json/key_schema',
			args: Optional[dict[str, Union[Any, None]]] = None,
			description: MDStr = '',
			deprecated: bool = False,
			allowMultilineStr: Optional[bool] = None
	):
		super(JsonKeySchema, self).__init__(
			type=type,
			args=args,
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)
		self.forProp: Optional[JsonProperty] = None


JSON_KEY_SCHEMA = JsonKeySchema(allowMultilineStr=None)


@as_dataclass(hashable=True, readonly=True)
class DecidingPropRef:
	lookback: int
	name: str

	def __str__(self):
		return f'(lookback={self.lookback!r}, name={self.name!r})'


@as_dataclass(hashable=True, readonly=True)
class DecidingPropNotFound:
	msg: str


def getDecidingPropValue(decidingProp: DecidingPropRef, parent: JsonObject) -> JsonValue | DecidingPropNotFound:
	decidingPropParent = parent
	for _ in range(decidingProp.lookback):
		decidingPropParent = decidingPropParent.parent
		if decidingPropParent is None:
			msg = f"encountered missing parent while resolving decidingProp with lookback={decidingProp.lookback}."
			logWarning(msg)
			return DecidingPropNotFound(msg)
	if not isinstance(decidingPropParent, JsonObject):
		msg = f"resolved parent of decidingProp is not a JsonObject, but rather a {decidingPropParent.typeName} with decidingProp={decidingProp}."
		logWarning(msg)
		return DecidingPropNotFound(msg)

	return getEffectivePropertyValue(decidingProp.name, decidingPropParent)


class PropertySchema(JsonSchema):
	DATA_TYPE: ClassVar[Type[JsonNode]] = JsonProperty
	typeName: ClassVar[str] = 'property'
	_fields: ClassVar[FieldsMeta] = dict(
		name=(..., Nothing),
		optional=(..., Nothing),
		default=(..., None),
		value=(..., None),
		decidingProp=(..., None),
		values=(..., FrozenDict.EMPTY),
		requires=(..., ()),
		hates=(..., ()),
	)

	def __init__(
			self,
			*,
			name: Union[str, Anything],
			description: MDStr = '',
			value: Optional[JsonDataSchema],
			optional: bool = False,
			default: PyJsonValue = None,
			decidingProp: Optional[DecidingPropRef] = None,
			values: dict[PyJsonSimpleValue | tuple[PyJsonSimpleValue, ...], JsonDataSchema] = None,
			requires: Optional[tuple[str, ...]] = None,
			hates: tuple[str, ...] = (),
			deprecated: bool = False,
			allowMultilineStr: Optional[bool]):
		super(PropertySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.name: Union[str, Anything] = name
		self.optional: bool = optional
		self.default: PyJsonValue = default
		self.value: Optional[JsonDataSchema] = value
		self.decidingProp: Optional[DecidingPropRef] = decidingProp
		self.values: dict[PyJsonSimpleValue, JsonDataSchema] = {}
		if requires is None:
			requires = ()
		elif isinstance(requires, str):
			requires = (requires,)
		self.requires: tuple[str, ...] = requires
		self.hates: tuple[str, ...] = hates
		if values is not None:
			for key, val in values.items():
				if isinstance(key, tuple):
					for k in key:
						self.values[k] = val
				else:
					self.values[key] = val

	@property
	def mandatory(self) -> bool:
		return not self.optional

	def getValueSchemaForParent(self, parent: JsonObject) -> Optional[JsonDataSchema]:
		decidingProp = self.decidingProp
		if decidingProp is not None:
			dVal = getDecidingPropValue(decidingProp, parent)
			if isinstance(dVal, DecidingPropNotFound):
				return JsonUnionSchema(description=MDStr(dVal.msg), options=[], allowMultilineStr=None)
			if not callable(getattr(dVal, '__hash__', None)):
				msg = f"value of decidingProp is not a simple value, but rather a {type(dVal).__name__}."
				return JsonUnionSchema(description=MDStr(msg), options=[], allowMultilineStr=None)
			selectedSchema = self.values.get(dVal, self.value)
		else:
			selectedSchema = self.value

		return resolveCalculatedSchema(selectedSchema, parent)

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		# type_ = structure.pop('$type')
		# assert type_ == self.typeName
		pass


class JsonObjectSchema(JsonDataSchema):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonObject
	typeName: ClassVar[str] = 'object'
	_fields: ClassVar[FieldsMeta] = dict(
		inherits=(..., ()),
		properties=(..., Nothing),
	)

	def __init__(self, *, description: MDStr = '', properties: list[PropertySchema], inherits: list[Inheritance] = (), deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(JsonObjectSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.inherits: tuple[Inheritance, ...] = tuple(inherits)
		self.properties: tuple[PropertySchema, ...] = tuple(properties)
		self.propertiesDict: Mapping[str, PropertySchema] = {}
		self.anythingProp: Optional[PropertySchema] = None
		self.isFinished: bool = False
		# self.finish()

	def finish(self) -> JsonObjectSchema:
		if not self.isFinished:
			self.propertiesDict, self.anythingProp = self._buildPropertiesDict()
			self.isFinished = True
		return self

	def _buildPropertiesDict(self) -> tuple[Mapping[str, PropertySchema], Optional[PropertySchema]]:
		propsDict: dict[str, PropertySchema] = dict()
		anythingProp = None

		for inherit in self.inherits:
			if not inherit.schema.isFinished:
				inherit.schema.finish()
			if inherit.decidingProp is None:
				for prop in inherit.schema.propertiesDict.values():
					anythingProp = self._addProp(anythingProp, prop, propsDict)
			else:
				for prop in inherit.schema.propertiesDict.values():
					assert prop.value is not None
					newProp = PropertySchema(
						name=prop.name,
						description=prop.description,
						value=None,
						optional=prop.optional,
						default=prop.default,
						decidingProp=inherit.decidingProp,
						values={dVal: prop.value for dVal in inherit.decidingValues},
						requires=prop.requires,
						hates=prop.hates,
						deprecated=prop.deprecated,
						allowMultilineStr=None,
					)
					newProp.setSpan(prop.span, prop.filePath)
					anythingProp = self._addProp(anythingProp, newProp, propsDict)

		for prop in self.properties:
			anythingProp = self._addProp(anythingProp, prop, propsDict)
		return propsDict, anythingProp

	def _addProp(self, anythingProp: Optional[PropertySchema], prop: PropertySchema, propsDict: dict[str, PropertySchema]) -> Optional[PropertySchema]:
		if prop.name is Anything:
			# quietly overwrite:
			# if anythingProp is not None:
			# 	raise ValueError(f"JsonObjectSchema.properties contains duplicate anything Property")
			anythingProp = prop
		else:
			# quietly overwrite:
			# if prop.name in propsDict:
			# 	raise ValueError(f"JsonObjectSchema.properties contains duplicate names {prop.name!r}")
			if (origProp := propsDict.get(prop.name)) is not None:
				prop = self._joinProps(origProp, prop)

			propsDict[prop.name] = prop
		return anythingProp

	@staticmethod
	def _joinProps(prop1: PropertySchema, prop2: PropertySchema) -> PropertySchema:
		if prop1.decidingProp != prop2.decidingProp:
			logWarning(f"Cannot join properties with differing deciding props [{prop1.decidingProp}, {prop2.decidingProp}]. prop.name = {prop1.name!r}, locations = [({prop1.filePath!r}, {prop1.span}), ({prop2.filePath!r}, {prop2.span})]")
			return prop2
		if prop1.decidingProp is not None:
			values = prop1.values.copy()
			for decVal, val in prop2.values.items():
				if decVal in values:
					val = JsonUnionSchema(description=MDStr(''), options=[values[decVal], val], allowMultilineStr=None)
				values[decVal] = val
			value = None
		else:
			values = None
			value = JsonUnionSchema(description=MDStr(''), options=[prop1.value, prop2.value], allowMultilineStr=None)
		newProp = PropertySchema(
			name=prop1.name,
			description=prop1.description,
			value=value,
			optional=prop1.optional,
			default=prop1.default,
			decidingProp=prop1.decidingProp,
			values=values,
			requires=prop1.requires,
			hates=prop1.hates,
			deprecated=prop1.deprecated,
			allowMultilineStr=None,
		)
		if prop2.filePath:
			newProp.setSpan(prop2.span, prop2.filePath)
		else:
			newProp.setSpan(prop1.span, prop1.filePath)
		return newProp

	def getSchemaForProp(self, name: str) -> Optional[PropertySchema]:
		return self.propertiesDict.get(name, self.anythingProp)

	def getSchemaForPropAndVal(self, name: str, parent: JsonObject) -> tuple[Optional[PropertySchema], Optional[JsonSchema]]:
		propSchema = self.propertiesDict.get(name, self.anythingProp)
		valueSchema = propSchema.getValueSchemaForParent(parent) if propSchema is not None else None
		return propSchema, valueSchema

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		properties = structure['properties']
		properties2 = {}
		for prop in properties:
			propName = prop.pop('name')
			if propName is Anything:
				if 'default-property' in structure:
					raise KeyError(f"'default-property' already defined")
				structure['default-property'] = prop
			else:
				if propName in properties2:
					raise KeyError(f"{propName !r} already in dict")
				properties2[propName] = prop
		structure['properties'] = properties2


@dataclass
class Inheritance:
	schema: JsonObjectSchema
	decidingProp: Optional[DecidingPropRef] = None
	decidingValues: tuple[str, ...] = ()


class JsonUnionSchema(JsonDataSchema):
	typeName: ClassVar[str] = 'union'
	_fields: ClassVar[FieldsMeta] = dict(options=(..., Nothing))

	def __init__(self, *, description: MDStr = '', options: Sequence[JsonDataSchema], allowMultilineStr: Optional[bool]):
		super(JsonUnionSchema, self).__init__(description=description, allowMultilineStr=allowMultilineStr)
		self.options: Sequence[JsonDataSchema] = options

	def _getAllOptions(self) -> list[JsonDataSchema]:
		result = []
		for opt in self.options:
			if isinstance(opt, JsonUnionSchema):
				result.extend(opt.allOptions)
			else:
				result.append(opt)
		return result

	allOptions: list[JsonDataSchema] = CachedProperty(_getAllOptions)

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"({'|'.join(o.asString for o in self.options)})"


class JsonCalculatedValueSchema(JsonDataSchema):
	typeName: ClassVar[str] = 'calculated'
	_fields: ClassVar[FieldsMeta] = dict(func=(..., Nothing))

	def __init__(self, *, description: MDStr = '', func: Callable[[JsonObject], Optional[JsonSchema]], deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(JsonCalculatedValueSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.func: Callable[[JsonObject], Optional[JsonSchema]] = func

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"(...)"

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		func = structure.pop('func')
		function = f'{func.__module__}.{func.__qualname__}'
		structure['function'] = function


def resolveCalculatedSchema(schema: JsonSchema, parent: JsonObject) -> Optional[JsonSchema]:
	if isinstance(schema, JsonCalculatedValueSchema):
		schema = schema.func(parent)
	return schema


class JsonAnySchema(JsonDataSchema):
	typeName: ClassVar[str] = 'any'

	def __init__(self, *, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(JsonAnySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


class JsonIllegalSchema(JsonDataSchema):
	typeName: ClassVar[str] = 'illegal'

	def __init__(self, *, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(JsonIllegalSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


JSON_ANY_SCHEMA: JsonAnySchema = JsonAnySchema(allowMultilineStr=None)
JSON_ILLEGAL_SCHEMA: JsonIllegalSchema = JsonIllegalSchema(allowMultilineStr=None)


def resolvePath(data: JsonData, path: tuple[str | int, ...]) -> Optional[JsonData]:
	result = data
	for item in path:
		if isinstance(item, str):
			if not isinstance(result, JsonObject):
				return None
			prop = result.data.get(item)
			if prop is None:
				return None
			result = prop.value
		else:
			if not isinstance(result, JsonArray):
				return None
			if item >= len(result.data):
				return None
			result = result.data[item]
	return result


def getEffectivePropertyValue(propertyName: str, jObject: JsonObject) -> PyJsonValue:
	dp = jObject.data.get(propertyName)
	if dp is not None:
		dVal = toPyValue(dp.value)
	elif isinstance(jObject.schema, JsonObjectSchema) and (propSchema := jObject.schema.getSchemaForProp(propertyName)) is not None:
		# property was not set. Try to get the default value for property
		dVal = propSchema.default
	else:  # property was not set and there's no default value.
		dVal = None
	return dVal


_toPyValueHandlers: dict[str, Callable[[JsonData, Callable[[JsonData, _TT], _TT]], Any]] = {}

_toPyValueHandler = AddToDictDecorator(_toPyValueHandlers)


@overload
def toPyValue(data: JsonData) -> PyJsonValue: ...
@overload
def toPyValue(data: _TT, resolver: Callable[[JsonData, _TT], _TT]) -> PyJsonValue: ...


def toPyValue(data: _TT, resolver: Callable[[JsonData, _TT], _TT] = ...) -> PyJsonValue:
	if resolver is ...:
		return _toPyValue(data, lambda e, parent: e)
	return _toPyValue(data, resolver)


def _toPyValue(data: _TT, resolver: Callable[[JsonData, _TT], _TT]) -> PyJsonValue:
	return _toPyValueHandlers[data.typeName](data, resolver)


@_toPyValueHandler('invalid')
def _invalidHandler(node: JsonObject, resolver: Callable[[JsonData, _TT], _TT]) -> None:
	return None


@_toPyValueHandler('object')
def _objectHandler(node: JsonObject, resolver: Callable[[JsonData, _TT], _TT]) -> PyJsonObject:
	return {toPyValue(resolver(p.key, node), resolver): toPyValue(resolver(p.value, node), resolver) for p in node.data.values()}


@_toPyValueHandler('array')
def _arrayHandler(node: JsonArray, resolver: Callable[[JsonData, _TT], _TT]) -> PyJsonArray:
	return [toPyValue(resolver(e, node), resolver) for e in node.data]


@_toPyValueHandler('string')
@_toPyValueHandler('boolean')
@_toPyValueHandler('number')
@_toPyValueHandler('null')
def _stringHandler(node: JsonData, resolver: Callable[[JsonData, _TT], _TT]) -> PyJsonValue:
	return node.data


@dataclass
class JsonArgType:
	def __post_init__(self):
		if type(self) is JsonArgType:
			registerNamedJsonArgType(self)

	name: str
	description: MDStr = ''
	description2: MDStr = ''
	example: MDStr = ''
	examples: MDStr = ''
	jsonProperties: str = ''


ALL_NAMED_JSON_ARG_TYPES: dict[str, JsonArgType] = {}
_registerNamedJsonArgType: AddToDictDecorator[str, JsonArgType] = AddToDictDecorator(ALL_NAMED_JSON_ARG_TYPES)


def registerNamedJsonArgType(jsonArgType: JsonArgType, forceOverride: bool = False) -> None:
	_registerNamedJsonArgType(jsonArgType.name, forceOverride=forceOverride)(jsonArgType)


OPTIONS_JSON_ARG_TYPE = JsonArgType(
	name='options',
	description=MDStr(""),
	description2=MDStr(""),
	examples=MDStr(""),
)


__all__ = [

	'TokenType',
	'VALUE_TOKENS',
	'Token',

	'Array',
	'Object',
	'JsonValue',
	'PyJsonArray',
	'PyJsonObject',
	'PyJsonValue',

	'JsonNode',
	'JsonData',
	'JsonInvalid',
	'JsonNull',
	'JsonBool',
	'JsonNumber',
	'JsonString',
	'JsonArray',
	'JsonObject',
	'JsonProperty',
	'JSON_ID2',

	'JsonSchema',
	'JsonNullSchema',
	'JsonBoolSchema',
	'JsonNumberSchema',
	'JsonIntSchema',
	'JsonFloatSchema',
	'JsonStringSchema',
	'JsonStringOptionsSchema',
	'JsonArraySchema',
	'JsonKeySchema',
	'JSON_KEY_SCHEMA',
	'DecidingPropRef',
	'PropertySchema',
	'JsonObjectSchema',
	'Inheritance',
	'JsonUnionSchema',
	'JsonCalculatedValueSchema',
	'resolveCalculatedSchema',
	'JsonAnySchema',
	'JsonIllegalSchema',
	'JSON_ANY_SCHEMA',
	'JSON_ILLEGAL_SCHEMA',

	'resolvePath',
	'getEffectivePropertyValue',
	'toPyValue',

	'JsonArgType',
	'ALL_NAMED_JSON_ARG_TYPES',
	'OPTIONS_JSON_ARG_TYPE',
]
