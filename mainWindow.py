from __future__ import annotations
import os
from math import floor
from operator import attrgetter
from typing import Optional, Sequence, Iterable, Iterator

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication

import Cat
from Cat.CatPythonGUI.GUI import CORNERS, NO_OVERLAP, NO_MARGINS, SizePolicy, Overlap, RoundedCorners, maskCorners, adjustOverlap
from Cat.CatPythonGUI.GUI.codeEditor import Position, Error
from Cat.CatPythonGUI.GUI.enums import TabPosition, MessageBoxStyle, MessageBoxButton
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.pythonGUI import PythonGUIWidget
from Cat.icons import icons
from Cat.utils import openOrCreate, Maybe, format_full_exc
from Cat.utils.collections_ import OrderedMultiDict, OrderedDict
from Cat.utils.formatters import formatVal, FW
from Cat.utils.profiling import logError, logInfo
from gui.editors import TextDocumentEditor, DatapackFilesEditor, DocumentsViewEditor, DocumentsViewsContainerEditor
from keySequences import KEY_SEQUENCES
from model.commands.commands import AllCommands, BASIC_COMMAND_INFO
from model.commands.parser import parseMCFunction
from model.parsingUtils import Span
from session.documents import Document, DocumentTypeDescription, getDocumentTypes, getFilePathForDisplay, getErrorCounts
from gui.checkAllDialog import CheckAllDialog
from gui.searchAllDialog import SearchAllDialog
from gui.spotlightSearch import SpotlightSearchGui
from model.pathUtils import FilePath
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries
from session.session import getSession, WindowId, getSessionFilePath, saveSessionToFile, loadSessionFromFile
from settings import applicationSettings
from settings.settingsDialog import SettingsDialog


def frange(a: float, b: float, jump: float, *, includeLAst: bool = False):
	cnt = int(floor(abs(b - a) / jump))
	cnt = cnt + 1 if includeLAst else cnt
	for i in range(cnt):
		yield a + jump * i


class MainWindow(CatFramelessWindowMixin, QMainWindow):  # QtWidgets.QWidget):
	TIP_dataDir = 'Directory containing the raw data.'

	__allMainWindows: dict[WindowId, MainWindow] = {}

	@classmethod
	def registerMainWindow(cls, window: MainWindow, id: WindowId):
		"""
		this is to prevent a very strange bug, where a main window gets closed when:
			- it is not stored in a python object and therefore can be garbage collected  AND
			- and the user selects one (or sometimes more) roles in the non-modal searchAllDialog dialog with a treeView
			this materialized in following behavior:
				- RuntimeError: wrapped C/C++ object of type QGridLayout has been deleted
				- when the user selects one (or sometimes more) roles in the non-modal searchAllDialog dialog for the first time
				- while a treeView is in the searchAllDialog (the results list is a treeView)
				- and no treeView is visible in the main window.
			slightly different behavior is shown:
				- when the searchAllDialog is missing its results list --> no crash
				- when the searchAllDialog is modal                    --> no crash
				- when a t
		:param window:
		:param id:
		:return:
		"""
		cls.__allMainWindows[id] = window
		window._id = id

	@classmethod
	def deregisterMainWindow(cls, id: WindowId):
		cls.__allMainWindows.pop(id, None)

	def __init__(self, id: WindowId):
		super().__init__(GUICls=DatapackEditorGUI)

		self._gitConsoleRefreshTimer: QTimer = QTimer(self) # for the git tab
		self._gui._name = f'main Window GUI {id}'
		self._id: WindowId = id
		MainWindow.registerMainWindow(self, id)
		self._disableContentMargins = True
		self._disableSidebarMargins = True
		self._drawTitleToolbarBorder = False
		self.roundedCorners = CORNERS.ALL

		# TODO: change initial _lastOpenPath:
		self._lastOpenPath = 'D:/Development/svn/CODIM_0_9_6/de.ascon_systems.sms/webapp/WEB-INF/model'

		#GUI
		self.checkAllDialog = CheckAllDialog(self)
		self.searchAllDialog = SearchAllDialog(self)
		self.settingsDialog = SettingsDialog(self)
		self.currentDocumenSubGUI: Optional[DatapackEditorGUI] = None

		self.setAcceptDrops(True)

		getSession().documents.onCanCloseModifiedDocument = self._canCloseModifiedDocument

		# close document as shortcut:
		# self.closeDocumentShortcut = QShortcut(KEY_SEQUENCES.CLOSE_DOCUMENT, self, lambda d=document, s=self: self._safelyCloseDocument(gui, getSession().selectedDocument),
		# TODO:		  lambda d=document, s=self: asdasdasdasdasd s._safelyCloseDocument(gui, d), Qt.WidgetWithChildrenShortcut)

	@property
	def id(self) -> WindowId:
		return self._id

	def closeEvent(self, event: QCloseEvent):
		self._saveSession()
		MainWindow.deregisterMainWindow(self.id)
		event.accept()

	# properties:

	@property
	def isToolbarInTitleBar(self) -> bool:
		return applicationSettings.appearance.useCompactLayout

	@property
	def disableStatusbarMargins(self) -> bool:
		return applicationSettings.appearance.useCompactLayout

	# GUI:

	def _mainAreaGUI(self, gui: DatapackEditorGUI, overlap: Overlap, roundedCorners: RoundedCorners):
		contentsMargins = self._mainAreaMargins
		with gui.vLayout(contentsMargins=contentsMargins):
			self.OnGUI(gui)

	def OnGUI(self, gui: DatapackEditorGUI):
		# app = cast(QApplication, QApplication.instance())
		# self._updateApplicationDisplayName(app)
		tabBarOverlap = (0, 1, 0, 1) if self.drawTitleToolbarBorder else (0, 0, 0, 1)
		with gui.vSplitter(handleWidth=self.windowSpacing) as splitter:
			# main Panel:
			with splitter.addArea(stretchFactor=2, id_='mainPanel', verticalSpacing=0):
				gui.editor(DocumentsViewsContainerEditor, getSession().documents.viewsC, roundedCorners=CORNERS.LEFT).redrawLater('MainWindow.OnGUI(...)')
			# bottom Panel:
			with splitter.addArea(stretchFactor=0, id_='bottomPanel', verticalSpacing=0):
				bottomPanel = gui.subGUI(type(gui), lambda gui: self.bottomPanelGUI(gui, roundedCorners=(True,  False,  True, False), cornerRadius=self.windowCornerRadius))
				bottomPanel.redrawGUI()
		# getSession().documents.onSelectedDocumentChanged.connect('mainWindowGUI', self.redraw)
		self._saveSession()

	def OnToolbarGUI(self, gui: DatapackEditorGUI):
		self.toolBarGUI2(gui)

	def OnStatusbarGUI(self, gui: DatapackEditorGUI):
		mg = self._gui.margin if self.disableStatusbarMargins else 0
		with gui.hLayout(contentsMargins=(mg, 0, mg, 0)):
			pass
			# self.sessionToolBarGUI(gui)
			# gui.hSeparator()
			# gui.propertyField(applicationSettings, applicationSettings.appearanceProp.useCompactLayout)

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		gui.editor(DatapackFilesEditor, getSession().world).redrawLater()

	def toolBarGUI2(self, gui: DatapackEditorGUI):
		# TODO: INVESTIGATE calculation of hSpacing:
		sdm = gui.smallDefaultMargins
		dm = gui.defaultMargins
		avgMarginsDiff = ((dm[0] - sdm[0]) + (dm[1] - sdm[1])) / 2
		hSpacing = gui.smallSpacing  # + int(avgMarginsDiff * gui._scale)

		button = gui.framelessButton
		btnCorners = CORNERS.ALL
		btnMargins = gui.smallDefaultMargins
		btnOverlap = (0, 0, 0, 1) if self.isToolbarInTitleBar else NO_OVERLAP

		with gui.hLayout(horizontalSpacing=hSpacing):
			hasOpenedWorld = getSession().hasOpenedWorld
			if button(icon=icons.globeAlt, tip='Switch World' if hasOpenedWorld else 'Load World', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, default=not hasOpenedWorld):
				self._loadWorldDialog(gui)

			document = self.selectedDocument
			if button(icon=icons.file, tip='New File', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, windowShortcut=KEY_SEQUENCES.NEW):
				self._createNewDocument(gui)

			if button(icon=icons.open, tip='Open File', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, windowShortcut=QKeySequence.Open):
				filePath = gui.showFileDialog(self._lastOpenPath, [('model', '.xml'), ('java', '.java'), ('All files', '*')], style='open')
				if filePath:
					self._tryOpenOrSelectDocument(filePath)

			isEnabled = True  # bool(document) and os.path.exists(document.filePathForDisplay)
			if button(icon=icons.save, tip='Save File', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, enabled=isEnabled, windowShortcut=QKeySequence.Save):
				self._saveOrSaveAs(gui, document)

			if button(icon=icons.saveAs, tip='Save As', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, enabled=bool(document), windowShortcut=KEY_SEQUENCES.SAVE_AS):
				self._saveAs(gui, document)

			if button(icon=icons.refresh, tip='Reload File', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, enabled=bool(document), windowShortcut=QKeySequence.Refresh):
				filePath = document.filePath
				if filePath:
					try:
						document.loadFromFile()
					except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
						gui.showAndLogError(e)

			with gui.hLayout(horizontalSpacing=0):
				if button(icon=icons.undo, tip='Undo', roundedCorners=maskCorners(btnCorners, CORNERS.LEFT), overlap=btnOverlap, margins=btnMargins, enabled=bool(document), windowShortcut=QKeySequence.Undo):
					document.undoRedoStack.undoOnce()

				if button(icon=icons.redo, tip='Redo', roundedCorners=maskCorners(btnCorners, CORNERS.RIGHT), overlap=adjustOverlap(btnOverlap, (1, None, None, None)), margins=btnMargins, enabled=bool(document), windowShortcut=QKeySequence.Redo):
					document.undoRedoStack.redoOnce()

			gui.addHSpacer(0, SizePolicy.Expanding)

		self.fileSearchFieldGUI(gui, roundedCorners=btnCorners, overlap=btnOverlap)

		with gui.hLayout(horizontalSpacing=hSpacing):
			gui.addHSpacer(0, SizePolicy.Expanding)

			if button(icon=icons.search, tip='Search all', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, windowShortcut=KEY_SEQUENCES.FIND_ALL):
				self.searchAllDialog.show()

			if button(icon=icons.spellCheck, tip='Check all Files', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, enabled=True):
				self.checkAllDialog.show()

			if button(icon=icons.settings, tip='Settings', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, windowShortcut=QKeySequence.Preferences):
				self._showSettingsDialog(gui)

			# if button(icon=icons.windowRestore, tip='New Window', roundedCorners=btnCorners, margins=btnMargins):
			# 	newMainWindow()

			gui.hSeparator()
			if button(icon=icons.camera_ban, tip='Ban Cameras', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins):
				if gui.askUser(title='Really?', message='You want to ban all cameras?!'):
					gui.showErrorDialog(title='Error', message='You cannot ban all cameras!')
				else:
					gui.showInformationDialog(title='phew...', message='Thank goodness!')

			if button(icon=icons.camera, tip='parse MCFunction', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, enabled=document is not None):
				if self.selectedDocument is not None:
					text = self.selectedDocument.content
					func, errors = parseMCFunction(text)
					filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/mcFunction.ast"
					with openOrCreate(filePath, "w") as outFfile:
						formatVal((func, errors), s=FW(outFfile))
					self._tryOpenOrSelectDocument(filePath)

			if applicationSettings.debugging.isDeveloperMode:
				gui.hSeparator()
				if button(icon=icons.camera, tip='showCommandInfo', roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins):
					try:
						ac = AllCommands.create(BASIC_COMMAND_INFO=BASIC_COMMAND_INFO)
						filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/commands.ast"
						with openOrCreate(filePath, "w") as outFfile:
							ac.toJSON(outFfile)
						self._tryOpenOrSelectDocument(filePath)
					except Exception as e:
						fullMsg = format_full_exc(e)
						logError(fullMsg)
						gui.showErrorDialog(
							type(e).__name__,
							f"```{fullMsg}```",
							textFormat=Qt.MarkdownText
						)
				gui.hSeparator()
				Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled = gui.toggleSwitch(Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled, enabled=True)
				gui.label('P')

			if self.isToolbarInTitleBar:
				gui.hSeparator()

	def sessionToolBarGUI(self, gui: DatapackEditorGUI):
		gui.filePathField(getSessionFilePath(), filters=[("JSON", ".json")], style='save', enabled=True)
		with gui.hLayout():
			if gui.button('Reset'):
				getSession().reset()
			if gui.button('Save'):
				saveSessionToFile()
			if gui.button('Load'):
				loadSessionFromFile()

	def bottomPanelGUI(self, gui: DatapackEditorGUI, roundedCorners: RoundedCorners, cornerRadius: float):
		document = self.selectedDocument

		tabs = OrderedDict([
			((icons.error, 'Errors',),     (
				lambda *args, **kwargs: self._gitConsoleRefreshTimer.stop() or self.documentErrorsGUI(*args, **kwargs),
				None
			)),
			((icons.terminal, 'Console',), (
				lambda *args, **kwargs: None, # self.commandsConsoleGUI,
				lambda *args, **kwargs: None, # self.commandsConsoleTollButtonsGUI
			)),
		])
		with gui.vLayout(verticalSpacing=0, contentsMargins=NO_MARGINS):
			with gui.hPanel(contentsMargins=(0, 0, gui.margin, 0), overlap=(0, -1), roundedCorners=maskCorners(roundedCorners, CORNERS.TOP), windowPanel=True):
				index = gui.tabBar(
					list(tabs.keys()),
					drawBase=False,
					documentMode=True,
					expanding=False,
					position=TabPosition.North,
					overlap=(0, -1),
					roundedCorners=maskCorners(roundedCorners, CORNERS.TOP_LEFT),
					# cornerRadius=cornerRadius,
					hSizePolicy=SizePolicy.Expanding.value
				)
				guiFunc, toolBtnFunc = list(tabs.values())[index]

				if toolBtnFunc is not None:
					toolBtnFunc(gui, overlap=(0, -1))
					gui.hSeparator()
				if document is not None:
					gui.errorsSummaryGUI(getErrorCounts([], document.errors))

			with gui.vPanel(
				vSizePolicy=SizePolicy.Expanding.value,
				contentsMargins=NO_MARGINS,
				roundedCorners=maskCorners(roundedCorners, CORNERS.BOTTOM),
				cornerRadius=cornerRadius,
				windowPanel=True
			):
				guiFunc(gui, roundedCorners=maskCorners(roundedCorners, CORNERS.BOTTOM), cornerRadius=cornerRadius)

	def documentErrorsGUI(self, gui: DatapackEditorGUI, roundedCorners: RoundedCorners, cornerRadius: float) -> None:
		document: Optional[Document] = self.selectedDocument
		if document is not None:
			errors: Sequence[Error] = document.errors
			errors = sorted(errors, key=attrgetter('position'))
		else:
			errors: Sequence[Error] = []
		with gui.scrollBox(preventVStretch=True, roundedCorners=roundedCorners, cornerRadius=cornerRadius):
			gui.drawErrors(errors, onDoubleClicked=lambda e, d=document, s=self: d.locatePosition(e.position, e.end) or s._gui.redrawGUI())
			#gui.addVSpacer(0, SizePolicy.Expanding)

	# def documentsGUI(self, gui: DatapackEditorGUI):
	# 	def onGUI(gui: DatapackEditorGUI, document: Document):
	# 		gui.editor(TextDocumentEditor, document)
	#
	# 	def onInit(widget: PythonGUIWidget, document: Document):
	# 		widget.redraw()  # redraw a second time!
	#
	# 	if getSession().documents:
	# 		selectedDocumentId = self.selectedDocumentId
	# 		with gui.stackedWidget(selectedView=selectedDocumentId) as stacked:
	# 			for document in getSession().documents:
	# 				with stacked.addView(id_=document.filePathForDisplay):
	# 					subGUI = gui.subGUI(
	# 						DatapackEditorGUI,
	# 						guiFunc=lambda gui, document=document: onGUI(gui, document),
	# 						onInit=lambda w, document=document: onInit(w, document) or True
	# 					)
	# 					if document.filePathForDisplay == selectedDocumentId:
	# 						self.currentDocumenSubGUI = subGUI
	# 	else:  # no documents are opened:
	# 		mg = gui.margin
	# 		with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
	# 			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
	# 			gui.label('No Document Opened.', wordWrap=False, alignment=Qt.AlignCenter)
	# 			gui.addVSpacer(mg, SizePolicy.Fixed)
	# 			gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.GO_TO_FILE.toString()}</font>' to search for a file.", wordWrap=False, alignment=Qt.AlignCenter)
	# 			gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.NEW.toString()}</font>' to create a new file.", wordWrap=False, alignment=Qt.AlignCenter)
	# 			gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
	#
	# 	if self.selectedDocument is None:
	# 		self.currentDocumenSubGUI = None
	# 	if self.currentDocumenSubGUI is not None:
	# 		self.currentDocumenSubGUI.redrawGUI()

	# def documentsTabBarGUI(self, gui: DatapackEditorGUI, position: TabPosition = TabPosition.North, overlap: Overlap = (0, 0), roundedCorners: RoundedCorners = CORNERS.ALL):
	# 	tabs = OrderedMultiDict((
	# 		(document.filePathForDisplay, (document.fileName + (' *' if document.documentChanged else '   '), ))
	# 		for document in getSession().documents
	# 	))
	#
	# 	try:
	# 		selectedTab = list(tabs.keys()).index(self.selectedDocumentId)
	# 	except ValueError:
	# 		selectedTab = None
	#
	# 	def tabCloseRequested(index: int):
	# 		if index in range(len(getSession().documents)):
	# 			self._safelyCloseDocument(gui, getSession().documents[index])
	#
	# 	def tabMoved(from_: int, to: int):
	# 		print(f"tab {from_} moved to {to}.")
	# 		indexRange = range(len(getSession().documents))
	# 		if from_ in indexRange and to in indexRange:
	# 			self._safelyMoveDocumentPosition(gui, getSession().documents[from_], to)
	#
	# 	index = gui.tabBar(
	# 		list(tabs.values()),
	# 		selectedTab=selectedTab,
	# 		drawBase=False,
	# 		documentMode=True,
	# 		expanding=False,
	# 		position=position,
	# 		overlap=adjustOverlap(overlap, (None, None, 0, None)),
	# 		roundedCorners=roundedCorners,
	# 		movable=True,
	# 		tabsClosable=True,
	# 		closeIcon=icons.closeTab,
	# 		onTabMoved=tabMoved,
	# 		onTabCloseRequested=tabCloseRequested,
	# 	)
	#
	# 	if index in range(len(tabs)):
	# 		self.selectedDocumentId = list(tabs.keys())[index]
	# 	else:
	# 		self.selectedDocumentId = None
	#
	# 	if gui.toolButton(icon=icons.chevronDown, overlap=adjustOverlap(overlap, (0, None, None, None)), roundedCorners=CORNERS.NONE):
	# 		self._showOpenedDocumentsPopup(gui)

	# Dialogs:

	def _showSettingsDialog(self, gui: DatapackEditorGUI) -> None:
		oldStyle = applicationSettings.appearance.applicationStyle

		gui.showOverlay()
		self.settingsDialog.exec()
		gui.hideOverlay()

		newStyle = applicationSettings.appearance.applicationStyle
		if oldStyle != newStyle:
			QApplication.setStyle(newStyle)

	def _saveAsDialog(self, gui: DatapackEditorGUI, document: Document) -> str:
		filePath = gui.showFileDialog(document.filePathForDisplay, [('model', '.xml'), ('java', '.java'), ('All files', '*')], style='save')
		if filePath:
			self._lastOpenPath = os.path.dirname(filePath)
		return filePath

	@staticmethod
	def _selectDocumentTypeDialog(gui: DatapackEditorGUI) -> Optional[DocumentTypeDescription]:
		documentType: Optional[DocumentTypeDescription] = None
		documentType = gui.searchableChoicePopup(
			documentType,
			'New File',
			getDocumentTypes(),
			getSearchStr=lambda x: x.name,
			labelMaker=lambda x, i: (x.name, ', '.join(x.extensions))[i],
			iconMaker=lambda x, i: (getattr(icons, x.icon, None) if x.icon is not None else None, None)[i],
			toolTipMaker=lambda x, i: x.tip,
			columnCount=2,
			width=200,
			height=175,
		)
		return documentType

	@staticmethod
	def _loadWorldDialog(gui: DatapackEditorGUI) -> None:
		session = getSession()
		oldPath = session.world.path
		oldPath = applicationSettings.minecraft.savesLocation
		newPath = gui.showFolderDialog(oldPath)
		if newPath is not None:
			session.openWorld(newPath)

	# Fields:

	@staticmethod
	def fileSearchFieldGUI(gui: DatapackEditorGUI, roundedCorners: RoundedCorners = CORNERS.ALL, **kwargs) -> None:
		gui.customWidget(
			SpotlightSearchGui,
			placeholderText=f'Press \'{KEY_SEQUENCES.GO_TO_FILE.toString()}\' to find a file',
			roundedCorners=roundedCorners,
			alignment=Qt.AlignCenter,
			windowShortcut=KEY_SEQUENCES.GO_TO_FILE,
			**kwargs
		)

	# Functionality:

	@staticmethod
	def _saveSession():
		saveSessionToFile()

	def _createNewDocument(self, gui: DatapackEditorGUI):
		docType = self._selectDocumentTypeDialog(gui)
		if docType is None:
			return
		# create document:
		doc = getSession().documents.createNewDocument(docType, None)
		getSession().documents.selectDocument(doc)
		self.redraw()

	def _saveAs(self, gui: DatapackEditorGUI, document: Document) -> bool:
		filePath = self._saveAsDialog(gui, document)
		if filePath:
			document.filePath = filePath
			try:
				document.saveToFile()
			except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
				gui.showAndLogError(e)
				return False
			return True
		return False

	def _saveOrSaveAs(self, gui: DatapackEditorGUI, document: Document) -> bool:
		filePath = document.filePath
		if not filePath:
			return self._saveAs(gui, document)
		else:
			try:
				document.saveToFile()
			except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
				gui.showAndLogError(e)
				return False
			return True

	def _tryOpenOrSelectDocument(self, filePath: FilePath, selectedPosition: Optional[Position] = None):
		# find Document if is alredy open:
		try:
			getSession().documents.openOrShowDocument(filePath, Span(selectedPosition) if selectedPosition is not None else None)
			self._gui.redrawGUI()
		except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
			self._gui.showAndLogError(e)

	def _safelyCloseDocument(self, gui: DatapackEditorGUI, document: Document):
		getSession().documents.safelyCloseDocument(document)
		self._gui.redrawGUI()
		self._gui.redrawGUI()

	def _canCloseModifiedDocument(self, doc: Document) -> bool:
		if doc.documentChanged:
			msgBoxResult = self._gui.showMessageDialog(
				# f'Save Changes?',
				f'Do you want to save the changes made to the file {doc.fileName}?',
				# '{document.fileName} has been modified. \nSave changes?',
				f'You can discard to undo the changes since you have last saved / opened the file.',
				MessageBoxStyle.Warning,
				{MessageBoxButton.Save, MessageBoxButton.Discard, MessageBoxButton.Cancel}
			)
			if msgBoxResult == MessageBoxButton.Save:
				self._saveOrSaveAs(self._gui, doc)  # will reset documentChanged
				return not doc.documentChanged
			elif msgBoxResult == MessageBoxButton.Discard:
				return True  # close it anyways
			else:  # Cancel
				return False

	# @staticmethod
	# def _safelyMoveDocumentPosition(gui: DatapackEditorGUI, document: Document, newPosition: int):
	# 	documents = getSession().documents
	# 	if newPosition not in range(len(documents)):
	# 		raise ValueError(f"newPosition is out of range (newPosition={newPosition}, len(documents)={len(documents)}")
	#
	# 	oldPosition = documents.index(document)
	# 	if oldPosition == newPosition:
	# 		return
	#
	# 	del documents[oldPosition]
	# 	documents.insert(newPosition, document)

	@property
	def selectedDocument(self) -> Optional[Document]:
		return getSession().documents.currentView.selectedDocument

	# @selectedDocument.setter
	# def selectedDocument(self, document: Optional[Document]) -> None:
	# 	getSession().selectedDocuments[self.id] = document

	# @property
	# def selectedDocumentId(self) -> Optional[str]:
	# 	return Maybe(self.selectedDocument).getattr('filePathForDisplay').get()
	#
	# @selectedDocumentId.setter
	# def selectedDocumentId(self, document: Optional[str]) -> None:
	# 	getSession().selectedDocumentIds[self.id] = document
	#
	#
	#
					
					
					
					
					
					
					
					