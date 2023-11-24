from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Type

from PyQt5.QtCore import QEventLoop, QTimer, pyqtBoundSignal, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QWidget
from timerit import Timer

from base.model.pathUtils import FilePathTpl, ZipFilePool
from base.model.project.project import Root
from base.model.session import getSession
from basePlugins.projectFiles import FilesIndex
from cat.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from cat.GUI.utilities import CrashReportWrapped, connectOnlyOnce
from cat.utils import BusyIndicator
from cat.utils.profiling import TimedMethod
from gui.datapackEditorGUI import DatapackEditorGUI


@dataclass
class AllFileOptions:
	includedRoots: list[Root] = field(default_factory=list)
	fileTypesStr: str = ""
	fileTypes: tuple[str, ...] = field(init=False)

	def __post_init__(self):
		self.fileTypes = tuple(ext.strip().lower() for ext in self.fileTypesStr.split(',') if ext.strip())


class OnProjectFilesDialogBase(CatFramelessWindowMixin, QDialog):

	def __init__(self, GUICls: Type[DatapackEditorGUI] = DatapackEditorGUI, parent: Optional[QWidget] = None):
		super().__init__(GUICls=GUICls, parent=parent)
		self.disableSidebarMargins = True
		self.disableContentMargins = True

		self._allFileOptions: AllFileOptions = AllFileOptions()
		self._allFiles: list[FilePathTpl] = []
		self._processedFilesCount: int = 0

	progressSignal: pyqtBoundSignal = pyqtSignal(int)

	@property
	def allFiles(self) -> list[FilePathTpl]:
		return self._allFiles

	@property
	def allFilesCount(self) -> int:
		return len(self._allFiles)

	@property
	def processedFilesCount(self) -> int:
		return self._processedFilesCount

	def resetUserInterface(self):
		self._allFiles = self.collectAllFiles()
		self._processedFilesCount = 0

	def collectAllFiles(self) -> list[FilePathTpl]:
		fileTypes = self._allFileOptions.fileTypes or ""
		return [
			fe.fullPath
			for p in self._allFileOptions.includedRoots
			if (filesIndex := p.indexBundles.get(FilesIndex)) is not None
			for fe in filesIndex.files.values()
			if fe.fullPath[1].lower().endswith(fileTypes)
		]

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		self._allFileOptions = self.allFilesGUI(gui, self._allFileOptions)

	@classmethod
	def allFilesGUI(cls, gui: DatapackEditorGUI, allFiles: AllFileOptions) -> AllFileOptions:
		with gui.vPanel(preventVStretch=False, seamless=False, windowPanel=True):
			fileTypesStr = gui.codeField(allFiles.fileTypesStr, placeholderText="file extensions...", tip="comma-separated list of file extensions eg.: '.json, .xml'. Leave blank for all files.", isMultiline=False)

		oldIncludedRootIds = {r.name for r in allFiles.includedRoots}
		includedRoots = []
		with gui.scrollBox(preventVStretch=True, verticalSpacing=0):
			includedRoots += cls._rootsListGUI(gui, oldIncludedRootIds, getSession().project.roots)
			gui.vSeparator()
			includedRoots += cls._rootsListGUI(gui, oldIncludedRootIds, getSession().project.deepDependencies)

		return AllFileOptions(fileTypesStr=fileTypesStr, includedRoots=includedRoots)

	@staticmethod
	def _rootsListGUI(gui: DatapackEditorGUI, oldIncludedRootIds: set[str], allRoots: list[Root]) -> list[Root]:
		return [
			root for root in allRoots
			if gui.checkboxLeft((root.name in oldIncludedRootIds), root.name)
		]

	def OnGUI(self, gui: DatapackEditorGUI):
		self.optionsGUI(gui)
		resultsSummaryGUI = gui.subGUI(type(gui), self.resultsSummaryGUI, suppressRedrawLogging=False, seamless=True)
		connectOnlyOnce(self, self.progressSignal, lambda i: resultsSummaryGUI.redrawGUI(), 'resultsGUI')
		resultsSummaryGUI.redrawGUI()
		self.resultsGUI(gui)

	def addProgressBar(self, gui):
		gui.progressBar(self.progressSignal, min=0, max=self.allFilesCount, value=self.processedFilesCount, format='', textVisible=True)

	@abstractmethod
	def optionsGUI(self, gui: DatapackEditorGUI):
		raise NotImplementedError()

	@abstractmethod
	def resultsSummaryGUI(self, gui: DatapackEditorGUI) -> None:
		raise NotImplementedError()

	@abstractmethod
	def resultsGUI(self, gui: DatapackEditorGUI) -> None:
		raise NotImplementedError()

	@abstractmethod
	def prepareRun(self) -> tuple[bool, Any]:
		"""
		returns a tuple consisting of two entries:
			- True if it is OK to run, otherwise return false
			- an arbitrary value, which is passed on to each processFile(...) method.
		"""
		raise NotImplementedError()

	@abstractmethod
	def finishedRun(self, fromPrepareRun: Any) -> None:
		raise NotImplementedError()

	@abstractmethod
	def processFile(self, filePath: FilePathTpl, pool: ZipFilePool, fromPrepareRun: Any):
		raise NotImplementedError()

	def run(self) -> None:
		self.resetUserInterface()
		QTimer.singleShot(1, self._run)

	@property
	def resultSummaryUpdateInterval(self) -> int:
		return 100

	@property
	def resultSummaryUpdateMaxTimeDeltaSeconds(self) -> float:
		return 0.5

	@CrashReportWrapped
	@BusyIndicator
	@TimedMethod()
	def _run(self) -> None:
		isOk, fromPrepareRun = self.prepareRun()
		try:
			if not isOk:
				return
			modulo = self.resultSummaryUpdateInterval
			maxTimeDelta = self.resultSummaryUpdateMaxTimeDeltaSeconds

			with Timer(verbose=False) as timer, ZipFilePool() as pool:
				processedCount: int = 0
				for filePath in self._allFiles:
					processedCount += 1
					self._processedFilesCount = processedCount
					if processedCount % modulo == 0 or timer.elapsed > maxTimeDelta:
						self.progressSignal.emit(processedCount)
						QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 1)
						timer.tic()  # reset timer
					self.processFile(filePath, pool, fromPrepareRun)
		finally:
			self.finishedRun(fromPrepareRun)
			self._gui.redrawGUILater()
