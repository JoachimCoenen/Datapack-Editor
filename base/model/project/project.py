from __future__ import annotations

import os
from abc import ABC
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, ClassVar

from Cat.Serializable.dataclassJson import SerializableDataclass, catMeta
from Cat.utils.graphs import collectAndSemiTopolSortAllNodes
from Cat.utils.logging_ import logWarning
from base.model.project.index import IndexBundle
from base.model.pathUtils import FilePath, FilePathTpl, FilePathStr, normalizeDirSeparatorsStr
from base.model.aspect import AspectDict, Aspect
from base.model.utils import Span, GeneralError, MDStr, SemanticsError


def _fillProjectAspects(aspectsDict: AspectDict):
	from base.plugin import PLUGIN_SERVICE
	for plugin in PLUGIN_SERVICE.activePlugins:
		for aspectCls in plugin.projectAspects():
			aspectsDict.add(aspectCls)


@dataclass
class Project(SerializableDataclass, ABC):
	name: str = 'new Project'
	path: FilePath = ''  # save path for the project, might also be usd for git, etc.
	roots: list[ProjectRoot] = field(default_factory=list)
	deepDependencies: list[Root] = field(default_factory=list, metadata=catMeta(serialize=False))
	"""all dependencies recursively, excluding all ProjectRoots."""
	# projectSettings: ProjectSettings
	aspects: AspectDict[ProjectAspect] = field(default_factory=lambda: AspectDict(ProjectAspect), metadata=catMeta(serialize=False))

	@property
	def isValid(self) -> bool:
		return len(self.path) > 0 and os.path.exists(self.path)

	@property
	def isEmpty(self) -> bool:
		return not self.roots

	@property
	def allRoots(self) -> list[Root]:
		return self.roots + self.deepDependencies

	def resolveDependencies(self):
		self.deepDependencies = resolveDependencies(self)

	def insertRoot(self, idx: int, root: ProjectRoot):
		self.roots.insert(idx, root)
		for aspect in self.aspects:
			aspect.onRootAdded(root, self)
		self.analyzeRoot(root)

	def addRoot(self, root: ProjectRoot):
		self.insertRoot(len(self.roots), root)

	def removeRoot(self, root: ProjectRoot):
		self.roots.remove(root)
		for aspect in self.aspects:
			aspect.onRootRemoved(root, self)

	def analyzeRoots(self):
		aspects = [a for a in self.aspects if a.aspectFeatures.analyzeRoots]
		for projRoot in self.roots:
			self.analyzeRoot(projRoot, aspects)

	def analyzeDependencies(self):
		aspects = [a for a in self.aspects if a.aspectFeatures.analyzeRoots]
		for dependency in self.deepDependencies:
			self.analyzeRoot(dependency, aspects)

	def analyzeRoot(self, root: Root, aspects: list[ProjectAspect] = ...):
		if aspects is ...:
			aspects = [a for a in self.aspects if a.aspectFeatures.analyzeRoots]
		for idxBundle in root.indexBundles:
			idxBundle.clear()
		for a in aspects:
			a.analyzeRoot(root)

	def setup(self):
		""" only call once!"""
		_fillProjectAspects(self.aspects)
		roots = self.roots
		self.roots = []
		for root in roots:
			self.addRoot(root)
		self.resolveDependencies()
		self.analyzeDependencies()

	def close(self):
		""" only call once!"""
		roots = self.roots.copy()
		for root in roots:
			self.removeRoot(root)


def resolveDependencies(project: Project):
	aspects = [a for a in project.aspects if a.aspectFeatures.dependencies]

	# just a cache:
	dependencyDict: dict[str, Optional[Root]] = {}
	# seenDependencies: set[str] = set()
	errorsByRoot: dict[str, list[GeneralError]] = defaultdict(list)

	def getDestinations(root: Root) -> list[Root]:
		dependencies = []
		for aspect in aspects:
			aDependencies = aspect.getDependencies(root)
			root.dependencies = aDependencies
			for dep in aDependencies:
				# seenDependencies.add(dep.identifier)
				# root.dependencies.append(dep)
				if dep.identifier not in dependencyDict:
					dep.resolved = aspect.resolveDependency(dep)
				else:
					dep.resolved = dependencyDict[dep.identifier]
				if dep.resolved is not None:
					dependencyDict[dep.identifier] = dep.resolved
					dependencies.append(dep.resolved)
				else:
					errorsByRoot[root.name].append(
						SemanticsError(MDStr(f"Missing mandatory dependency '{dep.name}'."), span=dep.span)
						if dep.mandatory else
						SemanticsError(MDStr(f"Missing optional dependency '{dep.name}'."), span=dep.span, style='info')
					)
		return dependencies

	projectRoots: list[Root] = project.roots
	deepDependencies = collectAndSemiTopolSortAllNodes(projectRoots, getDestinations, lambda p: p.name)
	projectRootNames = {root.name for root in projectRoots}
	deepDependencies = [dep for dep in deepDependencies if dep.name not in projectRootNames]  # remove project roots.

	if errorsByRoot:
		for rootName, errors in errorsByRoot.items():
			logWarning(f"Project '{rootName}':")
			for error in errors:
				logWarning(str(error), indentLvl=1)

	return deepDependencies


@dataclass(slots=True)
class DependencyDescr:
	name: str  # used for displaying
	identifier: str  # used for unique identification, of the root (i.e. two DependencyDescr objects with the same identifier ALWAYS point o the same Root.
	mandatory: bool
	span: Optional[Span] = None
	resolved: Optional[Root] = None


@dataclass
class IndexBundleAspect(Aspect, IndexBundle, ABC):
	pass


@dataclass(kw_only=True)
class AspectFeatures:
	dependencies: bool = False
	"""
	def getDependencies(self, root: Root) -> list[DependencyDescr]: ...
	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]: ...
	"""
	analyzeRoots: bool = False
	"""
	def analyzeRoot(self, root: Root) -> None: ...
	def onRootRenamed(self, root: Root, project: Project, oldName: str, newName: str) -> None: ...
	"""
	analyzeFiles: bool = False
	"""
	def analyzeFile(self, root: Root, path: FilePathTpl) -> None: ...
	"""


@dataclass
class ProjectAspect(Aspect, ABC):
	aspectFeatures: ClassVar[AspectFeatures]

	def __init_subclass__(cls, *, features: AspectFeatures = None, **kwargs):
		super().__init_subclass__(**kwargs)
		if features is None:
			# maybe use a warning here?
			raise TypeError(f"ProjectAspect '{cls.__name__}' does not define its features. use the 'features' keyword argument to define the available features of a ProjectAspect:\n"
							f"    class {cls.__name__}(ProjectAspect, features=AspectFeatures(analyzeProject=True, ...)):\n"
							f"        ...")
		cls.aspectFeatures = features

	def getDependencies(self, root: Root) -> list[DependencyDescr]:
		"""
		for now. might change.
		enabled with: class MyAspect(Aspect, features=AspectFeatures(dependencies=True)): ...
		"""
		pass

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		"""
		for now. might change.
		enabled with: class MyAspect(Aspect, features=AspectFeatures(dependencies=True)): ...
		"""
		pass

	def analyzeRoot(self, root: Root) -> None:
		"""
		enabled with: class MyAspect(Aspect, features=AspectFeatures(analyzeRoots=True)): ...
		"""
		pass

	def onRootRenamed(self, root: Root, oldName: str, newName: str) -> None:
		"""
		enabled with: class MyAspect(Aspect, features=AspectFeatures(analyzeRoots=True)): ...
		"""
		pass

	def onRootAdded(self, root: Root, project: Project) -> None:
		"""
		enabled with: <always enabled>
		"""
		pass

	def onRootRemoved(self, root: Root, project: Project) -> None:
		"""
		enabled with: <always enabled>
		"""
		pass

	def analyzeFile(self, root: Root, path: FilePathTpl) -> None:
		"""
		enabled with: class MyAspect(Aspect, features=AspectFeatures(analyzeFiles=True)): ...
		"""
		pass


@dataclass
class Root(SerializableDataclass):
	_name: str = field(metadata=catMeta(serializedName='name'))
	_location: str  # =FilePathStr  # maybe?
	dependencies: list[DependencyDescr] = field(default_factory=list, metadata=catMeta(serialize=False))
	indexBundles: AspectDict[IndexBundleAspect] = field(default_factory=lambda: AspectDict(IndexBundleAspect), metadata=catMeta(serialize=False))

	@property
	def location(self) -> str:
		return self._location

	@property
	def normalizedLocation(self) -> FilePathStr:
		return normalizeDirSeparatorsStr(self.location).rstrip('/')

	@property
	def name(self) -> str:
		return self._name

	@name.setter
	def name(self, newName: str):
		oldName = self._name
		if oldName != newName:
			from base.model.session import getSession
			for aspect in getSession().project.aspects:
				if aspect.aspectFeatures.analyzeRoots:
					aspect.onRootRenamed(self, oldName, newName)
		self._name = newName


@dataclass
class ProjectRoot(Root):
	pass
