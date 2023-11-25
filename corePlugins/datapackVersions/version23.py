import os

from corePlugins.datapack.datapackContents import RESOURCES, buildJsonMeta, EntryHandlerInfo, NAME_SPACE_VAR, DatapackContents, GenerationInfo, DefaultFileInfo, \
	buildFunctionMeta, buildNbtMeta, buildEntryHandlers
from corePlugins.datapack.dpVersions import DPVersion, registerDPVersion
from corePlugins.json.core import JsonSchema
from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
from corePlugins.mcFunction.command import MCFunctionSchema
from corePlugins.minecraft_data.fullData import getFullMcData
from .allVersions import REGISTRY_TAGS, WORLDGEN
from .commands.v1_20_2_schema import COMMANDS


def initVersion() -> None:
	registerDPVersion(version18)
	registerDPVersion(version23)


LOAD_JSON_CONTENTS = f"""{{
	"values": [
		"{NAME_SPACE_VAR}:load"
	]
}}"""

TICK_JSON_CONTENTS = f"""{{
	"values": [
		"{NAME_SPACE_VAR}:tick"
	]
}}"""

LOAD_MCFUNCTION_CONTENTS = f"say loading {NAME_SPACE_VAR} ..."

TICK_MCFUNCTION_CONTENTS = f"# add commands here..."


DATAPACK_CONTENTS: list[EntryHandlerInfo] = [
	EntryHandlerInfo(
		folder='/',
		extension='pack.mcmeta',
		isTag=False,
		includeSubdirs=False,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:pack'),
		getIndex=None
	),
	EntryHandlerInfo(
		folder='/',
		extension='dependencies.json',
		isTag=False,
		includeSubdirs=False,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='dpe:dependencies'),
		getIndex=None
	),

	# TagInfos:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/functions/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/function'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.TAGS.FUNCTION),
		generation=GenerationInfo(
			initialFiles=[
				DefaultFileInfo(
					'load.json',
					'minecraft',
					LOAD_JSON_CONTENTS
				),
				DefaultFileInfo(
					'tick.json',
					'minecraft',
					TICK_JSON_CONTENTS
				),
			]
		)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/instrument/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/instrument'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.TAGS.INSTRUMENT)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/damage_type/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/damage_type'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.TAGS.DAMAGE_TYPE)
	),
	*[
		EntryHandlerInfo(
			folder=f'data/{NAME_SPACE_VAR}/{folder}/',
			extension='.json',
			isTag=True,
			includeSubdirs=True,
			buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId=f'minecraft:{indexPath}'),
			getIndex=lambda p, indexPath=indexPath: p.indexBundles.setdefault(DatapackContents).resources.getIndex(indexPath)
		)
		for indexPath, folder in REGISTRY_TAGS.items()
	],

	# WorldGenInfos:
	*[
		EntryHandlerInfo(
			folder=f'data/{NAME_SPACE_VAR}/{folder}/',
			extension='.json',
			isTag=False,
			includeSubdirs=True,
			buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId=f'minecraft:{indexPath}'),
			getIndex=lambda p, indexPath=indexPath: p.indexBundles.setdefault(DatapackContents).resources.getIndex(indexPath)
		)
		for indexPath, folder in WORLDGEN.items()
	],

	# DatapackContents:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/advancements/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:advancement'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.ADVANCEMENTS)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/functions/',
		extension='.mcfunction',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildFunctionMeta(fp),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.FUNCTIONS),
		generation=GenerationInfo(
			initialFiles=[
				DefaultFileInfo(
					'load.mcfunction',
					NAME_SPACE_VAR,
					LOAD_MCFUNCTION_CONTENTS
				),
				DefaultFileInfo(
					'tick.mcfunction',
					NAME_SPACE_VAR,
					TICK_MCFUNCTION_CONTENTS
				),
			]
		)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/item_modifiers/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:item_modifiers'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.ITEM_MODIFIERS)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/loot_tables/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:loot_tables'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.LOOT_TABLES)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/predicates/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:predicate'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.PREDICATES)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/recipes/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:recipe'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.RECIPES)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/structures/',
		extension='.nbt',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildNbtMeta(fp),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.STRUCTURES)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.DIMENSION)
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension_type/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension_type'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).resources.getIndex(RESOURCES.DIMENSION_TYPE)
	),
]


def buildMCFunctionSchema() -> MCFunctionSchema:
	version1_20_3 = getFullMcData('1.20.3')
	schema_1_20_3 = COMMANDS.buildSchema(version1_20_3)  # todo: update!
	return schema_1_20_3


def loadJsonSchemas() -> dict[str, JsonSchema]:
	resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
	v23Dir = os.path.join(resourcesDir, "v23/")
	v23Schemas = {
		**JSON_SCHEMA_LOADER.loadSchemaLibrary('minecraft:tags', os.path.join(v23Dir, 'tags.json')),
		'minecraft:raw_json_text': JSON_SCHEMA_LOADER.loadSchema('minecraft:raw_json_text', os.path.join(v23Dir, 'rawJsonText.json')),
		'minecraft:predicate': JSON_SCHEMA_LOADER.loadSchema('minecraft:predicate', os.path.join(v23Dir, 'predicate.json')),
		'minecraft:recipe': JSON_SCHEMA_LOADER.loadSchema('minecraft:recipe', os.path.join(v23Dir, 'recipe.json')),
		'minecraft:pack': JSON_SCHEMA_LOADER.loadSchema('minecraft:pack', os.path.join(v23Dir, 'pack.json')),
		'minecraft:loot_table': JSON_SCHEMA_LOADER.loadSchema('minecraft:loot_table', os.path.join(v23Dir, 'loot_table.json')),
		'minecraft:item_modifier': JSON_SCHEMA_LOADER.loadSchema('minecraft:item_modifier', os.path.join(v23Dir, 'item_modifier.json')),
		'minecraft:advancement': JSON_SCHEMA_LOADER.loadSchema('minecraft:advancement', os.path.join(v23Dir, 'advancements/advancement.json')),  # advancement.json is for datapack version 23!
	}
	return v23Schemas


JSON_SCHEMAS = loadJsonSchemas()

version23 = DPVersion(
	name='23',
	structure=buildEntryHandlers(DATAPACK_CONTENTS),
	jsonSchemas=JSON_SCHEMAS,  # todo add schemata here, so they are synced to datapack version.
	mcFunctionSchema=buildMCFunctionSchema()
)

version18 = DPVersion(
	name='18',
	structure=buildEntryHandlers(DATAPACK_CONTENTS),
	jsonSchemas=JSON_SCHEMAS,
	mcFunctionSchema=buildMCFunctionSchema()
)

# DATAPACK_CONTENTS_STRUCTURE: EntryHandlers = buildEntryHandlers(DATAPACK_CONTENTS)
