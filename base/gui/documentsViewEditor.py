from typing import Optional

from PyQt5.QtCore import Qt

from Cat.GUI.pythonGUI import EditorBase, TabOptions
from Cat.GUI.components.catWidgetMixins import CatFramedWidgetMixin
from Cat.GUI.enums import TabPosition, SizePolicy
from gui.icons import icons
from Cat.utils.collections_ import OrderedMultiDict
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries
from base.gui.documentEditors import getDocumentEditor
from keySequences import KEY_SEQUENCES
from base.model.documentHandling import View, ViewContainer
from base.model.documents import Document
from base.model.session import getSession


class DocumentsViewEditor(EditorBase[View], CatFramedWidgetMixin):
	def postInit(self) -> None:
		self._shouldForceFocus: bool = self.model().isCurrent

	def onSetModel(self, new: View, old: Optional[View]) -> None:
		super(DocumentsViewEditor, self).onSetModel(new, old)
		if old is not None:
			old.onDocumentsChanged.disconnect('editorRedraw')
			old.onMadeCurrent.disconnect('editor')
		new.onDocumentsChanged.reconnect('editorRedraw', lambda: self.redraw('onDocumentsChanged'))
		new.onMadeCurrent.reconnect('editor', self._forceFocus)
		new.onSelectedDocumentChanged.reconnect('editor', self._forceFocus)
		self._shouldForceFocus = self.model().isCurrent

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.vPanel(seamless=True, windowPanel=True):
			with gui.hLayout(seamless=True):
				self.documentsTabBarGUI(gui, position=TabPosition.North)
			with gui.vLayout(seamless=True):  # , windowPanel=True):
				self.documentsGUI(gui)

	def documentsTabBarGUI(self, gui: DatapackEditorGUI, position: TabPosition = TabPosition.North):
		view = self.model()
		tabs = OrderedMultiDict((
			(document, TabOptions(document.fileName + (' *' if document.documentChanged else '   '), tip=document.filePathForDisplay, icon=icons.file_code))
			for document in view.documents
		))

		try:
			selectedTab = list(tabs.keys()).index(view.selectedDocument)
		except ValueError:
			selectedTab = None

		if tabs:
			with gui.hPanel(seamless=True, windowPanel=True):
				index = gui.tabBar(
					list(tabs.values()),
					selectedTab=selectedTab,
					drawBase=False,
					documentMode=True,
					expanding=False,
					position=position,
					movable=True,
					tabsClosable=True,
					onTabMoved=self._tabMoved,
					onTabCloseRequested=self._tabCloseRequested,
					onContextMenuRequested=self._showFileContextMenu,
				)

			if index in range(len(tabs)):
				if index != selectedTab:
					view.manager.showDocument(list(tabs.keys())[index])
			else:
				view.selectDocument(None)
		else:
			gui.addHSpacer(5, SizePolicy.Expanding)
			view.selectDocument(None)

		if view.documents:
			if gui.toolButton(icon=icons.chevronDown):
				self._showOpenedDocumentsPopup(gui)

		if gui.toolButton(icon=icons.bars):  # , overlap=adjustOverlap(overlap, (1 if view.documents else 0, None, None, None if view.documents else 0)), roundedCorners=CORNERS.NONE):
			self._showViewsContextMenu()

	def _tabCloseRequested(self, index: int) -> None:
		view = self.model()
		if index in range(len(view.documents)):
			doc = view.documents[index]
			getSession().documents.safelyCloseDocument(doc)

	def _tabMoved(self, from_: int, to: int) -> None:
		view = self.model()
		print(f"tab {from_} moved to {to}.")

		indexRange = range(len(view.documents))
		if from_ in indexRange and to in indexRange:
			doc = view.documents[from_]
			view.moveDocument(doc, to)

	def _showFileContextMenu(self, index: int) -> None:
		view = self.model()
		gui = self._gui
		if index not in range(len(view.documents)):
			return
		doc = view.documents[index]

		documents = getSession().documents

		with gui.popupMenu(True) as menu:
			# menu.addItem("move to new View", lambda: documents.moveDocument(doc, documents.addView()))
			menu.addItem(
				"&move to View...",
				[
					(f"#&{i + 1}", lambda i=i: documents.moveDocument(doc, documents.views[i]))
					for i in range(len(documents.views))
				]
			)
			menu.addSeparator()
			menu.addItems(ContextMenuEntries.pathItems(doc.filePath))

	def _showViewsContextMenu(self) -> None:
		view = self.model()
		gui = self._gui
		with gui.popupMenu(True) as menu:
			menu.addItem("split horizontally", lambda: view.splitView(False) and None)
			menu.addItem("split vertically", lambda: view.splitView(True) and None)
			menu.addSeparator()
			menu.addItem("close view", lambda: view.manager.safelyCloseView(view), enabled=len(view.documents) == 0)

	def documentsGUI(self, gui: DatapackEditorGUI) -> None:
		view = self.model()

		currentDocEditor = None

		if view.documents:
			selectedDocumentId = view.selectedDocument.filePathForDisplay if view.selectedDocument is not None else None
			with gui.stackedWidget(selectedView=selectedDocumentId) as stacked:
				for document in view.documents:
					with stacked.addView(id_=document.filePathForDisplay, seamless=True):
						documentEditorCls = getDocumentEditor(type(document))
						docEditor = gui.editor(
							documentEditorCls,
							document,
							onEditorFocusReceived=lambda fr: view.makeCurrent(),
							seamless=True
						)
						if document.filePathForDisplay == selectedDocumentId:
							currentDocEditor = docEditor
		else:  # no documents are opened:
			self._noDocumentOrProjectOpenedGUI(gui)

		if view.selectedDocument is None:
			currentDocEditor = None
		if currentDocEditor is not None:
			currentDocEditor.redrawLater('DocumentsViewEditor.documentsGUI(...)')
			if self._shouldForceFocus:
				currentDocEditor.setFocus()
		self._shouldForceFocus = False

	def _noDocumentOrProjectOpenedGUI(self, gui: DatapackEditorGUI) -> None:
		mg = gui.margin
		with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
			gui.addVSpacer(int(50 * gui.scale), SizePolicy.Expanding)
			if not getSession().hasOpenedProject:
				self._noProjectOpenedGUI(gui)
			else:
				self._noDocumentOpenedGUI(gui)
			gui.addVSpacer(int(50 * gui.scale), SizePolicy.Expanding)

	def _noDocumentOpenedGUI(self, gui: DatapackEditorGUI) -> None:
		gui.label('No Document Opened.', wordWrap=False, alignment=Qt.AlignCenter)
		gui.addVSpacer(gui.margin, SizePolicy.Fixed)
		gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.GO_TO_FILE.toString()}</font>' to search for a file.", wordWrap=False, alignment=Qt.AlignCenter)
		gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.NEW.toString()}</font>' to create a new file.", wordWrap=False, alignment=Qt.AlignCenter)
		gui.addVSpacer(int(50 * gui.scale), SizePolicy.Fixed)
		with gui.hLayout():
			gui.addHSpacer(int(20 * gui.scale), SizePolicy.Expanding)
			if gui.button("close View", icon=icons.close, hSizePolicy=SizePolicy.Fixed.value):
				self.model().manager.safelyCloseView(self.model())
			gui.addHSpacer(int(20 * gui.scale), SizePolicy.Expanding)

	def _noProjectOpenedGUI(self, gui: DatapackEditorGUI) -> None:
		gui.label('No project loaded.', wordWrap=False, alignment=Qt.AlignCenter)
		gui.addVSpacer(gui.margin, SizePolicy.Fixed)
		gui.label(f"Please open a project.", wordWrap=False, alignment=Qt.AlignCenter)
		gui.addVSpacer(gui.margin, SizePolicy.Fixed)
		with gui.hLayout():
			gui.addHSpacer(int(20 * gui.scale), SizePolicy.Expanding)
			if gui.framelessButton("Open / Create Project", icon=icons.project, tip="Load Project", default=True):
				self.window()._openOrCreateProjectDialog(gui)
			gui.addHSpacer(int(20 * gui.scale), SizePolicy.Expanding)

	def _showOpenedDocumentsPopup(self, gui: DatapackEditorGUI) -> None:
		view = self.model()
		selectedDocument = view.selectedDocument

		def onContextMenu(d: Document, _: int):
			print(f"showing ContextMenu for Document '{d.fileName}'")
			with gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('close', lambda: getSession().documents.safelyCloseDocument(d) and None, tip=f'close {d.filePath}')
				menu.addItems(ContextMenuEntries.pathItems(d.filePath))

		# calculate dimensions:
		width, height = self.__sizeForOpenedDocumentsPopup(gui, view.documents)

		selectedDocument = gui.searchableChoicePopup(
			selectedDocument,
			'Opened Files',
			view.documents,
			getSearchStr=lambda x: x.fileName,
			labelMaker=lambda x, i: (x.fileName, x.filePathForDisplay)[i],
			iconMaker=lambda x, i: None,
			toolTipMaker=lambda x, i: x.filePath,
			columnCount=1,
			onContextMenu=onContextMenu,
			reevaluateAllChoices=True,
			width=width,
			height=height,
		)

		if selectedDocument in view.documents:
			view.selectDocument(selectedDocument)
			view.makeCurrent()

	@staticmethod
	def __sizeForOpenedDocumentsPopup(gui: DatapackEditorGUI, documents: list[Document]) -> tuple[int, int]:
		# fm = gui.lastWidget.fontMetrics()
		fm = gui.host.fontMetrics()
		scale = gui.scale
		width: int = int(10 * scale)
		height: int = int(25 * scale)
		for d in documents:
			s = fm.size(Qt.TextSingleLine, d.fileName)
			width = max(s.width(), width)
			height += s.height()
		width += int((2 * 10) * scale) + 1
		height += int(24 * scale) + 1
		# clamp sizes:
		width = min(int(720 * scale), width)
		height = min(int(720 * scale), height)
		width += 2*13  # beware of window shadow
		height += 2*13  # beware of window shadow

		# hPadding = int((2 * 3) * scale)
		# listHeight = len(documents) * (fm.height() + hPadding)
		# height = max(listHeight, height)
		return width, height

	def _forceFocus(self) -> None:
		self._shouldForceFocus = self.model().isCurrent
		self.redraw('DocumentsViewEditor._forceFocus(...)')


class DocumentsViewsContainerEditor(EditorBase[ViewContainer]):

	def onSetModel(self, new: ViewContainer, old: Optional[ViewContainer]) -> None:
		super(DocumentsViewsContainerEditor, self).onSetModel(new, old)
		if old is not None:
			old.onViewsChanged.disconnect('editorRedraw')
		new.onViewsChanged.reconnect('editorRedraw', lambda: self.redraw('onViewsChanged'))

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		viewContainer = self.model()
		splitterFunc = gui.vSplitter if viewContainer.isVertical else gui.hSplitter

		with splitterFunc(handleWidth=gui.smallSpacing) as splitter:
			for view in viewContainer.views:
				with splitter.addArea(seamless=True):
					if isinstance(view, ViewContainer):
						gui.editor(DocumentsViewsContainerEditor, view, seamless=True).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')
					else:
						gui.editor(DocumentsViewEditor, view, seamless=True).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')


__all__ = ['DocumentsViewEditor', 'DocumentsViewsContainerEditor']
