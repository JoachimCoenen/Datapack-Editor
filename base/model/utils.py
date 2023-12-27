from __future__ import annotations

import builtins
import itertools as it
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Iterator, NewType, Optional, final

import markdown
from recordclass import as_dataclass

from cat.utils import strings, GlobalGeneratingCache, Deprecated, escapeForXmlTextContent

LanguageId = NewType('LanguageId', str)


class MessageLike(ABC):
	@abstractmethod
	def format(self, *args) -> MDStr: ...


@dataclass(frozen=True)
class Message(MessageLike):
	rawMessage: str
	argsCount: int
	argumentTransformers: tuple[Optional[Callable[[str], str]], ...] = field(default=(), kw_only=True)

	def __post_init__(self):
		if len(self.argumentTransformers) > self.argsCount:
			raise ValueError(f"There are more argumentTransformers thn expected arguments. (argumentTransformers: {len(self.argumentTransformers)}, argsCount: {self.argsCount}).")

	def format(self, *args: str) -> MDStr:
		if len(args) > self.argsCount:
			raise ValueError(f"too many arguments supplied. expected {self.argsCount}, but got {len(args)}")
		elif len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected {self.argsCount}, but got {len(args)}")

		if self.argumentTransformers:
			args = tuple(
				arg if transform is None else transform(arg)
				for arg, transform in it.zip_longest(args, self.argumentTransformers, fillvalue=None)
			)

		return MDStr(self.rawMessage.format(*args))


@dataclass(frozen=True)
class MessageAdapter(MessageLike):
	rawMessage: str
	argsCount: int

	def format(self, msg: MessageLike, *args: str) -> MDStr:
		if len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected at least {self.argsCount}, but got {len(args)}")

		selfArgs = args[:self.argsCount]
		innerArgs = args[self.argsCount:]
		innerMsg = msg.format(*innerArgs)
		return MDStr(self.rawMessage.format(*selfArgs, msg=innerMsg))


@final
@as_dataclass(fast_new=True, hashable=True)
class Position:
	line: int
	column: int
	index: int

	def __iter__(self):
		yield self.line
		yield self.column

	def __len__(self):
		return 2

	def __str__(self):
		return f"{self.line + 1}:{self.column}"

	def __repr__(self):
		return f"Position(line={self.line!r}, column={self.column!r}, index={self.index!r})"

	def __add__(self, other: int) -> Position:
		return Position(self.line, column=self.column + other, index=self.index + other)

	def __sub__(self, other: int) -> Position:
		return Position(self.line, column=self.column - other, index=self.index - other)

	def __lt__(self, other):
		return self.index < other.index

	def __gt__(self, other):
		return self.index > other.index

	def __le__(self, other):
		return self.index <= other.index

	def __ge__(self, other):
		return self.index >= other.index

	def __eq__(self, other):
		if type(other) is not Position:
			return False
		return self.index == other.index

	def __ne__(self, other):
		if type(other) is not Position:
			return True
		return self.index != other.index

	def __hash__(self):
		return hash(self.index) + 31


@final
@as_dataclass(hashable=True, fast_new=True)
class Span:
	start: Position
	end: Position

	def __init__(self, start: Position = None, end: Position = None):
		self.start = NULL_POSITION if start is None else start
		self.end = self.start if end is None else end
		# assert isinstance(self.start, Position)
		# assert isinstance(self.end, Position)

	@property
	def slice(self) -> builtins.slice:
		return builtins.slice(self.start.index, self.end.index)

	@property
	def asTuple(self) -> tuple[Position, Position]:
		return self.start, self.end

	@property
	def length(self) -> int:
		return self.end.index - self.start.index

	def overlaps(self, other: Span) -> bool:
		return not (
			other.end.index <= self.start.index or
			self.end.index <= other.start.index
		)

	def __iter__(self) -> Iterator[Position]:
		yield self.start
		yield self.end

	def __contains__(self, item: Position):
		return self.start.index <= item.index <= self.end.index

	def __str__(self):
		return f'{self.start}-{self.end}'

	def __repr__(self):
		return f'Span({self.start!r}, {self.end!r})'

	@staticmethod
	def between(start: Span, end: Span) -> Span:
		return Span(start.end, end.start)

	@staticmethod
	def encompassing(start: Span, end: Span) -> Span:
		return Span(start.start, end.end)


NULL_POSITION = Position(-1, -1, -1)
NULL_SPAN = Span()


HTMLStr = strings.HTMLStr
"""A HTML string."""

MDStr = NewType('MDStr', str)
"""A Markdown string. (see: https://daringfireball.net/projects/markdown/)"""


_FORMAT_MARKDOWN_CACHE: GlobalGeneratingCache[str, HTMLStr] = GlobalGeneratingCache("_FORMAT_MARKDOWN_CACHE", lambda text: HTMLStr(markdown.markdown(text)), maxSize=32)


def formatMarkdown(text: str, /) -> HTMLStr:
	return _FORMAT_MARKDOWN_CACHE.getOrGenerate(text)


def wrapInMarkdownCode(text: str) -> MDStr:
	lenText = len(text)
	needsDouble = False
	if (idx := text.find('`')) >= 0:
		startsWith = idx == 0
		endsWith = text[-1] == '`'
		needsDouble = True
		while (idx := text.find('``', idx)) != -1:
			idx += 2
			if idx >= lenText or text[idx] != '`':
				needsDouble = False

		if startsWith:
			text = ' ' + text
		if endsWith:
			text += ' '

	if needsDouble:
		text = f'``{text}``'
	else:
		text = f'`{text}`'
	return MDStr(text)


wrapInMDCode = wrapInMarkdownCode  # an alias


def addStyle(message: str, /, style: str) -> MDStr | HTMLStr:
	from cat.GUI import PythonGUI
	md = f'<div style="{PythonGUI.helpBoxStyles[style]}">{message}</div>'
	return MDStr(md)


def formatAsHint(message: str, /) -> MDStr | HTMLStr:
	return addStyle(message, "hint")


def formatAsWarning(message: str, /) -> MDStr | HTMLStr:
	return addStyle(message, "warning")


def formatAsError(message: str, /) -> MDStr | HTMLStr:
	return addStyle(message, "error")


class GeneralError:  # TODO: find better & more descriptive name
	def __init__(self, message: MDStr, span: Span, style: str = 'error'):
		super(GeneralError, self).__init__()
		if self.__class__ is GeneralError:
			raise RuntimeError("GeneralError should not be instantiated directly")
		self.message: MDStr = message
		self.htmlMessage: HTMLStr = formatMarkdown(message)
		self.span: Span = span
		self.style: str = style

	def __str__(self):
		return f"{self.message} at {self.span.start}"

	@property
	@Deprecated(msg="use property 'Span.start' instead")
	def position(self) -> Position:
		return self.span.start

	@property
	def start(self) -> Position:
		return self.span.start

	@property
	def end(self) -> Position:
		return self.span.end


class ParsingError(GeneralError):
	pass


class SemanticsError(GeneralError):
	pass


class WrappedError(GeneralError):
	"""
	just a wrapper for any Exception
	satisfies protocol `Error`
	"""
	def __init__(self, exception: Exception, *, span: Span = None, style: str = 'error'):
		if span is None:
			span = NULL_SPAN
		super(WrappedError, self).__init__(MDStr(escapeForXmlTextContent(f"{type(exception).__name__}: {str(exception)}")), span=span, style=style)
		self.wrappedEx = exception


__all__ = [
	'LanguageId',
	'MessageLike',
	'Message',
	'MessageAdapter',
	'Position',
	'Span',
	'NULL_POSITION',
	'NULL_SPAN',
	'HTMLStr',
	'MDStr',
	'formatMarkdown',
	'wrapInMarkdownCode',
	'wrapInMDCode',
	'addStyle',
	'formatAsHint',
	'formatAsWarning',
	'formatAsError',
	'GeneralError',
	'ParsingError',
	'SemanticsError',
	'WrappedError',
]
