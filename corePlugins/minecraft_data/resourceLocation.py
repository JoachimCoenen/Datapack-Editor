from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


_BASE_PATTERN_BYTES = rb'(?:[0-9a-zA-Z._-]+:)?[0-9a-zA-Z._/-]*'

RESOURCE_LOCATION_NO_TAG_PATTERN = re.compile(_BASE_PATTERN_BYTES)
RESOURCE_LOCATION_PATTERN = re.compile(b'#?' + _BASE_PATTERN_BYTES)


@dataclass(order=False, eq=False, unsafe_hash=False, frozen=True, slots=True)
class ResourceLocation:
	"""
	The namespace and the path of a resource location should only contain the following symbols:
		- '0123456789' Numbers
		- 'abcdefghijklmnopqrstuvwxyz' Lowercase letters
		- '_' Underscore
		- '-' Hyphen/minus
		- '.' Dot
	The following characters are illegal in the namespace, but acceptable in the path:
		- '/' Forward slash (directory separator)
	The preferred naming convention for either namespace or path is snake_case.
	"""
	namespace: Optional[str]
	path: str
	isTag: bool

	def __post_init__(self):
		assert self.namespace is None or self.namespace.strip()

	@property
	def isMCNamespace(self) -> bool:
		return self.namespace is None or self.namespace == 'minecraft'

	@property
	def actualNamespace(self) -> str:
		return self.namespace or 'minecraft'  #  'minecraft' if self.namespace is None else self.namespace

	@property
	def asString(self) -> str:
		"""
		ResourceLocation.fromString('end_rod').asString == 'end_rod'
		ResourceLocation.fromString('minecraft:end_rod').asString == 'minecraft:end_rod'
		:return: The pure string representation
		"""
		tag = '#' if self.isTag else ''
		if self.namespace is None:
			return f'{tag}{self.path}'
		else:
			return f'{tag}{self.namespace}:{self.path}'

	@property
	def asCompactString(self) -> str:
		"""
		Omits the 'minecraft:' namespace if possible.

			ResourceLocation.fromString('end_rod').asString == 'end_rod'
			ResourceLocation.fromString('minecraft:end_rod').asString == 'end_rod'
		"""
		tag = '#' if self.isTag else ''
		namespace = self.namespace
		if namespace is None or namespace == 'minecraft':
			return f'{tag}{self.path}'
		else:
			return f'{tag}{namespace}:{self.path}'

	@property
	def asQualifiedString(self) -> str:
		"""
		Always prepends the namespace, even if it could be omitted.

			ResourceLocation.fromString('end_rod').asString == 'minecraft:end_rod'
			ResourceLocation.fromString('minecraft:end_rod').asString == 'minecraft:end_rod'
		"""
		tag = '#' if self.isTag else ''
		return f'{tag}{self.actualNamespace}:{self.path}'

	@classmethod
	def splitString(cls, value: str) -> tuple[Optional[str], str, bool]:
		namespace, _, path = value.partition(':')
		isTag = namespace.startswith('#')
		if isTag:
			namespace = namespace[1:]
		if not _:
			path = namespace
			namespace = None
		return namespace, path, isTag

	@classmethod
	def fromString(cls, value: str) -> ResourceLocation:
		return cls(*cls.splitString(value))

	@property
	def _asTuple(self) -> tuple[bool, str, str]:
		return self.isTag, self.actualNamespace, self.path,

	def __eq__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple == other._asTuple
		return NotImplemented

	def __lt__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple < other._asTuple
		return NotImplemented

	def __le__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple <= other._asTuple
		return NotImplemented

	def __gt__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple > other._asTuple
		return NotImplemented

	def __ge__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple >= other._asTuple
		return NotImplemented

	def __hash__(self):
		return hash(self._asTuple)


def isNamespaceValid(namespace: str) -> bool:
	pattern = r'[0-9a-z_.-]+'
	return re.fullmatch(pattern, namespace) is not None


__all__ = [
	'RESOURCE_LOCATION_NO_TAG_PATTERN',
	'RESOURCE_LOCATION_PATTERN',
	'ResourceLocation',
	'isNamespaceValid',
]
