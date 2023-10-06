from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, Mapping, ClassVar

from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from .datapackContents import EntryHandlers
from corePlugins.json.core import JsonSchema
from corePlugins.mcFunction import MC_FUNCTION_DEFAULT_SCHEMA_ID
from corePlugins.mcFunction.command import MCFunctionSchema


@dataclass
class DPVersion:
	name: str
	structure: EntryHandlers
	jsonSchemas: dict[str, JsonSchema]
	mcFunctionSchema: MCFunctionSchema

	def getJsonSchema(self, name: str) -> Optional[JsonSchema]:
		return GLOBAL_SCHEMA_STORE.get(name + ' ' + self.name, JsonSchema)

	def activate(self) -> None:
		self.activateJsonSchemas(self.jsonSchemas)
		self.activateMcFunctionSchema(self.mcFunctionSchema)

	def activateJsonSchemas(self, jsonSchemas: dict[str, JsonSchema]):
		for name, schema in jsonSchemas.items():
			# schema = self.getJsonSchema(name)
			if schema is not None:
				GLOBAL_SCHEMA_STORE.registerSchema(name, schema)

	def activateMcFunctionSchema(self, mcFunctionSchema: MCFunctionSchema):
		if mcFunctionSchema is not None:
			GLOBAL_SCHEMA_STORE.registerSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, mcFunctionSchema)

	def deactivate(self) -> None:
		self.deactivateJsonSchemas(self.jsonSchemas)
		self.deactivateMcFunctionSchema(self.mcFunctionSchema)

	def deactivateJsonSchemas(self, jsonSchemas: dict[str, JsonSchema]):
		for name, schema in jsonSchemas.items():
			# schema = self.getJsonSchema(name)
			if schema is not None:
				if GLOBAL_SCHEMA_STORE.get(name, JsonSchema) is schema:
					GLOBAL_SCHEMA_STORE.unregisterSchema(name, JsonSchema)

	def deactivateMcFunctionSchema(self, mcFunctionSchema: MCFunctionSchema):
		if mcFunctionSchema is not None:
			if GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema) is mcFunctionSchema:
				GLOBAL_SCHEMA_STORE.unregisterSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema.language)

	EMPTY: ClassVar[DPVersion]


DPVersion.EMPTY = DPVersion('No Version', MappingProxyType({}), {}, MCFunctionSchema('', commands={}))


_ALL_DP_VERSIONS: dict[str, DPVersion] = {}


def registerDPVersion(version: DPVersion) -> None:
	_ALL_DP_VERSIONS[version.name] = version


def getDPVersion(name: str) -> DPVersion:
	return _ALL_DP_VERSIONS.get(name, DPVersion.EMPTY)


def getAllDPVersions() -> Mapping[str, DPVersion]:
	return _ALL_DP_VERSIONS
