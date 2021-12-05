import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Sequence, Union

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QWidget

from Cat.CatPythonGUI.GUI import CORNERS, PythonGUI
from Cat.CatPythonGUI.GUI.Widgets import HTMLDelegate
from Cat.CatPythonGUI.GUI.codeEditor import Position, SearchOptions, SearchMode
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.treeBuilders import DataTreeBuilder
from Cat.icons import icons
from Cat.utils import escapeForXml
from Cat.utils.collections_ import OrderedMultiDict
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
	occurrences: OrderedMultiDict[FilePath, Occurrence] = field(default_factory=OrderedMultiDict)
	filesSearched: int = 0
	error: Optional[Exception] = None


@dataclass
class FilterByFilterOptions:
	filterStrFolder: str = "src/main/webapp/**"
	filterStrZip: str = "**"
	extensionRegEx: str = ".xml"


class FilterBy(Enum):
	Role = 1
	Filter = 2


class SearchAllDialog(CatFramelessWindowMixin, QDialog):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=PythonGUI, parent=parent)

		self.selectedDatapacks: list[Datapack] = []
		self.searchOptions: SearchOptions = SearchOptions(
			searchMode=SearchMode.Normal,
			isCaseSensitive=False,
			isMultiLine=False,
		)

		self._searchResult: SearchResult = SearchResult()
		self.htmlDelegate = HTMLDelegate()
		self.OnSidebarGUI = None

		self.setWindowTitle('Search')

	# def OnSidebarGUI(self, gui: PythonGUI):
	# 	self.selectedProjs = self.datapacksSelectionGUI(gui)

	def OnGUI(self, gui: PythonGUI):
		self.selectedProjs = self.datapacksSelectionGUI(gui)
		self.mainGUI(gui, self.selectedProjs)

	def datapacksSelectionGUI(self, gui: PythonGUI) -> list[Datapack]:
		datapacks = getSession().world.datapacks
		# skip this gui for now:
		return datapacks
		searchAllProjs = gui.toggleLeft(None, label='search in all datapacks')

		with gui.vLayout(verticalSpacing=0):
			filterStr, allFilteredProjects = gui.advancedFilterTextField(
				None,
				allProjsList,
				getStrChoices=lambda x: (pr.name for pr in x),
				filterFunc=filterComputedChoices(Datapack.name.get),
				valuesName='data packs',
				enabled=not searchAllProjs,
			)

			def onContextMenu(x: Project, column: int, *, s=self):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.datapackItems(x, s.parent()._tryOpenOrSelectDocument))

			selectedProj = gui.tree(DataListBuilder(
				allFilteredProjects,
				lambda p, i: p.name,
				None,
				lambda p, i: str(p.path),
				1,
				onContextMenu=onContextMenu
			), enabled=not searchAllProjs).selectedItem

			if searchAllProjs:
				return allProjsList
			else:
				if selectedProj is not None:
					return [selectedProj]
				else:
					return []

	def mainGUI(self, gui: PythonGUI, selectedProjs: list[Datapack]):
		with gui.vLayout(preventVStretch=False):
			with gui.vLayout(preventVStretch=False):
				with gui.hLayout(horizontalSpacing=0):
					searchExpr = gui.codeField(None, isMultiline=False, roundedCorners=CORNERS.NONE)
					searchPressed = gui.toolButton(icon=icons.search, overlap=(1, 0), roundedCorners=(False, True, False, True), default=True, windowShortcut=QKeySequence("Return"))
				if self.searchOptions.searchMode == SearchMode.RegEx:
					try:
						re.compile(searchExpr)
					except Exception as e:
						gui.helpBox(str(e),  'error', hasLabel=False)

			# ============ Search Options: ============
			self._searchOptionsGUI(gui)
			# ============ Search Results: ============
			if searchPressed:
				searchFiles = self.getFilePathsToSearch(selectedProjs)
				if searchFiles is not None:
					self._searchResult = self.search(searchExpr, self.searchOptions, searchFiles)
					self._searchResult.filesSearched = len(searchFiles)

			gui.vSeparator()
			self._resultsGUI(gui)

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

	def _resultsGUI(self, gui: PythonGUI) -> None:
		if self._searchResult.error is not None:
			gui.helpBox(f'error during search: {self._searchResult.error}', style='error')
		else:
			gui.label(f'found {len(self._searchResult.occurrences)} occurrences in {len(self._searchResult.occurrences.uniqueKeys())} files ({self._searchResult.filesSearched} files searched total): (double-click to open)')

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
			# if isinstance(x[0], tuple):
			# 	filename = x[0][1].rpartition('/')[2]
			# else:
			# 	filename = x[0].rpartition('/')[2]
			# return (
			# 	x[1][0],
			# 	filename,
			# 	str(x[0]),
			# )[i]

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

	def getFilePathsToSearch(
			self,
			allDatapacks: list[Datapack],
	) -> Optional[list[FilePath]]:

		filePathsToSearch: list[FilePath] = []
		for datapack in allDatapacks:
			filePathsToSearch.extend(datapack.files)

		return filePathsToSearch

	def search(self, expr: str, searchOptions: SearchOptions, allFilePaths: Iterable[FilePath]) -> SearchResult:
		result: SearchResult = SearchResult()

		try:
			searcher = makeTextSearcher(expr, searchOptions)
		except Exception as e:
			result.error = e
			return result

		with ZipFilePool() as zipFilePool:
			for filePath in allFilePaths:
				try:
					text = loadTextFile(filePath, zipFilePool)
				except UnicodeDecodeError:
					continue
				lastStart = 0
				lastLineNr = 0
				for matchStart, matchEnd in searcher(text):
					start = text.rfind('\n', 0, matchStart)
					start = start + 1  # skip \n at beginnig of line  # if start != -1 else 0
					end = text.find('\n', matchEnd)
					end = end if end != -1 else len(text)
					occurrenceStr = f'<font>{escapeForXml(text[start:matchStart])}<b>{escapeForXml(text[matchStart:matchEnd])}</b>{escapeForXml(text[matchEnd:end])}</font>'

					lastLineNr += text.count('\n', lastStart, start)
					lastStart = start

					result.occurrences.add(filePath, Occurrence(filePath, Position(lastLineNr, matchStart - start), occurrenceStr))
		return result

