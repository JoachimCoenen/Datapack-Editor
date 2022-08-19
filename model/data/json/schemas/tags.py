import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from Cat.utils.logging_ import logWarning, logInfo
from model.data.json import argTypes
from model.data.json.schemas import providers
from model.json.jsonSchema import SchemaBuilderOrchestrator
from model.json.core import *

argTypes.init()
providers.init()


@dataclass
class _SchemaLibPath:  # todo find better name for class _SchemaLibPath
	path: str
	includedDefinitions: tuple[str, ...] = ()


@dataclass
class _SchemaDef:  # todo find better name for class _SchemaPath
	schemas: dict[str, JsonSchema]


@dataclass(frozen=True)
class JsonSchemaStore:
	_registeredSchemas: dict[str, dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
	_registeredLibraries: dict[str, dict[str, _SchemaLibPath]] = field(default_factory=lambda: defaultdict(dict))
	_loadedSchemas: dict[str, dict[str, JsonSchema]] = field(default_factory=lambda: defaultdict(dict))

	orchestrator: SchemaBuilderOrchestrator = field(default_factory=lambda: SchemaBuilderOrchestrator(''))

	def get(self, name: str) -> Optional[JsonSchema]:
		ns, _, name = name.rpartition(':')
		return self._loadedSchemas.get(ns, {}).get(name)

	def registerSchema(self, name: str, path: str):
		ns, _, name = name.rpartition(':')
		self._registeredSchemas[ns][name] = path
		self._load_schema(ns, name, path)
		self.logErrors()
		self.clearErrors()

	def registerSchemaLibrary(self, name: str, path: str, includedDefinitions: tuple[str, ...] = None) -> None:
		"""

		:param name:
		:param path:
		:param includedDefinitions: if set to None, all definitions are included.
		:return:
		"""
		ns, _, name = name.rpartition(':')
		lib_path = _SchemaLibPath(path, includedDefinitions)
		self._registeredLibraries[ns][name] = lib_path
		self._load_library(ns, name, lib_path)
		self.logErrors()
		self.clearErrors()

	def _load_schema(self, ns: str, name: str, path: str):
		schema = self.orchestrator.parseJsonSchema(path)
		if schema is not None:
			self._loadedSchemas[ns][name] = schema
		else:
			logWarning(f"Failed to load schema '{path}'")

	def _load_library(self, ns: str, name: str, path: _SchemaLibPath):
		library = self.orchestrator.getSchemaLibrary(path.path)
		inclDefs = path.includedDefinitions or list(library.definitions.keys())
		for defName in inclDefs:
			if (schema := library.definitions.get(defName)) is not None:
				self._loadedSchemas[ns][f'{name}/{defName}'] = schema
			else:
				logWarning(f"schema library '{path.path}' has no definition for '{defName}")

	def reloadAllSchemas(self):
		logInfo(f"reloadAllSchemas():")
		self._loadedSchemas.clear()
		self.orchestrator.clear()

		for ns, content in self._registeredSchemas.items():
			for name, path in content.items():
				self._load_schema(ns, name, path)

		for ns, content in self._registeredLibraries.items():
			for name, path in content.items():
				self._load_library(ns, name, path)

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


GLOBAL_SCHEMA_STORE = JsonSchemaStore()

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
	'JsonSchemaStore',
	'GLOBAL_SCHEMA_STORE',
]
