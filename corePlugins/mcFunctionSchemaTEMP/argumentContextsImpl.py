import re
from abc import abstractmethod, ABC
from typing import Optional, Iterable, Any

from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getClickableRanges, onIndicatorClicked, getDocumentation, parseNPrepare, CtxInfo, \
	prepareTree
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema
from base.model.pathUtils import FilePath
from base.model.session import getSession
from base.model.utils import Span, Position, GeneralError, MDStr, Message, LanguageId
from corePlugins.datapack.datapackContents import ResourceLocation, ResourceLocationNode, ResourceLocationSchema
from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.argumentValues import BlockState, ItemStack, FilterArguments, TargetSelector
from corePlugins.mcFunction.command import ArgumentSchema, ParsedArgument, CommandPart
from corePlugins.mcFunction.commandContext import ArgumentContext, argumentContext, makeParsedArgument, missingArgumentParser, getArgumentContext
from corePlugins.mcFunction.snbt import parseNBTPath
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.mcFunction.utils import CommandSyntaxError, CommandSemanticsError
from corePlugins.mcFunctionSchemaTEMP.argumentParsersImpl import _parse3dPos, tryReadNBTCompoundTag, _parseResourceLocation, _parse2dPos, _get3dPosSuggestions, _get2dPosSuggestions
from corePlugins.mcFunctionSchemaTEMP.filterArgs import parseFilterArgs, suggestionsForFilterArgs, clickableRangesForFilterArgs, onIndicatorClickedForFilterArgs, \
	FilterArgumentInfo, validateFilterArgs
from corePlugins.mcFunctionSchemaTEMP.targetSelector import TARGET_SELECTOR_ARGUMENTS_DICT
from corePlugins.nbt.tags import NBTTagSchema
from model.messages import *
# from sessionOld.session import getSession


def initPlugin() -> None:
	pass


OBJECTIVE_NAME_LONGER_THAN_16_MSG: Message = Message(f"Objective names cannot be longer than 16 characters.", 0)


class ResourceLocationLikeHandler(ArgumentContext, ABC):
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
	def schema(self) -> ResourceLocationSchema:
		pass

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, self.schema)

	def prepare(self, node: ParsedArgument, info: CtxInfo[ParsedArgument], errorsIO: list[GeneralError]) -> None:
		prepareTree(node.value, node.source, info.filePath)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		validateTree(node.value, node.source, errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		if node is None:
			value = ResourceLocationNode.fromString(b'', Span(pos), self.schema)
			return getSuggestions(value, b'', pos, replaceCtx)
		else:
			return getSuggestions(node.value, node.source, pos, replaceCtx)

	def getDocumentation(self, node: ParsedArgument, position: Position) -> MDStr:
		return getDocumentation(node.value, node.source, position) or super(ResourceLocationLikeHandler, self).getDocumentation(node, position)

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.value, node.source, node.span)

	def onIndicatorClicked(self, node: ParsedArgument, position: Position) -> None:
		return onIndicatorClicked(node.value, node.source, position)


class ParsingHandler(ArgumentContext, ABC):

	@abstractmethod
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		pass

	def getParserKwArgs(self, ai: ArgumentSchema) -> dict[str, Any]:
		return {}

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# remainder = sr.tryReadRemaining()
		if sr.hasReachedEnd:
			return None
		sr.save()
		schema = self.getSchema(ai)
		language = self.getLanguage(ai)

		data, errors = parseNPrepare(
			sr.source[sr.cursor:],
			filePath=filePath,
			language=language,
			schema=schema,
			line=sr._lineNo,
			lineStart=sr._lineStart,
			cursor=0,
			cursorOffset=sr.cursor + sr._lineStart,
			**self.getParserKwArgs(ai)
		)
		# sr.tryReadRemaining()

		errorsIO.extend(errors)
		if data is not None:
			sr.cursor += data.span.length
			sr._lineNo = data.span.end.line
			sr._lineStart = data.span.end.index - data.span.end.column
			return makeParsedArgument(sr, ai, value=data)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		validateTree(node.value, node.source, errorsIO)
		# errors = validateJson(node.value)
		# nss = node.span.start
		# for er in errors:
		# 	s = Position(
		# 		nss.line,
		# 		nss.column + er.span.start.index,
		# 		nss.index + er.span.start.index
		# 	)
		# 	e = Position(
		# 		nss.line,
		# 		nss.column + er.span.end.index,
		# 		nss.index + er.span.end.index
		# 	)
		# 	if isinstance(er, GeneralError):
		# 		er.span = Span(s, e)
		# 	else:
		# 		er = CommandSemanticsError(er.message, Span(s, e), er.style)
		# 	errorsIO.append(er)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		"""
		:param ai:
		:param node:
		:param pos: cursor position
		:param replaceCtx: the string that will be replaced
		:return:
		"""
		if node is not None:
			return getSuggestions(node.value, node.source, pos, replaceCtx)
		return []

	def getDocumentation(self, node: ParsedArgument, pos: Position) -> MDStr:
		docs = [
			super(ParsingHandler, self).getDocumentation(node, pos),
			getDocumentation(node.value, node.source, pos)
		]
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: ParsedArgument) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.value, node.source)

	def onIndicatorClicked(self, node: ParsedArgument, pos: Position) -> None:
		onIndicatorClicked(node.value, node.source, pos)


@argumentContext(BRIGADIER_BOOL.name)
class BoolHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadBoolean()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[CommandPart], pos: Position, replaceCtx: str) -> Suggestions:
		return ['true', 'false']


@argumentContext(BRIGADIER_DOUBLE.name)
class DoubleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_FLOAT.name)
class FloatHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadFloat()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_INTEGER.name)
class IntegerHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_LONG.name)
class LongHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadInt()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


@argumentContext(BRIGADIER_STRING.name)
class StringHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadString()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)


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


@argumentContext(MINECRAFT_BLOCK_STATE.name)
class BlockStateHandler(ArgumentContext):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	def _getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		return getSession().minecraftData.getBlockStatesDict(blockID)

	rlcSchema = ResourceLocationSchema('', 'block')

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# block_id[block_states]{data_tags}
		blockID = sr.readResourceLocation(allowTag=self._allowTag)
		blockID = ResourceLocationNode.fromString(blockID, sr.currentSpan, self.rlcSchema)

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
		if pos.index >= argsStart.index:
			blockStatesDict = self._getBlockStatesDict(blockID)
			suggestions += suggestionsForFilterArgs(blockState.states, node.source[argsStart.index:node.end.index], pos.index - argsStart.index, pos, replaceCtx, blockStatesDict)

		if blockID.span.__contains__(pos):
			suggestions += getSuggestions(blockState.blockId, node.source, pos, replaceCtx)
			# suggestions += rlc.BlockContext(self._allowTag).getSuggestions(contextStr, cursorPos, replaceCtx)

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


@argumentContext(MINECRAFT_BLOCK_PREDICATE.name)
class BlockPredicateHandler(BlockStateHandler):
	def __init__(self):
		super().__init__(allowTag=True)

	rlcSchema = ResourceLocationSchema('', 'block_type')


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


@argumentContext(MINECRAFT_DIMENSION.name)
class DimensionHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'dimension')


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


@argumentContext(MINECRAFT_ENTITY_SUMMON.name)
class EntitySummonHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'entity_summon')


@argumentContext(MINECRAFT_ENTITY_TYPE.name)
class EntityTypeHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'entity_type')


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


@argumentContext(MINECRAFT_FUNCTION.name)
class FunctionHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'function')


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


@argumentContext(MINECRAFT_ITEM_ENCHANTMENT.name)
class ItemEnchantmentHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'enchantment')


@argumentContext(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(rb'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		slot: str = node.value
		if slot not in getSession().minecraftData.slots:
			errorsIO.append(CommandSemanticsError(UNKNOWN_MSG.format("item slot",  slot), node.span, style='error'))

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		return [bytesToStr(slot) for slot in getSession().minecraftData.slots.keys()]


@argumentContext(MINECRAFT_ITEM_STACK.name)
class ItemStackHandler(ArgumentContext):
	def __init__(self, allowTag: bool = False):
		super().__init__()
		self._allowTag: bool = allowTag

	rlcSchema = ResourceLocationSchema('', 'item')

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# item_id{data_tags}
		itemID = sr.readResourceLocation(allowTag=self._allowTag)
		itemID = ResourceLocationNode.fromString(itemID, sr.currentSpan, self.rlcSchema)

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


@argumentContext(MINECRAFT_ITEM_PREDICATE.name)
class ItemPredicateHandler(ItemStackHandler):
	def __init__(self):
		super().__init__(allowTag=True)


@argumentContext(MINECRAFT_MESSAGE.name)
class MessageHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


@argumentContext(MINECRAFT_MOB_EFFECT.name)
class MobEffectHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'mob_effect')


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
		if len(node.value) > 16 and getSession().minecraftData.name < '1.18':
			errorsIO.append(CommandSemanticsError(OBJECTIVE_NAME_LONGER_THAN_16_MSG.format(), node.span, style='error'))


@argumentContext(MINECRAFT_OBJECTIVE_CRITERIA.name)
class ObjectiveCriteriaHandler(ArgumentContext):
	rlcSchema = ResourceLocationSchema('', 'any_no_tag')

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, self.rlcSchema)
		# TODO: add validation for objective_criteria


@argumentContext(MINECRAFT_PARTICLE.name)
class ParticleHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'particle')


@argumentContext(MINECRAFT_PREDICATE.name)
class PredicateHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'predicate')


@argumentContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'any_no_tag')


@argumentContext(DPE_ADVANCEMENT.name)
class ResourceLocationHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'advancement')


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


@argumentContext(DPE_BIOME_ID.name)
class BiomeIdHandler(ResourceLocationLikeHandler):

	@property
	def schema(self) -> ResourceLocationSchema:
		return ResourceLocationSchema('', 'biome')


@argumentContext(ST_DPE_DATAPACK.name)
class StDpeDataPackHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


# check if there's an ArgumentContext for every registered named ArgumentType:
for name, argType in ALL_NAMED_ARGUMENT_TYPES.items():
	if name != argType.name:
		raise ValueError(f"argumentType {argType.name!r} registered under wrong name {name!r}.")
	if getArgumentContext(argType) is None:
		raise ValueError(f"missing argumentContext for argumentType {argType.name!r}.")
