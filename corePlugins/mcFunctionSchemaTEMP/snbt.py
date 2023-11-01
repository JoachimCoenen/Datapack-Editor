from typing import Optional

from nbtlib import Parser, tokenize, Int, String, List, Compound, Path, ListIndex, CompoundMatch, InvalidLiteral
from nbtlib.path import can_be_converted_to_int, NamedKey, extend_accessors

from corePlugins.mcFunction.stringReader import StringReader
from corePlugins.mcFunction.utils import CommandSyntaxError
from corePlugins.nbt.tags import NBTTag, NBTTagSchema
from base.model.parsing.bytesUtils import bytesToStr
from base.model.parsing.contextProvider import parseNPrepare
from base.model.pathUtils import FilePath
from base.model.utils import Span, GeneralError, LanguageId, wrapInMarkdownCode


def parseNBTTag(sr: StringReader, filePath: FilePath, *, errorsIO: list[GeneralError]) -> Optional[NBTTag]:
	# parse_nbt('{foo: [hello, world], bar: [I; 1, 2, 3]}')
	sr.save()
	literal = sr.text[sr.cursor:]
	if not literal:
		sr.rollback()
		return None

	tag, errors = parseNPrepare(
		sr.text[sr.cursor:],
		filePath=filePath,
		language=LanguageId('SNBT'),
		schema=NBTTagSchema(''),
		line=sr.line,
		lineStart=sr.lineStart,
		cursor=0,
		cursorOffset=sr.cursor + sr.lineStart,
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
		sr.line = tag.span.end.line
		sr.lineStart = tag.span.end.index - tag.span.end.column
	else:
		sr.rollback()
	return tag


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
			begin, end = sr.currentSpan.asTuple
		else:
			start = ex.args[0][0] + sr.cursor
			stop = ex.args[0][1] + sr.cursor
			begin = sr.posFromColumn(start)
			end = sr.posFromColumn(stop)
		errorsIO.append(CommandSyntaxError(wrapInMarkdownCode(message), Span(begin, end), style='error'))
		sr.rollback()
		return None

	return path


def parseNBTPath(sr: StringReader, *, errorsIO: list[CommandSyntaxError]) -> Optional[Path]:
	path: Optional[Path] = _parseNBTPathBare(sr, errorsIO=errorsIO)
	if path is None:
		return None
	return path
