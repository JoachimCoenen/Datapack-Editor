import re
from abc import abstractmethod, ABCMeta
from dataclasses import replace
from itertools import chain
from json import JSONDecodeError
from typing import Optional, Iterable

from PyQt5.QtWidgets import QWidget

from Cat.utils import HTMLStr, abstract
from model.Model import Datapack, choicesForDatapackContents, metaInfoFromDatapackContents
from model.commands.argumentParsersImpl import _parse3dPos, tryReadNBTCompoundTag, _parseResourceLocation, _parse2dPos, _get3dPosSuggestions, _get2dPosSuggestions
from model.commands.argumentTypes import *
from model.commands.argumentValues import BlockState, ItemStack, FilterArguments, TargetSelector
from model.commands.command import ArgumentSchema, ParsedArgument
from model.commands.commandContext import ArgumentContext, argumentContext, makeParsedArgument, missingArgumentParser, getArgumentContext
from model.commands.filterArgs import parseFilterArgs, suggestionsForFilterArgs, clickableRangesForFilterArgs, onIndicatorClickedForFilterArgs
from model.commands.snbt import parseNBTPath, parseNBTTag
from model.commands.stringReader import StringReader
from model.commands.targetSelector import TARGET_SELECTOR_ARGUMENTS_DICT
from model.commands.utils import CommandSyntaxError, CommandSemanticsError
from model.datapackContents import ResourceLocation, choicesFromResourceLocations, containsResourceLocation
from model.json.parser import parseJsonStr
from model.json.validator import validateJson
import model.resourceLocationContext as rlc
from model.parsing.contextProvider import Suggestions
from model.utils import Span, Position, GeneralError
from session.session import getSession


def _init():
	pass  # do not remove!


@abstract
class ResourceLocationLikeHandler(ArgumentContext, metaclass=ABCMeta):
	# @property
	# @abstractmethod
	# def name(self) -> str:
	# 	pass
	#
	# @abstractmethod
	# def allowTags(self, ai: ArgumentSchema) -> bool:
	# 	pass
	#
	# @abstractmethod
	# def tagsFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
	# 	pass
	#
	# @abstractmethod
	# def valuesFromDP(self, dp: Datapack) -> Iterable[Mapping[ResourceLocation, MetaInfo]]:
	# 	pass
	#
	# @abstractmethod
	# def valuesFromMC(self, mc: MCVersion) -> Iterable[ResourceLocation]:
	# 	pass

	@property
	@abstractmethod
	def context(self) -> rlc.ResourceLocationContext:
		pass

	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=self.context.allowTags)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		self.context.validate(node.value, node.span, errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return self.context.getSuggestions(contextStr, cursorPos, replaceCtx)

	def getDocumentation(self, node: ParsedArgument, position: Position) -> HTMLStr:
		return self.context.getDocumentation(node.value) or super(ResourceLocationLikeHandler, self).getDocumentation(node, position)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		return self.context.getClickableRanges(node.value, node.span)

	def onIndicatorClicked(self, node: ParsedArgument, position: Position, window: QWidget) -> None:
		return self.context.onIndicatorClicked(node.value, window)


@argumentContext(BRIGADIER_BOOL.name)
class BoolHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadBoolean()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['true', 'false']


@argumentContext(BRIGADIER_DOUBLE.name)
class DoubleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_FLOAT.name)
class FloatHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_INTEGER.name)
class IntegerHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_LONG.name)
class LongHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_STRING.name)
class StringHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadString()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(MINECRAFT_ANGLE.name)
class AngleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		angle = sr.tryReadTildeNotation()
		if angle is None:
			angle = sr.tryReadFloat()
		if angle is None:
			return None
		return makeParsedArgument(sr, ai, value=angle)


@argumentContext(MINECRAFT_BLOCK_POS.name)
class BlockPosHandler(ArgumentContext):
	@staticmethod
	def useFloat(ai: ArgumentSchema):
		return ai.args is not None and ai.args.get('type', None) is float

	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=self.useFloat(ai), errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, contextStr, cursorPos, useFloat=self.useFloat(ai))


@argumentContext(MINECRAFT_BLOCK_STATE.name)
class BlockStateHandler(ArgumentContext):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		blockState: BlockState = node.value
		if not isinstance(blockState, BlockState):
			errorsIO.append(CommandSemanticsError(f"Internal Error! expected BlockState , but got'{blockState}'.", node.span))
			return

		blockId = blockState.blockId
		if blockId.isTag:
			isValid = any(blockId in dp.contents.tags.blocks for dp in getSession().world.datapacks)
			if not isValid:
				errorsIO.append(CommandSemanticsError(f"Unknown block tag '{blockId.asString}'.", node.span, style='error'))
		else:
			if not containsResourceLocation(blockId, getSession().minecraftData.blocks):
				errorsIO.append(CommandSemanticsError(f"Unknown block id '{blockId.asString}'.", node.span, style='warning'))

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
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
			tags = choicesForDatapackContents(contextStr, Datapack.contents.tags.blocks)
			suggestions += tags
		return suggestions

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		blockState: BlockState = node.value
		if not isinstance(blockState, BlockState):
			return None

		blockId = blockState.blockId
		start = node.span.start
		end = node.span.end
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

	def onIndicatorClicked(self, node: ParsedArgument, position: Position, window: QWidget) -> None:
		blockState: BlockState = node.value
		if position.index <= node.start.index + len(blockState.blockId.asString):
			if (metaInfo := metaInfoFromDatapackContents(blockState.blockId, Datapack.contents.tags.blocks)) is not None:
				window._tryOpenOrSelectDocument(metaInfo.filePath)  # very bad...
		else:
			onIndicatorClickedForFilterArgs(blockState.states, position, window)


@argumentContext(MINECRAFT_BLOCK_PREDICATE.name)
class BlockPredicateHandler(BlockStateHandler):
	def __init__(self):
		super().__init__(allowTag=True)


@argumentContext(MINECRAFT_COLUMN_POS.name)
class ColumnPosHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['~ ~']


@argumentContext(MINECRAFT_COMPONENT.name)
class ComponentHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# TODO: parseComponent(...): Must be a raw JSON text.
		remainder = sr.tryReadRemaining()
		if remainder is None:
			return None
		try:
			schema = getSession().datapackData.jsonSchemas.get('rawJsonText')
			jsonData, errors = parseJsonStr(remainder, False, schema)
			for e in errors:
				position = sr.posFromColumn(sr.lastCursors.peek() + e.span.start.index)
				end = sr.posFromColumn(sr.lastCursors.peek() + e.span.end.index)
				errorsIO.append(CommandSyntaxError(e.message, Span(position, end), style=e.style))
		except JSONDecodeError as e:
			position = sr.posFromColumn(sr.lastCursors.peek() + e.colno)
			end = sr.currentPos
			errorsIO.append(CommandSyntaxError(e.msg, Span(position, end), style='error'))
			return None
		else:
			return makeParsedArgument(sr, ai, value=jsonData)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		errors = validateJson(node.value)
		nss = node.span.start
		for er in errors:
			s = Position(
				nss.line,
				nss.column + er.span.start.index,
				nss.index + er.span.start.index
			)
			e = Position(
				nss.line,
				nss.column + er.span.end.index,
				nss.index + er.span.end.index
			)
			if isinstance(er, GeneralError):
				er.span = Span(s, e)
			else:
				er = CommandSemanticsError(er.message, Span(s, e), er.style)
			errorsIO.append(er)


@argumentContext(MINECRAFT_DIMENSION.name)
class DimensionHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.DimensionContext()


@argumentContext(MINECRAFT_ENTITY.name)
class EntityHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		if 0 <= cursorPos < 2:
			return ['@a', '@e', '@s', '@p', '@r', ]
		else:
			return suggestionsForFilterArgs(contextStr[2:], cursorPos - 2, replaceCtx, TARGET_SELECTOR_ARGUMENTS_DICT)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		targetSelector: TargetSelector = node.value
		if not isinstance(targetSelector, TargetSelector):
			return None
		ranges = clickableRangesForFilterArgs(targetSelector.arguments)
		return ranges

	def onIndicatorClicked(self, node: ParsedArgument, position: Position, window: QWidget) -> None:
		onIndicatorClickedForFilterArgs(node.value.arguments, position, window)


@argumentContext(MINECRAFT_ENTITY_SUMMON.name)
class EntitySummonHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.EntitySummonHandler()


@argumentContext(MINECRAFT_ENTITY_TYPE.name)
class EntityTypeHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.EntityTypeHandler()


@argumentContext(MINECRAFT_FLOAT_RANGE.name)
class FloatRangeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		float1Regex = r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)'
		float2Regex = r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
		separatorRegex = r'\.\.'
		pattern = re.compile(f"{float1Regex}(?:{separatorRegex}(?:{float2Regex})?)?|{separatorRegex}{float2Regex}")
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentContext(MINECRAFT_FUNCTION.name)
class FunctionHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.FunctionContext()


@argumentContext(MINECRAFT_GAME_PROFILE.name)
class GameProfileHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# TODO: parseGameProfile(...)
		return EntityHandler().parse(sr, ai, errorsIO=errorsIO)


@argumentContext(MINECRAFT_INT_RANGE.name)
class IntRangeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		intRegex = r'-?[0-9]+'
		separatorRegex = r'\.\.'
		pattern = re.compile(f"{intRegex}(?:{separatorRegex}(?:{intRegex})?)?|{separatorRegex}{intRegex}")
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentContext(MINECRAFT_ITEM_ENCHANTMENT.name)
class ItemEnchantmentHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.ItemEnchantmentContext()


@argumentContext(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(r'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		slot: str = node.value
		if slot not in getSession().minecraftData.slots:
			errorsIO.append(CommandSemanticsError(f"Unknown item slot '{slot}'.", node.span, style='error'))

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return list(getSession().minecraftData.slots.keys())


@argumentContext(MINECRAFT_ITEM_STACK.name)
class ItemStackHandler(ArgumentContext):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		itemStack: ItemStack = node.value
		if not isinstance(itemStack, ItemStack):
			errorsIO.append(CommandSemanticsError(f"Internal Error! expected ItemStack , but got '{itemStack}'.", node.span))
			return

		itemId = itemStack.itemId
		if itemId.isTag:
			isValid = any(itemId in dp.contents.tags.items for dp in getSession().world.datapacks) \
					or any(itemId in dp.contents.tags.blocks for dp in getSession().world.datapacks)  # I think so...
			if not isValid:
				errorsIO.append(CommandSemanticsError(f"Unknown block tag '{itemId.asString}'.", node.span, style='error'))
		else:
			if not (containsResourceLocation(itemId, getSession().minecraftData.items) or containsResourceLocation(itemId, getSession().minecraftData.blocks)):
				errorsIO.append(CommandSemanticsError(f"Unknown item id '{itemId.asString}'.", node.span, style='warning'))
		return None

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		result = choicesFromResourceLocations(contextStr, chain(getSession().minecraftData.items, getSession().minecraftData.blocks))
		if self._allowTag:
			result.extend(choicesForDatapackContents(contextStr, Datapack.contents.tags.items))
			result.extend(choicesForDatapackContents(contextStr, Datapack.contents.tags.blocks))
		return result

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		itemStack: ItemStack = node.value
		if not isinstance(itemStack, ItemStack):
			return None

		itemId = itemStack.itemId
		if itemId.isTag:
			start = node.span.start
			end = node.span.end
			end = replace(
				end,
				column=min(end.column, start.column + len(itemId.asString)),
				index=min(end.index, start.index + len(itemId.asString))
			)
			span = Span(start, end)
			return [span]
		return None

	def onIndicatorClicked(self, node: ParsedArgument, position: Position, window: QWidget) -> None:
		if (metaInfo := metaInfoFromDatapackContents(node.value.itemId, Datapack.contents.tags.items)) is not None:
			window._tryOpenOrSelectDocument(metaInfo.filePath)  # very bad...
		elif (metaInfo := metaInfoFromDatapackContents(node.value.itemId, Datapack.contents.tags.blocks)) is not None:
			window._tryOpenOrSelectDocument(metaInfo.filePath)  # very bad...


@argumentContext(MINECRAFT_ITEM_PREDICATE.name)
class ItemPredicateHandler(ItemStackHandler):
	def __init__(self):
		super().__init__(allowTag=True)


@argumentContext(MINECRAFT_MESSAGE.name)
class MessageHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


@argumentContext(MINECRAFT_MOB_EFFECT.name)
class MobEffectHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.MobEffectContext()


@argumentContext(MINECRAFT_NBT_COMPOUND_TAG.name)
class NbtCompoundTagHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
		if nbt is None:
			return None
		return makeParsedArgument(sr, ai, value=nbt)


@argumentContext(MINECRAFT_NBT_PATH.name)
class NbtPathHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		path = parseNBTPath(sr, errorsIO=errorsIO)
		if path is None:
			return None
		return makeParsedArgument(sr, ai, value=path)


@argumentContext(MINECRAFT_NBT_TAG.name)
class NbtTagHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		nbt = parseNBTTag(sr, errorsIO=errorsIO)
		if nbt is None:
			return None
		return makeParsedArgument(sr, ai, value=nbt)


@argumentContext(MINECRAFT_OBJECTIVE.name)
class ObjectiveHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pattern = re.compile(r"[a-zA-Z0-9_.+-]+")
		objective = sr.tryReadRegex(pattern)
		if objective is None:
			return None
		return makeParsedArgument(sr, ai, value=objective)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		if len(node.value) > 16 and getSession().minecraftData.name < '1.18':
			errorsIO.append(CommandSemanticsError(f"Objective names cannot be longer than 16 characters.", node.span, style='error'))


@argumentContext(MINECRAFT_OBJECTIVE_CRITERIA.name)
class ObjectiveCriteriaHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, allowTag=False, errorsIO=errorsIO)
		# TODO: add validation for objective_criteria


@argumentContext(MINECRAFT_PARTICLE.name)
class ParticleHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.ParticleContext()


@argumentContext(MINECRAFT_PREDICATE.name)
class PredicateHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.PredicateContext()


@argumentContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)


@argumentContext(MINECRAFT_ROTATION.name)
class RotationHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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


@argumentContext(MINECRAFT_SCORE_HOLDER.name)
class ScoreHolderHandler(EntityHandler):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		suggestions = super(ScoreHolderHandler, self).getSuggestions2(ai, contextStr, cursorPos, replaceCtx)
		if cursorPos <= 2:
			suggestions.append('*')
		return suggestions


@argumentContext(MINECRAFT_SCOREBOARD_SLOT.name)
class ScoreboardSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		literal = sr.tryReadLiteral()
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_SWIZZLE.name)
class SwizzleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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


@argumentContext(MINECRAFT_TEAM.name)
class TeamHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# -, +, ., _, A-Z, a-z, and 0-9
		literal = sr.tryReadRegex(re.compile(r'[-+._A-Za-z0-9]+'))
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_TIME.name)
class TimeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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


@argumentContext(MINECRAFT_UUID.name)
class UuidHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# 8-4-4-4-12
		literal = sr.tryReadRegex(UUID_PATTERN)
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_VEC2.name)
class Vec2Handler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse2dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get2dPosSuggestions(ai, contextStr, cursorPos, useFloat=True)


@argumentContext(MINECRAFT_VEC3.name)
class Vec3Handler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, contextStr, cursorPos, useFloat=True)


@argumentContext(DPE_BIOME_ID.name)
class BiomeIdHandler(ResourceLocationLikeHandler):

	@property
	def context(self) -> rlc.ResourceLocationContext:
		return rlc.BiomeIdContext()


@argumentContext(ST_DPE_DATAPACK.name)
class StDpeDataPackHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


# check if there's an ArgumentContext for every registered named ArgumentType:
for name, argType in ALL_NAMED_ARGUMENT_TYPES.items():
	if name != argType.name:
		raise ValueError(f"argumentType {argType.name!r} registered under wrong name {name!r}.")
	if getArgumentContext(argType) is None:
		raise ValueError(f"missing argumentContext for argumentType {argType.name!r}.")
