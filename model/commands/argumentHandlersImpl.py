import re
from abc import abstractmethod
from dataclasses import replace
from itertools import chain
from json import JSONDecodeError
from typing import Optional, Iterable, Mapping

from PyQt5.QtWidgets import QWidget

from Cat.Serializable import SerializedPropertyABC
from Cat.utils import HTMLStr, abstract
from Cat.utils.collections_ import OrderedDict
from model.Model import Datapack
from model.commands.argumentHandlers import argumentHandler, ArgumentHandler, missingArgumentParser, makeParsedArgument, defaultDocumentationProvider, Suggestions, \
	getArgumentHandler
from model.commands.argumentParsersImpl import _parse3dPos, tryReadNBTCompoundTag, _parseResourceLocation, _parse2dPos, _get3dPosSuggestions, _get2dPosSuggestions
from model.commands.argumentTypes import *
from model.commands.argumentValues import BlockState, ItemStack, FilterArguments, TargetSelector
from model.commands.command import ArgumentInfo
from model.commands.filterArgs import parseFilterArgs, suggestionsForFilterArgs, clickableRangesForFilterArgs, onIndicatorClickedForFilterArgs
from model.commands.parsedCommands import ParsedArgument, ParsedCommandPart
from model.commands.snbt import parseNBTPath, parseNBTTag
from model.commands.stringReader import StringReader
from model.commands.targetSelector import TARGET_SELECTOR_ARGUMENTS_DICT
from model.commands.utils import CommandSyntaxError, CommandSemanticsError
from model.data.mcVersions import MCVersion
from model.datapackContents import ResourceLocation, MetaInfo, choicesFromResourceLocations
from model.utils import Span, Position
from model.pathUtils import FilePath
from session.session import getSession


def _init():
	pass  # do not remove!


def _openOrSelectDocument(window: QWidget, filePath: FilePath, selectedPosition: Optional[Position] = None):
	window._tryOpenOrSelectDocument(filePath, selectedPosition=selectedPosition)  # very bad...


def _containsResourceLocation(rl: ResourceLocation, container: Iterable[ResourceLocation]) -> bool:
	if rl.namespace == 'minecraft':
		rl = replace(rl, namespace=None)
	return rl in container


def _choicesForDatapackContents(text: str, prop: SerializedPropertyABC[Datapack, OrderedDict[ResourceLocation, MetaInfo]]) -> Suggestions:
	locations = [b for dp in getSession().world.datapacks for b in prop.get(dp)]
	return choicesFromResourceLocations(text, locations)


def _openFromDatapackContents(window: QWidget, rl: ResourceLocation, prop: SerializedPropertyABC[Datapack, OrderedDict[ResourceLocation, MetaInfo]]) -> bool:
	for dp in getSession().world.datapacks:
		# TODO: show prompt, when there are multiple files this applies to.
		if (file := prop.get(dp).get(rl)) is not None:
			fp = file.filePath
			_openOrSelectDocument(window, fp)
			return True
	return False


def _openFromResourceLocation(window: QWidget, rl: ResourceLocation, values: Mapping[ResourceLocation, MetaInfo]) -> bool:
	# TODO: show prompt, when there are multiple files this applies to.
	if (file := values.get(rl)) is not None:
		fp = file.filePath
		_openOrSelectDocument(window, fp)
		return True
	return False


@abstract
class ResourceLocationLikeHandler(ArgumentHandler):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@abstractmethod
	def allowTags(self, ai: ArgumentInfo) -> bool:
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

	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=self.allowTags(ai))

	def validate(self, argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
		value: ResourceLocation = argument.value
		if not isinstance(value, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{value}'.", argument.span)

		if value.isTag:
			isValid = any(_containsResourceLocation(value, tags) for dp in getSession().world.datapacks for tags in self.tagsFromDP(dp))
		else:
			isValid = any(_containsResourceLocation(value, values) for dp in getSession().world.datapacks for values in self.valuesFromDP(dp))
			if not isValid:
				isValid = _containsResourceLocation(value, self.valuesFromMC(getSession().minecraftData))
		if isValid:
			return None
		else:
			if value.isTag:
				return CommandSemanticsError(f"{self.name} tag '{value.asString}' is never defined.", argument.span, style='warning')
			else:
				return CommandSemanticsError(f"Unknown {self.name} '{value.asString}'.", argument.span)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
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

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		value: ResourceLocation = argument.value
		if value.isTag:
			isValid = any(_containsResourceLocation(value, tags) for dp in getSession().world.datapacks for tags in self.tagsFromDP(dp))
		else:
			isValid = any(_containsResourceLocation(value, values) for dp in getSession().world.datapacks for values in self.valuesFromDP(dp))
		return [argument.span] if isValid else []

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		for dp in getSession().world.datapacks:
			for tags in self.tagsFromDP(dp):
				if _openFromResourceLocation(window, argument.value, tags):
					return
			for values in self.valuesFromDP(dp):
				if _openFromResourceLocation(window, argument.value, values):
					return


@argumentHandler(BRIGADIER_BOOL.name)
class BoolHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadBoolean()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['true', 'false']


@argumentHandler(BRIGADIER_DOUBLE.name)
class DoubleHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentHandler(BRIGADIER_FLOAT.name)
class FloatHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentHandler(BRIGADIER_INTEGER.name)
class IntegerHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentHandler(BRIGADIER_LONG.name)
class LongHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentHandler(BRIGADIER_STRING.name)
class StringHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadString()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentHandler(MINECRAFT_ANGLE.name)
class AngleHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		angle = sr.tryReadTildeNotation()
		if angle is None:
			angle = sr.tryReadFloat()
		if angle is None:
			return None
		return makeParsedArgument(sr, ai, value=angle)


@argumentHandler(MINECRAFT_BLOCK_POS.name)
class BlockPosHandler(ArgumentHandler):
	@staticmethod
	def useFloat(ai: ArgumentInfo):
		return ai.args is not None and ai.args.get('type', None) is float

	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=self.useFloat(ai), errorsIO=errorsIO)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, contextStr, cursorPos, useFloat=self.useFloat(ai))


@argumentHandler(MINECRAFT_BLOCK_STATE.name)
class BlockStateHandler(ArgumentHandler):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# block_id[block_states]{data_tags}
		blockID = sr.tryReadResourceLocation(allowTag=self._allowTag)
		if blockID is None:
			return None
		blockID = ResourceLocation.fromString(blockID)
		# block states:
		blockStatesDict = getSession().minecraftData.getBlockStatesDict(blockID)
		states: Optional[FilterArguments] = parseFilterArgs(sr, blockStatesDict, errorsIO=errorsIO)
		if states is not None:
			sr.mergeLastSave()
		else:
			states = FilterArguments()
		# data tags:
		if sr.tryConsumeChar('{'):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		blockPredicate = BlockState(blockId=blockID, states=states, nbt=nbt)
		return makeParsedArgument(sr, ai, value=blockPredicate)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		blockState: BlockState = argument.value
		if not isinstance(blockState, BlockState):
			return CommandSemanticsError(f"Internal Error! expected BlockState , but got'{blockState}'.", argument.span)

		blockId = blockState.blockId
		if blockId.isTag:
			isValid = any(blockId in dp.contents.tags.blocks for dp in getSession().world.datapacks)
			if not isValid:
				return CommandSemanticsError(f"Unknown block tag '{blockId.asString}'.", argument.span, style='error')
		else:
			if not _containsResourceLocation(blockId, getSession().minecraftData.blocks):
				return CommandSemanticsError(f"Unknown block id '{blockId.asString}'.", argument.span, style='warning')
		return None

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		suggestions: Suggestions = []
		if '[' in contextStr or cursorPos == len(contextStr):
			sr = StringReader(contextStr, 0, 0, contextStr)
			blockID = sr.tryReadResourceLocation(allowTag=self._allowTag)
			if blockID is not None:
				if cursorPos >= len(blockID):
					blockStatesDict = getSession().minecraftData.getBlockStatesDict(ResourceLocation.fromString(blockID))
					argsStart = sr.currentPos.index
					suggestions += suggestionsForFilterArgs(sr.tryReadRemaining() or '', cursorPos - argsStart, replaceCtx, blockStatesDict)
					if cursorPos > len(blockID):  # we're inside the block states, so don't suggest blocks anymore.
						return suggestions
		suggestions += choicesFromResourceLocations(contextStr, getSession().minecraftData.blocks)
		if self._allowTag:
			tags = _choicesForDatapackContents(contextStr, Datapack.contents.tags.blocks)
			suggestions += tags
		return suggestions

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		blockState: BlockState = argument.value
		if not isinstance(blockState, BlockState):
			return None

		blockId = blockState.blockId
		start = argument.span.start
		end = argument.span.end
		end = replace(
			end,
			column=min(end.column, start.column + len(blockId.asString)),
			index=min(end.index, start.index + len(blockId.asString))
		)

		ranges = []
		if blockId.isTag:
			span = Span(start, end)
			ranges.append(span)

		ranges += clickableRangesForFilterArgs(blockState.states)

		return ranges

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		blockState: BlockState = argument.value
		if position.index <= argument.start.index + len(blockState.blockId.asString):
			_openFromDatapackContents(window, blockState.blockId, Datapack.contents.tags.blocks)
		else:
			onIndicatorClickedForFilterArgs(blockState.states, position, window)


@argumentHandler(MINECRAFT_BLOCK_PREDICATE.name)
class BlockPredicateHandler(BlockStateHandler):
	def __init__(self):
		super().__init__(allowTag=True)


@argumentHandler(MINECRAFT_COLUMN_POS.name)
class ColumnPosHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		sr.save()
		columnPos1: Optional[str] = sr.tryReadInt() or sr.tryReadTildeNotation()
		if columnPos1 is None:
			sr.rollback()
			return None
		sr.mergeLastSave()
		if not sr.tryConsumeChar(' '):
			sr.rollback()
			return None

		columnPos2: Optional[str] = sr.tryReadInt() or sr.tryReadTildeNotation()
		if columnPos2 is None:
			sr.rollback()
			return None
		sr.mergeLastSave()

		blockPos = f'{columnPos1} {columnPos2}'
		return makeParsedArgument(sr, ai, value=blockPos)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['~ ~']


@argumentHandler(MINECRAFT_COMPONENT.name)
class ComponentHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# TODO: parseComponent(...): Must be a raw JSON text.
		import json
		remainder = sr.tryReadRemaining()
		if remainder is None:
			return None
		try:
			json = json.loads(remainder)
		except JSONDecodeError as e:
			position = sr.posFromColumn(sr.lastCursors.peek() + e.colno)
			end = sr.currentPos
			errorsIO.append(CommandSyntaxError(e.msg, Span(position, end), style='error'))
			return None
		else:
			return makeParsedArgument(sr, ai, value=json)


@argumentHandler(MINECRAFT_DIMENSION.name)
class DimensionHandler(ResourceLocationLikeHandler):

	@property
	def name(self) -> str:
		return 'dimension'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.dimension,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.dimensions


@argumentHandler(MINECRAFT_ENTITY.name)
class EntityHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID.
		locator = sr.tryReadString()
		if locator is None:
			# tryParse Target selector:
			variable = sr.tryReadRegex(re.compile(r'@[praes]\b'))
			if variable is None:
				return None
			arguments = parseFilterArgs(sr, TARGET_SELECTOR_ARGUMENTS_DICT, errorsIO=errorsIO)
			if arguments is None:
				arguments = FilterArguments()
			else:
				sr.mergeLastSave()
			locator = TargetSelector(variable=variable, arguments=arguments)

		return makeParsedArgument(sr, ai, value=locator)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		if 0 <= cursorPos < 2:
			return ['@a', '@e', '@s', '@p', '@r', ]
		else:
			return suggestionsForFilterArgs(contextStr[2:], cursorPos - 2, replaceCtx, TARGET_SELECTOR_ARGUMENTS_DICT)

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		targetSelector: TargetSelector = argument.value
		if not isinstance(targetSelector, TargetSelector):
			return None
		ranges = clickableRangesForFilterArgs(targetSelector.arguments)
		return ranges

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		onIndicatorClickedForFilterArgs(argument.value.arguments, position, window)


@abstract
class EntityTypeLikeHandler(ResourceLocationLikeHandler):

	@property
	def name(self) -> str:
		return 'entity'

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.entity_types,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.entities


@argumentHandler(MINECRAFT_ENTITY_SUMMON.name)
class EntitySummonHandler(EntityTypeLikeHandler):

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False


@argumentHandler(MINECRAFT_ENTITY_TYPE.name)
class EntityTypeHandler(EntityTypeLikeHandler):

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return True


@argumentHandler(MINECRAFT_FLOAT_RANGE.name)
class FloatRangeHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		float1Regex = r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)'
		float2Regex = r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
		separatorRegex = r'\.\.'
		pattern = re.compile(f"{float1Regex}(?:{separatorRegex}(?:{float2Regex})?)?|{separatorRegex}{float2Regex}")
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentHandler(MINECRAFT_FUNCTION.name)
class FunctionHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'function'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return True

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.tags.functions,)

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.functions,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()

	def getDocumentation(self, argument: ParsedCommandPart) -> HTMLStr:
		value: ResourceLocation = argument.value
		if not isinstance(value, ResourceLocation):
			return defaultDocumentationProvider(argument)
		if not value.isTag:
			for dp in getSession().world.datapacks:
				if (func := dp.contents.functions.get(value)) is not None:
					return func.documentation
		return defaultDocumentationProvider(argument)


@argumentHandler(MINECRAFT_GAME_PROFILE.name)
class GameProfileHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# TODO: parseGameProfile(...)
		return EntityHandler().parse(sr, ai, errorsIO=errorsIO)


@argumentHandler(MINECRAFT_INT_RANGE.name)
class IntRangeHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		intRegex = r'-?[0-9]+'
		separatorRegex = r'\.\.'
		pattern = re.compile(f"{intRegex}(?:{separatorRegex}(?:{intRegex})?)?|{separatorRegex}{intRegex}")
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentHandler(MINECRAFT_ITEM_ENCHANTMENT.name)
class ItemEnchantmentHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'enchantment'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.enchantments


@argumentHandler(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(r'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		slot: str = argument.value
		if slot not in getSession().minecraftData.slots:
			return CommandSemanticsError(f"Unknown item slot '{slot}'.", argument.span, style='error')

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return list(getSession().minecraftData.slots.keys())


@argumentHandler(MINECRAFT_ITEM_STACK.name)
class ItemStackHandler(ArgumentHandler):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# item_id{data_tags}
		itemID = sr.tryReadResourceLocation(allowTag=self._allowTag)
		if itemID is None:
			return None
		itemID = ResourceLocation.fromString(itemID)

		# data tags:
		if sr.tryConsumeChar('{'):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		itemStack = ItemStack(itemId=itemID, nbt=nbt)
		return makeParsedArgument(sr, ai, value=itemStack)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		itemStack: ItemStack = argument.value
		if not isinstance(itemStack, ItemStack):
			return CommandSemanticsError(f"Internal Error! expected ItemStack , but got '{itemStack}'.", argument.span)

		itemId = itemStack.itemId
		if itemId.isTag:
			isValid = any(itemId in dp.contents.tags.items for dp in getSession().world.datapacks) \
					or any(itemId in dp.contents.tags.blocks for dp in getSession().world.datapacks)  # I think so...
			if not isValid:
				return CommandSemanticsError(f"Unknown block tag '{itemId.asString}'.", argument.span, style='error')
		else:
			if not (_containsResourceLocation(itemId, getSession().minecraftData.items) or _containsResourceLocation(itemId, getSession().minecraftData.blocks)):
				return CommandSemanticsError(f"Unknown item id '{itemId.asString}'.", argument.span, style='warning')
		return None

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		result = choicesFromResourceLocations(contextStr, chain(getSession().minecraftData.items, getSession().minecraftData.blocks))
		if self._allowTag:
			result.extend(_choicesForDatapackContents(contextStr, Datapack.contents.tags.items))
			result.extend(_choicesForDatapackContents(contextStr, Datapack.contents.tags.blocks))
		return result

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		itemStack: ItemStack = argument.value
		if not isinstance(itemStack, ItemStack):
			return None

		itemId = itemStack.itemId
		if itemId.isTag:
			start = argument.span.start
			end = argument.span.end
			end = replace(
				end,
				column=min(end.column, start.column + len(itemId.asString)),
				index=min(end.index, start.index + len(itemId.asString))
			)
			span = Span(start, end)
			return [span]
		return None

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		if not _openFromDatapackContents(window, argument.value.itemId, Datapack.contents.tags.items):
			_openFromDatapackContents(window, argument.value.itemId, Datapack.contents.tags.blocks)


@argumentHandler(MINECRAFT_ITEM_PREDICATE.name)
class ItemPredicateHandler(ItemStackHandler):
	def __init__(self):
		super().__init__(allowTag=True)


@argumentHandler(MINECRAFT_MESSAGE.name)
class MessageHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


@argumentHandler(MINECRAFT_MOB_EFFECT.name)
class MobEffectHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'mob effect'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.effects


@argumentHandler(MINECRAFT_NBT_COMPOUND_TAG.name)
class NbtCompoundTagHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
		if nbt is None:
			return None
		return makeParsedArgument(sr, ai, value=nbt)


@argumentHandler(MINECRAFT_NBT_PATH.name)
class NbtPathHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		path = parseNBTPath(sr, errorsIO=errorsIO)
		if path is None:
			return None
		return makeParsedArgument(sr, ai, value=path)


@argumentHandler(MINECRAFT_NBT_TAG.name)
class NbtTagHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		nbt = parseNBTTag(sr, errorsIO=errorsIO)
		if nbt is None:
			return None
		return makeParsedArgument(sr, ai, value=nbt)


@argumentHandler(MINECRAFT_OBJECTIVE.name)
class ObjectiveHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pattern = re.compile(r"[a-zA-Z0-9_.+-]+")
		objective = sr.tryReadRegex(pattern)
		if objective is None:
			return None
		return makeParsedArgument(sr, ai, value=objective)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		if len(argument.value) > 16 and getSession().minecraftData.name < '1.18':
			return CommandSemanticsError(f"Objective names cannot be longer than 16 characters.", argument.span, style='error')


@argumentHandler(MINECRAFT_OBJECTIVE_CRITERIA.name)
class ObjectiveCriteriaHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, allowTag=False, errorsIO=errorsIO)
		# TODO: add validation for objective_criteria


@argumentHandler(MINECRAFT_PARTICLE.name)
class ParticleHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'particle'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.particles


@argumentHandler(MINECRAFT_PREDICATE.name)
class PredicateHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'predicate'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return (dp.contents.predicates,)

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return ()


@argumentHandler(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentHandler(MINECRAFT_ROTATION.name)
class RotationHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		numberReader = sr.tryReadFloat
		sr.save()
		yaw: Optional[str] = numberReader() or sr.tryReadTildeNotation()
		if yaw is None:
			sr.rollback()
			return None
		sr.mergeLastSave()
		if not sr.tryConsumeChar(' '):
			sr.rollback()
			return None

		pitch: Optional[str] = numberReader() or sr.tryReadTildeNotation()
		if pitch is None:
			sr.rollback()
			return None
		sr.mergeLastSave()

		rotation = f'{yaw} {pitch}'
		return makeParsedArgument(sr, ai, value=rotation)


@argumentHandler(MINECRAFT_SCORE_HOLDER.name)
class ScoreHolderHandler(EntityHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID, or *.
		result = super(ScoreHolderHandler, self).parse(sr, ai, errorsIO=errorsIO)
		if result is not None:
			return result
		sr.save()
		if sr.tryConsumeChar('*'):
			locator = '*'
		else:
			locator = sr.tryReadLiteral()
			if locator is None or locator.startswith('@'):
				sr.rollback()
				return None
		return makeParsedArgument(sr, ai, value=locator)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		suggestions = super(ScoreHolderHandler, self).getSuggestions(ai, contextStr, cursorPos, replaceCtx)
		if cursorPos <= 2:
			suggestions.append('*')
		return suggestions


@argumentHandler(MINECRAFT_SCOREBOARD_SLOT.name)
class ScoreboardSlotHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		literal = sr.tryReadLiteral()
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentHandler(MINECRAFT_SWIZZLE.name)
class SwizzleHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		swizzle = sr.tryReadLiteral()
		if swizzle is None:
			return None
		if re.fullmatch(r'[xyz]{1,3}', swizzle) is None:
			sr.rollback()
			return None
		if swizzle.count('x') > 1 or swizzle.count('y') > 1 or swizzle.count('z') > 1:
			sr.rollback()
			return None
		return makeParsedArgument(sr, ai, value=swizzle)


@argumentHandler(MINECRAFT_TEAM.name)
class TeamHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# -, +, ., _, A-Z, a-z, and 0-9
		literal = sr.tryReadRegex(re.compile(r'[-+._A-Za-z0-9]+'))
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentHandler(MINECRAFT_TIME.name)
class TimeHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		number = sr.tryReadFloat()
		if number is None:
			return None
		unit = sr.tryReadLiteral()
		if unit is None:
			sr.rollback()
			return None

		if unit not in ('d', 's', 't'):
			sr.rollback()
			sr.rollback()
			return None
		sr.mergeLastSave()
		return makeParsedArgument(sr, ai, value=(number, unit))


# 8-4-4-4-12
UUID_PATTERN = re.compile(r'[a-fA-F0-9]{1,8}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,12}')


@argumentHandler(MINECRAFT_UUID.name)
class UuidHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# 8-4-4-4-12
		literal = sr.tryReadRegex(UUID_PATTERN)
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentHandler(MINECRAFT_VEC2.name)
class Vec2Handler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse2dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get2dPosSuggestions(ai, contextStr, cursorPos, useFloat=True)


@argumentHandler(MINECRAFT_VEC3.name)
class Vec3Handler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions(self, ai: ArgumentInfo, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, contextStr, cursorPos, useFloat=True)


@argumentHandler(DPE_BIOME_ID.name)
class BiomeIdHandler(ResourceLocationLikeHandler):
	@property
	def name(self) -> str:
		return 'biome'

	def allowTags(self, ai: ArgumentInfo) -> bool:
		return False

	def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
		return ()

	def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
		return mc.biomes


@argumentHandler(ST_DPE_COMMAND.name)
class StDpeCommandHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_DATAPACK.name)
class StDpeDataPackHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_GAME_RULE.name)
class StDpeGameRuleHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_RAW_JSON_TEXT.name)
class StDpeRawJSONTextHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)

	def getDocumentation(self, argument: ParsedCommandPart) -> HTMLStr:
		return defaultDocumentationProvider(argument)


# check if there's an ArgumentHandler for every registered named ArgumentType:
for name, argType in ALL_NAMED_ARGUMENT_TYPES.items():
	if name != argType.name:
		raise ValueError(f"argumentType {argType.name!r} registered under wrong name {name!r}.")
	if getArgumentHandler(argType) is None:
		raise ValueError(f"missing argumentHandler for argumentType {argType.name!r}.")
