from ast import literal_eval
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, AbstractSet, Callable, cast, ClassVar

from base.model.parsing.bytesConstants import ORD_a, ORD_z, ORD_A_CAP, ORD_Z_CAP, ORD_u
from cat.utils import CachedProperty
from cat.utils.collections_ import OrderedMultiDict
from cat.utils.profiling import ProfiledFunction

from base.model.messages import *
from base.model.parsing.bytesUtils import bytesToStr, strToBytes, ORD_BACKSLASH, ORD_DOUBLE_QUOTE, ORD_SINGLE_QUOTE
from base.model.parsing.parser import ParserBase, IndexMapBuilder, IndexMapper, TokenizerBase
from base.model.utils import Span, MDStr, Message, NULL_SPAN, Position, wrapInMDCode
from corePlugins.nbtJsonBase.core import (
	KeySchema,
	StructureDataNode,
	StructureDataSchema,
	TokenType,
	Token,
	InvalidNode,
	NullNode,
	BooleanNode,
	NumberNode,
	StringNode,
	ListNode,
	NumberArrayNode,
	StructureProperty,
	ObjectNode, StructureNode, StructureKind,
)
from corePlugins.nbtJsonBase.schema import pathify, enrichWithSchema

ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG = Message("JSON standard allows only double quoted string as property key", 0)
MISSING_VALUE_MSG = Message("Missing value for property", 0)
INVALID_NUMBER_MSG: Message = Message("Invalid {0}: '`{1}`'", 2)
ARRAY_PREFIX_MUST_BE_CAPITALIZED_MSG: Message = Message("Array prefix must be capitalized.", 0)

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

_BOOLEAN_TOKENS = {
	b'true': True,
	b'false': False,
}


@dataclass
class NumberInfo[T: int | float]:
	suffix: tuple[bytes, ...]
	min: T
	max: T
	name: str
	pyType: Callable[[str], T]


NUMBER_INFO: dict[str, NumberInfo] = {
	'byte': NumberInfo((b'b', b'B'), -128, 127, 'a Byte', int),
	'short': NumberInfo((b's', b'S'), -32768,  32767, 'a Short', int),
	'int': NumberInfo((b'',), -2147483648, 2147483647, 'a Int', int),
	'long': NumberInfo((b'l', b'L'), -9223372036854775808, 9223372036854775807, 'a Long', int),
	'json_long': NumberInfo((b'',), -9223372036854775808, 9223372036854775807, 'a Long', int),
	'float': NumberInfo((b'f', b'F', b''), -3.4E+38, +3.4E+38, 'a Float', float),
	'double': NumberInfo((b'd', b'D'), -1.7E+308, 1.7E+308, 'a Double', float),
	'json_double': NumberInfo((b'',), -1.7E+308, 1.7E+308, 'a Double', float),
}

NUMBER_INFO_BY_SUFFIX: dict[bytes, NumberInfo] = {suffix: info for info in NUMBER_INFO.values() for suffix in info.suffix if suffix}


@dataclass
class StructureNodeParserBase(ParserBase[StructureNode, StructureDataSchema]):

	ignoreTrailingChars: bool = False

	_waitingForClosing: dict[TokenType, int] = field(default_factory=lambda: defaultdict(int), init=False)
	_tokenizer: TokenizerBase[Token] = field(init=False)
	_current: Token = field(init=False)
	_eofToken: Token = field(init=False)
	_last: Token = field(init=False)

	_eofAlreadyLogged: bool = field(default=False, init=False)

	structureKind: ClassVar[StructureKind]
	_valid_key_tokens: ClassVar[set[TokenType]] = set()

	def __post_init__(self) -> None:
		super().__post_init__()
		self.errors = self._tokenizer.errors  # sync errors
		self._current = cast(Any, None)
		self._next()  # sets self._current, self._last

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
			if not self._eofAlreadyLogged:  # prevent repeated 'unexpected eof' messages
				span = self._last.span if self._last is not None else NULL_SPAN
				self.errorMsg(UNEXPECTED_EOF_MSG, span=span)
				self._eofAlreadyLogged = True
			return True
		return False

	def accept(self, tokenType: TokenType, advanceIfBad: bool = True) -> Token:
		current = self._current
		if self._checkEof():
			return current

		if current.type is not tokenType:
			self.errorMsg(EXPECTED_BUT_GOT_MSG, tokenType.asString, bytesToStr(current.value), span=current.span)
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
			self.errorMsg(EXPECTED_BUT_GOT_MSG, name, bytesToStr(current.value), span=current.span)
			if advanceIfBad:
				self._next()
		else:
			self._next()
		return current  # current == (self._last if _next() was called, else self._current)

	def parse_object2(self) -> ObjectNode:
		"""Parses an object out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.invalid, TokenType.colon}
		goodValueTokens = {TokenType.unquoted_string}
		objData: OrderedMultiDict[str, StructureProperty] = OrderedMultiDict()

		def parse_property() -> None:
			nonlocal objData
			colonAlreadySeen = False
			token = self._last
			# parse KEY:
			if token.type in self._valid_key_tokens:
				key: StringNode = self.parse_string()
			elif token.type in self._PARSERS.keys():
				key = self._internalParseTokens()  # type: ignore
				if key.typeName != StringNode.typeName:
					self.errorMsg(ONLY_DBL_QUOTED_STR_AS_PROP_KEY_MSG, span=key.span)
					key = InvalidNode(key.span, None, bytesToStr(self.text[key.span.slice]), structureKind=self.structureKind)  # type: ignore
			elif token.type == TokenType.invalid:
				key = self.parse_invalid()  # type: ignore
			elif token.type == TokenType.colon:
				key = InvalidNode(Span(token.span.start), None, '', structureKind=self.structureKind)  # type: ignore
				colonAlreadySeen = True
			else:
				assert False, f"invalid state: invalid TokenType {token.type} for property"
			key.schema = KeySchema()

			if not colonAlreadySeen:
				token = self.accept(TokenType.colon, advanceIfBad=False)

			if token.type is not TokenType.colon:
				value: StructureDataNode = InvalidNode(Span(self._last.span.end, token.span.end), None, '', structureKind=self.structureKind)
				objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
				return

			# duplicate colons:
			while (tkn2 := self.tryAccept(TokenType.colon)) is not None:
				self.errorMsg(DUPLICATE_NOT_ALLOWED_MSG, TokenType.colon.asString, span=tkn2.span)

			if token.type is TokenType.eof:
				value = InvalidNode(Span(self._last.span.end, token.span.end), None, '', structureKind=self.structureKind)
				objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
				return
			elif self._waitingForClosing[self._current.type] > 0:
				self.errorMsg(MISSING_VALUE_MSG, span=self._last.span)
				value = InvalidNode(Span(self._last.span.end, self._current.span.start), None, '', structureKind=self.structureKind)
				objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
				return
			elif self.tryAcceptAnyOf(self._PARSERS.keys()) is not None:
				value = self._internalParseTokens()
				objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
				return
			else:
				# force error, but don't consume:
				self.acceptAnyOf(self._PARSERS.keys(), advanceIfBad=False)
				if self.tryAccept(TokenType.invalid) is not None:
					value = self.parse_invalid()
					objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
					return
				elif (token2 := self.tryAccept(TokenType.eof)) is not None:
					value = InvalidNode(Span(self._last.span.end, token2.span.end), None, '', structureKind=self.structureKind)
					objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
					return
				else:
					value = InvalidNode(Span(self._last.span.end, self._current.span.start), None, '', structureKind=self.structureKind)
					objData.add(key.data, StructureProperty(Span(key.span.start, value.span.end), None, key, value, structureKind=self.structureKind))
					return

		start = self._last.span.start
		end = self._parse_list_like(TokenType.comma, TokenType.object_end, valueTokens, goodValueTokens, parse_property)
		return ObjectNode(Span(start, end), None, objData, structureKind=self.structureKind)

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
						tkn = tkn2
					if self.tryAccept(closing) is not None:
						if self.structureKind is StructureKind.JSON: # JSON does not allow trailing commas.
							self.errorMsg(TRAILING_NOT_ALLOWED_MSG, delimiter.asString, span=tkn.span)
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

	def parse_list(self) -> ListNode:
		"""Parses an array out of JSON tokens"""
		valueTokens = {*self._PARSERS.keys(), TokenType.invalid}
		goodValueTokens = {*self._PARSERS.keys()}
		arrayData: list[StructureDataNode] = []

		def parse_element() -> None:
			nonlocal arrayData
			value = self._internalParseTokens()
			arrayData.append(value)

		start = self._last.span.start
		end = self._parse_list_like(TokenType.comma, TokenType.list_end, valueTokens, goodValueTokens, parse_element)
		return ListNode(Span(start, end), None, arrayData, structureKind=self.structureKind)

	@CachedProperty
	def _arrayTagByPrefix(self) -> dict[int, Callable[[], NumberNode]]:
		return {
			ord('B'): self.parse_byte,
			ord('I'): self.parse_int,
			ord('L'): self.parse_long,
		}

	def parse_array(self) -> NumberArrayNode:
		prefix = self._last.value[1]
		if prefix in b'bil':
			self.errorMsg(ARRAY_PREFIX_MUST_BE_CAPITALIZED_MSG, span=self._last.span)
			prefix += ord('A') - ord('a')

		if prefix not in b'BIL':
			self.errorMsg(UNKNOWN_MSG, "array prefix", chr(prefix), span=self._last.span)
			prefix = ord('L')

		parseTag = self._arrayTagByPrefix[prefix]

		valueTokens = {TokenType.number, TokenType.invalid}
		goodValueTokens = {TokenType.number}
		arrayData: list[NumberNode] = []

		def parse_element() -> None:
			nonlocal arrayData
			tag = parseTag()
			arrayData.append(tag)

		start = self._last.span.start
		end = self._parse_list_like(TokenType.comma, TokenType.list_end, valueTokens, goodValueTokens, parse_element)
		return NumberArrayNode(Span(start, end), None, arrayData, bytes([prefix]), structureKind=self.structureKind)

	def _parse_string_or_bool(self) -> StructureDataNode:
		current = self._last
		content = current.value
		if content == b'true':
			return BooleanNode(current.span, None, True, content, structureKind=self.structureKind)
		elif content == b'false':
			return BooleanNode(current.span, None, False, content, structureKind=self.structureKind)
		else:
			innerSlice = current.span.slice
			return StringNode(current.span, None, bytesToStr(content), content, content, innerSlice, self.indexMapper, structureKind=self.structureKind)

	def parse_string(self) -> StringNode:
		"""Parses a string out of a JSON token"""
		# TODO: usage of IndexMapBuilder needs a thorough testing. It is completely untested. [23-7-2023]
		token = self._last
		string = raw = token.value
		hasEscapeSequence = b'\\' in string

		# calculate innerSlice:
		if token.type == TokenType.quoted_string:
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
				if self.structureKind is StructureKind.JSON and next_char == ORD_u:  # SNBT does not support unicode escapes like JSON.
					# 'růže' -> "r\u016f\u017ee"
					hex_string = string[index + 2:index + 6]
					try:
						unicode_char = literal_eval(f'"\\u{bytesToStr(hex_string)}"')
					except SyntaxError:
						self.error(MDStr(f"Invalid unicode escape: `\\u{bytesToStr(hex_string)}`"), span=token.span)
						unicode_char = b'\\u' + hex_string
					else:
						unicode_char = strToBytes(unicode_char)
						idxMapBldr.addMarker(index - 1,     decIdx)  # just before (=start of) escape sequence
						idxMapBldr.addMarker(index - 1 + 6, decIdx + 1)  # just after (=end of) escape sequence

					chars += unicode_char
					index += 6
					strStreakStart = index
					continue
				else:
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

		return StringNode(token.span, None, value, raw, string, innerSlice, idxMap, structureKind=self.structureKind)

	def makeIndexMapBuilderForStr(self, contentStartIdx: int) -> IndexMapBuilder:
		return IndexMapBuilder(self.indexMapper, self.indexMapper.toDecoded(contentStartIdx))

	def parse_number(self) -> NumberNode:
		# TODO: all numbers are interoperable (even int / float, ...)
		# TODO: floats & doubles don't need a suffix.
		current = self._last
		content = current.value

		suffix = content[-1:]
		numberInfo = NUMBER_INFO_BY_SUFFIX.get(suffix)
		if numberInfo is not None:
			return self._parse_number_internal(numberInfo)
		if any(c in content for c in b'.eE'):
			return self._parse_number_internal(NUMBER_INFO['float' if self.structureKind is StructureKind.SNBT else 'json_double'])
		else:
			return self._parse_number_internal(NUMBER_INFO['int' if self.structureKind is StructureKind.SNBT else 'json_long'])

	def _parse_number_internal[T: int | float](self, numberInfo: NumberInfo[T]) -> NumberNode:
		current = self._last
		content = current.value

		if content.endswith(numberInfo.suffix):
			try:
				strVal = content
				for sfx in numberInfo.suffix:
					if content.endswith(sfx):
						strVal = strVal.removesuffix(sfx)
						break
				value: T = numberInfo.pyType(bytesToStr(strVal))
			except ValueError:
				self.errorMsg(INVALID_NUMBER_MSG, numberInfo.pyType.__name__, bytesToStr(content), span=current.span)
				value = numberInfo.pyType('0')
			if not numberInfo.min <= value <= numberInfo.max:  # type: ignore
				self.errorMsg(NUMBER_OUT_OF_BOUNDS_MSG, str(numberInfo.min), str(numberInfo.max), span=current.span)

			return NumberNode(current.span, None, value, content, structureKind=self.structureKind)
		else:
			self.errorMsg(EXPECTED_BUT_GOT_MSG_RAW, numberInfo.name, wrapInMDCode(bytesToStr(content)), span=current.span)
			if ORD_a <= content[-1] <= ORD_z or ORD_A_CAP <= content[-1] <= ORD_Z_CAP:
				valueBad = float(bytesToStr(content[:-1]))
			else:
				valueBad = float(bytesToStr(content))
			return NumberNode(current.span, None, valueBad, content, structureKind=self.structureKind)

	def parse_byte(self) -> NumberNode[int]:
		return self._parse_number_internal(NUMBER_INFO['byte'])

	def parse_int(self) -> NumberNode[int]:
		return self._parse_number_internal(NUMBER_INFO['int'])

	def parse_long(self) -> NumberNode[int]:
		return self._parse_number_internal(NUMBER_INFO['long'])

	def parse_boolean(self) -> BooleanNode:
		"""Parses a boolean out of a JSON token"""
		token = self._last
		value = _BOOLEAN_TOKENS[token.value]
		return BooleanNode(token.span, None, value, token.value, structureKind=self.structureKind)

	def parse_null(self) -> NullNode:
		"""Parses a null value out of a JSON token"""
		token = self._last
		return NullNode(token.span, None, structureKind=self.structureKind)

	def parse_invalid(self) -> InvalidNode:
		"""Parses an invalid token out of a JSON token"""
		token = self._last
		return InvalidNode(token.span, None, bytesToStr(token.value), structureKind=self.structureKind)

	@CachedProperty
	def _PARSERS(self) -> dict[TokenType, Callable[[], StructureDataNode]]:
		return {
			TokenType.list_start: self.parse_list,
			TokenType.array_start: self.parse_array,
			TokenType.object_start: self.parse_object2,
			TokenType.quoted_string: self.parse_string,
			TokenType.unquoted_string: self._parse_string_or_bool,
			TokenType.number: self.parse_number,
			TokenType.boolean: self.parse_boolean,
			TokenType.null: self.parse_null,
		}

	def _internalParseTokens(self) -> StructureDataNode:
		"""Recursive JSON parse implementation"""
		token = self._last
		parser = self._PARSERS.get(token.type)
		if parser is not None:
			value = parser()
			return value
		else:
			return InvalidNode(token.span, None, bytesToStr(token.value), structureKind=self.structureKind)

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

		if not self.ignoreTrailingChars and self._current is not None and self._current.type is not TokenType.eof:
			self.error(
				MDStr(f"Invalid SNBT at `{bytesToStr(self._current.value)}`"),
				span=self._current.span
			)

		self.cursor = self._tokenizer.cursor
		self.line = self._tokenizer.line
		self.lineStart = self._tokenizer.lineStart
		return value
