import os
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from qtpy import QtCore

from base.model.settingsAspectSetup import SettingsAspectSetup, SettingsSetup
from cat.GUI import _StyleProperty, setStyles, Style, Styles, MessageBoxButton, applyStyle, getStyles
from cat.GUI.components import catWidgetMixins
from cat.GUI.propertyDecorators import ValidatorResult
from cat.GUI.pythonGUI import ValidatedDialog
from cat.Serializable.serializableDataclasses import getField
from gui.icons import icons
from cat.utils import getExePath, logging_
from cat.utils.formatters import FW
from cat.utils.logging_ import loggingIndentInfo
from base.model import filesystemEvents
from base.model.session import loadSessionFromFile
from base.plugin import PLUGIN_SERVICE, loadAllPlugins, getBasePluginsDir, getCorePluginsDir, getPluginsDir
from gui.datapackEditorGUI import DatapackEditorGUI
from mainWindow import MainWindow
from cat.utils.profiling import Timer
from base.model.applicationSettings import AppearanceSettings, ApplicationSettings, saveApplicationSettings, loadApplicationSettings, resetApplicationSettings, \
	getApplicationSettings


class ResizableStyles(Styles):
	@_StyleProperty
	def hostWidgetStyle(self) -> Style:
		return Style({
			'font-family': getApplicationSettings().appearance.fontFamily,
			'font-size': f'{getApplicationSettings().appearance.fontSize}pt',
		})  # + self.layoutingBorder

	@_StyleProperty
	def fixedWidthChar(self) -> Style:
		return Style({
			'font-family': getApplicationSettings().appearance.monospaceFontFamily,
			'font-size': f'{getApplicationSettings().appearance.fontSize}pt',
		})

	@_StyleProperty
	def title(self) -> Style:
		return Style({
			'padding-top': f'{int(8 * getApplicationSettings().appearance.fontSize / 10)}px',
			'font-family': getApplicationSettings().appearance.fontFamily,
			'font-size': f'{int(getApplicationSettings().appearance.fontSize * 1.5)}pt',
		})


setStyles(ResizableStyles())  # .hostWidgetStyle._func, 'hostWidgetStyle'))


class WelcomeSetup(SettingsSetup):

	@property
	def title(self) -> str:
		return "Welcome!"

	def validate(self, settings: ApplicationSettings) -> list[ValidatorResult]:
		return []

	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings) -> None:
		with gui.vLayout():
			gui.label("We'll have to set up a few things before we can start. This shouldn't take long.")
			with gui.hLayout(preventHStretch=True):
				gui.label("You can always change these later under Settings ")
				gui.label(icons.settings)


class AppearanceSettingsSetup(SettingsAspectSetup[AppearanceSettings]):

	@property
	def title(self) -> str:
		return "Appearance"

	def getSettingsAspect(self, settings: ApplicationSettings) -> AppearanceSettings:
		return settings.appearance

	def aspectGUI(self, gui: DatapackEditorGUI, aspect: AppearanceSettings) -> None:
		gui.propertyField(aspect, getField(aspect, 'useCompactLayout'))
		gui.propertyField(aspect, getField(aspect, 'fontSize'))
		gui.propertyField(aspect, getField(aspect, 'colorScheme'))

	def resetAspect(self, aspect: AppearanceSettings) -> None:
		aspect.colorScheme = 'Default Dark'


class SetupDialog(ValidatedDialog):
	def __init__(self, **kwargs) -> None:
		super().__init__(GUICls=DatapackEditorGUI, **kwargs)
		self.settingsSetups: list[SettingsSetup] = [
			WelcomeSetup(),
			AppearanceSettingsSetup(),
			*(
				pcCls()
				for plugin in PLUGIN_SERVICE.activePlugins
				for pcCls in plugin.settingsAspectSetups()
			)
		]

		self.reset()

	def reset(self) -> None:
		resetApplicationSettings()
		settings = getApplicationSettings()
		for sas in self.settingsSetups:
			sas.reset(settings)

	def validate(self) -> list[ValidatorResult]:
		settings = getApplicationSettings()
		return [vr for sas in self.settingsSetups for vr in sas.validate(settings)]

	def additionalButtons(self) -> dict[MessageBoxButton, Callable[[MessageBoxButton], None] | tuple[Callable[[MessageBoxButton], None], dict[str, Any]]]:
		return {
			MessageBoxButton.Abort: lambda b: self.reject(),
			MessageBoxButton.RestoreDefaults: lambda b: self.reset() or self.redraw()
		}

	def OnGUI(self, gui: DatapackEditorGUI):
		if gui.isLastRedraw:
			for child in self.children():
				if isinstance(child, QtWidgets.QWidget):
					child.resize(QtCore.QSize(3, 3))  # force a proper redraw.

		with gui.vLayout(preventVStretch=True, verticalSpacing=gui.spacing + gui.smallSpacing):
			settings = getApplicationSettings()
			for sas in self.settingsSetups:
				with gui.vLayout():
					gui.title(sas.title, addSeparator=True)
				with gui.indentation():
					sas.onGUI(gui, settings)


def showSetupDialogIfNecessary() -> None:
	if getApplicationSettings().isUserSetupFinished:
		return
	else:
		setupResult = SetupDialog().exec()
		if setupResult != 1:
			return exit(0)
		getApplicationSettings().isUserSetupFinished = True
		saveApplicationSettings()


def loadActualBasePlugins() -> None:
	loadAllPlugins(*getBasePluginsDir())


def loadActualCorePlugins() -> None:
	loadAllPlugins(*getCorePluginsDir())


def loadActualPlugins() -> None:
	loadAllPlugins(*getPluginsDir())


def loadColorSchemes() -> None:
	from base.model.theme import loadAllColorSchemes
	loadAllColorSchemes()


@dataclass
class AppOptions:
	appName: str
	appDisplayName: str
	appVersion: str
	organization: str
	windowIcon: Callable[[], QIcon] | None


def _startInternal(argv: list[str], appOptions: AppOptions) -> QtWidgets.QApplication:

	os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, False)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
		app = QtWidgets.QApplication(argv)

		app.setApplicationName(appOptions.appName)
		app.setApplicationDisplayName(appOptions.appName)
		app.setApplicationVersion(appOptions.appVersion)
		app.setOrganizationName(appOptions.organization)
		if appOptions.windowIcon is not None:
			app.setWindowIcon(appOptions.windowIcon())

		loadColorSchemes()
		loadApplicationSettings()

		QtWidgets.QApplication.setStyle('Fusion')
		applyStyle(app, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		catWidgetMixins.setGUIColors(catWidgetMixins.getGUIColors())

		with loggingIndentInfo("Collecting & Loading all plugins..."):
			loadActualBasePlugins()
			loadActualCorePlugins()
			loadActualPlugins()

		with loggingIndentInfo("Initializing all plugins..."):
			PLUGIN_SERVICE.initAllPlugins()

		with loggingIndentInfo("Loading Session..."):
			loadSessionFromFile()
		showSetupDialogIfNecessary()

		window = MainWindow(uuid.uuid4())
		window.show()
		window.resize(1280, 720)
		window.resize(1334 + 26, 852 + 26)
		window.redraw()

	print(f" << << it took {timer.elapsed:.3}, seconds to start the Application")
	return app


def start(argv: list[str], appOptions: AppOptions) -> None:
	with open(os.path.join(os.path.dirname(getExePath()), 'logfile.log'), 'w', encoding='utf-8') as logFile:
		logging_.setLoggingStream(FW(logFile))
		with filesystemEvents.FILESYSTEM_OBSERVER:
			app = _startInternal(argv=argv, appOptions=appOptions)
			app.exec_()
