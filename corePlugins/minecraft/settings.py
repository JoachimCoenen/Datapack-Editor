import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from PyQt5.QtGui import QIcon

from base.model.searchUtils import filterComputedChoices
from base.model.utils import addStyle, formatMarkdown, wrapInMDCode
from cat.GUI import propertyDecorators as pd
from cat.GUI.propertyDecorators import ValidatorResult
from cat.GUI.components.treeBuilders import DataListBuilder, StringHeaderBuilder
from cat.GUI.pythonGUI import WidgetDrawer
from cat.Serializable.serializableDataclasses import catMeta, SerializableDataclass

from base.model.applicationSettings import SettingsAspect
from base.model.aspect import AspectType
from cat.utils import PLATFORM_IS_WINDOWS, escapeForXmlTextContent
from corePlugins.minecraft_data.fullData import getAllFullMcDatas, getLatestFullMcData
from gui.datapackEditorGUI import EditableSerializableDataclassList, DatapackEditorGUI

MINECRAFT_ASPECT_TYPE = AspectType('dpe:minecraft')


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
			with open(path, 'r'):
				pass
		except OSError as e:
			result = ValidatorResult(str(e), 'error')
	return result


def minecraftVersionValidator(version: str) -> Optional[ValidatorResult]:
	if not version.strip():
		return ValidatorResult(f"Please select a Minecraft version.", 'error')
	if version not in getAllFullMcDatas():
		return ValidatorResult(f"No Minecraft version '{version}' known.", 'error')
	return None


def getDefaultMcExecutablePath(versionName: str) -> str:
	if PLATFORM_IS_WINDOWS:
		return os.path.expanduser(f'~/AppData/Roaming/.minecraft/versions/{versionName}/{versionName}.jar').replace('\\', '/')
	else:
		import platform
		raise ValueError(f"This operating system ({platform.system()}) is currently not supported.")  # TODO: add support for other operating systems


@dataclass
class MinecraftVersion(SerializableDataclass):
	name: str = field(
		default_factory=lambda: getLatestFullMcData().name,  # by default selects the latest version
		metadata=catMeta(
			kwargs=dict(label='Name'),
			decorators=[]
		)
	)

	version: str = field(
		default_factory=lambda: getLatestFullMcData().name,  # by default selects the latest version
		metadata=catMeta(
			kwargs=dict(label='Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda x: sorted(getAllFullMcDatas().keys())), editable=True),
				pd.Validator(minecraftVersionValidator)
			]
		)
	)

	minecraftExecutable: str = field(
		default_factory=lambda: getDefaultMcExecutablePath(getLatestFullMcData().name),
		metadata=catMeta(
			kwargs=dict(label='Executable'),
			decorators=[
				pd.FilePath([('jar', '.jar')]),
				pd.Validator(minecraftJarValidator)
			]
		)
	)


@WidgetDrawer(MinecraftVersion)
def minecraftVersionDrawer(gui: DatapackEditorGUI, mcVersion: MinecraftVersion, **kwargs) -> MinecraftVersion:
	gui.propertyField(mcVersion, 'name', **kwargs)

	oldVersion = mcVersion.version
	gui.propertyField(mcVersion, 'version', **kwargs)
	newVersion = mcVersion.version

	if oldVersion != newVersion:
		if mcVersion.name == oldVersion or not mcVersion.name.strip():
			mcVersion.name = newVersion
		if mcVersion.minecraftExecutable == getDefaultMcExecutablePath(oldVersion):
			mcVersion.minecraftExecutable = getDefaultMcExecutablePath(newVersion)

	gui.propertyField(mcVersion, 'minecraftExecutable', **kwargs)

	return mcVersion


def _validateMcVersionAndCheckDuplicate(mv: MinecraftVersion, mcVersions: list[MinecraftVersion]) -> list[ValidatorResult]:
	# TODO: Checking for duplicates only works properly when list is not filtered, because `mcVersions` only contains the filtered list of versions.
	duplicatesExist = len([v for v in mcVersions if v.name.strip() == mv.name.strip()]) > 1

	valResult = mv.validate()
	if duplicatesExist:
		valResult.append(ValidatorResult('There are multiple Minecraft versions registered with the same name.', 'warning'))
	return valResult


def _iconMakerMaker(mcVersions: list[MinecraftVersion]) -> Callable[[MinecraftVersion, int], Optional[QIcon]]:
	def _iconMaker(mv: MinecraftVersion, c: int) -> Optional[QIcon]:
		if c != 0:
			return None
		valResult = _validateMcVersionAndCheckDuplicate(mv, mcVersions)
		if valResult:
			maxErrorStyle = max(valResult, key=lambda r: {'info': 10, 'warning': 20, 'error': 30}.get(r.style, 40)).style
			return DatapackEditorGUI.getErrorIcon(maxErrorStyle)
		return None

	return _iconMaker


def _toolTipMakerMaker(mcVersions: list[MinecraftVersion]) -> Callable[[MinecraftVersion, int], Optional[str]]:
	def _toolTipMaker(mv: MinecraftVersion, c: int=0) -> Optional[str]:
		valResult = _validateMcVersionAndCheckDuplicate(mv, mcVersions)
		tips = [f"<nobr>{formatMarkdown(wrapInMDCode(mv.minecraftExecutable))}</nobr>"]
		tips += [f"<p>{addStyle(escapeForXmlTextContent(e.message), style=e.style)}</p>" for e in valResult]
		return '\n'.join(tips)

	return _toolTipMaker


@dataclass()
class MinecraftSettings(SettingsAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return MINECRAFT_ASPECT_TYPE

	minecraftVersions: list[MinecraftVersion] = field(
		default_factory=list,
		metadata=catMeta(
			kwargs=dict(label='Minecraft Versions'),
			decorators=[
				EditableSerializableDataclassList(
					'minecraftVersions',
					lambda mcVersions: DataListBuilder(
						mcVersions,
						labelMaker=lambda mv, c: (mv.name, mv.version, mv.minecraftExecutable)[c],
						iconMaker=_iconMakerMaker(mcVersions),
						toolTipMaker=_toolTipMakerMaker(mcVersions),
						onCopy=_toolTipMakerMaker(mcVersions),
						columnCount=3,
						getId=id
					),
					headerBuilderBuilder=lambda: StringHeaderBuilder(('Name', 'Version', 'Executable')),
					getStrChoices=lambda items: [mv.name for mv in items],
					filterFunc=filterComputedChoices(lambda mv: mv.name),
					dialogWidth=800
				),
				pd.Title("Minecraft Versions"),
			]
		)
	)


# def _getMinecraftVersion(self) -> str:
# 	return getattr(self, '_minecraftVersion', '') or 'Default'
#
#
# def _setMinecraftVersion(self, newVal: str) -> None:
# 	applicationSettings = getApplicationSettings()
# 	if applicationSettings is not None and applicationSettings.aspects.get(MinecraftSettings) is self:
# 		oldVal = getattr(self, '_minecraftVersion', None)
# 		if True or newVal != oldVal:
# 			mcVersion = getMCVersion(oldVal)
# 			if mcVersion is not None:
# 				mcVersion.deactivate()
# 			mcVersion = getMCVersion(newVal)
# 			if mcVersion is not None:
# 				mcVersion.activate()
# 	setattr(self, '_minecraftVersion',  newVal)
#
#
# MinecraftSettings.minecraftVersion = property(_getMinecraftVersion, _setMinecraftVersion)
