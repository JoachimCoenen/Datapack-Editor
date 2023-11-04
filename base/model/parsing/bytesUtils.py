from typing import Optional


def bytesToStr(raw: bytes) -> str:
	return str(raw, encoding='utf-8', errors='replace')


def strToBytes(raw: str) -> bytes:
	return bytes(raw, encoding='utf-8', errors='replace')


def bytesOptToStr(raw: Optional[bytes]) -> Optional[str]:
	return str(raw, encoding='utf-8', errors='replace') if raw is not None else None


def strOptToBytes(raw: Optional[str]) -> Optional[bytes]:
	return bytes(raw, encoding='utf-8', errors='replace') if raw is not None else None


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

# ordinal values dor common symbols ad chars:

ORD_a = ord(b'a')
ORD_b = ord(b'b')
ORD_c = ord(b'c')
ORD_d = ord(b'd')
ORD_e = ord(b'e')
ORD_f = ord(b'f')
ORD_g = ord(b'g')
ORD_h = ord(b'h')
ORD_i = ord(b'i')
ORD_j = ord(b'j')
ORD_k = ord(b'k')
ORD_l = ord(b'l')
ORD_m = ord(b'm')
ORD_n = ord(b'n')
ORD_o = ord(b'o')
ORD_p = ord(b'p')
ORD_q = ord(b'q')
ORD_r = ord(b'r')
ORD_s = ord(b's')
ORD_t = ord(b't')
ORD_u = ord(b'u')
ORD_v = ord(b'v')
ORD_w = ord(b'w')
ORD_x = ord(b'x')
ORD_y = ord(b'y')
ORD_z = ord(b'z')

ORD_A_CAP = ord(b'A')
ORD_B_CAP = ord(b'B')
ORD_C_CAP = ord(b'C')
ORD_D_CAP = ord(b'D')
ORD_E_CAP = ord(b'E')
ORD_F_CAP = ord(b'F')
ORD_G_CAP = ord(b'G')
ORD_H_CAP = ord(b'H')
ORD_I_CAP = ord(b'I')
ORD_J_CAP = ord(b'J')
ORD_K_CAP = ord(b'K')
ORD_L_CAP = ord(b'L')
ORD_M_CAP = ord(b'M')
ORD_N_CAP = ord(b'N')
ORD_O_CAP = ord(b'O')
ORD_P_CAP = ord(b'P')
ORD_Q_CAP = ord(b'Q')
ORD_R_CAP = ord(b'R')
ORD_S_CAP = ord(b'S')
ORD_T_CAP = ord(b'T')
ORD_U_CAP = ord(b'U')
ORD_V_CAP = ord(b'V')
ORD_W_CAP = ord(b'W')
ORD_X_CAP = ord(b'X')
ORD_Y_CAP = ord(b'Y')
ORD_Z_CAP = ord(b'Z')

ORD_0 = ord(b'0')
ORD_1 = ord(b'1')
ORD_2 = ord(b'2')
ORD_3 = ord(b'3')
ORD_4 = ord(b'4')
ORD_5 = ord(b'5')
ORD_6 = ord(b'6')
ORD_7 = ord(b'7')
ORD_8 = ord(b'8')
ORD_9 = ord(b'9')

ORD_BACKSLASH = ord(b'\\')
ORD_SLASH = ord(b'/')
ORD_ASTERISK = ord(b'*')
ORD_MINUS = ord(b'-')
ORD_PLUS = ord(b'+')

ORD_DOUBLE_QUOTE = ord(b'"')
ORD_SINGLE_QUOTE = ord(b"'")

ORD_LF = ord(b'\n')