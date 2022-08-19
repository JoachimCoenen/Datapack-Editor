from __future__ import annotations

import gc
import os
import traceback
from json import JSONDecodeError
from typing import NewType, Callable

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, Computed
from Cat.utils import getExePath, openOrCreate, format_full_exc
from Cat.utils.profiling import logError
from Cat.utils.signals import CatSignal, CatBoundSignal
from model.data.mcVersions import MCVersion, getMCVersion
from model.data.dpVersion import DPVersion, getDPVersion
from model.project import Project
from session.documentHandling import DocumentsManager
from settings import applicationSettings

WindowId = NewType('WindowId', str)


@RegisterContainer
class Session(SerializableContainer):
	"""docstring for Session"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	project: Project = Serialized(default_factory=Project)
	hasOpenedProject: bool = Computed(getInitValue=lambda s: bool(s.project.isValid))

	documents: DocumentsManager = Serialized(default_factory=DocumentsManager, decorators=[pd.NoUI()])

	minecraftData: MCVersion = Computed(default_factory=lambda: getMCVersion(applicationSettings.minecraft.version))
	datapackData: DPVersion = Computed(default_factory=lambda: getDPVersion(applicationSettings.minecraft.dpVersion))

	def closeProject(self) -> None:
		project = self.project
		project.reset()
		# resetAllGlobalCaches()
		gc.collect()

	def openProject(self, newWorldPath: str) -> None:
		self.closeProject()
		self.project.path = newWorldPath

	onError: CatBoundSignal[Session, Callable[[Exception, str], None]] = CatSignal[Callable[[Exception, str], None]]('onError')

	def showAndLogError(self, e: Exception, title: str = 'Error') -> None:
		self.onError.emit(e, title)


__session = Session()

__session.onError.connect('logError', lambda e, title: logError(f'title:', format_full_exc(e)))


def getSession() -> Session:
	return __session


def setSession(session: Session):
	global __session
	assert isinstance(session, Session)
	if session is not __session:
		__session.reset()
		__session.copyFrom(session)


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
			session = getSession().fromJSON(inFile.read(), onError=_logError)
			setSession(session)
			# deferredSelf = getSession().fromJSONDefer(inFile.read(), onError=_logError)
			# setSession(next(deferredSelf))
			# next(deferredSelf)
	except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load session: \n{traceback.format_exc()}')


def saveSessionToFile(filePath: str = None) -> None:
	if filePath is None:
		filePath = getSessionFilePath()
	with openOrCreate(filePath, "w") as outFile:
		getSession().toJSON(outFile)
