"""
open document, close document, select document, move to view, etc. ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, Optional, TYPE_CHECKING, Callable, Iterable, Iterator, cast

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import SerializableContainer, RegisterContainer, Serialized, Computed
from Cat.utils import abstract, override
from Cat.utils.abc_ import abstractmethod
from Cat.utils.collections_ import Stack
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
@abstract
class ViewBase(SerializableContainer):
	__slots__ = ()
	parent: Optional[ViewContainer] = Serialized(default=None, decorators=[pd.NoUI()])
	manager: DocumentsManager = Serialized(default=None, decorators=[pd.NoUI()])

	# def __init__(self, parent: Optional[ViewContainer] = None):
	# 	super(ViewBase, self).__init__()
	# 	self.parent = parent
	# 	if parent is not None:
	# 		self.manager = parent.manager

	def __init__(self, manager: DocumentsManager = None):
		super(ViewBase, self).__init__()
		if manager is not None:
			self.manager = manager

	@abstractmethod
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		...

@RegisterContainer
class ViewContainer(ViewBase):
	__slots__ = ()

	isVertical: bool = Serialized(default=False)
	views: list[ViewBase] = Serialized(default_factory=list)
	onViewsChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onViewsChanged')

	@staticmethod
	def _setParentFor(view: ViewBase, newParent: Optional[ViewContainer]):
		if view.parent is not None and view.parent is not newParent:
			try:
				view.parent.views.remove(view)
				view.parent.flattenDown()
				view.parent.onViewsChanged.emit()
			except ValueError:
				pass  # element already has been removed for us
		view.parent = newParent

	def forceRemove(self, view: ViewBase) -> None:
		self.views.remove(view)
		self._setParentFor(view, None)
		self.flattenDown()
		self.onViewsChanged.emit()

	def insertView(self, view: ViewBase, pos: int) -> None:
		# get insert position:
		if pos == -1:
			pos = len(self.views)

		if isinstance(view, ViewContainer) and view.isVertical == self.isVertical:
			# flatten views:
			viewsCopy = view.views.copy()
			for v in viewsCopy:
				self.insertView(v, pos)
				pos += 1
			assert not view.views
			self.flattenDown()
		else:
			self.views.insert(pos, view)
			self._setParentFor(view, self)
			self.onViewsChanged.emit()

	def insertNewView(self, pos: int) -> View:
		view = View(self.manager)
		self.insertView(view, pos)
		return view

	def splitView(self, view: ViewBase, isVertical: bool) -> View:
		assert view in self.views
		pos = self.views.index(view)
		if self.isVertical == isVertical:
			newView = self.insertNewView(pos + 1)
		else:
			if isinstance(view, ViewContainer) and view.isVertical == isVertical:
				newView = view.insertNewView(-1)
			else:
				newContainer = ViewContainer(self.manager)
				newContainer.isVertical = isVertical
				self.views[pos] = newContainer
				newContainer.insertView(view, -1)
				newView = newContainer.insertNewView(-1)
				newContainer.parent = self
				self.onViewsChanged.emit()
		return newView

	def flatten(self) -> None:
		newViews: list[ViewBase] = []
		for view in self.views:
			if isinstance(view, ViewContainer):
				view.flatten()
				if view.isVertical == self.isVertical or len(view.views) == 1:
					newViews.extend(view.views)
					view.views.clear()
				elif view.views:
					newViews.append(view)
			else:
				newViews.append(view)

		if len(newViews) == 1:
			if isinstance(newViews[0], ViewContainer):
				self.isVertical = newViews[0].isVertical
				newViews = newViews[0].views.copy()
				newViews[0].views.clear()

		for view in newViews:
			self._setParentFor(view, self)
		self.views = newViews

	def flattenDown(self) -> None:
		newViews: list[ViewBase] = []
		for view in self.views:
			if isinstance(view, ViewContainer):
				if view.isVertical == self.isVertical or len(view.views) == 1:
					newViews.extend(view.views)
					view.views.clear()
				elif view.views:
					newViews.append(view)
			else:
				newViews.append(view)

		if len(newViews) == 1:
			if isinstance(newViews[0], ViewContainer):
				self.isVertical = newViews[0].isVertical
				newViews = newViews[0].views.copy()
				newViews[0].views.clear()

		for view in newViews:
			self._setParentFor(view, self)
		self.views = newViews
		if self.parent is not None and len(newViews) <= 1:
			self.parent.flattenDown()
		else:
			self.onViewsChanged.emit()

	@override
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		for view in self.views:
			view = view.getViewForDocument(doc)
			if view is not None:
				return view
		return None


@RegisterContainer
class View(ViewBase):
	__slots__ = ()
	documents: list[Document] = Serialized(default_factory=list, decorators=[pd.NoUI()])
	selectedDocument: Optional[Document] = Serialized(default=None, decorators=[pd.NoUI()])

	onDocumentsChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onDocumentsChanged')
	onMadeCurrent: CatBoundSignal[Callable[[], None]] = CatSignal('onMadeCurrent')
	onSelectedDocumentChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onSelectedDocumentChanged')

	isCurrent: bool = Computed(getInitValue=lambda s: s.manager.currentView is s)

	# documents related:
	def insertDocument(self, doc: Document, pos: Optional[int]) -> None:
		# get insert position:
		if pos is None:
			currentDocument: Optional[Document] = self.selectedDocument
			try:
				pos = self.documents.index(currentDocument) + 1
			except ValueError:
				pos = len(self.documents)
		elif pos == -1:
			pos = len(self.documents)

		self.documents.insert(pos, doc)
		self.onDocumentsChanged.emit()

	def removeDocument(self, doc: Document) -> None:
		if self.selectedDocument is doc:
			# change selected document:
			try:
				idx = self.documents.index(doc)
			except ValueError:
				idx = -1
			try:
				self.selectDocument(self.documents[idx-1])
			except IndexError:
				if len(self.documents) == 1 and idx != -1:
					self.selectDocument(None)
				elif len(self.documents) == 0:
					self.selectDocument(None)
				else:
					self.selectDocument(self.documents[0])
		# remove
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

	def selectDocument(self, doc: Optional[Document]) -> None:
		old = self.selectedDocument
		if doc is not old:
			self.selectedDocument = doc
			if self.isCurrent:
				self.manager.onSelectedDocumentChanged.emit()
			self.onSelectedDocumentChanged.emit()


	# view related:
	def makeCurrent(self) -> None:
		self._ensureManagerIsSet()
		self.manager.selectView(self)

	def splitView(self, isVertical: bool) -> View:
		assert self.parent
		# if self.parent is None:
		return self.parent.splitView(self, isVertical)

	# houseKeeping:
	def _ensureManagerIsSet(self) -> None:
		if self.manager is None:
			from session.session import getSession
			self.manager = getSession().documents

	@override
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		if doc in self.documents:
			return self
		return None


@RegisterContainer
class DocumentsManager(SerializableContainer):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	viewsC: ViewContainer = Serialized(getInitValue=ViewContainer)
	#views: list[View] = Serialized(default_factory=list)

	@property
	def views(self) -> list[View]:
		stack: Stack[Iterator[ViewBase]] = Stack()
		stack.push(iter(self.viewsC.views))
		views: list[View] = []
		while stack:
			v = next(stack.peek(), None)
			if v is None:
				stack.pop()
			elif isinstance(v, ViewContainer):
				stack.push(iter(v.views))
			else:
				views.append(cast(View, v))
		return views

	currentView: View = Serialized(getInitValue=lambda s: s._getFirstView())

	# callbacks (must be set externally, for prompting the user, etc...):
	onCanCloseModifiedDocument: Callable[[Document], bool] = Serialized(default=lambda d: True, shouldSerialize=False)
	onCurrentViewChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onCurrentViewChanged')
	onSelectedDocumentChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onSelectedDocumentChanged')

	# views:
	def _getFirstView(self) -> View:
		if not self.viewsC.views:
			view = self.viewsC.insertNewView(-1)
		else:
			view = self.views[0]
		return view

	def addView(self) -> View:
		view = View(self)
		self.views.append(view)
		self.onViewsChanged.emit()
		return view

	@staticmethod
	def forceCloseView(view: View) -> None:
		if view.parent is not None:
			view.parent.forceRemove(view)

	def safelyCloseView(self, view: View) -> None:
		for doc in view.documents:
			if not self.safelyCloseDocument(doc):
				return
		self.forceCloseView(view)

	def selectView(self, view: View) -> None:
		# try:
		# 	idx = self.views.index(view)
		# except ValueError:
		# 	idx = -1
		# logInfo(f"selecting View #{idx}.")
		# print(f"~ ~ ~ ~ ~ selecting View #{idx}.")
		if self.currentView is not view:
			logInfo(f"selecting View {view}.")
			self.currentView = view
			view.onMadeCurrent.emit()
			self.onCurrentViewChanged.emit()
			self.onSelectedDocumentChanged.emit()

	def selectDocument(self, doc: Document, cursor: Span = None) -> None:
		self.showDocument(doc, cursor)

	def _getViewForDocument(self, doc: Document) -> Optional[View]:
		return self.viewsC.getViewForDocument(doc)

	# utility:

	@staticmethod
	def _insertDocument(doc: Document, view: View, pos: Optional[int]):
		view.insertDocument(doc, pos)

	# open / close / select / ...

	def showDocument(self, doc: Document, cursor: Span = None) -> None:
		view = self._getViewForDocument(doc)
		if view is not None:
			if cursor is not None:
				doc.locatePosition(*cursor)
			view.selectDocument(doc)
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

	def safelyCloseDocument(self, doc: Document) -> bool:
		if doc.documentChanged:
			cb = self.onCanCloseModifiedDocument
			if cb(doc):
				self.forceCloseDocument(doc)
				return True
		else:
			self.forceCloseDocument(doc)
			return True
		return False

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

	def moveDocument(self, document: Document, newView: View, newPosition: Optional[int] = None) -> None:
		oldView = self._getViewForDocument(document)
		if oldView == newView:
			if newPosition is not None:
				newView.moveDocument(document, newPosition)
		else:
			oldView.removeDocument(document)
			newView.insertDocument(document, newPosition)
			newView.selectDocument(document)

	# accessors:

	def getDocument(self, filePath: FilePath) -> Optional[Document]:
		filePathForDisplay = getFilePathForDisplay(filePath)

		for view in self.views:
			for doc in view.documents:
				if doc.filePathForDisplay == filePathForDisplay:
					return doc
		return None
