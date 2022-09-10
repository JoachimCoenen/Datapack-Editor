"""
for Minecraft version 1.17
"""

from model.data.dpVersion import registerDPVersion, DPVersion
from model.data.json.schemas.tags import GLOBAL_SCHEMA_STORE
from model.datapack.datapackContents import NAME_SPACE_VAR, EntryHandlerInfo, DatapackContents, GenerationInfo, DefaultFileInfo, \
	buildFunctionMeta, buildEntryHandlers, buildJsonMeta, buildNbtMeta


def initPlugin() -> None:
	registerDPVersion(version6)
	from model.data.json import contexts
	contexts.init()


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
		folder=f'data/{NAME_SPACE_VAR}/tags/blocks/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/block_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.blocks
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/entity_types/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/entity_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.entity_types
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/fluids/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/fluid_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.fluids
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/functions/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/function'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.functions,
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
		folder=f'data/{NAME_SPACE_VAR}/tags/game_events/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/game_event'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.game_events
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/tags/items/',
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:tags/item_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.items
	),

	# WorldGenInfos:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/biome/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/biome'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.biome
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_carver/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_carver'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_carver
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_feature/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_feature'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_feature
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_structure_feature/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_structure_feature'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_structure_feature
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/configured_surface_builder/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/configured_surface_builder'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_surface_builder
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/noise_settings/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/noise_settings'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.noise_settings
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/processor_list/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/processor_list'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.processor_list
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/worldgen/template_pool/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:worldgen/template_pool'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.template_pool
	),

	# DatapackContents:
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/advancements/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:advancements'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).advancements
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/functions/',
		extension='.mcfunction',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildFunctionMeta(fp),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).functions,
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
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).item_modifiers
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/loot_tables/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:loot_tables'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).loot_tables
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/predicates/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:predicate'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).predicates
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/recipes/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:recipe'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).recipes
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/structures/',
		extension='.nbt',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildNbtMeta(fp),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).structures
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).dimension
	),
	EntryHandlerInfo(
		folder=f'data/{NAME_SPACE_VAR}/dimension_type/',
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='minecraft:dimension_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).dimension_type
	),
]

version6 = DPVersion(
	name='6',
	structure=buildEntryHandlers(DATAPACK_CONTENTS),
	jsonSchemas=GLOBAL_SCHEMA_STORE
)
