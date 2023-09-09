import os
import sys
from dataclasses import fields

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from qtpy import QtCore

from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import _StyleProperty, setStyles, Style, Styles, SizePolicy, MessageBoxButton, applyStyle, \
	getStyles, catWidgetMixins
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.icons import icons
from Cat.utils import getExePath, logging_
from Cat.utils.formatters import FW
from Cat.utils.logging_ import loggingIndentInfo
from base.model import filesystemEvents
from base.model.session import loadSessionFromFile
from base.plugin import PLUGIN_SERVICE, loadAllPlugins, getBasePluginsDir, getCorePluginsDir, getPluginsDir
from mainWindow import MainWindow, WindowId
from Cat.utils.profiling import Timer
from base.model.applicationSettings import saveApplicationSettings, loadApplicationSettings, resetApplicationSettings, \
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


class SetupDialog(CatFramelessWindowMixin, QDialog):
	def __init__(self, **kwargs) -> None:
		super(SetupDialog, self).__init__(**kwargs)
		self.reset()

	def reset(self) -> None:
		resetApplicationSettings()
		getApplicationSettings().appearance.colorScheme = 'Default Dark'

	def OnGUI(self, gui: AutoGUI):
		if gui.isLastRedraw:
			for child in self.children():
				if isinstance(child, QtWidgets.QWidget):
					child.resize(QtCore.QSize(3, 3))  # force a proper redraw.

		spacerSize = int(9 * getApplicationSettings().appearance.fontSize / 10)

		def vSpacer() -> None:
			gui.addVSpacer(spacerSize, SizePolicy.Fixed)  # just a spacer

		appearanceSettings = getApplicationSettings().appearance
		appearanceFields = {f.name: f for f in fields(appearanceSettings)}

		from corePlugins.mcFunctionSchemaTEMP.settings import MinecraftSettingsTemp
		minecraftSettings = getApplicationSettings().aspects.get(MinecraftSettingsTemp)
		minecraftFields = {f.name: f for f in fields(minecraftSettings)}

		with gui.vLayout(preventVStretch=True):
			with gui.groupBox('Welcome!', addSeparator=True):
				vSpacer()  # just a spacer
				gui.label("We'll have to set up a few things before we can start. This shouldn't take long.")
				with gui.hLayout(preventHStretch=True):
					gui.label("You can always change these later under Settings ")
					gui.label(icons.settings)
				vSpacer()  # just a spacer

			with gui.groupBox('Appearance', addSeparator=True):
				vSpacer()  # just a spacer
				gui.propertyField(appearanceSettings, appearanceFields['useCompactLayout'])
				vSpacer()  # just a spacer
				gui.propertyField(appearanceSettings, appearanceFields['fontSize'])
				vSpacer()  # just a spacer
				gui.propertyField(appearanceSettings, appearanceFields['colorScheme'])
				vSpacer()  # just a spacer

			with gui.groupBox('Minecraft', addSeparator=True):
				vSpacer()  # just a spacer
				gui.propertyField(minecraftSettings, minecraftFields['minecraftVersion'])  # , hSizePolicy=SizePolicy.Fixed.value)
				vSpacer()  # just a spacer
				gui.propertyField(minecraftSettings, minecraftFields['minecraftExecutable'])
				vSpacer()  # just a spacer

		gui.dialogButtons({
			MessageBoxButton.Ok    : lambda b: self.accept(),
			MessageBoxButton.Abort : lambda b: self.reject(),
			MessageBoxButton.RestoreDefaults: lambda b: self.reset() or gui.redrawGUI(),
		})


def showSetupDialogIfNecessary() -> None:
	if getApplicationSettings().isUserSetupFinished:
		return
	else:
		setupResult = SetupDialog(GUICls=AutoGUI).exec()
		if setupResult != 1:
			return exit(0)
		getApplicationSettings().isUserSetupFinished = True
		saveApplicationSettings()


# def loadBasePlugins():
# 	from basePlugins import projectPage, projectFiles, pluginDebug
#
# 	projectPage.initPlugin()
# 	projectFiles.initPlugin()
# 	pluginDebug.initPlugin()


# def loadCorePlugins():
# 	from corePlugins import json
# 	from corePlugins import nbt
# 	from corePlugins import minecraft
# 	from corePlugins import mcFunction
# 	from corePlugins import mcFunctionSchemaTEMP
# 	from corePlugins import datapack
# 	from corePlugins import datapackSchemas
#
# 	json.initPlugin()
# 	nbt.initPlugin()
# 	minecraft.initPlugin()
# 	mcFunction.initPlugin()
# 	mcFunctionSchemaTEMP.initPlugin()
# 	datapack.initPlugin()
# 	datapackSchemas.initPlugin()


def loadActualBasePlugins() -> None:
	loadAllPlugins(*getBasePluginsDir())


def loadActualCorePlugins() -> None:
	loadAllPlugins(*getCorePluginsDir())


def loadActualPlugins() -> None:
	loadAllPlugins(*getPluginsDir())


def loadColorSchemes() -> None:
	from base.model.theme import loadAllColorSchemes
	loadAllColorSchemes()


def start(argv) -> QtWidgets.QApplication:

	os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, False)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
		app = QtWidgets.QApplication(argv)

		loadColorSchemes()
		loadApplicationSettings()

		QtWidgets.QApplication.setStyle(getApplicationSettings().appearance.applicationStyle)

		app.setApplicationName(getApplicationSettings().applicationName)
		app.setApplicationDisplayName(getApplicationSettings().applicationName)
		app.setApplicationVersion(getApplicationSettings().version)
		app.setOrganizationName(getApplicationSettings().organization)

		applyStyle(app, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		catWidgetMixins.setGUIColors(catWidgetMixins.standardBaseColors)

		with loggingIndentInfo("Collecting & Loading all plugins..."):
			loadActualBasePlugins()
			loadActualCorePlugins()
			loadActualPlugins()

		with loggingIndentInfo("Initializing all plugins..."):
			PLUGIN_SERVICE.initAllPlugins()

		with loggingIndentInfo("Loading Session..."):
			loadSessionFromFile()
		showSetupDialogIfNecessary()

		window = MainWindow(WindowId('0'))
		window.show()
		window.redraw()

		# from trials import iconsPreview
		# iconsPreview.createWindow()

	print(f" << << it took {timer.elapsed:.3}, seconds to start the Application")
	return app


def run() -> None:
	with open(os.path.join(os.path.dirname(getExePath()), 'logfile.log'), 'w', encoding='utf-8') as logFile:
		logging_.setLoggingStream(FW(logFile))
		# startObserver()
		with filesystemEvents.FILESYSTEM_OBSERVER:
			app = start(argv=sys.argv)
			app.exec_()


if __name__ == '__main__':
	run()
