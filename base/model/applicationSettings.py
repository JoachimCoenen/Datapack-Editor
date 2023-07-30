from __future__ import annotations

import copy
import enum
import os
import traceback
from abc import ABC
from dataclasses import dataclass, field, fields
from json import JSONDecodeError
from typing import final, Iterator, TypeVar, Any, Callable, cast

from PyQt5.Qsci import QsciScintillaBase
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.GUI import getStyles
from Cat.Serializable.dataclassJson import SerializableDataclass, shouldSerialize, catMeta
from Cat.utils import getExePath
from Cat.utils.formatters import formatVal
from Cat.utils.profiling import logError
from PyQt5.QtWidgets import QStyleFactory


QFont.__deepcopy__ = lambda x, m: QFont(x)

# from model.data.mcVersions import ALL_MC_VERSIONS
# from model.data.dpVersion import ALL_DP_VERSIONS
from base.model.aspect import AspectDict, Aspect, AspectType


class ColorSchemePD(pd.PropertyDecorator):
	pass


class WhitespaceVisibility(enum.IntEnum):
	Invisible = QsciScintillaBase.SCWS_INVISIBLE
	AlwaysVisible = QsciScintillaBase.SCWS_VISIBLEALWAYS
	VisibleAfterIndent = QsciScintillaBase.SCWS_VISIBLEAFTERINDENT
	VisibleOnlyInIndent = QsciScintillaBase.SCWS_VISIBLEONLYININDENT


@dataclass()
class AppearanceSettings(SerializableDataclass):
	applicationStyle: str = field(
		default='Fusion',
		metadata=catMeta(
			kwargs=dict(label='Application Style'),
			decorators=[
				pd.ComboBox(choices=QStyleFactory.keys()),
				pd.NoUI()
			]
		)
	)

	useCompactLayout: bool = field(
		default=False,
		metadata=catMeta(
			kwargs=dict(
				label='Compact layout',
				tip="Merges title bar & toolbar.",
			),
			decorators=[pd.ToggleSwitch()]
		)
	)

	fontSize: float = field(
		default=10.,
		metadata=catMeta(
			kwargs=dict(label='Font Size', min=4, max=36, step=1.0, decimals=0, suffix=' pt'),
			decorators=[],
		)
	)

	fontFamily: str = field(
		default='Segoe UI',
		metadata=catMeta(
			kwargs=dict(label='Font'),
			decorators=[pd.FontFamily(QFontDatabase.Latin, smoothlyScalable=True)],
		)
	)

	@property
	def font(self) -> QFont:
		font = QFont(self.fontFamily)
		font.setPointSizeF(self.fontSize)
		return font

	colorScheme: str = field(
		default='',
		metadata=catMeta(
			kwargs=dict(label='Color Scheme'),
			decorators=[ColorSchemePD()],
		)
	)

	monospaceFontFamily: str = field(
		default='Consolas',
		metadata=catMeta(
			kwargs=dict(label='Monospace Font'),
			decorators=[
				pd.FontFamily(QFontDatabase.Latin, smoothlyScalable=True, fixedPitch=True),
				pd.Title("Code View")
			],
		)
	)

	@property
	def monospaceFont(self) -> QFont:
		font = QFont(self.monospaceFontFamily)
		font.setPointSizeF(self.fontSize)
		return font

	whitespaceVisibility: WhitespaceVisibility = field(
		default=WhitespaceVisibility.VisibleOnlyInIndent,
		metadata=catMeta(
			kwargs=dict(
				label='Whitespace Visibility',
				tip="How whitespace should be displayed.",
			),
		)
	)


def _getColorScheme(self) -> str:
	return getattr(self, '_colorScheme', '') or 'Default'


def _setColorScheme(self, newVal: str) -> None:
	from gui.themes import theme
	if applicationSettings is not None and applicationSettings.appearance is self:
		oldVal = getattr(self, '_colorScheme', None)
		if newVal != oldVal:
			theme.setCurrentColorScheme(newVal)
	setattr(self, '_colorScheme',  newVal)


AppearanceSettings.colorScheme = property(_getColorScheme, _setColorScheme)


# @RegisterContainer
# class MinecraftSettings(SerializableContainer):
# 	__slots__ = ()
# 	version: str = Serialized(
# 		label='Minecraft Version',
# 		default='1.17',
# 		decorators=[
# 			pd.ComboBox(choices=ALL_MC_VERSIONS.keys()),
# 		],
# 		shouldSerialize=True
# 	)
# 	dpVersion: str = Serialized(
# 		label='Datapack Version',
# 		default='6',
# 		decorators=[
# 			pd.ComboBox(choices=ALL_DP_VERSIONS.keys()),
# 		],
# 		shouldSerialize=True
# 	)
#
# 	executable: str = Serialized(
# 		label='Minecraft Executable',
# 		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/versions/1.17.1/1.17.1.jar').replace('\\', '/'),
# 		decorators=[
# 			pd.FilePath([('jar', '.jar')]),
# 			pd.Validator(minecraftJarValidator)
# 		]
# 	)
#
# 	savesLocation: str = Serialized(
# 		label="Datapack Dependencies Location",
# 		tip="DPE will search in this directory to resolve dependencies",
# 		default_factory=lambda: os.path.expanduser('~/.dpe/dependencies').replace('\\', '/'),
# 		decorators=[
# 			pd.FolderPath(),
# 			pd.Validator(folderPathValidator)
# 		]
# 	)


@dataclass()
class DebugSettings(SerializableDataclass):

	isDeveloperMode: bool = field(
		default=False,
		metadata=catMeta(
			decorators=[
				pd.ToggleSwitch(),
				pd.Title('Developer Mode')
			]
		)
	)

	showUndoRedoPane: bool = field(default=False, metadata=catMeta(decorators=[pd.ToggleSwitch()]))

	test: str = field(
		default='Test',
		metadata=catMeta(
			decorators=[pd.Title('Test')],
			serialize=False
		)
	)


@final
class AboutQt:
	"""
	Just a placeholder for the aboutQt dialog.
	"""
	pass


@dataclass()
class AboutSettings(SerializableDataclass):
	pass  # TODO AboutSettings

	title: str = field(default="Datapack Editor", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', style=getStyles().title), decorators=[pd.ReadOnlyLabel()]))

	version: str = field(default="""0.3.0-alpha""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Version'), decorators=[pd.ReadOnlyLabel()]))

	# @pd.NoUI()
	@property
	def organization(self) -> str:
		return """Joachim Coenen"""

	copyright: str = field(default="""<font>© 2021 Joachim Coenen. All Rights Reserved</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label='Copyright'), decorators=[pd.ReadOnlyLabel()]))
	about: str = field(default="""<font>Written and maintained by <a href="https://www.github.com/JoachimCoenen">Joachim Coenen</a>.\n<br/>If you have any questions, bugs or improvements, please share them on GitHub.\n</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	# @pd.ReadOnlyLabel()
	# @Serialized(serialize=False, wordWrap=True, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True)
	# def about(self) -> str:
	# 	return """<font>Written and maintained by <a href="https://www.github.com/JoachimCoenen">Joachim Coenen</a>.\n<br/>If you have any questions, bugs or improvements, please share them on GitHub.\n</font>"""

	homepage: str = field(default="""<font><a href="https://www.github.com/JoachimCoenen/Datapack-Editor">github.com/JoachimCoenen/Datapack-Editor</a></font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Homepage', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	disclaimer: str = field(default="""<font>Some information is taken from the Minecraft Wiki (see <a href="https://minecraft.gamepedia.com/Minecraft_Wiki:General_disclaimer">Minecraft Wiki:General disclaimer</a>).</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Disclaimer', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	affiliation: str = field(default="""<font>This program is not affiliated with Mojang Studios.</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	aboutQt: AboutQt = field(default_factory=AboutQt, metadata=catMeta(serialize=False, kwargs=dict(label=' ')))


def _fillSettingsAspects(aspectsDict: AspectDict):
	from base.plugin import PLUGIN_SERVICE
	for plugin in PLUGIN_SERVICE.activePlugins:
		for aspectCls in plugin.settingsAspects():
			aspectsDict.add(aspectCls)


@dataclass
class SettingsAspect(Aspect, SerializableDataclass, ABC):
	def reset(self):
		pass


@dataclass()
class ApplicationSettings(SerializableDataclass):
	aspects: AspectDict[SettingsAspect] = field(default_factory=lambda: AspectDict(SettingsAspect), metadata=catMeta(serialize=False))
	unknownSettings: dict[str, Any] = field(default_factory=dict, metadata=catMeta(serialize=False))

	# def __post_init__(self):
	# 	_fillSettingsAspects(self.aspects)

	def serializeJson(self, strict: bool, memo: dict, path: tuple[str | int, ...]) -> dict[str, Any]:
		result = super(ApplicationSettings, self).serializeJson(strict, memo, path)
		result['aspects'] = self._serializeAspects(strict)
		return result

	def _serializeAspects(self, strict: bool) -> dict[str, Any]:
		result = {}
		result |= self.unknownSettings

		for aspect in self.aspects:
			key = aspect.getAspectType()
			memo = {}
			value = aspect.serializeJson(strict, memo, ('aspects', key,))
			result[key] = value
		return result

	@classmethod
	def fromJSONDict(cls: ApplicationSettings, jsonDict: dict[str, dict], memo: dict, path: tuple[str | int, ...], onError: Callable[[Exception, str], None] = None) -> ApplicationSettings:
		self = cast(ApplicationSettings, super(ApplicationSettings, cls).fromJSONDict(jsonDict, memo, path, onError=onError))
		aspectsJson = jsonDict.get('aspects', {}).copy()
		for aspectType, aspectJson in aspectsJson.items():
			self.loadAspectSettings(aspectType, aspectJson, onError)
		return self

	def loadAspectSettings(self, aspectType: AspectType, aspectJson: dict[str, dict], onError: Callable[[Exception, str], None] = None):
		aspect = self.aspects._aspects.get(aspectType)
		if aspect is not None:
			memo = {}
			try:
				newAspect = aspect.fromJSONDict(aspectJson, memo, ('aspects', aspectType), onError=onError)
			except Exception as e:
				if True and onError is not None:
					onError(e, f'{formatVal(type(aspect))} in {type(type(aspect)).__name__}')
					newAspect = None
				else:
					print(f"ERROR  : f'{formatVal(type(aspect))} in {type(type(aspect)).__name__}")
					raise
			if newAspect is not None:
				copyAppSettings(self.aspects.get(type(aspect)), newAspect)
				return
		self.unknownSettings[aspectType] = aspectJson  # we could not find an appropriate settingsAspect, so, just remember the, values

	appearance: AppearanceSettings = field(default_factory=AppearanceSettings, metadata=catMeta(kwargs=dict(label='Appearance')))
	# minecraft: MinecraftSettings = Serialized(default_factory=MinecraftSettings, label='Minecraft')
	debugging: DebugSettings = field(default_factory=DebugSettings, metadata=catMeta(kwargs=dict(label='Debugging')))
	about: AboutSettings = field(default_factory=AboutSettings, metadata=catMeta(kwargs=dict(label='About')))

	applicationName: str = field(default='Minecraft Datapack Editor', metadata=catMeta(decorators=[pd.NoUI()]))

	@property
	def version(self) -> str:
		return self.about.version

	@property
	def organization(self) -> str:
		return self.about.organization

	isUserSetupFinished: bool = field(default=False, metadata=catMeta(decorators=[pd.NoUI()]))


applicationSettings = None
applicationSettings = ApplicationSettings()


def _getSettingsPath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'settings.json')


def getApplicationSettings() -> ApplicationSettings:
	return applicationSettings


def setApplicationSettings(newSettings: ApplicationSettings):
	global applicationSettings
	copyAppSettings(applicationSettings, copy.deepcopy(newSettings))
	#applicationSettings.copyFrom(copy.deepcopy(newSettings))


_TT = TypeVar('_TT')
_TU = TypeVar('_TU')


def createCopy(otherVal: _TT) -> Iterator[_TT]:
	if isinstance(otherVal, SerializableDataclass):
		return createCopySerializableDataclass(otherVal)
	elif isinstance(otherVal, list):
		return createCopyList(otherVal)
	elif isinstance(otherVal, dict):
		return createCopyDict(otherVal)
	else:
		return createCopySimple(otherVal)


def createCopySerializableDataclass(other: SerializableDataclass) -> Iterator[SerializableDataclass]:
	self = type(other)()
	yield self
	copyAppSettings(self, other)


def createCopyList(other: list[_TT]) -> Iterator[list[_TT]]:
	self = type(other)()
	yield self
	for otherVal in other:
		selfValIt = createCopy(otherVal)
		self.append(next(selfValIt))
		next(selfValIt, None)


def createCopyDict(other: dict[_TU, _TT]) -> Iterator[dict[_TU, _TT]]:
	self = type(other)()
	yield self
	for otherKey, otherVal in other.items():
		selfKeyIt = createCopy(otherKey)
		selfValIt = createCopy(otherVal)
		selfKey = next(selfKeyIt)
		next(selfKeyIt, None)
		self[selfKey] = next(selfValIt)
		next(selfValIt, None)


def createCopySimple(other: list[_TT]) -> Iterator[list[_TT]]:
	self = copy.deepcopy(other)
	yield self


def copyAppSettings(self: SerializableDataclass, other: SerializableDataclass) -> None:
	"""sets self to a shallow copy of other"""
	if self is other:  # handle singletons
		return
	if not isinstance(other, SerializableDataclass):
		raise ValueError(f"expected a SerializableDataclass, but got {other}")
	for aField in fields(self):
		if shouldSerialize(aField, None):
			otherVal = getattr(other, aField.name)
			selfValIt = createCopy(otherVal)
			setattr(self, aField.name, next(selfValIt))
			next(selfValIt, None)

	if isinstance(self, ApplicationSettings):
		assert isinstance(other, ApplicationSettings)
		for aspect in self.aspects._aspects.copy().values():
			otherAspect = other.aspects.get(type(aspect))
			copyAppSettings(aspect, otherAspect)
		self.unknownSettings = other.unknownSettings.copy()


def saveApplicationSettings():
	with open(_getSettingsPath(), 'w', encoding='utf-8') as settingsFile:
		applicationSettings.dumpJson(settingsFile)


def loadApplicationSettings():
	try:
		with open(_getSettingsPath(), "r", encoding='utf-8') as settingsFile:
			newSettings = applicationSettings.fromJson(settingsFile.read(), onError=logError)
		setApplicationSettings(newSettings)
	except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load settings: \n{traceback.format_exc()}')


__all__ = (
	'AppearanceSettings',
	'DebugSettings',
	'AboutSettings',
	'ApplicationSettings',
	'applicationSettings',

	'getApplicationSettings',

	'setApplicationSettings',
	'saveApplicationSettings',
	'loadApplicationSettings',
)