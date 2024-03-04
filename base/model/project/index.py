from __future__ import annotations

from abc import ABC
from collections import defaultdict
from dataclasses import dataclass, field, fields
from typing import Collection, Generic, TypeVar, Hashable, Iterator, Mapping, Optional

from recordclass import as_dataclass

from base.model.pathUtils import FilePathTpl
from cat.utils import CachedProperty
from cat.utils.typing_ import SupportsItems

_TT = TypeVar('_TT')
_TD = TypeVar('_TD')
_TV = TypeVar('_TV')
_TK = TypeVar('_TK', bound=Hashable)
_TV_co = TypeVar('_TV_co', covariant=True)
_TK_co = TypeVar('_TK_co', bound=Hashable, covariant=True)
_TCol = TypeVar('_TCol', bound=Collection)


@as_dataclass()
class IndexEntry(Generic[_TK, _TV]):
	key: _TK
	data: _TV
	sources: set[FilePathTpl]


class IndexLike(Mapping[_TK, _TV], Generic[_TK, _TV], ABC):
	def add(self, key: _TK, source: FilePathTpl, data: _TV) -> _TV:
		...

	def discard(self, key: _TK, source: FilePathTpl) -> Optional[_TV]:
		"""returns the value if it is still remaining in the index (i.e. if there are other sources still present.). Returns None if it was removed or never existed."""
		...

	def discardSource(self, source: FilePathTpl) -> None:
		...

	def discardDirectory(self, source: FilePathTpl) -> None:
		...

	def clear(self) -> None:
		...


@dataclass
class Index(IndexLike[_TK, _TV], Generic[_TK, _TV]):

	byKey: dict[_TK, IndexEntry[_TK, _TV]] = field(default_factory=dict)
	bySource: dict[FilePathTpl, dict[_TK, IndexEntry[_TK, _TV]]] = field(default_factory=lambda: defaultdict(dict))

	def add(self, key: _TK, source: FilePathTpl, data: _TV) -> _TV:
		entry = self.byKey.get(key)
		if entry is None:
			entry = IndexEntry(key, data, set())
			self.byKey[key] = entry
		else:
			entry.data = data
		entry.sources.add(source)
		self.bySource[source][key] = entry
		return data

	def addAll(self, other: SupportsItems[_TK, _TV], source: FilePathTpl) -> None:
		"""
		corresponds to MutableMapping.update(...), but this name seems more appropriate, as we perform an Index.add(...) for each entry in the given Mapping.
		"""
		for key, data in other.items():
			self.add(key, source, data)

	def update(self, other: SupportsItems[_TK, _TV], source: FilePathTpl) -> None:
		self.addAll(other, source)

	def discard(self, key: _TK, source: FilePathTpl) -> Optional[_TV]:
		entry = self.byKey.get(key)
		if entry is None:
			return None

		fromSource = self.bySource.get(source)
		if fromSource is not None:
			entry2 = fromSource.pop(key, None)
			assert entry2 is entry
			if not fromSource:
				del self.bySource[source]

		entry.sources.discard(source)
		if not entry.sources:
			del self.byKey[key]
		else:
			return entry.data

	def discardSource(self, source: FilePathTpl) -> None:
		fromSource = self.bySource.get(source)
		if fromSource is not None:
			fromSource = fromSource.copy()
			for key in fromSource:
				if (remaining := self.discard(key, source)) is not None and callable(discardSource := getattr(remaining, 'discardSource', None)):
					discardSource(source)

	def discardDirectory(self, directory: FilePathTpl) -> None:
		for source, entries in self.bySource.copy().items():
			if source[0] == directory[0] and source[1].startswith(directory[1]):
				for key in entries.copy().keys():
					if (remaining := self.discard(key, source)) is not None and callable(discardSource := getattr(remaining, 'discardSource', None)):
						discardSource(source)

	def clear(self) -> None:
		self.byKey.clear()
		self.bySource.clear()

	def __len__(self) -> int:
		return len(self.byKey)

	def __getitem__(self, key: _TK) -> _TV:
		return self.byKey[key].data

	def get(self, key: _TK, default: _TD = None) -> _TV | _TD:
		if (entry := self.byKey.get(key)) is not None:
			return entry.data
		return default

	def __contains__(self, key: _TK) -> bool:
		return key in self.byKey

	def keys(self) -> _KeysView[_TK, Index]:
		return _KeysView(self)

	def values(self) -> _IndexValuesView[_TV]:
		return _IndexValuesView(self)

	def items(self) -> _IndexItemsView[_TK, _TV]:
		return _IndexItemsView[_TK, _TV](self)

	def __iter__(self) -> Iterator[_TK]:
		return iter(self.byKey)


@dataclass
class IndexBundle(ABC):

	@CachedProperty
	def subIndicesByName(self) -> dict[str, Index | IndexBundle]:
		indices = {}
		for f in fields(self):
			if (dpe := f.metadata.get('dpe')) is None:
				continue
			if dpe.get('isIndex'):
				indices[f.name] = getattr(self, f.name)
		return indices

	def clear(self) -> None:
		for idx in self.subIndicesByName.values():
			idx.clear()

	def discardSource(self, source: FilePathTpl) -> None:
		for idx in self.subIndicesByName.values():
			idx.discardSource(source)

	def discardDirectory(self, source: FilePathTpl) -> None:
		for idx in self.subIndicesByName.values():
			idx.discardDirectory(source)


@dataclass
class DeepIndex(IndexLike[tuple[str, _TK], _TV], Generic[_TK, _TV]):

	indices: defaultdict[str, Index[_TK, _TV]] = field(default_factory=lambda: defaultdict(Index))

	def add(self, key: tuple[str, _TK], source: FilePathTpl, data: _TV) -> _TV:
		return self.indices[key[0]].add(key[1], source, data)

	def discard(self, key: tuple[str, _TK], source: FilePathTpl) -> Optional[_TV]:
		if (index := self.indices.get(key[0])) is not None:
			result = index.discard(key[1], source)
			if not index:
				del self.indices[key[0]]
			return result
		return None

	def discardSource(self, source: FilePathTpl) -> None:
		for key0, index in list(self.indices.items()):
			index.discardSource(source)
			if not index:
				del self.indices[key0]

	def discardDirectory(self, source: FilePathTpl) -> None:
		for key0, index in list(self.indices.items()):
			index.discardDirectory(source)
			if not index:
				del self.indices[key0]

	def clear(self) -> None:
		self.indices.clear()

	def __len__(self) -> int:
		return sum(map(len, self.indices))

	def __getitem__(self, key: tuple[str, _TK]) -> _TV:
		if (index := self.indices.get(key[0])) is not None:
			return index[key[1]]
		raise KeyError(key)

	def get(self, key: tuple[str, _TK], default: _TD = None) -> _TV | _TD:
		if (index := self.indices.get(key[0])) is not None:
			return index.get(key[1], default)
		return default

	def getIndex(self, path: str) -> Index[_TK, _TT]:
		return self.indices[path]

	def __contains__(self, key: tuple[str, _TK]) -> bool:
		if (index := self.indices.get(key[0])) is not None:
			return key[1] in index
		return False

	def keys(self) -> _KeysView[tuple[str, _TK], DeepIndex]:
		return _KeysView(self)

	def values(self) -> _DeepIndexValuesView[_TV]:
		return _DeepIndexValuesView(self)

	def items(self) -> _DeepIndexItemsView[_TK, _TV]:
		return _DeepIndexItemsView[_TK, _TV](self)

	def __iter__(self) -> Iterator[_TK]:
		for path, index in self.indices.keys():
			for key in index.byKey.keys():
				yield path, key


class _ViewBase(Generic[_TT, _TCol]):
	__slots__ = ('_impl', )

	def __init__(self, impl: _TCol):
		self._impl: _TCol = impl

	def __len__(self) -> int:
		return len(self._impl)

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({self._impl!r})'


class _IndexItemsView(_ViewBase[tuple[_TK_co, _TV_co], Index], Generic[_TK_co, _TV_co]):
	def __contains__(self, item: tuple[_TK_co, _TV_co]) -> bool:
		key, value = item
		if (entry := self._impl.byKey.get(key)) is not None:
			return entry.data is value or entry.data == value
		return False

	def __iter__(self) -> Iterator[tuple[_TK_co, _TV_co]]:
		for key, entry in self._impl.byKey.copy().items():
			yield key, entry.data


class _DeepIndexItemsView(_ViewBase[tuple[tuple[str, _TK_co], _TV_co], DeepIndex], Generic[_TK_co, _TV_co]):
	def __contains__(self, item: tuple[tuple[str, _TK_co], _TV_co]) -> bool:
		key, value = item
		if (entry := self._impl.get(key)) is not None:
			return entry.data is value or entry.data == value
		return False

	def __iter__(self) -> Iterator[tuple[tuple[str, _TK_co], _TV_co]]:
		for path, index in self._impl.indices.copy().items():
			for key, entry in index.byKey.copy().items():
				yield (path, key), entry.data


class _IndexValuesView(_ViewBase[_TV_co, Index], Generic[_TV_co]):
	def __contains__(self, value: _TV_co) -> bool:
		for entry in self._impl.byKey.copy().values():
			if entry.data == value:
				return True
		return False

	def __iter__(self) -> Iterator[_TV_co]:
		for entry in self._impl.byKey.copy().values():
			yield entry.data


class _DeepIndexValuesView(_ViewBase[_TV_co, DeepIndex], Generic[_TV_co]):
	def __contains__(self, value: _TV_co) -> bool:
		for index in self._impl.indices.copy().values():
			if value in index.values():
				return True
		return False

	def __iter__(self) -> Iterator[_TV_co]:
		for index in self._impl.indices.values():
			yield from index.values()


class _KeysView(_ViewBase[_TK, _TCol], Generic[_TK, _TCol]):
	def __contains__(self, key: _TK) -> bool:
		return key in self._impl

	def __iter__(self) -> Iterator[_TK]:
		return iter(self._impl)


__all__ = [
	"IndexLike",
	"Index",
	"IndexBundle",
	"DeepIndex",
]
