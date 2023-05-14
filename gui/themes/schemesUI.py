from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.AutoGUI.decoratorDrawers import registerDecoratorDrawer, InnerDrawPropertyFunc
from Cat.CatPythonGUI.GUI import CORNERS
from Cat.Serializable import SerializableContainer
from Cat.icons import icons
from Cat.utils import showInFileSystem
from gui.themes import theme
from base.model.applicationSettings import ColorSchemePD


@registerDecoratorDrawer(ColorSchemePD)
def drawColorSchemePD(gui_: AutoGUI, value_: str, type_, decorator_: ColorSchemePD, drawProperty_: InnerDrawPropertyFunc[str], owner_: SerializableContainer, **kwargs) -> str:
	choices = [cs.name for cs in theme.getAllColorSchemes()]

	with gui_.hLayout(
			horizontalSpacing=0,
			label=kwargs.pop('label', None),
			fullSize=kwargs.pop('fullSize', False),
			enabled=kwargs.get('enabled', True),
			tip=kwargs.get('tip', ''),
	):
		result = gui_.comboBox(value_, choices=choices, **kwargs)
		if gui_.button(icon=icons.refresh, tip="reload color schemes", roundedCorners=CORNERS.NONE, overlap=(1, 0, 0, 0)):
			theme.reloadAllColorSchemes()
		if gui_.button(icon=icons.folder_open, tip="open color schemes folder", roundedCorners=CORNERS.RIGHT, overlap=(1, 0, 0, 0)):
			showInFileSystem(theme.getColorSchemesDir())

	return result
