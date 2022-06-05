from model.datapack.json.argTypes import MINECRAFT_RESOURCE_LOCATION
from model.datapackContents import ResourceLocationSchema
from model.json.core import JsonStringSchema


def JsonResourceLocationSchema(name: str, doc: str = ''):
	return JsonStringSchema(type=MINECRAFT_RESOURCE_LOCATION, args=dict(schema=ResourceLocationSchema(doc, name)))


__all__ = [
	'JsonResourceLocationSchema',
]