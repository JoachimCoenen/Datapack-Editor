import json
import os
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtCore import Qt

import cat.GUI.propertyDecorators as pd
from cat.GUI import SizePolicy
from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.utils.utils import openOrCreate
from base.model.pathUtils import joinFilePath, FilePathStr
from base.model.project.project import Project, ProjectRoot
from base.model.project.projectCreator import ProjectCreator
from .aspect import DatapackAspect, allRegisteredMinecraftVersions, minecraftVersionValidator
from .datapackContents import NAME_SPACE_VAR
from .dpVersions import getAllDPVersions
from corePlugins.minecraft.resourceLocation import isNamespaceValid
from gui.datapackEditorGUI import DatapackEditorGUI


def newProjDirectoryPathValidator(path: str) -> Optional[pd.ValidatorResult]:
	if os.path.lexists(path):
		return pd.ValidatorResult("Project directory already exists.", 'warning')
	return None


def validateNamespace(namespace: str) -> Optional[pd.ValidatorResult]:
	if not isNamespaceValid(namespace):
		return pd.ValidatorResult(
			f"Not a valid namespace.\nNamespaces mut only contain:\n"
			f" - Numbers (0-9)\n"
			f" - Lowercase letters (a-z)\n"
			f" - Underscore (_)\n"
			f" - Hyphen/minus (-)\n"
			f" - dot (.)", 'error'
		)
	return None


@dataclass
class DatapackProjectCreatorData(SerializableDataclass):

	namespace: str = field(
		default='new_datapack',
		metadata=catMeta(
			kwargs=dict(label='Namespace'),
			decorators=[pd.Validator(validateNamespace, textFormat=Qt.TextFormat.MarkdownText)]
		)
	)

	description: str = field(
		default='[{"text": "new_datapack", "color":"white"}, {"text":"\\nCreated with","color":"white"}, {"text":"Data Pack Editor", "color":"yellow"}] ',
		metadata=catMeta(
			kwargs=dict(label='Description', isMultiline=True),
		)
	)

	dpVersion: str = field(
		default='18',
		metadata=catMeta(
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys())),
			]
		)
	)

	minecraftVersion: str = field(
		default='1.20.2',
		metadata=catMeta(
			kwargs=dict(label='Minecraft Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: allRegisteredMinecraftVersions()), editable=True),
				pd.Validator(minecraftVersionValidator),
			]
		)
	)

	generateDependenciesJson: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate dependencies.json'),
		)
	)

	generatePackMcMeta: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate pack.mcmeta'),
		)
	)

	generateSkeleton: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate Skeleton'),
		)
	)


class DatapackProjectCreator(ProjectCreator[DatapackProjectCreatorData]):
	def __init__(self):
		super().__init__(DatapackProjectCreatorData())

	@property
	def title(self) -> str:
		return "Datapack"

	def onGUI(self, gui: DatapackEditorGUI) -> None:
		data = self.data
		gui.propertyField(data, 'namespace')
		gui.propertyField(data, 'description')
		gui.propertyField(data, 'dpVersion')
		gui.propertyField(data, 'minecraftVersion')
		gui.propertyField(data, 'generateDependenciesJson')
		gui.propertyField(data, 'generatePackMcMeta')
		gui.propertyField(data, 'generateSkeleton')
		gui.addVSpacer(0, SizePolicy.Expanding)  # preventVStretch

	def initializeProject(self, gui: DatapackEditorGUI, project: Project) -> None:
		data = self.data
		# setup aspect:
		datapackAspect = project.aspects.get(DatapackAspect)
		datapackAspect.dpVersion = data.dpVersion
		datapackAspect.minecraftVersion = data.minecraftVersion
		# setup structure (roots, etc.)
		newRoot = project.addRoot(ProjectRoot(project.name, project.path))
		# setup files:
		if data.generatePackMcMeta:
			self.generatePackMcMetaFile(newRoot)
		if data.generateDependenciesJson:
			self.generateDependenciesFile(newRoot)
		if data.generateSkeleton:
			self.generateSkeleton(newRoot, project)

	def generatePackMcMetaFile(self, root: ProjectRoot):
		data = self.data
		path = joinFilePath(root.normalizedLocation, 'pack.mcmeta')

		packFormat = data.dpVersion
		try:
			packFormat = int(packFormat)
		except ValueError:
			packFormat = 0  # not great

		jsonData = {
			"pack": {
				"pack_format": packFormat,
				"description": data.description
				}
			}

		createJsonFileFormatted(path, jsonData)

	@staticmethod
	def generateDependenciesFile(root: ProjectRoot):
		path = joinFilePath(root.normalizedLocation, 'dependencies.json')

		jsonData = (
			'[\n'  # just some example data
			'\t{"name": "DatapackUtilities_v3.4.1", "mandatory": False},\n'
			'\t{"name": "another-dependency", "mandatory": False}\n'
			']'
		)

		with openOrCreate(path, 'w') as f:
			f.write(jsonData)

	def generateSkeleton(self, root: ProjectRoot, project: Project):
		datapackPath = root.normalizedLocation
		data = self.data
		dpAspect = project.aspects.get(DatapackAspect)
		structure = dpAspect.dpVersionData.structure
		for handlers in structure.values():
			for handler in handlers:
				folderPath = handler.folder.replace(NAME_SPACE_VAR, data.namespace)
				# folderPath = f"data/{data.namespace}/{handler.folder}"
				os.makedirs(f"{datapackPath}/{folderPath}", exist_ok=True)

				for file in handler.generation.initialFiles:
					fileNS = file.namespace.replace(NAME_SPACE_VAR, data.namespace)
					folderPath = handler.folder.replace(NAME_SPACE_VAR, fileNS)
					filePath = f"{datapackPath}/{folderPath}{file.name}"
					with openOrCreate(filePath, 'w') as f:
						f.write(file.contents.replace(NAME_SPACE_VAR, data.namespace))


def createJsonFileFormatted(path: FilePathStr, jsonData: list | dict):
	with openOrCreate(path, 'w') as f:
		json.dump(
			jsonData,
			f,
			skipkeys=False,
			ensure_ascii=True,
			check_circular=True,
			allow_nan=True,
			sort_keys=False,
			indent='\t',  # todo: get from settings. maybe even project settings?
			separators=None
		)
