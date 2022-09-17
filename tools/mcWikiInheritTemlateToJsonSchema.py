import os
import re
from typing import Optional, Callable, NamedTuple, Union

from Cat.extensions import processRecursively
from Cat.utils import openOrCreate
from Cat.utils.collections_ import AddToDictDecorator, Stack, OrderedMultiDict
from Cat.utils.formatters import indentMultilineStr
from Cat.utils.typing_ import replace_tuple


INDENT = '\t'
NL = '\n'
SEP = f',{NL}'
f',{NL}'


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


ALL_IMPORTS = set()
DATA_IMPORT_PREFIX = 'model.data'
SCHEMA_IMPORT_PREFIX = f'{DATA_IMPORT_PREFIX}.json.schemas'


def addImports(text, name):
	imports = NL.join(im for im in ALL_IMPORTS if not im.endswith(name))
	ALL_IMPORTS.clear()
	return (
		f"from Cat.utils import Anything\n"
		f"from {DATA_IMPORT_PREFIX}.json.argTypes import *\n"
		f"from {DATA_IMPORT_PREFIX}.json.utils import *\n"
		f"from model.json.core import *\n"
		f"from model.utils import MDStr\n"
		f"\n"
		f"{imports}\n"
		f"\n"
		f"{text}\n")


def convert3(text: str, name: str, *, forceOptional: bool) -> str:
	original = text
	text = extractOnlyinclude(text)
	lines = text.splitlines()
	linesStack = Stack(reversed([x for x in enumerate(lines, start=1)]))
	schema = handleObjectSchema(linesStack, 1, None, None, forceOptional)
	schema = f"{name} = {schema}\n"
	return addImports(schema, name)


def convert2(text: str, name: str, imports: str, *, forceOptional: bool) -> str:
	original = text
	text = extractOnlyinclude(text)
	lines = text.splitlines()
	linesStack = Stack(reversed([x for x in enumerate(lines, start=1)]))
	doc, props = handleProperties(linesStack, 2, None, forceOptional=forceOptional)
	propsStr = indentMultilineStr(SEP.join(props), indent=INDENT)
	schema = buildObjectSchema([], doc)
	schema = (
		f"{name} = {schema}\n"
		f"{name}.properties = (\n"
		f"{propsStr}\n"
		f")\n"
		f"\n"
		f"{name}.buildPropertiesDict()\n"
	)
	return addImports(schema, name)


TYPE_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)}})'
PROPERTY_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)\|([\w<: >\']+)}})'
PROPERTY_PATTERN = re.compile(rf' {PROPERTY_MARKER}(?:: ?)?(.*)')
ELEMENT_PATTERN = re.compile(rf' {TYPE_MARKER}(?:: ?)?(.*)')

PROPERTY_UNION_PATTERN = re.compile(rf' ({TYPE_MARKER}*){PROPERTY_MARKER}(?:: ?)?(.*)')
UNION_SPLIT_PATTERN = re.compile(rf'({TYPE_MARKER}*){TYPE_MARKER}')

INHERIT_PATTERN = re.compile(r' {{[Nn][Bb][Tt] inherit/([\w/]+)(?:\|indent=\*+)?}}')
DEPENDANT_PROP_PATTERN = re.compile(r" '''(\w+)'''")


class Proptions(NamedTuple):
	name: str
	doc: str
	value: str
	depProp: Optional[tuple[str, str]]
	default: Optional[str]
	optional: bool
	deprecated: bool


def handleProp(lineNoLine: tuple[int, str], linesStack: Stack[tuple[int, str]], depth: int, depProp: Optional[tuple[str, str]], *, forceOptional: bool) -> Union[str, Proptions]:
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
				return '# ' + line
			schema = handler(linesStack, depth + 0, doc if depProp is not None else None, doc, forceOptional)
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
		print(f"[ ] can't mix INHERIT and normal props at line {lineNo}: {line!r}, depProp={depProp!r}")
		path = match.group(1)
		const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"
		if depProp is not None:
			print(f"[ ] can't use depProp with INHERIT at line {lineNo}: {line!r}, depProp={depProp!r}")
		return f'*{const}.properties'

	else:
		print(f"[ ] line didn't match property at line {lineNo}: {line!r}, depProp={depProp!r}")
		return '# ' + line


def handlePropertiesInner(linesStack: Stack[tuple[int, str]], depth: int, depProp: Optional[tuple[str, str]], *, forceOptional: bool) -> list[Union[str, Proptions]]:
	properties = []
	lastProp: Optional[Proptions] = None
	while linesStack:
		lineNo, line = linesStack.peek()
		if not line.startswith('*' * depth + ' '):
			if line.startswith('*' * depth):
				linesStack.pop()
				print(f"too many asterisks at start of line {lineNo}: {line!r}")
				properties.append('# ' + line)
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
			properties.extend(handlePropertiesInner(linesStack, depth + 1, (lastProp.name, name), forceOptional=forceOptional))
		else:
			prop = handleProp((lineNo, line), linesStack, depth, depProp, forceOptional=forceOptional)
			if isinstance(prop, Proptions):
				lastProp = prop
			properties.append(prop)
	return properties


def buildUnionSchema(schemas: list[str], doc: Optional[str]) -> str:
	if len(schemas) == 1:
		return schemas[0]
	else:
		options = SEP.join(schemas)
		if doc is not None:
			propsStr = indentMultilineStr(options, indent=INDENT * 2)
			return (
				f"JsonUnionSchema(\n"
				f"\tdescription=MDStr({doc!r}),\n"
				f"\toptions=[\n"
				f"{propsStr}\n"
				f"\t]\n"
				f")"
			)
		else:
			propsStr = indentMultilineStr(options, indent=INDENT * 1)
			return f"JsonUnionSchema(options=[\n{propsStr}\n])"


def buildObjectSchema(properties: list[str], doc: Optional[str]) -> str:
	if doc:
		propertiesStr = indentMultilineStr(SEP.join(properties), indent=INDENT*2)
		return (
			f"JsonObjectSchema(\n"
			f'\tdescription=MDStr({doc!r}),\n'
			f"\tproperties=[\n"
			f"{propertiesStr}\n"
			f"\t]\n"
			f")")
	else:
		propertiesStr = indentMultilineStr(SEP.join(properties), indent=INDENT)
		return f"JsonObjectSchema(properties=[\n{propertiesStr}\n])"


_schemaHandlers: dict[str, Callable[[Stack[tuple[int, str]], int, Optional[str], Optional[str], bool], str]] = {}
schemaHandler = AddToDictDecorator(_schemaHandlers)


@schemaHandler('compound')
def handleObjectSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	# are we inheriting anything?
	lineNo, line = linesStack.peek()
	if (match := INHERIT_PATTERN.match(line, depth + 1)) is not None:
		linesStack.pop()
		path = match.group(1)
		const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"

		import_ = 'Advancement.' + path.replace('/', '.')
		import_ = import_.replace('.conditions', '.Conditions')
		ALL_IMPORTS.add(f'from {SCHEMA_IMPORT_PREFIX}.{import_} import {const}')

		return f'{const}'

	# "normal" object definition:
	doc, propStrings = handleProperties(linesStack, depth + 1, doc, forceOptional=forceOptional)

	return buildObjectSchema(propStrings, doc)


def handleProperties(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], *, forceOptional: bool) -> tuple[Optional[str], list[str]]:
	properties = handlePropertiesInner(linesStack, depth, None, forceOptional=forceOptional)
	propStrings = []
	byName: OrderedMultiDict[str, Proptions] = OrderedMultiDict()
	for prop in properties:
		if isinstance(prop, str):
			propStrings.append(prop)
		else:
			byName.add(prop.name, prop)
	for name in byName.uniqueKeys():
		props = byName.getall(name)
		decidingProp = props[0].depProp
		if decidingProp is not None:
			decidingProp = decidingProp[0]
			byDecidingVal = OrderedMultiDict((p.depProp[1], p) for p in props)
			values = []
			for decidingVal in byDecidingVal.uniqueKeys():
				iProps = byDecidingVal.getall(decidingVal)
				for p in iProps:
					if p.depProp[0] != decidingProp:
						print(f"[ ] decidingProps don't match: expected:{decidingProp}, got {p.depProp[0]}")
				if len(iProps) > 1:
					valueStr = buildUnionSchema([pp.value for pp in iProps], None)
				else:
					valueStr = iProps[0].value
				value = f"'{decidingVal}': {valueStr}"
				values.append(value)

			valuesStr = indentMultilineStr(SEP.join(values), indent=INDENT * 2)
			valueRelatedStrs = [
				f"\tdecidingProp='{decidingProp}'",
				f"\tvalues={{\n{valuesStr}\n\t}}",
				f"\tvalue=None",
			]
		else:
			p = props[0]
			if len(props) > 1:
				valueStr = buildUnionSchema([pp.value for pp in props], None)
			else:
				valueStr = p.value
			valueStr = indentMultilineStr(valueStr, indent=INDENT, indentFirstLine=False)
			valueRelatedStrs = [
				f'\tdescription=MDStr({p.doc!r})',
				f"\tvalue={valueStr}",
			]
		if props[0].optional:
			valueRelatedStrs.append(f"\toptional=True")
		if props[0].default is not None:
			valueRelatedStrs.append(f"\tdefault={props[0].default!r}")
		if props[0].deprecated:
			valueRelatedStrs.append(f"\tdeprecated=True")
		valueRelatedStr = SEP.join(valueRelatedStrs)

		if name.startswith(('<', "''")):
			doc = f'{name}: {doc}'
			name = 'Anything'
		else:
			name = f'"{name}"'
		propStrings.append(
			f'PropertySchema(\n'
			f'\tname={name},\n'
			f'{valueRelatedStr}\n'
			f')'
		)
	return doc, propStrings


@schemaHandler('bool')
@schemaHandler('boolean')
def handleBoolSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonBoolSchema({docStr})"


@schemaHandler('int')
def handleIntSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonIntSchema({docStr})"


@schemaHandler('double')
@schemaHandler('float')
def handleFloatSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonFloatSchema({docStr})"


RES_LOC_MATCHER_1 = re.compile(r'\[\[[^]\n]*values#(\w+)')
RES_LOC_MATCHER_2 = re.compile(r'(\w+) ids?]]')

NBT_MATCHER_1 = re.compile(r'(?<!{{)nbt')


@schemaHandler('string')
def handleStrSchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''

	docToAnalyze = doc if doc else parentDoc
	if docToAnalyze:
		docToAnalyze = docToAnalyze.lower()

		resLoc = None
		if resLocs := list(RES_LOC_MATCHER_1.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1).removesuffix('s')
		elif resLocs := list(RES_LOC_MATCHER_2.finditer(docToAnalyze)):
			resLoc = resLocs[0].group(1)
		if resLoc:
			return f"JsonResourceLocationSchema({resLoc!r}, {docStr!r})"

		if list(NBT_MATCHER_1.finditer(docToAnalyze)):
			return f"JsonStringSchema({docStr}type=MINECRAFT_NBT_COMPOUND_TAG)"

	return f"JsonStringSchema({docStr})"


@schemaHandler('list')
def handleArraySchema(linesStack: Stack[tuple[int, str]], depth: int, doc: Optional[str], parentDoc: Optional[str], forceOptional: bool) -> str:
	if linesStack:
		lineNo, line = linesStack.peek()
		if not line.startswith('*' * (depth + 1) + ' '):
			if line.startswith('*' * (depth + 1)):
				linesStack.pop()
				print(f"too many asterix at start of line {lineNo}: {line!r}")
				element = line
			else:
				element = None
		else:
			linesStack.pop()

			if (match := ELEMENT_PATTERN.match(line, depth + 1)) is not None:
				type_ = match.group(1)
				iDoc = match.group(2)
				handler = _schemaHandlers.get(type_)
				if handler is None:
					print(f"[ ] no handler for type_ at line {lineNo}: {line!r}, type_ = {type_!r}")
					element = line
				else:
					element = handler(linesStack, depth + 1, iDoc, doc, forceOptional)
			else:
				print(f"[ ] line {lineNo} didn't match element: {line!r}")
				element = line
	else:
		element = None

	if element is None:
		element = handleStrSchema(linesStack, depth + 1, doc, parentDoc, forceOptional)
	# element = indentMultilineStr(element, indent=INDENT, indentFirstLine=False)
	return f"JsonArraySchema(element={element})"


def processFile(srcPath: str, dstPath: str, name: str, imports: str, *, forceOptional: bool):
	with open(srcPath, 'r', encoding='utf-8') as f:
		text = f.read()
	newText = convert2(text, name, imports, forceOptional=forceOptional)
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
		dstPath = os.path.join(DST_FOLDER, pathPart).replace('\\', '/') + '.py'
		name = pathPart.replace('/', '_').upper()
		import_ = pathPart.replace('/', '.')
		imports.append(f'from {SCHEMA_IMPORT_PREFIX}.{import_} import {name}')
		allPaths.append((srcPath, dstPath, name))

	# imports = NL.join(imports)

	global CURRENT_FILE_PATH
	for i, (srcPath, dstPath, name) in enumerate(allPaths):
		CURRENT_FILE_PATH = srcPath
		# if i % 100 == 0:
		print(f"")
		print(f"processing file {i}, name = {name}, path = {srcPath}")
		print(f"==========================================================================")
		processFile(srcPath, dstPath, name, '', forceOptional=True)


run()
