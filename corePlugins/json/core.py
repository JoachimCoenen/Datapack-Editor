from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import ClassVar

from recordclass import as_dataclass

from base.model.parsing.tree import LanguageId2, Node
from base.model.utils import LanguageId, Span
from corePlugins.nbtJsonBase.core import *


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


@dataclass
class JsonNode(Node['JsonNode', StructureSchema]):
	language: ClassVar[LanguageId] = 'JSON'


@dataclass
class JsonInvalid(JsonNode, InvalidNode[JsonNode]):
	pass


@dataclass
class JsonNull(JsonNode, NullNode[JsonNode]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonBool(JsonNode, BooleanNode[JsonNode]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonNumber(JsonNode, NumberNode[JsonNode, float]):
	pass


@dataclass(unsafe_hash=True, order=True)
class JsonString(JsonNode, StringNode[JsonNode]):
	pass


@dataclass
class JsonArray(JsonNode, ListLikeNode[JsonNode, StructureDataNode]):
	pass


@dataclass
class JsonProperty(JsonNode, StructureProperty[JsonNode]):
	pass


@dataclass
class JsonObject(JsonNode, ObjectNode[JsonNode]):
	pass


JSON_ID2: LanguageId2[JsonNode] = LanguageId2('JSON', JsonNode)


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
