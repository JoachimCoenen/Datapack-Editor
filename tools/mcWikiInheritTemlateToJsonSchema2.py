import enum
import os
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Callable, NamedTuple, Literal

from cat.processFiles import processRecursively
from cat.utils import openOrCreate
from cat.utils.collections_ import AddToDictDecorator, Stack, OrderedMultiDict
from cat.utils.typing_ import replace_tuple
from corePlugins.json import emitter
from corePlugins.json.core import *
from base.model.parsing.parser import IndexMapper
from base.model.utils import NULL_SPAN
from tools.transformDependantProps import transformDependantPropsInFile

INDENT = '\t'
NL = '\n'
SEP = f',{NL}'
f',{NL}'


def jNull() -> JsonNull:
	return JsonNull(NULL_SPAN, None)


def jBool(value: bool) -> JsonBool:
	return JsonBool(NULL_SPAN, None, value)


def jNum(value: int | float) -> JsonNumber:
	return JsonNumber(NULL_SPAN, None, value)


def jStr(value: str) -> JsonString:
	return JsonString(NULL_SPAN, None, value, IndexMapper())


def jArr(elements: list[JsonData]) -> JsonArray:
	return JsonArray(NULL_SPAN, None, list(elements))


def makeJProp(key: str, value: JsonData) -> JsonProperty:
	return JsonProperty(NULL_SPAN, None, jStr(key), value)


def jObj(props: OrderedDict[str, JsonData]) -> JsonObject:
	properties = OrderedMultiDict((key, makeJProp(key, value)) for key, value in props.items())
	return JsonObject(NULL_SPAN, None, properties)


SchemaTypeType = Literal['object', 'array', 'union', 'any', 'string', 'enum', 'boolean', 'integer', 'float', 'null', 'calculated']


def buildSchema(type_: SchemaTypeType, *, doc: Optional[str], props: dict[str, JsonData] = ...) -> JsonObject:
	if props is ...:
		props = {}
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


def removeUselessLines(lines: list[str]) -> list[str]:
	return [
		line
		for line in lines
		if not line.startswith(('<div ', '</div>'))
	]


DATA_IMPORT_PREFIX = 'model.data'
SCHEMA_IMPORT_PREFIX = f'{DATA_IMPORT_PREFIX}.json.schemas'


class LineNoLine(NamedTuple):
	lineNo: int
	line: str


LineNoLineStack = Stack[LineNoLine]


@dataclass
class Context:
	srcFolder: str
	imports: OrderedDict[str, str] = field(default_factory=OrderedDict)
	templates: OrderedDict[str, JsonObject] = field(default_factory=OrderedDict)
	definitions: OrderedDict[str, JsonObject] = field(default_factory=OrderedDict)
	# temporaries:
	# props: whatever


def convert2(text: str, name: str, srcFolder: str, *, forceOptional: bool) -> JsonObject:
	text = extractOnlyinclude(text)
	lines = text.splitlines()
	lines = removeUselessLines(lines)
	linesStack = makeLineStack(lines)
	ctx = Context(srcFolder)
	body = handleObjectSchema(LineNoLine(-1, ' '), linesStack, 1, None, None, forceOptional, ctx)
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


def makeLineStack(lines: list[str]) -> LineNoLineStack:
	return LineNoLineStack(reversed([LineNoLine(*x) for x in enumerate(lines, start=1)]))


def buildDefRef(name: str) -> JsonObject:
	return jObj(OrderedDict([("$defRef", jStr(name))]))


TYPE_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)}})'
PROPERTY_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)\|([\w<(: )>\']+)}})'
PROPERTY_PATTERN = re.compile(rf' ?{PROPERTY_MARKER}(?:: ?)?(.*)')
ELEMENT_PATTERN = re.compile(rf' ?{TYPE_MARKER}(?:: ?)?(.*)')

PROPERTY_UNION_PATTERN = re.compile(rf' ?({TYPE_MARKER}+){PROPERTY_MARKER}(?:: ?)?(.*)')
UNION_SPLIT_PATTERN = re.compile(rf'({TYPE_MARKER}*){TYPE_MARKER}')

INHERIT_PATTERN = re.compile(r' ?{{[Nn][Bb][Tt] inherit/([\w/]+)(?:\|indent=\*+)?}}')
DEPENDANT_PROP_PATTERN = re.compile(r" ?'''(\w+)'''")
DEPENDANT_PROPS_FROM_FILE_PATTERN = re.compile(r" ?~~dependantProps\( *([./\w-]+) *, *(.+)\)~~")

RAW_JSON_TEXT_MATCHER_1 = re.compile(r'\[Raw JSON text format\|')


class InheritInfo(NamedTuple):
	path: str
	name: str
	depProp: Optional[tuple[str, str]]


@dataclass(frozen=True)
class DepProp:
	decidingProp: str
	decidingValue: str


class Proptions(NamedTuple):
	name: str
	doc: str  # maybe not applicable if value is InheritInfo
	value: JsonObject
	# inherits: Optional[InheritInfo]
	depProp: Optional[DepProp]
	default: Optional[str]  # not applicable if value is InheritInfo
	optional: bool  # not applicable if value is InheritInfo
	deprecated: bool  # not applicable if value is InheritInfo
	lineNoLine: LineNoLine


def _log(msg: str, ctx: Context, lineNoLine: LineNoLine, *, kind: str) -> None:
	if not msg.endswith(('.', '!', '?')):
		msg = msg + '.'
	position = f" at line {lineNoLine.lineNo}: {lineNoLine.line!r}"
	print(f"[{kind}] {msg}" + position)


def error(msg: str, ctx: Context, lineNoLine: LineNoLine) -> None:
	_log(msg, ctx, lineNoLine, kind='error  ')


def warning(msg: str, ctx: Context, lineNoLine: LineNoLine) -> None:
	_log(msg, ctx, lineNoLine, kind='warning')


def handleProp(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, depProp: Optional[DepProp], ctx: Context, *, forceOptional: bool) -> Optional[Proptions | InheritInfo]:
	lineNo, line = lineNoLine
	if (match := INHERIT_PATTERN.match(line, depth)) is not None:
		path = match.group(1)
		name = path.rpartition('/')[2]
		return InheritInfo(path, name, depProp)

	elif (match := PROPERTY_UNION_PATTERN.match(line, depth)) is not None:
		typeMarkers = match.group(1)
		lastType_ = match.group(3)
		name = match.group(4)
		doc = match.group(5)
		iDoc = doc if depProp is not None else None

		if list(RAW_JSON_TEXT_MATCHER_1.finditer(doc)):
			ctx.imports['rawJsonText'] = 'rawJsonText-library.json'
			schema = buildDefRef('rawJsonText:rawJsonText')
		else:
			types = []
			while typeMarkers:
				imatch = UNION_SPLIT_PATTERN.match(typeMarkers)
				typeMarkers = imatch.group(1)
				types.append(imatch.group(3))
			types.append(lastType_)

			schemas = []
			for type_ in types:
				innerSchema = applySchemaHandler(type_, lineNoLine, iDoc, doc, linesStack, depth, depProp, ctx, forceOptional=forceOptional, doesBreakIgnore=True)
				if innerSchema is None:
					continue
				schemas.append(innerSchema)
			schema = buildUnionSchema(schemas, doc)
	elif (match := PROPERTY_PATTERN.match(line, depth)) is not None:
		type_ = match.group(1)
		name = match.group(2)
		doc = match.group(3)
		iDoc = doc if depProp is not None else None

		schema = applySchemaHandler(type_, lineNoLine, iDoc, doc, linesStack, depth, depProp, ctx, forceOptional=forceOptional, doesBreakIgnore=True)
		if schema is None:
			return None
	else:
		error(f"line didn't match property, depProp={depProp!r}", ctx, lineNoLine)
		return None  # '# ' + line

	default = None
	optional = False or forceOptional
	deprecated = 'deprecated' in doc.lower()
	if doc.startswith("<span style=\"color:red;\">'''*'''</span>: "):
		optional = False
		doc = doc.removeprefix("<span style=\"color:red;\">'''*'''</span>: ")
	return Proptions(name, doc, schema, depProp, default, optional, deprecated, lineNoLine)


class CheckDepthResult(enum.Enum):
	OK = 0
	TOO_SHALLOW = 1
	TOO_DEEP = 2
	ILLEGAL_CHAR = 3  # 'illegal char' or 'line too short'


def checkDepth(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, ctx: Context) -> CheckDepthResult:
	asterisks = '*' * depth
	properLineStart = (' ', '{', "'")
	line = lineNoLine.line
	if not line.startswith(asterisks):
		return CheckDepthResult.TOO_SHALLOW
	elif line.startswith(properLineStart, depth):
		return CheckDepthResult.OK
	elif line.startswith('*', depth):
		linesStack.pop()  # we don't know what to do with the line, so remove it.
		error(f"too many asterisks at start of line. Expected {depth} asterisks.", ctx, lineNoLine)
		return CheckDepthResult.TOO_DEEP
	else:  # something else is after the appropriate amount of asterisks
		linesStack.pop()  # we don't know what to do with the line, so remove it.
		butMsg = f"the following character ({line[depth]!r}) is illegal." if len(line) > depth else f"the line is too short."
		error(f"illegal start of line. Number of asterisks is correct, but {butMsg}", ctx, lineNoLine)
		return CheckDepthResult.ILLEGAL_CHAR


def startsWithDepthOLD(line: str, depth: int) -> bool:
	asterisks = '*' * depth
	return line.startswith((asterisks + ' ', asterisks + '{', asterisks + "'"))


def checkDepthOLD(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, ctx: Context) -> CheckDepthResult:
	lineNo, line = lineNoLine
	if not startsWithDepthOLD(line, depth):
		if line.startswith('*' * (depth+1)):  #
			linesStack.pop()
			error(f"too many asterisks at start of line. Expected {depth} asterisks.", ctx, lineNoLine)
			# properties.append('# ' + line)
			return CheckDepthResult.TOO_DEEP
		elif line.startswith('*' * depth):
			linesStack.pop()
			butMsg = f"the following character ({line[depth]!r}) is illegal." if len(line) > depth else f"the line is too short."
			error(f"illegal start of line. Number of asterisks is correct, but {butMsg}", ctx, lineNoLine)
			# properties.append('# ' + line)
			return CheckDepthResult.ILLEGAL_CHAR
		return CheckDepthResult.TOO_SHALLOW
	else:
		return CheckDepthResult.OK


def handlePropertiesInner(linesStack: LineNoLineStack, depth: int, depProp: Optional[DepProp], ctx: Context, *, forceOptional: bool) -> list[Proptions | InheritInfo]:
	properties: list[Proptions | InheritInfo] = []
	lastProp: Optional[Proptions | InheritInfo] = None
	while linesStack:
		lineNoLine = linesStack.peek()
		match checkDepth(lineNoLine, linesStack, depth, ctx):
			case CheckDepthResult.OK:
				pass  # do actual work
			case CheckDepthResult.TOO_SHALLOW:
				break
			case CheckDepthResult.TOO_DEEP | CheckDepthResult.ILLEGAL_CHAR:
				continue
			case checkDepthResult:
				raise ValueError(f"unhandled checkDepth(...) result: {checkDepthResult!r}")

		linesStack.pop()
		if (match := DEPENDANT_PROP_PATTERN.match(lineNoLine.line, depth)) is not None:
			if isinstance(lastProp, InheritInfo):
				error(f"dependant property after inherit is not allowed", ctx, lineNoLine)  # maybe add depProp info, idk ?
			elif lastProp is None:
				error(f"dependant property requires a previous property, but it seems to be missing...", ctx, lineNoLine)  # maybe add depProp info, idk ?
			else:
				lastProp = makeDecidingPropMandatory(lastProp, properties)
				properties.extend(handleDependantProp(linesStack, depth, lastProp.name, ctx, match, forceOptional=forceOptional))
		elif (match := DEPENDANT_PROPS_FROM_FILE_PATTERN.match(lineNoLine.line, depth)) is not None:
			properties.extend(handleDependantPropsFromFile(depth, ctx, match, forceOptional=forceOptional))
		else:
			prop = handleProp(lineNoLine, linesStack, depth, depProp, ctx, forceOptional=forceOptional)
			if prop is not None:
				lastProp = prop
				properties.append(prop)
	return properties


#ef handleDependantPropsFromFile(ctx, depProp: Optional[DepProp], depth, forceOptional, match, properties):
def handleDependantPropsFromFile(depth: int, ctx: Context, match: re.Match[str], *, forceOptional: bool):
	depPropName = match.group(1)
	relFilePath = match.group(2)
	filePath = f'{ctx.srcFolder}/{relFilePath}'
	linesStack = makeLineStack(transformDependantPropsInFile(filePath, level=depth))
	properties: list[Proptions | InheritInfo] = []
	while linesStack:
		lineNoLine = linesStack.peek()
		match checkDepth(lineNoLine, linesStack, depth, ctx):
			case CheckDepthResult.OK:
				pass  # do actual work
			case CheckDepthResult.TOO_SHALLOW:
				break
			case CheckDepthResult.TOO_DEEP | CheckDepthResult.ILLEGAL_CHAR:
				continue
			case checkDepthResult:
				raise ValueError(f"unhandled checkDepth(...) result: {checkDepthResult!r}")

		linesStack.pop()
		if (match := DEPENDANT_PROP_PATTERN.match(lineNoLine.line, depth)) is not None:
			# todo: IMPORTANT! lastProp = makeDecidingPropMandatory(lastProp, properties)
			properties.extend(handleDependantProp(linesStack, depth, depPropName, ctx, match, forceOptional=forceOptional))
		else:
			error(f"line didn't match dependant property", ctx, lineNoLine)
	return properties


def handleDependantProp(linesStack: LineNoLineStack, depth: int, depPropName: str, ctx: Context, match: re.Match[str], *, forceOptional: bool) -> list[Proptions | InheritInfo]:
	"""
	:return: lastProp (which might have been modified.)
	"""
	decidingValue = match.group(1)
	return handlePropertiesInner(linesStack, depth + 1, DepProp(depPropName, decidingValue), ctx, forceOptional=forceOptional)


def makeDecidingPropMandatory(decidingProp: Proptions, properties: list[Proptions | InheritInfo]):
	if decidingProp.optional and decidingProp.default is None:
		# a decidingProp cannot be optional.
		idx = properties.index(decidingProp)
		lastProp = replace_tuple(decidingProp, optional=False)
		properties[idx] = lastProp
	return decidingProp


def buildUnionSchema(schemas: list[JsonObject], doc: Optional[str]) -> JsonObject:
	if len(schemas) == 1:
		return schemas[0]
	else:
		return buildSchema('union', doc=doc, props=dict(options=jArr(schemas)))


_schemaHandlers: dict[str, Callable[[LineNoLine, LineNoLineStack, int, Optional[str], Optional[str], bool, Context], JsonObject]] = {}
schemaHandler = AddToDictDecorator(_schemaHandlers)


def applySchemaHandler(type_: str, lineNoLine: LineNoLine, iDoc: Optional[str], doc: str, linesStack: LineNoLineStack, depth: int, depProp: Optional[DepProp], ctx: Context, *, forceOptional: bool, doesBreakIgnore: bool) -> Optional[JsonObject]:
	handler = _schemaHandlers.get(type_)
	if handler is None:
		depPropMsg = f", depProp={depProp!r}" if depProp is not None else ""
		breakMsg = f"Breaking/Ignoring!" if doesBreakIgnore is not None else "Replacing with any-schema."
		error(f"no handler for type_ = {type_!r}{depPropMsg}. {breakMsg}", ctx, lineNoLine)
		return None
	return handler(lineNoLine, linesStack, depth + 0, iDoc, doc, forceOptional, ctx)


def buildProperty(props: list[Proptions], ctx: Context) -> JsonObject:
	propertyProps: OrderedDict[str, JsonData] = OrderedDict()

	firstProp = props[0]
	firstDepProp = firstProp.depProp
	if firstDepProp is not None:
		firstDecidingProp = firstDepProp.decidingProp
		byDecidingVal = OrderedMultiDict((p.depProp.decidingValue, p) for p in props)
		values = OrderedDict()
		for decidingVal in byDecidingVal.uniqueKeys():
			iProps: list[Proptions] = byDecidingVal.getall(decidingVal)
			for p in iProps:
				if p.depProp.decidingProp != firstDecidingProp:
					error(f"decidingProps don't match: expected:{firstDecidingProp}, got {p.depProp.decidingProp}", ctx, p.lineNoLine)
			if len(iProps) > 1:
				value = buildUnionSchema([pp.value for pp in iProps], None)
			else:
				value = iProps[0].value

			defRefName = f'%{firstProp.name}-{decidingVal}'
			if defRefName in ctx.definitions:
				i = 2
				while (defRefName2 := f'{defRefName}-{i}') in ctx.definitions:
					i += 1
				warning(f"definition with name '{defRefName}'already exists. Using '{defRefName2}' instead", ctx, firstProp.lineNoLine)
				defRefName = defRefName2

			ctx.definitions[defRefName] = value
			defRef = buildDefRef(defRefName)
			# values[f'minecraft:{decidingVal}'] = defRef
			values[decidingVal] = defRef

		propertyProps.update(
			decidingProp=jStr(firstDecidingProp),
			values=jObj(values),
			optionalPrefixes=jArr([jStr('minecraft:')])
		)

	else:
		p = firstProp
		if len(props) > 1:
			value = buildUnionSchema([pp.value for pp in props], None)
		else:
			value = p.value
		propertyProps.update(
			description=jStr(p.doc),
			value=value,
		)

	if firstProp.optional:
		propertyProps["optional"] = jBool(True)
	if firstProp.default is not None:
		propertyProps["default"] = jStr(firstProp.default)
	if firstProp.deprecated:
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
def handleBoolSchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('boolean', doc=doc)


@schemaHandler('int')
def handleIntSchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('integer', doc=doc)


@schemaHandler('double')
@schemaHandler('float')
def handleFloatSchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	return buildSchema('float', doc=doc)


RES_LOC_MATCHER_1 = re.compile(r'\[\[[^]\n]*values#(\w+)')
RES_LOC_MATCHER_2 = re.compile(r'(\w+) ids?]]')

NBT_MATCHER_1 = re.compile(r'(?<!{{)nbt')


@schemaHandler('string')
def handleStrSchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	docToAnalyze = doc if doc else parentDoc
	if docToAnalyze:
		docToAnalyze = docToAnalyze.lower()

		resLoc = None
		if resLocs := list(RES_LOC_MATCHER_1.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1).removesuffix('s')
		elif resLocs := list(RES_LOC_MATCHER_2.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1)
		if resLoc:
			return buildSchema('string', doc=doc, props=dict(type=jStr('minecraft:resource_location'), args=jObj(OrderedDict(schema=jStr(resLoc)))))
		if list(NBT_MATCHER_1.finditer(docToAnalyze)):
			return buildSchema('string', doc=doc, props=dict(type=jStr('minecraft:nbt_compound_tag')))

	return buildSchema('string', doc=doc)


@schemaHandler('list')
def handleArraySchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
	nextDepth = depth + 1
	elements: list[JsonObject] = []

	while linesStack:
		lineNoLine = linesStack.peek()

		match checkDepth(lineNoLine, linesStack, nextDepth, ctx):
			case CheckDepthResult.OK:
				pass  # do actual work
			case CheckDepthResult.TOO_SHALLOW:
				break
			case CheckDepthResult.TOO_DEEP | CheckDepthResult.ILLEGAL_CHAR:
				# elements.append(buildSchema('any', doc=line))
				continue
			case checkDepthResult:
				raise ValueError(f"unhandled checkDepth(...) result: {checkDepthResult!r}")

		linesStack.pop()
		if (match := ELEMENT_PATTERN.match(lineNoLine.line, nextDepth)) is not None:
			type_ = match.group(1)
			iDoc = match.group(2)

			innerSchema = applySchemaHandler(type_, lineNoLine, iDoc, doc, linesStack, nextDepth, None, ctx, forceOptional=forceOptional, doesBreakIgnore=False)
			if innerSchema is None:
				innerSchema = buildSchema('any', doc=lineNoLine.line)
			elements.append(innerSchema)
		else:
			elements.append(handleObjectSchema(lineNoLine, linesStack, depth + 0, None, None, forceOptional, ctx))
			# # error(f"MESSAGGEE", ctx, lineNoLine)
			# # print(f"[ ] line {lineNo} didn't match element: {line!r}")
			# # elements.append(buildSchema('any', doc=line))
			# # linesStack.pop()
			# error("illegal element pattern", ctx, lineNoLine)

	if not elements:
		warning(f"no element schemas for list.", ctx, lineNoLine)
		element = handleStrSchema(lineNoLine, linesStack, nextDepth, doc, parentDoc, forceOptional, ctx)
	else:
		element = buildUnionSchema(elements, None)
	# element = indentMultilineStr(element, indent=INDENT, indentFirstLine=False)
	return buildSchema('array', doc=doc, props=dict(element=element))


@schemaHandler('compound')
def handleObjectSchema(lineNoLine: LineNoLine, linesStack: LineNoLineStack, depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool, ctx: Context) -> JsonObject:
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
		inheritsByNamePathProp.add((inh.name, inh.path, inh.depProp[0] if inh.depProp is not None else None), inh)

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

	return buildSchema('object', doc=doc, props=jProps)


def processFile(srcPath: str, dstPath: str, name: str, *, forceOptional: bool):
	with open(srcPath, 'r', encoding='utf-8') as f:
		text = f.read()
	srcFolder = srcPath.rpartition('/')[0]
	schema = convert2(text, name, srcFolder, forceOptional=forceOptional)
	newText = emitter.emitJson(schema, indent=2)
	with openOrCreate(dstPath, 'w', encoding='utf-8') as f:
		f.write(newText)


# SRC_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/Item_modifier"
# DST_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWikiCompiled2/Item_modifier"

SRC_FOLDER: str = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/Advancement/advancement.wiki"
DST_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWikiCompiled2/Advancement"
FOLDER_FILTER = "**"

CURRENT_FILE_PATH: str = ""


def run():
	global SRC_FOLDER
	allFiles: list[str] = []

	def addToAllFiles(path: str):
		if path.endswith('.wiki'):
			allFiles.append(path)

	if SRC_FOLDER.endswith('.wiki'):
		allFiles.append(SRC_FOLDER)
		SRC_FOLDER = SRC_FOLDER.rpartition('/')[0]
	else:
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
