
from dataclasses import dataclass
from typing import ClassVar, cast

from base.model.parsing.tree import LanguageId2
from . import SNBT_ID
from .snbtTokenizer import SNBTTokenizer
from corePlugins.nbtJsonBase.core import TokenType, StructureDataNode, StructureKind
from corePlugins.nbtJsonBase.parserBase import StructureNodeParserBase


SNBT_ID2 = LanguageId2(SNBT_ID, StructureDataNode)


@dataclass
class SNBTParser(StructureNodeParserBase):

	ignoreTrailingChars: bool = False

	structureKind: ClassVar[StructureKind] = StructureKind.SNBT
	_valid_key_tokens: ClassVar[set[TokenType]] = {
		TokenType.unquoted_string,
		TokenType.quoted_string,
		TokenType.number,
		TokenType.boolean,
		TokenType.null,
	}

	def __post_init__(self) -> None:
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
		super().__post_init__()

	def parse(self) -> StructureDataNode | None:
		value = super().parse()

		self.cursor = cast(SNBTTokenizer, self._tokenizer).lastCursor
		self.line = cast(SNBTTokenizer, self._tokenizer).lastLine
		self.lineStart = cast(SNBTTokenizer, self._tokenizer).lastLineStart
		return value
