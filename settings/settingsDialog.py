import copy
from typing import NamedTuple, Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.CatPythonGUI.GUI.treeBuilders import DataTreeBuilder
from Cat.Serializable import SerializableContainer

from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI.pythonGUI import MessageBoxButton, SizePolicy, PythonGUI, WidgetDrawer
from settings import ApplicationSettings, applicationSettings, setApplicationSettings, saveApplicationSettings
from settings._applicationSettings import AboutQt

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


class _Field(NamedTuple):
	value: SerializableContainer
	label: str
	toolTip: Optional[str]


def _childrenMaker(data: _Field) -> list[_Field]:
	value = data.value
	children = [
		_Field(value=v, label=prop.label_, toolTip=prop.kwargs.get('tip', None))
		for prop, v in ((p, p.get(value)) for p in value.getSerializedProperties())
		if isinstance(v, SerializableContainer)
	]
	return children


class SettingsDialog(CatFramelessWindowMixin, QDialog):
	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=AutoGUI, parent=parent)
		self._settingsCopy: ApplicationSettings = applicationSettings
		self._selectedPage: Optional[SerializableContainer] = None
		self.setWindowTitle('Settings')
		self.disableContentMargins = True
		self.disableSidebarMargins = True
		self.drawTitleToolbarBorder = True
		self.resize(750, 500)

	def OnSidebarGUI(self, gui: PythonGUI):
		self._selectedPage = self.settingsPageSelectionGUI(gui)

	def OnStatusbarGUI(self, gui: PythonGUI):
		gui.dialogButtons({
			MessageBoxButton.Apply          : lambda b: self.apply(),
			MessageBoxButton.Ok             : lambda b: self.accept(),
			MessageBoxButton.Cancel         : lambda b: self.reject(),
			MessageBoxButton.RestoreDefaults: lambda b: self._settingsCopy.reset() or gui.redrawGUI(),
		})

	# def _mainAreaGUI(self, gui: PythonGUI, overlap: Overlap, roundedCorners: RoundedCorners):
	# 	contentsMargins = self._mainAreaMargins
	# 	with gui.vLayout(contentsMargins=contentsMargins):
	# 		self.OnGUI(gui)

	def OnGUI(self, gui: AutoGUI):
		# def drawGUI(gui: AutoGUI):
		# 	with gui.vLayout(preventVStretch=True):
		# 		for prop in settingsPage.getSerializedProperties():
		# 			if isinstance(prop.decorator, pd.NoUI):
		# 				continue
		# 			gui.propertyField(settingsPage, prop, True, enabled=True)
		# 			gui.addVSpacer(gui.spacing, SizePolicy.Fixed)  # just a spacer
		with gui.vPanel(windowPanel=True, preventVStretch=True):
			if self._selectedPage is None:
				gui.helpBox('Please select a category.')
			else:
				for prop in self._selectedPage.getSerializedProperties():
					if isinstance(prop.decorator, pd.NoUI):
						continue
					gui.propertyField(self._selectedPage, prop, True, enabled=True)
					gui.addVSpacer(gui.spacing, SizePolicy.Fixed)  # just a spacer

	def settingsPageSelectionGUI(self, gui: PythonGUI) -> Optional[SerializableContainer]:
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