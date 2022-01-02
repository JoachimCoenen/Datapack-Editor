from model.commands.argumentTypes import *
from model.json.core import *

TAGS_BLOCKS = JsonObjectSchema(
	description='Allow grouping of items, blocks, fluids, entity types, or functions together using JSON files.',
	properties=[
		PropertySchema(
			name='replace',
			description=
			"Whether or not contents of this tag should completely replace tag contents from different lower priority data packs with the same resource location. "
			"When `false` the tag's content is appended to the contents of the higher priority data packs, instead.",
			value=JsonBoolSchema(),
			default=False,
		),
		PropertySchema(
			name='values',
			description="A list of mix and match of object names and tag names. For tags, recursive reference is possible, but a circular reference causes a loading failure. ",
			value=JsonArraySchema(
				element=JsonUnionSchema(
					options=[
						JsonStringSchema(
							description="An object's resource location in the form `namespace:path`.\nID of another tag of the same type in the form `#namespace:path`.",
							type=MINECRAFT_RESOURCE_LOCATION,
						),
						JsonObjectSchema(
							description="An entry with additional options. (1.16.2+) ",
							properties=[
								PropertySchema(
									name='id',
									description="A string in one of the string formats above.",
									value=JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION),
								),
								PropertySchema(
									name='required',
									description=
									"Whether or not loading this tag should fail if this entry is not found, `true` by default (also for the string entries). "
									"A tag that fails to load can still be referenced in any data pack and be (re)defined in other data packs. "
									"In other words, only the entries in this JSON file is ignored if this entry cannot be found.",
									value=JsonBoolSchema(),
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
