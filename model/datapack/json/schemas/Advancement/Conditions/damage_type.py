from Cat.utils import Anything
from model.datapack.json.schemas.Advancement.Conditions.entity import ADVANCEMENT_CONDITIONS_ENTITY
from model.json.core import *
from model.utils import MDStr

ADVANCEMENT_CONDITIONS_DAMAGE_TYPE = JsonObjectSchema(properties=[

])
ADVANCEMENT_CONDITIONS_DAMAGE_TYPE.properties = (
	PropertySchema(
		name="bypasses_armor",
		description=MDStr('Checks if the damage bypassed the armor of the player (suffocation damage predominantly).'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="bypasses_invulnerability",
		description=MDStr('Checks if the damage bypassed the invulnerability status of the player (void or {{cmd|kill}} damage). '),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="bypasses_magic",
		description=MDStr('Checks if the damage was caused by starvation.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="direct_entity",
		description=MDStr('The entity that was the direct cause of the damage.'),
		value=ADVANCEMENT_CONDITIONS_ENTITY,
		optional=True
	),
	PropertySchema(
		name="is_explosion",
		description=MDStr('Checks if the damage originated from an explosion.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="is_fire",
		description=MDStr('Checks if the damage originated from fire.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="is_magic",
		description=MDStr('Checks if the damage originated from magic.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="is_projectile",
		description=MDStr('Checks if the damage originated from a projectile.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="is_lightning",
		description=MDStr('Checks if the damage originated from lightning.'),
		value=JsonBoolSchema(),
		optional=True
	),
	PropertySchema(
		name="source_entity",
		description=MDStr('Checks the entity that was the source of the damage (for example: The skeleton that shot the arrow).'),
		value=ADVANCEMENT_CONDITIONS_ENTITY,
		optional=True
	)
)

ADVANCEMENT_CONDITIONS_DAMAGE_TYPE.buildPropertiesDict()

