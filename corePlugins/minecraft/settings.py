import os
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtGui import QIcon

from base.model.searchUtils import filterComputedChoices
from cat.GUI import propertyDecorators as pd
from cat.GUI.propertyDecorators import ValidatorResult
from cat.GUI.components.treeBuilders import DataListBuilder, StringHeaderBuilder
from cat.Serializable.serializableDataclasses import catMeta, SerializableDataclass

from base.model.applicationSettings import SettingsAspect
from base.model.aspect import AspectType
from corePlugins.minecraft_data.fullData import getAllFullMcDatas
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
		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/versions/1.20.2/1.20.2.jar').replace('\\', '/'),
		metadata=catMeta(
			kwargs=dict(label='Executable'),
			decorators=[
				pd.FilePath([('jar', '.jar')]),
				pd.Validator(minecraftJarValidator)
			]
		)
	)


class MinecraftVersionsPD(pd.PropertyDecorator):
	pass


def _iconMaker(mv: MinecraftVersion, c: int) -> Optional[QIcon]:
	if c != 0:
		return None
	valResult = mv.validate()
	if valResult:
		maxErrorStyle = max(valResult, key=lambda r: {'info': 10, 'warning': 20, 'error': 30}.get(r.style, 40)).style
		return DatapackEditorGUI.getErrorIcon(maxErrorStyle)
	return None


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
					lambda data: DataListBuilder(
						data,
						labelMaker=lambda mv, c: (mv.name, mv.version, mv.minecraftExecutable)[c],
						iconMaker=_iconMaker,
						toolTipMaker=lambda mv, c: mv.minecraftExecutable,
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
