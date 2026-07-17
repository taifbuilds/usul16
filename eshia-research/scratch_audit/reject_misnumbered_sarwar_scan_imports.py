"""Reject the 62 Sarwar scan imports invalidated by edition-number drift.

The published scans are genuine Muhammad Sarwar sources, but their printed
global H numbers do not align with the ThaqalaynData/static global numbering in
the affected ranges.  The prior importer joined on that incompatible number.
This correction preserves every audit row while removing the translations
from public/green status.  Dry-run is the default.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import (
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)


JOB_KEY = "alkafi-sarwar-179-source-recovery-v1"
EXPECTED = 62
FLAG = {
    "code": "incompatible_edition_h_number",
    "severity": "critical",
    "detail": (
        "Post-import audit found that the published Sarwar scan and the static "
        "edition use incompatible global H-number sequences in this range; "
        "the English source is genuine but belongs to a different report."
    ),
}


def add_flag(value: list | None) -> list:
    flags = list(value or [])
    if not any(isinstance(flag, dict) and flag.get("code") == FLAG["code"] for flag in flags):
        flags.append(FLAG)
    return flags


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with SessionLocal() as db:
        translations = list(
            db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.provider == "sarwar-published-scan",
                    HadithTranslation.model == "muhammad-sarwar",
                    HadithTranslation.prompt_version == "sarwar_179_arabic_anchor_v1",
                )
            ).scalars()
        )
        if len(translations) != EXPECTED:
            raise RuntimeError(
                f"Expected exactly {EXPECTED} affected scan imports; found {len(translations)}"
            )
        hadith_ids = {translation.hadith_id for translation in translations}
        public_ids = sorted(
            db.get(Hadith, hadith_id).public_id for hadith_id in hadith_ids
        )
        job = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)
        ).scalar_one()
        items = list(
            db.execute(
                select(TranslationJobItem).where(
                    TranslationJobItem.job_id == job.id,
                    TranslationJobItem.hadith_id.in_(hadith_ids),
                )
            ).scalars()
        )
        if len(items) != EXPECTED:
            raise RuntimeError(f"Expected {EXPECTED} affected job items; found {len(items)}")
        item_ids = {item.id for item in items}
        attempts = list(
            db.execute(
                select(TranslationAttempt).where(
                    TranslationAttempt.job_id == job.id,
                    TranslationAttempt.item_id.in_(item_ids),
                )
            ).scalars()
        )
        if len(attempts) != EXPECTED:
            raise RuntimeError(f"Expected {EXPECTED} affected attempts; found {len(attempts)}")
        segments = list(
            db.execute(
                select(TranslationSegment).where(
                    TranslationSegment.translation_id.in_(
                        {translation.id for translation in translations}
                    )
                )
            ).scalars()
        )
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "affected_translations": len(translations),
                    "affected_segments": len(segments),
                    "affected_job_items": len(items),
                    "affected_attempts": len(attempts),
                    "first_public_id": public_ids[0],
                    "last_public_id": public_ids[-1],
                },
                indent=2,
            )
        )
        if not args.apply:
            db.rollback()
            return

        now = dt.datetime.now(dt.timezone.utc)
        for translation in translations:
            translation.status = "rejected"
            translation.risk_level = "red"
            translation.risk_flags = add_flag(translation.risk_flags)
            provenance = dict(translation.provenance_json or {})
            provenance["post_import_audit"] = {
                "status": "rejected",
                "reason": FLAG["code"],
                "audited_at": now.isoformat(),
            }
            translation.provenance_json = provenance
            translation.updated_at = now
        for segment in segments:
            segment.status = "qa_failed"
            segment.risk_level = "red"
            segment.risk_flags = add_flag(segment.risk_flags)
            metadata = dict(segment.metadata_json or {})
            metadata["post_import_audit"] = {
                "status": "rejected",
                "reason": FLAG["code"],
                "audited_at": now.isoformat(),
            }
            segment.metadata_json = metadata
            segment.updated_at = now
        for item in items:
            item.status = "qa_failed"
            item.risk_level = "red"
            item.updated_at = now
        for attempt in attempts:
            response = dict(attempt.response_json or {})
            response["post_import_audit"] = {
                "status": "rejected",
                "reason": FLAG["code"],
                "audited_at": now.isoformat(),
            }
            attempt.response_json = response
        job.hadith_count = 47
        job.segment_count = 47
        scope = dict(job.scope_json or {})
        scope["post_import_audit"] = {
            "accepted": 47,
            "rejected": EXPECTED,
            "reason": FLAG["code"],
            "audited_at": now.isoformat(),
        }
        job.scope_json = scope
        job.updated_at = now
        db.commit()
        print(f"rejected={EXPECTED}")


if __name__ == "__main__":
    main()
