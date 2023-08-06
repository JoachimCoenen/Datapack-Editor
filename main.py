import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from qtpy import QtCore

from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import _StyleProperty, setStyles, Style, Styles, SizePolicy, MessageBoxButton, applyStyle, getStyles, catWidgetMixins
from Cat.CatPythonGUI.GUI.framelessWindow.catFramelessWindowMixin import CatFramelessWindowMixin
from Cat.icons import icons
from Cat.utils import getExePath, logging_
from Cat.utils.formatters import FW
from base.model import filesystemEvents
from base.model.session import loadSessionFromFile
from mainWindow import MainWindow, WindowId
from Cat.utils.profiling import Timer
from base.model.applicationSettings import applicationSettings, saveApplicationSettings, loadApplicationSettings, AppearanceSettings
# from settings._applicationSettings import MinecraftSettings


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
	def __init__(self, **kwargs):
		super(SetupDialog, self).__init__(**kwargs)
		self.reset()

	def reset(self):
		applicationSettings.reset()
		applicationSettings.appearance.colorScheme = 'Default Dark'

	def OnGUI(self, gui: AutoGUI):
		if gui.isLastRedraw:
			for child in self.children():
				if isinstance(child, QtWidgets.QWidget):
					child.resize(QtCore.QSize(3, 3))  # force a proper redraw.

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
				# with gui.hLayout2R(preventHStretch=True):
				# 	gui.propertyField(appearanceSettings, AppearanceSettings.useCompactLayout)
				# gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
				#with gui.hLayout2R():
				gui.propertyField(appearanceSettings, AppearanceSettings.fontSize)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
				gui.propertyField(appearanceSettings, AppearanceSettings.colorScheme)
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

			# with gui.groupBox('Minecraft'):
			# 	#with gui.hLayout2R():
			# 	gui.propertyField(minecraftSettings, MinecraftSettings.version)  # , hSizePolicy=SizePolicy.Fixed.value)
			# 	gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
			# 	gui.propertyField(minecraftSettings, MinecraftSettings.executable)
			# 	gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
			# 	gui.propertyField(minecraftSettings, MinecraftSettings.savesLocation)
			# 	gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

		gui.dialogButtons({
			MessageBoxButton.Ok    : lambda b: self.accept(),
			MessageBoxButton.Abort : lambda b: self.reject(),
			MessageBoxButton.RestoreDefaults: lambda b: self.reset() or gui.redrawGUI(),
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


def loadBasePlugins():

	from basePlugins import projectPage, projectFiles, pluginDebug

	projectPage.initPlugin()
	projectFiles.initPlugin()
	pluginDebug.initPlugin()


def loadCorePlugins():

	from corePlugins import json
	from corePlugins import nbt
	from corePlugins import mcFunction
	from corePlugins import mcFunctionSchemaTEMP
	from corePlugins import datapack
	from corePlugins import datapackSchemas

	json.initPlugin()
	nbt.initPlugin()
	mcFunction.initPlugin()
	mcFunctionSchemaTEMP.initPlugin()
	datapack.initPlugin()
	datapackSchemas.initPlugin()
	#
	# from model import json, commands, nbt
	#
	# json.initPlugin()
	# commands.initPlugin()
	# nbt.initPlugin()
	#
	# from sessionOld import documentsImpl
	#
	# documentsImpl.initPlugin()


def loadPlugins():

	from model.data import json as jsonData
	jsonData.initPlugin()

	from model.data import version1_16, version1_17, version1_18
	version1_16.initPlugin()
	version1_17.initPlugin()
	version1_18.initPlugin()

	from model.data import version6
	version6.initPlugin()


def loadColorSchemes():
	from gui.themes.theme import loadAllColorSchemes
	loadAllColorSchemes()


def start(argv):

	os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, False)
		QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
		app = QtWidgets.QApplication(argv)

		loadColorSchemes()
		loadApplicationSettings()

		QtWidgets.QApplication.setStyle(applicationSettings.appearance.applicationStyle)

		app.setApplicationName(applicationSettings.applicationName)
		app.setApplicationDisplayName(applicationSettings.applicationName)
		app.setApplicationVersion(applicationSettings.version)
		app.setOrganizationName(applicationSettings.organization)

		applyStyle(app, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		catWidgetMixins.setGUIColors(catWidgetMixins.standardBaseColors)

		import gui.themes.schemesUI  # DO NOT REMOVE!

		loadBasePlugins()
		loadCorePlugins()
		#
		loadSessionFromFile()
		# showSetupDialogIfNecessary()
		# loadPlugins()

		window = MainWindow(WindowId('0'))
		window.show()
		window.redraw()

		# from trials import iconsPreview
		# iconsPreview.createWindow()

	print(f" << << it took {timer.elapsed:.3}, seconds to start the Application")
	return app


def run():
	with open(os.path.join(os.path.dirname(getExePath()), 'logfile.log'), 'w', encoding='utf-8') as logFile:
		logging_.setLoggingStream(FW(logFile))
		# startObserver()
		with filesystemEvents.FILESYSTEM_OBSERVER:
			app = start(argv=sys.argv)
			app.exec_()


if __name__ == '__main__':
	run()