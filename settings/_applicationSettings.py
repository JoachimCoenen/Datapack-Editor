from __future__ import annotations

import copy
import os
import traceback
from json import JSONDecodeError
from typing import Optional, final
from zipfile import ZipFile

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from Cat.CatPythonGUI.GUI import getStyles
from Cat.Serializable import Computed, RegisterContainer, SerializableContainer, Serialized
from Cat.Serializable.serializedProperty import ComputedCached
from Cat.utils import getExePath
from Cat.utils.profiling import logError
from PyQt5.QtWidgets import QStyleFactory


QFont.__deepcopy__ = lambda x, m: QFont(x)

from model.data.mcVersions import ALL_MC_VERSIONS


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
		tip="Merges title bar & toolbar.",
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


def folderPathValidator(path: str) -> Optional[ValidatorResult]:
	if not os.path.lexists(path):
		return ValidatorResult('Folder not found', 'error')

	if not os.path.isdir(path):
		return ValidatorResult('Not a directory', 'error')

	return None


def jarPathValidator(path: str) -> Optional[ValidatorResult]:
	if not os.path.lexists(path):
		return ValidatorResult('File not found', 'error')

	if not os.path.isfile(path) or os.path.splitext(path)[1].lower() != '.jar':
		return ValidatorResult('Not a .jar File', 'error')

	return None


def minecraftJarValidator(path: str) -> Optional[ValidatorResult]:
	result = jarPathValidator(path)

	if not result:
		try:
			with ZipFile(path, 'r'):
				pass
		except (FileNotFoundError, PermissionError) as e:
			result = ValidatorResult(str(e), 'error')
	return result


@RegisterContainer
class MinecraftSettings(SerializableContainer):
	__slots__ = ()
	version: str = Serialized(
		label='Minecraft Version',
		default='1.17',
		decorators=[
			pd.ComboBox(choices=ALL_MC_VERSIONS.keys()),
		],
		shouldSerialize=True
	)

	executable: str = Serialized(
		label='Minecraft Executable',
		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/versions/1.17.1/1.17.1.jar').replace('\\', '/'),
		decorators=[
			pd.FilePath([('jar', '.jar')]),
			pd.Validator(minecraftJarValidator)
		]
	)

	savesLocation: str = Serialized(
		label="Minecraft Saves Directory",
		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/saves').replace('\\', '/'),
		decorators=[
			pd.FolderPath(),
			pd.Validator(folderPathValidator)
		]
	)


@RegisterContainer
class DebugSettings(SerializableContainer):
	__slots__ = ()

	isDeveloperMode: bool = Serialized(
		default=False,
		decorators=[
			pd.ToggleSwitch(),
			pd.Title('Developer Mode')
		]
	)

	showUndoRedoPane: bool = Serialized(default=False, decorators=[pd.ToggleSwitch()])

	test: str = Serialized(
		default='Test',
		decorators=[pd.Title('Test')],
		shouldSerialize=False
	)


@final
class AboutQt:
	"""
	Just a placeholder for the aboutQt dialog.
	"""
	pass

@RegisterContainer
class AboutSettings(SerializableContainer):
	__slots__ = ()

	@pd.ReadOnlyLabel()
	@Computed(shouldSerialize=False, wordWrap=False, label=' ', style=getStyles().title)
	def title(self) -> str:
		return "Datapack Editor"

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=False, label='Version')
	def version(self) -> str:
		return """0.2.1-alpha"""

	organization: str = Computed(default="""Joachim Coenen""", decorators=[pd.NoUI()])

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=True, label='Copyright')
	def copyright(self) -> str:
		return """<font>© 2021 Joachim Coenen. All Rights Reserved</font>"""

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=True, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True)
	def about(self) -> str:
		return """<font>Written and maintained by <a href="https://www.github.com/JoachimCoenen">Joachim Coenen</a>. 
		<br/>If you have any questions, bugs or improvements, please share them on GitHub.
		</font>"""

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=False, label='Homepage', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True)
	def homepage(self) -> str:
		return """<font><a href="https://www.github.com/JoachimCoenen/Datapack-Editor">github.com/JoachimCoenen/Datapack-Editor</a></font>"""

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=False, label='Disclaimer', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True)
	def disclaimer(self) -> str:
		return """<font>Some contents are from the Minecraft Wiki (see <a href="https://minecraft.gamepedia.com/Minecraft_Wiki:General_disclaimer">Minecraft Wiki:General disclaimer</a>).</font>"""

	@pd.ReadOnlyLabel()
	@Serialized(shouldSerialize=False, wordWrap=False, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True)
	def affiliation(self) -> str:
		return """<font>This program is <em>not</em> affiliated with Mojang Studios.</font>"""

	@Serialized(shouldSerialize=False, label=' ')
	def aboutQt(self) -> AboutQt:
		return AboutQt()


@RegisterContainer
class ApplicationSettings(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.applicationName: str = ''
		self.appearance: AppearanceSettings = AppearanceSettings()
		self.minecraft: MinecraftSettings = MinecraftSettings()
		self.debugging: DebugSettings = DebugSettings()
		self.about: AboutSettings = AboutSettings()
		self.isUserSetupFinished: bool = False

	appearance: AppearanceSettings = Serialized(default_factory=AppearanceSettings, label='Appearance')
	minecraft: MinecraftSettings = Serialized(default_factory=MinecraftSettings, label='Minecraft')
	debugging: DebugSettings = Serialized(default_factory=DebugSettings, label='Debugging')
	about: AboutSettings = Serialized(default_factory=AboutSettings, label='About')

	applicationName: str = Computed(default='Minecraft Datapack Editor', decorators=[pd.NoUI()])
	version: str = about.version
	organization: str = about.organization

	isUserSetupFinished: bool = Serialized(default=False, decorators=[pd.NoUI()])

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
	'AppearanceSettings',
	'DebugSettings',
	'AboutSettings',
	'ApplicationSettings',
	'applicationSettings',

	'setApplicationSettings',
	'saveApplicationSettings',
	'loadApplicationSettings',
)