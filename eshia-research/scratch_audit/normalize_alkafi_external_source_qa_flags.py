"""Normalize draft-oriented QA false positives on verified source imports.

Dry-run is the default.  This script never changes English or Arabic text.  It
only replaces three known generic-draft diagnostics with informational,
source-edition-specific flags after verifying that the current English still
matches its pinned provenance checksum.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import sha256_text
from eshia_research.translation.thaqalayn_importer import (
    SOURCE_IMPORT_DIAGNOSTIC_FLAGS,
    SOURCE_IMPORT_QA_VERSION,
    source_import_publication_flags,
)


SOURCE_BOOK_ID = "11005"
EXPECTED_ROWS = 7176
EXPECTED_DIAGNOSTICS = Counter(
    {
        "number_mismatch": 7123,
        "missing_placeholder": 6093,
        "provider_refusal_text": 3,
    }
)
NORMALIZATION_VERSION = "alkafi_external_source_qa_normalization_v1"


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
            value = pdf.get("matn_sha256")
            if isinstance(value, str) and value:
                values.add(value)
    return values


def _critical_source_diagnostics(flags: object) -> list[dict]:
    if not isinstance(flags, list):
        return []
    return [
        flag
        for flag in flags
        if isinstance(flag, dict)
        and flag.get("severity") == "critical"
        and flag.get("code") in SOURCE_IMPORT_DIAGNOSTIC_FLAGS
    ]


def _has_critical(flags: object) -> bool:
    return bool(
        isinstance(flags, list)
        and any(
            isinstance(flag, dict) and flag.get("severity") == "critical"
            for flag in flags
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    with SessionLocal() as db:
        rows = list(
            db.execute(
                select(HadithTranslation)
                .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
                .join(Book, Book.id == Hadith.book_id)
                .where(
                    Book.source_book_id == SOURCE_BOOK_ID,
                    Hadith.review_status != "rejected",
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
        candidates = [row for row in rows if _critical_source_diagnostics(row.risk_flags)]
        diagnostic_counts: Counter[str] = Counter(
            flag["code"]
            for row in candidates
            for flag in _critical_source_diagnostics(row.risk_flags)
        )
        if candidates and (
            len(candidates) != EXPECTED_ROWS or diagnostic_counts != EXPECTED_DIAGNOSTICS
        ):
            raise RuntimeError(
                "Refusing unexpected QA normalization set: "
                f"rows={len(candidates)} diagnostics={dict(diagnostic_counts)}"
            )

        changed_segments = 0
        providers: Counter[str] = Counter()
        for translation in candidates:
            hadith = translation.hadith
            if hadith is None or not translation.matn_translation:
                raise RuntimeError(f"Missing text/parent for translation {translation.id}")
            english_hash = sha256_text(translation.matn_translation)
            if english_hash not in _evidence_hashes(translation.provenance_json):
                raise RuntimeError(
                    f"Pinned English evidence mismatch for {hadith.public_id}"
                )

            published_segments = [
                segment
                for segment in translation.segments
                if segment.status == "published" and segment.risk_level == "green"
            ]
            if len(published_segments) != 1:
                raise RuntimeError(
                    f"Expected one public segment for {hadith.public_id}, "
                    f"found {len(published_segments)}"
                )
            segment = published_segments[0]
            if segment.translation_text != translation.matn_translation:
                raise RuntimeError(f"Segment text mismatch for {hadith.public_id}")

            original_codes = sorted(
                flag["code"] for flag in _critical_source_diagnostics(translation.risk_flags)
            )
            normalized_flags = source_import_publication_flags(translation.risk_flags)
            if _has_critical(normalized_flags):
                raise RuntimeError(
                    f"Unresolved critical flag after normalization: {hadith.public_id}"
                )
            audit = {
                "version": NORMALIZATION_VERSION,
                "basis": "checksum-pinned external human source text",
                "normalized_original_codes": original_codes,
                "source_english_sha256": english_hash,
                "normalized_at": now.isoformat(),
            }
            provenance = dict(translation.provenance_json or {})
            provenance["qa_flag_normalization"] = audit
            translation.provenance_json = provenance
            translation.risk_flags = normalized_flags
            translation.qa_version = SOURCE_IMPORT_QA_VERSION
            translation.updated_at = now

            segment.risk_flags = source_import_publication_flags(segment.risk_flags)
            if _has_critical(segment.risk_flags):
                raise RuntimeError(
                    f"Unresolved segment critical flag: {hadith.public_id}"
                )
            metadata = dict(segment.metadata_json or {})
            metadata["qa_flag_normalization"] = audit
            segment.metadata_json = metadata
            segment.updated_at = now
            changed_segments += 1
            providers[translation.provider or "unknown"] += 1

        remaining_critical = [row for row in rows if _has_critical(row.risk_flags)]
        if remaining_critical:
            sample = [row.hadith.public_id for row in remaining_critical[:10]]
            raise RuntimeError(
                f"Public green rows retain critical flags: {len(remaining_critical)} {sample}"
            )

        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "selected_rows": len(candidates),
            "changed_segments": changed_segments,
            "original_diagnostics": dict(sorted(diagnostic_counts.items())),
            "providers": dict(sorted(providers.items())),
            "remaining_public_green_critical_rows": len(remaining_critical),
            "english_text_changes": 0,
            "arabic_text_changes": 0,
            "normalization_version": NORMALIZATION_VERSION,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not args.apply:
            db.rollback()
            return
        db.commit()


if __name__ == "__main__":
    main()
