from __future__ import annotations
import os
from collections import defaultdict
from dataclasses import dataclass
from operator import itemgetter
from typing import Optional, Collection

from PyQt5.QtCore import pyqtSignal, QEventLoop, QObject, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QSizePolicy, QWidget

from cat.GUI import SizePolicy
from cat.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from cat.GUI.utilities import connect
from gui.icons import icons
from cat.utils import format_full_exc, BusyIndicator
from cat.utils.formatters import SW, formatDictOnly
from cat.utils.profiling import TimedMethod, logError
from base.model.project.project import Root
from base.model.session import getSession
from basePlugins.projectFiles import FilesIndex
from base.model.utils import WrappedError, GeneralError
from base.model.documents import ErrorCounts, getErrorCounts, loadDocument
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries
from base.model.pathUtils import FilePath, ZipFilePool, ArchiveFilePool, FilePathTpl


def checkFile(filePath: FilePath, archiveFilePool: ArchiveFilePool) -> Collection[GeneralError]:
	try:
		document = loadDocument(filePath, archiveFilePool, observeFileSystem=False)
		document.asyncValidate.callNow()
		errors = document.errors
		return errors
	except Exception as e:
		logError(f"filePath = {filePath!r}")
		logError(format_full_exc())
		return [WrappedError(e)]


class CheckAllDialog(CatFramelessWindowMixin, QDialog):

	progressSignal = pyqtSignal(int)
	errorCountsUpdateSignal = pyqtSignal()

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=DatapackEditorGUI, parent=parent)

		self.totalErrorCounts: ErrorCounts = ErrorCounts()
		self.errorsByFile: dict[FilePath, Collection[GeneralError]] = {}

		self._includedRoots: list[Root] = []
		# self._fileTypes: dict[str, EntryHandlerInfo] = {}
		self._allFiles: list[FilePath] = []
		self._filesCount: int = 0
		self._filesChecked: int = -1

		self._spoilerSizePolicy = QSizePolicy(SizePolicy.Expanding.value, SizePolicy.Fixed.value)

		self.setWindowTitle('Validate Files')

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
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

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.hLayout():
			gui.progressBar(self.progressSignal, min=0, max=self._filesCount, value=self._filesChecked, format='', textVisible=True)
			if gui.button('Check Files', default=True):
				self.resetUserInterface()
				QTimer.singleShot(1, self.checkAllFiles)
			if self._filesChecked > -1:
				if gui.button(icon=icons.signal, tip='Show Stats', default=False):
					stats = getErrorStats(self.errorsByFile)
					errorStatsStr = errorStatsToStr(stats)
					gui.askUserInput(
						"Check all Files Results",
						errorStatsStr,
						lambda g, v: g.codeField(errorStatsStr)
					)

		self.totalErrorsSummaryGUI(gui)

		with gui.scrollBox():
			errorsByFile: list[tuple[FilePath, Collection[GeneralError], ErrorCounts]] = \
				[(fp, ers, getErrorCounts(ers)) for fp, ers in self.errorsByFile.items() if ers]

			errorsByFile = sorted(errorsByFile, key=lambda itm: (itm[2].errors,), reverse=True)

			def onContextMenu(x: FilePath, *, s=self):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x, getSession().tryOpenOrSelectDocument))

			for file, errors, errorCounts in errorsByFile:
				label = ''
				if isinstance(file, str):
					label = f"{os.path.basename(file)} ('{file}')"
				else:
					label = f"{os.path.basename(file[1])} ('{file[1]}') in '{file[0]}'"
				label = f'errors: {errorCounts.errors:2} | warnings: {errorCounts.warnings:2} | hints: {errorCounts.hints:2} | {label}'

				opened = gui.spoiler(
					label=label,
					isOpen=None,
					sizePolicy=self._spoilerSizePolicy,
					onDoubleClicked=lambda _, file=file, s=self: getSession().tryOpenOrSelectDocument(file),
					contextMenuPolicy=Qt.CustomContextMenu,
					onCustomContextMenuRequested=lambda pos, file=file: onContextMenu(file),
				)

				with gui.indentation():
					if opened:
						gui.errorsList(errors, onDoubleClicked=lambda e, file=file, s=self: getSession().tryOpenOrSelectDocument(file, e.span))

			gui.addVSpacer(0, SizePolicy.Expanding)

	def totalErrorsSummaryGUI(self, gui: DatapackEditorGUI) -> None:
		def innerTotalErrorsSummaryGUI(gui: DatapackEditorGUI, self=self):
			with gui.hLayout(preventHStretch=True):
				gui.errorsSummaryGUI(self.totalErrorCounts)
				if self._filesChecked > 0:
					errorsPerFile = self.totalErrorCounts.errors / self._filesChecked
				else:
					errorsPerFile = 0
				gui.label(f'{self._filesChecked} / {self._filesCount} files checked. ({errorsPerFile:.1f} errors / file)')

		errorsSummary = gui.subGUI(DatapackEditorGUI, innerTotalErrorsSummaryGUI, suppressRedrawLogging=True)
		errorsSummary.redrawGUI()
		# connect to signal:
		if QObject.receivers(self, self.errorCountsUpdateSignal) > 0:
			self.errorCountsUpdateSignal.disconnect()
		connect(self.errorCountsUpdateSignal, lambda es=errorsSummary: es.redrawGUI())

	def resetUserInterface(self):
		self.errorsByFile.clear()
		self.totalErrorCounts = ErrorCounts()
		self._allFiles = self.collectAllFiles()
		self._filesCount = len(self._allFiles)
		self._filesChecked = -1

	def collectAllFiles(self):
		filePathsToSearch: list[FilePath] = []
		for p in self._includedRoots:
			if (filesIndex := p.indexBundles.get(FilesIndex)) is not None:
				for fe in filesIndex.files.values():
					filePathsToSearch.append(fe.fullPath)

		return filePathsToSearch

	@BusyIndicator
	@TimedMethod()
	def checkAllFiles(self) -> None:
		gui = self._gui

		gui.redrawGUI()
		try:
			self.totalErrorCounts = ErrorCounts()
			with ZipFilePool() as archiveFilePool:
				for i, filePath in enumerate(self._allFiles):
					self._filesChecked = i + 1
					errors = checkFile(filePath, archiveFilePool)

					self.totalErrorCounts += getErrorCounts(errors)
					self.errorsByFile[filePath] = errors

					if i % 25 == 0:
						self.progressSignal.emit(i + 1)
						self.errorCountsUpdateSignal.emit()
						QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 1)
		finally:
			self.errorCountsUpdateSignal.emit()
			gui.redrawGUILater()


@dataclass
class TotalErrorStats:
	errorCountsByPath: dict[FilePathTpl, int]
	errorCountHistogram: dict[int, int]
	total: int = 0

	def add(self, filePath: FilePathTpl, errorsCount: int) -> None:
		self.errorCountsByPath[filePath] = errorsCount
		self.errorCountHistogram[errorsCount] += 1
		self.total += errorsCount

	def finish(self) -> TotalErrorStats:
		self.errorCountsByPath = dict(sorted(filter(lambda x: x[1] > 0, self.errorCountsByPath.items()), key=itemgetter(1), reverse=True))
		self.errorCountHistogram = dict(sorted(self.errorCountHistogram.items(), key=itemgetter(0), reverse=False))
		return self


def getErrorStats(errorsByPath: dict[FilePathTpl, Collection[GeneralError]]) -> TotalErrorStats:
	totalErrorCounts = ErrorCounts()
	errorStats = TotalErrorStats({}, defaultdict(int))

	for filePath, errors in errorsByPath.items():
		errorCounts = getErrorCounts(errors)
		totalErrorCounts += errorCounts
		errorStats.add(filePath, errorCounts.errors)

	return errorStats.finish()


def errorStatsToStr(errorStats: TotalErrorStats) -> str:
	errors1Str = SW()
	errors2Str = SW()
	formatDictOnly(errorStats.errorCountsByPath, tab=1, s=errors1Str)
	formatDictOnly(errorStats.errorCountHistogram, tab=1, s=errors2Str)
	result = (
		f"Errors By Path = {errors1Str}\n"
		f"Errors Histogram = {errors2Str}\n"
		f"Errors Total = {errorStats.total}\n"
	)
	return result
