import re
from dataclasses import replace
from itertools import chain
from json import JSONDecodeError
from typing import Optional, Iterable

from PyQt5.QtWidgets import QWidget

from Cat.utils.collections import OrderedDict
from Cat.utils.utils import HTMLStr
from model.commands.argumentHandlers import argumentHandler, ArgumentHandler, missingArgumentParser, makeParsedArgument, defaultDocumentationProvider
from model.commands.argumentParsersImpl import _parse3dPos, _parseBlockStates, tryReadNBTCompoundTag, _parseResourceLocation, _parseEntityLocator, _parse2dPos
from model.commands.argumentTypes import *
from model.commands.argumentValues import BlockState, ItemStack
from model.commands.command import ArgumentInfo
from model.commands.parsedCommands import ParsedArgument, ParsedCommandPart
from model.commands.snbt import parseNBTPath, parseNBTTag
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError, CommandSemanticsError
from model.data.dataValues import BLOCKS, DIMENSIONS, ITEMS, SLOTS, ENTITIES, EFFECTS, ENCHANTMENTS, BIOMES, PARTICLES
from model.datapackContents import ResourceLocation
from model.parsingUtils import Span, Position
from session.session import getSession


def _init():
	pass  # do not remove!


def _containsResourceLocation(rl: ResourceLocation, container: set[ResourceLocation]) -> bool:
	if rl.namespace == 'minecraft':
		rl = replace(rl, namespace=None)
	return rl in container


@argumentHandler(BRIGADIER_BOOL.name)
class BoolHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		string = sr.tryReadBoolean()
		if string is None:
			return None
		return makeParsedArgument(sr, ai, value=string)

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
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
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		useFloat = ai.args is not None and ai.args.get('type', None) is float
		return _parse3dPos(sr, ai, useFloat=useFloat, errorsIO=errorsIO)

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		return ['^ ^ ^', '~ ~ ~']


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
		states: Optional[OrderedDict[str, str]] = _parseBlockStates(sr, ai, errorsIO=errorsIO)
		if states is not None:
			sr.mergeLastSave()
		else:
			states = OrderedDict()
		# data tags:
		if sr.tryConsumeChar('{'):
			sr.cursor -= 1
			nbt = tryReadNBTCompoundTag(sr, ai, errorsIO=errorsIO)
		else:
			nbt = None
		if nbt is not None:
			sr.mergeLastSave()

		blockPredicate = BlockState.create(blockId=blockID, states=states, nbt=nbt)
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
			if not _containsResourceLocation(blockId, BLOCKS):
				return CommandSemanticsError(f"Unknown block id '{blockId.asString}'.", argument.span, style='warning')
		return None

	def getSuggestions(self, ai: ArgumentInfo) -> list[str]:
		result = [b.asString for b in BLOCKS]
		if self._allowTag:
			result.extend(b.asString for dp in getSession().world.datapacks for b in dp.contents.tags.blocks)
		return result

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		blockState: BlockState = argument.value
		if not isinstance(blockState, BlockState):
			return None

		blockId = blockState.blockId
		start = argument.span.end.copy()
		end = argument.span.end.copy()
		end.column = min(end.column, start.column + len(blockId.asString))
		end.index = min(end.index, start.index + len(blockId.asString))

		if blockId.isTag:
			span = Span(start, end)
			return [span]
		return None

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		for dp in getSession().world.datapacks:
			if (func := dp.contents.tags.blocks.get(argument.value)) is not None:
				# TODO: show prompt, when there are multiple files this applies to.
				fp = func.filePath
				window._tryOpenOrSelectDocument(fp)  # very bad...
				break


@argumentHandler(MINECRAFT_BLOCK_PREDICATE.name)
class BlockPredicateHandler(BlockStateHandler):
	def __init__(self, allowTag: bool = False):
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

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
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
class DimensionHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
		if not _containsResourceLocation(argument.value, DIMENSIONS):
			return CommandSemanticsError(f"Unknown dimension '{argument.value}'.", argument.span)
		else:
			return None

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		return [d.asString for d in DIMENSIONS]


@argumentHandler(MINECRAFT_ENTITY.name)
class EntityHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID.
		locator = _parseEntityLocator(sr, ai, errorsIO=errorsIO)
		if locator is None:
			return None
		return makeParsedArgument(sr, ai, value=locator)

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		return ['@a', '@e', '@s', '@p', '@r', ]


@argumentHandler(MINECRAFT_ENTITY_SUMMON.name)
class EntitySummonHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		entity: ResourceLocation = argument.value
		if not isinstance(entity, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{entity}'.", argument.span)

		if not _containsResourceLocation(entity, ENTITIES):
			return CommandSemanticsError(f"Unknown entity id '{entity.asString}'.", argument.span, style='warning')

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [b.asString for b in ENTITIES]
		return result


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

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		return ['0...']


@argumentHandler(MINECRAFT_FUNCTION.name)
class FunctionHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, allowTag=True, errorsIO=errorsIO)

	def validate(self, argument: ParsedCommandPart) -> Optional[CommandSemanticsError]:
		value: ResourceLocation = argument.value
		if value.isTag:
			isValid = any(value in dp.contents.tags.functions for dp in getSession().world.datapacks)
		else:
			isValid = any(value in dp.contents.functions for dp in getSession().world.datapacks)
		if isValid:
			return None
		else:
			if value.isTag:
				return CommandSemanticsError(f"function tag '{value.asString}' is never defined.", argument.span, style='warning')
			else:
				return CommandSemanticsError(f"Unknown function '{value.asString}'.", argument.span)

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [f.asString for dp in getSession().world.datapacks for f in chain(dp.contents.functions, dp.contents.tags.functions)]
		return result

	def getDocumentation(self, argument: ParsedCommandPart) -> HTMLStr:
		value: ResourceLocation = argument.value
		if not isinstance(value, ResourceLocation):
			return defaultDocumentationProvider(argument)
		if not value.isTag:
			for dp in getSession().world.datapacks:
				if (func := dp.contents.functions.get(value)) is not None:
					return func.documentation
		return defaultDocumentationProvider(argument)

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		return [argument.span]

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		for dp in getSession().world.datapacks:
			if (func := dp.contents.functions.get(argument.value)) is not None:
				fp = func.filePath
				window._tryOpenOrSelectDocument(fp)  # very bad...
				break

			if (func := dp.contents.tags.functions.get(argument.value)) is not None:
				# TODO: show prompt, when there are multiple files this applies to.
				fp = func.filePath
				window._tryOpenOrSelectDocument(fp)  # very bad...
				break


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

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		return ['0...']


@argumentHandler(MINECRAFT_ITEM_ENCHANTMENT.name)
class ItemEnchantmentHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		enchantment: ResourceLocation = argument.value
		if not isinstance(enchantment, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{enchantment}'.", argument.span)

		if not _containsResourceLocation(enchantment, ENCHANTMENTS):
			return CommandSemanticsError(f"Unknown enchantment '{enchantment.asString}'.", argument.span, style='warning')

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [b.asString for b in ENCHANTMENTS]
		return result


@argumentHandler(MINECRAFT_ITEM_SLOT.name)
class ItemSlotHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		slot = sr.tryReadRegex(re.compile(r'\w+(?:\.\w+)?'))
		if slot is None:
			return None
		return makeParsedArgument(sr, ai, value=slot)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		slot: str = argument.value
		if slot not in SLOTS:
			return CommandSemanticsError(f"Unknown item slot '{slot}'.", argument.span, style='error')

	def getSuggestions(self, ai: ArgumentInfo) -> list[str]:
		return list(SLOTS.keys())


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

		itemStack = ItemStack.create(itemId=itemID, nbt=nbt)
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
			if not (_containsResourceLocation(itemId, ITEMS) or _containsResourceLocation(itemId, BLOCKS)):
				return CommandSemanticsError(f"Unknown item id '{itemId.asString}'.", argument.span, style='warning')
		return None

	def getSuggestions(self, ai: ArgumentInfo) -> list[str]:
		result = [b.asString for b in chain(ITEMS, BLOCKS)]
		if self._allowTag:
			result.extend(b.asString for dp in getSession().world.datapacks for b in dp.contents.tags.items)
			result.extend(b.asString for dp in getSession().world.datapacks for b in dp.contents.tags.blocks)
		return result

	def getClickableRanges(self, argument: ParsedArgument) -> Optional[Iterable[Span]]:
		itemStack: ItemStack = argument.value
		if not isinstance(itemStack, ItemStack):
			return None

		itemId = itemStack.itemId
		if itemId.isTag:
			start = argument.span.end.copy()
			end = argument.span.end.copy()
			end.column = min(end.column, start.column + len(itemId.asString))
			end.index = min(end.index, start.index + len(itemId.asString))
			span = Span(start, end)
			return [span]
		return None

	def onIndicatorClicked(self, argument: ParsedArgument, position: Position, window: QWidget) -> None:
		for dp in getSession().world.datapacks:
			if (func := dp.contents.tags.items.get(argument.value)) is not None \
			or (func := dp.contents.tags.blocks.get(argument.value)) is not None:
				# TODO: show prompt, when there are multiple files this applies to.
				fp = func.filePath
				window._tryOpenOrSelectDocument(fp)  # very bad...
				break


@argumentHandler(MINECRAFT_ITEM_PREDICATE.name)
class ItemPredicateHandler(ItemStackHandler):
	def __init__(self, allowTag: bool = False):
		super().__init__(allowTag=True)


@argumentHandler(MINECRAFT_MESSAGE.name)
class MessageHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		message = sr.tryReadRemaining()
		if message is None:
			return None
		return makeParsedArgument(sr, ai, value=message)


@argumentHandler(MINECRAFT_MOB_EFFECT.name)
class MobEffectHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		effect: ResourceLocation = argument.value
		if not isinstance(effect, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{effect}'.", argument.span)

		if not _containsResourceLocation(effect, EFFECTS):
			return CommandSemanticsError(f"Unknown mob effect '{effect.asString}'.", argument.span, style='warning')

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [b.asString for b in EFFECTS]
		return result


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
		pattern = re.compile(r"[a-zA-Z0-9_.+-]{0,16}")
		objective = sr.tryReadRegex(pattern)
		if objective is None:
			return None
		return makeParsedArgument(sr, ai, value=objective)


@argumentHandler(MINECRAFT_OBJECTIVE_CRITERIA.name)
class ObjectiveCriteriaHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, allowTag=False, errorsIO=errorsIO)


@argumentHandler(MINECRAFT_PARTICLE.name)
class ParticleHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		particle: ResourceLocation = argument.value
		if not isinstance(particle, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{particle}'.", argument.span)

		if not _containsResourceLocation(particle, PARTICLES):
			return CommandSemanticsError(f"Unknown biome '{particle.asString}'.", argument.span, style='warning')

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [b.asString for b in PARTICLES]
		return result


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
class ScoreHolderHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		# Must be a player name, a target selector or a UUID, or *.
		locator = _parseEntityLocator(sr, ai, errorsIO=errorsIO)
		if locator is None:
			sr.save()
			if sr.tryConsumeChar('*'):
				locator = '*'
			else:
				locator = sr.tryReadLiteral()
				if locator is None:
					sr.rollback()
					return None
		return makeParsedArgument(sr, ai, value=locator)


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


@argumentHandler(MINECRAFT_UUID.name)
class UuidHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(MINECRAFT_VEC2.name)
class Vec2Handler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse2dPos(sr, ai, useFloat=True, errorsIO=errorsIO)


@argumentHandler(MINECRAFT_VEC3.name)
class Vec3Handler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parse3dPos(sr, ai, useFloat=True, errorsIO=errorsIO)


@argumentHandler(DPE_BIOME_ID.name)
class BiomeIdHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return _parseResourceLocation(sr, ai, errorsIO=errorsIO, allowTag=False)

	def validate(self, argument: ParsedArgument) -> Optional[CommandSemanticsError]:
		biome: ResourceLocation = argument.value
		if not isinstance(biome, ResourceLocation):
			return CommandSemanticsError(f"Internal Error! expected ResourceLocation , but got '{biome}'.", argument.span)

		if not _containsResourceLocation(biome, BIOMES):
			return CommandSemanticsError(f"Unknown biome '{biome.asString}'.", argument.span, style='warning')

	def getSuggestions(self, argument: ParsedCommandPart) -> list[str]:
		result = [b.asString for b in BIOMES]
		return result

@argumentHandler(ST_DPE_COMMAND.name)
class ST_DPE_COMMANDHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_DATAPACK.name)
class ST_DPE_DATAPACKHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_GAME_RULE.name)
class ST_DPE_GAME_RULEHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)


@argumentHandler(ST_DPE_RAW_JSON_TEXT.name)
class ST_DPE_RAW_JSON_TEXTHandler(ArgumentHandler):
	def parse(self, sr: StringReader, ai: ArgumentInfo, *, errorsIO: list[CommandSyntaxError]) -> Optional[ParsedArgument]:
		return missingArgumentParser(sr, ai, errorsIO=errorsIO)

	def getDocumentation(self, argument: ParsedCommandPart) -> HTMLStr:
		return defaultDocumentationProvider(argument)