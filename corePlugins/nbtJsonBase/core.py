from __future__ import annotations

from _weakref import ref, ReferenceType
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import inf
from types import NoneType
from typing import ClassVar, Optional, Collection, Any, Type, Sequence, Callable, Mapping, overload, Iterator

from better_orderedmultidict import OrderedMultiDict
from recordclass import as_dataclass

from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import IndexMapper
from base.model.parsing.tree import Node, Schema
from base.model.utils import LanguageId, MDStr, Span, NULL_SPAN
from cat.utils import CachedProperty, Anything
from cat.utils.collections_ import AddToDictDecorator
from cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from cat.utils.logging_ import logWarning


type ListLike[T: StructureDataNode] = list[T]
type Object[N: StructureNode[N]] = OrderedMultiDict[str, StructureProperty[N]]
type StructureValue[N: StructureNode[N]] = NoneType | bool | int | float | str | ListLike[StructureDataNode[N]] | Object[N]


type PyStructureList = list['PyStructureValue']
type PyStructureObject = dict[str, 'PyStructureValue']
type PyStructureSimpleValue = NoneType | bool | int | float | str
type PyStructureValue = PyStructureSimpleValue | PyStructureList | PyStructureObject


@dataclass
class StructureNode[N: 'StructureNode[N]'](Node[N, 'StructureSchema']):  # should also inherit ABC, but that creates an inconsistent method resolution order (MRO).
	typeName: ClassVar[str] = 'structure_node'
	language: ClassVar[LanguageId] = 'Structure'

	schema: Optional[StructureSchema] = field(hash=False, compare=False)

	def walkTree(self) -> Iterator[StructureNode]:
		yield self
		yield from _walkChildren(self.children)

	@abstractmethod
	def asString(self) -> bytes:
		raise NotImplementedError()

	def __str__(self) -> str:
		return bytesToStr(self.asString())


def _walkChildren(children: Collection[StructureNode]) -> Iterator[StructureNode]:
	for child in children:
		yield child
		if child.typeName in {'property', 'object', 'array'}:
			if innerChildren := child.children:
				yield from _walkChildren(innerChildren)


@dataclass
class StructureDataNode[N: StructureNode[N], T: StructureValue[N]](StructureNode[N]):  # should also inherit ABC, but that creates an inconsistent method resolution order (MRO).
	typeName: ClassVar[str] = 'structure_node'
	data: T
	path: str = field(default='', init=False)
	_parent: Optional[ReferenceType[ObjectNode[N] | ListLikeNode[N, StructureDataNode[N]]]] = field(default=None, init=False)

	schema: Optional[StructureDataSchema] = field(hash=False, compare=False)

	@property
	def parent(self) -> Optional[ObjectNode[N] | ListLikeNode[N, StructureDataNode[N]]]:
		return self._parent and self._parent()


@dataclass
class InvalidNode[N: StructureNode[N]](StructureDataNode[N, str]):
	typeName: ClassVar[str] = 'invalid'
	data: str

	@property
	def children(self) -> Collection[N]:
		return ()

	def asString(self) -> bytes:
		return b'<invalid>'


@dataclass
class BasicDataNode[N: StructureNode[N], T](StructureDataNode[N, T]):
	# typeName: ClassVar[str] = 'basic_data_node'
	data: T
	raw: bytes
	"""The raw value as read from the bytes, without any parsing, escape sequence processing, etc"""

	@property
	def children(self) -> Collection[N]:
		return ()

	def asString(self) -> bytes:
		return self.raw


@dataclass
class NullNode[N: StructureNode[N]](BasicDataNode[N, None]):
	typeName: ClassVar[str] = 'null'
	data: None = None
	raw: bytes = b'null'


@dataclass
class BooleanNode[N: StructureNode[N]](BasicDataNode[N, bool]):
	typeName: ClassVar[str] = 'boolean'
	data: bool


@dataclass
class NumberNode[N: StructureNode[N], T: int | float](BasicDataNode[N, T]):
	typeName: ClassVar[str] = 'number'
	data: T


# @dataclass
# class ByteNode(NumberNode[int]):
# 	typeName: ClassVar[str] = 'byte_node'
# 	data: int
#
#
# @dataclass
# class ShortNode(NumberNode[int]):
# 	typeName: ClassVar[str] = 'short_node'
# 	data: int
#
#
# @dataclass
# class IntNode(NumberNode[int]):
# 	typeName: ClassVar[str] = 'int_node'
# 	data: int
#
#
# @dataclass
# class LongNode(NumberNode[int]):
# 	typeName: ClassVar[str] = 'long_node'
# 	data: int
#
#
# @dataclass
# class FloatNode(NumberNode[float]):
# 	typeName: ClassVar[str] = 'float_node'
# 	data: float
#
#
# @dataclass
# class DoubleNode(NumberNode[float]):
# 	typeName: ClassVar[str] = 'double_node'
# 	data: float


@dataclass
class StringNode[N: StructureNode[N]](BasicDataNode[N, str]):
	typeName: ClassVar[str] = 'string'
	data: str
	rawData: bytes
	""" The actual value of the string expressed in bytes. Not to be confused with field 'raw'. """
	indexMapper: IndexMapper
	parsedValue: Optional[Any] = None


@dataclass
class ListLikeNode[N: StructureNode[N], T: StructureDataNode[N]](StructureDataNode[N, ListLike[N, T]]):
	typeName: ClassVar[str] = 'array'
	data: list[T]

	@property
	def children(self) -> Collection[N]:
		return self.data

	def asString(self) -> bytes:
		return b'[' + b', '.join(d.asString() for d in self.data) + b']'


@dataclass
class StructureProperty[N: StructureNode[N]](StructureNode[N]):
	typeName: ClassVar[str] = 'property'
	key: StringNode
	value: StructureDataNode[N]
	
	schema: Optional[PropertySchema] = field(hash=False, compare=False)

	def __post_init__(self) -> None:
		if isinstance(self.key.schema, KeySchema):
			self.key.schema.forProp = self

	@property
	def children(self) -> Collection[N]:
		return self.key, self.value

	def asString(self) -> bytes:
		return self.key.asString() + b': ' + self.value.asString()


@dataclass
class ObjectNode[N: StructureNode[N]](StructureDataNode[N, Object[N]]):
	typeName: ClassVar[str] = 'object'
	data: Object[N]

	def __post_init__(self) -> None:
		selfRef = ref(self)
		for prop in self.data.values():
			prop.key._parent = selfRef
			prop.value._parent = selfRef

	@property
	def children(self) -> Collection[StructureProperty[N]]:
		return self.data.values()

	def getValue[TD](self, key: str, default: TD = None) -> StructureDataNode[N] | TD:
		prop = self.data.get(key)
		return prop.value if prop is not None else default

	def asString(self) -> bytes:
		return b'{' + b', '.join(d.asString() for d in self.data.values()) + b'}'


# ## SCHEMAS: #############################################################################


class StructureSchema(Schema, ABC):
	"""
	A schema description to contextualize and validate SNBT and JSON files.
	Note: This is NOT an implementation of the JSON Schema specification!
	"""
	DATA_TYPE: ClassVar[Type[StructureNode]] = StructureNode
	typeName: ClassVar[str] = 'StructureNode'
	language: ClassVar[LanguageId] = 'Structure'

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


class StructureDataSchema(StructureSchema, ABC):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = StructureDataNode
	typeName: ClassVar[str] = 'StructureDataNode'


class NullSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = NullNode
	typeName: ClassVar[str] = 'null'


class BooleanSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = BooleanNode
	typeName: ClassVar[str] = 'boolean'


class NumberSchema(StructureDataSchema, ABC):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = NumberNode
	typeName: ClassVar[str] = 'number'

	def __init__(self, *, minVal: float | int = -inf, maxVal: float | int = inf, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool] = None):
		super(NumberSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.min: float | int = minVal
		self.max: float | int = maxVal


class IntSchema(NumberSchema):
	typeName: ClassVar[str] = 'integer'


class FloatSchema(NumberSchema):
	typeName: ClassVar[str] = 'float'


class StringSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = StringNode
	typeName: ClassVar[str] = 'string'

	def __init__(
			self,
			*,
			type: Optional[str | StructureArgType] = None,
			args: Optional[dict[str, Any | None]] = None,
			description: MDStr = '',
			deprecated: bool = False,
			allowMultilineStr: Optional[bool]
	):
		super(StringSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.type: Optional[str] = getattr(type, 'name', type)
		self.args: Optional[dict[str, Any | None]] = args if args is not None else {}


class StringOptionsSchema(StringSchema):
	def __init__(
			self,
			*,
			options: dict[str, MDStr],
			description: MDStr = '',
			deprecated: bool = False,
			warningOnly: bool = False,
			allowMultilineStr: Optional[bool]
	):
		super().__init__(
			type=OPTIONS_STRUCTURE_ARG_TYPE,
			args=dict(values=options, warningOnly=warningOnly),
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)


class ListLikeSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = ListLikeNode
	typeName: ClassVar[str] = 'list'

	def __init__(self, *, description: MDStr = '', element: StructureDataSchema, minElemCount: int | None, maxElemCount: int | None, deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super().__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.element: StructureDataSchema = element
		self.minElemCount: int | None = minElemCount
		self.maxElemCount: int | None = maxElemCount


class KeySchema(StringSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = StringNode
	typeName: ClassVar[str] = 'key'

	def __init__(
			self,
			*,
			type: Optional[str] = 'dpe:structure/key_schema',
			args: Optional[dict[str, Any | None]] = None,
			description: MDStr = '',
			deprecated: bool = False,
			allowMultilineStr: Optional[bool] = None
	):
		super(KeySchema, self).__init__(
			type=type,
			args=args,
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)
		self.forProp: Optional[StructureProperty] = None


@as_dataclass(hashable=True, readonly=True)
class DecidingPropRef:
	lookback: int
	name: str

	def __str__(self) -> str:
		return f'(lookback={self.lookback!r}, name={self.name!r})'


@as_dataclass(hashable=True, readonly=True)
class DecidingPropNotFound:
	msg: str


def getDecidingPropValue[N: StructureNode[N]](decidingProp: DecidingPropRef, parent: ObjectNode[N]) -> StructureValue[N] | DecidingPropNotFound:
	decidingPropParent = parent
	for _ in range(decidingProp.lookback):
		decidingPropParent = decidingPropParent.parent
		if decidingPropParent is None:
			msg = f"encountered missing parent while resolving decidingProp with lookback={decidingProp.lookback}."
			logWarning(msg)
			return DecidingPropNotFound(msg)
	if not isinstance(decidingPropParent, ObjectNode):
		msg = f"resolved parent of decidingProp is not a ObjectNode, but rather a {decidingPropParent.typeName} with decidingProp={decidingProp}."
		logWarning(msg)
		return DecidingPropNotFound(msg)

	return getEffectivePropertyValue(decidingProp.name, decidingPropParent)


class PropertySchema(StructureSchema):
	DATA_TYPE: ClassVar[Type[StructureNode]] = StructureProperty
	typeName: ClassVar[str] = 'property'

	def __init__(
			self,
			*,
			name: str | Anything,
			description: MDStr = '',
			value: Optional[StructureDataSchema],
			optional: bool = False,
			default: PyStructureValue = None,
			decidingProp: Optional[DecidingPropRef] = None,
			values: dict[PyStructureSimpleValue | tuple[PyStructureSimpleValue, ...], StructureDataSchema] = None,
			requires: Optional[tuple[str, ...]] = None,
			hates: tuple[str, ...] = (),
			deprecated: bool = False,
			allowMultilineStr: Optional[bool]):
		super(PropertySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.name: str | Anything = name
		self.optional: bool = optional
		self.default: PyStructureValue = default
		self.value: Optional[StructureDataSchema] = value
		self.decidingProp: Optional[DecidingPropRef] = decidingProp
		self.values: dict[PyStructureSimpleValue, StructureDataSchema] = {}
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

	def getValueSchemaForParent(self, parent: ObjectNode) -> Optional[StructureDataSchema]:
		decidingProp = self.decidingProp
		if decidingProp is not None:
			dVal = getDecidingPropValue(decidingProp, parent)
			if isinstance(dVal, DecidingPropNotFound):
				return UnionSchema(description=MDStr(dVal.msg), options=[], allowMultilineStr=None)
			if not callable(getattr(dVal, '__hash__', None)):
				msg = f"value of decidingProp is not a simple value, but rather a {type(dVal).__name__}."
				return UnionSchema(description=MDStr(msg), options=[], allowMultilineStr=None)
			selectedSchema = self.values.get(dVal, self.value)
		else:
			selectedSchema = self.value

		return resolveCalculatedSchema(selectedSchema, parent)


class ObjectSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = ObjectNode
	typeName: ClassVar[str] = 'object'

	def __init__(self, *, description: MDStr = '', properties: list[PropertySchema], inherits: list[Inheritance] = (), definingProps: AbstractSet[str] = frozenset(), deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(ObjectSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.inherits: list[Inheritance] = inherits
		self.definingProps: AbstractSet[str] = definingProps
		"""
		Used to help select the correct choice from a UnionSchema of ObjectSchema. 
		If any of the definingProps are given, then THIS must be the correct choice from the union.
		
		A defining prop is not necessarily mandatory and Missing definingProps do have no effect on the selected choice.
		"""
		self.properties: list[PropertySchema] = properties
		self.propertiesDict: Mapping[str, PropertySchema] = {}
		self.anythingProp: Optional[PropertySchema] = None
		self.isFinished: bool = False
		# self.finish()

	def finish(self) -> ObjectSchema:
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
			# 	raise ValueError(f"ObjectSchema.properties contains duplicate anything Property")
			anythingProp = prop
		else:
			# quietly overwrite:
			# if prop.name in propsDict:
			# 	raise ValueError(f"ObjectSchema.properties contains duplicate names {prop.name!r}")
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
					val = UnionSchema(description=MDStr(''), options=[values[decVal], val], allowMultilineStr=None)
				values[decVal] = val
			value = None
		else:
			values = None
			value = UnionSchema(description=MDStr(''), options=[prop1.value, prop2.value], allowMultilineStr=None)
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

	def getSchemaForPropAndVal(self, name: str, parent: ObjectNode) -> tuple[Optional[PropertySchema], Optional[StructureDataSchema]]:
		propSchema = self.propertiesDict.get(name, self.anythingProp)
		valueSchema = propSchema.getValueSchemaForParent(parent) if propSchema is not None else None
		return propSchema, valueSchema


@dataclass
class Inheritance:
	schema: ObjectSchema
	decidingProp: Optional[DecidingPropRef] = None
	decidingValues: tuple[str, ...] = ()


class UnionSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'union'

	def __init__(self, *, description: MDStr = '', options: Sequence[StructureDataSchema], allowMultilineStr: Optional[bool]):
		super(UnionSchema, self).__init__(description=description, allowMultilineStr=allowMultilineStr)
		self.options: Sequence[StructureDataSchema] = options

	def _getAllOptions(self) -> list[StructureDataSchema]:
		result = []
		for opt in self.options:
			if isinstance(opt, UnionSchema):
				result.extend(opt.allOptions)
			else:
				result.append(opt)
		return result

	allOptions: list[StructureDataSchema] = CachedProperty(_getAllOptions)

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"({'|'.join(o.asString for o in self.options)})"


class CalculatedValueSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'calculated'

	def __init__(self, *, description: MDStr = '', func: Callable[[ObjectNode], Optional[StructureSchema]], deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(CalculatedValueSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.func: Callable[[ObjectNode], Optional[StructureSchema]] = func

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"(...)"


def resolveCalculatedSchema(schema: StructureSchema, parent: ObjectNode) -> Optional[StructureDataSchema]:
	if isinstance(schema, CalculatedValueSchema):
		schema = schema.func(parent)
	return schema


class AnySchema(StructureDataSchema):
	typeName: ClassVar[str] = 'any'

	def __init__(self, *, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(AnySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


class IllegalSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'illegal'

	def __init__(self, *, description: MDStr = '', deprecated: bool = False, allowMultilineStr: Optional[bool]):
		super(IllegalSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


STRUCTURE_ANY_SCHEMA: AnySchema = AnySchema(allowMultilineStr=None)
STRUCTURE_ILLEGAL_SCHEMA: IllegalSchema = IllegalSchema(allowMultilineStr=None)


def resolvePath[N: StructureNode[N]](data: StructureDataNode[N], path: tuple[str | int, ...]) -> Optional[StructureDataNode[N]]:
	result = data
	for item in path:
		if isinstance(item, str):
			if not isinstance(result, ObjectNode):
				return None
			prop = result.data.get(item)
			if prop is None:
				return None
			result = prop.value
		else:
			if not isinstance(result, ListLikeNode):
				return None
			if item >= len(result.data):
				return None
			result = result.data[item]
	return result


def getEffectivePropertyValue(propertyName: str, jObject: ObjectNode) -> PyStructureValue:
	dp = jObject.data.get(propertyName)
	if dp is not None:
		dVal = toPyValue(dp.value)
	elif isinstance(jObject.schema, ObjectSchema) and (propSchema := jObject.schema.getSchemaForProp(propertyName)) is not None:
		# property was not set. Try to get the default value for property
		dVal = propSchema.default
	else:  # property was not set and there's no default value.
		dVal = None
	return dVal


_toPyValueHandlers: dict[Type[StructureDataNode], Callable[[StructureDataNode, Callable[[StructureDataNode, Any], Any]], Any]] = {}

_toPyValueHandler = AddToDictDecorator(_toPyValueHandlers)

_getToPyValueHandler = IfKeyIssubclassGetter(_toPyValueHandlers)


@overload
def toPyValue(data: StructureDataNode) -> PyStructureValue: ...
@overload
def toPyValue[T](data: T, resolver: Callable[[StructureDataNode, T], T]) -> PyStructureValue: ...


def toPyValue[T](data: T, resolver: Callable[[StructureDataNode, T], T] = ...) -> PyStructureValue:
	if resolver is ...:
		return _toPyValue(data, lambda e, parent: e)
	return _toPyValue(data, resolver)


def _toPyValue[T](data: T, resolver: Callable[[StructureDataNode, T], T]) -> PyStructureValue:
	if hasattr(data, 'n'):
		handler = _getToPyValueHandler(type(data.n))
	else:
		handler = _getToPyValueHandler(type(data))
	return handler(data, resolver)


@_toPyValueHandler(InvalidNode)
def _invalidHandler[T](node: InvalidNode, resolver: Callable[[StructureDataNode, T], T]) -> None:
	return None


@_toPyValueHandler(ObjectNode)
def _objectHandler[T](node: ObjectNode, resolver: Callable[[StructureDataNode, T], T]) -> PyStructureObject:
	return {toPyValue(resolver(p.key, node), resolver): toPyValue(resolver(p.value, node), resolver) for p in node.data.values()}


@_toPyValueHandler(ListLikeNode)
def _arrayHandler[T](node: ListLikeNode, resolver: Callable[[StructureDataNode, T], T]) -> PyStructureList:
	return [toPyValue(resolver(e, node), resolver) for e in node.data]


@_toPyValueHandler(BooleanNode)
@_toPyValueHandler(NumberNode)
@_toPyValueHandler(StringNode)
@_toPyValueHandler(NullNode)
def _stringHandler[T](node: BasicDataNode, resolver: Callable[[StructureDataNode, T], T]) -> PyStructureValue:
	return node.data


@dataclass
class StructureArgType:
	def __post_init__(self) -> None:
		if type(self) is StructureArgType:
			registerNamedStructureArgType(self)

	name: str
	description: MDStr = ''
	description2: MDStr = ''
	example: MDStr = ''
	examples: MDStr = ''
	NBTProperties: str = ''  # todo what??


ALL_NAMED_STRUCTURE_ARG_TYPES: dict[str, StructureArgType] = {}
_registerNamedStructureArgType: AddToDictDecorator[str, StructureArgType] = AddToDictDecorator(ALL_NAMED_STRUCTURE_ARG_TYPES)


def registerNamedStructureArgType(structureArgType: StructureArgType, forceOverride: bool = False) -> None:
	_registerNamedStructureArgType(structureArgType.name, forceOverride=forceOverride)(structureArgType)


OPTIONS_STRUCTURE_ARG_TYPE = StructureArgType(
	name='options',
	description=MDStr(""),
	description2=MDStr(""),
	examples=MDStr(""),
)


__all__ = [
	'ListLike',
	'Object',
	'StructureValue',
	'PyStructureList',
	'PyStructureObject',
	'PyStructureSimpleValue',
	'PyStructureValue',

	'StructureNode',
	'StructureDataNode',
	'InvalidNode',
	'BasicDataNode',
	'NullNode',
	'BooleanNode',
	'NumberNode',
	'StringNode',
	'ListLikeNode',
	'StructureProperty',
	'ObjectNode',

	'StructureSchema',
	'StructureDataSchema',
	'NullSchema',
	'BooleanSchema',
	'NumberSchema',
	'IntSchema',
	'FloatSchema',
	'StringSchema',
	'StringOptionsSchema',
	'ListLikeSchema',
	'KeySchema',
	'DecidingPropRef',
	'PropertySchema',
	'ObjectSchema',
	'Inheritance',
	'UnionSchema',
	'CalculatedValueSchema',
	'resolveCalculatedSchema',
	'AnySchema',
	'IllegalSchema',
	
	'STRUCTURE_ANY_SCHEMA',
	'STRUCTURE_ILLEGAL_SCHEMA',

	'resolvePath',
	'getEffectivePropertyValue',
	'toPyValue',

	'StructureArgType',
	'ALL_NAMED_STRUCTURE_ARG_TYPES',
	'OPTIONS_STRUCTURE_ARG_TYPE',
]
