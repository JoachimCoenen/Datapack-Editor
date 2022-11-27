import os
from dataclasses import dataclass
from typing import Optional, Callable

from Cat.utils.logging_ import logWarning
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.project.aspect import AspectType
from base.model.project.project import AspectFeatures, Root, ProjectAspect, DependencyDescr
from base.model.parsing.contextProvider import parseNPrepare, validateTree
from base.model.pathUtils import ZipFilePool, loadBinaryFile, normalizeDirSeparators
from base.model.utils import LANGUAGES, GeneralError, MDStr
from settings import applicationSettings

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')
# DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


@dataclass
class DatapackAspect(ProjectAspect, features=AspectFeatures(dependencies=True, analyzeRoots=False)):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	def getDependencies(self, root: Root) -> list[DependencyDescr]:
		fileName = 'dependencies.json'
		projectPath = root.normalizedLocation
		schema = GLOBAL_SCHEMA_STORE.get2('dpe:dependencies', LANGUAGES.JSON)

		if projectPath.lower().endswith('.jar'):
			# Minecraft does not need to itself as a dependency.
			return []

		# dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
		dependencies: list[DependencyDescr] = []  # TODO: DependencyDescr(applicationSettings.minecraft.executable, 'minecraft', mandatory=True)]

		filePath = (projectPath, fileName)
		try:
			with ZipFilePool() as pool:
				file = loadBinaryFile(filePath, pool)
		except (OSError, KeyError) as e:
			node, errors = None, [GeneralError(MDStr(f"{type(e).__name__}: {str(e)}"))]
		else:
			node, errors = parseNPrepare(file, filePath=filePath, language=LANGUAGES.JSON, schema=schema, allowMultilineStr=False)

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
				logWarning(error, indentLvl=1)

		return dependencies

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		return resolveDependency(dependencyDescr)

	# def onRootAdded(self, root: Root, project: Project) -> None:
	# 	filesystemEvents.FILESYSTEM_OBSERVER.schedule("dpe:files_aspect", root.normalizedLocation, Handler(root, project))
	#
	# def onRootRemoved(self, root: Root, project: Project) -> None:
	# 	filesystemEvents.FILESYSTEM_OBSERVER.unschedule("dpe:files_aspect", root.normalizedLocation)
	#
	# def analyzeFile(self, root: Root, path: FilePathTpl) -> None:
	# 	pass

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
	from settings import applicationSettings
	sl = os.path.expanduser('~/.dpe/dependencies').replace('\\', '/')  # TODO: applicationSettings.minecraft.savesLocation
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
				return Root(name=dep.name, _location=normalizeDirSeparators(path))
			path = path + '.zip'
			if os.path.exists(path):
				return Root(name=dep.name, _location=normalizeDirSeparators(path))
	return None