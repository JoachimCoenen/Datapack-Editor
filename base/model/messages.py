from base.model.utils import Message, MessageAdapter

INTERNAL_ERROR_MSG: MessageAdapter = MessageAdapter("Internal Error! {msg}", 0)

EXPECTED_MSG: Message = Message("Expected {0}", 1)
EXPECTED_BUT_GOT_MSG: Message = Message("Expected {0} but got `{1}`", 2)
NUMBER_OUT_OF_BOUNDS_MSG = Message("Number out of bounds (min = {0}, max = {1})", 2)
UNEXPECTED_EOF_MSG: Message = Message("Unexpected end of file while parsing", 0)
UNKNOWN_MSG: Message = Message("Unknown {0}: '{1}'", 2)
DUPLICATE_NOT_ALLOWED_MSG: Message = Message("Duplicate {0} not allowed", 1)
TRAILING_NOT_ALLOWED_MSG: Message = Message("Trailing {0} not allowed", 1)
MISSING_DELIMITER_MSG = Message("Missing delimiter `{0}", 1)
MISSING_CLOSING_MSG = Message("Missing closing `{0}`", 1)


__all__ = [
	'INTERNAL_ERROR_MSG',

	'EXPECTED_MSG',
	'EXPECTED_BUT_GOT_MSG',
	'NUMBER_OUT_OF_BOUNDS_MSG',
	'UNEXPECTED_EOF_MSG',
	'UNKNOWN_MSG',
	'DUPLICATE_NOT_ALLOWED_MSG',
	'TRAILING_NOT_ALLOWED_MSG',
	'MISSING_DELIMITER_MSG',
	'MISSING_CLOSING_MSG',
]