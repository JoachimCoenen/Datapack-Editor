from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Type, Generic, Mapping, overload

from base.model.parsing.tree import Schema
from base.model.utils import LanguageId


_TSchema = TypeVar('_TSchema', bound=Schema)


@dataclass(frozen=True)
class SchemaStore(Generic[_TSchema]):
	# _registeredSchemas: dict[str, dict[str, _TSchema]] = field(default_factory=lambda: defaultdict(dict))
	_registeredSchemas2: dict[str, _TSchema] = field(default_factory=dict)

	def get(self, name: str) -> Optional[_TSchema]:
		# ns, _, name = name.rpartition(':')
		# return self._registeredSchemas.get(ns, {}).get(name)
		return self._registeredSchemas2.get(name)

	def registerSchema(self, name: str, schema: _TSchema):
		# ns, _, name = name.rpartition(':')
		# self._registeredSchemas[ns][name] = schema
		self._registeredSchemas2[name] = schema

	def unregisterSchema(self, name: str):
		# ns, _, name = name.rpartition(':')
		# byName = self._registeredSchemas.get(ns)
		# if byName is not None:
		# 	byName.pop(name, None)
		# 	if not byName:
		# 		self._registeredSchemas.pop(ns)
		self._registeredSchemas2.pop(name, None)

	# def unregisterNamespace(self, ns: str):
	# 	self._registeredSchemas.pop(ns, None)


@dataclass(frozen=True)
class GlobalSchemaStore:
	_schemaStores: dict[LanguageId, SchemaStore] = field(default_factory=lambda: defaultdict(SchemaStore))

	@overload
	def get(self, name: str, language: LanguageId) -> Optional[Schema]: ...
	@overload
	def get(self, name: str, schemaCls: Type[_TSchema]) -> Optional[_TSchema]: ...

	def get(self, name: str, languageSchemaCls: LanguageId | Type[_TSchema]) -> Optional[Schema]:
		if isinstance(languageSchemaCls, str):
			language = languageSchemaCls
		else:
			language = languageSchemaCls.language
		return self._schemaStores[language].get(name)

	def getAllForLanguage(self, language: LanguageId) -> Mapping[str, Schema]:
		return self._schemaStores[language]._registeredSchemas2

	def registerSchema(self, name: str, schema: Schema):
		self._schemaStores[schema.language].registerSchema(name, schema)

	def unregisterSchema(self, name: str, language: LanguageId):
		self._schemaStores[language].unregisterSchema(name)

	# def unregisterNamespace(self, ns: str, language: LanguageId):
	# 	self._schemaStores[language].unregisterNamespace(ns)


GLOBAL_SCHEMA_STORE: GlobalSchemaStore = GlobalSchemaStore()

__all__ = [
	'SchemaStore',
	'GlobalSchemaStore',
	'GLOBAL_SCHEMA_STORE',
]
