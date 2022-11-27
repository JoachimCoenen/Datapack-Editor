from __future__ import annotations
import os
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Type, Sequence, Callable, TypeVar, Collection, Any

from PyQt5.QtCore import QTimer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent, FileClosedEvent

from Cat import undoRedo
from Cat.CatPythonGUI.GUI import codeEditor
from Cat.Serializable import Computed, RegisterContainer, Serialized, SerializableContainer, Transient
from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.undoRedo import UndoRedoStack2, MakeMementoIfDiffFunc
from Cat.utils import utils, Decorator
from Cat.utils.logging_ import logWarning
from Cat.utils.profiling import logInfo, logError, TimedMethod

from Cat.utils.signals import CatSignal
from base.model import filesystemEvents
from base.model.parsing.contextProvider import parseNPrepare, getContextProvider
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Node, Schema
from base.model.pathUtils import fileNameFromFilePath, FilePath, ZipFilePool, loadTextFile, ArchiveFilePool, unitePath, toDisplayPath, unitePathTpl
from base.model.utils import GeneralError, Position, WrappedError, LanguageId

TTarget = TypeVar("TTarget")


@dataclass
class ErrorCounts:
	parserErrors: int = 0
	configErrors: int = 0
	configWarnings: int = 0
	configHints: int = 0

	@property
	def totalErrors(self) -> int:
		return self.parserErrors + self.configErrors

	@property
	def total(self) -> int:
		return self.parserErrors + self.configErrors + self.configWarnings + self.configHints

	def __add__(self, other: ErrorCounts) -> ErrorCounts:
		if not isinstance(other, ErrorCounts):
			raise TypeError(f"unsupported operand type(s) for +: '{type(self)!r}' and '{type(other)!r}'")
		return ErrorCounts(
			self.parserErrors + other.parserErrors,
			self.configErrors + other.configErrors,
			self.configWarnings + other.configWarnings,
			self.configHints + other.configHints,
		)

	def __iadd__(self, other: ErrorCounts):
		if not isinstance(other, ErrorCounts):
			raise TypeError(f"unsupported operand type(s) for +=: '{type(self)!r}' and '{type(other)!r}'")
		self.parserErrors += other.parserErrors
		self.configErrors += other.configErrors
		self.configWarnings += other.configWarnings
		self.configHints += other.configHints
		return self


def getErrorCounts(parserErrors: Collection[GeneralError], otherErrors: Collection[GeneralError]) -> ErrorCounts:
	errorCounts = ErrorCounts()

	errorCounts.parserErrors = len(parserErrors)

	for error in otherErrors:
		if error.style == 'error':
			errorCounts.configErrors += 1
		elif error.style == 'warning':
			errorCounts.configWarnings += 1
		elif error.style in {'hint', 'info'}:
			errorCounts.configHints += 1
		else:
			logError(f'Unknown configError style: {error.style!r}')
	return errorCounts


@dataclass
class DocumentTypeDescription:
	type: Type[Document]
	name: str
	icon: Optional[str] = None
	tip: Optional[str] = None
	extensions: list[str] = field(default_factory=list)
	suffixesForDocTypeMatching: list[str] = field(default=None)
	defaultLanguage: str = 'PlainText'

	def __post_init__(self):
		suffixes = self.suffixesForDocTypeMatching
		if suffixes is None:
			suffixes = self.extensions
		self.suffixesForDocTypeMatching = sorted(suffixes, key=len, reverse=True)

	def newDocument(self) -> Document:
		return self.type.create(language=self.defaultLanguage)

	def __eq__(self, other):
		return self is other

	def __ne__(self, other):
		return self is not other

	def __hash__(self):
		return id(self)

_documentTypes: list[DocumentTypeDescription] = []
_documentTypesByName: dict[str, DocumentTypeDescription] = {}


@Decorator
class RegisterDocument:
	def __init__(
			self,
			name: str,
			*,
			ext: list[str],
			suffixes: list[str] = None,
			defaultLanguage: str = 'PlainText',
			icon: str=None,
			tip: str=None
	):
		if suffixes is None:
			suffixes = ext
		self._documentName: str = name
		self._extensions: list[str] = ext
		self._extensionsForDocTypeSelection: list[str] = ext
		self._suffixesForDocTypeMatching: list[str] = suffixes
		self._icon:  Optional[str] = icon
		self._tip:  Optional[str] = tip
		self._defaultLanguage: str = defaultLanguage

	def __call__(self, documentCls: Type[Document]):
		docTypeDescr = DocumentTypeDescription(
			type=documentCls,
			name=self._documentName,
			icon=self._icon,
			tip=self._tip,
			extensions=self._extensions,
			suffixesForDocTypeMatching=sorted(self._suffixesForDocTypeMatching, key=len, reverse=True),
			defaultLanguage=self._defaultLanguage
		)
		registerDocumentTypeDescription(docTypeDescr)
		return documentCls


def registerDocumentTypeDescription(docTypeDescr: DocumentTypeDescription):
	assert issubclass(docTypeDescr.type, Document)
	assert not docTypeDescr.type is Document
	docName = docTypeDescr.name
	assert docName not in _documentTypesByName, f"A document type named '{docName}' is already registered ({_documentTypesByName[docName]})."
	_documentTypes.append(docTypeDescr)
	_documentTypesByName[docName] = docTypeDescr


def getDocumentTypes() -> list[DocumentTypeDescription]:
	return _documentTypes


def getDocumentTypeForFilePath(path: FilePath, default: Optional[DocumentTypeDescription] = None) -> Optional[DocumentTypeDescription]:
	fileName = fileNameFromFilePath(path).lower()
	bestDocTypeGuess: Optional[DocumentTypeDescription] = None
	bestDocTypeMatchQuality: int = 0
	for dt in _documentTypes:
		for suffix in dt.suffixesForDocTypeMatching:
			if fileName.endswith(suffix.lower()):
				if len(suffix) > bestDocTypeMatchQuality:
					bestDocTypeMatchQuality = len(suffix)
					bestDocTypeGuess = dt
					break
	return bestDocTypeGuess if bestDocTypeGuess is not None else default


def getDocTypeByName(name: str, default: Optional[DocumentTypeDescription] = None) -> Optional[DocumentTypeDescription]:
	return _documentTypesByName.get(name, default)


def loadDocument(filePath: FilePath, archiveFilePool: ArchiveFilePool = None) -> Document:  # throws OSError
	docType = getDocumentTypeForFilePath(filePath, default=getDocTypeByName('text'))
	doc = docType.newDocument()
	doc.filePath = filePath
	doc.loadFromFile(archiveFilePool)
	return doc


def addErrors(self):
	parserErrors = self.parserErrors
	validationErrors = self.validationErrors
	summ = parserErrors + validationErrors
	return summ


class FileChangedHandler(FileSystemEventHandler):
	def __init__(self):
		super(FileChangedHandler, self).__init__()
		self.fileChanged: bool = False

	def on_any_event(self, event):
		pass

	def on_moved(self, event: FileMovedEvent):
		if event.is_directory:
			pass
		else:
			self.fileChanged = True

	def on_created(self, event: FileCreatedEvent):
		"""Called when a file or directory is created.

		:param event:
			Event representing file/directory creation.
		:type event:
			:class:`DirCreatedEvent` or :class:`FileCreatedEvent`
		"""
		logWarning("Unexpected on_created event for existing file", event.src_path)

	def on_deleted(self, event: FileDeletedEvent):
		if event.is_directory:
			pass
		else:
			self.fileChanged = True

	def on_modified(self, event: FileModifiedEvent):
		if event.is_directory:
			pass
		else:
			self.fileChanged = True

	def on_closed(self, event: FileClosedEvent):
		pass


@RegisterContainer
class Document(SerializableContainer):
	__slots__ = ('undoRedoStack', 'inUndoRedoMode')
	"""docstring for Document"""
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self._filePath: FilePath = ''
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: ~TTarget = None
		self.highlightErrors: bool = True
		self.errors: Sequence[GeneralError] = []

	def __init__(self):
		super().__init__()
		self.undoRedoStack: Optional[UndoRedoStack2] = None  # must be set with _initUndoRedoStack(...) in constructor of subclasses
		self.inUndoRedoMode: bool = False
		type(self)._originalContent.get(self)  # init _originalContent

	_filePath: FilePath = Serialized(default='')
	_fileChangedHandler: FileChangedHandler = Serialized(default_factory=FileChangedHandler, shouldSerialize=False, shouldPrint=False)

	@property
	def filePath(self) -> FilePath:
		return self._filePath

	@filePath.setter
	def filePath(self, filePath: FilePath):
		oldPath = self._filePath
		self._filePath = filePath
		self._rescheduleFileChangedHandler(oldPath, filePath)

	def _rescheduleFileChangedHandler(self, oldPath: FilePath, newPath: FilePath):
		oldListenerPath = self._getListenerPath(oldPath)
		newListenerPath = self._getListenerPath(newPath)
		filesystemEvents.FILESYSTEM_OBSERVER.reschedule("dpe:file_changed", oldListenerPath, newListenerPath, self._fileChangedHandler)

	def _unscheduleFileChangedHandler(self, oldPath: FilePath):
		oldListenerPath = self._getListenerPath(oldPath)
		filesystemEvents.FILESYSTEM_OBSERVER.unschedule("dpe:file_changed", oldListenerPath)

	@staticmethod
	def _getListenerPath(path: FilePath) -> str:
		if isinstance(path, str):
			return path
		elif os.path.isdir(path[0]):
			return unitePathTpl(path)
		else:
			return path[0]

	language: str = Serialized(default='PlainText', decorators=[pd.ComboBox(choices=Computed(default_factory=codeEditor.getAllLanguages))])

	def _initUndoRedoStack(self, makeMementoIfDiff: MakeMementoIfDiffFunc[TTarget]):
		self.undoRedoStack = UndoRedoStack2(self, self.contentProp, makeMementoIfDiff)

	@Computed()
	def documentChanged(self) -> bool:
		"""Whether the document has been changed (and may need to be saved)."""
		return self.content != self._originalContent

	encoding: str = Serialized(default='utf-8')
	_undoRedoStackInitialized: bool = Serialized(default=False, shouldSerialize=False)
	content: TTarget = Serialized(default=None, decorators=[pd.NoUI()])
	_originalContent: TTarget = Serialized(getInitValue=lambda s: s.content, decorators=[pd.NoUI()])

	# tree: Optional[Node] = Serialized(default=None, shouldSerialize=False, shouldPrint=False, decorators=[pd.NoUI()])
	@Serialized(shouldSerialize=False)
	def tree(self) -> Optional[Node]:
		tree, self.parserErrors = self.parse(self.content)
		return tree

	@content.onSet
	def content(self, newVal: bytes, oldVal: Optional[bytes]) -> bytes:
		self.contentOnSet(newVal, oldVal)
		return newVal

	def contentOnSet(self, newVal: bytes, oldVal: Optional[bytes]) -> None:
		if not self._undoRedoStackInitialized:
			# do take a snapshot to initialize the undoRedoStack:
			self.undoRedoStack.takeSnapshotIfChanged(doDeepCopy=True)
			self._undoRedoStackInitialized = True

		if newVal == oldVal:
			return
		self.asyncParse.callNow(newVal)
		self.asyncValidate()
		# self.asyncParseNValidate()

		self._setDocumentChanged()

		if self.inUndoRedoMode:
			self._asyncTakeSnapshot.cancelPending()
			return

		self._asyncTakeSnapshot()

	highlightErrors: bool = Serialized(default=True)
	onErrorsChanged: CatSignal[Callable[[Document], None]] = CatSignal('onErrorsChanged')
	parserErrors: Sequence[GeneralError] = Serialized(default_factory=list, shouldSerialize=False)
	validationErrors: Sequence[GeneralError] = Serialized(default_factory=list, shouldSerialize=False)
	# validationErrors: Sequence[GeneralError] = Serialized(getInitValue=lambda s: s.validate(), shouldSerialize=False)
	errors: Sequence[GeneralError] = Computed(getInitValue=addErrors, shouldSerialize=False)

	@parserErrors.onSet
	def parserErrors(self, newVal: Sequence[GeneralError], oldVal: Optional[Sequence[GeneralError]]) -> Sequence[GeneralError]:
		if newVal != oldVal:
			QTimer.singleShot(0, lambda self=self: self.onErrorsChanged.emit(self))
		return newVal

	@validationErrors.onSet
	def validationErrors(self, newVal: Sequence[GeneralError], oldVal: Optional[Sequence[GeneralError]]) -> Sequence[GeneralError]:
		if newVal != oldVal:
			QTimer.singleShot(0, lambda self=self: self.onErrorsChanged.emit(self))
		return newVal

	cursorPosition: tuple[int, int] = Serialized(default=(0, 0))
	selection: tuple[int, int, int, int] = Serialized(default=(-1, -1, -1, -1))
	hasSelection: bool = Computed(getInitValue=lambda s: s.selection != (-1, -1, -1, -1))
	forceLocate: bool = Serialized(default=True, shouldSerialize=False)

	def locatePosition(self, position: Position, end: Optional[Position] = None) -> None:
		self.cursorPosition = position.line, position.column
		if end is None:
			self.selectionProp.reset(self)
		else:
			self.selection = position.line, position.column, end.line, end.column
		self.forceLocate = True

	@property
	def unitedFilePath(self) -> str:
		return unitePath(self.filePath)

	@property
	def filePathForDisplay(self) -> str:
		return toDisplayPath(self.filePath)

	@property
	def fileName(self) -> str:
		filePathForDisplay = self.filePathForDisplay
		return os.path.split(filePathForDisplay)[1] if filePathForDisplay else 'untitled'

	@property
	def fileChanged(self) -> bool:
		"""Whether the file has changed on disk (and may need to be reloaded)."""
		return self._fileChangedHandler.fileChanged

	def _resetFileSystemChanged(self):
		self._fileChangedHandler.fileChanged = False

	__MISSING = object()
	def _resetDocumentChanged(self, content: TTarget = __MISSING):
		if content is Document.__MISSING:
			content = self.content
		self._originalContent = content
		# self.documentChanged = False

	def _setDocumentChanged(self):
		# self.documentChanged = True
		pass

	def parse(self, text: bytes) -> tuple[Optional[Node], Sequence[GeneralError]]:
		return None, []

	def validate(self) -> Sequence[GeneralError]:
		return []

	@utils.DeferredCallOnceMethod(delay=333)
	@utils.BusyIndicator
	def asyncParse(self, text: bytes = None) -> None:
		if text is None:
			text = self.content
		self.tree, self.parserErrors = self.parse(text)

	@utils.DeferredCallOnceMethod(delay=333)
	@utils.BusyIndicator
	def asyncValidate(self) -> None:
		self.validationErrors = self.validate()

	@utils.DeferredCallOnceMethod(delay=333)
	@utils.BusyIndicator
	def asyncParseNValidate(self) -> None:
		self.asyncParse.callNow()
		self.asyncValidate.callNow()

	@utils.DeferredCallOnceMethod(delay=333)
	def _asyncTakeSnapshot(self) -> None:
		# MUST be deferred with a delay > 0!
		self.undoRedoStack.takeSnapshotIfChanged(doDeepCopy=True)

	def toRepr(self):
		raise NotImplemented()

	def fromRepr(self, string):
		raise NotImplemented()

	def saveToFile(self):
		assert self.filePath
		logInfo("saving File in:{}".format(self.filePath))
		with open(self.unitedFilePath, 'w', encoding=self.encoding) as f:   # open file
			f.write(self.toRepr())
		self._resetDocumentChanged()
		self._resetFileSystemChanged()

	def loadFromText(self, text: str):
		self._resetFileSystemChanged()
		self._setDocumentChanged()
		self.fromRepr(text)

	def loadFromFile(self, archiveFilePool: ArchiveFilePool = None):
		assert self.filePath, "cannot load file from empty filePath"
		logInfo("loading File from:{}".format(self.filePath))
		self._resetFileSystemChanged()

		if archiveFilePool is None:
			with ZipFilePool() as zfp:
				self.fromRepr(loadTextFile(self.filePath, zfp, encoding=self.encoding))
		else:
			self.fromRepr(loadTextFile(self.filePath, archiveFilePool, encoding=self.encoding))
		self._resetDocumentChanged()
		return

	def discardFileSystemChanges(self):
		self._resetFileSystemChanged()
		self._setDocumentChanged()

	# def open(self):
	# 	self._rescheduleFileChangedHandler(self.filePath)

	def close(self):
		self._unscheduleFileChangedHandler(self.filePath)

	def __del__(self):
		self._unscheduleFileChangedHandler(self.filePath)


@RegisterDocument('text', ext=['.txt'])
@RegisterContainer
class TextDocument(Document):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(TextDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: bytes = b''
		self.strContent: str = ''

	def __init__(self):
		super().__init__()
		self._initUndoRedoStack(undoRedo.makesSnapshotMementoIfDiff)

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('Text', '.txt')])
	])
	content: bytes = Serialized(
		default=b'',
		decode=lambda s, v: bytes(v, encoding=s.encoding, errors='replace'),
		encode=lambda s, v: str(v, encoding=s.encoding, errors='replace'),
		shouldSerialize=True,
		decorators=[pd.NoUI()]
	)
	_originalContent: bytes = Serialized(
		getInitValue=lambda s: s.content,
		decode=lambda s, v: bytes(v, encoding=s.encoding, errors='replace') if isinstance(v, str) else v,
		encode=lambda s, v: str(v, encoding=s.encoding, errors='replace'),
		decorators=[pd.NoUI()]
	)

	@content.onSet
	def content(self, newVal: bytes, oldVal: Optional[bytes]) -> bytes:
		self.contentOnSet(newVal, oldVal)
		return newVal

	strContent: str = Transient(
		getter=lambda s: str(s.content, encoding=s.encoding, errors='replace'),
		setter=lambda s, v: s.contentProp.set(s, bytes(v, encoding=s.encoding, errors='replace')),
		shouldSerialize=False,
		decorators=[pd.NoUI()])

	def toRepr(self) -> str:
		return self.strContent

	def fromRepr(self, string: str):
		self.strContent = string


class ParsedDocument(TextDocument):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(ParsedDocument, self).__typeCheckerInfo___()
		self.tree: Optional[Node] = None
		# self.metaInfo: Optional[MetaInfo] = None

	# @ComputedCached(shouldSerialize=False)
	# def metaInfo(self) -> Optional[MetaInfo]:
	# 	return getMetaInfo(self.filePath, getSession().datapackData.structure)

	schemaId: Optional[str] = Serialized(default=None)

	@property
	def schema(self) -> Optional[Schema]:
		if self.schemaId is not None:
			return GLOBAL_SCHEMA_STORE.get2(self.schemaId, LanguageId(self.language))

	@property
	def parseKwArgs(self) -> dict[str, Any]:
		return {}

	@TimedMethod(enabled=True)
	def parse(self, text: bytes) -> tuple[Optional[Node], Sequence[GeneralError]]:
		try:
			schema = self.schema
			language = schema.language if schema is not None else self.language
			return parseNPrepare(text, filePath=self.filePath, language=language, schema=schema, **self.parseKwArgs)
		except Exception as e:
			logError(e)
			return None, [WrappedError(e)]

	@TimedMethod(enabled=True)
	def validate(self) -> Sequence[GeneralError]:
		errors = []
		try:
			if (tree := self.tree) is not None:
				ctxProvider = getContextProvider(tree, self.content)
				if ctxProvider is not None:
					ctxProvider.validateTree(errors)
			return errors
		except Exception as e:
			logError(e)
			return [WrappedError(e)]

