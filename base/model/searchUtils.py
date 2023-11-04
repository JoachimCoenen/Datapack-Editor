from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Callable, cast, Collection, Generic, Iterable, Iterator, Mapping, Optional, overload, TypeVar

from recordclass import as_dataclass

from cat.utils import first


_TT = TypeVar('_TT')


@overload
def autocompleteFromList(text: str, allChoices: Iterable[str]) -> str:
	pass


@overload
def autocompleteFromList(text: str, allChoices: Iterable[_TT], getStr: Callable[[_TT], str]) -> str:
	pass


def autocompleteFromList(text: str, allChoices: Iterable[Any], getStr: Callable[[Any], str] = None) -> str:
	searchStr = text.lower()
	if getStr is not None:
		lowerChoices = [(getStr(c).lower(), c) for c in allChoices]
	else:
		lowerChoices = [(c.lower(), c) for c in allChoices]

	searchStrIndices = [cl.find(searchStr) for cl, c in lowerChoices]
	filteredChoices = [(i, cl[i:], c) for i, (cl, c) in zip(searchStrIndices, lowerChoices) if i >= 0]
	loweredFilteredChoices = [cl for i, cl, c in filteredChoices]

	prefix = os.path.commonprefix(loweredFilteredChoices)
	if prefix:
		firstFilteredChoice = first(filteredChoices, (0, '', ''))
		start = firstFilteredChoice[0]
		end = start + len(prefix)
		prefix = firstFilteredChoice[2][start:end]
		text = prefix
	return text


# FilterStr = NewType('FilterStr', str)
# @ft.total_ordering
class FilterStr:
	def __init__(self, string: str, isRegex: bool):
		self.__string: str = string
		self.__filters: tuple[str, ...] = tuple(filter(None, map(str.strip, string.lower().split('|'))))
		self.__iter__ = self.__filters.__iter__  # speedup of call to iter(filterStr)

		self.__isRegex: bool = isRegex
		self.__pattern: Optional[re.Pattern[str]] = None
		self.__regexError: Optional[re.error] = None
		if isRegex:
			try:
				self.__pattern = re.compile(string)
			except re.error as error:
				self.__regexError = error

	@property
	def string(self) -> str:
		return self.__string

	@property
	def filters(self) -> tuple[str, ...]:
		return self.__filters

	@property
	def isRegex(self) -> bool:
		return self.__isRegex

	@property
	def pattern(self) -> Optional[re.Pattern]:
		return self.__pattern

	@property
	def regexError(self) -> Optional[re.error]:
		return self.__regexError

	def matches(self, text: str) -> bool:
		if self.__isRegex:
			return self.__pattern is not None and self.__pattern.search(text) is not None
		else:
			text = text.lower()
			return any(f in text for f in self.__filters)

	def matchesAny(self, text: Iterable[str]) -> bool:
		if self.__isRegex:
			return self.__pattern is not None and any(self.__pattern.search(t) is not None for t in text)
		else:
			return any(f in t for t in map(str.lower, text) for f in self.__filters)

	@property
	def matcher(self) -> Callable[[str], bool]:
		if self.__isRegex:
			if (pattern := self.__pattern) is not None:
				return cast(Callable[[str], bool], pattern.search)
			else:
				return lambda x: False
		else:
			filters = self.__filters
			if len(filters) == 0:
				return lambda x: True
			elif len(filters) == 1:
				f = filters[0]
				return lambda choice: f in choice.lower()
			else:
				def search(choice: str):
					choice = choice.lower()
					return any(f in choice for f in filters)
				return search

	def filter(self, collection: Collection[str]) -> tuple[int, int, Collection[str]]:
		if not self:
			result = list(collection)
		else:
			result = list(filter(self.matcher, collection))
		return len(collection), len(result), result

	def filterValuesByKey(self, mapping: Mapping[str, _TT]) -> tuple[int, int, Collection[_TT]]:
		if not self:
			result = mapping.values()
		else:
			search = self.matcher
			result = [value for key, value in mapping.items() if search(key)]
		return len(mapping), len(result), result

	def filterItemsByKey(self, mapping: Mapping[str, _TT]) -> tuple[int, int, Collection[tuple[str, _TT]]]:
		if not self:
			result = mapping.items()
		else:
			search = self.matcher
			result = [item for item in mapping.items() if search(item[0])]
		return len(mapping), len(result), result

	def filterByTransformed(self, collection: Collection[_TT], trafo: Callable[[_TT], str]) -> tuple[int, int, Collection[_TT]]:
		if not self:
			result = list(collection)
		else:
			search = self.matcher
			result = [choice for choice in collection if search(trafo(choice))]
		return len(collection), len(result), result

	def __str__(self) -> str:
		return self.__string

	def __repr__(self) -> str:
		return f"{type(self).__name__}({self.__string!r}, isRegex={self.__isRegex})"

	def __eq__(self, other: Any) -> bool:
		if isinstance(other, FilterStr):
			return self.__isRegex is other.__isRegex and self.__string == other.__string
			# if self.__isRegex is not other.__isRegex:
			# 	return False
			# return self.__filters == other.__filters if not self.__isRegex else self.__string == other.__string
		else:
			return False

	def __iter__(self) -> Iterator[str]:
		return self.__filters.__iter__()

	def __bool__(self) -> bool:
		return any(self.__filters)


def filterStrChoices(filterStr: FilterStr, allChoices: Collection[str]) -> tuple[int, int, Collection[str]]:
	return filterStr.filter(allChoices)
	# return [choice for choice in allChoices if filterStr.matches(choice)]
	# return [choice[1] for choice in ((choice.lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]


# def filterDictChoices(filterStr: FilterStr, allChoices: Mapping[str, _TT]) -> Collection[_TT]:
# 	if not filterStr:
# 		return list(allChoices.values())
# 	return filterStr.filterValuesByKey(allChoices)
# 	# return [value for key, value in allChoices.items() if filterStr.matches(key)]
# 	# return [choice[1] for choice in ((key.lower(), value) for key, value in allChoices.items()) if any(f in choice[0] for f in filterStr)]
#
#
# def filterDictItemChoices(filterStr: FilterStr, allChoices: Mapping[str, _TT]) -> Collection[tuple[str, _TT]]:
# 	if not filterStr:
# 		return list(allChoices.items())
# 	return filterStr.filterItemsByKey(allChoices)


def filterComputedChoices(getStr: Callable[[_TT], str]) -> Callable[[FilterStr, Collection[_TT]], tuple[int, int, Collection[_TT]]]:
	def innerFilterComputedChoices(filterStr: FilterStr, allChoices: Collection[_TT]) -> tuple[int, int, Collection[_TT]]:
		return filterStr.filterByTransformed(allChoices, getStr)
	return innerFilterComputedChoices


def filterAnyComputedChoices(getStrs: Callable[[_TT], tuple[str, ...]]) -> Callable[[FilterStr, Collection[_TT]], Collection[_TT]]:
	def innerFilterComputedChoices(filterStr: FilterStr, allChoices: Collection[_TT]) -> Collection[_TT]:
		if not filterStr:
			return allChoices
		return [
			choice[1]
			for choice in (
				((s.lower() for s in getStrs(choice)), choice)
				for choice in allChoices
			)
			if any(filterStr.matches(s) for s in choice[0])]
		# return [choice[1] for choice in (((s.lower() for s in getStrs(choice)), choice) for choice in allChoices) if any(f in s for f in filterStr for s in choice[0])]
	return innerFilterComputedChoices


# ########################################################################################
# FuzzySearch: ###########################################################################
# ########################################################################################


SplitStrs = list[tuple[int, str]]


@as_dataclass()
class SplitStrsItem(Generic[_TT]):
	""""""
	value: _TT
	splitStrs: SplitStrs


@as_dataclass()
class SearchTerms:
	searchTerm: str
	subTerms: list[tuple[int, str]]
	lowerSubTerms: list[str]


@as_dataclass()
class FuzzyMatch:
	indices: list[tuple[int, slice]]  # = field(default_factory=list)
	matchQuality: tuple[float, float]  # = (fullMatches / partsCnt, partialMatches / partsCnt)

	@property
	def anyMatch(self) -> bool:
		return bool(self.indices)


@as_dataclass()
class SearchResult(Generic[_TT]):
	fe: _TT
	aMatch: FuzzyMatch  # = field(compare=False)

	def __class_getitem__(cls, params):
		return cls

	def __eq__(self, other):
		if type(other) is not SearchResult:
			return False
		return self.fe == other.fe

	def __ne__(self, other):
		if type(other) is not SearchResult:
			return True
		return self.fe != other.fe


@dataclass
class SearchResults(Generic[_TT]):
	searchTerm: str
	results: list[SearchResult[_TT]]


def splitStringForSearch(string: str) -> SplitStrs:
	# subTerms = [st for st in re.split(r'(?=[^a-z0-9])', string.strip())]
	# subTerms = [st.lower() for st in re.split(r'(?=[A-Z])|\b', string.strip()) if st]

	subTerms: SplitStrs = []
	idx = 0
	for i, st in enumerate(re.split(r'((?=[A-Z])|[\W_]+)', string.strip())):
		if st:
			if i % 2 == 0:  # we don't have a separator:
				subTerms.append((idx, st.lower()))
			idx += len(st)

	return subTerms


def getSearchTerms(searchTerm: str) -> SearchTerms:
	subTerms = splitStringForSearch(searchTerm)
	lowerSubTerms = [s[1].lower() for s in subTerms]
	return SearchTerms(searchTerm, subTerms, lowerSubTerms)


def getFuzzyMatch(searchTerms: SearchTerms, string: str, *, strict: bool) -> Optional[FuzzyMatch]:
	lastIndex: int = 0
	indices = []
	lowerString = string.lower()

	for i, st in enumerate(searchTerms.lowerSubTerms):
		index = lowerString.find(st, lastIndex)
		if index < 0:
			if strict:
				return None
		else:
			lastIndex = index + len(st)
			indices.append((i, slice(index, lastIndex)))

	return FuzzyMatch(indices, (.5, .5))


def getFuzzyMatch2(allSearchTerms: SearchTerms, splitStrs: SplitStrs) -> Optional[FuzzyMatch]:
	if not allSearchTerms.lowerSubTerms:
		return FuzzyMatch([], (0, 0))

	indices: list[tuple[int, slice]] = []
	fullMatchCount: int = 0
	partialMatchCount: int = 0

	splitStrsLen = len(splitStrs)
	splitIdx = 0

	searchTerms = allSearchTerms.lowerSubTerms
	searchTermsLen = len(searchTerms)
	stIdx = 0
	st: str = searchTerms[stIdx]
	while stIdx < searchTermsLen and splitIdx < splitStrsLen:
		splitStartIdx, subStr = splitStrs[splitIdx]
		if st.startswith(subStr):
			oldStartIdx = splitStartIdx
			oldSplitIdx = splitIdx
			while True:
				fullMatchCount += 1
				splitIdx += 1
				if splitIdx >= splitStrsLen:
					break
				idxInSt = len(subStr)
				splitStartIdx, subStr = splitStrs[splitIdx]
				st = st[idxInSt:]
				if not st or not st.startswith(subStr):
					break
			if st:  # we have some leftovers:
				if subStr.startswith(st):  # leftovers could be matched:
					partialMatchCount += 1
					indices.append((stIdx, slice(oldStartIdx, splitStartIdx)))
					splitIdx += 1
					stIdx += 1
					if stIdx < searchTermsLen:
						st = searchTerms[stIdx]
						continue
					else:
						break
				else:  # leftovers couldn't be matched, so do a rollback:
					splitIdx = oldSplitIdx + 1  # bc. splitStrs[splitIdx] was a failure
					st = searchTerms[stIdx]
					continue
			else:  # we have NO leftovers:
				indices.append((stIdx, slice(oldStartIdx, splitStartIdx)))
				stIdx += 1
				if stIdx < searchTermsLen:
					st = searchTerms[stIdx]
					continue
				else:
					break
		elif subStr.startswith(st):
			partialMatchCount += 1
			indices.append((stIdx, slice(splitStartIdx, splitStartIdx + len(st))))
			splitIdx += 1
			stIdx += 1
			if stIdx < searchTermsLen:
				st = searchTerms[stIdx]
				continue
			else:
				break
			pass
		else:
			splitIdx += 1

	if stIdx < searchTermsLen:
		return None

	# assert len(indices) == len(searchTerms)
	assert stIdx == len(searchTerms)
	return FuzzyMatch(indices, (fullMatchCount / splitStrsLen, partialMatchCount / splitStrsLen))


def _performFuzzySearch(allChoices: Iterable[_TT], searchTerms: SearchTerms, getSplitStr: Callable[[_TT], SplitStrs]) -> SearchResults[_TT]:
	searchResults: list[SearchResult[_TT]] = []
	for fe in allChoices:
		match = getFuzzyMatch2(searchTerms, getSplitStr(fe))
		if match is not None:
			searchResults.append(SearchResult(fe, match))
	return SearchResults(searchTerms.searchTerm, searchResults)


def performFuzzySearch(allChoices: Iterable[_TT], searchTerm: str, getSplitStr: Callable[[_TT], SplitStrs]) -> SearchResults[_TT]:
	searchTerms = getSearchTerms(searchTerm)
	searchResults = _performFuzzySearch(allChoices, searchTerms, getSplitStr)
	searchResults.results.sort(key=lambda x: x.aMatch.matchQuality, reverse=True)
	return searchResults


# def getStrSplitChoices(allChoices: Iterable[str]) -> list[SplitStrs]:
# 	return [SplitStrs(choice, splitStringForSearch(choice)) for choice in allChoices]
#
#
# def getComputedSplitChoices(allChoices: Iterable[_TT], getStr: Callable[[_TT], str]) -> list[SplitStrsItem[_TT]]:
# 	return [SplitStrs(choice, splitStringForSearch(getStr(choice))) for choice in allChoices]


def performFuzzyStrSearch(allChoices: Iterable[str], searchTerm: str) -> SearchResults[str]:
	return performFuzzySearch(allChoices, searchTerm, splitStringForSearch)


def performFuzzyComputedSearch(allChoices: Iterable[_TT], searchTerm: str, getStr: Callable[[_TT], str]) -> SearchResults[_TT]:
	return performFuzzySearch(allChoices, searchTerm, lambda choice: splitStringForSearch(getStr(choice)))


__all__ = [
	'autocompleteFromList',
	'FilterStr',
	'filterStrChoices',
	# 'filterDictChoices',
	'filterComputedChoices',
	'filterAnyComputedChoices',

	'SplitStrs',
	'SearchTerms',
	'FuzzyMatch',
	'SearchResult',
	'SearchResults',

	'splitStringForSearch',
	'getSearchTerms',

	'getFuzzyMatch',
	'getFuzzyMatch2',

	'performFuzzySearch',
	'performFuzzyStrSearch',

	# 'getStrSplitChoices',
	# 'getComputedSplitChoices',
]
