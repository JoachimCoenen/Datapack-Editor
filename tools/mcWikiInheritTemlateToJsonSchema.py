import os
import re
from typing import Optional, Callable, NamedTuple, Union

from Cat.extensions import processRecursively
from Cat.utils import openOrCreate
from Cat.utils.collections_ import AddToDictDecorator, Stack, OrderedMultiDict
from Cat.utils.formatters import indentMultilineStr
from Cat.utils.typing_ import replace_tuple

# BOOL_REPLACE = \
# """\tPropertySchema(
# \t\tname="\\1",
# \t\tdescription=MDStr("\\2"),
# \t\tvalue=JsonBoolSchema()
# \t),"""
#
#
# INT_REPLACE = \
# """\tPropertySchema(
# \t\tname="\\1",
# \t\tdescription=MDStr("\\2"),
# \t\tvalue=JsonIntSchema()
# \t),"""
#
#
# FLOAT_REPLACE = \
# """\tPropertySchema(
# \t\tname="\\1",
# \t\tdescription=MDStr("\\2"),
# \t\tvalue=JsonFloatSchema()
# \t),"""
#
#
# STRING_REPLACE = \
# """\tPropertySchema(
# \t\tname="\\1",
# \t\tdescription=MDStr("\\2"),
# \t\tvalue=JsonStringSchema()
# \t),"""
#
#
# COMPOUND_1_REPLACE = \
# """\tPropertySchema(
# \t\tname="\\1",
# \t\tdescription=MDStr("\\2"),
# \t\tvalue=JsonObjectSchema(properties=["""
#
#
# def COMPOUND_REPLACE(match: re.Match) -> str:
# 	return f"""\tPropertySchema(
# \t\tname="{match.group(1)}",
# \t\tdescription=MDStr("{match.group(2)}"),
# \t\tvalue=ADVANCEMENT_{match.group(3).replace('/', '_').upper()}
# \t),"""
#
#
# def convert(text: str, name: str):
# 	original = text
#
# 	text = extractOnlyinclude(text)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|boolean\|(\w+)}}(?: ?)(.*)',
# 		BOOL_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|int\|(\w+)}}(?: ?)(.*)',
# 		INT_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|(?:double|float)\|(\w+)}}(?: ?)(.*)',
# 		FLOAT_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|string\|(\w+)}}(?: ?)(.*)',
# 		STRING_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|compound\|(\w+)}}: ?(.*)\n\*\*\*+ {{nbt inherit/([\w/]+)\|indent=\*+}}',
# 		COMPOUND_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = re.sub(
# 		r'\*\* {{[nN]bt\|compound\|(\w+)}}(?: ?)(.*)',
# 		COMPOUND_1_REPLACE,
# 		text,
# 		flags=re.MULTILINE
# 	)
#
# 	text = (
# 		f"{name} = JsonObjectSchema( properties=[\n"
# 		f"{text}\n"
# 		f"])\n")
# 	text = addImports(text)
# 	return text
#
#
# def handleLines(linesStack: Stack[str], depth: int) -> tuple[Optional[str], Optional[str]]:
# 	"""
# 	:param linesStack:
# 	:param depth:
# 	:return: (generated str, name of prop (if any))
# 	"""
# 	if not linesStack.isEmpty():
# 		line = linesStack.peek()
# 		if not line.startswith('*'*depth + ' {{'):
# 			if line.startswith('*' * depth):
# 				linesStack.pop()
# 				print(f"too many asterix at start of line: {line!r}")
# 				return line, None
# 			return None, None
# 		else:
# 			linesStack.pop()
# 		# if not line.startswith('*'*depth + ' {{nbt|'):
# 		# if not line.startswith(' {{nbt|', depth):
# 		# 	return line
# 		if (match := PROPERTY_PATTERN.match(line, depth)) is not None:
# 			type_ = match.group(1)
# 			name = match.group(2)
# 			doc = match.group(3)
#
# 			handler = _schemaHandlers.get(type_)
# 			if handler is None:
# 				print(f"[ ] no handler for type_ = {type_!r}")
# 				return line, name
# 			schema = handler(linesStack, depth + 0, None)
# 			return jsonPropertySchema(name, doc, schema), name
#
# 		elif (match := INHERIT_PATTERN.match(line, depth)) is not None:
# 			path = match.group(1)
# 			const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"
# 			return f'*{const}.properties', None
#
# 		elif (match := ELEMENT_PATTERN.match(line, depth)) is not None:
# 			type_ = match.group(1)
# 			doc = match.group(2)
# 			handler = _schemaHandlers.get(type_)
# 			if handler is None:
# 				print(f"[ ] no handler for type_ = {type_!r}")
# 				return line, None
# 			return handler(linesStack, depth + 0, doc), None
#
# 		# elif (match := DEPENDANT_PROP_PATTERN.match(line, depth)) is not None:
# 		# 	name = match.group(1)
# 		# 	handler = _schemaHandlers.get(type_)
# 		# 	if handler is None:
# 		# 		print(f"[ ] no handler for type_ = {type_!r}")
# 		# 		return line, None
# 		# 	return handler(linesStack, depth + 0, doc), None
#
# 		else:
# 			print(f"[ ] line didn't match property: {line!r}")
# 			return line, None
# 	return None, None
#
#
# def jsonPropertySchema(name: str, doc: str, value: str) -> str:
# 	if name.startswith('<'):
# 		doc = f'{name}: {doc}'
# 		name = 'Anything'
# 	else:
# 		name = f'"{name}"'
# 	value = indentMultilineStr(value, indent=INDENT, indentFirstLine=False)
# 	return (
# 		f'PropertySchema(\n'
# 		f'\tname={name},\n'
# 		f'\tdescription=MDStr({doc!r}),\n'
# 		f'\tvalue={value}\n'
# 		f')')


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


def addImports(text):
	return (
		f"from Cat.utils import Anything\n"
		f"from model.json.core import *\n"
		f"from model.utils import MDStr\n"
		f"\n"
		f"{text}\n")


def convert2(text: str, name: str, *, forceOptional: bool) -> str:
	original = text
	text = extractOnlyinclude(text)
	lines = text.splitlines()
	inesStack = Stack(list(reversed(lines)))
	schema = handleObjectSchema(inesStack, 1, None, forceOptional)
	schema = f"{name} = {schema}\n"
	return addImports(schema)


TYPE_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)}})'
PROPERTY_MARKER = r'(?:{{[Nn][Bb][Tt]\|(\w+)\|([\w<: >\']+)}})'
PROPERTY_PATTERN = re.compile(rf' {PROPERTY_MARKER}(?:: ?)?(.*)')
ELEMENT_PATTERN = re.compile(rf' {TYPE_MARKER}(?:: ?)?(.*)')

PROPERTY_UNION_PATTERN = re.compile(rf' ({TYPE_MARKER}*){PROPERTY_MARKER}(?:: ?)?(.*)')
UNION_SPLIT_PATTERN = re.compile(rf'({TYPE_MARKER}*){TYPE_MARKER}')

INHERIT_PATTERN = re.compile(r' {{[Nn][Bb][Tt] inherit/([\w/]+)\|indent=\*+}}')
DEPENDANT_PROP_PATTERN = re.compile(r" '''(\w+)'''")


class Proptions(NamedTuple):
	name: str
	doc: str
	value: str
	depProp: Optional[tuple[str, str]]
	default: Optional[str]
	optional: bool
	deprecated: bool


def handleProp(line: str, linesStack: Stack[str], depth: int, depProp: Optional[tuple[str, str]], *, forceOptional: bool) -> Union[str, Proptions]:
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
				print(f"[ ] no handler for type_ = {type_!r}, depProp={depProp!r}")
				return line
			schema = handler(linesStack, depth + 0, doc if depProp is not None else None, forceOptional)
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
		const = f"ADVANCEMENT_{path.replace('/', '_').upper()}"
		if depProp is not None:
			print(f"[ ] can't use depProp with INHERIT: {line!r}, depProp={depProp!r}")
		return f'*{const}.properties'

	else:
		print(f"[ ] line didn't match property: {line!r}, depProp={depProp!r}")
		return line


def handleProperties(linesStack: Stack[str], depth: int, depProp: Optional[tuple[str, str]], *, forceOptional: bool) -> list[Union[str, Proptions]]:
	properties = []
	lastProp: Optional[Proptions] = None
	while not linesStack.isEmpty():
		line = linesStack.peek()
		if not line.startswith('*' * depth + ' '):
			if line.startswith('*' * depth):
				linesStack.pop()
				print(f"too many asterisks at start of line: {line!r}")
				properties.append(line)
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
			properties.extend(handleProperties(linesStack, depth + 1, (lastProp.name, name), forceOptional=forceOptional))
		else:
			prop = handleProp(line, linesStack, depth, depProp, forceOptional=forceOptional)
			if isinstance(prop, Proptions):
				lastProp = prop
			properties.append(prop)
	return properties


def buildUnionSchema(schemas: list[str], doc: Optional[str]) -> str:
	if len(schemas) == 1:
		schema = schemas[0]
	else:
		options = SEP.join(schemas)
		if doc is not None:
			propsStr = indentMultilineStr(options, indent=INDENT * 2)
			schema = (
				f"JsonUnionSchema(\n"
				f"\tdescription=MDStr({doc!r}),\n"
				f"\toptions=[\n"
				f"{propsStr}\n"
				f"\t]\n"
				f")"
			)
		else:
			propsStr = indentMultilineStr(options, indent=INDENT * 1)
			schema = f"JsonUnionSchema(options=[\n{propsStr}\n])"
	return schema


_schemaHandlers: dict[str, Callable[[Stack[str], int, Optional[str], bool], str]] = {}
schemaHandler = AddToDictDecorator(_schemaHandlers)


@schemaHandler('compound')
def handleObjectSchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	properties = handleProperties(linesStack, depth + 1, None, forceOptional=forceOptional)
	propStrings = []
	byName: OrderedMultiDict[str, Proptions] = OrderedMultiDict()
	for prop in properties:
		if isinstance(prop, str):
			propStrings.append(f'# {prop}')
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

			valuesStr = indentMultilineStr(SEP.join(values), indent=INDENT*2)
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
			valueRelatedStrs.append(f"\tdefault={p.default!r}")
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
			f')')

	if doc:
		propertiesStr = f"[\n{indentMultilineStr(SEP.join(propStrings), indent=INDENT*2)}\n{INDENT}]"
		return (
			f"JsonObjectSchema(\n"
			f'\tdescription=MDStr({doc!r}),\n'
			f"\tproperties={propertiesStr}\n"
			f")")
	else:
		propertiesStr = f"[\n{indentMultilineStr(SEP.join(propStrings), indent=INDENT)}\n]"
		return f"JsonObjectSchema(properties={propertiesStr})"


@schemaHandler('bool')
@schemaHandler('boolean')
def handleBoolSchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonBoolSchema({docStr})"


@schemaHandler('int')
def handleIntSchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonIntSchema({docStr})"


@schemaHandler('double')
@schemaHandler('float')
def handleFloatSchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonFloatSchema({docStr})"


@schemaHandler('string')
def handleStrSchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	docStr = f'description=MDStr({doc!r})' if doc else ''
	return f"JsonStringSchema({docStr})"


@schemaHandler('list')
def handleArraySchema(linesStack: Stack[str], depth: int, doc: Optional[str], forceOptional: bool) -> str:
	if not linesStack.isEmpty():
		line = linesStack.peek()
		if not line.startswith('*' * (depth + 1) + ' '):
			if line.startswith('*' * (depth + 1)):
				linesStack.pop()
				print(f"too many asterix at start of line: {line!r}")
				element = line
			else:
				element = None
		else:
			linesStack.pop()

			if (match := ELEMENT_PATTERN.match(line, depth + 1)) is not None:
				type_ = match.group(1)
				doc = match.group(2)
				handler = _schemaHandlers.get(type_)
				if handler is None:
					print(f"[ ] no handler for type_ = {type_!r}")
					element = line
				else:
					element = handler(linesStack, depth + 1, doc, forceOptional)
			else:
				print(f"[ ] line didn't match element: {line!r}")
				element = line
	else:
		element = None

	if element is None:
		element = handleStrSchema(linesStack, depth + 1, doc, forceOptional)
	# element = indentMultilineStr(element, indent=INDENT, indentFirstLine=False)
	return f"JsonArraySchema(element={element})"


def processFile(path: str, *, forceOptional: bool):
	path = path.replace('\\', '/')
	pathPart = path.removeprefix(SRC_FOLDER).rpartition('.')[0]
	dstPath = os.path.join(DST_FOLDER, pathPart).replace('\\', '/') + '.py'
	name = pathPart.replace('/', '_').upper()
	with open(path, 'r', encoding='utf-8') as f:
		text = f.read()
	newText = convert2(text, name, forceOptional=forceOptional)
	with openOrCreate(dstPath, 'w', encoding='utf-8') as f:
		f.write(newText)


testData = """
<div class="treeview"><onlyinclude>
** {{nbt|boolean|bypasses_armor}}: Checks if the damage bypassed the armor of the player (suffocation damage predominantly).
** {{nbt|boolean|bypasses_invulnerability}}: Checks if the damage bypassed the invulnerability status of the player (void or {{cmd|kill}} damage). 
** {{nbt|boolean|bypasses_magic}}: Checks if the damage was caused by starvation.
** {{nbt|compound|direct_entity}}: The entity that was the direct cause of the damage.
*** {{nbt inherit/conditions/entity|indent=***}}
** {{nbt|boolean|is_explosion}}: Checks if the damage originated from an explosion.
** {{nbt|boolean|is_fire}}: Checks if the damage originated from fire.
** {{nbt|boolean|is_magic}}: Checks if the damage originated from magic.
** {{nbt|boolean|is_projectile}}: Checks if the damage originated from a projectile.
** {{nbt|boolean|is_lightning}}: Checks if the damage originated from lightning.
** {{nbt|compound|source_entity}}: Checks the entity that was the source of the damage (for example: The skeleton that shot the arrow).
*** {{nbt inherit/conditions/entity|indent=***}}
</onlyinclude></div><noinclude>
[[Category:Top-level data pages]]
</noinclude>
"""

# print(convert(testData))


SRC_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/"
DST_FOLDER = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWikiCompiled2/"
FOLDER_FILTER = "**"


def run():
	allFiles: list[str] = []

	def addToAllFiles(path: str):
		if path.endswith('.wiki'):
			allFiles.append(path)

	processRecursively(SRC_FOLDER, FOLDER_FILTER, addToAllFiles)

	print(f"There are {len(allFiles)} files to edit...")

	for i, path in enumerate(allFiles):
		if i % 100 == 0:
			print(f"processing file {i}")
		processFile(path, forceOptional=True)


run()
