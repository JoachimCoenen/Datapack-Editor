from typing import TypeVar, Generic, final, Optional

from PyQt5.QtCore import Qt, QEvent, pyqtSignal

from Cat.CatPythonGUI.GUI import NO_MARGINS, SizePolicy, getStyles
from Cat.utils import format_full_exc, override
from Cat.utils.abc_ import abstractmethod
from Cat.utils.formatters import indentMultilineStr
from Cat.utils.profiling import logError
from session.documents import TextDocument, Document
from gui.datapackEditorGUI import EditorBase, DatapackEditorGUI, ContextMenuEntries, drawCodeField
from settings import applicationSettings

TDoc = TypeVar('TDoc', bound=Document)


class DocumentEditorBase(EditorBase[TDoc], Generic[TDoc]):
	editorFocusReceived = pyqtSignal(Qt.FocusReason)

	def onSetModel(self, new: TDoc, old: Optional[TDoc]) -> None:
		super(DocumentEditorBase, self).onSetModel(new, old)
		if old is not None:
			old.onErrorsChanged.disconnect('editorRedraw')
		new.onErrorsChanged.disconnect('editorRedraw')
		new.onErrorsChanged.connect('editorRedraw', lambda d: self.redraw())

	@final
	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()
		if applicationSettings.debugging.showUndoRedoPane:
			with gui.hSplitter() as splitter:
				with splitter.addArea(contentsMargins=NO_MARGINS):
					self.documentGUI(gui)
				with splitter.addArea():
					gui.valueField(document.undoRedoStack)
		else:
			self.documentGUI(gui)
		# footer:
		space = int(3 * gui._scale) + 1
		mg = gui.smallPanelMargin
		with gui.hLayout(contentsMargins=(mg, 0, mg, space)):
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
			# textInteractionFlags=Qt.TextSelectableByMouse | Qt.LinksAcces	sibleByMouse,
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


_qEventMap = {
	QEvent.None_: 'None_', QEvent.Timer: 'Timer', QEvent.MouseButtonPress: 'MouseButtonPress',
	QEvent.MouseButtonRelease: 'MouseButtonRelease', QEvent.MouseButtonDblClick: 'MouseButtonDblClick', QEvent.MouseMove: 'MouseMove',
	QEvent.KeyPress: 'KeyPress', QEvent.KeyRelease: 'KeyRelease', QEvent.FocusIn: 'FocusIn',
	QEvent.FocusOut: 'FocusOut', QEvent.Enter: 'Enter', QEvent.Leave: 'Leave',
	QEvent.Paint: 'Paint', QEvent.Move: 'Move', QEvent.Resize: 'Resize',
	QEvent.Show: 'Show', QEvent.Hide: 'Hide', QEvent.Close: 'Close',
	QEvent.ParentChange: 'ParentChange', QEvent.ParentAboutToChange: 'ParentAboutToChange', QEvent.ThreadChange: 'ThreadChange',
	QEvent.WindowActivate: 'WindowActivate', QEvent.WindowDeactivate: 'WindowDeactivate', QEvent.ShowToParent: 'ShowToParent',
	QEvent.HideToParent: 'HideToParent', QEvent.Wheel: 'Wheel', QEvent.WindowTitleChange: 'WindowTitleChange',
	QEvent.WindowIconChange: 'WindowIconChange', QEvent.ApplicationWindowIconChange: 'ApplicationWindowIconChange', QEvent.ApplicationFontChange: 'ApplicationFontChange',
	QEvent.ApplicationLayoutDirectionChange: 'ApplicationLayoutDirectionChange', QEvent.ApplicationPaletteChange: 'ApplicationPaletteChange', QEvent.PaletteChange: 'PaletteChange',
	QEvent.Clipboard: 'Clipboard', QEvent.MetaCall: 'MetaCall', QEvent.SockAct: 'SockAct',
	QEvent.WinEventAct: 'WinEventAct', QEvent.DeferredDelete: 'DeferredDelete', QEvent.DragEnter: 'DragEnter',
	QEvent.DragMove: 'DragMove', QEvent.DragLeave: 'DragLeave', QEvent.Drop: 'Drop',
	QEvent.ChildAdded: 'ChildAdded', QEvent.ChildPolished: 'ChildPolished', QEvent.ChildRemoved: 'ChildRemoved',
	QEvent.PolishRequest: 'PolishRequest', QEvent.Polish: 'Polish', QEvent.LayoutRequest: 'LayoutRequest',
	QEvent.UpdateRequest: 'UpdateRequest', QEvent.UpdateLater: 'UpdateLater', QEvent.ContextMenu: 'ContextMenu',
	QEvent.InputMethod: 'InputMethod', QEvent.TabletMove: 'TabletMove', QEvent.LocaleChange: 'LocaleChange',
	QEvent.LanguageChange: 'LanguageChange', QEvent.LayoutDirectionChange: 'LayoutDirectionChange', QEvent.TabletPress: 'TabletPress',
	QEvent.TabletRelease: 'TabletRelease', QEvent.OkRequest: 'OkRequest', QEvent.IconDrag: 'IconDrag',
	QEvent.FontChange: 'FontChange', QEvent.EnabledChange: 'EnabledChange', QEvent.ActivationChange: 'ActivationChange',
	QEvent.StyleChange: 'StyleChange', QEvent.IconTextChange: 'IconTextChange', QEvent.ModifiedChange: 'ModifiedChange',
	QEvent.MouseTrackingChange: 'MouseTrackingChange', QEvent.WindowBlocked: 'WindowBlocked', QEvent.WindowUnblocked: 'WindowUnblocked',
	QEvent.WindowStateChange: 'WindowStateChange', QEvent.ToolTip: 'ToolTip', QEvent.WhatsThis: 'WhatsThis',
	QEvent.StatusTip: 'StatusTip', QEvent.ActionChanged: 'ActionChanged', QEvent.ActionAdded: 'ActionAdded',
	QEvent.ActionRemoved: 'ActionRemoved', QEvent.FileOpen: 'FileOpen', QEvent.Shortcut: 'Shortcut',
	QEvent.ShortcutOverride: 'ShortcutOverride', QEvent.WhatsThisClicked: 'WhatsThisClicked', QEvent.ToolBarChange: 'ToolBarChange',
	QEvent.ApplicationActivate: 'ApplicationActivate', QEvent.ApplicationActivated: 'ApplicationActivated', QEvent.ApplicationDeactivate: 'ApplicationDeactivate',
	QEvent.ApplicationDeactivated: 'ApplicationDeactivated', QEvent.QueryWhatsThis: 'QueryWhatsThis', QEvent.EnterWhatsThisMode: 'EnterWhatsThisMode',
	QEvent.LeaveWhatsThisMode: 'LeaveWhatsThisMode', QEvent.ZOrderChange: 'ZOrderChange', QEvent.HoverEnter: 'HoverEnter',
	QEvent.HoverLeave: 'HoverLeave', QEvent.HoverMove: 'HoverMove', QEvent.GraphicsSceneMouseMove: 'GraphicsSceneMouseMove',
	QEvent.GraphicsSceneMousePress: 'GraphicsSceneMousePress', QEvent.GraphicsSceneMouseRelease: 'GraphicsSceneMouseRelease',
	QEvent.GraphicsSceneMouseDoubleClick: 'GraphicsSceneMouseDoubleClick',
	QEvent.GraphicsSceneContextMenu: 'GraphicsSceneContextMenu', QEvent.GraphicsSceneHoverEnter: 'GraphicsSceneHoverEnter', QEvent.GraphicsSceneHoverMove: 'GraphicsSceneHoverMove',
	QEvent.GraphicsSceneHoverLeave: 'GraphicsSceneHoverLeave', QEvent.GraphicsSceneHelp: 'GraphicsSceneHelp', QEvent.GraphicsSceneDragEnter: 'GraphicsSceneDragEnter',
	QEvent.GraphicsSceneDragMove: 'GraphicsSceneDragMove', QEvent.GraphicsSceneDragLeave: 'GraphicsSceneDragLeave', QEvent.GraphicsSceneDrop: 'GraphicsSceneDrop',
	QEvent.GraphicsSceneWheel: 'GraphicsSceneWheel', QEvent.GraphicsSceneResize: 'GraphicsSceneResize', QEvent.GraphicsSceneMove: 'GraphicsSceneMove',
	QEvent.KeyboardLayoutChange: 'KeyboardLayoutChange', QEvent.DynamicPropertyChange: 'DynamicPropertyChange', QEvent.TabletEnterProximity: 'TabletEnterProximity',
	QEvent.TabletLeaveProximity: 'TabletLeaveProximity', QEvent.NonClientAreaMouseMove: 'NonClientAreaMouseMove',
	QEvent.NonClientAreaMouseButtonPress: 'NonClientAreaMouseButtonPress',
	QEvent.NonClientAreaMouseButtonRelease: 'NonClientAreaMouseButtonRelease', QEvent.NonClientAreaMouseButtonDblClick: 'NonClientAreaMouseButtonDblClick',
	QEvent.MacSizeChange: 'MacSizeChange',
	QEvent.ContentsRectChange: 'ContentsRectChange', QEvent.CursorChange: 'CursorChange', QEvent.ToolTipChange: 'ToolTipChange',
	QEvent.GrabMouse: 'GrabMouse', QEvent.UngrabMouse: 'UngrabMouse', QEvent.GrabKeyboard: 'GrabKeyboard',
	QEvent.UngrabKeyboard: 'UngrabKeyboard', QEvent.StateMachineSignal: 'StateMachineSignal', QEvent.StateMachineWrapped: 'StateMachineWrapped',
	QEvent.TouchBegin: 'TouchBegin', QEvent.TouchUpdate: 'TouchUpdate', QEvent.TouchEnd: 'TouchEnd',
	QEvent.RequestSoftwareInputPanel: 'RequestSoftwareInputPanel', QEvent.CloseSoftwareInputPanel: 'CloseSoftwareInputPanel', QEvent.WinIdChange: 'WinIdChange',
	QEvent.Gesture: 'Gesture', QEvent.GestureOverride: 'GestureOverride', QEvent.FocusAboutToChange: 'FocusAboutToChange',
	QEvent.ScrollPrepare: 'ScrollPrepare', QEvent.Scroll: 'Scroll', QEvent.Expose: 'Expose',
	QEvent.InputMethodQuery: 'InputMethodQuery', QEvent.OrientationChange: 'OrientationChange', QEvent.TouchCancel: 'TouchCancel',
	QEvent.PlatformPanel: 'PlatformPanel', QEvent.ApplicationStateChange: 'ApplicationStateChange', QEvent.ReadOnlyChange: 'ReadOnlyChange',
	QEvent.PlatformSurface: 'PlatformSurface', QEvent.TabletTrackingChange: 'TabletTrackingChange', QEvent.User: 'User',
	QEvent.MaxUser: 'MaxUser',
}


class TextDocumentEditor(DocumentEditorBase[TextDocument]):

	@override
	def postInit(self):
		self.redraw()  # force a second redraw!

	@override
	def documentGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()
		try:
			if document.highlightErrors:
				errors = [error for error in document.errors if error.position is not None and error.end is not None]
			else:
				errors = []

			document.content, document.highlightErrors, document.cursorPosition, document.forceLocate = drawCodeField(
				gui,
				document.content,
				language=document.language,
				errors=errors,
				forceLocateElement=True,
				currentCursorPos=document.cursorPosition,
				selectionTo=document.selection[2:] if document.selection[0] != -1 else None,
				highlightErrors=document.highlightErrors,
				onCursorPositionChanged=lambda a, b, d=document: type(d).cursorPosition.set(d, (a, b)),
				onSelectionChanged2=lambda a1, b1, a2, b2, d=document: type(d).selection.set(d, (a1, b1, a2, b2)),
				onFocusReceived=lambda fr: self.editorFocusReceived.emit(fr),
				focusPolicy=Qt.StrongFocus,
				#autoCompletionTree=getSession().project.models.allTypesAutoCompletionTree

			)
			# document.content = gui.codeField(document.content)
			self.setFocusProxy(gui._lastTabWidget)
		except Exception as e:
			logError(f'{e}:\n{indentMultilineStr(format_full_exc(), indent="  ")} ')
			gui.helpBox(f'cannot draw document: {e}')
			gui.button('retry')  # pressing causes a gui update & redraw

	@override
	def documentFooterGUI(self, gui: DatapackEditorGUI) -> None:
		document = self.model()
		super(TextDocumentEditor, self).documentFooterGUI(gui)
		gui.addHSpacer(0, SizePolicy.Expanding)
		gui.propertyField(document, document.languageProp)


__all__ = [
	'DocumentEditorBase',
	'TextDocumentEditor',
]
