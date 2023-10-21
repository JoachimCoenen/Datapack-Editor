import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, TypeVar, overload, Type

from Cat.processFiles import makeSearchPath
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.pathUtils import FilePathTpl
from base.model.utils import LanguageId


_TSchema = TypeVar('_TSchema', bound=Schema)


@dataclass
class SchemaMapping:
	schemaId: str
	pathFilter: str
	"""
	A filter string.

	searchStr syntax:

	``?``
		any single char, except \\\\ or /
	``\\*``
		any multiple chars, except \\\\ or /  (name of a single folder or file)
	``\\*\\*``
		any multiple chars, including \\\\ or /  (files or folders within any subdirectories)

	examples:

	``'C:\\\\Users\\\\*'``
		all user folders on windows
	``'C:/Users/*/Downloads'``
		the download folder of all user folders on windows
	``'C:/Users/roo?/**'``
		all files of all users that have a four letter name starting with 'roo', 'Roo', 'ROO', etc...
	``'C:\\\\**\\\\desktop.ini'``
		all desktop.ini files on your ``C:`` drive
	``'/**/hello*there*/no?Way/'``
		something crazy...
	``'webapp/WEB-INF/model/**'``
		everything within ``webapp/WEB-INF/model/``
	"""

	pattern: re.Pattern[str] = field(init=False)
	""" pattern generated from SchemaMapping.pathFilter """

	def __post_init__(self):
		_, regexStr = makeSearchPath(self.pathFilter, '')
		self.pattern = re.compile(regexStr)


_schemaMappings: dict[LanguageId, list[SchemaMapping]] = defaultdict(list)


def addSchemaMapping(language: LanguageId, mapping: SchemaMapping):
	_schemaMappings[language].append(mapping)


def getSchemaMapping(path: FilePathTpl, language: LanguageId) -> Optional[SchemaMapping]:
	if (mappings := _schemaMappings.get(language)) is not None:
		for mapping in mappings:
			if mapping.pattern.fullmatch(path[1]) is not None:
				return mapping


@overload
def getSchemaForPath(path: FilePathTpl, language: LanguageId) -> Optional[Schema]: ...
@overload
def getSchemaForPath(path: FilePathTpl, schemaCls: Type[_TSchema]) -> Optional[_TSchema]: ...


def getSchemaForPath(path: FilePathTpl, languageSchemaCls: LanguageId | Type[_TSchema]) -> Optional[Schema]:
	if isinstance(languageSchemaCls, str):
		language = languageSchemaCls
	else:
		language = languageSchemaCls.language
	mapping = getSchemaMapping(path, language)
	if mapping is not None:
		return GLOBAL_SCHEMA_STORE.get(mapping.schemaId, language)
	return None
