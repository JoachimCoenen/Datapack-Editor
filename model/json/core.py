from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar, Type, Any, Collection, Iterator, Callable, NamedTuple

from Cat.utils import CachedProperty, Anything, Nothing
from Cat.utils.collections_ import OrderedMultiDict, OrderedDict, AddToDictDecorator
from model.parsing.parser import IndexMapper
from model.parsing.tree import Node, Schema
from model.utils import GeneralError, MDStr, LanguageId, Span


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


class Token(NamedTuple):
	"""Represents a Token extracted by the parser"""
	value: bytes
	type: TokenType
	span: Span
	# isValid: bool = True


Array = list['JsonData']
Object = OrderedMultiDict[str, 'JsonProperty']

JsonTypes = Union[None, bool, int, float, str, Array, Object]

_TT = TypeVar('_TT')  # , NoneType, bool, int, float, str, Array, Object)
_TT2 = TypeVar('_TT2')  # , NoneType, bool, int, float, str, Array, Object)
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


@dataclass
class JsonInvalid(JsonData):
	typeName: ClassVar[str] = 'invalid'
	data: str

	@property
	def children(self) -> Collection[JsonNode]:
		return ()


@dataclass
class JsonNull(JsonData[None]):
	typeName: ClassVar[str] = 'null'
	data: None = None

	@property
	def children(self) -> Collection[JsonNode]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData[bool]):
	data: bool
	typeName: ClassVar[str] = 'boolean'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData[Union[int, float]]):
	data: Union[int, float]
	typeName: ClassVar[str] = 'number'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData[str]):
	data: str
	indexMapper: IndexMapper
	parsedValue: Optional[Any] = None
	typeName: ClassVar[str] = 'string'

	@property
	def children(self) -> Collection[JsonNode]:
		return ()


@dataclass
class JsonArray(JsonData[Array]):
	data: Array
	typeName: ClassVar[str] = 'array'

	@property
	def children(self) -> Collection[JsonData]:
		return self.data


@dataclass
class JsonProperty(JsonNode):
	key: JsonString
	value: JsonData
	schema: Optional[SwitchingPropertySchema] = field(hash=False, compare=False)

	typeName: ClassVar[str] = 'property'

	def __post_init__(self):
		if isinstance(self.key.schema, JsonKeySchema):
			self.key.schema.forProp = self

	@property
	def children(self) -> Collection[JsonData]:
		return self.key, self.value


@dataclass
class JsonObject(JsonData[Object]):
	data: Object
	typeName: ClassVar[str] = 'object'

	@property
	def children(self) -> Collection[JsonProperty]:
		return self.data.values()


# ## SCHEMAS: #############################################################################


class JsonSchema(Schema, Generic[_TT], ABC):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	DATA_TYPE: ClassVar[Type[_TT]] = JsonData
	typeName: ClassVar[str] = 'JsonData'
	language: ClassVar[LanguageId] = 'JSON'
	_fields: ClassVar[dict[str, Any]] = dict(description='', deprecated=False)

	def __init__(self, *, description: MDStr = '', deprecated: bool = False):
		self.description: MDStr = description
		self.deprecated: bool = deprecated
		self.span: Span = Span()
		self.filePath: str = ''

	@property
	def asString(self) -> str:
		return self.typeName

	def setSpan(self, newSpan: Span, filePath: str):
		self.span = newSpan
		self.filePath = filePath
		return self

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		pass


class JsonNullSchema(JsonSchema[JsonNull]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNull
	typeName: ClassVar[str] = 'null'


class JsonBoolSchema(JsonSchema[JsonBool]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonBool
	typeName: ClassVar[str] = 'boolean'


class JsonNumberSchema(JsonSchema[JsonNumber], ABC):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNumber
	typeName: ClassVar[str] = 'number'
	_fields: ClassVar[dict[str, Any]] = dict(min=-inf, max=inf)

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: MDStr = '', deprecated: bool = False):
		super(JsonNumberSchema, self).__init__(description=description, deprecated=deprecated)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'integer'


class JsonFloatSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'float'


class JsonStringSchema(JsonSchema[JsonString]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'string'
	_fields: ClassVar[dict[str, Any]] = dict(type=None, args={})

	def __init__(
			self,
			*,
			type: Optional[str | JsonArgType] = None,
			args: Optional[dict[str, Union[Any, None]]] = None,
			description: MDStr = '',
			deprecated: bool = False
	):
		super(JsonStringSchema, self).__init__(description=description, deprecated=deprecated)
		self.type: Optional[str] = getattr(type, 'name', type)
		self.args: Optional[dict[str, Union[Any, None]]] = args or {}


class JsonStringOptionsSchema(JsonStringSchema):
	def __init__(
			self,
			*,
			options: dict[str, MDStr],
			description: MDStr = '',
			deprecated: bool = False
	):
		super(JsonStringOptionsSchema, self).__init__(
			type=OPTIONS_JSON_ARG_TYPE,
			args=dict(values=options),
			description=description,
			deprecated=deprecated
		)

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		structure['$type'] = 'enum'
		structure['options'] = structure.pop('args')['values']
		del structure['type']


class JsonArraySchema(JsonSchema[JsonArray]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonArray
	typeName: ClassVar[str] = 'array'
	_fields: ClassVar[dict[str, Any]] = dict(element=Nothing)

	def __init__(self, *, description: MDStr = '', element: JsonSchema, deprecated: bool = False):
		super(JsonArraySchema, self).__init__(description=description, deprecated=deprecated)
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
			deprecated: bool = False
	):
		super(JsonKeySchema, self).__init__(
			type=type,
			args=args,
			description=description,
			deprecated=deprecated,
		)
		self.forProp: Optional[JsonProperty] = None


JSON_KEY_SCHEMA = JsonKeySchema()


# @dataclass
# class PropertyOptions:
# 	pass
#
#
# @dataclass
# class SinglePropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# @dataclass
# class AllPropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# @dataclass
# class AnyPropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# @dataclass
# class OneOfPropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# @dataclass
# class OneOfPropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# @dataclass
# class OneOfPropertyOption(PropertyOptions):
# 	pass  # TODO
#
#
# class PropertySchema(JsonSchema[JsonProperty]):
# 	typeName: ClassVar[str] = 'property'
# 	_fields: ClassVar[dict[str, Any]] = dict(
# 		name=Nothing,
# 		optional=Nothing,
# 		default=None,
# 		value=None,
# 	)
#
# 	def __init__(
# 			self,
# 			*,
# 			name: Union[str, Anything],
# 			description: MDStr = '',
# 			value: Optional[JsonSchema[_TT2]],
# 			optional: bool = False,
# 			default: JsonTypes = None,
# 			deprecated: bool = False):
# 		super(SwitchingPropertySchema, self).__init__(description=description, deprecated=deprecated)
# 		self.name: Union[str, Anything] = name
# 		self.optional: bool = optional
# 		self.default: Optional[_TT2] = default
# 		self.value: Optional[JsonSchema[_TT2]] = value
#
# 	@property
# 	def mandatory(self) -> bool:
# 		return not self.optional
#
# 	def valueForParent(self, parent: JsonObject) -> Optional[JsonSchema[_TT2]]:
# 		# TODO find better name for .valueForParent(...)
# 		# if self.value is not None:
# 		# 	return self.value
# 		selectedSchema = self.value
# 		if isinstance(selectedSchema, JsonCalculatedValueSchema):
# 			selectedSchema = selectedSchema.func(parent)
# 		return selectedSchema
#
# 	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
# 		type_ = structure.pop('$type')
# 		assert type_ == self.typeName


# class PropertySchema(Generic[_TT]):
# 	def __init__(self, *, name: str, description: MDStr = '', default: Optional[_TT] = None, value: JsonSchema[_TT]):
# 		self.name: str = name
# 		self.description: MDStr = description
# 		self.default: Optional[_TT] = default
# 		self.value: JsonSchema[_TT] = value
#
# 	@property
# 	def mandatory(self) -> bool:
# 		return self.default is None


class SwitchingPropertySchema(JsonSchema[JsonProperty]):
	DATA_TYPE: ClassVar[Type[JsonNode]] = JsonProperty
	typeName: ClassVar[str] = 'property'
	_fields: ClassVar[dict[str, Any]] = dict(
		name=Nothing,
		optional=Nothing,
		default=None,
		value=None,
		decidingProp=None,
		values={},
		requires=()
	)

	def __init__(
			self,
			*,
			name: Union[str, Anything],
			description: MDStr = '',
			value: Optional[JsonSchema[_TT2]],
			optional: bool = False,
			default: JsonTypes = None,
			decidingProp: Optional[str] = None,
			values: dict[Union[tuple[Union[str, int, bool], ...], Union[str, int, bool]], JsonSchema[_TT2]] = None,
			requires: Optional[tuple[str, ...]] = None,
			hates:tuple[str, ...] = (),
			deprecated: bool = False):
		super(SwitchingPropertySchema, self).__init__(description=description, deprecated=deprecated)
		self.name: Union[str, Anything] = name
		self.optional: bool = optional
		self.default: Optional[_TT2] = default
		self.value: Optional[JsonSchema[_TT2]] = value
		self.decidingProp: Optional[str] = decidingProp
		self.values: dict[Union[str, int, bool], JsonSchema[_TT2]] = {}
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

	def valueForParent(self, parent: JsonObject) -> Optional[JsonSchema[_TT2]]:
		# TODO find better name for .valueForParent(...)
		# if self.value is not None:
		# 	return self.value
		decidingProp = self.decidingProp
		if decidingProp is not None:
			dp = parent.data.get(decidingProp)
			if dp is not None:
				dVal = getattr(dp.value, 'data')
			else:
				dVal = None
			if not callable(getattr(dVal, '__hash__', None)):
				dVal = None
			selectedSchema = self.values.get(dVal, self.value)
		else:
			selectedSchema = self.value

		if isinstance(selectedSchema, JsonCalculatedValueSchema):
			selectedSchema = selectedSchema.func(parent)
		return selectedSchema

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		type_ = structure.pop('$type')
		assert type_ == self.typeName


PropertySchema = SwitchingPropertySchema


class JsonObjectSchema(JsonSchema[Object]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonObject
	typeName: ClassVar[str] = 'object'
	_fields: ClassVar[dict[str, Any]] = dict(properties=Nothing)

	def __init__(self, *, description: MDStr = '', properties: list[SwitchingPropertySchema], mandatoryProperties: list[str | tuple[str, ...]] = (), deprecated: bool = False):
		super(JsonObjectSchema, self).__init__(description=description, deprecated=deprecated)
		self.properties: tuple[SwitchingPropertySchema, ...] = tuple(properties)
		# self.mandatoryProperties: list[tuple[str, ...]] = [s if isinstance(s, tuple) else (s,) for s in mandatoryProperties]
		self.propertiesDict: Mapping[str, SwitchingPropertySchema] = {}
		self.anythingProp: Optional[SwitchingPropertySchema] = None
		self.buildPropertiesDict()

	def buildPropertiesDict(self) -> None:
		self.propertiesDict, self.anythingProp = self._buildPropertiesDict()

	def _buildPropertiesDict(self) -> tuple[Mapping[str, SwitchingPropertySchema], Optional[SwitchingPropertySchema]]:
		propsDict: dict[str, SwitchingPropertySchema] = dict[str, SwitchingPropertySchema]()
		anythingProp = None
		for prop in self.properties:
			if prop.name is Anything:
				if anythingProp is not None:
					raise ValueError(f"JsonObjectSchema.properties contains duplicate anything Property")
				anythingProp = prop
			else:
				if prop.name in propsDict:
					raise ValueError(f"JsonObjectSchema.properties contains duplicate names {prop.name!r}")
				propsDict[prop.name] = prop
		return propsDict, anythingProp

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		properties = structure['properties']
		properties2 = {}
		for prop in properties:
			# if prop is None:
			# 	continue
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


class JsonUnionSchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'union'
	_fields: ClassVar[dict[str, Any]] = dict(options=Nothing)

	def __init__(self, *, description: MDStr = '', options: Sequence[JsonSchema]):
		super(JsonUnionSchema, self).__init__(description=description)
		self.options: Sequence[JsonSchema] = options

	def optionsDict2(self) -> dict[Type[JsonData], JsonSchema]:
		result = {}
		for opt in self.options:
			if isinstance(opt, JsonUnionSchema):
				result.update(opt.optionsDict2)
			else:
				result[opt.DATA_TYPE] = opt
		return result

	optionsDict2: dict[Type[JsonData], JsonSchema] = CachedProperty(optionsDict2)

	def allOptions(self) -> list[JsonSchema]:
		result = []
		for opt in self.options:
			if isinstance(opt, JsonUnionSchema):
				result.extend(opt.allOptions)
			else:
				result.append(opt)
		return result

	allOptions: list[JsonSchema] = CachedProperty(allOptions)

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"({'|'.join(o.asString for o in self.options)})"


class JsonCalculatedValueSchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'calculated'
	_fields: ClassVar[dict[str, Any]] = dict(func=Nothing)

	def __init__(self, *, description: MDStr = '', func: Callable[[JsonObject], Optional[JsonSchema]], deprecated: bool = False):
		super(JsonCalculatedValueSchema, self).__init__(description=description, deprecated=deprecated)
		self.func: Callable[[JsonObject], Optional[JsonSchema]] = func

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"(...)"

	def postProcessJsonStructure(self, structure: dict[str, Any]) -> None:
		func = structure.pop('func')
		function = f'{func.__module__}.{func.__qualname__}'
		structure['function'] = function


class JsonAnySchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'any'
	_fields: ClassVar[dict[str, Any]] = dict()

	def __init__(self, *, description: MDStr = '', deprecated: bool = False):
		super(JsonAnySchema, self).__init__(description=description, deprecated=deprecated)


JSON_ANY_SCHEMA = JsonAnySchema()


def resolvePath(data: JsonData, path: tuple[str|int, ...]) -> Optional[JsonData]:
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


class JsonTokenizeError(GeneralError):
	pass


class JsonParseError(GeneralError):
	pass


class JsonSemanticsError(GeneralError):
	pass


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


ALL_NAMED_JSON_ARG_TYPES: OrderedDict[str, JsonArgType] = OrderedDict()
_registerNamedJsonArgType: AddToDictDecorator[str, JsonArgType] = AddToDictDecorator(ALL_NAMED_JSON_ARG_TYPES)


def registerNamedJsonArgType(jsonArgType: JsonArgType, forceOverride: bool = False) -> None:
	_registerNamedJsonArgType(jsonArgType.name, forceOverride)(jsonArgType)


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
	'JsonTypes',

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
	'PropertySchema',
	'SwitchingPropertySchema',
	'JsonObjectSchema',
	'JsonUnionSchema',
	'JsonCalculatedValueSchema',
	'JsonAnySchema',
	'JSON_ANY_SCHEMA',

	'resolvePath',

	'JsonTokenizeError',
	'JsonParseError',
	'JsonSemanticsError',

	'JsonArgType',
]