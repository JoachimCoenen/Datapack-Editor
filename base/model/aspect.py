from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import NewType, TypeVar, Generic, Type, Optional, Iterator

AspectType = NewType('AspectType', str)


@dataclass
class Aspect(ABC):

	@classmethod
	@abstractmethod
	def getAspectType(cls) -> AspectType:
		pass


_TAspect = TypeVar('_TAspect', bound=Aspect)
_TAspect2 = TypeVar('_TAspect2', bound=Aspect)


@dataclass
class AspectDict(Generic[_TAspect]):
	# _type: Type[_TAspect] = Serialized(default=None)
	# parent: Project = Serialized(default=None, shouldPrint=False)
	# aspects: dict[AspectType, _TAspect] = Serialized(default_factory=dict)
	_type: Type[_TAspect]
	_aspects: dict[AspectType, _TAspect] = field(default_factory=dict, init=False)

	def _get(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		return self._aspects.get(aspectCls.getAspectType())

	def _add(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		"""blindly adds an aspect, possibly overwriting another one. It check the type tho"""
		return self.replace(aspectCls, aspectCls())

	def add(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if self._get(aspectCls) is not None:
			raise ValueError(f"Aspect of type {aspectCls.getAspectType()!r} already assigned.")
		return self._add(aspectCls)

	def replace(self, aspectCls: Type[_TAspect2], aspect: _TAspect2) -> _TAspect2:
		assert issubclass(aspectCls, getattr(self, '_type'))  # don't confuse the pycharm type checker
		assert isinstance(aspect, aspectCls)
		self._aspects[aspectCls.getAspectType()] = aspect
		return aspect

	def get(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		aspect = self._get(aspectCls)
		# if aspect is None:
		# 	raise KeyError(f"Aspect of type {aspectType!r} not assigned to project.")
		# no explicit isinstance check, to allow duck typing.
		# if not isinstance(aspect, aspectCls):
		# 	raise TypeError(f"Aspect not of expected type: expected {aspectCls}, but got {type(aspect)}.")
		return aspect

	def setdefault(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if (aspect := self._get(aspectCls)) is not None:
			return aspect
		return self._add(aspectCls)

	def __getitem__(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if (aspect := self._get(aspectCls)) is not None:
			return aspect
		raise KeyError(f"{aspectCls}({aspectCls.getAspectType()!r})")

	def __contains__(self, aspectCls: Type[_TAspect2]) -> bool:
		return self._get(aspectCls) is not None

	def __iter__(self) -> Iterator[_TAspect]:
		yield from self._aspects.values()
