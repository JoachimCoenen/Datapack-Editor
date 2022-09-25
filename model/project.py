from __future__ import annotations

import functools as ft
import os
from abc import ABC
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import NewType, Type, TypeVar, Optional, Generic, Callable

from Cat.Serializable import SerializableContainer, Serialized, ComputedCached
from Cat.extensions import FilesChangedDependency
from Cat.utils.abc_ import abstractmethod
from Cat.utils.graphs import collectAndSemiTopolSortAllNodes
from Cat.utils.logging_ import logWarning
from model.index import IndexBundle
from model.pathUtils import fileNameFromFilePath, FilePathTpl, getAllFilesFromSearchPath, normalizeDirSeparators
from model.utils import GeneralError, MDStr, Span

_TT = TypeVar('_TT')
_TS = TypeVar('_TS')


@dataclass
class Dependency:
	name: str
	mandatory: bool
	span: Optional[Span] = None


AspectType = NewType('AspectType', str)


@dataclass
class Aspect(ABC):
	parent: Project = field(repr=False)

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
	parent: Project = field(repr=False, compare=False)
	_aspects: dict[AspectType, _TAspect] = field(default_factory=dict, init=False)

	def _get(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		return self._aspects.get(aspectCls.getAspectType())

	def _add(self, aspectCls: Type[_TAspect2]) -> Optional[_TAspect2]:
		"""blindly adds an aspect, possibly overwriting another one. It check the type tho"""
		assert issubclass(aspectCls, getattr(self, '_type'))  # don't confuse the pycharm type checker
		aspect = aspectCls(parent=self.parent)
		self._aspects[aspectCls.getAspectType()] = aspect
		return aspect

	def add(self, aspectCls: Type[_TAspect2]) -> _TAspect2:
		if self._get(aspectCls) is not None:
			raise ValueError(f"Aspect of type {aspectCls.getAspectType()!r} already assigned.")
		return self._add(aspectCls)

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


_ALL_PROJECT_ASPECTS = []


@dataclass
class ProjectAspect(Aspect, ABC):

	@property
	@abstractmethod
	def dependencies(self) -> list[Dependency]:
		""" for now. might change"""

	@abstractmethod
	def analyzeProject(self) -> None:
		pass

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		_ALL_PROJECT_ASPECTS.append(cls)


def buildProjectAspects(p: Project):
	result = AspectDict(ProjectAspect, p)
	for aspectCls in _ALL_PROJECT_ASPECTS:
		result.add(aspectCls)
	return result


_TProjectAspect = TypeVar('_TProjectAspect', bound=ProjectAspect)


@dataclass
class IndexBundleAspect(Aspect, IndexBundle, ABC):
	pass


_TIndexBundle = TypeVar('_TIndexBundle', bound=IndexBundleAspect)


dependencySearchLocations: list[Callable[[], list[str]]] = []
"""search in these directories to resolve dependencies"""


def defaultSearchLocations():
	from settings import applicationSettings
	sl = applicationSettings.minecraft.savesLocation
	if sl:
		return [sl]
	return []

dependencySearchLocations.append(defaultSearchLocations)


class Project(SerializableContainer):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.deepDependencies: list[Project] = []

	path: str = Serialized(default='')
	isArchive: bool = ComputedCached(getInitValue=lambda s: os.path.isfile(s.path), ependencies_=[path])
	aspects: AspectDict[ProjectAspect] = Serialized(getInitValue=buildProjectAspects, shouldSerialize=False)
	indexBundles: AspectDict[IndexBundleAspect] = Serialized(getInitValue=ft.partial(AspectDict, IndexBundleAspect), shouldSerialize=False)

	@property
	def isImmutable(self) -> bool:
		return self.isArchive

	@property
	def isValid(self) -> bool:
		return len(self.path) > 0 and os.path.exists(self.path)

	@property
	def name(self) -> str:
		return fileNameFromFilePath(self.path)

	@property
	def dependencies(self) -> list[Dependency]:
		""" for now. might change"""
		result = {}
		for aspect in self.aspects:
			for dependency in aspect.dependencies:
				if dependency.mandatory or dependency.name not in result:
					result[dependency.name] = dependency
		return list(result.values())

	@ComputedCached()
	def deepDependencies(self) -> list[Project]:
		""" for now. might change"""
		return collectAllDependencies(self)

	_fileSystemChanges: int = FilesChangedDependency(path, '**', shouldSerialize=False)
	_isRebuildingIndices: bool = Serialized(default=False, shouldSerialize=False)

	@ComputedCached(dependencies_=[_fileSystemChanges])
	def files(self) -> list[FilePathTpl]:
		allLocalFiles: list[FilePathTpl] = []
		if self.path.endswith('.jar'):  # we don't need '.class' files. This is not a Java IDE.
			pathInFolder = 'data/**'
			pathInZip = 'data/**'
		else:
			pathInFolder = '/**'
			pathInZip = '/**'
		pif = pathInFolder
		piz = pathInZip

		rawLocalFiles = getAllFilesFromSearchPath(self.path, pif, piz, extensions=tuple(), excludes=None)

		localFiles = []
		for jf in rawLocalFiles:
			if isinstance(jf, tuple):
				localFiles.append(jf)
			else:
				if jf.startswith(self.path):
					localFiles.append((self.path, jf[len(self.path):].lstrip('/')))
				else:
					localFiles.append(jf)
		allLocalFiles.extend(localFiles)
		return allLocalFiles

	def rebuildIndices(self) -> None:
		try:
			self._isRebuildingIndices = True
			for idxBundle in self.indexBundles:
				idxBundle.clear()

			for aspect in self.aspects:
				aspect.analyzeProject()
		finally:
			self._isRebuildingIndices = False

	def addAspect(self, aspectCls: Type[_TProjectAspect]) -> _TProjectAspect:
		return self.aspects.add(aspectCls)

	def getAspect(self, aspectCls: Type[_TProjectAspect]) -> Optional[_TProjectAspect]:
		return self.aspects.get(aspectCls)

	def addIndex(self, indexCls: Type[_TIndexBundle]) -> _TIndexBundle:
		return self.indexBundles.add(indexCls)

	_fileSystemChangesOfCurrentIndex: int = Serialized(default=-2, shouldSerialize=False)

	def _checkIndices(self) -> None:
		if not self._isRebuildingIndices:
			if self._fileSystemChangesOfCurrentIndex != self._fileSystemChanges:
				self._fileSystemChangesOfCurrentIndex = self._fileSystemChanges
				self.rebuildIndices()

	def setdefaultIndex(self, indexCls: Type[_TIndexBundle]) -> _TIndexBundle:
		"""Works similar to dict.setdefault(...)."""
		self._checkIndices()
		return self.indexBundles.setdefault(indexCls)

	def getIndex(self, indexCls: Type[_TIndexBundle]) -> Optional[_TIndexBundle]:
		self._checkIndices()
		return self.indexBundles.get(indexCls)

	def __str__(self):
		return f"<{self.__class__.__name__}({self.name!r})>"


def resolveDependency(dep: Dependency) -> Optional[Project]:
	if '/' in dep.name and os.path.exists(dep.name):
		return Project.create(path=dep.name)
	for dslProvider in dependencySearchLocations:
		dsls = dslProvider()
		for dsl in dsls:
			path = os.path.join(dsl, dep.name)
			if os.path.exists(path):
				return Project.create(path=normalizeDirSeparators(path))
			path = path + '.zip'
			if os.path.exists(path):
				return Project.create(path=normalizeDirSeparators(path))
	return None


def collectAllDependencies(project: Project):
	# just a cache:
	dependencyDict: dict[str, Optional[Project]] = {}
	errorsByProj: dict[str, list[GeneralError]] = defaultdict(list)

	def getDestinations(project: Project) -> list[Project]:
		dependencies = []
		for dep in project.dependencies:
			if dep.name not in dependencyDict:
				dependencyDict[dep.name] = resolveDependency(dep)
			if (depProj := dependencyDict[dep.name]) is not None:
				dependencies.append(depProj)
			else:
				errorsByProj[project.name].append(
					GeneralError(MDStr(f"Missing mandatory dependency '{dep.name}'."), span=dep.span)
					if dep.mandatory else
					GeneralError(MDStr(f"Missing optional dependency '{dep.name}'."), span=dep.span, style='info')
				)
		return dependencies

	allDependencies = collectAndSemiTopolSortAllNodes(project, getDestinations, lambda p: p.name)

	if errorsByProj:
		for projName, errors in errorsByProj.items():
			logWarning(f"Project '{projName}':")
			for error in errors:
				logWarning(error, indentLvl=1)

	return allDependencies


__all__ = [
	'Dependency',
	'AspectType',
	'Aspect',
	'AspectDict',
	'ProjectAspect',
	'IndexBundleAspect',
	'dependencySearchLocations',
	'Project',
]