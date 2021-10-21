from __future__ import annotations
import itertools as it
import os
import traceback
from math import floor
from operator import attrgetter
from typing import Optional, Sequence, Iterable, Iterator

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication

import Cat
from Cat import utils
from Cat.CatPythonGUI.GUI import CORNERS, NO_OVERLAP, NO_MARGINS, SizePolicy, Overlap, RoundedCorners, getStyles, maskCorners, adjustOverlap
from Cat.CatPythonGUI.GUI.codeEditor import Position, Error
from Cat.CatPythonGUI.GUI.enums import TabPosition, MessageBoxStyle, MessageBoxButton
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.pythonGUI import PythonGUIWidget
from Cat.icons import icons
from Cat.utils import openOrCreate, CachedProperty, Maybe
from Cat.utils.collections import OrderedMultiDict, OrderedDict
from Cat.utils.formatters import indentMultilineStr, formatVal, FW
from Cat.utils.profiling import logError, logInfo
from model.commands.commands import AllCommands, BASIC_COMMAND_INFO
from model.commands.parser import parseMCFunction
from documents import Document, DocumentTypeDescription, getDocumentTypes, getFilePathForDisplay, getErrorCounts
from gui import editors
from gui.checkAllDialog import CheckAllDialog
from gui.searchAllDialog import SearchAllDialog
from gui.spotlightSearch import SpotlightSearchGui
from model.pathUtils import FilePath
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries, DocumentGUIFunc, getDocumentDrawer
from session import getSession, WindowId, getSessionFilePath, saveSessionToFile, loadSessionFromFile
from settings import applicationSettings
from settings.settingsDialog import SettingsDialog


def frange(a: float, b: float, jump: float, *, includeLAst: bool = False):
	cnt = int(floor(abs(b - a) / jump))
	cnt = cnt + 1 if includeLAst else cnt
	for i in range(cnt):
		yield a + jump * i


class KeySequences:
	@CachedProperty
	def FIND_ALL(self) -> QKeySequence:
		return QKeySequence('Ctrl+Shift+F')

	@CachedProperty
	def GO_TO_FILE(self) -> QKeySequence:
		return QKeySequence('Ctrl+P')

	@CachedProperty
	def NEW(self) -> QKeySequence:
		return QKeySequence(QKeySequence.New)

	@CachedProperty
	def SAVE_AS(self) -> QKeySequence:
		# windows does not have a standard key sequence for 'Save As':
		return QKeySequence('Ctrl+Shift+S') if utils.PLATFORM_IS_WINDOWS else QKeySequence(QKeySequence.SaveAs)

	@CachedProperty
	def CLOSE_DOCUMENT(self) -> QKeySequence:
		return QKeySequence('Ctrl+W') if utils.PLATFORM_IS_WINDOWS else QKeySequence(QKeySequence.Close)


KEY_SEQUENCES = KeySequences()


def newMainWindow() -> MainWindow:
	# find first id that is not used:
	existingIds = set()#set(getSession().selectedDocumentIds.keys())
	newId = next(it.filterfalse(lambda x: existingIds.__contains__(str(x)), it.count(0)))
	newId = WindowId(str(newId))
	window = MainWindow(newId)
	window._gui.redrawGUI()
	window.show()
	return window


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
		super().__init__(GUICls=DatapackEditorGUI)#, flags=Qt.Window)

		self._gitConsoleRefreshTimer: QTimer = QTimer(self) # for the git tab
		self._gui._name = f'main Window GUI {id}'
		self._id: WindowId = id
		MainWindow.registerMainWindow(self, id)
		self.disableContentMargins = True
		self.disableSidebarMargins = True
		self._isToolbarInTitleBar = False
		self._drawTitleToolbarBorder = False
		self.roundedCorners = CORNERS.ALL

		self._lastOpenPath = 'D:/Development/svn/CODIM_0_9_6/de.ascon_systems.sms/webapp/WEB-INF/model'
		#self._searchDirectory = 'C:/users\\';

		#GUI
		self.checkAllDialog = CheckAllDialog(self)
		self.searchAllDialog = SearchAllDialog(self)
		self.settingsDialog = SettingsDialog(self)
		self.currentDcumenSubGUI: Optional[DatapackEditorGUI] = None

		self.setAcceptDrops(True)

		# close document as shortcut:
		# self.closeDocumentShortcut = QShortcut(KEY_SEQUENCES.CLOSE_DOCUMENT, self, lambda d=document, s=self: self._safelyCloseDocument(gui, getSession().selectedDocument),
		# TODO:		  lambda d=document, s=self: asdasdasdasdasd s._safelyCloseDocument(gui, d), Qt.WidgetWithChildrenShortcut)

	@property
	def id(self) -> WindowId:
		return self._id

	def closeEvent(self, event: QCloseEvent):
		self._saveSession()
		getSession().selectedDocuments.pop(self.id)
		MainWindow.deregisterMainWindow(self.id)
		event.accept()

	def _mainAreaGUI(self, gui: DatapackEditorGUI, overlap: Overlap, roundedCorners: RoundedCorners):
		contentsMargins = self._mainAreaMargins
		with gui.vLayout(contentsMargins=contentsMargins):
			self.OnGUI(gui)

	def OnGUI(self, gui: DatapackEditorGUI):
		# app = cast(QApplication, QApplication.instance())
		# self._updateApplicationDisplayName(app)
		tabBarOverlap = (0, 1, 0, 1) if self._drawTitleToolbarBorder else (0, 0, 0, 1)
		with gui.vSplitter(handleWidth=self.margin) as splitter:
			with splitter.addArea(stretchFactor=2, id_=1, verticalSpacing=0):
				with gui.hPanel(contentsMargins=NO_MARGINS, horizontalSpacing=0, overlap=tabBarOverlap, roundedCorners=CORNERS.TOP_LEFT, windowPanel=True):
					self.documentsTabBarGUI(gui, position=TabPosition.North, overlap=tabBarOverlap, roundedCorners=CORNERS.TOP_LEFT)
				panelOverlap = NO_OVERLAP if getSession().documents else (0, 1, 0, 0)
				with gui.vPanel(contentsMargins=NO_MARGINS, overlap=panelOverlap, roundedCorners=CORNERS.BOTTOM_LEFT, windowPanel=True):
					self.documentsGUI(gui)
			with splitter.addArea(stretchFactor=0, id_=2, verticalSpacing=0):
				bottomPanel = gui.subGUI(type(gui), lambda gui: self.bottomPanelGUI(gui, roundedCorners=(True,  False,  True, False), cornerRadius=self.windowCornerRadius))
				# connect to errorChanged Signal:
				Document.onErrorsChanged.disconnectFromAllInstances(key='bottomPanelGUI')
				document = self.selectedDocument
				if document is not None:
					document.onErrorsChanged.connect('bottomPanelGUI', lambda d, bottomPanel=bottomPanel: bottomPanel.redrawGUI())

				bottomPanel.redrawGUI()
		self._saveSession()

	def OnToolbarGUI(self, gui: DatapackEditorGUI):
		self.toolBarGUI2(gui)

	def OnStatusbarGUI(self, gui: DatapackEditorGUI):
		self.sessionToolBarGUI(gui)

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		gui.editor(editors.DatapackFilesEditor, getSession().world)

	def toolbarGUI(self, gui: DatapackEditorGUI):
		if gui.button('Ban Cameras', icons.camera_ban):
			if gui.askUser(title='Really?', message='Do you want to ban all cameras?'):
				gui.showErrorDialog(title='Error', message='You cannot ban all cameras!')
			else:
				gui.showInformationDialog(title='phew...', message='Thank goodness!')

		if gui.button(icon=icons.camera, tip='showCommandInfo'):
			ac = AllCommands.create(BASIC_COMMAND_INFO=BASIC_COMMAND_INFO)
			filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/commands.ast"
			with openOrCreate(filePath, "w") as outFfile:
				ac.toJSON(outFfile)
			self._tryOpenOrSelectDocument(filePath)
			# gui.askUserInput('title', cisStr, guiFuncKwArgs=dict(style=getStyles().fixedWidthChar, isMultiline=True))

		if gui.button(icon=icons.camera, tip='parse MCFunction'):
			text = self.selectedDocument.content
			func, errors = parseMCFunction(text)
			filePath = "D:/Programming/Python/MinecraftDataPackEditor/sessions/mcFunction.ast"
			with openOrCreate(filePath, "w") as outFfile:
				formatVal((func, errors), s=FW(outFfile))
			self._tryOpenOrSelectDocument(filePath)
			# gui.askUserInput('title', cisStr, guiFuncKwArgs=dict(style=getStyles().fixedWidthChar, isMultiline=True))

	def toolBarGUI2(self, gui: DatapackEditorGUI):
		sdm = gui.smallDefaultMargins
		dm = gui.defaultMargins
		hSpacing = self.spacing + int(((dm[0] - sdm[0]) + (dm[1] - sdm[1])) * gui._scale / 2)

		button = gui.toolButton
		btnCorners = CORNERS.ALL
		btnMargins = gui.smallDefaultMargins

		with gui.hLayout(horizontalSpacing=hSpacing):
			hasOpenedWorld = getSession().hasOpenedWorld
			if button(icon=icons.globeAlt, tip='Switch World' if hasOpenedWorld else 'Load World', roundedCorners=btnCorners, margins=btnMargins, default=not hasOpenedWorld):
				self._loadWorldDialog(gui)

			document = self.selectedDocument
			if gui.toolButton(icon=icons.file, tip='New File', roundedCorners=btnCorners, margins=btnMargins, shortcut=KEY_SEQUENCES.NEW):
				self._createNewDocument(gui)

			if gui.toolButton(icon=icons.open, tip='Open File', roundedCorners=btnCorners, margins=btnMargins, shortcut=QKeySequence.Open):
				filePath = gui.showFileDialog(self._lastOpenPath, [('model', '.xml'), ('java', '.java'), ('All files', '*')], style='open')
				if filePath:
					self._tryOpenOrSelectDocument(filePath)

			isEnabled = True  # bool(document) and os.path.exists(document.filePathForDisplay)
			if gui.toolButton(icon=icons.save, tip='Save File', roundedCorners=btnCorners, margins=btnMargins, enabled=isEnabled, shortcut=QKeySequence.Save):
				self._saveOrSaveAs(gui, document)

			if gui.toolButton(icon=icons.saveAs, tip='Save As', roundedCorners=btnCorners, margins=btnMargins, enabled=bool(document), shortcut=KEY_SEQUENCES.SAVE_AS):
				self._saveAs(gui, document)

			if gui.toolButton(icon=icons.refresh, tip='Reload File', roundedCorners=btnCorners, margins=btnMargins, enabled=bool(document), shortcut=QKeySequence.Refresh):
				filePath = document.filePath
				if filePath:
					try:
						document.loadFromFile()
					except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
						gui.showAndLogError(e)

			with gui.hLayout(horizontalSpacing=0):
				if gui.toolButton(icon=icons.undo, tip='Undo', roundedCorners=maskCorners(btnCorners, CORNERS.LEFT), margins=btnMargins, enabled=bool(document), shortcut=QKeySequence.Undo):
					document.undoRedoStack.undoOnce()

				if gui.toolButton(icon=icons.redo, tip='Redo', roundedCorners=maskCorners(btnCorners, CORNERS.RIGHT), margins=btnMargins, overlap=(1, 0), enabled=bool(document), shortcut=QKeySequence.Redo):
					document.undoRedoStack.redoOnce()

			gui.addHSpacer(0, SizePolicy.Expanding)

		self.fileSearchFieldGUI(gui, btnCorners)

		with gui.hLayout(horizontalSpacing=hSpacing):
			gui.addHSpacer(0, SizePolicy.Expanding)

			if button(icon=icons.search, tip='Search all', roundedCorners=btnCorners, margins=btnMargins, shortcut=KEY_SEQUENCES.FIND_ALL):
				self.searchAllDialog.show()

			if button(icon=icons.spellCheck, tip='Check all Files', roundedCorners=btnCorners, margins=btnMargins, enabled=True):
				self.checkAllDialog.show()

			if button(icon=icons.settings, tip='Settings', roundedCorners=btnCorners, margins=btnMargins, shortcut=QKeySequence.Preferences):
				self._showSettingsDialog(gui)

			if button(icon=icons.windowRestore, tip='New Window', roundedCorners=btnCorners, margins=btnMargins):
				newMainWindow()

			self.toolbarGUI(gui)

			if applicationSettings.debugging.isDeveloperMode:
				gui.hSeparator()
				Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled = gui.toggleSwitch(Cat.CatPythonGUI.GUI.pythonGUI.profilingEnabled, enabled=True)
				gui.label('P')

	def sessionToolBarGUI(self, gui: DatapackEditorGUI):
		with gui.hLayout():
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
			with gui.hPanel(contentsMargins=(0, 0, self.margin, 0), overlap=(0, -1), roundedCorners=maskCorners(roundedCorners, CORNERS.TOP), windowPanel=True):
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

	def documentsGUI(self, gui: DatapackEditorGUI):
		def onGUI(gui: DatapackEditorGUI, document: Document):
			if applicationSettings.debugging.showUndoRedoPane:
				with gui.hSplitter() as splitter:
					with splitter.addArea(contentsMargins=NO_MARGINS):
						self.documentFieldGUI(gui, document)
					with splitter.addArea():
						gui.valueField(document.undoRedoStack)
			else:
				self.documentFieldGUI(gui, document)
			self.documentFooterGUI(gui, document)

			#gui.valueField(document.undoRedoStack)
			# document.undoRedoStack.serializePy(s, strict=False)
			# gui.advancedCodeField(str(s), language='Python')

		def onInit(widget: PythonGUIWidget, document: Document):
			# undo/redo shortcuts:
			# QShortcut(QKeySequence.Undo, widget, lambda d=document, w=widget: d.undoRedoStack.undoOnce() or w._gui.redrawGUI(), lambda d=document, w=widget: d.undoRedoStack.undoOnce() or w._gui.redrawGUI(), Qt.WidgetWithChildrenShortcut)
			# QShortcut(QKeySequence.Redo, widget, lambda d=document, w=widget: d.undoRedoStack.redoOnce() or w._gui.redrawGUI(), lambda d=document, w=widget: d.undoRedoStack.redoOnce() or w._gui.redrawGUI(), Qt.WidgetWithChildrenShortcut)
			# save/save as shortcuts:
			# QShortcut(QKeySequence.Save, widget, lambda d=document, w=widget: d. or w._gui.redrawGUI(), lambda d=document, w=widget: d.undoRedoStack.undoOnce() or w._gui.redrawGUI(), Qt.WidgetWithChildrenShortcut)
			# QShortcut(QKeySequence.Redo, widget, lambda d=document, w=widget: d.undoRedoStack.redoOnce() or w._gui.redrawGUI(), lambda d=document, w=widget: d.undoRedoStack.redoOnce() or w._gui.redrawGUI(), Qt.WidgetWithChildrenShortcut)
			widget.redraw()  # redraw a second time!

		if getSession().documents:
			selectedDocumentId = self.selectedDocumentId
			with gui.stackedWidget(selectedView=selectedDocumentId) as stacked:
				for document in getSession().documents:
					with stacked.addView(id_=document.filePathForDisplay):
						subGUI = gui.subGUI(
							DatapackEditorGUI,
							guiFunc=lambda gui, document=document: onGUI(gui, document),
							onInit=lambda w, document=document: onInit(w, document) or True
						)
						if document.filePathForDisplay == selectedDocumentId:
							self.currentDcumenSubGUI = subGUI
		else: # no documents are open:
			mg = self.margin
			with gui.vLayout(contentsMargins=(mg, mg, mg, mg)):
				gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)
				gui.label('No Document Opened.', wordWrap=False, alignment=Qt.AlignCenter)
				gui.addVSpacer(mg, SizePolicy.Fixed)
				gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.GO_TO_FILE.toString()}</font>' to search for a file.", wordWrap=False, alignment=Qt.AlignCenter)
				gui.label(f"Press '<font style=\"font-weight: 500\">{KEY_SEQUENCES.NEW.toString()}</font>' to create a new file.", wordWrap=False, alignment=Qt.AlignCenter)
				gui.addVSpacer(int(50 * gui._scale), SizePolicy.Expanding)

		if self.selectedDocument is None:
			self.currentDcumenSubGUI = None
		if self.currentDcumenSubGUI is not None:
			self.currentDcumenSubGUI.redrawGUI()

	def documentsTabBarGUI(self, gui: DatapackEditorGUI, position: TabPosition = TabPosition.North, overlap: Overlap = (0, 0), roundedCorners: RoundedCorners = CORNERS.ALL):
		tabs = OrderedMultiDict((
			(document.filePathForDisplay, (document.fileName + (' *' if document.documentChanged else '   '), ))
			for document in getSession().documents
		))

		try:
			selectedTab = list(tabs.keys()).index(self.selectedDocumentId)
		except ValueError:
			selectedTab = None

		def tabCloseRequested(index: int):
			if index in range(len(getSession().documents)):
				self._safelyCloseDocument(gui, getSession().documents[index])

		def tabMoved(from_: int, to: int):
			print(f"tab {from_} moved to {to}.")
			indexRange = range(len(getSession().documents))
			if from_ in indexRange and to in indexRange:
				self._safelyMoveDocumentPosition(gui, getSession().documents[from_], to)

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
			self.selectedDocumentId = list(tabs.keys())[index]
		else:
			self.selectedDocumentId = None

		if gui.toolButton(icon=icons.chevronDown, overlap=adjustOverlap(overlap, (0, None, None, None)), roundedCorners=CORNERS.NONE):
			self._showOpenedDocumentsPopup(gui)

	def documentFooterGUI(self, gui: DatapackEditorGUI, document: Document):
		space = int(3 * gui._scale) + 1
		mg = self.smallSpacing
		with gui.hLayout(contentsMargins=(mg, 0, mg, space)):
			def fileContextMenu(pos):
				with gui.popupMenu(True) as menu:
					menu.addItems(ContextMenuEntries.pathItems(document.filePath))

			gui.elidedLabel(
				document.filePathForDisplay,
				elideMode=Qt.ElideMiddle,
				sizePolicy=(SizePolicy.Maximum.value, SizePolicy.Fixed.value),
				# textInteractionFlags=Qt.TextSelectableByMouse | Qt.LinksAcces	sibleByMouse,
				contextMenuPolicy=Qt.CustomContextMenu,
				onCustomContextMenuRequested=fileContextMenu
			)
			if document.documentChanged:
				gui.label('*', style=getStyles().bold)

			gui.addHSpacer(0, SizePolicy.Expanding)

			gui.propertyField(document, document.languageProp)

	@staticmethod
	def documentFieldGUI(gui: DatapackEditorGUI, document: Document):
		if document:
			try:
				docDrawer: DocumentGUIFunc = getDocumentDrawer(type(document))
				document = docDrawer(gui, document)

				if document.fileChanged:
					reloadFile: bool = not document.documentChanged
					if not reloadFile:
						reloadFile = gui.askUser(
							f'{document.fileName} has changed on disk',
							f"Do you want to reload it?"
						)
					if reloadFile:
						document.loadFromFile()
					else:
						document.discardFileSystemChanges()

				# oldUndoCount = document.undoRedoStack.undoCount
				# document.undoRedoStack.takeSnapshotIfChanged(doDeepCopy=True)
				# if oldUndoCount != document.undoRedoStack.undoCount:
				# 	document.documentChanged = True
			except Exception as e:
				traceback.format_exc()
				logError(f'{e}:\n{indentMultilineStr(traceback.format_exc(), indent="  ")} ')
				gui.helpBox(f'cannot draw document: {e}')
				gui.button('retry')  # pressing causes a gui update & redraw
		else:
			gui.helpBox('No Document opened', style='info')

	# Dialogs:

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

	def _showOpenedDocumentsPopup(self, gui: DatapackEditorGUI) -> None:
		class Documents:
			def __iter__(self) -> Iterator[Document]:
				yield from getSession().documents

		selectedDocument = self.selectedDocument

		def onContextMenu(d: Document, column: int):
			print(f"showning ContextMenu for Document '{d.fileName}'")
			with gui.popupMenu(atMousePosition=True) as menu:
				menu.addItem('close', lambda d=d: self._safelyCloseDocument(gui, d), tip=f'close {d.filePath}')
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
			self.selectedDocument = selectedDocument

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
		newPath = gui.showFolderDialog(session.world.path)
		if newPath is not None:
			session.openWorld(newPath)

	# Fields:

	@staticmethod
	def fileSearchFieldGUI(gui: DatapackEditorGUI, roundedCorners: RoundedCorners = CORNERS.ALL) -> None:
		gui.customWidget(
			SpotlightSearchGui,
			placeholderText=f'Press \'{KEY_SEQUENCES.GO_TO_FILE.toString()}\' to find a file',
			roundedCorners=roundedCorners,
			alignment=Qt.AlignCenter,
			windowShortcut=KEY_SEQUENCES.GO_TO_FILE
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
		doc = getSession().createNewDocument(docType, None, self.id)
		self.selectedDocument = doc
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
		doc = getSession().getDocument(filePath)
		if doc is None:
			doc = self._tryOpenDocument(filePath)
		if doc is not None:
			self.selectedDocument = doc
			if selectedPosition is not None:
				doc.locatePosition(selectedPosition)
		self._gui.redrawGUI()

	def _tryOpenDocument(self, filePath: FilePath) -> Optional[Document]:
		try:
			doc = self._openDocument(filePath)
			self._gui.redrawGUI()
			return doc
		except (FileNotFoundError, PermissionError) as e:  # TODO: catch other openFile Errors
			self._gui.showAndLogError(e)
		return None

	def _openDocument(self, filePath: FilePath) -> Document:
		# TODO: move method to Session class...
		assert(filePath)
		logInfo("opening File from:{}".format(filePath))
		displayPath = getFilePathForDisplay(filePath)
		if os.path.exists(displayPath):
			self._lastOpenPath = os.path.dirname(displayPath)

		return getSession().openDocument(filePath, self.id, atPosition=None)

	def _safelyCloseDocument(self, gui: DatapackEditorGUI, document: Document):
		forceClose = False
		if document.documentChanged:
			msgBoxResult = gui.showMessageDialog(
				# f'Save Changes?',
				f'Do you want to save the changes made to the file {document.fileName}?',
				# '{document.fileName} has been modified. \nSave changes?',
				f'You can discard to undo the changes since you have last saved / opened the file.',
				MessageBoxStyle.Warning,
				{MessageBoxButton.Save, MessageBoxButton.Discard, MessageBoxButton.Cancel}
			)
			if msgBoxResult == MessageBoxButton.Save:
				self._saveOrSaveAs(gui, document)  # will reset documentChanged
			elif msgBoxResult == MessageBoxButton.Discard:
				forceClose = True  # close it anyways
			else:  # Cancel
				pass

		if not document.documentChanged or forceClose:
			getSession().closeDocument(document, self.id)
			self._gui.redrawGUI()
			self._gui.redrawGUI()

	@staticmethod
	def _safelyMoveDocumentPosition(gui: DatapackEditorGUI, document: Document, newPosition: int):
		documents = getSession().documents
		if newPosition not in range(len(documents)):
			raise ValueError(f"newPosition is out of range (newPosition={newPosition}, len(documents)={len(documents)}")

		oldPosition = documents.index(document)
		if oldPosition == newPosition:
			return

		del documents[oldPosition]
		documents.insert(newPosition, document)

	@property
	def selectedDocument(self) -> Optional[Document]:
		return getSession().selectedDocuments[self.id]

	@selectedDocument.setter
	def selectedDocument(self, document: Optional[Document]) -> None:
		getSession().selectedDocuments[self.id] = document

	@property
	def selectedDocumentId(self) -> Optional[str]:
		return Maybe(self.selectedDocument).getattr('filePathForDisplay').get()

	@selectedDocumentId.setter
	def selectedDocumentId(self, document: Optional[str]) -> None:
		getSession().selectedDocumentIds[self.id] = document

	
					
					
					
					
					
					
					
					
					