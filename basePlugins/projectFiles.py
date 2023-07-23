from __future__ import annotations

import dataclasses
import os
import shutil
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Optional, Callable, NamedTuple, ClassVar, Type

from PyQt5.QtGui import QIcon, QKeySequence
from watchdog.events import FileSystemEventHandler, FileClosedEvent, FileModifiedEvent, FileDeletedEvent, FileCreatedEvent, FileMovedEvent

from Cat.CatPythonGUI.GUI import SizePolicy
from Cat.CatPythonGUI.GUI.pythonGUI import TabOptions, EditorBase, MenuItemData
from Cat.CatPythonGUI.GUI.treeBuilders import DataTreeBuilder
from Cat.icons import icons
from Cat.utils import DeferredCallOnceMethod, openOrCreate
from base.model import filesystemEvents
from base.model.pathUtils import FilePath, SearchPath, FilePathTpl, normalizeDirSeparators, splitPath, normalizeDirSeparatorsStr, unitePath, \
	fileNameFromFilePath, getAllFilesFoldersFromFolder, joinFilePath, getAllFilesFromArchive
from base.model.aspect import AspectType
from base.model.project.index import Index
from base.model.project.project import Project, ProjectRoot, ProjectAspect, DependencyDescr, Root, IndexBundleAspect, AspectFeatures
from base.model.session import getSession
from base.model.utils import Span
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries
from base.plugin import PluginBase, SideBarTabGUIFunc, PLUGIN_SERVICE, ToolBtnFunc


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('ProjectFiles', ProjectFilesPlugin())


class ProjectFilesPlugin(PluginBase):
	def sideBarTabs(self) -> list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]]:
		return [(TabOptions('Files', icon=icons.folder_open), projectFilesGUI, None)]

	def projectAspects(self) -> list[Type[ProjectAspect]]:
		return [FilesAspect]


def projectFilesGUI(gui: DatapackEditorGUI):
	gui.editor(DatapackFilesEditor, getSession().project, seamless=True)


@dataclass(slots=True)
class FilesTreeItem:
	"""Only used by the files tree GUI to denote directories and files"""
	label: str
	icon: Optional[QIcon] = dataclasses.field(compare=False)
	commonVPath: str = dataclasses.field(compare=False)
	commonPath: FilePathTpl = dataclasses.field(compare=False)
	filePaths: list[FileEntry] = dataclasses.field(compare=False)

	isImmutable: bool = dataclasses.field(compare=False)
	isArchive: bool = dataclasses.field(default=False, compare=False)

	@property
	def folderPath(self) -> Optional[FilePathTpl]:
		""":return: path of the folder if isFile is False, else None"""
		if self.isFile:
			return None
		return self.commonPath

	@property
	def filePath(self) -> Optional[FilePathTpl]:
		""":return: path of the file if isFile is True, else None"""
		if not self.isFile:
			return None
		return self.filePaths[0].fullPath

	@property
	def isFile(self) -> bool:
		filePathsCount = len(self.filePaths)
		return filePathsCount == 1 and self.commonPath == self.filePaths[0].fullPath and self.filePaths[0].isFile


@dataclass
class FilesTreeRoot:
	"""Only used by the files tree GUI to denote file roots, (i.e. ProjectRoot, Root, etc.)"""
	projects: list[AnyFilesTreeElement] = dataclasses.field(compare=False)
	label: str = '<ROOT>'
	icon: Optional[QIcon] = None
	commonVPath: str = ''
	# commonPath: FilePathTpl = Not Needed! :D

	@property
	def filePaths(self) -> list[FileEntry]:
		return []

	isImmutable: ClassVar[bool] = False
	isArchive: ClassVar[bool] = False

	@property
	def folderPath(self) -> Optional[FilePathTpl]:
		""":return: path of the folder if isFile is False, else None"""
		return None

	@property
	def filePath(self) -> Optional[FilePathTpl]:
		""":return: path of the file if isFile is True, else None"""
		return None

	@property
	def isFile(self) -> bool:
		return False


AnyFilesTreeElement = FilesTreeRoot | FilesTreeItem


class DatapackFilesEditor(EditorBase[Project]):

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.vLayout(seamless=True):
			self.filteredProjectsFilesTreeGUI(
				gui,
				self.model().roots,
				self.model().deepDependencies,
				onDoubleClick=self._onDoubleClick,
				onContextMenu=self._onContextMenu,
			)

			with gui.hPanel(seamless=True):
				gui.addHSpacer(5, SizePolicy.Expanding)
				if gui.toolButton(
					icon=icons.add,
					tip="create new Datapack",
					enabled=True
				):
					self._createNewDatapackGUI()
				if gui.toolButton(
					icon=icons.refresh,
					tip="refresh",
					enabled=True
				):
					self._refreshDependencies()

	def _openFunc(self, filePath: FilePath, selectedSpan: Optional[Span] = None):
		getSession().tryOpenOrSelectDocument(filePath, selectedSpan)

	@DeferredCallOnceMethod(delay=0)  # needed to avoid transferring keyPresses (Return Key) to another widget, if a focusChange happens.
	def _onDoubleClick(self, data: FilesTreeItem):
		if data.isFile:
			self._openFunc(data.filePaths[0].fullPath)
			return True
		return False

	def _renameFileOrFolder(self, data: FilesTreeItem):
		if data.isFile:
			path = data.filePaths[0].fullPath
		else:
			path = data.folderPath
			if path is None:
				return
			path = path[0], path[1].rstrip('/')

		lPath, __, name = path[1].rpartition('/')
		newName, isOk = self._gui.askUserInput(f"rename '{name}'", name)
		if isOk:
			if lPath:
				newPath = (path[0], f'{lPath}/{newName}')
			else:
				newPath = (path[0], newName)
			joinedNewPath = os.path.join(*newPath)
			if os.path.exists(joinedNewPath):
				self._gui.showInformationDialog(f"The name \"{newName}\" cannot be used.", "Another file with the same name already exists.")
			else:
				try:
					os.rename(os.path.join(*path), joinedNewPath)
				except OSError as e:
					getSession().showAndLogError(e)
				else:
					data.label = newName
					# update paths of opened files:
					for fe2 in data.filePaths:
						filePath = fe2.fullPath
						doc = getSession().documents.getDocument(filePath)
						if doc is not None:
							pathLen = len(path[1])
							if doc.filePath[1].startswith(path[1]):
								newFilePath = newPath[0], newPath[1] + doc.filePath[1][pathLen:]
								doc.filePath = newFilePath
						view = getSession().documents._getViewForDocument(doc)
						if view is not None:
							view.onDocumentsChanged.emit()
			self.redraw('DatapackFilesEditor._renameFileOrFolder(...)')

	def _deleteFileFunc(self, path: FilePath):
		_, __, name = path[1].rstrip('/').rpartition('/')
		if self._gui.askUser(f"Delete file '{name}'?", 'this cannot be undone!'):
			try:
				os.unlink(os.path.join(*path))
			except OSError as e:
				getSession().showAndLogError(e)
			self.redraw('DatapackFilesEditor._deleteFileFunc(...)')
			# TODO: maybe close opened file?

	def _deleteFolderFunc(self, path: FilePath):
		name = fileNameFromFilePath(path)
		unitedPath = unitePath(path)
		isEmpty = not any(os.scandir(unitedPath))
		try:
			if isEmpty:
				if self._gui.askUser(f"Delete folder '{name}'?", 'This cannot be undone!'):
					os.rmdir(unitedPath)
			else:
				if self._gui.askUser(f"Delete folder '{name}' and all its contents?", 'This cannot be undone!'):
					shutil.rmtree(unitedPath)
			# TODO: maybe close opened files?
		except OSError as e:
			getSession().showAndLogError(e)
		self.redraw('DatapackFilesEditor._deleteFileFunc(...)')

	def _newDatapackDialog(self):
		pass  # todo: _newDatapackDialog(...)?

	def _createNewDatapackGUI(self) -> None:
		self._gui.showWarningDialog("Out of Order", "This feature is currently out of order.")
		# TODO: _createNewDatapackGUI()
		# def datapackPathFromName(name: str):
		# 	return normalizeDirSeparators(os.path.join(getSession().world.path, 'datapacks', name))
		#
		# def validateName(name: str) -> Optional[ValidatorResult]:
		# 	datapackPath = datapackPathFromName(name)
		# 	if os.path.exists(datapackPath):
		# 		return ValidatorResult(f"Another datapack with the same name already exists.", 'error')
		# 	return None
		#
		# def validateNamespace(namespace: str) -> Optional[ValidatorResult]:
		# 	if not isNamespaceValid(namespace):
		# 		return ValidatorResult(f"Not a valid namespace.\nNamespaces mut only contain:\n"
		# 							   f" - Numbers (0-9)\n"
		# 							   f" - Lowercase letters (a-z)\n"
		# 							   f" - Underscore (_)\n"
		# 							   f" - Hyphen/minus (-)\n"
		# 							   f" - dot (.)\n", 'error')
		# 	return None
		#
		# class Context(SerializableContainer):
		# 	name: str = Serialized(default='new Datapack', decorators=[Validator(validateName)])
		# 	namespace: str = Serialized(default='new_datapack', decorators=[Validator(validateNamespace)])
		#
		# def guiFunc(gui: DatapackEditorGUI, context: Context) -> Context:
		# 	gui.propertyField(context, Context.name)
		# 	gui.propertyField(context, Context.namespace)
		# 	return context
		#
		# context = Context()
		# while True:
		# 	context, isOk = self._gui.askUserInput(f"new Datapack", context, guiFunc)
		# 	if not isOk:
		# 		return
		# 	isValid = validateName(context.name) is None and validateNamespace(context.namespace) is None
		# 	if isValid:
		# 		break
		#
		# datapackPath = datapackPathFromName(context.name)
		#
		# try:
		# 	with openOrCreate(f"{datapackPath}/pack.mcmeta", 'w') as f:
		# 		f.write(
		# 			'{\n'
		# 			'	"pack": {\n'
		# 			'		"pack_format": 6,\n'
		# 			'		"description": "[{"text":" """ + context.name + """ ","color":"white"}{"text":"\\nCreated with","color":"white"},{"text":"Data Pack Editor","color":"yellow"}] "\n'
		# 			'	}\n'
		# 			'}')
		#
		# 	for folder in getSession().datapackData.structure.values():
		# 		folderPath = f"data/{context.namespace}/{folder.folder}"
		# 		createNewFolder(datapackPath, folderPath)
		#
		# 		for file in folder.generation.initialFiles:
		# 			fileNS = file.namespace.replace(NAME_SPACE_VAR, context.namespace)
		# 			filePath = f"{datapackPath}/data/{fileNS}/{folder.folder}{file.name}"
		# 			with openOrCreate(filePath, 'w') as f:
		# 				f.write(file.contents.replace(NAME_SPACE_VAR, context.namespace))
		#
		# except OSError as e:
		# 	getSession().showAndLogError(e)
		# else:
		# 	self.redraw('DatapackFilesEditor._createNewDatapackGUI(...)')
		return

	def _refreshDependencies(self) -> None:
		self.model().analyzeRoots()
		self.model().analyzeDependencies()

	def _onContextMenu(self, data: FilesTreeItem, column: int):
		isMutableDict = dict(enabled=not data.isImmutable)

		menuItems: list[MenuItemData] = []

		if data.filePaths and isinstance(data.filePaths[0], FilesTreeItem):
			# not a real file or folder, but a 'virtual' folder:
			folderPath = data.folderPath
			if folderPath is None:
				return
			if isinstance(folderPath, tuple):
				folderPath = folderPath[0]
			menuItems = ContextMenuEntries.pathItems(folderPath)

		elif data.isFile:
			filePath = data.filePath
			if filePath is None:
				return
			menuItems = [
				('rename File', lambda: self._renameFileOrFolder(data), isMutableDict),
				('delete File', lambda: self._deleteFileFunc(filePath), isMutableDict),
				('', None),
				*ContextMenuEntries.fileItems(filePath, openFunc=self._openFunc)
			]

		else:
			# it is a 'real' folder:
			folderPath = data.folderPath
			if folderPath is None:
				return
			menuItems = [
				('new File', lambda p=folderPath: createNewFileGUI(p, self._gui, self._openFunc), isMutableDict),
				('new Folder', lambda p=folderPath: createNewFolderGUI(p, self._gui), isMutableDict),
				('rename Folder', lambda: self._renameFileOrFolder(data), isMutableDict),
				('delete Folder', lambda: self._deleteFolderFunc(folderPath), isMutableDict),
				('', None),
				*ContextMenuEntries.pathItems(folderPath)
			]

		with self._gui.popupMenu(atMousePosition=True) as menu:
			menu.addItems(menuItems)

	def filteredProjectsFilesTreeGUI(
			self,
			gui: DatapackEditorGUI,
			projectRoots: list[ProjectRoot],
			dependencies: list[Root],
			onDoubleClick : Optional[Callable[[FilesTreeItem], None]] = None,
			onContextMenu : Optional[Callable[[FilesTreeItem, int], None]] = None,
			onCopy        : Optional[Callable[[FilesTreeItem], Optional[str]]] = None,
			onCut         : Optional[Callable[[FilesTreeItem], Optional[str]]] = None,
			onPaste       : Optional[Callable[[FilesTreeItem, str], None]] = None,
			onDelete      : Optional[Callable[[FilesTreeItem], None]] = None,
			isSelected    : Optional[Callable[[FilesTreeItem], bool]] = None,

	):
		allAutocompleteStrings, projectItems = self.buildFilesTreeRoot(projectRoots, dependencies)

		with gui.vLayout(seamless=True):
			with gui.hLayout(seamless=True):
				filterStr = gui.filterTextField(None, allAutocompleteStrings, shortcut=QKeySequence.Find).lower()
				totalFilesCount = len(allAutocompleteStrings)
				filteredFilesCount, filteredProjectItems = self.filterFiles(totalFilesCount, filterStr, projectItems)
				gui.toolButton(f'{filteredFilesCount:,} of {totalFilesCount:,}',)

			gui.tree(
				DataTreeBuilder(
					FilesTreeRoot(filteredProjectItems),
					_filesTreeChildrenMaker,
					_labelMaker,
					_iconMaker,
					_toolTipMaker,
					columnCount=2,
					suppressUpdate=False,
					showRoot=False,
					onDoubleClick=onDoubleClick,
					onContextMenu=onContextMenu,
					onCopy=onCopy,
					onCut=onCut,
					onPaste=onPaste,
					onDelete=onDelete,
					isSelected=isSelected,
					getId=lambda x: x.label,
				),
				loadDeferred=True,
			)

	def filterFiles(self, totalFilesCount: int, filterStr: str, projectItems: list[AnyFilesTreeElement]) -> tuple[int, list[AnyFilesTreeElement]]:
		if filterStr:
			filteredFilesCount, filteredProjectItems = self._filterFilesInternal(filterStr, projectItems)
		else:
			filteredFilesCount = totalFilesCount
			filteredProjectItems = projectItems
		return filteredFilesCount, filteredProjectItems

	def _filterFilesInternal(self, filterStr: str, projectItems: list[AnyFilesTreeElement]) -> tuple[int, list[AnyFilesTreeElement]]:
		filteredFilesCount = 0
		filteredProjectItems = []
		for projItem in projectItems:
			if isinstance(projItem, FilesTreeRoot):
				filteredFilesCount2, _ = self._filterFilesInternal(filterStr, projItem.projects)
				filteredFilesCount += filteredFilesCount2
				filteredProjectItems.append(projItem)
			else:
				projItem.filePaths = [fp for fp in projItem.filePaths if filterStr in fp.virtualPath.lower()]
				if projItem.filePaths:
					filteredFilesCount += len(projItem.filePaths)
					filteredProjectItems.append(projItem)

		return filteredFilesCount, filteredProjectItems

	def buildFilesTreeRoot(self, projectRoots: list[ProjectRoot], dependencies: list[Root]) -> tuple[list[str], list[AnyFilesTreeElement]]:
		# autocomplete strings:
		allAutocompleteStrings: list[str] = []
		projectItems: list[AnyFilesTreeElement] = []
		for proj in projectRoots:
			self.handleRoot(proj, allAutocompleteStrings, projectItems, icons.project)

		dependenciesItems = []
		for proj in dependencies:
			self.handleRoot(proj, allAutocompleteStrings, dependenciesItems, icons.book)
		dependenciesItem = FilesTreeRoot(dependenciesItems, "Dependencies", icons.sitemap)
		projectItems.append(dependenciesItem)
		return allAutocompleteStrings, projectItems

	def handleRoot(self, root: Root, allAutocompleteStringsIO: list[str], projectItemsIO: list[FilesTreeItem], icon: QIcon) -> None:
		rootName = root.name
		filesForProj = []
		isImmutable = not isinstance(root, ProjectRoot)
		isArchive = isImmutable
		projItem = FilesTreeItem(rootName, icon, rootName + '/', (root.normalizedLocation, ''), filesForProj, isImmutable, isArchive)
		filesIndex = root.indexBundles.setdefault(FilesIndex)
		filesForProj.extend(filesIndex.folders.values())
		filesForProj.extend(filesIndex.files.values())
		allAutocompleteStringsIO.extend(map(attrgetter('virtualPath'), filesForProj))
		# for fullPath in filesIndex.folders.values():
		# 	# getRight:
		# 	# virtualPath = rootName + fullPath[1]
		# 	# allAutocompleteStringsIO.append(virtualPath)
		# 	# filesForProj.append(FileEntry(fullPath, rootName + fullPath[1], False))
		# 	filesForProj.append(fullPath)
		# for fullPath in filesIndex.files.values():
		# 	# getRight:
		# 	# virtualPath = rootName + fullPath[1]
		# 	# allAutocompleteStringsIO.append(virtualPath)
		# 	# filesForProj.append(FileEntry(fullPath, rootName + fullPath[1], True))
		# 	filesForProj.append(fullPath)
		if True or projItem.filePaths:
			projectItemsIO.append(projItem)


def _labelMaker(data: FilesTreeItem, column: int) -> str:
	return (data.label, str(len(data.filePaths)))[column]


def _iconMaker(data: FilesTreeItem, column: int) -> QIcon:
	return data.icon if column == 0 else None
	# if data.isFile:
	# 	return icons.file_code
	# elif data.isArchive:
	# 	return icons.archive
	# return icons.folderInTree


def _toolTipMaker(data: FilesTreeItem, column: int) -> str:
	return data.commonVPath


def _filesTreeChildrenMaker(data: FilesTreeItem) -> list[AnyFilesTreeElement]:
	if isinstance(data, FilesTreeRoot):
		return data.projects

	filePathsCount = len(data.filePaths)
	if data.isFile or filePathsCount == 0:
		return []

	children: dict[str, FilesTreeItem] = {}
	cVPathLen = len(data.commonVPath)
	isImmutable = data.isImmutable
	for entry in data.filePaths:
		if data.commonPath == entry.fullPath:
			continue
		index2 = entry.virtualPath.find('/', cVPathLen)
		isFile = index2 == -1
		if isFile:
			index2 = len(entry.virtualPath)
		label = entry.virtualPath[cVPathLen:index2]

		child = children.get(label, None)
		if child is None:
			suffix = label if isFile else f'{label}/'
			icon = icons.file_code if isFile else icons.folderInTree
			children[label] = FilesTreeItem(
				label,
				icon,
				f'{data.commonVPath}{suffix}',
				(data.commonPath[0], f'{data.commonPath[1]}{suffix}'),
				[entry],
				isImmutable
			)
		else:
			child.filePaths.append(entry)

	return sorted(children.values(), key=lambda x: (x.isFile, x.label.lower()))


def createNewFileGUI(folderPath: FilePath, gui: DatapackEditorGUI, openFunc: Callable[[FilePath], None]):
	# todo: createNewFileGUI(...)
	getSession().showAndLogWarning(None, "createNewFileGUI()... not yet implemented")
	# nsHandlers = getEntryHandlersForFolder(folderPath, getSession().datapackData.structure)
	# extensions = [h.extension for ns, h, _ in nsHandlers]
	# CUSTOM_EXT = "[custom]"
	# extensions.append(CUSTOM_EXT)
	#
	# @dataclass
	# class Context:
	# 	extension: int = 0
	# 	name: str = "untitled"
	#
	# def guiFunc(gui: DatapackEditorGUI, context: Context) -> Context:
	# 	context.name = gui.textField(context.name, "name:")
	# 	context.extension = gui.radioButtonGroup(context.extension, extensions, "extension:")
	# 	return context
	#
	# context = Context()
	# context, isOk = gui.askUserInput(f"new File", context, guiFunc)
	# if not isOk:  # or not context.name:
	# 	return
	#
	# ext = extensions[context.extension]
	# if ext == CUSTOM_EXT:
	# 	ext = ''
	# try:
	# 	filePath = createNewFile(folderPath, context.name.removesuffix(ext) + ext)
	# 	openFunc(filePath)
	# except OSError as e:
	# 	getSession().showAndLogError(e, "Cannot create file")
	return


def createNewFolderGUI(folderPath: FilePath, gui: DatapackEditorGUI):
	name, ok = gui.askUserInput('New Folder', 'New folder')
	if not ok or not name:
		return

	try:
		createNewFolder(folderPath, name)
	except OSError as e:
		getSession().showAndLogError(e, "Cannot create folder")


# Non-GUI stuff:


class _FileSysytemChangeHandler(FileSystemEventHandler):
	"""
	Base file system event handler that you can override methods from.
	"""

	def __init__(self, root: Root, project: Project):
		super(_FileSysytemChangeHandler, self).__init__()
		self._project: Project = project
		self._root: Root = root

	def on_any_event(self, event):
		"""Catch-all event handler.

		:param event:
			The event object representing the file system event.
		:type event:
			:class:`FileSystemEvent`
		"""
		path = normalizeDirSeparatorsStr(event.src_path)
		if event.is_directory:
			path = path + '/'
		if (jf := splitPath(path, self._root.normalizedLocation)) is not None:
			path = jf
		event.split_src_path = path

	def on_moved(self, event: FileMovedEvent):
		"""Called when a file or a directory is moved or renamed.

		:param event:
			Event representing file/directory movement.
		:type event:
			:class:`DirMovedEvent` or :class:`FileMovedEvent`
		"""
		if event.is_directory:
			index = self._root.indexBundles.setdefault(FilesIndex).folders
			index.discardSource(event.split_src_path)
			if (jf := splitPath(event.dest_path, self._root.normalizedLocation)) is not None:
				index.add(jf[1], jf, FileEntry(jf, f'{self._root.name}/{jf[1]}', False))
			# TODO: analyze Files for DirMovedEvent
		else:
			for index in self._root.indexBundles:
				index.discardSource(event.split_src_path)
			if (jf := splitPath(event.dest_path, self._root.normalizedLocation)) is not None:
				index = self._root.indexBundles.setdefault(FilesIndex).files
				index.add(jf[1], jf, FileEntry(jf, f'{self._root.name}/{jf[1]}', True))
				for aspect in self._project.aspects:
					if aspect.aspectFeatures.analyzeFiles:
						aspect.analyzeFile(self._root, jf)

	def on_created(self, event: FileCreatedEvent):
		"""Called when a file or directory is created.

		:param event:
			Event representing file/directory creation.
		:type event:
			:class:`DirCreatedEvent` or :class:`FileCreatedEvent`
		"""
		path = event.split_src_path
		if event.is_directory:
			self._root.indexBundles.setdefault(FilesIndex).folders.add(path[1], path, FileEntry(path, f'{self._root.name}/{path[1]}', False))
		else:
			index = self._root.indexBundles.setdefault(FilesIndex).files
			index.add(path[1], path, FileEntry(path, f'{self._root.name}/{path[1]}', True))
			for aspect in self._project.aspects:
				if aspect.aspectFeatures.analyzeFiles:
					aspect.analyzeFile(self._root, path)

	def on_deleted(self, event: FileDeletedEvent):
		"""Called when a file or directory is deleted.

		:param event:
			Event representing file/directory deletion.
		:type event:
			:class:`DirDeletedEvent` or :class:`FileDeletedEvent`
		"""
		path = event.split_src_path
		if event.is_directory:
			for index in self._root.indexBundles:
				index.discardDirectory(path)
		else:
			# due to a bug (?) in Watchdog on Windows, a deleted directory will cause a FileDeletedEvent instead of a DirDeletedEvent:
			index = self._root.indexBundles.setdefault(FilesIndex).folders
			index.discardSource(joinFilePath(path, '/'))
			# normal FileDeletedEvent handling:
			for index in self._root.indexBundles:
				index.discardSource(path)

	def on_modified(self, event: FileModifiedEvent):
		"""Called when a file or directory is modified.

		:param event:
			Event representing file/directory modification.
		:type event:
			:class:`DirModifiedEvent` or :class:`FileModifiedEvent`
		"""
		if event.is_directory:
			pass
		else:
			path = event.split_src_path
			for index in self._root.indexBundles:
				index.discardSource(path)
			index = self._root.indexBundles.setdefault(FilesIndex).files
			index.add(path[1], path, FileEntry(path,  f'{self._root.name}/{path[1]}', True))
			for aspect in self._project.aspects:
				if aspect.aspectFeatures.analyzeFiles:
					aspect.analyzeFile(self._root, path)

	def on_closed(self, event: FileClosedEvent):
		"""Called when a file opened for writing is closed.

		:param event:
			Event representing file closing.
		:type event:
			:class:`FileClosedEvent`
		"""
		pass


@dataclass
class FilesAspect(ProjectAspect, features=AspectFeatures(analyzeRoots=True)):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return AspectType('FilesAspect')

	def getDependencies(self, root: Root) -> list[DependencyDescr]:
		return []

	def resolveDependency(self, dependencyDescr: DependencyDescr) -> Optional[Root]:
		pass

	def onRootAdded(self, root: Root, project: Project) -> None:
		filesystemEvents.FILESYSTEM_OBSERVER.schedule("dpe:files_aspect", root.normalizedLocation, _FileSysytemChangeHandler(root, project))

	def onRootRemoved(self, root: Root, project: Project) -> None:
		filesystemEvents.FILESYSTEM_OBSERVER.unschedule("dpe:files_aspect", root.normalizedLocation)

	def analyzeFile(self, root: Root, path: FilePathTpl) -> None:
		pass
		# idx = root.indexBundles.setdefault(FilesIndex).files
		# idx.add(path[1], path, path)

	def analyzeRoot(self, root: Root) -> None:
		location = root.normalizedLocation
		if location.endswith('.jar'):  # we don't need '.class' files. This is not a Java IDE.
			pathInFolder = 'data/**'
			pathInZip = 'data/**'
		else:
			pathInFolder = '/**'
			pathInZip = '/**'
		pif = SearchPath(pathInFolder, location.rstrip('/'))
		piz = pathInZip

		# rawLocalFiles = getAllFilesFromSearchPath(location, pif, piz, extensions=tuple(), excludes=None)
		if not pif.divider:
			return

		if not os.path.exists(location):
			return
		if os.path.isdir(location):
			rawLocalFiles, rawLocalFolders = getAllFilesFoldersFromFolder(location, pif.divider)
		elif os.path.isfile(location):
			rawLocalFiles = getAllFilesFromArchive(location, piz, (), ())
			rawLocalFolders = []
		else:
			return
		idx = root.indexBundles.setdefault(FilesIndex).files
		for jf in rawLocalFiles:
			# TODO: fix when name of root changes the files tree breaks for that root because the virtualPaths are invalid, because it is created here:
			idx.add(jf[1], jf, FileEntry(jf, f'{root.name}/{jf[1]}', True))

		idx = root.indexBundles.get(FilesIndex).folders
		for jf in rawLocalFolders:
			# TODO: fix when name of root changes the files tree breaks for that root because the virtualPaths are invalid, because it is created here:
			idx.add(jf[1], jf, FileEntry(jf, f'{root.name}/{jf[1]}', False))


@dataclass
class FilesIndex(IndexBundleAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return AspectType('FilesIndex')

	files: Index[str, FileEntry] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	folders: Index[str, FileEntry] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))


class FileEntry(NamedTuple):
	fullPath: FilePathTpl
	virtualPath: str  # = dataclasses.field(compare=False)
	isFile: bool


def createNewFile(folderPath: FilePath, name: str) -> FilePath:
	if isinstance(folderPath, tuple):
		filePath = folderPath[0], os.path.join(folderPath[1], name)
	else:
		filePath = (folderPath, name)
	with openOrCreate(os.path.join(*filePath), 'a'):
		pass  # creates the File
	return normalizeDirSeparators(filePath)


def createNewFolder(folderPath: FilePath, name: str):
	if isinstance(folderPath, tuple):
		filePath = folderPath[0], os.path.join(folderPath[1], name)
		joinedFilePath = os.path.join(*filePath, '_ignoreMe.txt')
	else:
		filePath = os.path.join(folderPath, name)
		joinedFilePath = os.path.join(filePath, '_ignoreMe.txt')

	with openOrCreate(joinedFilePath, 'w'):
		pass  # creates the File
