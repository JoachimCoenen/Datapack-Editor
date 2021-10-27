from typing import Iterator, Iterable

from PyQt5 import sip
from PyQt5.QtCore import Qt

from Cat.CatPythonGUI.GUI import NO_MARGINS, CORNERS, NO_OVERLAP, Overlap, RoundedCorners, adjustOverlap
from Cat.CatPythonGUI.GUI.enums import TabPosition, SizePolicy
from Cat.icons import icons
from Cat.utils import override
from Cat.utils.collections import OrderedMultiDict
from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, ContextMenuEntries
from gui.editors import TextDocumentEditor
from keySequences import KEY_SEQUENCES
from session.documentHandling import View
from session.documents import Document
from session.session import getSession


class DocumentsViewEditor(EditorBase[View]):
	def __init__(self, model: View):
		super(DocumentsViewEditor, self).__init__(model)
		model.onDocumentsChanged.connect('editorRedraw', self.redraw)
		model.onMadeCurrent.connect('editor', self._forceFocus)
		self._shouldForceFocus: bool = model.isCurrent

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		view = self.model()
		tabBarOverlap = (0, 0, 0, 1)
		with gui.vLayout(verticalSpacing=0):
			with gui.hPanel(contentsMargins=NO_MARGINS, horizontalSpacing=0, overlap=tabBarOverlap, roundedCorners=CORNERS.TOP_LEFT, windowPanel=True):
				self.documentsTabBarGUI(gui, position=TabPosition.North, overlap=tabBarOverlap, roundedCorners=CORNERS.TOP_LEFT)
			panelOverlap = NO_OVERLAP if view.documents else (0, 1, 0, 0)
			with gui.vPanel(contentsMargins=NO_MARGINS, overlap=panelOverlap, roundedCorners=CORNERS.BOTTOM_LEFT, windowPanel=True):
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
		)

		if index in range(len(tabs)):
			view.selectedDocument = list(tabs.keys())[index]
		else:
			view.selectedDocument = None

		if gui.toolButton(icon=icons.chevronDown, overlap=adjustOverlap(overlap, (0, None, None, None)), roundedCorners=CORNERS.NONE):
			self._showOpenedDocumentsPopup(gui)

	def documentsGUI(self, gui: DatapackEditorGUI):
		view = self.model()

		currentDocumenSubGUI = None

		if view.documents:
			selectedDocumentId = view.selectedDocument.filePathForDisplay if view.selectedDocument is not None else None
			with gui.stackedWidget(selectedView=selectedDocumentId) as stacked:
				for document in view.documents:
					with stacked.addView(id_=document.filePathForDisplay):
						subGUI = gui.editor(TextDocumentEditor, document, onEditorFocusReceived=lambda fr: view.makeCurrent())
						if document.filePathForDisplay == selectedDocumentId:
							currentDocumenSubGUI = subGUI
		else:  # no documents are opened:
			mg = gui.margin
			with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
				gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
				gui.label('No Document Opened.', wordWrap=False, alignment=Qt.AlignCenter)
				gui.addVSpacer(mg, SizePolicy.Fixed)
				gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.GO_TO_FILE.toString()}</font>' to search for a file.", wordWrap=False, alignment=Qt.AlignCenter)
				gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.NEW.toString()}</font>' to create a new file.", wordWrap=False, alignment=Qt.AlignCenter)
				gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)

		if view.selectedDocument is None:
			currentDocumenSubGUI = None
		if currentDocumenSubGUI is not None:
			currentDocumenSubGUI.redraw()
			if self._shouldForceFocus:
				currentDocumenSubGUI.setFocus()
		self._shouldForceFocus = False

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
			view.selectedDocument = selectedDocument

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
		self._shouldForceFocus = True
		self.redraw()

	@override
	def redraw(self) -> None:
		if not sip.isdeleted(self):
			super(DocumentsViewEditor, self).redraw()


__all__ = [
	'DocumentsViewEditor',
]