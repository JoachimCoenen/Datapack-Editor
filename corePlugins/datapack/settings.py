import os
from dataclasses import dataclass, field

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable.dataclassJson import catMeta
from base.model.applicationSettings import SettingsAspect
from base.model.aspect import AspectType

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')


@dataclass()
class DatapackSettings(SettingsAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	# dpVersion: str = field(
	# 	default='6',
	# 	metadata=catMeta(
	# 		kwargs=dict(label='Datapack Version'),
	# 		decorators=[
	# 			pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys())),
	# 		]
	# 	)
	# )

	dependenciesLocation: str = field(
		default_factory=lambda: os.path.expanduser('~/.dpe/dependencies').replace('\\', '/'),
		metadata=catMeta(
			kwargs=dict(
				label="Datapack Dependencies Location",
				tip="DPE will search in this directory to resolve dependencies",
			),
			decorators=[
				pd.FolderPath(),
				pd.Validator(pd.folderPathValidator)
			]
		)
	)
