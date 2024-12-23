import os

from corePlugins.datapack.datapackContents import buildEntryHandlers
from corePlugins.datapack.dpVersions import DPVersion, registerDPVersion
from corePlugins.json.core import JsonSchema
from corePlugins.json.schemaStore import JSON_SCHEMA_LOADER
from corePlugins.minecraft_data.fullData import getFullMcData


def initVersion() -> None:
	registerDPVersion(buildVersion41())


def loadJsonSchemas() -> dict[str, JsonSchema]:
	resourcesDir = os.path.join(os.path.dirname(__file__), "resources/")
	v23Dir = os.path.join(resourcesDir, "v23/")
	v23Schemas = {
		**JSON_SCHEMA_LOADER.loadSchemaLibrary('minecraft:tags', os.path.join(v23Dir, 'tags.json')),
		'minecraft:raw_json_text': JSON_SCHEMA_LOADER.loadSchema('minecraft:raw_json_text', os.path.join(v23Dir, 'rawJsonText.json')),
		'minecraft:raw_json_style': JSON_SCHEMA_LOADER.loadSchema('minecraft:raw_json_style', os.path.join(v23Dir, 'rawJsonStyle.json')),
		'minecraft:predicate': JSON_SCHEMA_LOADER.loadSchema('minecraft:predicate', os.path.join(v23Dir, 'predicate.json')),
		'minecraft:recipe': JSON_SCHEMA_LOADER.loadSchema('minecraft:recipe', os.path.join(v23Dir, 'recipe.json')),
		'minecraft:pack': JSON_SCHEMA_LOADER.loadSchema('minecraft:pack', os.path.join(v23Dir, 'pack.json')),
		'minecraft:loot_table': JSON_SCHEMA_LOADER.loadSchema('minecraft:loot_table', os.path.join(v23Dir, 'loot_table.json')),
		'minecraft:item_modifier': JSON_SCHEMA_LOADER.loadSchema('minecraft:item_modifier', os.path.join(v23Dir, 'item_modifier.json')),
		'minecraft:advancement': JSON_SCHEMA_LOADER.loadSchema('minecraft:advancement', os.path.join(v23Dir, 'advancements/advancement.json')),  # advancement.json is for datapack version 23!
	}
	return v23Schemas


JSON_SCHEMAS = loadJsonSchemas()


def buildVersion41() -> DPVersion:
	from .commands.v1_20_5_schema import COMMANDS_V41
	from .version23 import DATAPACK_CONTENTS
	return DPVersion(
		name='41',
		structure=buildEntryHandlers(DATAPACK_CONTENTS),
		jsonSchemas=JSON_SCHEMAS,
		mcFunctionSchema=COMMANDS_V41.buildSchema(getFullMcData('1.20.5'))
	)
