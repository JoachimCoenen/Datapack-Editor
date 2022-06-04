from __future__ import annotations
import re
from dataclasses import dataclass, field, replace
from typing import Optional, TypeVar, Type, Callable, NamedTuple, Iterable, TYPE_CHECKING, Union, Mapping

from Cat.CatPythonGUI.GUI.codeEditor import AutoCompletionTree, buildSimpleAutoCompletionTree, choicesFromAutoCompletionTree
from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, SerializedPropertyBaseBase
from Cat.utils.collections_ import OrderedDict
from Cat.utils.profiling import logError
from Cat.utils import unescapeFromXml, escapeForXmlAttribute, CachedProperty, Deprecated
from model.parsing.bytesUtils import bytesToStr
from model.parsing.tree import Schema, Node
from model.pathUtils import FilePathTpl, loadTextFile, ZipFilePool
from model.utils import MDStr, Span


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


@dataclass
class ResourceLocationSchema(Schema):
	name: str

	def asString(self) -> str:
		return self.name


@dataclass(order=False, eq=False, unsafe_hash=False, frozen=True)
class ResourceLocationNode(Node['ResourceLocationNode', ResourceLocationSchema], ResourceLocation):
	# TODO: maybe move to different module, or move ResourceLocationContext implementations?

	@classmethod
	def fromString(cls, value: bytes, span: Span, schema: Optional[ResourceLocationSchema]) -> ResourceLocationNode:
		assert isinstance(value, bytes)
		value = bytesToStr(value)
		namespace, path, isTag = cls.splitString(value)
		return cls(namespace, path, isTag, span, schema)

	__eq__ = ResourceLocation.__eq__
	__lt__ = ResourceLocation.__lt__
	__le__ = ResourceLocation.__le__
	__gt__ = ResourceLocation.__gt__
	__ge__ = ResourceLocation.__ge__
	__hash__ = ResourceLocation.__hash__


@dataclass
class MetaInfo:
	filePath: FilePathTpl = FilePathTpl(('', ''))
	resourceLocation: ResourceLocation = ResourceLocation(None, '', False)

	@property
	def documentation(self) -> MDStr:
		return MDStr('')


_TMetaInfo = TypeVar('_TMetaInfo', bound=MetaInfo)


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
				file = loadTextFile(self.filePath, pool)
		except OSError as e:
			logError(e)
			return MDStr('')

		from model.json.parser import parseJsonStr
		json, errors = parseJsonStr(file, True, None)

		from model.json.core import JsonObject
		if json is not None and isinstance(json, JsonObject):
			description = json.data.get('description')
			from model.json.core import JsonString
			if description is not None and isinstance(description.value, JsonString):
				return MDStr(description.value.data)

		return MDStr('')


@dataclass
class NbtMeta(MetaInfo):
	pass


@RegisterContainer
class TagInfos(SerializableContainer):
	__slots__ = ()
	blocks: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	entity_types: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	fluids: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	functions: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	game_events: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	items: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)


@RegisterContainer
class WorldGenInfos(SerializableContainer):
	__slots__ = ()
	biome: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	configured_carver: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	configured_feature: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	configured_structure_feature: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	configured_surface_builder: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	noise_settings: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	processor_list: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	template_pool: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)


@RegisterContainer
class DatapackContents(SerializableContainer):
	__slots__ = ()
	advancements: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	functions: OrderedDict[ResourceLocation, FunctionMeta] = Serialized(default_factory=OrderedDict)
	item_modifiers: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	loot_tables: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	predicates: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	recipes: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	structures: OrderedDict[ResourceLocation, NbtMeta] = Serialized(default_factory=OrderedDict)
	tags: TagInfos = Serialized(default_factory=TagInfos)
	dimension: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	dimension_type: OrderedDict[ResourceLocation, JsonMeta] = Serialized(default_factory=OrderedDict)
	worldGen: WorldGenInfos = Serialized(default_factory=WorldGenInfos)
	# if TYPE_CHECKING:
	# 	advancementsProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	functionsProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, FunctionMeta]]] = Serialized()
	# 	item_modifiersProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	loot_tablesProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	predicatesProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	recipesProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	structuresProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, NbtMeta]]] = Serialized()
	# 	tagsProp: ClassVar[Serialized[ResourceLocation, TagInfos]] = Serialized()
	# 	dimensionProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	dimension_typeProp: ClassVar[Serialized[ResourceLocation, OrderedDict[ResourceLocation, JsonMeta]]] = Serialized()
	# 	worldGenProp: ClassVar[Serialized[ResourceLocation, WorldGenInfos]] = Serialized()


def createMetaInfo(cls: Type[_TMetaInfo], filePath: FilePathTpl, resourceLocation: ResourceLocation) -> _TMetaInfo:
	return cls(filePath, resourceLocation)


def buildDefaultMeta(filePath: FilePathTpl, resourceLocation: ResourceLocation) -> _TMetaInfo:
	return createMetaInfo(MetaInfo, filePath, resourceLocation)


def buildFunctionMeta(filePath: FilePathTpl, resourceLocation: ResourceLocation) -> FunctionMeta:
	return createMetaInfo(FunctionMeta, filePath, resourceLocation)


def buildJsonMeta(filePath: FilePathTpl, resourceLocation: ResourceLocation, *, schemaId: str) -> JsonMeta:
	info = createMetaInfo(JsonMeta, filePath, resourceLocation)
	info.schemaId = schemaId
	return info


def buildNbtMeta(filePath: FilePathTpl, resourceLocation: ResourceLocation) -> NbtMeta:
	return createMetaInfo(NbtMeta, filePath, resourceLocation)


NAME_SPACE_VAR = '${namespace}'


@dataclass(frozen=True)
class DefaultFileInfo:
	name: str
	namespace: Optional[str]
	contents: str


@dataclass(frozen=True)
class GenerationInfo:
	initialFiles: list[DefaultFileInfo] = field(default_factory=list)


if TYPE_CHECKING:
	@dataclass(frozen=True)
	class EntryHandlerInfo:
		folder: str
		extension: str
		isTag: bool
		buildMetaInfo: Callable[[FilePathTpl, ResourceLocation], MetaInfo]
		contentsProp: Union[SerializedPropertyBaseBase[DatapackContents, OrderedDict[ResourceLocation, MetaInfo]], OrderedDict[ResourceLocation, MetaInfo]]
		generation: GenerationInfo = field(default_factory=GenerationInfo)
else:
	@dataclass(frozen=True)
	class EntryHandlerInfo:
		folder: str
		extension: str
		isTag: bool
		buildMetaInfo: Callable[[FilePathTpl, ResourceLocation], MetaInfo]
		contentsProp: SerializedPropertyBaseBase[DatapackContents, OrderedDict[ResourceLocation, MetaInfo]]
		generation: GenerationInfo = field(default_factory=GenerationInfo)


class EntryHandlerKey(NamedTuple):
	folder: str
	extension: str


EntryHandlers = dict[EntryHandlerKey, EntryHandlerInfo]


def buildEntryHandlers(handlers: list[EntryHandlerInfo]) -> EntryHandlers:
	handlersDict = {EntryHandlerKey(handler.folder, handler.extension): handler for handler in handlers}
	return handlersDict


def getEntryHandlerForFile(fullPath: FilePathTpl, handlers: EntryHandlers) -> Optional[tuple[ResourceLocation, EntryHandlerInfo]]:
	dpPath, filePath = fullPath
	if filePath.startswith('data/'):
		filePath = filePath.removeprefix('data/')
	else:
		return None
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
		if (handler := handlers.get(EntryHandlerKey(prefix, extension))) is not None:
			rest = rest[:len(rest) - len(extension)]
			resourceLocation = ResourceLocation(namespace, rest, handler.isTag)
			return resourceLocation, handler
		continue
	return None


def getEntryHandlersForFolder(fullPath: FilePathTpl, handlers: dict[str, list[EntryHandlerInfo]]) -> list[EntryHandlerInfo]:
	dpPath, filePath = fullPath
	if filePath.startswith('data/'):
		filePath = filePath.removeprefix('data/')
	else:
		return []
	namespace, _, path = filePath.partition('/')

	prefix = ''
	rest = path
	while rest:
		p, _, rest = rest.partition('/')
		prefix += p + '/'
		if (handler := handlers.get(prefix)) is not None:
			return handler
		continue
	return []


@Deprecated
def getMetaInfo(fullPath: FilePathTpl, handlers: EntryHandlers) -> Optional[MetaInfo]:
	resLocHandler = getEntryHandlerForFile(fullPath, handlers)
	if resLocHandler is None:
		return None
	resLoc, handler = resLocHandler
	return handler.buildMetaInfo(fullPath, resLoc)


def collectAllEntries(files: list[FilePathTpl], handlers: EntryHandlers, contents: DatapackContents) -> None:
	for fullPath in files:
		resLocHandler = getEntryHandlerForFile(fullPath, handlers)
		if resLocHandler is None:
			continue
		resLoc, handler = resLocHandler
		metaInfo = handler.buildMetaInfo(fullPath, resLoc)
		handler.contentsProp.get(contents)[resLoc] = metaInfo


def autoCompletionTreeForResourceLocations(locations: Iterable[ResourceLocation]) -> AutoCompletionTree:
	locationStrs = [l.asString for l in locations]
	tree = buildSimpleAutoCompletionTree(locationStrs, (':', '/'))
	return tree


def choicesFromResourceLocations(text: str, locations: Iterable[ResourceLocation]) -> list[str]:
	tree = autoCompletionTreeForResourceLocations(locations)
	return choicesFromAutoCompletionTree(tree, text)


def containsResourceLocation(rl: ResourceLocation, container: Iterable[ResourceLocation]) -> bool:
	if rl.namespace == 'minecraft':
		rl = replace(rl, namespace=None)
	return rl in container


def metaInfoFromResourceLocation(rl: ResourceLocation, values: Mapping[ResourceLocation, MetaInfo]) -> Optional[MetaInfo]:
	# TODO: show prompt, when there are multiple files this applies to.
	return values.get(rl)
