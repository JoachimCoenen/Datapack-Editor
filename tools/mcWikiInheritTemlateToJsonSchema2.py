import os
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Callable, NamedTuple, Literal

from Cat.extensions import processRecursively
from Cat.utils import openOrCreate
from Cat.utils.collections_ import AddToDictDecorator, Stack, OrderedMultiDict
from Cat.utils.logging_ import logError
from Cat.utils.typing_ import replace_tuple
from model.json import emitter
from model.json.core import *
from model.parsing.parser import IndexMapper
from model.utils import Span

INDENT = '\t'
NL = '\n'
SEP = f',{NL}'
f',{NL}'


def jNull() -> JsonNull:
	return JsonNull(Span(), None)


def jBool(value: bool) -> JsonBool:
	return JsonBool(Span(), None, value)


def jNum(value: int | float) -> JsonNumber:
	return JsonNumber(Span(), None, value)


def jStr(value: str) -> JsonString:
	return JsonString(Span(), None, value, IndexMapper())


def jArr(elements: list[JsonData]) -> JsonArray:
	return JsonArray(Span(), None, list(elements))


def makeJProp(key: str, value: JsonData) -> JsonProperty:
	return JsonProperty(Span(), None, jStr(key), value)


def jObj(props: OrderedDict[str, JsonData]) -> JsonObject:
	properties = OrderedMultiDict((key, makeJProp(key, value)) for key, value in props.items())
	return JsonObject(Span(), None, properties)


SchemaTypeType = Literal['object', 'array', 'union', 'any', 'string', 'enum', 'boolean', 'integer', 'float', 'null', 'calculated']


def buildSchema(type_: SchemaTypeType, doc: Optional[str], **props: JsonData) -> JsonObject:
	if doc:
		return jObj(OrderedDict(
			[('$type', jStr(type_))],
			description=jStr(doc),
			**props
		))
	else:
		return jObj(OrderedDict(
			[('$type', jStr(type_))],
			**props
		))


def buildDoc(doc: Optional[str], **props: JsonData) -> JsonObject:
	if doc:
		return jObj(OrderedDict(
			description=jStr(doc),
			**props
		))
	else:
		return jObj(OrderedDict(props))


def extractOnlyinclude(text: str) -> str:
	text = re.sub(
		r'<div class="treeview">\s*<onlyinclude>\s*',
		'',
		text,
		flags=re.MULTILINE
	)
	text = re.sub(
		r'\s*</onlyinclude>(.|\n)*',
		'',
		text,
		flags=re.MULTILINE
	)
	return text


DATA_IMPORT_PREFIX = 'model.data'
SCHEMA_IMPORT_PREFIX = f'{DATA_IMPORT_PREFIX}.json.schemas'


@dataclass
class Context:
	imports: OrderedDict[str, str] = field(default_factory=OrderedDict)
	templates: OrderedDict[str, JsonObject] = field(default_factory=OrderedDict)
	definitions: OrderedDict[str, JsonObject] = field(default_factory=OrderedDict)


def convert2(text: str, name: str, *, forceOptional: bool) -> JsonObject:
	text = extractOnlyinclude(text)
	lines = text.splitlines()
	linesStack = Stack(reversed([x for x in enumerate(lines, start=1)]))
	ctx = Context()
	body = handleObjectSchema(linesStack, 1, None, None, forceOptional, ctx)
	if name in ctx.definitions:
		raise ValueError(f"definition with name '{name}'already exists.")
	ctx.definitions[name] = body
	ctx.definitions.move_to_end(name, last=False)

	libraries = jObj(OrderedDict((ns, jStr(path)) for ns, path in ctx.imports.items()))
	definitions = jObj(ctx.definitions)
	templates = jObj(ctx.templates)
	schema = OrderedDict()
	schema["$schema"] = jStr("dpe/json/schema/library")
	schema["$libraries"] = libraries
	schema["$body"] = buildDefRef(name)
	schema["$templates"] = templates
	schema["$definitions"] = definitions

	return jObj(schema)


def buildDefRef(name: str) -> JsonObject:
	return jObj(OrderedDict([("$defRef", jStr(name))]))


TYPE_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)}})'
PROPERTY_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)\|([\w<(: )>\']+)}})'
PROPERTY_PATTERN = re.compile(rf' {PROPERTY_MARKER}(?:: ?)?(.*)')
ELEMENT_PATTERN = re.compile(rf' {TYPE_MARKER}(?:: ?)?(.*)')

PROPERTY_UNION_PATTERN = re.compile(rf' ({TYPE_MARKER}*){PROPERTY_MARKER}(?:: ?)?(.*)')
UNION_SPLIT_PATTERN = re.compile(rf'({TYPE_MARKER}*){TYPE_MARKER}')

INHERIT_PATTERN = re.compile(r' {{[Nn][Bb][Tt] inherit/([\w/]+)(?:\|indent=\*+)?}}')
DEPENDANT_PROP_PATTERN = re.compile(r" '''(\w+)'''")


class InheritInfo(NamedTuple):
	path: str
	name: str
	depProp: Optional[tuple[str, str]]


class Proptions(NamedTuple):
	name: str
	doc: str  # maybe not applicable if value is InheritInfo
	value: JsonObject
	# inherits: Optional[InheritInfo]
	depProp: Optional[tuple[str, str]]
	default: Optional[str]  # not applicable if value is InheritInfo
	optional: bool  # not applicable if value is InheritInfo
	deprecated: bool  # not applicable if value is InheritInfo


def handleProp(lineNoLine: tuple[int, str], linesStack: Stack[tuple[int, str]], depth: int, depProp: Optional[tuple[str, str]], ctx: Context, *, forceOptional: bool) -> Optional[Proptions | InheritInfo]:
	lineNo, line = lineNoLine
	if (match := PROPERTY_UNION_PATTERN.match(line, depth)) is not None:
		typeMarkers = match.group(1)
		lastType_ = match.group(3)
		name = match.group(4)
		doc = match.group(5)

		types = []
		while typeMarkers:
			imatch = UNION_SPLIT_PATTERN.match(typeMarkers)
			typeMarkers = imatch.group(1)
			types.append(imatch.group(3))
		types.append(lastType_)

		schemas = []
		for type_ in types:
			handler = _schemaHandlers.get(type_)
			if handler is None:
				print(f"[ ] no handler for type_ = {type_!r}, depProp={depProp!r} at line {lineNo}: {line!r}")
				return None  # '# ' + line
			schema = handler(linesStack, depth + 0, doc if depProp is not None else None, doc, forceOptional, ctx)
			schemas.append(schema)
		schema = buildUnionSchema(schemas, doc)
		default = None
		optional = False or forceOptional
		deprecated = 'deprecated' in doc.lower()
		return Proptions(name, doc, schema, depProp, default, optional, deprecated)

	# elif (match := PROPERTY_PATTERN.match(line, depth)) is not None:
	# 	type_ = match.group(1)
	# 	name = match.group(2)
	# 	doc = match.group(3)
	#
	# 	handler = _schemaHandlers.get(type_)
	# 	if handler is None:
	# 		print(f"[ ] no handler for type_ = {type_!r}, depProp={depProp!r}")
	# 		return line
	# 	schema = handler(linesStack, depth + 0, doc if depProp is not None else None, forceOptional)
	# 	default = None
	# 	optional = False or forceOptional
	# 	deprecated = 'deprecated' in doc.lower()
	# 	return Proptions(name, doc, schema, depProp, default, optional, deprecated)

	elif (match := INHERIT_PATTERN.match(line, depth)) is not None:
		path = match.group(1)
		name = path.rpartition('/')[2]
		return InheritInfo(path, name, depProp)
		# print(f"[ ] can't mix INHERIT and normal props at line {lineNo}: {line!r}, depProp={depProp!r}")
		# path = match.group(1)
		# const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"
		# if depProp is not None:
		# 	print(f"[ ] can't use depProp with INHERIT at line {lineNo}: {line!r}, depProp={depProp!r}")
		# return f'*{const}.properties'

	else:
		print(f"[ ] line didn't match property at line {lineNo}: {line!r}, depProp={depProp!r}")
		return None  # '# ' + line


def handlePropertiesInner(linesStack: Stack[tuple[int, str]], depth: int, depProp: Optional[tuple[str, str]], ctx: Context, *, forceOptional: bool) -> list[Proptions | InheritInfo]:
	properties: list[Proptions] = []
	lastProp: Optional[Proptions] = None
	while linesStack:
		lineNo, line = linesStack.peek()
		if not line.startswith('*' * depth + ' '):
			if line.startswith('*' * depth):
				linesStack.pop()
				print(f"too many asterisks at start of line {lineNo}: {line!r}")
				# properties.append('# ' + line)
				continue
			break
		else:
			linesStack.pop()

		if (match := DEPENDANT_PROP_PATTERN.match(line, depth)) is not None:
			if lastProp.optional and lastProp.default is None:
				# a decidingProp cannot be optional.
				idx = properties.index(lastProp)
				lastProp = replace_tuple(lastProp, optional=False)
				properties[idx] = lastProp

			name = match.group(1)
			properties.extend(handlePropertiesInner(linesStack, depth + 1, (lastProp.name, name), ctx, forceOptional=forceOptional))
		else:
			prop = handleProp((lineNo, line), linesStack, depth, depProp, ctx, forceOptional=forceOptional)
			if prop is not None:
				lastProp = prop
				properties.append(prop)
	return properties


def buildUnionSchema(schemas: list[JsonObject], doc: Optional[str]) -> JsonObject:
	if len(schemas) == 1:
		return schemas[0]
	else:
		return buildSchema('union', doc, options=jArr(schemas))


_schemaHandlers: dict[str, Callable[[Stack[tuple[int, str]], int, Optional[str], Optional[str], bool, Context], JsonObject]] = {}
schemaHandler = AddToDictDecorator(_schemaHandlers)


@schemaHandler('compound')
def handleObjectSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	# # are we inheriting anything?
	# lineNo, line = linesStack.peek()
	# if (match := INHERIT_PATTERN.match(line, depth + 1)) is not None:
	# 	linesStack.pop()
	# 	path = match.group(1)
	# 	const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"
	#
	# 	import_ = 'Advancement.' + path.replace('/', '.')
	# 	import_ = import_.replace('.conditions', '.Conditions')
	# 	ALL_IMPORTS.add(f'from {SCHEMA_IMPORT_PREFIX}.{import_} import {const}')
	#
	# 	return f'{const}'

	# "normal" object definition:
	properties = handlePropertiesInner(linesStack, depth + 1, None, ctx, forceOptional=forceOptional)
	inheritances: list[InheritInfo] = []
	byName: OrderedMultiDict[str, Proptions] = OrderedMultiDict()
	for proption in properties:
		if isinstance(proption, InheritInfo):
			inheritances.append(proption)
		else:
			byName.add(proption.name, proption)

	propsDict: OrderedDict[str, JsonObject] = OrderedDict()
	defaultProps: list[JsonObject] = []
	for name in byName.uniqueKeys():
		prop = buildProperty(byName.getall(name), ctx)

		if name.startswith(('<', "''", '(')):
			doc = f'{name}: {doc}'
			defaultProps.append(prop)
		else:
			propsDict[name] = prop

	inheritsByNamePathProp: OrderedMultiDict[tuple[str, str, str], InheritInfo] = OrderedMultiDict()
	for inh in inheritances:
		inheritsByNamePathProp.add((inh.name, inh.path, inh.depProp[0]), inh)

	inheritsList = []
	for key in inheritsByNamePathProp.uniqueKeys():
		inheritance = buildInheritance(inheritsByNamePathProp.getall(key), ctx)
		inheritsList.append(inheritance)
	# inheritsList = [buildInheritance(inheritance) for inheritance in inheritances]

	if not defaultProps:
		defaultProp = None
	elif len(defaultProps) == 1:
		defaultProp = defaultProps[0]
	else:
		defaultProp = buildUnionSchema(defaultProps, None)  # HERETIC! union of property is not possible!

	jProps = OrderedDict()
	if inheritsList:
		jProps['inherits'] = jArr(inheritsList)
	jProps['properties'] = jObj(propsDict)
	if defaultProp is not None:
		jProps['default-property'] = defaultProp

	return buildSchema('object', doc, **jProps)


def buildProperty(props: list[Proptions], ctx: Context) -> JsonObject:
	propertyProps: OrderedDict[str, JsonData] = OrderedDict()

	decidingProp = props[0].depProp
	if decidingProp is not None:
		decidingProp = decidingProp[0]
		byDecidingVal = OrderedMultiDict((p.depProp[1], p) for p in props)
		values = OrderedDict()
		for decidingVal in byDecidingVal.uniqueKeys():
			iProps = byDecidingVal.getall(decidingVal)
			for p in iProps:
				if p.depProp[0] != decidingProp:
					print(f"[ ] decidingProps don't match: expected:{decidingProp}, got {p.depProp[0]}")
			if len(iProps) > 1:
				value = buildUnionSchema([pp.value for pp in iProps], None)
			else:
				value = iProps[0].value

			defRefName = f'%{props[0].name}-{decidingVal}'
			if defRefName in ctx.definitions:
				i = 2
				while (defRefName2 := f'{defRefName}-{i}') in ctx.definitions:
					i += 1
				logError(f"definition with name '{defRefName}'already exists. Using '{defRefName2}' instead")
				defRefName = defRefName2

			ctx.definitions[defRefName] = value
			defRef = buildDefRef(defRefName)
			values[f'minecraft:{decidingVal}'] = defRef
			values[decidingVal] = defRef

		propertyProps.update(
			decidingProp=jStr(decidingProp),
			values=jObj(values),
		)

	else:
		p = props[0]
		if len(props) > 1:
			value = buildUnionSchema([pp.value for pp in props], None)
		else:
			value = p.value
		propertyProps.update(
			description=jStr(p.doc),
			value=value,
		)

	if props[0].optional:
		propertyProps["optional"] = jBool(True)
	if props[0].default is not None:
		propertyProps["default"] = jStr(props[0].default)
	if props[0].deprecated:
		propertyProps["deprecated"] = jBool(True)
	return jObj(propertyProps)


def buildInheritance(inheritances: list[InheritInfo], ctx: Context) -> JsonObject:
	ns = inheritances[0].path.rpartition('/')[2]
	ctx.imports[ns] = inheritances[0].path + '.json'
	defRef = jStr(f'{ns}:{inheritances[0].name}')
	if inheritances[0].depProp is not None:
		values = []
		for inh in inheritances:
			values.append(jStr(inh.depProp[1]))
			values.append(jStr(f'minecraft:{inh.depProp[1]}'))
		return jObj(OrderedDict(
			defRef=defRef,
			decidingProp=jStr(inheritances[0].depProp[0]),
			decidingValues=jArr(values),
		))
	else:
		return jObj(OrderedDict(
			defRef=defRef,
		))


@schemaHandler('bool')
@schemaHandler('boolean')
def handleBoolSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('boolean', doc)


@schemaHandler('int')
def handleIntSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('integer', doc)


@schemaHandler('double')
@schemaHandler('float')
def handleFloatSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('float', doc)


RES_LOC_MATCHER_1 = re.compile(r'\[\[[^]\n]*values#(\w+)')
RES_LOC_MATCHER_2 = re.compile(r'(\w+) ids?]]')

NBT_MATCHER_1 = re.compile(r'(?<!{{)nbt')


@schemaHandler('string')
def handleStrSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	docToAnalyze = doc if doc else parentDoc
	if docToAnalyze:
		docToAnalyze = docToAnalyze.lower()

		resLoc = None
		if resLocs := list(RES_LOC_MATCHER_1.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1).removesuffix('s')
		elif resLocs := list(RES_LOC_MATCHER_2.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1)
		if resLoc:
			return buildSchema('string', doc, type=jStr('minecraft:resource_location'), args=jObj(OrderedDict(schema=jStr(resLoc))))
		if list(NBT_MATCHER_1.finditer(docToAnalyze)):
			return buildSchema('string', doc, type=jStr('minecraft:nbt_compound_tag'))

	return buildSchema('string', doc)


@schemaHandler('list')
def handleArraySchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	elements: list[JsonObject] = []
	if linesStack:
		lineNo, line = linesStack.peek()
		if not line.startswith('*' * (depth + 1) + ' '):
			if line.startswith('*' * (depth + 1)):
				linesStack.pop()
				print(f"too many asterix at start of line {lineNo}: {line!r}")
				elements.append(buildSchema('any', line))
			else:
				pass  # element = None
		else:
			if ELEMENT_PATTERN.match(line, depth + 1) is None:
				print(f"[ ] line {lineNo} didn't match element: {line!r}")
				elements.append(buildSchema('any', line))
				linesStack.pop()
			else:
				while (match := ELEMENT_PATTERN.match(line, depth + 1)) is not None:
					linesStack.pop()
					type_ = match.group(1)
					iDoc = match.group(2)
					handler = _schemaHandlers.get(type_)
					if handler is None:
						print(f"[ ] no handler for type_ at line {lineNo}: {line!r}, type_ = {type_!r}")
						elements.append(buildSchema('any', line))
					else:
						elements.append(handler(linesStack, depth + 1, iDoc, doc, forceOptional, ctx))
					if linesStack:
						lineNo, line = linesStack.peek()
					else:
						break
	else:
		pass  # element = None

	if not elements:
		element = handleStrSchema(linesStack, depth + 1, doc, parentDoc, forceOptional, ctx)
	else:
		element = buildUnionSchema(elements, None)
	# element = indentMultilineStr(element, indent=INDENT, indentFirstLine=False)
	return buildSchema('array', doc, element=element)


def processFile(srcPath: str, dstPath: str, name: str, *, forceOptional: bool):
	with open(srcPath, 'r', encoding='utf-8') as f:
		text = f.read()
	schema = convert2(text, name, forceOptional=forceOptional)
	newText = emitter.emitJson(schema, indent=2)
	with openOrCreate(dstPath, 'w', encoding='utf-8') as f:
		f.write(newText)


SRC_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/Recipe"
DST_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWikiCompiled2/Recipe"
FOLDER_FILTER = "**"

CURRENT_FILE_PATH: str = ""


def run():
	allFiles: list[str] = []

	def addToAllFiles(path: str):
		if path.endswith('.wiki'):
			allFiles.append(path)

	processRecursively(SRC_FOLDER, FOLDER_FILTER, addToAllFiles)

	print(f"There are {len(allFiles)} files to edit...")

	allPaths: list[tuple[str, str, str]] = []
	imports = []

	for srcPath in allFiles:
		srcPath = srcPath.replace('\\', '/')
		pathPart = srcPath.removeprefix(SRC_FOLDER).rpartition('.')[0]
		pathPart = pathPart.strip('/')
		dstPath = os.path.join(DST_FOLDER, pathPart).replace('\\', '/') + '.json'
		name = pathPart.rpartition('/')[2]
		import_ = pathPart.replace('/', '.')
		imports.append(f'from {SCHEMA_IMPORT_PREFIX}.{import_} import {name}')
		allPaths.append((srcPath, dstPath, name))

	# imports = NL.join(imports)

	global CURRENT_FILE_PATH
	for i, (srcPath, dstPath, name) in enumerate(allPaths):
		CURRENT_FILE_PATH = srcPath
		# if i % 100 == 0:
		print(f"")
		print(f"processing file {i}, name = {name}")
		print(f"path      = {srcPath}")
		print(f"save path = {dstPath}")
		processFile(srcPath, dstPath, name, forceOptional=True)
		print(f"==========================================================================")


run()
