from dataclasses import dataclass, field
from typing import Optional

from base.model.utils import WrappedError
from cat.utils.logging_ import logWarning, logInfo
from base.model.pathUtils import FilePathStr
from .core import JsonSchema
from .jsonSchema import SchemaBuilderOrchestrator


@dataclass
class _SchemaLibPath:  # todo find better name for class _SchemaLibPath
	path: str
	includedDefinitions: tuple[str, ...] = ()


@dataclass(frozen=True)
class JsonSchemaLoader:
	"""
	loads JSON schemas and schema libraries, and remembers where thy have been loaded from, so they can be reloaded.
	Also Caches them for when schemas rely on each other (see also SchemaBuilderOrchestrator).
	"""
	_registeredSchemas: dict[str, FilePathStr] = field(default_factory=dict)
	_registeredLibraries: dict[str, _SchemaLibPath] = field(default_factory=dict)

	orchestrator: SchemaBuilderOrchestrator = field(default_factory=lambda: SchemaBuilderOrchestrator(''))

	def loadSchema(self, name: str, path: str) -> Optional[JsonSchema]:
		self._registeredSchemas[name] = path
		schema = self._load_schema(path)
		self.logAndClearErrors()
		return schema

	# def registerSchemaLibrary(self, name: str, path: str, includedDefinitions: tuple[str, ...] = None) -> dict[str, JsonSchema]:
	def loadSchemaLibrary(self, name: str, path: str, includedDefinitions: tuple[str, ...] = None) -> dict[str, JsonSchema]:
		"""

		:param name:
		:param path:
		:param includedDefinitions: if set to None, all definitions are included.
		:return:
		"""
		lib_path = _SchemaLibPath(path, includedDefinitions)
		self._registeredLibraries[name] = lib_path
		schemas = self._load_library(name, lib_path)
		self.logAndClearErrors()
		return schemas

	def _load_schema(self, path: FilePathStr) -> Optional[JsonSchema]:
		schema = self.orchestrator.getSchema(path)
		if schema is None:
			logWarning(f"Failed to load schema '{path}'")
		return schema

	def _load_library(self, name: str, path: _SchemaLibPath) -> dict[str, JsonSchema]:
		library = self.orchestrator.getSchemaLibrary(path.path)
		inclDefs = path.includedDefinitions or list(library.definitions.keys())
		schemas = {}
		for defName in inclDefs:
			fullDefName = f'{name}/{defName}'
			if (schema := library.definitions.get(defName)) is not None:
				schemas[fullDefName] = schema
			else:
				logWarning(f"schema library '{path.path}' has no definition for '{defName}")
		return schemas

	def reloadAllSchemas(self) -> dict[str, JsonSchema]:
		logInfo(f"reloadAllSchemas():")
		self.orchestrator.clear()
		schemas = {}

		for name, path in self._registeredSchemas.items():
			schema = self._load_schema(path)
			if schema is not None:
				schemas[name] = schema

		for name, path in self._registeredLibraries.items():
			schemas |= self._load_library(name, path)

		self.logAndClearErrors()
		logInfo(f"reloadAllSchemas finished:")
		return schemas

	def logErrors(self):
		for path, errors in self.orchestrator.errors.items():
			if errors:
				logWarning(path)
				for error in errors:
					if isinstance(error, WrappedError):
						logWarning(error.wrappedEx, indentLvl=1)
					else:
						logWarning(str(error), indentLvl=1)

	def clearErrors(self):
		self.orchestrator.errors.clear()

	def logAndClearErrors(self):
		self.logErrors()
		self.clearErrors()


JSON_SCHEMA_LOADER: JsonSchemaLoader = JsonSchemaLoader()

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
