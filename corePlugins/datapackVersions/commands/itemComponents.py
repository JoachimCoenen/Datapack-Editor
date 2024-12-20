from corePlugins.mcFunction.command import ArgumentSchema
from corePlugins.mcFunction.filterArgs import FilterArgOptions, FilterArgumentInfo, NegationStyle
from corePlugins.minecraft_data.fullData import getCurrentFullMcData
from corePlugins.minecraft_data.resourceLocation import ResourceLocation
from .argumentTypes import *


def getItemComponentArgInfo(resLoc: ResourceLocation) -> FilterArgumentInfo:
	if resLoc in getCurrentFullMcData().itemComponents:
		schema = f'{resLoc.actualNamespace}:item_components/{resLoc.path}'
	else:
		schema = None

	return FilterArgumentInfo(
		name=resLoc.asQualifiedString,
		valueSchema=ArgumentSchema(
			name=resLoc.asQualifiedString,
			type=MINECRAFT_NBT_TAG,
			args=dict(schema=schema)
		),
		multipleAllowed=False,
		isNegatable=True,
		canBeEmpty=True,
		description=""
	)


ITEM_COMPONENT_ARG_OPTIONS: FilterArgOptions = FilterArgOptions(
	opening=b'[',
	closing=b']',
	allowTrailingComma=False,
	negationStyle=NegationStyle.KEY_NEGATION,
	keySchema=ArgumentSchema(
		name='key',
		type=MINECRAFT_RESOURCE_LOCATION,
		args=dict(schema='item_components'),
	),
	getArgsInfo=lambda key: getItemComponentArgInfo(key.value),
	description=""
)


__all__ = [
	'ITEM_COMPONENT_ARG_OPTIONS',
]
