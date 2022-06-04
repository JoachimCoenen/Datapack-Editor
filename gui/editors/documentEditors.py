import functools as ft
from typing import TypeVar, Generic, final, Optional, Type

from PyQt5.Qsci import QsciLexer
from PyQt5.QtCore import Qt, pyqtSignal

from Cat.CatPythonGUI.GUI import NO_MARGINS, SizePolicy, getStyles, codeEditor, adjustOverlap, maskCorners, CORNERS
from Cat.CatPythonGUI.GUI.codeEditor import getLexer
from Cat.CatPythonGUI.GUI.pythonGUI import EditorBase
from Cat.utils import format_full_exc, override
from Cat.utils.abc_ import abstractmethod
from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclassOrEqual
from Cat.utils.formatters import indentMultilineStr
from Cat.utils.profiling import logError
from gui.lexers.documentLexer import DocumentLexerBase
from session.documents import TextDocument, Document
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries, drawCodeField
from settings import applicationSettings

TDoc = TypeVar('TDoc', bound=Document)


class DocumentEditorBase(EditorBase[TDoc], Generic[TDoc]):
	editorFocusReceived = pyqtSignal(Qt.FocusReason)

	def onSetModel(self, new: TDoc, old: Optional[TDoc]) -> None:
		super(DocumentEditorBase, self).onSetModel(new, old)
		self._gui._name = f"'<{type(new).__name__} at 0x{id(new):x}>'"
		self._gui._name = f"'<{type(new).__name__} at {{{new.fileName}}}>'"
		if old is not None:
			old.onErrorsChanged.disconnect('editorRedraw')
		new.onErrorsChanged.reconnect('editorRedraw', lambda d: self.redrawLater('onErrorsChanged'))


	@final
	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()

		with gui.vLayout(verticalSpacing=0):
			try:
				if applicationSettings.debugging.showUndoRedoPane:
					with gui.hSplitter() as splitter:
						with splitter.addArea(contentsMargins=NO_MARGINS):
							self.documentGUI(gui)
						with splitter.addArea():
							gui.valueField(document.undoRedoStack)
				else:
					self.documentGUI(gui)

			except Exception as e:
				logError(f'{e}:\n{indentMultilineStr(format_full_exc(), indent="  ")} ')
				gui.helpBox(f'cannot draw document: {e}')
				gui.button('retry')  # pressing causes a gui update & redraw

			# footer:
			space = int(3 * gui.scale) + 1
			mg = gui.smallPanelMargin
			#with gui.hLayout(contentsMargins=(mg, 0, mg, space)):
			with gui.hPanel(
				windowPanel=True,
				contentsMargins=(mg, mg, mg, mg),
				#contentsMargins=(mg, 0, mg, space),
				overlap=adjustOverlap(self.overlap(), (None, 1, None, None)),
				roundedCorners=maskCorners(self.roundedCorners(), CORNERS.BOTTOM),
				cornerRadius=self.cornerRadius(),
			):
				self.documentFooterGUI(gui)

	@abstractmethod
	def documentGUI(self, gui: DatapackEditorGUI) -> None:
		raise NotImplementedError()

	def documentFooterGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()

		def fileContextMenu(pos):
			with gui.popupMenu(True) as menu:
				menu.addItems(ContextMenuEntries.pathItems(document.filePath))

		gui.elidedLabel(
			document.filePathForDisplay,
			elideMode=Qt.ElideMiddle,
			sizePolicy=(SizePolicy.Maximum.value, SizePolicy.Fixed.value),
			contextMenuPolicy=Qt.CustomContextMenu,
			onCustomContextMenuRequested=fileContextMenu
		)
		if document.documentChanged:
			gui.label('*', style=getStyles().bold)

		self.checkForFileSystemChanges(gui)

	def checkForFileSystemChanges(self, gui: DatapackEditorGUI) -> None:
		document = self.model()
		if document.fileChanged:
			reloadFile: bool = not document.documentChanged
			if not reloadFile:
				reloadFile = gui.askUser(
					f'{document.fileName} has changed on disk',
					f"Do you want to reload it?"
				)
			if reloadFile:
				document.loadFromFile()
			else:
				document.discardFileSystemChanges()


TDocumentEditorBase = TypeVar('TDocumentEditorBase', bound=DocumentEditorBase)


__documentEditors: dict[Type[Document], Type[TDocumentEditorBase]] = {}
documentEditor = AddToDictDecorator(__documentEditors)
getDocumentEditor = ft.partial(getIfKeyIssubclassOrEqual, __documentEditors)


@documentEditor(TextDocument)
class TextDocumentEditor(DocumentEditorBase[TextDocument]):

	@override
	def postInit(self):
		super(TextDocumentEditor, self).postInit()
		self._currentLexer: Optional[QsciLexer] = None
		self.redraw('TextDocumentEditor.postInit(...)')  # force a second redraw!

	@override
	def documentGUI(self, gui: DatapackEditorGUI) -> None:
		self.codeEditorForDoc(gui, self.model())
		self.setFocusProxy(gui.lastTabWidget)

	@override
	def documentFooterGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()

		super(TextDocumentEditor, self).documentFooterGUI(gui)
		gui.addHSpacer(gui.spacing * 2, SizePolicy.Expanding)

		gui.label(
			f"<div>{document.language}</div>",
			tip="Right-click to change",
			contextMenuPolicy=Qt.CustomContextMenu,
			onCustomContextMenuRequested=self.languageContextMenu
		)

	def codeEditorForDoc(self, gui: DatapackEditorGUI, document: TextDocument, *, autoIndent: bool = True, **kwargs) -> None:
		if document.highlightErrors:
			errors = [error for error in document.errors if error.position is not None and error.end is not None]
		else:
			errors = []

		lexerCls = getLexer(document.language)
		if type(self._currentLexer) is lexerCls:
			lexer = self._currentLexer
		else:
			if lexerCls is None:
				lexer = None
			else:
				lexer = lexerCls(self)
			self._currentLexer = lexer
		if isinstance(lexer, DocumentLexerBase):
			lexer.setDocument(document)

		document.strContent, document.highlightErrors, document.cursorPosition, document.forceLocate = drawCodeField(
			gui,
			document.strContent,
			lexer=lexer,
			errors=errors,
			forceLocateElement=True,
			currentCursorPos=document.cursorPosition,
			selectionTo=document.selection[2:] if document.selection[0] != -1 else None,
			highlightErrors=document.highlightErrors,
			onCursorPositionChanged=lambda a, b, d=document: type(d).cursorPosition.set(d, (a, b)),
			onSelectionChanged2=lambda a1, b1, a2, b2, d=document: type(d).selection.set(d, (a1, b1, a2, b2)),
			onFocusReceived=lambda fr: self.editorFocusReceived.emit(fr),
			focusPolicy=Qt.StrongFocus,
			autoIndent=autoIndent,
			**kwargs
		)

	def languageContextMenu(self, pos):
		document = self.model()
		with self._gui.popupMenu(True) as menu:
			for language in codeEditor.getAllLanguages():
				menu.addItem(language, lambda l=language: document.languageProp.set(document, l))


__all__ = [
	'DocumentEditorBase',
	'getDocumentEditor'
	'TextDocumentEditor',
]
