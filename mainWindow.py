from __future__ import annotations
import os
from math import floor
from operator import attrgetter
from typing import Optional, Sequence

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication

import Cat
from Cat.CatPythonGUI.GUI import CORNERS, NO_OVERLAP, NO_MARGINS, SizePolicy, Overlap, RoundedCorners, maskCorners, adjustOverlap
from Cat.CatPythonGUI.GUI.codeEditor import Position, Error
from Cat.CatPythonGUI.GUI.enums import TabPosition, MessageBoxStyle, MessageBoxButton
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.pythonGUI import TabOptions
from Cat.icons import icons
from Cat.utils import openOrCreate
from Cat.utils.formatters import formatVal, FW
from gui.editors import DatapackFilesEditor, DocumentsViewsContainerEditor
from keySequences import KEY_SEQUENCES
from model.commands.parser import parseMCFunction
from model.utils import Span
from session.session import getSession, WindowId, saveSessionToFile
from session.documents import Document, DocumentTypeDescription, getDocumentTypes, getErrorCounts
from session import documentsImpl
from gui.checkAllDialog import CheckAllDialog
from gui.searchAllDialog import SearchAllDialog
from gui.spotlightSearch import SpotlightSearchGui
from model.pathUtils import FilePath
from gui.datapackEditorGUI import DatapackEditorGUI
from settings import applicationSettings
from settings.settingsDialog import SettingsDialog


documentsImpl.init()


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
		self._lastOpenPath = ''

		#GUI
		self.checkAllDialog = CheckAllDialog(self)
		self.searchAllDialog = SearchAllDialog(self)
		self.settingsDialog = SettingsDialog(self)
		self.currentDocumenSubGUI: Optional[DatapackEditorGUI] = None

		self.setAcceptDrops(True)

		getSession().documents.onCanCloseModifiedDocument = self._canCloseModifiedDocument
		getSession().onError.connect('showError', lambda e, title: self._gui.showWarningDialog(title, str(e)))

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

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		gui.editor(DatapackFilesEditor, getSession().world, roundedCorners=CORNERS.RIGHT).redrawLater()

	def documentToolBarGUI(self, gui: DatapackEditorGUI, button, btnCorners, btnOverlap, btnMargins):
		button = gui.framelessButton
		document = self.selectedDocument
		btnKwArgs = dict(roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value)
		with gui.hLayout():
			if button(icon=icons.file, tip='New File', **btnKwArgs, windowShortcut=KEY_SEQUENCES.NEW):
				self._createNewDocument(gui)

			if button(icon=icons.open, tip='Open File', **btnKwArgs, windowShortcut=QKeySequence.Open):
				filePath = gui.showFileDialog(self._lastOpenPath, [('All files', '*')], style='open')
				if filePath:
					self._tryOpenOrSelectDocument(filePath)

			isEnabled = True  # bool(document) and os.path.exists(document.filePathForDisplay)
			if button(icon=icons.save, tip='Save File', **btnKwArgs, enabled=isEnabled, windowShortcut=QKeySequence.Save):
				self._saveOrSaveAs(gui, document)

			if button(icon=icons.saveAs, tip='Save As', **btnKwArgs, enabled=bool(document), windowShortcut=KEY_SEQUENCES.SAVE_AS):
				self._saveAs(gui, document)

			if button(icon=icons.refresh, tip='Reload File', **btnKwArgs, enabled=bool(document), windowShortcut=QKeySequence.Refresh):
				filePath = document.filePath
				if filePath:
					try:
						document.loadFromFile()
					except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
						getSession().showAndLogError(e)

			with gui.hLayout(horizontalSpacing=0):
				if button(icon=icons.undo, tip='Undo', roundedCorners=maskCorners(btnCorners, CORNERS.LEFT), overlap=btnOverlap, margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value, enabled=bool(document), windowShortcut=QKeySequence.Undo):
					document.undoRedoStack.undoOnce()

				if button(icon=icons.redo, tip='Redo', roundedCorners=maskCorners(btnCorners, CORNERS.RIGHT), overlap=adjustOverlap(btnOverlap, (1, None, None, None)), margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value, enabled=bool(document), windowShortcut=QKeySequence.Redo):
					document.undoRedoStack.redoOnce()

			if button(icon=icons.camera, tip='parse MCFunction', **btnKwArgs, enabled=document is not None):
				if self.selectedDocument is not None:
					text = self.selectedDocument.content
					func, errors = parseMCFunction(getSession().minecraftData.commands, text)
					filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/mcFunction.ast"
					with openOrCreate(filePath, "w") as outFfile:
						formatVal((func, errors), s=FW(outFfile))
					self._tryOpenOrSelectDocument(filePath)

	def toolBarGUI2(self, gui: DatapackEditorGUI):
		# TODO: INVESTIGATE calculation of hSpacing:
		sdm = gui.smallDefaultMargins
		dm = gui.defaultMargins
		avgMarginsDiff = ((dm[0] - sdm[0]) + (dm[1] - sdm[1])) / 2
		hSpacing = gui.smallSpacing  # + int(avgMarginsDiff * gui.scale)

		button = gui.framelessButton
		btnCorners = CORNERS.ALL
		btnMargins = gui.smallDefaultMargins
		btnOverlap = (0, 0, 0, 1) if self.isToolbarInTitleBar else NO_OVERLAP
		btnKwArgs = dict(roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value)

		with gui.hLayout(horizontalSpacing=hSpacing):
			hasOpenedWorld = getSession().hasOpenedWorld
			if button(icon=icons.globeAlt, tip='Switch World' if hasOpenedWorld else 'Load World', **btnKwArgs, default=not hasOpenedWorld):
				self._loadWorldDialog(gui)

			docToolBarGUI = gui.subGUI(type(gui), lambda g: self.documentToolBarGUI(g, button=button, btnCorners=btnCorners, btnOverlap=btnOverlap, btnMargins=btnMargins), hSizePolicy=SizePolicy.Fixed.value)
			getSession().documents.onSelectedDocumentChanged.disconnect('documentToolBarGUI')
			getSession().documents.onSelectedDocumentChanged.connect('documentToolBarGUI', docToolBarGUI.host.redraw)
			docToolBarGUI.redrawGUI()
			docToolBarGUI._name = 'docToolBarGUI'

			gui.addHSpacer(0, SizePolicy.Expanding)

		self.fileSearchFieldGUI(gui, roundedCorners=btnCorners, overlap=btnOverlap)

		with gui.hLayout(horizontalSpacing=hSpacing):
			gui.addHSpacer(0, SizePolicy.Expanding)

			if button(icon=icons.search, tip='Search all', **btnKwArgs, windowShortcut=KEY_SEQUENCES.FIND_ALL):
				self.searchAllDialog.show()

			if button(icon=icons.spellCheck, tip='Check all Files', **btnKwArgs, enabled=True):
				self.checkAllDialog.show()

			if button(icon=icons.settings, tip='Settings', **btnKwArgs, windowShortcut=QKeySequence.Preferences):
				self._showSettingsDialog(gui)

			if applicationSettings.debugging.isDeveloperMode:
				gui.hSeparator()
				Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled = gui.toggleSwitch(Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled, enabled=True)
				gui.label('P')

			if self.isToolbarInTitleBar:
				gui.hSeparator()

	def bottomPanelGUI(self, gui: DatapackEditorGUI, roundedCorners: RoundedCorners, cornerRadius: float):
		document = self.selectedDocument

		# connect to errorChanged Signal:
		Document.onErrorsChanged.disconnectFromAllInstances(key='bottomPanelGUI')
		if document is not None:
			document.onErrorsChanged.connect('bottomPanelGUI', lambda d: gui.host.redrawLater('onErrorsChanged'))
		getSession().documents.onSelectedDocumentChanged.connect('bottomPanelGUI', lambda: gui.host.redrawLater('onSelectedDocumentChanged'))

		tabs = [
			(('Errors', TabOptions(icon=icons.error)),     (
				lambda *args, **kwargs: self._gitConsoleRefreshTimer.stop() or self.documentErrorsGUI(*args, **kwargs),
				None
			)),
			(('Console', TabOptions(icon=icons.terminal),), (
				lambda *args, **kwargs: None,
				lambda *args, **kwargs: None,
			)),
		]
		with gui.vLayout(verticalSpacing=0, contentsMargins=NO_MARGINS):
			with gui.hPanel(contentsMargins=(0, 0, gui.margin, 0), overlap=(0, -1), roundedCorners=maskCorners(roundedCorners, CORNERS.TOP), windowPanel=True):
				index = gui.tabBar(
					[tab[0] for tab in tabs],
					drawBase=False,
					documentMode=True,
					expanding=False,
					position=TabPosition.North,
					overlap=(0, -1),
					roundedCorners=maskCorners(roundedCorners, CORNERS.TOP_LEFT),
					# cornerRadius=cornerRadius,
					hSizePolicy=SizePolicy.Expanding.value
				)
				guiFunc, toolBtnFunc = tabs[index][1]

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
		# TODO: better save dialog (with proper filters)
		filePath = gui.showFileDialog(document.filePathForDisplay, [('All files', '*')], style='save')
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
				getSession().showAndLogError(e)
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
				getSession().showAndLogError(e)
				return False
			return True

	def _tryOpenOrSelectDocument(self, filePath: FilePath, selectedPosition: Optional[Position] = None):
		# find Document if is alredy open:
		try:
			getSession().documents.openOrShowDocument(filePath, Span(selectedPosition) if selectedPosition is not None else None)
			self._gui.redrawGUI()
		except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
			getSession().showAndLogError(e)

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

	@property
	def selectedDocument(self) -> Optional[Document]:
		return getSession().documents.currentView.selectedDocument

					
					
					
					
					
					
					
					