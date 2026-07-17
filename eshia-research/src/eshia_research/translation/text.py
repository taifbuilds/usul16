"""Small text utilities for the translation pipeline."""

from __future__ import annotations

import hashlib
import math
import re

from eshia_research.normalise import normalise_arabic_persian


ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
FOOTNOTE_MARKER_RE = re.compile(r"\[([0-9٠-٩۰-۹]+)\]")
NUMBER_RE = re.compile(r"[0-9٠-٩۰-۹]+")
WHITESPACE_RE = re.compile(r"\s+")

_DIGIT_MAP = str.maketrans(
    {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
    }
)


def clean_ws(text: str | None) -> str:
    if not text:
        return ""
    return WHITESPACE_RE.sub(" ", text).strip()


def sha256_text(text: str | None) -> str:
    return hashlib.sha256(clean_ws(text).encode("utf-8")).hexdigest()


def source_norm(text: str | None) -> str:
    return normalise_arabic_persian(clean_ws(text or ""))


def approx_tokens_from_chars(chars: int, *, chars_per_token: float = 3.0) -> int:
    if chars <= 0:
        return 0
    return math.ceil(chars / chars_per_token)


def arabic_char_count(text: str | None) -> int:
    return len(ARABIC_RE.findall(text or ""))


def arabic_ratio(text: str | None) -> float:
    cleaned = clean_ws(text)
    if not cleaned:
        return 0.0
    return arabic_char_count(cleaned) / len(cleaned)


def normalise_digits(text: str) -> str:
    return text.translate(_DIGIT_MAP)


def number_tokens(text: str | None) -> list[str]:
    return [normalise_digits(match.group(0)) for match in NUMBER_RE.finditer(text or "")]


def footnote_markers(text: str | None) -> set[str]:
    return {normalise_digits(match.group(1)) for match in FOOTNOTE_MARKER_RE.finditer(text or "")}

