"""
for Minecraft version 1.17
"""
import re

from model.data.dpVersion import registerDPVersion, DPVersion
from model.data.json.schemas.dependency import DEPENDENCIES_SCHEMA
from model.data.json.schemas.predicate import PREDICATE_SCHEMA
from model.data.json.schemas.rawJsonText import RAW_JSON_TEXT_SCHEMA
from model.data.json.schemas.tags import *
from model.datapack.datapackContents import NAME_SPACE_VAR, EntryHandlerInfo, DatapackContents, GenerationInfo, DefaultFileInfo, \
	buildFunctionMeta, buildEntryHandlers, buildJsonMeta, buildNbtMeta, NAME_SPACE_CAPTURE_GROUP
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
	EntryHandlerInfo(
		folder=re.compile('/'),
		extension='pack.mcmeta',
		isTag=False,
		includeSubdirs=False,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='pack.mcmeta'),
		getIndex=None
	),
	EntryHandlerInfo(
		folder=re.compile('/'),
		extension='dependencies.json',
		isTag=False,
		includeSubdirs=False,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='dependencies.json'),
		getIndex=None
	),
	# TagInfos:
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/blocks/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/blocks'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.blocks
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/entity_types/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/entity_types'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.entity_types
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/fluids/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/fluids'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.fluids
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/functions/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/functions'),
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
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/game_events/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/game_events'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.game_events
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/tags/items/'),
		extension='.json',
		isTag=True,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='tags/items'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).tags.items
	),

	# WorldGenInfos:
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/biome/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/biome'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.biome
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/configured_carver/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/configured_carver'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_carver
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/configured_feature/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/configured_feature'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_feature
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/configured_structure_feature/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/configured_structure_feature'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_structure_feature
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/configured_surface_builder/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/configured_surface_builder'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.configured_surface_builder
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/noise_settings/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/noise_settings'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.noise_settings
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/processor_list/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/processor_list'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.processor_list
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/worldgen/template_pool/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='worldgen/template_pool'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).worldGen.template_pool
	),

	# DatapackContents:
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/advancements/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='advancements'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).advancements
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/functions/'),
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
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/item_modifiers/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='item_modifiers'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).item_modifiers
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/loot_tables/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='loot_tables'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).loot_tables
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/predicates/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='predicates'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).predicates
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/recipes/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='recipes'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).recipes
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/structures/'),
		extension='.nbt',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildNbtMeta(fp),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).structures
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/dimension/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='dimension'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).dimension
	),
	EntryHandlerInfo(
		folder=re.compile(f'data/{NAME_SPACE_CAPTURE_GROUP}/dimension_type/'),
		extension='.json',
		isTag=False,
		includeSubdirs=True,
		buildMetaInfo=lambda fp: buildJsonMeta(fp, schemaId='dimension_type'),
		getIndex=lambda p: p.setdefaultIndex(DatapackContents).dimension_type
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
	'dependencies.json': DEPENDENCIES_SCHEMA,
}

version6 = DPVersion(
	name='6',
	structure=buildEntryHandlers(DATAPACK_CONTENTS),
	jsonSchemas=DATAPACK_JSON_SCHEMAS
)
