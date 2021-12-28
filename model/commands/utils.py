from __future__ import annotations

from model.utils import Message, GeneralParsingError

EXPECTED_ARGUMENT_SEPARATOR_MSG: Message = Message("Expected whitespace to end one argument, but found trailing data: `{}`", 1)


class CommandSyntaxError(GeneralParsingError):
	pass


class CommandSemanticsError(GeneralParsingError):
	pass


__all__ = [
	'EXPECTED_ARGUMENT_SEPARATOR_MSG',
	'CommandSyntaxError',
	'CommandSemanticsError',
]