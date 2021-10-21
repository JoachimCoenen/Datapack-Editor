from typing import TypeVar

from Cat.CatPythonGUI.GUI import CORNERS, NO_OVERLAP
from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, LocalFilesPropInfo
from model.Model import World, Datapack

__all__ = [
	'DatapackFilesEditor'
]

class DatapackFilesEditor(EditorBase[World]):

	def __init__(self, model: World):
		super(DatapackFilesEditor, self).__init__(model)

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		gui.filteredProjectsFilesTree3(
			self.model().datapacks,
			[
				LocalFilesPropInfo(Datapack.files, 'data/', 'data'),
			],

			self.window()._tryOpenOrSelectDocument,
			roundedCorners=self.roundedCorners(),
			overlap=self.overlap()
		)





