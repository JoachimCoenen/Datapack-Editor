import os
from dataclasses import dataclass, field
from typing import Optional

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder
from Cat.Serializable.dataclassJson import catMeta, SerializableDataclass

from base.model.applicationSettings import SettingsAspect
from base.model.aspect import AspectType
from gui.datapackEditorGUI import EditableSerializableDataclassList, filterComputedChoices

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


@dataclass()
class MinecraftVersion(SerializableDataclass):
	name: str = field(
		default='1.17',
		metadata=catMeta(
			kwargs=dict(label='Name'),
			decorators=[]
		)
	)

	minecraftExecutable: str = field(
		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/versions/1.17.1/1.17.1.jar').replace('\\', '/'),
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
						labelMaker=lambda mv, c: (mv.name, mv.minecraftExecutable)[c],
						iconMaker=None,
						toolTipMaker=lambda mv, c: mv.minecraftExecutable,
						columnCount=2,
						getId=id
					),
					getStrChoices=lambda items: [mv.name for mv in items],
					filterFunc=filterComputedChoices(lambda mv: mv.name),
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