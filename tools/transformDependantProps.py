import re

from cat.utils import openOrCreate

EXAMPLE_MATCHER_1 = re.compile(r'<div class="collapsible collapsed collapsetoggle-inline"((?!</syntaxhighlight>).*\n)+</syntaxhighlight></div></div>\n')
DEPENDANT_PROP_MATCHER_1 = re.compile(r'=== minecraft:(\w+) ===\n(.+)\n(?:<div class="treeview">\n((?:(?!</div>).+\n)+)</div>)?')


def removeExamples(text: str) -> str:
	return EXAMPLE_MATCHER_1.sub('', text)


def transformDependantProps(text: str, level: int) -> list[str]:
	lines = []
	indent = '*' * level
	matches = list(DEPENDANT_PROP_MATCHER_1.finditer(text))
	for match in matches:
		name = match.group(1)
		doc = match.group(2)
		contents = match.group(3) or ''
		lines.append(f"{indent} '''{name}'''&mdash;{doc}")
		contentLines = contents.splitlines(keepends=False)
		if contentLines and contentLines[0].startswith('* {{nbt|compound|'):
			for contentLine in contentLines[1:]:
				lines.append(indent + contentLine.removeprefix('*'))
		else:  # fallback
			for contentLine in contentLines:
				lines.append(indent + contentLine)
	return lines


def transformDependantPropsInFile(srcPath: str, *, level: int) -> list[str]:
	with open(srcPath, 'r', encoding='utf-8') as f:
		text = f.read()
	text2 = removeExamples(text)
	lines = transformDependantProps(text2, level=level)
	return lines


def processFile(srcPath: str, dstPath: str):
	with open(srcPath, 'r', encoding='utf-8') as f:
		text = f.read()
	text2 = removeExamples(text)
	lines = transformDependantProps(text2, level=3)
	with openOrCreate(dstPath, 'w', encoding='utf-8') as f:
		f.write('\n'.join(lines))


SRC_FILE: str = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/Advancement/List of triggers.wiki2"
DST_FILE = "D:/Programming/Python/MinecraftDataPackEditor/tools/mcWiki/Advancement/List of triggers.wiki"


CURRENT_FILE_PATH: str = ""


def run():
	allFiles: list[str] = []

	print(f"There are {len(allFiles)} files to edit...")

	# imports = NL.join(imports)

	name = SRC_FILE.rpartition('/')[2]
	# if i % 100 == 0:
	print(f"")
	print(f"processing file {0}, name = {name}")
	print(f"path      = {SRC_FILE}")
	print(f"save path = {DST_FILE}")
	processFile(SRC_FILE, DST_FILE)
	print(f"==========================================================================")


if __name__ == '__main__':
	run()
