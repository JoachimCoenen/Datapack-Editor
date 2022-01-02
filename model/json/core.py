from __future__ import annotations
from dataclasses import dataclass, field
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar, Type

from Cat.utils import abstract, CachedProperty, NoneType
from Cat.utils.collections_ import OrderedMultiDict
from model.commands.argumentTypes import ArgumentType
from model.json.lexer import TokenType
from model.utils import Span

Array = list['JsonData']
Object = OrderedMultiDict[str, 'JsonProperty']

JsonTypes = Union[None, bool, int, float, str, Array, Object]

_TT = TypeVar('_TT', NoneType, bool, int, float, str, Array, Object)
_TN = TypeVar('_TN', int, float)


@dataclass
class JsonProperty:
	key: JsonString
	value: JsonData
	schema: Optional[SwitchingPropertySchema]

	typeName: ClassVar[str] = 'JsonProperty'


@abstract
@dataclass
class JsonData(Generic[_TT]):
	data: _TT
	span: Span = field(hash=False, compare=False)
	schema: Optional[JsonSchema]

	typeName: ClassVar[str] = 'JsonData'


@dataclass
class JsonNull(JsonData[None]):
	typeName: ClassVar[str] = 'null'


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData[bool]):
	typeName: ClassVar[str] = 'boolean'


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData[Union[int, float]]):
	typeName: ClassVar[str] = 'number'


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData[str]):
	typeName: ClassVar[str] = 'string'


@dataclass
class JsonArray(JsonData[Array]):
	typeName: ClassVar[str] = 'array'


@dataclass
class JsonObject(JsonData[Object]):
	typeName: ClassVar[str] = 'object'


@abstract
class JsonSchema(Generic[_TT]):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	TOKEN: TokenType = TokenType.invalid
	"""The parser tries to use a Schema of this Type if the parser encounters a token == TOKEN. (see also class JsonUnionSchema)"""
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonData
	typeName: ClassVar[str] = 'JsonData'

	def __init__(self, *, description: str = '', deprecated: bool = False):
		self.description: str = description
		self.deprecated: bool = deprecated


class JsonNullSchema(JsonSchema[None]):
	TOKEN = TokenType.null
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNull
	typeName: ClassVar[str] = 'null'


class JsonBoolSchema(JsonSchema[bool]):
	TOKEN = TokenType.boolean
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonBool
	typeName: ClassVar[str] = 'boolean'


@abstract
class JsonNumberSchema(JsonSchema[_TN], Generic[_TN]):
	TOKEN = TokenType.number
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonNumber
	typeName: ClassVar[str] = 'number'

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: str = '', deprecated: bool = False):
		super(JsonNumberSchema, self).__init__(description=description, deprecated=deprecated)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema[int]):
	typeName: ClassVar[str] = 'integer'


class JsonFloatSchema(JsonNumberSchema[float]):
	typeName: ClassVar[str] = 'float'


class JsonStringSchema(JsonSchema[str]):
	TOKEN = TokenType.string
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonString
	typeName: ClassVar[str] = 'string'

	def __init__(self, *, type: Optional[ArgumentType] = None, description: str = '', deprecated: bool = False):
		super(JsonStringSchema, self).__init__(description=description, deprecated=deprecated)
		self.type: Optional[ArgumentType] = type


class JsonArraySchema(JsonSchema[Array]):
	TOKEN = TokenType.left_bracket
	DATA_TYPE: ClassVar[Type[JsonData]] = JsonArray
	typeName: ClassVar[str] = 'array'

	def __init__(self, *, description: str = '', element: JsonSchema, deprecated: bool = False):
		super(JsonArraySchema, self).__init__(description=description, deprecated=deprecated)
		self.element: JsonSchema = element


class PropertySchema(Generic[_TT]):
	def __init__(self, *, name: str, description: str = '', default: Optional[_TT] = None, value: JsonSchema[_TT]):
		self.name: str = name
		self.description: str = description
		self.default: Optional[_TT] = default
		self.value: JsonSchema[_TT] = value

	@property
	def mandatory(self) -> bool:
		return self.default is None


class SwitchingPropertySchema(Generic[_TT]):
	def __init__(self, *, name: str, description: str = '', default: Optional[_TT] = None, value: JsonSchema[_TT], decidingProp: Optional[str] = None, values: dict[Union[str, int, bool], JsonSchema[_TT]] = None, deprecated: bool = False):
		self.name: str = name
		self.description: str = description
		self.deprecated: bool = deprecated
		self.default: Optional[_TT] = default
		self.value: JsonSchema[_TT] = value
		self.decidingProp: Optional[str] = decidingProp
		self.values: dict[Union[str, int, bool], JsonSchema[_TT]] = values or {}

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


class JsonUnionSchema(JsonSchema[JsonTypes]):
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

	@CachedProperty
	def typeName(self) -> str:
		return f"({'|'.join(o.typeName for o in self.optionsDict.values())})"


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
	'PropertySchema',
	'SwitchingPropertySchema',
	'JsonObjectSchema',
	'JsonUnionSchema',
]
