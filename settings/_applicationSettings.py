from __future__ import annotations

import copy
import os
import traceback
from enum import Enum
from json import JSONDecodeError

from PyQt5.QtGui import QFont, QFontDatabase

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import Computed, RegisterContainer, SerializableContainer, Serialized
from Cat.Serializable.serializedProperty import ComputedCached
from Cat.utils import getExePath
from Cat.utils.profiling import logError
from PyQt5.QtWidgets import QStyleFactory


QFont.__deepcopy__ = lambda x, m: QFont(x)


@RegisterContainer
class AppearanceSettings(SerializableContainer):
	__slots__ = ()
	applicationStyle: str = Serialized(
		default='Fusion',
		label='Application Style',
		decorators=[
			pd.ComboBox(choices=QStyleFactory.keys()),
			pd.NoUI()
		]
	)

	useCompactLayout: bool = Serialized(
		default=False,
		label='Compact layout',
		decorators=[pd.ToggleSwitch()]
	)

	fontSize: float = Serialized(
		default=10.,
		label='Font Size', min=4, max=36, step=1.0, decimals=0, suffix=' pt',
		decorators=[],
	)

	fontFamily: str = Serialized(
		default='Segoe UI',
		label='Font',
		decorators=[pd.FontFamily(QFontDatabase.Latin, smoothlyScalable=True)],
	)

	@pd.NoUI()
	@ComputedCached(dependencies_=[fontSize, fontFamily], shouldSerialize=False)
	def font(self) -> QFont:
		font = QFont(self.fontFamily)
		font.setPointSizeF(self.fontSize)
		return font

	monospaceFontFamily: str = Serialized(
		default='Consolas',
		label='Monospace Font',
		decorators=[pd.FontFamily(QFontDatabase.Latin, smoothlyScalable=True, fixedPitch=True)],
	)

	@pd.NoUI()
	@ComputedCached(dependencies_=[fontSize, monospaceFontFamily], shouldSerialize=False)
	def monospaceFont(self) -> QFont:
		font = QFont(self.monospaceFontFamily)
		font.setPointSizeF(self.fontSize)
		return font



class ProfilingNodeColoringScheme(Enum):
	ColourNodesByTotalTime = 0
	ColourNodesBySelfTime = 1


@RegisterContainer
class ProfilingSettings(SerializableContainer):
	__slots__ = ()
	enabled: bool = Serialized(
		default=False,
		decorators=[pd.ToggleSwitch()]
	)

	nodeColoringScheme: ProfilingNodeColoringScheme = Serialized(
		default=ProfilingNodeColoringScheme.ColourNodesByTotalTime,
		label='Node Coloring Scheme',
	)

	@pd.NoUI()
	@Computed()
	def colourNodesBySelftime(self) -> bool:
		return self.nodeColoringScheme == ProfilingNodeColoringScheme.ColourNodesBySelfTime


@RegisterContainer
class DebugSettings(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		# self.repository: Repository = Repository()
		pass

	@pd.Title('Developer Mode')
	@pd.ToggleSwitch()
	@Serialized()
	def isDeveloperMode(self) -> bool :
		return False

	@pd.ToggleSwitch()
	@Serialized()
	def showUndoRedoPane(self) -> bool :
		return False

	# @Serialized()
	# def showLayoutsPanel(self) -> bool :
	# 	return True
	#
	# @Serialized()
	# def showApplicationConfigPanel(self) -> bool :
	# 	return True
	#
	# @Serialized()
	# def showInternationalizationPanel(self) -> bool :
	# 	return True
	#
	# @Serialized()
	# def showJavaPanel(self) -> bool :
	# 	return True
	#
	# @Serialized()
	# def showDataModelPanel(self) -> bool :
	# 	return True
	#
	# @Serialized()
	# def showGitPanel(self) -> bool :
	# 	return True

	test: str = Serialized(
		default='Test',
		decorators=[pd.Title('Test')],
		shouldSerialize=False
	)


@RegisterContainer
class CopyrightSettings(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		pass

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=True, label='Copyright ©')
	def copyright(self) -> str :
		return """<font>Copyright (c) 2021 Joachim Coenen. All Rights Reserved
		<br/>Written and maintained by Joachim Coenen. 
		<br/>If you have any questions, bugs or improvements, share them on GitHub.
		<br/><br/><i>Intended for INTERNAL use only!<i/>
		</font>"""

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, label='License')
	def license(self) -> str :
		return ' --- '


@RegisterContainer
class ApplicationSettings(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.applicationName: str = ''
		self.appearance: AppearanceSettings = AppearanceSettings()
		self.debugging: DebugSettings = DebugSettings()
		self.copyright: CopyrightSettings = CopyrightSettings()
		self.isUserSetupFinished: bool = False

	@pd.NoUI()
	@Computed()
	def applicationName(self) -> str:
		return 'Minecraft Datapack Editor'

	@Serialized(label='Appearance')
	def appearance(self) -> AppearanceSettings:
		return AppearanceSettings()

	@Serialized(label='Debugging')
	def debugging(self) -> DebugSettings :
		return DebugSettings()

	@Serialized(label='Copyright & License')
	def copyright(self) -> CopyrightSettings :
		return CopyrightSettings()

	@pd.NoUI()
	@Serialized()
	def isUserSetupFinished(self) -> bool:
		return False

applicationSettings = ApplicationSettings()


def _getSettingsPath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'settings.json')


def setApplicationSettings(newSettings: ApplicationSettings):
	global applicationSettings
	applicationSettings.copyFrom(copy.deepcopy(newSettings))



def saveApplicationSettings():
	with open(_getSettingsPath(), 'w', encoding='utf-8') as settingsFile:
		applicationSettings.toJSON(settingsFile)


def loadApplicationSettings():
	try:
		with open(_getSettingsPath(), "r", encoding='utf-8') as settingsFile:
			newSettings = applicationSettings.fromJSON(settingsFile.read(), onError=logError)
		setApplicationSettings(newSettings)
	except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load settings: \n{traceback.format_exc()}')


__all__ = (
	'ProfilingSettings',
	'AppearanceSettings',
	'DebugSettings',
	'CopyrightSettings',
	'ApplicationSettings',
	'applicationSettings',

	'setApplicationSettings',
	'saveApplicationSettings',
	'loadApplicationSettings',
)