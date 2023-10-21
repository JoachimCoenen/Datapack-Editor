from __future__ import annotations

from sys import exit  # required when running packaged as an executable. See: https://stackoverflow.com/questions/45066518/nameerror-name-exit-is-not-defined
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol, Iterable, TYPE_CHECKING, Optional, Type

from PyQt5.Qsci import QsciLexerCustom

from Cat.GUI.components.codeEditor import CodeEditorLexer
from Cat.GUI.pythonGUI import TabOptions
from Cat.utils import getExePath
from Cat.utils.collections_ import AddToDictDecorator
from Cat.utils.graphs import getCycles, semiTopologicalSort2
from Cat.utils.logging_ import logError, logWarning, logInfo, logFatal, loggingIndentInfo
from base.gui.documentLexer import DocumentLexer
from base.gui.styler import registerStyler, CatStyler
from base.model.applicationSettings import SettingsAspect, getApplicationSettings, ApplicationSettings
from base.model.aspect import registerAspectForType
from base.model.defaultSchemaProvider import SchemaMapping, addSchemaMapping
from base.model.documents import DocumentTypeDescription, registerDocumentTypeDescription
from base.model.parsing.contextProvider import ContextProvider, registerContextProvider
from base.model.parsing.parser import ParserBase, registerParser
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Node, Schema
from base.model.pathUtils import FilePathStr
from base.model.project.project import ProjectAspect, Project
from base.model.project.projectCreator import ProjectCreator
from base.model.utils import LanguageId
from base.modules import loadAllModules, FolderAndFileFilter

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
		plugin._name = name

	def initAllPlugins(self):
		pluginByName = self.plugins

		# dependenciesByPlugin = {plugin.name: list(filter(None, (pluginByName.get(dep) for dep in plugin.dependencies()))) for plugin in self.plugins.values()}
		dependenciesDict: defaultdict[str, list[str]] = defaultdict(list)
		unknownDependenciesDict: defaultdict[str, list[str]] = defaultdict(list)
		unknownOptionalDependenciesDict: defaultdict[str, list[str]] = defaultdict(list)

		for plugin in self.plugins.values():
			for dep in plugin.dependencies():
				depsDict = unknownDependenciesDict if dep not in pluginByName else dependenciesDict
				depsDict[plugin.name].append(dep)
			for dep in plugin.optionalDependencies():
				depsDict = unknownOptionalDependenciesDict if dep not in pluginByName else dependenciesDict
				depsDict[plugin.name].append(dep)

		if unknownDependenciesDict:
			msg = f"There are missing mandatory dependencies for plugins. Aborting!"
			msg2 = '\n'.join(f"{plugin}: {', '.join(dependencies)}" for plugin, dependencies in unknownDependenciesDict.items())
			logFatal(msg)
			logFatal(msg2, indentLvl=1)
			exit(f"There are missing mandatory dependencies for plugins. See 'logfile.log'. Aborting!")  # a bit harsh, I know...
		del unknownDependenciesDict

		if unknownOptionalDependenciesDict:
			msg = f"There are missing optional dependencies for plugins. They dependencies will be ignored:"
			msg2 = '\n'.join(f"{plugin}: {', '.join(dependencies)}" for plugin, dependencies in unknownOptionalDependenciesDict.items())
			logInfo(msg)
			logInfo(msg2, indentLvl=1)
		del unknownOptionalDependenciesDict

		# check for cycles:
		emptyList = []
		cycles = getCycles(pluginByName.keys(), lambda p: dependenciesDict.get(p, emptyList), lambda p: p)
		if cycles:
			msg = f"There are dependency cycle(s) between plugins. Aborting!"
			msg2 = '\n'.join(
				f"  - " + _formatPluginsOrder(cycle + [cycle[0]])
				for cycle in cycles
			)
			logFatal(msg, )
			logFatal(msg2, indentLvl=1)
			exit(f"There are dependency cycles between plugins. See 'logfile.log'. Aborting!")  # a bit harsh, I know...

		# sort topologically:
		allPluginsSorted = semiTopologicalSort2(pluginByName.keys(), lambda p: dependenciesDict.get(p, emptyList), lambda x: x, reverse=True)
		pluginOrderStr = _formatPluginsOrder(allPluginsSorted)
		logInfo("Initializing plugins in the following order:", pluginOrderStr)

		# initialize plugins
		self.plugins: dict[str, PluginBase] = {}
		for pluginName in allPluginsSorted:
			plugin = pluginByName.get(pluginName)
			self.plugins[pluginName] = plugin
			with loggingIndentInfo(f"Initializing plugin '{pluginName}' ({type(plugin).__qualname__}) "):
				self._initPlugin(plugin)

	@staticmethod
	def _initPlugin(plugin: PluginBase):
		for languageId, parserCls in (plugin.parsers() or {}).items():
			registerParser(languageId)(parserCls)

		for nodeCls, ctxProviderCls in (plugin.contextProviders() or {}).items():
			registerContextProvider(nodeCls)(ctxProviderCls)

		for docTypeDescr in (plugin.documentTypes() or ()):
			registerDocumentTypeDescription(docTypeDescr)

		for languageId, stylerCls in (plugin.stylers() or {}).items():
			registerStyler(languageId)(stylerCls)
			CodeEditorLexer(languageId, forceOverride=True)(DocumentLexer)

		for languageId, lexerCls in (plugin.lexers() or {}).items():
			CodeEditorLexer(languageId, forceOverride=True)(lexerCls)

		plugin.initPlugin()

		schemas = plugin.schemas() or {}
		for name, schema in schemas.items():
			if schema is not None:
				GLOBAL_SCHEMA_STORE.registerSchema(name, schema)
			else:
				logWarning(f"Schema with name'{name}' was null. it won't be added to the GLOBAL_SCHEMA_STORE.")

		schemaMappings = plugin.schemaMappings() or {}
		for languageId, mappings in schemaMappings.items():
			for mapping in mappings:
				addSchemaMapping(languageId, mapping)

		for aspectCls in (plugin.projectAspects() or []):
			registerAspectForType(Project, aspectCls, forceOverride=False)

		application_settings = getApplicationSettings()
		for aspectCls in (plugin.settingsAspects() or []):
			registerAspectForType(ApplicationSettings, aspectCls, forceOverride=False)
			application_settings.aspects.add(aspectCls)
			aspect_type = aspectCls.getAspectType()
			aspectJson = application_settings.unknownAspects.get(aspect_type)
			if aspectJson is not None:
				del application_settings.unknownAspects[aspect_type]
				application_settings.loadAspectData(aspect_type, aspectJson, logError)


PLUGIN_SERVICE = PluginService({})


def _formatPluginsOrder(plugins: list[str]) -> str:
	return ' -> '.join(plugins)


class SideBarTabGUIFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI) -> None:
		pass


class ToolBtnFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI):
		pass


class PluginBase(ABC):

	def __init__(self):
		self._name: str = ""  # will be set when registering.

	@property
	def name(self) -> str:
		"""
		The plugin identifier usually in the format "<namespace>:<plugin_name>_plugin".
		::
			E.g.:
			  dpe:json_plugin
			  dpe:mc_function_plugin
			  cce:project_files
		:return:
		"""
		return self._name

	def initPlugin(self) -> None:
		pass

	@property
	def displayName(self) -> str:
		"""
		Override this property to give your plugin a proper display name.
		By defaults returns this plugins' identifier (name).
		:return:
		"""
		return self.name

	@abstractmethod
	def dependencies(self) -> set[str]:
		return set()

	def optionalDependencies(self) -> set[str]:
		return set()

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

	def stylers(self) -> dict[LanguageId, Type[CatStyler]]:
		return {}

	def schemas(self) -> dict[str, Schema]:
		return {}

	def schemaMappings(self) -> dict[LanguageId, list[SchemaMapping]]:
		return {}

	def projectCreators(self) -> list[Type[ProjectCreator]]:
		return []


def getPluginsDir() -> tuple[str, FilePathStr]:
	baseModuleName = 'plugins'
	pluginsDir = os.path.dirname(os.path.abspath(getExePath()))
	pluginsDir = os.path.join(pluginsDir, baseModuleName)
	return baseModuleName, pluginsDir


def getBasePluginsDir() -> tuple[str, FilePathStr]:
	baseModuleName = 'basePlugins'
	pluginsDir = os.path.dirname(os.path.dirname(__file__))
	pluginsDir = os.path.join(pluginsDir, baseModuleName)
	return baseModuleName, pluginsDir


def getCorePluginsDir() -> tuple[str, FilePathStr]:
	baseModuleName = 'corePlugins'
	pluginsDir = os.path.dirname(os.path.dirname(__file__))
	pluginsDir = os.path.join(pluginsDir, baseModuleName)
	return baseModuleName, pluginsDir


def loadAllPlugins(baseModuleName: str, pluginsDir: FilePathStr) -> None:
	loadAllModules(
		baseModuleName,
		pluginsDir,
		[
			# all single-file plugins
			FolderAndFileFilter('/', r'(?!__)[\w_]+\.py'),
			# all multi-file plugins (plugins inside a package
			FolderAndFileFilter('/*', r'__init__\.py'),
		],
		initMethodName='initPlugin'
	)
