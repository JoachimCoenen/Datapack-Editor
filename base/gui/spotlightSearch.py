from operator import attrgetter
from typing import Optional

from PyQt5.QtCore import QPoint, Qt, QSize
from PyQt5.QtGui import QFocusEvent, QFont, QKeyEvent, QMoveEvent, QResizeEvent
from PyQt5.QtWidgets import QWidget, QLayout

from base.model.applicationSettings import getApplicationSettings
from base.model.project.project import Root, FileEntry
from base.model.searchUtils import FuzzyMatch, getSearchTerms, SearchResults, SearchResult, getFuzzyMatch,\
	performFuzzySearch, autocompleteFromList
from base.model.session import getSession
from basePlugins.projectFiles import FilesIndex
from cat import utils
from cat.GUI import SizePolicy
from cat.GUI.components.Widgets import CatTextField
from cat.GUI.components.catWidgetMixins import CORNERS, NO_MARGINS, NO_OVERLAP, Overlap, RoundedCorners
from cat.GUI.pythonGUI import PythonGUIDialog, PythonGUI
from cat.GUI.utilities import connect, CrashReportWrapped
from cat.utils.profiling import ProfiledFunction, TimedMethod
from gui.datapackEditorGUI import ContextMenuEntries


class SpotlightSearchGui(CatTextField):
	def __init__(self):
		super().__init__()

		self._searchResults: SearchResults[FileEntry] = SearchResults('', [])
		self._resultsPopup: FileSearchPopup = FileSearchPopup(self)
		self.focusEndOfText: bool = False

		self.allChoices: list[FileEntry] = []

		self.setRoundedCorners(CORNERS.ALL)

		connect(self.textChanged, self.onTextChanged)

	@property
	def isPopupVisible(self) -> bool:
		return self._resultsPopup.isVisible()

	@TimedMethod()
	@CrashReportWrapped
	def focusInEvent(self, event: QFocusEvent) -> None:
		super(SpotlightSearchGui, self).focusInEvent(event)
		self.updateAllChoices()

	@CrashReportWrapped
	def keyPressEvent(self, event: QKeyEvent):
		super(SpotlightSearchGui, self).keyPressEvent(event)
		key = event.key()
		if key in (Qt.Key_Up, Qt.Key_Down):
			return self._resultsPopup.onKeyPressed(event)
		elif key == Qt.Key_Tab:
			# do Tab Completion:
			prefix = autocompleteFromList(self.text().strip(), [c.virtualPath for c in self.allChoices])
			if prefix:
				self.setText(prefix)
			return
		elif key == Qt.Key_Escape:
			if self.isPopupVisible:
				self._rejectPopup()
			else:
				self.setText('')
			return
		elif key in (Qt.Key_Return, Qt.Key_Enter):
			self._acceptPopup()
			return
		else:
			return

	@CrashReportWrapped
	def onTextChanged(self, text: str):
		if self.text().strip():
			self.performSearchAndShowPopup()
		else:
			self._rejectPopup()

		# QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 5)
		self._updatePopupGeometry()

	@utils.DeferredCallOnceMethod(delay=166)
	@utils.BusyIndicator
	@TimedMethod(enabled=True)
	@ProfiledFunction(enabled=False)
	# @MethodCallCounter(enabled=True, minPrintCount=10)
	def performSearchAndShowPopup(self):
		text = self.text().strip()
		if text:
			self.performSearch(text)
			self._resultsPopup.setSearchResults(self._searchResults)
			self._showPopup()

	def performSearch(self, searchTerm: str):
		if searchTerm != self._searchResults.searchTerm:
			self._searchResults = performFuzzySearch(self.allChoices, searchTerm, attrgetter('splitNameForSearch'))

	# @ProfiledFunction()
	def updateAllChoices(self) -> None:
		allRoots = self.getAllRoots()
		filePathsToSearch: list[FileEntry] = []

		for pack in allRoots:
			if (filesIndex := pack.indexBundles.get(FilesIndex)) is not None:
				filePathsToSearch.extend(filesIndex.files.values())

		self.allChoices = filePathsToSearch

	def getAllRoots(self) -> list[Root]:
		return getSession().project.allRoots

	def _showPopup(self):
		self._resultsPopup.setTextField(self)
		self._resultsPopup.setFocusProxy(self)
		if not self.isPopupVisible:
			self._resultsPopup.show()

	def _rejectPopup(self):
		self._resultsPopup.setFocusProxy(None)
		if self.isPopupVisible:
			self._resultsPopup.reject()

	def _acceptPopup(self):
		self._resultsPopup.setFocusProxy(None)
		if self.isPopupVisible:
			self._resultsPopup.accept()

	def _updatePopupGeometry(self):
		self._resultsPopup.recalculateGeometry()

		width = max(self.width(), int( 200 * self._scale))
		height = max(self._resultsPopup.height(), int( 0 * self._scale))
		self._resultsPopup.resize(width, height)

	@CrashReportWrapped
	def resizeEvent(self, event: QResizeEvent) -> None:
		super(SpotlightSearchGui, self).resizeEvent(event)
		self._updatePopupGeometry()
		self.setCornerRadius(int(self.height() / 2 / self._scale))

	@CrashReportWrapped
	def moveEvent(self, event: QMoveEvent) -> None:
		super(SpotlightSearchGui, self).moveEvent(event)
		self._updatePopupGeometry()

	def focusOutEvent(self, event: QFocusEvent) -> None:
		super(SpotlightSearchGui, self).focusOutEvent(event)
		if not self._resultsPopup.isActiveWindow():
			self._rejectPopup()
		else:
			self.setFocus()
			self.window().activateWindow()


class FileSearchPopup(PythonGUIDialog):
	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=PythonGUI, parent=parent, flags=Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
		self._isTitlebarVisible = False
		self._disableContentMargins = True
		self.setSuppressRedrawLogging(True)
		# self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.setAttribute(Qt.WA_TranslucentBackground)
		# self.setAttribute(Qt.WA_MacNoShadow)

		self._textField: Optional[CatTextField] = None
		self._searchResults: SearchResults[FileEntry] = SearchResults('', [])
		self._shownResults: list[SearchResult[FileEntry]] = []
		self.selectedItem: Optional[SearchResult[FileEntry]] = None

		self.layout().setSizeConstraint(QLayout.SetFixedSize)

	def setSearchResults(self, searchResults: SearchResults[FileEntry]):
		self._searchResults = searchResults
		self._shownResults = self._searchResults.results[:10]
		if self.selectedItem not in self._shownResults:
			self.selectedItem = None
		else:
			self.selectedItem = self._shownResults[self._shownResults.index(self.selectedItem)]
		if self.selectedItem is None and len(self._shownResults) == 1:
			self.selectedItem = self._shownResults[0]
		self._gui.redrawGUI()

	def setTextField(self, textField: Optional[CatTextField]):
		self._textField = textField

	def OnGUI(self, gui: PythonGUI):
		self.layout().setContentsMargins(*NO_MARGINS)
		with gui.vLayout(preventVStretch=False, verticalSpacing=0):
			if not self._shownResults:
				pass  # gui.addToolbarSpacer(SizePolicy.Ignored, overlap=NO_OVERLAP, roundedCorners=CORNERS.ALL)
			else:
				if len(self._shownResults) == 1:
					self.listElementGUI(gui, self._shownResults[0], overlap=NO_OVERLAP, roundedCorners=CORNERS.ALL)
				else:
					self.listElementGUI(gui, self._shownResults[0], overlap=NO_OVERLAP, roundedCorners=CORNERS.TOP)

					for sr in self._shownResults[1:-1]:
						self.listElementGUI(gui, sr, overlap=(0, 1), roundedCorners=CORNERS.NONE)

					remainingElementsCount = len(self._searchResults.results) - len(self._shownResults)
					if remainingElementsCount == 0:
						self.listElementGUI(gui, self._shownResults[-1], overlap=(0, 1), roundedCorners=(False, False, True, True))
					else:
						self.listElementGUI(gui, self._shownResults[-1], overlap=(0, 1), roundedCorners=CORNERS.NONE)
						self.remainingElementsGUI(gui, remainingElementsCount, overlap=(0, 1), roundedCorners=(False, False, True, True))

	def listElementGUI(self, gui: PythonGUI, sr: SearchResult[FileEntry], overlap: Overlap, roundedCorners: RoundedCorners):

		def labelMaker(formattedStr: str, style: str) -> str:
			return f'<font style="{style}">{formattedStr}</font>'

		def labelMaker1(x: str, fuzzyMatch: FuzzyMatch, style: str) -> str:
			formattedStr = ''
			lastIndex = 0
			for i, matchSlice in fuzzyMatch.indices:
				formattedStr += utils.escapeForXml(x[lastIndex:matchSlice.start])
				lastIndex = matchSlice.stop
				formattedStr += f'<b>{utils.escapeForXml(x[matchSlice])}</b>'
			formattedStr += utils.escapeForXml(x[lastIndex:])

			occurrenceStr = labelMaker(formattedStr, style)
			return occurrenceStr

		def labelMaker2(x: str, style: str) -> str:
			searchTerms = getSearchTerms(self._searchResults.searchTerm)
			fuzzyMatch = getFuzzyMatch(searchTerms, x, strict=False)

			occurrenceStr = labelMaker1(x, fuzzyMatch, style)
			return occurrenceStr

		@CrashReportWrapped
		def onContextMenu(x: FileEntry, *, s=self):
			with gui.popupMenu(atMousePosition=True) as menu:
				menu.addItems(ContextMenuEntries.fileItems(x.fullPath, getSession().tryOpenOrSelectDocument))

		fe = sr.fe
		isSelected = self.selectedItem is not None and fe == self.selectedItem.fe

		fontSize = self.getLargeFontSize()
		if isSelected:
			fileNameStyle = f'font-size: {fontSize}pt; color: #ffffff;'
			pathStyle = f'color: #ffffff'
			font = QFont(self.font())
			font.setWeight(font.weight() + 7)
		else:
			fileNameStyle = f'font-size: {fontSize}pt;'
			pathStyle = f'color: #808080'
			font = self.font()

		with gui.vPanel(
			overlap=overlap,
			roundedCorners=roundedCorners,
			default=isSelected,
			onCustomContextMenuRequested=lambda pos, fe=fe: onContextMenu(fe),
			vSizePolicy=SizePolicy.Fixed.value
		):
			with gui.hLayout():
				if gui.doubleClickLabel(labelMaker1(fe.fileName, sr.aMatch, fileNameStyle), font=font):
					self.selectedItem = sr
					self.accept()
				if gui.doubleClickLabel(labelMaker2(fe.projectName, pathStyle), alignment=Qt.AlignRight, font=font):
					self.selectedItem = sr
					self.accept()
			if gui.doubleClickLabel(labelMaker2(fe.virtualPath, pathStyle), font=font):
				self.selectedItem = sr
				self.accept()

	def getLargeFontSize(self):
		fontSize = int(round(getApplicationSettings().appearance.fontSize * 1.3333))
		return fontSize

	def remainingElementsGUI(self, gui: PythonGUI, count: int, overlap: Overlap, roundedCorners: RoundedCorners):
		with gui.hPanel(overlap=overlap, roundedCorners=roundedCorners):
			fileNameStyle = f'font-size: {self.getLargeFontSize()}pt;'
			if count > 0:
				gui.label(f'<font style="{fileNameStyle}">and {count} more ...</font>')
			else:
				gui.label(f'<font style="{fileNameStyle}"> </font>')

	@CrashReportWrapped
	def openDocument(self, x: FileEntry):
		getSession().tryOpenOrSelectDocument(x.fullPath)

	@CrashReportWrapped
	def accept(self) -> None:
		if self.isVisible():
			if self.selectedItem is not None:
				self.openDocument(self.selectedItem.fe)
		super(FileSearchPopup, self).accept()

	@CrashReportWrapped
	def show(self) -> None:
		super(FileSearchPopup, self).show()
		self.setFocus()

	def onKeyPressed(self, event: QKeyEvent):
		selectedItem = self.selectedItem
		if selectedItem is None:
			currentIndex = -1
		else:
			try:
				currentIndex = self._shownResults.index(selectedItem)
			except ValueError:
				currentIndex = -1
		key = event.key()
		if key in (Qt.Key_Up, Qt.Key_Down):
			if key == Qt.Key_Up:
				if currentIndex == -1:
					newIndex = -1
				else:
					newIndex = currentIndex - 1
			else:
				newIndex = currentIndex + 1
			if newIndex < 0:
				newIndex += len(self._shownResults)
			if newIndex >= len(self._shownResults):
				newIndex -= len(self._shownResults)

			self.selectedItem = self._shownResults[newIndex]
			self._gui.redrawGUI()

	@CrashReportWrapped
	def keyPressEvent(self, event: QKeyEvent) -> None:
			if self._textField is not None:
				self._textField.keyPressEvent(event)
			else:
				super(FileSearchPopup, self).keyPressEvent(event)

	@CrashReportWrapped
	def focusOutEvent(self, event: QFocusEvent) -> None:
		super(FileSearchPopup, self).focusOutEvent(event)
		self.hide()

	def recalculateGeometry(self):
		textField = self._textField
		if textField is not None:
			center = QPoint(textField.width() // 2, textField.height())
			center = textField.mapToGlobal(center)

			width = self.width()
			height = self.height()

			top = center.y() - int(9 * self._gui.scale)
			left = center.x() - width // 2
			self.move(left, top)

	@CrashReportWrapped
	def sizeHint(self) -> QSize:
		textField = self._textField
		if textField is not None:
			return QSize(
				max(textField.width(), int(200 * self._gui.scale)),
				self.minimumSizeHint().height(),
			)
		else:
			return self.minimumSizeHint()

	@CrashReportWrapped
	def resizeEvent(self, event: QResizeEvent) -> None:
		super(FileSearchPopup, self).resizeEvent(event)
		self.recalculateGeometry()
