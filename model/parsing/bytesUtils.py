

def bytesToStr(raw: bytes) -> str:
	return str(raw, encoding='utf-8', errors='replace')


def strToBytes(raw: str) -> bytes:
	return bytes(raw, encoding='utf-8', errors='replace')


WHITESPACE = b' \t\n\r\v\f'
WHITESPACE_CHARS = set(WHITESPACE)

WHITESPACE_NO_LF = b' \t\r\v\f'
"""without the line feed character (\\n)"""
WHITESPACE_NO_LF_CHARS = set(WHITESPACE_NO_LF)


CR_LF = b'\r\n'
"""carriage return & line feed (\\r\\n)"""
CR_LF_CHARS = set(CR_LF)

ASCII_LOWERCASE = b'abcdefghijklmnopqrstuvwxyz'
ASCII_LOWERCASE_RANGE = range(ASCII_LOWERCASE[0], ASCII_LOWERCASE[-1])
ASCII_UPPERCASE = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ASCII_UPPERCASE_RANGE = range(ASCII_UPPERCASE[0], ASCII_UPPERCASE[-1])

ASCII_LETTERS = ASCII_LOWERCASE + ASCII_UPPERCASE

DIGITS = b'0123456789'
DIGITS_RANGE = range(DIGITS[0], DIGITS[-1]+1)

# A character is a Java whitespace character if and only if it satisfies one of the following criteria:
JAVA_WHITESPACES: set[bytes] = {bytes(__char, encoding='utf-8', errors='replace') for __char in [
	# It is a Unicode space character (SPACE_SEPARATOR, LINE_SEPARATOR, or PARAGRAPH_SEPARATOR) but is not also a non-breaking space ('\u00A0', '\u2007', '\u202F'):
	# SPACE_SEPARATORs:
	'\u0020',  # Space
	# '\u00A0', (excluded) # No-Break Space
	'\u1680',  # Ogham Space Mark
	'\u2000',  # En Quad
	'\u2001',  # Em Quad
	'\u2002',  # En Space
	'\u2003',  # Em Space
	'\u2004',  # Three-Per-Em Space
	'\u2005',  # Four-Per-Em Space
	'\u2006',  # Six-Per-Em Space
	# '\u2007', (excluded)  # Figure Space
	'\u2008',  # Punctuation Space
	'\u2009',  # Thin Space
	'\u200A',  # Hair Space
	# '\u202F',  (excluded) # Narrow No-Break Space
	'\u205F',  # Medium Mathematical Space
	'\u3000',  # Ideographic Space
	# LINE_SEPARATORs:
	'\u2028',  # Line Separator
	# PARAGRAPH_SEPARATORs:
	'\u2029',  # Paragraph Separator
	# Explicitly named Characters:
	'\t',      # It is '\t', U+0009 HORIZONTAL TABULATION.
	'\n',      # It is '\n', U+000A LINE FEED.
	'\u000B',  # It is '\u000B', U+000B VERTICAL TABULATION.
	'\f',      # It is '\f', U+000C FORM FEED.
	'\r',      # It is '\r', U+000D CARRIAGE RETURN.
	'\u001C',  # It is '\u001C', U+001C FILE SEPARATOR.
	'\u001D',  # It is '\u001D', U+001D GROUP SEPARATOR.
	'\u001E',  # It is '\u001E', U+001E RECORD SEPARATOR.
	'\u001F',  # It is '\u001F', U+001F UNIT SEPARATOR.
]}

JAVA_WHITESPACES_SINGLE_BYTE: set[int] = {__char[0] for __char in JAVA_WHITESPACES if len(__char) == 1}

JAVA_WHITESPACES_THREE_BYTES: set[bytes] = {__char for __char in JAVA_WHITESPACES if len(__char) == 3}

assert len(JAVA_WHITESPACES_SINGLE_BYTE) + len(JAVA_WHITESPACES_THREE_BYTES) == len(JAVA_WHITESPACES)
