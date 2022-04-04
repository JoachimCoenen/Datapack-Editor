from abc import abstractmethod, ABC
from typing import Iterable, Mapping, Optional

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLStr
from model.Model import Datapack
from model.data.mcVersions import MCVersion
from model.datapackContents import ResourceLocation, MetaInfo, choicesFromResourceLocations, metaInfoFromResourceLocation, containsResourceLocation
from model.parsing.contextProvider import Suggestions
from model.utils import Span, GeneralError, SemanticsError
from session.session import getSession


class ResourceLocationContext(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	@abstractmethod
	def allowTags(self) -> bool:
		pass

	@abstractmethod
	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		pass

	@abstractmethod
	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		pass

	@abstractmethod
	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		pass

	def validate(self, value: ResourceLocation, span: Span, errorsIO: list[GeneralError]) -> None:
		if not isinstance(value, ResourceLocation):
			errorsIO.append(SemanticsError(f"Internal Error! expected ResourceLocation , but got '{value}'.", span))
			return

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
				errorsIO.append(SemanticsError(f"{self.name} tag '{value.asString}' is never defined.", span, style='warning'))
				return
			else:
				errorsIO.append(SemanticsError(f"Unknown {self.name} '{value.asString}'.", span))
				return

	def getSuggestions(self, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		class chain:
			def __init__(self, *iterables: Iterable):
				self.iterables = iterables

			def __iter__(self):
				for it in self.iterables:
					yield from it

		locations = chain(*chain(
			*(self.tagsFromDP(dp) for dp in getSession().world.datapacks),
			*(self.valuesFromDP(dp) for dp in getSession().world.datapacks)
		),
			self.valuesFromMC(getSession().minecraftData))
		return choicesFromResourceLocations(contextStr, locations)

	def getDocumentation(self, value: ResourceLocation) -> HTMLStr:
		if not isinstance(value, ResourceLocation):
			return HTMLStr('')
		if not value.isTag:
			for dp in getSession().world.datapacks:
				for values in self.valuesFromDP(dp):
					if (info := values.get(value)) is not None:
						return info.documentation
		return HTMLStr('')

	def getClickableRanges(self, value: ResourceLocation, span: Span) -> Optional[Iterable[Span]]:  # TODO: check for if not isinstance(value, ResourceLocation):
		if value.isTag:
			isValid = any(containsResourceLocation(value, tags) for dp in getSession().world.datapacks for tags in self.tagsFromDP(dp))
		else:
			isValid = any(containsResourceLocation(value, values) for dp in getSession().world.datapacks for values in self.valuesFromDP(dp))
		return [span] if isValid else []

	def onIndicatorClicked(self, value: ResourceLocation, window: QWidget) -> None:
		for dp in getSession().world.datapacks:
			for tags in self.tagsFromDP(dp):
				if (metaInfo := metaInfoFromResourceLocation(value, tags)) is not None:
					window._tryOpenOrSelectDocument(metaInfo.filePath)
					return
			for values in self.valuesFromDP(dp):
				if (metaInfo := metaInfoFromResourceLocation(value, values)) is not None:
					window._tryOpenOrSelectDocument(metaInfo.filePath)
					return


class DimensionContext(ResourceLocationContext):

	@property
	def name(self) -> str:
		return 'dimension'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.dimension,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.dimensions


class EntityTypeLikeContext(ResourceLocationContext, ABC):

	@property
	def name(self) -> str:
		return 'entity'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.entity_types,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.entities


class EntitySummonHandler(EntityTypeLikeContext):

	@property
	def allowTags(self) -> bool:
		return False


class EntityTypeHandler(EntityTypeLikeContext):

	@property
	def allowTags(self) -> bool:
		return True


class FunctionContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'function'

	@property
	def allowTags(self) -> bool:
		return True

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.functions,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.functions,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


class ItemEnchantmentContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'enchantment'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.enchantments


class MobEffectContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'mob effect'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.effects


class ParticleContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'particle'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.particles


class PredicateContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'predicate'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.predicates,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


class BiomeIdContext(ResourceLocationContext):
	@property
	def name(self) -> str:
		return 'biome'

	@property
	def allowTags(self) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.biomes

# (?<=def |\.)(name|allowTags|tagsFromDP|valuesFromDP|valuesFromMC)\b