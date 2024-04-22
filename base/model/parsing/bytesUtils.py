from typing import Optional
from .bytesConstants import *  # do not remove


def bytesToStr(raw: bytes) -> str:
	return str(raw, encoding='utf-8', errors='replace')


def strToBytes(raw: str) -> bytes:
	return bytes(raw, encoding='utf-8', errors='replace')


def bytesOptToStr(raw: Optional[bytes]) -> Optional[str]:
	return str(raw, encoding='utf-8', errors='replace') if raw is not None else None


def strOptToBytes(raw: Optional[str]) -> Optional[bytes]:
	return bytes(raw, encoding='utf-8', errors='replace') if raw is not None else None


def readNextUTF8char(raw: bytes, start: int = 0) -> tuple[str, int]:
	"""
	returns: (the read character, number of bytes read.) Rhe read character contains between 0 and 1 characters.
	"""
	if start >= len(raw):
		return '', 0

	# simplest case:
	if (raw[start] & 0b10000000) == 0b00000000:
		return bytesToStr(raw[start: start + 1]), 1

	if (raw[start] & 0b11111000) == 0b11110000:
		length = 4
	elif (raw[start] & 0b11110000) == 0b11100000:
		length = 3
	elif (raw[start] & 0b11100000) == 0b11000000:
		length = 2
	elif (raw[start] & 0b11000000) == 0b10000000:
		# we are somewhere inside a character, not at the start. Read 'till the end.
		# bytesToStr(...) will deal with the rest.
		if (start + 1) >= len(raw) or (raw[start + 1] & 0b11000000) != 0b10000000:
			length = 1
		elif (start + 2) >= len(raw) or (raw[start + 2] & 0b11000000) != 0b10000000:
			length = 2
		else:
			length = 3
	else:
		# raw[start] is of the form 0b11111xxx which is illegal.
		# so just assume l = 1. bytesToStr(...) will deal with the rest.
		length = 1

	return bytesToStr(raw[start: start + length]), min(len(raw) - start, length)
