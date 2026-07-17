"""Build a checksum-pinned Sarwar PDF manifest for 20 retired-pilot rows.

These are the Al-Kafi rows beyond ``alkafi-1`` .. ``alkafi-34`` that were
actually sent through the retired model pilot.  Their current public English
is already byte-for-byte human-source text from Thaqalayn.  Nineteen of those
rows, however, store an older Sarwar chain and matn together in the matn
field.  This manifest replaces all 20 with separately bounded English isnad
and matn excerpts from the published Muhammad Sarwar PDFs.

No translation is generated here.  The PDF bytes, the two identity snapshots,
the local Arabic, the report order, and both English extents are all checked.
If a row cannot meet the evidence thresholds it is emitted under ``blocked``;
it is never guessed into the importable ``records`` list.
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

from build_alkafi_opening_sarwar_pdf_manifest import (
    ARABIC_OR_PUA_RE,
    CLOSE_QUOTE,
    LATIN_RE,
    OPEN_QUOTE,
    PDF_MARKER_RE,
    _clean_pdf_block,
    _first_alpha_is_latin,
    _normalise_arabic_identity,
    arabic_identity_score,
    canonical_json_sha256,
    english_chain_token_f1,
    exact_text_sha256,
    file_sha256,
)
from eshia_research.db import SessionLocal
from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationSegment,
)
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_importer import (
    ThaqalaynRecord,
    parse_record,
    parse_static_row,
)


SOURCE_BOOK_ID = "11005"
EXPECTED_COUNT = 20
CLASSIFICATION = "verbatim_external_matn_excerpt"
TARGET_PROVIDER = "sarwar-published-scan"
TARGET_MODEL = "muhammad-sarwar-published"
EXTRACTION_VERSION = "alkafi_remaining_sarwar_pdf_blocks_v1"

PDF_SOURCES: dict[int, dict[str, Any]] = {
    1: {
        "path": Path(
            os.path.expandvars(r"%TEMP%\sarwar-alkafi-almurtaza\volume-1.pdf")
        ),
        "source_url": (
            "https://al-murtaza.org/wp-content/uploads/2021/08/"
            "Al-Kafi_Volume-1.pdf"
        ),
        "sha256": "969ff47af5fe9d0bf6ca542aa11f2d27130437b156448ee9cb4b141ba2f1d41a",
        # Zero-based page range, end-exclusive.  It deliberately includes a
        # following marker so every selected extent has a hard right bound.
        "page_range": [11, 32],
    },
    2: {
        "path": Path(
            os.path.expandvars(r"%TEMP%\sarwar-alkafi-almurtaza\volume-2.pdf")
        ),
        "source_url": (
            "https://al-murtaza.org/wp-content/uploads/2021/08/"
            "Al-Kafi_Volume-2.pdf"
        ),
        "sha256": "f65ed085faa56d6901763e138c7ce7232e344e04e5373ed1863218ff074d084a",
        "page_range": [15, 30],
    },
}

API_SNAPSHOT = {
    "path": Path(
        os.path.expandvars(
            r"%TEMP%\sarwar-alkafi-audit\thaqalayn-api-alkafi.json"
        )
    ),
    "source_url": (
        "https://www.thaqalayn-api.net/api/v2/Al-Kafi-Volume-1-Kulayni"
    ),
    "sha256": "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2",
}
STATIC_SNAPSHOT = {
    "path": Path(
        os.path.expandvars(r"%TEMP%\thaqalayn-al-kafi-static-full-fromzip.json")
    ),
    "source_url": "https://thaqalayndata.netlify.app",
    "sha256": "a0e57d41ae653a9f8d2b88dca4c0a3e149ce0a25b07ba3a880ffb461db920d43",
}

DEFAULT_OUTPUT = Path(__file__).with_name(
    "alkafi_remaining_sarwar_pdf_manifest_20260716.json"
)

MIN_ARABIC_IDENTITY_SCORE = 0.80
MIN_ARABIC_SHORTER_SEQUENCE_COVERAGE = 0.98
MIN_ENGLISH_CHAIN_TOKEN_F1 = 0.55
MIN_ENGLISH_MATN_SIMILARITY = 0.55
MIN_ENGLISH_FULL_SIMILARITY = 0.65

SPACE_RE = re.compile(r"\s+")
HYPHEN_LINE_WRAP_RE = re.compile(r"-[ \t]*\r?\n[ \t]*")
LEADING_REPORT_NUMBER_RE = re.compile(r"^\s*\d+\s*[.]\s*")
SUBREPORT_BOUNDARY_RE = re.compile(
    rf"{re.escape(CLOSE_QUOTE)}\s*\((?P<label>[ab])\)\s*"
)
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
BLOCKING_QA_CODES = {
    "empty_translation",
    "provider_refusal_text",
    "translation_too_short",
    "translation_too_long",
    "untranslated_arabic_block",
}


@dataclass(frozen=True)
class TargetSpec:
    public_id: str
    sequence: int
    local_volume: int
    printed_number: str
    pdf_volume: int
    pdf_number: int
    expected_marker: str
    expected_pages: tuple[int, ...]
    extent_kind: str
    source_kind: str
    source_url: str


def _v1(
    public_number: int,
    pdf_number: int,
    local_number: int,
    pages: tuple[int, ...],
) -> TargetSpec:
    return TargetSpec(
        public_id=f"alkafi-{public_number}",
        sequence=public_number,
        local_volume=1,
        printed_number=str(local_number).translate(
            str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
        ),
        pdf_volume=1,
        pdf_number=pdf_number,
        expected_marker=f"H {pdf_number}, Ch. {1 if pdf_number <= 43 else 2}, h{local_number}",
        expected_pages=pages,
        extent_kind="marker_bound",
        source_kind="static",
        source_url=(
            "https://thaqalayn.net/books/al-kafi:1:2:"
            f"{1 if pdf_number <= 43 else 2}:{local_number}"
        ),
    )


def _v2(
    public_number: int,
    pdf_number: int,
    printed_number: int,
    marker: str,
    page: int,
    source_path: str,
) -> TargetSpec:
    return TargetSpec(
        public_id=f"alkafi-{public_number}",
        sequence=public_number + 1,
        local_volume=2,
        printed_number=str(printed_number).translate(
            str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
        ),
        pdf_volume=2,
        pdf_number=pdf_number,
        expected_marker=marker,
        expected_pages=(page,),
        extent_kind="marker_bound",
        source_kind="static",
        source_url=f"https://thaqalayn.net/books/{source_path}",
    )


TARGET_SPECS: tuple[TargetSpec, ...] = (
    TargetSpec(
        public_id="alkafi-36",
        sequence=36,
        local_volume=1,
        printed_number="٣٦",
        pdf_volume=1,
        pdf_number=34,
        expected_marker="H 34, Ch. 1, h34",
        expected_pages=(27,),
        extent_kind="subreport_b",
        source_kind="api",
        source_url="https://thaqalayn.net/hadith/1/1/0/36",
    ),
    _v1(37, 35, 1, (28,)),
    _v1(38, 36, 2, (28,)),
    _v1(39, 37, 3, (28,)),
    _v1(41, 39, 5, (28, 29)),
    _v1(42, 40, 6, (29,)),
    _v1(43, 41, 7, (29,)),
    _v1(44, 42, 8, (29,)),
    _v1(45, 43, 9, (29,)),
    _v1(48, 46, 3, (30,)),
    _v1(49, 47, 4, (30,)),
    _v2(1444, 1438, 1, "H 1438, CH 1a, h 1", 17, "al-kafi:2:1:1:1"),
    _v2(1445, 1439, 2, "H 1439, CH 1a, h 2", 17, "al-kafi:2:1:1:2"),
    _v2(1446, 1440, 3, "H 1440, CH 1a, h 3", 17, "al-kafi:2:1:1:3"),
    _v2(1447, 1441, 4, "H 1441, CH 1a, h 4", 18, "al-kafi:2:1:1:4"),
    _v2(1448, 1442, 5, "H 1442, CH 1a, h 5", 18, "al-kafi:2:1:1:5"),
    _v2(1449, 1443, 6, "H 1443, CH 1a, h 6", 18, "al-kafi:2:1:1:6"),
    _v2(1459, 1453, 3, "H 1453, CH 1c, h 3", 25, "al-kafi:2:1:4:3"),
    _v2(1460, 1454, 1, "H 1454, CH 3, h 1", 25, "al-kafi:2:1:5:1"),
    _v2(1461, 1455, 1, "H 1455, CH 4, h 1", 25, "al-kafi:2:1:6:1"),
)

if len(TARGET_SPECS) != EXPECTED_COUNT:
    raise RuntimeError("Target specification cardinality changed")


@dataclass(frozen=True)
class LocatedChunk:
    page: int
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class PdfRecord:
    public_id: str
    pdf_volume: int
    pdf_number: int
    marker: str
    extent_kind: str
    english_isnad: str
    english_matn: str
    pages: list[int]
    preceding_marker: str
    following_marker: str
    english_isnad_sha256: str
    english_matn_sha256: str
    full_record_sha256: str
    layout_operations: list[dict[str, Any]]


@dataclass(frozen=True)
class IdentitySource:
    kind: str
    provider: str
    snapshot_sha256: str
    snapshot_source_url: str
    source_url: str
    record: ThaqalaynRecord
    raw: dict[str, Any]
    stored_english: str
    english_isnad: str
    english_matn: str


class EvidenceFailure(RuntimeError):
    """A row-specific failure that must produce a blocked manifest entry."""


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise EvidenceFailure(detail)


def _assert_checksum(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"Missing {label}: {path}")
    actual = file_sha256(path)
    if actual.casefold() != expected.casefold():
        raise RuntimeError(
            f"{label} checksum changed: expected={expected} actual={actual} path={path}"
        )


def _clean_layout_block(value: str) -> str:
    # A source line ending in ``al-`` continues as the same printed word on
    # the next line.  Join only that explicit PDF layout boundary before the
    # opening builder removes cross-column Arabic contamination.
    value = HYPHEN_LINE_WRAP_RE.sub("-", value)
    return _clean_pdf_block(value)


def _english_stream(
    path: Path, page_range: tuple[int, int] | list[int]
) -> tuple[str, list[LocatedChunk]]:
    document = pymupdf.open(path)
    start_page, end_page = (int(value) for value in page_range)
    pieces: list[tuple[int, str]] = []
    for page_index in range(start_page, min(end_page, document.page_count)):
        physical_page = page_index + 1
        for block in document[page_index].get_text("blocks", sort=True):
            x0, y0, x1, y1, raw_text, *_ = block
            if y1 <= 40 or y0 >= 750:
                continue
            text = _clean_layout_block(raw_text)
            if not text:
                continue
            in_english_column = (
                physical_page % 2 == 0 and x0 >= 300
            ) or (
                physical_page % 2 == 1 and x1 <= 310
            )
            marker_prefix = PDF_MARKER_RE.match(text) is not None
            mixed_english_prefix = (
                _first_alpha_is_latin(text)
                and len(LATIN_RE.findall(text)) >= 10
            )
            if in_english_column or marker_prefix or mixed_english_prefix:
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


def _split_english_extent(raw: str, public_id: str) -> tuple[str, str, int]:
    open_index = raw.find(OPEN_QUOTE)
    close_index = raw.rfind(CLOSE_QUOTE)
    _require(open_index > 0, f"{public_id}: English matn opening quote missing")
    _require(
        close_index > open_index,
        f"{public_id}: English matn closing quote missing",
    )
    english_isnad = clean_ws(raw[:open_index])
    english_matn = clean_ws(raw[open_index : close_index + 1])
    _require(bool(english_isnad), f"{public_id}: empty English isnad")
    _require(bool(english_matn), f"{public_id}: empty English matn")
    return english_isnad, english_matn, close_index + 1


def _normalise_marker(value: str) -> str:
    return clean_ws(value)


def extract_pdf_records(pdf_paths: dict[int, Path]) -> dict[str, PdfRecord]:
    records: dict[str, PdfRecord] = {}
    for volume, source in PDF_SOURCES.items():
        path = pdf_paths[volume]
        _assert_checksum(path, str(source["sha256"]), f"Sarwar Volume {volume} PDF")
        stream, chunks = _english_stream(path, source["page_range"])
        markers = list(PDF_MARKER_RE.finditer(stream))
        by_number: dict[int, list[tuple[int, re.Match[str]]]] = {}
        for index, marker in enumerate(markers):
            number = int(marker.group("hadith") or marker.group("first"))
            by_number.setdefault(number, []).append((index, marker))

        for spec in (row for row in TARGET_SPECS if row.pdf_volume == volume):
            matches = by_number.get(spec.pdf_number, [])
            _require(
                len(matches) == 1,
                f"{spec.public_id}: expected one PDF H{spec.pdf_number} marker; "
                f"found {len(matches)}",
            )
            marker_index, marker = matches[0]
            _require(
                marker_index + 1 < len(markers),
                f"{spec.public_id}: selected PDF marker has no following bound",
            )
            next_marker = markers[marker_index + 1]
            marker_text = _normalise_marker(marker.group(0))
            _require(
                marker_text == spec.expected_marker,
                f"{spec.public_id}: PDF marker changed: {marker_text!r}",
            )
            raw_between = stream[marker.end() : next_marker.start()]
            absolute_start = marker.end()
            extent_note = "bounded from selected H marker to its final English quotation"

            if spec.extent_kind == "subreport_b":
                boundaries = list(SUBREPORT_BOUNDARY_RE.finditer(raw_between))
                _require(
                    [boundary.group("label") for boundary in boundaries] == ["a", "b"],
                    f"{spec.public_id}: H34 printed (a)/(b) boundaries changed",
                )
                boundary = boundaries[1]
                raw_between = raw_between[boundary.end() :]
                absolute_start += boundary.end()
                extent_note = (
                    "bounded after the unique printed H34 subreport (b) label and "
                    "before the following H35 marker; the final English quotation "
                    "excludes the intervening end-of-book headings"
                )

            english_isnad, english_matn, used_length = _split_english_extent(
                raw_between, spec.public_id
            )
            absolute_end = absolute_start + used_length
            pages = _pages_for_extent(chunks, absolute_start, absolute_end)
            _require(
                pages == list(spec.expected_pages),
                f"{spec.public_id}: PDF extent pages changed: {pages}",
            )

            layout_operations: list[dict[str, Any]] = []
            if spec.public_id == "alkafi-1444":
                # The PDF text layer breaks the visually continuous printed
                # word ``man`` into ``m`` and ``an`` at a line boundary.  The
                # pinned Thaqalayn human-source record independently has
                # ``a man from``.  Repair this one extraction artefact only.
                _require(
                    english_isnad.count("m an") == 1,
                    "alkafi-1444: expected PDF text-layer fragment 'm an' changed",
                )
                english_isnad = english_isnad.replace("m an", "man", 1)
                layout_operations.append(
                    {
                        "operation": "join_pdf_text_layer_word_fragment",
                        "field": "english_isnad",
                        "from": "m an",
                        "to": "man",
                        "occurrences": 1,
                        "reason": (
                            "The printed word crosses a malformed PDF text-layer line "
                            "boundary; the pinned human-source record corroborates 'man'."
                        ),
                    }
                )

            _require(
                not ARABIC_OR_PUA_RE.search(english_isnad + english_matn),
                f"{spec.public_id}: Arabic/PUA contamination remains in PDF English",
            )
            forbidden = [
                marker_value
                for marker_value in FORBIDDEN_SOURCE_MARKERS
                if marker_value in (english_isnad + " " + english_matn).casefold()
            ]
            _require(
                not forbidden,
                f"{spec.public_id}: forbidden source marker(s) in PDF: {forbidden}",
            )
            preceding = (
                _normalise_marker(markers[marker_index - 1].group(0))
                if marker_index > 0
                else ""
            )
            following = _normalise_marker(next_marker.group(0))
            record_marker = (
                f"{marker_text} (b)" if spec.extent_kind == "subreport_b" else marker_text
            )
            full_record = clean_ws(
                f"{record_marker} {english_isnad} {english_matn}"
            )
            record_operations = [
                {
                    "operation": "join_hyphenated_pdf_line_wraps",
                    "scope": "PDF block extraction",
                    "reason": "Remove layout-only whitespace after a line-final hyphen.",
                },
                *layout_operations,
                {
                    "operation": "bound_pdf_report_extent",
                    "extent_kind": spec.extent_kind,
                    "detail": extent_note,
                },
            ]
            records[spec.public_id] = PdfRecord(
                public_id=spec.public_id,
                pdf_volume=volume,
                pdf_number=spec.pdf_number,
                marker=record_marker,
                extent_kind=spec.extent_kind,
                english_isnad=english_isnad,
                english_matn=english_matn,
                pages=pages,
                preceding_marker=preceding,
                following_marker=following,
                english_isnad_sha256=exact_text_sha256(english_isnad),
                english_matn_sha256=exact_text_sha256(english_matn),
                full_record_sha256=exact_text_sha256(full_record),
                layout_operations=record_operations,
            )

    _require(
        list(records) == [spec.public_id for spec in TARGET_SPECS],
        "PDF extraction did not produce the exact target order",
    )
    return records


def _split_static_english(value: str, public_id: str) -> tuple[str, str]:
    body = LEADING_REPORT_NUMBER_RE.sub("", value, count=1)
    open_index = body.find(OPEN_QUOTE)
    _require(open_index > 0, f"{public_id}: static English chain/matn split missing")
    _require(
        body.rfind(CLOSE_QUOTE) > open_index,
        f"{public_id}: static English closing quote missing",
    )
    # The static source is itself the bounded field.  A few records retain an
    # additional closing single quotation mark after the final double mark;
    # keep that source punctuation in the identity comparison instead of
    # silently trimming it.
    return clean_ws(body[:open_index]), clean_ws(body[open_index:])


def load_identity_sources(
    api_path: Path, static_path: Path
) -> dict[str, IdentitySource]:
    _assert_checksum(api_path, str(API_SNAPSHOT["sha256"]), "Thaqalayn API snapshot")
    _assert_checksum(
        static_path, str(STATIC_SNAPSHOT["sha256"]), "ThaqalaynData snapshot"
    )
    api_payload = json.loads(api_path.read_text(encoding="utf-8"))
    static_payload = json.loads(static_path.read_text(encoding="utf-8"))
    api_by_url = {
        str(row.get("URL")): row
        for rows in api_payload.values()
        for row in rows
        if row.get("URL")
    }
    static_by_url = {
        str(row.get("source_url")): row
        for row in static_payload
        if row.get("source_url")
    }

    sources: dict[str, IdentitySource] = {}
    for spec in TARGET_SPECS:
        if spec.source_kind == "api":
            raw = api_by_url.get(spec.source_url)
            _require(raw is not None, f"{spec.public_id}: API identity row missing")
            assert raw is not None
            record = parse_record(raw)
            stored_english = str(raw.get("thaqalaynMatn") or "")
            english_isnad = clean_ws(raw.get("thaqalaynSanad"))
            english_matn = clean_ws(stored_english)
            _require(
                stored_english == english_matn,
                f"{spec.public_id}: API English now requires undocumented normalization",
            )
            provider = "thaqalayn-api"
            snapshot = API_SNAPSHOT
        else:
            raw = static_by_url.get(spec.source_url)
            _require(raw is not None, f"{spec.public_id}: static identity row missing")
            assert raw is not None
            record = parse_static_row(raw)
            _require(record is not None, f"{spec.public_id}: static identity row is unusable")
            assert record is not None
            stored_english = str(raw.get("en_sarwar") or "")
            _require(
                stored_english == clean_ws(stored_english),
                f"{spec.public_id}: static English now requires undocumented normalization",
            )
            english_isnad, english_matn = _split_static_english(
                stored_english, spec.public_id
            )
            provider = "thaqalayn-data"
            snapshot = STATIC_SNAPSHOT

        _require(record.url == spec.source_url, f"{spec.public_id}: source URL changed")
        _require(
            record.translator == "Muhammad Sarwar",
            f"{spec.public_id}: translator attribution changed: {record.translator!r}",
        )
        _require(bool(record.arabic_text), f"{spec.public_id}: source Arabic is empty")
        _require(bool(english_isnad), f"{spec.public_id}: source English isnad is empty")
        _require(bool(english_matn), f"{spec.public_id}: source English matn is empty")
        sources[spec.public_id] = IdentitySource(
            kind=spec.source_kind,
            provider=provider,
            snapshot_sha256=str(snapshot["sha256"]),
            snapshot_source_url=str(snapshot["source_url"]),
            source_url=spec.source_url,
            record=record,
            raw=raw,
            stored_english=stored_english,
            english_isnad=english_isnad,
            english_matn=english_matn,
        )
    return sources


def _normalise_english_identity(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    value = LEADING_REPORT_NUMBER_RE.sub("", value)
    for phrase in (
        "recipient of divine supreme covenant",
        "(a.s.)",
        "(a.s)",
        "(sw)",
        "(s.a)",
    ):
        value = value.replace(phrase, " ")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def english_identity_similarity(left: str, right: str) -> float:
    left_norm = _normalise_english_identity(left)
    right_norm = _normalise_english_identity(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(
        None, left_norm, right_norm, autojunk=False
    ).ratio()


def identity_metrics(
    hadith: Hadith,
    pdf_record: PdfRecord,
    identity_source: IdentitySource,
) -> dict[str, Any]:
    # The API identity row contains the whole Arabic report, while the static
    # ThaqalaynData field contains the matn only.  Compare like-for-like and
    # record the chosen local extent explicitly.
    local_arabic_extent = (
        hadith.full_text_raw
        if identity_source.kind == "api"
        else hadith.matn_raw
    )
    local_arabic_norm = _normalise_arabic_identity(local_arabic_extent)
    source_arabic_norm = _normalise_arabic_identity(
        identity_source.record.arabic_text
    )
    arabic_match = difflib.SequenceMatcher(
        None, local_arabic_norm, source_arabic_norm, autojunk=False
    )
    matching_arabic_chars = sum(
        block.size for block in arabic_match.get_matching_blocks()
    )
    shorter_arabic_length = min(
        len(local_arabic_norm), len(source_arabic_norm)
    )
    pdf_full = clean_ws(f"{pdf_record.english_isnad} {pdf_record.english_matn}")
    source_full = clean_ws(
        f"{identity_source.english_isnad} {identity_source.english_matn}"
    )
    return {
        "arabic_sequence_score": round(
            arabic_identity_score(
                local_arabic_extent, identity_source.record.arabic_text
            ),
            8,
        ),
        "arabic_shorter_sequence_coverage": round(
            matching_arabic_chars / shorter_arabic_length
            if shorter_arabic_length
            else 0.0,
            8,
        ),
        "arabic_local_extent": (
            "full_report" if identity_source.kind == "api" else "matn"
        ),
        "english_chain_token_f1": round(
            english_chain_token_f1(
                pdf_record.english_isnad, identity_source.english_isnad
            ),
            8,
        ),
        "english_matn_similarity": round(
            english_identity_similarity(
                pdf_record.english_matn, identity_source.english_matn
            ),
            8,
        ),
        "english_full_similarity": round(
            english_identity_similarity(pdf_full, source_full),
            8,
        ),
        "thresholds": {
            "minimum_arabic_sequence_score": MIN_ARABIC_IDENTITY_SCORE,
            "minimum_arabic_shorter_sequence_coverage": (
                MIN_ARABIC_SHORTER_SEQUENCE_COVERAGE
            ),
            "minimum_english_chain_token_f1": MIN_ENGLISH_CHAIN_TOKEN_F1,
            "minimum_english_matn_similarity": MIN_ENGLISH_MATN_SIMILARITY,
            "minimum_english_full_similarity": MIN_ENGLISH_FULL_SIMILARITY,
        },
    }


def source_evidence_for_record(
    spec: TargetSpec,
    pdf_record: PdfRecord,
    identity_source: IdentitySource,
) -> dict[str, Any]:
    pdf_source = PDF_SOURCES[spec.pdf_volume]
    return {
        "classification": CLASSIFICATION,
        "translator": "Muhammad Sarwar",
        "pdf": {
            "physical_volume": spec.pdf_volume,
            "source_url": pdf_source["source_url"],
            "sha256": pdf_source["sha256"],
            "pages": pdf_record.pages,
            "marker": pdf_record.marker,
            "extent_kind": pdf_record.extent_kind,
            "preceding_marker": pdf_record.preceding_marker,
            "following_marker": pdf_record.following_marker,
            "english_isnad_sha256": pdf_record.english_isnad_sha256,
            "matn_sha256": pdf_record.english_matn_sha256,
            "full_record_sha256": pdf_record.full_record_sha256,
            "layout_operations": pdf_record.layout_operations,
        },
        "human_source_identity": {
            "provider": identity_source.provider,
            "snapshot_source_url": identity_source.snapshot_source_url,
            "snapshot_sha256": identity_source.snapshot_sha256,
            "source_url": identity_source.source_url,
            "record_id": identity_source.record.id,
            "record_sha256": canonical_json_sha256(identity_source.raw),
            "translator": identity_source.record.translator,
            "arabic_sha256": exact_text_sha256(
                identity_source.record.arabic_text
            ),
            "stored_english_sha256": exact_text_sha256(
                identity_source.stored_english
            ),
            "english_isnad_sha256": exact_text_sha256(
                identity_source.english_isnad
            ),
            "english_matn_sha256": exact_text_sha256(
                identity_source.english_matn
            ),
        },
    }


def identity_payload(
    spec: TargetSpec,
    hadith: Hadith,
    pdf_record: PdfRecord,
    identity_source: IdentitySource,
) -> dict[str, Any]:
    return {
        **identity_metrics(hadith, pdf_record, identity_source),
        "local_sequence_evidence": {
            "public_id": spec.public_id,
            "sequence_in_book": spec.sequence,
            "volume": spec.local_volume,
            "printed_number": spec.printed_number,
        },
        "pdf_extent_evidence": {
            "physical_volume": spec.pdf_volume,
            "printed_hadith_number": spec.pdf_number,
            "marker": pdf_record.marker,
            "extent_kind": spec.extent_kind,
            "pages": pdf_record.pages,
            "preceding_marker": pdf_record.preceding_marker,
            "following_marker": pdf_record.following_marker,
        },
    }


def _whole_matn_segment(db, hadith: Hadith) -> TranslationSegment | None:
    rows = list(
        db.execute(
            select(TranslationSegment).where(
                TranslationSegment.hadith_id == hadith.id,
                TranslationSegment.language == "en",
                TranslationSegment.translation_version == TRANSLATION_VERSION,
                TranslationSegment.segment_kind == "matn",
                TranslationSegment.segment_index == 0,
                TranslationSegment.source_sha256 == sha256_text(hadith.matn_raw),
            )
        ).scalars()
    )
    _require(
        len(rows) <= 1,
        f"{hadith.public_id}: multiple current whole-matn segments",
    )
    return rows[0] if rows else None


def current_translation_payload(
    translation: HadithTranslation | None,
) -> dict[str, Any]:
    if translation is None:
        return {"translation_id": None}
    return {
        "translation_id": translation.id,
        "provider": translation.provider,
        "model": translation.model,
        "status": translation.status,
        "risk_level": translation.risk_level,
        "source_full_sha256": translation.source_full_sha256,
        "source_isnad_sha256": translation.source_isnad_sha256,
        "source_matn_sha256": translation.source_matn_sha256,
        "rendered_isnad_sha256": (
            exact_text_sha256(translation.rendered_isnad_en)
            if translation.rendered_isnad_en
            else None
        ),
        "matn_sha256": (
            exact_text_sha256(translation.matn_translation)
            if translation.matn_translation
            else None
        ),
        "provenance_sha256": canonical_json_sha256(
            translation.provenance_json or {}
        ),
    }


def current_segment_payload(
    segment: TranslationSegment | None,
) -> dict[str, Any]:
    if segment is None:
        return {"segment_id": None}
    return {
        "segment_id": segment.id,
        "translation_id": segment.translation_id,
        "source_sha256": segment.source_sha256,
        "translation_sha256": (
            exact_text_sha256(segment.translation_text)
            if segment.translation_text
            else None
        ),
        "status": segment.status,
        "risk_level": segment.risk_level,
        "metadata_sha256": canonical_json_sha256(segment.metadata_json or {}),
    }


def _publication_qa(hadith: Hadith, english_matn: str) -> dict[str, Any]:
    qa = assess_translation(hadith.matn_raw, english_matn)
    flags = [asdict(flag) for flag in qa.flags]
    blocking = [
        flag["code"] for flag in flags if flag["code"] in BLOCKING_QA_CODES
    ]
    _require(not blocking, f"{hadith.public_id}: blocking PDF QA: {blocking}")
    publication_flags: list[dict[str, str]] = []
    codes = {flag["code"] for flag in flags}
    if "number_mismatch" in codes:
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
    if "missing_placeholder" in codes:
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
    return {
        "qa_version": qa.qa_version,
        "diagnostic_risk": qa.risk_level,
        "flags": flags,
        "blocking_flags": blocking,
        "publication_risk": "green",
        "publication_flags": publication_flags,
        "source_purity": "passed",
    }


def _build_record(
    spec: TargetSpec,
    hadith: Hadith,
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    pdf_record: PdfRecord,
    identity_source: IdentitySource,
) -> dict[str, Any]:
    _require(hadith.public_id == spec.public_id, f"{spec.public_id}: local ID changed")
    _require(
        hadith.sequence_in_book == spec.sequence,
        f"{spec.public_id}: local sequence changed: {hadith.sequence_in_book}",
    )
    _require(
        hadith.volume_start == spec.local_volume,
        f"{spec.public_id}: local volume changed: {hadith.volume_start}",
    )
    _require(
        hadith.printed_number == spec.printed_number,
        f"{spec.public_id}: local printed number changed: {hadith.printed_number!r}",
    )
    _require(
        hadith.review_status != "rejected_non_hadith_fragment",
        f"{spec.public_id}: local row is rejected as a non-hadith fragment",
    )
    _require(translation is not None, f"{spec.public_id}: current translation missing")
    assert translation is not None
    _require(
        translation.provider == identity_source.provider,
        f"{spec.public_id}: current provider no longer matches identity source",
    )
    _require(
        translation.model == "muhammad-sarwar",
        f"{spec.public_id}: current translator model changed",
    )
    _require(
        translation.matn_translation == identity_source.stored_english,
        f"{spec.public_id}: current public English is not byte-exact to pinned source",
    )
    if spec.source_kind == "api":
        _require(
            translation.rendered_isnad_en == identity_source.english_isnad,
            f"{spec.public_id}: current API English isnad changed",
        )
    else:
        _require(
            translation.rendered_isnad_en is None,
            f"{spec.public_id}: expected unsplit static source state changed",
        )
    provenance = translation.provenance_json or {}
    expected_snapshot = (
        API_SNAPSHOT["sha256"]
        if spec.source_kind == "api"
        else STATIC_SNAPSHOT["sha256"]
    )
    _require(
        provenance.get("source_url") == spec.source_url,
        f"{spec.public_id}: current source URL changed",
    )
    _require(
        provenance.get("translator") == "Muhammad Sarwar",
        f"{spec.public_id}: current translator attribution changed",
    )
    _require(
        provenance.get("source_snapshot_sha256") == expected_snapshot,
        f"{spec.public_id}: current source snapshot pin changed",
    )
    _require(
        provenance.get("source_record_sha256")
        == canonical_json_sha256(identity_source.raw),
        f"{spec.public_id}: current source-record pin changed",
    )

    metrics = identity_metrics(hadith, pdf_record, identity_source)
    thresholds = metrics["thresholds"]
    _require(
        metrics["arabic_sequence_score"]
        >= thresholds["minimum_arabic_sequence_score"],
        f"{spec.public_id}: Arabic identity below threshold: "
        f"{metrics['arabic_sequence_score']}",
    )
    _require(
        metrics["arabic_shorter_sequence_coverage"]
        >= thresholds["minimum_arabic_shorter_sequence_coverage"],
        f"{spec.public_id}: Arabic shorter-sequence coverage below threshold: "
        f"{metrics['arabic_shorter_sequence_coverage']}",
    )
    _require(
        metrics["english_chain_token_f1"]
        >= thresholds["minimum_english_chain_token_f1"],
        f"{spec.public_id}: English-chain identity below threshold: "
        f"{metrics['english_chain_token_f1']}",
    )
    _require(
        metrics["english_matn_similarity"]
        >= thresholds["minimum_english_matn_similarity"],
        f"{spec.public_id}: English-matn identity below threshold: "
        f"{metrics['english_matn_similarity']}",
    )
    _require(
        metrics["english_full_similarity"]
        >= thresholds["minimum_english_full_similarity"],
        f"{spec.public_id}: English-full identity below threshold: "
        f"{metrics['english_full_similarity']}",
    )

    qa = _publication_qa(hadith, pdf_record.english_matn)
    evidence = source_evidence_for_record(
        spec, pdf_record, identity_source
    )
    return {
        "public_id": spec.public_id,
        "sequence": spec.sequence,
        "volume": spec.local_volume,
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
        "english_isnad_sha256": pdf_record.english_isnad_sha256,
        "english_matn_sha256": pdf_record.english_matn_sha256,
        "source_evidence": evidence,
        "identity": identity_payload(
            spec, hadith, pdf_record, identity_source
        ),
        "qa": qa,
        "current_translation": current_translation_payload(translation),
        "current_segment": current_segment_payload(segment),
        "target": {
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
            "status": "published",
            "risk_level": "green",
            "classification": CLASSIFICATION,
            "editorial_operations": pdf_record.layout_operations,
        },
    }


def build_manifest(
    pdf_paths: dict[int, Path],
    api_path: Path,
    static_path: Path,
) -> dict[str, Any]:
    pdf_records = extract_pdf_records(pdf_paths)
    identity_sources = load_identity_sources(api_path, static_path)
    records: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        hadiths = {
            row.public_id: row
            for row in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_([spec.public_id for spec in TARGET_SPECS]),
                )
            ).scalars()
        }
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                    HadithTranslation.hadith_id.in_(
                        [row.id for row in hadiths.values()]
                    ),
                )
            ).scalars()
        }

        for spec in TARGET_SPECS:
            try:
                hadith = hadiths.get(spec.public_id)
                _require(hadith is not None, f"{spec.public_id}: local hadith missing")
                assert hadith is not None
                translation = translations.get(hadith.id)
                segment = _whole_matn_segment(db, hadith)
                records.append(
                    _build_record(
                        spec,
                        hadith,
                        translation,
                        segment,
                        pdf_records[spec.public_id],
                        identity_sources[spec.public_id],
                    )
                )
            except EvidenceFailure as exc:
                blocked.append(
                    {
                        "public_id": spec.public_id,
                        "sequence": spec.sequence,
                        "reason": str(exc),
                        "target_spec": asdict(spec),
                    }
                )

    current_counts = Counter(
        str(record["current_translation"].get("provider")) for record in records
    )
    score_fields = (
        "arabic_sequence_score",
        "arabic_shorter_sequence_coverage",
        "english_chain_token_f1",
        "english_matn_similarity",
        "english_full_similarity",
    )
    score_ranges = {
        field: [
            min(record["identity"][field] for record in records),
            max(record["identity"][field] for record in records),
        ]
        for field in score_fields
        if records
    }
    return {
        "schema_version": 1,
        "extraction_version": EXTRACTION_VERSION,
        "summary": {
            "source_book_id": SOURCE_BOOK_ID,
            "expected": EXPECTED_COUNT,
            "selected": len(records),
            "blocked": len(blocked),
            "public_ids": [record["public_id"] for record in records],
            "blocked_public_ids": [record["public_id"] for record in blocked],
            "source_classification": CLASSIFICATION,
            "translator": "Muhammad Sarwar",
            "target_provider": TARGET_PROVIDER,
            "target_model": TARGET_MODEL,
            "current_provider_counts": dict(sorted(current_counts.items())),
            "identity_score_ranges": score_ranges,
            "blocking_qa_count": sum(
                bool(record["qa"]["blocking_flags"]) for record in records
            ),
        },
        "sources": {
            "pdfs": {
                str(volume): {
                    "path": str(pdf_paths[volume].resolve()),
                    "source_url": source["source_url"],
                    "sha256": source["sha256"],
                }
                for volume, source in PDF_SOURCES.items()
            },
            "api_snapshot": {
                "path": str(api_path.resolve()),
                "source_url": API_SNAPSHOT["source_url"],
                "sha256": API_SNAPSHOT["sha256"],
            },
            "static_snapshot": {
                "path": str(static_path.resolve()),
                "source_url": STATIC_SNAPSHOT["source_url"],
                "sha256": STATIC_SNAPSHOT["sha256"],
            },
        },
        "records": records,
        "blocked": blocked,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    parser.add_argument("--volume-1-pdf", type=Path, default=PDF_SOURCES[1]["path"])
    parser.add_argument("--volume-2-pdf", type=Path, default=PDF_SOURCES[2]["path"])
    parser.add_argument("--api-snapshot", type=Path, default=API_SNAPSHOT["path"])
    parser.add_argument(
        "--static-snapshot", type=Path, default=STATIC_SNAPSHOT["path"]
    )
    args = parser.parse_args()

    manifest = build_manifest(
        {1: args.volume_1_pdf, 2: args.volume_2_pdf},
        args.api_snapshot,
        args.static_snapshot,
    )
    encoded = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    if manifest["blocked"]:
        print(json.dumps({"blocked": manifest["blocked"]}, ensure_ascii=False, indent=2))
    print(f"output={args.output}")
    print(f"manifest_sha256={file_sha256(args.output)}")


if __name__ == "__main__":
    main()
