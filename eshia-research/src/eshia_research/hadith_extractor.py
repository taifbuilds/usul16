"""Extract persistent hadith records from crawled page text.

This is intentionally conservative: it builds a first research layer from
the canonical Four Books, where the eShia text has regular printed hadith
numbering. The original page text stays untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy import delete
from sqlalchemy.orm import Session

from eshia_research.corpus import (
    BIHAR_DAR_IHYA_SOURCE_BOOK_ID,
    CANONICAL_FOUR_BOOK_SOURCE_IDS,
    CATALOG_EXCLUDED_SOURCE_BOOK_IDS,
    book_slug,
)
from eshia_research.models import Book, Hadith, Page
from eshia_research.normalise import normalise_arabic_persian, strip_diacritics

NUM = r"[0-9\u0660-\u0669\u06f0-\u06f9]+"
GAP = r"[\s\u200c\u200d]*"
SEP = r"[\u0640\-–—.]"

HADITH_START_RE = re.compile(
    rf"^(?:[\[(]{GAP}({NUM}){GAP}[\])]{GAP}(?:[.]{GAP})?)?"
    rf"({NUM}(?:{GAP}/{GAP}{NUM})?){GAP}(?:وَ?{GAP})?{SEP}{GAP}(.+)$"
)
BARE_SERIAL_RE = re.compile(rf"^[\[(]\s*({NUM})\s*[\])]\s*[.]?$")
BRACKET_SEQ_START_RE = re.compile(
    rf"^[\[(]{GAP}({NUM}){GAP}[\])]{GAP}({NUM}){GAP}"
    rf"((?:عنه|وعن|وبإسناده|وبهذا|وفي).*)$"
)
BRACKET_DASH_SEQ_START_RE = re.compile(
    rf"^[\[(]{GAP}({NUM}){GAP}[\])]{GAP}{SEP}{GAP}({NUM}){GAP}(.+)$"
)

HEADING_RE = re.compile(
    rf"^(?:[\[(]?{NUM}[\])]?\s*{SEP}\s*)?(?:كتاب|باب|أبواب)\s"
)
COMMENTARY_RE = re.compile(
    r"^(?:بيان|أقول|توضيح|إيضاح|تبيين|تبيان|شرح|فالوجه|"
    r"فأما ما رواه|قال الشيخ|قال مصنف|ورواه)(?=[\s:：،\u200c]|$)"
)
APPARATUS_HEADING_RE = re.compile(
    r"^(?:مراجعنا في التعليق|رموزها|في تأييد المؤمن من اللّه|قد كنّا وعدنا ذيل حديث)"
)
CITATION_RE = re.compile(
    r"(?:^|[\s،(])(?:ج|ص|ح)\s*[0-9\u0660-\u0669\u06f0-\u06f9]+|"
    r"[0-9\u0660-\u0669\u06f0-\u06f9]+\s*:\s*"
    r"[0-9\u0660-\u0669\u06f0-\u06f9]+(?:\s*[/|]\s*[0-9\u0660-\u0669\u06f0-\u06f9]+)?"
)
# A space after «[N]» is usual but not guaranteed — some notes open
# directly with a quotation mark («[3]« قوله...»), so \s* not \s+. Safe
# because _match_footnote caps markers at 50 and screens out the
# bracket-serial hadith shapes first.
BRACKET_FOOTNOTE_RE = re.compile(rf"^\[\s*({NUM})\s*\]\s*[.:]?\s*(.+)$")
PAREN_FOOTNOTE_RE = re.compile(
    rf"^\(\s*({NUM})\s*\)\s*[.:]?\s+(?!{NUM}\s*(?:/|{SEP}\s))(.+)$"
)
DASH_FOOTNOTE_RE = re.compile(rf"^\*?\s*\u0640?\s*({NUM})\s*{SEP}\s*(.+)$")

NUMBER_BOUNDARY_RE = re.compile(
    rf"(?<!\])([.؟!»])\s+"
    rf"(?=(?:[\[(]\s*{NUM}\s*[\])]\s*)?{NUM}(?:\s*/\s*{NUM})?"
    rf"\s*(?:وَ?\s*)?[\u0640\-–—][\s])"
)
COMMENTARY_BOUNDARY_RE = re.compile(
    r"([.؟!»])\s+(?=(?:بيان|أقول|توضيح|إيضاح|تبيين)\s*[:：])"
)
INLINE_COMMENTARY_MARKER_BOUNDARY_RE = re.compile(
    rf"([\[(]\s*{NUM}\s*[\])])\s*(?="
    r"(?:\u0628\u064a\u0627\u0646|\u0623\u0642\u0648\u0644|\u062a\u0648\u0636\u064a\u062d|"
    r"\u0625\u064a\u0636\u0627\u062d|\u062a\u0628\u064a\u064a\u0646|\u062a\u0628\u064a\u0627\u0646)"
    r"\s*[:\uff1a])"
)
COMMENTARY_COLON_BOUNDARY_RE = re.compile(
    r"([:\uff1a])\s+(?="
    r"(?:\u0628\u064a\u0627\u0646|\u0623\u0642\u0648\u0644|\u062a\u0648\u0636\u064a\u062d|"
    r"\u0625\u064a\u0636\u0627\u062d|\u062a\u0628\u064a\u064a\u0646|\u062a\u0628\u064a\u0627\u0646)"
    r"\s*[:\uff1a])"
)
UNPUNCTUATED_COMMENTARY_BOUNDARY_RE = re.compile(
    r"\s+(?="
    r"(?:\u0628\u064a\u0627\u0646|\u062a\u0648\u0636\u064a\u062d|\u0625\u064a\u0636\u0627\u062d|"
    r"\u062a\u0628\u064a\u064a\u0646|\u062a\u0628\u064a\u0627\u0646|\u0634\u0631\u062d)"
    r"\s*[:\uff1a])"
)
END_OF_PART_BOUNDARY_RE = re.compile(
    r"\s+(?=\u0625\u0644\u0649\s+\u0647\u0646\u0627\s+\u062a\u0645)"
)
SECTION_BOUNDARY_RE = re.compile(
    rf"([.?!\u061f\u00bb])\s+(?=(?:[\[(]?{NUM}[\])]?\s*{SEP}\s*)?"
    r"(?:\u0643\u062a\u0627\u0628|\u0628\u0627\u0628|\u0623\u0628\u0648\u0627\u0628)\s)"
)
PAREN_SECTION_BOUNDARY_RE = re.compile(
    rf"([.?!\u061f\u00bb])\s+(?=\(?\s*(?:\u0643\u062a\u0627\u0628|\u0628\u0627\u0628|\u0623\u0628\u0648\u0627\u0628)(?:\s*{NUM})?\b)"
)
FOOTNOTE_MARKER_BEFORE_HADITH_RE = re.compile(
    rf"[\[(]\s*({NUM})\s*[\])]\s+"
    rf"({NUM}(?:{GAP}/{GAP}{NUM})?{GAP}{SEP}{GAP})"
)
NUMBERED_HADITH_BOUNDARY_RE = re.compile(
    rf"\s+(?={NUM}(?:{GAP}/{GAP}{NUM})?{GAP}(?:\u0648\u064e?{GAP})?"
    rf"{SEP}{GAP}(?:[\u0621-\u064a]{{1,12}}\s*[:\u060c]|"
    r"\u0645\u062d\u0645\u062f|\u0639\u0644\u064a|\u0623\u062e\u0628\u0631|"
    r"\u0627\u062e\u0628\u0631|\u062d\u062f\u062b|\u0648\u0639\u0646\u0647|"
    r"\u0639\u0646\u0647|\u0648\u0628\u0647\u0630\u0627|\u0648\u0628\u0625\u0633\u0646\u0627\u062f\u0647))"
)
NESTED_NUMBER_PREFIX_RE = re.compile(
    rf"(?<![0-9\u0660-\u0669\u06f0-\u06f9]){NUM}{GAP}"
    rf"(?:\u0648\u064e?{GAP})?{SEP}{GAP}(?={NUM}{GAP}(?:\u0648\u064e?{GAP})?{SEP}{GAP})"
)
PAGE_NUMBER_BEFORE_HADITH_RE = re.compile(
    rf"(?<![0-9\u0660-\u0669\u06f0-\u06f9]){NUM}\s+"
    rf"(?={NUM}{GAP}(?:\u0648\u064e?{GAP})?{SEP}{GAP})"
)
_INLINE_NUMBERED_VARIANT_PLAIN_RE = re.compile(
    rf"(?<![0-9\u0660-\u0669\u06f0-\u06f9])({NUM})\s+"
    r"(?=(?:(?:\u0648\s*)?\u0631\u0648\u0627\u0647|(?:\u0648\s*)?\u0641\u064a\s+\u0631\u0648\u0627\u064a\u0629))"
)
INLINE_FOOTNOTE_BODY_RE = re.compile(
    rf"([\[(]\s*({NUM})\s*[\])])(?="
    r"(?:\u0628\u0627\u0644|\u0647\u0648|\u062d\u0643\u0649|\u0644\u0645 \u0646\u0642\u0641|"
    r"\u0627\u0633\u0645\u0647|\u0627\u0644\u0635\u062d\u0641\u0649|"
    r"\s+(?:\u0647\u0648|\u062a\u0642\u062f\u0645|\u0641\u064a \u0627\u0644\u0643\u0646\u0632|"
    r"\u0641\u064a \u0646\u0633\u062e\u0629|\u0643\u0630\u0627)))"
)
HARAKAT_RE = re.compile(r"[\u064b-\u065f\u0670]")
PAREN_HEADING_RE = re.compile(
    r"^\(?\s*(?:\u0643\u062a\u0627\u0628|\u0628\u0627\u0628|\u0623\u0628\u0648\u0627\u0628)(?=[\s\)\uff09]|$)"
)
PLAIN_HEADING_RE = re.compile(
    r"^(?:(?:\u0643\u062a\u0627\u0628|\u0628\u0627\u0628|\u0623\u0628\u0648\u0627\u0628)(?:\s|$)|"
    r"\u062d\u062f\u064a\u062b\s+.{1,80}\s+\u0639$)"
)
APPARATUS_EXTRA_RE = re.compile(
    r"^(?:\*?\s*[\u00ab\"]?\s*\u0631\u0645\u0648\u0632\s+\u0627\u0644\u0643\u062a\u0627\u0628|"
    r"\u0627\u0644\u0645\u0648\u0636\u0648\u0639\s+\u0627\u0644\u0635\u0641(?:\u062d\u0629|\u064a\u0641\u0629)|"
    r"\u0625\u0644\u0649\s+\u0647\u0646\u0627\s+\u062a\u0645)"
)
BIHAR_APPARATUS_PAGE_RE = re.compile(
    r"^(?:\s*\*?\s*[\u00ab\"]?\s*\u0631\u0645\u0648\u0632\s*\u0627\u0644[\u0643\u06a9]\u062a\u0627\u0628|"
    r"\s*\u0627\u0644\u0645\u0648\u0636\u0648\u0639\s+\u0627\u0644\u0635\u0641(?:\u062d\u0629|\u064a\u0641\u0629)|"
    r"\s*\u0627\u0644\u0628\u0627\u0628\s+\u0627\u0644\u0639\u0646\u0648\u0627\u0646\s+\u0627\u0644\u0635\u0641\u062d\u0629|"
    r"\s*\u062a\u0639\u0631\u064a\u0641\s+\u0627\u0644\u0643\u062a\u0627\u0628|"
    r"\s*\u062e\u0637\u0628\u0629\s+\u0627\u0644\u0643\u062a\u0627\u0628|"
    r"\s*\u0627\u064a\u0646\s+\u0635\u0641\u062d\u0647\s+\u062f\u0631\s+\u0643\u062a\u0627\u0628|"
    r"\s*\u0647\u0630\u0647\s+\u0627\u0644\u0635\u0641\u062d\u0629\s+\u0641\u0627\u0631\u063a\u0629)"
)

SPEECH_RE = re.compile(
    r"(?:قَالَ|قَالَتْ|قال|قالت)"
    r"(?:\s*[:：]|\s+(?=سَمِعْتُ|سمعت|قُلْتُ|قلت|سَأَلْتُ|سألت|"
    r"كَتَبْتُ|كتبت|قَالَ|قال|فَقَالَ|فقال|يَقُولُ|يقول|لِي|لي|"
    r"أَبُو|أبو|أَبِي|أبي|أَمِيرُ|أمير|رَسُولُ|رسول|النَّبِيُّ|النبي|"
    r"عَلِيُّ|علي|الْحَسَنُ|الحسن|الْحُسَيْنُ|الحسين))"
)
ISNAD_HINT_RE = re.compile(
    r"عَنْ|عن |بْن|بن |حَدَّثَ|أَخْبَرَ|عِدَّة|رَوَى|روى|"
    r"رويته|بإسناده|بِإِسْنَادِهِ"
)

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

# Override the broad speech-boundary regex above with a UTF-8-stable version.
# It adds dual forms such as "قالا" and keeps the original common triggers.
SPEECH_RE = re.compile(
    r"(?:\u0642\u0627\u0644\u0627|\u0642\u064e\u0627\u0644\u064e\u0627|"
    r"\u0642\u0627\u0644\u062a|\u0642\u064e\u0627\u0644\u064e\u062a\u0652|"
    r"\u0642\u0627\u0644|\u0642\u064e\u0627\u0644\u064e|"
    r"\u0641\u0642\u0627\u0644|\u0641\u064e\u0642\u064e\u0627\u0644\u064e|"
    r"\u0642\u0644\u062a|\u0642\u064f\u0644\u0652\u062a\u064f|"
    r"\u0633\u0623\u0644\u062a|\u0633\u064e\u0623\u064e\u0644\u0652\u062a\u064f|"
    r"\u0633\u0645\u0639\u062a|\u0633\u064e\u0645\u0650\u0639\u0652\u062a\u064f|"
    r"\u0643\u062a\u0628\u062a|\u0643\u064e\u062a\u064e\u0628\u0652\u062a\u064f|"
    r"\u064a\u0642\u0648\u0644|\u064a\u064e\u0642\u064f\u0648\u0644\u064f)"
    r"(?:\s*[:\uff1a]|\s+)"
)
AN_REPORT_RE = re.compile(
    r"\s+(?:\u0623\u0646|\u0623\u0646\u0647|\u0623\u0646\u0647\u0627|"
    r"\u0627\u0646|\u0627\u0646\u0647|\u0627\u0646\u0647\u0627|\u0625\u0646)(?=\s)"
)
FI_REPORT_RE = re.compile(
    r"\s+(?=\u0641[\u064b-\u065f\u0670]*\u064a[\u064b-\u065f\u0670]*\s)"
)
TERMINAL_COLON_RE = re.compile(r"[:\uff1a]\s*")
TERMINAL_MARKER_RE = re.compile(
    r"(\u0639\u0644\u064a\u0647(?:\u0645\u0627|\u0645|\u0627)?(?:\s*\u0627\u0644\u0635\u0644\u0627\u0629)?\s*"
    r"\u0648?\s*\u0627\u0644\u0633\u0644\u0627\u0645|"
    r"\u0631\u0633\u0648\u0644\s+\u0627\u0644\u0644\u0647|\u0627\u0644\u0646\u0628\u064a|"
    r"\u0623\u0645\u064a\u0631\s+\u0627\u0644\u0645\u0624\u0645\u0646\u064a\u0646|"
    r"\u0627\u0644\u0635\u0627\u062f\u0642|\u0627\u0644\u0628\u0627\u0642\u0631|\u0627\u0644\u0631\u0636\u0627|"
    r"\u0623\u0628\u064a\s+\u0639\u0628\u062f\s+\u0627\u0644\u0644\u0647|\u0623\u0628\u064a\s+\u062c\u0639\u0641\u0631|"
    r"\u0623\u0628\u064a\s+\u0627\u0644\u062d\u0633\u0646|\u0643\u0644\u064a\u0647\u0645\u0627|"
    r"[789])"
)
STRONG_ISNAD_HINT_RE = re.compile(
    r"(?<![\u0621-\u064a])(?:\u0639\u0646)(?=\s)|"
    r"(?<![\u0621-\u064a])(?:\u062d\u062f\u062b|\u062d\u062f\u062b\u0646\u0627|\u062d\u062f\u062b\u0646\u064a|"
    r"\u0623\u062e\u0628\u0631|\u0627\u062e\u0628\u0631|\u0639\u062f\u0629\s+\u0645\u0646\s+\u0623\u0635\u062d\u0627\u0628\u0646\u0627|"
    r"\u0628\u0625\u0633\u0646\u0627\u062f\u0647|\u0631\u0648\u0649|\u0631\u0648\u0627\u0647|\u0631\u0648\u064a)(?![\u0621-\u064a])"
)

BIHAR_FIRST_HADITH_VOLUME = 1
BIHAR_FIRST_HADITH_PAGE = 82


@dataclass
class ParsedUnit:
    kind: str
    text: str
    number: str | None = None
    section_title: str | None = None
    sequence_in_page: int = 0


@dataclass
class ExtractionStats:
    books: int = 0
    pages: int = 0
    hadiths: int = 0
    continuations_merged: int = 0
    skipped_books: int = 0


def _digit_to_int_char(char: str) -> str:
    if char in ARABIC_DIGITS:
        return str(ARABIC_DIGITS.index(char))
    if char in PERSIAN_DIGITS:
        return str(PERSIAN_DIGITS.index(char))
    return char


def _to_int(value: str) -> int:
    return int("".join(_digit_to_int_char(ch) for ch in value if ch.isdigit()))


def _to_arabic_digits(value: str) -> str:
    western = "".join(_digit_to_int_char(ch) if ch.isdigit() else ch for ch in value)
    return "".join(ARABIC_DIGITS[int(ch)] if ch.isdigit() else ch for ch in western)


def _number_label(serial: str | None, sequence: str) -> str:
    seq = re.sub(r"\s+", " ", _to_arabic_digits(sequence)).strip()
    if not serial:
        return seq
    # A small bracketed marker immediately before a large report number is a
    # footnote anchor left by page flattening, not an outer hadith serial.
    if _is_footnote_marker(serial) and _to_int(sequence) > 50:
        return seq
    return f"{_to_arabic_digits(serial)} / {seq}"


def _is_footnote_marker(value: str) -> bool:
    try:
        return _to_int(value) <= 50
    except ValueError:
        return False


def _is_heading(line: str) -> bool:
    # Keep tatweel because many editions use it as the printed separator in
    # headings, e.g. "١ ـ باب ...".
    plain = HARAKAT_RE.sub("", line).replace("\u200c", " ").strip()
    return bool(
        HEADING_RE.match(plain)
        or PAREN_HEADING_RE.match(plain)
        or PLAIN_HEADING_RE.match(plain)
    )


_EDITORIAL_COMMENTARY_PREFIXES = (
    "\u0642\u0648\u0644\u0647",  # قوله
    "\u0648 \u0642\u0648\u0644\u0647",  # و قوله
    "\u0648\u0642\u0648\u0644\u0647",  # وقوله
    "\u0648 \u0627\u0639\u0644\u0645",  # و اعلم
    "\u0648\u0627\u0639\u0644\u0645",  # واعلم
    "\u0647\u0643\u0630\u0627",  # هكذا
    "\u0642\u064a\u0644",  # قيل
    "\u0623\u064a ",  # أي
    "\u0627\u0644\u0645\u0631\u0627\u062f",  # المراد
    "\u064a\u0639\u0646\u064a",  # يعني
    "\u0627\u0644\u0638\u0627\u0647\u0631",  # الظاهر
    "\u0641\u064a \u0628\u0639\u0636 \u0627\u0644\u0646\u0633\u062e",  # في بعض النسخ
    "\u0642\u0627\u0644 \u0627\u0644\u0641\u064a\u0636",  # قال الفيض
    "\u0642\u0627\u0644 \u0627\u0644\u0645\u062c\u0644\u0633\u064a",  # قال المجلسي
    "\u0627\u0644\u062d\u0635\u0631",  # الحصر
    "\u0627\u0644\u0639\u0646\u0643\u0628\u0648\u062a:",  # العنكبوت:
    "\u0647\u0648\u062f:",  # هود:
    "\u062b\u0642\u0641\u0647",  # ثقفه
    "\u0644\u0647\u0645\u0627 \u0645\u0646\u0639\u0647",  # لهما منعه
    "\u0639\u0644\u064a\u0647 \u0623\u062c\u0631\u0627",  # عليه أجرا
    "\u0648 \u0627\u0646 \u062a\u0637\u0626\u0648\u0627",  # و ان تطئوا
    "\u0648 \u0623\u0646 \u062a\u0646\u062a\u0638\u0631\u0648\u0627",  # و أن تنتظروا
    "\u0642\u0627\u0644: \u0648 \u0627\u0644\u0646\u0641\u0627\u0642 \u0639\u0644\u0649 \u0623\u0631\u0628\u0639",  # continuation
    "\u0642\u062f \u0642\u0627\u0644 \u0627\u0644\u0646\u0628\u064a",  # continuation
    "\u0631\u0648\u0627\u0647 \u0645\u0636\u0645\u0631\u0627",  # editorial: رواه مضمرا
    "\u0648 \u0627\u0644\u0645\u0642\u0631\u0628\u0629",  # editorial: و المقربة
)


def _is_editorial_commentary_body(text: str) -> bool:
    plain = strip_diacritics(text).strip()
    return any(plain.startswith(prefix) for prefix in _EDITORIAL_COMMENTARY_PREFIXES)


def _plain_text_with_raw_map(text: str) -> tuple[str, list[int]]:
    """Strip Arabic marks while retaining the source index of every character."""
    plain: list[str] = []
    mapping: list[int] = []
    for index, char in enumerate(text):
        # Tatweel doubles as a printed number separator (``١ ـ ...``), so it
        # must survive even though normal search normalisation removes it.
        stripped = char if char == "\u0640" else strip_diacritics(char)
        if not stripped:
            continue
        plain.append(stripped)
        mapping.append(index)
    return "".join(plain), mapping


def _insert_numbered_variant_boundaries(text: str) -> str:
    """Restore numbered ``ورواه`` routes printed without a dash.

    Work on a diacritic-free shadow string while applying the two insertions
    (newline before the serial, dash after it) to the untouched source text.
    """
    plain, mapping = _plain_text_with_raw_map(text)
    if not plain:
        return text

    edits: list[tuple[int, str]] = []
    for match in _INLINE_NUMBERED_VARIANT_PLAIN_RE.finditer(plain):
        # These dashless variant routes use the chapter-local hadith number.
        # Large numbers here are page/citation references inside apparatus
        # (for example ``414 في رواية أخرى``), not report boundaries.
        if _to_int(match.group(1)) > 50:
            continue
        if match.start() > 0 and plain[match.start() - 1] != "\n":
            edits.append((mapping[match.start()], "\n"))
        edits.append((mapping[match.end(1) - 1] + 1, "-"))
    for position, insertion in sorted(edits, key=lambda item: item[0], reverse=True):
        text = text[:position] + insertion + text[position:]
    return text


# Takhrij apparatus: «* (٢٢) الاستبصار ج ١ ص ٨٢ الكافي ج ١ ص ١٢...» — the
# editor's per-hadith cross-references in Tahdhib/Istibsar. The leading «*»
# is a reliable signal; the marker is the hadith's own printed serial (can
# exceed the ≤50 footnote-marker cap) and refers to the numbered hadith, not
# to an inline anchor. These runs sit INLINE at the end of text lines (even
# mid-hadith when a page boundary interrupts), so they are stripped as spans
# from the whole page text, not matched per line.
def _skip_page_for_hadith_index(source_book_id: str, page: Page) -> bool:
    if source_book_id != BIHAR_DAR_IHYA_SOURCE_BOOK_ID:
        return False
    volume = page.volume_number or 0
    if volume < BIHAR_FIRST_HADITH_VOLUME:
        return True
    if volume == BIHAR_FIRST_HADITH_VOLUME and page.page_number < BIHAR_FIRST_HADITH_PAGE:
        return True
    plain = strip_diacritics(page.text_raw or "").strip()
    if BIHAR_APPARATUS_PAGE_RE.match(plain):
        return True
    if "\u0631\u0645\u0648\u0632" in plain[:500] and re.search(
        r"\u0631\u0645\u0648\u0632\s*\u0627\u0644[\u0643\u06a9]\u062a\u0627\u0628", plain[:500]
    ):
        return True
    if "\u0641\u0647\u0631\u0633" in plain[:300]:
        return True
    if plain.startswith("\u0627\u0644\u0628\u0627\u0628 ") and plain[:1000].count("\u0627\u0644\u0628\u0627\u0628") >= 3:
        return True
    return False


TAKHRIJ_START_RE = re.compile(rf"\*\s*[\[(]\s*({NUM})\s*[\])]")
_CITE_TOKEN_RE = re.compile(rf"[\[(]\s*{NUM}\s*[\])]|[جص]\s*{NUM}|{NUM}")
_LOOSE_MARKER_RE = re.compile(rf"^[\[(]\s*({NUM})\s*[\])]\s*[.:]?\s*(.+)$")
_TAKHRIJ_BODY_RE = re.compile(rf"ج\s*{NUM}(?:\s*ص\s*{NUM})?")


def _strip_takhrij(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Remove takhrij spans from page text; return (clean_text, notes).

    A span starts at «* (N)» and extends over the run of citation tokens
    (numbers, «ج N», «ص N», serials) with short connective gaps («واخرج
    الأول الكليني في», «بتفاوت يسير»), absorbing a trailing sentence closer.
    Whatever follows (often the hadith's own continuation after a page
    break) is left in place.
    """
    notes: list[tuple[str, str]] = []
    out: list[str] = []
    pos = 0
    for match in TAKHRIJ_START_RE.finditer(text):
        if match.start() < pos:
            continue
        end = match.end()
        scan = end
        while True:
            nxt = _CITE_TOKEN_RE.search(text, scan)
            if not nxt or nxt.start() - scan > 45 or "\n" in text[scan : nxt.start()]:
                break
            end = nxt.end()
            scan = end
        closer = text.find(".", end)
        if closer != -1 and closer - end <= 40 and "\n" not in text[end:closer]:
            end = closer + 1
        body = text[match.start() : end].lstrip("* ").strip()
        notes.append((match.group(1), body))
        out.append(text[pos : match.start()])
        pos = end
    out.append(text[pos:])
    return "".join(out), notes

# A fihrist (index) heading opens the volume's table of contents; the
# numbered lines that follow are index entries, not hadiths.
FIHRIST_RE = re.compile(
    r"^(?:(?:\u0627\u0644)?\u0641\u0647\u0631\u0633\u062a?|"
    r"\u0627\u0644\u0645\u0648\u0636\u0648\u0639\s+\u0627\u0644\u0635\u0641\u062d\u0629)\b"
)


def _match_footnote(line: str, saw_hadith: bool) -> tuple[str, str] | None:
    """Return (marker, body) when the line is a footnote, else None.

    A bracket-opening line is only *hadith* text when it matches the exact
    bracket-serial shapes the parser recognises (BRACKET_SEQ/BRACKET_DASH,
    e.g. Wasa'il-style «[123] 5- عنه عن...»). Anything else numbered after a
    hadith was seen is edition apparatus. (An earlier heuristic instead kept
    any bracket line whose body mentioned عن/بن — but ordinary commentary
    prose contains those words constantly, so whole footnotes leaked into
    hadith texts, e.g. al-Kafi v1 p81 notes [3]/[4].)
    """
    if not saw_hadith:
        return None
    bracket = BRACKET_FOOTNOTE_RE.match(line)
    if bracket and _is_footnote_marker(bracket.group(1)):
        if BRACKET_SEQ_START_RE.match(line) or BRACKET_DASH_SEQ_START_RE.match(line):
            return None
        return bracket.group(1), bracket.group(2)
    paren = PAREN_FOOTNOTE_RE.match(line)
    if paren and _is_footnote_marker(paren.group(1)):
        return paren.group(1), paren.group(2)
    # Takhrij continuation lines: «(١٢٣) الاستبصار ج ١ ص ٨٣...» — only the
    # first entry of a page's takhrij block carries the «*», the rest are
    # bare-numbered with serials that can exceed the ≤50 marker cap. The
    # «ج N [ص N]» citation shape near the start is the tell.
    loose = _LOOSE_MARKER_RE.match(line)
    if loose and _TAKHRIJ_BODY_RE.search(loose.group(2)[:90]):
        return loose.group(1), loose.group(2)
    dash = DASH_FOOTNOTE_RE.match(line)
    if dash and len(dash.group(2)) < 180 and CITATION_RE.search(dash.group(2)):
        return dash.group(1), dash.group(2)
    return None


def _insert_inline_boundaries(text: str) -> str:
    # A page/verse number can be flattened directly before the real printed
    # marker (``15- 9-``). It is never a legitimate two-number hadith label;
    # remove the outer artefact before boundary detection.
    text = NESTED_NUMBER_PREFIX_RE.sub("\n", text)
    text = PAGE_NUMBER_BEFORE_HADITH_RE.sub("\n", text)
    text = NUMBER_BOUNDARY_RE.sub(r"\1\n", text)
    text = NUMBERED_HADITH_BOUNDARY_RE.sub("\n", text)
    text = _insert_numbered_variant_boundaries(text)
    text = COMMENTARY_BOUNDARY_RE.sub(r"\1\n", text)
    text = INLINE_COMMENTARY_MARKER_BOUNDARY_RE.sub(r"\1\n", text)
    text = COMMENTARY_COLON_BOUNDARY_RE.sub(r"\1\n", text)
    text = UNPUNCTUATED_COMMENTARY_BOUNDARY_RE.sub("\n", text)
    text = END_OF_PART_BOUNDARY_RE.sub("\n", text)
    text = SECTION_BOUNDARY_RE.sub(r"\1\n", text)
    text = PAREN_SECTION_BOUNDARY_RE.sub(r"\1\n", text)

    def marker_before_hadith(match: re.Match) -> str:
        if _is_footnote_marker(match.group(1)):
            return "\n" + match.group(2)
        return match.group(0)

    text = FOOTNOTE_MARKER_BEFORE_HADITH_RE.sub(marker_before_hadith, text)
    return INLINE_FOOTNOTE_BODY_RE.sub(r"\1\n\1", text)


def _valid_isnad_prefix(
    isnad: str,
    matn: str,
    *,
    max_len: int = 900,
    require_strong_hint: bool = False,
) -> bool:
    if len(isnad) > max_len or not matn:
        return False
    plain = strip_diacritics(isnad)
    hint_re = STRONG_ISNAD_HINT_RE if require_strong_hint else ISNAD_HINT_RE
    return bool(hint_re.search(plain))


def _has_terminal_marker(text: str) -> bool:
    return bool(TERMINAL_MARKER_RE.search(strip_diacritics(text)[-220:]))


def _has_recent_terminal_marker(text: str, *, max_gap: int = 24) -> bool:
    plain = strip_diacritics(text)
    return any(len(plain) - match.end() <= max_gap for match in TERMINAL_MARKER_RE.finditer(plain))


def _has_recent_terminal_chain_marker(text: str, *, max_gap: int = 80) -> bool:
    plain = strip_diacritics(text)
    for match in TERMINAL_MARKER_RE.finditer(plain):
        if len(plain) - match.end() > max_gap:
            continue
        lead = plain[max(0, match.start() - 60) : match.start()]
        if re.search(r"(?:^|[^\u0621-\u064a])(?:\u0639\u0646|\u0625\u0644\u0649|\u0627\u0644\u0649|\u0627\u0644\u064a)\s*$", lead):
            return True
    return False


def _strong_hint_count(text: str) -> int:
    return len(STRONG_ISNAD_HINT_RE.findall(strip_diacritics(text)))


def _split_on_intro(
    flattened: str,
    pattern: re.Pattern,
    *,
    before: int | None = None,
    max_prefix_len: int = 900,
    require_terminal: bool = False,
    terminal_max_gap: int = 24,
    min_strong_hints: int = 1,
) -> tuple[str, str] | None:
    for match in pattern.finditer(flattened):
        if before is not None and match.start() >= before:
            return None
        isnad = flattened[: match.start()].strip()
        matn = flattened[match.start() :].strip()
        if require_terminal and not _has_recent_terminal_marker(isnad, max_gap=terminal_max_gap):
            continue
        if _strong_hint_count(isnad) < min_strong_hints:
            continue
        if _valid_isnad_prefix(
            isnad,
            matn,
            max_len=max_prefix_len,
            require_strong_hint=require_terminal,
        ):
            return isnad, matn
    return None


def _split_on_terminal_colon(flattened: str, before: int | None = None) -> tuple[str, str] | None:
    for match in TERMINAL_COLON_RE.finditer(flattened):
        if before is not None and match.start() >= before:
            return None
        isnad = flattened[: match.end()].strip()
        matn = flattened[match.end() :].strip()
        if _has_recent_terminal_chain_marker(isnad, max_gap=80) and _valid_isnad_prefix(
            isnad, matn, max_len=700, require_strong_hint=True
        ):
            return isnad, matn
    return None


def _split_on_terminal_speech(flattened: str) -> tuple[str, str] | None:
    for match in SPEECH_RE.finditer(flattened):
        isnad = flattened[: match.end()].strip()
        matn = flattened[match.end() :].strip()
        if _has_recent_terminal_chain_marker(isnad, max_gap=80) and _valid_isnad_prefix(
            isnad,
            matn,
            max_len=1600,
            require_strong_hint=True,
        ):
            return isnad, matn
    return None


def split_isnad_matn(text: str) -> tuple[str | None, str]:
    """Best-effort split of a hadith into chain and report body.

    The raw full text remains authoritative; this split is reviewable
    extracted metadata.
    """
    flattened = re.sub(r"\s+", " ", text).strip()
    match = SPEECH_RE.search(flattened)
    boundary = match.start() if match else None
    for split in (
        _split_on_terminal_speech(flattened),
        _split_on_terminal_colon(flattened),
        _split_on_intro(
            flattened,
            AN_REPORT_RE,
            before=boundary,
            max_prefix_len=500,
            min_strong_hints=2,
        ),
        _split_on_intro(
            flattened,
            FI_REPORT_RE,
            before=boundary,
            max_prefix_len=700,
            require_terminal=True,
            terminal_max_gap=24,
        ),
    ):
        if split is not None:
            return split

    if not match:
        for split in (
            _split_on_terminal_speech(flattened),
            _split_on_terminal_colon(flattened),
            _split_on_intro(flattened, AN_REPORT_RE, max_prefix_len=500, min_strong_hints=2),
            _split_on_intro(
                flattened,
                FI_REPORT_RE,
                max_prefix_len=700,
                require_terminal=True,
                terminal_max_gap=24,
            ),
        ):
            if split is not None:
                return split
        return None, flattened

    end = match.end()
    isnad = flattened[:end].strip()
    matn = flattened[end:].strip()
    if not _valid_isnad_prefix(isnad, matn):
        for split in (
            _split_on_terminal_speech(flattened),
            _split_on_terminal_colon(flattened),
            _split_on_intro(flattened, AN_REPORT_RE, max_prefix_len=500, min_strong_hints=2),
            _split_on_intro(
                flattened,
                FI_REPORT_RE,
                max_prefix_len=700,
                require_terminal=True,
                terminal_max_gap=24,
            ),
        ):
            if split is not None:
                return split
        return None, flattened

    return isnad, matn


class PageHadithParser:
    def __init__(
        self,
        initial_section: str | None = None,
        initial_in_fihrist: bool = False,
        initial_saw_hadith: bool = False,
    ) -> None:
        self.units: list[ParsedUnit] = []
        self.pending_serial: str | None = None
        # Carried from the previous page of the same volume so hadiths keep
        # their باب title across page boundaries (headings only print once).
        self.current_section: str | None = initial_section
        # Seeded True when the previous page ended inside a hadith: a page
        # that is entirely mid-hadith (no new number anywhere on it) must
        # yield continuation units, or long hadiths silently lose their
        # middle pages (al-Kafi v8 h1 spans p2-14; only ~9% of its text
        # survived before this was seeded).
        self.saw_hadith = initial_saw_hadith
        self.sequence_in_page = 0
        self.in_apparatus = False
        # The volume's trailing index: numbered lines there («٥ ـ طهور
        # الماء.») are TOC entries, not hadiths. Carried across index pages.
        self.in_fihrist = initial_in_fihrist

    def _append_to_previous(self, text: str) -> None:
        if not self.units:
            self.units.append(ParsedUnit(kind="text", text=text, section_title=self.current_section))
            return
        previous = self.units[-1]
        if previous.kind in {"hadith", "continuation", "text", "footnote"}:
            previous.text = f"{previous.text}\n{text}".strip()
        else:
            self.units.append(ParsedUnit(kind="text", text=text, section_title=self.current_section))

    def _add_hadith(self, number: str, body: str) -> None:
        self.sequence_in_page += 1
        self.saw_hadith = True
        self.units.append(
            ParsedUnit(
                kind="hadith",
                number=number,
                text=body.strip(),
                section_title=self.current_section,
                sequence_in_page=self.sequence_in_page,
            )
        )

    def add_line(self, line: str) -> None:
        line = line.strip()
        if not line:
            return

        if FIHRIST_RE.match(strip_diacritics(line)):
            self.in_fihrist = True
            self.units.append(ParsedUnit(kind="heading", text=line, section_title=self.current_section))
            return

        if _is_heading(line):
            if not self.in_fihrist:
                # Inside the index, «باب طهور الماء ٥» is a TOC line quoting
                # a heading, not a new section.
                self.current_section = line
            self.units.append(ParsedUnit(kind="heading", text=line, section_title=self.current_section))
            return

        footnote = _match_footnote(line, self.saw_hadith)
        if footnote is not None:
            marker, body = footnote
            self.units.append(
                ParsedUnit(
                    kind="footnote", number=marker, text=body, section_title=self.current_section
                )
            )
            return

        plain_line = strip_diacritics(line)
        if APPARATUS_HEADING_RE.match(plain_line) or APPARATUS_EXTRA_RE.match(plain_line):
            self.units.append(ParsedUnit(kind="commentary", text=line, section_title=self.current_section))
            self.in_apparatus = True
            return

        if self.in_apparatus or self.in_fihrist:
            self.units.append(ParsedUnit(kind="commentary", text=line, section_title=self.current_section))
            return

        if COMMENTARY_RE.match(strip_diacritics(line)):
            self.units.append(ParsedUnit(kind="commentary", text=line, section_title=self.current_section))
            return

        bare_serial = BARE_SERIAL_RE.match(line)
        if bare_serial:
            if self.saw_hadith and line.rstrip().endswith("."):
                self.units.append(
                    ParsedUnit(
                        kind="footnote",
                        number=bare_serial.group(1),
                        text="",
                        section_title=self.current_section,
                    )
                )
            else:
                self.pending_serial = bare_serial.group(1)
            return

        bracket_dash = BRACKET_DASH_SEQ_START_RE.match(line)
        if bracket_dash:
            self._add_hadith(_number_label(bracket_dash.group(1), bracket_dash.group(2)), bracket_dash.group(3))
            self.pending_serial = None
            return

        bracket_seq = BRACKET_SEQ_START_RE.match(line)
        if bracket_seq:
            self._add_hadith(_number_label(bracket_seq.group(1), bracket_seq.group(2)), bracket_seq.group(3))
            self.pending_serial = None
            return

        hadith_start = HADITH_START_RE.match(line)
        if hadith_start:
            serial = hadith_start.group(1) or self.pending_serial
            body = hadith_start.group(3)
            if _is_heading(body):
                self.current_section = body.strip()
                self.units.append(
                    ParsedUnit(kind="heading", text=body.strip(), section_title=self.current_section)
                )
                self.pending_serial = None
                return
            if _is_editorial_commentary_body(body):
                # Numbered verse/page references in the edition's footnotes
                # can look exactly like hadith markers after HTML flattening.
                # Keep them as apparatus and do not let them become the page's
                # final hadith for cross-page continuation state.
                self.units.append(
                    ParsedUnit(
                        kind="footnote",
                        number=hadith_start.group(2),
                        text=body.strip(),
                        section_title=self.current_section,
                    )
                )
                self.pending_serial = None
                return
            if not serial and len(body) < 160 and CITATION_RE.search(body):
                self._append_to_previous(line)
                return
            self._add_hadith(_number_label(serial, hadith_start.group(2)), body)
            self.pending_serial = None
            return

        if not self.saw_hadith:
            self.units.append(ParsedUnit(kind="text", text=line, section_title=self.current_section))
            return

        self._append_to_previous(line)

    def finalise(self) -> list[ParsedUnit]:
        if not self.saw_hadith:
            return self.units
        for unit in self.units:
            if unit.kind in {"hadith", "heading"}:
                # A heading closes the previous hadith — prose after it is
                # the new bab's introduction, not a continuation.
                break
            if unit.kind == "commentary":
                continue
            if unit.kind == "text" and len(unit.text.strip()) > 20:
                unit.kind = "continuation"
        return self.units


_INLINE_MARKER_TEMPLATE = r"[\[(]\s*(?:{variants})\s*[\])]"


def _inline_marker_re(marker: str) -> re.Pattern:
    """Regex matching the in-text anchor of a footnote marker, in either
    digit system («[4]», «[٤]», «(4)»…)."""
    western = "".join(_digit_to_int_char(ch) for ch in marker if ch.isdigit())
    variants = {re.escape(western), re.escape(_to_arabic_digits(western))}
    return re.compile(_INLINE_MARKER_TEMPLATE.format(variants="|".join(variants)))


def parse_page_state(
    text_raw: str,
    *,
    initial_section: str | None = None,
    initial_in_fihrist: bool = False,
    initial_saw_hadith: bool = False,
) -> tuple[list[ParsedUnit], "PageHadithParser"]:
    """Parse one page, seeding cross-page state (section title, fihrist flag,
    mid-hadith flag) carried from the previous page of the same volume.
    Returns the units and the parser so the caller can carry its end-of-page
    state forward."""
    text = text_raw.replace("\r\n", " ").replace("\r", " ")
    text, takhrij_notes = _strip_takhrij(text)
    text = _insert_inline_boundaries(text).strip()
    parser = PageHadithParser(
        initial_section=initial_section,
        initial_in_fihrist=initial_in_fihrist,
        initial_saw_hadith=initial_saw_hadith,
    )
    for line in re.split(r"\n+", text):
        parser.add_line(line)
    units = parser.finalise()
    for marker, body in takhrij_notes:
        units.append(ParsedUnit(kind="footnote", number=marker, text=body))
    return units, parser


def parse_page_text(text_raw: str) -> list[ParsedUnit]:
    units, _parser = parse_page_state(text_raw)
    return units


def _public_id(source_book_id: str, sequence_in_book: int) -> str:
    """Citable hadith ID: book slug + running number in the book
    («alkafi-2041»). Deterministic for a given extraction of the corpus;
    `extraction_method` records the parser version behind the numbering."""
    return f"{book_slug(source_book_id)}-{sequence_in_book}"


def _confidence_for(full_text: str, isnad: str | None, matn: str) -> int:
    confidence = 80
    if isnad and matn != full_text:
        confidence += 10
    if len(full_text) < 40:
        confidence -= 15
    return max(40, min(confidence, 95))


def _append_continuation(hadith: Hadith, text: str, page: Page) -> None:
    hadith.full_text_raw = f"{hadith.full_text_raw}\n{text}".strip()
    hadith.full_text_normalised = normalise_arabic_persian(hadith.full_text_raw)
    # Re-split on the merged text: when a page boundary cuts the chain
    # mid-isnad (e.g. al-Kafi v1 h6, «عن أبي سعيد | الزهري عن...»), the split
    # on the first page's fragment rightly failed — but it can succeed now.
    isnad, matn = split_isnad_matn(hadith.full_text_raw)
    hadith.isnad_raw = isnad
    hadith.isnad_normalised = normalise_arabic_persian(isnad) if isnad else None
    hadith.matn_raw = matn
    hadith.matn_normalised = normalise_arabic_persian(matn)
    hadith.page_end_id = page.id
    hadith.volume_end = page.volume_number
    hadith.page_end = page.page_number


def rebuild_hadith_index(
    db: Session,
    *,
    source_book_ids: tuple[str, ...] | list[str] | None = None,
    book_ids: list[int] | None = None,
    include_excluded_editions: bool = False,
    commit: bool = True,
) -> ExtractionStats:
    """Rebuild hadith rows for selected books from existing page text."""
    selected_source_ids = tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)
    query = db.query(Book)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    elif selected_source_ids:
        query = query.filter(Book.source_book_id.in_(selected_source_ids))

    if not include_excluded_editions:
        query = query.filter(~Book.source_book_id.in_(CATALOG_EXCLUDED_SOURCE_BOOK_IDS))

    books = query.order_by(Book.id).all()
    stats = ExtractionStats()
    if not books:
        return stats

    book_id_values = [book.id for book in books]
    db.execute(delete(Hadith).where(Hadith.book_id.in_(book_id_values)))
    db.flush()

    for book in books:
        stats.books += 1
        sequence_in_book = 0
        volume_ordinal = 0
        # Transient hadith -> its ordinal within the current volume; takhrij
        # serials number hadiths per volume, so this is the attribution key.
        ordinals: dict[int, int] = {}
        last_hadith: Hadith | None = None
        last_volume: int | None = None
        carried_section: str | None = None
        carried_in_fihrist = False
        # A page-opening text block is only a continuation of the previous
        # hadith when the previous page actually *ended* inside one — if it
        # ended in commentary (بيان/apparatus), appending would contaminate
        # the matn with the commentator's words.
        prev_page_ended_in_hadith = False
        pages = (
            db.query(Page)
            .filter(Page.book_id == book.id, Page.text_raw.isnot(None))
            .order_by(Page.volume_number, Page.page_number, Page.id)
            .all()
        )
        for page in pages:
            if not page.text_raw or not page.text_raw.strip():
                continue
            if last_volume is not None and page.volume_number != last_volume:
                last_hadith = None
                carried_section = None
                carried_in_fihrist = False
                prev_page_ended_in_hadith = False
                volume_ordinal = 0
                ordinals.clear()
            last_volume = page.volume_number
            if _skip_page_for_hadith_index(book.source_book_id, page):
                last_hadith = None
                carried_section = None
                carried_in_fihrist = False
                prev_page_ended_in_hadith = False
                continue
            stats.pages += 1
            units, parser = parse_page_state(
                page.text_raw,
                initial_section=carried_section,
                initial_in_fihrist=carried_in_fihrist,
                initial_saw_hadith=prev_page_ended_in_hadith,
            )
            carried_section = parser.current_section
            carried_in_fihrist = parser.in_fihrist
            # (page-chunk text, hadith) pairs — a footnote's inline anchor
            # («ابن مسكان[4]») identifies which hadith on this page owns it.
            page_targets: list[tuple[str, Hadith]] = []
            for unit in units:
                if unit.kind == "continuation":
                    if last_hadith is not None and prev_page_ended_in_hadith:
                        _append_continuation(last_hadith, unit.text, page)
                        page_targets.append((unit.text, last_hadith))
                        stats.continuations_merged += 1
                    continue
                if unit.kind != "hadith":
                    continue

                sequence_in_book += 1
                isnad, matn = split_isnad_matn(unit.text)
                hadith = Hadith(
                    public_id=_public_id(book.source_book_id, sequence_in_book),
                    book_id=book.id,
                    page_start_id=page.id,
                    page_end_id=page.id,
                    sequence_in_book=sequence_in_book,
                    sequence_in_page=unit.sequence_in_page,
                    printed_number=unit.number,
                    volume_start=page.volume_number,
                    volume_end=page.volume_number,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    section_title=unit.section_title,
                    full_text_raw=unit.text,
                    full_text_normalised=normalise_arabic_persian(unit.text),
                    isnad_raw=isnad,
                    isnad_normalised=normalise_arabic_persian(isnad) if isnad else None,
                    matn_raw=matn,
                    matn_normalised=normalise_arabic_persian(matn),
                    source_url=page.source_url,
                    extraction_method="regex_v1",
                    extraction_confidence=_confidence_for(unit.text, isnad, matn),
                    review_status="pending",
                )
                db.add(hadith)
                page_targets.append((unit.text, hadith))
                volume_ordinal += 1
                ordinals[id(hadith)] = volume_ordinal
                last_hadith = hadith
                stats.hadiths += 1

            for unit in units:
                if unit.kind != "footnote" or not unit.number:
                    continue
                anchor = _inline_marker_re(unit.number)
                target: Hadith | None = None
                for chunk, hadith in page_targets:
                    if anchor.search(chunk):
                        target = hadith
                        break
                if target is None:
                    # Takhrij markers are per-volume hadith serials, not
                    # inline anchors — match against the volume ordinal,
                    # falling back to the printed number's own groups.
                    try:
                        marker_value = _to_int(unit.number)
                    except ValueError:
                        marker_value = None
                    if marker_value is not None:
                        for _chunk, hadith in page_targets:
                            if ordinals.get(id(hadith)) == marker_value:
                                target = hadith
                                break
                        if target is None:
                            for _chunk, hadith in page_targets:
                                groups = re.findall(
                                    r"[0-9٠-٩۰-۹]+", hadith.printed_number or ""
                                )
                                if any(_to_int(g) == marker_value for g in groups):
                                    target = hadith
                                    break
                if target is not None:
                    notes = list(target.footnotes_json or [])
                    notes.append(
                        {
                            "marker": unit.number,
                            "text": unit.text,
                            "volume": page.volume_number,
                            "page": page.page_number,
                        }
                    )
                    target.footnotes_json = notes

            # Did this page end inside a hadith? (Footnotes trail the page
            # regardless, so they don't count.)
            for unit in reversed(units):
                if unit.kind == "footnote":
                    continue
                prev_page_ended_in_hadith = unit.kind in {"hadith", "continuation"}
                break

        db.flush()

    if commit:
        db.commit()
    return stats
