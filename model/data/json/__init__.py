import os


def initPlugin() -> None:
	resourcesDir = os.path.join(os.path.dirname(__file__), "schemas/resources/")
	from model.data.json.schemas.tags import GLOBAL_SCHEMA_STORE
	GLOBAL_SCHEMA_STORE.registerSchemaLibrary('minecraft:tags', os.path.join(resourcesDir, 'tags.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('minecraft:raw_json_text', os.path.join(resourcesDir, 'rawJsonText.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('minecraft:predicate', os.path.join(resourcesDir, 'predicate.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('minecraft:recipe', os.path.join(resourcesDir, 'recipe.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('dpe:json_schema', os.path.join(resourcesDir, 'jsonSchema.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('dpe:dependencies', os.path.join(resourcesDir, 'dependencies.json'))
	GLOBAL_SCHEMA_STORE.registerSchema('minecraft:pack', os.path.join(resourcesDir, 'pack.json'))
