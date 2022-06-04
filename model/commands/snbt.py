import functools as ft
from typing import Optional

from nbtlib import Parser, tokenize, Base, Byte, Short, Int, Long, Float, Double, String, List, Compound, ByteArray, IntArray, LongArray, Path, \
	ListIndex, CompoundMatch, InvalidLiteral
from nbtlib.path import can_be_converted_to_int, NamedKey, extend_accessors

from Cat.utils import escapeForXml
from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclass, OrderedDict
from model.commands.stringReader import StringReader
from model.commands.utils import CommandSyntaxError
from model.nbt.snbtParser import SNBTParser, SNBTError
from model.nbt.tags import NBTTag, ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag, ListTag, CompoundTag, ByteArrayTag, IntArrayTag, LongArrayTag, NBTTagSchema
from model.parsing.bytesUtils import bytesToStr
from model.parsing.contextProvider import parseNPrepare
from model.utils import Span, GeneralError, LanguageId


def _parseNBTTagBare(sr: StringReader, *, errorsIO: list[CommandSyntaxError]) -> Optional[Base]:
	# parse_nbt('{foo: [hello, world], bar: [I; 1, 2, 3]}')
	sr.save()
	literal = sr.source[sr.cursor:]
	if not literal:
		sr.rollback()
		return None
	try:
		parser = Parser(tokenize(literal))
		tag = parser.parse()

		cursor = parser.token_span[1]
		# account for whitespace at the end:
		strVal = literal[:cursor]
		strVal = strVal.rstrip()
		cursor = len(strVal)

		sr.cursor += cursor
	except InvalidLiteral as ex:
		if ex.args[0] != (0, 1):
			message = ex.args[1]
			start = ex.args[0][0] + sr.cursor
			stop = ex.args[0][1] + sr.cursor
			begin = sr.posFromColumn(start)
			end = sr.posFromColumn(stop)
			errorsIO.append(CommandSyntaxError(escapeForXml(message), Span(begin, end), style='error'))
		sr.rollback()
		return None
	return tag


def parseNBTTag1(sr: StringReader, *, errorsIO: list[CommandSyntaxError]) -> Optional[NBTTag]:
	tag: Optional[Base] = _parseNBTTagBare(sr, errorsIO=errorsIO)
	if tag is None:
		return None
	result = convertTag(tag)
	return result


def parseNBTTag3(sr: StringReader, *, errorsIO: list[GeneralError]) -> Optional[NBTTag]:
	# parse_nbt('{foo: [hello, world], bar: [I; 1, 2, 3]}')
	sr.save()
	literal = sr.source[sr.cursor:]
	if not literal:
		sr.rollback()
		return None

	tag, errors = parseNPrepare(
		sr.source[sr.cursor:],
		language=LanguageId('SNBT'),
		schema=NBTTagSchema(''),
		line=sr._lineNo,
		lineStart=sr._lineStart,
		cursor=0,
		cursorOffset=sr.cursor + sr._lineStart,
		ignoreTrailingChars=True
	)

	# parser = SNBTParser(literal, ignoreTrailingChars=True)
	# tag = parser.parseNBTTag()
	#
	# for ex in parser.errors:
	# 	message = ex.message
	# 	start = ex.span.start.index + sr.cursor
	# 	stop = ex.span.end.index + sr.cursor
	# 	begin = sr.posFromColumn(start)
	# 	end = sr.posFromColumn(stop)
	# 	style = ex.style
	# 	errorsIO.append(SNBTError(message, Span(begin, end), style=style))
	errorsIO.extend(errors)

	if tag is not None:
		sr.cursor += tag.span.length
		sr._lineNo = tag.span.end.line
		sr._lineStart = tag.span.end.index - tag.span.end.column
	else:
		sr.rollback()
	return tag


parseNBTTag = parseNBTTag3


class InvalidPath(ValueError):
	"""Raised when creating an invalid nbt path."""

	def __str__(self):
		return f"{self.args[1]} at position {self.args[0][0]}"


def parse_accessors(parser: Parser, literal: str):
	while True:
		try:
			tag = parser.parse()
		except InvalidLiteral as exc:
			raise InvalidPath(exc.args[0], f"Invalid path. ({exc.args[1]})") from exc

		if isinstance(tag, String):
			if parser.current_token.type == "QUOTED_STRING":
				yield NamedKey(tag[:])
			else:
				yield from (NamedKey(key) for key in tag.split(".") if key)

		elif isinstance(tag, List):
			if not tag:
				yield ListIndex(index=None)
			elif len(tag) != 1:
				raise InvalidPath(None, "Brackets should only contain one element")
			elif issubclass(tag.subtype, Compound):
				yield ListIndex(index=None)
				yield CompoundMatch(tag[0])
			elif issubclass(tag.subtype, Int) or can_be_converted_to_int(tag[0]):
				yield ListIndex(int(tag[0]))
			else:
				raise InvalidPath(
					None, "Brackets should only contain an integer or a compound"
				)

		elif isinstance(tag, Compound):
			yield CompoundMatch(tag)

		elif parser.current_token.type == "NUMBER":
			yield from (
				NamedKey(key) for key in parser.current_token.value.split(".") if key
			)

		else:
			raise InvalidPath(None, f"Invalid path element {tag}")

		try:
			nextCharPos = parser.token_span[1] - 1
			if nextCharPos < len(literal) and literal[nextCharPos] in {' ', '\t'}:
				break
			parser.next()
		except InvalidLiteral:
			break


def _parseNBTPathBare(sr: StringReader, *, errorsIO: list[CommandSyntaxError]) -> Optional[NBTTag]:
	sr.save()

	literal = sr.source[sr.cursor:]
	literal = bytesToStr(literal)  # TODO utf-8-ify _parseNBTPathBare(...)!
	parser = None
	try:
		parser = Parser(tokenize(literal))
	except InvalidLiteral:
		accessorsIter = ()
	else:
		accessorsIter = parse_accessors(parser, literal)

	try:
		accessors = ()
		for accessor in accessorsIter:
			accessors = extend_accessors(accessors, accessor)

		path = Path.from_accessors(accessors)
		if parser is not None:
			cursor = parser.token_span[1]
			if cursor != len(literal):
				cursor -= 1
			sr.cursor += cursor
	except (InvalidLiteral, InvalidPath) as ex:
		message = ex.args[1]
		if ex.args[0] is None:
			begin, end = sr.currentSpan.asTuple
		else:
			start = ex.args[0][0] + sr.cursor
			stop = ex.args[0][1] + sr.cursor
			begin = sr.posFromColumn(start)
			end = sr.posFromColumn(stop)
		errorsIO.append(CommandSyntaxError(escapeForXml(message), Span(begin, end), style='error'))
		sr.rollback()
		return None

	return path


def parseNBTPath(sr: StringReader, *, errorsIO: list[CommandSyntaxError]) -> Optional[Path]:
	path: Optional[Path] = _parseNBTPathBare(sr, errorsIO=errorsIO)
	if path is None:
		return None
	return path
	# result = convertTag(path)
	# return result


__tagConverters: dict = {}
TagConverter = AddToDictDecorator(__tagConverters)
getTagConverter = ft.partial(getIfKeyIssubclass, __tagConverters)


def convertTag(tag: Base) -> NBTTag:
	tagType = type(tag)
	converter = getTagConverter(tagType)
	return converter(tag)

# @TagConverter(Boolean)
# def convertBooleanTag(tag: Boolean) -> BooleanTag:
# 	pass


@TagConverter(Byte)
def convertByteTag(tag: Byte) -> ByteTag:
	return ByteTag(int(tag))


@TagConverter(Short)
def convertShortTag(tag: Short) -> ShortTag:
	return ShortTag(int(tag))


@TagConverter(Int)
def convertIntTag(tag: Int) -> IntTag:
	return IntTag(int(tag))


@TagConverter(Long)
def convertLongTag(tag: Long) -> LongTag:
	return LongTag(int(tag))


@TagConverter(Float)
def convertFloatTag(tag: Float) -> FloatTag:
	return FloatTag(float(tag))


@TagConverter(Double)
def convertDoubleTag(tag: Double) -> DoubleTag:
	return DoubleTag(float(tag))


@TagConverter(String)
def convertStringTag(tag: String) -> StringTag:
	return StringTag(tag)


@TagConverter(List)
def convertListTag(tag: List) -> ListTag:
	return ListTag([convertTag(t) for t in tag])


@TagConverter(Compound)
def convertCompoundTag(tag: Compound) -> CompoundTag:
	return CompoundTag(OrderedDict((n, convertTag(t)) for n, t in tag.items()))


@TagConverter(ByteArray)
def convertByteArrayTag(tag: ByteArray) -> ByteArrayTag:
	return ByteArrayTag([convertByteTag(t) for t in tag])


@TagConverter(IntArray)
def convertIntArrayTag(tag: IntArray) -> IntArrayTag:
	return IntArrayTag([convertIntTag(t) for t in tag])


@TagConverter(LongArray)
def convertLongArrayTag(tag: LongArray) -> LongArrayTag:
	return LongArrayTag([convertLongTag(t) for t in tag])

