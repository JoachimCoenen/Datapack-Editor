from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Type, Optional, ClassVar

from cat.utils import Decorator
from cat.utils.collections_ import AddToDictDecorator
from base.gui.styler import DEFAULT_STYLE_ID, CatStyler, StyleIdEnum, StyleId
from .argumentTypes import *
from .command import CommandSchema, MCFunction, ParsedComment, ParsedCommand, KeywordSchema, ArgumentSchema, CommandPart, ParsedArgument
from base.model.utils import LanguageId


class StyleIds(StyleIdEnum):
	Default = DEFAULT_STYLE_ID
	Command = DEFAULT_STYLE_ID + 1
	String = DEFAULT_STYLE_ID + 2
	Number = DEFAULT_STYLE_ID + 3
	Constant = DEFAULT_STYLE_ID + 4
	TargetSelector = DEFAULT_STYLE_ID + 5
	Operator = DEFAULT_STYLE_ID + 6
	Keyword = DEFAULT_STYLE_ID + 7

	Complex = DEFAULT_STYLE_ID + 8
	Comment = DEFAULT_STYLE_ID + 9
	Error = DEFAULT_STYLE_ID + 10

	# KeyWord = 14
	# Variable = 11
	# BuiltinFunction = 17


_allArgumentTypeStyles: dict[str, Optional[StyleId]] = {
	BRIGADIER_BOOL.name:               StyleIds.Constant,
	BRIGADIER_DOUBLE.name:             StyleIds.Number,
	BRIGADIER_FLOAT.name:              StyleIds.Number,
	BRIGADIER_INTEGER.name:            StyleIds.Number,
	BRIGADIER_LONG.name:               StyleIds.Number,
	BRIGADIER_STRING.name:             StyleIds.String,
}


@dataclass
class ArgumentStyler(ABC):
	# innerStylers: dict[Type[Node], CatStyler]
	commandStyler: MCCommandStyler
	offset: int = field(init=False)
	#setStyling: StylingFunc = field(init=False)

	def __post_init__(self):
		self.offset = self.commandStyler.offset
		#2self.setStyling = self.commandStyler.setStyling

	def setStyling(self, span: slice, style: StyleIds) -> None:
		self.commandStyler.setStyling(span, StyleId(style + self.offset))

	@classmethod
	@abstractmethod
	def localLanguages(cls) -> list[LanguageId]:
		pass

	@abstractmethod
	def style(self, argument: ParsedArgument) -> None:
		pass


_argumentStylers: dict[str, Type[ArgumentStyler]] = {}
argumentStyler = Decorator(AddToDictDecorator(_argumentStylers))


@dataclass
class MCCommandStyler(CatStyler[CommandPart]):

	@property
	def styleIdEnum(self) -> Type[StyleIdEnum]:
		return StyleIds

	argumentStylers: dict[str, ArgumentStyler] = field(init=False, repr=False, compare=False)

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		localInnerLanguages = []
		for argS in _argumentStylers.values():
			localInnerLanguages.extend(argS.localLanguages())
		return list(set(localInnerLanguages))
		# return [LanguageId('JSON')]

	def __post_init__(self):
		super(MCCommandStyler, self).__post_init__()
		self.argumentStylers = {
			name: argStylerCls(self) for name, argStylerCls in _argumentStylers.items()
		}

	def styleNode(self, data: CommandPart) -> int:
		if isinstance(data, MCFunction):
			return self.styleMCFunction(data)
		elif isinstance(data, ParsedComment):
			return self.styleComment(data)
		else:
			data: ParsedCommand
			return self.styleCommand(data)

	def styleMCFunction(self, function: MCFunction) -> int:
		end = function.span.start.index
		for child in function.children:
			if child is None:
				continue
			elif isinstance(child, ParsedComment):
				end = self.styleComment(child)
			else:
				child: ParsedCommand
				end = self.styleCommand(child)
		return end

	def styleComment(self, comment: ParsedComment) -> int:
		self.setStyling(comment.span.slice, StyleIds.Comment)
		return comment.span.end.index

	def styleCommand(self, command: ParsedCommand) -> int:
		return self.styleArguments(command.next)

	def styleArguments(self, argument: CommandPart) -> int:
		span = argument.span.slice
		while argument is not None:
			span = self.styleArgument(argument)
			argument = argument.next
		return span.stop

	def styleArgument(self, argument: CommandPart) -> slice:
		argument: ParsedArgument
		span = argument.span.slice
		schema = argument.schema
		if isinstance(schema, KeywordSchema):
			style = StyleIds.Keyword
		elif isinstance(schema, ArgumentSchema):
			if isinstance(schema.type, LiteralsArgumentType):
				style = StyleIds.Constant
			else:
				typeName = schema.typeName
				# style = _allArgumentTypeStyles.get(typeName, StyleIds.Error)
				styler = self.argumentStylers.get(typeName, None)
				if styler is None:
					style = StyleIds.Error
				else:
					styler.style(argument)
					return span
		elif isinstance(schema, CommandSchema):
			style = StyleIds.Command
		else:
			style = StyleIds.Error
		self.setStyling(span, StyleId(style.value + self.offset))
		return span


def addSimpleArgumentStyler(style: StyleIds, *, forArgTypes: list[ArgumentType]) -> None:
	styleId = style

	class SimpleArgumentStyler(ArgumentStyler):
		STYLE: ClassVar[StyleId] = styleId

		@classmethod
		def localLanguages(cls) -> list[LanguageId]:
			return []

		def style(self, argument: ParsedArgument) -> None:
			self.setStyling(argument.span.slice, styleId)

	for argType in forArgTypes:
		argumentStyler(argType.name)(SimpleArgumentStyler)


addSimpleArgumentStyler(StyleIds.Constant, forArgTypes=[
	BRIGADIER_BOOL,
])

addSimpleArgumentStyler(StyleIds.Number, forArgTypes=[
	BRIGADIER_DOUBLE,
	BRIGADIER_FLOAT,
	BRIGADIER_INTEGER,
	BRIGADIER_LONG,
])

addSimpleArgumentStyler(StyleIds.String, forArgTypes=[
	BRIGADIER_STRING,
])
