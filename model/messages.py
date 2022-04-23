from model.utils import Message, MessageAdapter

INTERNAL_ERROR_MSG: MessageAdapter = MessageAdapter("Internal Error! {msg}", 0)

EXPECTED_MSG: Message = Message("Expected {0}", 1)
EXPECTED_BUT_GOT_MSG: Message = Message("Expected {0} but got `{1}`", 2)
NUMBER_OUT_OF_BOUNDS_MSG = Message("Number out of bounds (min = {0}, max = {1})", 2)
UNEXPECTED_EOF_MSG: Message = Message("Unexpected end of file while parsing", 0)
UNKNOWN_MSG: Message = Message("Unknown {0}: '{1}'.", 2)


__all__ = [
	'INTERNAL_ERROR_MSG',

	'EXPECTED_MSG',
	'EXPECTED_BUT_GOT_MSG',
	'NUMBER_OUT_OF_BOUNDS_MSG',
	'UNEXPECTED_EOF_MSG',
	'UNKNOWN_MSG',
]