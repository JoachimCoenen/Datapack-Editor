from __future__ import annotations

import copy
import enum
import os
import traceback
from abc import ABC
from dataclasses import dataclass, field, fields
from json import JSONDecodeError
from typing import final, Iterator, TypeVar, Type, Optional

from PyQt5.Qsci import QsciScintillaBase
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.GUI import getStyles
from Cat.Serializable.dataclassJson import SerializableDataclass, shouldSerialize, catMeta
from Cat.utils import getExePath, override
from Cat.utils.profiling import logError
from PyQt5.QtWidgets import QStyleFactory

from base.model.aspect import AspectDict, Aspect, AspectType, SerializableDataclassWithAspects, getAspectsForClass
from base.model import theme

QFont.__deepcopy__ = lambda x, m: QFont(x)


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
	if applicationSettings is not None and applicationSettings.appearance is self:
		oldVal = getattr(self, '_colorScheme', None)
		if newVal != oldVal:
			theme.setCurrentColorScheme(newVal)
	setattr(self, '_colorScheme',  newVal)


AppearanceSettings.colorScheme = property(_getColorScheme, _setColorScheme)


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

	loadedPlugins: list[tuple[str]] = field(
		init=False,
		metadata=catMeta(
			readOnly=True,
			serialize=False,
			decorators=[pd.Title("Loaded Plugins")],
			kwargs=dict(headers=("plugins",), label=None)
		)
	)


def getLoadedPlugins(self) -> list[tuple[str]]:
	from base.plugin import PLUGIN_SERVICE
	return [(plugin.name,) for plugin in PLUGIN_SERVICE.activePlugins]


DebugSettings.loadedPlugins = property(getLoadedPlugins)


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


@dataclass
class ApplicationSettings(SerializableDataclassWithAspects[SettingsAspect]):

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

	def __post_init__(self):
		for aspectCls in getAspectsForClass(type(self)).values():
			self.aspects.add(aspectCls)

	@override
	def _setAspect(self, newAspect: SettingsAspect):
		copyAppSettings(self.aspects.get(type(newAspect)), newAspect)

	@override
	def _getAspectCls(self, aspectType: AspectType) -> Optional[Type[SettingsAspect]]:
		aspect = self.aspects._aspects.get(aspectType)
		return type(aspect) if aspect is not None else None


applicationSettings = None
applicationSettings = ApplicationSettings()


def _getSettingsPath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'settings.json')


def getApplicationSettings() -> ApplicationSettings:
	return applicationSettings


def setApplicationSettings(newSettings: ApplicationSettings):
	global applicationSettings
	copyAppSettings(applicationSettings, copy.deepcopy(newSettings))


def resetApplicationSettings():
	setApplicationSettings(ApplicationSettings())


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

	if isinstance(self, SerializableDataclassWithAspects):
		assert isinstance(other, SerializableDataclassWithAspects)
		oldSelfAspects: dict[AspectType, Aspect] = self.aspects._aspects.copy()
		self.aspects._aspects.clear()
		otherAspect: Aspect
		for otherAspect in other.aspects._aspects.copy().values():
			# isinstance(otherAspect, Aspect) check only added to not confuse the type checker.
			assert isinstance(otherAspect, SerializableDataclass) and isinstance(otherAspect, Aspect), "Aspect must be SerializableDataclass in order to be copyable."
			selfAspect = oldSelfAspects.pop(otherAspect.getAspectType(), None)
			assert isinstance(selfAspect, SerializableDataclass)
			if selfAspect is None:
				selfAspect = type(otherAspect)()
			self.aspects.add(selfAspect)
			copyAppSettings(selfAspect, otherAspect)


		self.unknownAspects = other.unknownAspects.copy()


def saveApplicationSettings():
	with open(_getSettingsPath(), 'w', encoding='utf-8') as settingsFile:
		applicationSettings.dumpJson(settingsFile)


def loadApplicationSettings():
	try:
		with open(_getSettingsPath(), "r", encoding='utf-8') as settingsFile:
			newSettings = applicationSettings.fromJson(settingsFile.read(), onError=logError)
		setApplicationSettings(newSettings)
	except (JSONDecodeError, OSError, AttributeError, TypeError, RuntimeError) as e:
		logError(f'Unable to load settings: \n{traceback.format_exc()}')


__all__ = (
	'AppearanceSettings',
	'DebugSettings',
	'AboutSettings',
	'SettingsAspect',
	'ApplicationSettings',
	'applicationSettings',

	'getApplicationSettings',
	'setApplicationSettings',
	'resetApplicationSettings',
	'saveApplicationSettings',
	'loadApplicationSettings',
)