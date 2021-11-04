from typing import Iterator, Iterable, Optional

from PyQt5.QtCore import Qt

from Cat.CatPythonGUI.GUI import NO_MARGINS, CORNERS, NO_OVERLAP, Overlap, RoundedCorners, adjustOverlap, maskCorners
from Cat.CatPythonGUI.GUI.catWidgetMixins import CatFramedWidgetMixin
from Cat.CatPythonGUI.GUI.enums import TabPosition, SizePolicy
from Cat.icons import icons
from Cat.utils.collections import OrderedMultiDict
from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, ContextMenuEntries
from gui.editors import TextDocumentEditor
from keySequences import KEY_SEQUENCES
from session.documentHandling import View
from session.documents import Document
from session.session import getSession


class DocumentsViewEditor(EditorBase[View], CatFramedWidgetMixin):
	def postInit(self) -> None:
		self._shouldForceFocus: bool = self.model().isCurrent

	def onSetModel(self, new: View, old: Optional[View]) -> None:
		super(DocumentsViewEditor, self).onSetModel(new, old)
		if old is not None:
			old.onDocumentsChanged.disconnect('editorRedraw')
			old.onMadeCurrent.disconnect('editor')
		new.onDocumentsChanged.disconnect('editorRedraw')
		new.onDocumentsChanged.connect('editorRedraw', self.redraw)
		new.onMadeCurrent.disconnect('editor')
		new.onMadeCurrent.connect('editor', self._forceFocus)
		new.onSelectedDocumentChanged.disconnect('editor')
		new.onSelectedDocumentChanged.connect('editor', self._forceFocus)
		self._shouldForceFocus = self.model().isCurrent

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		view = self.model()
		tabBarOverlap = (0, 0, 0, 1)
		with gui.vLayout(verticalSpacing=0):
			with gui.hPanel(contentsMargins=NO_MARGINS, horizontalSpacing=0, overlap=tabBarOverlap, roundedCorners=maskCorners(self.roundedCorners(), CORNERS.TOP), windowPanel=True):
				self.documentsTabBarGUI(gui, position=TabPosition.North, overlap=tabBarOverlap, roundedCorners=maskCorners(self.roundedCorners(), CORNERS.TOP))
			panelOverlap = NO_OVERLAP if view.documents else (0, 1, 0, 0)
			with gui.vPanel(contentsMargins=NO_MARGINS, overlap=panelOverlap, roundedCorners=maskCorners(self.roundedCorners(), CORNERS.BOTTOM), windowPanel=True):
				self.documentsGUI(gui)

	def documentsTabBarGUI(self, gui: DatapackEditorGUI, position: TabPosition = TabPosition.North, overlap: Overlap = (0, 0), roundedCorners: RoundedCorners = CORNERS.ALL):
		view = self.model()
		tabs = OrderedMultiDict((
			(document, (document.fileName + (' *' if document.documentChanged else '   '), ))
			for document in view.documents
		))

		try:
			selectedTab = list(tabs.keys()).index(view.selectedDocument)
		except ValueError:
			selectedTab = None

		def tabCloseRequested(index: int):
			if index in range(len(view.documents)):
				doc = view.documents[index]
				getSession().documents.safelyCloseDocument(doc)

		def tabMoved(from_: int, to: int):
			print(f"tab {from_} moved to {to}.")

			indexRange = range(len(view.documents))
			if from_ in indexRange and to in indexRange:
				doc = view.documents[from_]
				view.moveDocument(doc, to)

		def fileContextMenu(index):
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

		index = gui.tabBar(
			list(tabs.values()),
			selectedTab=selectedTab,
			drawBase=False,
			documentMode=True,
			expanding=False,
			position=position,
			overlap=adjustOverlap(overlap, (None, None, 0, None)),
			roundedCorners=roundedCorners,
			movable=True,
			tabsClosable=True,
			closeIcon=icons.closeTab,
			onTabMoved=tabMoved,
			onTabCloseRequested=tabCloseRequested,
			onContextMenuRequested=fileContextMenu,
		)

		if index in range(len(tabs)):
			if index != selectedTab:
				view.manager.showDocument(list(tabs.keys())[index])
		else:
			view.selectDocument(None)

		if view.documents:
			if gui.toolButton(icon=icons.chevronDown, overlap=adjustOverlap(overlap, (0, None, None, None)), roundedCorners=CORNERS.NONE):
				self._showOpenedDocumentsPopup(gui)

		if gui.toolButton(icon=icons.bars, overlap=adjustOverlap(overlap, (1 if view.documents else 0, None, None, None if view.documents else 0)), roundedCorners=CORNERS.NONE):
			with gui.popupMenu(True) as menu:
				menu.addItem("split horizontally", lambda: view.splitView(False))
				menu.addItem("split vertically", lambda: view.splitView(True))
				menu.addSeparator()
				menu.addItem("close view", lambda: view.manager.safelyCloseView(view), enabled=len(view.documents)==0)

	def documentsGUI(self, gui: DatapackEditorGUI) -> None:
		view = self.model()

		currentDocEditor = None

		if view.documents:
			selectedDocumentId = view.selectedDocument.filePathForDisplay if view.selectedDocument is not None else None
			with gui.stackedWidget(selectedView=selectedDocumentId) as stacked:
				for document in view.documents:
					with stacked.addView(id_=document.filePathForDisplay):
						docEditor = gui.editor(TextDocumentEditor, document, onEditorFocusReceived=lambda fr: view.makeCurrent())
						if document.filePathForDisplay == selectedDocumentId:
							currentDocEditor = docEditor
		else:  # no documents are opened:
			self._noDocumentOpenedGUI(gui)

		if view.selectedDocument is None:
			currentDocEditor = None
		if currentDocEditor is not None:
			currentDocEditor.redraw()
			if self._shouldForceFocus:
				currentDocEditor.setFocus()
		self._shouldForceFocus = False

	def _noDocumentOpenedGUI(self, gui: DatapackEditorGUI) -> None:
		mg = gui.margin
		with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
			gui.label('No Document Opened.', wordWrap=False, alignment=Qt.AlignCenter)
			gui.addVSpacer(mg, SizePolicy.Fixed)
			gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.GO_TO_FILE.toString()}</font>' to search for a file.", wordWrap=False, alignment=Qt.AlignCenter)
			gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.NEW.toString()}</font>' to create a new file.", wordWrap=False, alignment=Qt.AlignCenter)
			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Fixed)
			with gui.hLayout():
				gui.addHSpacer(int(20 * gui._scale), SizePolicy.Expanding)
				if gui.button("close View", icon=icons.close2, hSizePolicy=SizePolicy.Fixed.value):
					self.model().manager.safelyCloseView(self.model())
				gui.addHSpacer(int(20 * gui._scale), SizePolicy.Expanding)
			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)

	@staticmethod
	def _noWorldLoadedGUI(gui: DatapackEditorGUI) -> None:
		mg = gui.margin
		with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
			gui.label('No world loaded.', wordWrap=False, alignment=Qt.AlignCenter)
			gui.addVSpacer(mg, SizePolicy.Fixed)
			gui.label(f"Please open a Minecraft world.", wordWrap=False, alignment=Qt.AlignCenter)
			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)

	def _showOpenedDocumentsPopup(self, gui: DatapackEditorGUI) -> None:
		view = self.model()

		class Documents:
			def __iter__(self) -> Iterator[Document]:
				yield from view.documents

		selectedDocument = view.selectedDocument

		def onContextMenu(d: Document, column: int):
			print(f"showning ContextMenu for Document '{d.fileName}'")
			with gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('close', lambda d=d: getSession().documents.safelyCloseDocument(d), tip=f'close {d.filePath}')
				menu.addItems(ContextMenuEntries.pathItems(d.filePath))

		# calculate dimensions:
		width, height = self.__sizeForOpenedDocumentsPopup(gui, Documents())

		selectedDocument = gui.searchableChoicePopup(
			selectedDocument,
			'Opened Files',
			Documents(),
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

		if selectedDocument in Documents():
			view.selectDocument(selectedDocument)

	@staticmethod
	def __sizeForOpenedDocumentsPopup(gui: DatapackEditorGUI, documents: Iterable[Document]) -> tuple[int, int]:
		fm = gui._lastTabWidget.fontMetrics()
		scale = gui._scale
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
		self.redraw()


__all__ = [
	'DocumentsViewEditor',
]