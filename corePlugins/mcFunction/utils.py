from __future__ import annotations

from base.model.utils import Message, GeneralError

EXPECTED_ARGUMENT_SEPARATOR_MSG: Message = Message("Expected whitespace to end one argument, but found trailing data: `{}`", 1)


class CommandSyntaxError(GeneralError):
	pass


class CommandSemanticsError(GeneralError):
	pass


__all__ = [
	'EXPECTED_ARGUMENT_SEPARATOR_MSG',
	'CommandSyntaxError',
	'CommandSemanticsError',
]