from Cat.utils import Anything
from model.datapack.json.argTypes import *
from model.datapack.json.utils import *
from model.json.core import *
from model.utils import MDStr



ADVANCEMENT_CONDITIONS_LOCATION = JsonObjectSchema(properties=[

])
ADVANCEMENT_CONDITIONS_LOCATION.properties = (
	PropertySchema(
		name="biome",
		description=MDStr('The biome the entity is currently in. This tag is a [[resource location]] for a biome (see [[Biome#Biome IDs]] for the ones used in vanilla).'),
		value=JsonResourceLocationSchema('biome', ''),
		optional=True
	),
	PropertySchema(
		name="block",
		description=MDStr('The block at the location.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="blocks",
				description=MDStr('A list of [[Java Edition data values#Blocks|block IDs]].'),
				value=JsonArraySchema(element=JsonResourceLocationSchema('block', '')),
				optional=True
			),
			PropertySchema(
				name="tag",
				description=MDStr('The block [[tag]].'),
				value=JsonStringSchema(),
				optional=True
			),
			PropertySchema(
				name="nbt",
				description=MDStr('The block NBT.'),
				value=JsonStringSchema(type=MINECRAFT_NBT_COMPOUND_TAG),
				optional=True
			),
			PropertySchema(
				name="state",
				description=MDStr("A map of block property names to values. Test will fail if the block doesn't match."),
				value=JsonObjectSchema(
					description=MDStr("''key'': None"),
					properties=[
						PropertySchema(
							name=Anything,
							description=MDStr('Block property key and value pair.'),
							value=JsonUnionSchema(options=[
								JsonUnionSchema(
									description=MDStr('Block property key and value pair.'),
									options=[
										JsonIntSchema(),
										JsonBoolSchema(),
										JsonStringSchema()
									]
								),
								JsonObjectSchema(properties=[
									PropertySchema(
										name="max",
										description=MDStr('A maximum value.'),
										value=JsonIntSchema(),
										optional=True
									),
									PropertySchema(
										name="min",
										description=MDStr('A minimum value.'),
										value=JsonIntSchema(),
										optional=True
									)
								])
							]),
							optional=True
						)
					]
				),
				optional=True
			)
		]),
		optional=True
	),
	PropertySchema(
		name="dimension",
		description=MDStr('The dimension the entity is currently in.'),
		value=JsonStringSchema(),
		optional=True
	),
	PropertySchema(
		name="feature",
		description=MDStr('{{until|java 1.19}}: The structure the entity is currently in. This tag is a [[resource location]] for a structure feature (see [[Java Edition data values#Structures]] for the ones used in vanilla).'),
		value=JsonResourceLocationSchema('structure', ''),
		optional=True
	),
	PropertySchema(
		name="fluid",
		description=MDStr('The fluid at the location.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="fluid",
				description=MDStr('The [[Java Edition data values#Fluids|fluid ID]].'),
				value=JsonResourceLocationSchema('fluid', ''),
				optional=True
			),
			PropertySchema(
				name="tag",
				description=MDStr('The fluid [[tag]].'),
				value=JsonStringSchema(),
				optional=True
			),
			PropertySchema(
				name="state",
				description=MDStr("A map of fluid property names to values. Test will fail if the fluid doesn't match."),
				value=JsonObjectSchema(
					description=MDStr("''key'': None"),
					properties=[
						PropertySchema(
							name=Anything,
							description=MDStr('Fluid property key and value pair.'),
							value=JsonUnionSchema(options=[
								JsonUnionSchema(
									description=MDStr('Fluid property key and value pair.'),
									options=[
										JsonIntSchema(),
										JsonBoolSchema(),
										JsonStringSchema()
									]
								),
								JsonObjectSchema(properties=[
									PropertySchema(
										name="max",
										description=MDStr('A maximum value.'),
										value=JsonIntSchema(),
										optional=True
									),
									PropertySchema(
										name="min",
										description=MDStr('A minimum value.'),
										value=JsonIntSchema(),
										optional=True
									)
								])
							]),
							optional=True
						)
					]
				),
				optional=True
			)
		]),
		optional=True
	),
	PropertySchema(
		name="light",
		description=MDStr('The light at the location.'),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="light",
				description=MDStr('The light Level of visible light. Calculated using: <code>(max(sky-darkening,block))</code>.'),
				value=JsonUnionSchema(options=[
					JsonIntSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('A maximum value.'),
							value=JsonIntSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('A minimum value.'),
							value=JsonIntSchema(),
							optional=True
						)
					])
				]),
				optional=True
			)
		]),
		optional=True
	),
	PropertySchema(
		name="position",
		description=MDStr(''),
		value=JsonObjectSchema(properties=[
			PropertySchema(
				name="x",
				description=MDStr('The x position.'),
				value=JsonUnionSchema(options=[
					JsonFloatSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('A maximum value.'),
							value=JsonFloatSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('A minimum value.'),
							value=JsonFloatSchema(),
							optional=True
						)
					])
				]),
				optional=True
			),
			PropertySchema(
				name="y",
				description=MDStr('The y position.'),
				value=JsonUnionSchema(options=[
					JsonFloatSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('A maximum value.'),
							value=JsonFloatSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('A minimum value.'),
							value=JsonFloatSchema(),
							optional=True
						)
					])
				]),
				optional=True
			),
			PropertySchema(
				name="z",
				description=MDStr('The z position.'),
				value=JsonUnionSchema(options=[
					JsonFloatSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('A maximum value.'),
							value=JsonFloatSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('A minimum value.'),
							value=JsonFloatSchema(),
							optional=True
						)
					])
				]),
				optional=True
			)
		]),
		optional=True
	),
	PropertySchema(
		name="smokey",
		description=MDStr('True if the block is closely above a campfire or soul campfire.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="structure",
		description=MDStr('{{upcoming|java 1.19}}: The structure the entity is currently in. This tag is a [[resource location]] for a structure feature (see [[Java Edition data values#Structures]] for the ones used in vanilla).'),
		value=JsonResourceLocationSchema('structure', ''),
		optional=True
	)
)

ADVANCEMENT_CONDITIONS_LOCATION.buildPropertiesDict()

