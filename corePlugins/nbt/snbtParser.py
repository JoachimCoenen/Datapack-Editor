from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type, Union, Callable, NamedTuple, overload, TypeVar, ClassVar

from cat.utils.collections_ import OrderedDict
from base.model.messages import *
from .snbtTokenizer import SNBTTokenizer, Token, TokenType
from .tags import *
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import ParserBase
from base.model.utils import Message, Position, Span, MDStr, wrapInMDCode

INVALID_NUMBER_MSG: Message = Message("Invalid {0}: '`{1}`'", 2)


class NumberInfo(NamedTuple):
	suffix: tuple[bytes, ...]
	min: Union[int, float]
	max: Union[int, float]
	name: str
	pyType: Type


NUMBER_INFO = {
	ByteTag: NumberInfo((b'b', b'B'), -128, 127, 'a Byte', int),
	ShortTag: NumberInfo((b's', b'S'), -32768,  32767, 'a Short', int),
	IntTag: NumberInfo((b'',), -2147483648, 2147483647, 'a Int', int),
	LongTag: NumberInfo((b'l', b'L'), -9223372036854775808, 9223372036854775807, 'a Long', int),
	FloatTag: NumberInfo((b'f', b'F', b''), -3.4E+38, +3.4E+38, 'a Float', float),
	DoubleTag: NumberInfo((b'd', b'D'), -1.7E+308, 1.7E+308, 'a Double', float),
}

NUMBER_TAG_BY_SUFFIX = {suffix: tagType for tagType, info in NUMBER_INFO.items() for suffix in info[0] if suffix}


_ESCAPE_CHAR_MAP = {
	ord('"'): '"',
	ord("'"): "'",
	ord('/'): '/',
	ord('\\'): '\\',
	ord('b'): '\b',
	ord('f'): '\f',
	ord('n'): '\n',
	ord('r'): '\r',
	ord('t'): '\t',
}


_TNumber = TypeVar('_TNumber', int, float)
_TNBTTag = TypeVar('_TNBTTag', bound=BasicDataTag)

@dataclass
class SNBTParser(ParserBase[NBTTag, NBTTagSchema]):
	ignoreTrailingChars: bool = False
	_tokenizer: SNBTTokenizer = field(init=False)
	_current: Optional[Token] = field(init=False)
	_last: Optional[Token] = field(init=False, default=None)

	def __post_init__(self):
		self._tokenizer = SNBTTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
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

	def parseNBTTag(self) -> Optional[NBTTag]:
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
	
	def _parseStringOrBoolTag(self) -> Optional[NBTTag]:
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
			return StringTag(current.span, None, bytesToStr(content), content)
		
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
		tagType = NUMBER_TAG_BY_SUFFIX.get(suffix)
		if tagType is not None:
			return self._parseNumberTagInternal(tagType, *NUMBER_INFO[tagType])
		if any(c in content for c in b'.eE'):
			return self._parseNumberTagInternal(FloatTag, *NUMBER_INFO[FloatTag])
		else:
			return self._parseNumberTagInternal(IntTag, *NUMBER_INFO[IntTag])

	@overload
	def _parseNumberTagInternal(self, cls: Callable[[Span, Optional[NBTTagSchema], int, bytes], NumberTag[int]], suffix: tuple[bytes, ...], minVal: int, maxVal: int, name: str, number: Type[int]) -> Optional[NumberTag[int]]: ...
	@overload
	def _parseNumberTagInternal(self, cls: Callable[[Span, Optional[NBTTagSchema], float, bytes], NumberTag[float]], suffix: tuple[bytes, ...], minVal: float, maxVal: float, name: str, number: Type[float]) -> Optional[NumberTag[float]]: ...

	def _parseNumberTagInternal(self, cls: Callable[[Span, Optional[NBTTagSchema], _TNumber, bytes], NumberTag[_TNumber]], suffix: tuple[bytes, ...], minVal: _TNumber, maxVal: _TNumber, name: str, number: Type[_TNumber]) -> Optional[NumberTag[_TNumber]]:
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
					value = number(bytesToStr(strVal))
				except ValueError:
					self._error(INVALID_NUMBER_MSG.format(cls.__name__, bytesToStr(content)), current)
					value = 0
				if not minVal <= value <= maxVal:
					self._error(NUMBER_OUT_OF_BOUNDS_MSG.format(minVal, maxVal), current)
				self._next()
				return cls(current.span, None, value, content)
		self._error(EXPECTED_BUT_GOT_MSG_RAW.format(name, wrapInMDCode(bytesToStr(content))), current)
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

	def unescapeString(self, string: bytes, span: Span) -> str:
		if b'\\' in string:
			chars: list[str] = []
			index = 0
			strStreakStart = index
			end = len(string)
			while index < end:
				char = string[index]

				if char != '\\':
					# chars.append(char)
					index += 1
					continue

				chars.append(bytesToStr(string[strStreakStart:index]))
				next_char = string[index + 1]

				next_char_str = _ESCAPE_CHAR_MAP.get(next_char)
				if next_char_str is not None:
					chars.append(next_char_str)
				else:
					self.error(MDStr(f"Unknown escape sequence: `{bytesToStr(string)}`"), span=span)

				index += 2
				strStreakStart = index

			value = ''.join(chars)
		elif string:
			value = bytesToStr(string)
		else:
			value = ''
		return value

	def parseStringTag(self, acceptNumber: bool = False) -> Optional[StringTag]:
		current = self._current
		if current is None:
			self._error(EXPECTED_BUT_GOT_MSG_RAW.format('a String', 'nothing'), self._last)
			return None  # oh no!

		content: bytes = self._getContent(current)
		if current.type == TokenType.QuotedString:
			data: str = self.unescapeString(content, current.span)
		elif (current.type == TokenType.String) or (acceptNumber and current.type == TokenType.Number):
			data: str = bytesToStr(content)  # we're good
		else:
			self._error(EXPECTED_BUT_GOT_MSG.format('a String', wrapInMDCode(bytesToStr(content))), current)
			return None  # oh no!

		self._next()
		return StringTag(current.span, None, data, content)

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
		if not self._consumeToken(TokenType.Colon):
			valueTag = InvalidTag(Span(keyTag.span.end), None, b'')
		else:
			valueTag = self.parseNBTTag()
			if valueTag is None:
				current = self._current
				if current is None:
					valueTag = InvalidTag(Span(keyTag.span.end), None, b'')
				else:
					if current.type in {TokenType.Comma, TokenType.CloseCompound}:
						valueTag = InvalidTag(Span.between(self._last.span, current.span), None, b'')
					else:
						valueTag = InvalidTag(Span(keyTag.span.end), None, b'')
						# todo? tag = InvalidTag(current.span, None, self._getContent(current))
					# return False
		return NBTProperty(Span.encompassing(keyTag.span, valueTag.span), None, (keyTag, valueTag))

	def parseCompoundTag(self) -> Optional[CompoundTag]:
		if not self._consumeToken(TokenType.Compound):
			return None
		openingToken = self._last
		values = OrderedDict[str, NBTTag]()

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
	def _parseArrayTag(self, cls: Callable[[Span, Optional[NBTTagSchema], list[_TNBTTag]], ArrayTag[_TNBTTag]], opening: TokenType, parseTag: Callable[[], Optional[NBTTag]]) -> Optional[ArrayTag[_TNBTTag]]:
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

	def parse(self) -> Optional[NBTTag]:
		tag = self.parseNBTTag()
		self.cursor = self._tokenizer.lastCursor
		self.line = self._tokenizer.lastLine
		self.lineStart = self._tokenizer.lastLineStart
		return tag


def init():
	pass
