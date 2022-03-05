from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional, Type, Sequence, Callable, TypeVar, Collection, Any

from PyQt5.QtCore import QTimer

from Cat import undoRedo
from Cat.CatPythonGUI.GUI import codeEditor
from Cat.Serializable import Computed, RegisterContainer, Serialized, SerializableContainer, ComputedCached
from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.extensions.fileSystemChangedDependency import SingleFileChangedDependencyProperty
from Cat.undoRedo import UndoRedoStack2, MakeMementoIfDiffFunc
from Cat.utils import utils, Decorator
from Cat.utils.profiling import logInfo, logError

from Cat.utils.signals import CatSignal
from model.pathUtils import fileNameFromFilePath, FilePath, getMTimeForFilePath, ZipFilePool, loadTextFile, ArchiveFilePool
from model.utils import GeneralError, Position

TTarget = TypeVar("TTarget")


def getFilePathForDisplay(filePath: FilePath) -> str:
	filePath = filePath
	if isinstance(filePath, str):
		return filePath
	else:
		if filePath[0] and not filePath[0].endswith('/') and filePath[1] and not filePath[1].startswith('/'):
			return f'{filePath[0]}/{filePath[1]}'
		else:
			return f'{filePath[0]}{filePath[1]}'


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


@RegisterContainer
class DocumentTypeDescription(SerializableContainer):
	__slots__ = ()
	type: Type[Document] = Serialized(default=None)
	name: str = Serialized(default='')
	icon: Optional[str] = Serialized(default=None)
	tip: Optional[str] = Serialized(default=None)
	extensions: list[str] = Serialized(default_factory=list)
	suffixesForDocTypeMatching: list[str] = Serialized(default_factory=list)
	defaultLanguage: str = Serialized(default='PlainText')

	def newDocument(self) -> Document:
		return self.type.create(language=self.defaultLanguage)

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
		assert issubclass(documentCls, Document)
		assert not documentCls is Document
		docTypeDescr = DocumentTypeDescription.create(
			type=documentCls,
			name=self._documentName,
			icon=self._icon,
			tip=self._tip,
			extensions=self._extensions,
			suffixesForDocTypeMatching=sorted(self._suffixesForDocTypeMatching, key=len, reverse=True),
			defaultLanguage=self._defaultLanguage
		)
		docName = docTypeDescr.name
		assert docName not in _documentTypesByName, f"A document type named '{docName}' is already registered ({_documentTypesByName[docName]})."
		_documentTypes.append(docTypeDescr)
		_documentTypesByName[docName] = docTypeDescr
		return documentCls


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


@RegisterContainer
class Document(SerializableContainer):
	__slots__ = ('undoRedoStack', 'inUndoRedoMode')
	"""docstring for Document"""
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self._lastFileMTime: float = 0.
		self._currentFileMTime: float = 0.
		self.fileChanged: bool = False
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

	filePath: FilePath = Serialized(default='')
	language: str = Serialized(default='PlainText', decorators=[pd.ComboBox(choices=Computed(default_factory=codeEditor.getAllLanguages))])

	def _initUndoRedoStack(self, makeMementoIfDiff: MakeMementoIfDiffFunc[TTarget]):
		self.undoRedoStack = UndoRedoStack2(self, self.contentProp, makeMementoIfDiff)

	@Computed()
	def documentChanged(self) -> bool:
		"""Whether the document has been changed (and may need to be saved)."""
		return self.content != self._originalContent

	encoding: str = Serialized(default='utf-8')
	_contentVersion: int = Serialized(default=0, shouldSerialize=False, decorators=[pd.NoUI()])
	content: TTarget = Serialized(default=None, decorators=[pd.NoUI()])
	_originalContent: TTarget = Serialized(getInitValue=lambda s: s.content, decorators=[pd.NoUI()])

	@content.onSet
	def content(self, newVal: str, oldVal: Optional[str]) -> str:
		self.contentOnSet(newVal, oldVal)
		return newVal

	def contentOnSet(self, newVal: str, oldVal: Optional[str]) -> None:
		if self._contentVersion == 0:
			# do take a snapshot to initialize the undoRedoStack:
			self.undoRedoStack.takeSnapshotIfChanged(doDeepCopy=True)

		if newVal == oldVal:
			return

		self._setDocumentChanged()
		self._contentVersion += 1

		if self.inUndoRedoMode:
			return

		self._asyncTakeSnapshot()

		self.asyncValidate()

	@utils.DeferredCallOnceMethod(delay=333)
	def _asyncTakeSnapshot(self) -> None:
		# MUST be deferred with a delay > 0!
		self.undoRedoStack.takeSnapshotIfChanged(doDeepCopy=True)

	@utils.DeferredCallOnceMethod(delay=333)
	@utils.BusyIndicator
	def asyncValidate(self) -> None:
		self.errors = self.validate()

	def validate(self) -> Sequence[GeneralError]:
		return []

	# TODO: def parse(self) -> Sequence[GeneralError]:
	# 	return []

	highlightErrors: bool = Serialized(default=True)

	errors: Sequence[GeneralError] = Serialized(getInitValue=lambda s: s.validate(), shouldSerialize=False)

	@errors.onSet
	def errors(self, newVal: Sequence[GeneralError], oldVal: Optional[Sequence[GeneralError]]) -> Sequence[GeneralError]:
		if newVal != oldVal:
			QTimer.singleShot(0, lambda self=self: self.onErrorsChanged.emit(self))
		return newVal

	onErrorsChanged: CatSignal[Callable[[Document], None]] = CatSignal('onErrorsChanged')

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

	@Computed()
	def filePathForDisplay(self) -> str:
		return getFilePathForDisplay(self.filePath)

	@Computed()
	def fileName(self) -> str:
		filePathForDisplay = self.filePathForDisplay
		return os.path.split(filePathForDisplay)[1] if filePathForDisplay else 'untitled'

	@Computed()
	def fileLocationAbsolute(self) -> FilePath:
		"""The directory of the file"""
		filePath = self.filePath
		if isinstance(filePath, str):
			return os.path.split(filePath)[0] if filePath else ''
		else:
			return filePath[0], os.path.split(filePath[1])[0] if filePath[1] else ''

	_lastFileMTime: float = Serialized(default=0.)

	@ComputedCached(dependencies_=[SingleFileChangedDependencyProperty(filePath.map(lambda fp: fp if isinstance(fp, str) else (os.path.join(*fp) if os.path.isdir(fp[0]) else fp[0]), str))])
	def _currentFileMTime(self) -> float:
		try:
			return getMTimeForFilePath(self.filePath)
		except OSError:
			return 0.

	@ComputedCached(dependencies_=[_currentFileMTime])
	def fileChanged(self) -> bool:
		"""Whether the file has changed on disk (and may need to be reloaded)."""
		if self._currentFileMTime != self._lastFileMTime:
			try:
				with ZipFilePool() as zfp:
					txt = loadTextFile(self.filePath, zfp, encoding=self.encoding)
				return self.toRepr() != txt
			except OSError:
				return False
		else:
			return False

	def _resetFileSystemChanged(self):
		self._lastFileMTime = self._currentFileMTime
		self.fileChangedProp.setCachedValue(self, False)

	__MISSING = object()
	def _resetDocumentChanged(self, content: TTarget = __MISSING):
		if content is Document.__MISSING:
			content = self.content
		self._originalContent = content
		# self.documentChanged = False

	#@Deprecated(msg='')
	def _setDocumentChanged(self):
		# self.documentChanged = True
		pass

	def toRepr(self):
		raise NotImplemented()

	def fromRepr(self, string):
		raise NotImplemented()

	def saveToFile(self):
		assert self.filePath
		logInfo("saving File in:{}".format(self.filePath))
		with open(self.filePathForDisplay, 'w', encoding=self.encoding) as f:   # open file
			f.write(self.toRepr())
		self._resetFileSystemChanged()
		self._resetDocumentChanged()

	def loadFromText(self, text: str):
		self._resetFileSystemChanged()
		self._setDocumentChanged()
		self.fromRepr(text)

	def loadFromFile(self, archiveFilePool: ArchiveFilePool = None):
		assert(self.filePath)
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


@RegisterDocument('text', ext=['.txt'])
@RegisterContainer
class TextDocument(Document):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(TextDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: str = ''

	def __init__(self):
		super().__init__()
		self._initUndoRedoStack(undoRedo.makesSnapshotMementoIfDiff)

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('Text', '.txt')])
	])
	content: str = Serialized(default='', decorators=[pd.NoUI()])
	_originalContent: str = Serialized(getInitValue=lambda s: s.content, decorators=[pd.NoUI()])

	tree: Optional[Any] = Serialized(default=None, shouldSerialize=False, shouldPrint=False, decorators=[pd.NoUI()])

	@content.onSet
	def content(self, newVal: str, oldVal: Optional[str]) -> str:
		self.contentOnSet(newVal, oldVal)
		return newVal

	def toRepr(self) -> str:
		return self.content

	def fromRepr(self, string):
		self.content = string
