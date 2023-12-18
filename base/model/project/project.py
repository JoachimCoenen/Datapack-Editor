from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar, final

from recordclass import as_dataclass

from base.model.searchUtils import SplitStrs, splitStringForSearch
from cat.GUI import propertyDecorators as pd
from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.utils.graphs import collectAndSemiTopolSortAllNodes
from cat.utils.logging_ import logWarning
from base.model.project.index import IndexBundle
from base.model.pathUtils import FilePathTpl, FilePathStr, normalizeDirSeparatorsStr, ArchiveFilePool
from base.model.aspect import AspectDict, Aspect, SerializableDataclassWithAspects
from base.model.utils import Span, GeneralError, MDStr, SemanticsError, NULL_SPAN


def _fillProjectAspects(aspectsDict: AspectDict):
	from base.plugin import PLUGIN_SERVICE
	for plugin in PLUGIN_SERVICE.activePlugins:
		for aspectCls in plugin.projectAspects():
			aspectsDict.setdefault(aspectCls)


_TProjectAspect = TypeVar('_TProjectAspect', bound='ProjectAspect')


@dataclass
class ProjectAspectPart(Generic[_TProjectAspect], ABC):
	"""
	todo: description for ProjectAspectPart
	"""
	aspect: _TProjectAspect


@dataclass
class DependenciesAspectPart(ProjectAspectPart[_TProjectAspect], Generic[_TProjectAspect], ABC):

	@abstractmethod
	def preResolveDependencies(self, project: Project) -> None:
		"""
		called once for a project, just before all dependencies are resolved (.getDependencies(...) and .resolveDependency(...) for all roots & dependencies)
		"""
		pass

	@abstractmethod
	def getDependencies(self, root: Root, project: Project) -> list[DependencyDescr]:
		"""
		for now. might change.
		"""
		return []

	@abstractmethod
	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		"""
		for now. might change.
		"""
		pass

	@abstractmethod
	def postResolveDependencies(self, project: Project) -> None:
		"""
		called once for a project, just after all dependencies were resolved (.getDependencies(...) and .resolveDependency(...) for all roots & dependencies)
		"""
		pass


@dataclass
class AnalyzeRootsAspectPart(ProjectAspectPart[_TProjectAspect], Generic[_TProjectAspect], ABC):

	@abstractmethod
	def analyzeRoot(self, root: Root, project: Project) -> None:
		pass

	@abstractmethod
	def onRootRenamed(self, root: Root, oldName: str, newName: str) -> None:
		pass

	@abstractmethod
	def onRootAdded(self, root: Root, project: Project) -> None:
		pass

	@abstractmethod
	def onRootRemoved(self, root: Root, project: Project) -> None:
		pass


@dataclass
class AnalyzeFilesAspectPart(ProjectAspectPart[_TProjectAspect], Generic[_TProjectAspect], ABC):

	@abstractmethod
	def analyzeFile(self, root: Root, fileEntry: FileEntry, pool: ArchiveFilePool) -> None:
		pass


@dataclass
class ProjectAspect(Aspect, SerializableDataclass, ABC):

	dependenciesPart: Optional[DependenciesAspectPart] = field(default=None, init=False, metadata=catMeta(serialize=False, decorators=[pd.NoUI()]))
	analyzeRootsPart: Optional[AnalyzeRootsAspectPart] = field(default=None, init=False, metadata=catMeta(serialize=False, decorators=[pd.NoUI()]))
	analyzeFilesPart: Optional[AnalyzeFilesAspectPart] = field(default=None, init=False, metadata=catMeta(serialize=False, decorators=[pd.NoUI()]))

	def onCloseProject(self, project: Project) -> None:
		"""
		always enabled.
		Called just before closing a Project,
		"""
		pass

	def onProjectLoaded(self, project: Project) -> None:
		"""
		always enabled.
		"""
		pass


@dataclass
class Project(SerializableDataclassWithAspects[ProjectAspect], ABC):
	"""
	Project is always the child of a Session (Composition).
	"""
	name: str = 'new Project'
	roots: list[ProjectRoot] = field(default_factory=list)
	deepDependencies: list[Root] = field(default_factory=list, metadata=catMeta(serialize=False))
	"""all dependencies recursively, excluding all ProjectRoots."""
	# projectSettings: ProjectSettings

	@property
	def path(self) -> FilePathStr:
		# maybe... warn(f"use getSession().projectPath instead", DeprecationWarning, 2)
		from base.model.session import getSession
		return getSession().projectPath

	@property
	def configPath(self) -> FilePathTpl:
		# maybe... warn(f"use getSession().getProjectConfigPath instead", DeprecationWarning, 2)
		from base.model.session import getSession
		return getSession().projectConfigPath

	@property
	def hasConfigFile(self) -> bool:
		from base.model.session import getSession
		return getSession().hasProjectConfigFile

	@property
	def isOpened(self) -> bool:
		from base.model.session import getSession
		return getSession().hasOpenedProject

	@property
	def isEmpty(self) -> bool:
		return not self.roots

	@property
	def allRoots(self) -> list[Root]:
		return self.roots + self.deepDependencies

	def resolveDependencies(self) -> None:
		aspects = [a.dependenciesPart for a in self.aspects if a.dependenciesPart is not None]
		for aspect in aspects:
			aspect.preResolveDependencies(self)
		self.deepDependencies = resolveDependencies(self, aspects)
		for aspect in aspects:
			aspect.postResolveDependencies(self)

	def insertRoot(self, idx: int, root: ProjectRoot) -> ProjectRoot:
		self.roots.insert(idx, root)
		for aspect in self.aspects:
			if aspect.analyzeRootsPart is not None:
				aspect.analyzeRootsPart.onRootAdded(root, self)
		self.analyzeRoot(root)
		return root

	def addRoot(self, root: ProjectRoot) -> ProjectRoot:
		return self.insertRoot(len(self.roots), root)

	def removeRoot(self, root: ProjectRoot):
		self.roots.remove(root)
		for aspect in self.aspects:
			if aspect.analyzeRootsPart is not None:
				aspect.analyzeRootsPart.onRootRemoved(root, self)

	def analyzeRoots(self):
		aspects = [a.analyzeRootsPart for a in self.aspects if a.analyzeRootsPart is not None]
		for projRoot in self.roots:
			self.analyzeRoot(projRoot, aspects)

	def analyzeDependencies(self):
		aspects = [a.analyzeRootsPart for a in self.aspects if a.analyzeRootsPart is not None]
		for dependency in self.deepDependencies:
			self.analyzeRoot(dependency, aspects)

	def analyzeRoot(self, root: Root, aspects: list[AnalyzeRootsAspectPart] = ...):
		if aspects is ...:
			aspects = [a.analyzeRootsPart for a in self.aspects if a.analyzeRootsPart is not None]
		for idxBundle in root.indexBundles:
			idxBundle.clear()
		for a in aspects:
			a.analyzeRoot(root, self)

	def setup(self):
		""" only call once!"""
		_fillProjectAspects(self.aspects)
		roots = self.roots
		self.roots = []
		for root in roots:
			self.addRoot(root)
		self.resolveDependencies()
		self.analyzeDependencies()

		for aspect in self.aspects:
			aspect.onProjectLoaded(self)

	def close(self):
		""" only call once!"""
		for aspect in self.aspects:
			aspect.onCloseProject(self)

		roots = self.roots.copy()
		for root in roots:
			self.removeRoot(root)


def resolveDependencies(project: Project, aspects: list[DependenciesAspectPart]):
	# just a cache:
	dependencyDict: dict[str, Optional[Root]] = {rt.identifier: rt for rt in project.roots}
	# seenDependencies: set[str] = set()
	errorsByRoot: dict[str, list[GeneralError]] = defaultdict(list)

	def getDestinations(root: Root) -> list[Root]:
		root.dependencies = []
		dependencyRoots = []
		seenDependencies = set()
		for aspect in aspects:
			aDependencies = aspect.getDependencies(root, project)
			for dep in aDependencies:
				if dep.identifier in seenDependencies:
					continue
				seenDependencies.add(dep.identifier)
				root.dependencies.append(dep)
				if dep.identifier not in dependencyDict:
					dep.resolved = aspect.resolveDependency(dep)
				else:
					dep.resolved = dependencyDict[dep.identifier]
				if dep.resolved is not None:
					dependencyDict[dep.identifier] = dep.resolved
					dependencyRoots.append(dep.resolved)
				else:
					errorsByRoot[root.name].append(
						SemanticsError(MDStr(f"Missing mandatory dependency '{dep.name}'."), span=dep.span if dep.span is not None else NULL_SPAN)
						if dep.mandatory else
						SemanticsError(MDStr(f"Missing optional dependency '{dep.name}'."), span=dep.span if dep.span is not None else NULL_SPAN, style='info')
					)
		return dependencyRoots

	projectRoots: list[Root] = project.roots
	for projectRoot in projectRoots:
		if projectRoot.identifier:
			dependencyDict[projectRoot.identifier] = projectRoot
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
	name: str
	"""used for displaying"""
	identifier: str
	"""Used for unique identification, of the root. Two DependencyDescr objects with the same identifier ALWAYS point o the same Root."""
	mandatory: bool
	span: Optional[Span] = None
	resolved: Optional[Root] = None


@dataclass
class IndexBundleAspect(Aspect, IndexBundle, ABC):
	pass


@dataclass
class Root(SerializableDataclass):
	_name: str = field(metadata=catMeta(serializedName='name'))
	_location: str  # =FilePathStr  # maybe?
	_identifier: str = field(default='', metadata=catMeta(serializedName='identifier'))
	"""Used for unique identification, of the root. Two DependencyDescr objects with the same identifier ALWAYS point o the same Root."""
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
				if aspect.analyzeRootsPart is not None:
					aspect.analyzeRootsPart.onRootRenamed(self, oldName, newName)
		self._name = newName

	@property
	def identifier(self) -> str:
		"""Used for unique identification, of the root. Two DependencyDescr objects with the same identifier ALWAYS point o the same Root."""
		return self._identifier


@dataclass
class ProjectRoot(Root):
	pass


@final
@as_dataclass(fast_new=True, hashable=True)
class FileEntry:
	fullPath: FilePathTpl
	virtualPath: str  # = dataclasses.field(compare=False)
	splitNameForSearch: SplitStrs
	isFile: bool

	@property
	def fileName(self) -> str:
		return self.virtualPath.rpartition('/')[2]

	@property
	def projectName(self) -> str:
		return self.virtualPath.partition('/')[0]

	def __eq__(self, other):
		if type(other) is not FileEntry:
			return False
		return self.virtualPath == other.virtualPath and self.fullPath == other.fullPath and self.isFile == other.isFile

	def __ne__(self, other):
		if type(other) is not FileEntry:
			return True
		return self.virtualPath != other.virtualPath or self.fullPath != other.fullPath or self.isFile != other.isFile

	def __hash__(self):
		return hash((56783265, self.fullPath))


def makeFileEntry(fullPath: FilePathTpl, root: Root, isFile: bool) -> FileEntry:
	virtualPath = f'{root.name}/{fullPath[1]}'
	splitNameForSearch = splitStringForSearch(virtualPath.rpartition('/')[2])
	return FileEntry(fullPath, virtualPath, splitNameForSearch, isFile)
