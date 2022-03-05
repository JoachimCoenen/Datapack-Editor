from __future__ import annotations
import os
import traceback
from json import JSONDecodeError
from typing import TypeVar, Optional

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, Computed, ComputedCached, SerializedPropertyABC
from Cat.extensions import FilesChangedDependency, SingleFileChangedDependency
from Cat.utils.collections_ import OrderedDict
from Cat.utils.profiling import logError
from model.datapackContents import ResourceLocation, collectAllEntries, DatapackContents, MetaInfo, choicesFromResourceLocations
from model.parsing.contextProvider import Suggestions
from model.pathUtils import getAllFilesFromSearchPath, fileNameFromFilePath, FilePathTpl
from settings import applicationSettings

_TT = TypeVar('_TT')


@RegisterContainer
class PackDescription(SerializableContainer):
	__slots__ = ()
	pack_format: int = Serialized(default=0)
	description: str = Serialized(default='')


@RegisterContainer
class Pack(SerializableContainer):
	__slots__ = ()
	pack: PackDescription = Serialized(default_factory=PackDescription)



@RegisterContainer
class Datapack(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.name: str = ''
		self.meta: PackDescription = PackDescription()
		self.files: list[FilePathTpl] = []
		self.allLocalMcFunctions: OrderedDict[ResourceLocation, FilePathTpl] = OrderedDict()
		self.contents: DatapackContents = DatapackContents()

	path: str = Serialized(default='')
	isZipped: bool = ComputedCached(getInitValue=lambda s: os.path.isfile(s.path), ependencies_=[path])

	@ComputedCached(dependencies_=[path])
	def name(self) -> str:
		return fileNameFromFilePath(self.path)

	@pd.Framed()
	@ComputedCached(dependencies_=[SingleFileChangedDependency(path.map(lambda p: os.path.join(p, 'pack.mcmeta'), str))])
	def meta(self) -> PackDescription:
		descriptionPath = os.path.join(self.path, 'pack.mcmeta')
		try:
			with open(descriptionPath, "r") as f:
				text = f.read()
				pack = Pack.fromJSON(text, onError=logError)
		except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError) as e:
			logError(f"Unable to load meta information for datapack at '{self.path}'': \n{traceback.format_exc()}")
			return PackDescription()
		return pack.pack

	description: str = meta.description

	@ComputedCached(dependencies_=[FilesChangedDependency(path, 'data/**')])
	def files(self) -> list[FilePathTpl]:
		allLocalFiles: list[FilePathTpl] = []
		pathInFolder = 'data/**'
		pathInZip = 'data/**'
		pif = pathInFolder
		piz = pathInZip

		rawLocalFiles = getAllFilesFromSearchPath(self.path, pif, piz, extensions=tuple(), excludes=None)
		paritioner = pif[:-2]
		localFiles = []
		for jf in rawLocalFiles:
			if isinstance(jf, tuple):
				localFiles.append(jf)
			else:
				jfPart = jf.rpartition(paritioner)
				localFiles.append((jfPart[0], jfPart[1] + jfPart[2],))
		allLocalFiles.extend(localFiles)
		return allLocalFiles

	@ComputedCached(dependencies_=[FilesChangedDependency(path, 'data/**')])
	def allLocalMcFunctions(self) -> OrderedDict[ResourceLocation, FilePathTpl]:
		result = OrderedDict[ResourceLocation, FilePathTpl]()
		for fullPath in self.files:
			dpPath, filePath = fullPath
			if filePath.startswith('data/'):
				filePath = filePath.removeprefix('data/')
			else:
				continue
			namespace, _, path = filePath.partition('/')
			if path.startswith('functions/'):
				path = path.removeprefix('functions/')
				path = path.removesuffix('.mcfunction')
				isTag = False
			elif path.startswith('tags/functions/'):
				path = path.removeprefix('tags/functions/')
				path = path.removesuffix('.json')
				isTag = True
			else:
				continue
			resourceLocation = ResourceLocation(namespace, path, isTag)
			result[resourceLocation] = filePath
		return result

	@ComputedCached(dependencies_=[FilesChangedDependency(path, 'data/**')])
	def contents(self) -> DatapackContents:
		contents = DatapackContents()
		# allEntryHandlers = [
		# 	# TagInfos:
		# 	EntryHandlerInfo(
		# 		'tags/blocks/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.blocks.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'tags/entity_types/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.entity_types.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'tags/fluids/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.fluids.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'tags/functions/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.functions.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'tags/game_events/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.game_events.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'tags/items/',
		# 		'.json',
		# 		True,
		# 		lambda fp, rl: contents.tags.items.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		#
		# 	# WorldGenInfos:
		# 	EntryHandlerInfo(
		# 		'worldgen/biome/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.biome.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/configured_carver/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.configured_carver.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/configured_feature/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.configured_feature.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/configured_structure_feature/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.configured_structure_feature.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/configured_surface_builder/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.configured_surface_builder.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/noise_settings/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.noise_settings.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/processor_list/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.processor_list.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'worldgen/template_pool/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.worldGen.template_pool.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		#
		# 	# DatapackContents:
		# 	EntryHandlerInfo(
		# 		'advancements/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.advancements.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'functions/',
		# 		'.mcfunction',
		# 		False,
		# 		lambda fp, rl: contents.functions.__setitem__(rl, buildFunctionMeta(fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'item_modifiers/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.item_modifiers.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'loot_tables/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.loot_tables.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'predicates/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.predicates.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'recipes/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.recipes.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'structures/',
		# 		'.nbt',
		# 		False,
		# 		lambda fp, rl: contents.structures.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'dimension/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.dimension.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		# 	EntryHandlerInfo(
		# 		'dimension_type/',
		# 		'.json',
		# 		False,
		# 		lambda fp, rl: contents.dimension_type.__setitem__(rl, buildMetaInfo(MetaInfo, fp, rl)),
		# 	),
		#
		# ]
		from session.session import getSession
		allEntryHandlers = getSession().datapackData.structure
		collectAllEntries(self.files, allEntryHandlers, contents)
		return contents

@RegisterContainer
class World(SerializableContainer):
	__slots__ = ()
	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		self.name: str = ''
		self.datapackPaths: list[str] = []
		self.datapacks: list[Datapack] = []

	path: str = Serialized(default='', decorators=[pd.FolderPath()])


	@Computed()
	def isValid(self) -> bool:
		return len(self.path) > 0 and os.path.isdir(self.path)

	@ComputedCached(dependencies_=[path])
	def name(self) -> str:
		return fileNameFromFilePath(self.path)

	@pd.List()
	@ComputedCached(dependencies_=[path, FilesChangedDependency(path, 'datapacks/*'), Computed(default_factory=lambda: applicationSettings.minecraft.executable)])
	def datapackPaths(self) -> list[str]:
		datapacksPath = os.path.join(self.path, 'datapacks/')
		try:
			datapackFiles = [os.path.join(datapacksPath, f) for f in os.listdir(datapacksPath)]
		except (JSONDecodeError, FileNotFoundError, AttributeError, TypeError) as e:
			logError(f'Unable to find datapacks: \n{traceback.format_exc()}')
			return []
		minecraftExec = applicationSettings.minecraft.executable
		if minecraftExec and os.path.isfile(minecraftExec):
			datapackFiles.append(minecraftExec)
		return datapackFiles

	_oldDatapacks: list[Datapack] = Serialized(default_factory=list, shouldSerialize=False, shouldPrint=False, decorators=[pd.NoUI()])

	@pd.List()
	@ComputedCached(dependencies_=[datapackPaths])
	def datapacks(self) -> list[Datapack]:
		oldDps = {dp.name: dp for dp in self._oldDatapacks}
		datapacks = [
			Datapack.create(path=p)
			for p in self.datapackPaths
		]
		datapacks = [oldDps.get(dp.name, dp) for dp in datapacks]
		self._oldDatapacks = datapacks.copy()
		return datapacks


def choicesForDatapackContents(text: str, prop: SerializedPropertyABC[Datapack, OrderedDict[ResourceLocation, MetaInfo]]) -> Suggestions:
	from session.session import getSession
	locations = [b for dp in getSession().world.datapacks for b in prop.get(dp)]
	return choicesFromResourceLocations(text, locations)


def metaInfoFromDatapackContents(rl: ResourceLocation, prop: SerializedPropertyABC[Datapack, OrderedDict[ResourceLocation, MetaInfo]]) -> Optional[MetaInfo]:
	from session.session import getSession
	for dp in getSession().world.datapacks:
		# TODO: show prompt, when there are multiple files this applies to.
		if (file := prop.get(dp).get(rl)) is not None:
			return file
	return None