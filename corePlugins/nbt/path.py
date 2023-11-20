from dataclasses import dataclass
from typing import ClassVar, Collection, Optional

from nbtlib import Compound, CompoundMatch, Int, InvalidLiteral, List, ListIndex, Parser, Path, String, tokenize
from nbtlib.path import NamedKey, can_be_converted_to_int, extend_accessors

from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.parser import ParserBase
from base.model.parsing.tree import Node, Schema, _TNode
from base.model.utils import GeneralError, LanguageId, ParsingError, Span, wrapInMarkdownCode


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


def _parseNBTPathBare(sr: ParserBase, *, errorsIO: list[GeneralError]) -> Optional[Path]:
	p1 = sr.currentPos

	literal = sr.text[sr.cursor:]
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
			p2 = sr.currentPos
			begin, end = p1, p2
		else:
			start = ex.args[0][0] + sr.cursor
			stop = ex.args[0][1] + sr.cursor
			begin = sr._posFromColumn(start)
			end = sr._posFromColumn(stop)
		errorsIO.append(ParsingError(wrapInMarkdownCode(message), Span(begin, end), style='error'))
		return None

	return path


SNBT_PATH_ID: LanguageId = LanguageId('SNBTPath')


class NBTPathSchema(Schema):
	def asString(self) -> str:
		return 'NBTPathSchema'
	language: ClassVar[LanguageId] = SNBT_PATH_ID


@dataclass
class NBTPath(Node['NBTPath', NBTPathSchema]):
	@property
	def children(self) -> Collection[_TNode]:
		return ()

	language: ClassVar[LanguageId] = SNBT_PATH_ID
	path: Path


@dataclass
class SNBTPathParser(ParserBase[NBTPath, NBTPathSchema]):
	ignoreTrailingChars: bool = False

	def parse(self) -> Optional[NBTPath]:
		p1 = self.currentPos
		path: Optional[Path] = _parseNBTPathBare(self, errorsIO=self.errors)
		if path is None:
			return None
		p2 = self.currentPos
		return NBTPath(Span(p1, p2), self.schema, path)

