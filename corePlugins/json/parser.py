from dataclasses import dataclass
from typing import ClassVar

from .lexer import JsonTokenizer
from corePlugins.nbtJsonBase.parserBase import StructureNodeParserBase
from corePlugins.nbtJsonBase.core import TokenType, StructureKind


@dataclass
class JsonParser(StructureNodeParserBase):

	structureKind: ClassVar[StructureKind] = StructureKind.JSON
	_valid_key_tokens: ClassVar[set[TokenType]] = {TokenType.quoted_string}

	def __post_init__(self) -> None:
		allowMultilineStr = True or self.schema is not None and self.schema.allowMultilineStr
		self._tokenizer = JsonTokenizer(
			self.text,
			self.line,
			self.lineStart,
			self.cursor,
			self.cursorOffset,
			self.indexMapper,
			self.fullSource,
			allowMultilineStr
		)
		super().__post_init__()
