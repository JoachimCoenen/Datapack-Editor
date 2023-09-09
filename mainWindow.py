from __future__ import annotations
import os
from math import floor
from operator import attrgetter
from typing import Optional, Sequence, NewType

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeySequence, QDragEnterEvent, QDropEvent, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication

from Cat.CatPythonGUI.GUI import CORNERS, NO_OVERLAP, SizePolicy, RoundedCorners, pythonGUI, catWidgetMixins, Widgets
from Cat.CatPythonGUI.GUI.enums import TabPosition, MessageBoxStyle, MessageBoxButton, FileExtensionFilter
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.icons import iconCombiner, CompositionMode
from Cat.CatPythonGUI.GUI.pythonGUI import TabOptions
from Cat.icons import icons
from Cat.icons.icons import _Icons
from base.gui.newProjectDialog import NewProjectDialog
from base.gui.documentsViewEditor import DocumentsViewsContainerEditor
from gui.profileParsingDialog import ProfileParsingDialog
from base.model import theme
from keySequences import KEY_SEQUENCES
from base.model.utils import GeneralError
from base.model.session import getSession, saveSessionToFile, GLOBAL_SIGNALS
from base.model.documents import Document, DocumentTypeDescription, getDocumentTypes, getErrorCounts, getAllFileExtensionFilters, getDocumentTypeForDocument
from base.gui.checkAllDialog import CheckAllDialog
from base.gui.searchAllDialog import SearchAllDialog
from base.gui.spotlightSearch import SpotlightSearchGui
from gui.datapackEditorGUI import DatapackEditorGUI
from base.plugin import PLUGIN_SERVICE, SideBarTabGUIFunc, ToolBtnFunc
from base.model.applicationSettings import applicationSettings
from base.gui.settingsDialog import SettingsDialog


class _DpeIcons:
	__slots__ = ()
	_shadowedChevronDown = (
		(_Icons.chevronDown, dict(mode=CompositionMode.Erase, scale=.5, offset=(+0.00 + .3, -0.10 + .3))),
		(_Icons.chevronDown, dict(mode=CompositionMode.Erase, scale=.5, offset=(-0.051 + .3, -0.051 + .3))),
		(_Icons.chevronDown, dict(mode=CompositionMode.Erase, scale=.5, offset=(-0.10 + .3, +0.00 + .3))),
		(_Icons.chevronDown, dict(scale=.5, offset=(+0.00 + .3, +0.00 + .3)))
	)

	project_chevronDown: QIcon = iconCombiner(_Icons.project, *_shadowedChevronDown)


dpeIcons = _DpeIcons()


ALL_FILES_FILTER: FileExtensionFilter = ('All files', '*')


def frange(a: float, b: float, jump: float, *, includeLAst: bool = False):
	cnt = int(floor(abs(b - a) / jump))
	cnt = cnt + 1 if includeLAst else cnt
	for i in range(cnt):
		yield a + jump * i


WindowId = NewType('WindowId', str)


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
		self.disableContentMargins = True
		self.disableSidebarMargins = True
		self.disableBottombarMargins = True
		self.drawTitleToolbarBorder = True
		self.roundedCorners = CORNERS.ALL

		# TODO: change initial _lastOpenPath:
		self._lastOpenPath = ''

		#GUI
		self.checkAllDialog = CheckAllDialog(self)
		self.searchAllDialog = SearchAllDialog(self)
		self.settingsDialog = SettingsDialog(self, GUICls=DatapackEditorGUI)
		self.profileParsingDialog = ProfileParsingDialog(self)
		self.currentDocumenSubGUI: Optional[DatapackEditorGUI] = None

		self.setAcceptDrops(True)

		getSession().documents.onCanCloseModifiedDocument = self._canCloseModifiedDocument
		GLOBAL_SIGNALS.onError.reconnect('showError', lambda e, title: self._gui.showWarningDialog(title, str(e)))
		GLOBAL_SIGNALS.onWarning.reconnect('showWarning', lambda e, title: self._gui.showWarningDialog(title, '' if e is None else str(e)))

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

	def dragEnterEvent(self, e: QDragEnterEvent):
		if e.mimeData().hasUrls() and all(url.isValid() for url in e.mimeData().urls()):
			e.acceptProposedAction()

	def dropEvent(self, e: QDropEvent):
		for url in e.mimeData().urls():
			filePath = url.toLocalFile()
			getSession().tryOpenOrSelectDocument(filePath)

	# properties:

	@property
	def isToolbarInTitleBar(self) -> bool:
		return applicationSettings.appearance.useCompactLayout

	@property
	def disableStatusbarMargins(self) -> bool:
		return applicationSettings.appearance.useCompactLayout

	# GUI:

	def OnGUI(self, gui: DatapackEditorGUI):
		gui.editor(DocumentsViewsContainerEditor, getSession().documents.viewsC, seamless=True).redrawLater('MainWindow.OnGUI(...)')
		self._saveSession()

	def OnToolbarGUI(self, gui: DatapackEditorGUI):
		self.toolBarGUI2(gui)

	def OnStatusbarGUI(self, gui: DatapackEditorGUI):
		mg = self._gui.margin if self.disableStatusbarMargins else 0
		with gui.hLayout(contentsMargins=(mg, 0, mg, 0)):
			gui.label("this is a status bar.")

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		roundedCorners = CORNERS.RIGHT
		# gui.editor(DatapackFilesEditor, getSession(), roundedCorners=roundedCorners).redrawLater()

		tabs: list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]] = []
		for plugin in PLUGIN_SERVICE.activePlugins:
			tabs.extend(plugin.sideBarTabs())

		with gui.hPanel(seamless=True, roundedCorners=CORNERS.RIGHT):
			with gui.vPanel(seamless=True, windowPanel=True, hSizePolicy=SizePolicy.Fixed.value):
				index = gui.tabBar(
					[tab[0] for tab in tabs],
					drawBase=False,
					documentMode=True,
					expanding=False,
					position=TabPosition.West,
					vSizePolicy=SizePolicy.Expanding.value
				)
			if tabs:
				_, guiFunc, toolBtnFunc = tabs[index]

				if toolBtnFunc is not None:
					toolBtnFunc(gui)
					gui.hSeparator()

				subGui = gui.subGUI(type(gui), guiFunc, seamless=True)
				subGui.redrawGUILater()

	def OnBottombarGUI(self, gui: DatapackEditorGUI):
		bottomPanel = gui.subGUI(type(gui), lambda gui: self.bottomPanelGUI(gui), seamless=True)
		bottomPanel.redrawGUI()

	def documentToolBarGUI(self, gui: DatapackEditorGUI, button, btnCorners, btnOverlap, btnMargins):
		button = gui.framelessButton
		document = self.selectedDocument
		btnKwArgs = dict(roundedCorners=btnCorners, overlap=btnOverlap, margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value)
		with gui.hLayout():
			if button(icon=icons.file, tip='New File', **btnKwArgs, windowShortcut=KEY_SEQUENCES.NEW):
				self._createNewDocument(gui)

			if button(icon=icons.open, tip='Open File', **btnKwArgs, windowShortcut=QKeySequence.Open):
				filePath = gui.showFileDialog(self._lastOpenPath, [*getAllFileExtensionFilters(), ALL_FILES_FILTER], selectedFilter=ALL_FILES_FILTER, style='open')
				if filePath:
					getSession().tryOpenOrSelectDocument(filePath)

			isEnabled = True  # bool(document) and os.path.exists(document.filePathForDisplay)
			if button(icon=icons.save, tip='Save File', **btnKwArgs, enabled=isEnabled, windowShortcut=QKeySequence.Save):
				self._saveOrSaveAs(gui, document)

			if button(icon=icons.saveAs, tip='Save As', **btnKwArgs, enabled=bool(document), windowShortcut=KEY_SEQUENCES.SAVE_AS):
				self._saveAs(gui, document)

			if button(icon=icons.refresh, tip='Reload File', **btnKwArgs, enabled=bool(document) and not document.isNew, windowShortcut=QKeySequence.Refresh):
				if not document.isNew:
					getSession().reloadDocument(document)

			with gui.hLayout(seamless=True, roundedCorners=btnCorners, overlap=btnOverlap):
				if button(icon=icons.undo, tip='Undo', margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value, enabled=bool(document), windowShortcut=QKeySequence.Undo):
					document.undoRedoStack.undoOnce()

				if button(icon=icons.redo, tip='Redo', margins=btnMargins, hSizePolicy=SizePolicy.Fixed.value, enabled=bool(document), windowShortcut=QKeySequence.Redo):
					document.undoRedoStack.redoOnce()

			if button(icon=icons.camera, tip='parse MCFunction', **btnKwArgs, enabled=document is not None):
				gui.showErrorDialog('parse MCFunction', 'This feature ha not been implemented yet')
				# if self.selectedDocument is not None:
				# 	text = self.selectedDocument.strContent
				# 	func, errors = parseMCFunction(getSession().minecraftData.commands, text)
				# 	filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/mcFunction.ast"
				# 	with openOrCreate(filePath, "w") as outFfile:
				# 		formatVal((func, errors), s=FW(outFfile))
				# 	getSession().tryOpenOrSelectDocument(filePath)

	def projectMenu(self, gui: DatapackEditorGUI):
		hasOpenedProject = getSession().hasOpenedProject
		with gui.popupMenu() as menu:
			menu.addAction('Open / Create Project', lambda: self._openOrCreateProjectDialog(gui), icon=icons.project),
			menu.addAction('Close Project', lambda: self._closeProjectDialog(gui), icon=icons.project, enabled=hasOpenedProject),

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
			hasOpenedProject = getSession().hasOpenedProject
			if button(icon=dpeIcons.project_chevronDown, tip='Project...', **btnKwArgs, default=not hasOpenedProject):
				self.projectMenu(gui)

			docToolBarGUI = gui.subGUI(type(gui), lambda g: self.documentToolBarGUI(g, button=button, btnCorners=btnCorners, btnOverlap=btnOverlap, btnMargins=btnMargins), hSizePolicy=SizePolicy.Fixed.value)
			getSession().documents.onSelectedDocumentChanged.reconnect('documentToolBarGUI', docToolBarGUI.host.redraw)
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

			if button(icon=icons.color, tip='Reload Color Scheme', **btnKwArgs, enabled=True):
				theme.reloadAllColorSchemes()

			if button(icon=icons.settings, tip='Settings', **btnKwArgs, windowShortcut=QKeySequence.Preferences):
				self._showSettingsDialog(gui)

			if applicationSettings.debugging.isDeveloperMode:
				gui.hSeparator()
				if button(icon=icons.chevronDown, tip='developer tools', **btnKwArgs, enabled=True):
					self.devToolsDropDownGUI(gui)

				# if button(icon=icons.stopwatch, tip='Profile Parsing', **btnKwArgs, enabled=True):
				# 	self.profileParsingDialog.show()

				# pythonGUI.PROFILING_ENABLED = gui.toggleSwitch(pythonGUI.PROFILING_ENABLED, enabled=True)
				# gui.label('P')

			if self.isToolbarInTitleBar:
				gui.hSeparator()

	def devToolsDropDownGUI(self, gui: DatapackEditorGUI):
		def setProfilingEnabled(checked):
			pythonGUI.PROFILING_ENABLED = checked

		def setLayoutInfoAsToolTip(checked):
			pythonGUI.ADD_LAYOUT_INFO_AS_TOOL_TIP = checked

		def setDebugLayout(checked):
			Widgets.DEBUG_LAYOUT = checked

		def setDebugPaintEvent(checked):
			catWidgetMixins.DO_DEBUG_PAINT_EVENT = checked

		with gui.popupMenu(atMousePosition=False) as popup:
			popup.addAction('Profile Parsing', self.profileParsingDialog.show, icon=icons.stopwatch)
			popup.addAction('profiling Enabled', setProfilingEnabled, icon=icons.stopwatch, checkable=True, checked=pythonGUI.PROFILING_ENABLED)
			popup.addToggle('layout info as tool tip', pythonGUI.ADD_LAYOUT_INFO_AS_TOOL_TIP, setLayoutInfoAsToolTip)
			popup.addToggle('debug layout', Widgets.DEBUG_LAYOUT, setDebugLayout)
			popup.addToggle('debug paint event', catWidgetMixins.DO_DEBUG_PAINT_EVENT, setDebugPaintEvent)

	def bottomPanelGUI(self, gui: DatapackEditorGUI):
		document = self.selectedDocument

		# connect to errorChanged Signal:
		Document.onErrorsChanged.disconnectFromAllInstances(key='bottomPanelGUI')
		if document is not None:
			document.onErrorsChanged.connect('bottomPanelGUI', lambda d: gui.host.redrawLater('onErrorsChanged'))
		getSession().documents.onSelectedDocumentChanged.reconnect('bottomPanelGUI', lambda: gui.host.redrawLater('onSelectedDocumentChanged'))

		tabs = [
			(TabOptions('Errors', icon=icons.error),     (
				lambda *args, **kwargs: self._gitConsoleRefreshTimer.stop() or self.documentErrorsGUI(*args, **kwargs),
				None
			)),
			(TabOptions('Console', icon=icons.terminal), (
				lambda *args, **kwargs: None,
				lambda *args, **kwargs: None,
			)),
		]
		with gui.vLayout(seamless=True):
			with gui.hLayout(seamless=True):  # , windowPanel=True):
				index = gui.tabBar(
					[tab[0] for tab in tabs],
					drawBase=False,
					documentMode=True,
					expanding=False,
					position=TabPosition.North,
					hSizePolicy=SizePolicy.Expanding.value
				)
				guiFunc, toolBtnFunc = tabs[index][1]

				if toolBtnFunc is not None:
					toolBtnFunc(gui)
					gui.hSeparator()
				if document is not None:
					gui.errorsSummaryGUI(getErrorCounts(document.errors))

			with gui.vLayout(seamless=True):  # vSizePolicy=SizePolicy.Expanding.value, seamless=True, windowPanel=True):
				guiFunc(gui)

	def documentErrorsGUI(self, gui: DatapackEditorGUI) -> None:
		document: Optional[Document] = self.selectedDocument
		if document is not None:
			errors: Sequence[GeneralError] = document.errors
			errors = sorted(errors, key=attrgetter('position'))
		else:
			errors: Sequence[GeneralError] = []
		gui.errorsList(
			errors,
			onDoubleClicked=lambda e: (document.locatePosition(e.position, e.end) if e.position is not None else None) or self._gui.redrawGUI(),
		)

	# Dialogs:

	def _showSettingsDialog(self, gui: DatapackEditorGUI) -> None:
		oldStyle = applicationSettings.appearance.applicationStyle

		with gui.overlay():
			self.settingsDialog.exec()

		newStyle = applicationSettings.appearance.applicationStyle
		if oldStyle != newStyle:
			QApplication.setStyle(newStyle)

	def _saveAsDialog(self, gui: DatapackEditorGUI, document: Document) -> str:
		dt = getDocumentTypeForDocument(document)
		if dt is not None:
			selectedFilter = dt.fileExtensionFilter
			selectedFilter = [(selectedFilter[0], f) for f in selectedFilter[1]][0]
		else:
			selectedFilter = ALL_FILES_FILTER
		filePath = gui.showFileDialog(document.unitedFilePath, [*getAllFileExtensionFilters(expanded=True), ALL_FILES_FILTER], selectedFilter=selectedFilter, style='save')
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
	def _closeProjectDialog(gui: DatapackEditorGUI) -> None:
		session = getSession()
		if gui.askUser("Close Project", "Are you sure?", style=MessageBoxStyle.Warning):
			getSession().closeProject()

	@staticmethod
	def _openOrCreateProjectDialog(gui: DatapackEditorGUI) -> None:
		with gui.overlay():
			page, isOk = NewProjectDialog.showModal()
			if not isOk:
				return

			with gui.waitCursor():
				page.acceptAction(gui)

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
			getSession().saveDocument(document)
		return False

	def _saveOrSaveAs(self, gui: DatapackEditorGUI, document: Document) -> bool:
		if document.isNew:
			return self._saveAs(gui, document)
		else:
			return getSession().saveDocument(document)

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
				return True  # close it anyway
			else:  # Cancel
				return False

	@property
	def selectedDocument(self) -> Optional[Document]:
		return getSession().documents.currentView.selectedDocument
