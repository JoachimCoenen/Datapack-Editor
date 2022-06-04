from Cat.utils import Anything
from model.json.core import *
from model.utils import MDStr

ADVANCEMENT_CONDITIONS_DAMAGE = JsonObjectSchema(properties=[
	PropertySchema(
		name="blocked",
		description=MDStr('Checks if the damage was successfully blocked.'),
		value=JsonBoolSchema()
	),
	PropertySchema(
		name="dealt",
		description=MDStr('Checks the amount of incoming damage before damage reduction.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('A maximum value.'),
					value=JsonFloatSchema()
				),
				PropertySchema(
					name="min",
					description=MDStr('A minimum value.'),
					value=JsonFloatSchema()
				)
			])
		])
	),
	PropertySchema(
		name="source_entity",
		description=MDStr('Checks the entity that was the source of the damage (for example: The skeleton that shot the arrow).'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_ENTITY.properties
		])
	),
	PropertySchema(
		name="taken",
		description=MDStr('Checks the amount of incoming damage after damage reduction.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('A maximum value.'),
					value=JsonFloatSchema()
				),
				PropertySchema(
					name="min",
					description=MDStr('A minimum value.'),
					value=JsonFloatSchema()
				)
			])
		])
	),
	PropertySchema(
		name="type",
		description=MDStr('Checks the type of damage done.'),
		value=JsonObjectSchema(properties=[
			# *ADVANCEMENT_CONDITIONS_DAMAGE_TYPE.properties
		])
	)
])

