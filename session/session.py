from __future__ import annotations

import gc
import os
import traceback
from json import JSONDecodeError
from typing import NewType

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, Computed
from Cat.utils import getExePath
from Cat.utils.profiling import logError
from model.Model import World
from session.documentHandling import DocumentsManager

WindowId = NewType('WindowId', str)


@RegisterContainer
class Session(SerializableContainer):
	"""docstring for Session"""
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	world: World = Serialized(default_factory=World)
	hasOpenedWorld: bool = Computed(getInitValue=lambda s: bool(s.world.isValid))

	documents: DocumentsManager = Serialized(default_factory=DocumentsManager, decorators=[pd.NoUI()])

	def closeWorld(self) -> None:
		world = self.world
		world.reset()
		# resetAllGlobalCaches()
		gc.collect()

	def openWorld(self, newWorldPath: str) -> None:
		self.closeWorld()
		self.world.path = newWorldPath


__session = Session()


def getSession() -> Session:
	return __session


def setSession(session: Session):
	global __session
	assert isinstance(session, Session)
	__session = session


def getSessionFilePath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'sessions', 'session1.json')


def _logError(e, s):
	logError(e, s)
	raise e


def loadSessionFromFile(filePath: str = None) -> None:
	if filePath is None:
		filePath = getSessionFilePath()
	try:
		with open(filePath, "r") as inFile:
			deferredSelf = getSession().fromJSONDefer(inFile.read(), onError=_logError)
			setSession(next(deferredSelf))
			next(deferredSelf)
	except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load session: \n{traceback.format_exc()}')


def saveSessionToFile(filePath: str = None) -> None:
	if filePath is None:
		filePath = getSessionFilePath()
	with open(filePath, "w") as outFile:
		getSession().toJSON(outFile)


from model import commands

commands.setGetSession(getSession)
