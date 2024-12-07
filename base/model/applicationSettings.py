from __future__ import annotations

import copy
import enum
import os
import traceback
from abc import ABC
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import final, Type, Optional, Callable

from PyQt5.Qsci import QsciScintillaBase
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon

from base.model.application import getApp
from cat.GUI import getStyles, propertyDecorators as pd
from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.utils import getExePath, override
from cat.utils.profiling import logError

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


@dataclass
class AppearanceSettings(SerializableDataclass):

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
	return getattr(self, '_colorScheme', '') or 'Default Dark'


def _setColorScheme(self, newVal: str) -> None:
	if applicationSettings is not None and getApplicationSettings().appearance is self:
		oldVal = getattr(self, '_colorScheme', None)
		if newVal != oldVal:
			theme.setCurrentColorScheme(newVal)
	setattr(self, '_colorScheme',  newVal)


AppearanceSettings.colorScheme = property(_getColorScheme, _setColorScheme)


@dataclass
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


@dataclass
class AboutSettings(SerializableDataclass):

	title: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', style=property(lambda s: getStyles().title)), decorators=[pd.ReadOnlyLabel()]))
	icon: QIcon = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(label=' ', iconScale=4.0), decorators=[pd.ReadOnlyLabel()]))
	version: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Version'), decorators=[pd.ReadOnlyLabel()]))
	copyright: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label='Copyright'), decorators=[pd.ReadOnlyLabel()]))
	about: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))
	homepage: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Homepage', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))
	disclaimer: str = field(init=False, metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Disclaimer', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))
	# affiliation: str = field(default="""<font>This program is not affiliated with Mojang Studios.</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	catCodeEditorTitle: str = field(default="Cat Code Editor", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', style=property(lambda s: getStyles().title)), decorators=[pd.ReadOnlyLabel()]))

	catCodeEditorUsage: str = field(default=f"<font>This App is based on the Cat Code Editor.</font>", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))
	catCodeEditorVersion: str = field(default="0.8.0-alpha", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Version'), decorators=[pd.ReadOnlyLabel()]))
	catCodeEditorCopyright: str = field(default="© 2024 Joachim Coenen. All Rights Reserved", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label='Copyright'), decorators=[pd.ReadOnlyLabel()]))
	catCodeEditorAbout: str = field(default="""<font>Written and maintained by <a href="https://www.github.com/JoachimCoenen">Joachim Coenen</a>.\n<br/>If you have any questions, bugs or improvements, please share them on GitHub.\n</font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=True, label=' ', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))
	catCodeEditorHomepage: str = field(default="""<font><a href="https://www.github.com/JoachimCoenen/Datapack-Editor">github.com/JoachimCoenen/Datapack-Editor</a></font>""", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label='Homepage', textInteractionFlags=Qt.TextBrowserInteraction, openExternalLinks=True), decorators=[pd.ReadOnlyLabel()]))

	qtTitle: str = field(default="Qt5", metadata=catMeta(serialize=False, kwargs=dict(wordWrap=False, label=' ', style=property(lambda s: getStyles().title)), decorators=[pd.ReadOnlyLabel()]))

	aboutQt: AboutQt = field(default_factory=AboutQt, metadata=catMeta(serialize=False, kwargs=dict(label=' ')))


AboutSettings.title = property(lambda s: getApp().info.appDisplayName, lambda s, x: None)
AboutSettings.icon = property(lambda s: getApp().info.windowIcon(), lambda s, x: None)
AboutSettings.version = property(lambda s: getApp().info.appVersion, lambda s, x: None)
AboutSettings.copyright = property(lambda s: f"<font>{getApp().info.copyright}</font>", lambda s, x: None)
AboutSettings.about = property(lambda s: f"<font>{getApp().info.about}</font>", lambda s, x: None)
AboutSettings.homepage = property(lambda s: f"""<font><a href="{getApp().info.homepageLink}">{getApp().info.homepageLink}</a></font>""", lambda s, x: None)
AboutSettings.disclaimer = property(lambda s: f"""<font>{getApp().info.disclaimer if getApp().info.disclaimer is not None else '---'}</font>""", lambda s, x: None)
# AboutSettings.disclaimer = property(lambda s: f"<font>{getApp().info.disclaimer}</font>", lambda s, x: None)
# AboutSettings.about = property(lambda s: f"<font>{getApp().info.about}</font>", lambda s, x: None)
# AboutSettings.version = property(lambda s: getApp().info.appVersion, lambda s, x: None)


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
	debugging: DebugSettings = field(default_factory=DebugSettings, metadata=catMeta(kwargs=dict(label='Debugging')))
	about: AboutSettings = field(default_factory=AboutSettings, metadata=catMeta(kwargs=dict(label='About')))

	isUserSetupFinished: bool = field(default=False, metadata=catMeta(decorators=[pd.NoUI()]))

	def __post_init__(self):
		for aspectCls in getAspectsForClass(type(self)).values():
			self.aspects.add(aspectCls)

	@override
	def _setAspect(self, newAspect: SettingsAspect):
		self.aspects.get(type(newAspect)).copyFrom(newAspect)

	@override
	def _getAspectCls(self, aspectType: AspectType) -> Optional[Type[SettingsAspect]]:
		aspect = self.aspects._aspects.get(aspectType)
		return type(aspect) if aspect is not None else None


applicationSettings = None
applicationSettings: ApplicationSettings = ApplicationSettings()


def _getSettingsPath() -> str:
	return os.path.join(os.path.dirname(getExePath()), 'settings.json')


def getApplicationSettings() -> ApplicationSettings:
	return applicationSettings


def setApplicationSettings(newSettings: ApplicationSettings):
	global applicationSettings
	applicationSettings.copyFrom(copy.deepcopy(newSettings))


def resetApplicationSettings():
	setApplicationSettings(ApplicationSettings())


def saveApplicationSettings():
	with open(_getSettingsPath(), 'w', encoding='utf-8') as settingsFile:
		getApplicationSettings().dumpJson(settingsFile)


def loadApplicationSettings():
	try:
		with open(_getSettingsPath(), "r", encoding='utf-8') as settingsFile:
			newSettings = getApplicationSettings().fromJson(settingsFile.read(), onError=logError)
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
