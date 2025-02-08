import os

from corePlugins.datapack.datapackContents import buildEntryHandlers
from corePlugins.datapack.dpVersions import DPVersion, registerDPVersion
from corePlugins.minecraft_data.fullData import getFullMcData
from corePlugins.nbtJsonBase.core import StructureDataSchema
from corePlugins.nbtJsonBase.schemaStore import STRUCTURE_SCHEMA_LOADER


def initVersion() -> None:
	registerDPVersion(buildVersion41())


def loadJsonSchemas() -> dict[str, StructureDataSchema]:
	resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
	v41Dir = os.path.join(resourcesDir, "v41")
	v41Schemas = {
		**STRUCTURE_SCHEMA_LOADER.loadSchemaLibrary('minecraft:tags', os.path.join(v41Dir, 'tags.json')),
		'minecraft:raw_json_text': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:raw_json_text', os.path.join(v41Dir, 'rawJsonText.json')),
		'minecraft:raw_json_style': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:raw_json_style', os.path.join(v41Dir, 'rawJsonStyle.json')),
		'minecraft:predicate': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:predicate', os.path.join(v41Dir, 'predicate.json')),
		'minecraft:recipe': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:recipe', os.path.join(v41Dir, 'recipe.json')),
		'minecraft:pack': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:pack', os.path.join(v41Dir, 'pack.snbt')),
		'minecraft:loot_table': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:loot_table', os.path.join(v41Dir, 'loot_table.json')),
		'minecraft:item_modifier': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:item_modifier', os.path.join(v41Dir, 'item_modifier.json')),
		'minecraft:advancement': STRUCTURE_SCHEMA_LOADER.loadSchema('minecraft:advancement', os.path.join(v41Dir, 'advancements/advancement.json')),  # advancement.json is for datapack version 23!

		# **STRUCTURE_SCHEMA_LOADER.loadSchemaLibrary('minecraft:particle_configuration_tags', os.path.join(v41Dir, 'particle_configuration_tags.json')),  # todo DBG remove again
	}

	v41Schemas |= {
		**STRUCTURE_SCHEMA_LOADER.loadSchemaLibrary('minecraft:particle_configuration_tags', os.path.join(v41Dir, 'particle_configuration_tags.json')),
		**STRUCTURE_SCHEMA_LOADER.loadSchemaLibrary('minecraft:item_sub_predicates', os.path.join(v41Dir, 'item_sub_predicates.json')),
	}
	return v41Schemas


JSON_SCHEMAS = loadJsonSchemas()
SNBT_SCHEMAS = JSON_SCHEMAS


def buildVersion41() -> DPVersion:
	from .commands.v1_20_5_schema import COMMANDS_V41
	from .version23 import DATAPACK_CONTENTS
	return DPVersion(
		name='41',
		structure=buildEntryHandlers(DATAPACK_CONTENTS),
		jsonSchemas=JSON_SCHEMAS,
		snbtSchemas=SNBT_SCHEMAS,
		mcFunctionSchema=COMMANDS_V41.buildSchema(getFullMcData('1.20.5'))
	)
