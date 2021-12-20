import copy
from typing import Any, List, NamedTuple, Optional, Type, Union

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget, QApplication

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.GUI import CORNERS, Overlap, RoundedCorners
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


class SettingsDialog(CatFramelessWindowMixin, QDialog):
	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(GUICls=PythonGUI, parent=parent)
		self._settingsCopy: ApplicationSettings = applicationSettings
		self._selectedPage: SerializableContainer = None
		self.setWindowTitle('Settings')
		self._disableContentMargins = True
		self._disableSidebarMargins = True
		self._drawTitleToolbarBorder = False
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

	def _mainAreaGUI(self, gui: PythonGUI, overlap: Overlap, roundedCorners: RoundedCorners):
		contentsMargins = self._mainAreaMargins
		with gui.vLayout(contentsMargins=contentsMargins):
			self.OnGUI(gui)

	def OnGUI(self, gui: PythonGUI):
		self.settingsPageGUI(gui, self._selectedPage)

	def settingsPageSelectionGUI(self, gui: PythonGUI) -> Optional[SerializableContainer]:
		DataValue = Union[SerializableContainer, Any, None]

		class Field(NamedTuple):
			value: DataValue
			label: str
			toolTip: Optional[str]
			type: Type

		def childrenMaker(data: Field):
			value = data.value
			children: List[Field] = []

			valueCls = type(value)
			for prop in valueCls.getSerializedProperties():
				v = prop.__get__(value, valueCls)
				if isinstance(v, SerializableContainer):
					children.append(Field(
						value=v,
						label=prop.label_,
						toolTip=prop.kwargs.get('tip', None),
						type=prop.typeHint_
					))
			return children

		def labelMaker(data: Field, column: int) -> str:
			return data.label

		def toolTipMaker(data: Field, column: int) -> Optional[str]:
			return data.toolTip

		root = Field(
			value=self._settingsCopy,
			label='Settings',
			toolTip=None,
			type=type(self._settingsCopy)
		)

		settings = gui.tree(
			DataTreeBuilder(root, childrenMaker, labelMaker, None, toolTipMaker, 1, showRoot=False, getId=lambda x: x.label),
			headerVisible=True,
			loadDeferred=True,
			roundedCorners=CORNERS.RIGHT
		).selectedItem
		return settings.value if settings is not None else None

	def settingsPageGUI(self, outerGui: PythonGUI, settingsPage: Optional[SerializableContainer]):
		def drawGUI(gui: AutoGUI):
			with gui.vLayout(preventVStretch=True):
				for prop in settingsPage.getSerializedProperties():
					if isinstance(prop.decorator, pd.NoUI):
						continue
					gui.propertyField(settingsPage, prop, True, enabled=True)
					gui.addVSpacer(gui.spacing, SizePolicy.Fixed)  # just a spacer

		with outerGui.vPanel(roundedCorners=CORNERS.LEFT, windowPanel=True):
			if settingsPage is None:
				outerGui.helpBox('Please select a category.')
			else:
				subGui = outerGui.subGUI(AutoGUI, drawGUI)
				subGui.OnGUI = drawGUI
				subGui.redrawGUI()

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