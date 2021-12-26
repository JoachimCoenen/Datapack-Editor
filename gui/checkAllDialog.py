import os
from math import log10
from operator import itemgetter
from typing import Optional, Tuple, Collection

from PyQt5.QtCore import pyqtSignal, QEventLoop, QObject, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QSizePolicy, QWidget

from Cat.CatPythonGUI.GUI import SizePolicy
from Cat.CatPythonGUI.GUI.codeEditor import Error, Position
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.utilities import connect
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, Computed
from Cat.utils import format_full_exc
from Cat.utils.collections_ import OrderedDict, OrderedMultiDict
from Cat.utils.formatters import formatDictItem, formatListLike2, INDENT, SW
from Cat.utils.profiling import TimedMethod, logError
from model.Model import Datapack
from model.commands.parser import parseMCFunction
from model.commands.validator import checkMCFunction
from session.documents import ErrorCounts, getErrorCounts
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries
from model.pathUtils import FilePath, ZipFilePool, ArchiveFilePool, loadTextFile
from session.session import getSession


@RegisterContainer
class WrappedError(SerializableContainer):
	__slots__ = ()
	"""
	just a wrapper for any Exception
	satisfies protocol `Error`
	"""
	def __init__(self, exception: Exception):
		super(WrappedError, self).__init__()
		self.wrappedEx = exception

	wrappedEx: Exception = Serialized(default_factory=lambda: Exception(''))
	message: str = Computed(getInitValue=wrappedEx.map(str, str).get)
	position: Optional[Position] = Computed(default=None)
	end:      Optional[Position] = Computed(default=None)
	style:    str = Computed(default='error')


def checkMcFunctionFile(filePath: FilePath, archiveFilePool: ArchiveFilePool) -> Collection[Error]:
	try:
		sourceCode = loadTextFile(filePath, archiveFilePool)
		tree, errors = parseMCFunction(getSession().minecraftData.commands, sourceCode)
		if tree is not None:
			errors += checkMCFunction(tree)
		return errors
	except Exception as e:
		logError(f"filePath = {filePath!r}")
		logError(format_full_exc())
		return [WrappedError(e)]


class CheckAllDialog(CatFramelessWindowMixin, QDialog):

	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=DatapackEditorGUI, parent=parent)

		self.totalErrorCounts: ErrorCounts = ErrorCounts()
		self.errorsByFile: OrderedDict[FilePath, Collection[Error]] = OrderedDict()

		self._includedDatapacks: list[Datapack] = []
		self._allFiles: list[FilePath] = []
		self._filesCount: int = 100
		self._filesChecked: int = 50

		self._spoilerSizePolicy = QSizePolicy(SizePolicy.Expanding.value, SizePolicy.Fixed.value)

		self.setWindowTitle('Validate Files')

	def OnSidebarGUI(self, gui: DatapackEditorGUI):
		includedDatapacks = []
		with gui.vLayout(preventVStretch=True, verticalSpacing=0):
			for dp in getSession().world.datapacks:
				if gui.checkboxLeft(None, dp.name):
					includedDatapacks.append(dp)
		self._includedDatapacks = includedDatapacks

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		with gui.hLayout():
			gui.progressBar(self.progressSignal, min=0, max=self._filesCount, value=self._filesChecked, format='', textVisible=True)
			if gui.button('check files', default=True):
				self.resetUserInterface()
				QTimer.singleShot(1, self.checkAllFiles)

		self.totalErrorsSummaryGUI(gui)

		with gui.scrollBox():
			errorsByFile: list[Tuple[FilePath, Collection[Error], ErrorCounts]] = \
				[(fp, ers, getErrorCounts([], ers)) for fp, ers in self.errorsByFile.items() if ers]

			errorsByFile = sorted(errorsByFile, key=lambda itm: (itm[2].parserErrors, itm[2].configErrors, ), reverse=True)

			def onContextMenu(x: FilePath, *, s=self):
				with gui.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(x, s.parent()._tryOpenOrSelectDocument))

			for file, errors, errorCounts in errorsByFile:
				label = ''
				if isinstance(file, str):
					label = f"{os.path.basename(file[1])} ('{file}')"
				else:
					label = f"{os.path.basename(file[1])} ('{file[1]}') in '{file[0]}'"
				label = f'errors: {errorCounts.parserErrors + errorCounts.configErrors:2} | warnings: {errorCounts.configWarnings:2} | hints: {errorCounts.configHints:2} | {label}'

				opened = gui.spoiler(
					label=label,
					isOpen=None,
					sizePolicy=self._spoilerSizePolicy,
					onDoubleClicked=lambda _, file=file, s=self: s.parent()._tryOpenOrSelectDocument(file),
					contextMenuPolicy=Qt.CustomContextMenu,
					onCustomContextMenuRequested=lambda pos, file=file: onContextMenu(file),
				)

				with gui.indentation():
					if opened:
						gui.drawErrors(errors, onDoubleClicked=lambda e, file=file, s=self: s.parent()._tryOpenOrSelectDocument(file, e.position))

			gui.addVSpacer(0, SizePolicy.Expanding)

	def totalErrorsSummaryGUI(self, gui: DatapackEditorGUI) -> None:
		def innerTotalErrorsSummaryGUI(gui: DatapackEditorGUI, self=self):
			with gui.hLayout(preventHStretch=True):
				gui.errorsSummaryGUI(self.totalErrorCounts)
				if self._filesChecked > 0:
					errorsPerFile = self.totalErrorCounts.totalErrors / self._filesChecked
				else:
					errorsPerFile = 0
				gui.label(f'{self._filesChecked} files checked. ({errorsPerFile:.1f} errors / file)')

		errorsSummary = gui.subGUI(DatapackEditorGUI, innerTotalErrorsSummaryGUI, suppressRedrawLogging=True)
		errorsSummary.redrawGUI()
		# connect to signal:
		if QObject.receivers(self, self.errorCountsUpdateSignal) > 0:
			self.errorCountsUpdateSignal.disconnect()
		connect(self.errorCountsUpdateSignal, lambda es=errorsSummary: es.redrawGUI())

	progressSignal = pyqtSignal(int)
	errorCountsUpdateSignal = pyqtSignal()

	def resetUserInterface(self):
		self.errorsByFile.clear()
		self.totalErrorCounts = ErrorCounts()

		# allFiles = getSession().world.datapacksProp[:].files[:].get(getSession().world)
		# allFiles = [f for dp in self._includedDatapacks for f in dp.files]
		self._allFiles = []
		for dp in self._includedDatapacks:
			for f in dp.files:
				if isinstance(f, tuple):
					fn = f[1]
				else:
					fn = f
				if fn.endswith('.mcfunction'):
					self._allFiles.append(f)

		self._filesCount = len(self._allFiles)
		self._filesChecked = -1

	@TimedMethod()
	def checkAllFiles(self):
		gui = self._gui

		gui.redrawGUI()
		self.setCursor(Qt.WaitCursor)
		try:
			if self._filesCount > 0:
				digits = int(log10(self._filesCount)) + 1
			else:
				digits = 1
			formatStr = f"({{i:0{digits}}} / {self._filesCount}) file: {{file}}"

			self.totalErrorCounts = ErrorCounts()
			allErrorCounts1 = OrderedMultiDict()
			allErrorCounts2 = {}
			with ZipFilePool() as archiveFilePool:
				for i, filePath in enumerate(self._allFiles):
					self._filesChecked = i+1
					self.progressSignal.emit(i+1)

					errors = checkMcFunctionFile(filePath, archiveFilePool)

					self.totalErrorCounts += getErrorCounts([], errors)
					self.errorsByFile[filePath] = errors

					errorCounter = 0

					if errorCounter > 0:
						allErrorCounts1.add(filePath, errorCounter)
					allErrorCounts2[errorCounter] = allErrorCounts2.get(errorCounter, 0) + 1

					if i % 10 == 0:
						self.errorCountsUpdateSignal.emit()
						QApplication.processEvents(QEventLoop.ExcludeUserInputEvents, 1)

			print("   ========\n" * 5)

			errors1Str = SW()
			errors2Str = SW()
			allErrorCounts1 = sorted(allErrorCounts1.items(), key=itemgetter(1), reverse=True)
			allErrorCounts2 = sorted(allErrorCounts2.items(), key=itemgetter(0), reverse=False)
			formatListLike2(iter(allErrorCounts1), tab=1, localFormatters={}, singleIndent=INDENT, separator=',', newLine='\n', s=errors1Str,
							parenthesies='{}', formatListItem=formatDictItem)
			formatListLike2(iter(allErrorCounts2), tab=1, localFormatters={}, singleIndent=INDENT, separator=',', newLine='\n', s=errors2Str,
							parenthesies='{}', formatListItem=formatDictItem)
			print(f"Errors1 = {errors1Str}")
			print(f"Errors2 = {errors2Str}")
			print(f"Total Errors = {sum(k*v for k, v in allErrorCounts2)}")
		finally:
			self.errorCountsUpdateSignal.emit()
			self.setCursor(Qt.ArrowCursor)
			gui.redrawGUI()