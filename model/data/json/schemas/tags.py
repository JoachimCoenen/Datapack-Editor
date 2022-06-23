from model.data.json.argTypes import MINECRAFT_RESOURCE_LOCATION
from model.datapackContents import ResourceLocationSchema
from model.json.core import *
from model.utils import MDStr


def buildTagsSchema(schema: ResourceLocationSchema) -> JsonObjectSchema:
	return JsonObjectSchema(
		description=MDStr('Allow grouping of items, blocks, fluids, entity types, or functions together using JSON files.'),
		properties=[
			PropertySchema(
				name='description',
				description=MDStr("A textual description of the contents of this file. Will be ignored by Minecraft."),
				value=JsonStringSchema(),
				optional=True,
			),
			PropertySchema(
				name='replace',
				description=MDStr(
					"Whether or not contents of this tag should completely replace tag contents from different lower priority data packs with the same resource location. "
					"When `false` the tag's content is appended to the contents of the higher priority data packs, instead."),
				value=JsonBoolSchema(),
				optional=True,
				default=False,
			),
			PropertySchema(
				name='values',
				description=MDStr("A list of mix and match of object names and tag names. For tags, recursive reference is possible, but a circular reference causes a loading failure. "),
				value=JsonArraySchema(
					element=JsonUnionSchema(
						options=[
							JsonStringSchema(
								description=MDStr("An object's resource location in the form `namespace:path`.\nID of another tag of the same type in the form `#namespace:path`."),
								type=MINECRAFT_RESOURCE_LOCATION,
								args=dict(schema=schema)
							),
							JsonObjectSchema(
								description=MDStr("An entry with additional options. (1.16.2+) "),
								properties=[
									PropertySchema(
										name='id',
										description=MDStr("A string in one of the string formats above."),
										value=JsonStringSchema(
											type=MINECRAFT_RESOURCE_LOCATION,
											args=dict(schema=schema)
										),
									),
									PropertySchema(
										name='required',
										description=MDStr(
											"Whether or not loading this tag should fail if this entry is not found, `true` by default (also for the string entries). "
											"A tag that fails to load can still be referenced in any data pack and be (re)defined in other data packs. "
											"In other words, only the entries in this JSON file is ignored if this entry cannot be found."),
										value=JsonBoolSchema(),
										optional=True,
										default=True,
									),
								],
							),
						],
					),
				),
			),
		]
	)


TAGS_BLOCKS = buildTagsSchema(ResourceLocationSchema('', 'block_type'))  # rlc.BlockContext())
TAGS_ENTITY_TYPES = buildTagsSchema(ResourceLocationSchema('', 'entity_type'))  # rlc.EntityTypeContext())
TAGS_FLUIDS = buildTagsSchema(ResourceLocationSchema('', 'fluid_type'))  # rlc.FluidContext())
TAGS_FUNCTIONS = buildTagsSchema(ResourceLocationSchema('', 'function'))  # rlc.FunctionContext())
TAGS_GAME_EVENTS = buildTagsSchema(ResourceLocationSchema('', 'game_event'))  # rlc.GameEventsContext())
TAGS_ITEMS = buildTagsSchema(ResourceLocationSchema('', 'item_type'))  # rlc.ItemsContext())

__all__ = [
	'TAGS_BLOCKS',
	'TAGS_ENTITY_TYPES',
	'TAGS_FLUIDS',
	'TAGS_FUNCTIONS',
	'TAGS_GAME_EVENTS',
	'TAGS_ITEMS',
]
