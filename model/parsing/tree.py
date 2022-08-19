from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Collection, Iterable, Iterator, TypeVar, Generic, Optional, ClassVar, Protocol

from model.utils import Span, LanguageId

_TNode = TypeVar('_TNode', bound='Node')
_TSchema = TypeVar('_TSchema', bound='Schema')


class TokenLike(Protocol):
	type: Enum
	span: Span
	startEnd: slice


def _walkTree(children: Iterable[_TNode]) -> Iterator[_TNode]:
	for child in children:
		yield child
		if innerChildren := child.children:
			yield from _walkTree(innerChildren)


@dataclass
class Node(Generic[_TNode, _TSchema], ABC):
	span: Span = field(hash=False, compare=False)
	schema: Optional[_TSchema] = field(hash=False, compare=False)

	language: ClassVar[LanguageId] = ''

	# @property
	# @abstractmethod
	# def documentation(self) -> str:
	# 	"""
	# 	:return: a markdown string or an empty string, never None
	# 	"""
	# 	pass

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
	'TokenLike',
	'Node',
	'Schema',
]
