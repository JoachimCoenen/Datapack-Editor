from __future__ import annotations

import math
import os.path
import sys
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Type, Callable, Mapping, Any, Generator, AbstractSet, Generic, TypeAlias, final

from Cat.utils import Nothing, Anything
from Cat.utils.collections_ import AddToDictDecorator
from . import JSON_ID
from .core import *
from base.model.parsing.bytesUtils import strToBytes
from base.model.parsing.parser import parse
from base.model.pathUtils import normalizeDirSeparators, fromDisplayPath, loadBinaryFile, ZipFilePool
from base.model.utils import GeneralError, MDStr, Span, SemanticsError, WrappedError

JSON_TYPE_NAMES = {'null', 'boolean', 'number', 'string', 'array', 'object'}

_TT = TypeVar('_TT')
_TT2 = TypeVar('_TT2')
_TD = TypeVar('_TD')
_TJN = TypeVar('_TJN', bound=JsonNode)
_TJSD = TypeVar('_TJSD', bound=JsonData)


@dataclass(frozen=True, slots=True)
class V(Generic[_TT]):
	n: _TT
	ctx: TemplateContext

@final
@dataclass(frozen=True, slots=True)
class JD(V[_TJSD], Generic[_TJSD, _TT2]):
	n: _TJSD

	@property
	def data(self) -> _TT2:
		return self.n.data

	@property
	def span(self) -> Span:
		return self.n.span

	@property
	def schema(self) -> JsonSchema:
		return self.n.schema

	@property
	def typeName(self) -> str:
		return self.n.typeName


#JD = J[JsonData]
JInvalid: TypeAlias = JD[JsonInvalid, None]
JNull: TypeAlias = JD[JsonNull, None]
JBool: TypeAlias = JD[JsonBool, bool]
JNumber: TypeAlias = JD[JsonNumber, int | float]
JString: TypeAlias = JD[JsonString, str]
JArray: TypeAlias = JD[JsonArray, Array]
JObject: TypeAlias = JD[JsonObject, Object]


@dataclass
class SchemaLibrary:
	description: MDStr
	libraries: dict[str, SchemaLibrary]  # = field(default_factory=dict, init=False)
	templates: dict[str, SchemaTemplate]  # = field(default_factory=dict, init=False)
	definitions: dict[str, JsonSchema]  # = field(default_factory=dict, init=False)
	filePath: str

	@property
	def dirPath(self) -> str:
		return self.filePath.rpartition('/')[0]


@dataclass
class SchemaTemplate:
	description: MDStr
	params: OrderedDict[str, TemplateParam]
	body: JsonObject
	span: Span


@dataclass
class TemplateParam:
	name: str
	type: str
	description: MDStr
	optional: bool
	default: Optional[JD]
	span: Span


@dataclass
class TemplateContext:
	name: str
	filePath: str
	libraries: dict[str, SchemaLibrary]  # = field(default_factory=dict, init=False)
	arguments: dict[str, TemplateArg]  # = field(default_factory=dict, init=False)


@dataclass
class TemplateArg:
	value: Optional[JD]
	#libraries: dict[str, SchemaLibrary]
	# context: TemplateContext


@dataclass
class SchemaBuilder:
	orchestrator: SchemaBuilderOrchestrator
	errors: list[GeneralError] = field(default_factory=list, init=False)
	libraries: dict[str, SchemaLibrary] = field(default_factory=dict, init=False)

	@staticmethod
	def createError(message: MDStr, span: Span, style: str) -> SemanticsError:
		return SemanticsError(message, span=span, style=style)

	def error(self, message: MDStr, *, span: Span, ctx: TemplateContext, style: str = 'error') -> None:
		error = self.createError(message, span, style)
		self.errors.append(error)
		if style == 'error':
			raise ValueError(f"{error} in file {ctx.filePath}")

	# def parseSchemas(self, node: JsonObject) -> Optional[JsonSchema]:
	# 	title = self.optStrVal(node, 'title', '')
	# 	if (templates := self.optObject(node, '$templates')) is not None:
	# 		self.templates.update(self.parseTemplates(templates))
	#
	# 	if (definitions := self.optObject(node, '$definitions')) is not None:
	# 		self.definitions.update(self.parseDefinitions(definitions))
	#
	# 	body = self.reqObject(node, '$body')
	# 	schema = self.parseBody(body)
	# 	return schema

	def parseJsonSchema(self, root: JsonObject, filePath: str) -> Optional[JsonSchema]:
		ctx = TemplateContext('', filePath, self.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.optStrVal(root2, '$schema') != 'dpe/json/schema':
			self.error(MDStr("Not a JSON Schema"), span=root.span, ctx=ctx)
			return None

		title = self.optStrVal(root2, 'title', '')
		library = self._parseLibrary(root2, filePath, ctx)

		body = self.reqObject(root2, '$body')
		schema = self.parseBody(body)
		return schema

	def parseSchemaLibrary(self, root: JsonObject, filePath: str) -> Optional[SchemaLibrary]:
		ctx = TemplateContext('', filePath, self.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.optStrVal(root2, '$schema') != 'dpe/json/schema/library':
			self.error(MDStr("Not a JSON Schema Library"), span=root.span, ctx=ctx)
			return None

		title = self.optStrVal(root2, 'title', '')
		library = self._parseLibrary(root2, filePath, ctx)

		return root2.ctx.libraries['']

	def _parseLibrary(self, root: JObject, filePath: str, ctx: TemplateContext) -> SchemaLibrary:
		description = MDStr(self.optStrVal(root, 'description', ''))

		ctx.libraries[''] = SchemaLibrary(
			description=description,
			libraries=ctx.libraries,
			templates={},
			definitions={},
			filePath=filePath
		)

		libraries = self.optObjectRaw(root, '$libraries')
		if libraries.n is not None:
			self.parseLibraries(libraries, ctx)

		templates = self.optObjectRaw(root, '$templates')
		if templates.n is not None:
			self.parseTemplates(templates, ctx)

		definitions = self.optObjectRaw(root, '$definitions')
		if definitions.n is not None:
			self.parseDefinitions(definitions, ctx)

		return ctx.libraries['']

	def parseBody(self, body: JObject) -> JsonSchema:
		return self.parseType(body)

	def parseDefinitions(self, definitionsNode: JObject, ctx: TemplateContext) -> None:
		definitions: dict[str, JsonSchema] = ctx.libraries[''].definitions
		partialDefinitions = []
		for ref, prop in definitionsNode.data.items():
			if ref in definitions:
				self.error(MDStr(f"definition {ref!r} already defined before at {definitionsNode.data[ref].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			definition = self.reqObject(definitionsNode, ref)
			partialDefinition = self.handleTypePartial(definition)
			partialDefinitions.append(partialDefinition)
			definitions[ref] = next(partialDefinition)
		for partialDefinition in partialDefinitions:
			self.completePartialType(partialDefinition)

	def parseTemplates(self, templatesNode: JObject, ctx: TemplateContext) -> None:
		templates: dict[str, SchemaTemplate] = ctx.libraries[''].templates
		for ref, prop in templatesNode.data.items():
			if ref in templates:
				self.error(MDStr(f"template {ref!r} already defined before at {templates[ref].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			templateNode = self.reqObject(templatesNode, ref)
			templates[ref] = self.parseTemplate(templateNode, prop.key.span)

	def parseLibraries(self, librariesNode: JObject, ctx: TemplateContext) -> None:
		libraries: dict[str, SchemaLibrary] = ctx.libraries[''].libraries
		for ns, prop in librariesNode.data.items():
			if ns in libraries:
				self.error(MDStr(f"namespace {ns!r} already defined before at {librariesNode.data[ns].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			if not ns:
				self.error(MDStr(f"namespace cannot be an empty string"), span=prop.key.span, ctx=ctx)
				continue
			libraryFilePath = self.reqStrVal(librariesNode, ns)
			if dirPath := ctx.libraries[''].dirPath:
				libraryFilePath = f'{dirPath}/{libraryFilePath}'
			libraries[ns] = self.orchestrator.getSchemaLibrary(libraryFilePath)

	def parseArguments(self, refNode: JObject, template: SchemaTemplate, templateCtx: TemplateContext) -> dict[str, TemplateArg]:
		args = {}
		remainingParams = template.params.copy()
		for name, prop in refNode.data.items():
			if name.startswith('$'):
				continue
			if name in args:
				self.error(MDStr(f"args {name!r} already defined before at {args[name].value.span.start}"), span=prop.key.span, ctx=refNode.ctx)
			if (param := remainingParams.pop(name, None)) is not None:
				arg = prop.value
				arg = self.fromRef(JD(arg, refNode.ctx))
				if arg.typeName != param.type:
					msg = f"Unexpected argument type. Got {arg.typeName}, but expected type: {param.type}"
					self.error(MDStr(msg), span=arg.span, ctx=arg.ctx)
					raise ValueError(msg)
				args[name] = TemplateArg(arg)
			else:
				self.error(MDStr(f"unknown param {name!r}."), span=prop.key.span, ctx=refNode.ctx)

		for name, param in remainingParams.items():
			if param.default is not None:
				args[name] = TemplateArg(JD(param.default.n, templateCtx))
			elif param.optional:
				args[name] = TemplateArg(JD(None, templateCtx))
			else:
				self.error(MDStr(f"missing argument for param {name!r}."), span=refNode.span, ctx=refNode.ctx)
		return args

	def resolveDefRef(self, refNode: JString) -> JsonSchema:
		library, ns, lref = self.getNamespace(refNode)
		if (definition := library.definitions.get(lref)) is not None:
			return definition
		else:
			self.error(MDStr(f"No definition \"{lref}\" in namespace \"{ns}\"."), span=refNode.span, ctx=refNode.ctx)
			return JsonAnySchema(allowMultilineStr=None)

	def handleTypePartial(self, node: JObject) -> Generator[JsonSchema]:
		refNode = self.optStr(node, '$defRef')
		if refNode.n is not None:
			if len(node.data) > 1:
				self.error(MDStr(f"no additional attributes allowed for referenced definitions."), span=refNode.span, style='warning', ctx=node.ctx)
			yield self.resolveDefRef(refNode)
		else:
			type_ = self.reqStr(node, '$type')
			try:
				th = _typeHandlers[type_.n.data]
			except KeyError as e:
				self.error(MDStr(f"Unknown $type '{type_.n.data}'."),span=type_.n.span, ctx=type_.ctx)
				raise
			else:
				generator = th(self, node)
				definition = next(generator).setSpan(node.n.span, node.ctx.filePath)
				yield definition
				yield from generator

	@staticmethod
	def completePartialType(partialNode):
		try:
			next(partialNode)
		except StopIteration:
			pass
		else:
			raise RuntimeError("generator didn't stop")

	def parseType(self, node: JObject) -> JsonSchema:
		partialNode = self.handleTypePartial(node)
		schema = next(partialNode)
		self.completePartialType(partialNode)
		return schema

	def parseTemplate(self, node: JObject, span: Span) -> SchemaTemplate:
		description = MDStr(self.optStrVal(node, 'description', ''))
		paramsNode = self.optObject(node, '$params')
		if paramsNode.n is not None:
			params = self.parseParams(paramsNode)
		else:
			params = OrderedDict()
		body = self.reqObjectRaw(node, '$body')

		template = SchemaTemplate(
			description=description,
			params=params,
			body=body.n,
			span=span
		)
		return template

	def parseParams(self, paramsNode: JObject) -> OrderedDict[str, TemplateParam]:
		params = OrderedDict()
		for name, prop in paramsNode.data.items():
			if name in params:
				self.error(MDStr(f"param {name!r} already defined before at {params[name].span.start}"), span=prop.key.span, ctx=paramsNode.ctx)
				continue
			paramNode = self.reqObjectRaw(paramsNode, name)
			param = self.parseParam(paramNode, name, prop.key.span)
			params[name] = param
		return params

	def parseParam(self, node: JObject, name: str, span: Span) -> TemplateParam:
		type_ = MDStr(self.reqEnumVal(node, 'type', JSON_TYPE_NAMES))
		description = MDStr(self.optStrVal(node, 'description', ''))
		optional = self.optBoolVal(node, 'optional', False)
		# default = self.optVal(node, 'default')
		default = node.data.get('default')
		if default is not None:
			default = self.fromRef(JD(default.value, node.ctx))

		param = TemplateParam(
			name=name,
			type=type_,
			description=description,
			optional=optional,
			default=default,
			span=span
		)
		return param

	def fromRef(self, node: JD) -> JD:
		if not isinstance(node.n, JsonObject):
			return node
		refNode = self.optStr(node, '$ref')
		if refNode.n is None:
			return node
		ref = refNode.data

		if ref.startswith('#'):
			arg = refNode.ctx.arguments.get(ref[1:])
			if arg is None:
				self.error(MDStr(f"no parameter \"{ref[1:]}\" registered in current context ({refNode.ctx.filePath})."), span=refNode.span, ctx=refNode.ctx)
			return self.fromRef(arg.value)

		library, ns, lref = self.getNamespace(refNode)

		if (template := library.templates.get(lref)) is not None:
			templateCtx = TemplateContext(lref, library.filePath, library.libraries, {})
			templateCtx.arguments.update(self.parseArguments(node, template, templateCtx))
			return JD(template.body, templateCtx)
		else:
			self.error(MDStr(f"No template \"{lref}\" in namespace \"{ns}\"."), span=refNode.span, ctx=refNode.ctx)

	def getNamespace(self, refNode: JString):
		ns, _, lref = refNode.data.rpartition(':')
		library = refNode.ctx.libraries.get(ns)
		if library is None:
			self.error(
				MDStr(f"no namespace \"{ns}\" registered in current context ({refNode.ctx.filePath})."), span=Span(
					refNode.span.start + 1,
					refNode.span.start + 1 + refNode.n.indexMapper.toEncoded(len(strToBytes(ns)))
				), ctx=refNode.ctx)
		return library, ns, lref

	def checkType(self, data: JD, type_: Type[_TJSD]) -> JD[_TJSD]:
		if isinstance(data.n, type_):
			return data
		msg = f"Unexpected type. Got {type(data.n)}, but expected type: {type_}"
		self.error(MDStr(msg), span=data.span, ctx=data.ctx)
		raise ValueError(msg)

	def fromRefCheckType(self, node: JD, type_: Type[_TJSD]) -> JD[_TJSD]:
		value = self.fromRef(node)
		return self.checkType(value, type_)

	def _req(self, obj: JObject, key: str) -> JD:
		if (prop := obj.n.data.get(key)) is not None:
			return JD(prop.value, obj.ctx)
		msg = MDStr(f"Missing required property '{key}'")
		self.error(msg, span=obj.span, ctx=obj.ctx)
		raise ValueError(msg)

	def _opt(self, obj: JObject, key: str) -> JD:
		if (prop := obj.n.data.get(key)) is not None:
			return self.fromRef(JD(prop.value, obj.ctx))
		return JD(None, obj.ctx)

	def checkOptions(self, data: JD[_TJSD], options: AbstractSet[_TT]) -> JD[_TJSD]:
		if data.n.data in options:
			return data
		optionsStr = ', '.join(repr(opt) for opt in options)
		msg = f"Unexpected value. Got {data.n.data}, but expected one of: ({optionsStr})"
		self.error(MDStr(msg), span=data.span, ctx=data.ctx)
		raise ValueError(msg)

	def reqType(self, obj: JObject, key: str, type_: Type[_TJSD]) -> JD[_TJSD]:
		if (prop := obj.n.data.get(key)) is not None:
			return self.fromRefCheckType(JD(prop.value, obj.ctx), type_)
		msg = f"Missing required property '{key}'"
		self.error(MDStr(msg), span=obj.span, ctx=obj.ctx)
		raise ValueError(msg)

	def optType(self, obj: JObject, key: str, type_: Type[_TJSD], default: _TD = None) -> JD[_TJSD | _TD]:
		if (prop := obj.n.data.get(key)) is not None:
			return self.fromRefCheckType(JD(prop.value, obj.ctx), type_)
		return JD(default, obj.ctx)

	def reqBool(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonBool).n

	def reqNumber(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonNumber).n

	def reqStr(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonString)

	def reqArray(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonArray)

	def reqObject(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonObject)

	def reqObjectRaw(self, obj: JObject, key: str):
		return self.checkType(self._req(obj, key), JsonObject)

	def optBool(self, obj: JObject, key: str, default=None):
		return self.optType(obj, key, JsonBool, default).n

	def optNumber(self, obj: JObject, key: str, default=None):
		return self.optType(obj, key, JsonNumber, default).n

	def optStr(self, obj: JObject, key: str, default=None):
		return self.optType(obj, key, JsonString, default)

	def optArray(self, obj: JObject, key: str, default=None):
		return self.optType(obj, key, JsonArray, default)

	def optObject(self, obj: JObject, key: str, default=None):
		return self.optType(obj, key, JsonObject, default)

	def optObjectRaw(self, obj: JObject, key: str, default=None):
		if (prop := obj.n.data.get(key)) is not None:
			return self.checkType(JD(prop.value, obj.ctx), JsonObject)
		return JD(default, obj.ctx)

	def reqBoolVal(self, obj: JObject, key: str) -> bool:
		return self.reqType(obj, key, JsonBool).n.data

	def reqNumberVal(self, obj: JObject, key: str) -> int | float:
		return self.reqType(obj, key, JsonNumber).n.data

	def reqStrVal(self, obj: JObject, key: str) -> str:
		return self.reqType(obj, key, JsonString).n.data

	def reqEnumVal(self, obj: JObject, key: str, options: AbstractSet[str]) -> str:
		data = self.reqStr(obj, key)
		return self.checkOptions(data, options).n.data

	def reqArrayVal(self, obj: JObject, key: str) -> V[list[JsonData]]:
		array = self.reqType(obj, key, JsonArray)
		return V(array.n.data, array.ctx)

	def reqArrayVal2(self, obj: JObject, key: str, type_: Type[_TJN]) -> list[JD[_TJN]]:
		array = self.reqType(obj, key, JsonArray)
		return [self.fromRefCheckType(JD(elem, array.ctx), type_) for elem in array.n.data]

	def optVal(self, obj: JObject, key: str, default: _TD = None) -> V[JsonTypes | _TD]:
		if (prop := obj.n.data.get(key)) is not None:
			value = self.fromRef(JD(prop.value, obj.ctx))
			return V(value.n.data, value.ctx)
		return V(default, obj.ctx)

	def optBoolVal(self, obj: JObject, key: str, default: _TD = None) -> bool | _TD:
		if (data := self.optType(obj, key, JsonBool, None).n) is not None:
			return data.data
		return default

	def optNumberVal(self, obj: JObject, key: str, default: _TD = None) -> int | float | _TD:
		if (data := self.optType(obj, key, JsonNumber, None).n) is not None:
			return data.data
		return default

	def optStrVal(self, obj: JObject, key: str, default: _TD = None) -> str | _TD:
		if (data := self.optType(obj, key, JsonString, None).n) is not None:
			return data.data
		return default

	def optEnumVal(self, obj: JObject, key: str, options: AbstractSet[str], default: _TD = None) -> str | _TD:
		data = self.optStr(obj, key)
		if data.n is not None:
			return self.checkOptions(data, options).n.data
		return default

	def optArrayVal(self, obj: JObject, key: str, default: _TD = None) -> V[list[JsonData] | _TD]:
		array = self.optType(obj, key, JsonArray, None)
		if array.n is not None:
			return V(array.n.data, array.ctx)
		return V(default, obj.ctx)

	def optArrayVal2(self, obj: JObject, key: str, type_: Type[_TJSD]) -> list[JD[_TJSD]]:
		array = self.optArrayVal(obj, key, None)
		if array.n is not None:
			return [self.fromRefCheckType(JD(elem, array.ctx), type_) for elem in array.n]
		return []


@dataclass
class SchemaBuilderOrchestrator:
	baseDir: str
	# paths: dict[str, JsonSchema]
	# files: dict[str, JsonSchema] = field(default_factory=dict, init=False)
	schemas: dict[str, JsonSchema] = field(default_factory=dict, init=False)
	libraries: dict[str, SchemaLibrary] = field(default_factory=dict, init=False)
	errors: dict[str, list[GeneralError]] = field(default_factory=lambda: defaultdict(list), init=False)

	def getSchemaLibrary(self, path: str) -> SchemaLibrary:
		fullPath = self.getFullPath(path)
		if (library := self.libraries.get(fullPath)) is not None:
			return library
		library = self.libraries[fullPath] = self._loadLibrary(fullPath)
		return library

	def getSchema(self, path: str) -> Optional[JsonSchema]:
		fullPath = self.getFullPath(path)
		if (schema := self.schemas.get(fullPath)) is not None:
			return schema
		schema = self.schemas[fullPath] = self._loadJsonSchema(fullPath)
		return schema

	def getFullPath(self, path: str) -> str:
		fullPath = os.path.join(self.baseDir, path)
		fullPath = normalizeDirSeparators(fullPath)
		return fullPath

	def clear(self):
		self.schemas.clear()
		self.libraries.clear()
		self.errors.clear()

	def clearErrors(self):
		self.errors.clear()

	def _loadJsonSchema(self, fullPath: str) -> Optional[JsonSchema]:
		try:
			with ZipFilePool() as pool:
				schemaBytes = loadBinaryFile(fromDisplayPath(fullPath), pool)
		except OSError as ex:
			self.errors[fullPath].append(WrappedError(ex))
			return None
		schemaJson, errors = parse(schemaBytes, filePath=fullPath, language=JSON_ID, schema=None)
		schemaJson: JsonObject
		self.errors[fullPath].extend(errors)
		builder = SchemaBuilder(orchestrator=self)
		try:
			schema = builder.parseJsonSchema(schemaJson, fullPath)
		except Exception as ex:
			self.errors[fullPath].extend(builder.errors)
			self.errors[fullPath].append(WrappedError(ex))
			return None
		self.errors[fullPath].extend(builder.errors)
		return schema

	def _loadLibrary(self, fullPath: str) -> SchemaLibrary:
		try:
			with ZipFilePool() as pool:
				schemaBytes = loadBinaryFile(fromDisplayPath(fullPath), pool)
		except OSError as ex:
			self.errors[fullPath].append(WrappedError(ex))
			return SchemaLibrary(MDStr(''), {}, {}, {}, fullPath)
		schemaJson, errors = parse(schemaBytes, filePath=fullPath, language=JSON_ID, schema=None)
		schemaJson: JsonObject
		self.errors[fullPath].extend(errors)
		builder = SchemaBuilder(orchestrator=self)
		try:
			library = builder.parseSchemaLibrary(schemaJson, fullPath)
		except Exception as ex:
			self.errors[fullPath].extend(builder.errors)
			self.errors[fullPath].append(WrappedError(ex))
			return SchemaLibrary(MDStr(''), {}, {}, {}, fullPath)
		return library


_typeHandlers: dict[str, Callable[[SchemaBuilder, JObject], Generator[JsonSchema]]] = {}


def propertyHandler(self: SchemaBuilder, name: str, node: JObject) -> PropertySchema:
	type_ = self.optStrVal(node, '$type') or self.optStrVal(node, '$defRef')
	if type_ is not None:
		value = node
		description = None
		optional = False
		default = None
		decidingProp = None
		requires = ()
		hates = ()
		deprecated = False
		allowMultilineStr = None
		values = JD(None, node.ctx)
	else:
		description, deprecated, allowMultilineStr = readCommonValues(self, node)
		optional = self.optBoolVal(node, 'optional', False)
		default = self._opt(node, 'default')
		if default.n is not None:
			default = toPyValue(self, default)
		else:
			default = None
		decidingProp = self.optStrVal(node, 'decidingProp', None)
		# reqVal = self.optArrayVal(node, 'requires', [])
		# requires = tuple(self.fromRefCheckType(data, reqValCtx, JsonString).n.data for data in reqVal)
		requires = tuple(elem.n.data for elem in self.optArrayVal2(node, 'requires', JsonString))
		hates = tuple(elem.n.data for elem in self.optArrayVal2(node, 'hates', JsonString))

		value = self.optObject(node, 'value')
		values = self.optObject(node, 'values')

	if value.n is not None:
		value = self.parseType(value)
		values = None
	elif values.n is not None:
		value = None
		if decidingProp is None:
			self.error(MDStr(f"Missing property 'decidingProp' required by property 'values'"), span=node.span, ctx=node.ctx)
		values = {
			key: self.parseType(self.reqObject(values, key))
			for key in values.n.data.keys()
		}
	else:
		self.error(MDStr(f"Missing required property: oneOf('value', 'values')"), span=node.span, ctx=node.ctx)

	return PropertySchema(
		name=name,
		description=description,
		value=value,
		optional=optional,
		default=default,  # todo
		decidingProp=decidingProp,
		values=values,
		requires=requires,
		hates=hates,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)


def inheritanceHandler(self: SchemaBuilder, node: JObject) -> Inheritance:
	refNode = self.reqStr(node, 'defRef')
	decidingProp = self.optStrVal(node, 'decidingProp', None)
	if decidingProp:
		decidingValues = self.reqArrayVal2(node, 'decidingValues', JsonString)
	else:
		decidingValues = []

	refSchema = self.resolveDefRef(refNode)
	if not isinstance(refSchema, JsonObjectSchema):
		self.error(MDStr(f"Definition \"{refNode.data}\" is not an object schema."), span=refNode.span, ctx=refNode.ctx)
	return Inheritance(
		schema=refSchema,
		decidingProp=decidingProp,
		decidingValues=tuple(dv.data for dv in decidingValues),
	)


typeHandler = AddToDictDecorator(_typeHandlers)


@typeHandler('object')
def objectHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	defaultProp = self.optType(node, 'default-property', JsonObject)
	if defaultProp.n is not None:
		properties = self.optObjectRaw(node, 'properties')
	else:
		properties = self.reqObjectRaw(node, 'properties')

	inherits = self.optArrayVal2(node, 'inherits', JsonObject)

	objectSchema = JsonObjectSchema(
		description=description,
		properties=[],
		inherits=[],
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema

	schemaProps = []
	if properties.n is not None:
		for name in properties.n.data.keys():
			prop = self.reqType(properties, name, JsonObject)
			schemaProps.append(propertyHandler(self, name, prop).setSpan(properties.n.data[name].value.span, properties.ctx.filePath))
	if defaultProp.n is not None:
		schemaProps.append(propertyHandler(self, Anything(), defaultProp).setSpan(node.n.data['default-property'].value.span, node.ctx.filePath))

	schemaInherits = []
	for inherit in inherits:
		schemaInherits.append(inheritanceHandler(self, inherit))

	objectSchema.properties = tuple(schemaProps)
	objectSchema.inherits = tuple(schemaInherits)
	objectSchema.buildPropertiesDict()


@typeHandler('array')
def arrayHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	partialElement = self.handleTypePartial(self.reqObject(node, 'element'))
	element = next(partialElement)
	objectSchema = JsonArraySchema(
		description=description,
		element=element,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	self.completePartialType(partialElement)


@typeHandler('union')
def unionHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	options = self.reqArrayVal2(node, 'options', JsonObject)
	objectSchema = JsonUnionSchema(
		description=description,
		options=[],
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema

	schemaOptions = []
	for option in options:
		option4 = self.parseType(option)
		schemaOptions.append(option4)
	objectSchema.options = tuple(schemaOptions)


@typeHandler('any')
def anyHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	objectSchema = JsonAnySchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


@typeHandler('string')
def stringHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	type_ = self.optStr(node, 'type')
	args = self.optObject(node, 'args')

	objectSchema = JsonStringSchema(
		description=description,
		type=_getJsonArgType(self, type_) if type_.n is not None else None,
		args=toPyValue(self, args) if args.n is not None else None,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


@typeHandler('enum')
def enumHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	options = self.reqObject(node, 'options')
	oCtx = options.ctx
	options2 = {self.fromRefCheckType(JD(p.key, oCtx), JsonString).data: self.fromRefCheckType(JD(p.value, oCtx), JsonString).data for p in options.data.values()}

	objectSchema = JsonStringOptionsSchema(
		description=description,
		options=options2,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


@typeHandler('boolean')
def boolHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	objectSchema = JsonBoolSchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


def _numberHandler(self: SchemaBuilder, node: JObject, cls: Type[JsonNumberSchema]) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	minVal = self.optNumberVal(node, 'min', -math.inf)
	maxVal = self.optNumberVal(node, 'max', math.inf)
	objectSchema = cls(
		description=description,
		minVal=minVal,
		maxVal=maxVal,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


@typeHandler('integer')
def integerHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	return _numberHandler(self, node, JsonIntSchema)


@typeHandler('float')
def floatHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	return _numberHandler(self, node, JsonFloatSchema)


@typeHandler('null')
def nullHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	objectSchema = JsonNullSchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


@typeHandler('calculated')
def calculatedHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	func = self.reqStrVal(node, 'function')
	func = lookupFunction(func)

	objectSchema = JsonCalculatedValueSchema(
		description=description,
		func=func,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema


def lookupFunction(qName: str) -> Callable:
	splitQName = qName.split('.')
	mod = sys.modules.get(splitQName[0])
	f = mod
	for part in splitQName[1:]:
		f = getattr(f, part)
	assert callable(f)
	return f


def readCommonValues(self: SchemaBuilder, node: JObject) -> tuple[MDStr, bool, bool]:
	description = MDStr(self.optStrVal(node, 'description', ''))
	deprecated = self.optBoolVal(node, 'deprecated', False)
	allowMultilineStr = self.optBoolVal(node, 'allowMultilineStr')
	return description, deprecated, allowMultilineStr


def _getJsonArgType(self: SchemaBuilder, type_: JString) -> Optional[JsonArgType]:
	try:
		return ALL_NAMED_JSON_ARG_TYPES[type_.data]
	except KeyError:
		pass
	# from model.commands.argumentTypes import ALL_NAMED_ARGUMENT_TYPES
	# try:
	# TODO: maybe 	return ALL_NAMED_ARGUMENT_TYPES[type_.data]
	# except KeyError:
	# 	pass
	self.error(MDStr(f"Unknown JsonArgType '{type_.data}'"), span=type_.span, ctx=type_.ctx, style='warning')
	return None


_toPyValueHandlers: dict[str, Callable[[SchemaBuilder, JD], Any]] = {}

_toPyValueHandler = AddToDictDecorator(_toPyValueHandlers)


def toPyValue(self: SchemaBuilder, data: JD) -> Any:
	return _toPyValueHandlers[data.typeName](self, data)


@_toPyValueHandler('object')
def _objectHandler(self: SchemaBuilder, node: JObject) -> dict:
	return {toPyValue(self, self.fromRef(JD(p.key, node.ctx))): toPyValue(self, self.fromRef(JD(p.value, node.ctx))) for p in node.data.values()}


@_toPyValueHandler('array')
def _arrayHandler(self: SchemaBuilder, node: JArray) -> list:
	return [toPyValue(self, self.fromRef(JD(e, node.ctx))) for e in node.data]


@_toPyValueHandler('string')
@_toPyValueHandler('boolean')
@_toPyValueHandler('number')
@_toPyValueHandler('null')
def _stringHandler(self: SchemaBuilder, node: JString) -> str:
	return node.data


def bytesFromFile(srcPath: str) -> bytes:
	with open(srcPath, 'rb') as f:
		return f.read()


# class ComplexEncoder(json.JSONEncoder):
# 	def default(self, obj):
# 		# if isinstance(obj, JsonSchema):
# 		# 	raise ValueError('ComplexEncoder JsonSchema')
# 		# 	dict_ = OrderedDict((attr, getattr(obj, attr)) for st in type(obj).__mro__ for attr in getattr(st, '_fields', ()))
# 		# 	dict_['$type'] = obj.typeName
# 		# 	dict_.move_to_end('$type', False)
# 		# 	return dict_
# 		from model.datapack.datapackContents import ResourceLocationSchema
# 		if isinstance(obj, (JsonArgType, ResourceLocationSchema, ArgumentType)):
# 			return obj.name
# 		# Let the base class default method raise the TypeError
# 		return json.JSONEncoder.default(self, obj)
#
#
# def emitSchema(schema: JsonSchema) -> str:
# 	structure = buildJsonStructure(schema)
# 	text = emitter.emitJson(structure, cls=ComplexEncoder, indent=2)
# 	return text


def traverse(obj, memo: dict[int, JsonSchema], onHasMemo: Callable[[JsonSchema], Any], *, skipMemoCheck: bool = False):
	if isinstance(obj, JsonSchema):
		if id(obj) in memo and not skipMemoCheck:
			return onHasMemo(obj)
		memo[id(obj)] = obj

		result = OrderedDict()
		result['$type'] = obj.typeName
		for st in type(obj).__mro__:
			for attr, defaultVal in getattr(st, '_fields', {}).items():
				val = getattr(obj, attr)
				if val is Nothing or val != defaultVal:
					result[attr] = traverse(val, memo, onHasMemo)
		obj.postProcessJsonStructure(result)
	elif isinstance(obj, (list, tuple)):
		result = []
		for val in obj:
			result.append(traverse(val, memo, onHasMemo))
	elif isinstance(obj, Mapping):
		result = OrderedDict()
		for key, val in obj.items():
			result[key] = traverse(val, memo, onHasMemo)
	else:
		result = obj
	return result


def buildJsonStructure(schema: JsonSchema):
	sharedSchemas = findDuplicates(schema)

	def onHasMemo2(obj: JsonSchema):
		return {'$defRef': sharedSchemas[id(obj)][0]}

	memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
	definitions = {}
	for id_, (ref, obj) in sharedSchemas.items():
		definitions[ref] = traverse(obj, memo2, onHasMemo2, skipMemoCheck=True)

	# memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
	body = traverse(schema, memo2, onHasMemo2)

	structure = {
		'$schema': 'dpe/json/schema',
		'$body': body,
		'$definitions': definitions,
	}
	return structure


def findDuplicates(schema: JsonSchema):
	usageCounts = defaultdict(int)

	def onHasMemo(obj: JsonSchema):
		usageCounts[id(obj)] += 1
		return None

	memo = {}
	traverse(schema, memo, onHasMemo)
	sharedSchemas = {
		id_: (f'%%{i}!', memo[id_])
		for i, (id_, cnt) in enumerate(usageCounts.items())
	}
	return sharedSchemas







