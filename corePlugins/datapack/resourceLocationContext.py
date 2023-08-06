from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import replace
from typing import Iterable, Mapping, Optional, final, Collection

from Cat.utils import Decorator, Deprecated
from base.model.pathUtils import FilePath
from base.model.project.project import Root
from base.model.session import getSession
from model.messages import *
# from corePlugins.mcFunctionSchemaTEMP.mcVersions import MCVersion
from .datapackContents import ResourceLocation, MetaInfo, choicesFromResourceLocations, containsResourceLocation, ResourceLocationNode, ResourceLocationSchema, DatapackContents
from base.model.parsing.contextProvider import Suggestions, ContextProvider, Match, AddContextToDictDecorator, Context
from base.model.utils import Span, GeneralError, SemanticsError, MDStr, Position


@Deprecated
class MCVersion:
	# just an alias, or forward definition!
	blocks: set[ResourceLocation]
	fluids: set[ResourceLocation]
	items: set[ResourceLocation]

	entities: set[ResourceLocation]
	potions: set[ResourceLocation]
	effects: set[ResourceLocation]
	enchantments: set[ResourceLocation]
	biomes: set[ResourceLocation]
	particles: set[ResourceLocation]
	dimensions: set[ResourceLocation]
	predicateConditions: set[ResourceLocation]
	gameEvents: set[ResourceLocation]  # introduced in version 1.19
	structures: set[ResourceLocation]
	pass


class ResourceLocationCtxProvider(ContextProvider[ResourceLocationNode]):

	def getBestMatch(self, pos: Position) -> Match[ResourceLocationNode]:
		tree = self.tree
		if pos.index < tree.span.start.index:
			return Match(None, None, tree, [])
		elif tree.span.end.index < pos.index:
			return Match(tree, None, None, [])
		else:
			return Match(None, tree, None, [])

	def getContext(self, node: ResourceLocationNode) -> Optional[Context]:
		schema = node.schema
		if isinstance(schema, ResourceLocationSchema):
			return getResourceLocationContext(schema.name)
		return None

	def prepareTree(self, filePath: FilePath) -> list[GeneralError]:
		pass

	def getSuggestions(self, pos: Position, replaceCtx: str) -> Suggestions:
		return super().getSuggestions(pos, replaceCtx)

	def getCallTips(self, pos: Position) -> list[str]:
		return ['?']

	def getClickableRangesInternal(self, span: Span) -> Iterable[Span]:
		if (ctx := self.getContext(self.tree)) is not None:
			return ctx.getClickableRanges(self.tree)
		return ()


class ResourceLocationContext(Context[ResourceLocationNode], ABC):
	def __init__(self, allowTags: bool, onlyTags: bool = False):
		self._allowTags: bool = allowTags
		self._onlyTags: bool = onlyTags

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	@final
	def allowTags(self) -> bool:
		return self._allowTags

	@property
	@final
	def onlyTags(self) -> bool:
		return self._onlyTags

	@abstractmethod
	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		pass

	@abstractmethod
	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		pass

	@abstractmethod
	@Deprecated
	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		pass

	@staticmethod
	def _checkIsResourceLocation(node: ResourceLocationNode, errorsIO: list[GeneralError]) -> bool:
		if len(node.asString) == 0:
			errorsIO.append(SemanticsError(INTERNAL_ERROR_MSG.format(EXPECTED_MSG, '`ResourceLocation`'), node.span))
			return False
		return True

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		if not self.checkCorrectNodeType(node, ResourceLocationNode):
			return
		if self.onlyTags:
			node = replace(node, isTag=True)
		if node.isTag:
			isValid = pointsToFile = any(containsResourceLocation(node, tags) for dp in getSession().project.allRoots for tags in self.tagsFromDP(dp))
		else:
			isValid = pointsToFile = any(containsResourceLocation(node, values) for dp in getSession().project.allRoots for values in self.valuesFromDP(dp))
			if not isValid:
				isValid = containsResourceLocation(node, self.valuesFromMC(getSession().minecraftData))
				pointsToFile = False
		object.__setattr__(node, 'pointsToFile', pointsToFile)
		object.__setattr__(node, 'isValid', isValid)
		if not isValid:
			if node.isTag:
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format(f'{self.name} tag', node.asString), node.span, style='warning'))
			else:
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format(self.name, node.asString), node.span))

	def getSuggestions(self, node: ResourceLocationNode, pos: Position, replaceCtx: str) -> Suggestions:
		if not self.checkCorrectNodeType(node, ResourceLocationNode):
			return []
		locations: list[ResourceLocation] = []

		if self.allowTags:
			for dp in getSession().project.allRoots:
				for tags in self.tagsFromDP(dp):
					locations.extend(tags)

		if not self.onlyTags:
			for dp in getSession().project.allRoots:
				for values in self.valuesFromDP(dp):
					locations.extend(values)
			if mcValues := self.valuesFromMC(getSession().minecraftData):
				locations.extend(mcValues)

		if self.onlyTags:
			node = replace(node, isTag=True)

		result = choicesFromResourceLocations(node.asString, locations)
		if self.onlyTags:
			result = [s.removeprefix('#') for s in result]
		return result

	def getDocumentation(self, node: ResourceLocationNode, pos: Position) -> MDStr:
		if not self.checkCorrectNodeType(node, ResourceLocationNode):
			return MDStr('')
		for dp in getSession().project.allRoots:
			if self.onlyTags:
				node = replace(node, isTag=True)
			if node.isTag:
				for tags in self.tagsFromDP(dp):
					if (info := tags.get(node)) is not None:
						return info.documentation
			else:
				for values in self.valuesFromDP(dp):
					if (info := values.get(node)) is not None:
						return info.documentation
		return MDStr('')

	def getClickableRanges(self, node: ResourceLocationNode) -> Iterable[Span]:  # TODO: check for if not isinstance(value, ResourceLocation):
		if not self.checkCorrectNodeType(node, ResourceLocationNode):
			return ()
		return [node.span] if node.pointsToFile else ()

	def onIndicatorClicked(self, node: ResourceLocationNode, pos: Position) -> None:
		if not self.checkCorrectNodeType(node, ResourceLocationNode):
			return None
		if self.onlyTags:
			node = replace(node, isTag=True)
		for dp in getSession().project.allRoots:
			for tags in self.tagsFromDP(dp):
				# TODO: show prompt, when there are multiple files for this resource location.
				if (metaInfo := tags.get(node)) is not None:
					getSession().tryOpenOrSelectDocument(metaInfo.filePath)
					return
			for values in self.valuesFromDP(dp):
				if (metaInfo := values.get(node)) is not None:
					getSession().tryOpenOrSelectDocument(metaInfo.filePath)
					return


__resourceLocationContexts: dict[str, ResourceLocationContext] = {}
resourceLocationContext = Decorator(AddContextToDictDecorator[ResourceLocationContext](__resourceLocationContexts))


def getResourceLocationContext(aType: str) -> Optional[ResourceLocationContext]:
	return __resourceLocationContexts.get(aType, None)


@resourceLocationContext('advancement', allowTags=False)
class DimensionContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'advancement'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.advancements,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('block', allowTags=False)
@resourceLocationContext('block_type', allowTags=True)
@resourceLocationContext('block_tag', allowTags=True, onlyTags=True)
class BlockContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'block'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.blocks,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.blocks


@resourceLocationContext('dimension', allowTags=False)
class DimensionContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'dimension'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.dimension,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.dimensions


@resourceLocationContext('entity_summon', allowTags=False)
@resourceLocationContext('entity_type', allowTags=True)
class EntityContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'entity'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.entity_types,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.entities


# EntitySummonContext, EntityTypeContext, EntityTypeLikeContext


@resourceLocationContext('fluid', allowTags=False)
@resourceLocationContext('fluid_type', allowTags=True)
class FluidContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'fluid'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.fluids,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.fluids


@resourceLocationContext('function', allowTags=True)
class FunctionContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'function'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.functions,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.functions,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('game_event', allowTags=True)
class GameEventsContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'game_event'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.game_events,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.gameEvents


@resourceLocationContext('enchantment', allowTags=False)
class ItemEnchantmentContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'enchantment'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.enchantments


@resourceLocationContext('item', allowTags=False)
@resourceLocationContext('item_type', allowTags=True)
@resourceLocationContext('item_tag', allowTags=True, onlyTags=True)
class ItemsContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'item'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.tags.items,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.items


@resourceLocationContext('mob_effect', allowTags=False)
class MobEffectContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'mob_effect'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.effects


@resourceLocationContext('particle', allowTags=False)
class ParticleContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'particle'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.particles


@resourceLocationContext('predicate', allowTags=False)
class PredicateContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'predicate'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return (contents.predicates,) if (contents := dp.indexBundles.get(DatapackContents)) is not None else ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return ()


@resourceLocationContext('potion', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'potion'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.potions


@resourceLocationContext('biome', allowTags=False)
class BiomeIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'biome'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.biomes


@resourceLocationContext('structure', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'structure'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.structures


@resourceLocationContext('condition', allowTags=False)
class ConditionIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'condition'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return mc.predicateConditions


@resourceLocationContext('command_storage', allowTags=False)
class CommandStorageContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'command_storage'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


@resourceLocationContext('any_no_tag', allowTags=False)
@resourceLocationContext('any', allowTags=True)
class AnyContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'resource_location'

	def tagsFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromDP(self, dp: Root) -> tuple[Mapping[ResourceLocation, MetaInfo], ...]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Collection[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


__all__ = [
	'ResourceLocationCtxProvider',
	'ResourceLocationContext',
	'BlockContext',
	'DimensionContext',
	'EntityContext',
	'FluidContext',
	'FunctionContext',
	'ItemEnchantmentContext',
	'ItemsContext',
	'MobEffectContext',
	'ParticleContext',
	'PredicateContext',
	'BiomeIdContext',
	'AnyContext',
]
