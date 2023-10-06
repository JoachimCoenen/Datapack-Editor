import os
from dataclasses import dataclass, field
from typing import Optional, Callable

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from Cat.Serializable.dataclassJson import catMeta
from Cat.utils import first
from Cat.utils.logging_ import logWarning
from base.model.applicationSettings import getApplicationSettings
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.aspect import AspectType
from base.model.project.project import AspectFeatures, Root, ProjectAspect, DependencyDescr, FileEntry, Project
from base.model.parsing.contextProvider import parseNPrepare, validateTree
from base.model.pathUtils import ZipFilePool, loadBinaryFile, normalizeDirSeparators
from base.model.session import getSession
from base.model.utils import WrappedError
from .datapackContents import collectEntry
from .dpVersions import getAllDPVersions, getDPVersion, DPVersion
from corePlugins.json import JSON_ID
from corePlugins.json.core import JsonData
from corePlugins.minecraft.settings import MinecraftSettings, MinecraftVersion
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData


def minecraftVersionValidator(version: str) -> Optional[pd.ValidatorResult]:
	versions = getApplicationSettings().aspects.get(MinecraftSettings).minecraftVersions
	if not any(v.name == version for v in versions):
		return ValidatorResult('No minecraft executable for this name configured. executables can be configured in settings -> minecraft.', 'warning')
	return None


def allRegisteredMinecraftVersions() -> list[str]:
	return [v.name for v in getApplicationSettings().aspects.get(MinecraftSettings).minecraftVersions]


def getRegisteredMinecraftVersion(version: str) -> Optional[MinecraftVersion]:
	return first(
		(mv for mv in getApplicationSettings().aspects.get(MinecraftSettings).minecraftVersions if mv.name == version),
		None
	)


def _getFullMcDataFromRegisteredMinecraftVersion(version: str) -> FullMCData:
	registeredVersion = getRegisteredMinecraftVersion(version)
	result = getFullMcData(registeredVersion.version if registeredVersion is not None else '')  # returns FullMCData.EMPTY if registeredVersion is None.
	return result


@dataclass
class DatapackAspect(ProjectAspect, features=AspectFeatures(dependencies=True, analyzeRoots=False, analyzeFiles=True)):

	@classmethod
	def getAspectType(cls) -> AspectType:
		from .settings import DATAPACK_ASPECT_TYPE
		return DATAPACK_ASPECT_TYPE

	dpVersion: str = field(
		default='7',
		metadata=catMeta(
			deferLoading=True,
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys()), editable=True),
			]
		)
	)

	minecraftVersion: str = field(
		default='1.17',
		metadata=catMeta(
			kwargs=dict(label='Minecraft Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: allRegisteredMinecraftVersions()), editable=True),
				pd.Validator(minecraftVersionValidator),
			]
		)
	)

	@property
	def dpVersionData(self) -> DPVersion:
		result = getDPVersion(self.dpVersion)
		return result

	@property
	def mcVersionData(self) -> FullMCData:
		return _getFullMcDataFromRegisteredMinecraftVersion(self.minecraftVersion)

	def getDependencies(self, root: Root, project: Project) -> list[DependencyDescr]:
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

		# minecraft dependency
		registeredVersion = getRegisteredMinecraftVersion(self.minecraftVersion)
		if registeredVersion is not None:
			dependencies.append(DependencyDescr(
				name=registeredVersion.minecraftExecutable,
				identifier=registeredVersion.minecraftExecutable,
				mandatory=True,
				span=None
			))

		return dependencies

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		return resolveDependency(dependencyDescr)

	def analyzeFile(self, root: Root, fileEntry: FileEntry) -> None:
		handlers = self.dpVersionData.structure
		collectEntry(fileEntry.fullPath, handlers, root)

	def onCloseProject(self, project: Project) -> None:
		_reloadDPVersion(self.dpVersion, None)
		_reloadMinecraftVersion(self.minecraftVersion, None)

	def onProjectLoaded(self, project: Project) -> None:
		_reloadDPVersion(None, self.dpVersion)
		_reloadMinecraftVersion(None, self.minecraftVersion)


def _getDPVersion(self: DatapackAspect) -> str:
	return getattr(self, '_dpVersion', '') or 'Default'


def _setDPVersion(self: DatapackAspect, newVal: str) -> None:
	project = getSession().project
	if project is not None and project.aspects.get(DatapackAspect) is self:
		oldVal = getattr(self, '_dpVersion', None)
		if True and newVal != oldVal:
			_reloadDPVersion(oldVal, newVal)
	setattr(self, '_dpVersion',  newVal)


DatapackAspect.dpVersion = property(_getDPVersion, _setDPVersion)


def _reloadDPVersion(oldVersion: Optional[str], newVersion: Optional[str]):
	dpVersion = getDPVersion(oldVersion)
	if dpVersion is not None:
		dpVersion.deactivate()
	dpVersion = getDPVersion(newVersion)
	if dpVersion is not None:
		dpVersion.activate()


def _getMinecraftVersion(self: DatapackAspect) -> str:
	return getattr(self, '_minecraftVersion', '') or 'Default'


def _setMinecraftVersion(self: DatapackAspect, newVal: str) -> None:
	project = getSession().project
	if project is not None and project.aspects.get(DatapackAspect) is self:
		oldVal = getattr(self, '_minecraftVersion', None)
		if True and newVal != oldVal:
			_reloadMinecraftVersion(oldVal, newVal)
	setattr(self, '_minecraftVersion',  newVal)


DatapackAspect.minecraftVersion = property(_getMinecraftVersion, _setMinecraftVersion)


def _reloadMinecraftVersion(oldVersion: Optional[str], newVersion: Optional[str]):
	minecraftVersion = _getFullMcDataFromRegisteredMinecraftVersion(oldVersion)
	if minecraftVersion is not None:
		minecraftVersion.deactivate()
	minecraftVersion = _getFullMcDataFromRegisteredMinecraftVersion(newVersion)
	if minecraftVersion is not None:
		minecraftVersion.activate()


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
