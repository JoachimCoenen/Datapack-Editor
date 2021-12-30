from __future__ import annotations
from dataclasses import dataclass, field
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping, ClassVar

from Cat.utils import abstract, CachedProperty, NoneType
from Cat.utils.collections_ import OrderedMultiDict
from model.commands.argumentTypes import ArgumentType
from model.json.lexer import TokenType
from model.utils import Span

Array = list['JsonData']
Object = OrderedMultiDict['JsonString', 'JsonData']

JsonTypes = Union[None, bool, int, float, str, Array, Object]

_TT = TypeVar('_TT', NoneType, bool, int, float, str, Array, Object)
_TN = TypeVar('_TN', int, float)


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
	typeName: ClassVar[str] = 'JsonData'

	def __init__(self, *, description: str = ''):
		self.description: str = description


class JsonNullSchema(JsonSchema[None]):
	TOKEN = TokenType.null
	typeName: ClassVar[str] = 'null'


class JsonBoolSchema(JsonSchema[bool]):
	TOKEN = TokenType.boolean
	typeName: ClassVar[str] = 'boolean'


@abstract
class JsonNumberSchema(JsonSchema[_TN], Generic[_TN]):
	TOKEN = TokenType.number
	typeName: ClassVar[str] = 'number'

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: str = ''):
		super(JsonNumberSchema, self).__init__(description=description)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema[int]):
	typeName: ClassVar[str] = 'integer'


class JsonFloatSchema(JsonNumberSchema[float]):
	typeName: ClassVar[str] = 'float'


class JsonStringSchema(JsonSchema[str]):
	TOKEN = TokenType.string
	typeName: ClassVar[str] = 'string'

	def __init__(self, *, type_: ArgumentType, description: str = ''):
		super(JsonStringSchema, self).__init__(description=description)
		self.type: ArgumentType = type_


class JsonArraySchema(JsonSchema[Array]):
	TOKEN = TokenType.left_bracket
	typeName: ClassVar[str] = 'array'

	def __init__(self, *, description: str = '', element: JsonSchema):
		super(JsonArraySchema, self).__init__(description=description)
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


class JsonObjectSchema(JsonSchema[Object]):
	TOKEN = TokenType.left_brace
	typeName: ClassVar[str] = 'object'

	def __init__(self, *, description: str = '', properties: list[PropertySchema]):
		super(JsonObjectSchema, self).__init__(description=description)
		self.properties: tuple[PropertySchema, ...] = tuple(properties)
		self.propertiesDict: Mapping[str, PropertySchema] = self._buildPropertiesDict()

	def _buildPropertiesDict(self) -> Mapping[str, PropertySchema]:
		propsDict: dict[str, PropertySchema] = dict[str, PropertySchema]()
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
	def typeName(self) -> str:
		return f"({'|'.join(o.typeName for o in self.optionsDict.values())})"


__all__ = [
	'Array',
	'Object',
	'JsonTypes',

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
	'JsonObjectSchema',
	'JsonUnionSchema',
]
