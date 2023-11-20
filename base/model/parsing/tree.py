from __future__ import annotations

import functools as ft
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Collection, Iterable, Iterator, TypeVar, Generic, Optional, ClassVar, Protocol, Type

from base.model.utils import Span, LanguageId

_TNode = TypeVar('_TNode', bound='Node')
_TSchema = TypeVar('_TSchema', bound='Schema')


@ft.total_ordering
@dataclass(eq=False, order=False, unsafe_hash=False, frozen=True)
class LanguageId2(Generic[_TNode]):
	name: str
	nodeCls: Type[_TNode]

	def __lt__(self, other) -> bool:
		return self.name < (other.name if isinstance(other, LanguageId2) else other)

	def __eq__(self, other) -> bool:
		return self.name == (other.name if isinstance(other, LanguageId2) else other)

	def __hash__(self) -> int:
		return hash(self.name)


class TokenLike(Protocol):
	type: Enum
	span: Span
	startEnd: slice


def _walkTree(children: Iterable[_TNode]) -> Iterator[_TNode]:
	for child in children:
		yield child
		if innerChildren := child.children:
			yield from _walkTree(innerChildren)


@dataclass  # (slots=True) because: TypeError: multiple bases have instance layout conflict FOR ResourceLocationNode
class Node(Generic[_TNode, _TSchema], ABC):
	span: Span = field(hash=False, compare=False)
	schema: Optional[_TSchema] = field(hash=False, compare=False)

	language: ClassVar[LanguageId] = ''

	@property
	@abstractmethod
	def children(self) -> Collection[_TNode]:
		"""
		:return: a collection of its children
		"""
		return ()

	def walkTree(self) -> Iterator[_TNode]:
		yield self
		yield from _walkTree(self.children)


@dataclass
class Schema:
	description: str

	language: ClassVar[LanguageId] = ''

	@property
	@abstractmethod
	def asString(self) -> str:
		pass


__all__ = [
	'LanguageId2',
	'TokenLike',
	'Node',
	'Schema',
]
