from __future__ import annotations

import gc
import os
import traceback
from json import JSONDecodeError
from typing import Optional, NewType

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, ComputedCached, Computed
from Cat.utils import getExePath
from Cat.utils.profiling import logError
from documents import Document, getFilePathForDisplay, getDocTypeByName, getDocumentTypeForFilePath, DocumentTypeDescription
from model.pathUtils import FilePath
from model.Model import World

WindowId = NewType('WindowId', str)

@RegisterContainer
class Session(SerializableContainer):
	"""docstring for Session"""
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	class SelectedDocumentProxy:
		def __init__(self, session: Session):
			self._session: Session = session

		def pop(self, windowId: WindowId) -> None:
			self._session.selectedDocumentIds.pop(windowId, None)

		def __getitem__(self, windowId: WindowId) -> Optional[Document]:
			docName = self._session.selectedDocumentIds.get(windowId, None)
			if docName is not None:
				return getSession().getDocument(docName)
			return None

		def __setitem__(self, windowId: WindowId, document: Optional[Document]):
			if document is not None:
				assert document in self._session.documents
				self._session.selectedDocumentIds[windowId] = document.filePathForDisplay
			else:
				self._session.selectedDocumentIds[windowId] = None

	world: World = Serialized(default_factory=World)
	hasOpenedWorld: bool = Computed(getInitValue=lambda s: bool(s.world.isValid))

	documents: list[Document] = Serialized(default_factory=list, decorators=[pd.NoUI()])
	selectedDocumentIds: dict[WindowId, Optional[str]] = Serialized(default_factory=dict, doc="the key is the window id, the value is the displayName of the selected document if any.", decorators=[pd.NoUI()])
	selectedDocuments: SelectedDocumentProxy = ComputedCached(getInitValue=SelectedDocumentProxy, doc="the key is the window id, the value is The selected document if any.", shouldSerialize=False, decorators=[pd.NoUI()])

	def _insertDocument(self, doc: Document, windowId: WindowId, atPosition: int):
		# get insert position:
		if atPosition is None:
			currentDocument: Optional[Document] = self.selectedDocuments[windowId]
			try:
				atPosition = self.documents.index(currentDocument) + 1
			except ValueError:
				atPosition = len(self.documents)
		elif atPosition == -1:
			atPosition = len(self.documents)

		self.documents.insert(atPosition, doc)

	def createNewDocument(self, docType: DocumentTypeDescription, filePath: Optional[str], windowId: WindowId, *, atPosition: int = None) -> Document:
		if filePath is None:
			# find a new file name:
			existingDocNames = {doc.filePathForDisplay for doc in getSession().documents}
			i: int = 0
			while True:
				i += 1
				docName = f'untitled {i}'
				if docName not in existingDocNames:
					filePath = docName
					break
		# create document:
		doc = docType.newDocument()
		doc.filePath = filePath
		self._insertDocument(doc, windowId, atPosition)
		return doc

	def openDocument(self, filePath: FilePath, windowId: WindowId, *, atPosition: int = None) -> Document:
		fps = filePath if isinstance(filePath, str) else filePath[1]
		_, ext = os.path.splitext(fps)

		docType = getDocumentTypeForFilePath(filePath, default=getDocTypeByName('text'))
		doc = docType.newDocument()
		doc.filePath = filePath
		doc.loadFromFile()
		self._insertDocument(doc, windowId, atPosition)
		return doc

	def closeDocument(self, doc: Document, windowId: WindowId) -> None:
		self.documents.remove(doc)

	def getDocument(self, filePath: FilePath) -> Optional[Document]:
		filePathForDisplay = getFilePathForDisplay(filePath)
		for doc in self.documents:
			if doc.filePathForDisplay == filePathForDisplay:
				return doc
		return None

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
