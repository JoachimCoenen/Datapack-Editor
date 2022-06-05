from Cat.utils import Anything
from model.datapack.json.argTypes import *
from model.datapack.json.utils import *
from model.json.core import *
from model.utils import MDStr

from model.datapack.json.schemas.Advancement.Conditions.damage_type import ADVANCEMENT_CONDITIONS_DAMAGE_TYPE
from model.datapack.json.schemas.Advancement.Conditions.entity import ADVANCEMENT_CONDITIONS_ENTITY

ADVANCEMENT_CONDITIONS_DAMAGE = JsonObjectSchema(properties=[

])
ADVANCEMENT_CONDITIONS_DAMAGE.properties = (
	PropertySchema(
		name="blocked",
		description=MDStr('Checks if the damage was successfully blocked.'),
		value=JsonBoolSchema(),
		optional=True
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
		name="source_entity",
		description=MDStr('Checks the entity that was the source of the damage (for example: The skeleton that shot the arrow).'),
		value=ADVANCEMENT_CONDITIONS_ENTITY,
		optional=True
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
		name="type",
		description=MDStr('Checks the type of damage done.'),
		value=ADVANCEMENT_CONDITIONS_DAMAGE_TYPE,
		optional=True
	)
)

ADVANCEMENT_CONDITIONS_DAMAGE.buildPropertiesDict()

