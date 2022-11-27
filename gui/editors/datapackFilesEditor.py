import os
from typing import Optional

from Cat.CatPythonGUI.GUI import adjustOverlap, maskCorners, CORNERS, SizePolicy, NO_MARGINS
from Cat.CatPythonGUI.GUI.pythonGUI import EditorBase
from Cat.icons import icons
from Cat.utils import DeferredCallOnceMethod
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries, FilesTreeItem, createNewFileGUI, createNewFolderGUI
from base.model.utils import Span
from base.model.pathUtils import FilePath
from sessionOld.session import getSession, Session


class DatapackFilesEditor(EditorBase[Session]):

	def _openFunc(self, filePath: FilePath, selectedSpan: Optional[Span] = None):
		self.window()._tryOpenOrSelectDocument(filePath, selectedSpan)

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

	def _newDatapackDialog(self):
		pass

	def _createNewDatapackGUI(self) -> None:
		self._gui.showWarningDialog("Out of Order", "This feature is currently out of order.")
		return
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

	def _refreshDependencies(self) -> None:
		self.model().project.deepDependenciesProp.reset(self.model().project)

	def _onContextMenu(self, data: FilesTreeItem, column: int):
		if not data.filePaths:
			return

		isMutable = not data.isImmutable

		if isinstance(data.filePaths[0], FilesTreeItem):
			# we have a data pack:
			folderPath = data.folderPath
			if folderPath is None:
				return
			if isinstance(folderPath, tuple):
				folderPath = folderPath[0]
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('edit description', lambda: self._openFunc((folderPath, 'pack.mcmeta')))
				# menu.addItem('rename Folder', lambda: self._renameFileOrFolder(data), enabled=isMutable)
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.pathItems(folderPath))
		elif data.isFile:
			filePath = data.filePaths[0].fullPath
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('rename File', lambda: self._renameFileOrFolder(data), enabled=isMutable)
				menu.addItem('delete File', lambda: self._deleteFileFunc(filePath), enabled=isMutable)
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.fileItems(filePath, openFunc=self._openFunc))
		else:
			folderPath = data.folderPath
			if folderPath is None:
				return
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('new File', lambda p=folderPath: createNewFileGUI(p, self._gui, self._openFunc), enabled=isMutable)
				menu.addItem('new Folder', lambda p=folderPath: createNewFolderGUI(p, self._gui), enabled=isMutable)
				menu.addItem('rename Folder', lambda: self._renameFileOrFolder(data), enabled=isMutable)
				menu.addItem('delete Folder', lambda: self._deleteFileFunc(folderPath), enabled=False and isMutable)
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.pathItems(folderPath))

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.vLayout(verticalSpacing=0):
			gui.filteredProjectsFilesTree1(
				self.model().project.deepDependencies,
				onDoubleClick=self._onDoubleClick,
				onContextMenu=self._onContextMenu,
				overlap=adjustOverlap(self.overlap(), (None, None, None, 0)),
				roundedCorners=maskCorners(self.roundedCorners(), CORNERS.TOP),
			)

			with gui.hPanel(
				horizontalSpacing=0,
				contentsMargins=NO_MARGINS,
				overlap=adjustOverlap(self.overlap(), (None, 1, None, None)),
				roundedCorners=maskCorners(self.roundedCorners(), CORNERS.BOTTOM),
			):
				gui.addHSpacer(5, SizePolicy.Expanding)
				if gui.toolButton(
					icon=icons.add,
					tip="create new Datapack",
					overlap=adjustOverlap(self.overlap(), (0, 1, 0, None)),
					roundedCorners=maskCorners(self.roundedCorners(), CORNERS.NONE),
					enabled=True
				):
					self._createNewDatapackGUI()
				if gui.toolButton(
					icon=icons.refresh,
					tip="refresh dependencies",
					overlap=adjustOverlap(self.overlap(), (1, 1, None, None)),
					roundedCorners=maskCorners(self.roundedCorners(), CORNERS.BOTTOM_RIGHT),
					enabled=True
				):
					self._refreshDependencies()


__all__ = [
	'DatapackFilesEditor'
]
