from dataclasses import dataclass
from typing import Optional, TypeVar, Type, Callable, NamedTuple

from Cat.Serializable import RegisterContainer, Serialized, SerializableContainer, ComputedCached
from Cat.utils.profiling import logError
from Cat.utils import HTMLStr, HTMLifyMarkDownSubSet, unescapeFromXml, escapeForXmlAttribute
from model.pathUtils import FilePathTpl, loadTextFile, ZipFilePool


@dataclass(order=True, unsafe_hash=True, frozen=True)
class ResourceLocation:
	__slots__ = ('namespace', 'path', 'isTag')
	namespace: Optional[str]
	path: str
	isTag: bool

	@property
	def asString(self) -> str:
		tag = '#' if self.isTag else ''
		if self.namespace is not None:
			return f'{tag}{self.namespace}:{self.path}'
		else:
			return f'{tag}minecraft:{self.path}'

	@classmethod
	def fromString(cls, value: str):
		namespace, _, path = value.partition(':')
		isTag = namespace.startswith('#')
		if isTag:
			namespace = namespace[1:]
		if not _:
			path = namespace
			namespace = None
		return cls(namespace, path, isTag)


@RegisterContainer
class MetaInfo(SerializableContainer):
	__slots__ = ()
	filePath: FilePathTpl = Serialized(default=FilePathTpl(('', '')))
	resourceLocation: ResourceLocation = Serialized(default=ResourceLocation(None, '', False))


_TMetaInfo = TypeVar('_TMetaInfo', bound=MetaInfo)

@RegisterContainer
class FunctionMeta(MetaInfo):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		self.documentation: HTMLStr = HTMLStr('')

	@ComputedCached()
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
	return cls.create(filePath=filePath, resourceLocation=resourceLocation)


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
