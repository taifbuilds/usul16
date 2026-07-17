"""Apply a reviewed Sarwar-only Al-Kafi rematch manifest.

This script is dry-run by default.  It accepts only volume-wide Arabic matches
above the normal importer threshold, with a clear runner-up margin, no remote
record already owned by another public translation, and no blocking QA flag.
It can replace a current HubeAli fallback or fill a currently unpublished row.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationJobItem,
)
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_importer import (
    IMPORT_BLOCKING_QA_CODES,
    MATCHER_VERSION,
    MIN_MATCH_SCORE,
    MODEL,
    PROVIDER,
    TranslationMatch,
    _get_or_create_job,
    _upsert_segment,
    _upsert_translation,
    match_norm,
    match_score_parts,
    match_words,
    parse_record,
)


JOB_KEY = "alkafi-sarwar-verified-global-rematch-v1"
MATCHER = "sarwar_api_verified_global_rematch_v1"
PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
MIN_MARGIN = 0.03


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("api_cache", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    api_payload = json.loads(args.api_cache.read_text(encoding="utf-8"))
    remote = {
        (int(volume), int(row["id"])): parse_record(row)
        for volume, rows in api_payload.items()
        for row in rows
    }
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

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
        api_owners: dict[tuple[int, int], str] = {}
        for public_id, hadith in hadiths.items():
            translation = translations.get(hadith.id)
            if translation is None or translation.provider != PROVIDER:
                continue
            provenance = translation.provenance_json or {}
            remote_id = provenance.get("thaqalayn_id")
            if remote_id is not None:
                api_owners[(hadith.volume_start or 0, int(remote_id))] = public_id

        selected: list[tuple[Hadith, HadithTranslation | None, TranslationMatch, float]] = []
        selected_remote: set[tuple[int, int]] = set()
        for item in manifest:
            score = float(item["best_score"])
            margin = float(item["margin"])
            if score < MIN_MATCH_SCORE or margin < MIN_MARGIN or item.get("blocking"):
                continue
            public_id = str(item["public_id"])
            hadith = hadiths.get(public_id)
            if hadith is None:
                raise RuntimeError(f"Manifest target is not a visible Al-Kafi row: {public_id}")
            translation = translations.get(hadith.id)
            kind = str(item["kind"])
            if kind == "hubeali":
                if translation is None or translation.model != "hubeali":
                    continue
            elif kind == "missing":
                if (
                    translation is not None
                    and translation.status in PUBLIC_STATUSES
                    and translation.risk_level == "green"
                    and clean_ws(translation.matn_translation)
                ):
                    continue
            else:
                raise RuntimeError(f"Unknown manifest kind for {public_id}: {kind}")

            key = (int(item["volume"]), int(item["best_id"]))
            owner = api_owners.get(key)
            if owner not in {None, public_id}:
                continue
            if key in selected_remote:
                raise RuntimeError(f"Remote Sarwar record selected twice: {key}")
            record = remote[key]
            actual_score = match_score_parts(
                local_full=match_norm(hadith.full_text_raw),
                local_matn=match_norm(hadith.matn_raw),
                local_full_words=match_words(hadith.full_text_raw),
                local_matn_words=match_words(hadith.matn_raw),
                remote=record,
            )
            if abs(actual_score - score) > 1e-9:
                raise RuntimeError(
                    f"Arabic match score changed for {public_id}: {score} -> {actual_score}"
                )
            if clean_ws(record.usable_translation) != clean_ws(item["english"]):
                raise RuntimeError(f"Cached Sarwar text changed for {public_id}")
            qa = assess_translation(hadith.matn_raw, record.usable_translation)
            flags = [flag.__dict__ for flag in qa.flags]
            blocking = [
                flag["code"] for flag in flags if flag["code"] in IMPORT_BLOCKING_QA_CODES
            ]
            if blocking:
                raise RuntimeError(f"Blocking translation QA for {public_id}: {blocking}")
            match = TranslationMatch(
                hadith_id=hadith.id,
                public_id=hadith.public_id,
                volume=hadith.volume_start or 0,
                thaqalayn_id=record.id,
                score=actual_score,
                url=record.url,
                english_text=record.usable_translation,
                rendered_isnad_en=record.thaqalayn_sanad,
                provider=PROVIDER,
                model=MODEL,
                source_name="thaqalayn-api",
                translator=record.translator or "Muhammad Sarwar",
                matcher_version=MATCHER,
                qa_risk_level=qa.risk_level,
                qa_flags=flags,
            )
            if not match.publishable:
                raise RuntimeError(f"Selected match is not publishable: {public_id}")
            selected.append((hadith, translation, match, margin))
            selected_remote.add(key)

        replacements = sum(translation is not None for _, translation, _, _ in selected)
        additions = len(selected) - replacements
        print(
            f"selected={len(selected)} replacements={replacements} additions={additions} "
            f"mode={'APPLY' if args.apply else 'DRY-RUN'}"
        )
        for hadith, translation, match, margin in selected:
            print(
                f"{hadith.public_id}\t{translation.model if translation else 'missing'}"
                f" -> {match.model}\tv{match.volume}:api-{match.thaqalayn_id}"
                f"\tscore={match.score:.6f}\tmargin={margin:.6f}\t{match.url}"
            )
        if not args.apply or not selected:
            db.rollback()
            return

        now = dt.datetime.now(dt.timezone.utc)
        job = _get_or_create_job(
            db,
            source_book_id="11005",
            match_count=len(selected),
            now=now,
            job_key=JOB_KEY,
            provider=PROVIDER,
            model=MODEL,
        )
        next_item_index = len(job.items) + 1
        for hadith, _, match, margin in selected:
            translation = _upsert_translation(db, hadith, match, now=now)
            segment = _upsert_segment(db, translation, hadith, match, now=now)
            job_item = TranslationJobItem(
                job_id=job.id,
                hadith_id=hadith.id,
                segment_id=segment.id,
                item_index=next_item_index,
                source_sha256=sha256_text(hadith.matn_raw),
                status="verified",
                risk_level="green",
                created_at=now,
                updated_at=now,
            )
            db.add(job_item)
            db.flush()
            db.add(
                TranslationAttempt(
                    job_id=job.id,
                    item_id=job_item.id,
                    provider=PROVIDER,
                    model=MODEL,
                    status="completed",
                    request_json={
                        "url": match.url,
                        "thaqalayn_id": match.thaqalayn_id,
                        "matcher": MATCHER,
                    },
                    response_json={
                        "match_score": match.score,
                        "runner_up_margin": margin,
                        "qa_risk_level": match.qa_risk_level,
                        "qa_flags": match.qa_flags,
                    },
                    input_tokens=0,
                    output_tokens=0,
                    cost_estimate_usd=0.0,
                    created_at=now,
                )
            )
            next_item_index += 1
        job.hadith_count = len(selected)
        job.segment_count = len(selected)
        job.status = "completed"
        job.completed_at = now
        job.updated_at = now
        db.commit()
        print(f"committed={len(selected)}")


if __name__ == "__main__":
    main()
