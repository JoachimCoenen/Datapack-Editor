import re
from math import inf
from typing import Any, Callable, Optional, ClassVar

from better_orderedmultidict import OrderedMultiDict

from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr, strToBytes, bytesOptToStr
from base.model.parsing.contextProvider import Suggestions, errorMsg
from base.model.parsing.schemaStore import GLOBAL_SCHEMA_STORE
from base.model.parsing.tree import Schema, Node
from base.model.pathUtils import FilePath
from base.model.utils import GeneralError, LanguageId, Message, Position, Span
from cat.utils.collections_ import FrozenDict
from cat.utils.logging_ import logError
from corePlugins.mcFunction.argumentContextsImpl import ParsingHandler, checkArgumentContextsForRegisteredArgumentTypes
from corePlugins.mcFunction.argumentTypes import makeLiteralsArgumentType
from corePlugins.mcFunction.command import ArgumentSchema, CommandPart, ParsedArgument
from corePlugins.mcFunction.commandContext import ArgumentContext, argumentContext, makeParsedArgument, \
	missingArgumentParser, StructuredArgumentContext
from corePlugins.mcFunction.filterArgs import FilterArgOptions, parseFilterArgsLike, FALLBACK_FILTER_ARGUMENT_INFO, \
	FilterArgumentInfo
from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.minecraft.resourceLocation import RESOURCE_LOCATION_ID, ResourceLocation, ResourceLocationNode, ResourceLocationSchema
from corePlugins.minecraft_data.fullData import getCurrentFullMcData
from corePlugins.nbt import SNBT_ID
from corePlugins.nbt.path import NBTPathSchema, SNBT_PATH_ID
from corePlugins.nbt.tags import NBTTagSchema
from .argumentParsersImpl import _parseVec, _readResourceLocation, tryReadNBTCompoundTag, tryReadNBTTag, readPredicateArgs
from .argumentTypes import *
from .argumentValues import BlockState, FilterArguments, ItemStack, TargetSelector, ItemSlot, ResourceLocationOrInlineNBT
from .itemComponents import ITEM_COMPONENT_ARG_OPTIONS
from .targetSelector import TARGET_SELECTOR_ARG_OPTIONS
from corePlugins.datapackVersions.commands.predicateArgs import PredicateArgs

OBJECTIVE_NAME_LONGER_THAN_16_MSG: Message = Message(f"Objective names cannot be longer than 16 characters.", 0)


@argumentContext(MINECRAFT_DIMENSION.name, rlcSchema=ResourceLocationSchema('', 'dimension', allowTags=False))
@argumentContext(MINECRAFT_ENTITY_SUMMON.name, rlcSchema=ResourceLocationSchema('', 'entity_type', allowTags=False))
@argumentContext(MINECRAFT_ENTITY_TYPE.name, rlcSchema=ResourceLocationSchema('', 'entity_type', allowTags=True))
@argumentContext(MINECRAFT_FUNCTION.name, rlcSchema=ResourceLocationSchema('', 'functions', allowTags=True))
@argumentContext(MINECRAFT_ITEM_ENCHANTMENT.name, rlcSchema=ResourceLocationSchema('', 'enchantment', allowTags=False))
@argumentContext(MINECRAFT_MOB_EFFECT.name, rlcSchema=ResourceLocationSchema('', 'mob_effect', allowTags=False))
@argumentContext(MINECRAFT_PARTICLE.name, rlcSchema=ResourceLocationSchema('', 'particle', allowTags=False))
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

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[ResourceLocationNode]:
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

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[ResourceLocationNode]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.getSchema(ai))


@argumentContext(MINECRAFT_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'predicate', allowTags=False), nbtSchema='minecraft:predicate')
@argumentContext(MINECRAFT_LOOT_TABLE.name, rlcSchema=ResourceLocationSchema('', 'loot_table', allowTags=False), nbtSchema='minecraft:loot_table')
@argumentContext(MINECRAFT_LOOT_MODIFIER.name, rlcSchema=ResourceLocationSchema('', 'item_modifier', allowTags=False), nbtSchema='minecraft:item_modifier')
class ResourceLocationOrSNBTHandler(StructuredArgumentContext):
	def __init__(self, rlcSchema: ResourceLocationSchema, nbtSchema: str):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema
		self.nbtSchema: str = nbtSchema

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		resLoc = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)
		if resLoc is not None:
			value = ResourceLocationOrInlineNBT(resLoc=resLoc, nbt=None)
			return makeParsedArgument(sr, ai, value=value)

		nbtTagSchema = GLOBAL_SCHEMA_STORE.get(self.nbtSchema, LanguageId('SNBT'))
		if nbtTagSchema is None:
			nbtTagSchema = NBTTagSchema('')
		nbt = tryReadNBTTag(sr, nbtTagSchema, filePath, errorsIO=errorsIO)
		if nbt is not None:
			value = ResourceLocationOrInlineNBT(resLoc=None, nbt=nbt)
			return makeParsedArgument(sr, ai, value=value)
		return None

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[ResourceLocationNode]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.rlcSchema)


@argumentContext(MINECRAFT_ANGLE.name)
class AngleHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return _parseVec(sr, ai, useFloat=True, count=1, notation=b'~')


@argumentContext(MINECRAFT_BLOCK_STATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=False))
@argumentContext(MINECRAFT_BLOCK_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'block', allowTags=True))
class BlockStateHandler(StructuredArgumentContext[BlockState]):
	def __init__(self, rlcSchema: ResourceLocationSchema):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema

	def _getBlockStatesDict(self, blockID: ResourceLocation) -> dict[bytes, FilterArgumentInfo]:
		blockStates = getCurrentFullMcData().getBlockStates(blockID)
		return {strToBytes(argument.name): argument.fai for argument in blockStates}

	def _getBlockStatesArgOptions(self, blockStates: dict[bytes, FilterArgumentInfo]) -> FilterArgOptions:
		return FilterArgOptions(
			opening=b'[',
			closing=b']',
			keySchema=ArgumentSchema(
				name='key',
				type=makeLiteralsArgumentType(list(blockStates.keys())),
			),
			getArgsInfo=lambda key: blockStates.get(key.content, FALLBACK_FILTER_ARGUMENT_INFO),
			description=""
		)  # todo: improve performance!

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# block_id[block_states]{data_tags}
		blockID = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)
		if blockID is None:
			return None
		# block states:
		states = None
		if sr.tryPeek() == ord('['):
			blockStatesDict = self._getBlockStatesDict(blockID)
			blockStatesOptions = self._getBlockStatesArgOptions(blockStatesDict)
			states: Optional[FilterArguments] = parseFilterArgsLike(sr, blockStatesOptions, filePath, errorsIO=errorsIO)
			if states is not None:
				sr.mergeLastSave()
		if states is None:
			currentPos = sr.currentPos
			blockStatesOptions = self._getBlockStatesArgOptions({})
			states = FilterArguments(Span(currentPos), blockStatesOptions, sr.fullSource, OrderedMultiDict())
		# data tags:
		if sr.tryConsumeByte(ord('{')):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, NBTTagSchema(''), filePath, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		blockPredicate = BlockState(blockId=blockID, states=states, nbt=nbt)
		return makeParsedArgument(sr, ai, value=blockPredicate)

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[Node]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.rlcSchema)


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
class EntityHandler(StructuredArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID.
		locator = sr.tryReadString()
		if locator is None:
			# tryParse Target selector:
			variable = sr.tryReadRegex(re.compile(rb'@[praes]\b'))
			if variable is None:
				return None
			variable = bytesToStr(variable)
			arguments = parseFilterArgsLike(sr, TARGET_SELECTOR_ARG_OPTIONS, filePath, errorsIO=errorsIO)
			if arguments is None:
				currentPos = sr.currentPos
				blockStatesOptions = TARGET_SELECTOR_ARG_OPTIONS
				arguments = FilterArguments(Span(currentPos), blockStatesOptions, sr.fullSource, OrderedMultiDict())
			else:
				sr.mergeLastSave()
			locator = TargetSelector(variable=variable, arguments=arguments)

		return makeParsedArgument(sr, ai, value=locator)

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[Node]:
		return None  # not needed

	SELECTOR_SUGGESTIONS : ClassVar[Suggestions] = ['@a', '@e', '@s', '@p', '@r', ]

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		if node is None or pos.index - node.span.start.index < 2:
			return self.SELECTOR_SUGGESTIONS
		else:
			return super().getSuggestions2(ai, node, pos, replaceCtx)


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
class NumberRangeHandler(ArgumentContext):
	def __init__(self, pattern: re.Pattern[bytes], numberParser: Callable[[str], int | float]):
		super().__init__()
		self.pattern: re.Pattern[bytes] = pattern
		self.numberParser: Callable[[str], int | float] = numberParser

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		groups = sr.tryReadRegexGroups(self.pattern)
		if groups is None:
			return None

		args = ai.args or FrozenDict.EMPTY
		stringMin = groups[0]
		separator = groups[1] or groups[3]
		stringMax = groups[2] or groups[4]
		numberMin = args.get('minVal', -inf) if not stringMin else self.numberParser(bytesToStr(stringMin))
		numberMax = args.get('maxVal', +inf) if not stringMax else self.numberParser(bytesToStr(stringMax))
		if not separator:  # we only have one number
			if not stringMin:
				numberMin = numberMax
			elif not stringMax:
				numberMax = numberMin
			else:
				raise TypeError("Internal Error that should never be possible. Has a RegEx gone bad?")

		return makeParsedArgument(sr, ai, (numberMin, numberMax))

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		if node.value is None:
			return
		args = node.schema.args or FrozenDict.EMPTY
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
				suggestions.setdefault(f'..{maxStr}')
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


@argumentContext(MINECRAFT_ITEM_SLOT.name, allowWildcard=False)
@argumentContext(MINECRAFT_ITEM_SLOTS.name, allowWildcard=True)
class ItemSlotHandler(ArgumentContext):
	def __init__(self, allowWildcard: bool):
		super().__init__()
		self.allowWildcard: bool = allowWildcard

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		if self.allowWildcard:
			slot = sr.tryReadRegex(re.compile(rb'\w+(?:\.\w+)*(?:\.\*?)?'))
		else:
			slot = sr.tryReadRegex(re.compile(rb'\w+(?:\.\w+)*\.?'))

		if slot is None:
			return None

		slots = getCurrentFullMcData().slots
		if slot not in slots:
			slotType, _, slotNumber = slot.rpartition(b'.')
		else:
			slotType, slotNumber = slot, None

		isValid = slotType in slots and (slotNumber in slots[slotType] or (
				self.allowWildcard and slotNumber == b'*')
				and slots[slotType] and not (len(slots[slotType]) == 1 and None in slots[slotType])  # exclude those that do not have a slotNumber.
		)
		if not isValid:
			errorMsg(UNKNOWN_MSG, "item slot", bytesToStr(slot), span=sr.currentSpan, style='error', errorsIO=errorsIO)

		return makeParsedArgument(sr, ai, value=ItemSlot(bytesToStr(slotType), bytesOptToStr(slotNumber)))

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		slots = getCurrentFullMcData().slots
		suggestions = [bytesToStr(slotType if not slotNumber else slotType + b'.' + slotNumber) for slotType, slotNumbers in slots.items() for slotNumber in slotNumbers]
		if self.allowWildcard:
			suggestions += [
				bytesToStr(slotType + b'.*')
				for slotType, slotNumbers in slots.items()
				if slotNumbers and not (len(slotNumbers) == 1 and None in slotNumbers)  # exclude those that do not have a slotNumber.
			]
		return suggestions


@argumentContext(MINECRAFT_ITEM_STACK.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=False), allowWildcard=False)
@argumentContext(MINECRAFT_ITEM_PREDICATE.name, rlcSchema=ResourceLocationSchema('', 'item', allowTags=True), allowWildcard=True)
class ItemStackHandler(StructuredArgumentContext[ItemStack]):
	def __init__(self, rlcSchema: ResourceLocationSchema, allowWildcard: bool):
		super().__init__()
		self.rlcSchema: ResourceLocationSchema = rlcSchema
		self.allowWildcard: bool = allowWildcard

	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		itemID = _readResourceLocation(sr, filePath, self.rlcSchema, errorsIO=errorsIO)
		if itemID is None and self.allowWildcard and getCurrentFullMcData().name >= '1.20.5' and sr.tryPeek() == ord('*'):
			sr.save()
			sr.skip()
			itemID = '*'
		if itemID is None:
			return None

		if getCurrentFullMcData().name < '1.20.5':
			# until 1.20.5 (excl.):
			# data tags:
			if sr.tryPeek() == ord('{'):
				nbt = tryReadNBTCompoundTag(sr, NBTTagSchema(''), filePath, errorsIO=errorsIO)
				if nbt is not None:
					sr.mergeLastSave()
			else:
				nbt = None
			itemComponents = None
		else:
			# since 1.20.5 (incl.):
			# item Components:
			itemComponents = readPredicateArgs(sr, ITEM_COMPONENT_ARG_OPTIONS, filePath, errorsIO=errorsIO)
			if itemComponents is None:
				currentPos = sr.currentPos
				blockStatesOptions = ITEM_COMPONENT_ARG_OPTIONS
				itemComponents = PredicateArgs(Span(currentPos), blockStatesOptions, [])
			else:
				sr.mergeLastSave()
			nbt = None

		itemStack = ItemStack(itemId=itemID, nbt=nbt, components=itemComponents)
		return makeParsedArgument(sr, ai, value=itemStack)

	def getEmptyValueForSuggestions(self, ai: ArgumentSchema, pos: Position, replaceCtx: str) -> Optional[Node]:
		return ResourceLocationNode.fromString(b'', Span(pos), self.rlcSchema)


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


@argumentContext(MINECRAFT_STYLE.name)
class ComponentHandler(ParsingHandler):
	def getSchema(self, ai: ArgumentSchema) -> Optional[Schema]:
		return GLOBAL_SCHEMA_STORE.get('minecraft:raw_json_style', LanguageId('JSON'))

	def getLanguage(self, ai: ArgumentSchema) -> LanguageId:
		return LanguageId('JSON')


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
		number = float(bytesToStr(number))
		unit = sr.tryReadLiteral()
		if unit is None:
			unit = b't'
		elif unit not in (b'd', b's', b't'):
			sr.rollback()
			sr.rollback()
			return None
		else:
			sr.mergeLastSave()
		return makeParsedArgument(sr, ai, value=(number, unit))

	def validate(self, node: ParsedArgument, errorsIO: list[GeneralError]) -> None:
		number, unit = node.value

		match unit:
			case b't':
				ticks = number * 1
			case b's':
				ticks = number * 20
			case b'd':
				ticks = number * 24_000  # 24 thousand
			case _:
				logError(f"cannot validate a {MINECRAFT_TIME.name} with unknown unit '{bytesOptToStr(unit)}'")
				return

		args = node.schema.args or FrozenDict.EMPTY
		minVal = args.get('min', -inf)
		maxVal = args.get('max', +inf)

		if not minVal <= ticks <= maxVal:
			errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, minVal, maxVal, span=node.span, errorsIO=errorsIO)

	def getSuggestions2(self, ai: ArgumentSchema, node: Optional[ParsedArgument], pos: Position, replaceCtx: str) -> Suggestions:
		args = ai.args or FrozenDict.EMPTY
		minVal = args.get('min', -inf)
		maxVal = args.get('max', +inf)
		additionalSuggestions = args.get('suggestions', ())

		suggestions = []
		if replaceCtx and not replaceCtx.endswith(('t', 's', 'd')):
			suggestions.append(replaceCtx + 't')
			suggestions.append(replaceCtx + 's')
			suggestions.append(replaceCtx + 'd')
		elif node is not None and not node.content.endswith((b't', b's', b'd')):
			# this is justa workaround, because currently, replaceCtx is always empty for numbers.
			suggestions.append('t')
			suggestions.append('s')
			suggestions.append('d')

		def add(number: int):
			if number // 24_000 > 0 and number % 24_000 == 0:
				suggestions.append(f'{number//24_000}d')
			elif number // 20 > 0 and number % 20 == 0:
				suggestions.append(f'{number//20}s')
			else:
				suggestions.append(f'{number}t')

		for suggestion in additionalSuggestions:
			add(suggestion)

		if minVal > -inf:
			add(minVal)

		if minVal < 0 < maxVal:
			add(0)

		if minVal < maxVal < +inf:
			add(maxVal)

		return suggestions


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



@argumentContext(ST_DPE_HOSTNAME.name)
class StDpeHostnameHandler(ArgumentContext):
	def parse(self, sr: StringReader, ai: ArgumentSchema, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


# make sure there's an ArgumentContext for every registered named ArgumentType:
checkArgumentContextsForRegisteredArgumentTypes()
