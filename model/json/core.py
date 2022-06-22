from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar, Type, Any, Collection, Iterator, Callable, NamedTuple

from Cat.utils import CachedProperty, Anything
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
_TN = TypeVar('_TN', int, float)


@dataclass
class JsonData(Node['JsonData', 'JsonSchema'], ABC):
	schema: Optional[JsonSchema]

	typeName: ClassVar[str] = 'JsonData'

	language: ClassVar[LanguageId] = 'JSON'

	@property
	@abstractmethod
	def children(self) -> Collection[JsonData]:
		return ()

	def walkTree(self) -> Iterator[JsonData]:
		yield self
		yield from _walkChildren(self.children)


def _walkChildren(children: Collection[JsonData]) -> Iterator[JsonData]:
	for child in children:
		yield child
		innerChildren = child.children
		if innerChildren:
			yield from _walkChildren(innerChildren)


@dataclass
class JsonInvalid(JsonData):
	typeName: ClassVar[str] = 'invalid'
	data: str

	@property
	def children(self) -> Collection[JsonData]:
		return ()


@dataclass
class JsonNull(JsonData):
	typeName: ClassVar[str] = 'null'

	@property
	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData):
	data: bool
	typeName: ClassVar[str] = 'boolean'

	@property
	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData):
	data: Union[int, float]
	typeName: ClassVar[str] = 'number'

	@property
	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData):
	data: str
	indexMapper: IndexMapper
	parsedValue: Optional[Any] = None
	typeName: ClassVar[str] = 'string'

	@property
	def children(self) -> Collection[JsonData]:
		return ()


@dataclass
class JsonArray(JsonData):
	data: Array
	typeName: ClassVar[str] = 'array'

	@property
	def children(self) -> Collection[JsonData]:
		return self.data


@dataclass
class JsonProperty(JsonData):
	key: JsonString
	value: JsonData
	schema: Optional[SwitchingPropertySchema]

	typeName: ClassVar[str] = 'property'

	@property
	def children(self) -> Collection[JsonData]:
		return self.key, self.value


@dataclass
class JsonObject(JsonData):
	data: Object
	typeName: ClassVar[str] = 'object'

	@property
	def children(self) -> Collection[JsonData]:
		return self.data.values()


class JsonSchema(Schema, Generic[_TT], ABC):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	TOKEN: TokenType = TokenType.invalid
	"""The parser tries to use a Schema of this Type if the parser encounters a token == TOKEN. (see also class JsonUnionSchema)"""
	DATA_TYPE: ClassVar[Type[_TT]] = JsonData
	typeName: ClassVar[str] = 'JsonData'
	language: ClassVar[LanguageId] = 'JSON'

	def __init__(self, *, description: MDStr = '', deprecated: bool = False):
		self.description: MDStr = description
		self.deprecated: bool = deprecated

	@property
	def asString(self) -> str:
		return self.typeName


class JsonNullSchema(JsonSchema[JsonNull]):
	TOKEN = TokenType.null
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNull
	typeName: ClassVar[str] = 'null'


class JsonBoolSchema(JsonSchema[JsonBool]):
	TOKEN = TokenType.boolean
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonBool
	typeName: ClassVar[str] = 'boolean'


class JsonNumberSchema(JsonSchema[JsonNumber], ABC):
	TOKEN = TokenType.number
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNumber
	typeName: ClassVar[str] = 'number'

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: MDStr = '', deprecated: bool = False):
		super(JsonNumberSchema, self).__init__(description=description, deprecated=deprecated)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'integer'


class JsonFloatSchema(JsonNumberSchema):
	typeName: ClassVar[str] = 'float'


class JsonStringSchema(JsonSchema[JsonString]):
	TOKEN = TokenType.string
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'string'

	def __init__(
			self,
			*,
			type: Optional[JsonArgType] = None,
			subType: Optional[JsonArgType] = None,
			args: Optional[dict[str, Union[Any, None]]] = None,
			description: MDStr = '',
			deprecated: bool = False
	):
		super(JsonStringSchema, self).__init__(description=description, deprecated=deprecated)
		self.type: Optional[JsonArgType] = type
		self.subType: Optional[JsonArgType] = subType
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


class JsonArraySchema(JsonSchema[JsonArray]):
	TOKEN = TokenType.left_bracket
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonArray
	typeName: ClassVar[str] = 'array'

	def __init__(self, *, description: MDStr = '', element: JsonSchema, deprecated: bool = False):
		super(JsonArraySchema, self).__init__(description=description, deprecated=deprecated)
		self.element: JsonSchema = element


class JsonKeySchema(JsonSchema[JsonString]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'key'


JSON_KEY_SCHEMA = JsonKeySchema()


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
	TOKEN = TokenType.invalid
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonProperty
	typeName: ClassVar[str] = 'property'

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
			requiresProp: Optional[tuple[str, ...]] = None,
			deprecated: bool = False):
		super(SwitchingPropertySchema, self).__init__(description=description, deprecated=deprecated)
		self.name: Union[str, Anything] = name
		self.isOptional: bool = optional
		self.default: Optional[_TT2] = default
		self.value: Optional[JsonSchema[_TT2]] = value
		self.decidingProp: Optional[str] = decidingProp
		self.values: dict[Union[str, int, bool], JsonSchema[_TT2]] = {}
		if requiresProp is None:
			requiresProp = ()
		elif isinstance(requiresProp, str):
			requiresProp = (requiresProp,)
		self.requiresProp: tuple[str, ...] = requiresProp
		if values is not None:
			for key, val in values.items():
				if isinstance(key, tuple):
					for k in key:
						self.values[k] = val
				else:
					self.values[key] = val

	@property
	def isMandatory(self) -> bool:
		return not self.isOptional

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
			selectedSchema = self.values.get(dVal, self.value)
		else:
			selectedSchema = self.value

		if isinstance(selectedSchema, JsonCalculatedValueSchema):
			selectedSchema = selectedSchema.func(parent)
		return selectedSchema


PropertySchema = SwitchingPropertySchema


class JsonObjectSchema(JsonSchema[Object]):
	TOKEN = TokenType.left_brace
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonObject
	typeName: ClassVar[str] = 'object'

	def __init__(self, *, description: MDStr = '', properties: list[SwitchingPropertySchema], deprecated: bool = False):
		super(JsonObjectSchema, self).__init__(description=description, deprecated=deprecated)
		self.properties: tuple[SwitchingPropertySchema, ...] = tuple(properties)
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


class JsonUnionSchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'union'

	def __init__(self, *, description: MDStr = '', options: Sequence[JsonSchema]):
		super(JsonUnionSchema, self).__init__(description=description)
		self.options: Sequence[JsonSchema] = options

	@CachedProperty
	def optionsDict(self) -> dict[TokenType, JsonSchema]:
		result = {}
		for opt in self.options:
			if isinstance(opt, JsonUnionSchema):
				result.update(opt.optionsDict)
			else:
				result[opt.TOKEN] = opt
		return result

	@CachedProperty
	def optionsDict2(self) -> dict[Type[JsonData], JsonSchema]:
		result = {}
		for opt in self.options:
			if isinstance(opt, JsonUnionSchema):
				result.update(opt.optionsDict2)
			else:
				result[opt.DATA_TYPE] = opt
		return result

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"({'|'.join(o.asString for o in self.optionsDict2.values())})"


class JsonCalculatedValueSchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'calculated'

	def __init__(self, *, description: MDStr = '', func: Callable[[JsonObject], Optional[JsonSchema]]):
		super(JsonCalculatedValueSchema, self).__init__(description=description)
		self.func: Callable[[JsonObject], Optional[JsonSchema]] = func

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"(...)"


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
	'Token',

	'Array',
	'Object',
	'JsonTypes',

	'JsonProperty',
	'JsonData',
	'JsonInvalid',
	'JsonNull',
	'JsonBool',
	'JsonNumber',
	'JsonString',
	'JsonArray',
	'JsonObject',

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

	'JsonTokenizeError',
	'JsonParseError',
	'JsonSemanticsError',

	'JsonArgType',
]
