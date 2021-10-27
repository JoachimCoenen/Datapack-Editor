"""
open document, close document, select document, move to view, etc. ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, Optional, TYPE_CHECKING, Callable

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, Computed
from Cat.utils.profiling import logInfo
from Cat.utils.signals import CatSignal, CatBoundSignal
from model.parsingUtils import Span
from model.pathUtils import FilePath
from session.documents import Document, DocumentTypeDescription, getDocumentTypeForFilePath, getDocTypeByName, getFilePathForDisplay

if TYPE_CHECKING:
	pass


WindowId = NewType('WindowId', str)


@dataclass(unsafe_hash=True, frozen=True)
class ViewId:
	window: WindowId


@RegisterContainer
class View(SerializableContainer):
	parent: Optional[Documents] = Serialized(default=None, decorators=[pd.NoUI()])
	documents: list[Document] = Serialized(default_factory=list, decorators=[pd.NoUI()])
	selectedDocument: Optional[Document] = Serialized(default=None, decorators=[pd.NoUI()])

	@selectedDocument.onSet
	def selectedDocument(self, new: Optional[Document], old: Optional[Document]) -> Optional[Document]:
		if new is not old:
			pass
		return new

	onDocumentsChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onDocumentsChanged')
	onMadeCurrent: CatBoundSignal[Callable[[], None]] = CatSignal('onMadeCurrent')

	isCurrent: bool = Computed(getInitValue=lambda s: s.parent.currentView is s)

	def __init__(self, parent: Optional[Documents] = None):
		super(View, self).__init__()
		self.parent = parent

	# documents related:
	def insertDocument(self, doc: Document, atPosition: Optional[int]) -> None:
		# get insert position:
		if atPosition is None:
			currentDocument: Optional[Document] = self.selectedDocument
			try:
				atPosition = self.documents.index(currentDocument) + 1
			except ValueError:
				atPosition = len(self.documents)
		elif atPosition == -1:
			atPosition = len(self.documents)

		self.documents.insert(atPosition, doc)
		self.onDocumentsChanged.emit()

	def removeDocument(self, doc: Document) -> None:
		try:
			self.documents.remove(doc)
		except ValueError:
			return
		self.onDocumentsChanged.emit()

	def moveDocument(self, document: Document, newPosition: int) -> None:
		documents = self.documents
		if newPosition not in range(len(documents)):
			raise ValueError(f"newPosition is out of range (newPosition={newPosition}, len(documents)={len(documents)}")

		oldPosition = documents.index(document)
		if oldPosition == newPosition:
			return

		del documents[oldPosition]
		documents.insert(newPosition, document)
		self.onDocumentsChanged.emit()

	# view related:
	def makeCurrent(self) -> None:
		if self.parent is None:
			from session.session import getSession
			self.parent = getSession().documents
		self.parent.selectView(self)


@RegisterContainer
class Documents(SerializableContainer):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	# callbacks (must be set externally, for prompting the user, etc...):
	onCanCloseModifiedDocument: Callable[[Document], bool] = Serialized(default=lambda d: True, shouldSerialize=False)

	# class SelectedDocumentProxy:
	# 	def __init__(self, documents: Documents):
	# 		self._documents: Documents = documents
	#
	# 	def pop(self, windowId: WindowId) -> None:
	# 		self._documents.selectedDocumentIds.pop(windowId, None)
	#
	# 	def __getitem__(self, windowId: WindowId) -> Optional[Document]:
	# 		docName = self._documents.selectedDocumentIds.get(windowId, None)
	# 		if docName is not None:
	# 			return self._documents.getDocument(docName)
	# 		return None
	#
	# 	def __setitem__(self, windowId: WindowId, document: Optional[Document]):
	# 		if document is not None:
	# 			assert document in self._documents._documents
	# 			self._documents.selectedDocumentIds[windowId] = document.filePathForDisplay
	# 		else:
	# 			self._documents.selectedDocumentIds[windowId] = None

	views: list[View] = Serialized(default_factory=list)

	# _documents: list[Document] = Serialized(default_factory=list, decorators=[pd.NoUI()])

	# _documents: list[Document] = Serialized(default_factory=list, decorators=[pd.NoUI()])
	# selectedDocumentIds: dict[WindowId, Optional[str]] = Serialized(default_factory=dict, doc="the key is the window id, the value is the displayName of the selected document if any.", decorators=[pd.NoUI()])
	# selectedDocuments: SelectedDocumentProxy = ComputedCached(getInitValue=SelectedDocumentProxy, doc="the key is the window id, the value is The selected document if any.", shouldSerialize=False, decorators=[pd.NoUI()])

	currentView: View = Serialized(getInitValue=lambda s: s._getFirstView())

	# views:
	def _getFirstView(self) -> View:
		if not self.views:
			view = View(self)
			self.views.append(view)
		else:
			view = self.views[0]
		return view

	def _addView(self) -> View:
		view = View(self)
		self.views.append(view)
		return view

	def _closeView(self, view: View) -> None:
		...

	def selectView(self, view: View) -> None:
		try:
			idx = self.views.index(view)
		except ValueError:
			idx = -1
		logInfo(f"selecting View #{idx}.")
		print(f"~ ~ ~ ~ ~ selecting View #{idx}.")
		self.currentView = view
		view.onMadeCurrent.emit()

	def _getViewForDocument(self, doc: Document) -> Optional[View]:
		for view in self.views:
			if doc in view.documents:
				return view
		return None

	# utility:

	@staticmethod
	def _insertDocument(doc: Document, view: View, atPosition: Optional[int]):
		view.insertDocument(doc, atPosition)

	# open / close / select / ...

	def showDocument(self, doc: Document, cursor: Span = None) -> None:
		view = self._getViewForDocument(doc)
		if view is not None:
			if cursor is not None:
				doc.locatePosition(*cursor)
			view.selectedDocument = doc
			self.selectView(view)

	def openOrShowDocument(self, filePath: FilePath, cursor: Span = None) -> None:  # throws OSError
		doc = self.getDocument(filePath)
		if doc is None:  # open it:
			doc = self._openDocument(filePath, None)
		self.showDocument(doc, cursor)

	def _openDocument(self, filePath: FilePath, view: View = None) -> Document:  # throws OSError
		logInfo("opening File from:{}".format(filePath))

		docType = getDocumentTypeForFilePath(filePath, default=getDocTypeByName('text'))
		doc = docType.newDocument()
		doc.filePath = filePath

		view = view or self.currentView
		self._insertDocument(doc, view, None)

		doc.loadFromFile()
		return doc

	def safelyCloseDocument(self, doc: Document) -> None:
		if doc.documentChanged:
			cb = self.onCanCloseModifiedDocument
			if cb(doc):
				self.forceCloseDocument(doc)
		else:
			self.forceCloseDocument(doc)

	def forceCloseDocument(self, doc: Document) -> None:
		view = self._getViewForDocument(doc)
		if view is not None:
			view.removeDocument(doc)

	def createNewDocument(self, docType: DocumentTypeDescription, filePath: Optional[str]) -> Document:
		if filePath is None:
			# find a new file name:
			existingDocNames = {doc.filePathForDisplay for view in self.views for doc in view.documents}
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
		view = self.currentView
		self._insertDocument(doc, view, None)
		return doc

	# accessors:

	def getDocument(self, filePath: FilePath) -> Optional[Document]:
		filePathForDisplay = getFilePathForDisplay(filePath)

		for view in self.views:
			for doc in view.documents:
				if doc.filePathForDisplay == filePathForDisplay:
					return doc
		return None
