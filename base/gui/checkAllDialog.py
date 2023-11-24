from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from operator import itemgetter
from typing import Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSizePolicy, QWidget
from recordclass import as_dataclass

from base.gui.onProjectFilesDialogBase import OnProjectFilesDialogBase
from base.model.documents import ErrorCounts, getErrorCounts, loadDocument
from base.model.pathUtils import ArchiveFilePool, FilePathTpl, ZipFilePool, fileNameFromFilePath, toDisplayPath
from base.model.session import getSession
from base.model.utils import GeneralError, Span, WrappedError
from cat.GUI import SizePolicy
from cat.GUI.components.treeBuilders import DataTreeBuilder
from cat.utils import format_full_exc, override
from cat.utils.formatters import SW, formatDictOnly
from cat.utils.profiling import logError
from gui.datapackEditorGUI import ContextMenuEntries, DatapackEditorGUI
from gui.icons import icons


@as_dataclass()
class ErrorsResult:
	file: FilePathTpl
	errors: Sequence[GeneralError]
	counts: ErrorCounts

	def __ne__(self, other):
		if type(other) is not type(self):
			return NotImplemented
		return self.file != other.file

	def __eq__(self, other):
		if type(other) is not type(self):
			return NotImplemented
		return self.file == other.file

	def __hash__(self):
		return hash(self.file)


@as_dataclass(hashable=True)
class Error:
	file: FilePathTpl
	error: GeneralError


@dataclass()
class ResultRoot:
	results: list[ErrorsResult]
	errorCountHistogram: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
	totalCounts: ErrorCounts = field(default_factory=ErrorCounts)

	def add(self, result: ErrorsResult) -> None:
		self.results.append(result)
		self.errorCountHistogram[result.counts.errors] += 1
		self.totalCounts += result.counts

	def sort(self) -> None:
		self.results.sort(key=lambda ers: ers.counts.errors, reverse=True)
		self.errorCountHistogram = defaultdict(int, sorted(self.errorCountHistogram.items(), key=itemgetter(0), reverse=False))

	def clear(self):
		self.results.clear()
		self.errorCountHistogram.clear()
		self.totalCounts = ErrorCounts()

	def __hash__(self):
		return id(self)


def errorStatsToStr(errorStats: ResultRoot) -> str:
	errors1Str = SW()
	errors2Str = SW()
	formatDictOnly({er.file: er.counts.errors for er in errorStats.results if er.counts.errors > 0}, tab=1, s=errors1Str)
	formatDictOnly(errorStats.errorCountHistogram, tab=1, s=errors2Str)
	result = (
		f"Errors By Path = {errors1Str}\n"
		f"Errors Histogram = {errors2Str}\n"
		f"Errors Total = {errorStats.totalCounts}\n"
	)
	return result


def checkFile(filePath: FilePathTpl, archiveFilePool: ArchiveFilePool) -> Sequence[GeneralError]:
	try:
		document = loadDocument(filePath, archiveFilePool, observeFileSystem=False)
		if getattr(document, 'schema', 123) is None:
			# we have no schema, so we can only perform a syntax check.
			if document.tree is None:
				document.asyncParse.callNow()
		else:
			document.asyncValidate .callNow()
		errors = document.errors
		return errors
	except Exception as e:
		logError(f"filePath = {filePath!r}")
		logError(format_full_exc())
		return [WrappedError(e)]


class CheckAllDialog(OnProjectFilesDialogBase):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=DatapackEditorGUI, parent=parent)
		self.result: ResultRoot = ResultRoot([])

		self._spoilerSizePolicy = QSizePolicy(SizePolicy.Expanding.value, SizePolicy.Fixed.value)

		self.setWindowTitle('Validate Files')

	@override
	def optionsGUI(self, gui: DatapackEditorGUI):
		pass  # moved to resultsSummaryGUI

	@override
	def resultsSummaryGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.vPanel(windowPanel=True):
			with gui.hLayout():
				self.addProgressBar(gui)
				if gui.button('Check Files', default=True):
					self.run()
				if self.processedFilesCount > -1:
					if gui.button(icon=icons.signal, tip='Show Stats', default=False):
						errorStatsStr = errorStatsToStr(self.result)
						gui.askUserInput(
							"Check all Files Results",
							errorStatsStr,
							lambda g, v: g.codeField(errorStatsStr)
						)
			with gui.hLayout(preventHStretch=True):
				gui.errorsSummaryGUI(self.result.totalCounts)
				if self.processedFilesCount > 0:
					errorsPerFile = self.result.totalCounts.errors / self.processedFilesCount
				else:
					errorsPerFile = 0
				gui.label(f'{self.processedFilesCount} / {self.allFilesCount} files checked. ({errorsPerFile:.1f} errors / file)')

	@override
	def resetUserInterface(self):
		super().resetUserInterface()
		self.result.clear()

	@override
	def resultsGUI(self, gui: DatapackEditorGUI) -> None:
		self.resultsGUI2(gui)

	def resultsGUI1(self, gui: DatapackEditorGUI) -> None:

		def onContextMenu(x: FilePathTpl):
			with gui.popupMenu(atMousePosition=True) as menu:
				menu.addItems(ContextMenuEntries.fileItems(x, getSession().tryOpenOrSelectDocument))

		with gui.scrollBox():
			for errors in self.result.results:
				file = errors.file
				counts = errors.counts
				label = f"{fileNameFromFilePath(file)} ('{file[1]}') in '{file[0]}'"
				label = f'errors: {counts.errors:2} | warnings: {counts.warnings:2} | hints: {counts.hints:2} | {label}'

				opened = gui.spoiler(
					label=label,
					isOpen=None,
					sizePolicy=self._spoilerSizePolicy,
					onDoubleClicked=lambda _, f=file: getSession().tryOpenOrSelectDocument(f),
					contextMenuPolicy=Qt.CustomContextMenu,
					onCustomContextMenuRequested=lambda pos, f=file: onContextMenu(f),
				)

				with gui.indentation():
					if opened:
						gui.errorsList(errors.errors, onDoubleClicked=lambda e, f=file: getSession().tryOpenOrSelectDocument(f, Span(e.start)))

			gui.addVSpacer(0, SizePolicy.Expanding)

	def resultsGUI2(self, gui: DatapackEditorGUI) -> None:

		def labelMaker(x: ResultRoot | ErrorsResult | Error, i: int) -> str:
			if isinstance(x, Error):
				return gui.getErrorLabelForList(x.error, i)
			elif isinstance(x, ErrorsResult):
				if i == 0:
					return fileNameFromFilePath(x.file[1])
				elif i == 1:
					counts = x.counts
					return f'errors: {counts.errors:2} | warnings: {counts.warnings:2} | hints: {counts.hints:2}'
				elif i == 2:
					return fileNameFromFilePath(x.file[0])
			return "<root>"

		def iconMaker(x: ResultRoot | ErrorsResult | Error, i: int) -> Optional[QIcon]:
			if isinstance(x, Error):
				return gui.getErrorIconForList(x.error, i)
			return None

		def toolTipMaker(x: ResultRoot | ErrorsResult | Error, i: int) -> Optional[str]:
			if isinstance(x, Error):
				return gui.getErrorToolTipForList(x.error, i)
			elif isinstance(x, ErrorsResult):
				return toDisplayPath(x.file)
			return ""

		def openDocument(x: ResultRoot | ErrorsResult | Error) -> None:
			if isinstance(x, Error):
				getSession().tryOpenOrSelectDocument(x.file, Span(x.error.start))
			elif isinstance(x, ErrorsResult):
				getSession().tryOpenOrSelectDocument(x.file)

		def onContextMenu(x: ResultRoot | ErrorsResult | Error, column: int) -> None:
			if isinstance(x, Error):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x.file, lambda fp: getSession().tryOpenOrSelectDocument(fp, Span(x.error.start))))
			elif isinstance(x, ErrorsResult):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x.file, getSession().tryOpenOrSelectDocument))

		def onCopy(x: ResultRoot | ErrorsResult | Error) -> Optional[str]:
			if isinstance(x, Error):
				return x.error.message
			elif isinstance(x, ErrorsResult):
				return toDisplayPath(x.file)

		def childrenMaker(x: ResultRoot | ErrorsResult | Error) -> Sequence[ErrorsResult | Error]:
			if isinstance(x, Error):
				return ()
			elif isinstance(x, ErrorsResult):
				return [Error(x.file, e) for e in x.errors]
				# return [(fp, x.occurrences.getall(fp)) for fp in x.occurrences.uniqueKeys()]
			else:
				return [er for er in x.results if er.errors]

		gui.tree(
			DataTreeBuilder(
				self.result,
				childrenMaker,  # lambda x: x.occurrences.items() if isinstance(x, SearchResult) else [],
				labelMaker,
				iconMaker,
				toolTipMaker,
				3,
				showRoot=False,
				onDoubleClick=openDocument,
				onContextMenu=onContextMenu,
				onCopy=onCopy
			),
			itemDelegate=gui.htmlDelegate
		)

	@override
	def prepareRun(self) -> tuple[bool, None]:
		"""
		returns a tuple consisting of two entries:
			- True if it is OK to run, otherwise return false
			- an arbitrary value, which is passed on to each processFile(...) method.
		"""
		return True, None

	@override
	def finishedRun(self, fromPrepareRun: None) -> None:
		self.result.sort()

	@override
	def processFile(self, filePath: FilePathTpl, pool: ZipFilePool, fromPrepareRun: None):
		errors = checkFile(filePath, pool)
		counts = getErrorCounts(errors)
		self.result.add(ErrorsResult(filePath, errors, counts))
