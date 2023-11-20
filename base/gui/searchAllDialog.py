import re
from dataclasses import dataclass, field
from typing import Callable, Iterator, Optional, Sequence

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget
from recordclass import as_dataclass

from base.gui.onProjectFilesDialogBase import OnProjectFilesDialogBase
from base.model.pathUtils import FilePathTpl, ZipFilePool, dirFromFilePath, fileNameFromFilePath, loadTextFile
from base.model.session import getSession
from base.model.utils import Position, Span
from cat.GUI import CORNERS
from cat.GUI.components.codeEditor import IndexSpan, SearchMode, SearchOptions
from cat.GUI.components.treeBuilders import DataTreeBuilder
from cat.utils import escapeForXml, override
from cat.utils.collections_ import OrderedMultiDict
from gui.datapackEditorGUI import ContextMenuEntries, DatapackEditorGUI, makeTextSearcher
from gui.icons import icons


@as_dataclass(hashable=True)
class Occurrence:
	file: FilePathTpl
	span: Span
	line: str


@dataclass
class SearchResult:
	occurrences: OrderedMultiDict[FilePathTpl, Occurrence] = field(default_factory=OrderedMultiDict)
	error: Optional[Exception] = None


class SearchAllDialog(OnProjectFilesDialogBase):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=DatapackEditorGUI, parent=parent)

		self.searchExpr: str = ''
		self.searchOptions: SearchOptions = SearchOptions(
			searchMode=SearchMode.Normal,
			isCaseSensitive=False,
			isMultiLine=False,
		)
		self._searchResult: SearchResult = SearchResult()

		self.setWindowTitle('Search')

	@override
	def resetUserInterface(self):
		super().resetUserInterface()
		self._searchResult = SearchResult()

	@override
	def optionsGUI(self, gui: DatapackEditorGUI):
		with gui.vLayout(preventVStretch=False):
			with gui.hLayout(horizontalSpacing=0):
				self.searchExpr = gui.codeField(self.searchExpr, isMultiline=False, roundedCorners=CORNERS.NONE)
				if gui.toolButton(icon=icons.search, overlap=(1, 0), roundedCorners=(False, True, False, True), default=True, windowShortcut=QKeySequence("Return")):
					self.run()
			if self.searchOptions.searchMode == SearchMode.RegEx:
				try:
					re.compile(self.searchExpr)
				except Exception as e:
					gui.helpBox(str(e), 'error', hasLabel=False)

		self._searchOptionsGUI(gui)
		self.addProgressBar(gui)

	def _searchOptionsGUI(self, gui: DatapackEditorGUI):
		so = self.searchOptions
		# ============ Search Options: ============
		with gui.hLayout(preventHStretch=True):
			# Search Mode:
			so.searchMode = SearchMode.Normal if gui.radioButton(so.searchMode == SearchMode.Normal, 'Normal', group='searchMode', id=0) else so.searchMode
			so.searchMode = SearchMode.RegEx  if gui.radioButton(so.searchMode == SearchMode.RegEx,  'RegEx',  group='searchMode', id=2) else so.searchMode

			# Search Options:
			so.isCaseSensitive = gui.toggleLeft(so.isCaseSensitive, 'Case sensitive')
			so.isMultiLine = gui.toggleLeft(so.isMultiLine, 'Multiline', enabled=so.searchMode == SearchMode.RegEx)

	@override
	def resultsSummaryGUI(self, gui: DatapackEditorGUI) -> None:
		if self._searchResult.error is not None:
			gui.helpBox(f'error during search: {self._searchResult.error}', style='error')
		else:
			gui.label(f'found {len(self._searchResult.occurrences)} occurrences in {len(self._searchResult.occurrences.uniqueKeys())} files ({self.processedFilesCount} files searched total): (double-click to open)')

	@override
	def resultsGUI(self, gui: DatapackEditorGUI) -> None:
		def labelMaker(x: SearchResult | FilePathTpl | Occurrence, column: int) -> str:
			if isinstance(x, Occurrence):
				return x.line if column == 0 else str(x.span.start)
			elif isinstance(x, SearchResult):
				return '<root>'
			else:
				if column == 0:
					fileName = fileNameFromFilePath(x[1])
					projectName = fileNameFromFilePath(x[0])
					pathInProj = dirFromFilePath(x[1]).removeprefix('/')
					countInFile = len(self._searchResult.occurrences.getall(x))
					return f'{fileName} - ({countInFile}) - "{projectName}/{pathInProj}"'
				else:
					return ''

		def openDocument(x: SearchResult | FilePathTpl | Occurrence) -> None:
			if isinstance(x, Occurrence):
				getSession().tryOpenOrSelectDocument(x.file, x.span)
			else:
				getSession().tryOpenOrSelectDocument(x)

		def onContextMenu(x: SearchResult | FilePathTpl | Occurrence, column: int) -> None:
			if isinstance(x, Occurrence):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x.file, getSession().tryOpenOrSelectDocument))
			elif not isinstance(x, SearchResult):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x, getSession().tryOpenOrSelectDocument))

		def childrenMaker(x: SearchResult | FilePathTpl | Occurrence) -> Sequence[FilePathTpl | Occurrence]:
			if isinstance(x, Occurrence):
				return tuple()
			elif isinstance(x, SearchResult):
				return list(x.occurrences.uniqueKeys())
			else:
				return self._searchResult.occurrences.getall(x)

		gui.tree(
			DataTreeBuilder(
				self._searchResult,
				childrenMaker,
				labelMaker,
				None,
				None,
				2,
				showRoot=False,
				onDoubleClick=openDocument,
				onContextMenu=onContextMenu
			),
			# headerVisible=True,
			itemDelegate=gui.htmlDelegate
		)

	@override
	def prepareRun(self) -> tuple[bool, Callable[[str], Iterator[IndexSpan]]]:
		"""
		returns a tuple consisting of two entries:
			- True if it is OK to run, otherwise return false
			- an arbitrary value, which is passed on to each processFile(...) method.
		"""
		try:
			return True, makeTextSearcher(self.searchExpr, self.searchOptions)
		except Exception as e:
			self._searchResult.error = e
			return False, lambda x: iter(())

	@override
	def finishedRun(self, searcher: Callable[[str], Iterator[IndexSpan]]) -> None:
		pass

	@override
	def processFile(self, filePath: FilePathTpl, pool: ZipFilePool, searcher: Callable[[str], Iterator[IndexSpan]]):
		try:
			text = loadTextFile(filePath, pool)
		except UnicodeDecodeError:
			return

		lastLineStart = 0
		lastLineNr = 0
		for matchStart, matchEnd in searcher(text):
			lineStart = text.rfind('\n', 0, matchStart)
			lineStart = lineStart + 1  # skip \n at beginning of line  # if start != -1 else 0
			lineEnd = text.find('\n', matchEnd)
			lineEnd = lineEnd if lineEnd != -1 else len(text)
			# trim overly long lines:
			MAX_LINE_LEN = 120
			if lineEnd - lineStart > MAX_LINE_LEN:
				machLen = matchEnd - matchStart
				left = (MAX_LINE_LEN - machLen) // 2  # try to put the match in the middle.
				left = max(15, left)  # but leave at least 15 characters before the match.
				windowStart = max(lineStart, matchStart - left)  # don't go beyond lineStart.
				windowEnd = min(lineEnd, matchStart + MAX_LINE_LEN)  # don't go beyond lineEnd.
				textLeft = text[windowStart:matchStart]
				textRight = text[matchEnd:windowEnd]
				if windowStart > lineStart:
					textLeft = '...' + textLeft
				if windowEnd < lineEnd:
					textRight = textRight + '...'
			else:
				textLeft = text[lineStart:matchStart]
				textRight = text[matchEnd:lineEnd]

			occurrenceStr = f'<font>{escapeForXml(textLeft)}<b>{escapeForXml(text[matchStart:matchEnd])}</b>{escapeForXml(textRight)}</font>'

			lastLineNr += text.count('\n', lastLineStart, lineStart)
			lastLineStart = lineStart

			p1 = Position(lastLineNr, matchStart - lineStart, matchStart)
			p2 = Position(lastLineNr, matchEnd - lineStart, matchEnd)

			self._searchResult.occurrences.add(filePath, Occurrence(filePath, Span(p1, p2), occurrenceStr))
