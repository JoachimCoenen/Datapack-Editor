from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from itertools import chain
from typing import Optional, Collection, Iterable, final, Mapping, ClassVar

from base.model.parsing.parser import ParserBase
from cat.GUI.components.codeEditor import AutoCompletionTree, buildSimpleAutoCompletionTree, choicesFromAutoCompletionTree
from cat.utils import Deprecated, Decorator
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import ContextProvider, Match, Context, Suggestions, AddContextToDictDecorator
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePath, FilePathTpl
from base.model.project.project import Root
from base.model.session import getSession
from base.model.utils import Span, Position, GeneralError, SemanticsError, MDStr, LanguageId
from corePlugins.minecraft_data.fullData import getCurrentFullMcData, FullMCData
from corePlugins.minecraft_data.resourceLocation import isNamespaceValid, ResourceLocation, RESOURCE_LOCATION_PATTERN
from base.model.messages import INTERNAL_ERROR_MSG, EXPECTED_MSG, UNKNOWN_MSG, TRAILING_NOT_ALLOWED_MSG

RESOURCE_LOCATION_ID = LanguageId('minecraft:resource_location')


@dataclass(slots=True)
class ResourceLocationSchema(Schema):
	language: ClassVar[LanguageId] = RESOURCE_LOCATION_ID
	name: str

	def asString(self) -> str:
		return self.name


@dataclass(order=False, eq=False, unsafe_hash=False, frozen=True, slots=True)
class ResourceLocationNode(Node['ResourceLocationNode', ResourceLocationSchema], ResourceLocation):
	# TODO: maybe move to different module, or move ResourceLocationContext implementations?
	language: ClassVar[LanguageId] = RESOURCE_LOCATION_ID

	isValid: bool = field(default=True, compare=False, kw_only=True)
	pointsToFile: bool = field(default=False, compare=False, kw_only=True)

	@classmethod
	def fromString(cls, value: bytes, span: Span, schema: Optional[ResourceLocationSchema]) -> ResourceLocationNode:
		assert isinstance(value, bytes)
		value = bytesToStr(value)
		namespace, path, isTag = cls.splitString(value)
		return cls(namespace, path, isTag, span, schema)

	@property
	def children(self) -> Collection[ResourceLocationNode]:
		return ()

	__eq__ = ResourceLocation.__eq__
	__lt__ = ResourceLocation.__lt__
	__le__ = ResourceLocation.__le__
	__gt__ = ResourceLocation.__gt__
	__ge__ = ResourceLocation.__ge__
	__hash__ = ResourceLocation.__hash__


@dataclass
class ResourceLocationParser(ParserBase[ResourceLocationNode, ResourceLocationSchema]):
	ignoreTrailingChars: bool = False

	def parse(self) -> Optional[ResourceLocationNode]:
		p1 = self.currentPos
		location = self.tryReadRegex(RESOURCE_LOCATION_PATTERN)
		if location is None:
			self.errorMsg(EXPECTED_MSG, RESOURCE_LOCATION_ID, span=Span(p1))
			return None
		p2 = self.currentPos
		if not self.ignoreTrailingChars and self.cursor < self.length:
			self.advanceLineCounterAndUpdatePos(self.length)
			p3 = self.currentPos
			self.errorMsg(TRAILING_NOT_ALLOWED_MSG, "characters", span=Span(p2, p3))

		return ResourceLocationNode.fromString(location, Span(p1, p2), self.schema)


@dataclass
class MetaInfo:
	filePath: FilePathTpl = FilePathTpl(('', ''))
	# resourceLocation: ResourceLocation = ResourceLocation(None, '', False)

	@property
	def documentation(self) -> MDStr:
		return MDStr('')


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
	def valuesFromMC(self, mc: FullMCData) -> Collection[ResourceLocation]:
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
				isValid = containsResourceLocation(node, self.valuesFromMC(getCurrentFullMcData()))
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
			if mcValues := self.valuesFromMC(getCurrentFullMcData()):
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


def choicesFromResourceLocations(text: str, locations: Iterable[ResourceLocation]) -> list[str]:
	tree = autoCompletionTreeForResourceLocations(locations)
	return choicesFromAutoCompletionTree(tree, text)


def autoCompletionTreeForResourceLocations(locations: Iterable[ResourceLocation]) -> AutoCompletionTree:
	locationStrs = [l.asString for l in locations]
	mcLocationStrs = [l.asCompactString for l in locations if l.isMCNamespace]
	tree = buildSimpleAutoCompletionTree(chain(locationStrs, mcLocationStrs), (':', '/'))
	return tree


def containsResourceLocation(rl: ResourceLocation, container: Iterable[ResourceLocation]) -> bool:
	if rl.namespace == 'minecraft':
		rl = replace(rl, namespace=None)
	return rl in container


__all__ = [
	'RESOURCE_LOCATION_ID',
	'ResourceLocation',
	'ResourceLocationSchema',
	'ResourceLocationNode',
	'MetaInfo',
	'ResourceLocationCtxProvider',
	'ResourceLocationContext',
	'resourceLocationContext',
	'getResourceLocationContext',
	'containsResourceLocation',
	'isNamespaceValid',
]
