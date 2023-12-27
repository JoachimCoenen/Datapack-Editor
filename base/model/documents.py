from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Collection, Optional, Sequence, Type, TypeVar

from watchdog.events import FileClosedEvent, FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent, FileSystemEventHandler

from base.model import filesystemEvents
from base.model.defaultSchemaProvider import getSchemaMapping
from base.model.parsing.contextProvider import getContextProvider, parseNPrepare
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Node, Schema
from base.model.pathUtils import ArchiveFilePool, FilePath, ZipFilePool, fileNameFromFilePath, loadTextFile, toDisplayPath, unitePath, unitePathTpl
from base.model.utils import GeneralError, LanguageId, Position, WrappedError
from cat import undoRedo
from cat.GUI import propertyDecorators as pd
from cat.GUI.components import codeEditor
from cat.GUI.enums import FileExtensionFilter
from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.undoRedo import MakeMementoIfDiffFunc, UndoRedoStack2
from cat.utils import utils
from cat.utils.logging_ import logWarning
from cat.utils.profiling import TimedMethod, logError, logInfo
from cat.utils.signals import CatSignal
from cat.utils.utils import runLaterSafe

_TTarget = TypeVar("_TTarget")


@dataclass
class ErrorCounts:
	errors: int = 0
	warnings: int = 0
	hints: int = 0

	@property
	def total(self) -> int:
		return self.errors + self.warnings + self.hints

	def __add__(self, other: ErrorCounts) -> ErrorCounts:
		if not isinstance(other, ErrorCounts):
			raise TypeError(f"unsupported operand type(s) for +: '{type(self)!r}' and '{type(other)!r}'")
		return ErrorCounts(
			self.errors + other.errors,
			self.warnings + other.warnings,
			self.hints + other.hints,
		)

	def __iadd__(self, other: ErrorCounts):
		if not isinstance(other, ErrorCounts):
			raise TypeError(f"unsupported operand type(s) for +=: '{type(self)!r}' and '{type(other)!r}'")
		self.errors += other.errors
		self.warnings += other.warnings
		self.hints += other.hints
		return self


def getErrorCounts(allErrors: Collection[GeneralError]) -> ErrorCounts:
	errorCounts = ErrorCounts()

	for error in allErrors:
		if error.style == 'error':
			errorCounts.errors += 1
		elif error.style == 'warning':
			errorCounts.warnings += 1
		elif error.style in {'hint', 'info'}:
			errorCounts.hints += 1
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
	defaultSchemaId: str = ''
	encoding: Optional[str] = None
	defaultContentFactory: Optional[Callable[[], bytes]] = None

	def __post_init__(self):
		suffixes = self.suffixesForDocTypeMatching
		if suffixes is None:
			suffixes = self.extensions
		self.suffixesForDocTypeMatching = sorted(suffixes, key=len, reverse=True)

	@property
	def fileExtensionFilter(self) -> FileExtensionFilter:
		return self.name, self.extensions

	def newDocument(self, *, observeFileSystem: bool = True) -> Document:
		kwArgs = {}
		if self.encoding is not None:
			kwArgs['encoding'] = self.encoding
		doc = self.type(language=self.defaultLanguage, schemaId=self.defaultSchemaId, _observeFileSystem=observeFileSystem, **kwArgs)
		if self.defaultContentFactory is not None:
			doc.content = self.defaultContentFactory()

		return doc

	def __eq__(self, other):
		return self is other

	def __ne__(self, other):
		return self is not other

	def __hash__(self):
		return id(self)

_documentTypes: list[DocumentTypeDescription] = []
_documentTypesByName: dict[str, DocumentTypeDescription] = {}


@dataclass
class RegisterDocument:
	name: str
	ext: list[str] = field(kw_only=True)
	suffixes: list[str] = None
	defaultLanguage: str = field(default='PlainText', kw_only=True)
	defaultSchemaId: str = field(default='', kw_only=True)
	encoding: Optional[str] = field(default=None, kw_only=True)
	icon: str = field(default=None, kw_only=True)
	tip: str = field(default=None, kw_only=True)
	defaultContentFactory: Optional[Callable[[], bytes]] = field(default=None, kw_only=True)

	def __post_init__(self):
		if self.suffixes is None:
			self.suffixes = self.ext

	def __call__(self, documentCls: Type[Document]):
		docTypeDescr = DocumentTypeDescription(
			type=documentCls,
			name=self.name,
			icon=self.icon,
			tip=self.tip,
			extensions=self.ext,
			suffixesForDocTypeMatching=sorted(self.suffixes, key=len, reverse=True),
			defaultLanguage=self.defaultLanguage,
			defaultSchemaId=self.defaultSchemaId,
			encoding=self.encoding,
			defaultContentFactory=self.defaultContentFactory,
		)
		registerDocumentTypeDescription(docTypeDescr)
		return documentCls


def registerDocumentTypeDescription(docTypeDescr: DocumentTypeDescription):
	assert issubclass(docTypeDescr.type, Document)
	assert docTypeDescr.type is not Document
	docName = docTypeDescr.name
	assert docName not in _documentTypesByName, f"A document type named '{docName}' is already registered ({_documentTypesByName[docName]})."
	_documentTypes.append(docTypeDescr)
	_documentTypesByName[docName] = docTypeDescr


def getDocumentTypes() -> list[DocumentTypeDescription]:
	return _documentTypes


def getDocTypeByName(name: str, default: Optional[DocumentTypeDescription] = None) -> Optional[DocumentTypeDescription]:
	return _documentTypesByName.get(name, default)


def _chooseDocumentTypeByFilePath(choices: Collection[DocumentTypeDescription], path: FilePath) -> Optional[DocumentTypeDescription]:
	fileName = fileNameFromFilePath(path).lower()
	bestDocTypeGuess: Optional[DocumentTypeDescription] = None
	bestDocTypeMatchQuality: int = 0
	for dt in choices:
		for suffix in dt.suffixesForDocTypeMatching:
			if fileName.endswith(suffix.lower()):
				if len(suffix) > bestDocTypeMatchQuality:
					bestDocTypeMatchQuality = len(suffix)
					bestDocTypeGuess = dt
					break
	return bestDocTypeGuess


def _chooseDocumentTypeByLanguage(choices: Collection[DocumentTypeDescription], languageId: LanguageId, schemaId: Optional[str]) -> Optional[DocumentTypeDescription]:
	bestDocTypeGuess: Optional[DocumentTypeDescription] = None
	bestDocTypeMatchQuality: int = -1
	for dt in choices:
		if dt.defaultLanguage == languageId:
			if dt.defaultSchemaId == schemaId:
				matchQuality = 3
			elif dt.defaultSchemaId is None:
				matchQuality = 2
			elif schemaId is None:
				matchQuality = 1
			else:
				matchQuality = 0
			if matchQuality > bestDocTypeMatchQuality:
				bestDocTypeMatchQuality = matchQuality
				bestDocTypeGuess = dt
	return bestDocTypeGuess


def getDocumentTypeForFilePath(path: FilePath, default: Optional[DocumentTypeDescription] = None) -> Optional[DocumentTypeDescription]:
	bestDocTypeGuess = _chooseDocumentTypeByFilePath(_documentTypes, path)
	return bestDocTypeGuess if bestDocTypeGuess is not None else default


_docTypeGuessers = [
	lambda guesses, allDocTypes, document: _chooseDocumentTypeByFilePath(guesses, document.filePath),
	lambda guesses, allDocTypes, document: _chooseDocumentTypeByFilePath(allDocTypes, document.filePath),
	lambda guesses, allDocTypes, document: _chooseDocumentTypeByLanguage(guesses, document.language, document.schemaId),
	lambda guesses, allDocTypes, document: _chooseDocumentTypeByLanguage(allDocTypes, document.language, document.schemaId),
	lambda guesses, allDocTypes, document: guesses[0] if guesses else None,
]


def getDocumentTypeForDocument(document: Document, default: Optional[DocumentTypeDescription] = None) -> Optional[DocumentTypeDescription]:
	allDocTypes = _documentTypes
	guesses: list[DocumentTypeDescription] = []
	documentCls = type(document)
	for dt in allDocTypes:
		if documentCls is dt.type:
			guesses.append(dt)

	bestDocTypeGuess = None
	for guesser in _docTypeGuessers:
		bestDocTypeGuess = guesser(guesses, allDocTypes, document)
		if bestDocTypeGuess is not None:
			break
	return bestDocTypeGuess if bestDocTypeGuess is not None else default


def loadDocument(filePath: FilePath, archiveFilePool: ArchiveFilePool = None, *, observeFileSystem: bool = True) -> Document:  # throws OSError
	docType = getDocumentTypeForFilePath(filePath, default=getDocTypeByName('text'))
	doc = docType.newDocument(observeFileSystem=observeFileSystem)
	doc.filePath = filePath
	doc.loadFromFile(archiveFilePool)
	return doc


def createNewDocument(docType: DocumentTypeDescription, filePath: Optional[FilePath], *, observeFileSystem: bool = True) -> Document:
	isUntitled = filePath is None
	if isUntitled:
		# find a new file name:
		from base.model.session import getSession
		filePath = getSession().documents._getNewUntitledFileName()
	# create document:
	doc = docType.newDocument()
	if isUntitled:
		doc.setUntitledFilePath(filePath)
	else:
		doc.filePath = filePath
	return doc


def getAllFileExtensionFilters(expanded: bool = False) -> Sequence[FileExtensionFilter]:
	if expanded:
		filters: list[FileExtensionFilter] = []
		for dt in _documentTypes:
			filterName, extensions = dt.fileExtensionFilter
			filters.extend([(filterName, f) for f in extensions])
		return filters
	else:
		return [dt.fileExtensionFilter for dt in _documentTypes]


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


@dataclass(repr=False, slots=True)
class Document(SerializableDataclass):

	def __post_init__(self):
		self._initUndoRedoStack(undoRedo.makesSnapshotMementoIfDiff)
		self.undoRedoStack: Optional[UndoRedoStack2] = None  # must be set with _initUndoRedoStack(...) in constructor of subclasses
		self._resetDocumentChanged()

	_filePath: FilePath = field(default='')
	_isUntitled: bool = field(default=False, kw_only=True)
	_observeFileSystem: bool = field(default=True, kw_only=True)
	_fileChangedHandler: FileChangedHandler = field(default_factory=FileChangedHandler, repr=False, metadata=catMeta(serialize=False))  # has no reference to self!

	@property
	def filePath(self) -> FilePath:
		return self._filePath

	@filePath.setter
	def filePath(self, filePath: FilePath):
		self._setFilePath(filePath, isUntitled=False)

	def setUntitledFilePath(self, filePath: str):
		self._setFilePath(filePath, isUntitled=True)

	def _setFilePath(self, filePath: FilePath, *, isUntitled: bool):
		oldPath = self._filePath
		self._filePath = filePath
		if isUntitled:
			self._unscheduleFileChangedHandler(oldPath)
		else:
			self._rescheduleFileChangedHandler(oldPath, filePath)
		self._isUntitled = isUntitled

		schemaMapping = getSchemaMapping(filePath, LanguageId(self.language))
		if schemaMapping is not None:
			self.schemaId = schemaMapping.schemaId

		self.onFilePathChanged(filePath, oldPath)

	def onFilePathChanged(self, newPath: FilePath, oldPath: FilePath):
		"""
		gets called whenever the filePath changes.
		:return: Nothing
		"""
		pass

	def _rescheduleFileChangedHandler(self, oldPath: FilePath, newPath: FilePath):
		if not self._observeFileSystem:
			return
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

	@property
	def _languageChoices(self):
		return codeEditor.getAllLanguages

	language: LanguageId = field(
		default='PlainText',
		metadata=catMeta(decorators=[pd.ComboBox(choices=_languageChoices)])
	)

	schemaId: Optional[str] = field(default=None)

	def _initUndoRedoStack(self, makeMementoIfDiff: MakeMementoIfDiffFunc[_TTarget]):
		self.undoRedoStack = UndoRedoStack2(self, 'content', makeMementoIfDiff, doDeepCopy=True)

	encoding: str = field(default='utf-8')
	_undoRedoStackInitialized: bool = field(default=False, metadata=catMeta(serialize=False))
	_content: _TTarget = field(default=None, metadata=catMeta(decorators=[pd.NoUI()]))

	@property
	def content(self) -> bytes:
		return self._content

	@content.setter
	def content(self, newVal: bytes) -> None:
		self.contentOnSet(newVal, self._content)
		self._content = newVal

	_originalContent: Optional[_TTarget] = field(default=None, metadata=catMeta(decorators=[pd.NoUI()]))

	tree: Optional[Node] = field(default=None, repr=False, metadata=catMeta(serialize=False))

	def contentOnSet(self, newVal: bytes, oldVal: Optional[bytes]) -> None:
		if not self._undoRedoStackInitialized:
			# do take a snapshot to initialize the undoRedoStack:
			self.undoRedoStack.takeSnapshotIfChanged()
			self._undoRedoStackInitialized = True

		if newVal == oldVal:
			return
		self.asyncParse.callNow(newVal)
		self.asyncValidate()
		# self.asyncParseNValidate()

		self._setDocumentChanged()

		if self.undoRedoStack.isUndoingOrRedoing:
			self._asyncTakeSnapshot.cancelPending()
			return

		self._asyncTakeSnapshot()

	highlightErrors: bool = field(default=True)
	onErrorsChanged: ClassVar[CatSignal[Callable[[Document], None]]] = CatSignal('onErrorsChanged')
	_parserErrors: list[GeneralError] = field(default_factory=list, repr=False, metadata=catMeta(serialize=False))
	_validationErrors: list[GeneralError] = field(default_factory=list, repr=False, metadata=catMeta(serialize=False))
	# validationErrors: Sequence[GeneralError] = Serialized(getInitValue=lambda s: s.validate(), shouldSerialize=False)

	@property
	def parserErrors(self) -> list[GeneralError]:
		return self._parserErrors

	@parserErrors.setter
	def parserErrors(self, newVal: list[GeneralError]):
		if newVal != self._parserErrors:
			self._parserErrors = newVal
			runLaterSafe(0, lambda s=self: s.onErrorsChanged.emit(s))

	@property
	def validationErrors(self) -> list[GeneralError]:
		return self._validationErrors

	@validationErrors.setter
	def validationErrors(self, newVal: list[GeneralError]):
		if newVal != self._validationErrors:
			self._validationErrors = newVal
			runLaterSafe(0, lambda s=self: s.onErrorsChanged.emit(s))

	@property
	def errors(self) -> list[GeneralError]:
		return self.parserErrors + self.validationErrors

	cursorPosition: tuple[int, int] = field(default=(0, 0))
	selection: tuple[int, int, int, int] = field(default=(-1, -1, -1, -1))
	hasSelection: bool = property(lambda self: self.selection != (-1, -1, -1, -1))
	forceLocate: bool = field(default=True, repr=False, metadata=catMeta(serialize=False))

	def locatePosition(self, position: Position, end: Optional[Position] = None) -> None:
		self.cursorPosition = position.line, position.column
		if end is None:
			self.selection = (-1, -1, -1, -1)
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
	def isUntitled(self) -> bool:
		"""aka. Document.isNew, Whether the document is new and needs a path before saving. (Save As instead of Save)"""
		return self._isUntitled

	@property
	def isNew(self) -> bool:
		"""aka. Document.isUntitled, Whether the document is new and needs a path before saving. (Save As instead of Save)"""
		return self.isUntitled

	@property
	def documentChanged(self) -> bool:
		"""Whether the document has been changed (and may need to be saved)."""
		return self.content != self._originalContent

	@property
	def fileChanged(self) -> bool:
		"""Whether the file has changed on disk (and may need to be reloaded)."""
		return self._fileChangedHandler.fileChanged

	def _resetFileSystemChanged(self):
		self._fileChangedHandler.fileChanged = False

	__MISSING = object()

	def _resetDocumentChanged(self, content: _TTarget = __MISSING):
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
		self.undoRedoStack.takeSnapshotIfChanged()

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

	def __hash__(self):
		return hash(id(self)) + 91537523


@dataclass(frozen=True)
class IndentationSettings(SerializableDataclass):
	tabWidth: int = 4
	useSpaces: bool = False


@RegisterDocument('text', ext=['.txt'])
@dataclass(repr=False, slots=True)
class TextDocument(Document):

	def __post_init__(self):
		super(TextDocument, self).__post_init__()
		self._initUndoRedoStack(undoRedo.makesSnapshotMementoIfDiff)

	_content: bytes = field(
		default=b'',
		metadata=catMeta(
			decode=lambda s, v: bytes(v, encoding=s.encoding, errors='replace'),
			encode=lambda s, v: str(v, encoding=s.encoding, errors='replace'),
			deferLoading=True,
			decorators=[pd.NoUI()]
		)
	)
	_originalContent: Optional[bytes] = field(
		default=None,
		metadata=catMeta(
			decode=lambda s, v: bytes(v, encoding=s.encoding, errors='replace') if isinstance(v, str) else v,
			encode=lambda s, v: str(v, encoding=s.encoding, errors='replace'),
			deferLoading=True,
			decorators=[pd.NoUI()]
		)
	)

	indentationSettings: IndentationSettings = field(
		default_factory=IndentationSettings,
		metadata=catMeta(
			deferLoading=True,
			decorators=[pd.NoUI()]
		)
	)

	@property
	def strContent(self) -> str:
		return str(self.content, encoding=self.encoding, errors='replace')

	@strContent.setter
	def strContent(self, value: str):
		self.content = bytes(value, encoding=self.encoding, errors='replace')

	def toRepr(self) -> str:
		return self.strContent

	def fromRepr(self, string: str):
		self.strContent = string

	def __hash__(self):
		return hash(id(self)) + 91537522

	def convertIndentationsToUseTabsSettings(self):
		lines = self.content.split(b'\n')
		oldTab, newTab = b' '*self.indentationSettings.tabWidth, b'\t'
		toTabs = oldTab, newTab
		fromTabs = newTab, oldTab
		useSpaces = self.indentationSettings.useSpaces

		pattern = re.compile(rb'^(\s*)(.*)')
		pattern2 = re.compile(rb'[^\t]+\t')
		newLines = []
		for line in lines:
			match = pattern.match(line)
			indent, trailing = match.group(1, 2)
			# indent = match.group(1)
			# trailing = match.group(2)

			# 1. convert everything to tabs
			indent2 = indent.replace(*toTabs)

			# 2. Fix superfluous spaces
			#    This ensures correct handling of too few spaces before a tab.
			indent3 = pattern2.sub(b'\t', indent2)

			# 3. convert back to spaces, if necessary.
			if useSpaces:
				indent3 = indent3.replace(*fromTabs)

			newLines.append(indent3 + trailing)

		text = b'\n'.join(newLines)
		self.content = text


@dataclass(repr=False, slots=True)
class ParsedDocument(TextDocument):

	def __post_init__(self):
		super(ParsedDocument, self).__post_init__()

	@property
	def schema(self) -> Optional[Schema]:
		if self.schemaId is not None:
			return GLOBAL_SCHEMA_STORE.get(self.schemaId, LanguageId(self.language))

	@property
	def parseKwArgs(self) -> dict[str, Any]:
		return {}

	@TimedMethod(enabled=True)
	def parse(self, text: bytes) -> tuple[Optional[Node], Sequence[GeneralError]]:
		try:
			schema = self.schema
			language = schema.language if schema is not None else self.language
			node, errors, parser = parseNPrepare(text, filePath=self.filePath, language=language, schema=schema, **self.parseKwArgs)
			return node, errors
		except Exception as e:
			logError(e)
			return None, [WrappedError(e, style='info')]

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
			return [WrappedError(e, style='info')]

	def __hash__(self):
		return hash(id(self)) + 91537521
