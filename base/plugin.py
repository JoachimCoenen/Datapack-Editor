from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Protocol, Iterable, TYPE_CHECKING, Optional, Type

from PyQt5.Qsci import QsciLexerCustom

from Cat.CatPythonGUI.GUI.codeEditor import CodeEditorLexer
from Cat.CatPythonGUI.GUI.pythonGUI import TabOptions
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.logging_ import logError
from base.gui.styler import registerStyler, CatStyler
from base.model.applicationSettings import SettingsAspect, getApplicationSettings
from base.model.documents import DocumentTypeDescription, registerDocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider, registerContextProvider
from base.model.parsing.parser import ParserBase, registerParser
from base.model.parsing.tree import Node
from base.model.project.project import ProjectAspect
from base.model.utils import LanguageId

if TYPE_CHECKING:
	from gui.datapackEditorGUI import DatapackEditorGUI


@dataclass
class PluginService:
	plugins: dict[str, PluginBase]

	@property
	def activePlugins(self) -> Iterable[PluginBase]:
		return self.plugins.values()

	def registerPlugin(self, name: str, plugin: PluginBase):
		AddToDictDecorator(self.plugins)(name)(plugin)

		for languageId, parserCls in (plugin.parsers() or {}).items():
			registerParser(languageId)(parserCls)

		for nodeCls, ctxProviderCls in (plugin.contextProviders() or {}).items():
			registerContextProvider(nodeCls)(ctxProviderCls)

		for docTypeDescr in (plugin.documentTypes() or ()):
			registerDocumentTypeDescription(docTypeDescr)

		for languageId, lexer in (plugin.lexers() or {}).items():
			CodeEditorLexer(languageId, forceOverride=True)(lexer)

		for stylerCls in (plugin.stylers() or ()):
			registerStyler(stylerCls)

		plugin.initPlugin()

		for settingCls in (plugin.settingsAspects() or []):
			application_settings = getApplicationSettings()
			application_settings.aspects.add(settingCls)
			aspect_type = settingCls.getAspectType()
			aspectJson = application_settings.unknownSettings.get(aspect_type)
			if aspectJson is not None:
				del application_settings.unknownSettings[aspect_type]
				application_settings.loadAspectSettings(aspect_type, aspectJson, logError)

	# TODO: def initializeAllPlugins(self) -> None:
	# 	for plugin in self.activePlugins:
	# 		plugin.initPlugin()


PLUGIN_SERVICE = PluginService({})


# @dataclass
# class FileChanges:
# 	newFiles: list[FilePath]
# 	changedFiles: list[FilePath]
# 	deletedFiles: list[FilePath]


class SideBarTabGUIFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI) -> None:
		pass


class ToolBtnFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI):
		pass


class PluginBase(ABC):
	def initPlugin(self) -> None:
		pass

	def sideBarTabs(self) -> list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]]:
		return []

	def bottomBarTabs(self) -> list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]]:
		return []

	def parsers(self) -> dict[LanguageId, Type[ParserBase]]:
		return {}

	def contextProviders(self) -> dict[Type[Node], Type[ContextProvider]]:
		return {}

	def projectAspects(self) -> list[Type[ProjectAspect]]:
		return []

	def settingsAspects(self) -> list[Type[SettingsAspect]]:
		return []

	def documentTypes(self) -> list[DocumentTypeDescription]:
		return []

	def lexers(self) -> dict[LanguageId, Type[QsciLexerCustom]]:
		return {}

	def stylers(self) -> list[Type[CatStyler]]:
		return []

# class DatapackAspect(ProjectAspect):
# 	@classmethod
# 	def getAspectType(cls) -> AspectType:
# 		return DATAPACK_ASPECT_TYPE
#
# 	@property
# 	def dependencies(self) -> list[Dependency]:
# 		fileName = 'dependencies.json'
# 		projectPath = self.parent.path
# 		schema = GLOBAL_SCHEMA_STORE.get('dpe:dependencies')
#
# 		if projectPath == applicationSettings.minecraft.executable:
# 			# Minecraft does not need to itself as a dependency.
# 			return []
#
# 		dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
# 		filePath = (projectPath, fileName)
# 		try:
# 			with ZipFilePool() as pool:
# 				file = loadBinaryFile(filePath, pool)
# 		except (OSError, KeyError) as e:
# 			node, errors = None, [GeneralError(MDStr(f"{type(e).__name__}: {str(e)}"))]
# 		else:
# 			node, errors = parseNPrepare(file, filePath=filePath, language=LANGUAGES.JSON, schema=schema, allowMultilineStr=False)
#
# 		if node is not None:
# 			validateTree(node, file, errors)
#
# 		if node is not None and not errors:
# 			for element in node.data:
# 				dependencies.append(Dependency(
# 					element.data['name'].value.data,
# 					element.data['mandatory'].value.data,
# 					element.data['name'].value.span
# 				))
# 		if errors:
# 			logWarning(f"Failed to read '{fileName}' for project '{projectPath}':")
# 			for error in errors:
# 				logWarning(error, indentLvl=1)
#
# 		return dependencies
#
# 	def analyzeProject(self) -> None:
# 		from sessionOld.session import getSession
# 		allEntryHandlers = getSession().datapackData.structure
# 		collectAllEntries(self.parent.files, allEntryHandlers, self.parent)
#
