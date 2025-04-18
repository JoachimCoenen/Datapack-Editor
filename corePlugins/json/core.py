from __future__ import annotations

import enum
from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from recordclass import as_dataclass

from base.model.parsing.tree import LanguageId2, Node
from base.model.utils import LanguageId, Span
from corePlugins.nbtJsonBase.core import StructureDataNode, InvalidNode, NullNode, BooleanNode, NumberNode, StringNode, \
	ListLikeNode, StructureProperty, ObjectNode, StructureSchema


class TokenType(enum.Enum):
	default = 0
	null = 1
	boolean = 2
	number = 3
	string = 4
	list_start = 5
	list_end = 7
	object_start = 6
	object_end = 8
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
	TokenType.list_start: "'['",
	TokenType.object_start: "'{'",
	TokenType.list_end: "']'",
	TokenType.object_end: "'}'",
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
	TokenType.list_start,
	TokenType.object_start,
	# TokenType.list_end,
	# TokenType.object_end,
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


@dataclass
class JsonNode(Node['JsonNode', StructureSchema], ABC):
	language: ClassVar[LanguageId] = LanguageId('JSON')


@dataclass
class JsonInvalid(JsonNode, InvalidNode):
	pass


@dataclass
class JsonNull(JsonNode, NullNode):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonNode, BooleanNode):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonNode, NumberNode[float]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonNode, StringNode):
	pass


@dataclass
class JsonArray(JsonNode, ListLikeNode[StructureDataNode]):
	pass


@dataclass
class JsonProperty(JsonNode, StructureProperty):
	pass


@dataclass
class JsonObject(JsonNode, ObjectNode):
	pass


JSON_ID2: LanguageId2 = LanguageId2('JSON', JsonNode)


__all__ = [
	'TokenType',
	'VALUE_TOKENS',
	'Token',

	'JsonNode',
	'JsonInvalid',
	'JsonNull',
	'JsonBool',
	'JsonNumber',
	'JsonString',
	'JsonArray',
	'JsonObject',
	'JsonProperty',
	'JSON_ID2',
]
