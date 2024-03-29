from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QDialog, QWidget

from cat.GUI import SizePolicy
from cat.GUI.components.treeBuilders import DataListBuilder
from cat.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from cat.utils.profiling import ProfiledAction, TimedAction
from gui.datapackEditorGUI import DatapackEditorGUI
from base.model.documents import Document
from base.model.session import getSession


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
		with gui.hLayout():
			if gui.button('Profile!', enabled=self._selectedDocument is not None):
				with ProfiledAction(fileName):
					for _ in range(self._repetitions):
						self._selectedDocument.parse(self._selectedDocument.content)
			if gui.button('Time!', enabled=self._selectedDocument is not None):
				with TimedAction(fileName):
					for _ in range(self._repetitions):
						self._selectedDocument.parse(self._selectedDocument.content)

		gui.title("Validating:")
		with gui.hLayout():
			if gui.button('Profile!', enabled=self._selectedDocument is not None):
				with ProfiledAction(fileName):
					for _ in range(self._repetitions):
						self._selectedDocument.validate()
			if gui.button('Time!', enabled=self._selectedDocument is not None):
				with TimedAction(fileName):
					for _ in range(self._repetitions):
						self._selectedDocument.validate()

		gui.addVSpacer(0, SizePolicy.Expanding)
