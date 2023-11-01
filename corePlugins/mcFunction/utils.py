from __future__ import annotations

from base.model.utils import Message, GeneralError


class CommandSyntaxError(GeneralError):
	pass


class CommandSemanticsError(GeneralError):
	pass


__all__ = [
	'CommandSyntaxError',
	'CommandSemanticsError',
]