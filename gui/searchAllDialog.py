import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence, Union

from PyQt5.QtCore import QEventLoop, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from Cat.CatPythonGUI.GUI import CORNERS, PythonGUI
from Cat.CatPythonGUI.GUI.Widgets import HTMLDelegate
from Cat.CatPythonGUI.GUI.codeEditor import Position, SearchOptions, SearchMode
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.treeBuilders import DataTreeBuilder
from Cat.CatPythonGUI.utilities import connectOnlyOnce
from Cat.icons import icons
from Cat.utils import escapeForXml
from Cat.utils.collections_ import OrderedMultiDict
from Cat.utils.profiling import TimedMethod
from gui.datapackEditorGUI import ContextMenuEntries, makeTextSearcher
from model.Model import Datapack
from model.pathUtils import FilePath, ZipFilePool, loadTextFile
from session.session import getSession


@dataclass(unsafe_hash=True)
class Occurrence:
	file: FilePath
	position: Position
	line: str


@dataclass
class SearchResult:
	filesToSearch: list[FilePath] = field(default_factory=list)
	occurrences: OrderedMultiDict[FilePath, Occurrence] = field(default_factory=OrderedMultiDict)
	filesSearched: int = 0
	error: Optional[Exception] = None


class SearchAllDialog(CatFramelessWindowMixin, QDialog):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=PythonGUI, parent=parent)

		self._includedDatapacks: list[Datapack] = []
		self.searchExpr: str = ''
		self.searchOptions: SearchOptions = SearchOptions(
			searchMode=SearchMode.Normal,
			isCaseSensitive=False,
			isMultiLine=False,
		)

		self._searchResult: SearchResult = SearchResult()
		self.htmlDelegate = HTMLDelegate()

		self.setWindowTitle('Search')

	progressSignal = pyqtSignal(int)

	def resetUserInterface(self):
		allFilePaths = self.filePathsToSearch
		self._searchResult = SearchResult(allFilePaths)

	def OnSidebarGUI(self, gui: PythonGUI):
		includedDatapacks = []
		with gui.vLayout(preventVStretch=True, verticalSpacing=0):
			for dp in getSession().world.datapacks:
				if gui.checkboxLeft(None, dp.name):
					includedDatapacks.append(dp)
		self._includedDatapacks = includedDatapacks

	def OnGUI(self, gui: PythonGUI):
		with gui.vLayout(preventVStretch=False):
			with gui.vLayout(preventVStretch=False):
				with gui.hLayout(horizontalSpacing=0):
					self.searchExpr = gui.codeField(self.searchExpr, isMultiline=False, roundedCorners=CORNERS.NONE)
					if gui.toolButton(icon=icons.search, overlap=(1, 0), roundedCorners=(False, True, False, True), default=True, windowShortcut=QKeySequence("Return")):
						self.resetUserInterface()
						QTimer.singleShot(1, self.search)
				if self.searchOptions.searchMode == SearchMode.RegEx:
					try:
						re.compile(self.searchExpr)
					except Exception as e:
						gui.helpBox(str(e),  'error', hasLabel=False)

			self._searchOptionsGUI(gui)
			gui.progressBar(self.progressSignal, min=0, max=len(self._searchResult.filesToSearch), value=self._searchResult.filesSearched, format='', textVisible=True)
			resultsGUI = gui.subGUI(PythonGUI, self._resultsGUI1, suppressRedrawLogging=False)
			connectOnlyOnce(self, self.progressSignal, lambda i: resultsGUI.redrawGUI(), 'resultsGUI')
			resultsGUI.redrawGUI()
			self._resultsGUI2(gui)

	def _searchOptionsGUI(self, gui: PythonGUI):
		so = self.searchOptions
		# ============ Search Options: ============
		with gui.hLayout(preventHStretch=True):
			# Search Mode:
			so.searchMode = SearchMode.Normal if gui.radioButton(so.searchMode == SearchMode.Normal, 'Normal', group='searchMode', id=0) else so.searchMode
			so.searchMode = SearchMode.RegEx  if gui.radioButton(so.searchMode == SearchMode.RegEx,  'RegEx',  group='searchMode', id=2) else so.searchMode

			# Search Options:
			so.isCaseSensitive = gui.toggleLeft(so.isCaseSensitive, 'Case sensitive')
			so.isMultiLine = gui.toggleLeft(so.isMultiLine, 'Multiline', enabled=so.searchMode == SearchMode.RegEx)

	def _resultsGUI1(self, gui: PythonGUI) -> None:
		if self._searchResult.error is not None:
			gui.helpBox(f'error during search: {self._searchResult.error}', style='error')
		else:
			gui.label(f'found {len(self._searchResult.occurrences)} occurrences in {len(self._searchResult.occurrences.uniqueKeys())} files ({self._searchResult.filesSearched} files searched total): (double-click to open)')

	def _resultsGUI2(self, gui: PythonGUI) -> None:
		def labelMaker(x:  Union[SearchResult, FilePath, Occurrence], i: int) -> str:
			if isinstance(x, Occurrence):
				return x.line
			else:
				countInFile = len(self._searchResult.occurrences.getall(x))
				if isinstance(x, tuple):
					filename = x[1].rpartition('/')[2]
					return f'{filename} - ({countInFile}) - "{str(x[0])}"'
				elif isinstance(x, str):
					filename = x.rpartition('/')[2]
					return f'{filename} - (countInFile) - "{str(x[0])}"'
			return '<root>'

		def openDocument(x: Union[FilePath, Occurrence], *, s=self):
			if isinstance(x, Occurrence):
				s.parent()._tryOpenOrSelectDocument(x.file, x.position)
			else:
				s.parent()._tryOpenOrSelectDocument(x)

		def onContextMenu(x: Union[SearchResult, FilePath, Occurrence], column: int, *, s=self):
			if isinstance(x, Occurrence):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x.file, s.parent()._tryOpenOrSelectDocument))
			elif not isinstance(x, SearchResult):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x, s.parent()._tryOpenOrSelectDocument))

		def childrenMaker(x: Union[SearchResult, FilePath, Occurrence], *, s=self) -> Sequence:
			if isinstance(x, SearchResult):
				return list(x.occurrences.uniqueKeys())
				# return [(fp, x.occurrences.getall(fp)) for fp in x.occurrences.uniqueKeys()]
			elif isinstance(x, Occurrence):
				return tuple()
			else:
				return self._searchResult.occurrences.getall(x)

		gui.tree(
			DataTreeBuilder(
				self._searchResult,
				childrenMaker,  # lambda x: x.occurrences.items() if isinstance(x, SearchResult) else [],
				labelMaker,
				None, None, 1,
				showRoot=False,
				onDoubleClick=lambda x: openDocument(x),
				onContextMenu=onContextMenu
			),
			headerVisible=True,
			itemDelegate=self.htmlDelegate
		)

	@property
	def filePathsToSearch(self) -> list[FilePath]:
		filePathsToSearch: list[FilePath] = []
		for datapack in self._includedDatapacks:
			filePathsToSearch.extend(datapack.files)
		return filePathsToSearch

	@TimedMethod()
	def search(self) -> None:
		searchResult = self._searchResult

		try:
			try:
				searcher = makeTextSearcher(self.searchExpr, self.searchOptions)
			except Exception as e:
				searchResult.error = e
				return
			with ZipFilePool() as zipFilePool:
				for i, filePath in enumerate(searchResult.filesToSearch):
					self._searchResult.filesSearched = i + 1
					if i % 100 == 0:
						self.progressSignal.emit(i+1)
						QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 1)
					try:
						text = loadTextFile(filePath, zipFilePool)
					except UnicodeDecodeError:
						continue
					lastStart = 0
					lastLineNr = 0
					for matchStart, matchEnd in searcher(text):
						start = text.rfind('\n', 0, matchStart)
						start = start + 1  # skip \n at beginning of line  # if start != -1 else 0
						end = text.find('\n', matchEnd)
						end = end if end != -1 else len(text)
						occurrenceStr = f'<font>{escapeForXml(text[start:matchStart])}<b>{escapeForXml(text[matchStart:matchEnd])}</b>{escapeForXml(text[matchEnd:end])}</font>'

						lastLineNr += text.count('\n', lastStart, start)
						lastStart = start

						searchResult.occurrences.add(filePath, Occurrence(filePath, Position(lastLineNr, matchStart - start), occurrenceStr))
		finally:
			self._gui.redrawGUI()
