from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, Mapping

from .datapackContents import EntryHandlers


@dataclass
class DPVersion:
	name: str
	structure: EntryHandlers
	# jsonSchemas: JsonSchemaStore

	def activate(self) -> None:
		# schema = self.mcFunctionSchema
		# if schema is not None:
		# 	GLOBAL_SCHEMA_STORE.registerSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, schema)
		pass

	def deactivate(self) -> None:
		# schema = self.mcFunctionSchema
		# if schema is not None:
		# 	if GLOBAL_SCHEMA_STORE.get(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema) is schema:
		# 		GLOBAL_SCHEMA_STORE.unregisterSchema(MC_FUNCTION_DEFAULT_SCHEMA_ID, MCFunctionSchema.language)
		pass


DP_EMPTY_VERSION = DPVersion('No Version', MappingProxyType({}))


# def _copyRecursive(data):
# 	newData = copy(data)
# 	field: Field
# 	for field in fields(data):
# 		value = getattr(data, field.name)
# 		if is_dataclass(field.type):
# 			value = _copyRecursive(value)
# 		else:
# 			value = copy(value)
# 		setattr(newData, field.name, value)
# 	return newData
#
#
# def newVersionFrom(version: DPVersion, *, name: str) -> DPVersion:
# 	newVersion = _copyRecursive(version)
# 	newVersion.name = name
# 	return newVersion


_ALL_DP_VERSIONS: dict[str, DPVersion] = {}


def registerDPVersion(version: DPVersion, forceOverwrite: bool = False) -> None:
	_ALL_DP_VERSIONS[version.name] = version


def getDPVersion(name: str) -> Optional[DPVersion]:
	return _ALL_DP_VERSIONS.get(name)


def getAllDPVersions() -> Mapping[str, DPVersion]:
	return _ALL_DP_VERSIONS
