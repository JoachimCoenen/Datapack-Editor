import os
from dataclasses import dataclass, field
from typing import Optional, Callable, cast

from cat.GUI import propertyDecorators as pd
from cat.GUI.propertyDecorators import ValidatorResult
from cat.Serializable.serializableDataclasses import catMeta
from cat.utils import first
from cat.utils.logging_ import logWarning
from base.model.applicationSettings import getApplicationSettings
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.aspect import AspectType
from base.model.project.project import AnalyzeFilesAspectPart, DependenciesAspectPart, ProjectInfoAspectPart, Root, ProjectAspect, DependencyDescr, FileEntry, Project
from base.model.parsing.contextProvider import parseNPrepare, validateTree
from base.model.pathUtils import ArchiveFilePool, ZipFilePool, loadBinaryFile, normalizeDirSeparators
from base.model.session import getSession
from base.model.utils import GeneralError, MDStr, NULL_SPAN, SemanticsError
from .datapackContents import collectEntry
from .dpVersions import getAllDPVersions, getDPVersion, DPVersion
from corePlugins.json import JSON_ID
from corePlugins.json.core import JsonData
from corePlugins.minecraft.settings import MinecraftSettings, MinecraftVersion
from corePlugins.minecraft_data.fullData import FullMCData, getFullMcData


def minecraftVersionValidator(version: str) -> Optional[pd.ValidatorResult]:
	versions = allRegisteredMinecraftVersions()
	if version not in versions:
		return ValidatorResult(f"No minecraft executable with name '{version}' configured. Executables can be configured in settings -> minecraft.", 'warning')
	return None


def datapackVersionValidator(version: str) -> Optional[pd.ValidatorResult]:
	versions = getAllDPVersions()
	if version not in versions:
		return ValidatorResult(f"Datapack version '{version}' not supported by your current installation of {getApplicationSettings().applicationName}. You might need to update your installation or install a plugin.", 'warning')
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
class DatapackAspect(ProjectAspect):

	@classmethod
	def getAspectType(cls) -> AspectType:
		from .settings import DATAPACK_ASPECT_TYPE
		return DATAPACK_ASPECT_TYPE

	def __post_init__(self):
		self.analyzeFilesPart = AnalyzeFilesDatapackAspectPart(self)
		self.dependenciesPart = DependenciesDatapackAspectPart(self)
		self.projectInfoPart = ProjectInfoAspectPart[DatapackAspect](self)

	dpVersion: str = field(
		default='18',
		metadata=catMeta(
			deferLoading=True,
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys()), editable=True),
				pd.Validator(datapackVersionValidator),
			]
		)
	)

	minecraftVersion: str = field(
		default='1.20.2',
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

	def onCloseProject(self, project: Project) -> None:
		self._reloadDPVersion(self.dpVersion, None)
		self._reloadMinecraftVersion(self.minecraftVersion, None)

	def onProjectLoaded(self, project: Project) -> None:
		self._reloadDPVersion(None, self.dpVersion)
		self._reloadMinecraftVersion(None, self.minecraftVersion)

	def _reloadDPVersion(self, oldVersion: Optional[str], newVersion: Optional[str]):
		dpVersion = getDPVersion(oldVersion)
		if dpVersion is not None:
			dpVersion.deactivate()
		dpVersion = getDPVersion(newVersion)
		if dpVersion is not None:
			dpVersion.activate()
		if newVersion is not None and (problem := datapackVersionValidator(newVersion)) is not None:
			error = SemanticsError(MDStr(f"DatapackAspect: {problem.message}"), NULL_SPAN, problem.style)
			self.projectInfoPart.setErrors('dpVersion', (error,))
		else:
			self.projectInfoPart.setErrors('dpVersion', ())

	def _reloadMinecraftVersion(self, oldVersion: Optional[str], newVersion: Optional[str]):
		minecraftVersion = _getFullMcDataFromRegisteredMinecraftVersion(oldVersion)
		if minecraftVersion is not None:
			minecraftVersion.deactivate()
		minecraftVersion = _getFullMcDataFromRegisteredMinecraftVersion(newVersion)
		if minecraftVersion is not None:
			minecraftVersion.activate()
		if newVersion is not None and (problem := minecraftVersionValidator(newVersion)) is not None:
			error = SemanticsError(MDStr(f"DatapackAspect: {problem.message}"), NULL_SPAN, problem.style)
			self.projectInfoPart.setErrors('minecraftVersion', (error,))
		else:
			self.projectInfoPart.setErrors('minecraftVersion', ())


def _getDPVersion(self: DatapackAspect) -> str:
	return getattr(self, '_dpVersion', '') or 'Default'


def _setDPVersion(self: DatapackAspect, newVal: str) -> None:
	project = getSession().project
	if project is not None and project.aspects.get(DatapackAspect) is self:
		oldVal = getattr(self, '_dpVersion', None)
		if True and newVal != oldVal:
			self._reloadDPVersion(oldVal, newVal)

	setattr(self, '_dpVersion',  newVal)


DatapackAspect.dpVersion = property(_getDPVersion, _setDPVersion)


def _getMinecraftVersion(self: DatapackAspect) -> str:
	return getattr(self, '_minecraftVersion', '') or 'Default'


def _setMinecraftVersion(self: DatapackAspect, newVal: str) -> None:
	project = getSession().project
	if project is not None and project.aspects.get(DatapackAspect) is self:
		oldVal = getattr(self, '_minecraftVersion', None)
		if True and newVal != oldVal:
			self._reloadMinecraftVersion(oldVal, newVal)

	setattr(self, '_minecraftVersion',  newVal)


DatapackAspect.minecraftVersion = property(_getMinecraftVersion, _setMinecraftVersion)


@dataclass
class DependenciesDatapackAspectPart(DependenciesAspectPart[DatapackAspect]):

	def preResolveDependencies(self, project: Project) -> None:
		self.aspect.projectInfoPart.setErrors('dependencies', [])

	def _getErrorsList(self) -> list[GeneralError]:
		return cast(list[GeneralError], self.aspect.projectInfoPart.getErrors('dependencies'))

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
			node, errors = None, [SemanticsError(MDStr(f"Root '{root.name}' has no 'dependencies.json' file."), span=NULL_SPAN, style='info')]
		else:
			node, errors, _ = parseNPrepare(file, filePath=filePath, language=JSON_ID, schema=schema)

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
			self._getErrorsList().append(errors[0])  # only append the first error!
			logWarning(f"Failed to read '{fileName}' for root '{rootPath}':")
			for error in errors:
				logWarning(str(error), indentLvl=1)

		# minecraft dependency
		registeredVersion = getRegisteredMinecraftVersion(self.aspect.minecraftVersion)
		if registeredVersion is not None:
			dependencies.append(DependencyDescr(
				name=registeredVersion.minecraftExecutable,
				identifier=registeredVersion.minecraftExecutable,
				mandatory=True,
				span=None
			))

		return dependencies

	def resolveDependency(self, dep: DependencyDescr) -> Optional[Root]:
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
		return None  # missing dependency error is logged by Project itself.

	def postResolveDependencies(self, project: Project) -> None:
		pass  # nothing to do here...


@dataclass
class AnalyzeFilesDatapackAspectPart(AnalyzeFilesAspectPart[DatapackAspect]):

	def analyzeFile(self, root: Root, fileEntry: FileEntry, pool: ArchiveFilePool) -> None:
		handlers = self.aspect.dpVersionData.structure
		collectEntry(fileEntry.fullPath, handlers, root, pool)


DEPENDENCY_SEARCH_LOCATIONS: list[Callable[[], list[str]]] = []
"""search in these directories to resolve dependencies"""


def defaultSearchLocations():
	from .settings import DatapackSettings
	sl = getApplicationSettings().aspects.get(DatapackSettings).dependenciesLocation
	if sl:
		return [sl]
	return []


DEPENDENCY_SEARCH_LOCATIONS.append(defaultSearchLocations)
