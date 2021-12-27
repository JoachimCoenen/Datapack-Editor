from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, TypeVar, Type, Callable, NamedTuple, Iterable

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, buildSimpleAutoCompletionTree, choicesFromAutoCompletionTree
from Cat.utils.profiling import logError
from Cat.utils import HTMLStr, HTMLifyMarkDownSubSet, unescapeFromXml, escapeForXmlAttribute, CachedProperty
from model.pathUtils import FilePathTpl, loadTextFile, ZipFilePool


def isNamespaceValid(namespace: str) -> bool:
	pattern = r'[0-9a-z_.-]+'
	return re.fullmatch(pattern, namespace) is not None


@dataclass(order=False, eq=False, unsafe_hash=False, frozen=True)
class ResourceLocation:
	__slots__ = ('namespace', 'path', 'isTag')
	namespace: Optional[str]
	path: str
	isTag: bool

	def __post_init__(self):
		assert self.namespace is None or self.namespace.strip()

	@property
	def actualNamespace(self) -> str:
		return 'minecraft' if self.namespace is None else self.namespace

	@property
	def asString(self) -> str:
		"""
		ResourceLocation.fromString('end_rod').asString == 'end_rod'
		ResourceLocation.fromString('minecraft:end_rod').asString == 'minecraft:end_rod'
		:return: The pure string representation
		"""
		tag = '#' if self.isTag else ''
		if self.namespace is None:
			return f'{tag}{self.path}'
		else:
			return f'{tag}{self.namespace}:{self.path}'

	@property
	def asCompactString(self) -> str:
		"""
		Omits the 'minecraft:' namespace if possible.

			ResourceLocation.fromString('end_rod').asString == 'end_rod'
			ResourceLocation.fromString('minecraft:end_rod').asString == 'end_rod'
		"""
		tag = '#' if self.isTag else ''
		namespace = self.namespace
		if namespace is None or namespace == 'minecraft':
			return f'{tag}{self.path}'
		else:
			return f'{tag}{namespace}:{self.path}'

	@property
	def asQualifiedString(self) -> str:
		"""
		Always the prepends the namespace, even if it could be omited.

			ResourceLocation.fromString('end_rod').asString == 'minecraft:end_rod'
			ResourceLocation.fromString('minecraft:end_rod').asString == 'minecraft:end_rod'
		"""
		tag = '#' if self.isTag else ''
		return f'{tag}{self.actualNamespace}:{self.path}'

	@classmethod
	def fromString(cls, value: str) -> ResourceLocation:
		namespace, _, path = value.partition(':')
		isTag = namespace.startswith('#')
		if isTag:
			namespace = namespace[1:]
		if not _:
			path = namespace
			namespace = None
		return cls(namespace, path, isTag)

	@property
	def _asTuple(self) -> tuple[bool, str, str]:
		return self.isTag, self.actualNamespace, self.path,

	def __eq__(self, other):
		if other.__class__ is self.__class__:
			return self._asTuple == other._asTuple
		return NotImplemented

	def __lt__(self, other):
		if other.__class__ is self.__class__:
			return self._asTuple < other._asTuple
		return NotImplemented

	def __le__(self, other):
		if other.__class__ is self.__class__:
			return self._asTuple <= other._asTuple
		return NotImplemented

	def __gt__(self, other):
		if other.__class__ is self.__class__:
			return self._asTuple > other._asTuple
		return NotImplemented

	def __ge__(self, other):
		if other.__class__ is self.__class__:
			return self._asTuple >= other._asTuple
		return NotImplemented

	def __hash__(self):
		return hash(self._asTuple)


@dataclass
class MetaInfo:
	filePath: FilePathTpl = FilePathTpl(('', ''))
	resourceLocation: ResourceLocation = ResourceLocation(None, '', False)


_TMetaInfo = TypeVar('_TMetaInfo', bound=MetaInfo)


class FunctionMeta(MetaInfo):

	@CachedProperty
	def documentation(self) -> HTMLStr:
		"""
		TODO: add documentation for Formatting of MCFunction Documentation
		Special parameters:
			Desc: a short version of the description
			Called by: a comma-separated list of other functions that call this function
		:return:
		"""
		lines: list[str] = []
		try:
			with ZipFilePool() as pool:
				file = loadTextFile(self.filePath, pool)
				lines = file.splitlines()
		except OSError as e:
			logError(e)

		doc = ''
		whiteSpaces = 999  # way to many
		for line in lines:
			if not line.startswith('#'):
				break

			# remove '#':
			line = line[1:]
			# remove leading whiteSpaces:
			line2 = line.lstrip()
			if line2:
				whiteSpaces = min(whiteSpaces, len(line) - len(line2))
				line2 = line[whiteSpaces:]
			line = line2
			del line2

			# handle special parameters:
			if line.startswith('Desc:'):
				line = '<b>Description:</b>' + line[len('Desc:'):] + '\n'
			elif line.startswith('Called by:'):
				line2 = line[len('Called by:'):]
				functions = line2.split(',')

				line = '<b>Called by:</b><ul>'
				for f in functions:
					f = f.strip()
					f = unescapeFromXml(f)
					f = escapeForXmlAttribute(f)
					line += f'\n\t<li><a href="@dpe.function:{f}">`{f}`</a></li>'
				line += '\n</ul>'
			doc += f'\n{line}'

		return HTMLifyMarkDownSubSet(doc)


def buildMetaInfo(cls: Type[_TMetaInfo], filePath: FilePathTpl, resourceLocation: ResourceLocation) -> _TMetaInfo:
	return cls(filePath, resourceLocation)


def buildFunctionMeta(filePath: FilePathTpl, resourceLocation: ResourceLocation) -> FunctionMeta:
	return buildMetaInfo(FunctionMeta, filePath, resourceLocation)


class EntryHandlerInfo(NamedTuple):
	folder: str
	extension: str
	isTag: bool
	buildMetaInfo: Callable[[FilePathTpl, ResourceLocation], None]


def collectAllEntries(files: list[FilePathTpl], handlers: list[EntryHandlerInfo]) -> None:
	handlersDict: dict[tuple[str, str], EntryHandlerInfo] = {(handler.folder, handler.extension): handler for handler in handlers}

	for fullPath in files:
		dpPath, filePath = fullPath
		if filePath.startswith('data/'):
			filePath = filePath.removeprefix('data/')
		else:
			continue
		namespace, _, path = filePath.partition('/')

		extIndex = path.rfind('.')
		if extIndex >= 0:
			extension = path[extIndex:]
		else:
			extension = ''

		prefix = ''
		rest = path
		while rest:
			p, _, rest = rest.partition('/')
			prefix += p + '/'
			handler = handlersDict.get((prefix, extension))
			if handler is None:
				continue
			rest = rest[:len(rest) - len(extension)]
			resourceLocation = ResourceLocation(namespace, rest, handler.isTag)
			handler.buildMetaInfo(fullPath, resourceLocation)


def autoCompletionTreeForResourceLocations(locations: Iterable[ResourceLocation]) -> AutoCompletionTree:
	locationStrs = [l.asString for l in locations]
	tree = buildSimpleAutoCompletionTree(locationStrs, (':', '/'))
	return tree


def choicesFromResourceLocations(text: str, locations: Iterable[ResourceLocation]) -> list[str]:
	tree = autoCompletionTreeForResourceLocations(locations)
	return choicesFromAutoCompletionTree(tree, text)
