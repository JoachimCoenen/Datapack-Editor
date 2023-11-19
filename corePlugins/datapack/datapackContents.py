from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Type, Callable, Mapping

from cat.utils.profiling import logError
from cat.utils import unescapeFromXml, escapeForXmlAttribute, CachedProperty
from base.model.aspect import AspectType
from base.model.project.index import DeepIndex, Index
from base.model.parsing.parser import parse
from base.model.pathUtils import FilePathTpl, loadBinaryFile, loadTextFile, ZipFilePool
from base.model.project.project import IndexBundleAspect, Root
from base.model.utils import MDStr
from corePlugins.minecraft.resourceLocation import ResourceLocation, MetaInfo

DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')

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
		json, errors, _ = parse(file, filePath=self.filePath, language=JSON_ID, schema=None)

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
class DatapackContents(IndexBundleAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_CONTENTS_TYPE
	
	resources: DeepIndex[ResourceLocation, MetaInfo] = field(default_factory=DeepIndex, init=False, metadata=dict(dpe=dict(isIndex=True)))


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
	getIndex: Callable[[Root], Index[ResourceLocation, MetaInfo]] | None = field(kw_only=True)
	generation: GenerationInfo = field(default_factory=GenerationInfo, kw_only=True)

	def __post_init__(self):
		object.__setattr__(self, 'folderPattern', folderPatternFromPath(self.folder))


def folderPatternFromPath(path: str) -> re.Pattern:
	path2 = path.replace(NAME_SPACE_VAR, NAME_SPACE_CAPTURE_GROUP)
	return re.compile(path2)


EntryHandlers = Mapping[str, list[EntryHandlerInfo]]


def buildEntryHandlers(handlers: list[EntryHandlerInfo]) -> EntryHandlers:
	result = {}
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


def collectEntry(fullPath: FilePathTpl, handlers: EntryHandlers, root: Root) -> None:
	if (resLocHandler := getEntryHandlerForFile(fullPath, handlers)) is not None:
		resLoc: ResourceLocation | None
		handler: EntryHandlerInfo
		resLoc, handler = resLocHandler
		if resLoc is None:
			return
		metaInfo = handler.buildMetaInfo(fullPath)
		if handler.getIndex is not None:
			handler.getIndex(root).add(resLoc, fullPath, metaInfo)


class _TagWorldgenIndices:
	def __init__(self, prefix: str):
		self.CARVER: str = f'{prefix}carver'  # World carver
		self.CONFIGURED_CARVER: str = f'{prefix}configured_carver'  # Configured world carver
		self.FEATURE: str = f'{prefix}feature'  # Feature
		self.CONFIGURED_FEATURE: str = f'{prefix}configured_feature'  # Configured feature
		self.STRUCTURE_SET: str = f'{prefix}structure_set'  # Structure set
		self.STRUCTURE_PROCESSOR: str = f'{prefix}structure_processor'  # Structure processor type
		self.PROCESSOR_LIST: str = f'{prefix}processor_list'  # Structure processor list
		self.STRUCTURE_POOL_ELEMENT: str = f'{prefix}structure_pool_element'  # Structure pool element type
		self.TEMPLATE_POOL: str = f'{prefix}template_pool'  # Structure template pool
		self.STRUCTURE_PIECE: str = f'{prefix}structure_piece'  # Structure piece type
		self.STRUCTURE_TYPE: str = f'{prefix}structure_type'  # Structure feature
		self.STRUCTURE: str = f'{prefix}structure'  # Configured structure feature
		self.STRUCTURE_PLACEMENT: str = f'{prefix}structure_placement'  # Structure placement type
		self.PLACEMENT_MODIFIER_TYPE: str = f'{prefix}placement_modifier_type'  # Placement modifier type
		self.PLACED_FEATURE: str = f'{prefix}placed_feature'  # Placed feature
		self.BIOME: str = f'{prefix}biome'  # Biome
		self.BIOME_SOURCE: str = f'{prefix}biome_source'  # Biome source
		self.NOISE: str = f'{prefix}noise'  # Normal noise
		self.NOISE_SETTINGS: str = f'{prefix}noise_settings'  # Noise generator settings
		self.DENSITY_FUNCTION: str = f'{prefix}density_function'  # Density function
		self.DENSITY_FUNCTION_TYPE: str = f'{prefix}density_function_type'  # Density function type
		self.WORLD_PRESET: str = f'{prefix}world_preset'  # World preset
		self.FLAT_LEVEL_GENERATOR_PRESET: str = f'{prefix}flat_level_generator_preset'  # Flat world generator preset
		self.CHUNK_GENERATOR: str = f'{prefix}chunk_generator'  # Chunk generator
		self.MATERIAL_CONDITION: str = f'{prefix}material_condition'  # Surface condition source
		self.MATERIAL_RULE: str = f'{prefix}material_rule'  # Surface rule source
		self.BLOCK_STATE_PROVIDER_TYPE: str = f'{prefix}block_state_provider_type'  # Block state provider type
		self.FOLIAGE_PLACER_TYPE: str = f'{prefix}foliage_placer_type'  # Foliage placer type
		self.TRUNK_PLACER_TYPE: str = f'{prefix}trunk_placer_type'  # Trunk placer type
		self.TREE_DECORATOR_TYPE: str = f'{prefix}tree_decorator_type'  # Tree decorator type
		self.FEATURE_SIZE_TYPE: str = f'{prefix}feature_size_type'  # Feature size type


class _TagIndices:
	def __init__(self, prefix: str):
		# NON-REGISTRY_TAGS =
		self.FUNCTION: str = f'{prefix}function'  # Attribute
		self.CHAT_TYPE: str = f'{prefix}chat_type'  # Attribute
		self.DAMAGE_TYPE: str = f'{prefix}damage_type'  # Attribute
		self.INSTRUMENT: str = f'{prefix}instrument'  # Attribute
	
		# REGISTRY_TAGS =
		self.ATTRIBUTE: str = f'{prefix}attribute'  # Attribute
		self.BLOCK: str = f'{prefix}block'  # Block
		self.BLOCK_ENTITY_TYPE: str = f'{prefix}block_entity_type'  # Block entity type
		self.CHUNK_STATUS: str = f'{prefix}chunk_status'  # Chunk status
		self.COMMAND_ARGUMENT_TYPE: str = f'{prefix}command_argument_type'  # Command argument type
		self.DIMENSION: str = f'{prefix}dimension'  # Dimension and Level stem
		self.DIMENSION_TYPE: str = f'{prefix}dimension_type'  # Dimension type
		self.ENCHANTMENT: str = f'{prefix}enchantment'  # Enchantment
		self.ENTITY_TYPE: str = f'{prefix}entity_type'  # Entity type
		self.FLUID: str = f'{prefix}fluid'  # Fluid
		self.GAME_EVENT: str = f'{prefix}game_event'  # Game event
		self.POSITION_SOURCE_TYPE: str = f'{prefix}position_source_type'  # Position source type (used by game events)
		self.ITEM: str = f'{prefix}item'  # Item
		self.MENU: str = f'{prefix}menu'  # Menu type
		self.MOB_EFFECT: str = f'{prefix}mob_effect'  # Mob effect
		self.PARTICLE_TYPE: str = f'{prefix}particle_type'  # Particle type
		self.POTION: str = f'{prefix}potion'  # Potion
		self.RECIPE_SERIALIZER: str = f'{prefix}recipe_serializer'  # Recipe serializer
		self.RECIPE_TYPE: str = f'{prefix}recipe_type'  # Recipe type
		self.SOUND_EVENT: str = f'{prefix}sound_event'  # Sound event
		self.STAT_TYPE: str = f'{prefix}stat_type'  # Statistics type
		self.CUSTOM_STAT: str = f'{prefix}custom_stat'  # Custom Statistics
		# Entity data registries
		self.ACTIVITY: str = f'{prefix}activity'  # Entity schedule activity
		self.MEMORY_MODULE_TYPE: str = f'{prefix}memory_module_type'  # Entity memory module type
		self.SCHEDULE: str = f'{prefix}schedule'  # Entity schedule
		self.SENSOR_TYPE: str = f'{prefix}sensor_type'  # Entity AI sensor type
		self.MOTIVE: str = f'{prefix}motive'  # Painting motive
		self.VILLAGER_PROFESSION: str = f'{prefix}villager_profession'  # Villager profession
		self.VILLAGER_TYPE: str = f'{prefix}villager_type'  # Villager type
		self.POINT_OF_INTEREST_TYPE: str = f'{prefix}point_of_interest_type'  # Poi type
		# Loot table serializer registries:
		self.LOOT_CONDITION_TYPE: str = f'{prefix}loot_condition_type'  # Loot condition type
		self.LOOT_FUNCTION_TYPE: str = f'{prefix}loot_function_type'  # Loot function type
		self.LOOT_NBT_PROVIDER_TYPE: str = f'{prefix}loot_nbt_provider_type'  # Loot nbt provider type
		self.LOOT_NUMBER_PROVIDER_TYPE: str = f'{prefix}loot_number_provider_type'  # Loot number provider type
		self.LOOT_POOL_ENTRY_TYPE: str = f'{prefix}loot_pool_entry_type'  # Loot pool entry type
		self.LOOT_SCORE_PROVIDER_TYPE: str = f'{prefix}loot_score_provider_type'  # Loot score provider type
		# Json file value provider registries:
		self.FLOAT_PROVIDER_TYPE: str = f'{prefix}float_provider_type'  # Float provider type
		self.INT_PROVIDER_TYPE: str = f'{prefix}int_provider_type'  # Int provider type
		self.HEIGHT_PROVIDER_TYPE: str = f'{prefix}height_provider_type'  # Height provider type
		# World generator registries:
		self.BLOCK_PREDICATE_TYPE: str = f'{prefix}block_predicate_type'  # Block predicate type
		self.RULE_TEST: str = f'{prefix}rule_test'  # Structure featrue rule test type
		self.POS_RULE_TEST: str = f'{prefix}pos_rule_test'  # Structure featrue position rule test type
		self.WORLDGEN: _TagWorldgenIndices = _TagWorldgenIndices(f'{prefix}worldgen/')


class _WorldgenIndices:
	def __init__(self, prefix: str):
		# todo add all folders. minecraft seems to have more folders here, than the wiki says...
		self.BIOME: str = f'{prefix}biome'
		self.CONFIGURED_CARVER: str = f'{prefix}configured_carver'
		self.CONFIGURED_FEATURE: str = f'{prefix}configured_feature'
		self.CONFIGURED_STRUCTURE_FEATURE: str = f'{prefix}configured_structure_feature'  # todo check if this is still true!
		self.CONFIGURED_SURFACE_BUILDER: str = f'{prefix}configured_surface_builder'  # todo check if this is still true!
		self.DENSITY_FUNCTION: str = f'{prefix}density_function'
		self.FLAT_LEVEL_GENERATOR_PRESET: str = f'{prefix}flat_level_generator_preset'
		self.NOISE: str = f'{prefix}noise'
		self.NOISE_SETTINGS: str = f'{prefix}noise_settings'
		self.PLACED_FEATURE: str = f'{prefix}placed_feature'
		self.PROCESSOR_LIST: str = f'{prefix}processor_list'
		self.STRUCTURE: str = f'{prefix}structure'
		self.STRUCTURE_SET: str = f'{prefix}structure_set'
		self.TEMPLATE_POOL: str = f'{prefix}template_pool'
		self.WORLD_PRESET: str = f'{prefix}world_preset'


class _ResourceLocationIndices:
	def __init__(self, prefix: str):
		self.ADVANCEMENTS: str = f'{prefix}advancements'
		self.FUNCTIONS: str = f'{prefix}functions'
		self.ITEM_MODIFIERS: str = f'{prefix}item_modifiers'
		self.LOOT_TABLES: str = f'{prefix}loot_tables'
		self.PREDICATES: str = f'{prefix}predicates'
		self.RECIPES: str = f'{prefix}recipes'
		self.STRUCTURES: str = f'{prefix}structures'
		self.TAGS: _TagIndices = _TagIndices(f'{prefix}tags/')
		self.DIMENSION: str = f'{prefix}dimension'
		self.DIMENSION_TYPE: str = f'{prefix}dimension_type'
		self.WORLDGEN: _WorldgenIndices = _WorldgenIndices(f'{prefix}worldgen/')


RESOURCES: _ResourceLocationIndices = _ResourceLocationIndices('')
TAGS: _TagIndices = RESOURCES.TAGS
