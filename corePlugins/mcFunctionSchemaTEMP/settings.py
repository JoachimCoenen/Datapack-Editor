import os
from dataclasses import dataclass, field
from typing import Optional
from zipfile import ZipFile

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from Cat.Serializable.dataclassJson import catMeta

from base.model.applicationSettings import SettingsAspect, getApplicationSettings
from base.model.aspect import AspectType
from corePlugins.mcFunctionSchemaTEMP.mcVersions import ALL_MC_VERSIONS, getMCVersion

MINECRAFT_ASPECT_TYPE = AspectType('dpe:minecraft')


ALL_DP_VERSIONS: dict[str, int] = {}


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


@dataclass()
class MinecraftSettings(SettingsAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return MINECRAFT_ASPECT_TYPE

	minecraftVersion: str = field(
		default='1.17',
		metadata=catMeta(
			kwargs=dict(label='Minecraft Version'),
			decorators=[
				pd.ComboBox(choices=ALL_MC_VERSIONS.keys()),
			]
		)
	)

	minecraftExecutable: str = field(
		default_factory=lambda: os.path.expanduser('~/AppData/Roaming/.minecraft/versions/1.17.1/1.17.1.jar').replace('\\', '/'),
		metadata=catMeta(
			kwargs=dict(label='Minecraft Executable'),
			decorators=[
				pd.FilePath([('jar', '.jar')]),
				pd.Validator(minecraftJarValidator)
			]
		)
	)


def _getMinecraftVersion(self) -> str:
	return getattr(self, '_minecraftVersion', '') or 'Default'


def _setMinecraftVersion(self, newVal: str) -> None:
	applicationSettings = getApplicationSettings()
	if applicationSettings is not None and applicationSettings.aspects.get(MinecraftSettings) is self:
		oldVal = getattr(self, '_minecraftVersion', None)
		if True or newVal != oldVal:
			mcVersion = getMCVersion(oldVal)
			if mcVersion is not None:
				mcVersion.deactivate()
			mcVersion = getMCVersion(newVal)
			if mcVersion is not None:
				mcVersion.activate()
	setattr(self, '_minecraftVersion',  newVal)


MinecraftSettings.minecraftVersion = property(_getMinecraftVersion, _setMinecraftVersion)