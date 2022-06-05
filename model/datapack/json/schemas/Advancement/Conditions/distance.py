from Cat.utils import Anything
from model.json.core import *
from model.utils import MDStr

ADVANCEMENT_CONDITIONS_DISTANCE = JsonObjectSchema(properties=[

])
ADVANCEMENT_CONDITIONS_DISTANCE.properties = (
	PropertySchema(
		name="absolute",
		description=MDStr('Test the distance between the two points in 3D space.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonFloatSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonFloatSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="horizontal",
		description=MDStr('Test the distance between the two points, ignoring the Y value.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonFloatSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonFloatSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="x",
		description=MDStr('Test the absolute difference between the X-coordinates of the two points.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonFloatSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonFloatSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="y",
		description=MDStr('Test the absolute difference between the Y-coordinates of the two points.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonFloatSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonFloatSchema(),
					optional=True
				)
			])
		]),
		optional=True
	),
	PropertySchema(
		name="z",
		description=MDStr('Test the absolute difference between the Z-coordinates of the two points.'),
		value=JsonUnionSchema(options=[
			JsonFloatSchema(),
			JsonObjectSchema(properties=[
				PropertySchema(
					name="max",
					description=MDStr('The maximum value.'),
					value=JsonFloatSchema(),
					optional=True
				),
				PropertySchema(
					name="min",
					description=MDStr('The minimum value.'),
					value=JsonFloatSchema(),
					optional=True
				)
			])
		]),
		optional=True
	)
)

ADVANCEMENT_CONDITIONS_DISTANCE.buildPropertiesDict()

