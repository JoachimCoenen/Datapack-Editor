from __future__ import annotations

import math
import os.path
import sys
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Collection, NamedTuple, Optional, TypeVar, Type, Callable, Mapping, Any, Generator, AbstractSet, \
	Generic, TypeAlias, final, overload, Literal, NoReturn, cast, Iterator

from cat.utils import Nothing, Anything
from cat.utils.collections_ import AddToDictDecorator
from . import JSON_ID
from .core import *
from base.model.parsing.bytesUtils import strToBytes
from base.model.parsing.parser import parse
from base.model.pathUtils import normalizeDirSeparators, fromDisplayPath, loadBinaryFile, ZipFilePool
from base.model.utils import GeneralError, MDStr, Span, SemanticsError, WrappedError


TEMPLATE_REF_PROP = '$ref'
DEF_REF_PROP = '$defRef'
OPTIONAL_PREFIXES_PROP = 'optionalPrefixes'

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
	errors: list[GeneralError] = field(default_factory=list)
	libraries: dict[str, SchemaLibrary] = field(default_factory=dict, init=False)
	objectSchemasToBeFinished: list[JsonObjectSchema] = field(default_factory=list, init=False)

	@staticmethod
	def createError(message: MDStr, span: Span, style: str) -> SemanticsError:
		return SemanticsError(message, span=span, style=style)

	@overload
	def error(self, message: MDStr, *, span: Span, ctx: TemplateContext, style: Literal['error'] = 'error') -> NoReturn: ...
	@overload
	def error(self, message: MDStr, *, span: Span, ctx: TemplateContext, style: Literal['warning', 'hint']) -> None: ...

	def error(self, message: MDStr, *, span: Span, ctx: TemplateContext, style: str = 'error') -> None:
		error = self.createError(message, span, style)
		self.addErrors((error,), ctx=ctx)

	def addErrors(self, errors: Collection[GeneralError], *, ctx: TemplateContext) -> None:
		self.errors.extend(errors)
		if any(error.style == 'error' for error in errors):
			raise ValueError(f"There are errors in file {ctx.filePath}")

	def parseJsonSchema(self, root: JsonObject, filePath: str) -> Optional[JsonSchema]:
		ctx = TemplateContext('', filePath, self.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.optStrVal(root2, '$schema') != 'dpe/json/schema':
			self.error(MDStr("Not a JSON Schema"), span=root.span, ctx=ctx)
			return None

		title = self.optStrVal(root2, 'title', '')
		library, partial = self._parseLibraryPartial(root2, filePath, ctx)
		partial.do().do().finish()

		body = self.reqObject(root2, '$body')
		schema = self.parseBody(body)
		return schema

	def parseSchemaLibraryPartial(self, root: JsonObject, filePath: str) -> tuple[Optional[SchemaLibrary], Doer2]:
		"""" !!! 3-step generator !!! """
		ctx = TemplateContext('', filePath, self.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.optStrVal(root2, '$schema') != 'dpe/json/schema/library':
			self.error(MDStr("Not a JSON Schema Library"), span=root.span, ctx=ctx)
			return None, Doer2.NOP
		else:
			return self._parseLibraryPartial(root2, filePath, ctx)

	def _parseLibraryPartial(self: SchemaBuilder, root: JObject, filePath: str, ctx: TemplateContext) -> tuple[SchemaLibrary, Doer2]:
		description = MDStr(self.optStrVal(root, 'description', ''))

		library = ctx.libraries[''] = SchemaLibrary(
			description=description,
			libraries=ctx.libraries,
			templates={},
			definitions={},
			filePath=filePath
		)

		def _parseLibraryPartial1() -> Doer1:
			"""" !!! 3-step generator !!! """

			libraries = self.optObjectRaw(root, '$libraries')
			partialLibraries = self._parsePartial(libraries, self.parseLibrariesPartial, ctx)
			next(partialLibraries)

			templates = self.optObjectRaw(root, '$templates')
			if templates is not None:
				self.parseTemplates(templates, ctx)

			definitions = self.optObjectRaw(root, '$definitions')
			partialDefinitions = self._parsePartial(definitions, self.parseDefinitionsPartial, ctx)
			next(partialDefinitions)

			def _parseLibraryPartial2() -> Finisher:
				next(partialLibraries)
				next(partialDefinitions)

				def _parseLibraryPartial3() -> None:
					completePartialParse(partialLibraries)
					completePartialParse(partialDefinitions)

				return Finisher(_parseLibraryPartial3)

			return Doer1(_parseLibraryPartial2)

		return library, Doer2(_parseLibraryPartial1)

	@staticmethod
	def _parsePartial(node: Optional[JObject], parser: Callable[[JObject, TemplateContext], Generator[None]], ctx: TemplateContext) -> Generator[None]:
		return parser(node, ctx) if node is not None else _nopParserPartial(None, 2)

	def parseBody(self, body: JObject) -> JsonSchema:
		body, finisher = self.parseType(body)
		finisher.finish()
		return body

	def parseDefinitionsPartial(self, definitionsNode: JObject, ctx: TemplateContext) -> Generator[None]:
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

		yield None
		for partialDefinition in partialDefinitions:
			next(partialDefinition)

		yield None
		for partialDefinition in partialDefinitions:
			completePartialParse(partialDefinition)

	def parseTemplates(self, templatesNode: JObject, ctx: TemplateContext) -> None:
		templates: dict[str, SchemaTemplate] = ctx.libraries[''].templates
		for ref, prop in templatesNode.data.items():
			if ref in templates:
				self.error(MDStr(f"template {ref!r} already defined before at {templates[ref].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			templateNode = self.reqObject(templatesNode, ref)
			templates[ref] = self.parseTemplate(templateNode, prop.key.span)

	def parseLibrariesPartial(self, librariesNode: JObject, ctx: TemplateContext) -> Generator[None]:
		"""" !!! 3-step generator !!! """
		partialLibraries2: list[Doer2] = []
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

			libraries[ns], partial = self.orchestrator._getSchemaLibraryPartial(libraryFilePath)
			partialLibraries2.append(partial)
		yield

		partialLibraries1 = [partial.do() for partial in partialLibraries2]
		finishers = [partial.do() for partial in partialLibraries1]
		yield
		for finisher in finishers:
			finisher.finish()

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
				arg = self.fromRef2(arg, refNode.ctx)
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
			else:
				self.error(MDStr(f"missing argument for param {name!r}."), span=refNode.span, ctx=refNode.ctx)
		return args

	def handleTypePartial(self, node: JObject) -> Generator[JsonSchema]:
		refNode = self.optStr(node, DEF_REF_PROP)
		if refNode is not None:
			if len(node.data) > 1:
				self.error(MDStr(f"no additional attributes allowed for referenced definitions."), span=refNode.span, style='warning', ctx=node.ctx)
			yield self.resolveDefRef(refNode)
			yield None
		else:
			type_ = self.reqStr(node, '$type')
			try:
				th = _typeHandlers[type_.n.data]
			except KeyError as e:
				self.error(MDStr(f"Unknown $type '{type_.n.data}'."), span=type_.n.span, ctx=type_.ctx)
				raise
			else:
				partialDefinition = th(self, node)
				definition = next(partialDefinition).setSpan(node.n.span, node.ctx.filePath)
				yield definition
				definition = next(partialDefinition)
				yield definition
				completePartialParse(partialDefinition)

	def parseType(self, node: JObject) -> tuple[JsonSchema, Finisher]:
		partialNode = self.handleTypePartial(node)
		schema = next(partialNode)
		next(partialNode)
		return schema, Finisher(lambda: completePartialParse(partialNode))

	def parseTemplate(self, node: JObject, span: Span) -> SchemaTemplate:
		description = MDStr(self.optStrVal(node, 'description', ''))
		paramsNode = self.optObject(node, '$params')
		params = self.parseParams(paramsNode) if paramsNode is not None else OrderedDict()
		body = self.reqObjectRaw(node, '$body')  # will be resolved later, if necessary.

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
		default = self._optProp(node, 'default')

		param = TemplateParam(
			name=name,
			type=type_,
			description=description,
			default=default,
			span=span
		)
		return param

	def getNamespace(self, refNode: JString) -> tuple[Optional[SchemaLibrary], str, str]:
		ns, _, lref = refNode.data.rpartition(':')
		library = refNode.ctx.libraries.get(ns)
		if library is None:
			self.error(
				MDStr(f"no namespace \"{ns}\" registered in current context ({refNode.ctx.filePath})."), span=Span(
					refNode.span.start + 1,
					refNode.span.start + 1 + refNode.n.indexMapper.toEncoded(len(strToBytes(ns)))
				), ctx=refNode.ctx)
		return library, ns, lref

	def resolveDefRef(self, refNode: JString) -> JsonSchema:
		library, ns, lref = self.getNamespace(refNode)
		if (definition := library.definitions.get(lref)) is not None:
			return definition
		else:
			self.error(MDStr(f"No definition \"{lref}\" in namespace \"{ns}\"."), span=refNode.span, ctx=refNode.ctx)
			return JsonAnySchema(allowMultilineStr=None)

	def fromRef(self, node: JD) -> JD:
		if not isinstance(node.n, JsonObject):
			return node
		if (refNode := self.optStr(node, TEMPLATE_REF_PROP)) is None:
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
			return self.fromRef(JD(template.body, templateCtx))  # be aware of possible infinite recursion!
		else:
			self.error(MDStr(f"No template \"{lref}\" in namespace \"{ns}\"."), span=refNode.span, ctx=refNode.ctx)

	def fromRef2(self, data: _TJSD, ctx: TemplateContext) -> JD[_TJSD]:
		return self.fromRef(JD(data, ctx))

	def checkType(self, data: JD, type_: Type[_TJSD]) -> JD[_TJSD]:
		if isinstance(data.n, type_):
			return data
		msg = f"Unexpected type. Got {type(data.n)}, but expected type: {type_}"
		self.error(MDStr(msg), span=data.span, ctx=data.ctx)
		raise ValueError(msg)

	def checkOptions(self, data: JD[_TJSD], options: AbstractSet[_TT]) -> JD[_TJSD]:
		if data.n.data in options:
			return data
		optionsStr = ', '.join(repr(opt) for opt in options)
		msg = f"Unexpected value. Got {data.n.data}, but expected one of: ({optionsStr})"
		self.error(MDStr(msg), span=data.span, ctx=data.ctx)
		raise ValueError(msg)

	def _reqProp(self, obj: JObject, key: str) -> JD:
		if (prop := obj.n.data.get(key)) is not None:
			return JD(prop.value, obj.ctx)
		msg = MDStr(f"Missing required property '{key}'")
		self.error(msg, span=obj.span, ctx=obj.ctx)
		raise ValueError(msg)

	def _optProp(self, obj: JObject, key: str) -> Optional[JD]:
		if (prop := obj.n.data.get(key)) is not None:
			return self.fromRef2(prop.value, obj.ctx)
		return None

	def reqType(self, obj: JObject, key: str, type_: Type[_TJSD]) -> JD[_TJSD]:
		data = self._reqProp(obj, key)
		return self.checkType(self.fromRef(data), type_)

	def reqBool(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonBool)

	def reqNumber(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonNumber)

	def reqStr(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonString)

	def reqArray(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonArray)

	def reqObject(self, obj: JObject, key: str):
		return self.reqType(obj, key, JsonObject)

	def reqObjectRaw(self, obj: JObject, key: str):
		return self.checkType(self._reqProp(obj, key), JsonObject)

	def optType(self, obj: JObject, key: str, type_: Type[_TJSD]) -> Optional[JD[_TJSD]]:
		data = self._optProp(obj, key)
		return self.checkType(self.fromRef(data), type_) if data is not None else None

	def optBool(self, obj: JObject, key: str):
		return self.optType(obj, key, JsonBool)

	def optNumber(self, obj: JObject, key: str):
		return self.optType(obj, key, JsonNumber)

	def optStr(self, obj: JObject, key: str):
		return self.optType(obj, key, JsonString)

	def optArray(self, obj: JObject, key: str):
		return self.optType(obj, key, JsonArray)

	def optObject(self, obj: JObject, key: str):
		return self.optType(obj, key, JsonObject)

	def optObjectRaw(self, obj: JObject, key: str):
		if (prop := obj.n.data.get(key)) is not None:
			return self.checkType(JD(prop.value, obj.ctx), JsonObject)
		return None

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
		ctx = array.ctx
		return [self.checkType(self.fromRef2(elem, ctx), type_) for elem in array.n.data]

	def optBoolVal(self, obj: JObject, key: str, default: _TD = None) -> bool | _TD:
		if (data := self.optType(obj, key, JsonBool)) is not None:
			return data.n.data
		return default

	def optNumberVal(self, obj: JObject, key: str, default: _TD = None) -> int | float | _TD:
		if (data := self.optType(obj, key, JsonNumber)) is not None:
			return data.n.data
		return default

	def optStrVal(self, obj: JObject, key: str, default: _TD = None) -> str | _TD:
		if (data := self.optType(obj, key, JsonString)) is not None:
			return data.n.data
		return default

	def optEnumVal(self, obj: JObject, key: str, options: AbstractSet[str], default: _TD = None) -> str | _TD:
		data = self.optStr(obj, key)
		if data is not None:
			return self.checkOptions(data, options).n.data
		return default

	def optArrayVal(self, obj: JObject, key: str) -> Optional[V[list[JsonData]]]:
		array = self.optType(obj, key, JsonArray)
		if array is not None:
			return V(array.n.data, array.ctx)
		return None

	def optArrayVal2(self, obj: JObject, key: str, type_: Type[_TJSD]) -> list[JD[_TJSD]]:
		array = self.optType(obj, key, JsonArray)
		if array is not None:
			ctx = array.ctx
			return [self.checkType(self.fromRef2(elem, ctx), type_) for elem in array.n.data]
		return []


def completePartialParse(partialNode: Generator):
	try:
		next(partialNode)
	except StopIteration:
		pass
	else:
		raise RuntimeError("generator didn't stop")


def _nopParserPartial(val: _TT, yieldCount: int) -> Generator[_TT]:
	for _ in range(yieldCount):
		yield val
	return


class Finisher(NamedTuple):
	finish: Callable[[], None]

	def _doWrapped(self, errors: list[GeneralError]) -> None:
		try:
			self.finish()
		except Exception as ex:
			errors.append(WrappedError(ex))


Finisher.NOP = Finisher(lambda: None)


class Doer1(NamedTuple):
	do: Callable[[], Finisher]

	def _doWrapped(self, errors: list[GeneralError]) -> Finisher:
		try:
			finisher = self.do()
			return Finisher(lambda: finisher._doWrapped(errors))
		except Exception as ex:
			errors.append(WrappedError(ex))
			return Finisher.NOP

	def wrapExc(self, errors: list[GeneralError]) -> Doer1:
		return Doer1(lambda: self._doWrapped(errors))



Doer1.NOP = Doer1(lambda: Finisher.NOP)


class Doer2(NamedTuple):
	do: Callable[[], Doer1]

	def _doWrapped(self, errors: list[GeneralError]) -> Doer1:
		try:
			doer1 = self.do()
			return Doer1(lambda: doer1._doWrapped(errors))
		except Exception as ex:
			errors.append(WrappedError(ex))
			return Doer1.NOP

	def wrapExc(self, errors: list[GeneralError]) -> Doer2:
		return Doer2(lambda: self._doWrapped(errors))


Doer2.NOP = Doer2(lambda: Doer1.NOP)


@dataclass
class SchemaBuilderOrchestrator:
	baseDir: str
	schemas: dict[str, JsonSchema] = field(default_factory=dict, init=False)
	libraries: dict[str, SchemaLibrary] = field(default_factory=dict, init=False)
	errors: dict[str, list[GeneralError]] = field(default_factory=lambda: defaultdict(list), init=False)

	def _getSchemaLibraryPartial(self, path: str) -> tuple[SchemaLibrary, Doer2]:
		fullPath = self.getFullPath(path)
		if (library := self.libraries.get(fullPath)) is not None:
			partial = Doer2.NOP
		else:
			library, partial = self._loadLibraryPartial(fullPath)
			self.libraries[fullPath] = library
		return library, partial

	def getSchemaLibrary(self, path: str) -> SchemaLibrary:
		library, partial = self._getSchemaLibraryPartial(path)
		partial.do().do().finish()
		return library

	def getSchema(self, path: str) -> Optional[JsonSchema]:
		fullPath = self.getFullPath(path)
		if (schema := self.schemas.get(fullPath)) is not None:
			return schema
		schema = self.schemas[fullPath] = self._loadJsonSchema(fullPath)
		return schema

	def getFullPath(self, path: str) -> str:
		fullPath = os.path.join(self.baseDir, path)
		fullPath = os.path.abspath(fullPath)
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
		schemaJson, errors, _ = parse(schemaBytes, filePath=fullPath, language=JSON_ID, schema=None)
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

	def _loadLibraryPartial(self, fullPath: str) -> tuple[SchemaLibrary, Doer2]:
		"""" !!! 3-step generator !!! """
		try:
			with ZipFilePool() as pool:
				schemaBytes = loadBinaryFile(fromDisplayPath(fullPath), pool)
		except OSError as ex:
			self.errors[fullPath].append(WrappedError(ex))
			library, partial = None, Doer2.NOP
		else:
			schemaJson, errors, _ = parse(schemaBytes, filePath=fullPath, language=JSON_ID, schema=None)
			self.errors[fullPath].extend(errors)

			builder = SchemaBuilder(orchestrator=self, errors=self.errors[fullPath])

			# finish parsing and collect exception, no matter where it happens
			try:
				library, partial = builder.parseSchemaLibraryPartial(schemaJson, fullPath)
			except Exception as ex:
				self.errors[fullPath].append(WrappedError(ex))
				library, partial = None, Doer2.NOP

		if library is None:
			library = SchemaLibrary(MDStr(''), {}, {}, {}, fullPath)

		return library, partial.wrapExc(self.errors[fullPath])


def decodeDecidingProp(decidingProp: Optional[str]) -> Optional[DecidingPropRef]:
	if decidingProp is None:
		return None
	lookback = 0
	while decidingProp.startswith('../', lookback * 3):
		lookback += 1
	return DecidingPropRef(lookback, decidingProp[lookback * 3:])


def propertyHandler(self: SchemaBuilder, name: str, node: JObject) -> tuple[PropertySchema, Finisher]:
	type_ = self.optStrVal(node, '$type') or self.optStrVal(node, DEF_REF_PROP)
	if type_ is not None:
		valueNode = node
		description = None
		optional = False
		default = None
		decidingProp = None
		requires = ()
		hates = ()
		deprecated = False
		allowMultilineStr = None
		valuesNode = None
		prefixes, prefixesSpan = [], None
	else:
		description, deprecated, allowMultilineStr = readCommonValues(self, node)
		optional = self.optBoolVal(node, 'optional', False)
		default = self._optProp(node, 'default')
		if default is not None:
			default = toPyValue(self, default)
		else:
			default = None
		decidingProp = self.optStrVal(node, 'decidingProp', None)
		# reqVal = self.optArrayVal(node, 'requires', [])
		# requires = tuple(self.checkType(fromRef(data), JsonString).n.data for data in reqVal)
		requires = tuple(elem.n.data for elem in self.optArrayVal2(node, 'requires', JsonString))
		hates = tuple(elem.n.data for elem in self.optArrayVal2(node, 'hates', JsonString))

		valueNode = self.optObject(node, 'value')
		valuesNode = self.optObject(node, 'values')
		prefixes, prefixesSpan = _readOptionalPrefixes(self, node)

	if valueNode is not None:
		value, finisher = self.parseType(valueNode)
		values = None
		if prefixesSpan is not None:  # we have prefixes!
			self.error(MDStr(f"'optionalPrefixes' only work with property 'values' and 'decidingProp'. it will be ignored"), span=prefixesSpan, ctx=node.ctx, style='warning')

	elif valuesNode is not None:
		value = None
		if decidingProp is None:
			self.error(MDStr(f"Missing property 'decidingProp' required by property 'values'"), span=node.span, ctx=node.ctx)
		values2 = {
			key: self.parseType(self.reqObject(valuesNode, key))
			for key in valuesNode.n.data.keys()
		}
		values = {
			f'{prefix}{key}': type_[0]
			for key, type_ in values2.items()
			for prefix in prefixes
		}

		def _doFinish():
			for type_, finisher in values2.values():
				finisher.finish()
		finisher = Finisher(_doFinish)
	else:
		self.error(MDStr(f"Missing required property: oneOf('value', 'values')"), span=node.span, ctx=node.ctx)
		raise ValueError()  # we should NEVER be here. But the type checker does not believe, that self.error(...) always raises an exception.

	return PropertySchema(
		name=name,
		description=description,
		value=value,
		optional=optional,
		default=default,  # todo
		decidingProp=decodeDecidingProp(decidingProp),
		values=values,
		requires=requires,
		hates=hates,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	), finisher


def inheritanceHandler(self: SchemaBuilder, node: JObject) -> Inheritance:
	refNode = self.reqStr(node, 'defRef')
	decidingProp = self.optStrVal(node, 'decidingProp', None)

	prefixes, prefixesSpan = _readOptionalPrefixes(self, node)

	if decidingProp:
		decidingValuesNodes = self.reqArrayVal2(node, 'decidingValues', JsonString)
		decidingValues = tuple(
			f'{prefix}{dv.data}'
			for dv in decidingValuesNodes
			for prefix in prefixes
		)

	else:
		decidingValues = ()
		if prefixesSpan is not None:
			self.error(MDStr(f"'optionalPrefixes' only work with property 'decidingValues' and 'decidingProp'. it will be ignored"), span=prefixesSpan, ctx=node.ctx, style='warning')

	refSchema = self.resolveDefRef(refNode)
	if not isinstance(refSchema, JsonObjectSchema):
		self.error(MDStr(f"Definition \"{refNode.data}\" is not an object schema."), span=refNode.span, ctx=refNode.ctx)
	return Inheritance(
		schema=refSchema,
		decidingProp=decodeDecidingProp(decidingProp),
		decidingValues=decidingValues,
	)


_typeHandlers: dict[str, Callable[[SchemaBuilder, JObject], Generator[JsonSchema]]] = {}
typeHandler = AddToDictDecorator(_typeHandlers)


@typeHandler('object')
def objectHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	defaultProp = self.optType(node, 'default-property', JsonObject)
	if defaultProp is not None:
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

	finishers = []
	schemaProps = []
	if properties is not None:
		for name in properties.n.data.keys():
			propObj = self.reqType(properties, name, JsonObject)
			prop, finisher = propertyHandler(self, name, propObj)
			schemaProps.append(prop.setSpan(properties.n.data[name].value.span, properties.ctx.filePath))
			finishers.append(finisher)
	if defaultProp is not None:
		# 'default-property' might be a reference, so get the span from the raw (non-resolved ) value!
		prop, finisher = propertyHandler(self, Anything(), defaultProp)
		schemaProps.append(prop.setSpan(node.n.data['default-property'].value.span, node.ctx.filePath))
		finishers.append(finisher)

	schemaInherits = []
	for inherit in inherits:
		schemaInherits.append(inheritanceHandler(self, inherit))

	objectSchema.properties = tuple(schemaProps)
	objectSchema.inherits = tuple(schemaInherits)
	yield objectSchema
	objectSchema.finish()
	for finisher in finishers:
		finisher.finish()


@typeHandler('array')
def arrayHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	element = self.reqObject(node, 'element')
	objectSchema = JsonArraySchema(
		description=description,
		element=cast(JsonSchema, None),  # will be set later.
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	objectSchema.element, finisher = self.parseType(element)
	yield objectSchema
	finisher.finish()


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
	finishers = []
	for option in options:
		option4, finisher = self.parseType(option)
		schemaOptions.append(option4)
		finishers.append(finisher)
	objectSchema.options = tuple(schemaOptions)

	yield objectSchema
	for finisher in finishers:
		finisher.finish()

@typeHandler('any')
def anyHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	objectSchema = JsonAnySchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('string')
def stringHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	from .jsonContext import getJsonStringContext
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	type_ = self.optStr(node, 'type')
	args = self.optObject(node, 'args')

	jsonArgType = ALL_NAMED_JSON_ARG_TYPES.get(type_.data) if type_ is not None else None
	if jsonArgType is None and type_ is not None:
		self.error(MDStr(f"Unknown JsonArgType '{type_.data}'"), span=type_.span, ctx=type_.ctx, style='warning')
	pyArgs = toPyValue(self, args) if args is not None else None

	# validate args:
	if jsonArgType is not None:
		if (ctx := getJsonStringContext(jsonArgType.name)) is not None:
			ctx.validateSchemaArgs(self, jsonArgType, args, node)

	objectSchema = JsonStringSchema(
		description=description,
		type=jsonArgType,
		args=pyArgs,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('enum')
def enumHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	options = self.reqObject(node, 'options')
	warningOnly = self.optBoolVal(node, 'warningOnly', False)
	oCtx = options.ctx
	options2: dict[str, MDStr] = {self.checkType(self.fromRef2(p.key, oCtx), JsonString).data: self.checkType(self.fromRef2(p.value, oCtx), JsonString).data for p in options.data.values()}

	prefixes, prefixesSpan = _readOptionalPrefixes(self, node)
	options2 = {
		f'{prefix}{key}': descr
		for key, descr in options2.items()
		for prefix in prefixes
	}

	objectSchema = JsonStringOptionsSchema(
		description=description,
		options=options2,
		deprecated=deprecated,
		warningOnly=warningOnly,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
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
	yield objectSchema


@typeHandler('calculated')
def calculatedHandler(self: SchemaBuilder, node: JObject) -> Generator[JsonSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self, node)
	func = self.reqStrVal(node, 'function')
	try:
		func = lookupFunction(func)
	except Exception as ex:
		self.errors.append(WrappedError(ex, span=node.n.data.get('function').value.span))
		func = lambda x: None

	objectSchema = JsonCalculatedValueSchema(
		description=description,
		func=func,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


def lookupFunction(qName: str) -> Callable:
	splitQName = qName.rpartition('.')[::2]
	mod = sys.modules.get(splitQName[0])
	f = mod
	for part in splitQName[1:]:
		f = getattr(f, part)
	assert callable(f), f"{qName} is not a callable type({qName}): {type(qName)}"
	return f


def readCommonValues(self: SchemaBuilder, node: JObject) -> tuple[MDStr, bool, bool]:
	description = MDStr(self.optStrVal(node, 'description', ''))
	deprecated = self.optBoolVal(node, 'deprecated', False)
	allowMultilineStr = self.optBoolVal(node, 'allowMultilineStr')
	return description, deprecated, allowMultilineStr


_toPyValueHandlers: dict[str, Callable[[SchemaBuilder, JD], Any]] = {}
_toPyValueHandler = AddToDictDecorator(_toPyValueHandlers)


def toPyValue(self: SchemaBuilder, data: JD) -> Any:
	return _toPyValueHandlers[data.typeName](self, data)


@_toPyValueHandler('object')
def _objectHandler(self: SchemaBuilder, node: JObject) -> dict:
	return {toPyValue(self, self.fromRef2(p.key, node.ctx)): toPyValue(self, self.fromRef2(p.value, node.ctx)) for p in node.data.values()}


@_toPyValueHandler('array')
def _arrayHandler(self: SchemaBuilder, node: JArray) -> list:
	return [toPyValue(self, self.fromRef2(e, node.ctx)) for e in node.data]


@_toPyValueHandler('string')
@_toPyValueHandler('boolean')
@_toPyValueHandler('number')
@_toPyValueHandler('null')
def _stringHandler(self: SchemaBuilder, node: JString) -> str:
	return node.data


def _readOptionalPrefixes(self: SchemaBuilder, node: JObject) -> tuple[list[str], Span]:
	prefixesNode = self.optArray(node, OPTIONAL_PREFIXES_PROP)
	prefixes = self.optArrayVal2(node, OPTIONAL_PREFIXES_PROP, JsonString) if prefixesNode is not None else []
	return [''] + [prefix.data for prefix in prefixes], (prefixesNode and prefixesNode.span)


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


def traverseSchema(obj: JsonSchema, onHasMemo: Callable[[JsonSchema], Any], *, memoIO: dict[int, JsonSchema], skipMemoCheck: bool = False) -> PyJsonObject:
	if id(obj) in memoIO and not skipMemoCheck:
		return onHasMemo(obj)
	memoIO[id(obj)] = obj

	result = OrderedDict()
	result['$type'] = obj.typeName
	for st in type(obj).__mro__:
		for attr, defaultVal in getattr(st, '_fields', {}).items():
			val = getattr(obj, attr)
			if val is Nothing or val != defaultVal:
				result[attr] = traverse(val, onHasMemo, memoIO=memoIO)
	obj.postProcessJsonStructure(result)
	return result


def traverseMapping(obj: Mapping[str, Any], onHasMemo: Callable[[JsonSchema], Any], *, memoIO: dict[int, JsonSchema], skipMemoCheck: bool = False) -> PyJsonObject:
	return {key: traverse(val, onHasMemo, memoIO=memoIO) for key, val in obj.items()}


def traverseList(obj: list | tuple, onHasMemo: Callable[[JsonSchema], Any], *, memoIO: dict[int, JsonSchema], skipMemoCheck: bool = False) -> PyJsonArray:
	return [traverse(val, onHasMemo, memoIO=memoIO) for val in obj]


def traverse(obj, onHasMemo: Callable[[JsonSchema], Any], *, memoIO: dict[int, JsonSchema]) -> PyJsonValue:
	if isinstance(obj, JsonSchema):
		result = traverseSchema(obj, onHasMemo, memoIO=memoIO, skipMemoCheck=False)  # don't skip memo checks recursively
	elif isinstance(obj, (list, tuple)):
		result = traverseList(obj, onHasMemo, memoIO=memoIO)
	elif isinstance(obj, Mapping):
		result = traverseMapping(obj, onHasMemo, memoIO=memoIO)
	else:
		result = obj
	return result


def buildJsonStructure(schema: JsonSchema):
	sharedSchemas = findDuplicates(schema)

	def onHasMemo2(obj: JsonSchema) -> dict[str, JsonSchema]:
		return {DEF_REF_PROP: sharedSchemas[id(obj)][0]}

	memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
	definitions = {}
	for id_, (ref, obj) in sharedSchemas.items():
		definitions[ref] = traverseSchema(obj, onHasMemo2, memoIO=memo2, skipMemoCheck=True)

	# memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
	body = traverseSchema(schema, onHasMemo2, memoIO=memo2)

	structure = {
		'$schema': 'dpe/json/schema',
		'$body': body,
		'$definitions': definitions,
	}
	return structure


def findDuplicates(schema: JsonSchema) -> dict[int, tuple[str, JsonSchema]]:
	usageCounts: defaultdict[int, int] = defaultdict(int)

	def onHasMemo(obj: JsonSchema):
		usageCounts[id(obj)] += 1
		return None

	memo: dict[int, JsonSchema] = {}
	traverseSchema(schema, onHasMemo, memoIO=memo)
	enumeratedUsageCounts: Iterator[tuple[int, tuple[int, int]]] = enumerate(usageCounts.items())
	sharedSchemas: dict[int, tuple[str, JsonSchema]] = {
		id_: (f'%%{i}!', memo[id_])
		for i, (id_, cnt) in enumeratedUsageCounts
	}
	return sharedSchemas

