import os
import uuid
from dataclasses import Field
from typing import Any, Callable

from PyQt5 import QtWidgets
from qtpy import QtCore

from base.model.application import AppInfo, instantiateApp, App
from base.model.settingsAspectSetup import SettingsAspectSetup, SettingsSetup
from cat.GUI import _StyleProperty, setStyles, Style, Styles, MessageBoxButton, applyStyle, getStyles, SizePolicy
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

	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings, vSpacer: Callable[[DatapackEditorGUI], None]) -> None:
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

	def getAspectFields(self, aspect: AppearanceSettings) -> list[Field]:
		return [
			getField(aspect, 'useCompactLayout'),
			getField(aspect, 'fontSize'),
			getField(aspect, 'colorScheme'),
		]


class SetupDialog(ValidatedDialog):
	def __init__(self, **kwargs) -> None:
		super().__init__(GUICls=DatapackEditorGUI, **kwargs)
		self.drawStatusbarBorder = False
		self.statusbarIsWindowPanel = True
		self.settingsSetups: list[SettingsSetup] = [
			WelcomeSetup(),
			AppearanceSettingsSetup(),
			*(
				pcCls()
				for plugin in PLUGIN_SERVICE.activePlugins
				for pcCls in plugin.settingsAspectSetups()
			)
		]

	def reset(self) -> None:
		resetApplicationSettings()
		settings = getApplicationSettings()
		for sas in self.settingsSetups:
			sas.additionalReset(settings)

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

		spacerSize = int(9 * gui.scale)

		def vSpacer(gui2: DatapackEditorGUI) -> None:
			gui2.addVSpacer(spacerSize, SizePolicy.Fixed)  # just a spacer

		with gui.vLayout(preventVStretch=True):  # , verticalSpacing=gui.spacing + gui.smallSpacing):
			settings = getApplicationSettings()
			for sas in self.settingsSetups:
				vSpacer(gui)
				with gui.vLayout():
					gui.title(sas.title, addSeparator=True)
				with gui.indentation():
					vSpacer(gui)
					sas.onGUI(gui, settings, vSpacer)


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


def _startInternal(argv: list[str], appInfo: AppInfo) -> App:

	os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, False)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)

		app = instantiateApp(argv, appInfo)

		loadColorSchemes()
		loadApplicationSettings()

		QtWidgets.QApplication.setStyle('Fusion')
		applyStyle(app.qApp, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		catWidgetMixins.setGUIColors(catWidgetMixins.getGUIColors())

		# we need to create the main window so early, because its gui is responsible for showing errors, warnings, and questions.
		window = MainWindow(uuid.uuid4())

		with loggingIndentInfo("Collecting & Loading all plugins..."):
			loadActualBasePlugins()
			loadActualCorePlugins()
			loadActualPlugins()

		with loggingIndentInfo("Initializing all plugins..."):
			PLUGIN_SERVICE.initAllPlugins()

		with loggingIndentInfo("Loading Session..."):
			loadSessionFromFile()
		showSetupDialogIfNecessary()

		window.show()
		window.resize(1280, 720)
		window.resize(1334 + 26, 852 + 26)
		window.redraw()

	print(f" << << it took {timer.elapsed:.3}, seconds to start the Application")
	return app


def start(argv: list[str], appInfo: AppInfo) -> None:
	with open(os.path.join(os.path.dirname(getExePath()), 'logfile.log'), 'w', encoding='utf-8') as logFile:
		logging_.setLoggingStream(FW(logFile))
		with filesystemEvents.FILESYSTEM_OBSERVER:
			app = _startInternal(argv=argv, appInfo=appInfo)
			app.exec()
