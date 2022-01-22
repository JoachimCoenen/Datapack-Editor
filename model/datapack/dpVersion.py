from copy import copy
from dataclasses import dataclass, fields, Field, is_dataclass
from typing import Optional

from model.datapackContents import EntryHandlers, EntryHandlerInfo
from model.json.core import JsonSchema


@dataclass
class DPVersion:
	name: str

	structure: EntryHandlers

	@property
	def byFolder(self) -> dict[str, list[EntryHandlerInfo]]:
		result = {}
		for handler in self.structure.values():
			result.setdefault(handler.folder, []).append(handler)
		return result

	jsonSchemas: dict[str, JsonSchema]


def _copyRecursive(data):
	newData = copy(data)
	field: Field
	for field in fields(data):
		value = getattr(data, field.name)
		if is_dataclass(field.type):
			value = _copyRecursive(value)
		else:
			value = copy(value)
		setattr(newData, field.name, value)
	return newData


def newVersionFrom(version: DPVersion, *, name: str) -> DPVersion:
	newVersion = _copyRecursive(version)
	newVersion.name = name
	return newVersion


ALL_DP_VERSIONS: dict[str, DPVersion] = {}


def registerDPVersion(version: DPVersion, forceOverwrite: bool = False) -> None:
	ALL_DP_VERSIONS[version.name] = version


def getDPVersion(name: str) -> Optional[DPVersion]:
	return ALL_DP_VERSIONS.get(name)
