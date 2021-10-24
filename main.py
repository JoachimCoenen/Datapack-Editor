# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
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
from Cat.utils import getExePath, profiling
from Cat.utils.formatters import FW
from mainWindow import MainWindow
from Cat.utils.profiling import Timer
from session import WindowId, getSession, loadSessionFromFile
from settings import applicationSettings, saveApplicationSettings, loadApplicationSettings


class ModelMakerStyles(Styles):
	@_StyleProperty
	def hostWidgetStyle(self) -> Style:
		return Style({
			#'font-family': 'Segoe UI',
			#'font-family': 'Liberation Sans',
			#'font-family': 'Microsoft Sans Serif',
			'font-family': applicationSettings.appearance.fontFamily,
			'font-size': f'{applicationSettings.appearance.fontSize}pt',
		})  # + self.layoutingBorder

	@_StyleProperty
	def fixedWidthChar(self) -> Style:
		return Style({
			'font-family': applicationSettings.appearance.monospaceFontFamily,
			'font-size': f'{applicationSettings.appearance.fontSize}pt',
		})

setStyles(ModelMakerStyles())  #.hostWidgetStyle._func, 'hostWidgetStyle'))


class SetupDialog(CatFramelessWindowMixin, QDialog):
	def OnGUI(self, gui: AutoGUI):
		with gui.vLayout1C(preventVStretch=True):
			with gui.groupBox('Welcome!'):
				gui.label("We'll have to set up a few things before we can start. This shouldn't take long.")
				with gui.hLayout(preventHStretch=True):
					gui.label("You can always change these later under Settings ")
					gui.label("("); gui.label(icons.settings); gui.label(").")
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
			with gui.groupBox('Basic Settings'):
				gui.helpBox('Nothing.')
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer
			with gui.groupBox('Optional Settings'):
				gui.helpBox('Nothing.')
				gui.addVSpacer(9, SizePolicy.Fixed)  # just a spacer

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
		profiling._currentOutStream = FW(logFile)
		startObserver()
		app = start(argv=sys.argv)
		app.exec_()


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

		applyStyle(app, Style({'QWidget': getStyles().hostWidgetStyle}))  # + styles.layoutingBorder))
		palette = app.palette()
		# palette.setColor(palette.Active, palette.Highlight, catWidgetMixins._standardHighlightColor)
		# palette.setColor(palette.Disabled, palette.Highlight, catWidgetMixins._standardDisabledHighlightColor)
		app.setPalette(palette)

		loadSessionFromFile()
		showSetupDialogIfNecessary()

		from model.commands import argumentHandlersImpl
		argumentHandlersImpl._init()  # do not remove!

		if not getSession().selectedDocumentIds:
			getSession().selectedDocumentIds[WindowId('0')] = None
		# getSession().project.getAllTypedConfigFiles()
		for id in getSession().selectedDocumentIds.keys():
			window = MainWindow(id)
			window.show()
			window._gui.redrawGUI()

	print(" << << it took {:.3}, seconds to start the Application".format(timer.elapsed)
	)
	return app

	timer = Timer()
	with timer:
		QtWidgets.QApplication.setStyle('Fusion')
		app = QtWidgets.QApplication(argv)
		app.setApplicationName("Minecraft Datapack Editor")
		window = MainWindow(WindowId('1'))
		try:
			pass  # getSession().openDocument(xmlPath)
		except FileNotFoundError as e:
			print(e)

		#window._gui.redrawGUI()
		window.show()
		app.exec()

	print("it took {:.3}, seconds to start the Application".format(timer.elapsed))
	return app


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
	run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
