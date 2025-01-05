from corePlugins.minecraft.resourceLocation import ResourceLocationSchema
from corePlugins.minecraft_data.fullData import getCurrentFullMcData
from corePlugins.minecraft_data.resourceLocation import ResourceLocation
from .predicateArgs import PredicateArgOptions, PredicateArgInfo


def getItemComponentArgInfo(resLoc: ResourceLocation) -> PredicateArgInfo:
	if resLoc in getCurrentFullMcData().itemComponents:
		valueSchema = f'{resLoc.actualNamespace}:item_components/{resLoc.path}'
	else:
		valueSchema = None
	if resLoc in getCurrentFullMcData().itemSubPredicates:
		subPredicateSchema = f'{resLoc.actualNamespace}:item_sub_predicates/{resLoc.path}'
	else:
		subPredicateSchema = None

	if valueSchema is None and subPredicateSchema is None:
		valueSchema = 'dpe:anything'
		subPredicateSchema = 'dpe:anything'

	return PredicateArgInfo(
		name=resLoc.asQualifiedString,
		valueSchema=valueSchema,
		subPredicateSchema=subPredicateSchema,
		description=""
	)


ITEM_COMPONENT_ARG_OPTIONS: PredicateArgOptions = PredicateArgOptions(
	keySchema=ResourceLocationSchema('', 'item_components', allowTags=False),
	getArgsInfo=lambda key: getItemComponentArgInfo(key),
	description=""
)


__all__ = [
	'ITEM_COMPONENT_ARG_OPTIONS',
]
