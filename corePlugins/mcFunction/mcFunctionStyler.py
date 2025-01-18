from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Type, ClassVar

from cat.utils import Decorator
from cat.utils.collections_ import AddToDictDecorator
from base.gui.styler import DEFAULT_STYLE_ID, CatStyler, StyleIdEnum, StyleId, CommonStyleIds
from . import MC_FUNCTION_ID
from .argumentTypes import *
from .command import CommandSchema, MCFunction, ParsedComment, ParsedCommand, KeywordSchema, ArgumentSchema, CommandPart, ParsedArgument
from base.model.utils import LanguageId
from .filterArgs import FilterArgNode, FilterArgument


@dataclass
class ArgumentStyler(ABC):
	commandStyler: MCCommandStyler
	offset: int = field(init=False)

	def __post_init__(self) -> None:
		self.offset = self.commandStyler.offset

	def setStyling(self, span: slice, style: StyleId) -> None:
		self.commandStyler.setStyling(span, style)

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

	@classmethod
	def usesCommonStyleIds(cls) -> bool:
		return True

	argumentStylers: dict[str, ArgumentStyler] = field(init=False, repr=False, compare=False)

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		localInnerLanguages = []
		for argS in _argumentStylers.values():
			localInnerLanguages.extend(argS.localLanguages())
		return list(set(localInnerLanguages))
		# return [LanguageId('JSON')]

	def __post_init__(self) -> None:
		super(MCCommandStyler, self).__post_init__()
		self.argumentStylers = {
			name: argStylerCls(self) for name, argStylerCls in _argumentStylers.items()
		}

	def styleNode(self, data: CommandPart) -> int:
		if isinstance(data, ParsedCommand):
			return self.styleCommand(data)
		elif isinstance(data, ParsedComment):
			return self.styleComment(data)
		elif isinstance(data, MCFunction):
			return self.styleMCFunction(data)
		else:
			data: ParsedArgument
			return self.styleArguments(data)

	def styleMCFunction(self, function: MCFunction) -> int:
		end = function.span.start.index
		for child in function.children:
			if child is None:
				continue
			if child.start.index > self.ctx.end:
				break
			if child.end.index < self.ctx.start:
				continue
			if isinstance(child, ParsedComment):
				end = self.styleComment(child)
			else:
				child: ParsedCommand
				end = self.styleCommand(child)
		return end

	def styleComment(self, comment: ParsedComment) -> int:
		self.setStyling(comment.span.slice, CommonStyleIds.comment)
		return comment.span.end.index

	def styleCommand(self, command: ParsedCommand) -> int:
		return self.styleArguments(command.next)

	def styleArguments(self, argument: CommandPart) -> int:
		span = argument.span.slice
		while argument is not None:
			if argument.start.index > self.ctx.end:
				break
			if argument.end.index >= self.ctx.start:
				span = self.styleArgument(argument)
			argument = argument.next
		return span.stop

	def styleArgument(self, argument: CommandPart) -> slice:
		argument: ParsedArgument
		span = argument.span.slice
		schema = argument.schema

		if isinstance(schema, KeywordSchema):
			style = CommonStyleIds.default
		elif isinstance(schema, ArgumentSchema):
			typeName = schema.type.name
			styler = self.argumentStylers.get(typeName, None)
			if styler is not None:
				styler.style(argument)
				return span
			elif isinstance(schema.type, LiteralsArgumentType):
				style = CommonStyleIds.special_constant
			else:
				style = CommonStyleIds.error
		elif isinstance(schema, CommandSchema):
			style = CommonStyleIds.keyword
		else:
			style = CommonStyleIds.error
		self.setStyling(span, StyleId(style.value))
		return span


def addSimpleArgumentStyler(style: StyleId, *, forArgTypes: list[ArgumentType]) -> None:
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


addSimpleArgumentStyler(CommonStyleIds.special_constant, forArgTypes=[
	BRIGADIER_BOOL,
])

addSimpleArgumentStyler(CommonStyleIds.number, forArgTypes=[
	BRIGADIER_DOUBLE,
	BRIGADIER_FLOAT,
	BRIGADIER_INTEGER,
	BRIGADIER_LONG,
])

addSimpleArgumentStyler(CommonStyleIds.string, forArgTypes=[
	BRIGADIER_STRING,
])


class FilterArgumentsStyleIds(StyleIdEnum):
	Default = DEFAULT_STYLE_ID


@dataclass
class FilterArgumentsStyler(CatStyler[FilterArgNode]):

	@classmethod
	def usesCommonStyleIds(cls) -> bool:
		return True

	@classmethod
	def localInnerLanguages(cls) -> list[LanguageId]:
		return [MC_FUNCTION_ID]

	def styleNode(self, node: FilterArgNode) -> int:
		if node.typeName == FilterArgument.typeName:
			return self.styleStructuredNodeForeignNodes(node, DEFAULT_STYLE_ID)
		else:
			return self.styleStructuredNodeChildNodes(node, DEFAULT_STYLE_ID)
