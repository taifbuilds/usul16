"""Apply the reviewed 26-report Al-Kafi deep-scan recovery manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)
from eshia_research.translation import QA_VERSION, TRANSLATION_VERSION
from eshia_research.translation.text import clean_ws, sha256_text, source_norm


JOB_KEY = "alkafi-deep-scan-recovery-v1"
MATCHER = "alkafi_arabic_content_deep_scan_v1"
EXPECTED = 26
PUBLIC = {"machine_verified", "human_reviewed", "published"}


def is_public(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    payload = json.loads(manifest_bytes)
    records = payload["records"]
    if payload["summary"]["selected"] != EXPECTED or len(records) != EXPECTED:
        raise RuntimeError(f"Expected {EXPECTED} reviewed records; found {len(records)}")
    public_ids = [record["public_id"] for record in records]
    if len(set(public_ids)) != EXPECTED:
        raise RuntimeError("Duplicate public ID in reviewed manifest")

    with SessionLocal() as db:
        book = db.execute(select(Book).where(Book.source_book_id == "11005")).scalar_one()
        hadiths = {
            row.public_id: row
            for row in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
            ).scalars()
        }
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        }
        selected = []
        for record in records:
            hadith = hadiths.get(record["public_id"])
            if hadith is None:
                raise RuntimeError(f"Reviewed report disappeared: {record['public_id']}")
            if hadith.full_text_raw != record["arabic"] or hadith.matn_raw != record["matn"]:
                raise RuntimeError(f"Reviewed Arabic changed: {record['public_id']}")
            if sha256_text(hadith.full_text_raw) != record["source_full_sha256"]:
                raise RuntimeError(f"Reviewed full hash changed: {record['public_id']}")
            if sha256_text(hadith.matn_raw) != record["source_matn_sha256"]:
                raise RuntimeError(f"Reviewed matn hash changed: {record['public_id']}")
            english = clean_ws(record["english"])
            if not english:
                raise RuntimeError(f"Empty reviewed English: {record['public_id']}")
            lowered = english.casefold()
            forbidden = [
                marker for marker in ("hubeali.com", "(azwj)", "(saww)", "(asws)")
                if marker in lowered
            ]
            if forbidden:
                raise RuntimeError(f"Forbidden source marker for {record['public_id']}: {forbidden}")
            existing = translations.get(hadith.id)
            if is_public(existing, hadith):
                continue
            selected.append((record, hadith, existing, english))

        if len(selected) not in {0, EXPECTED}:
            raise RuntimeError(f"Refusing partial apply: {len(selected)} of {EXPECTED}")
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "manifest_sha256": manifest_sha,
                    "selected": len(selected),
                    "providers": {
                        provider: sum(row[0]["provider"] == provider for row in selected)
                        for provider in sorted({row[0]["provider"] for row in selected})
                    },
                    "editorially_modified": sum(
                        bool(row[0]["editorial_operations"]) for row in selected
                    ),
                },
                indent=2,
            )
        )
        if not args.apply or not selected:
            db.rollback()
            return

        if db.execute(select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)).scalar_one_or_none():
            raise RuntimeError(f"Audit job already exists while batch is incomplete: {JOB_KEY}")
        now = dt.datetime.now(dt.timezone.utc)
        job = TranslationJob(
            job_key=JOB_KEY,
            source_book_id="11005",
            language="en",
            status="running",
            provider="mixed-source-deep-scan",
            model="muhammad-sarwar-and-source-aligned-editorial",
            prompt_version=MATCHER,
            scope_json={
                "manifest_sha256": manifest_sha,
                "selected": EXPECTED,
                "public_ids": public_ids,
            },
            batch_policy_json={
                "identity": "Arabic content match; never global H-number cross-edition join",
                "source_priority": "Muhammad Sarwar with transparent bounded editorial recovery",
            },
            hadith_count=0,
            segment_count=0,
            input_chars=0,
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            estimated_cost_usd=0.0,
            created_at=now,
            updated_at=now,
            started_at=now,
        )
        db.add(job)
        db.flush()
        for item_index, (record, hadith, translation, english) in enumerate(selected, start=1):
            provenance = {
                "source": "Thaqalayn Arabic/content crosswalk",
                "source_url": record["source_url"],
                "additional_source_urls": record["additional_source_urls"],
                "remote_id": record["remote_id"],
                "translator": "Muhammad Sarwar",
                "arabic_match_score": record["arabic_match_score"],
                "runner_up_margin": record["runner_up_margin"],
                "editorial_operations": record["editorial_operations"],
                "original_source_english_sha256": sha256_text(
                    record["original_source_english"] or english
                ),
                "review_basis": record["review_basis"],
                "matcher_version": MATCHER,
                "manifest_sha256": manifest_sha,
            }
            values = {
                "source_full_sha256": sha256_text(hadith.full_text_raw),
                "source_isnad_sha256": sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None,
                "source_matn_sha256": sha256_text(hadith.matn_raw),
                "rendered_isnad_en": None,
                "matn_translation": english,
                "full_translation": None,
                "status": "published",
                "risk_level": "green",
                "risk_flags": record["qa_flags"],
                "provider": record["provider"],
                "model": record["model"],
                "prompt_version": MATCHER,
                "glossary_version": None,
                "qa_version": QA_VERSION,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_estimate_usd": 0.0,
                "provenance_json": provenance,
                "updated_at": now,
            }
            if translation is None:
                translation = HadithTranslation(
                    hadith_id=hadith.id,
                    language="en",
                    translation_version=TRANSLATION_VERSION,
                    created_at=now,
                    **values,
                )
                db.add(translation)
            else:
                for key, value in values.items():
                    setattr(translation, key, value)
            db.flush()

            source_hash = sha256_text(hadith.matn_raw)
            segment = db.execute(
                select(TranslationSegment).where(
                    TranslationSegment.hadith_id == hadith.id,
                    TranslationSegment.language == "en",
                    TranslationSegment.translation_version == TRANSLATION_VERSION,
                    TranslationSegment.segment_kind == "matn",
                    TranslationSegment.segment_index == 0,
                    TranslationSegment.source_sha256 == source_hash,
                )
            ).scalar_one_or_none()
            segment_values = {
                "translation_id": translation.id,
                "source_text": hadith.matn_raw,
                "translation_text": english,
                "status": "published",
                "risk_level": "green",
                "risk_flags": record["qa_flags"],
                "metadata_json": {
                    "source_norm": source_norm(hadith.matn_raw),
                    "provider": record["provider"],
                    "provenance": provenance,
                },
                "updated_at": now,
            }
            if segment is None:
                segment = TranslationSegment(
                    hadith_id=hadith.id,
                    language="en",
                    translation_version=TRANSLATION_VERSION,
                    segment_kind="matn",
                    segment_index=0,
                    source_sha256=source_hash,
                    created_at=now,
                    **segment_values,
                )
                db.add(segment)
            else:
                for key, value in segment_values.items():
                    setattr(segment, key, value)
            db.flush()

            item = TranslationJobItem(
                job_id=job.id,
                hadith_id=hadith.id,
                segment_id=segment.id,
                item_index=item_index,
                source_sha256=source_hash,
                status="verified",
                risk_level="green",
                created_at=now,
                updated_at=now,
            )
            db.add(item)
            db.flush()
            db.add(
                TranslationAttempt(
                    job_id=job.id,
                    item_id=item.id,
                    provider=record["provider"],
                    model=record["model"],
                    status="completed",
                    request_json={
                        "source_url": record["source_url"],
                        "remote_id": record["remote_id"],
                        "arabic_match_score": record["arabic_match_score"],
                    },
                    response_json={
                        "published": True,
                        "editorial_operations": record["editorial_operations"],
                        "qa_flags": record["qa_flags"],
                    },
                    input_tokens=0,
                    output_tokens=0,
                    cost_estimate_usd=0.0,
                    created_at=now,
                )
            )
        job.hadith_count = EXPECTED
        job.segment_count = EXPECTED
        job.status = "completed"
        job.completed_at = now
        job.updated_at = now
        db.commit()
        print(f"committed={EXPECTED}")


if __name__ == "__main__":
    main()
