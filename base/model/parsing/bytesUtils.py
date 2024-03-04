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
