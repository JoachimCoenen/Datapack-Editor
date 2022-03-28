from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar, Type, Any, Collection, Iterator

from Cat.utils import abstract, CachedProperty
from Cat.utils.collections_ import OrderedMultiDict
from model.commands.argumentTypes import ArgumentType
from model.json.lexer import TokenType
from model.parsing.tree import Node
from model.utils import GeneralError

Array = list['JsonData']
Object = OrderedMultiDict[str, 'JsonProperty']

JsonTypes = Union[None, bool, int, float, str, Array, Object]

_TT = TypeVar('_TT')  # , NoneType, bool, int, float, str, Array, Object)
_TT2 = TypeVar('_TT2')  # , NoneType, bool, int, float, str, Array, Object)
_TN = TypeVar('_TN', int, float)


# @abstract
@dataclass
class JsonData(Node['JsonData', 'JsonSchema'], ABC):
	schema: Optional[JsonSchema]

	typeName: ClassVar[str] = 'JsonData'

	def walkTree(self) -> Iterator[JsonData]:
		yield self
		for child in self.children():
			yield from child.walkTree()


@dataclass
class JsonInvalid(JsonData):
	typeName: ClassVar[str] = 'invalid'
	data: str

	def children(self) -> Collection[JsonData]:
		return ()


@dataclass
class JsonNull(JsonData):
	typeName: ClassVar[str] = 'null'

	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData):
	data: bool
	typeName: ClassVar[str] = 'boolean'

	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData):
	data: Union[int, float]
	typeName: ClassVar[str] = 'number'

	def children(self) -> Collection[JsonData]:
		return ()


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData):
	data: str
	parsedValue: Optional[Any] = None
	typeName: ClassVar[str] = 'string'

	def children(self) -> Collection[JsonData]:
		return ()


@dataclass
class JsonArray(JsonData):
	data: Array
	typeName: ClassVar[str] = 'array'

	def children(self) -> Collection[JsonData]:
		return self.data


@dataclass
class JsonProperty(JsonData):
	key: JsonString
	value: JsonData
	schema: Optional[SwitchingPropertySchema]

	typeName: ClassVar[str] = 'property'

	def children(self) -> Collection[JsonData]:
		return self.key, self.value


@dataclass
class JsonObject(JsonData):
	data: Object
	typeName: ClassVar[str] = 'object'

	def children(self) -> Collection[JsonData]:
		return self.data.values()


class JsonSchema(Generic[_TT], ABC):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	TOKEN: TokenType = TokenType.invalid
	"""The parser tries to use a Schema of this Type if the parser encounters a token == TOKEN. (see also class JsonUnionSchema)"""
	DATA_TYPE: ClassVar[Type[_TT]] = JsonData
	typeName: ClassVar[str] = 'JsonData'

	def __init__(self, *, description: str = '', deprecated: bool = False):
		self.description: str = description
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

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: str = '', deprecated: bool = False):
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

	def __init__(self, *, type: Optional[ArgumentType] = None, description: str = '', deprecated: bool = False):
		super(JsonStringSchema, self).__init__(description=description, deprecated=deprecated)
		self.type: Optional[ArgumentType] = type


class JsonArraySchema(JsonSchema[JsonArray]):
	TOKEN = TokenType.left_bracket
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonArray
	typeName: ClassVar[str] = 'array'

	def __init__(self, *, description: str = '', element: JsonSchema, deprecated: bool = False):
		super(JsonArraySchema, self).__init__(description=description, deprecated=deprecated)
		self.element: JsonSchema = element


class JsonKeySchema(JsonSchema[JsonString]):
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'key'


JSON_KEY_SCHEMA = JsonKeySchema()


# class PropertySchema(Generic[_TT]):
# 	def __init__(self, *, name: str, description: str = '', default: Optional[_TT] = None, value: JsonSchema[_TT]):
# 		self.name: str = name
# 		self.description: str = description
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

	def __init__(self, *, name: str, description: str = '', value: JsonSchema[_TT2], default: JsonTypes = None, decidingProp: Optional[str] = None, values: dict[Union[str, int, bool], JsonSchema[_TT]] = None, deprecated: bool = False):
		self.name: str = name
		self.description: str = description
		self.deprecated: bool = deprecated
		self.default: Optional[_TT2] = default
		self.value: JsonSchema[_TT2] = value
		self.decidingProp: Optional[str] = decidingProp
		self.values: dict[Union[str, int, bool], JsonSchema[_TT2]] = values or {}

	@property
	def mandatory(self) -> bool:
		return self.default is None


PropertySchema = SwitchingPropertySchema


class JsonObjectSchema(JsonSchema[Object]):
	TOKEN = TokenType.left_brace
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonObject
	typeName: ClassVar[str] = 'object'

	def __init__(self, *, description: str = '', properties: list[SwitchingPropertySchema], deprecated: bool = False):
		super(JsonObjectSchema, self).__init__(description=description, deprecated=deprecated)
		self.properties: tuple[SwitchingPropertySchema, ...] = tuple(properties)
		self.propertiesDict: Mapping[str, SwitchingPropertySchema] = self._buildPropertiesDict()

	def _buildPropertiesDict(self) -> Mapping[str, SwitchingPropertySchema]:
		propsDict: dict[str, SwitchingPropertySchema] = dict[str, SwitchingPropertySchema]()
		for prop in self.properties:
			if prop.name in propsDict:
				raise ValueError(f"JsonObjectSchema.properties contains duplicate names {prop.name!r}")
			propsDict[prop.name] = prop
		return propsDict


class JsonUnionSchema(JsonSchema[JsonData]):
	typeName: ClassVar[str] = 'union'

	def __init__(self, *, description: str = '', options: Sequence[JsonSchema]):
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


class JsonSemanticsError(GeneralError):
	pass


__all__ = [
	'Array',
	'Object',
	'JsonTypes',

	'JsonProperty',
	'JsonData',
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
	'JsonArraySchema',
	'JsonKeySchema',
	'JSON_KEY_SCHEMA',
	'PropertySchema',
	'SwitchingPropertySchema',
	'JsonObjectSchema',
	'JsonUnionSchema',
]
