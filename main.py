import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from qtpy import QtCore

from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import _StyleProperty, setStyles, Style, Styles, SizePolicy, MessageBoxButton, applyStyle, getStyles, catWidgetMixins
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.extensions.fileSystemChangedDependency import startObserver
from Cat.icons import icons
from Cat.utils import getExePath, logging_
from Cat.utils.formatters import FW
from gui.themes.theme import currentColorScheme
from mainWindow import MainWindow
from Cat.utils.profiling import Timer
from session.session import WindowId, loadSessionFromFile
from settings import applicationSettings, saveApplicationSettings, loadApplicationSettings, AppearanceSettings
from settings._applicationSettings import MinecraftSettings


class ResizableStyles(Styles):
	@_StyleProperty
	def hostWidgetStyle(self) -> Style:
		return Style({
			'font-family': applicationSettings.appearance.fontFamily,
			'font-size': f'{applicationSettings.appearance.fontSize}pt',
		})  # + self.layoutingBorder

	@_StyleProperty
	def fixedWidthChar(self) -> Style:
		return Style({
			'font-family': applicationSettings.appearance.monospaceFontFamily,
			'font-size': f'{applicationSettings.appearance.fontSize}pt',
		})


setStyles(ResizableStyles())  # .hostWidgetStyle._func, 'hostWidgetStyle'))


class SetupDialog(CatFramelessWindowMixin, QDialog):
	def OnGUI(self, gui: AutoGUI):
		appearanceSettings = applicationSettings.appearance
		minecraftSettings = applicationSettings.minecraft
		with gui.vLayout1C(preventVStretch=True):
			with gui.groupBox('Welcome!'):
				gui.label("We'll have to set up a few things before we can start. This shouldn't take long.")
				with gui.hLayout(preventHStretch=True):
					gui.label("You can always change these later under Settings ")
					gui.label("("); gui.label(icons.settings); gui.label(").")
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

			with gui.groupBox('Appearance'):
				# gui.propertyField(appearanceSettings, AppearanceSettings.useCompactLayout)
				# gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
				gui.propertyField(appearanceSettings, AppearanceSettings.fontSize)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

			with gui.groupBox('Minecraft'):
				gui.propertyField(minecraftSettings, MinecraftSettings.version)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
				gui.propertyField(minecraftSettings, MinecraftSettings.executable)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
				gui.propertyField(minecraftSettings, MinecraftSettings.savesLocation)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
			#
			# with gui.groupBox('Optional Settings'):
			# 	gui.helpBox('Nothing.')
			# 	gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

		gui.dialogButtons({
			MessageBoxButton.Ok    : lambda b: self.accept(),
			MessageBoxButton.Abort : lambda b: self.reject(),
		})


def showSetupDialogIfNecessary():
	if applicationSettings.isUserSetupFinished:
		return
	else:
		setupResult = SetupDialog(GUICls=AutoGUI).exec()
		if setupResult != 1:
			return exit(0)
		applicationSettings.isUserSetupFinished = True
		saveApplicationSettings()


def run():
	with open(os.path.join(os.path.dirname(getExePath()), 'logfile.log'), 'w', encoding='utf-8') as logFile:
		loadApplicationSettings()
		logging_.setLoggingStream(FW(logFile))
		startObserver()
		app = start(argv=sys.argv)
		app.exec_()


def loadPlugins():
	from model.commands import argumentContextsImpl
	argumentContextsImpl.init()  # do not remove!

	from model.data import version1_16, version1_17, version1_18
	version1_16.initPlugin()
	version1_17.initPlugin()
	version1_18.initPlugin()

	from model.data import version6
	version6.initPlugin()


def loadColorSchemes():
	from gui.themes.theme import loadAllColorSchemes
	loadAllColorSchemes()
	catWidgetMixins.setGUIColors(currentColorScheme().uiColors)


def start(argv):

	os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, False)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
		QtWidgets.QApplication.setStyle(applicationSettings.appearance.applicationStyle)
		app = QtWidgets.QApplication(argv)

		app.setApplicationName(applicationSettings.applicationName)
		app.setApplicationDisplayName(applicationSettings.applicationName)
		app.setApplicationVersion(applicationSettings.version)
		app.setOrganizationName(applicationSettings.organization)

		applyStyle(app, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		catWidgetMixins.setGUIColors(catWidgetMixins.standardBaseColors)

		loadSessionFromFile()
		showSetupDialogIfNecessary()

		import gui.themes.schemesUI  # DO NOT REMOVE!

		loadPlugins()
		loadColorSchemes()

		window = MainWindow(WindowId('0'))
		window.show()
		window.redraw()

	print(f" << << it took {timer.elapsed:.3}, seconds to start the Application")
	return app


if __name__ == '__main__':
	run()