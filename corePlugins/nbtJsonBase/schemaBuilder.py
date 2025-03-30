from __future__ import annotations

import math
import os.path
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import NamedTuple, Optional, TypeVar, Type, Callable, Generator, cast

from base.model.parsing.parser import parse
from base.model.pathUtils import normalizeDirSeparators, fromDisplayPath, loadBinaryFile, ZipFilePool
from base.model.utils import GeneralError, MDStr, Span, WrappedError, LanguageId, NULL_SPAN, ParsingError
from cat.utils import Anything
from cat.utils.collections_ import AddToDictDecorator
from .core import *
from .structureReader import StructureReader, TemplateContext, SchemaLibrary, JObject, JD, JString

DEF_REF_PROP = '$defRef'
OPTIONAL_PREFIXES_PROP = 'optionalPrefixes'

_TT = TypeVar('_TT')


@dataclass
class SchemaBuilder:
	orchestrator: SchemaBuilderOrchestrator
	reader: StructureReader = field(default_factory=StructureReader)
	objectSchemasToBeFinished: list[ObjectSchema] = field(default_factory=list, init=False)

	def parseSchema(self, root: ObjectNode, filePath: str) -> Optional[StructureDataSchema]:
		ctx = TemplateContext('', filePath, self.reader.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.reader.optStrVal(root2, '$schema') != 'dpe/json/schema':
			self.reader.error(MDStr("Not a JSON Schema"), span=root.span, ctx=ctx)
			return None

		title = self.reader.optStrVal(root2, 'title', '')
		library, partial = self._parseLibraryPartial(root2, filePath, ctx)
		partial.do().do().finish()

		body = self.reader.reqObject(root2, '$body')
		schema = self.parseBody(body)
		return schema

	def parseSchemaLibraryPartial(self, root: ObjectNode, filePath: str) -> tuple[Optional[SchemaLibrary], Doer2]:
		"""" !!! 3-step generator !!! """
		ctx = TemplateContext('', filePath, self.reader.libraries, {})
		root2: JObject = JD(root, ctx)
		if self.reader.optStrVal(root2, '$schema') != 'dpe/json/schema/library':
			self.reader.error(MDStr("Not a JSON Schema Library"), span=root.span, ctx=ctx)
			return None, Doer2.NOP
		else:
			return self._parseLibraryPartial(root2, filePath, ctx)

	def _parseLibraryPartial(self: SchemaBuilder, root: JObject, filePath: str, ctx: TemplateContext) -> tuple[SchemaLibrary, Doer2]:
		description = MDStr(self.reader.optStrVal(root, 'description', ''))

		library = ctx.libraries[''] = SchemaLibrary(
			description=description,
			libraries=cast(dict[str, SchemaLibrary], ctx.libraries),
			templates={},
			additional={},
			filePath=filePath,
			exists=True
		)

		def _parseLibraryPartial1() -> Doer1:
			"""" !!! 3-step generator !!! """

			libraries = self.reader.optObjectRaw(root, '$libraries')
			partialLibraries = self._parsePartial(libraries, self.parseLibrariesPartial, ctx)
			next(partialLibraries)

			templates = self.reader.optObjectRaw(root, '$templates')
			if templates is not None:
				self.reader.parseTemplates(templates, ctx)

			definitions = self.reader.optObjectRaw(root, '$definitions')
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

	def parseBody(self, body: JObject) -> StructureDataSchema:
		body, finisher = self.parseType(body)
		finisher.finish()
		return body

	def parseDefinitionsPartial(self, definitionsNode: JObject, ctx: TemplateContext) -> Generator[None]:
		definitions: dict[str, StructureDataSchema] = ctx.libraries[''].additional['definitions']
		partialDefinitions = []
		for ref, prop in definitionsNode.data.items():
			if ref in definitions:
				self.reader.error(MDStr(f"definition {ref!r} already defined before at {definitionsNode.data[ref].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			definition = self.reader.reqObject(definitionsNode, ref)
			partialDefinition = self.handleTypePartial(definition)
			partialDefinitions.append(partialDefinition)
			definitions[ref] = next(partialDefinition)

		yield None
		for partialDefinition in partialDefinitions:
			next(partialDefinition)

		yield None
		for partialDefinition in partialDefinitions:
			completePartialParse(partialDefinition)

	def parseLibrariesPartial(self, librariesNode: JObject, ctx: TemplateContext) -> Generator[None]:
		"""" !!! 3-step generator !!! """
		partialLibraries2: list[Doer2] = []
		libraries: dict[str, SchemaLibrary] = cast(SchemaLibrary, ctx.libraries['']).libraries
		for ns, prop in librariesNode.data.items():
			if ns in libraries:
				self.reader.error(MDStr(f"namespace {ns!r} already defined before at {librariesNode.data[ns].span.start}"), span=prop.key.span, ctx=ctx)
				continue
			if not ns:
				self.reader.error(MDStr(f"namespace cannot be an empty string"), span=prop.key.span, ctx=ctx)
				continue
			libraryFilePath = self.reader.reqStrVal(librariesNode, ns)
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

	def handleTypePartial(self, node: JObject) -> Generator[StructureDataSchema]:
		refNode = self.reader.optStr(node, DEF_REF_PROP)
		if refNode is not None:
			if len(node.data) > 1:
				self.reader.error(MDStr(f"no additional attributes allowed for referenced definitions."), span=refNode.span, style='warning', ctx=node.ctx)
			yield self.resolveDefRef(refNode)
			yield None
		else:
			type_ = self.reader.reqStr(node, '$type')
			try:
				th = _typeHandlers[type_.n.data]
			except KeyError as e:
				self.reader.error(MDStr(f"Unknown $type '{type_.n.data}'."), span=type_.n.span, ctx=type_.ctx)
				raise
			else:
				partialDefinition = th(self, node)
				definition = next(partialDefinition).setSpan(node.n.span, node.ctx.filePath)
				yield definition
				definition = next(partialDefinition)
				yield definition
				completePartialParse(partialDefinition)

	def parseType(self, node: JObject) -> tuple[StructureDataSchema, Finisher]:
		partialNode = self.handleTypePartial(node)
		schema = next(partialNode)
		next(partialNode)
		return schema, Finisher(lambda: completePartialParse(partialNode))

	def resolveDefRef(self, refNode: JString) -> StructureDataSchema:
		library, ns, lref = self.reader.getNamespace(refNode)
		if (definition := library.additional['definitions'].get(lref)) is not None:
			return definition
		else:
			self.reader.error(MDStr(f"No definition \"{lref}\" in namespace \"{ns}\"."), span=refNode.span, ctx=refNode.ctx)
			return AnySchema(allowMultilineStr=None)


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

SUPPORTED_LANGUAGE_IDS_BY_EXTENSION = {
	'.json': LanguageId('JSON'),
	'.snbt': LanguageId('SNBT'),
}


@dataclass
class SchemaBuilderOrchestrator:
	baseDir: str
	schemas: dict[str, StructureDataSchema] = field(default_factory=dict, init=False)
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

	def getSchema(self, path: str) -> Optional[StructureDataSchema]:
		fullPath = self.getFullPath(path)
		if (schema := self.schemas.get(fullPath)) is not None:
			return schema
		schema = self.schemas[fullPath] = self._loadSchema(fullPath)
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

	def _loadAndParseFile(self, fullPath: str) -> Optional[ObjectNode]:
		try:
			with ZipFilePool() as pool:
				schemaBytes = loadBinaryFile(fromDisplayPath(fullPath), pool)
		except OSError as ex:
			self.errors[fullPath].append(WrappedError(ex))
			return None

		_, _, ext = fullPath.rpartition('.')
		langaugeId = SUPPORTED_LANGUAGE_IDS_BY_EXTENSION.get('.' + ext.lower())
		if langaugeId is None:
			self.errors[fullPath].append(ParsingError(MDStr(f"Schema files with extension '{ext}' are not supported."), span=NULL_SPAN))

		schemaStructure, errors, _ = parse(schemaBytes, filePath=fullPath, language=langaugeId, schema=None)
		schemaStructure: ObjectNode
		self.errors[fullPath].extend(errors)
		return schemaStructure

	def _loadSchema(self, fullPath: str) -> Optional[StructureDataSchema]:
		schemaStructure = self._loadAndParseFile(fullPath)
		if schemaStructure is None:
			return None

		builder = SchemaBuilder(orchestrator=self)
		try:
			schema = builder.parseSchema(schemaStructure, fullPath)
		except Exception as ex:
			self.errors[fullPath].extend(builder.reader.errors)
			self.errors[fullPath].append(WrappedError(ex))
			return None
		self.errors[fullPath].extend(builder.reader.errors)
		return schema

	def _loadLibraryPartial(self, fullPath: str) -> tuple[SchemaLibrary, Doer2]:
		"""" !!! 3-step generator !!! """
		schemaStructure = self._loadAndParseFile(fullPath)
		if schemaStructure is None:
			library, partial = None, Doer2.NOP
		else:
			builder = SchemaBuilder(orchestrator=self, reader=StructureReader(errors=self.errors[fullPath]))

			# finish parsing and collect exception, no matter where it happens
			try:
				library, partial = builder.parseSchemaLibraryPartial(schemaStructure, fullPath)
			except Exception as ex:
				self.errors[fullPath].append(WrappedError(ex))
				library, partial = None, Doer2.NOP

		if library is None:
			library = SchemaLibrary(MDStr(''), {}, {}, {}, fullPath, exists=False)

		return library, partial.wrapExc(self.errors[fullPath])


def decodeDecidingProp(decidingProp: Optional[str]) -> Optional[DecidingPropRef]:
	if decidingProp is None:
		return None
	lookback = 0
	while decidingProp.startswith('../', lookback * 3):
		lookback += 1
	return DecidingPropRef(lookback, decidingProp[lookback * 3:])


def propertyHandler(self: SchemaBuilder, name: str | Anything, node: JObject) -> tuple[PropertySchema, Finisher]:
	reader = self.reader
	type_ = reader.optStrVal(node, '$type') or reader.optStrVal(node, DEF_REF_PROP)
	if type_ is not None:
		valueNode = node
		description = None
		optional = False
		default = None
		decidingProp = None
		requires = ()
		hates = ()
		exclusionGroups = ()
		deprecated = False
		allowMultilineStr = None
		valuesNode = None
		prefixes, prefixesSpan = [], None
	else:
		description, deprecated, allowMultilineStr = readCommonValues(reader, node)
		optional = reader.optBoolVal(node, 'optional', False)
		default = reader._optProp(node, 'default')
		if default is not None:
			default = toPyValue(default, lambda e, parent: reader.fromRef2(e, parent.ctx))
		else:
			default = None
		decidingProp = reader.optStrVal(node, 'decidingProp', None)
		# reqVal = reader.optListLikeVal(node, 'requires', [])
		# requires = tuple(reader.checkType(fromRef(data), StringNode).n.data for data in reqVal)
		requires = tuple(elem.n.data for elem in reader.optListLikeVal2(node, 'requires', StringNode))
		hates = tuple(elem.n.data for elem in reader.optListLikeVal2(node, 'hates', StringNode))
		exclusionGroups = tuple(elem.n.data for elem in reader.optListLikeVal2(node, 'exclusionGroups', StringNode))

		valueNode = reader.optObject(node, 'value')
		valuesNode = reader.optObject(node, 'values')
		prefixes, prefixesSpan = readOptionalPrefixes(reader, node)

	if valueNode is not None:
		value, finisher = self.parseType(valueNode)
		values = None
		if prefixesSpan is not None:  # we have prefixes!
			reader.error(MDStr(f"'optionalPrefixes' only work with property 'values' and 'decidingProp'. it will be ignored"), span=prefixesSpan, ctx=node.ctx, style='warning')

	elif valuesNode is not None:
		value = None
		if decidingProp is None:
			reader.error(MDStr(f"Missing property 'decidingProp' required by property 'values'"), span=node.span, ctx=node.ctx)
		values2 = {
			key: self.parseType(reader.reqObject(valuesNode, key))
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
		reader.error(MDStr(f"Missing required property: oneOf('value', 'values')"), span=node.span, ctx=node.ctx)
		raise ValueError()  # we should NEVER be here. But the type checker does not believe, that reader.error(...) always raises an exception.

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
		exclusionGroups=exclusionGroups,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	), finisher


def inheritanceHandler(self: SchemaBuilder, node: JObject) -> Inheritance:
	reader = self.reader
	refNode = reader.reqStr(node, 'defRef')
	decidingProp = reader.optStrVal(node, 'decidingProp', None)

	prefixes, prefixesSpan = readOptionalPrefixes(reader, node)

	if decidingProp:
		decidingValuesNodes = reader.reqListLikeVal2(node, 'decidingValues', StringNode)
		decidingValues = tuple(
			f'{prefix}{dv.data}'
			for dv in decidingValuesNodes
			for prefix in prefixes
		)

	else:
		decidingValues = ()
		if prefixesSpan is not None:
			reader.error(MDStr(f"'optionalPrefixes' only work with property 'decidingValues' and 'decidingProp'. it will be ignored"), span=prefixesSpan, ctx=node.ctx, style='warning')

	refSchema = self.resolveDefRef(refNode)
	if not isinstance(refSchema, ObjectSchema):
		reader.error(MDStr(f"Definition \"{refNode.data}\" is not an object schema."), span=refNode.span, ctx=refNode.ctx)
	return Inheritance(
		schema=refSchema,
		decidingProp=decodeDecidingProp(decidingProp),
		decidingValues=decidingValues,
	)


_typeHandlers: dict[str, Callable[[SchemaBuilder, JObject], Generator[StructureDataSchema]]] = {}
typeHandler = AddToDictDecorator(_typeHandlers)


@typeHandler('object')
def objectHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	reader = self.reader
	description, deprecated, allowMultilineStr = readCommonValues(reader, node)
	defaultProp = reader.optObject(node, 'default-property')
	defaultKey = reader.optObject(node, 'default-key')

	if defaultProp is not None:
		properties = reader.optObjectRaw(node, 'properties')
	else:
		properties = reader.reqObjectRaw(node, 'properties')

	inherits = reader.optListLikeVal2(node, 'inherits', ObjectNode)

	definingProps = reader.optListLikeVal2(node, 'defining-properties', StringNode)
	if definingProps is not None:
		definingProps = frozenset({definingProp.data for definingProp in definingProps})
	else:
		definingProps = frozenset()

	objectSchema = ObjectSchema(
		description=description,
		definingProps=definingProps,
		properties=[],
		inherits=[],
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema

	finishers = []
	schemaProps = []
	anythingKey = None
	if properties is not None:
		for name in properties.n.data.keys():
			propObj = reader.reqType(properties, name, ObjectNode)
			prop, finisher = propertyHandler(self, name, propObj)
			schemaProps.append(prop.setSpan(properties.n.data[name].value.span, properties.ctx.filePath))
			finishers.append(finisher)
	if defaultProp is not None:
		# 'default-property' might be a reference, so get the span from the raw (non-resolved) value!
		prop, finisher = propertyHandler(self, Anything, defaultProp)
		schemaProps.append(prop.setSpan(node.n.data['default-property'].value.span, node.ctx.filePath))
		finishers.append(finisher)
	if defaultKey is not None:
		anythingKey, finisher = self.parseType(defaultKey)
		finishers.append(finisher)
		if not isinstance(anythingKey, StringSchema):
			# 'default-key' might be a reference, so get the span from the raw (non-resolved) value!
			span = node.n.data['default-key'].value.span
			reader.error(MDStr(f"Definition  is not an string schema."), span=span, ctx=node.ctx)
			anythingKey = None

	schemaInherits = []
	for inherit in inherits:
		schemaInherits.append(inheritanceHandler(self, inherit))

	objectSchema.properties = tuple(schemaProps)
	objectSchema.inherits = tuple(schemaInherits)
	objectSchema.anythingKey = anythingKey
	yield objectSchema
	objectSchema.finish()
	for finisher in finishers:
		finisher.finish()


@typeHandler('array')
def arrayHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	element = self.reader.reqObject(node, 'element')
	minElemCount = self.reader.optNumberVal(node, 'minCount', None)
	maxElemCount = self.reader.optNumberVal(node, 'maxCount', None)
	objectSchema = ListLikeSchema(
		description=description,
		element=cast(StructureDataSchema, None),  # will be set later.
		minElemCount=minElemCount,
		maxElemCount=maxElemCount,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	objectSchema.element, finisher = self.parseType(element)
	yield objectSchema
	finisher.finish()


@typeHandler('union')
def unionHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	options = self.reader.reqListLikeVal2(node, 'options', ObjectNode)
	objectSchema = UnionSchema(
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
def anyHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	objectSchema = AnySchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('string')
def stringHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	from .context import getStringNodeContext
	reader = self.reader
	description, deprecated, allowMultilineStr = readCommonValues(reader, node)
	type_ = reader.optStr(node, 'type')
	args = reader.optObject(node, 'args')

	argType = ALL_NAMED_STRUCTURE_ARG_TYPES.get(type_.data) if type_ is not None else None
	if argType is None and type_ is not None:
		reader.error(MDStr(f"Unknown StructureArgType '{type_.data}'"), span=type_.span, ctx=type_.ctx, style='warning')
	pyArgs = toPyValue(args, lambda e, parent: reader.fromRef2(e, parent.ctx)) if args is not None else None

	# validate args:
	if argType is not None:
		if (ctx := getStringNodeContext(argType.name)) is not None:
			ctx.validateSchemaArgs(self, argType, args, node)

	objectSchema = StringSchema(
		description=description,
		type=type_.data if type_ is not None else None,
		args=pyArgs,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('enum')
def enumHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	reader = self.reader
	description, deprecated, allowMultilineStr = readCommonValues(reader, node)
	options = reader.reqObject(node, 'options')
	warningOnly = reader.optBoolVal(node, 'warningOnly', False)
	oCtx = options.ctx
	options2: dict[str, MDStr] = {reader.checkType(reader.fromRef2(p.key, oCtx), StringNode).data: reader.checkType(reader.fromRef2(p.value, oCtx), StringNode).data for p in options.data.values()}

	prefixes, prefixesSpan = readOptionalPrefixes(reader, node)
	options2 = {
		f'{prefix}{key}': descr
		for key, descr in options2.items()
		for prefix in prefixes
	}

	objectSchema = StringOptionsSchema(
		description=description,
		options=options2,
		deprecated=deprecated,
		warningOnly=warningOnly,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('boolean')
def boolHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	objectSchema = BooleanSchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


def _numberHandler(self: SchemaBuilder, node: JObject, cls: Type[NumberSchema]) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	minVal = self.reader.optNumberVal(node, 'min', -math.inf)
	maxVal = self.reader.optNumberVal(node, 'max', math.inf)
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
def integerHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	return _numberHandler(self, node, IntSchema)


@typeHandler('float')
def floatHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	return _numberHandler(self, node, FloatSchema)


@typeHandler('null')
def nullHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	objectSchema = NullSchema(
		description=description,
		deprecated=deprecated,
		allowMultilineStr=allowMultilineStr
	)
	yield objectSchema
	yield objectSchema


@typeHandler('calculated')
def calculatedHandler(self: SchemaBuilder, node: JObject) -> Generator[StructureDataSchema]:
	description, deprecated, allowMultilineStr = readCommonValues(self.reader, node)
	func = self.reader.reqStrVal(node, 'function')
	try:
		func = lookupFunction(func)
	except Exception as ex:
		self.reader.errors.append(WrappedError(ex, span=node.n.data.get('function').value.span))
		func = lambda x: STRUCTURE_ILLEGAL_SCHEMA

	objectSchema = CalculatedValueSchema(
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


def readCommonValues(reader: StructureReader, node: JObject) -> tuple[MDStr, bool, bool]:
	description = MDStr(reader.optStrVal(node, 'description', ''))
	deprecated = reader.optBoolVal(node, 'deprecated', False)
	allowMultilineStr = reader.optBoolVal(node, 'allowMultilineStr')
	return description, deprecated, allowMultilineStr


def readOptionalPrefixes(reader: StructureReader, node: JObject) -> tuple[list[str], Span]:
	prefixesNode = reader.optListLike(node, OPTIONAL_PREFIXES_PROP)
	prefixes = reader.optListLikeVal2(node, OPTIONAL_PREFIXES_PROP, StringNode) if prefixesNode is not None else []
	return [''] + [prefix.data for prefix in prefixes], (prefixesNode and prefixesNode.span)


# ############################################################################################
# # might be removable:
# ############################################################################################
#
# # class ComplexEncoder(json.JSONEncoder):
# # 	def default(self, obj):
# # 		# if isinstance(obj, StructureDataSchema):
# # 		# 	raise ValueError('ComplexEncoder StructureDataSchema')
# # 		# 	dict_ = OrderedDict((attr, getattr(obj, attr)) for st in type(obj).__mro__ for attr in getattr(st, '_fields', ()))
# # 		# 	dict_['$type'] = obj.typeName
# # 		# 	dict_.move_to_end('$type', False)
# # 		# 	return dict_
# # 		from model.datapack.datapackContents import ResourceLocationSchema
# # 		if isinstance(obj, (JsonArgType, ResourceLocationSchema, ArgumentType)):
# # 			return obj.name
# # 		# Let the base class default method raise the TypeError
# # 		return json.JSONEncoder.default(self, obj)
# #
# #
# # def emitSchema(schema: StructureDataSchema) -> str:
# # 	structure = buildJsonStructure(schema)
# # 	text = emitter.emitJson(structure, cls=ComplexEncoder, indent=2)
# # 	return text
#
#
# def traverse(obj, onHasMemo: Callable[[StructureDataSchema], Any], *, memoIO: dict[int, StructureDataSchema]) -> PyStructureValue:
# 	if isinstance(obj, StructureDataSchema):
# 		result = traverseSchema(obj, onHasMemo=onHasMemo, memoIO=memoIO, skipMemoCheck=False)  # don't skip memo checks recursively
# 	elif isinstance(obj, (list, tuple)):
# 		result = traverseList(obj, onHasMemo, memoIO=memoIO)
# 	elif isinstance(obj, Mapping):
# 		result = traverseMapping(obj, onHasMemo, memoIO=memoIO)
# 	else:
# 		result = obj
# 	return result
#
#
# def traverseSchema(obj: StructureDataSchema, *, onHasMemo: Callable[[StructureDataSchema], Any], memoIO: dict[int, StructureDataSchema], skipMemoCheck: bool = False) -> PyStructureObject:
# 	if id(obj) in memoIO and not skipMemoCheck:
# 		return onHasMemo(obj)
# 	memoIO[id(obj)] = obj
#
# 	result = {
# 		(attr if name is ... else name): traverse(val, onHasMemo, memoIO=memoIO)
# 		for st in type(obj).__mro__
# 		for attr, (name, defaultVal) in getattr(st, '_fields', FrozenDict.EMPTY).items()
# 		if (val := getattr(obj, attr)) is Nothing or val != defaultVal
# 	}
# 	obj.postProcessJsonStructure(result)
# 	return result
#
#
# def traverseMapping(obj: Mapping[str, Any], onHasMemo: Callable[[StructureDataSchema], Any], *, memoIO: dict[int, StructureDataSchema], skipMemoCheck: bool = False) -> PyStructureObject:
# 	return {key: traverse(val, onHasMemo, memoIO=memoIO) for key, val in obj.items()}
#
#
# def traverseList(obj: list | tuple, onHasMemo: Callable[[StructureDataSchema], Any], *, memoIO: dict[int, StructureDataSchema], skipMemoCheck: bool = False) -> PyStructureList:
# 	return [traverse(val, onHasMemo, memoIO=memoIO) for val in obj]
#
#
# def buildJsonStructure(schema: StructureDataSchema):
# 	sharedSchemas = findDuplicates(schema)
#
# 	def onHasMemo2(obj: StructureDataSchema) -> dict[str, StructureDataSchema]:
# 		return {DEF_REF_PROP: sharedSchemas[id(obj)][0]}
#
# 	memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
# 	definitions = {}
# 	for id_, (ref, obj) in sharedSchemas.items():
# 		definitions[ref] = traverseSchema(obj, onHasMemo=onHasMemo2, memoIO=memo2, skipMemoCheck=True)
#
# 	# memo2 = {id_: obj for id_, (ref, obj) in sharedSchemas.items()}
# 	body = traverseSchema(schema, onHasMemo=onHasMemo2, memoIO=memo2)
#
# 	structure = {
# 		'$schema': 'dpe/json/schema',
# 		'$body': body,
# 		'$definitions': definitions,
# 	}
# 	return structure
#
#
# def findDuplicates(schema: StructureDataSchema) -> dict[int, tuple[str, StructureDataSchema]]:
# 	usageCounts: defaultdict[int, int] = defaultdict(int)
#
# 	def onHasMemo(obj: StructureDataSchema):
# 		usageCounts[id(obj)] += 1
# 		return None
#
# 	memo: dict[int, StructureDataSchema] = {}
# 	traverseSchema(schema, onHasMemo=onHasMemo, memoIO=memo)
# 	enumeratedUsageCounts: Iterator[tuple[int, tuple[int, int]]] = enumerate(usageCounts.items())
# 	sharedSchemas: dict[int, tuple[str, StructureDataSchema]] = {
# 		id_: (f'%%{i}!', memo[id_])
# 		for i, (id_, cnt) in enumeratedUsageCounts
# 	}
# 	return sharedSchemas
#
