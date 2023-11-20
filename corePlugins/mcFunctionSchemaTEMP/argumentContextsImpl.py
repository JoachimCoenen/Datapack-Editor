import re
from math import inf
from typing import Any, Callable, Iterable, Optional

from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.contextProvider import Suggestions, errorMsg, getClickableRanges, getSuggestions, onIndicatorClicked, validateTree
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.pathUtils import FilePath
from base.model.utils import GeneralError, LanguageId, Message, Position, Span
from cat.utils.collections_ import FrozenDict
from corePlugins.mcFunction.argumentContextsImpl import ParsingHandler, checkArgumentContextsForRegisteredArgumentTypes
from corePlugins.mcFunction.command import ArgumentSchema, CommandPart, FilterArgumentInfo, ParsedArgument
from corePlugins.mcFunction.commandContext import ArgumentContext, argumentContext, makeParsedArgument, missingArgumentParser
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import RESOURCE_LOCATION_ID, ResourceLocation, ResourceLocationNode, ResourceLocationSchema
from corePlugins.minecraft_data.fullData import getCurrentFullMcData
from corePlugins.nbt import SNBT_ID
from corePlugins.nbt.path import NBTPathSchema, SNBT_PATH_ID
from corePlugins.nbt.tags import NBTTagSchema
from .argumentParsersImpl import _parseVec, _readResourceLocation, tryReadNBTCompoundTag
from .argumentTypes import *
from .argumentValues import BlockState, FilterArguments, ItemStack, TargetSelector
from .filterArgs import clickableRangesForFilterArgs, onIndicatorClickedForFilterArgs, parseFilterArgs, suggestionsForFilterArgs, validateFilterArgs
from .targetSelector import TARGET_SELECTOR_ARGUMENTS_DICT


def initPlugin() -> None:
	pass


OBJECTIVE_NAME_LONGER_THAN_16_MSG: Message = Message(f"Objective names cannot be longer than 16 characters.", 0)


@argumentContext(MINECRAFT_DIMENSION.name, rlcSchema=ResourceLocationSchema('', 'dimension', allowTags=False))
@argumentContext(MINECRAFT_ENTITY_SUMMON.name, rlcSchema=ResourceLocationSchema('', 'entity_type', allowTags=False))
@argumentContext(MINECRAFT_ENTITY_TYPE.name, rlcSchema=ResourceLocationSchema('', 'entity_type', allowTags=True))
@argumentContext(MINECRAFT_FUNCTION.name, rlcSchema=ResourceLocationSchema('', 'function', allowTags=True))
@argumentContext(MINECRAFT_ITEM_ENCHANTMENT.name, rlcSchema=ResourceLocationSchema('', 'enchantment', allowTags=False))
@argumentContext(MINECRAFT_MOB_EFFECT.name, rlcSchema=ResourceLocationSchema('', 'mob_effect', allowTags=False))
@argumentContext(MINECRAFT_PARTICLE.name, rlcSchema=ResourceLocationSchema('', 'particle', allowTags=False))
@argumentContext(MINECRAFT_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'predicate', allowTags=False))
@argumentContext(MINECRAFT_LOOT_TABLE.name, rlcSchema=ResourceLocationSchema('', 'loot_table', allowTags=False))
@argumentContext(MINECRAFT_OBJECTIVE_CRITERIA.name, rlcSchema=ResourceLocationSchema('', 'any', allowTags=False))  # TODO: add validation for objective_criteria
@argumentContext(DPE_ADVANCEMENT.name, rlcSchema=ResourceLocationSchema('', 'advancement', allowTags=False))
@argumentContext(DPE_BIOME_ID.name, rlcSchema=ResourceLocationSchema('', 'biome', allowTags=False))  # outdated. TODO: remove
class ResourceLocationLikeHandler(ParsingHandler):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def getSchema(self, ai: ArgumentSchema) -> ResourceLocationSchema:
		return self.rlcSchema

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return RESOURCE_LOCATION_ID

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return dict(ignoreTrailingChars=True)

	def getErsatzNodeForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[ResourceLocationNode]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.getSchema(ai))


@argumentContext(MINECRAFT_RESOURCE_LOCATION.name, rlcSchema=ResourceLocationSchema('', 'any', allowTags=False))
class ResourceLocationHandler(ParsingHandler):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def getSchema(self, ai: ArgumentSchema) -> ResourceLocationSchema:
		args = ai.args or FrozenDict.EMPTY
		schema = args.get('schema', 'any')  # todo add warning if no 'schema' is given.
		allowTags = args.get('allowTags', False)
		onlyTags = args.get('onlyTags', False)
		rlcSchema = ResourceLocationSchema('', schema, allowTags=allowTags, onlyTags=onlyTags)
		return rlcSchema

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return RESOURCE_LOCATION_ID

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return dict(ignoreTrailingChars=True)

	def getErsatzNodeForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[ResourceLocationNode]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.getSchema(ai))


@argumentContext(MINECRAFT_ANGLE.name)
class AngleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return _parseVec(sr, ai, useFloat=True, count=1, notation=b'~')


@argumentContext(MINECRAFT_BLOCK_STATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=False))
@argumentContext(MINECRAFT_BLOCK_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=True))
class BlockStateHandler(ArgumentContext):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def _getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		blockStates = getCurrentFullMcData().getBlockStates(blockID)
		return {strToBytes(argument.name): argument.fai for argument in blockStates}

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# block_id[block_states]{data_tags}
		blockID = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)

		# block states:
		blockStatesDict = self._getBlockStatesDict(blockID)
		states: Optional[FilterArguments] = parseFilterArgs(sr, blockStatesDict, filePath, errorsIO=errorsIO)
		if states is not None:
			sr.mergeLastSave()
		else:
			states = FilterArguments()
		# data tags:
		if sr.tryConsumeByte(ord('{')):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, ai, filePath, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		blockPredicate = BlockState(blockId=blockID, states=states, nbt=nbt)
		return makeParsedArgument(sr, ai, value=blockPredicate)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		blockState: BlockState = node.value
		if not isinstance(blockState, BlockState):
			errorMsg(INTERNAL_ERROR_MSG, EXPECTED_BUT_GOT_MSG, 'BlockState', type(blockState).__name__, span=node.span, errorsIO=errorsIO)
			return

		validateTree(blockState.blockId, node.source, errorsIO)
		blockStatesDict = self._getBlockStatesDict(blockState.blockId)
		validateFilterArgs(blockState.states, blockStatesDict, errorsIO)

		if blockState.nbt is not None:
			validateTree(blockState.nbt, node.source, errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		if node is None:
			blockID = ResourceLocationNode.fromString(b'', Span(pos), self.rlcSchema)
			return getSuggestions(blockID, b'', pos, replaceCtx)
		blockState: BlockState = node.value
		if not isinstance(blockState, BlockState):
			return []

		suggestions: Suggestions = []

		blockID = blockState.blockId
		argsStart = blockID.span.end

		if pos.index >= argsStart.index and not (blockState.nbt is not None and blockState.nbt.span.__contains__(pos)) and (blockStatesDict := self._getBlockStatesDict(blockID)):
			contextStr = node.source[argsStart.index:node.end.index]
			relCursorPos = pos.index - argsStart.index
			suggestions += suggestionsForFilterArgs(blockState.states, contextStr, relCursorPos, pos, replaceCtx, blockStatesDict)

		if blockID.span.__contains__(pos):
			suggestions += getSuggestions(blockState.blockId, node.source, pos, replaceCtx)

		if blockState.nbt is not None and blockState.nbt.span.__contains__(pos):
			suggestions += getSuggestions(blockState.nbt, node.source, pos, replaceCtx)

		return suggestions

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		blockState: BlockState = node.value
		if not isinstance(blockState, BlockState):
			return None

		ranges = []
		ranges += getClickableRanges(blockState.blockId, node.source, node.span)
		ranges += clickableRangesForFilterArgs(blockState.states)
		if blockState.nbt is not None:
			ranges += getClickableRanges(blockState.nbt, node.source, node.span)

		return ranges

	def onIndicatorClicked(self, node: ParsedArgument, position: Position) -> None:
		blockState: BlockState = node.value
		if blockState.blockId.span.__contains__(position):
			onIndicatorClicked(blockState.blockId, node.source, position)
		elif blockState.nbt is not None and blockState.nbt.span.__contains__(position):
			onIndicatorClicked(blockState.nbt, node.source, position)
		else:
			onIndicatorClickedForFilterArgs(blockState.states, position)


@argumentContext(MINECRAFT_COLUMN_POS.name)
class ColumnPosHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return _parseVec(sr, ai, useFloat=False, count=2, notation=b'~')

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return ['~ ~']


@argumentContext(MINECRAFT_COMPONENT.name)
class ComponentHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return GLOBAL_SCHEMA_STORE.get('minecraft:raw_json_text', LanguageId('JSON'))

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return LanguageId('JSON')


@argumentContext(MINECRAFT_ENTITY.name)
class EntityHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID.
		locator = sr.tryReadString()
		if locator is None:
			# tryParse Target selector:
			variable = sr.tryReadRegex(re.compile(rb'@[praes]\b'))
			if variable is None:
				return None
			variable = bytesToStr(variable)
			arguments = parseFilterArgs(sr, TARGET_SELECTOR_ARGUMENTS_DICT, filePath, errorsIO=errorsIO)
			if arguments is None:
				arguments = FilterArguments()
			else:
				sr.mergeLastSave()
			locator = TargetSelector(variable=variable, arguments=arguments)

		return makeParsedArgument(sr, ai, value=locator)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		if node is None or pos.index - node.span.start.index < 2:
			return ['@a', '@e', '@s', '@p', '@r', ]
		targetSelector: TargetSelector = node.value
		if not isinstance(targetSelector, TargetSelector):
			return []
		return suggestionsForFilterArgs(targetSelector.arguments, node.content[2:], pos.index - node.span.start.index - 2, pos, replaceCtx, TARGET_SELECTOR_ARGUMENTS_DICT)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		targetSelector: TargetSelector = node.value
		if not isinstance(targetSelector, TargetSelector):
			return None
		ranges = clickableRangesForFilterArgs(targetSelector.arguments)
		return ranges

	def onIndicatorClicked(self, node: ParsedArgument, position: Position) -> None:
		onIndicatorClickedForFilterArgs(node.value.arguments, position)


_INTEGER_REGEX = r'-?[0-9]+'
_FLOAT_1_REGEX = r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)'
_FLOAT_2_REGEX = r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
_SEPARATOR_REGEX = r'\.\.'
#                       group 0              group 1             group 2               group 3             group 4
_INTEG_RANGE_REGEX = f"({_INTEGER_REGEX})(?:({_SEPARATOR_REGEX})({_INTEGER_REGEX})?)?|({_SEPARATOR_REGEX})({_INTEGER_REGEX})"
_FLOAT_RANGE_REGEX = f"({_FLOAT_1_REGEX})(?:({_SEPARATOR_REGEX})({_FLOAT_2_REGEX})?)?|({_SEPARATOR_REGEX})({_FLOAT_2_REGEX})"
_INT_RANGE_PATTERN = re.compile(strToBytes(_INTEG_RANGE_REGEX))
_FLOAT_RANGE_PATTERN = re.compile(strToBytes(_FLOAT_RANGE_REGEX))


@argumentContext(MINECRAFT_FLOAT_RANGE.name, pattern=_FLOAT_RANGE_PATTERN, numberParser=float)
@argumentContext(MINECRAFT_INT_RANGE.name, pattern=_INT_RANGE_PATTERN, numberParser=int)
class IntRangeHandler(ArgumentContext):
	def __init__(self, pattern: re.Pattern[bytes], numberParser: Callable[[str], int | float]):
		super().__init__()
		self.pattern: re.Pattern[bytes] = pattern
		self.numberParser: Callable[[str], int | float] = numberParser

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		groups = sr.tryReadRegexGroups(self.pattern)
		if groups is None:
			return None

		stringMin = groups[0]
		separator = groups[1] or groups[3]
		stringMax = groups[2] or groups[4]
		numberMin = -inf if not stringMin else self.numberParser(bytesToStr(stringMin))
		numberMax = +inf if not stringMax else self.numberParser(bytesToStr(stringMax))
		if not separator:  # we only have one number
			if not stringMin:
				numberMin = numberMax
			elif not stringMax:
				numberMax = numberMin
			else:
				raise TypeError("Internal Error that should never be possible. Has a RegEx gone bad?")

		return makeParsedArgument(sr, ai, (numberMin, numberMax))

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		args = node.schema.args or FrozenDict.EMPTY
		# bounded = args.get('bounded', False)
		minSize = args.get('minSize', 0)
		maxSize = args.get('maxSize', +inf)
		minVal = args.get('minVal', -inf)
		maxVal = args.get('maxVal', +inf)
		numberMin, numberMax = node.value
		# intAdjust is necessary, because the intRange 0...1 has a span of only 1-0 = 1, but contains two values (0, 1).
		intAdjust = 1 if self.numberParser is int else 0

		if not minVal <= numberMin <= maxVal:
			errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, minVal, maxVal, span=node.span, errorsIO=errorsIO)
		elif not minVal <= numberMax <= maxVal:
			errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, minVal, maxVal, span=node.span, errorsIO=errorsIO)

		if numberMax < numberMin:
			errorMsg(RANGE_INVERTED_MSG, span=node.span, errorsIO=errorsIO)
		elif (numberMax - numberMin + intAdjust) < minSize:
			errorMsg(RANGE_TOO_SMALL_MSG, minSize, span=node.span, errorsIO=errorsIO)
		elif (numberMax - numberMin + intAdjust) > maxSize:
			errorMsg(RANGE_TOO_BIG_MSG, maxSize, span=node.span, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		args = ai.args or FrozenDict.EMPTY
		minVal = args.get('minVal', -inf)
		maxVal = args.get('maxVal', +inf)
		noLowerBound = minVal == -inf
		includeMinVal = minVal >= -1000
		includeMaxVal = maxVal <= +1000
		includeMinZero = minVal <= 0
		includeMaxZero = maxVal >= 0

		suggestions = {}

		def addSuggestion(minStr: str, maxStr: str) -> None:
			suggestions.setdefault(f'{minStr}' if minStr == maxStr else f'{minStr}...{maxStr}')

		def addSuggestions(maxStr: str):
			if noLowerBound:
				suggestions.setdefault(f'...{maxStr}')
			if includeMinVal:
				addSuggestion(minStr=f'{minVal}', maxStr=maxStr)
			if includeMinZero:
				addSuggestion(minStr='0', maxStr=maxStr)

		addSuggestions(maxStr='')
		if includeMaxVal:
			addSuggestions(maxStr=f'{maxVal}')
		if includeMaxZero:
			addSuggestions(maxStr='0')

		return list(suggestions)


@argumentContext(MINECRAFT_GAME_PROFILE.name)
class GameProfileHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# TODO: parseGameProfile(...)
		return EntityHandler().parse(sr, ai, filePath, errorsIO=errorsIO)


@argumentContext(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(rb'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		slot: str = node.value
		if slot not in getCurrentFullMcData().slots:
			errorMsg(UNKNOWN_MSG, "item slot",  slot, span=node.span, style='error', errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return [bytesToStr(slot) for slot in getCurrentFullMcData().slots.keys()]


@argumentContext(MINECRAFT_ITEM_STACK.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=False))
@argumentContext(MINECRAFT_ITEM_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=True))
class ItemStackHandler(ArgumentContext):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# item_id{data_tags}
		itemID = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)
		if itemID is None:
			return None

		# data tags:
		if sr.tryConsumeByte(ord('{')):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, ai, filePath, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		itemStack = ItemStack(itemId=itemID, nbt=nbt)
		return makeParsedArgument(sr, ai, value=itemStack)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		itemStack: ItemStack = node.value
		if not isinstance(itemStack, ItemStack):
			errorMsg(INTERNAL_ERROR_MSG, EXPECTED_BUT_GOT_MSG, 'ItemStack', type(itemStack).__name__, span=node.span, errorsIO=errorsIO)
			return

		validateTree(itemStack.itemId, node.source, errorsIO)
		if itemStack.nbt is not None:
			validateTree(itemStack.nbt, node.source, errorsIO)
		return None

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		# return result
		if node is None:
			itemId = ResourceLocationNode.fromString(b'', Span(pos), self.rlcSchema)
			return getSuggestions(itemId, b'', pos, replaceCtx)
		itemStack: ItemStack = node.value
		if not isinstance(itemStack, ItemStack):
			return []

		suggestions = []
		if itemStack.itemId.span.__contains__(pos):
			suggestions += getSuggestions(itemStack.itemId, node.source, pos, replaceCtx)

		if itemStack.nbt is not None and itemStack.nbt.span.__contains__(pos):
			suggestions += getSuggestions(itemStack.nbt, node.source, pos, replaceCtx)

		return suggestions

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		itemStack: ItemStack = node.value
		if not isinstance(itemStack, ItemStack):
			return None

		ranges = []
		ranges += getClickableRanges(itemStack.itemId, node.source)

		if itemStack.nbt is not None:
			ranges += getClickableRanges(itemStack.nbt, node.source)

		return ranges

	def onIndicatorClicked(self, node: ParsedArgument, position: Position) -> None:
		itemStack: ItemStack = node.value
		if itemStack.itemId.span.__contains__(position):
			onIndicatorClicked(itemStack.itemId, node.source, position)
		elif itemStack.nbt is not None and itemStack.nbt.span.__contains__(position):
			onIndicatorClicked(itemStack.nbt, node.source, position)


@argumentContext(MINECRAFT_MESSAGE.name)
class MessageHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


@argumentContext(MINECRAFT_NBT_PATH.name)
class NbtPathHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return NBTPathSchema('')

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return SNBT_PATH_ID

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return dict(ignoreTrailingChars=True)


@argumentContext(MINECRAFT_NBT_COMPOUND_TAG.name)
@argumentContext(MINECRAFT_NBT_TAG.name)
class NbtTagHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return NBTTagSchema('')

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return SNBT_ID

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return dict(ignoreTrailingChars=True)


@argumentContext(MINECRAFT_OBJECTIVE.name)
class ObjectiveHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		pattern = re.compile(rb"[a-zA-Z0-9_.+-]+")
		objective = sr.tryReadRegex(pattern)
		if objective is None:
			return None
		return makeParsedArgument(sr, ai, value=objective)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		if len(node.value) > 16 and getCurrentFullMcData().name < '1.18':
			errorMsg(OBJECTIVE_NAME_LONGER_THAN_16_MSG, span=node.span, style='error', errorsIO=errorsIO)


@argumentContext(MINECRAFT_ROTATION.name)
class RotationHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# (yaw, pitch)
		return _parseVec(sr, ai, useFloat=True, count=2, notation=b'~')


@argumentContext(MINECRAFT_SCORE_HOLDER.name)
class ScoreHolderHandler(EntityHandler):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID, or *.
		result = super(ScoreHolderHandler, self).parse(sr, ai, filePath, errorsIO=errorsIO)
		if result is not None:
			return result
		sr.save()
		if sr.tryConsumeByte(ord('*')):
			locator = b'*'
		else:
			locator = sr.tryReadLiteral()
			if locator is None or locator.startswith(b'@'):
				sr.rollback()
				return None
		return makeParsedArgument(sr, ai, value=locator)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		suggestions = super(ScoreHolderHandler, self).getSuggestions2(ai, node, pos, replaceCtx)
		if node is None or (node.start.index - pos.index) <= 2:
			suggestions.append('*')
		return suggestions


@argumentContext(MINECRAFT_SCOREBOARD_SLOT.name)
class ScoreboardSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		literal = sr.tryReadLiteral()
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_SWIZZLE.name)
class SwizzleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		swizzle = sr.tryReadLiteral()
		if swizzle is None:
			return None
		if re.fullmatch(rb'[xyz]{1,3}', swizzle) is None:
			sr.rollback()
			return None
		if swizzle.count(b'x') > 1 or swizzle.count(b'y') > 1 or swizzle.count(b'z') > 1:
			sr.rollback()
			return None
		return makeParsedArgument(sr, ai, value=swizzle)


@argumentContext(MINECRAFT_TEAM.name)
class TeamHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# -, +, ., _, A-Z, a-z, and 0-9
		literal = sr.tryReadRegex(re.compile(rb'[-+._A-Za-z0-9]+'))
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_TIME.name)
class TimeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		number = sr.tryReadFloat()
		if number is None:
			return None
		unit = sr.tryReadLiteral()
		if unit is None:
			sr.rollback()
			return None

		if unit not in (b'd', b's', b't'):
			sr.rollback()
			sr.rollback()
			return None
		sr.mergeLastSave()
		return makeParsedArgument(sr, ai, value=(number, unit))


# 8-4-4-4-12
UUID_PATTERN = re.compile(rb'[a-fA-F0-9]{1,8}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,4}-[a-fA-F0-9]{1,12}')


@argumentContext(MINECRAFT_UUID.name)
class UuidHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# 8-4-4-4-12
		literal = sr.tryReadRegex(UUID_PATTERN)
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_VEC2.name)
class Vec2Handler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return _parseVec(sr, ai, useFloat=True, count=2, notation=b'~^')

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return ['~ ~', '0 0']


@argumentContext(MINECRAFT_BLOCK_POS.name, useFloat=False)
@argumentContext(MINECRAFT_VEC3.name, useFloat=True)
class Vec3Handler(ArgumentContext):
	def __init__(self, useFloat: bool):
		self.useFloat: bool = useFloat

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return _parseVec(sr, ai, useFloat=self.useFloat, count=3, notation=b'~^')

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[CommandPart], pos: Position, replaceCtx: str) -> Suggestions:
		return ['~ ~ ~', '^ ^ ^', '0 0 0']


@argumentContext(ST_DPE_DATAPACK.name)
class StDpeDataPackHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


# make sure there's an ArgumentContext for every registered named ArgumentType:
checkArgumentContextsForRegisteredArgumentTypes()
