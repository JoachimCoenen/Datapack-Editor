import os
from dataclasses import dataclass, field
from typing import Optional, Callable

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable.dataclassJson import catMeta
from Cat.utils.logging_ import logWarning
from base.model.applicationSettings import getApplicationSettings
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.aspect import AspectType
from base.model.project.project import AspectFeatures, Root, ProjectAspect, DependencyDescr, FileEntry
from base.model.parsing.contextProvider import parseNPrepare, validateTree
from base.model.pathUtils import ZipFilePool, loadBinaryFile, normalizeDirSeparators
from base.model.session import getSession
from base.model.utils import WrappedError
from .datapackContents import collectEntry
from .dpVersions import getAllDPVersions, getDPVersion, DPVersion, DP_EMPTY_VERSION
from corePlugins.json import JSON_ID
from corePlugins.json.core import JsonData


@dataclass
class DatapackAspect(ProjectAspect, features=AspectFeatures(dependencies=True, analyzeRoots=False, analyzeFiles=True)):
	@classmethod
	def getAspectType(cls) -> AspectType:
		from .settings import DATAPACK_ASPECT_TYPE
		return DATAPACK_ASPECT_TYPE

	dpVersion: str = field(
		default='7',
		metadata=catMeta(
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys())),
			]
		)
	)

	@property
	def dpVersionData(self) -> DPVersion:
		result = getDPVersion(self.dpVersion)
		if result is None:
			result = DP_EMPTY_VERSION
		return result

	def getDependencies(self, root: Root) -> list[DependencyDescr]:
		fileName = 'dependencies.json'
		rootPath = root.normalizedLocation
		schema = GLOBAL_SCHEMA_STORE.get('dpe:dependencies', JSON_ID)

		if rootPath.lower().endswith('.jar'):
			# Minecraft does not need itself as a dependency.
			return []

		# dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
		dependencies: list[DependencyDescr] = []  # TODO: DependencyDescr(applicationSettings.minecraft.executable, 'minecraft', mandatory=True)]

		filePath = (rootPath, fileName)
		node: Optional[JsonData]
		try:
			with ZipFilePool() as pool:
				file = loadBinaryFile(filePath, pool)
		except (OSError, KeyError) as e:
			node, errors = None, [WrappedError(e)]
		else:
			node, errors = parseNPrepare(file, filePath=filePath, language=JSON_ID, schema=schema)

		if node is not None:
			validateTree(node, file, errors)

		if node is not None and not errors:
			for element in node.data:
				name = element.data['name'].value
				dependencies.append(DependencyDescr(
					name=name.data,
					identifier=name.data,
					mandatory=element.data['mandatory'].value.data,
					span=name.span
				))
		if errors:
			logWarning(f"Failed to read '{fileName}' for root '{rootPath}':")
			for error in errors:
				logWarning(str(error), indentLvl=1)

		return dependencies

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		return resolveDependency(dependencyDescr)

	def analyzeFile(self, root: Root, fileEntry: FileEntry) -> None:
		handlers = self.dpVersionData.structure
		collectEntry(fileEntry.fullPath, handlers, root)


def _getDPVersion(self: DatapackAspect) -> str:
	return getattr(self, '_dpVersion', '') or 'Default'


def _setDPVersion(self: DatapackAspect, newVal: str) -> None:
	project = getSession().project
	if project is not None and project.aspects.get(DatapackAspect) is self:
		oldVal = getattr(self, '_dpVersion', None)
		if True or newVal != oldVal:
			dpVersion = getDPVersion(oldVal)
			if dpVersion is not None:
				dpVersion.deactivate()
			dpVersion = getDPVersion(newVal)
			if dpVersion is not None:
				dpVersion.activate()
	setattr(self, '_minecraftVersion',  newVal)


DEPENDENCY_SEARCH_LOCATIONS: list[Callable[[], list[str]]] = []
"""search in these directories to resolve dependencies"""


def defaultSearchLocations():
	from .settings import DatapackSettings
	sl = getApplicationSettings().aspects.get(DatapackSettings).dependenciesLocation
	if sl:
		return [sl]
	return []


DEPENDENCY_SEARCH_LOCATIONS.append(defaultSearchLocations)


def resolveDependency(dep: DependencyDescr) -> Optional[Root]:
	if '/' in dep.name and os.path.exists(dep.name):
		return Root(dep.name, dep.name)
	for dslProvider in DEPENDENCY_SEARCH_LOCATIONS:
		dsls = dslProvider()
		for dsl in dsls:
			path = os.path.join(dsl, dep.name)
			if os.path.exists(path):
				return Root(_name=dep.name, _location=normalizeDirSeparators(path))
			path = path + '.zip'
			if os.path.exists(path):
				return Root(_name=dep.name, _location=normalizeDirSeparators(path))
	return None
