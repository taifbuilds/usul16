"""Build the final atomic Sarwar repair manifest for wrong Al-Kafi pairings.

This script never writes to the database.  It creates a reproducible evidence
manifest for 53 of the 57 translations identified as wrong-English pairings in
the exhaustive extent/pairing dossier.  English is copied verbatim from either
the checksum-pinned Thaqalayn API snapshot (whose translator field is exactly
``Muhammad Sarwar``), the pinned static ``en_sarwar`` field, or an exact bounded
record in the checksum-pinned published Sarwar scan.  Matching Arabic and an
independent source witness are required for every selected report.

The remaining four records are deliberately emitted as quarantined.  No
translation is generated, inferred, or completed by this script.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for import_root in (SRC_ROOT, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from sqlalchemy import select

from build_alkafi_opening_sarwar_pdf_manifest import (
    _normalise_arabic_identity,
    arabic_identity_score,
    canonical_json_sha256,
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
from eshia_research.translation.text import sha256_text


SOURCE_BOOK_ID = "11005"
DOSSIER_SCHEMA = "alkafi_translation_extent_pairing_blockers_v2_compact"
DOSSIER_SHA256 = (
    "d7744e88ecf8632500073be4c4f685d7737e9978ec04ca5d5810ef96929c5a94"
)
API_SHA256 = (
    "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
)
STATIC_SHA256 = (
    "a0e57d41ae653a9f8d2b88dca4c0a3e149ce0a25b07ba3a880ffb461db920d43"
)
SCAN_MANIFEST_SHA256 = (
    "a229fe1dfbb4405508f6b235dbbec984123461fa96099b0e1524c524896d1d7d"
)
EXPECTED_DOSSIER_WRONG = 57
EXPECTED_REPAIRABLE = 53
EXPECTED_QUARANTINED = 4

DEFAULT_DOSSIER = Path(__file__).with_name(
    "alkafi_translation_extent_pairing_blockers_20260716.json"
)
DEFAULT_API = Path(
    os.path.expandvars(r"%TEMP%\sarwar-alkafi-audit\thaqalayn-api-alkafi.json")
)
DEFAULT_STATIC = Path(
    os.path.expandvars(r"%TEMP%\thaqalayn-al-kafi-static-full-fromzip.json")
)
DEFAULT_SCAN_MANIFEST = Path(__file__).with_name(
    "sarwar_scan_records_almurtaza_v1_v8_20260716.json"
)
DEFAULT_OUTPUT = Path(__file__).with_name(
    "alkafi_wrong_pair_sarwar_repair_manifest_20260716.json"
)

FORBIDDEN_AI_MARKERS = (
    "codex",
    "openai",
    "chatgpt",
    "gpt-",
    "machine-generated translation",
    "machine translation",
    "project-authored",
    "machine verified draft",
    "hubeali.com",
    "(asws)",
    "(saww)",
    "(azwj)",
)

# The API IDs are explicit review decisions, not fuzzy-match outputs at apply
# time.  All 44 must remain present and attributed to Muhammad Sarwar.
API_IDS: dict[str, int] = {
    "alkafi-187": 188,
    "alkafi-1126": 1124,
    "alkafi-1166": 1161,
    "alkafi-1196": 1190,
    "alkafi-1203": 1197,
    "alkafi-1205": 1199,
    "alkafi-1231": 1226,
    "alkafi-1237": 1232,
    "alkafi-1269": 1267,
    "alkafi-1299": 1301,
    "alkafi-1313": 1316,
    "alkafi-1315": 1318,
    "alkafi-1322": 1326,
    "alkafi-1335": 1340,
    "alkafi-1418": 1424,
    "alkafi-6873": 898,
    "alkafi-8264": 94,
    "alkafi-8304": 133,
    "alkafi-9073": 902,
    "alkafi-10843": 470,
    "alkafi-10846": 473,
    "alkafi-10847": 474,
    "alkafi-10848": 475,
    "alkafi-12723": 2193,
    "alkafi-12726": 2196,
    "alkafi-12727": 2197,
    "alkafi-12728": 2198,
    "alkafi-12730": 2200,
    "alkafi-12731": 2201,
    "alkafi-12732": 2202,
    "alkafi-12733": 2203,
    "alkafi-12734": 2204,
    "alkafi-12736": 2206,
    "alkafi-12740": 2210,
    "alkafi-12741": 2211,
    "alkafi-12742": 2212,
    "alkafi-12744": 2214,
    "alkafi-12747": 2217,
    "alkafi-12748": 2218,
    "alkafi-14454": 594,
    "alkafi-14455": 595,
    "alkafi-14456": 596,
    "alkafi-14457": 597,
    "alkafi-14458": 598,
}

# Exact human-source resolutions for reports whose API row is absent, shifted,
# or overmerged. ``scan`` imports the complete bounded H-marker extent.
# ``static`` imports the pinned ``en_sarwar`` field (optionally after a reviewed
# start marker) and requires an independent match to the published Sarwar scan.
SCAN_REPAIR_SPECS: dict[str, dict[str, Any]] = {
    "alkafi-368": {
        "volume": 1,
        "pdf_h": 366,
        "arabic_static_index": 373,
        "target_kind": "scan",
    },
    "alkafi-1114": {
        "volume": 1,
        "pdf_h": 1109,
        "arabic_static_index": 1121,
        "target_kind": "scan",
    },
    "alkafi-1154": {
        "volume": 1,
        "pdf_h": 1149,
        "arabic_static_index": 1161,
        "target_kind": "scan",
    },
    "alkafi-1161": {
        "volume": 1,
        "pdf_h": 1156,
        "arabic_static_index": 1168,
        "target_kind": "static",
        "target_static_index": 1166,
        "target_start": "Al-Husayn ibn Muhammad has narrated",
    },
    # API id 1160 is an upstream overmerge: its Arabic is this report, but its
    # English contains both this report and alkafi-1165. Use bounded H1159.
    "alkafi-1164": {
        "volume": 1,
        "pdf_h": 1159,
        "arabic_api_id": 1160,
        "arabic_static_index": 1171,
        "target_kind": "scan",
    },
    "alkafi-1165": {
        "volume": 1,
        "pdf_h": 1160,
        "arabic_static_index": 1172,
        "target_kind": "static",
        "target_static_index": 1169,
        "target_start": (
            "A number of our people has narrated from Ahmad ibn Muhammad "
            "ibn abu Nasr"
        ),
    },
    "alkafi-1263": {
        "volume": 1,
        "pdf_h": 1258,
        "arabic_static_index": 1272,
        "target_kind": "static",
        "target_static_index": 1273,
    },
    "alkafi-1342": {
        "volume": 1,
        "pdf_h": 1336,
        "arabic_static_index": 1359,
        "target_kind": "static",
        "target_static_index": 1360,
    },
    "alkafi-10545": {
        "volume": 6,
        "pdf_h": 10412,
        "arabic_static_index": 10554,
        "target_kind": "scan",
    },
}

# Reviewed global H-marker crosswalk in the checksum-pinned published scans.
# Volume 8 has no machine-readable H-marker text layer and is therefore absent;
# its PDF file remains checksum-pinned as bibliographic evidence.
PDF_H_BY_PUBLIC_ID: dict[str, int] = {
    "alkafi-187": 185,
    "alkafi-1126": 1121,
    "alkafi-1166": 1161,
    "alkafi-1196": 1191,
    "alkafi-1203": 1198,
    "alkafi-1205": 1200,
    "alkafi-1231": 1226,
    "alkafi-1237": 1232,
    "alkafi-1269": 1264,
    "alkafi-1299": 1293,
    "alkafi-1313": 1307,
    "alkafi-1315": 1309,
    "alkafi-1322": 1316,
    "alkafi-1335": 1329,
    "alkafi-1418": 1412,
    "alkafi-6873": 6863,
    "alkafi-8264": 8251,
    "alkafi-8304": 8290,
    "alkafi-9073": 9058,
    "alkafi-10843": 10711,
    "alkafi-10846": 10714,
    "alkafi-10847": 10715,
    "alkafi-10848": 10716,
    "alkafi-12723": 12432,
    "alkafi-12726": 12435,
    "alkafi-12727": 12436,
    "alkafi-12728": 12437,
    "alkafi-12730": 12439,
    "alkafi-12731": 12440,
    "alkafi-12732": 12441,
    "alkafi-12733": 12442,
    "alkafi-12734": 12443,
    "alkafi-12736": 12445,
    "alkafi-12740": 12449,
    "alkafi-12741": 12450,
    "alkafi-12742": 12451,
    "alkafi-12744": 12453,
    "alkafi-12747": 12456,
    "alkafi-12748": 12457,
    "alkafi-14454": 14151,
    "alkafi-14455": 14152,
    "alkafi-14456": 14153,
    "alkafi-14457": 14154,
    "alkafi-14458": 14155,
}

QUARANTINED_IDS = (
    "alkafi-11139",
    "alkafi-11140",
    "alkafi-15172",
    "alkafi-15286",
)
QUARANTINE_REASONS: dict[str, dict[str, str]] = {
    "alkafi-11139": {
        "status": "quarantined_sarwar_explicitly_omitted",
        "reason": (
            "Published Sarwar Volume 6 p282 explicitly states that the "
            "remaining slave/slave-girl chapters were not translated."
        ),
    },
    "alkafi-11140": {
        "status": "quarantined_sarwar_explicitly_omitted",
        "reason": (
            "Published Sarwar Volume 6 p282 explicitly states that the "
            "remaining slave/slave-girl chapters were not translated."
        ),
    },
    "alkafi-15172": {
        "status": "quarantined_no_published_sarwar_corroboration",
        "reason": (
            "The API English has no page-level published Sarwar witness; both "
            "public Volume 8 PDFs checked are HubeAli-branded."
        ),
    },
    "alkafi-15286": {
        "status": "quarantined_hubeali_only_false_sarwar_label",
        "reason": (
            "The available English is HubeAli-style text under a false "
            "en_sarwar label and is inadmissible under the source policy."
        ),
    },
}

if len(API_IDS) + len(SCAN_REPAIR_SPECS) != EXPECTED_REPAIRABLE:
    raise RuntimeError("Repair target cardinality changed")
if len(QUARANTINED_IDS) != EXPECTED_QUARANTINED:
    raise RuntimeError("Quarantine target cardinality changed")
if set(QUARANTINE_REASONS) != set(QUARANTINED_IDS):
    raise RuntimeError("Quarantine reason membership changed")
if set(API_IDS) & set(SCAN_REPAIR_SPECS):
    raise RuntimeError("API and scan/static repair sets overlap")
if (set(API_IDS) | set(SCAN_REPAIR_SPECS)) & set(QUARANTINED_IDS):
    raise RuntimeError("Repair and quarantine sets overlap")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _whole_matn_segment(db, hadith: Hadith) -> TranslationSegment | None:
    rows = list(
        db.execute(
            select(TranslationSegment).where(
                TranslationSegment.hadith_id == hadith.id,
                TranslationSegment.language == "en",
                TranslationSegment.translation_version == TRANSLATION_VERSION,
                TranslationSegment.segment_kind == "matn",
                TranslationSegment.segment_index == 0,
            )
        ).scalars()
    )
    _require(len(rows) <= 1, f"Multiple whole-matn segments: {hadith.public_id}")
    return rows[0] if rows else None


def _translation_payload(value: HadithTranslation | None) -> dict[str, Any]:
    if value is None:
        return {"translation_id": None}
    return {
        "translation_id": value.id,
        "provider": value.provider,
        "model": value.model,
        "status": value.status,
        "risk_level": value.risk_level,
        "source_full_sha256": value.source_full_sha256,
        "source_isnad_sha256": value.source_isnad_sha256,
        "source_matn_sha256": value.source_matn_sha256,
        "rendered_isnad_sha256": (
            exact_text_sha256(value.rendered_isnad_en)
            if value.rendered_isnad_en
            else None
        ),
        "matn_sha256": (
            exact_text_sha256(value.matn_translation)
            if value.matn_translation
            else None
        ),
        "provenance_sha256": canonical_json_sha256(value.provenance_json or {}),
    }


def _segment_payload(value: TranslationSegment | None) -> dict[str, Any]:
    if value is None:
        return {"segment_id": None}
    return {
        "segment_id": value.id,
        "translation_id": value.translation_id,
        "source_sha256": value.source_sha256,
        "translation_sha256": (
            exact_text_sha256(value.translation_text)
            if value.translation_text
            else None
        ),
        "status": value.status,
        "risk_level": value.risk_level,
        "metadata_sha256": canonical_json_sha256(value.metadata_json or {}),
    }


def _repair_mojibake(value: str) -> str:
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def _english_tokens(value: str) -> list[str]:
    value = _repair_mojibake(value or "")
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    return re.findall(r"[a-z0-9]+", value)


def _english_norm(value: str) -> str:
    return " ".join(_english_tokens(value))


def _ngrams(value: str, size: int = 5) -> set[str]:
    return {value[index : index + size] for index in range(len(value) - size + 1)}


def _token_coverage(needle: str, haystack: str) -> float:
    needle_tokens = Counter(_english_tokens(needle))
    haystack_tokens = Counter(_english_tokens(haystack))
    if not needle_tokens:
        return 0.0
    overlap = sum((needle_tokens & haystack_tokens).values())
    return overlap / sum(needle_tokens.values())


def _scan_index(records: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    index: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        item = dict(record)
        item["_english_norm"] = _english_norm(str(item.get("english") or ""))
        item["_ngrams"] = _ngrams(item["_english_norm"])
        index.setdefault(int(item["physical_volume"]), []).append(item)
    return index


def _pdf_witness(
    public_id: str,
    api_record: dict[str, Any],
    volume: int,
    records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    # The Volume 8 PDF is bibliographically pinned, but its text layer did not
    # expose parseable H-markers.  API+static Arabic remain independent pins.
    if not records:
        return None
    expected_h = PDF_H_BY_PUBLIC_ID[public_id]
    candidates = [
        record for record in records if int(record["hadith_number"]) == expected_h
    ]
    _require(
        len(candidates) == 1,
        f"Expected one published-scan H marker for {public_id}: {expected_h}",
    )
    record = candidates[0]
    api_english = str(api_record["englishText"]).strip()
    api_norm = _english_norm(api_english)
    sequence = difflib.SequenceMatcher(
        None, api_norm, record["_english_norm"], autojunk=False
    ).ratio()
    coverage = _token_coverage(api_english, str(record["english"]))
    _require(
        max(sequence, coverage) >= 0.72,
        f"No adequate published-scan witness for API id {api_record['id']}: "
        f"sequence={sequence:.4f}, coverage={coverage:.4f}",
    )
    return {
        "physical_volume": volume,
        "hadith_number": record["hadith_number"],
        "hadith_suffix": record.get("hadith_suffix"),
        "chapter_number": record.get("chapter_number"),
        "number_in_chapter": record.get("number_in_chapter"),
        "pdf_page": record["pdf_page"],
        "marker": record["marker"],
        "source_url": record["source_url"],
        "source_sha256": record["source_sha256"],
        "english_sha256": exact_text_sha256(str(record["english"])),
        "api_to_pdf_english_sequence_similarity": round(sequence, 6),
        "api_token_coverage_in_pdf_extent": round(coverage, 6),
        "witness_role": "published_scan_text_layer_corroboration",
    }


def _load_dossier(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    _require(file_sha256(path) == DOSSIER_SHA256, "Dossier checksum changed")
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(data.get("schema_version") == DOSSIER_SCHEMA, "Dossier schema changed")
    columns = data["record_columns"]
    wrong = {
        row[0]: dict(zip(columns, row, strict=True))
        for row in data["records"]
        if row[1] == "W"
    }
    _require(len(wrong) == EXPECTED_DOSSIER_WRONG, "Dossier W count changed")
    _require(
        set(wrong)
        == set(API_IDS) | set(SCAN_REPAIR_SPECS) | set(QUARANTINED_IDS),
        "Dossier W membership changed",
    )
    return data, wrong


def _api_records(data: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {
        (int(volume), int(record["id"])): record
        for volume, records in data.items()
        for record in records
    }


def _static_records(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record["source_url"]): record for record in data}


def _static_index(data: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    index = {int(record["index"]): record for record in data}
    _require(len(index) == len(data), "Duplicate static index")
    return index


def _arabic_shorter_coverage(left: str, right: str) -> float:
    left_norm = _normalise_arabic_identity(left)
    right_norm = _normalise_arabic_identity(right)
    if not left_norm or not right_norm:
        return 0.0
    shorter, longer = sorted((left_norm, right_norm), key=len)
    if shorter in longer:
        return 1.0
    matched = sum(
        block.size
        for block in difflib.SequenceMatcher(
            None, shorter, longer, autojunk=False
        ).get_matching_blocks()
    )
    return matched / len(shorter)


def _scan_record(
    records: list[dict[str, Any]], public_id: str, expected_h: int
) -> dict[str, Any]:
    candidates = [
        record for record in records if int(record["hadith_number"]) == expected_h
    ]
    _require(
        len(candidates) == 1,
        f"Expected one published-scan H marker for {public_id}: {expected_h}",
    )
    return candidates[0]


def _resolve_scan_repair(
    public_id: str,
    spec: dict[str, Any],
    hadith: Hadith,
    api_by_key: dict[tuple[int, int], dict[str, Any]],
    static_by_index: dict[int, dict[str, Any]],
    scan_by_volume: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    volume = int(spec["volume"])
    scan_record = _scan_record(
        scan_by_volume[volume], public_id, int(spec["pdf_h"])
    )
    scan_english = str(scan_record["english"]).strip()
    _require(bool(scan_english), f"Empty published-scan English: {public_id}")

    arabic_static = static_by_index[int(spec["arabic_static_index"])]
    static_full_score = arabic_identity_score(
        hadith.full_text_raw, str(arabic_static["arabic_text"])
    )
    static_matn_score = arabic_identity_score(
        hadith.matn_raw, str(arabic_static["arabic_text"])
    )
    static_coverage = max(
        _arabic_shorter_coverage(
            hadith.full_text_raw, str(arabic_static["arabic_text"])
        ),
        _arabic_shorter_coverage(
            hadith.matn_raw, str(arabic_static["arabic_text"])
        ),
    )

    arabic_api = None
    api_full_score = 0.0
    api_matn_score = 0.0
    api_coverage = 0.0
    if spec.get("arabic_api_id") is not None:
        arabic_api = api_by_key[(volume, int(spec["arabic_api_id"]))]
        _require(
            arabic_api.get("translator") == "Muhammad Sarwar",
            f"Arabic API witness attribution changed: {public_id}",
        )
        api_arabic = str(arabic_api["arabicText"])
        api_full_score = arabic_identity_score(hadith.full_text_raw, api_arabic)
        api_matn_score = arabic_identity_score(hadith.matn_raw, api_arabic)
        api_coverage = max(
            _arabic_shorter_coverage(hadith.full_text_raw, api_arabic),
            _arabic_shorter_coverage(hadith.matn_raw, api_arabic),
        )

    best_arabic_score = max(
        static_full_score,
        static_matn_score,
        static_coverage,
        api_full_score,
        api_matn_score,
        api_coverage,
    )
    _require(
        best_arabic_score >= 0.90,
        f"Exact Arabic identity gate failed: {public_id} ({best_arabic_score:.6f})",
    )

    target_kind = str(spec["target_kind"])
    if target_kind == "scan":
        english = scan_english
        target_source = {
            "kind": "published_sarwar_scan_bounded_h_record",
            "physical_volume": volume,
            "hadith_number": scan_record["hadith_number"],
            "hadith_suffix": scan_record.get("hadith_suffix"),
            "chapter_number": scan_record.get("chapter_number"),
            "number_in_chapter": scan_record.get("number_in_chapter"),
            "pdf_page": scan_record["pdf_page"],
            "marker": scan_record["marker"],
            "source_url": scan_record["source_url"],
            "source_sha256": scan_record["source_sha256"],
            "scan_record_english_sha256": exact_text_sha256(scan_english),
            "slice": "complete bounded H-marker extent",
        }
    elif target_kind == "static":
        target_static = static_by_index[int(spec["target_static_index"])]
        field_value = str(target_static.get("en_sarwar") or "").strip()
        _require(bool(field_value), f"Empty static en_sarwar field: {public_id}")
        start = spec.get("target_start")
        if start:
            _require(
                field_value.count(str(start)) == 1,
                f"Static target start marker changed: {public_id}",
            )
            english = field_value[field_value.index(str(start)) :].strip()
        else:
            english = field_value
        target_source = {
            "kind": "thaqalayn_static_en_sarwar",
            "index": target_static["index"],
            "url": target_static["source_url"],
            "record_sha256": canonical_json_sha256(target_static),
            "field": "en_sarwar",
            "field_sha256": exact_text_sha256(field_value),
            "slice_start": start,
            "snapshot_sha256": STATIC_SHA256,
        }
    else:
        raise RuntimeError(f"Unknown target kind for {public_id}: {target_kind}")

    lowered = english.casefold()
    found = [marker for marker in FORBIDDEN_AI_MARKERS if marker in lowered]
    _require(not found, f"Forbidden AI marker in target: {public_id}: {found}")
    pdf_sequence = difflib.SequenceMatcher(
        None, _english_norm(english), _english_norm(scan_english), autojunk=False
    ).ratio()
    pdf_coverage = _token_coverage(english, scan_english)
    _require(
        max(pdf_sequence, pdf_coverage) >= 0.80,
        f"Published Sarwar corroboration failed: {public_id} "
        f"({pdf_sequence:.6f}, {pdf_coverage:.6f})",
    )
    return {
        "english": english,
        "target_source": target_source,
        "arabic_static": arabic_static,
        "arabic_api": arabic_api,
        "scan_record": scan_record,
        "identity_metrics": {
            "static_full_arabic_sequence_similarity": round(static_full_score, 6),
            "static_matn_arabic_sequence_similarity": round(static_matn_score, 6),
            "static_shorter_arabic_coverage": round(static_coverage, 6),
            "api_full_arabic_sequence_similarity": round(api_full_score, 6),
            "api_matn_arabic_sequence_similarity": round(api_matn_score, 6),
            "api_shorter_arabic_coverage": round(api_coverage, 6),
            "best_arabic_identity_score": round(best_arabic_score, 6),
            "minimum_arabic_identity_score": 0.90,
            "target_to_pdf_english_sequence_similarity": round(pdf_sequence, 6),
            "target_token_coverage_in_pdf_extent": round(pdf_coverage, 6),
            "crosswalk": (
                "local Arabic -> exact pinned Arabic witness -> bounded human "
                "Muhammad Sarwar English -> published Sarwar PDF corroboration"
            ),
        },
    }


def _assert_human_source(api_record: dict[str, Any], public_id: str) -> str:
    _require(
        api_record.get("translator") == "Muhammad Sarwar",
        f"Non-Sarwar API record selected for {public_id}",
    )
    english = str(api_record.get("englishText") or "").strip()
    _require(bool(english), f"Empty API English for {public_id}")
    flattened = json.dumps(api_record, ensure_ascii=False).casefold()
    found = [marker for marker in FORBIDDEN_AI_MARKERS if marker in flattened]
    _require(not found, f"Forbidden AI marker for {public_id}: {found}")
    return english


def build_manifest(
    dossier_path: Path,
    api_path: Path,
    static_path: Path,
    scan_path: Path,
) -> dict[str, Any]:
    _, dossier = _load_dossier(dossier_path)
    _require(file_sha256(api_path) == API_SHA256, "API snapshot checksum changed")
    _require(
        file_sha256(static_path) == STATIC_SHA256,
        "Static snapshot checksum changed",
    )
    _require(
        file_sha256(scan_path) == SCAN_MANIFEST_SHA256,
        "Scan-record manifest checksum changed",
    )
    api_data = json.loads(api_path.read_text(encoding="utf-8"))
    static_data = json.loads(static_path.read_text(encoding="utf-8"))
    scan_data = json.loads(scan_path.read_text(encoding="utf-8"))
    api_by_key = _api_records(api_data)
    static_by_url = _static_records(static_data)
    static_by_index = _static_index(static_data)
    scan_by_volume = _scan_index(scan_data["records"])
    pdf_sources = {int(item["volume"]): item for item in scan_data["manifest"]}

    # The locally cached Volume 8 PDF is a HubeAli publication, so it is
    # intentionally excluded from Sarwar evidence.  Volume 8 targets require
    # independently pinned API and static ``en_sarwar`` evidence instead.
    required_volumes = {1, 4, 5, 6, 7}
    for volume in required_volumes:
        source = pdf_sources[volume]
        pdf_path = Path(source["path"])
        _require(pdf_path.exists(), f"Pinned PDF missing: Volume {volume}")
        _require(
            file_sha256(pdf_path) == source["sha256"],
            f"Pinned PDF checksum changed: Volume {volume}",
        )

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        all_ids = list(API_IDS) + list(SCAN_REPAIR_SPECS) + list(QUARANTINED_IDS)
        hadiths = {
            item.public_id: item
            for item in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_(all_ids),
                )
            ).scalars()
        }
        _require(set(hadiths) == set(all_ids), "Local W target membership changed")
        translations = {
            item.hadith_id: item
            for item in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.hadith_id.in_(
                        [hadith.id for hadith in hadiths.values()]
                    ),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        }

        records: list[dict[str, Any]] = []
        for public_id, api_id in API_IDS.items():
            blocker = dossier[public_id]
            hadith = hadiths[public_id]
            translation = translations.get(hadith.id)
            segment = _whole_matn_segment(db, hadith)
            _require(translation is not None, f"Missing translation row: {public_id}")
            _require(
                translation.id == blocker["translation_id"],
                f"Translation identity changed: {public_id}",
            )
            _require(
                translation.status == "rejected"
                and translation.risk_level == "red"
                and translation.rendered_isnad_en is None
                and translation.matn_translation is None,
                f"Expected quarantined translation state: {public_id}",
            )
            provenance = translation.provenance_json or {}
            alignment = provenance.get("source_alignment_audit") or {}
            _require(
                alignment.get("dossier_sha256") == DOSSIER_SHA256,
                f"Quarantine dossier pin changed: {public_id}",
            )
            _require(
                provenance.get("removed_english_sha256")
                == blocker["english_sha256"],
                f"Removed-English pin changed: {public_id}",
            )

            api_record = api_by_key[(int(blocker["volume"]), api_id)]
            english = _assert_human_source(api_record, public_id)
            api_arabic_score = arabic_identity_score(
                hadith.full_text_raw, str(api_record["arabicText"])
            )
            api_matn_score = arabic_identity_score(
                hadith.matn_raw, str(api_record["arabicText"])
            )
            best_api_score = max(api_arabic_score, api_matn_score)
            minimum_api_score = 0.80
            _require(
                best_api_score >= minimum_api_score,
                f"API Arabic identity below threshold: {public_id} "
                f"({best_api_score:.6f})",
            )

            static_record = static_by_url.get(str(blocker["source_url"]))
            _require(static_record is not None, f"Missing static row: {public_id}")
            _require(
                canonical_json_sha256(static_record)
                == blocker["source_record_sha256"],
                f"Dossier static-record pin changed: {public_id}",
            )
            static_score = max(
                arabic_identity_score(
                    hadith.full_text_raw, str(static_record["arabic_text"])
                ),
                arabic_identity_score(
                    hadith.matn_raw, str(static_record["arabic_text"])
                ),
            )
            volume = int(blocker["volume"])
            pdf_witness = (
                _pdf_witness(
                    public_id, api_record, volume, scan_by_volume.get(volume, [])
                )
                if volume in required_volumes
                else None
            )
            pdf_source = pdf_sources.get(volume) if volume in required_volumes else None
            source_hashes = {
                "source_full_sha256": sha256_text(hadith.full_text_raw),
                "source_isnad_sha256": (
                    sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
                ),
                "source_matn_sha256": sha256_text(hadith.matn_raw),
            }
            records.append(
                {
                    "public_id": public_id,
                    "hadith_id": hadith.id,
                    "sequence_in_book": hadith.sequence_in_book,
                    "volume": volume,
                    "printed_number": hadith.printed_number,
                    **source_hashes,
                    "dossier_evidence": {
                        "category": blocker["category_key"],
                        "subcategory": blocker["subcategory_key"],
                        "evidence_key": blocker["evidence_key"],
                        "wrong_english_sha256": blocker["english_sha256"],
                        "wrong_source_record_sha256": blocker[
                            "source_record_sha256"
                        ],
                        "wrong_source_url": blocker["source_url"],
                    },
                    "api_source": {
                        "id": api_record["id"],
                        "url": api_record["URL"],
                        "translator": api_record["translator"],
                        "volume": api_record["volume"],
                        "record_sha256": canonical_json_sha256(api_record),
                        "arabic_sha256": exact_text_sha256(
                            str(api_record["arabicText"])
                        ),
                        "english_sha256": exact_text_sha256(english),
                        "snapshot_sha256": API_SHA256,
                    },
                    "target_source": {
                        "kind": "thaqalayn_api_muhammad_sarwar",
                        "id": api_record["id"],
                        "url": api_record["URL"],
                        "record_sha256": canonical_json_sha256(api_record),
                        "field": "englishText",
                        "field_sha256": exact_text_sha256(english),
                        "snapshot_sha256": API_SHA256,
                    },
                    "static_arabic_witness": {
                        "url": static_record["source_url"],
                        "index": static_record["index"],
                        "record_sha256": canonical_json_sha256(static_record),
                        "arabic_sha256": exact_text_sha256(
                            str(static_record["arabic_text"])
                        ),
                        "snapshot_sha256": STATIC_SHA256,
                    },
                    "published_pdf": (
                        {
                            "source_url": pdf_source["source_url"],
                            "source_sha256": pdf_source["sha256"],
                            "pages": pdf_source["pages"],
                            "text_layer_witness": pdf_witness,
                        }
                        if pdf_source is not None
                        else None
                    ),
                    "identity_metrics": {
                        "api_full_arabic_sequence_similarity": round(
                            api_arabic_score, 6
                        ),
                        "api_matn_arabic_sequence_similarity": round(
                            api_matn_score, 6
                        ),
                        "best_api_arabic_sequence_similarity": round(
                            best_api_score, 6
                        ),
                        "minimum_api_arabic_sequence_similarity": (
                            minimum_api_score
                        ),
                        "static_arabic_sequence_similarity": round(
                            static_score, 6
                        ),
                        "static_witness_role": (
                            "positive_arabic_identity_witness"
                            if static_score >= 0.72
                            else "negative_witness_confirming_prior_mispair"
                        ),
                        "crosswalk": (
                            "local Arabic -> pinned API Arabic -> exact API "
                            "Muhammad Sarwar English; original static Arabic "
                            "and, where a genuine Sarwar scan is available, "
                            "the published PDF is an independent witness"
                        ),
                    },
                    "target": {
                        "english": english,
                        "english_sha256": exact_text_sha256(english),
                        "provider": "thaqalayn-api",
                        "model": "muhammad-sarwar",
                        "translator": "Muhammad Sarwar",
                        "classification": "verbatim_external_matn_excerpt",
                        "status": "published",
                        "risk_level": "green",
                        "translation_method": (
                            "verbatim checksum-pinned human source import; "
                            "no model translation"
                        ),
                    },
                    "current_translation": _translation_payload(translation),
                    "current_segment": _segment_payload(segment),
                }
            )

        for public_id, spec in SCAN_REPAIR_SPECS.items():
            blocker = dossier[public_id]
            hadith = hadiths[public_id]
            translation = translations.get(hadith.id)
            segment = _whole_matn_segment(db, hadith)
            _require(translation is not None, f"Missing translation row: {public_id}")
            _require(
                translation.id == blocker["translation_id"],
                f"Translation identity changed: {public_id}",
            )
            _require(
                translation.status == "rejected"
                and translation.risk_level == "red"
                and translation.rendered_isnad_en is None
                and translation.matn_translation is None,
                f"Expected quarantined translation state: {public_id}",
            )
            provenance = translation.provenance_json or {}
            alignment = provenance.get("source_alignment_audit") or {}
            _require(
                alignment.get("dossier_sha256") == DOSSIER_SHA256,
                f"Quarantine dossier pin changed: {public_id}",
            )
            _require(
                provenance.get("removed_english_sha256")
                == blocker["english_sha256"],
                f"Removed-English pin changed: {public_id}",
            )
            _require(
                int(blocker["volume"]) == int(spec["volume"]),
                f"Volume crosswalk changed: {public_id}",
            )
            wrong_static = static_by_url.get(str(blocker["source_url"]))
            _require(wrong_static is not None, f"Missing dossier static row: {public_id}")
            _require(
                canonical_json_sha256(wrong_static)
                == blocker["source_record_sha256"],
                f"Dossier static-record pin changed: {public_id}",
            )

            resolved = _resolve_scan_repair(
                public_id,
                spec,
                hadith,
                api_by_key,
                static_by_index,
                scan_by_volume,
            )
            english = resolved["english"]
            volume = int(spec["volume"])
            scan_record = resolved["scan_record"]
            pdf_source = pdf_sources[volume]
            arabic_static = resolved["arabic_static"]
            arabic_api = resolved["arabic_api"]
            source_hashes = {
                "source_full_sha256": sha256_text(hadith.full_text_raw),
                "source_isnad_sha256": (
                    sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
                ),
                "source_matn_sha256": sha256_text(hadith.matn_raw),
            }
            records.append(
                {
                    "public_id": public_id,
                    "hadith_id": hadith.id,
                    "sequence_in_book": hadith.sequence_in_book,
                    "volume": volume,
                    "printed_number": hadith.printed_number,
                    **source_hashes,
                    "dossier_evidence": {
                        "category": blocker["category_key"],
                        "subcategory": blocker["subcategory_key"],
                        "evidence_key": blocker["evidence_key"],
                        "wrong_english_sha256": blocker["english_sha256"],
                        "wrong_source_record_sha256": blocker[
                            "source_record_sha256"
                        ],
                        "wrong_source_url": blocker["source_url"],
                    },
                    "api_source": (
                        {
                            "id": arabic_api["id"],
                            "url": arabic_api["URL"],
                            "translator": arabic_api["translator"],
                            "volume": arabic_api["volume"],
                            "record_sha256": canonical_json_sha256(arabic_api),
                            "arabic_sha256": exact_text_sha256(
                                str(arabic_api["arabicText"])
                            ),
                            "snapshot_sha256": API_SHA256,
                            "witness_role": (
                                "Arabic identity only; overmerged English is "
                                "explicitly excluded"
                            ),
                        }
                        if arabic_api is not None
                        else None
                    ),
                    "target_source": resolved["target_source"],
                    "static_arabic_witness": {
                        "url": arabic_static["source_url"],
                        "index": arabic_static["index"],
                        "record_sha256": canonical_json_sha256(arabic_static),
                        "arabic_sha256": exact_text_sha256(
                            str(arabic_static["arabic_text"])
                        ),
                        "snapshot_sha256": STATIC_SHA256,
                    },
                    "published_pdf": {
                        "source_url": pdf_source["source_url"],
                        "source_sha256": pdf_source["sha256"],
                        "pages": pdf_source["pages"],
                        "text_layer_witness": {
                            "physical_volume": volume,
                            "hadith_number": scan_record["hadith_number"],
                            "hadith_suffix": scan_record.get("hadith_suffix"),
                            "chapter_number": scan_record.get("chapter_number"),
                            "number_in_chapter": scan_record.get(
                                "number_in_chapter"
                            ),
                            "pdf_page": scan_record["pdf_page"],
                            "marker": scan_record["marker"],
                            "source_url": scan_record["source_url"],
                            "source_sha256": scan_record["source_sha256"],
                            "english_sha256": exact_text_sha256(
                                str(scan_record["english"]).strip()
                            ),
                            "target_to_pdf_english_sequence_similarity": resolved[
                                "identity_metrics"
                            ]["target_to_pdf_english_sequence_similarity"],
                            "target_token_coverage_in_pdf_extent": resolved[
                                "identity_metrics"
                            ]["target_token_coverage_in_pdf_extent"],
                            "witness_role": (
                                "published Sarwar scan exact target or "
                                "independent text corroboration"
                            ),
                        },
                    },
                    "identity_metrics": resolved["identity_metrics"],
                    "target": {
                        "english": english,
                        "english_sha256": exact_text_sha256(english),
                        "provider": (
                            "sarwar-published-scan"
                            if spec["target_kind"] == "scan"
                            else "thaqalayn-static-en-sarwar"
                        ),
                        "model": "muhammad-sarwar",
                        "translator": "Muhammad Sarwar",
                        "classification": "verbatim_external_matn_excerpt",
                        "status": "published",
                        "risk_level": "green",
                        "translation_method": (
                            "verbatim checksum-pinned human source import; "
                            "no model translation"
                        ),
                    },
                    "current_translation": _translation_payload(translation),
                    "current_segment": _segment_payload(segment),
                }
            )

        quarantined = []
        for public_id in QUARANTINED_IDS:
            blocker = dossier[public_id]
            hadith = hadiths[public_id]
            translation = translations.get(hadith.id)
            _require(translation is not None, f"Missing quarantine row: {public_id}")
            _require(
                translation.status == "rejected"
                and translation.risk_level == "red"
                and translation.rendered_isnad_en is None
                and translation.matn_translation is None,
                f"Weak row is no longer quarantined: {public_id}",
            )
            quarantined.append(
                {
                    "public_id": public_id,
                    "hadith_id": hadith.id,
                    "volume": blocker["volume"],
                    "evidence_key": blocker["evidence_key"],
                    **QUARANTINE_REASONS[public_id],
                    "wrong_english_sha256": blocker["english_sha256"],
                    "translation_id": translation.id,
                }
            )

    _require(len(records) == EXPECTED_REPAIRABLE, "Repair output count changed")
    _require(
        len(quarantined) == EXPECTED_QUARANTINED,
        "Quarantine output count changed",
    )
    return {
        "schema_version": "alkafi_wrong_pair_sarwar_repair_manifest_v2",
        "scope": {
            "book": "Al-Kafi",
            "source_book_id": SOURCE_BOOK_ID,
            "dossier_wrong_pair_count": EXPECTED_DOSSIER_WRONG,
            "repairable_count": EXPECTED_REPAIRABLE,
            "quarantined_count": EXPECTED_QUARANTINED,
            "atomic_apply_cardinality": f"{EXPECTED_REPAIRABLE}-or-0",
            "translation_generation": "none",
        },
        "source_pins": {
            "dossier_sha256": DOSSIER_SHA256,
            "api_snapshot_sha256": API_SHA256,
            "static_snapshot_sha256": STATIC_SHA256,
            "scan_manifest_sha256": SCAN_MANIFEST_SHA256,
            "pdf_sha256": {
                str(volume): pdf_sources[volume]["sha256"]
                for volume in sorted(required_volumes)
            },
        },
        "publication_policy": {
            "translator": "Muhammad Sarwar",
            "human_source_only": True,
            "codex_or_model_translation_allowed": False,
            "hubeali_field_used": False,
            "hubeali_branded_volume_8_pdf_excluded": True,
            "overmerged_api_english_allowed": False,
            "weak_or_unproven_rows_remain_quarantined": True,
        },
        "records": records,
        "quarantined": quarantined,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--api-snapshot", type=Path, default=DEFAULT_API)
    parser.add_argument("--static-snapshot", type=Path, default=DEFAULT_STATIC)
    parser.add_argument("--scan-manifest", type=Path, default=DEFAULT_SCAN_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(
        args.dossier,
        args.api_snapshot,
        args.static_snapshot,
        args.scan_manifest,
    )
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "manifest_sha256": hashlib.sha256(
                    payload.encode("utf-8")
                ).hexdigest(),
                "repairable": len(manifest["records"]),
                "quarantined": len(manifest["quarantined"]),
                "codex_translations": 0,
                "hubeali_target_fields": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
