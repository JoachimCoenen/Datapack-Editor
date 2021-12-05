import re
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtCore import QPoint, Qt, QSize
from PyQt5.QtGui import QFocusEvent, QFont, QKeyEvent, QMoveEvent, QResizeEvent
from PyQt5.QtWidgets import QWidget, QLayout

from Cat.CatPythonGUI.GUI import SizePolicy
from Cat.CatPythonGUI.GUI.catWidgetMixins import CORNERS, NO_MARGINS, NO_OVERLAP, Overlap, RoundedCorners
from Cat.CatPythonGUI.GUI.pythonGUI import PythonGUIDialog, PythonGUI
from Cat.CatPythonGUI.GUI.Widgets import CatTextField
from Cat.CatPythonGUI.utilities import connect, CrashReportWrapped
from Cat.utils.profiling import ProfiledFunction, TimedMethod
from Cat import utils
from gui.datapackEditorGUI import autocompleteFromList, ContextMenuEntries
from model.Model import Datapack
from model.pathUtils import FilePath
from session.session import getSession

from settings import applicationSettings


@dataclass
class FileEntry:
	path: str
	splitPath: list[tuple[int, str]]
	fileName: str
	fullPath: FilePath
	datapack: Datapack

	def __hash__(self):
		return hash((56783265, self.fullPath))


@dataclass
class SearchTerms:
	searchTerm: str
	subTerms: list[tuple[int, str]]
	lowerSubTerms: list[str]



@dataclass
class FuzzyMatch:
	#indices: OrderedMultiDict[int, slice] = field(default_factory=OrderedMultiDict)
	indices: list[tuple[int, slice]]# = field(default_factory=list)
	matchQuality: tuple[float, float]  # = (fullMatches / partsCnt, partialMatches / partsCnt)

	@property
	def anyMatch(self) -> bool:
		return bool(self.indices)

	def clear(self) -> None:
		self.indices.clear()


@dataclass
class SearchResult:
	fe: FileEntry
	match_: FuzzyMatch = field(compare=False)

@dataclass
class SearchResults:
	searchTerm: str
	results: list[SearchResult]


def splitStringForSearch(string: str) -> list[tuple[int, str]]:
	# subTerms = [st for st in re.split(r'(?=[^a-z0-9])', string.strip())]
	# subTerms = [st.lower() for st in re.split(r'(?=[A-Z])|\b', string.strip()) if st]

	subTerms: list[tuple[int, str]] = []
	idx = 0
	for i, st in enumerate(re.split(r'((?=[A-Z])|[\W_]+)', string.strip())):
		if st:
			if i % 2 == 0: # we don't have a separator:
				subTerms.append((idx, st.lower()))
			idx += len(st)

	return subTerms


def getSearchTerms(searchTerm: str) -> SearchTerms:
	subTerms = splitStringForSearch(searchTerm)
	lowerSubTerms = [s[1].lower() for s in subTerms]
	return SearchTerms(searchTerm, subTerms, lowerSubTerms)


def getFuzzyMatch(searchTerms: SearchTerms, string: str, *, strict: bool) -> Optional[FuzzyMatch]:
	lastIndex: int = 0
	indices = []
	lowerString = string.lower()

	for i, st in enumerate(searchTerms.lowerSubTerms):
		index = lowerString.find(st, lastIndex)
		if index < 0:
			if strict:
				return None
		else:
			lastIndex = index + len(st)
			indices.append((i, slice(index, lastIndex)))

	return FuzzyMatch(indices, (.5, .5))


def getFuzzyMatch2(allSearchTerms: SearchTerms, splitStrs: list[tuple[int, str]], *, strict: bool) -> Optional[FuzzyMatch]:
	if not allSearchTerms.lowerSubTerms:
		return None

	indices: list[tuple[int, slice]] = []
	fullMatchCount: int = 0
	partialMatchCount: int = 0

	#splitStrs = splitStringForSearch(string)
	splitStrsLen = len(splitStrs)
	splitIdx = 0

	searchTerms = allSearchTerms.lowerSubTerms
	searchTermsLen = len(searchTerms)
	stIdx = 0
	st: str = searchTerms[stIdx]
	while stIdx < searchTermsLen and splitIdx < splitStrsLen:
		splitStartIdx, subStr = splitStrs[splitIdx]
		if st.startswith(subStr):
			oldStartIdx = splitStartIdx
			oldSplitIdx = splitIdx
			while True:
				fullMatchCount += 1
				splitIdx += 1
				if splitIdx >= splitStrsLen:
					break
				idxInSt = len(subStr)
				splitStartIdx, subStr = splitStrs[splitIdx]
				st = st[idxInSt:]
				if not st or not st.startswith(subStr):
					break
			if st:  # we have some leftovers:
				if subStr.startswith(st):  # leftovers could be matched:
					partialMatchCount += 1
					indices.append((stIdx, slice(oldStartIdx, splitStartIdx)))
					splitIdx += 1
					stIdx += 1
					if stIdx < searchTermsLen:
						st = searchTerms[stIdx]
						continue
					else:
						break
				else:  # leftovers couldn't be matched, so do a rollback:
					splitIdx = oldSplitIdx + 1  # bc. splitStrs[splitIdx] was a failure
					st = searchTerms[stIdx]
					continue
			else:  # we have NO leftovers:
				indices.append((stIdx, slice(oldStartIdx, splitStartIdx)))
				stIdx += 1
				if stIdx < searchTermsLen:
					st = searchTerms[stIdx]
					continue
				else:
					break
		elif subStr.startswith(st):
			partialMatchCount += 1
			indices.append((stIdx, slice(splitStartIdx, splitStartIdx + len(st))))
			splitIdx += 1
			stIdx += 1
			if stIdx < searchTermsLen:
				st = searchTerms[stIdx]
				continue
			else:
				break
			pass
		else:
			splitIdx += 1

	if stIdx < searchTermsLen:
		return None

	#assert len(indices) == len(searchTerms)
	assert stIdx == len(searchTerms)
	return FuzzyMatch(indices, (fullMatchCount / splitStrsLen, partialMatchCount / splitStrsLen))


class SpotlightSearchGui(CatTextField):
	def __init__(self):
		super().__init__()

		self._searchResults: SearchResults = SearchResults('', [])
		self._resultsPopup: FileSearchPopup = FileSearchPopup(self)
		self.focusEndOfText: bool = False

		self.allChoices: list[FileEntry] = []
		self.lastFEsCache: dict[tuple[str, int], tuple[list[FilePath], list[FileEntry]]] = {}
		#self.updateAllChoices()

		self.setRoundedCorners(CORNERS.ALL)

		connect(self.textChanged, self.onTextChanged)

	@property
	def isPopupVisible(self) -> bool:
		return self._resultsPopup.isVisible()

	@TimedMethod()
	@CrashReportWrapped
	#@ProfiledFunction()
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
			prefix = autocompleteFromList(self.text().strip(), [c.path for c in self.allChoices])
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

		#QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 5)
		self._updatePopupGeometry()

	@utils.DeferredCallOnceMethod(delay=166)
	@utils.BusyIndicator
	@TimedMethod(enabled=True)
	@ProfiledFunction(enabled=False)
	#@MethodCallCounter(enabled=True, minPrintCount=10)
	def performSearchAndShowPopup(self):
		text = self.text().strip()
		if text:
			self.performSearch(text)
			self._resultsPopup.setSearchResults(self._searchResults)
			self._showPopup()

	def performSearch(self, searchTerm: str):
		# searchTerms = getSearchTerms('ConFiFi')
		# fp = "org/docx4j/wml/CTMailMergeOdsoFMDFieldType.java"
		# searchResults = [
		# 	SearchResult(fe, fuzzyMatch)
		# 	for fe, fuzzyMatch in ((fe, getFuzzyMatch2(searchTerms, fe.splitPath, strict=True)) for fe in [
		# 		FileEntry(
		# 			fp,
		# 			splitStringForSearch(fp.rpartition('/')[2]),
		# 			fp.rpartition('/')[2],
		# 			fp,
		# 			getSession().project
		# 		)
		# 	])
		# 	if fuzzyMatch is not None
		# ]

		if searchTerm != self._searchResults.searchTerm:
			# update search results:
			searchTerms = getSearchTerms(searchTerm)

			searchResults = [
				sr
				for sr in (SearchResult(fe, getFuzzyMatch2(searchTerms, fe.splitPath, strict=True)) for fe in self.allChoices)
				if sr.match_ is not None
			]
			searchResults.sort(key=lambda x: x.match_.matchQuality, reverse=True)
			self._searchResults = SearchResults(searchTerm, searchResults)

	def updateAllChoices(self) -> None:
		# filterByRole: Optional[FilterByRoleOptions] = None
		# if filterByRole is None:
		# 	filterByRole = FilterByRoleOptions(
		# 		layouts=True,
		# 		configs=True,
		# 		models=True,
		# 		java=True,
		# 		properties=True,
		# 		translations=True,
		# 	)

		searchFileProps = [Datapack.files]

		allDatapacks = self.getAllDatapacks()
		filePathsToSearch: list[FileEntry] = []

		lastFEs: dict[tuple[str, int], tuple[list[FilePath], list[FileEntry]]] = self.lastFEsCache
		newFEs: dict[tuple[str, int], tuple[list[FilePath], list[FileEntry]]] = {}

		for pack in allDatapacks:
			for i, searchFileProp in enumerate(searchFileProps):
				feKey = (pack.name, i)
				lastFE = lastFEs.pop(feKey, None)
				fullPaths = searchFileProp.get(pack)
				if lastFE is not None and lastFE[0] == fullPaths:
					newFEs[feKey] = lastFE
					filePathsToSearch += lastFE[1]
				else:
					newFE = []
					for fullPath in fullPaths:
						path = fullPath[1] if isinstance(fullPath, tuple) else fullPath
						newFE.append(FileEntry(
							path,
							splitStringForSearch(path.rpartition('/')[2]),
							path.rpartition('/')[2],
							fullPath,
							pack
						))
					newFEs[feKey] = (fullPaths, newFE)
					filePathsToSearch += newFE

		self.lastFEsCache = newFEs
		self.allChoices = filePathsToSearch

	def getAllDatapacks(self) -> list[Datapack]:
		return getSession().world.datapacks

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
		return
		if self.parent() is not None:
			center = self.geometry().left() + self.geometry().width() / 2
			left = center - self._resultsPopup.width() / 2
			bottomLeft = self.parent().mapToGlobal(QPoint(int(left), int(self.geometry().bottom() + 9)))# * gui.scale))
			self._resultsPopup.move(bottomLeft)

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
		#self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.setAttribute(Qt.WA_TranslucentBackground)
		#self.setAttribute(Qt.WA_MacNoShadow)

		self._textField: Optional[CatTextField] = None
		self._searchResults: SearchResults = SearchResults('', [])
		self._shownResults: list[SearchResult] = []
		self.selectedItem: Optional[SearchResult] = None

		#self._topCenter: QPoint = QPoint()

		self.layout().setSizeConstraint(QLayout.SetFixedSize)
		# sp = self.sizePolicy()
		# sp.setVerticalPolicy(SizePolicy.Fixed.value)
		# sp.setHorizontalPolicy(SizePolicy.Fixed.value)
		# self.setSizePolicy(sp)

	def setSearchResults(self, searchResults: SearchResults):
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

	def listElementGUI(self, gui: PythonGUI, sr: SearchResult, overlap: Overlap, roundedCorners: RoundedCorners):

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
				menu.addItems(ContextMenuEntries.fileItems(x.fullPath, s.parent().window()._tryOpenOrSelectDocument))

		fe = sr.fe
		isSelected = self.selectedItem is not None and fe == self.selectedItem.fe


		if isSelected:
			fileNameStyle = f'font-size: {int(round(applicationSettings.appearance.fontSize * 1.3333))}pt; color: #ffffff;'
			pathStyle = f'color: #ffffff'
			font = QFont(self.font())
			font.setWeight(font.weight() + 7)
		else:
			fileNameStyle = f'font-size: {int(round(applicationSettings.appearance.fontSize * 1.3333))}pt;'
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
				if gui.doubleClickLabel(labelMaker1(fe.fileName, sr.match_, fileNameStyle), font=font):
					self.selectedItem = sr
					self.accept()
				if gui.doubleClickLabel(labelMaker2(fe.datapack.name, pathStyle), alignment=Qt.AlignRight, font=font):
					self.selectedItem = sr
					self.accept()
			if gui.doubleClickLabel(labelMaker2(fe.path, pathStyle), font=font):
				self.selectedItem = sr
				self.accept()

	def remainingElementsGUI(self, gui: PythonGUI, count: int, overlap: Overlap, roundedCorners: RoundedCorners):
		with gui.hPanel(overlap=overlap, roundedCorners=roundedCorners):
			fileNameStyle = f'font-size: {int(round(applicationSettings.appearance.fontSize * 1.3333))}pt;'
			if count > 0:
				gui.label(f'<font style="{fileNameStyle}">and {count} more ...</font>')
			else:
				gui.label(f'<font style="{fileNameStyle}"> </font>')

	@CrashReportWrapped
	def openDocument(self, x: FileEntry):
		self.parent().window()._tryOpenOrSelectDocument(x.fullPath)

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