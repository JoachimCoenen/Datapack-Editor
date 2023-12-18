from __future__ import annotations

from operator import attrgetter
from typing import Optional, Sequence

from PyQt5 import sip

from base.model.documents import Document, ErrorCounts, getErrorCounts
from base.model.session import getSession
from base.model.utils import GeneralError
from base.plugin import PLUGIN_SERVICE, PluginBase, SideBarOptions
from cat.GUI.pythonGUI import EditorBase, TabOptions
from gui.datapackEditorGUI import DatapackEditorGUI
from gui.icons import icons


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('DocumentErrors', DocumentErrorsPlugin())


class DocumentErrorsPlugin(PluginBase):

	def dependencies(self) -> set[str]:
		return set()

	def optionalDependencies(self) -> set[str]:
		return set()  # ordering of gui elements

	def bottomBarTabs(self) -> list[SideBarOptions]:
		return [
			SideBarOptions(TabOptions('Errors', icon=icons.error), DocumentErrorsGUI, DocumentErrorsSummaryGUI),
		]


class DocumentErrorsGUI(EditorBase[None]):
	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		document = getAndConnectDocument(self)
		# actual GUI
		if document is not None:
			errors = sorted(document.errors, key=attrgetter('position'))
		else:
			errors: Sequence[GeneralError] = []

		gui.errorsList(
			errors,
			onDoubleClicked=lambda e: getSession().documents.selectDocument(document, e.span),
		)


class DocumentErrorsSummaryGUI(EditorBase[None]):
	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		document = getAndConnectDocument(self)
		# actual GUI
		with gui.hLayout(seamless=True):
			if document is not None:
				gui.errorsSummaryGUI(getErrorCounts(document.errors))
			else:
				gui.errorsSummaryGUI(ErrorCounts())


def getAndConnectDocument(self: EditorBase[None]) -> Optional[Document]:
	document: Optional[Document] = getSession().documents.currentView.selectedDocument
	key = type(self).__name__
	# connect to errorChanged Signal:
	Document.onErrorsChanged.disconnectFromAllInstances(key=key)
	if document is not None:
		document.onErrorsChanged.connect(key, lambda d: self.redrawLater('onErrorsChanged') if not sip.isdeleted(self) else None)
	getSession().documents.onSelectedDocumentChanged.reconnect(key, lambda: self.redrawLater('onSelectedDocumentChanged') if not sip.isdeleted(self) else None)
	return document
