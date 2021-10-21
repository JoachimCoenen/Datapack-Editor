from __future__ import annotations
from typing import Any, Optional

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized


@RegisterContainer
class MCTokenDescription(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.name: str = ''


@RegisterContainer
class MCCommandPart(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	documentation: str = Serialized(default='')
	type: Optional[MCCommandType] = Serialized(default=None)
	overloads: list[MCCommandPart] = Serialized(default_factory=list)
	# arguments: list[Argument] = Serialized(default_factory=list)



@RegisterContainer
class MCCommandDescription(MCCommandPart):
	__slots__ = ()
	# arguments: list[Argument] = Serialized(default_factory=list)
	pass


@RegisterContainer
class MCCommandType(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	documentation: str = Serialized(default='')


@RegisterContainer
class MCCommandType(MCCommandType):
	__slots__ = ()
	name: str = Serialized(default='')
	documentation: str = Serialized(default='')


@RegisterContainer
class Argument(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	documentation: str = Serialized(default='')
	parameters: list[Parameter] = Serialized(default_factory=list)







