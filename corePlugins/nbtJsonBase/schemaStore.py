from dataclasses import dataclass, field
from typing import Optional

from base.model.utils import WrappedError
from cat.utils.logging_ import logWarning, logInfo, logError, LoggingFunction
from base.model.pathUtils import FilePathStr
from corePlugins.nbtJsonBase.core import StructureDataSchema
from corePlugins.nbtJsonBase.schemaBuilder import SchemaBuilderOrchestrator


@dataclass
class _SchemaLibPath:  # todo find better name for class _SchemaLibPath
	path: str
	includedDefinitions: tuple[str, ...] = ()
	"""if empty, all definitions are included."""


@dataclass(frozen=True)
class StructureSchemaLoader:
	"""
	loads JSON schemas and schema libraries, and remembers where thy have been loaded from, so they can be reloaded.
	Also Caches them for when schemas rely on each other (see also SchemaBuilderOrchestrator).
	"""
	_registeredSchemas: dict[str, FilePathStr] = field(default_factory=dict)
	_registeredLibraries: dict[str, _SchemaLibPath] = field(default_factory=dict)

	orchestrator: SchemaBuilderOrchestrator = field(default_factory=lambda: SchemaBuilderOrchestrator(''))

	def loadSchema(self, name: str, path: str) -> Optional[StructureDataSchema]:
		self._registeredSchemas[name] = path
		schema = self._load_schema(path)
		self.logAndClearErrors()
		return schema

	def loadSchemaLibrary(self, name: str, path: str, includedDefinitions: tuple[str, ...] = ()) -> dict[str, StructureDataSchema]:
		"""
		:param name:
		:param path:
		:param includedDefinitions: if empty, all definitions are included.
		:return:
		"""
		lib_path = _SchemaLibPath(path, includedDefinitions)
		self._registeredLibraries[name] = lib_path
		schemas = self._load_library(name, lib_path)
		self.logAndClearErrors()
		return schemas

	def _load_schema(self, path: FilePathStr) -> Optional[StructureDataSchema]:
		schema = self.orchestrator.getSchema(path)
		if schema is None:
			logWarning(f"Failed to load schema '{path}'")
		return schema

	def _load_library(self, name: str, path: _SchemaLibPath) -> dict[str, StructureDataSchema]:
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

	def reloadAllSchemas(self) -> dict[str, StructureDataSchema]:
		logInfo("reloadAllSchemas():")
		self.orchestrator.clear()
		schemas = {}

		for name, path in self._registeredSchemas.items():
			schema = self._load_schema(path)
			if schema is not None:
				schemas[name] = schema

		for name, libPath in self._registeredLibraries.items():
			schemas |= self._load_library(name, libPath)

		self.logAndClearErrors()
		logInfo("reloadAllSchemas finished:")
		return schemas

	def logErrors(self) -> None:
		for path, errors in self.orchestrator.errors.items():
			if errors:
				maxErrorStyle = max(errors, key=lambda r: {'info': 10, 'warning': 20, 'error': 30}.get(r.style, 40)).style
				logFunc = self._getLogFuncForErrorStyle(maxErrorStyle)
				logFunc(path)
				for error in errors:
					logFunc = self._getLogFuncForErrorStyle(error.style)
					if isinstance(error, WrappedError):
						logFunc(error.wrappedEx, indentLvl=1)
					else:
						logFunc(str(error), indentLvl=1)

	@staticmethod
	def _getLogFuncForErrorStyle(maxErrorStyle: str) -> LoggingFunction:
		logFunc = {'info': logInfo, 'warning': logWarning, 'error': logError}.get(maxErrorStyle, logError)
		return logFunc

	def clearErrors(self) -> None:
		self.orchestrator.errors.clear()

	def logAndClearErrors(self) -> None:
		self.logErrors()
		self.clearErrors()


STRUCTURE_SCHEMA_LOADER: StructureSchemaLoader = StructureSchemaLoader()


__all__ = [
	'StructureSchemaLoader',
	'STRUCTURE_SCHEMA_LOADER',
]
