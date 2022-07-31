from model.json.core import *

DEPENDENCIES_SCHEMA = JsonArraySchema(
	element=JsonObjectSchema(
		properties=[
			PropertySchema(name='name', value=JsonStringSchema()),
			PropertySchema(name='mandatory', value=JsonBoolSchema()),
		]
	)
)
