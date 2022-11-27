from dataclasses import dataclass, field

from Cat.utils.logging_ import logWarning, logInfo
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.pathUtils import FilePathStr
from corePlugins.json.jsonSchema import SchemaBuilderOrchestrator
from corePlugins.json.core import *


@dataclass
class _SchemaLibPath:  # todo find better name for class _SchemaLibPath
	path: str
	includedDefinitions: tuple[str, ...] = ()


@dataclass(frozen=True)
class JsonSchemaLoader:
	_registeredSchemas: dict[str, FilePathStr] = field(default_factory=dict)
	_registeredLibraries: dict[str, _SchemaLibPath] = field(default_factory=dict)

	orchestrator: SchemaBuilderOrchestrator = field(default_factory=lambda: SchemaBuilderOrchestrator(''))

	def registerSchema(self, name: str, path: str):
		self._registeredSchemas[name] = path
		self._load_schema(name, path)
		self.logErrors()
		self.clearErrors()

	def registerSchemaLibrary(self, name: str, path: str, includedDefinitions: tuple[str, ...] = None) -> None:
		"""

		:param name:
		:param path:
		:param includedDefinitions: if set to None, all definitions are included.
		:return:
		"""
		lib_path = _SchemaLibPath(path, includedDefinitions)
		self._registeredLibraries[name] = lib_path
		self._load_library(name, lib_path)
		self.logErrors()
		self.clearErrors()

	def _load_schema(self, name: str, path: FilePathStr):
		schema = self.orchestrator.parseJsonSchema(path)
		if schema is not None:
			GLOBAL_SCHEMA_STORE.registerSchema(name, schema)
		else:
			logWarning(f"Failed to load schema '{path}'")
			GLOBAL_SCHEMA_STORE.unregisterSchema(name, JSON_ID)

	def _load_library(self, name: str, path: _SchemaLibPath):
		library = self.orchestrator.getSchemaLibrary(path.path)
		inclDefs = path.includedDefinitions or list(library.definitions.keys())
		for defName in inclDefs:
			fullDefName = f'{name}/{defName}'
			if (schema := library.definitions.get(defName)) is not None:
				GLOBAL_SCHEMA_STORE.registerSchema(fullDefName, schema)
			else:
				logWarning(f"schema library '{path.path}' has no definition for '{defName}")
				GLOBAL_SCHEMA_STORE.unregisterSchema(fullDefName, JSON_ID)

	def reloadAllSchemas(self):
		logInfo(f"reloadAllSchemas():")
		self.orchestrator.clear()

		for name, path in self._registeredSchemas.items():
			self._load_schema(name, path)

		for name, path in self._registeredLibraries.items():
			self._load_library(name, path)

		self.logErrors()
		logInfo(f"reloadAllSchemas finished:")

	def logErrors(self):
		for path, errors in self.orchestrator.errors.items():
			if errors:
				logWarning(path)
				for error in errors:
					logWarning(error, indentLvl=1)

	def clearErrors(self):
		self.orchestrator.errors.clear()


JSON_SCHEMA_LOADER = JsonSchemaLoader()

# GLOBAL_SCHEMA_STORE.registerSchemaLibrary('tags.json')
# # TAGS_BLOCKS = tagsLib.definitions['block_type']
# # TAGS_ENTITY_TYPES = tagsLib.definitions['entity_type']
# # TAGS_FLUIDS = tagsLib.definitions['fluid_type']
# # TAGS_FUNCTIONS = tagsLib.definitions['function']
# # TAGS_GAME_EVENTS = tagsLib.definitions['game_event']
# # TAGS_ITEMS = tagsLib.definitions['item_type']
#
# RAW_JSON_TEXT_SCHEMA = orchestrator.parseJsonSchema('rawJsonText.json')
# PREDICATE_SCHEMA = orchestrator.parseJsonSchema('predicate.json')
# JSON_SCHEMA_SCHEMA = orchestrator.parseJsonSchema('jsonSchema.json')


__all__ = [
	'JsonSchemaLoader',
	'JSON_SCHEMA_LOADER',
]
