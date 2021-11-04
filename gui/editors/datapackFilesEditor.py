import os
from typing import Optional

from PyQt5.QtGui import QIcon

from Cat.icons import icons
from Cat.utils import DeferredCallOnceMethod
from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, LocalFilesPropInfo, ContextMenuEntries, FilesTreeItem, createNewFile, createNewFolder
from model.Model import World, Datapack

from model.parsingUtils import Position
from model.pathUtils import FilePath
from session.session import getSession


class DatapackFilesEditor(EditorBase[World]):
	def __init__(self, model: World):
		super(DatapackFilesEditor, self).__init__(model)

	def _openFunc(self, filePath: FilePath, selectedPosition: Optional[Position] = None):
		self.window()._tryOpenOrSelectDocument(filePath, selectedPosition)

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
			newPath = (path[0], f'{lPath}/{newName}')
			joinedNewPath = os.path.join(*newPath)
			if os.path.exists(joinedNewPath):
				self._gui.showInformationDialog(f"The name \"{newName}\" cannot be used.", "Another file with the same name already exists.")
			else:
				try:
					os.rename(os.path.join(*path), joinedNewPath)
				except OSError as e:
					self._gui.showAndLogError(e)
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
			self.redraw()

	def _deleteFileFunc(self, path: FilePath):
		_, __, name = path[1].rstrip('/').rpartition('/')
		if self._gui.askUser(f"Delete file '{name}'?", 'this cannot be undone!'):
			try:
				os.unlink(os.path.join(*path))
			except OSError as e:
				self._gui.showAndLogError(e)
			self.redraw()
			# TODO: maybe close opened file?

	def _onContextMenu(self, data: FilesTreeItem, column: int):
		if not data.filePaths:
			return
		if isinstance(data.filePaths[0], FilesTreeItem):
			return

		if data.isFile:
			filePath = data.filePaths[0].fullPath
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('rename File', lambda: self._renameFileOrFolder(data))
				menu.addItem('delete File', lambda: self._deleteFileFunc(filePath))
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.fileItems(filePath, openFunc=self._openFunc))
		else:
			folderPath = data.folderPath
			if folderPath is None:
				return
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('new File', lambda p=folderPath: createNewFile(p, self._gui, self._openFunc), enabled=not data.isImmutable)
				menu.addItem('new Folder', lambda p=folderPath: createNewFolder(p, self._gui), enabled=not data.isImmutable)
				menu.addItem('rename Folder', lambda: self._renameFileOrFolder(data))
				menu.addItem('delete Folder', lambda: self._deleteFileFunc(folderPath))
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.pathItems(folderPath))

	def _iconMaker(self, data: FilesTreeItem, column: int) -> QIcon:
		if data.isFile:
			return icons.file_code
		elif data.isArchive:
			return icons.archive
		return icons.folderInTree

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		gui.filteredProjectsFilesTree3(
			self.model().datapacks,
			[
				LocalFilesPropInfo(Datapack.files, 'data/', 'data'),
			],
			isImmutable=Datapack.isZipped.get,
			onDoubleClick=self._onDoubleClick,
			onContextMenu=self._onContextMenu,
			iconMaker=self._iconMaker,
			roundedCorners=self.roundedCorners(),
			overlap=self.overlap()
		)

		gui.propertyField(self.model(), self.model().selectedMinecraftExecProp)


__all__ = [
	'DatapackFilesEditor'
]
