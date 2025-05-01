from __future__ import annotations

import enum
from _weakref import ref, ReferenceType
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from math import inf
from typing import ClassVar, Collection, Any, Type, Sequence, Callable, Mapping, overload, Iterator, AbstractSet, Protocol


from better_orderedmultidict import OrderedMultiDict
from base.model.recordclassAdapter import as_dataclass

from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import IndexMapper
from base.model.parsing.tree import Node, Schema
from base.model.utils import LanguageId, MDStr, Span, NULL_SPAN
from cat.utils import CachedProperty, Anything, Nothing
from cat.utils.collections_ import AddToDictDecorator
from cat.utils.collections_.collections_ import IfKeyIssubclassGetter
from cat.utils.logging_ import logWarning


class TokenType(enum.Enum):
	invalid = enum.auto()

	null = enum.auto()
	boolean = enum.auto()
	number = enum.auto()
	quoted_string = enum.auto()
	unquoted_string = enum.auto()

	object_start = enum.auto()
	object_end = enum.auto()

	list_start = enum.auto()
	array_start = enum.auto()
	list_end = enum.auto()

	colon = enum.auto()
	comma = enum.auto()
	eof = enum.auto()

	@property
	def asString(self) -> str:
		return _TOKEN_TYPE_STR_REP[self]


_TOKEN_TYPE_STR_REP = {
	TokenType.invalid: "invalid",
	TokenType.null: "null",
	TokenType.boolean: "boolean",
	TokenType.number: "number",
	TokenType.quoted_string: "quoted string",
	TokenType.unquoted_string: "string",

	TokenType.object_start: "'{'",
	TokenType.object_end: "'}'",

	TokenType.array_start: "'[_;'",
	TokenType.list_start: "'['",
	TokenType.list_end: "']'",

	TokenType.colon: "':'",
	TokenType.comma: "','",
	TokenType.eof: "end of file",
}


@as_dataclass(frozen=True)
class Token:
	"""Represents a Token extracted by the parser"""
	type: TokenType
	span: Span
	value: bytes
	# isValid: bool = True


type ListLike[T: StructureDataNode] = Sequence[T]
type Object = OrderedMultiDict[str, StructureProperty]
type StructureValue = None | bool | int | float | str | ListLike[StructureDataNode] | Object


type PyStructureList = list['PyStructureValue']
type PyStructureObject = dict[str, 'PyStructureValue']
type PyStructureSimpleValue = None | bool | int | float | str
type PyStructureValue = PyStructureSimpleValue | PyStructureList | PyStructureObject


class StructureKind(enum.Enum):
	JSON = enum.auto()
	SNBT = enum.auto()


@dataclass
class StructureNode(Node['StructureNode', 'StructureSchema']):  # should also inherit ABC, but that creates an inconsistent method resolution order (MRO).
	typeName: ClassVar[str] = 'structure_node'
	language: ClassVar[LanguageId] = LanguageId('Structure')

	schema: StructureSchema | None = field(hash=False, compare=False)
	structureKind: StructureKind = field(hash=False, compare=False, kw_only=True)

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
class StructureDataNode[T: StructureValue](StructureNode):  # should also inherit ABC, but that creates an inconsistent method resolution order (MRO).
	typeName: ClassVar[str] = 'structure_node'
	data: T
	path: str = field(default='', init=False)
	_parent: ReferenceType[ObjectNode] | ReferenceType[ListLikeNode[StructureDataNode]] | None = field(default=None, init=False)

	schema: StructureDataSchema | None = field(hash=False, compare=False)

	@property
	def parent(self) -> ObjectNode | ListLikeNode[StructureDataNode] | None:
		return self._parent() if self._parent else None


@dataclass
class InvalidNode(StructureDataNode[str]):
	typeName: ClassVar[str] = 'invalid'
	data: str

	@property
	def children(self) -> Sequence[StructureNode]:
		return ()

	def asString(self) -> bytes:
		return b'<invalid>'


@dataclass
class BasicDataNode[T: StructureValue](StructureDataNode[T]):
	# typeName: ClassVar[str] = 'basic_data_node'
	data: T
	raw: bytes
	"""The raw value as read from the bytes, without any parsing, escape sequence processing, etc"""

	@property
	def children(self) -> Sequence[StructureNode]:
		return ()

	def asString(self) -> bytes:
		return self.raw


@dataclass
class NullNode(BasicDataNode[None]):
	typeName: ClassVar[str] = 'null'
	data: None = None
	raw: bytes = b'null'


@dataclass
class BooleanNode(BasicDataNode[bool]):
	typeName: ClassVar[str] = 'boolean'
	data: bool


@dataclass
class NumberNode[T: int | float](BasicDataNode[T]):
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
class StringNode(BasicDataNode[str]):
	typeName: ClassVar[str] = 'string'
	data: str
	rawData: bytes
	""" The actual value of the string expressed in bytes. Not to be confused with field 'raw'. """
	innerSlice: slice
	""" The actual Span *inside* the quotes. """
	indexMapper: IndexMapper
	parsedValue: Any | None = None


@dataclass
class ListLikeNode[T: StructureDataNode](StructureDataNode[ListLike[T]]):
	typeName: ClassVar[str] = 'array'
	data: list[T]

	@property
	def children(self) -> Sequence[StructureNode]:
		return self.data

	def asString(self) -> bytes:
		return b'[' + b', '.join(d.asString() for d in self.data) + b']'


@dataclass
class ListNode(ListLikeNode[StructureDataNode]):
	pass


@dataclass
class NumberArrayNode(ListLikeNode[NumberNode]):
	arrayTypeTag: bytes


@dataclass
class StructureProperty[N: StructureDataNode](StructureNode):
	typeName: ClassVar[str] = 'property'
	key: StringNode
	value: N
	
	schema: PropertySchema | None = field(hash=False, compare=False)

	def __post_init__(self) -> None:
		if isinstance(self.key.schema, KeySchema):
			self.key.schema.forProp = self

	@property
	def children(self) -> Sequence[StructureNode]:
		return self.key, self.value

	def asString(self) -> bytes:
		return self.key.asString() + b': ' + self.value.asString()


@dataclass
class ObjectNode(StructureDataNode[Object]):
	typeName: ClassVar[str] = 'object'
	data: Object

	def __post_init__(self) -> None:
		selfRef = ref(self)
		for prop in self.data.values():
			prop.key._parent = selfRef
			prop.value._parent = selfRef

	@property
	def children(self) -> Sequence[StructureProperty]:
		return self.data.values()  # type: ignore  # not 100% kosher, as _ValuesView is not indexable

	@overload
	def getValue(self, key: str) -> StructureDataNode | None: ...
	@overload
	def getValue[TD](self, key: str, default: TD) -> StructureDataNode | TD: ...

	def getValue[TD](self, key: str, default: TD | None = None) -> StructureDataNode | TD | None:
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
	DATA_TYPE: ClassVar[Type[StructureNode]] = StructureNode  # type: ignore
	typeName: ClassVar[str] = 'StructureNode'
	language: ClassVar[LanguageId] = LanguageId('Structure')  # not a real language

	def __init__(self, *, description: MDStr = MDStr(''), deprecated: bool = False, allowMultilineStr: bool | None = None):
		self.description: MDStr = description
		self.deprecated: bool = deprecated
		self.span: Span = NULL_SPAN
		self.filePath: str = ''
		self.allowMultilineStr: bool | None = allowMultilineStr

	@property
	def asString(self) -> str:
		return self.typeName

	def setSpan(self, newSpan: Span, filePath: str):
		self.span = newSpan
		self.filePath = filePath
		return self


class StructureDataSchema(StructureSchema, ABC):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = StructureDataNode  # type: ignore
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

	def __init__(self, *, minVal: float | int = -inf, maxVal: float | int = inf, description: MDStr = MDStr(''), deprecated: bool = False, allowMultilineStr: bool | None = None):
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
			type: str | None = None,
			args: dict[str, Any | None] | None = None,
			description: MDStr = MDStr(''),
			deprecated: bool = False,
			allowMultilineStr: bool | None
	):
		super(StringSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.type: str | None = type
		self.args: dict[str, Any | None] | None = args if args is not None else {}


class StringOptionsSchema(StringSchema):
	def __init__(
			self,
			*,
			options: dict[str, MDStr],
			description: MDStr = MDStr(''),
			deprecated: bool = False,
			warningOnly: bool = False,
			allowMultilineStr: bool | None
	):
		super().__init__(
			type=OPTIONS_STRUCTURE_ARG_TYPE.name,
			args=dict(values=options, warningOnly=warningOnly),
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)


class ListLikeSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = ListLikeNode
	typeName: ClassVar[str] = 'list'

	def __init__(self, *, description: MDStr = MDStr(''), element: StructureDataSchema, minElemCount: int | None, maxElemCount: int | None, deprecated: bool = False, allowMultilineStr: bool | None):
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
			type: str | None = 'dpe:structure/key_schema',
			args: dict[str, Any | None] | None = None,
			description: MDStr = MDStr(''),
			deprecated: bool = False,
			allowMultilineStr: bool | None = None
	):
		super(KeySchema, self).__init__(
			type=type,
			args=args,
			description=description,
			deprecated=deprecated,
			allowMultilineStr=allowMultilineStr,
		)
		self.forProp: StructureProperty | None = None


@as_dataclass(hashable=True, frozen=True)
class DecidingPropRef:
	lookback: int
	name: str

	def __str__(self) -> str:
		return f'(lookback={self.lookback!r}, name={self.name!r})'


@as_dataclass(hashable=True, frozen=True)
class DecidingPropNotFound:
	msg: str


def getDecidingPropValue(decidingProp: DecidingPropRef, parent: ObjectNode) -> PyStructureValue | DecidingPropNotFound:
	decidingPropParent: ObjectNode | ListLikeNode[StructureDataNode] = parent
	for _ in range(decidingProp.lookback):
		decidingPropParent = decidingPropParent.parent  # type: ignore  # ignore potential `None` result type
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
	"""
	Property of an Object.
	Properties that are part of an ExclusionGroup are all treated as mandatory if at least one valid property is mandatory.

	A property `P` is considered only iff:
		- none of the properties `P` hates exists. (PropertySchema.hates, deprecated)
		- AND `P` has a valid value definition.
	`P` has a valid value definition iff:
		- `P` has no PropertySchema.decidingProp.
		- OR `P` has a PropertySchema.decidingProp AND it has a valid value definition for the value of the given decidingProp. (PropertySchema.values)

	`.requires`: has no effect on whether a property is considered.

	`.exclusionGroup`: can be used to force only one of multiple properties. (see also documentation on class ExclusionGroup).
	"""
	DATA_TYPE: ClassVar[Type[StructureNode]] = StructureProperty
	typeName: ClassVar[str] = 'property'

	def __init__(
			self,
			*,
			name: str | Anything,
			description: MDStr = MDStr(''),
			value: StructureDataSchema | None,
			optional: bool = False,
			default: PyStructureValue = None,
			decidingProp: DecidingPropRef | None = None,
			values: Mapping[PyStructureSimpleValue | tuple[PyStructureSimpleValue, ...], StructureDataSchema] | None = None,
			requires: tuple[str, ...] | None = None,
			hates: tuple[str, ...] = (),
			exclusionGroups: tuple[str, ...] = (),
			deprecated: bool = False,
			allowMultilineStr: bool | None):
		super(PropertySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.name: str | Anything = name
		self.optional: bool = optional
		self.default: PyStructureValue = default
		self.value: StructureDataSchema | None = value
		self.decidingProp: DecidingPropRef | None = decidingProp
		self.values: dict[PyStructureSimpleValue, StructureDataSchema] = {}
		if requires is None:
			requires = ()
		elif isinstance(requires, str):
			requires = (requires,)
		self.requires: tuple[str, ...] = requires
		self.hates: tuple[str, ...] = hates
		self.exclusionGroups: tuple[str, ...] = exclusionGroups
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

	def isMissingRequiredProp(self, parent: ObjectNode) -> bool:
		return bool(self.requires) and all(p not in parent.data for p in self.requires)

	def hasIncompatibleProp(self, parent: ObjectNode) -> bool:
		return bool(self.hates) and any(p in parent.data for p in self.hates)

	def isConsidered(self, parent: ObjectNode) -> bool:
		missingRequiredProp = self.requires and all(p not in parent.data for p in self.requires)
		hasIncompatibleProp = self.hates and any(p in parent.data for p in self.hates)
		return not missingRequiredProp and not hasIncompatibleProp and self.getValueSchemaForParent(parent) is not None

	def getValueSchemaForParent(self, parent: ObjectNode) -> StructureDataSchema | None:
		decidingProp = self.decidingProp
		if decidingProp is not None:
			dVal = getDecidingPropValue(decidingProp, parent)
			if isinstance(dVal, DecidingPropNotFound):
				return UnionSchema(description=MDStr(dVal.msg), options=[], allowMultilineStr=None)
			if not callable(getattr(dVal, '__hash__', None)):
				msg = f"value of decidingProp is not a simple value, but rather a {type(dVal).__name__}."
				return UnionSchema(description=MDStr(msg), options=[], allowMultilineStr=None)
			selectedSchema: StructureDataSchema | None = self.values.get(dVal, self.value)  # type: ignore
		else:
			selectedSchema = self.value

		return resolveCalculatedSchema(selectedSchema, parent)


@dataclass(frozen=True, slots=True)
class ExclusionGroup:
	"""
	Properties that are part of an ExclusionGroup are all treated as mandatory if at least one *considered* property is mandatory.
	(For a definition of *considered* see class PropertySchema.)

	If there is no mandatory *considered* property, the properties of ExclusionGroup are optional (no surprises here...)/
	"""
	props: frozenset[str]
	"""All properties in the exclusion group"""
	mandatoryProps: frozenset[str]
	"""Any properties that could make this ExclusionGroup mandatory."""


@dataclass
class Inheritance:
	schema: ObjectSchema
	decidingProp: DecidingPropRef | None = None
	decidingValues: tuple[str, ...] = ()


class ObjectSchema(StructureDataSchema):
	DATA_TYPE: ClassVar[Type[StructureDataNode]] = ObjectNode
	typeName: ClassVar[str] = 'object'

	def __init__(
			self, *,
			description: MDStr = MDStr(''),
			properties: list[PropertySchema],
			inherits: list[Inheritance] | None = None,
			definingProps: AbstractSet[str] = frozenset(),
			deprecated: bool = False,
			allowMultilineStr: bool | None
	):
		super(ObjectSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.inherits: list[Inheritance] = inherits if inherits is not None else []
		self.definingProps: AbstractSet[str] = definingProps
		"""
		Used to help select the correct choice from a UnionSchema of ObjectSchema. 
		If any of the definingProps are given, then THIS must be the correct choice from the union.
		
		A defining prop is not necessarily mandatory and Missing definingProps do have no effect on the selected choice.
		"""
		self.properties: list[PropertySchema] = properties
		self.propertiesDict: Mapping[str, PropertySchema] = {}
		self.exclusionGroups: Mapping[str, ExclusionGroup] = {}
		"""Not every property in an exclusion group might be mandatory"""
		self.anythingProp: PropertySchema | None = None
		self.anythingKey: StringSchema | None = None
		"""Specialized key schema that can be applied together with anythingProp."""
		self.isFinished: bool = False
		# self.finish()

	def finish(self) -> ObjectSchema:
		if not self.isFinished:
			self.propertiesDict, self.anythingProp = _buildPropertiesDict(self.inherits, self.properties)
			self.exclusionGroups = _buildExclusionGroups(self.propertiesDict)
			self.isFinished = True
		return self

	def getSchemaForProp(self, name: str) -> PropertySchema | None:
		return self.propertiesDict.get(name, self.anythingProp)

	def getSchemaForPropAndVal(self, name: str, parent: ObjectNode) -> tuple[StringSchema | None, PropertySchema | None, StructureDataSchema | None]:
		"""
		:return: keySchema, propSchema, valueSchema.
				usually keySchema is None, unless a special schema for default-keys has been provided.
		"""
		keySchema = None
		propSchema = self.propertiesDict.get(name, None)
		if propSchema is None:
			propSchema = self.anythingProp
			keySchema = self.anythingKey
		valueSchema = propSchema.getValueSchemaForParent(parent) if propSchema is not None else None
		return keySchema, propSchema, valueSchema


def _buildExclusionGroups(properties: Mapping[str, PropertySchema]) -> Mapping[str, ExclusionGroup]:
	exclusionGroups: defaultdict[str, list[PropertySchema]] = defaultdict(list)

	for prop in properties.values():
		for name in prop.exclusionGroups:
			exclusionGroups[name].append(prop)

	return {
		name: ExclusionGroup(
			# Anything check only theoretically needed.
			frozenset({prop.name for prop in exclusions if prop.name is not Anything}),  # type: ignore  # mypy gets confused by `Anything`
			frozenset({prop.name for prop in exclusions if not prop.optional and prop.name is not Anything})  # type: ignore  # mypy gets confused by `Anything`
		)
		for name, exclusions in exclusionGroups.items()
	}


def _buildPropertiesDict(inherits: list[Inheritance], properties: list[PropertySchema]) -> tuple[Mapping[str, PropertySchema], PropertySchema | None]:
	propsDict: dict[str, PropertySchema] = dict()
	anythingProp = None

	for inherit in inherits:
		if not inherit.schema.isFinished:
			inherit.schema.finish()
		if inherit.decidingProp is None:
			for prop in inherit.schema.propertiesDict.values():
				anythingProp = _addProp(anythingProp, prop, propsDict)
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
					exclusionGroups=prop.exclusionGroups,
					deprecated=prop.deprecated,
					allowMultilineStr=None,
				)
				newProp.setSpan(prop.span, prop.filePath)
				anythingProp = _addProp(anythingProp, newProp, propsDict)

	for prop in properties:
		anythingProp = _addProp(anythingProp, prop, propsDict)
	return propsDict, anythingProp


def _addProp(anythingProp: PropertySchema | None, prop: PropertySchema, propsDict: dict[str, PropertySchema]) -> PropertySchema | None:
	if prop.name is Anything:
		# quietly overwrite:
		# if anythingProp is not None:
		# 	raise ValueError(f"ObjectSchema.properties contains duplicate anything Property")
		anythingProp = prop
	else:
		# quietly overwrite:
		# if prop.name in propsDict:
		# 	raise ValueError(f"ObjectSchema.properties contains duplicate names {prop.name!r}")
		if (origProp := propsDict.get(prop.name)) is not None:  # type: ignore  # mypy gets confused by `Anything`
			prop = _joinProps(origProp, prop)

		propsDict[prop.name] = prop  # type: ignore  # mypy gets confused by `Anything`
	return anythingProp


def _checkPropsNotDiffering(prop1: PropertySchema, prop2: PropertySchema, attribute: str) -> bool:
	val1 = getattr(prop1, attribute)
	val2 = getattr(prop2, attribute)
	if val1 != val2:
		logWarning(f"Properties have differing '{attribute}' value [{val1}, {val2}]. prop.name = {prop1.name!r}, locations = [({prop1.filePath!r}, {prop1.span}), ({prop2.filePath!r}, {prop2.span})]")
		return False
	return True


def _joinProps(prop1: PropertySchema, prop2: PropertySchema) -> PropertySchema:
	if prop1.decidingProp != prop2.decidingProp:
		logWarning(f"Cannot join properties with differing deciding props [{prop1.decidingProp}, {prop2.decidingProp}]. prop.name = {prop1.name!r}, locations = [({prop1.filePath!r}, {prop1.span}), ({prop2.filePath!r}, {prop2.span})]")
		return prop2
	_checkPropsNotDiffering(prop1, prop2, 'optional')
	_checkPropsNotDiffering(prop1, prop2, 'default')
	_checkPropsNotDiffering(prop1, prop2, 'requires')
	_checkPropsNotDiffering(prop1, prop2, 'hates')
	_checkPropsNotDiffering(prop1, prop2, 'deprecated')

	if prop1.decidingProp is not None:
		values = prop1.values.copy()
		for decVal, val in prop2.values.items():
			if decVal in values:
				val = UnionSchema(description=MDStr(''), options=[values[decVal], val], allowMultilineStr=None)
			values[decVal] = val
		value = None
	else:
		if prop1.value is None or prop2.value is None:
			raise ValueError("PropertySchema.value is None, but PropertySchema.decidingProp is not set.")
		values = None
		value = UnionSchema(description=MDStr(''), options=[prop1.value, prop2.value], allowMultilineStr=None)

	exclusionGroups = tuple({*prop1.exclusionGroups, *prop2.exclusionGroups})

	newProp = PropertySchema(
		name=prop1.name,
		description=prop1.description,
		value=value,
		optional=prop1.optional,
		default=prop1.default,
		decidingProp=prop1.decidingProp,
		values=values,  # type: ignore
		requires=prop1.requires,
		hates=prop1.hates,
		exclusionGroups=exclusionGroups,
		deprecated=prop1.deprecated,
		allowMultilineStr=None,
	)
	if prop2.filePath:
		newProp.setSpan(prop2.span, prop2.filePath)
	else:
		newProp.setSpan(prop1.span, prop1.filePath)
	return newProp


class UnionSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'union'

	def __init__(self, *, description: MDStr = MDStr(''), options: Sequence[StructureDataSchema], allowMultilineStr: bool | None):
		super(UnionSchema, self).__init__(description=description, allowMultilineStr=allowMultilineStr)
		self.options: Sequence[StructureDataSchema] = options

	@CachedProperty
	def allOptions(self) -> list[StructureDataSchema]:
		result = []
		for opt in self.options:
			if isinstance(opt, UnionSchema):
				result.extend(opt.allOptions)
			else:
				result.append(opt)
		return result

	# @CachedProperty
	@property
	def asString(self) -> str:
		return f"({'|'.join(o.asString for o in self.options)})"


class CalculatedValueSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'calculated'

	def __init__(self, *, description: MDStr = MDStr(''), func: Callable[[ObjectNode], StructureDataSchema | None], deprecated: bool = False, allowMultilineStr: bool | None):
		super(CalculatedValueSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)
		self.func: Callable[[ObjectNode], StructureDataSchema | None] = func

	# @CachedProperty
	@property
	def asString(self) -> str:
		return "(...)"


def resolveCalculatedSchema(schema: StructureDataSchema | None, parent: ObjectNode | None) -> StructureDataSchema | None:
	if isinstance(schema, CalculatedValueSchema) and parent is not None:
		schema = schema.func(parent)
	return schema


class AnySchema(StructureDataSchema):
	typeName: ClassVar[str] = 'any'

	def __init__(self, *, description: MDStr = MDStr(''), deprecated: bool = False, allowMultilineStr: bool | None):
		super(AnySchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


class IllegalSchema(StructureDataSchema):
	typeName: ClassVar[str] = 'illegal'

	def __init__(self, *, description: MDStr = MDStr(''), deprecated: bool = False, allowMultilineStr: bool | None):
		super(IllegalSchema, self).__init__(description=description, deprecated=deprecated, allowMultilineStr=allowMultilineStr)


STRUCTURE_ANY_SCHEMA: AnySchema = AnySchema(allowMultilineStr=None)
STRUCTURE_ILLEGAL_SCHEMA: IllegalSchema = IllegalSchema(allowMultilineStr=None)


def resolvePath(data: StructureDataNode, path: tuple[str | int, ...]) -> StructureDataNode | None:
	result = data
	for item in path:
		if isinstance(item, str):
			if not isinstance(result, ObjectNode):
				return None
			prop = result.data.get(item)
			if prop is None:
				return None
			result = prop.value
		elif isinstance(result, ListLikeNode):
			if item >= len(result.data):
				return None
			result = result.data[item]
		else:
			return None
	return result


def resolvePath2[R: StructureDataNode](data: StructureDataNode, path: tuple[str | int, ...], RCls: Type[R]) -> R | None:
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
	if isinstance(result, RCls):
		return result
	return None


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


class DataNodeLike(Protocol):
	# n: TJSD
	@property
	def data(self) -> StructureValue:
		...


_toPyValueHandlers: dict[Type[StructureDataNode], Callable[[DataNodeLike, Callable[[DataNodeLike, Any], DataNodeLike]], PyStructureValue]] = {}

_toPyValueHandler: AddToDictDecorator = AddToDictDecorator(_toPyValueHandlers)

_getToPyValueHandler = IfKeyIssubclassGetter(_toPyValueHandlers)


@overload
def toPyValue(data: DataNodeLike) -> PyStructureValue: ...
@overload
def toPyValue(data: DataNodeLike, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike]) -> PyStructureValue: ...


def toPyValue(data: DataNodeLike, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike] = lambda e, parent: e) -> PyStructureValue:
	if resolver is ...:
		return _toPyValue(data, lambda e, parent: e)
	return _toPyValue(data, resolver)


def _toPyValue(data: DataNodeLike, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike]) -> PyStructureValue:
	if hasattr(data, 'n'):
		handler = _getToPyValueHandler(type(data.n))
	else:
		handler = _getToPyValueHandler(type(data))  # type: ignore
	return handler(data, resolver)  # type: ignore


@_toPyValueHandler(InvalidNode)
def _invalidHandler[T](node: InvalidNode, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike]) -> None:
	return None


@_toPyValueHandler(ObjectNode)
def _objectHandler[T](node: ObjectNode, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike]) -> PyStructureObject:
	return {_stringHandler(p.key, resolver): toPyValue(resolver(p.value, node), resolver) for p in node.data.values()}  # type: ignore


@_toPyValueHandler(ListLikeNode)
def _arrayHandler[T](node: ListLikeNode, resolver: Callable[[StructureDataNode, DataNodeLike], DataNodeLike]) -> PyStructureList:
	return [toPyValue(resolver(e, node), resolver) for e in node.data]  # type: ignore


@_toPyValueHandler(BooleanNode)
@_toPyValueHandler(NumberNode)
@_toPyValueHandler(StringNode)
@_toPyValueHandler(NullNode)
def _stringHandler[T](node: BasicDataNode, resolver: Callable[[StructureDataNode, T], DataNodeLike]) -> PyStructureValue:
	return node.data


@dataclass
class StructureArgType:
	def __post_init__(self) -> None:
		if type(self) is StructureArgType:
			registerNamedStructureArgType(self)

	name: str
	description: MDStr = MDStr('')
	description2: MDStr = MDStr('')
	example: MDStr = MDStr('')
	examples: MDStr = MDStr('')
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
	'TokenType',
	'Token',

	'ListLike',
	'Object',
	'StructureValue',
	'PyStructureList',
	'PyStructureObject',
	'PyStructureSimpleValue',
	'PyStructureValue',

	'StructureKind',
	'StructureNode',
	'StructureDataNode',
	'InvalidNode',
	'BasicDataNode',
	'NullNode',
	'BooleanNode',
	'NumberNode',
	'StringNode',
	'ListLikeNode',
	'ListNode',
	'NumberArrayNode',
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
	'resolvePath2',
	'getEffectivePropertyValue',
	'toPyValue',

	'StructureArgType',
	'ALL_NAMED_STRUCTURE_ARG_TYPES',
	'OPTIONS_STRUCTURE_ARG_TYPE',
]
