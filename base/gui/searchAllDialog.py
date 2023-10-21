import re
from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

from PyQt5.QtCore import QEventLoop, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from cat.GUI import CORNERS, PythonGUI
from cat.GUI.components.Widgets import HTMLDelegate
from cat.GUI.components.codeEditor import SearchOptions, SearchMode
from cat.GUI.components.treeBuilders import DataTreeBuilder
from cat.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from cat.GUI.utilities import connectOnlyOnce
from gui.icons import icons
from cat.utils import escapeForXml
from cat.utils.collections_ import OrderedMultiDict
from cat.utils.profiling import TimedMethod
from base.model.project.project import Root
from base.model.session import getSession
from basePlugins.projectFiles import FilesIndex
from gui.datapackEditorGUI import ContextMenuEntries, makeTextSearcher
from base.model.pathUtils import FilePath, ZipFilePool, loadTextFile
from base.model.utils import Position, Span


@dataclass(unsafe_hash=True)
class Occurrence:
	file: FilePath
	span: Span
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

		self._includedRoots: list[Root] = []
		self.searchExpr: str = ''
		self.searchOptions: SearchOptions = SearchOptions(
			searchMode=SearchMode.Normal,
			isCaseSensitive=False,
			isMultiLine=False,
		)

		self._fileTypesStr: str = ""
		self._fileTypes: tuple[str, ...] = ()
		self._searchResult: SearchResult = SearchResult()
		self.htmlDelegate = HTMLDelegate()

		self.setWindowTitle('Search')

	progressSignal = pyqtSignal(int)

	def resetUserInterface(self):
		allFilePaths = self.filePathsToSearch
		self._searchResult = SearchResult(allFilePaths)

	def OnSidebarGUI(self, gui: PythonGUI):
		with gui.vLayout1C(preventVStretch=False):
			self._fileTypesStr = gui.codeField(self._fileTypesStr, label="File Extensions:", isMultiline=False, placeholderText="All Extensions")
			self._fileTypes = tuple(ext.strip() for ext in self._fileTypesStr.split(',') if ext.strip())

		gui.vSeparator()
		includedRoots = []
		with gui.vLayout(preventVStretch=True, verticalSpacing=0):
			for root in getSession().project.roots:
				if gui.checkboxLeft(None, root.name):
					includedRoots.append(root)
			gui.vSeparator()
			for root in getSession().project.deepDependencies:
				if gui.checkboxLeft(None, root.name):
					includedRoots.append(root)
		self._includedRoots = includedRoots

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
				getSession().tryOpenOrSelectDocument(x.file, x.span)
			else:
				getSession().tryOpenOrSelectDocument(x)

		def onContextMenu(x: Union[SearchResult, FilePath, Occurrence], column: int, *, s=self):
			if isinstance(x, Occurrence):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x.file, getSession().tryOpenOrSelectDocument))
			elif not isinstance(x, SearchResult):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x, getSession().tryOpenOrSelectDocument))

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
		fileTypes = self._fileTypes
		filePathsToSearch: list[FilePath] = []
		for p in self._includedRoots:
			if (filesIndex := p.indexBundles.get(FilesIndex)) is not None:
				for fe in filesIndex.files.values():
					f = fe.fullPath
					if isinstance(f, tuple):
						fn = f[1]
					else:
						fn = f
					if not fileTypes or fn.endswith(fileTypes):
						filePathsToSearch.append(f)

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
					lastLineStart = 0
					lastLineNr = 0
					for matchStart, matchEnd in searcher(text):
						lineStart = text.rfind('\n', 0, matchStart)
						lineStart = lineStart + 1  # skip \n at beginning of line  # if start != -1 else 0
						end = text.find('\n', matchEnd)
						end = end if end != -1 else len(text)
						occurrenceStr = f'<font>{escapeForXml(text[lineStart:matchStart])}<b>{escapeForXml(text[matchStart:matchEnd])}</b>{escapeForXml(text[matchEnd:end])}</font>'

						lastLineNr += text.count('\n', lastLineStart, lineStart)
						lastLineStart = lineStart

						p1 = Position(lastLineNr, matchStart - lineStart, matchStart)
						p2 = Position(lastLineNr, matchEnd - lineStart, matchEnd)

						searchResult.occurrences.add(filePath, Occurrence(filePath, Span(p1, p2), occurrenceStr))
		finally:
			self._gui.redrawGUI()
