"""Arabic/Persian text normalisation.

Normalisation is intentionally lossy and is only used to build a search-friendly
("text_normalised") variant of text. The original text is always preserved
alongside it (e.g. Page.text_raw vs Page.text_normalised).
"""

import re
import unicodedata

# Arabic combining diacritics (tashkīl) + tatweel + Quranic annotation marks.
_DIACRITICS_RE = re.compile(
    "["
    "ؐ-ؚ"  # Arabic honorifics / Quranic signs
    "ً-ٟ"  # fatha, damma, kasra, shadda, sukun, etc.
    "ٰ"  # superscript alef
    "ۖ-ۜ"  # Quranic annotation signs
    "۟-ۨ"
    "۪-ۭ"
    "ـ"  # tatweel (kashida)
    "]"
)

_YEH_VARIANTS_RE = re.compile("[يىۍێ]")  # Arabic yeh + lookalikes -> Persian yeh (ی)
_ALIF_VARIANTS_RE = re.compile("[أإآٱ]")  # hamza/madda alif variants -> bare alif (ا)
_WHITESPACE_RE = re.compile(r"\s+")
_ZWNJ_RE = re.compile("[‌‍‎‏]")  # zero-width joiners/marks


def strip_diacritics(text: str) -> str:
    return _DIACRITICS_RE.sub("", text)


def normalise_yeh(text: str) -> str:
    """Unify Arabic yeh (ي) and Persian yeh (ی) plus other yeh-like glyphs to ی."""
    return _YEH_VARIANTS_RE.sub("ی", text)


def normalise_kaf(text: str) -> str:
    """Unify Arabic kaf (ك) to Persian kaf (ک)."""
    return text.replace("ك", "ک")


def normalise_alif(text: str) -> str:
    """Collapse alif variants (hamza-above/below, madda) to bare alif ا."""
    return _ALIF_VARIANTS_RE.sub("ا", text)


def normalise_whitespace(text: str) -> str:
    text = _ZWNJ_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalise_arabic_persian(text: str) -> str:
    """Full normalisation pipeline used to populate *_normalised columns.

    Order matters: strip diacritics first so combining marks don't interfere
    with later character substitutions, then unify letter variants, then
    collapse whitespace last.
    """
    text = unicodedata.normalize("NFC", text)
    text = strip_diacritics(text)
    text = normalise_yeh(text)
    text = normalise_kaf(text)
    text = normalise_alif(text)
    text = normalise_whitespace(text)
    return text
