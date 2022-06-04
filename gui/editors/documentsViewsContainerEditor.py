from typing import Optional

from Cat.CatPythonGUI.GUI.catWidgetMixins import CatFramedWidgetMixin, CORNERS, maskCorners
from Cat.CatPythonGUI.GUI.pythonGUI import EditorBase
from gui.datapackEditorGUI import DatapackEditorGUI
from gui.editors import DocumentsViewEditor
from session.documentHandling import ViewContainer


class DocumentsViewsContainerEditor(EditorBase[ViewContainer], CatFramedWidgetMixin):

	def onSetModel(self, new: ViewContainer, old: Optional[ViewContainer]) -> None:
		super(DocumentsViewsContainerEditor, self).onSetModel(new, old)
		if old is not None:
			old.onViewsChanged.disconnect('editorRedraw')
		new.onViewsChanged.reconnect('editorRedraw', lambda: self.redraw('onViewsChanged'))

	def OnGUI(self, gui: DatapackEditorGUI) -> None:
		viewContainer = self.model()
		splitterFunc = gui.vSplitter if viewContainer.isVertical else gui.hSplitter

		cornerFilters = [CORNERS.NONE] * len(viewContainer.views)
		if len(cornerFilters) == 0:
			cornerFilters = []
		elif len(cornerFilters) == 1:
			cornerFilters[0] = CORNERS.ALL
		else:
			cornerFilters[0] = CORNERS.TOP if viewContainer.isVertical else CORNERS.LEFT
			cornerFilters[-1] = CORNERS.BOTTOM if viewContainer.isVertical else CORNERS.RIGHT

		with splitterFunc(handleWidth=gui.smallSpacing) as splitter:
			for view, cf in zip(viewContainer.views, cornerFilters):
				with splitter.addArea(verticalSpacing=0):
					if isinstance(view, ViewContainer):
						gui.editor(DocumentsViewsContainerEditor, view, roundedCorners=maskCorners(self.roundedCorners(), cf)).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')
					else:
						gui.editor(DocumentsViewEditor, view, roundedCorners=maskCorners(self.roundedCorners(), cf)).redrawLater('DocumentsViewsContainerEditor.OnGUI(...)')


__all__ = ['DocumentsViewsContainerEditor']
