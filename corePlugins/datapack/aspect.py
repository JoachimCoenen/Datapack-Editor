import os
from dataclasses import dataclass, field
from typing import Optional, Callable

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from Cat.Serializable.dataclassJson import catMeta
from Cat.utils.logging_ import logWarning
from base.model.applicationSettings import SettingsAspect, getApplicationSettings
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.aspect import AspectType
from base.model.project.project import AspectFeatures, Root, ProjectAspect, DependencyDescr, FileEntry
from base.model.parsing.contextProvider import parseNPrepare, validateTree
from base.model.pathUtils import ZipFilePool, loadBinaryFile, normalizeDirSeparators
from base.model.utils import WrappedError
from corePlugins.datapack.datapackContents import collectEntry
from corePlugins.json import JSON_ID
from corePlugins.json.core import JsonData

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')
# DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


@dataclass
class DatapackAspect(ProjectAspect, features=AspectFeatures(dependencies=True, analyzeRoots=False, analyzeFiles=True)):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	def getDependencies(self, root: Root) -> list[DependencyDescr]:
		fileName = 'dependencies.json'
		projectPath = root.normalizedLocation
		schema = GLOBAL_SCHEMA_STORE.get('dpe:dependencies', JSON_ID)

		if projectPath.lower().endswith('.jar'):
			# Minecraft does not need itself as a dependency.
			return []

		# dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
		dependencies: list[DependencyDescr] = []  # TODO: DependencyDescr(applicationSettings.minecraft.executable, 'minecraft', mandatory=True)]

		filePath = (projectPath, fileName)
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
			logWarning(f"Failed to read '{fileName}' for project '{projectPath}':")
			for error in errors:
				logWarning(str(error), indentLvl=1)

		return dependencies

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		return resolveDependency(dependencyDescr)

	def analyzeFile(self, root: Root, fileEntry: FileEntry) -> None:
		from corePlugins.datapack.datapackContentsContents import DATAPACK_CONTENTS_STRUCTURE
		handlers = DATAPACK_CONTENTS_STRUCTURE  # TODO: usedatapack version to get correct contents structure.
		collectEntry(fileEntry.fullPath, handlers, root)

		# pattern = folderPatternFromPath(f'data/{NAME_SPACE_VAR}/functions/')
		# filePath = fileEntry.fullPath[1]
		# match = pattern.match(filePath)
		# if match is None:
		# 	return
		#
		# namespace = match.groupdict().get('namespace')
		# rest = filePath[match.end():]
		#
		# dpPath, filePath = fileEntry.fullPath
		# name = fileEntry.fileName.partition('.')[0]
		#
		# if not filePath.endswith('.mcfunction'):
		# 	return
		# resLoc = ResourceLocation(namespace, rest + name, False) if namespace is not None else None
		# root.indexBundles.setdefault(DatapackContents).functions.add(resLoc, filePath, FunctionMeta(fileEntry.fullPath))
		# return None


	# def onRootAdded(self, root: Root, project: Project) -> None:
	# 	filesystemEvents.FILESYSTEM_OBSERVER.schedule("dpe:files_aspect", root.normalizedLocation, Handler(root, project))
	#
	# def onRootRemoved(self, root: Root, project: Project) -> None:
	# 	filesystemEvents.FILESYSTEM_OBSERVER.unschedule("dpe:files_aspect", root.normalizedLocation)

	# def analyzeRoot(self, root: Root) -> None:
	# 	location = root.normalizedLocation
	# 	if location.endswith('.jar'):  # we don't need '.class' files. This is not a Java IDE.
	# 		pathInFolder = 'data/**'
	# 		pathInZip = 'data/**'
	# 	else:
	# 		pathInFolder = '/**'
	# 		pathInZip = '/**'
	# 	pif = SearchPath(pathInFolder, location.rstrip('/'))
	# 	piz = pathInZip
	#
	# 	# rawLocalFiles = getAllFilesFromSearchPath(location, pif, piz, extensions=tuple(), excludes=None)
	# 	if not pif.divider:
	# 		return
	# 	rawLocalFiles, rawLocalFolders = getAllFilesFoldersFromFolder(location, pif.divider)
	#
	# 	idx = root.indexBundles.get(FilesIndex).files
	# 	for jf in rawLocalFiles:
	# 		idx.add(jf[1], jf, FileEntry(jf, root.name + jf[1], True))
	#
	# 	idx = root.indexBundles.get(FilesIndex).folders
	# 	for jf in rawLocalFolders:
	# 		idx.add(jf[1], jf, FileEntry(jf, root.name + jf[1], False))
	#
	# def analyzeProject(self) -> None:
	# 	from sessionOld.session import getSession
	# 	allEntryHandlers = getSession().datapackData.structure
	# 	collectAllEntries(self.parent.files, allEntryHandlers, self.parent)


DEPENDENCY_SEARCH_LOCATIONS: list[Callable[[], list[str]]] = []
"""search in these directories to resolve dependencies"""


def defaultSearchLocations():
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


ALL_DP_VERSIONS: dict[str, int] = {}


def folderPathValidator(path: str) -> Optional[ValidatorResult]:
	if not os.path.lexists(path):
		return ValidatorResult('Folder not found', 'error')

	if not os.path.isdir(path):
		return ValidatorResult('Not a directory', 'error')

	return None


@dataclass()
class DatapackSettings(SettingsAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	dpVersion: str = field(
		default='6',
		metadata=catMeta(
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=ALL_DP_VERSIONS.keys()),
			]
		)
	)

	dependenciesLocation: str = field(
		default_factory=lambda: os.path.expanduser('~/.dpe/dependencies').replace('\\', '/'),
		metadata=catMeta(
			kwargs=dict(
				label="Datapack Dependencies Location",
				tip="DPE will search in this directory to resolve dependencies",
			),
			decorators=[
				pd.FolderPath(),
				pd.Validator(folderPathValidator)
			]
		)
	)
