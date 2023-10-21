import copy
from dataclasses import fields
from typing import NamedTuple, Optional, Type

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from cat.GUI.autoGUI import AutoGUI
from cat.GUI.decoratorDrawers import registerDecoratorDrawer, InnerDrawPropertyFunc
from cat.GUI import CORNERS, propertyDecorators as pd
from cat.GUI.components.treeBuilders import DataTreeBuilder
from cat.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from cat.GUI.pythonGUI import MessageBoxButton, SizePolicy, PythonGUI, WidgetDrawer
from cat.Serializable.serializableDataclasses import SerializableDataclass, getDecorators, getKWArg
from gui.icons import icons
from cat.utils import showInFileSystem
from base.model import theme
from base.model.applicationSettings import AboutQt, ApplicationSettings, applicationSettings, setApplicationSettings,\
	saveApplicationSettings, ColorSchemePD

_qtIcon: Optional[QIcon] = None


@WidgetDrawer(AboutQt)
def aboutQt(gui: AutoGUI, v: AboutQt, **kwargs) -> AboutQt:
	global _qtIcon
	if _qtIcon is None:
		_qtIcon = QIcon(":/qt-project.org/qmessagebox/images/qtlogo-64.png")

	with gui.hLayout(preventHStretch=True, **kwargs):
		kwargs.pop('label', None)
		if gui.button("About Qt", icon=_qtIcon, **kwargs):
			QApplication.aboutQt()
	return v


@registerDecoratorDrawer(ColorSchemePD)
def drawColorSchemePD(gui_: AutoGUI, value_: str, type_, decorator_: ColorSchemePD, drawProperty_: InnerDrawPropertyFunc[str], owner_: SerializableDataclass, **kwargs) -> str:
	choices = [cs.name for cs in theme.getAllColorSchemes()]

	with gui_.hLayout(
		horizontalSpacing=0,
		label=kwargs.pop('label', None),
		fullSize=kwargs.pop('fullSize', False),
		enabled=kwargs.get('enabled', True),
		tip=kwargs.get('tip', ''),
		seamless=True,
		roundedCorners=CORNERS.RIGHT
	):
		result = gui_.comboBox(value_, choices=choices, **kwargs)
		if gui_.button(icon=icons.refresh, tip="reload color schemes"):
			theme.reloadAllColorSchemes()
		if gui_.button(icon=icons.folder_open, tip="open color schemes folder"):
			showInFileSystem(theme.getColorSchemesDir())

	return result


class _Field(NamedTuple):
	value: SerializableDataclass
	label: str
	toolTip: Optional[str]


def _childrenMaker(data: _Field) -> list[_Field]:
	value = data.value
	children = [
		_Field(value=v, label=getKWArg(prop, 'label', prop.name), toolTip=getKWArg(prop, 'tip', None))
		for prop, v in ((f, getattr(value, f.name)) for f in fields(value))
		if isinstance(v, SerializableDataclass)
	]
	if isinstance(value, ApplicationSettings):
		children += [
			_Field(value=aspect, label=aspect.getAspectType(), toolTip=None)
			for aspect in value.aspects
		]
	return children


class SettingsDialog(CatFramelessWindowMixin, QDialog):
	def __init__(self, parent: Optional[QWidget] = None, GUICls: Type[AutoGUI] = AutoGUI):
		super().__init__(GUICls=GUICls, parent=parent)
		self._settingsCopy: ApplicationSettings = applicationSettings
		self._selectedPage: Optional[SerializableDataclass] = None
		self.setWindowTitle('Settings')
		self.disableContentMargins = True
		self.disableSidebarMargins = True
		self.drawTitleToolbarBorder = True
		self.resize(750, 500)

	def OnSidebarGUI(self, gui: PythonGUI):
		self._selectedPage = self.settingsPageSelectionGUI(gui)

	def OnStatusbarGUI(self, gui: PythonGUI):
		gui.dialogButtons({
			MessageBoxButton.Apply: lambda b: self.apply(),
			MessageBoxButton.Ok: lambda b: self.accept(),
			MessageBoxButton.Cancel: lambda b: self.reject(),
			# TODO: MessageBoxButton.RestoreDefaults: lambda b: self._settingsCopy.reset() or gui.redrawGUI(),
		})

	def OnGUI(self, gui: AutoGUI):
		with gui.vPanel(windowPanel=True, preventVStretch=True):
			if self._selectedPage is None:
				gui.helpBox('Please select a category.')
			else:
				for field in fields(self._selectedPage):
					if any(isinstance(d, pd.NoUI) for d in getDecorators(field)):
						continue
					gui.propertyField(self._selectedPage, field, True, enabled=True)
					gui.addVSpacer(gui.spacing, SizePolicy.Fixed)  # just a spacer

	def settingsPageSelectionGUI(self, gui: PythonGUI) -> Optional[SerializableDataclass]:
		settings = gui.tree(
			DataTreeBuilder(
				_Field(value=self._settingsCopy, label='Settings', toolTip=None),
				_childrenMaker,
				lambda data, c: data.label,
				None,
				lambda data, c: data.toolTip,
				1, showRoot=False,
				getId=lambda data: data.label,
			),
			headerVisible=True,
			loadDeferred=True,
		).selectedItem
		return settings.value if settings is not None else None

	def exec(self):
		self._settingsCopy: ApplicationSettings = copy.deepcopy(applicationSettings)
		self._gui.redrawGUI()
		return super().exec()

	def apply(self):
		setApplicationSettings(self._settingsCopy)
		saveApplicationSettings()

	def accept(self):  # overrides QDialog.accept()
		self.apply()
		return super().accept()
