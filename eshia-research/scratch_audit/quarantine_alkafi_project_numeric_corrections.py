"""Remove the final two project-edited English rows from public Al-Kafi.

The upstream Sarwar text contains numerical errors relative to the local
Arabic.  Earlier project code silently corrected those numbers.  The user now
requires strictly external human-source English, so these rows remain hidden
until an external published correction can be cited.  Dry-run is the default.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eshia_research.db import SessionLocal
from eshia_research.models import (
    Hadith,
    HadithTranslation,
    TranslationJobItem,
)
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import sha256_text


TARGETS = {"alkafi-1282", "alkafi-1292"}
EXPECTED_CLASSIFICATION = "externally_sourced_numeric_correction"
FLAG = {
    "code": "project_editorial_change_prohibited",
    "severity": "critical",
    "detail": (
        "The English altered numbers in the external edition and is hidden "
        "until the correction is supported by a citable human source."
    ),
}


def _add_flag(flags: object) -> list:
    result = list(flags) if isinstance(flags, list) else []
    if not any(isinstance(flag, dict) and flag.get("code") == FLAG["code"] for flag in result):
        result.append(FLAG)
    return result


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
                .where(
                    Hadith.public_id.in_(TARGETS),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
                .options(
                    selectinload(HadithTranslation.hadith),
                    selectinload(HadithTranslation.segments),
                )
            ).scalars()
        )
        if {row.hadith.public_id for row in rows} != TARGETS:
            raise RuntimeError("Did not resolve exactly both numeric-correction rows")

        active = [
            row
            for row in rows
            if row.status != "rejected" or row.matn_translation is not None
        ]
        if len(active) not in {0, 2}:
            raise RuntimeError(f"Refusing partial quarantine state: {len(active)}")

        changed_segments = 0
        changed_items = 0
        removed_hashes: dict[str, str] = {}
        for translation in active:
            hadith = translation.hadith
            provenance = dict(translation.provenance_json or {})
            if provenance.get("translation_classification") != EXPECTED_CLASSIFICATION:
                raise RuntimeError(f"Unexpected classification for {hadith.public_id}")
            if not translation.matn_translation:
                raise RuntimeError(f"Missing current English for {hadith.public_id}")
            removed_hash = sha256_text(translation.matn_translation)
            if provenance.get("rendered_english_sha256") != removed_hash:
                raise RuntimeError(f"Rendered-English evidence mismatch for {hadith.public_id}")
            if not provenance.get("original_source_english_sha256"):
                raise RuntimeError(f"Missing original source hash for {hadith.public_id}")
            removed_hashes[hadith.public_id] = removed_hash

            provenance.update(
                {
                    "publication_status": "rejected",
                    "reason": FLAG["code"],
                    "removed_english_sha256": removed_hash,
                    "translation_classification": "project_authored_prohibited",
                    "audited_at": now.isoformat(),
                }
            )
            translation.provenance_json = provenance
            translation.matn_translation = None
            translation.full_translation = None
            translation.status = "rejected"
            translation.risk_level = "red"
            translation.risk_flags = _add_flag(translation.risk_flags)
            translation.updated_at = now

            segment_ids: list[int] = []
            for segment in translation.segments:
                if segment.translation_text not in {None, ""} and sha256_text(
                    segment.translation_text
                ) != removed_hash:
                    raise RuntimeError(f"Segment English mismatch for {hadith.public_id}")
                segment.translation_text = None
                segment.status = "qa_failed"
                segment.risk_level = "red"
                segment.risk_flags = _add_flag(segment.risk_flags)
                metadata = dict(segment.metadata_json or {})
                metadata.update(
                    {
                        "publication_status": "rejected",
                        "translation_text_redacted": True,
                        "reason": FLAG["code"],
                    }
                )
                segment.metadata_json = metadata
                segment.updated_at = now
                segment_ids.append(segment.id)
                changed_segments += 1

            if segment_ids:
                items = list(
                    db.execute(
                        select(TranslationJobItem).where(
                            TranslationJobItem.hadith_id == hadith.id,
                            TranslationJobItem.segment_id.in_(segment_ids),
                        )
                    ).scalars()
                )
                for item in items:
                    item.status = "qa_failed"
                    item.risk_level = "red"
                    item.updated_at = now
                    changed_items += 1

        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "selected_rows": len(active),
            "changed_segments": changed_segments,
            "changed_job_items": changed_items,
            "removed_english_sha256": removed_hashes,
            "english_replacements": 0,
            "arabic_text_changes": 0,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not args.apply:
            db.rollback()
            return
        db.commit()


if __name__ == "__main__":
    main()
