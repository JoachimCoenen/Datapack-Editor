from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Iterable, Mapping, Optional, final

from PyQt5.QtWidgets import QWidget

from Cat.utils import Decorator
from model.Model import Datapack
from model.data.mcVersions import MCVersion
from model.datapack.datapackContents import ResourceLocation, MetaInfo, choicesFromResourceLocations, metaInfoFromResourceLocation, containsResourceLocation, ResourceLocationNode, \
	ResourceLocationSchema
from model.messages import *
from model.parsing.contextProvider import Suggestions, registerContextProvider, ContextProvider, Match, AddContextToDictDecorator, Context
from model.utils import Span, GeneralError, SemanticsError, MDStr, Position
from session.session import getSession


@registerContextProvider(ResourceLocationNode)
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

	def prepareTree(self) -> list[GeneralError]:
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
	def __init__(self, allowTags: bool):
		self._allowTags: bool = allowTags

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	@final
	def allowTags(self) -> bool:
		return self._allowTags

	@abstractmethod
	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		pass

	@abstractmethod
	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		pass

	@abstractmethod
	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		pass

	@staticmethod
	def _checkIsResourceLocation(node: ResourceLocationNode, errorsIO: list[GeneralError]) -> bool:
		if len(node.asString) == 0:
			errorsIO.append(SemanticsError(INTERNAL_ERROR_MSG.format(EXPECTED_MSG, '`ResourceLocation`'), node.span))
			return False
		return True

	def validate(self, value: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		if value.isTag:
			isValid = any(containsResourceLocation(value, tags) for dp in getSession().world.datapacks for tags in self.tagsFromDP(dp))
		else:
			isValid = any(containsResourceLocation(value, values) for dp in getSession().world.datapacks for values in self.valuesFromDP(dp))
			if not isValid:
				isValid = containsResourceLocation(value, self.valuesFromMC(getSession().minecraftData))
		if isValid:
			return None
		else:
			if value.isTag:
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format(f'{self.name} tag', value.asString), value.span, style='warning'))
				return
			else:
				errorsIO.append(SemanticsError(UNKNOWN_MSG.format(self.name, value.asString), value.span))
				return

	def getSuggestions(self, node: ResourceLocationNode, pos: Position, replaceCtx: str) -> Suggestions:
		class chain:
			def __init__(self, *iterables: Iterable):
				self.iterables = iterables

			def __iter__(self):
				for it in self.iterables:
					yield from it

		if self.allowTags:
			tagsIter = (self.tagsFromDP(dp) for dp in getSession().world.datapacks)
		else:
			tagsIter = ()

		locations = chain(*chain(
				*tagsIter,
				*(self.valuesFromDP(dp) for dp in getSession().world.datapacks)
			),
			self.valuesFromMC(getSession().minecraftData)
		)
		return choicesFromResourceLocations(node.asString, locations)

	def getDocumentation(self, node: ResourceLocationNode, pos: Position) -> MDStr:
		if not isinstance(node, ResourceLocation):
			return MDStr('')
		for dp in getSession().world.datapacks:
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
		if not isinstance(node, ResourceLocation):
			return ()
		if node.isTag:
			isValid = any(containsResourceLocation(node, tags) for dp in getSession().world.datapacks for tags in self.tagsFromDP(dp))
		else:
			isValid = any(containsResourceLocation(node, values) for dp in getSession().world.datapacks for values in self.valuesFromDP(dp))
		return [node.span] if isValid else ()

	def onIndicatorClicked(self, node: ResourceLocationNode, pos: Position, window: QWidget) -> None:
		if not isinstance(node, ResourceLocation):
			return None
		for dp in getSession().world.datapacks:
			for tags in self.tagsFromDP(dp):
				if (metaInfo := metaInfoFromResourceLocation(node, tags)) is not None:
					window._tryOpenOrSelectDocument(metaInfo.filePath)
					return
			for values in self.valuesFromDP(dp):
				if (metaInfo := metaInfoFromResourceLocation(node, values)) is not None:
					window._tryOpenOrSelectDocument(metaInfo.filePath)
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

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.advancements,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


@resourceLocationContext('block', allowTags=False)
@resourceLocationContext('block_type', allowTags=True)
class BlockContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'block'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.blocks,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.blocks


@resourceLocationContext('dimension', allowTags=False)
class DimensionContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'dimension'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.dimension,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.dimensions


@resourceLocationContext('entity_summon', allowTags=False)
@resourceLocationContext('entity_type', allowTags=True)
class EntityContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'entity'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.entity_types,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.entities


# EntitySummonContext, EntityTypeContext, EntityTypeLikeContext


@resourceLocationContext('fluid', allowTags=False)
@resourceLocationContext('fluid_type', allowTags=True)
class FluidContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'fluid'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.fluids,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.fluids


@resourceLocationContext('function', allowTags=True)
class FunctionContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'function'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.functions,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.functions,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


@resourceLocationContext('game_event', allowTags=True)
class GameEventsContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'game_event'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.game_events,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.gameEvents


@resourceLocationContext('enchantment', allowTags=False)
class ItemEnchantmentContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'enchantment'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.enchantments


@resourceLocationContext('item', allowTags=False)
@resourceLocationContext('item_type', allowTags=True)
class ItemsContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'item'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.items,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.items


@resourceLocationContext('mob_effect', allowTags=False)
class MobEffectContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'mob_effect'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.effects


@resourceLocationContext('particle', allowTags=False)
class ParticleContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'particle'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.particles


@resourceLocationContext('predicate', allowTags=False)
class PredicateContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'predicate'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.predicates,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


@resourceLocationContext('potion', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'potion'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.potions


@resourceLocationContext('biome', allowTags=False)
class BiomeIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'biome'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.biomes


@resourceLocationContext('structure', allowTags=False)
class StructureContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'structure'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.structures


@resourceLocationContext('condition', allowTags=False)
class ConditionIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'condition'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.predicateConditions


@resourceLocationContext('command_storage', allowTags=False)
class CommandStorageContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'command_storage'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


@resourceLocationContext('any_no_tag', allowTags=False)
@resourceLocationContext('any', allowTags=True)
class AnyContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'resource_location'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()

	def validate(self, node: ResourceLocationNode, errorsIO: list[GeneralError]) -> None:
		self._checkIsResourceLocation(node, errorsIO)


__all__ = [
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
