import os
from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtCore import Qt

import cat.GUI.propertyDecorators as pd
from base.gui.documentEditors import getDocumentEditor
from base.model.documents import DocumentTypeDescription, ParsedDocument, createNewDocument
from cat.GUI import SizePolicy
from cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from cat.utils import last
from cat.utils.formatters import indentMultilineStr
from cat.utils.utils import openOrCreate
from base.model.pathUtils import joinFilePath
from base.model.project.project import Project, ProjectRoot
from base.model.project.projectCreator import ProjectCreator
from .aspect import DatapackAspect, allRegisteredMinecraftVersions, minecraftVersionValidator
from .datapackContents import NAME_SPACE_VAR
from .dpVersions import getAllDPVersions
from corePlugins.minecraft.resourceLocation import isNamespaceValid
from gui.datapackEditorGUI import DatapackEditorGUI
from ..json import JSON_ID


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


_DESCRIPTION_DOC_TYPE = DocumentTypeDescription(
	type=ParsedDocument,
	name='mcmeta',
	extensions=['.mcmeta'],
	defaultLanguage=JSON_ID,
	defaultSchemaId='minecraft:raw_json_text',
	defaultContentFactory=lambda: b'[\n  {"text": "new_datapack", "color": "white"},\n  {"text": "\\nCreated with", "color": "white"}, {"text":"Datapack Editor", "color":"yellow"}\n]'
)


@dataclass
class DatapackProjectCreatorData(SerializableDataclass):

	namespace: str = field(
		default='new_datapack',
		metadata=catMeta(
			kwargs=dict(label='Namespace'),
			decorators=[pd.Validator(validateNamespace, textFormat=Qt.TextFormat.MarkdownText)]
		)
	)

	description: ParsedDocument = field(
		default_factory=lambda: createNewDocument(_DESCRIPTION_DOC_TYPE, None, observeFileSystem=False),
		metadata=catMeta(
			kwargs=dict(label='Description', isMultiline=True),
		)
	)

	dpVersion: str = field(
		default_factory=lambda: last(sorted(getAllDPVersions().keys()), ''),  # by default selects the latest version
		metadata=catMeta(
			kwargs=dict(label='Datapack Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: getAllDPVersions().keys())),
			]
		)
	)

	minecraftVersion: str = field(
		default_factory=lambda: last(sorted(allRegisteredMinecraftVersions()), ''),  # by default selects the latest version
		metadata=catMeta(
			kwargs=dict(label='Minecraft Version'),
			decorators=[
				pd.ComboBox(choices=property(lambda self: allRegisteredMinecraftVersions()), editable=True),
				pd.Validator(minecraftVersionValidator),
			]
		)
	)

	shouldGenerateDependenciesJson: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate dependencies.json'),
		)
	)

	shouldGeneratePackMcMeta: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate pack.mcmeta'),
		)
	)

	shouldGenerateFolderStructure: bool = field(
		default=True,
		metadata=catMeta(
			kwargs=dict(label='Generate Folder Structure'),
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
		# gui.propertyField(data, 'description', enabled=data.shouldGeneratePackMcMeta)
		# data.description = gui.advancedCodeField(data.description, label="Description", language='JSON', enabled=data.shouldGeneratePackMcMeta)
		documentEditorCls = getDocumentEditor(type(data.description))
		gui.editor(
			documentEditorCls,
			data.description,
			label='Description',
			seamless=True,
			enabled=data.shouldGeneratePackMcMeta
		)

		gui.propertyField(data, 'dpVersion')
		gui.propertyField(data, 'minecraftVersion')
		gui.helpBox("(Missing a version? you can always register more versions in Settings -> Minecraft)")
		gui.propertyField(data, 'shouldGeneratePackMcMeta')
		gui.propertyField(data, 'shouldGenerateDependenciesJson')
		gui.propertyField(data, 'shouldGenerateFolderStructure')
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
		if data.shouldGeneratePackMcMeta:
			self.generatePackMcMetaFile(newRoot)
		if data.shouldGenerateDependenciesJson:
			self.generateDependenciesFile(newRoot)
		if data.shouldGenerateFolderStructure:
			self.generateFolderStructure(newRoot, project)

	def generatePackMcMetaFile(self, root: ProjectRoot):
		data = self.data
		path = joinFilePath(root.normalizedLocation, 'pack.mcmeta')

		packFormat = data.dpVersion
		try:
			packFormat = int(packFormat)
		except ValueError:
			packFormat = 0  # not great

		description = indentMultilineStr(data.description.strContent, indent="\t\t", indentFirstLine=False).s
		jsonData = (
			'{\n'  # todo: get from settings. maybe even project settings?
			'\t"pack": {\n'
			f'\t\t"pack_format": {packFormat},\n'
			f'\t\t"description": {description}\n'
			'\t}\n'
			'}'
		)
		with openOrCreate(path, 'w') as f:
			f.write(jsonData)

	@staticmethod
	def generateDependenciesFile(root: ProjectRoot):
		path = joinFilePath(root.normalizedLocation, 'dependencies.json')

		jsonData = (
			'[\n'  # just some example data
			'\t{"name": "DatapackUtilities_v3.4.1", "mandatory": false},\n'
			'\t{"name": "another-dependency", "mandatory": false}\n'
			']'
		)

		with openOrCreate(path, 'w') as f:
			f.write(jsonData)

	def generateFolderStructure(self, root: ProjectRoot, project: Project):
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
