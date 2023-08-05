from __future__ import annotations
import gc
import os
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Callable, ClassVar, Optional, overload

from PyQt5.QtCore import QTimer

from Cat.Serializable.dataclassJson import SerializableDataclass
from Cat.utils import format_full_exc, getExePath, openOrCreate, Singleton
from Cat.utils.logging_ import logError
from Cat.utils.signals import CatBoundSignal, CatSignal
from base.model.documents import Document
from base.model.pathUtils import FilePath
from base.model.project.project import Project
from base.model.documentHandling import DocumentsManager
from base.model.utils import Span


@dataclass
class Session(SerializableDataclass):
	"""docstring for Session"""

	project: Project = field(default_factory=Project)

	@property
	def hasOpenedProject(self) -> bool:
		return bool(self.project.isEmpty)

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
		# resetAllGlobalCaches()
		gc.collect()

	def openProject(self, newWorldPath: str) -> None:
		self.closeProject()
		self.project.path = newWorldPath

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

	@property
	def minecraftData(self):
		# todo: remove the 'minecraftData' property and build actual version system.
		from corePlugins.mcFunctionSchemaTEMP.mcVersions import getCurrentMCVersion
		return getCurrentMCVersion()

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
		__session.project.setup()
		# __session.reset()
		# __session.copyFrom(session)


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
	except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load session: \n{format_full_exc(e)}')
	else:
		setSession(session)


def saveSessionToFile(filePath: str = None) -> None:
	if filePath is None:
		filePath = getSessionFilePath()
	with openOrCreate(filePath, "w") as outFile:
		getSession().dumpJson(outFile)

