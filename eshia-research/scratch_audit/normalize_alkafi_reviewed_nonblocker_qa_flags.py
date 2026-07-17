"""Finalize QA metadata for the 7,101 reviewed Al-Kafi non-blockers.

This is deliberately narrower than importer behavior.  New imports continue
to block number mismatches.  Here, a checksum-pinned exhaustive audit first
identified and quarantined all 75 deterministic pairing/extent blockers; only
the exact complement may have legacy draft-oriented diagnostics reclassified
as source-edition information.  No Arabic or English text is changed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import QA_VERSION, TRANSLATION_VERSION
from eshia_research.translation.publication import (
    has_forbidden_ai_marker,
    has_public_human_source_metadata,
    source_hashes_are_current,
)
from eshia_research.translation.text import sha256_text


SOURCE_BOOK_ID = "11005"
DEFAULT_DOSSIER = Path(
    "scratch_audit/alkafi_translation_extent_pairing_blockers_20260716.json"
)
DOSSIER_SHA256 = "d7744e88ecf8632500073be4c4f685d7737e9978ec04ca5d5810ef96929c5a94"
DOSSIER_SCHEMA = "alkafi_translation_extent_pairing_blockers_v2_compact"
QUARANTINE_VERSION = "alkafi_translation_extent_pairing_quarantine_v1"
NORMALIZATION_VERSION = "alkafi_reviewed_source_alignment_qa_v2"
NORMALIZED_QA_VERSION = f"{QA_VERSION}+reviewed_source_alignment_v2"
EXPECTED_BLOCKERS = 75
EXPECTED_REVIEWED_SAFE_ROWS = 7101
EXPECTED_NORMALIZATION_ROWS = 7082
EXPECTED_CLEAN_SOURCE_REPLACEMENTS = 19
EXPECTED_ORIGINAL_ROWS = 7176
EXPECTED_ORIGINAL_DIAGNOSTICS = Counter(
    {
        "number_mismatch": 7123,
        "missing_placeholder": 6093,
        "provider_refusal_text": 3,
    }
)
REPLACEMENT_DIAGNOSTICS = Counter(
    {"number_mismatch": 17, "missing_placeholder": 11}
)
REPLACEMENT_MANIFEST_SHA256 = (
    "a7aac51a7b05acfde507493f0f988cd6f2ad354a4aca6ba7fbf6f2469e7d5f97"
)
REPLACED_CRITICAL_IDS = {
    "alkafi-37",
    "alkafi-38",
    "alkafi-39",
    "alkafi-41",
    "alkafi-42",
    "alkafi-43",
    "alkafi-44",
    "alkafi-45",
    "alkafi-48",
    "alkafi-49",
    "alkafi-1444",
    "alkafi-1445",
    "alkafi-1446",
    "alkafi-1447",
    "alkafi-1448",
    "alkafi-1449",
    "alkafi-1459",
    "alkafi-1460",
    "alkafi-1461",
}
MAPPINGS = {
    "number_mismatch": (
        "reviewed_external_source_numbering_difference",
        "The published human edition uses different numbering or source "
        "apparatus. This row was retained only after the pairing/extent blocker audit.",
    ),
    "missing_placeholder": (
        "external_source_footnote_marker_difference",
        "Local Arabic editorial footnote markers are not interpolated into the "
        "published human-source English.",
    ),
    "provider_refusal_text": (
        "external_source_literal_phrase",
        "A refusal-like phrase occurs inside the pinned published narrative; "
        "it is source text, not a provider response.",
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_blocker_ids(path: Path) -> set[str]:
    if _sha256_file(path) != DOSSIER_SHA256:
        raise RuntimeError("Blocker dossier checksum changed")
    payload = json.loads(path.read_bytes())
    if payload.get("schema_version") != DOSSIER_SCHEMA:
        raise RuntimeError("Unexpected blocker dossier schema")
    columns = payload.get("record_columns") or []
    rows = payload.get("records") or []
    if len(rows) != EXPECTED_BLOCKERS:
        raise RuntimeError(f"Expected {EXPECTED_BLOCKERS} blocker records")
    public_index = columns.index("public_id")
    ids = {row[public_index] for row in rows}
    if len(ids) != EXPECTED_BLOCKERS:
        raise RuntimeError("Duplicate blocker public IDs")
    return ids


def _evidence_hashes(provenance: object) -> set[str]:
    if not isinstance(provenance, dict):
        return set()
    keys = (
        "source_plaintext_english_sha256",
        "source_english_sha256",
        "rendered_english_sha256",
        "original_source_english_sha256",
    )
    values = {
        value
        for key in keys
        if isinstance((value := provenance.get(key)), str) and value
    }
    evidence = provenance.get("source_evidence")
    if isinstance(evidence, dict):
        pdf = evidence.get("pdf")
        if isinstance(pdf, dict):
            for key in ("matn_sha256", "english_matn_sha256"):
                value = pdf.get(key)
                if isinstance(value, str) and value:
                    values.add(value)
    return values


def _critical_flags(flags: object) -> list[dict[str, Any]]:
    if not isinstance(flags, list):
        return []
    return [
        flag
        for flag in flags
        if isinstance(flag, dict) and flag.get("severity") == "critical"
    ]


def _review_diagnostics(flags: object) -> list[dict[str, Any]]:
    return [flag for flag in _critical_flags(flags) if flag.get("code") in MAPPINGS]


def _normalize_flags(flags: object) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in flags or []:
        if not isinstance(raw, dict):
            continue
        flag = dict(raw)
        mapped = MAPPINGS.get(str(flag.get("code", "")))
        if mapped is None:
            normalized.append(flag)
            continue
        code, detail = mapped
        normalized.append(
            {
                "code": code,
                "severity": "info",
                "detail": detail,
                "original_diagnostic": flag.get("detail"),
                "normalization_version": NORMALIZATION_VERSION,
                "blocker_dossier_sha256": DOSSIER_SHA256,
            }
        )
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    blocker_ids = _load_blocker_ids(args.dossier)
    now = dt.datetime.now(dt.timezone.utc)

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        blocker_rows = list(
            db.execute(
                select(HadithTranslation)
                .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_(blocker_ids),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
                .options(selectinload(HadithTranslation.hadith))
            ).scalars()
        )
        if len(blocker_rows) != EXPECTED_BLOCKERS:
            raise RuntimeError("Did not resolve every blocker translation")
        for row in blocker_rows:
            audit = (row.provenance_json or {}).get("source_alignment_audit") or {}
            if not (
                row.status == "rejected"
                and row.risk_level == "red"
                and row.matn_translation is None
                and audit.get("version") == QUARANTINE_VERSION
                and audit.get("dossier_sha256") == DOSSIER_SHA256
            ):
                raise RuntimeError(
                    f"Blocker is not safely quarantined: {row.hadith.public_id}"
                )

        rows = list(
            db.execute(
                select(HadithTranslation)
                .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.review_status != "rejected_non_hadith_fragment",
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                    HadithTranslation.status.in_(("human_reviewed", "published")),
                    HadithTranslation.risk_level == "green",
                )
                .options(
                    selectinload(HadithTranslation.hadith),
                    selectinload(HadithTranslation.segments),
                )
            ).scalars()
        )
        candidates = [row for row in rows if _review_diagnostics(row.risk_flags)]
        normalized_existing = [
            row
            for row in rows
            if isinstance(row.provenance_json, dict)
            and (row.provenance_json.get("qa_flag_normalization") or {}).get("version")
            == NORMALIZATION_VERSION
        ]
        if candidates and normalized_existing:
            raise RuntimeError("Refusing partial reviewed-normalization state")
        if candidates and len(candidates) != EXPECTED_NORMALIZATION_ROWS:
            raise RuntimeError(
                f"Expected {EXPECTED_NORMALIZATION_ROWS} reviewed non-blockers; "
                f"found {len(candidates)}"
            )
        if not candidates and len(normalized_existing) != EXPECTED_NORMALIZATION_ROWS:
            raise RuntimeError(
                "Neither the exact pre-normalization nor target state is present: "
                f"normalized={len(normalized_existing)}"
            )
        candidate_ids = {row.hadith.public_id for row in candidates}
        if candidate_ids & blocker_ids:
            raise RuntimeError("A quarantined blocker entered the normalization set")

        clean_replacements = [
            row for row in rows if row.hadith.public_id in REPLACED_CRITICAL_IDS
        ]
        if {row.hadith.public_id for row in clean_replacements} != REPLACED_CRITICAL_IDS:
            raise RuntimeError("The 19 clean source replacements are incomplete")
        for row in clean_replacements:
            provenance = row.provenance_json or {}
            if not (
                row.provider == "sarwar-published-scan"
                and row.status == "published"
                and row.risk_level == "green"
                and not _critical_flags(row.risk_flags)
                and isinstance(provenance, dict)
                and provenance.get("manifest_sha256") == REPLACEMENT_MANIFEST_SHA256
            ):
                raise RuntimeError(
                    f"Clean source replacement changed: {row.hadith.public_id}"
                )

        blocker_diagnostic_counts: Counter[str] = Counter(
            flag["code"]
            for row in blocker_rows
            for flag in _review_diagnostics(row.risk_flags)
        )
        candidate_diagnostic_counts: Counter[str] = Counter(
            flag["code"]
            for row in candidates
            for flag in _review_diagnostics(row.risk_flags)
        )
        if candidates and (
            candidate_diagnostic_counts
            + blocker_diagnostic_counts
            + REPLACEMENT_DIAGNOSTICS
            != EXPECTED_ORIGINAL_DIAGNOSTICS
        ):
            raise RuntimeError(
                "Reviewed complement does not reconstruct the original audit population: "
                f"safe={dict(candidate_diagnostic_counts)}, "
                f"blockers={dict(blocker_diagnostic_counts)}, "
                f"source_replacements={dict(REPLACEMENT_DIAGNOSTICS)}"
            )

        providers: Counter[str] = Counter()
        changed_segments = 0
        for translation in candidates:
            hadith = translation.hadith
            critical = _critical_flags(translation.risk_flags)
            unknown_critical = [
                flag for flag in critical if flag.get("code") not in MAPPINGS
            ]
            if unknown_critical:
                raise RuntimeError(
                    f"Unreviewed critical flags on {hadith.public_id}: {unknown_critical}"
                )
            if not translation.matn_translation:
                raise RuntimeError(f"Missing English for {hadith.public_id}")
            if not source_hashes_are_current(translation, hadith):
                raise RuntimeError(f"Stale Arabic source hashes for {hadith.public_id}")
            if has_forbidden_ai_marker(
                translation.provider,
                translation.model,
                translation.provenance_json,
            ):
                raise RuntimeError(f"Forbidden AI provenance for {hadith.public_id}")
            if not has_public_human_source_metadata(translation.provenance_json):
                raise RuntimeError(f"Missing human-source metadata for {hadith.public_id}")
            english_hash = sha256_text(translation.matn_translation)
            if english_hash not in _evidence_hashes(translation.provenance_json):
                raise RuntimeError(f"Pinned English evidence mismatch for {hadith.public_id}")
            public_segments = [
                segment
                for segment in translation.segments
                if segment.status == "published" and segment.risk_level == "green"
            ]
            if len(public_segments) != 1:
                raise RuntimeError(
                    f"Expected one public segment for {hadith.public_id}; "
                    f"found {len(public_segments)}"
                )
            segment = public_segments[0]
            if segment.translation_text != translation.matn_translation:
                raise RuntimeError(f"Segment English mismatch for {hadith.public_id}")

            original_codes = sorted(flag["code"] for flag in critical)
            audit = {
                "version": NORMALIZATION_VERSION,
                "basis": (
                    "checksum-pinned human-source text retained after exhaustive "
                    "pairing/extent audit and exact 75-row blocker quarantine"
                ),
                "normalized_original_codes": original_codes,
                "source_english_sha256": english_hash,
                "blocker_dossier": args.dossier.as_posix(),
                "blocker_dossier_sha256": DOSSIER_SHA256,
                "normalized_at": now.isoformat(),
            }
            normalized_flags = _normalize_flags(translation.risk_flags)
            if _critical_flags(normalized_flags):
                raise RuntimeError(f"Critical flag remains for {hadith.public_id}")
            provenance = dict(translation.provenance_json or {})
            provenance["qa_flag_normalization"] = audit
            translation.provenance_json = provenance
            translation.risk_flags = normalized_flags
            translation.qa_version = NORMALIZED_QA_VERSION
            translation.updated_at = now

            segment.risk_flags = _normalize_flags(segment.risk_flags)
            if _critical_flags(segment.risk_flags):
                raise RuntimeError(f"Critical segment flag remains for {hadith.public_id}")
            metadata = dict(segment.metadata_json or {})
            metadata["qa_flag_normalization"] = audit
            segment.metadata_json = metadata
            segment.updated_at = now
            changed_segments += 1
            providers[translation.provider or "unknown"] += 1

        # Autoflush projects the apply state during dry-run; the transaction is
        # rolled back below unless --apply was supplied.
        db.flush()
        remaining_public_critical = [
            row
            for row in rows
            if _critical_flags(row.risk_flags)
            and row.hadith.public_id not in blocker_ids
        ]
        if remaining_public_critical:
            sample = [row.hadith.public_id for row in remaining_public_critical[:10]]
            raise RuntimeError(
                f"Public rows retain critical flags: "
                f"{len(remaining_public_critical)} {sample}"
            )

        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "selected_rows": len(candidates),
            "assertion": f"{EXPECTED_NORMALIZATION_ROWS}-or-0",
            "quarantined_blockers": len(blocker_rows),
            "source_replacements_already_clean": len(clean_replacements),
            "reviewed_safe_population": EXPECTED_REVIEWED_SAFE_ROWS,
            "original_population": EXPECTED_ORIGINAL_ROWS,
            "safe_diagnostics": dict(sorted(candidate_diagnostic_counts.items())),
            "blocker_diagnostics": dict(sorted(blocker_diagnostic_counts.items())),
            "providers": dict(sorted(providers.items())),
            "changed_segments": changed_segments,
            "remaining_public_green_critical_rows": len(remaining_public_critical),
            "english_text_changes": 0,
            "arabic_text_changes": 0,
            "normalization_version": NORMALIZATION_VERSION,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        if not args.apply:
            db.rollback()
            return
        if not candidates:
            db.rollback()
            print(f"already_normalized={EXPECTED_NORMALIZATION_ROWS}")
            return
        db.commit()
        print(f"committed={EXPECTED_NORMALIZATION_ROWS}")


if __name__ == "__main__":
    main()
