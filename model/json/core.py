from __future__ import annotations
from dataclasses import dataclass, field
from math import inf
from typing import Generic, TypeVar, Sequence, Optional, Union, Mapping

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


@dataclass
class JsonData(Generic[_TT]):
	data: _TT
	span: Span = field(hash=False, compare=False)
	schema: Optional[JsonSchema]


class JsonNull(JsonData[None]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonData[bool]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonData[Union[int, float]]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonData[str]):
	pass


class JsonArray(JsonData[Array]):
	pass


class JsonObject(JsonData[Object]):
	pass


@abstract
class JsonSchema(Generic[_TT]):
	"""
	A schema description to contextualize and validate JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	TOKEN: TokenType = TokenType.invalid
	"""The parser tries to use a Schema of this Type if the parser encounters a token == TOKEN. (see also class JsonUnionSchema)"""

	def __init__(self, *, description: str = ''):
		self.description: str = description


class JsonNullSchema(JsonSchema[None]):
	TOKEN = TokenType.null


class JsonBoolSchema(JsonSchema[bool]):
	TOKEN = TokenType.boolean


@abstract
class JsonNumberSchema(JsonSchema[_TN], Generic[_TN]):
	TOKEN = TokenType.number

	def __init__(self, *, minVal: _TN = -inf, maxVal: _TN = inf, description: str = ''):
		super(JsonNumberSchema, self).__init__(description=description)
		self.min: _TN = minVal
		self.max: _TN = maxVal


class JsonIntSchema(JsonNumberSchema[int]):
	pass


class JsonFloatSchema(JsonNumberSchema[float]):
	pass


class JsonStringSchema(JsonSchema[str]):
	TOKEN = TokenType.string

	def __init__(self, *, type_: ArgumentType, description: str = ''):
		super(JsonStringSchema, self).__init__(description=description)
		self.type: ArgumentType = type_


class JsonArraySchema(JsonSchema[Array]):
	TOKEN = TokenType.left_bracket

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
