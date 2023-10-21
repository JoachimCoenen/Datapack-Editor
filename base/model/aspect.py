from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import NewType, TypeVar, Generic, Type, Optional, Iterator, Any, Callable, cast, overload, Mapping

from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.utils.collections_ import getIfKeyIssubclass, AddToDictDecorator
from cat.utils.formatters import formatVal
from cat.utils.logging_ import logFatal

AspectType = NewType('AspectType', str)


@dataclass
class Aspect(ABC):

	@classmethod
	@abstractmethod
	def getAspectType(cls) -> AspectType:
		pass


_TS = TypeVar('_TS')
_TAspect = TypeVar('_TAspect', bound=Aspect)
_TAspect2 = TypeVar('_TAspect2', bound=Aspect)


@dataclass
class AspectDict(Generic[_TAspect]):
	_type: Type[_TAspect]
	_aspects: dict[AspectType, _TAspect] = field(default_factory=dict, init=False)

	def _get(self, aspectType: AspectType) -> Optional[_TAspect]:
		return self._aspects.get(aspectType)

	def _set(self, aspect: _TAspect2) -> _TAspect2:
		"""blindly sets an aspect, possibly overwriting another one. It checks the type tho"""
		assert isinstance(aspect, getattr(self, '_type'))  # don't confuse the pycharm type checker
		self._aspects[aspect.getAspectType()] = aspect
		return aspect

	@overload
	def add(self, aspectCls: Type[_TAspect2]) -> _TAspect2: ...
	@overload
	def add(self, aspect: _TAspect2) -> _TAspect2: ...

	def add(self, aspectCls: Type[_TAspect2] | _TAspect2) -> _TAspect2:
		if self._get(aspectCls.getAspectType()) is not None:
			raise ValueError(f"Aspect of type {aspectCls.getAspectType()!r} already assigned.")
		if isinstance(aspectCls, type):
			return self._set(aspectCls())
		return self._set(aspectCls)

	def replace(self, aspect: _TAspect2) -> _TAspect2:
		return self._set(aspect)

	def get(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		aspect = self._get(aspectCls.getAspectType())
		return aspect

	def setdefault(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if (aspect := self._get(aspectCls.getAspectType())) is not None:
			return aspect
		return self._set(aspectCls())

	def discard(self, aspectCls: Type[_TAspect2]) -> None:
		self._aspects.pop(aspectCls.getAspectType(), None)

	def __getitem__(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if (aspect := self._get(aspectCls.getAspectType())) is not None:
			return aspect
		raise KeyError(f"{aspectCls}({aspectCls.getAspectType()!r})")

	def __contains__(self, aspectCls: Type[_TAspect2]) -> bool:
		return self._get(aspectCls.getAspectType()) is not None

	def __iter__(self) -> Iterator[_TAspect]:
		yield from self._aspects.values()


_REGISTERED_ASPECTS_FOR_CLASS: dict[Type, dict[AspectType, Type[Aspect]]] = defaultdict(dict)


def registerAspectForType(parentCls: Type, aspectCls: Type[Aspect], *, forceOverride: bool = False) -> None:
	AddToDictDecorator(_REGISTERED_ASPECTS_FOR_CLASS[parentCls])(aspectCls.getAspectType(), forceOverride=forceOverride)(aspectCls)


def getAspectsForClass(parentCls: Type) -> Mapping[AspectType, Type[Aspect]]:
	aspects = getIfKeyIssubclass(_REGISTERED_ASPECTS_FOR_CLASS, parentCls)
	if aspects is None:
		aspects = {}
	return aspects


def getAspectCls(parentCls: Type, aspectType: AspectType) -> Optional[Type[Aspect]]:
	aspects = getIfKeyIssubclass(_REGISTERED_ASPECTS_FOR_CLASS, parentCls)
	if aspects is None:
		return None
	return aspects.get(aspectType)


@dataclass
class SerializableDataclassWithAspects(SerializableDataclass, Generic[_TAspect]):

	aspects: AspectDict[_TAspect] = field(default_factory=lambda: AspectDict(Aspect), metadata=catMeta(serialize=False))
	unknownAspects: dict[str, Any] = field(default_factory=dict, metadata=catMeta(serialize=False))

	def serializeJson(self, strict: bool, memo: dict, path: tuple[str | int, ...]) -> dict[str, Any]:
		result = super(SerializableDataclassWithAspects, self).serializeJson(strict, memo, path)
		result['aspects'] = self._serializeAspects(strict)
		return result

	def copyFrom(self: _TS, other: _TS) -> None:
		super().copyFrom(other)

		if isinstance(self, SerializableDataclassWithAspects):
			assert isinstance(other, SerializableDataclassWithAspects)
			oldSelfAspects: dict[AspectType, Aspect] = self.aspects._aspects.copy()
			self.aspects._aspects.clear()
			otherAspect: Aspect
			for otherAspect in other.aspects._aspects.copy().values():
				# isinstance(otherAspect, Aspect) check only added to not confuse the type checker.
				assert isinstance(otherAspect, SerializableDataclass) and isinstance(otherAspect, Aspect), "Aspect must be SerializableDataclass in order to be copyable."
				selfAspect = oldSelfAspects.pop(otherAspect.getAspectType(), None)
				assert isinstance(selfAspect, SerializableDataclass)
				if selfAspect is None:
					selfAspect = type(otherAspect)()
				self.aspects.add(selfAspect)
				selfAspect.copyFrom(otherAspect)

			self.unknownAspects = other.unknownAspects.copy()

	def _serializeAspects(self, strict: bool) -> dict[str, Any]:
		result = {}
		result |= self.unknownAspects

		for aspect in self.aspects:
			key = aspect.getAspectType()
			memo = {}
			value = aspect.serializeJson(strict, memo, ('aspects', key,))
			result[key] = value
		return result

	@classmethod
	def fromJSONDict(cls: SerializableDataclassWithAspects, jsonDict: dict[str, dict], memo: dict, path: tuple[str | int, ...], onError: Callable[[Exception, str], None] = None) -> SerializableDataclassWithAspects:
		self = cast(SerializableDataclassWithAspects, super(SerializableDataclassWithAspects, cls).fromJSONDict(jsonDict, memo, path, onError=onError))
		aspectsJson = jsonDict.get('aspects', {}).copy()
		for aspectType, aspectJson in aspectsJson.items():
			self.loadAspectData(aspectType, aspectJson, onError)
		return self

	def loadAspectData(self, aspectType: AspectType, aspectJson: dict[str, dict], onError: Callable[[Exception, str], None] = None):
		aspectCls = self._getAspectCls(aspectType)
		if aspectCls is not None:
			memo = {}
			try:
				newAspect = aspectCls.fromJSONDict(aspectJson, memo, ('aspects', aspectType), onError=onError)
			except Exception as e:
				msg = f"{formatVal(aspectCls)} in {aspectCls.__qualname__}"
				if True and onError is not None:
					onError(e, msg)
					newAspect = None
				else:
					logFatal(msg)
					print(f"FATAL  : {msg}")
					raise
			if newAspect is not None:
				self._setAspect(newAspect)
				return
		self.unknownAspects[aspectType] = aspectJson  # we could not find an appropriate aspect, so, just remember the values

	def _setAspect(self, newAspect: _TAspect) -> None:

		"""
		Adds `newAspect` to `self.aspects`. Override to use a custom behavior.
		:param newAspect: the aspect to be added.
		:return: None
		"""
		self.aspects.add(newAspect)

	def _getAspectCls(self, aspectType: AspectType) -> Optional[Type[_TAspect]]:
		"""
		Returns the Aspect class for the given AspectType or None if there is no such class.
		Default behavior returns classes registered using :func:`registerAspectForType`.
		Override to use a custom behavior.
		:param aspectType: the AspectType
		:return: the class or None.
		"""
		return getAspectCls(type(self), aspectType)
