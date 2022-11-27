from typing import Optional

from Cat.CatPythonGUI.GUI.pythonGUI import EditorBase
from gui.datapackEditorGUI import DatapackEditorGUI
from gui.editors import DocumentsViewEditor
from base.model.documentHandling import ViewContainer


class DocumentsViewsContainerEditor(EditorBase[ViewContainer]):

	def onSetModel(self, new: ViewContainer, old: Optional[ViewContainer]) -> None:
		super(DocumentsViewsContainerEditor, self).onSetModel(new, old)
		if old is not None:
			old.onViewsChanged.disconnect('editorRedraw')
		new.onViewsChanged.reconnect('editorRedraw', lambda: self.redraw('onViewsChanged'))

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		viewContainer = self.model()
		splitterFunc = gui.vSplitter if viewContainer.isVertical else gui.hSplitter

		with splitterFunc(handleWidth=gui.smallSpacing) as splitter:
			for view in viewContainer.views:
				with splitter.addArea(seamless=True):
					if isinstance(view, ViewContainer):
						gui.editor(DocumentsViewsContainerEditor, view, seamless=True).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')
					else:
						gui.editor(DocumentsViewEditor, view, seamless=True).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')


__all__ = ['DocumentsViewsContainerEditor']
