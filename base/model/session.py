from __future__ import annotations
import gc
import os
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Callable, ClassVar, Optional, overload

from PyQt5.QtCore import QTimer

from Cat.Serializable.dataclassJson import SerializableDataclass, catMeta
from Cat.utils import format_full_exc, getExePath, openOrCreate, Singleton
from Cat.utils.logging_ import logError
from Cat.utils.signals import CatBoundSignal, CatSignal
from base.model.documents import Document
from base.model.pathUtils import FilePath, FilePathStr, FilePathTpl, unitePathTpl
from base.model.project.project import Project
from base.model.documentHandling import DocumentsManager
from base.model.utils import Span


@dataclass
class Session(SerializableDataclass):
	"""docstring for Session"""

	project: Project = field(default_factory=Project, metadata=catMeta(serialize=False))
	""" This is a Composition (i.e. Session owns the Project and the Project cannot esxist without a Session)."""
	_projectPath: FilePathStr = field(default="", metadata=catMeta(serializedName='projectPath'))

	@property
	def projectPath(self) -> FilePathStr:
		"""
		is set using: :func:`Session.closeProject()`, :func:`Session.openProject()`
		:return: the path of the currently opened Project, or an empty str if no project is opened.

		"""
		return self._projectPath

	@classmethod
	def getProjectConfigPath(cls, projectPath: FilePathStr) -> FilePathTpl:
		return projectPath, '.dpeproj'

	@property
	def projectConfigPath(self) -> FilePathTpl:
		return self.getProjectConfigPath(self.projectPath)

	@property
	def hasOpenedProject(self) -> bool:
		return len(self.projectPath) > 0

	@property
	def hasProjectConfigFile(self) -> bool:
		return self.hasOpenedProject and os.path.exists(unitePathTpl(self.projectConfigPath))

	documents: DocumentsManager = field(default_factory=DocumentsManager)

	def tryOpenOrSelectDocument(self, filePath: FilePath, selectedSpan: Optional[Span] = None):
		# find Document if is already open:
		if filePath is None:
			cd = getSession().documents.currentDocument
			if cd is None:
				return
			filePath = cd.filePath

		def safeOpenOrShowDocument():
			try:
				self.documents._openOrShowDocument(filePath, selectedSpan)
			except OSError as e:
				getSession().showAndLogError(e)

		QTimer.singleShot(250, safeOpenOrShowDocument)

	def saveDocument(self, document: Document) -> bool:
		try:
			self.documents._saveDocument(document)
			return True
		except OSError as e:
			getSession().showAndLogError(e)
			return False

	def reloadDocument(self, document: Document) -> None:
		try:
			self.documents._reloadDocument(document)
		except OSError as e:
			getSession().showAndLogError(e)


	def closeProject(self) -> None:
		project = self.project
		project.close()
		self._projectPath = ''
		self.project = Project()
		# resetAllGlobalCaches()
		gc.collect()

	def openProject(self, newProjectPath: FilePathStr) -> Project:
		if not os.path.isdir(newProjectPath):
			raise ValueError(f"Not a valid directory: '{newProjectPath}'")

		self.closeProject()
		self._projectPath = newProjectPath
		projConfigPath = unitePathTpl(self.projectConfigPath)

		def _logError(ex, s):
			logError(ex, s)
			raise ex

		try:
			with open(projConfigPath, 'r') as inFile:
				newProject = Project.fromJson(inFile.read(), onError=_logError)
		except (JSONDecodeError, OSError, AttributeError, TypeError, RuntimeError) as e:
			self.showAndLogError(e, "Unable to load project")
			self._projectPath = ''
			newProject = Project()

		self.project = newProject
		self.project.setup()
		return self.project

	def saveProjectToFile(self) -> None:
		if self.hasProjectConfigFile:
			projConfigPath = unitePathTpl(self.projectConfigPath)
			with openOrCreate(projConfigPath, "w") as outFile:
				self.project.dumpJson(outFile)

	@staticmethod
	def showAndLogError(e: Exception, title: str = 'Error') -> None:
		GLOBAL_SIGNALS.onError.emit(e, title)

	@staticmethod
	@overload
	def showAndLogWarning(e: None, title: str) -> None: ...

	@staticmethod
	@overload
	def showAndLogWarning(e: Exception, title: str = 'Warning') -> None: ...

	@staticmethod
	def showAndLogWarning(e: Optional[Exception], title: str = 'Warning') -> None:
		GLOBAL_SIGNALS.onWarning.emit(e, title)


__session = Session()


class _GlobalSignals(Singleton):
	onError: ClassVar[CatBoundSignal[Session, Callable[[Exception, str], None]]] = CatSignal[Callable[[Exception, str], None]]('onError')
	onWarning: ClassVar[CatBoundSignal[Session, Callable[[Exception | None, str], None]]] = CatSignal[Callable[[Exception | None, str], None]]('onWarning')

	def __hash__(self):
		return hash((id(self), type(self)))


GLOBAL_SIGNALS = _GlobalSignals()

GLOBAL_SIGNALS.onError.connect('logError', lambda e, title: logError(f'{title}:', format_full_exc(e)))
GLOBAL_SIGNALS.onWarning.connect('logWarning', lambda e, title: logError(f'{title}') if e is None else logError(f'{title}:', format_full_exc(e)))


def getSession() -> Session:
	return __session


def setSession(session: Session):
	global __session
	assert isinstance(session, Session)
	if session is not __session:
		__session.closeProject()
		__session = session


def getSessionFilePath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'sessions', 'session1.json')


def loadSessionFromFile(filePath: str = None) -> None:
	def _logError(ex, s):
		logError(ex, s)
		raise ex

	if filePath is None:
		filePath = getSessionFilePath()
	try:
		with open(filePath, "r") as inFile:
			session = getSession().fromJson(inFile.read(), onError=_logError)
	except (JSONDecodeError, OSError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load session: \n{format_full_exc(e)}')
	else:
		setSession(session)
		if session.projectPath and os.path.isdir(session.projectPath):
			session.openProject(session.projectPath)
		else:
			session.project.setup()


def saveSessionToFile(filePath: str = None) -> None:
	if filePath is None:
		filePath = getSessionFilePath()
	with openOrCreate(filePath, "w") as outFile:
		getSession().dumpJson(outFile)

	if getSession().projectPath:
		getSession().saveProjectToFile()
