from Cat.utils import Anything
from model.json.core import *
from model.utils import MDStr

ADVANCEMENT_CONDITIONS_ITEM = JsonObjectSchema(properties=[
	PropertySchema(
		name="count",
		description=MDStr('Amount of the item.'),
		value=JsonUnionSchema(options=[
			JsonIntSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonIntSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonIntSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="durability",
		description=MDStr('The durability of the item.'),
		value=JsonUnionSchema(options=[
			JsonIntSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonIntSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonIntSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="enchantments",
		description=MDStr('List of enchantments.'),
		value=JsonArraySchema(element=JsonObjectSchema(properties=[
			PropertySchema(
				name="enchantment",
				description=MDStr('An [[Java Edition data values#Enchantments|enchantment ID]].'),
				value=JsonStringSchema(),
				optional=True
			),
			PropertySchema(
				name="levels",
				description=MDStr('The level of the enchantment.'),
				value=JsonUnionSchema(options=[
					JsonIntSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('The maximum value.'),
							value=JsonIntSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('The minimum value.'),
							value=JsonIntSchema(),
							optional=True
						)
					])
				]),
				optional=True
			)
		])),
		optional=True
	),
	PropertySchema(
		name="stored_enchantments",
		description=MDStr('List of stored enchantments.'),
		value=JsonArraySchema(element=JsonObjectSchema(properties=[
			PropertySchema(
				name="enchantment",
				description=MDStr('An [[Java Edition data values#Enchantments|enchantment ID]].'),
				value=JsonStringSchema(),
				optional=True
			),
			PropertySchema(
				name="levels",
				description=MDStr('The level of the enchantment.'),
				value=JsonUnionSchema(options=[
					JsonIntSchema(),
					JsonObjectSchema(properties=[
						PropertySchema(
							name="max",
							description=MDStr('The maximum value.'),
							value=JsonIntSchema(),
							optional=True
						),
						PropertySchema(
							name="min",
							description=MDStr('The minimum value.'),
							value=JsonIntSchema(),
							optional=True
						)
					])
				]),
				optional=True
			)
		])),
		optional=True
	),
	PropertySchema(
		name="items",
		description=MDStr('A list of [[Java Edition data values#Items|item IDs]].'),
		value=JsonArraySchema(element=JsonStringSchema()),
		optional=True
	),
	PropertySchema(
		name="nbt",
		description=MDStr('An NBT string.'),
		value=JsonStringSchema(),
		optional=True
	),
	PropertySchema(
		name="potion",
		description=MDStr('A [[Potion#Item data|brewed potion ID]].'),
		value=JsonStringSchema(),
		optional=True
	),
	PropertySchema(
		name="tag",
		description=MDStr('An item data pack tag.'),
		value=JsonStringSchema(),
		optional=True
	)
])

