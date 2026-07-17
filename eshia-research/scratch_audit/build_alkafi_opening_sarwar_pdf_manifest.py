"""Build a source-pinned Muhammad Sarwar manifest for Al-Kafi reports 1-34.

This utility is intentionally narrow.  It reads the alternating English
column in the published Volume 1 PDF with PyMuPDF blocks, removes only layout
whitespace and adjacent Arabic/PUA extraction contamination, and splits the
printed English chain from the quoted matn.  It does not translate, paraphrase,
or silently fall back to another English source.

The Thaqalayn API snapshot is used only to verify report identity and the
explicit translator attribution.  English publication text always comes from
the checksum-pinned Muhammad Sarwar PDF.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pymupdf
from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text


EXPECTED_COUNT = 34
SOURCE_BOOK_ID = "11005"
PDF_SHA256 = "969ff47af5fe9d0bf6ca542aa11f2d27130437b156448ee9cb4b141ba2f1d41a"
API_SNAPSHOT_SHA256 = "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
PDF_SOURCE_URL = (
    "https://al-murtaza.org/wp-content/uploads/2021/08/Al-Kafi_Volume-1.pdf"
)
API_SOURCE_URL = (
    "https://www.thaqalayn-api.net/api/v2/Al-Kafi-Volume-1-Kulayni"
)
EXTRACTION_VERSION = "alkafi_opening_sarwar_pdf_blocks_v1"
CLASSIFICATION = "verbatim_external_matn_excerpt"
TARGET_PROVIDER = "sarwar-published-scan"
TARGET_MODEL = "muhammad-sarwar-published"
MIN_ARABIC_IDENTITY_SCORE = 0.90
MIN_ENGLISH_CHAIN_TOKEN_F1 = 0.60

DEFAULT_PDF = Path(
    os.path.expandvars(r"%TEMP%\sarwar-alkafi-almurtaza\volume-1.pdf")
)
DEFAULT_API_SNAPSHOT = Path(
    os.path.expandvars(r"%TEMP%\sarwar-alkafi-audit\thaqalayn-api-alkafi.json")
)
DEFAULT_OUTPUT = Path(__file__).with_name(
    "alkafi_opening_sarwar_pdf_manifest_20260716.json"
)

SPACE_RE = re.compile(r"\s+")
LATIN_RE = re.compile(r"[A-Za-z]")
ARABIC_OR_PUA_RE = re.compile(
    "["
    "\u0600-\u06ff"
    "\u0750-\u077f"
    "\u08a0-\u08ff"
    "\ufb50-\ufdff"
    "\ufe70-\ufeff"
    "\ue000-\uf8ff"
    "]"
)
PDF_MARKER_RE = re.compile(
    r"(?i)(?:"
    r"\bH\s*(?P<hadith>\d+)\s*,\s*C(?:h|H)\.?\s*[^,\n]+,\s*h\s*[^\s]+"
    r"|\bHadith\s+(?P<first>1)\s*,\s*Chapter\s+1\s*,\s*hadith\s+1"
    r")"
)
H1_CHAIN_LABEL_RE = re.compile(
    r"^\s*\(The Bearers of this Hadith in consecutive order\):\s*"
)
H1_MATN_LABEL = "(The Text of this Hadith):"
OPEN_QUOTE = "\u201c"
CLOSE_QUOTE = "\u201d"

FORBIDDEN_SOURCE_MARKERS = (
    "hubeali.com",
    "(azwj)",
    "(saww)",
    "(asws)",
    "as an ai",
    "codex",
    "openai",
    "gpt-",
)

# These two reports are deliberately routed through explicit evidence checks
# because their older PDF chain wording is less similar to the modern API
# wording than the surrounding reports.  No other report receives an override.
MANUAL_IDENTITY_EVIDENCE: dict[int, dict[str, Any]] = {
    14: {
        "reason": (
            "Long report spanning the alternating columns on PDF pages 20-22; "
            "the PDF and API chains independently name Ahmad ibn Muhammad, "
            "Ali ibn Hadid, Sama'a and Mihran, and the canonical report is "
            "between the separately aligned H13 and H15 records."
        ),
        "required_chain_token_groups": [
            ["ahmad"],
            ["muhammad"],
            ["ali"],
            ["hadid", "hadeed"],
            ["samaa", "samaah"],
            ["mihran", "mehran"],
        ],
        "adjacent_report_numbers": [13, 15],
    },
    23: {
        "reason": (
            "The PDF uses 'a number of our people' while the API modernizes the "
            "same mursal chain; both name Ahmad ibn Muhammad and Abu Abd Allah, "
            "and the canonical report is between the separately aligned H22 and H24 records."
        ),
        "required_chain_token_groups": [
            ["ahmad"],
            ["muhammad"],
            ["abd", "abdillah"],
        ],
        "adjacent_report_numbers": [22, 24],
    },
}

LONG_REPORT_CROSS_CHECKS: dict[int, str] = {
    12: (
        "The long Hisham ibn al-Hakam report spans PDF pages 14-19.  Its English "
        "chain identity is checked independently of the long Arabic body, and the "
        "canonical URL and adjacent report order are asserted; no threshold is relaxed."
    )
}


@dataclass(frozen=True)
class LocatedChunk:
    page: int
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class PdfRecord:
    number: int
    marker: str
    english_isnad: str
    english_matn: str
    pages: list[int]
    full_record_sha256: str
    matn_sha256: str
    special_case: str | None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_checksum(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"Missing {label}: {path}")
    actual = file_sha256(path)
    if actual.casefold() != expected.casefold():
        raise RuntimeError(
            f"{label} checksum changed: expected={expected} actual={actual} path={path}"
        )


def _clean_pdf_block(value: str) -> str:
    """Remove adjacent Arabic glyph corruption without editing English words."""

    value = unicodedata.normalize("NFC", value)
    first_contamination = ARABIC_OR_PUA_RE.search(value)
    if (
        first_contamination is not None
        and len(LATIN_RE.findall(value[: first_contamination.start()])) >= 4
    ):
        # A few cross-column blocks begin with an English continuation/marker
        # and then append the Arabic column.  Only the English prefix belongs to
        # the source excerpt.
        value = value[: first_contamination.start()]
    value = ARABIC_OR_PUA_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip().rstrip(" -\u2013")


def _first_alpha_is_latin(value: str) -> bool:
    first = next((character for character in value if character.isalpha()), "")
    return bool(first and LATIN_RE.fullmatch(first))


def _english_chunks(document: pymupdf.Document) -> tuple[str, list[LocatedChunk]]:
    # The opening chapter starts on physical PDF page 12; H35 is the hard stop
    # on page 28.  Reading to H35 also captures the continuation of H34 on page
    # 27 without admitting the following chapter's first report.
    pieces: list[tuple[int, str]] = []
    for page_index in range(11, min(28, document.page_count)):
        physical_page = page_index + 1
        for block in document[page_index].get_text("blocks", sort=True):
            x0, y0, x1, y1, raw_text, *_ = block
            if y1 <= 40 or y0 >= 750:
                continue
            text = _clean_pdf_block(raw_text)
            if not text:
                continue
            in_english_column = (
                physical_page % 2 == 0 and x0 >= 300
            ) or (
                physical_page % 2 == 1 and x1 <= 310
            )
            is_marker_prefix = PDF_MARKER_RE.match(text) is not None
            is_mixed_english_prefix = (
                _first_alpha_is_latin(text)
                and len(LATIN_RE.findall(text)) >= 10
            )
            if in_english_column or is_marker_prefix or is_mixed_english_prefix:
                pieces.append((physical_page, text))

    chunks: list[LocatedChunk] = []
    stream_parts: list[str] = []
    cursor = 0
    for page, text in pieces:
        if stream_parts:
            stream_parts.append("\n")
            cursor += 1
        start = cursor
        stream_parts.append(text)
        cursor += len(text)
        chunks.append(LocatedChunk(page=page, text=text, start=start, end=cursor))
    return "".join(stream_parts), chunks


def _pages_for_extent(
    chunks: list[LocatedChunk], start: int, end: int
) -> list[int]:
    return sorted(
        {
            chunk.page
            for chunk in chunks
            if chunk.end > start and chunk.start < end
        }
    )


def extract_pdf_records(path: Path) -> dict[int, PdfRecord]:
    _assert_checksum(path, PDF_SHA256, "Muhammad Sarwar Volume 1 PDF")
    document = pymupdf.open(path)
    stream, chunks = _english_chunks(document)
    markers = list(PDF_MARKER_RE.finditer(stream))
    marker_numbers = [
        int(marker.group("hadith") or marker.group("first"))
        for marker in markers
    ]
    required_prefix = list(range(1, EXPECTED_COUNT + 2))
    if marker_numbers[: EXPECTED_COUNT + 1] != required_prefix:
        raise RuntimeError(
            "PDF marker sequence changed; expected H1-H35 at the opening: "
            f"{marker_numbers[: EXPECTED_COUNT + 1]}"
        )

    records: dict[int, PdfRecord] = {}
    for index, marker in enumerate(markers[:EXPECTED_COUNT]):
        number = int(marker.group("hadith") or marker.group("first"))
        next_marker = markers[index + 1]
        raw_excerpt = stream[marker.end() : next_marker.start()]
        absolute_excerpt_end = next_marker.start()
        if number == 34:
            # The printed H34 entry appends separately lettered reports (a)
            # and (b) after the local/API Arabic report has ended.  Bound the
            # excerpt at the first printed subreport marker; no English words
            # inside the matched report are changed.
            subreport = re.search(r"\u201d\s*\(a\)", raw_excerpt)
            if subreport is None:
                raise RuntimeError("H34 printed subreport boundary disappeared")
            boundary = subreport.start() + 1
            raw_excerpt = raw_excerpt[:boundary]
            absolute_excerpt_end = marker.end() + boundary
        excerpt = clean_ws(raw_excerpt)
        excerpt = H1_CHAIN_LABEL_RE.sub("", excerpt)
        if number == 1:
            if H1_MATN_LABEL not in excerpt:
                raise RuntimeError("H1 PDF matn label disappeared")
            excerpt = excerpt.replace(H1_MATN_LABEL, "", 1).strip()
        quote_index = excerpt.find(OPEN_QUOTE)
        if quote_index <= 0:
            raise RuntimeError(f"Could not split English chain/matn for H{number}")
        english_isnad = excerpt[:quote_index].strip()
        english_matn = excerpt[quote_index:].strip()
        close_index = english_matn.rfind(CLOSE_QUOTE)
        if close_index < 0:
            raise RuntimeError(f"H{number} PDF matn has no closing quotation mark")
        # Page furniture and the next chapter heading can occur between the
        # final quotation mark and the next H marker.  They are outside the
        # verbatim matn excerpt and are removed by this structural boundary.
        english_matn = english_matn[: close_index + 1]
        marker_text = clean_ws(marker.group(0))
        full_record = clean_ws(f"{marker_text} {english_isnad} {english_matn}")
        pages = _pages_for_extent(chunks, marker.start(), absolute_excerpt_end)
        special_case = None
        if number == 1:
            special_case = "unprefixed_h1_marker_and_printed_chain_labels"
        elif number == 5:
            special_case = "h5_marker_shared_pdf_block_with_arabic_column"
        elif number == 34:
            special_case = "bounded_before_printed_subreport_a"
        if ARABIC_OR_PUA_RE.search(english_isnad + english_matn):
            raise RuntimeError(f"Arabic/PUA contamination remains in H{number}")
        forbidden = [
            value
            for value in FORBIDDEN_SOURCE_MARKERS
            if value in english_matn.casefold()
        ]
        if forbidden:
            raise RuntimeError(f"Forbidden source marker in H{number}: {forbidden}")
        records[number] = PdfRecord(
            number=number,
            marker=marker_text,
            english_isnad=english_isnad,
            english_matn=english_matn,
            pages=pages,
            full_record_sha256=exact_text_sha256(full_record),
            matn_sha256=exact_text_sha256(english_matn),
            special_case=special_case,
        )
    if sorted(records) != list(range(1, EXPECTED_COUNT + 1)):
        raise RuntimeError(f"Expected 34 PDF records; found {sorted(records)}")
    return records


def load_api_snapshot(path: Path) -> dict[int, dict[str, Any]]:
    _assert_checksum(path, API_SNAPSHOT_SHA256, "Thaqalayn API snapshot")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("1")
    if not isinstance(rows, list):
        raise RuntimeError("The API snapshot no longer contains a Volume 1 list")
    by_number: dict[int, dict[str, Any]] = {}
    for number in range(1, EXPECTED_COUNT + 1):
        canonical_url = f"https://thaqalayn.net/hadith/1/1/0/{number}"
        matches = [row for row in rows if row.get("URL") == canonical_url]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one API record for {canonical_url}; found {len(matches)}"
            )
        row = matches[0]
        if row.get("translator") != "Muhammad Sarwar":
            raise RuntimeError(
                f"API translator changed for H{number}: {row.get('translator')!r}"
            )
        if int(row.get("volume") or 0) != 1:
            raise RuntimeError(f"API volume changed for H{number}")
        if not clean_ws(row.get("arabicText")):
            raise RuntimeError(f"API Arabic is empty for H{number}")
        if not clean_ws(row.get("thaqalaynSanad")):
            raise RuntimeError(f"API English chain is empty for H{number}")
        by_number[number] = row
    return by_number


def _normalise_arabic_identity(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\[[^\]]*\]", " ", value)
    value = value.replace("ـ", "")
    value = value.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ئ": "ي",
                "ؤ": "و",
                "ك": "ک",
            }
        )
    )
    value = "".join(
        character
        for character in value
        if unicodedata.category(character) != "Mn"
    )
    return "".join(re.findall(r"[\u0600-\u06ff]+", value))


def arabic_identity_score(left: str, right: str) -> float:
    left_norm = _normalise_arabic_identity(left)
    right_norm = _normalise_arabic_identity(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(
        None, left_norm, right_norm, autojunk=False
    ).ratio()


def _english_chain_tokens(value: str) -> list[str]:
    value = (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    value = re.sub(r"^\s*\d+\s*[.]\s*", " ", value)
    value = re.sub(r"\b(?:bin|b)\.?\b", " ibn ", value)
    for phrase in (
        "recipient of divine supreme covenant",
        "al-kulayni",
        "the following",
        "has narrated",
        "have narrated",
        "has said",
        "who has said",
        "who said",
        "narrated",
        "reported",
        "imam",
    ):
        value = value.replace(phrase, " ")
    return re.findall(r"[a-z0-9]+", value)


def english_chain_token_f1(left: str, right: str) -> float:
    left_tokens = _english_chain_tokens(left)
    right_tokens = _english_chain_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = sum((Counter(left_tokens) & Counter(right_tokens)).values())
    return (2 * overlap) / (len(left_tokens) + len(right_tokens))


def _validate_manual_evidence(
    number: int,
    pdf_record: PdfRecord,
    api_record: dict[str, Any],
) -> dict[str, Any] | None:
    evidence = MANUAL_IDENTITY_EVIDENCE.get(number)
    if evidence is None:
        return None
    pdf_tokens = set(_english_chain_tokens(pdf_record.english_isnad))
    api_tokens = set(_english_chain_tokens(str(api_record["thaqalaynSanad"])))
    required_groups = evidence["required_chain_token_groups"]
    if any(
        not (set(group) & pdf_tokens) or not (set(group) & api_tokens)
        for group in required_groups
    ):
        raise RuntimeError(
            f"Documented manual identity evidence no longer holds for H{number}"
        )
    return evidence


def source_evidence_for_record(
    number: int,
    pdf_record: PdfRecord,
    api_record: dict[str, Any],
) -> dict[str, Any]:
    api_arabic = str(api_record["arabicText"])
    api_chain = clean_ws(api_record["thaqalaynSanad"])
    return {
        "classification": CLASSIFICATION,
        "translator": "Muhammad Sarwar",
        "pdf": {
            "source_url": PDF_SOURCE_URL,
            "sha256": PDF_SHA256,
            "pages": pdf_record.pages,
            "marker": pdf_record.marker,
            "full_record_sha256": pdf_record.full_record_sha256,
            "matn_sha256": pdf_record.matn_sha256,
            "special_case": pdf_record.special_case,
        },
        "api_identity": {
            "snapshot_source_url": API_SOURCE_URL,
            "snapshot_sha256": API_SNAPSHOT_SHA256,
            "canonical_url": api_record["URL"],
            "record_id": int(api_record["id"]),
            "record_sha256": canonical_json_sha256(api_record),
            "arabic_sha256": exact_text_sha256(api_arabic),
            "english_chain_sha256": exact_text_sha256(api_chain),
        },
    }


def _current_translation_payload(
    translation: HadithTranslation | None,
) -> dict[str, Any]:
    if translation is None:
        return {
            "provider": None,
            "model": None,
            "status": None,
            "risk_level": None,
            "matn_sha256": None,
        }
    return {
        "provider": translation.provider,
        "model": translation.model,
        "status": translation.status,
        "risk_level": translation.risk_level,
        "matn_sha256": (
            exact_text_sha256(translation.matn_translation)
            if translation.matn_translation
            else None
        ),
    }


def build_manifest(pdf_path: Path, api_path: Path) -> dict[str, Any]:
    pdf_records = extract_pdf_records(pdf_path)
    api_records = load_api_snapshot(api_path)
    records: list[dict[str, Any]] = []

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        hadiths = list(
            db.execute(
                select(Hadith)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.sequence_in_book.between(1, EXPECTED_COUNT),
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
                .order_by(Hadith.sequence_in_book)
            ).scalars()
        )
        if [row.sequence_in_book for row in hadiths] != list(
            range(1, EXPECTED_COUNT + 1)
        ):
            raise RuntimeError("Local Al-Kafi opening sequence is no longer exactly 1-34")
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                    HadithTranslation.hadith_id.in_([row.id for row in hadiths]),
                )
            ).scalars()
        }

        for hadith in hadiths:
            number = int(hadith.sequence_in_book)
            public_id = f"alkafi-{number}"
            if hadith.public_id != public_id or hadith.volume_start != 1:
                raise RuntimeError(
                    f"Unexpected local identity at sequence {number}: {hadith.public_id}"
                )
            pdf_record = pdf_records[number]
            api_record = api_records[number]
            arabic_score = arabic_identity_score(
                hadith.full_text_raw, str(api_record["arabicText"])
            )
            chain_score = english_chain_token_f1(
                pdf_record.english_isnad, str(api_record["thaqalaynSanad"])
            )
            manual_evidence = _validate_manual_evidence(
                number, pdf_record, api_record
            )
            if manual_evidence is None:
                if arabic_score < MIN_ARABIC_IDENTITY_SCORE:
                    raise RuntimeError(
                        f"Arabic identity below threshold for H{number}: {arabic_score:.6f}"
                    )
                if chain_score < MIN_ENGLISH_CHAIN_TOKEN_F1:
                    raise RuntimeError(
                        f"English chain identity below threshold for H{number}: {chain_score:.6f}"
                    )
            qa = assess_translation(hadith.matn_raw, pdf_record.english_matn)
            qa_flags = [asdict(flag) for flag in qa.flags]
            blocking = [
                flag["code"]
                for flag in qa_flags
                if flag["code"]
                in {
                    "empty_translation",
                    "provider_refusal_text",
                    "translation_too_short",
                    "translation_too_long",
                    "untranslated_arabic_block",
                }
            ]
            if blocking:
                raise RuntimeError(f"Blocking QA for H{number}: {blocking}")
            publication_flags: list[dict[str, str]] = []
            diagnostic_codes = {flag["code"] for flag in qa_flags}
            if "number_mismatch" in diagnostic_codes:
                publication_flags.append(
                    {
                        "code": "external_source_numbering_difference",
                        "severity": "info",
                        "detail": (
                            "The source edition's printed verse/note numbers differ from "
                            "local Arabic footnote markers; the verbatim published excerpt "
                            "was not rewritten."
                        ),
                    }
                )
            if "missing_placeholder" in diagnostic_codes:
                publication_flags.append(
                    {
                        "code": "external_source_footnote_marker_difference",
                        "severity": "info",
                        "detail": (
                            "Local Arabic editorial footnote markers are not interpolated "
                            "into the checksum-pinned published English excerpt."
                        ),
                    }
                )
            records.append(
                {
                    "public_id": public_id,
                    "sequence": number,
                    "volume": 1,
                    "page_start": hadith.page_start,
                    "page_end": hadith.page_end,
                    "printed_number": hadith.printed_number,
                    "local_source_url": hadith.source_url,
                    "source_full_sha256": sha256_text(hadith.full_text_raw),
                    "source_isnad_sha256": (
                        sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
                    ),
                    "source_matn_sha256": sha256_text(hadith.matn_raw),
                    "english_isnad": pdf_record.english_isnad,
                    "english_matn": pdf_record.english_matn,
                    "english_isnad_sha256": exact_text_sha256(
                        pdf_record.english_isnad
                    ),
                    "english_matn_sha256": pdf_record.matn_sha256,
                    "source_evidence": source_evidence_for_record(
                        number, pdf_record, api_record
                    ),
                    "identity": {
                        "arabic_sequence_score": round(arabic_score, 8),
                        "english_chain_token_f1": round(chain_score, 8),
                        "minimum_arabic_score": MIN_ARABIC_IDENTITY_SCORE,
                        "minimum_english_chain_token_f1": MIN_ENGLISH_CHAIN_TOKEN_F1,
                        "manual_evidence": manual_evidence,
                        "long_report_cross_check": LONG_REPORT_CROSS_CHECKS.get(
                            number
                        ),
                    },
                    "qa": {
                        "qa_version": qa.qa_version,
                        "diagnostic_risk": qa.risk_level,
                        "flags": qa_flags,
                        "blocking_flags": blocking,
                        "publication_risk": "green",
                        "publication_flags": publication_flags,
                        "source_purity": "passed",
                    },
                    "current_translation": _current_translation_payload(
                        translations.get(hadith.id)
                    ),
                    "target": {
                        "provider": TARGET_PROVIDER,
                        "model": TARGET_MODEL,
                        "status": "published",
                        "risk_level": "green",
                        "classification": CLASSIFICATION,
                        "editorial_operations": [],
                    },
                }
            )

    if len(records) != EXPECTED_COUNT:
        raise RuntimeError(f"Expected 34 manifest records; found {len(records)}")
    current_counts = Counter(
        str(record["current_translation"]["provider"]) for record in records
    )
    return {
        "schema_version": 1,
        "extraction_version": EXTRACTION_VERSION,
        "summary": {
            "source_book_id": SOURCE_BOOK_ID,
            "selected": EXPECTED_COUNT,
            "public_ids": [record["public_id"] for record in records],
            "source_classification": CLASSIFICATION,
            "translator": "Muhammad Sarwar",
            "target_provider": TARGET_PROVIDER,
            "target_model": TARGET_MODEL,
            "current_provider_counts": dict(sorted(current_counts.items())),
            "manual_identity_evidence": sorted(MANUAL_IDENTITY_EVIDENCE),
            "long_report_cross_checks": sorted(LONG_REPORT_CROSS_CHECKS),
            "arabic_score_range": [
                min(record["identity"]["arabic_sequence_score"] for record in records),
                max(record["identity"]["arabic_sequence_score"] for record in records),
            ],
            "english_chain_score_range": [
                min(record["identity"]["english_chain_token_f1"] for record in records),
                max(record["identity"]["english_chain_token_f1"] for record in records),
            ],
            "blocking_qa_count": sum(
                bool(record["qa"]["blocking_flags"]) for record in records
            ),
        },
        "sources": {
            "pdf": {
                "path": str(pdf_path.resolve()),
                "source_url": PDF_SOURCE_URL,
                "sha256": PDF_SHA256,
            },
            "api_snapshot": {
                "path": str(api_path.resolve()),
                "source_url": API_SOURCE_URL,
                "sha256": API_SNAPSHOT_SHA256,
            },
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--api-snapshot", type=Path, default=DEFAULT_API_SNAPSHOT)
    args = parser.parse_args()

    manifest = build_manifest(args.pdf, args.api_snapshot)
    encoded = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(manifest["summary"], indent=2))
    print(f"output={args.output}")
    print(f"manifest_sha256={file_sha256(args.output)}")


if __name__ == "__main__":
    main()
