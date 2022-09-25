from __future__ import annotations
import builtins
from dataclasses import dataclass, field, replace
from typing import final, Iterator, NewType, Protocol

import markdown

from Cat.utils import escapeForXmlTextContent, strings

LanguageId = NewType('LanguageId', str)


class _LanguageIds:
	SNBT = LanguageId('SNBT')
	MCJson = LanguageId('MCJson')
	JSON = LanguageId('JSON')
	MCCommand = LanguageId('MCCommand')
	MCFunction = LanguageId('MCFunction')


LANGUAGES: _LanguageIds = _LanguageIds()


class MessageLike(Protocol):
	def format(self, *args) -> MDStr:
		pass


@dataclass(frozen=True)
class Message:
	rawMessage: str
	argsCount: int

	def format(self, *args) -> MDStr:
		if len(args) > self.argsCount:
			raise ValueError(f"too many arguments supplied. expected {self.argsCount}, but got {len(args)}")
		elif len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected {self.argsCount}, but got {len(args)}")

		return MDStr(self.rawMessage.format(*args))


@dataclass(frozen=True)
class MessageAdapter:
	rawMessage: str
	argsCount: int

	def format(self, msg: MessageLike, *args) -> MDStr:
		if len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected at least {self.argsCount}, but got {len(args)}")

		selfArgs = args[:self.argsCount]
		innerArgs = args[self.argsCount:]

		innerMsg = msg.format(*innerArgs)

		return MDStr(self.rawMessage.format(*selfArgs, msg=innerMsg))


@final
@dataclass(order=True, unsafe_hash=True, slots=True)
class Position:
	line: int = field(default=-1, hash=False, compare=False)
	column: int = field(default=-1, hash=False, compare=False)
	index: int = field(default=-1, hash=False, compare=True)

	def __iter__(self):
		yield self.line
		yield self.column

	def __len__(self):
		return 2

	def __add__(self, other: int) -> Position:
		return replace(self, column=self.column + other, index=self.index + other)

	def __sub__(self, other: int) -> Position:
		return replace(self, column=self.column - other, index=self.index - other)


@final
@dataclass(init=False, unsafe_hash=True, slots=True)
class Span:
	start: Position
	end: Position

	def __init__(self, start: Position = None, end: Position = None):
		self.start = Position() if start is None else start
		self.end = self.start if end is None else end
		assert isinstance(self.start, Position)
		assert isinstance(self.end, Position)

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

	def __repr__(self):
		return f' Span({self.start!r}, {self.end!r})'

	@staticmethod
	def between(start: Span, end: Span) -> Span:
		return Span(start.end, end.start)

	@staticmethod
	def encompassing(start: Span, end: Span) -> Span:
		return Span(start.start, end.end)


HTMLStr = strings.HTMLStr
"""A HTML string."""

MDStr = NewType('MDStr', str)
"""A Markdown string. (see: https://daringfireball.net/projects/markdown/)"""


_MD_CONVERTER = markdown.Markdown()


def formatMarkdown(text: str, /) -> HTMLStr:
	html = _MD_CONVERTER.convert(text)
	return HTMLStr(html)


def wrapInMarkdownCode(text: str) -> str:
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
	return text


def addStyle(message: str, /, style: str) -> MDStr:
	from Cat.CatPythonGUI.GUI import PythonGUI
	md = f'<div style="{PythonGUI.helpBoxStyles[style]}">{message}</div>'
	return MDStr(md)


def formatAsHint(message: str, /) -> MDStr:
	return addStyle(message, "hint")


def formatAsWarning(message: str, /) -> MDStr:
	return addStyle(message, "warning")


def formatAsError(message: str, /) -> MDStr:
	return addStyle(message, "error")


class GeneralError:  # TODO: find better & more descriptive name
	def __init__(self, message: MDStr, span: Span = None, style: str = 'error'):
		super(GeneralError, self).__init__()
		if span is None:
			span = Span()
		self.message: MDStr = message
		self.htmlMessage: HTMLStr = formatMarkdown(message)
		self.span: Span = span
		self.style: str = style

	def __str__(self):
		return f"{self.message}, at pos {self.span.start.column}, line {self.span.start.line + 1}"

	@property
	def position(self) -> Position:
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
		super(WrappedError, self).__init__(MDStr(escapeForXmlTextContent(str(exception))), span=span, style=style)
		self.wrappedEx = exception


__all__ = [
	'LanguageId',
	'LANGUAGES',
	'Message',
	'MessageAdapter',
	'Position',
	'Span',
	'HTMLStr',
	'MDStr',
	'formatMarkdown',
	'wrapInMarkdownCode',
	'addStyle',
	'formatAsHint',
	'formatAsWarning',
	'formatAsError',
	'GeneralError',
	'ParsingError',
	'SemanticsError',
	'WrappedError',
]
