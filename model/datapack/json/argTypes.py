from model.json.core import JsonArgType

MINECRAFT_RESOURCE_LOCATION = JsonArgType(
	name='minecraft:resource_location',
	description="{{Arg desc|je=resource_location}}",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo:bar}}
	* {{cd|012}}""",
)


def init() -> None:
	pass


__all__ = [
	'MINECRAFT_RESOURCE_LOCATION',
]
