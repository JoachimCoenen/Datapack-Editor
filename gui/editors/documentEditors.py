import functools as ft
from dataclasses import replace
from typing import TypeVar, Generic, final, Optional, Type

from PyQt5.Qsci import QsciLexer
from PyQt5.QtCore import Qt, pyqtSignal

from Cat.CatPythonGUI.GUI import SizePolicy, getStyles, codeEditor
from Cat.CatPythonGUI.GUI.codeEditor import getLexer
from Cat.CatPythonGUI.GUI.pythonGUI import EditorBase
from Cat.utils import format_full_exc, override
from Cat.utils.abc_ import abstractmethod
from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclassOrEqual
from Cat.utils.formatters import indentMultilineStr
from Cat.utils.profiling import logError
from base.gui.documentLexer import DocumentLexerBase
from base.model.documents import TextDocument, Document, ParsedDocument
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.utils import LanguageId
from gui.datapackEditorGUI import DatapackEditorGUI, ContextMenuEntries, drawCodeField
from base.model.applicationSettings import applicationSettings

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

		with gui.vLayout(seamless=True):
			try:
				if applicationSettings.debugging.showUndoRedoPane:
					with gui.hSplitter() as splitter:
						with splitter.addArea(seamless=True):
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
				seamless=False,
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

		if document.isUntitled:
			gui.label('🖉', onCustomContextMenuRequested=fileContextMenu)

		gui.elidedLabel(
			document.filePathForDisplay,
			elideMode=Qt.ElideMiddle,
			sizePolicy=(SizePolicy.Maximum.value, SizePolicy.Fixed.value),
			contextMenuPolicy=Qt.CustomContextMenu,
			onCustomContextMenuRequested=fileContextMenu
		)
		if document.documentChanged:
			gui.label('*', style=getStyles().bold, onCustomContextMenuRequested=fileContextMenu)

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
	def onSetModel(self, new: TextDocument, old: Optional[TextDocument]) -> None:
		super(TextDocumentEditor, self).onSetModel(new, old)
		if new.tree is None:
			new.asyncParseNValidate()

	@override
	def documentGUI(self, gui: DatapackEditorGUI) -> None:
		self.codeEditorForDoc(gui, self.model())
		self.setFocusProxy(gui.lastTabWidget)

	@override
	def documentFooterGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()

		super(TextDocumentEditor, self).documentFooterGUI(gui)
		gui.addHSpacer(gui.spacing * 2, SizePolicy.Expanding)

		gui.hSeparator()
		indentation = document.indentationSettings
		tabLabel = f"Spaces: {indentation.tabWidth}" if indentation.useSpaces else f"Tab Width: {indentation.tabWidth}"
		gui.label(
			f"<div>{tabLabel}</div>",
			tip="Indentation Settings, Right-click to change",
			contextMenuPolicy=Qt.CustomContextMenu,
			onCustomContextMenuRequested=self.tabSettingsContextMenu
		)

		if isinstance(document, ParsedDocument):
			gui.hSeparator()
			gui.label(
				f"<div>{document.schemaId}</div>",
				tip="Schema, Right-click to change",
				contextMenuPolicy=Qt.CustomContextMenu,
				onCustomContextMenuRequested=self.schemaContextMenu
			)

		gui.hSeparator()
		gui.label(
			f"<div>{document.language}</div>",
			tip="Language, Right-click to change",
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
			onCursorPositionChanged=lambda a, b, d=document: _setCursorPos(a, b, d),
			onSelectionChanged2=lambda a1, b1, a2, b2, d=document: _setSelection(a1, b1, a2, b2, d),
			onFocusReceived=lambda fr: self.editorFocusReceived.emit(fr),
			focusPolicy=Qt.StrongFocus,
			autoIndent=autoIndent,
			caretLineVisible=False,
			tabWidth=document.indentationSettings.tabWidth,
			indentationsUseTabs=not document.indentationSettings.useSpaces,
			whitespaceVisibility=applicationSettings.appearance.whitespaceVisibility,
			**kwargs
		)

	def languageContextMenu(self, pos):
		document = self.model()
		with self._gui.popupMenu(True) as menu:
			for language in codeEditor.getAllLanguages():
				menu.addItem(language, lambda l=language: setattr(document, 'language', l) or document.asyncParseNValidate())

	def schemaContextMenu(self, pos):
		document = self.model()
		if isinstance(document, ParsedDocument):
			with self._gui.popupMenu(True) as menu:
				menu.addItem("None", lambda: setattr(document, 'schemaId', None) or document.asyncParseNValidate())
				for schemaId in GLOBAL_SCHEMA_STORE.getAllForLanguage(LanguageId(document.language)):
					menu.addItem(schemaId, lambda l=schemaId: setattr(document, 'schemaId', l) or document.asyncParseNValidate())

	def tabSettingsContextMenu(self, pos):
		document = self.model()
		indentation = document.indentationSettings
		with self._gui.popupMenu(True) as menu:
			for i in range(1, 8+1):
				menu.addItem(f"Tab Width: {i}", lambda t=i: setattr(document, 'indentationSettings', replace(indentation, tabWidth=t)), checkable=True, checked=indentation.tabWidth == i)
			menu.addSeparator()
			menu.addItem(f"Indent Using Spaces", lambda t=i: setattr(document, 'indentationSettings', replace(indentation, useSpaces=not indentation.useSpaces)), checkable=True, checked=indentation.useSpaces)
			menu.addSeparator()
			menu.addItem(f"ConvertIndentation", lambda t=i: document.convertIndentationsToUseTabsSettings())


def _setCursorPos(a, b, d: Document):
	d.cursorPosition = (a, b)


def _setSelection(a1, b1, a2, b2, d: Document):
	d.selection = (a1, b1, a2, b2)

__all__ = [
	'DocumentEditorBase',
	'getDocumentEditor'
	'TextDocumentEditor',
]
