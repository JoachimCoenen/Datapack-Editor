from model.json.core import JsonArgType
from model.utils import MDStr

MINECRAFT_RESOURCE_LOCATION = JsonArgType(
	name='minecraft:resource_location',
	description=MDStr("{{Arg desc|je=resource_location}}"),
	description2=MDStr(""),
	examples=MDStr(
		"* {{cd|foo}}\n"
		"* {{cd|foo:bar}}\n"
		"* {{cd|012}}\n"
	),
)


def init() -> None:
	pass


__all__ = [
	'MINECRAFT_RESOURCE_LOCATION',
]
