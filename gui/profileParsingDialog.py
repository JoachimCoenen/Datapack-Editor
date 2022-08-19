from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QDialog, QWidget

from Cat.CatPythonGUI.GUI import SizePolicy
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder
from Cat.utils.profiling import ProfiledAction
from gui.datapackEditorGUI import DatapackEditorGUI
from session.documents import Document
from session.session import getSession


class ProfileParsingDialog(CatFramelessWindowMixin, QDialog):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=DatapackEditorGUI, parent=parent)

		self._selectedDocument: Optional[Document] = None
		self._repetitions: int = 10
		self.setWindowTitle('Profile Parsing')

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		self._selectedDocument = gui.tree(
			DataListBuilder(
				list(getSession().documents.allOpenedDocuments()),
				labelMaker=lambda d, i: d.fileName,
				iconMaker=None,
				toolTipMaker=lambda d, i: d.filePathForDisplay,
				columnCount=1
			),
		).selectedItem

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		gui.title("Settings:")
		fileName = self._selectedDocument.fileName if self._selectedDocument is not None else '---'
		fileNameSuffix = gui.textField(None, label='file name suffix', enabled=True)
		fileName = gui.textField(fileName + fileNameSuffix, label='file name', enabled=False)
		self._repetitions = gui.intField(self._repetitions, label='repetitions', min=1, enabled=True)
		gui.title("Parsing:")
		if gui.button('GO!', enabled=self._selectedDocument is not None):
			with ProfiledAction(fileName):
				for _ in range(self._repetitions):
					self._selectedDocument.parse(self._selectedDocument.content)

		gui.title("Validating:")
		if gui.button('GO!', enabled=self._selectedDocument is not None):
			with ProfiledAction(fileName):
				for _ in range(self._repetitions):
					self._selectedDocument.validate()

		gui.addVSpacer(0, SizePolicy.Expanding)
