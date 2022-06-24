from __future__ import annotations

from abc import ABC
from collections import defaultdict
from dataclasses import dataclass, field, fields
from typing import Generic, TypeVar, Hashable, Iterator, Mapping

from model.pathUtils import FilePath

_TT = TypeVar('_TT')
_TV = TypeVar('_TV')
_TK = TypeVar('_TK', bound=Hashable)
_TV_co = TypeVar('_TV_co', covariant=True)
_TK_co = TypeVar('_TK_co', bound=Hashable, covariant=True)


@dataclass
class IndexEntry(Generic[_TK, _TV]):
	key: _TK
	data: _TV
	sources: set[FilePath]


class _ViewBase(Generic[_TT]):
	__slots__ = ('_impl', )

	def __init__(self, impl: Index):
		self._impl: Index = impl

	def __len__(self):
		return len(self._impl.byId)

	def __repr__(self):
		return f'{self.__class__.__name__}({self._impl!r})'


class _ItemsView(_ViewBase[tuple[_TK_co, _TV_co]], Generic[_TK_co, _TV_co]):
	__slots__ = ()

	def __contains__(self, item: tuple[_TK_co, _TV_co]) -> bool:
		key, value = item
		if (entry := self._impl.byId.get(key)) is not None:
			return entry.data is value or entry.data == value
		return False

	def __iter__(self) -> Iterator[tuple[_TK_co, _TV_co]]:
		for key, entry in self._impl.byId.items():
			yield key, entry.data


class _ValuesView(_ViewBase[_TV_co], Generic[_TV_co]):
	__slots__ = ()

	def __contains__(self, value: _TV_co) -> bool:
		for entry in self._impl.byId.values():
			if entry.data == value:
				return True
		return False

	def __iter__(self) -> Iterator[_TV_co]:
		for entry in self._impl.byId.values():
			yield entry.data


class _KeysView(_ViewBase[_TK_co], Generic[_TK_co]):
	__slots__ = ()

	def __contains__(self, key: _TK_co) -> bool:
		return key in self._impl.byId

	def __iter__(self) -> Iterator[_TK_co]:
		return iter(self._impl.byId)


@dataclass
class Index(Mapping[_TK, _TV], Generic[_TK, _TV]):

	byId: dict[_TK, IndexEntry[_TK, _TV]] = field(default_factory=dict)
	bySource: dict[FilePath, dict[_TK, IndexEntry[_TV]]] = field(default_factory=lambda: defaultdict(dict))

	def add(self, key: _TK, source: FilePath, data: _TV) -> _TV:
		entry = self.byId.get(key)
		if entry is None:
			entry = IndexEntry(key, data, set())
			self.byId[key] = entry
		else:
			entry.data = data
		entry.sources.add(source)
		self.bySource[source][key] = entry
		return entry.data

	def discard(self, key: _TK, source: FilePath) -> None:
		entry = self.byId.get(key)
		if entry is not None:
			entry.sources.discard(source)
			if not entry.sources:
				del self.byId[key]

		fromSource = self.bySource.get(source)
		if fromSource is not None:
			entry2 = fromSource.pop(key, None)
			assert entry2 is entry
			if not fromSource:
				del self.bySource[source]

	def discardSource(self, source: FilePath) -> None:
		fromSource = self.bySource.get(source)
		if fromSource is not None:
			for key in fromSource:
				self.discard(key, source)

	def clear(self):
		self.byId.clear()
		self.bySource.clear()

	def __len__(self):
		return len(self.byId)

	def __getitem__(self, key: _TK) -> _TV:
		return self.byId[key].data

	def get(self, key: _TK, default: _TT = None) -> _TV | _TT:
		if (entry := self.byId.get(key)) is not None:
			return entry.data
		return default

	def __contains__(self, key: _TK) -> bool:
		return key in self.byId

	def keys(self) -> _KeysView[_TK]:
		return _KeysView(self)

	def values(self) -> _ValuesView[_TV]:
		return _ValuesView(self)

	def items(self) -> _ItemsView[_TK, _TV]:
		return _ItemsView(self)

	def __iter__(self) -> Iterator[_TK]:
		yield from self.byId


@dataclass
class IndexBundle(ABC):

	@property
	def _subIndices(self) -> Iterator[Index | IndexBundle]:
		for f in fields(self):
			if (dpe := f.metadata.get('dpe')) is None:
				continue
			if dpe.get('isIndex'):
				yield getattr(self, f.name)

	def clear(self) -> None:
		for idx in self._subIndices:
			idx.clear()

	def discardSource(self, source: FilePath) -> None:
		for idx in self._subIndices:
			idx.discardSource(source)


__all__ = [
	"Index",
	"IndexBundle",
]
