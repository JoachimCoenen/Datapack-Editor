import re
from typing import Optional, Iterable, Any

from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getClickableRanges, onIndicatorClicked
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.pathUtils import FilePath
from base.model.utils import Span, Position, GeneralError, Message, LanguageId
from corePlugins.mcFunction.command import ArgumentSchema, ParsedArgument, CommandPart
from corePlugins.mcFunction.commandContext import ArgumentContext, argumentContext, makeParsedArgument, missingArgumentParser
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.mcFunction.utils import CommandSyntaxError, CommandSemanticsError
from corePlugins.minecraft.resourceLocation import ResourceLocation, ResourceLocationSchema, ResourceLocationNode, RESOURCE_LOCATION_ID
from corePlugins.nbt.tags import NBTTagSchema
from base.model.messages import *
from .argumentParsersImpl import _parse3dPos, tryReadNBTCompoundTag, _parse2dPos, _get3dPosSuggestions, _get2dPosSuggestions, _readResourceLocation
from .argumentTypes import *
from .argumentValues import BlockState, ItemStack, FilterArguments, TargetSelector
from .filterArgs import parseFilterArgs, suggestionsForFilterArgs, clickableRangesForFilterArgs, onIndicatorClickedForFilterArgs, FilterArgumentInfo, validateFilterArgs
from .snbt import parseNBTPath
from .targetSelector import TARGET_SELECTOR_ARGUMENTS_DICT
from corePlugins.mcFunction.argumentContextsImpl import ParsingHandler, checkArgumentContextsForRegisteredArgumentTypes
from corePlugins.mcFunction.argumentTypes import makeLiteralsArgumentType, ALL_NAMED_ARGUMENT_TYPES
from corePlugins.minecraft_data.fullData import getCurrentFullMcData
from corePlugins.minecraft_data.mcdAdapter import BlockStateType


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
@argumentContext(MINECRAFT_RESOURCE_LOCATION.name, rlcSchema=ResourceLocationSchema('', 'any', allowTags=False))
@argumentContext(MINECRAFT_OBJECTIVE_CRITERIA.name, rlcSchema=ResourceLocationSchema('', 'any', allowTags=False))  # TODO: add validation for objective_criteria
@argumentContext(DPE_ADVANCEMENT.name, rlcSchema=ResourceLocationSchema('', 'advancement', allowTags=False))
@argumentContext(DPE_BIOME_ID.name, rlcSchema=ResourceLocationSchema('', 'biome', allowTags=False))
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


@argumentContext(MINECRAFT_ANGLE.name)
class AngleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=self.useFloat(ai), errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[CommandPart], pos: Position, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, node, pos, replaceCtx, useFloat=self.useFloat(ai))


@argumentContext(MINECRAFT_BLOCK_STATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=False))
@argumentContext(MINECRAFT_BLOCK_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=True))
class BlockStateHandler(ArgumentContext):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	@staticmethod
	def faiForBS(bs: BlockStateType) -> FilterArgumentInfo:
		if bs.values:
			argType = makeLiteralsArgumentType([strToBytes(val) for val in bs.values])
		else:
			argType = ALL_NAMED_ARGUMENT_TYPES[bs.type]

		return FilterArgumentInfo(
			name=bs.name,
			type=argType,
		)

	def _getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		blockStates = getCurrentFullMcData().getBlockStates(blockID)
		return {strToBytes(argument.name): self.faiForBS(argument) for argument in blockStates}

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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
			errorsIO.append(CommandSemanticsError(INTERNAL_ERROR_MSG.format(EXPECTED_BUT_GOT_MSG, '`BlockState`', type(blockState).__name__), node.span))
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

		if pos.index >= argsStart.index and (blockStatesDict := self._getBlockStatesDict(blockID)):
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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		sr.save()
		columnPos1: Optional[bytes] = sr.tryReadInt() or sr.tryReadTildeNotation()
		if columnPos1 is None:
			sr.rollback()
			return None
		sr.mergeLastSave()
		if not sr.tryConsumeByte(ord(' ')):
			sr.rollback()
			return None

		columnPos2: Optional[bytes] = sr.tryReadInt() or sr.tryReadTildeNotation()
		if columnPos2 is None:
			sr.rollback()
			return None
		sr.mergeLastSave()

		blockPos = (columnPos1, columnPos2)
		return makeParsedArgument(sr, ai, value=blockPos)

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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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


@argumentContext(MINECRAFT_FLOAT_RANGE.name)
class FloatRangeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		float1Regex = r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)'
		float2Regex = r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
		separatorRegex = r'\.\.'
		pattern = re.compile(strToBytes(f"{float1Regex}(?:{separatorRegex}(?:{float2Regex})?)?|{separatorRegex}{float2Regex}"))
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentContext(MINECRAFT_GAME_PROFILE.name)
class GameProfileHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# TODO: parseGameProfile(...)
		return EntityHandler().parse(sr, ai, filePath, errorsIO=errorsIO)


@argumentContext(MINECRAFT_INT_RANGE.name)
class IntRangeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		intRegex = r'-?[0-9]+'
		separatorRegex = r'\.\.'
		pattern = re.compile(strToBytes(f"{intRegex}(?:{separatorRegex}(?:{intRegex})?)?|{separatorRegex}{intRegex}"))
		range_ = sr.tryReadRegex(pattern)
		if range_ is None:
			return None
		return makeParsedArgument(sr, ai, value=range_)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return ['0...']


@argumentContext(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(rb'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		slot: str = node.value
		if slot not in getCurrentFullMcData().slots:
			errorsIO.append(CommandSemanticsError(UNKNOWN_MSG.format("item slot",  slot), node.span, style='error'))

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return [bytesToStr(slot) for slot in getCurrentFullMcData().slots.keys()]


@argumentContext(MINECRAFT_ITEM_STACK.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=False))
@argumentContext(MINECRAFT_ITEM_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=True))
class ItemStackHandler(ArgumentContext):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# item_id{data_tags}
		itemID = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)

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
			errorsIO.append(CommandSemanticsError(INTERNAL_ERROR_MSG.format(EXPECTED_BUT_GOT_MSG, '`ItemStack`', type(itemStack).__name__), node.span))
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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


# @argumentContext(MINECRAFT_NBT_COMPOUND_TAG.name)
# class NbtCompoundTagHandler(ArgumentContext):
# 	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
# 		nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
# 		if nbt is None:
# 			return None
# 		return makeParsedArgument(sr, ai, value=nbt)


@argumentContext(MINECRAFT_NBT_PATH.name)
class NbtPathHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		path = parseNBTPath(sr, errorsIO=errorsIO)
		if path is None:
			return None
		return makeParsedArgument(sr, ai, value=path)


@argumentContext(MINECRAFT_NBT_COMPOUND_TAG.name)
@argumentContext(MINECRAFT_NBT_TAG.name)
class NbtTagHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return NBTTagSchema('')

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return LanguageId('SNBT')

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return dict(ignoreTrailingChars=True)

	# def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
	# 	nbt = parseNBTTag(sr, errorsIO=errorsIO)
	# 	if nbt is None:
	# 		return None
	# 	return makeParsedArgument(sr, ai, value=nbt)


@argumentContext(MINECRAFT_OBJECTIVE.name)
class ObjectiveHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		pattern = re.compile(rb"[a-zA-Z0-9_.+-]+")
		objective = sr.tryReadRegex(pattern)
		if objective is None:
			return None
		return makeParsedArgument(sr, ai, value=objective)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		if len(node.value) > 16 and getCurrentFullMcData().name < '1.18':
			errorsIO.append(CommandSemanticsError(OBJECTIVE_NAME_LONGER_THAN_16_MSG.format(), node.span, style='error'))


@argumentContext(MINECRAFT_ROTATION.name)
class RotationHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		numberReader = sr.tryReadFloat
		sr.save()
		yaw: Optional[bytes] = numberReader() or sr.tryReadTildeNotation()
		if yaw is None:
			sr.rollback()
			return None
		sr.mergeLastSave()
		if not sr.tryConsumeByte(ord(' ')):
			sr.rollback()
			return None

		pitch: Optional[bytes] = numberReader() or sr.tryReadTildeNotation()
		if pitch is None:
			sr.rollback()
			return None
		sr.mergeLastSave()

		rotation = (yaw, pitch)
		return makeParsedArgument(sr, ai, value=rotation)


@argumentContext(MINECRAFT_SCORE_HOLDER.name)
class ScoreHolderHandler(EntityHandler):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		literal = sr.tryReadLiteral()
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_SWIZZLE.name)
class SwizzleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# -, +, ., _, A-Z, a-z, and 0-9
		literal = sr.tryReadRegex(re.compile(rb'[-+._A-Za-z0-9]+'))
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_TIME.name)
class TimeHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
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
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# 8-4-4-4-12
		literal = sr.tryReadRegex(UUID_PATTERN)
		if literal is None:
			return None
		return makeParsedArgument(sr, ai, value=literal)


@argumentContext(MINECRAFT_VEC2.name)
class Vec2Handler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse2dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return _get2dPosSuggestions(ai, node, pos, replaceCtx, useFloat=True)


@argumentContext(MINECRAFT_VEC3.name)
class Vec3Handler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=True, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return _get3dPosSuggestions(ai, node, pos, replaceCtx, useFloat=True)


@argumentContext(ST_DPE_DATAPACK.name)
class StDpeDataPackHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


# make sure there's an ArgumentContext for every registered named ArgumentType:
checkArgumentContextsForRegisteredArgumentTypes()
