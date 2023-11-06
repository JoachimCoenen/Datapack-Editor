import os

from corePlugins.datapack.datapackContents import buildJsonMeta, EntryHandlerInfo, NAME_SPACE_VAR, DatapackContents, GenerationInfo, DefaultFileInfo, buildFunctionMeta, buildNbtMeta, \
	buildEntryHandlers
from corePlugins.datapack.dpVersions import DPVersion, registerDPVersion
from corePlugins.datapackVersions.resources.allVersions import REGISTRY_TAGS
from corePlugins.json.core import JsonSchema
from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
from corePlugins.mcFunction.command import MCFunctionSchema
from corePlugins.mcFunctionSchemaTEMP.v1_17_schema import buildMCFunctionSchemaFor_v1_17
from corePlugins.minecraft_data.fullData import getFullMcData


def initVersion() -> None:
	registerDPVersion(version20)


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
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).tags.functions,
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
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).tags.instruments
	),
	*[
		EntryHandlerInfo(
			folder=f'data/{NAME_SPACE_VAR}/tags/{folder}/',
			extension='.json',
			isTag=True,
			includeSubdirs=True,
			buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId=f'minecraft:tags/{tag}'),
			getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).tags.allOther
		)
		for tag, folder in REGISTRY_TAGS.items()
	],

	# WorldGenInfos:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/biome/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/biome'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.biome
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_carver/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_carver'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.configured_carver
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_feature/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_feature'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.configured_feature
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_structure_feature/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_structure_feature'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.configured_structure_feature
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_surface_builder/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_surface_builder'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.configured_surface_builder
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/noise_settings/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/noise_settings'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.noise_settings
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/processor_list/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/processor_list'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.processor_list
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/template_pool/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/template_pool'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).worldGen.template_pool
	),

	# DatapackContents:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/advancements/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:advancement'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).advancements
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/functions/',
		extension='.mcfunction',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildFunctionMeta(fp),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).functions,
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
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).item_modifiers
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/loot_tables/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:loot_tables'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).loot_tables
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/predicates/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:predicate'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).predicates
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/recipes/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:recipe'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).recipes
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/structures/',
		extension='.nbt',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildNbtMeta(fp),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).structures
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).dimension
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension_type/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension_type'),
		getIndex=lambda p: p.indexBundles.setdefault(DatapackContents).dimension_type
	),
]


def buildMCFunctionSchema() -> MCFunctionSchema:
	version1_20 = getFullMcData('1.20')
	schema_1_17 = buildMCFunctionSchemaFor_v1_17(version1_20)  # todo: update!
	return schema_1_17


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

# DATAPACK_CONTENTS_STRUCTURE: EntryHandlers = buildEntryHandlers(DATAPACK_CONTENTS)
