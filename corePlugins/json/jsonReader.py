from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Collection, Optional, TypeVar, Type, Any, AbstractSet, Generic, TypeAlias, final, overload, Literal, NoReturn

from .core import *
from base.model.parsing.bytesUtils import strToBytes
from base.model.utils import GeneralError, MDStr, Span, SemanticsError


TEMPLATE_REF_PROP = '$ref'

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


_TSchemaLibrary = TypeVar('_TSchemaLibrary', bound='SchemaLibrary')

@dataclass
class SchemaLibrary:
	description: MDStr
	libraries: dict[str, SchemaLibrary]  # = field(default_factory=dict, init=False)
	templates: dict[str, SchemaTemplate]  # = field(default_factory=dict, init=False)
	additional: dict[str, Any]  # = field(default_factory=dict, init=False)
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


@dataclass
class JsonReader:
	errors: list[GeneralError] = field(default_factory=list)
	libraries: dict[str, SchemaLibrary] = field(default_factory=dict, init=False)

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

	def parseTemplates(self, templatesNode: JObject, ctx: TemplateContext) -> None:
		templates: dict[str, SchemaTemplate] = ctx.libraries[''].templates
		for ref, prop in templatesNode.data.items():
			if ref in templates:
				self.error(MDStr(f"template {ref!r} already defined before at {templates[ref].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			templateNode = self.reqObject(templatesNode, ref)
			templates[ref] = self.parseTemplate(templateNode, prop.key.span)

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
