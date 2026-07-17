"""Atomically import the reviewed Al-Kafi H1-H34 Sarwar PDF manifest.

Dry-run is the default.  ``--apply`` is accepted only when all 34 records need
the exact reviewed import or when all 34 are already in that state.  A partial
batch is rejected, so the opening chapter cannot silently become a mixture of
reviewed and stale states.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from build_alkafi_opening_sarwar_pdf_manifest import (
    API_SNAPSHOT_SHA256,
    CLASSIFICATION,
    DEFAULT_API_SNAPSHOT,
    DEFAULT_PDF,
    EXPECTED_COUNT,
    EXTRACTION_VERSION,
    PDF_SHA256,
    SOURCE_BOOK_ID,
    TARGET_MODEL,
    TARGET_PROVIDER,
    arabic_identity_score,
    canonical_json_sha256,
    english_chain_token_f1,
    exact_text_sha256,
    extract_pdf_records,
    file_sha256,
    load_api_snapshot,
    source_evidence_for_record,
)
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


JOB_KEY = "alkafi-opening-sarwar-pdf-verbatim-v1"
FORBIDDEN_AI_MARKERS = ("codex", "openai", "gpt-", "machine translation", "ai translation")


def _load_manifest(path: Path) -> tuple[dict[str, Any], str]:
    manifest_bytes = path.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") != 1:
        raise RuntimeError("Unsupported opening-Sarwar manifest schema")
    if manifest.get("extraction_version") != EXTRACTION_VERSION:
        raise RuntimeError("Manifest extraction version changed")
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_COUNT} manifest records")
    expected_ids = [f"alkafi-{number}" for number in range(1, EXPECTED_COUNT + 1)]
    if [record.get("public_id") for record in records] != expected_ids:
        raise RuntimeError("Manifest public-ID sequence is not exactly alkafi-1..alkafi-34")
    summary = manifest.get("summary") or {}
    if (
        summary.get("selected") != EXPECTED_COUNT
        or summary.get("source_classification") != CLASSIFICATION
        or summary.get("translator") != "Muhammad Sarwar"
        or summary.get("target_provider") != TARGET_PROVIDER
        or summary.get("target_model") != TARGET_MODEL
    ):
        raise RuntimeError("Manifest target/source summary changed")
    sources = manifest.get("sources") or {}
    if (sources.get("pdf") or {}).get("sha256") != PDF_SHA256:
        raise RuntimeError("Manifest PDF checksum is not the pinned checksum")
    if (sources.get("api_snapshot") or {}).get("sha256") != API_SNAPSHOT_SHA256:
        raise RuntimeError("Manifest API checksum is not the pinned checksum")
    return manifest, manifest_sha256


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
    if len(rows) > 1:
        raise RuntimeError(f"Multiple whole-matn segments for {hadith.public_id}")
    return rows[0] if rows else None


def _provenance(record: dict[str, Any], manifest_sha256: str) -> dict[str, Any]:
    return {
        "classification": CLASSIFICATION,
        "translation_method": "verbatim external source import; no model translation",
        "translator": "Muhammad Sarwar",
        "source_evidence": record["source_evidence"],
        "identity": record["identity"],
        "extraction_version": EXTRACTION_VERSION,
        "manifest_sha256": manifest_sha256,
        "editorial_operations": [],
    }


def _assert_no_ai_attribution(value: Any, public_id: str) -> None:
    flattened = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    found = [marker for marker in FORBIDDEN_AI_MARKERS if marker in flattened]
    if found:
        raise RuntimeError(f"Forbidden AI attribution for {public_id}: {found}")


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


def _translation_is_target(
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    hadith: Hadith,
    record: dict[str, Any],
    manifest_sha256: str,
) -> bool:
    provenance = _provenance(record, manifest_sha256)
    publication_flags = record["qa"]["publication_flags"]
    if translation is None or segment is None:
        return False
    translation_ok = (
        translation.language == "en"
        and translation.translation_version == TRANSLATION_VERSION
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
        and translation.source_isnad_sha256
        == (sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None)
        and translation.source_matn_sha256 == sha256_text(hadith.matn_raw)
        and translation.rendered_isnad_en == record["english_isnad"]
        and translation.matn_translation == record["english_matn"]
        and translation.full_translation is None
        and translation.status == "published"
        and translation.risk_level == "green"
        and translation.risk_flags == publication_flags
        and translation.provider == TARGET_PROVIDER
        and translation.model == TARGET_MODEL
        and translation.prompt_version == EXTRACTION_VERSION
        and translation.qa_version == QA_VERSION
        and translation.provenance_json == provenance
    )
    segment_ok = (
        segment.translation_id == translation.id
        and segment.source_text == hadith.matn_raw
        and segment.translation_text == record["english_matn"]
        and segment.status == "published"
        and segment.risk_level == "green"
        and segment.risk_flags == publication_flags
        and (segment.metadata_json or {}).get("extent") == "whole_matn"
        and (segment.metadata_json or {}).get("provider") == TARGET_PROVIDER
        and (segment.metadata_json or {}).get("model") == TARGET_MODEL
        and (segment.metadata_json or {}).get("translator") == "Muhammad Sarwar"
        and (segment.metadata_json or {}).get("classification") == CLASSIFICATION
        and (segment.metadata_json or {}).get("provenance") == provenance
    )
    return bool(translation_ok and segment_ok)


def _validate_record_sources(
    record: dict[str, Any],
    hadith: Hadith,
    pdf_record,
    api_record: dict[str, Any],
) -> None:
    number = int(record["sequence"])
    if record["public_id"] != hadith.public_id or number != hadith.sequence_in_book:
        raise RuntimeError(f"Local/manifest identity changed for {record['public_id']}")
    if hadith.volume_start != 1:
        raise RuntimeError(f"Local volume changed for {record['public_id']}")
    expected_local_hashes = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": (
            sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
        ),
        "source_matn_sha256": sha256_text(hadith.matn_raw),
    }
    for field, actual in expected_local_hashes.items():
        if record.get(field) != actual:
            raise RuntimeError(f"Local source hash changed for {record['public_id']}: {field}")

    if record["english_isnad"] != pdf_record.english_isnad:
        raise RuntimeError(f"PDF English chain changed for {record['public_id']}")
    if record["english_matn"] != pdf_record.english_matn:
        raise RuntimeError(f"PDF English matn changed for {record['public_id']}")
    if record["english_isnad_sha256"] != exact_text_sha256(pdf_record.english_isnad):
        raise RuntimeError(f"PDF English-chain hash changed for {record['public_id']}")
    if record["english_matn_sha256"] != pdf_record.matn_sha256:
        raise RuntimeError(f"PDF English-matn hash changed for {record['public_id']}")
    if record["source_evidence"] != source_evidence_for_record(
        number, pdf_record, api_record
    ):
        raise RuntimeError(f"Pinned source evidence changed for {record['public_id']}")
    if api_record.get("translator") != "Muhammad Sarwar":
        raise RuntimeError(f"API translator changed for {record['public_id']}")
    if canonical_json_sha256(api_record) != record["source_evidence"]["api_identity"]["record_sha256"]:
        raise RuntimeError(f"API record hash changed for {record['public_id']}")

    arabic_score = round(
        arabic_identity_score(hadith.full_text_raw, str(api_record["arabicText"])),
        8,
    )
    chain_score = round(
        english_chain_token_f1(
            pdf_record.english_isnad, str(api_record["thaqalaynSanad"])
        ),
        8,
    )
    if arabic_score != record["identity"]["arabic_sequence_score"]:
        raise RuntimeError(f"Arabic identity score changed for {record['public_id']}")
    if chain_score != record["identity"]["english_chain_token_f1"]:
        raise RuntimeError(f"English chain score changed for {record['public_id']}")
    if record["target"] != {
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "status": "published",
        "risk_level": "green",
        "classification": CLASSIFICATION,
        "editorial_operations": [],
    }:
        raise RuntimeError(f"Target declaration changed for {record['public_id']}")
    _assert_no_ai_attribution(
        {
            "target": record["target"],
            "source_evidence": record["source_evidence"],
            "english_isnad": record["english_isnad"],
            "english_matn": record["english_matn"],
        },
        record["public_id"],
    )


def _upsert_translation(
    db,
    hadith: Hadith,
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    record: dict[str, Any],
    manifest_sha256: str,
    now: dt.datetime,
) -> tuple[HadithTranslation, TranslationSegment]:
    provenance = _provenance(record, manifest_sha256)
    publication_flags = record["qa"]["publication_flags"]
    values = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": (
            sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
        ),
        "source_matn_sha256": sha256_text(hadith.matn_raw),
        "rendered_isnad_en": record["english_isnad"],
        "matn_translation": record["english_matn"],
        "full_translation": None,
        "status": "published",
        "risk_level": "green",
        "risk_flags": publication_flags,
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "prompt_version": EXTRACTION_VERSION,
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
        for field, value in values.items():
            setattr(translation, field, value)
    db.flush()

    segment_values = {
        "translation_id": translation.id,
        "source_text": hadith.matn_raw,
        "translation_text": record["english_matn"],
        "status": "published",
        "risk_level": "green",
        "risk_flags": publication_flags,
        "metadata_json": {
            "source_norm": source_norm(hadith.matn_raw),
            "extent": "whole_matn",
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
            "translator": "Muhammad Sarwar",
            "classification": CLASSIFICATION,
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
            source_sha256=sha256_text(hadith.matn_raw),
            created_at=now,
            **segment_values,
        )
        db.add(segment)
    else:
        for field, value in segment_values.items():
            setattr(segment, field, value)
    db.flush()
    return translation, segment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--api-snapshot", type=Path, default=DEFAULT_API_SNAPSHOT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest, manifest_sha256 = _load_manifest(args.manifest)
    if file_sha256(args.pdf).casefold() != PDF_SHA256:
        raise RuntimeError("Pinned PDF checksum changed")
    if file_sha256(args.api_snapshot).casefold() != API_SNAPSHOT_SHA256:
        raise RuntimeError("Pinned API snapshot checksum changed")
    pdf_records = extract_pdf_records(args.pdf)
    api_records = load_api_snapshot(args.api_snapshot)

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        hadiths = {
            row.public_id: row
            for row in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.sequence_in_book.between(1, EXPECTED_COUNT),
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
            ).scalars()
        }
        if set(hadiths) != {
            f"alkafi-{number}" for number in range(1, EXPECTED_COUNT + 1)
        }:
            raise RuntimeError("Local Al-Kafi opening set is no longer exactly H1-H34")
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                    HadithTranslation.hadith_id.in_([row.id for row in hadiths.values()]),
                )
            ).scalars()
        }

        reviewed: list[
            tuple[
                dict[str, Any],
                Hadith,
                HadithTranslation | None,
                TranslationSegment | None,
            ]
        ] = []
        selected = []
        for record in manifest["records"]:
            number = int(record["sequence"])
            hadith = hadiths[record["public_id"]]
            _validate_record_sources(
                record, hadith, pdf_records[number], api_records[number]
            )
            translation = translations.get(hadith.id)
            segment = _whole_matn_segment(db, hadith)
            entry = (record, hadith, translation, segment)
            reviewed.append(entry)
            if not _translation_is_target(
                translation, segment, hadith, record, manifest_sha256
            ):
                selected.append(entry)

        if len(selected) not in {0, EXPECTED_COUNT}:
            raise RuntimeError(
                f"Refusing partial opening import: {len(selected)} of {EXPECTED_COUNT} need changes"
            )
        # When a record still needs import, its current DB state must match the
        # state captured by the reviewed manifest.
        for record, _, translation, _ in selected:
            if _current_translation_payload(translation) != record["current_translation"]:
                raise RuntimeError(
                    f"Current translation changed after review: {record['public_id']}"
                )

        existing_job = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)
        ).scalar_one_or_none()
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "manifest_sha256": manifest_sha256,
                    "selected": len(selected),
                    "assertion": f"{EXPECTED_COUNT}-or-0",
                    "pdf_sha256": PDF_SHA256,
                    "api_snapshot_sha256": API_SNAPSHOT_SHA256,
                    "provider": TARGET_PROVIDER,
                    "model": TARGET_MODEL,
                    "translator": "Muhammad Sarwar",
                    "classification": CLASSIFICATION,
                },
                indent=2,
            )
        )
        if not args.apply:
            db.rollback()
            return
        if not selected:
            if existing_job is not None and (
                existing_job.status != "completed"
                or existing_job.hadith_count != EXPECTED_COUNT
                or existing_job.segment_count != EXPECTED_COUNT
            ):
                raise RuntimeError("Existing opening import job is not complete")
            db.rollback()
            print("already_applied=34")
            return
        if existing_job is not None:
            raise RuntimeError(f"Import job already exists while batch is incomplete: {JOB_KEY}")

        now = dt.datetime.now(dt.timezone.utc)
        job = TranslationJob(
            job_key=JOB_KEY,
            source_book_id=SOURCE_BOOK_ID,
            language="en",
            status="running",
            provider=TARGET_PROVIDER,
            model=TARGET_MODEL,
            prompt_version=EXTRACTION_VERSION,
            glossary_version=None,
            scope_json={
                "manifest_sha256": manifest_sha256,
                "public_ids": [record["public_id"] for record in manifest["records"]],
                "pdf_sha256": PDF_SHA256,
                "api_snapshot_sha256": API_SNAPSHOT_SHA256,
                "classification": CLASSIFICATION,
            },
            batch_policy_json={
                "source": "checksum-pinned published Muhammad Sarwar PDF",
                "identity": "canonical Thaqalayn URL plus Arabic and English-chain cross-check",
                "translation_generation": "none",
                "atomic_cardinality": f"{EXPECTED_COUNT}-or-0",
            },
            hadith_count=0,
            segment_count=0,
            input_chars=sum(len(hadith.matn_raw) for _, hadith, _, _ in selected),
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            estimated_cost_usd=0.0,
            created_at=now,
            updated_at=now,
            started_at=now,
        )
        db.add(job)
        db.flush()

        for item_index, (record, hadith, translation, segment) in enumerate(
            selected, start=1
        ):
            translation, segment = _upsert_translation(
                db,
                hadith,
                translation,
                segment,
                record,
                manifest_sha256,
                now,
            )
            if not _translation_is_target(
                translation, segment, hadith, record, manifest_sha256
            ):
                raise RuntimeError(f"Post-upsert target validation failed: {hadith.public_id}")
            item = TranslationJobItem(
                job_id=job.id,
                hadith_id=hadith.id,
                segment_id=segment.id,
                item_index=item_index,
                source_sha256=sha256_text(hadith.matn_raw),
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
                    provider=TARGET_PROVIDER,
                    model=TARGET_MODEL,
                    status="completed",
                    request_json={
                        "classification": CLASSIFICATION,
                        "source_evidence": record["source_evidence"],
                        "identity": record["identity"],
                        "source_full_sha256": record["source_full_sha256"],
                        "source_matn_sha256": record["source_matn_sha256"],
                    },
                    response_json={
                        "published": True,
                        "translation_method": "verbatim external source import",
                        "english_isnad_sha256": record["english_isnad_sha256"],
                        "english_matn_sha256": record["english_matn_sha256"],
                        "qa": record["qa"],
                    },
                    input_tokens=0,
                    output_tokens=0,
                    cost_estimate_usd=0.0,
                    created_at=now,
                )
            )

        job.hadith_count = EXPECTED_COUNT
        job.segment_count = EXPECTED_COUNT
        job.status = "completed"
        job.completed_at = now
        job.updated_at = now
        db.commit()
        print(f"committed={EXPECTED_COUNT}")


if __name__ == "__main__":
    main()
