from typing import Optional, Type, Union, Callable

from Cat.Serializable import RegisterContainer
from Cat.utils.collections import OrderedDict
from model.nbt.snbtTokenizer import SNBTTokenizer, Token, TokenType
from model.nbt.tags import *
from model.parsingUtils import Position, GeneralParsingError, Span
from model.utils import Message


EXPECTED_BUT_GOT_MSG: Message = Message("Expected {}, but got: `{}`", 2)
VALUE_OUT_OF_RANGE_MSG: Message = Message("Value is out of range (min={}, max={})", 2)
INVALID_NUMBER_MSG: Message = Message("Invalid {}: '`{}`'", 2)


@RegisterContainer
class SNBTError(GeneralParsingError):
	__slots__ = ()
	pass


NUMBER_INFO = {
	ByteTag: (('b', 'B'), -128, 127, 'a Byte', int),
	ShortTag: (('s', 'S'), -32768,  32767, 'a Short', int),
	IntTag: (('',), -2147483648, 2147483647, 'a Int', int),
	LongTag: (('l', 'L'), -9223372036854775808, 9223372036854775807, 'a Long', int),
	FloatTag: (('f', 'F', ''), -3.4E+38, +3.4E+38, 'a Float', float),
	DoubleTag: (('d', 'D'), -1.7E+308, 1.7E+308, 'a Double', float),
}

NUMBER_TAG_BY_SUFFIX = {suffix: tagType for tagType, info in NUMBER_INFO.items() for suffix in info[0] if suffix}


class SNBTParser:
	def __init__(self, source: str, ignoreTrailingChars: bool = False):
		self._source: str = source
		self._ignoreTrailingChars: bool = ignoreTrailingChars

		self._tokenizer = SNBTTokenizer(source, ignoreTrailingChars)
		self._current: Optional[Token] = self._tokenizer.nextToken()
		self._last: Optional[Token] = None

		self._errors: list[SNBTError] = []

	@property
	def errors(self) -> list[SNBTError]:
		return self._errors

	def _error(self, message: str, token: Token, style: str = 'error') -> None:
		if token is not None:
			self._error2(message, token.span, style)
		else:
			self._error2(message, Span(Position(0, 0, 0)), style)

	def _error2(self, message: str, span: Span, style: str = 'error') -> None:
		self._errors.append(SNBTError(message, span, style=style))

	def _next(self) -> None:
		self._last = self._current
		self._current = self._tokenizer.nextToken()

	def _getContent(self, token: Token) -> str:
		return self._source[token.span.slice]

	def _consumeToken(self, kind: TokenType) -> bool:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG.format(f"`{kind.name}`", 'end of str'), self._last)
			return False
		if current.type != kind:
			content = self._getContent(current)
			self._error(EXPECTED_BUT_GOT_MSG.format(f"`{kind.name}`", content), current)
			return False
		self._next()
		return True

	def _consumeAnyOfToken(self, kinds: set[TokenType]) -> bool:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG.format(f"any of ({', '.join(f'`{k.name}`' for k in kinds)})", 'end of str'), self._last)
			return False
		if current.type not in kinds:
			content = self._getContent(current)
			self._error(EXPECTED_BUT_GOT_MSG.format(f"any of ({', '.join(f'`{k.name}`' for k in kinds)})", content), current)
			return False
		self._next()
		return True

	def parseNBTTag(self) -> Optional[NBTTag]:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG.format("a NBTTag", 'end of str'), self._last)
			return None
		parserByType: dict[TokenType, Callable[[SNBTParser], Optional[NBTTag]]] = {
			TokenType.QuotedString: SNBTParser.parseStringTag,
			TokenType.Number: SNBTParser._parseNumberTag,
			TokenType.String: SNBTParser._parseStringOrBoolTag,
			TokenType.Compound: SNBTParser.parseCompoundTag,
			TokenType.ByteArray: SNBTParser.parseByteArrayTag,
			TokenType.IntArray: SNBTParser.parseIntArrayTag,
			TokenType.LongArray: SNBTParser.parseLongArrayTag,
			TokenType.List: SNBTParser.parseListTag,
		}

		parser = parserByType.get(current.type)
		if parser is not None:
			tag = parser(self)
			return tag
		else:
			self._error(EXPECTED_BUT_GOT_MSG.format("a NBTTag", self._current.type.name), current)
			return None
	
	def _parseStringOrBoolTag(self) -> Optional[NBTTag]:
		current = self._current
		content = self._getContent(current)
		if content in {'true'}:
			self._next()
			return BooleanTag(True, current.span)
		elif content in {'false'}:
			self._next()
			return BooleanTag(False, current.span)
		else:
			self._next()
			return StringTag(content, current.span)
		
	def parseBooleanTag(self) -> Optional[BooleanTag]:
		current = self._current
		content = self._getContent(current)
		if content in {'true', '1b'}:
			self._next()
			return BooleanTag(True, current.span)
		elif content in {'false', '0b'}:
			self._next()
			return BooleanTag(False, current.span)
		else:
			self._error(EXPECTED_BUT_GOT_MSG.format('a boolean', content), current)

	def _parseNumberTag(self) -> Optional[NumberTag]:
		# TODO: all numbers are interoperable (even int / float, ...)
		# TODO: floats & doubles don't need a suffix.
		current = self._current
		content = self._getContent(current)
		if not content:
			return None

		suffix = content[-1]
		tagType = NUMBER_TAG_BY_SUFFIX.get(suffix)
		if tagType is not None:
			return self._parseNumberTagInternal(tagType, *NUMBER_INFO[tagType])
		if any(c in content for c in '.eE'):
			return self._parseNumberTagInternal(FloatTag, *NUMBER_INFO[FloatTag])
		else:
			return self._parseNumberTagInternal(IntTag, *NUMBER_INFO[IntTag])

	def _parseNumberTagInternal(self, cls: Type[NumberTag], suffix: tuple[str, ...], minVal, maxVal, name: str, int=Union[Type[int], Type[float]]) -> Optional[NumberTag]:
		current = self._current
		content = self._getContent(current)
		if current.type == TokenType.Number:
			if content.endswith(suffix):
				try:
					strVal = content
					for sfx in suffix:
						if content.endswith(sfx):
							strVal = strVal.removesuffix(sfx)
							break
					value = int(strVal)
				except ValueError:
					self._error(INVALID_NUMBER_MSG.format(cls.__name__, content), current)
					value = 0
				if not minVal <= value <= maxVal:
					self._error(VALUE_OUT_OF_RANGE_MSG.format(minVal, maxVal), current)
				self._next()
				return cls(value, current.span)
		self._error(EXPECTED_BUT_GOT_MSG.format(name, content), current)
		return None

	def parseByteTag(self) -> Optional[ByteTag]:
		return self._parseNumberTagInternal(ByteTag, *NUMBER_INFO[ByteTag])

	def parseShortTag(self) -> Optional[ShortTag]:
		return self._parseNumberTagInternal(ShortTag, *NUMBER_INFO[ShortTag])

	def parseIntTag(self) -> Optional[IntTag]:
		return self._parseNumberTagInternal(IntTag, *NUMBER_INFO[IntTag])

	def parseLongTag(self) -> Optional[LongTag]:
		return self._parseNumberTagInternal(LongTag, *NUMBER_INFO[LongTag])

	def parseFloatTag(self) -> Optional[FloatTag]:
		return self._parseNumberTagInternal(FloatTag, *NUMBER_INFO[FloatTag])

	def parseDoubleTag(self) -> Optional[DoubleTag]:
		return self._parseNumberTagInternal(DoubleTag, *NUMBER_INFO[DoubleTag])

	def parseStringTag(self) -> Optional[StringTag]:
		current = self._current
		content = self._getContent(current)
		if current.type == TokenType.String:
			self._next()
			return StringTag(content, current.span)
		elif current.type == TokenType.QuotedString:
			# TODO: unescape QuotedString:
			self._next()
			return StringTag(content, current.span)
		else:
			self._error(EXPECTED_BUT_GOT_MSG.format('a String', content), current)
			return None

	def _parseListLike(self, delimiter: TokenType, closing: TokenType, parseItem: Callable[[], bool]) -> bool:
		if self._current is not None and self._current.type is closing:
			self._consumeToken(closing)
			return True
		while True:
			if not parseItem():
				return False
			if not self._consumeAnyOfToken({delimiter, closing}):
				return False
			if self._last.type == closing:
				return True

	def parseListTag(self) -> Optional[ListTag]:
		if not self._consumeToken(TokenType.List):
			return None
		openingToken = self._last
		values = list[NBTTag]()
		tagType: Optional[Type[NBTTag]] = None

		def parseItem() -> bool:
			nonlocal tagType
			tag = self.parseNBTTag()
			if tag is None:
				return False

			if tagType is None:
				tagType = type(tag)
			if type(tag) != tagType:
				self._error2(EXPECTED_BUT_GOT_MSG.format(f'`{tagType.__name__}`', type(tag).__name__), tag.span)
			values.append(tag)
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseList, parseItem)
		return ListTag(values, Span(openingToken.span.start, self._last.span.end))

	def parseCompoundTag(self) -> Optional[CompoundTag]:
		if not self._consumeToken(TokenType.Compound):
			return None
		openingToken = self._last
		values = OrderedDict[str, NBTTag]()

		def parseItem() -> bool:
			if not self._consumeAnyOfToken({TokenType.Number, TokenType.String, TokenType.QuotedString}):
				return False
			key = self._getContent(self._last)
			if not self._consumeToken(TokenType.Colon):
				return False
			tag = self.parseNBTTag()
			if tag is None:
				return False
			values[key] = tag
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseCompound, parseItem)
		return CompoundTag(values, Span(openingToken.span.start, self._last.span.end))

	def _parseArrayTag(self, cls: Type[ArrayTag], opening: TokenType, parseTag: Callable[[], Optional[NBTTag]]) -> Optional[ArrayTag]:
		if not self._consumeToken(opening):
			return None
		openingToken = self._last
		values = list[NBTTag]()
		
		def parseItem() -> bool:
			tag = parseTag()
			if tag is None:
				return False
			values.append(tag)
			return True

		self._parseListLike(TokenType.Comma, TokenType.CloseList, parseItem)
		return cls(values, Span(openingToken.span.start, self._last.span.end))

	def parseByteArrayTag(self) -> Optional[ByteArrayTag]:
		return self._parseArrayTag(ByteArrayTag, TokenType.ByteArray, self.parseByteTag)

	def parseIntArrayTag(self) -> Optional[IntArrayTag]:
		return self._parseArrayTag(IntArrayTag, TokenType.IntArray, self.parseIntTag)

	def parseLongArrayTag(self) -> Optional[LongArrayTag]:
		return self._parseArrayTag(LongArrayTag, TokenType.LongArray, self.parseLongTag)
