"""
open document, close document, select document, move to view, etc. ...
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import NewType, Optional, Callable, Iterator, cast, Sequence, ClassVar

from Cat.Serializable.dataclassJson import SerializableDataclass, catMeta
from Cat.utils import abstract, override
from Cat.utils.abc_ import abstractmethod
from Cat.utils.collections_ import Stack
from Cat.utils.profiling import logInfo
from Cat.utils.signals import CatSignal
from base.model.utils import Span
from base.model.pathUtils import FilePath, toDisplayPath
from base.model.documents import Document, DocumentTypeDescription, loadDocument

WindowId = NewType('WindowId', str)


@dataclass(unsafe_hash=True, frozen=True)
class ViewId:
	window: WindowId


@dataclass(repr=False, slots=True)
@abstract
class ViewBase(SerializableDataclass):
	parent: Optional[ViewContainer] = field(default=None, init=False, metadata=catMeta(serialize=True))
	manager: DocumentsManager

	@abstractmethod
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		...

	def __hash__(self):
		return hash(id(self)) + 17948354


@dataclass(repr=False, slots=True)
class ViewContainer(ViewBase):

	isVertical: bool = False
	views: list[ViewBase] = field(default_factory=list, metadata=catMeta(deferLoading=True))
	onViewsChanged: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onViewsChanged')
	# onViewsChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onViewsChanged')

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
		view.makeCurrent()
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
		oldViews: list[ViewBase] = self.views.copy()
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
				newViews0 = newViews[0]
				self.isVertical = newViews0.isVertical
				newViews = newViews0.views.copy()
				newViews0.views.clear()

		for view in newViews:
			self._setParentFor(view, self)
		self.views = newViews
		if self.parent is not None:
			self.parent.flattenDown()
		if newViews != oldViews:
			self.onViewsChanged.emit()

	@override
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		for view in self.views:
			view = view.getViewForDocument(doc)
			if view is not None:
				return view
		return None

	def __hash__(self):
		return hash(id(self)) + 17948353


@dataclass(repr=False, slots=True)
class View(ViewBase):
	documents: list[Document] = field(default_factory=list)
	selectedDocument: Optional[Document] = None

	onDocumentsChanged: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onDocumentsChanged')
	# onDocumentsChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onDocumentsChanged')
	onMadeCurrent: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onMadeCurrent')
	# onMadeCurrent: CatBoundSignal[Callable[[], None]] = CatSignal('onMadeCurrent')
	onSelectedDocumentChanged: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onSelectedDocumentChanged')
	# onSelectedDocumentChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onSelectedDocumentChanged')

	@property
	def isCurrent(self) -> bool:
		return self.manager.currentView is self

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

	def selectDocument(self, doc: Optional[Document], forceUpdate: bool = False) -> None:
		old = self.selectedDocument
		if doc is not old or forceUpdate:
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
			from base.model.session import getSession
			self.manager = getSession().documents

	@override
	def getViewForDocument(self, doc: Document) -> Optional[View]:
		if doc in self.documents:
			return self
		return None

	def __hash__(self):
		return hash(id(self)) + 17948352


@dataclass(repr=False, slots=True)
class DocumentsManager(SerializableDataclass):
	"""used in `DocumentsManager.safelyCloseDocument(...)` to overcome a bug with PyCharm 2021.2's type checker :'("""

	def __post_init__(self):
		self.viewsC = ViewContainer(self)
		self.currentView = self._getFirstView()

	viewsC: ViewContainer = field(init=False, metadata=catMeta(serialize=True))

	@property
	def views(self) -> Sequence[View]:
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

	def _getFirstView(self) -> View:
		if not self.views:
			view = self.viewsC.insertNewView(-1)
		else:
			view = self.views[0]
		return view
	currentView: View = field(init=False, metadata=catMeta(serialize=True))

	# callbacks (must be set externally, for prompting the user, etc...):
	onCanCloseModifiedDocument: Callable[[Document], bool] = field(default=lambda d: True, metadata=catMeta(serialize=False))
	onCurrentViewChanged: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onCurrentViewChanged')
	# onCurrentViewChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onCurrentViewChanged')
	onSelectedDocumentChanged: ClassVar[CatSignal[Callable[[], None]]] = CatSignal('onSelectedDocumentChanged')
	# onSelectedDocumentChanged: CatBoundSignal[Callable[[], None]] = CatSignal('onSelectedDocumentChanged')

	# views:

	def forceCloseView(self, view: View) -> None:
		if view.parent is not None:
			view.parent.forceRemove(view)
		if self.currentView is view:
			self.selectView(self._getFirstView())

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
		if getattr(self, 'currentView', None) is not view:
			logInfo(f"selecting View <{type(view).__qualname__} 0x{id(view):x}>.")
			self.currentView = view
			view.onMadeCurrent.emit()
			self.onCurrentViewChanged.emit()
			self.onSelectedDocumentChanged.emit()

	# utility:

	def _getViewForDocument(self, doc: Document) -> Optional[View]:
		return self.viewsC.getViewForDocument(doc)

	@staticmethod
	def _insertDocument(doc: Document, view: View, pos: Optional[int]):
		view.insertDocument(doc, pos)

	# documents: (open / close / select / ...)

	@property
	def currentDocument(self) -> Optional[Document]:
		return self.currentView.selectedDocument

	@property
	def selectedDocument(self) -> Optional[Document]:
		return self.currentDocument

	def showDocument(self, doc: Document, cursor: Span = None) -> None:
		view = self._getViewForDocument(doc)
		if view is not None:
			if cursor is not None:
				doc.locatePosition(*cursor)
			view.selectDocument(doc, forceUpdate=cursor is not None)
			self.selectView(view)

	def selectDocument(self, doc: Document, cursor: Span = None) -> None:
		self.showDocument(doc, cursor)

	def _openOrShowDocument(self, filePath: FilePath, cursor: Span = None) -> None:  # throws OSError
		doc = self.getDocument(filePath)
		if doc is None:  # open it:
			doc = self._openDocument(filePath, None)
		self.showDocument(doc, cursor)

	def _openDocument(self, filePath: FilePath, view: View = None) -> Document:  # throws OSError
		logInfo("opening File from:{}".format(filePath))
		doc = loadDocument(filePath)
		view = view or self.currentView
		self._insertDocument(doc, view, None)
		return doc

	def _saveDocument(self, document: Document) -> None:
		if document.isNew:
			raise ValueError("a path must be set before saving a document (document.isNew must be False)")
		else:
			document.saveToFile()

	def _reloadDocument(self, document: Document) -> None:
		if document.isNew:
			raise ValueError("a path must be set before reloading a document (document.isNew must be False)")
		else:
			document.loadFromFile()

	def safelyCloseDocument(self, doc: Document) -> bool:
		if doc.documentChanged:
			cb: Callable[[Document], bool] = self.onCanCloseModifiedDocument
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
			doc.close()

	def createNewDocument(self, docType: DocumentTypeDescription, filePath: Optional[FilePath]) -> Document:
		isUntitled = filePath is None
		if isUntitled:
			# find a new file name:
			filePath = self._getNewUntitledFileName()
		# create document:
		doc = docType.newDocument()
		if isUntitled:
			doc.setUntitledFilePath(filePath)
		else:
			doc.filePath = filePath
		view = self.currentView
		self._insertDocument(doc, view, None)
		return doc

	def _getNewUntitledFileName(self) -> str:
		existingDocNames = {doc.filePathForDisplay for view in self.views for doc in view.documents}
		i: int = 0
		while True:
			i += 1
			docName = f'untitled {i}'
			if docName not in existingDocNames:
				return docName

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
		filePathForDisplay = toDisplayPath(filePath)

		for view in self.views:
			for doc in view.documents:
				if doc.filePathForDisplay == filePathForDisplay:
					return doc
		return None

	def allOpenedDocuments(self) -> Iterator[Document]:
		for view in self.views:
			yield from view.documents

	def __hash__(self):
		return hash(id(self)) + 17948351
