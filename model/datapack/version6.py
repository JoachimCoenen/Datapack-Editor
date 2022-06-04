"""
for Minecraft version 1.17
"""
from model.datapack.dpVersion import registerDPVersion, DPVersion
from model.datapack.json.schemas.predicate import PREDICATE_SCHEMA
from model.datapack.json.schemas.rawJsonText import RAW_JSON_TEXT_SCHEMA
from model.datapack.json.schemas.tags import *
from model.datapackContents import NAME_SPACE_VAR, EntryHandlerInfo, DatapackContents, GenerationInfo, DefaultFileInfo, \
	buildFunctionMeta, buildEntryHandlers, buildJsonMeta, buildNbtMeta
from model.json.core import JsonSchema


def initPlugin() -> None:
	registerDPVersion(version6)
	from model.datapack.json import contexts
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
	# TagInfos:
	EntryHandlerInfo(
		'tags/blocks/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/blocks'),
		DatapackContents.tags.blocks
	),
	EntryHandlerInfo(
		'tags/entity_types/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/entity_types'),
		DatapackContents.tags.entity_types
	),
	EntryHandlerInfo(
		'tags/fluids/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/fluids'),
		DatapackContents.tags.fluids
	),
	EntryHandlerInfo(
		'tags/functions/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/functions'),
		DatapackContents.tags.functions,
		GenerationInfo(
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
		'tags/game_events/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/game_events'),
		DatapackContents.tags.game_events
	),
	EntryHandlerInfo(
		'tags/items/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/items'),
		DatapackContents.tags.items
	),

	# WorldGenInfos:
	EntryHandlerInfo(
		'worldgen/biome/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/biome'),
		DatapackContents.worldGen.biome
	),
	EntryHandlerInfo(
		'worldgen/configured_carver/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_carver'),
		DatapackContents.worldGen.configured_carver
	),
	EntryHandlerInfo(
		'worldgen/configured_feature/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_feature'),
		DatapackContents.worldGen.configured_feature
	),
	EntryHandlerInfo(
		'worldgen/configured_structure_feature/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_structure_feature'),
		DatapackContents.worldGen.configured_structure_feature
	),
	EntryHandlerInfo(
		'worldgen/configured_surface_builder/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_surface_builder'),
		DatapackContents.worldGen.configured_surface_builder
	),
	EntryHandlerInfo(
		'worldgen/noise_settings/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/noise_settings'),
		DatapackContents.worldGen.noise_settings
	),
	EntryHandlerInfo(
		'worldgen/processor_list/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/processor_list'),
		DatapackContents.worldGen.processor_list
	),
	EntryHandlerInfo(
		'worldgen/template_pool/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/template_pool'),
		DatapackContents.worldGen.template_pool
	),

	# DatapackContents:
	EntryHandlerInfo(
		'advancements/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='advancements'),
		DatapackContents.advancements
	),
	EntryHandlerInfo(
		'functions/',
		'.mcfunction',
		False,
		lambda fp, rl: buildFunctionMeta(fp, rl),
		DatapackContents.functions,
		GenerationInfo(
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
		'item_modifiers/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='item_modifiers'),
		DatapackContents.item_modifiers
	),
	EntryHandlerInfo(
		'loot_tables/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='loot_tables'),
		DatapackContents.loot_tables
	),
	EntryHandlerInfo(
		'predicates/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='predicates'),
		DatapackContents.predicates
	),
	EntryHandlerInfo(
		'recipes/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='recipes'),
		DatapackContents.recipes
	),
	EntryHandlerInfo(
		'structures/',
		'.nbt',
		False,
		lambda fp, rl: buildNbtMeta(fp, rl),
		DatapackContents.structures
	),
	EntryHandlerInfo(
		'dimension/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='dimension'),
		DatapackContents.dimension
	),
	EntryHandlerInfo(
		'dimension_type/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='dimension_type'),
		DatapackContents.dimension_type
	),

]

DATAPACK_JSON_SCHEMAS: dict[str, JsonSchema] = {
	'rawJsonText': RAW_JSON_TEXT_SCHEMA,
	'tags/blocks': TAGS_BLOCKS,
	'tags/entity_types': TAGS_ENTITY_TYPES,
	'tags/fluids': TAGS_FLUIDS,
	'tags/functions': TAGS_FUNCTIONS,
	'tags/game_events': TAGS_GAME_EVENTS,
	'tags/items': TAGS_ITEMS,
	'predicates': PREDICATE_SCHEMA,
}

version6 = DPVersion(
	name='6',
	structure=buildEntryHandlers(DATAPACK_CONTENTS),
	jsonSchemas=DATAPACK_JSON_SCHEMAS
)
