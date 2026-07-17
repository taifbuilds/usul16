"""Atomically import the 20 reviewed, checksum-pinned Sarwar PDF records.

Dry-run is the default.  ``--apply`` is accepted only when all 20 rows need
the exact import or when all 20 are already in that state.  Any blocked
manifest entry, source checksum change, local Arabic change, partial state, or
post-review source change aborts the transaction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from build_alkafi_remaining_sarwar_pdf_manifest import (
    API_SNAPSHOT,
    CLASSIFICATION,
    DEFAULT_OUTPUT,
    EXPECTED_COUNT,
    EXTRACTION_VERSION,
    FORBIDDEN_SOURCE_MARKERS,
    PDF_SOURCES,
    SOURCE_BOOK_ID,
    STATIC_SNAPSHOT,
    TARGET_MODEL,
    TARGET_PROVIDER,
    TARGET_SPECS,
    TargetSpec,
    _publication_qa,
    current_segment_payload,
    current_translation_payload,
    exact_text_sha256,
    extract_pdf_records,
    file_sha256,
    identity_payload,
    load_identity_sources,
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
from eshia_research.translation.text import sha256_text, source_norm


JOB_KEY = "alkafi-remaining-sarwar-pdf-verbatim-v1"
FORBIDDEN_AI_MARKERS = (
    "codex",
    "openai",
    "gpt-",
    "machine translation",
    "ai translation",
)


def _load_manifest(path: Path) -> tuple[dict[str, Any], str]:
    manifest_bytes = path.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") != 1:
        raise RuntimeError("Unsupported remaining-Sarwar manifest schema")
    if manifest.get("extraction_version") != EXTRACTION_VERSION:
        raise RuntimeError("Manifest extraction version changed")
    blocked = manifest.get("blocked")
    if not isinstance(blocked, list) or blocked:
        raise RuntimeError(
            f"Manifest contains blocked rows: "
            f"{[row.get('public_id') for row in blocked or []]}"
        )
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_COUNT} importable manifest records")
    expected_ids = [spec.public_id for spec in TARGET_SPECS]
    if [record.get("public_id") for record in records] != expected_ids:
        raise RuntimeError("Manifest public-ID order changed")
    summary = manifest.get("summary") or {}
    if (
        summary.get("expected") != EXPECTED_COUNT
        or summary.get("selected") != EXPECTED_COUNT
        or summary.get("blocked") != 0
        or summary.get("public_ids") != expected_ids
        or summary.get("source_classification") != CLASSIFICATION
        or summary.get("translator") != "Muhammad Sarwar"
        or summary.get("target_provider") != TARGET_PROVIDER
        or summary.get("target_model") != TARGET_MODEL
    ):
        raise RuntimeError("Manifest target/source summary changed")
    sources = manifest.get("sources") or {}
    pdfs = sources.get("pdfs") or {}
    for volume, source in PDF_SOURCES.items():
        if (pdfs.get(str(volume)) or {}).get("sha256") != source["sha256"]:
            raise RuntimeError(f"Manifest Volume {volume} PDF checksum changed")
    if (sources.get("api_snapshot") or {}).get("sha256") != API_SNAPSHOT["sha256"]:
        raise RuntimeError("Manifest API snapshot checksum changed")
    if (
        (sources.get("static_snapshot") or {}).get("sha256")
        != STATIC_SNAPSHOT["sha256"]
    ):
        raise RuntimeError("Manifest static snapshot checksum changed")
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
        "editorial_operations": record["target"]["editorial_operations"],
    }


def _segment_metadata(
    hadith: Hadith,
    record: dict[str, Any],
    manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "source_norm": source_norm(hadith.matn_raw),
        "extent": "whole_matn",
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "translator": "Muhammad Sarwar",
        "classification": CLASSIFICATION,
        "provenance": _provenance(record, manifest_sha256),
    }


def _assert_no_ai_attribution(value: Any, public_id: str) -> None:
    flattened = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    found = [marker for marker in FORBIDDEN_AI_MARKERS if marker in flattened]
    if found:
        raise RuntimeError(f"Forbidden AI attribution for {public_id}: {found}")


def _translation_is_target(
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    hadith: Hadith,
    record: dict[str, Any],
    manifest_sha256: str,
) -> bool:
    if translation is None or segment is None:
        return False
    provenance = _provenance(record, manifest_sha256)
    publication_flags = record["qa"]["publication_flags"]
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
        and translation.glossary_version is None
        and translation.qa_version == QA_VERSION
        and translation.input_tokens == 0
        and translation.output_tokens == 0
        and translation.cost_estimate_usd == 0.0
        and translation.provenance_json == provenance
    )
    segment_ok = (
        segment.translation_id == translation.id
        and segment.source_text == hadith.matn_raw
        and segment.source_sha256 == sha256_text(hadith.matn_raw)
        and segment.translation_text == record["english_matn"]
        and segment.status == "published"
        and segment.risk_level == "green"
        and segment.risk_flags == publication_flags
        and segment.metadata_json
        == _segment_metadata(hadith, record, manifest_sha256)
    )
    return bool(translation_ok and segment_ok)


def _validate_record_sources(
    spec: TargetSpec,
    record: dict[str, Any],
    hadith: Hadith,
    pdf_record,
    identity_source,
) -> None:
    if (
        record.get("public_id") != spec.public_id
        or record.get("sequence") != spec.sequence
        or hadith.public_id != spec.public_id
        or hadith.sequence_in_book != spec.sequence
        or hadith.volume_start != spec.local_volume
        or hadith.printed_number != spec.printed_number
    ):
        raise RuntimeError(f"Local/manifest identity changed for {spec.public_id}")
    if hadith.review_status == "rejected_non_hadith_fragment":
        raise RuntimeError(f"Local row is rejected: {spec.public_id}")
    local_hashes = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": (
            sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
        ),
        "source_matn_sha256": sha256_text(hadith.matn_raw),
    }
    for field, expected in local_hashes.items():
        if record.get(field) != expected:
            raise RuntimeError(f"Local source hash changed for {spec.public_id}: {field}")

    if record.get("english_isnad") != pdf_record.english_isnad:
        raise RuntimeError(f"PDF English isnad changed for {spec.public_id}")
    if record.get("english_matn") != pdf_record.english_matn:
        raise RuntimeError(f"PDF English matn changed for {spec.public_id}")
    if record.get("english_isnad_sha256") != exact_text_sha256(
        pdf_record.english_isnad
    ):
        raise RuntimeError(f"PDF English-isnad hash changed for {spec.public_id}")
    if record.get("english_matn_sha256") != exact_text_sha256(
        pdf_record.english_matn
    ):
        raise RuntimeError(f"PDF English-matn hash changed for {spec.public_id}")
    expected_evidence = source_evidence_for_record(
        spec, pdf_record, identity_source
    )
    if record.get("source_evidence") != expected_evidence:
        raise RuntimeError(f"Pinned source evidence changed for {spec.public_id}")
    expected_identity = identity_payload(
        spec, hadith, pdf_record, identity_source
    )
    if record.get("identity") != expected_identity:
        raise RuntimeError(f"Identity/extent evidence changed for {spec.public_id}")
    expected_qa = _publication_qa(hadith, pdf_record.english_matn)
    if record.get("qa") != expected_qa:
        raise RuntimeError(f"QA evidence changed for {spec.public_id}")
    expected_target = {
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "status": "published",
        "risk_level": "green",
        "classification": CLASSIFICATION,
        "editorial_operations": pdf_record.layout_operations,
    }
    if record.get("target") != expected_target:
        raise RuntimeError(f"Target declaration changed for {spec.public_id}")
    if identity_source.record.translator != "Muhammad Sarwar":
        raise RuntimeError(f"Translator attribution changed for {spec.public_id}")
    if any(
        marker in (record["english_isnad"] + " " + record["english_matn"]).casefold()
        for marker in FORBIDDEN_SOURCE_MARKERS
    ):
        raise RuntimeError(f"Forbidden source wording found for {spec.public_id}")
    _assert_no_ai_attribution(
        {
            "target": record["target"],
            "source_evidence": record["source_evidence"],
            "english_isnad": record["english_isnad"],
            "english_matn": record["english_matn"],
        },
        spec.public_id,
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
        "provenance_json": _provenance(record, manifest_sha256),
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
        "metadata_json": _segment_metadata(hadith, record, manifest_sha256),
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
    parser.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    parser.add_argument("--volume-1-pdf", type=Path, default=PDF_SOURCES[1]["path"])
    parser.add_argument("--volume-2-pdf", type=Path, default=PDF_SOURCES[2]["path"])
    parser.add_argument("--api-snapshot", type=Path, default=API_SNAPSHOT["path"])
    parser.add_argument(
        "--static-snapshot", type=Path, default=STATIC_SNAPSHOT["path"]
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest, manifest_sha256 = _load_manifest(args.manifest)
    pdf_paths = {1: args.volume_1_pdf, 2: args.volume_2_pdf}
    for volume, source in PDF_SOURCES.items():
        if file_sha256(pdf_paths[volume]).casefold() != source["sha256"]:
            raise RuntimeError(f"Pinned Volume {volume} PDF checksum changed")
    if file_sha256(args.api_snapshot).casefold() != API_SNAPSHOT["sha256"]:
        raise RuntimeError("Pinned API snapshot checksum changed")
    if file_sha256(args.static_snapshot).casefold() != STATIC_SNAPSHOT["sha256"]:
        raise RuntimeError("Pinned static snapshot checksum changed")
    pdf_records = extract_pdf_records(pdf_paths)
    identity_sources = load_identity_sources(
        args.api_snapshot, args.static_snapshot
    )

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
        expected_ids = {spec.public_id for spec in TARGET_SPECS}
        if set(hadiths) != expected_ids:
            raise RuntimeError("Local remaining-Sarwar target set changed")
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
        records_by_id = {
            record["public_id"]: record for record in manifest["records"]
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
        for spec in TARGET_SPECS:
            record = records_by_id[spec.public_id]
            hadith = hadiths[spec.public_id]
            _validate_record_sources(
                spec,
                record,
                hadith,
                pdf_records[spec.public_id],
                identity_sources[spec.public_id],
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
                f"Refusing partial remaining import: {len(selected)} of "
                f"{EXPECTED_COUNT} need changes"
            )
        for record, _, translation, segment in selected:
            if current_translation_payload(translation) != record["current_translation"]:
                raise RuntimeError(
                    f"Current translation changed after review: {record['public_id']}"
                )
            if current_segment_payload(segment) != record["current_segment"]:
                raise RuntimeError(
                    f"Current segment changed after review: {record['public_id']}"
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
                    "pdf_sha256": {
                        str(volume): source["sha256"]
                        for volume, source in PDF_SOURCES.items()
                    },
                    "api_snapshot_sha256": API_SNAPSHOT["sha256"],
                    "static_snapshot_sha256": STATIC_SNAPSHOT["sha256"],
                    "provider": TARGET_PROVIDER,
                    "model": TARGET_MODEL,
                    "translator": "Muhammad Sarwar",
                    "classification": CLASSIFICATION,
                    "blocked": 0,
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
                raise RuntimeError("Existing remaining import job is not complete")
            db.rollback()
            print(f"already_applied={EXPECTED_COUNT}")
            return
        if existing_job is not None:
            raise RuntimeError(
                f"Import job already exists while batch is incomplete: {JOB_KEY}"
            )

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
                "pdf_sha256": {
                    str(volume): source["sha256"]
                    for volume, source in PDF_SOURCES.items()
                },
                "api_snapshot_sha256": API_SNAPSHOT["sha256"],
                "static_snapshot_sha256": STATIC_SNAPSHOT["sha256"],
                "classification": CLASSIFICATION,
            },
            batch_policy_json={
                "source": "checksum-pinned published Muhammad Sarwar PDFs",
                "identity": (
                    "pinned human-source Arabic plus English chain/matn, local "
                    "sequence, and bounded PDF marker extent"
                ),
                "translation_generation": "none",
                "atomic_cardinality": f"{EXPECTED_COUNT}-or-0",
            },
            hadith_count=0,
            segment_count=0,
            input_chars=sum(
                len(hadith.matn_raw) for _, hadith, _, _ in selected
            ),
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
                raise RuntimeError(
                    f"Post-upsert target validation failed: {hadith.public_id}"
                )
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
