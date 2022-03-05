from abc import abstractmethod
from dataclasses import dataclass, field
from typing import TypeVar, Collection, Generic, Iterator, Optional

from model.utils import Span


_TNode = TypeVar('_TNode', bound='Node')
_TSchema = TypeVar('_TSchema', bound='Schema')


@dataclass
class Node(Generic[_TNode, _TSchema]):
	span: Span = field(hash=False, compare=False)
	schema: Optional[_TSchema] = field(hash=False, compare=False)

	# @property
	# @abstractmethod
	# def documentation(self) -> str:
	# 	"""
	# 	:return: a markdown string or an empty string, never None
	# 	"""
	# 	pass

	# @property
	# @abstractmethod
	# def children(self) -> Collection[_TNode]:
	# 	"""
	# 	:return: a collection of its children
	# 	"""
	# 	return ()
	#
	# def walkTree(self) -> Iterator[_TNode]:
	# 	yield self
	# 	for child in self.children:
	# 		yield from child.walkTree()


@dataclass
class Schema:
	description: str

	@property
	@abstractmethod
	def asString(self) -> str:
		pass



