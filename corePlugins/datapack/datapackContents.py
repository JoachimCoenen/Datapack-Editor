from __future__ import annotations
import re
from dataclasses import dataclass, field, replace
from itertools import chain
from typing import Optional, TypeVar, Type, Iterable, Mapping, Collection

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, buildSimpleAutoCompletionTree, choicesFromAutoCompletionTree
from Cat.utils.profiling import logError
from Cat.utils import unescapeFromXml, escapeForXmlAttribute, CachedProperty
from base.model.aspect import AspectType
from base.model.project.index import Index, IndexBundle
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import parse
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePathTpl, loadBinaryFile, loadTextFile, ZipFilePool
from base.model.project.project import IndexBundleAspect
from base.model.utils import MDStr, Span

DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


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
	def isMCNamespace(self) -> bool:
		return self.namespace is None or self.namespace == 'minecraft'

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
		Always prepends the namespace, even if it could be omitted.

			ResourceLocation.fromString('end_rod').asString == 'minecraft:end_rod'
			ResourceLocation.fromString('minecraft:end_rod').asString == 'minecraft:end_rod'
		"""
		tag = '#' if self.isTag else ''
		return f'{tag}{self.actualNamespace}:{self.path}'

	@classmethod
	def splitString(cls, value: str) -> tuple[Optional[str], str, bool]:
		namespace, _, path = value.partition(':')
		isTag = namespace.startswith('#')
		if isTag:
			namespace = namespace[1:]
		if not _:
			path = namespace
			namespace = None
		return namespace, path, isTag

	@classmethod
	def fromString(cls, value: str) -> ResourceLocation:
		return cls(*cls.splitString(value))

	@property
	def _asTuple(self) -> tuple[bool, str, str]:
		return self.isTag, self.actualNamespace, self.path,

	def __eq__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple == other._asTuple
		return NotImplemented

	def __lt__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple < other._asTuple
		return NotImplemented

	def __le__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple <= other._asTuple
		return NotImplemented

	def __gt__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple > other._asTuple
		return NotImplemented

	def __ge__(self, other):
		if hasattr(other, '_asTuple'):
			return self._asTuple >= other._asTuple
		return NotImplemented

	def __hash__(self):
		return hash(self._asTuple)


@dataclass(slots=True)
class ResourceLocationSchema(Schema):
	name: str

	def asString(self) -> str:
		return self.name


@dataclass(order=False, eq=False, unsafe_hash=False, frozen=True)
class ResourceLocationNode(Node['ResourceLocationNode', ResourceLocationSchema], ResourceLocation):
	# TODO: maybe move to different module, or move ResourceLocationContext implementations?

	isValid: bool = field(default=True, compare=False, kw_only=True)
	pointsToFile: bool = field(default=False, compare=False, kw_only=True)

	@classmethod
	def fromString(cls, value: bytes, span: Span, schema: Optional[ResourceLocationSchema]) -> ResourceLocationNode:
		assert isinstance(value, bytes)
		value = bytesToStr(value)
		namespace, path, isTag = cls.splitString(value)
		return cls(namespace, path, isTag, span, schema)

	@property
	def children(self) -> Collection[ResourceLocationNode]:
		return ()


	__eq__ = ResourceLocation.__eq__
	__lt__ = ResourceLocation.__lt__
	__le__ = ResourceLocation.__le__
	__gt__ = ResourceLocation.__gt__
	__ge__ = ResourceLocation.__ge__
	__hash__ = ResourceLocation.__hash__


@dataclass
class MetaInfo:
	filePath: FilePathTpl = FilePathTpl(('', ''))
	# resourceLocation: ResourceLocation = ResourceLocation(None, '', False)

	@property
	def documentation(self) -> MDStr:
		return MDStr('')


_TMetaInfo = TypeVar('_TMetaInfo', bound=MetaInfo)


@dataclass
class FunctionMeta(MetaInfo):

	@CachedProperty
	def documentation(self) -> MDStr:
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

		doc = []
		whiteSpaces = 999  # way too many
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
				doc.append('<b>Description:</b>' + line[len('Desc:'):])
			elif line.startswith('Called by:'):
				line2 = line[len('Called by:'):]
				functions = line2.split(',')

				doc.append('<b>Called by:</b>')
				for f in functions:
					f = f.strip()
					f = unescapeFromXml(f)
					f = escapeForXmlAttribute(f)
					doc.append(f'* [`{f}`](@dpe.function:{f})')
			else:
				doc.append(line)

		return MDStr('\n'.join(doc))


@dataclass
class JsonMeta(MetaInfo):
	schemaId: str = ''

	@CachedProperty
	def documentation(self) -> MDStr:
		try:
			with ZipFilePool() as pool:
				file = loadBinaryFile(self.filePath, pool)
		except OSError as e:
			logError(e)
			return MDStr('')

		from corePlugins.json import JSON_ID
		json, errors = parse(file, filePath=self.filePath, language=JSON_ID, schema=None, allowMultilineStr=True)

		from corePlugins.json.core import JsonObject, JsonString
		if json is not None and isinstance(json, JsonObject):
			description = json.data.get('description')
			if description is not None and isinstance(description.value, JsonString):
				return MDStr(description.value.data)

		return MDStr('')


@dataclass
class NbtMeta(MetaInfo):
	pass


@dataclass
class TagInfos(IndexBundle):
	blocks: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	entity_types: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	fluids: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	functions: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	game_events: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	items: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))


@dataclass
class WorldGenInfos(IndexBundle):
	biome: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	configured_carver: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	configured_feature: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	configured_structure_feature: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	configured_surface_builder: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	noise_settings: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	processor_list: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	template_pool: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))


@dataclass
class DatapackContents(IndexBundleAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_CONTENTS_TYPE

	advancements: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	functions: Index[ResourceLocation, FunctionMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	item_modifiers: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	loot_tables: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	predicates: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	recipes: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	structures: Index[ResourceLocation, NbtMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	tags: TagInfos = field(default_factory=TagInfos, init=False, metadata=dict(dpe=dict(isIndex=True)))
	dimension: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	dimension_type: Index[ResourceLocation, JsonMeta] = field(default_factory=Index, init=False, metadata=dict(dpe=dict(isIndex=True)))
	worldGen: WorldGenInfos = field(default_factory=WorldGenInfos, init=False, metadata=dict(dpe=dict(isIndex=True)))


def createMetaInfo(cls: Type[_TMetaInfo], filePath: FilePathTpl) -> _TMetaInfo:
	return cls(filePath)


def buildDefaultMeta(filePath: FilePathTpl) -> _TMetaInfo:
	return createMetaInfo(MetaInfo, filePath)


def buildFunctionMeta(filePath: FilePathTpl) -> FunctionMeta:
	return createMetaInfo(FunctionMeta, filePath)


def buildJsonMeta(filePath: FilePathTpl, *, schemaId: str) -> JsonMeta:
	info = createMetaInfo(JsonMeta, filePath)
	info.schemaId = schemaId
	return info


def buildNbtMeta(filePath: FilePathTpl) -> NbtMeta:
	return createMetaInfo(NbtMeta, filePath)


NAME_SPACE_VAR = '${namespace}'

NAME_SPACE_CAPTURE_GROUP = r'(?P<namespace>\w+)'
"""used to mark the namespace folder in EntryHandlerInfo.folder"""


@dataclass(frozen=True)
class DefaultFileInfo:
	name: str
	namespace: Optional[str]
	contents: str


@dataclass(frozen=True)
class GenerationInfo:
	initialFiles: list[DefaultFileInfo] = field(default_factory=list)


@dataclass(frozen=True)
class EntryHandlerInfo:
	folder: str = field(kw_only=True)
	folderPattern: re.Pattern[str] = field(init=False)
	extension: str = field(kw_only=True)
	isTag: bool = field(kw_only=True)
	includeSubdirs: bool = field(kw_only=True)
	buildMetaInfo: Callable[[FilePathTpl], MetaInfo] = field(kw_only=True)
	getIndex: Callable[[Project], Index[ResourceLocation, MetaInfo]] | None = field(kw_only=True)
	generation: GenerationInfo = field(default_factory=GenerationInfo, kw_only=True)

	def __post_init__(self):
		object.__setattr__(self, 'folderPattern', folderPatternFromPath(self.folder))


def folderPatternFromPath(path: str) -> re.Pattern:
	path2 = path.replace(NAME_SPACE_VAR, NAME_SPACE_CAPTURE_GROUP)
	return re.compile(path2)


EntryHandlers = OrderedDict[str, list[EntryHandlerInfo]]


def buildEntryHandlers(handlers: list[EntryHandlerInfo]) -> EntryHandlers:
	result = OrderedDict()
	for handler in handlers:
		result.setdefault(handler.folder, []).append(handler)
	return result


# def getEntryHandlerForFile_OLD(fullPath: FilePathTpl, handlers: EntryHandlers) -> Optional[tuple[ResourceLocation, EntryHandlerInfo]]:
# 	dpPath, filePath = fullPath
# 	if filePath.startswith('data/'):
# 		filePath = filePath.removeprefix('data/')
# 		namespace, _, path = filePath.partition('/')
# 	else:
# 		namespace = ''
# 		path = filePath
#
# 	extIndex = path.rfind('.')
# 	if extIndex >= 0:
# 		extension = path[extIndex:]
# 	else:
# 		extension = ''
# 	_, _, name = path.partition('/')
#
# 	prefix = ''
# 	rest = path
# 	while True:
# 		p, _, rest = rest.partition('/')
# 		prefix += p + '/'
# 		handler = handlers.get(EntryHandlerKey(prefix, extension))
# 		if handler is None:
# 			handler = handlers.get(EntryHandlerKey(prefix, name))
# 		if handler is not None:
# 			rest = rest[:len(rest) - len(extension)]
# 			resourceLocation = ResourceLocation(namespace, rest, handler.isTag)
# 			return resourceLocation, handler
# 		if not rest:
# 			break
# 	return None


def getEntryHandlerForFile(fullPath: FilePathTpl, handlersDict: EntryHandlers) -> tuple[ResourceLocation | None, EntryHandlerInfo] | None:
	dpPath, filePath = fullPath
	path, sep, name = filePath.rpartition('/')
	nsHandlers = getEntryHandlersForFolder((dpPath, path + sep), handlersDict)
	return getEntryHandlerForFile2(fullPath, nsHandlers)


def getEntryHandlerForFile2(fullPath: FilePathTpl, nsHandlers: list[tuple[str | None, EntryHandlerInfo, str]]) -> tuple[ResourceLocation | None, EntryHandlerInfo] | None:
	dpPath, filePath = fullPath
	name = filePath.rpartition('/')[2].partition('.')[0]

	for namespace, handler, rest in nsHandlers:
		if not filePath.endswith(handler.extension):
			continue
		resLoc = ResourceLocation(namespace, rest + name, handler.isTag) if namespace is not None else None
		return resLoc, handler

	return None


def getEntryHandlersForFolder(fullPath: FilePathTpl, handlersDict: EntryHandlers) -> list[tuple[str | None, EntryHandlerInfo, str]]:
	"""
	:param fullPath:
	:param handlersDict:
	:return: list[(namespace | None, EntryHandlerInfo, subdirectory)]
	"""
	dpPath, filePath = fullPath if isinstance(fullPath, tuple) else (fullPath, '')
	if filePath.startswith('/') and len(filePath) > 1:
		filePath = filePath[1:]
	if not filePath.endswith('/'):
		filePath = filePath + '/'

	result = []
	for pattern, handlers in handlersDict.items():
		match = folderPatternFromPath(pattern).match(filePath)
		if match is None:
			continue

		namespace = match.groupdict().get('namespace')
		rest = filePath[match.end():]

		for handler in handlers:
			if handler.includeSubdirs or not rest:
				result.append((namespace, handler, rest))

	return result


def getMetaInfo(fullPath: FilePathTpl, handlers: EntryHandlers) -> MetaInfo | None:
	if isinstance(fullPath, tuple):
		if (resLocHandler := getEntryHandlerForFile(fullPath, handlers)) is not None:
			rl, handler = resLocHandler
			metaInfo = handler.buildMetaInfo(fullPath)
			return metaInfo


def collectAllEntries(files: list[FilePathTpl], handlers: EntryHandlers, project: Project) -> None:
	for fullPath in files:
		if (resLocHandler := getEntryHandlerForFile(fullPath, handlers)) is not None:
			resLoc, handler = resLocHandler
			if resLoc is None:
				continue
			metaInfo = handler.buildMetaInfo(fullPath)
			if handler.getIndex is not None:
				handler.getIndex(project).add(resLoc, fullPath, metaInfo)


def autoCompletionTreeForResourceLocations(locations: Iterable[ResourceLocation]) -> AutoCompletionTree:
	locationStrs = [l.asString for l in locations]
	mcLocationStrs = [l.asCompactString for l in locations if l.isMCNamespace]
	tree = buildSimpleAutoCompletionTree(chain(locationStrs, mcLocationStrs), (':', '/'))
	return tree


def choicesFromResourceLocations(text: str, locations: Iterable[ResourceLocation]) -> list[str]:
	tree = autoCompletionTreeForResourceLocations(locations)
	return choicesFromAutoCompletionTree(tree, text)


def containsResourceLocation(rl: ResourceLocation, container: Iterable[ResourceLocation]) -> bool:
	if rl.namespace == 'minecraft':
		rl = replace(rl, namespace=None)
	return rl in container
