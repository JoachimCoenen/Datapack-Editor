"""
for Minecraft version 1.17
"""
from model.data.dpVersion import registerDPVersion, DPVersion
from model.data.json.schemas.predicate import PREDICATE_SCHEMA
from model.data.json.schemas.rawJsonText import RAW_JSON_TEXT_SCHEMA
from model.data.json.schemas.tags import *
from model.datapack.datapackContents import NAME_SPACE_VAR, EntryHandlerInfo, DatapackContents, GenerationInfo, DefaultFileInfo, \
	buildFunctionMeta, buildEntryHandlers, buildJsonMeta, buildNbtMeta
from model.json.core import JsonSchema


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
	# TagInfos:
	EntryHandlerInfo(
		'tags/blocks/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/blocks'),
		lambda p: p.setdefaultIndex(DatapackContents).tags.blocks
	),
	EntryHandlerInfo(
		'tags/entity_types/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/entity_types'),
		lambda p: p.setdefaultIndex(DatapackContents).tags.entity_types
	),
	EntryHandlerInfo(
		'tags/fluids/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/fluids'),
		lambda p: p.setdefaultIndex(DatapackContents).tags.fluids
	),
	EntryHandlerInfo(
		'tags/functions/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/functions'),
		lambda p: p.setdefaultIndex(DatapackContents).tags.functions,
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
		lambda p: p.setdefaultIndex(DatapackContents).tags.game_events
	),
	EntryHandlerInfo(
		'tags/items/',
		'.json',
		True,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='tags/items'),
		lambda p: p.setdefaultIndex(DatapackContents).tags.items
	),

	# WorldGenInfos:
	EntryHandlerInfo(
		'worldgen/biome/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/biome'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.biome
	),
	EntryHandlerInfo(
		'worldgen/configured_carver/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_carver'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_carver
	),
	EntryHandlerInfo(
		'worldgen/configured_feature/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_feature'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_feature
	),
	EntryHandlerInfo(
		'worldgen/configured_structure_feature/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_structure_feature'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_structure_feature
	),
	EntryHandlerInfo(
		'worldgen/configured_surface_builder/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/configured_surface_builder'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_surface_builder
	),
	EntryHandlerInfo(
		'worldgen/noise_settings/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/noise_settings'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.noise_settings
	),
	EntryHandlerInfo(
		'worldgen/processor_list/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/processor_list'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.processor_list
	),
	EntryHandlerInfo(
		'worldgen/template_pool/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='worldgen/template_pool'),
		lambda p: p.setdefaultIndex(DatapackContents).worldGen.template_pool
	),

	# DatapackContents:
	EntryHandlerInfo(
		'advancements/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='advancements'),
		lambda p: p.setdefaultIndex(DatapackContents).advancements
	),
	EntryHandlerInfo(
		'functions/',
		'.mcfunction',
		False,
		lambda fp, rl: buildFunctionMeta(fp, rl),
		lambda p: p.setdefaultIndex(DatapackContents).functions,
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
		lambda p: p.setdefaultIndex(DatapackContents).item_modifiers
	),
	EntryHandlerInfo(
		'loot_tables/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='loot_tables'),
		lambda p: p.setdefaultIndex(DatapackContents).loot_tables
	),
	EntryHandlerInfo(
		'predicates/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='predicates'),
		lambda p: p.setdefaultIndex(DatapackContents).predicates
	),
	EntryHandlerInfo(
		'recipes/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='recipes'),
		lambda p: p.setdefaultIndex(DatapackContents).recipes
	),
	EntryHandlerInfo(
		'structures/',
		'.nbt',
		False,
		lambda fp, rl: buildNbtMeta(fp, rl),
		lambda p: p.setdefaultIndex(DatapackContents).structures
	),
	EntryHandlerInfo(
		'dimension/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='dimension'),
		lambda p: p.setdefaultIndex(DatapackContents).dimension
	),
	EntryHandlerInfo(
		'dimension_type/',
		'.json',
		False,
		lambda fp, rl: buildJsonMeta(fp, rl, schemaId='dimension_type'),
		lambda p: p.setdefaultIndex(DatapackContents).dimension_type
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
