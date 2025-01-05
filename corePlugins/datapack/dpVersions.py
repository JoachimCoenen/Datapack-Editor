from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, Mapping, ClassVar

from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.utils import LanguageId
from .datapackContents import EntryHandlers
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID
from corePlugins.mcFunction.command import MCFunctionSchema
from corePlugins.nbtJsonBase.core import StructureSchema
from corePlugins.json import JSON_ID
from corePlugins.nbt import SNBT_ID


@dataclass
class DPVersion:
	name: str
	structure: EntryHandlers
	jsonSchemas: dict[str, StructureSchema]
	snbtSchemas: dict[str, StructureSchema]
	mcFunctionSchema: MCFunctionSchema

	def getJsonSchema(self, name: str) -> Optional[StructureSchema]:
		return GLOBAL_SCHEMA_STORE.get(name + ' ' + self.name, StructureSchema)

	def activate(self) -> None:
		self.activateSchemas(self.jsonSchemas, JSON_ID)
		self.activateSchemas(self.snbtSchemas, SNBT_ID)
		self.activateMcFunctionSchema(self.mcFunctionSchema)

	def activateSchemas(self, schemas: dict[str, Schema], languageId: LanguageId):
		for name, schema in schemas.items():
			if schema is not None:
				GLOBAL_SCHEMA_STORE.registerSchema(name, schema, languageId)

	def activateMcFunctionSchema(self, mcFunctionSchema: MCFunctionSchema):
		if mcFunctionSchema is not None:
			GLOBAL_SCHEMA_STORE.registerSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, mcFunctionSchema)

	def deactivate(self) -> None:
		self.deactivateSchemas(self.jsonSchemas, JSON_ID)
		self.deactivateSchemas(self.snbtSchemas, SNBT_ID)
		self.deactivateMcFunctionSchema(self.mcFunctionSchema)

	def deactivateSchemas(self, schemas: dict[str, Schema], languageId: LanguageId):
		for name, schema in schemas.items():
			if schema is not None:
				if GLOBAL_SCHEMA_STORE.get(name, languageId) is schema:
					GLOBAL_SCHEMA_STORE.unregisterSchema(name, languageId)

	def deactivateMcFunctionSchema(self, mcFunctionSchema: MCFunctionSchema):
		if mcFunctionSchema is not None:
			if GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema) is mcFunctionSchema:
				GLOBAL_SCHEMA_STORE.unregisterSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema.language)

	EMPTY: ClassVar[DPVersion]


DPVersion.EMPTY = DPVersion('No Version', MappingProxyType({}), {}, {}, MCFunctionSchema('', commands={}))


_ALL_DP_VERSIONS: dict[str, DPVersion] = {}


def registerDPVersion(version: DPVersion) -> None:
	_ALL_DP_VERSIONS[version.name] = version


def getDPVersion(name: str) -> DPVersion:
	return _ALL_DP_VERSIONS.get(name, DPVersion.EMPTY)


def getAllDPVersions() -> Mapping[str, DPVersion]:
	return _ALL_DP_VERSIONS
