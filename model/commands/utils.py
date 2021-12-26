from __future__ import annotations

from Cat.Serializable import RegisterContainer
from model.parsingUtils import GeneralParsingError
from model.utils import Message


EXPECTED_ARGUMENT_SEPARATOR_MSG: Message = Message("Expected whitespace to end one argument, but found trailing data: `{}`", 1)


@RegisterContainer
class CommandSyntaxError(GeneralParsingError):
	__slots__ = ()
	pass


@RegisterContainer
class CommandSemanticsError(GeneralParsingError):
	__slots__ = ()
	pass


__all__ = [
	'EXPECTED_ARGUMENT_SEPARATOR_MSG',
	'CommandSyntaxError',
	'CommandSemanticsError',
]