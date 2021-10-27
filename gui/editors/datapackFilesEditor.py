import os
from typing import Optional

from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, LocalFilesPropInfo, ContextMenuEntries, FilesTreeItem, createNewFile
from model.Model import World, Datapack

from model.parsingUtils import Position
from model.pathUtils import FilePath


class DatapackFilesEditor(EditorBase[World]):
	def __init__(self, model: World):
		super(DatapackFilesEditor, self).__init__(model)

	def _openFunc(self, filePath: FilePath, selectedPosition: Optional[Position] = None):
		self.window()._tryOpenOrSelectDocument(filePath, selectedPosition)

	def _onDoubleClick(self, data: FilesTreeItem):
		if data.isFile:
			self._openFunc(data.filePaths[0].fullPath)

	def _deleteFileFunc(self, path: FilePath):
		_, __, name = path[1].rpartition('/')
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
				menu.addItems(ContextMenuEntries.fileItems(filePath, openFunc=self._openFunc))
				menu.addSeparator()
				menu.addItem('delete file', lambda: self._deleteFileFunc(filePath))
		else:
			folderPath = data.folderPath
			if folderPath is None:
				return
			with self._gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('new File', lambda p=folderPath: createNewFile(p, self._gui, self._openFunc), enabled=not data.isImmutable)
				menu.addSeparator()
				menu.addItems(ContextMenuEntries.pathItems(folderPath))

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		gui.filteredProjectsFilesTree3(
			self.model().datapacks,
			[
				LocalFilesPropInfo(Datapack.files, 'data/', 'data'),
			],
			isImmutable=Datapack.isZipped.get,
			onDoubleClick=self._onDoubleClick,
			onContextMenu=self._onContextMenu,

			roundedCorners=self.roundedCorners(),
			overlap=self.overlap()
		)

		gui.propertyField(self.model(), self.model().selectedMinecraftExecProp)


__all__ = [
	'DatapackFilesEditor'
]
