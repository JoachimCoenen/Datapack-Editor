from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type, Callable, ClassVar, cast

from better_orderedmultidict import OrderedMultiDict

from base.model.messages import *
from base.model.parsing.bytesConstants import ORD_BACKSLASH
from base.model.parsing.bytesUtils import bytesToStr, strToBytes
from base.model.parsing.parser import ParserBase, IndexMapBuilder, IndexMapper
from base.model.utils import Message, Position, Span, MDStr, wrapInMDCode
from corePlugins.nbtJsonBase.core import StructureDataSchema, StructureDataNode, KeySchema, StructureValue
from corePlugins.nbtJsonBase.schema import pathify, enrichWithSchema
from .snbtTokenizer import SNBTTokenizer, Token, TokenType
from .tags import *

INVALID_NUMBER_MSG: Message = Message("Invalid {0}: '`{1}`'", 2)


type NumberTagCtor[T: int | float] = Callable[[Span, Optional[StructureDataSchema], T, bytes], NumberTag[T]]


@dataclass
class NumberInfo[T: int | float]:
	suffix: tuple[bytes, ...]
	min: T
	max: T
	name: str
	pyType: Type[T]
	numberTagCls: Type[NumberTag[T]]
	numberTagCtor: NumberTagCtor[T]


NUMBER_INFO = {
	ByteTag: NumberInfo((b'b', b'B'), -128, 127, 'a Byte', int, ByteTag, cast(NumberTagCtor, ByteTag)),
	ShortTag: NumberInfo((b's', b'S'), -32768,  32767, 'a Short', int, ShortTag, cast(NumberTagCtor, ShortTag)),
	IntTag: NumberInfo((b'',), -2147483648, 2147483647, 'a Int', int, IntTag, cast(NumberTagCtor, IntTag)),
	LongTag: NumberInfo((b'l', b'L'), -9223372036854775808, 9223372036854775807, 'a Long', int, LongTag, cast(NumberTagCtor, LongTag)),
	FloatTag: NumberInfo((b'f', b'F', b''), -3.4E+38, +3.4E+38, 'a Float', float, FloatTag, cast(NumberTagCtor, FloatTag)),
	DoubleTag: NumberInfo((b'd', b'D'), -1.7E+308, 1.7E+308, 'a Double', float, DoubleTag, cast(NumberTagCtor, DoubleTag)),
}

NUMBER_INFO_BY_SUFFIX: dict[bytes, NumberInfo] = {suffix: info for info in NUMBER_INFO.values() for suffix in info.suffix if suffix}


@dataclass
class SNBTParser(ParserBase[NBTNode, StructureDataSchema]):
	ignoreTrailingChars: bool = False
	_tokenizer: SNBTTokenizer = field(init=False)
	_current: Optional[Token] = field(init=False)
	_last: Optional[Token] = field(init=False, default=None)

	def __post_init__(self):
		super().__post_init__()
		self._tokenizer = SNBTTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
			self.fullSource,
			self.ignoreTrailingChars,
		)
		self.errors = self._tokenizer.errors  # sync errors
		self._current = self._tokenizer.nextToken()
		self._last = None

	def _error(self, message: MDStr, token: Optional[Token], style: str = 'error') -> None:
		if token is not None:
			self.error(message, span=token.span, style=style)
		else:
			self.error(message, span=Span(Position(0, 0, 0)), style=style)

	def _next(self) -> None:
		self._last = self._current
		self._current = self._tokenizer.nextToken()

	def _getContent(self, token: Token) -> bytes:
		return self.text[token.startEnd[0]:token.startEnd[1]]
		# return self.text[token.span.slice]

	def _consumeToken(self, kind: TokenType) -> bool:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG.format(f"{kind.name}", 'end of str'), self._last)
			return False
		if current.type != kind:
			content = self._getContent(current)
			self._error(EXPECTED_BUT_GOT_MSG.format(f"{kind.name}", bytesToStr(content)), current)
			return False
		self._next()
		return True

	def _consumeAnyOfToken(self, kinds: set[TokenType]) -> bool:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format(f"any of ({', '.join(wrapInMDCode(f'{k.name}') for k in kinds)})", 'end of str'), self._last)
			return False
		if current.type not in kinds:
			content = self._getContent(current)
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format(f"any of ({', '.join(wrapInMDCode(f'{k.name}') for k in kinds)})", wrapInMDCode(bytesToStr(content))), current)
			return False
		self._next()
		return True

	def parseNBTTag(self) -> Optional[StructureDataNode[NBTNode, StructureValue[NBTNode]]]:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format("a NBTTag", 'end of str'), self._last)
			return None

		parser = self._PARSER_BY_TYPE.get(current.type)
		if parser is not None:
			tag = parser(self)
			return tag
		else:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format("a NBTTag", self._current.type.name), current)
			return None
	
	def _parseStringOrBoolTag(self) -> Optional[NBTNode]:
		current = self._current
		content = self._getContent(current)
		if content == b'true':
			self._next()
			return BooleanTag(current.span, None, True, content)
		elif content == b'false':
			self._next()
			return BooleanTag(current.span, None, False, content)
		else:
			self._next()
			innerSlice = current.span.slice
			return StringTag(current.span, None, bytesToStr(content), content, content, innerSlice, self.indexMapper)
		
	def parseBooleanTag(self) -> Optional[BooleanTag]:
		current = self._current
		content = self._getContent(current)
		if content in {b'true', b'1b'}:
			self._next()
			return BooleanTag(current.span, None, True, content)
		elif content in {b'false', b'0b'}:
			self._next()
			return BooleanTag(current.span, None, False, content)
		else:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format('a boolean', wrapInMDCode(bytesToStr(content))), current)

	def _parseNumberTag(self) -> Optional[NumberTag]:
		# TODO: all numbers are interoperable (even int / float, ...)
		# TODO: floats & doubles don't need a suffix.
		current = self._current
		content = self._getContent(current)
		if not content:
			return None

		suffix = content[-1:]
		numberInfo = NUMBER_INFO_BY_SUFFIX.get(suffix)
		if numberInfo is not None:
			return self._parseNumberTagInternal(numberInfo)
		if any(c in content for c in b'.eE'):
			return self._parseNumberTagInternal(NUMBER_INFO[FloatTag])
		else:
			return self._parseNumberTagInternal(NUMBER_INFO[IntTag])

	# @overload
	# def _parseNumberTagInternal(self, cls: NumberTagCtor[int], suffix: tuple[bytes, ...], minVal: int, maxVal: int, name: str, number: Type[int]) -> Optional[NumberTag[int]]: ...
	# @overload
	# def _parseNumberTagInternal(self, cls: NumberTagCtor[float], suffix: tuple[bytes, ...], minVal: float, maxVal: float, name: str, number: Type[float]) -> Optional[NumberTag[float]]: ...

	def _parseNumberTagInternal[T: int | float](self, numberInfo: NumberInfo[T]) -> Optional[NumberTag[T]]:
		current = self._current
		content = self._getContent(current)
		if current.type == TokenType.Number:
			if content.endswith(numberInfo.suffix):
				try:
					strVal = content
					for sfx in numberInfo.suffix:
						if content.endswith(sfx):
							strVal = strVal.removesuffix(sfx)
							break
					value = numberInfo.pyType(bytesToStr(strVal))
				except ValueError:
					self._error(INVALID_NUMBER_MSG.format(numberInfo.numberTagCls.__name__, bytesToStr(content)), current)
					value = 0
				if not numberInfo.min <= value <= numberInfo.max:
					self._error(NUMBER_OUT_OF_BOUNDS_MSG.format(numberInfo.min, numberInfo.max), current)
				self._next()
				return numberInfo.numberTagCtor(current.span, None, value, content)
		self._error(EXPECTED_BUT_GOT_MSG_RAW.format(numberInfo.name, wrapInMDCode(bytesToStr(content))), current)
		return None

	def parseByteTag(self) -> Optional[ByteTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[ByteTag])

	def parseShortTag(self) -> Optional[ShortTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[ShortTag])

	def parseIntTag(self) -> Optional[IntTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[IntTag])

	def parseLongTag(self) -> Optional[LongTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[LongTag])

	def parseFloatTag(self) -> Optional[FloatTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[FloatTag])

	def parseDoubleTag(self) -> Optional[DoubleTag]:
		return self._parseNumberTagInternal(NUMBER_INFO[DoubleTag])

	def unescapeQuotedString(self, string: bytes, span: Span, innerSlice: slice) -> tuple[str, bytes, IndexMapper]:
		hasEscapeSequence = b'\\' in string
		quote: int = string[0]
		quotesLen = 1

		if hasEscapeSequence:
			idxMapBldr = self._makeIndexMapBuilderForStr(innerSlice.start)

			escapableChars = b'\\' + strToBytes(chr(quote))

			chars: bytes = b''  # list[str] = []
			index = quotesLen  # decoded index
			strStreakStart = index
			end = len(string) - quotesLen
			while index < end:
				char = string[index]

				if char != ORD_BACKSLASH:
					# chars.append(char)
					index += 1
					continue

				chars += (string[strStreakStart:index])
				decIdx = len(chars)
				next_char = string[index + 1]
				if next_char in escapableChars:
					next_char_str = bytes((next_char,))  # make bytes from ordinal
					chars += next_char_str
					idxMapBldr.addMarker(index - 1,     decIdx)  # just before (=start of) escape sequence
					idxMapBldr.addMarker(index - 1 + 2, decIdx + 1)  # just after (=end of) escape sequence
				else:
					self.error(MDStr(f"Unknown escape sequence: `{bytesToStr(string)}`"), span=span)
					chars += string[index:index+2]

				index += 2
				strStreakStart = index

			chars += (string[strStreakStart:index])
			decPosLastChar = len(chars)  # = index
			encPosLastChar = len(string) - 2  # we have to account for the quotation marks at start and end of string
			idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
			rawData = chars
			value = bytesToStr(chars)
		else:
			if string:
				rawData = string[quotesLen:].removesuffix(bytes((quote,)))  # todo probably to be removed. INVESTIGATE (see also JsonParser.parse_string())
				value = bytesToStr(rawData)
			else:
				rawData = b''
				value = ''

			if not self._idxMprIsIdentity:
				idxMapBldr = self._makeIndexMapBuilderForStr(innerSlice.start)
				decPosLastChar = len(string)
				encPosLastChar = decPosLastChar
				idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
			else:
				idxMap = IndexMapper.IDENTITY_MAPPER

		return value, rawData, idxMap

	def parseStringTag(self, acceptNumber: bool = False) -> Optional[StringTag]:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format('a String', 'nothing'), self._last)
			return None  # oh, no!

		content: bytes = self._getContent(current)
		if current.type == TokenType.QuotedString:
			if self.indexMapper.isIdentity:
				innerStart = current.span.start.index + 1
				innerEnd = current.span.end.index - 1
				innerSlice = slice(innerStart, innerEnd)
			else:
				innerStart = self.getActualEncCursor(self.getDecCursor(current.span.start.index) + 1)
				innerEnd = self.getActualEncCursor(self.getDecCursor(current.span.end.index) - 1)
				innerSlice = slice(innerStart, innerEnd)

			data, rawData, idxMap = self.unescapeQuotedString(content, current.span, innerSlice)

		elif (current.type == TokenType.String) or (acceptNumber and current.type == TokenType.Number):
			data: str = bytesToStr(content)  # we're good
			rawData: bytes = content
			idxMap = self.indexMapper
			innerSlice = current.span.slice
		else:
			self._error(EXPECTED_BUT_GOT_MSG.format('a String', wrapInMDCode(bytesToStr(content))), current)
			return None  # oh, no!

		self._next()

		return StringTag(current.span, None, data, content, rawData, innerSlice, idxMap)

	def _makeIndexMapBuilderForStr(self, contentStartIdx: int) -> IndexMapBuilder:
		return IndexMapBuilder(self.indexMapper, self.indexMapper.toDecoded(contentStartIdx))

	def _parseListLike(self, delimiter: TokenType, closing: TokenType, parseItem: Callable[[], bool]) -> bool:
		if self._current is not None and self._current.type is closing:
			self._consumeToken(closing)
			return True
		while True:
			if not parseItem():
				return False
			if not self._consumeAnyOfToken({delimiter, closing}):
				return False  # assume closing token
			if self._last.type is closing:
				return True
			elif self._current is not None and self._current.type is closing:
				self._next()
				return True

	def parseListTag(self) -> Optional[ListTag]:
		if not self._consumeToken(TokenType.List):
			return None
		openingToken = self._last
		values = list[StructureDataNode[NBTNode, StructureValue[NBTNode]]]()
		tagType: Optional[Type[NBTNode]] = None

		def parseItem() -> bool:
			nonlocal tagType
			tag = self.parseNBTTag()
			if tag is None:
				return False

			if tagType is None:
				tagType = type(tag)
			if type(tag) != tagType:
				self.errorMsg(EXPECTED_BUT_GOT_MSG_RAW, tagType.__name__, type(tag).__name__, span=tag.span)
			values.append(tag)
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseList, parseItem)
		span = Span(openingToken.span.start, self._last.span.end)
		return ListTag(span, None, values)

	def parsePropertyTag(self) -> Optional[NBTProperty]:
		keyTag = self.parseStringTag(acceptNumber=True)
		if keyTag is None:
			return None
		keyTag.schema = KeySchema()
		if not self._consumeToken(TokenType.Colon):
			valueTag = InvalidTag(Span(keyTag.span.end), None, '')
		else:
			valueTag = self.parseNBTTag()
			if valueTag is None:
				current = self._current
				if current is None:
					valueTag = InvalidTag(Span(keyTag.span.end), None, '')
				else:
					if current.type in {TokenType.Comma, TokenType.CloseCompound}:
						valueTag = InvalidTag(Span.between(self._last.span, current.span), None, '')
					else:
						valueTag = InvalidTag(Span(keyTag.span.end), None, '')
						# todo? tag = InvalidTag(current.span, None, self._getContent(current))
					# return False
		return NBTProperty(Span.encompassing(keyTag.span, valueTag.span), None, keyTag, valueTag)

	def parseCompoundTag(self) -> Optional[CompoundTag]:
		if not self._consumeToken(TokenType.Compound):
			return None
		openingToken = self._last
		values = OrderedMultiDict[str, NBTProperty]()

		def parseProperty() -> bool:
			tag = self.parsePropertyTag()
			if tag is None:
				return False
			values[tag.key.data] = tag
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseCompound, parseProperty)
		span = Span(openingToken.span.start, self._last.span.end)
		return CompoundTag(span, None, values)

	# def _parseArrayTag(self, cls: Type[ArrayTag], opening: TokenType, parseTag: Callable[[], Optional[NBTTag]]) -> Optional[ArrayTag]:
	def _parseArrayTag[T: NBTNode](self, cls: Callable[[Span, Optional[StructureDataSchema], list[T]], ArrayTag[T]], opening: TokenType, parseTag: Callable[[], Optional[T]]) -> Optional[ArrayTag[T]]:
		if not self._consumeToken(opening):
			return None
		openingToken = self._last
		values: list[T] = []
		
		def parseItem() -> bool:
			tag = parseTag()
			if tag is None:
				return False
			values.append(tag)
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseList, parseItem)
		span = Span(openingToken.span.start, self._last.span.end)
		return cls(span, None, values)

	def parseByteArrayTag(self) -> Optional[ByteArrayTag]:
		return self._parseArrayTag(ByteArrayTag, TokenType.ByteArray, self.parseByteTag)

	def parseIntArrayTag(self) -> Optional[IntArrayTag]:
		return self._parseArrayTag(IntArrayTag, TokenType.IntArray, self.parseIntTag)

	def parseLongArrayTag(self) -> Optional[LongArrayTag]:
		return self._parseArrayTag(LongArrayTag, TokenType.LongArray, self.parseLongTag)

	_PARSER_BY_TYPE: ClassVar[dict[TokenType, Callable[[SNBTParser], Optional[NBTTag]]]] = {
		TokenType.QuotedString: parseStringTag,
		TokenType.Number: _parseNumberTag,
		TokenType.String: _parseStringOrBoolTag,
		TokenType.Compound: parseCompoundTag,
		TokenType.ByteArray: parseByteArrayTag,
		TokenType.IntArray: parseIntArrayTag,
		TokenType.LongArray: parseLongArrayTag,
		TokenType.List: parseListTag,
	}

	def parse(self) -> Optional[NBTNode]:
		tag = self.parseNBTTag()
		if tag is not None:
			pathify(tag, '')
			enrichWithSchema(tag, self.schema)
		self.cursor = self._tokenizer.lastCursor
		self.line = self._tokenizer.lastLine
		self.lineStart = self._tokenizer.lastLineStart
		return tag


def init():
	pass
