from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, AbstractSet, Callable, cast, Type

from base.model.parsing.bytesConstants import ORD_a, ORD_z, ORD_A_CAP, ORD_Z_CAP
from cat.utils import CachedProperty
from cat.utils.collections_ import OrderedMultiDict
from cat.utils.profiling import ProfiledFunction
from .tags import NBTNode, InvalidTag, BooleanTag, NumberTag, ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, \
	StringTag, ListTag, NBTProperty, CompoundTag, ArrayTag, ByteArrayTag, IntArrayTag, LongArrayTag
from .snbtTokenizer import SNBTTokenizer, Token, TokenType
from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr, ORD_BACKSLASH, ORD_DOUBLE_QUOTE, ORD_SINGLE_QUOTE
from base.model.parsing.parser import ParserBase, IndexMapBuilder, IndexMapper
from base.model.utils import Span, MDStr, Message, NULL_SPAN, Position, wrapInMDCode
from corePlugins.nbtJsonBase.core import KeySchema, StructureDataNode, StructureDataSchema, StructureProperty
from corePlugins.nbtJsonBase.schema import pathify, enrichWithSchema

ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG = Message("JSON standard allows only double quoted string as property key", 0)
MISSING_VALUE_MSG = Message("Missing value for property", 0)
INVALID_NUMBER_MSG: Message = Message("Invalid {0}: '`{1}`'", 2)

_ESCAPE_CHAR_MAP = {
	ord('"'): b'"',
	ord("'"): b"'",
	ord('/'): b'/',
	ord('\\'): b'\\',
	ord('b'): b'\b',
	ord('f'): b'\f',
	ord('n'): b'\n',
	ord('r'): b'\r',
	ord('t'): b'\t',
}


type NumberTagCtor[T: int | float] = Callable[[Span, StructureDataSchema | None, T, bytes], NumberTag[T]]


@dataclass
class NumberInfo[T: int | float]:
	suffix: tuple[bytes, ...]
	min: T
	max: T
	name: str
	pyType: Callable[[str], T]
	numberTagCls: Type[NumberTag[T]]
	numberTagCtor: NumberTagCtor[T]


NUMBER_INFO: dict[Type[NumberTag], NumberInfo] = {
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

	_waitingForClosing: dict[TokenType, int] = field(default_factory=lambda: defaultdict(int), init=False)
	_tokenizer: SNBTTokenizer = field(init=False)
	_current: Token = field(init=False)
	_eofToken: Token = field(init=False)
	_last: Token = field(init=False)

	def __post_init__(self) -> None:
		super().__post_init__()
		self._tokenizer = SNBTTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
			self.fullSource,
			self.ignoreTrailingChars
		)
		self.errors = self._tokenizer.errors  # sync errors
		self._current = cast(Any, None)
		self._next()  # sets self._current, self._last

	def tokenize(self) -> tuple[list[Token], Token]:
		tokens = []
		while (tkn := self._tokenizer.nextToken()).type is not TokenType.eof:
			tokens.append(tkn)
		eofToken = tkn
		return tokens, eofToken

	def _getContent(self, token: Token) -> bytes:
		return self.text[token.startEnd[0]:token.startEnd[1]]
		# return self.text[token.span.slice]

	@property
	def hasTokens(self) -> bool:
		return self._current.type is not TokenType.eof

	def _next(self) -> None:
		self._last = self._current
		self._current = self._tokenizer.nextToken()

	def tryAccept(self, tokenType: TokenType) -> Token | None:
		if self._current.type is not tokenType:
			return None
		self._next()
		return self._last  # current == self._last

	def tryAcceptAnyOf(self, tokenTypes: AbstractSet[TokenType]) -> Token | None:
		if self._current.type not in tokenTypes:
			return None
		self._next()
		return self._last  # current == self._last

	def _checkEof(self) -> bool:
		if self._current.type is TokenType.eof:
			span = self._last.span if self._last is not None else NULL_SPAN
			self.errorMsg(UNEXPECTED_EOF_MSG, span=span)
			return True
		return False

	def accept(self, tokenType: TokenType, advanceIfBad: bool = True) -> Token:
		current = self._current
		if self._checkEof():
			return current

		if current.type is not tokenType:
			self.errorMsg(EXPECTED_BUT_GOT_MSG, tokenType.asString, bytesToStr(self._getContent(current)), span=current.span)
			if advanceIfBad:
				self._next()
		else:
			self._next()
		return current  # current == (self._last if _next() was called, else self._current)

	def acceptAnyOf(self, tokenTypes: AbstractSet[TokenType], advanceIfBad: bool = True) -> Token:
		current = self._current
		if self._checkEof():
			return current

		if current.type not in tokenTypes:
			name = ' | '.join(tk.asString for tk in tokenTypes)
			self.errorMsg(EXPECTED_BUT_GOT_MSG, name, bytesToStr(self._getContent(current)), span=current.span)
			if advanceIfBad:
				self._next()
		else:
			self._next()
		return current  # current == (self._last if _next() was called, else self._current)

	def parse_object2(self) -> CompoundTag:
		"""Parses an object out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.Invalid, TokenType.Colon}
		goodValueTokens = {TokenType.String}
		objData: OrderedMultiDict[str, StructureProperty] = OrderedMultiDict()

		def parse_property() -> None:
			nonlocal objData
			colonAlreadySeen = False
			token = self._last
			# parse KEY:
			if token.type == TokenType.String:
				key: StringTag = self.parse_string_tag()
			elif token.type in self._PARSERS.keys():
				key = self._internalParseTokens()  # type: ignore
				if key.typeName != StringTag.typeName:
					self.errorMsg(ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG, span=key.span)
					key = InvalidTag(key.span, None, bytesToStr(self.text[key.span.slice]))  # type: ignore
			elif token.type == TokenType.Invalid:
				key = self.parse_invalid()  # type: ignore
			elif token.type == TokenType.Colon:
				key = InvalidTag(Span(token.span.start), None, '')  # type: ignore
				colonAlreadySeen = True
			else:
				assert False, f"invalid state: invalid TokenType {token.type} for property"
			key.schema = KeySchema()

			if not colonAlreadySeen:
				token = self.accept(TokenType.Colon, advanceIfBad=False)

			if token.type is not TokenType.Colon:
				value: StructureDataNode = InvalidTag(Span(self._last.span.end, token.span.end), None, '')
				objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
				return

			# duplicate colons:
			while (tkn2 := self.tryAccept(TokenType.Colon)) is not None:
				self.errorMsg(DUPLICATE_NOT_ALLOWED_MSG, TokenType.Colon.asString, span=tkn2.span)

			if token.type is TokenType.eof:
				value = InvalidTag(Span(self._last.span.end, token.span.end), None, '')
				objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			elif self._waitingForClosing[self._current.type] > 0:
				self.errorMsg(MISSING_VALUE_MSG, span=self._last.span)
				value = InvalidTag(Span(self._last.span.end, self._current.span.start), None, '')
				objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			elif self.tryAcceptAnyOf(self._PARSERS.keys()) is not None:
				value = self._internalParseTokens()
				objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
				return
			else:
				# force error, but don't consume:
				self.acceptAnyOf(self._PARSERS.keys(), advanceIfBad=False)
				if self.tryAccept(TokenType.Invalid) is not None:
					value = self.parse_invalid()
					objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
					return
				elif (token2 := self.tryAccept(TokenType.eof)) is not None:
					value = InvalidTag(Span(self._last.span.end, token2.span.end), None, '')
					objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
					return
				else:
					value = InvalidTag(Span(self._last.span.end, self._current.span.start), None, '')
					objData.add(key.data, NBTProperty(Span(key.span.start, value.span.end), None, key, value))
					return

		start = self._last.span.start
		end = self._parse_list_like(TokenType.Comma, TokenType.CloseCompound, valueTokens, goodValueTokens, parse_property)
		return CompoundTag(Span(start, end), None, objData)

	def _parse_list_like(self, delimiter: TokenType, closing: TokenType, valueTokens: AbstractSet[TokenType], goodValueTokens: AbstractSet[TokenType], parseItem: Callable[[], None]) -> Position:
		"""
		:return: the end position of the list like.
		"""
		delimiterOrClosing = {delimiter, closing}

		def tryParseItem(goodTokens: AbstractSet[TokenType]) -> None:
			if self.tryAcceptAnyOf(valueTokens) is not None:
				parseItem()
			else:  # force error but don't consume:
				self.acceptAnyOf(goodTokens, advanceIfBad=False)

		if self.tryAccept(closing) is not None:
			return self._last.span.end
		self._waitingForClosing[closing] += 1
		tryParseItem(goodValueTokens | {closing})

		while True:
			# delimiter or closing:
			if (tkn := self.tryAcceptAnyOf(delimiterOrClosing)) is not None:
				if tkn.type is closing:
					self._waitingForClosing[closing] -= 1
					return self._last.span.end
				else:  # now: tkn.type is delimiter:
					while (tkn2 := self.tryAccept(delimiter)) is not None:
						self.errorMsg(DUPLICATE_NOT_ALLOWED_MSG, delimiter.asString, span=tkn2.span)
					if self.tryAccept(closing) is not None:
						# SNBT allows trailing commas. self.errorMsg(TRAILING_NOT_ALLOWED_MSG, delimiter.asString, span=tkn.span)
						self._waitingForClosing[closing] -= 1
						return self._last.span.end
					tryParseItem(goodValueTokens)
					continue
			else:
				if self._current.type in valueTokens:
					self.errorMsg(MISSING_DELIMITER_MSG, delimiter.asString, span=self._current.span)
					tryParseItem(goodValueTokens)
					continue
				elif self._waitingForClosing[self._current.type] > 0:
					self.errorMsg(MISSING_CLOSING_MSG, closing.asString, span=self._current.span)
					return self._current.span.end
				else:
					# force an error and consume the unknown token, so we don't end up
					# in an infinite loop of trying to parse that token:
					tkn = self.acceptAnyOf(delimiterOrClosing)
					if tkn.type is TokenType.eof:
						return self._current.span.end
					# tryParseItem(goodValueTokens)
					continue

	def parse_list_tag(self) -> ListTag:
		"""Parses an array out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.Invalid}
		goodValueTokens = {*self._PARSERS.keys()}
		arrayData: list[StructureDataNode] = []

		def parse_element() -> None:
			nonlocal arrayData
			value = self._internalParseTokens()
			arrayData.append(value)

		start = self._last.span.start
		end = self._parse_list_like(TokenType.Comma, TokenType.CloseList, valueTokens, goodValueTokens, parse_element)
		return ListTag(Span(start, end), None, arrayData)

	def _parse_array_tag[T: NBTNode, A: ArrayTag](
			self,
			cls: Callable[[Span, StructureDataSchema | None, list[T]], A],
			parseTag: Callable[[], T]
	) -> A:
		valueTokens = {TokenType.Number, TokenType.Invalid}
		goodValueTokens = {TokenType.Number}
		arrayData: list[T] = []

		def parse_element() -> None:
			nonlocal arrayData
			tag = parseTag()
			arrayData.append(tag)

		start = self._last.span.start
		end = self._parse_list_like(TokenType.Comma, TokenType.CloseList, valueTokens, goodValueTokens, parse_element)
		return cls(Span(start, end), None, arrayData)

	def parse_byte_array_tag(self) -> ByteArrayTag:
		return self._parse_array_tag(ByteArrayTag, self.parse_byte_tag)

	def parse_int_array_tag(self) -> IntArrayTag:
		return self._parse_array_tag(IntArrayTag, self.parse_int_tag)

	def parse_long_array_tag(self) -> LongArrayTag:
		return self._parse_array_tag(LongArrayTag, self.parse_long_tag)

	def _parse_string_or_bool_tag(self) -> StructureDataNode:
		current = self._last
		content = self._getContent(current)
		if content == b'true':
			return BooleanTag(current.span, None, True, content)
		elif content == b'false':
			return BooleanTag(current.span, None, False, content)
		else:
			innerSlice = current.span.slice
			return StringTag(current.span, None, bytesToStr(content), content, content, innerSlice, self.indexMapper)

	def parse_string_tag(self) -> StringTag:
		"""Parses a string out of a JSON token"""
		# TODO: usage of IndexMapBuilder needs a thorough testing. It is completely untested. [23-7-2023]
		token = self._last
		string = raw = self._getContent(token)
		hasEscapeSequence = b'\\' in string

		# calculate innerSlice:
		if token.type == TokenType.QuotedString:
			if self.indexMapper.isIdentity:
				innerStart = token.span.start.index + 1
				innerEnd = token.span.end.index - 1
				innerSlice = slice(innerStart, innerEnd)
			else:
				innerStart = self.getActualEncCursor(self.getDecCursor(token.span.start.index) + 1)
				innerEnd = self.getActualEncCursor(self.getDecCursor(token.span.end.index) - 1)
				innerSlice = slice(innerStart, innerEnd)
		else:
			innerSlice = token.span.slice

		# unescapeQuotedString:
		if hasEscapeSequence:
			idxMapBldr = self.makeIndexMapBuilderForStr(innerSlice.start)

			chars: bytes = b''  # list[str] = []
			index = 1  # decoded index
			strStreakStart = index
			end = len(string) - 1
			while index < end:
				char = string[index]

				if char != ORD_BACKSLASH:
					# chars.append(char)
					index += 1
					continue

				chars += (string[strStreakStart:index])
				decIdx = len(chars)
				next_char = string[index + 1]
				next_char_str = _ESCAPE_CHAR_MAP.get(next_char)
				if next_char_str is not None:
					chars += next_char_str
					idxMapBldr.addMarker(index - 1,     decIdx)  # just before (=start of) escape sequence
					idxMapBldr.addMarker(index - 1 + 2, decIdx + 1)  # just after (=end of) escape sequence
				else:
					self.error(MDStr(f"Unknown escape sequence: `{bytesToStr(string)}`"), span=token.span)
					chars += string[index:index+2]

				index += 2
				strStreakStart = index

			chars += (string[strStreakStart:index])
			decPosLastChar = len(chars)  # = index
			encPosLastChar = len(string) - 2  # we have to account for the quotation marks at start and end of string
			idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
			string = chars
			value = bytesToStr(chars)
		else:
			if string:
				if string[0] == ORD_DOUBLE_QUOTE:
					string = string[1:].removesuffix(b'"')  # todo probably to be removed. INVESTIGATE (see also SNBTParser.unescapeQuotedString())
				elif string[0] == ORD_SINGLE_QUOTE:
					string = string[1:].removesuffix(b"'")  # todo probably to be removed. INVESTIGATE (see also SNBTParser.unescapeQuotedString())
				value = bytesToStr(string)
			else:
				value = ''

			if not self._idxMprIsIdentity:
				idxMapBldr = self.makeIndexMapBuilderForStr(innerSlice.start)
				decPosLastChar = len(string)
				encPosLastChar = decPosLastChar
				idxMap = idxMapBldr.completeIndexMapper(encPosLastChar, decPosLastChar)
			else:
				idxMap = IndexMapper.IDENTITY_MAPPER

		return StringTag(token.span, None, value, raw, string, innerSlice, idxMap)

	def makeIndexMapBuilderForStr(self, contentStartIdx: int) -> IndexMapBuilder:
		return IndexMapBuilder(self.indexMapper, self.indexMapper.toDecoded(contentStartIdx))

	def parse_number_tag(self) -> NumberTag:
		# TODO: all numbers are interoperable (even int / float, ...)
		# TODO: floats & doubles don't need a suffix.
		current = self._last
		content = self._getContent(current)

		suffix = content[-1:]
		numberInfo = NUMBER_INFO_BY_SUFFIX.get(suffix)
		if numberInfo is not None:
			return self._parse_number_tag_internal(numberInfo)
		if any(c in content for c in b'.eE'):
			return self._parse_number_tag_internal(NUMBER_INFO[FloatTag])
		else:
			return self._parse_number_tag_internal(NUMBER_INFO[IntTag])

	def _parse_number_tag_internal[T: int | float](self, numberInfo: NumberInfo[T]) -> NumberTag:
		current = self._last
		content = self._getContent(current)

		if content.endswith(numberInfo.suffix):
			try:
				strVal = content
				for sfx in numberInfo.suffix:
					if content.endswith(sfx):
						strVal = strVal.removesuffix(sfx)
						break
				value: T = numberInfo.pyType(bytesToStr(strVal))
			except ValueError:
				self.errorMsg(INVALID_NUMBER_MSG, numberInfo.numberTagCls.__name__, bytesToStr(content), span=current.span)
				value = numberInfo.pyType('0')
			if not numberInfo.min <= value <= numberInfo.max:  # type: ignore
				self.errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, str(numberInfo.min), str(numberInfo.max), span=current.span)
			return numberInfo.numberTagCtor(current.span, None, value, content)
		else:
			self.errorMsg(EXPECTED_BUT_GOT_MSG_RAW, numberInfo.name, wrapInMDCode(bytesToStr(content)), span=current.span)
			if ORD_a <= content[-1] <= ORD_z or ORD_A_CAP <= content[-1] <= ORD_Z_CAP:
				valueBad = float(bytesToStr(content[:-1]))
			else:
				valueBad = float(bytesToStr(content))
			return NumberTag(current.span, None, valueBad, content)

	def parse_byte_tag(self) -> ByteTag:
		return self._parse_number_tag_internal(NUMBER_INFO[ByteTag])  # type: ignore

	def parse_int_tag(self) -> IntTag:
		return self._parse_number_tag_internal(NUMBER_INFO[IntTag])  # type: ignore

	def parse_long_tag(self) -> LongTag:
		return self._parse_number_tag_internal(NUMBER_INFO[LongTag])  # type: ignore

	def parse_invalid(self) -> InvalidTag:
		"""Parses an invalid token out of a JSON token"""
		token = self._last
		return InvalidTag(token.span, None, bytesToStr(self._getContent(token)))

	@CachedProperty
	def _PARSERS(self) -> dict[TokenType, Callable[[], StructureDataNode]]:
		return {
			TokenType.List: self.parse_list_tag,
			TokenType.ByteArray: self.parse_byte_array_tag,
			TokenType.IntArray: self.parse_int_array_tag,
			TokenType.LongArray: self.parse_long_array_tag,
			TokenType.Compound: self.parse_object2,
			TokenType.QuotedString: self.parse_string_tag,
			TokenType.String: self._parse_string_or_bool_tag,
			TokenType.Number: self.parse_number_tag,
		}

	def _internalParseTokens(self) -> StructureDataNode:
		"""Recursive JSON parse implementation"""
		token = self._last
		parser = self._PARSERS.get(token.type)
		if parser is not None:
			value = parser()
			return value
		else:
			return InvalidTag(token.span, None, bytesToStr(self._getContent(token)))

	def parseJsonTokens(self) -> StructureDataNode | None:
		"""Recursive JSON parse implementation"""
		token = self.acceptAnyOf(self._PARSERS.keys())
		if token.type is not TokenType.eof:
			data = self._internalParseTokens()
			pathify(data, '')
			enrichWithSchema(data, self.schema)
		else:
			data = None
		return data

	@ProfiledFunction(enabled=False)
	def parse(self) -> StructureDataNode | None:
		"""Parses a JSON string into a Python object"""
		value = self.parseJsonTokens()

		if self._current is not None and self._current.type is not TokenType.eof:
			self.error(
				MDStr(f"Invalid JSON at `{bytesToStr(self._getContent(self._current))}`"),
				span=self._current.span
			)

		self.cursor = self._tokenizer.lastCursor
		self.line = self._tokenizer.lastLine
		self.lineStart = self._tokenizer.lastLineStart
		return value
