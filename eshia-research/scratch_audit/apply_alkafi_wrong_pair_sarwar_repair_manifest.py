"""Dry-run or atomically apply the pinned 53-row Sarwar pairing repair.

The default mode is read-only.  ``--apply`` performs a 53-or-0 transaction;
partial state is refused.  Target English is exact human-source text already
stored in the checksum-pinned manifest.  No translation model is called.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for import_root in (SRC_ROOT, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from sqlalchemy import select

from build_alkafi_opening_sarwar_pdf_manifest import (
    canonical_json_sha256,
    exact_text_sha256,
    file_sha256,
)
from build_alkafi_wrong_pair_sarwar_repair_manifest import (
    API_SHA256,
    DEFAULT_API,
    DEFAULT_DOSSIER,
    DEFAULT_SCAN_MANIFEST,
    DEFAULT_STATIC,
    DOSSIER_SHA256,
    SCAN_MANIFEST_SHA256,
    STATIC_SHA256,
    _segment_payload,
    _translation_payload,
    _whole_matn_segment,
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
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import sha256_text


SOURCE_BOOK_ID = "11005"
SCHEMA_VERSION = "alkafi_wrong_pair_sarwar_repair_manifest_v2"
EXPECTED_COUNT = 53
EXPECTED_QUARANTINED = 4
MANIFEST_SHA256 = (
    "38f152528cb93c0644e1d26ee44d47905f98f03e90b91b67332c93e5254c8e76"
)
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_wrong_pair_sarwar_repair_manifest_20260716.json"
)
JOB_PROVIDER = "sarwar-human-source"
MODEL = "muhammad-sarwar"
CLASSIFICATION = "verbatim_external_matn_excerpt"
IMPORT_VERSION = "alkafi_wrong_pair_sarwar_repair_v2"
QA_VERSION = "alkafi_wrong_pair_sarwar_repair_qa_v2"
JOB_KEY = f"alkafi-sarwar-wrong-pair-repair-v2-{MANIFEST_SHA256[:16]}"

FORBIDDEN_TARGET_MARKERS = (
    "codex",
    "openai",
    "chatgpt",
    "gpt-",
    "machine-generated translation",
    "project-authored",
    "machine verified draft",
    "hubeali.com",
    "(asws)",
    "(saww)",
    "(azwj)",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _load_manifest(path: Path) -> dict[str, Any]:
    _require(file_sha256(path) == MANIFEST_SHA256, "Manifest checksum changed")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _require(manifest.get("schema_version") == SCHEMA_VERSION, "Schema changed")
    _require(len(manifest.get("records", [])) == EXPECTED_COUNT, "Count changed")
    _require(
        len(manifest.get("quarantined", [])) == EXPECTED_QUARANTINED,
        "Quarantine count changed",
    )
    scope = manifest["scope"]
    _require(scope["atomic_apply_cardinality"] == "53-or-0", "Atomicity changed")
    _require(scope["dossier_wrong_pair_count"] == 57, "Dossier count changed")
    pins = manifest["source_pins"]
    _require(pins["dossier_sha256"] == DOSSIER_SHA256, "Dossier pin changed")
    _require(pins["api_snapshot_sha256"] == API_SHA256, "API pin changed")
    _require(pins["static_snapshot_sha256"] == STATIC_SHA256, "Static pin changed")
    _require(
        pins["scan_manifest_sha256"] == SCAN_MANIFEST_SHA256,
        "Scan pin changed",
    )
    ids = [record["public_id"] for record in manifest["records"]]
    _require(len(ids) == len(set(ids)), "Duplicate repair IDs")
    quarantine_ids = [record["public_id"] for record in manifest["quarantined"]]
    _require(not set(ids) & set(quarantine_ids), "Repair/quarantine overlap")
    return manifest


def _risk_flags() -> list[dict[str, str]]:
    return [
        {
            "code": "source_alignment_repaired",
            "severity": "info",
            "detail": (
                "The previously mispaired English was quarantined and replaced "
                "with checksum-pinned Muhammad Sarwar human-source text."
            ),
        }
    ]


def _provenance(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "classification": CLASSIFICATION,
        "translation_method": (
            "verbatim checksum-pinned human source import; no model translation"
        ),
        "translator": "Muhammad Sarwar",
        "manifest_sha256": MANIFEST_SHA256,
        "dossier_evidence": record["dossier_evidence"],
        "api_source": record["api_source"],
        "target_source": record["target_source"],
        "static_arabic_witness": record["static_arabic_witness"],
        "published_pdf": record["published_pdf"],
        "identity_metrics": record["identity_metrics"],
    }


def _segment_metadata(record: dict[str, Any], hadith: Hadith) -> dict[str, Any]:
    return {
        "extent": "whole_matn",
        "source_norm_sha256": sha256_text(hadith.matn_normalised),
        "provider": record["target"]["provider"],
        "model": record["target"]["model"],
        "translator": "Muhammad Sarwar",
        "classification": CLASSIFICATION,
        "provenance": _provenance(record),
    }


def _target_is_present(
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    hadith: Hadith,
    record: dict[str, Any],
) -> bool:
    if translation is None or segment is None:
        return False
    english = record["target"]["english"]
    flags = _risk_flags()
    return bool(
        translation.language == "en"
        and translation.translation_version == TRANSLATION_VERSION
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
        and translation.source_isnad_sha256
        == (sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None)
        and translation.source_matn_sha256 == sha256_text(hadith.matn_raw)
        and translation.rendered_isnad_en is None
        and translation.matn_translation == english
        and translation.full_translation is None
        and translation.status == "published"
        and translation.risk_level == "green"
        and translation.risk_flags == flags
        and translation.provider == record["target"]["provider"]
        and translation.model == record["target"]["model"]
        and translation.prompt_version == IMPORT_VERSION
        and translation.qa_version == QA_VERSION
        and translation.input_tokens == 0
        and translation.output_tokens == 0
        and translation.cost_estimate_usd == 0.0
        and translation.provenance_json == _provenance(record)
        and segment.translation_id == translation.id
        and segment.source_text == hadith.matn_raw
        and segment.source_sha256 == sha256_text(hadith.matn_raw)
        and segment.translation_text == english
        and segment.status == "published"
        and segment.risk_level == "green"
        and segment.risk_flags == flags
        and segment.metadata_json == _segment_metadata(record, hadith)
    )


def _validate_external_sources(
    manifest: dict[str, Any],
    dossier_path: Path,
    api_path: Path,
    static_path: Path,
    scan_path: Path,
) -> None:
    _require(file_sha256(dossier_path) == DOSSIER_SHA256, "Dossier bytes changed")
    _require(file_sha256(api_path) == API_SHA256, "API bytes changed")
    _require(file_sha256(static_path) == STATIC_SHA256, "Static bytes changed")
    _require(
        file_sha256(scan_path) == SCAN_MANIFEST_SHA256,
        "Scan manifest bytes changed",
    )
    api = json.loads(api_path.read_text(encoding="utf-8"))
    static = json.loads(static_path.read_text(encoding="utf-8"))
    scans = json.loads(scan_path.read_text(encoding="utf-8"))
    api_by_key = {
        (int(volume), int(item["id"])): item
        for volume, rows in api.items()
        for item in rows
    }
    static_by_url = {str(item["source_url"]): item for item in static}
    scan_by_key = {
        (int(item["physical_volume"]), int(item["hadith_number"])): item
        for item in scans["records"]
    }
    pdf_by_volume = {int(item["volume"]): item for item in scans["manifest"]}
    for volume_text, expected_hash in manifest["source_pins"]["pdf_sha256"].items():
        source = pdf_by_volume[int(volume_text)]
        _require(source["sha256"] == expected_hash, f"PDF pin changed: {volume_text}")
        _require(
            file_sha256(Path(source["path"])) == expected_hash,
            f"PDF bytes changed: {volume_text}",
        )

    for record in manifest["records"]:
        public_id = record["public_id"]
        api_pin = record["api_source"]
        api_record = None
        if api_pin is not None:
            api_record = api_by_key[(int(record["volume"]), int(api_pin["id"]))]
            _require(
                api_record["URL"] == api_pin["url"],
                f"API URL changed: {public_id}",
            )
            _require(
                api_record["translator"] == "Muhammad Sarwar",
                f"Translator changed: {public_id}",
            )
            _require(
                canonical_json_sha256(api_record) == api_pin["record_sha256"],
                f"API record changed: {public_id}",
            )

        target_source = record["target_source"]
        source_kind = target_source["kind"]
        if source_kind == "thaqalayn_api_muhammad_sarwar":
            _require(api_record is not None, f"Missing target API record: {public_id}")
            _require(
                target_source["record_sha256"] == api_pin["record_sha256"],
                f"Target/API source pins diverged: {public_id}",
            )
            english = str(api_record["englishText"]).strip()
        elif source_kind == "published_sarwar_scan_bounded_h_record":
            scan_record = scan_by_key[
                (int(record["volume"]), int(target_source["hadith_number"]))
            ]
            _require(
                scan_record["marker"] == target_source["marker"],
                f"Target PDF marker changed: {public_id}",
            )
            _require(
                scan_record["source_sha256"] == target_source["source_sha256"],
                f"Target PDF source changed: {public_id}",
            )
            english = str(scan_record["english"]).strip()
            _require(
                exact_text_sha256(english)
                == target_source["scan_record_english_sha256"],
                f"Target PDF extent changed: {public_id}",
            )
        elif source_kind == "thaqalayn_static_en_sarwar":
            target_static = static_by_url[target_source["url"]]
            _require(
                canonical_json_sha256(target_static)
                == target_source["record_sha256"],
                f"Target static record changed: {public_id}",
            )
            field_value = str(target_static.get("en_sarwar") or "").strip()
            _require(
                exact_text_sha256(field_value) == target_source["field_sha256"],
                f"Target static field changed: {public_id}",
            )
            start = target_source.get("slice_start")
            if start:
                _require(
                    field_value.count(start) == 1,
                    f"Target static slice marker changed: {public_id}",
                )
                english = field_value[field_value.index(start) :].strip()
            else:
                english = field_value
        else:
            raise RuntimeError(f"Unknown target source kind: {public_id}: {source_kind}")

        _require(
            english == record["target"]["english"],
            f"English changed: {public_id}",
        )
        _require(
            exact_text_sha256(english) == record["target"]["english_sha256"],
            f"English hash changed: {public_id}",
        )
        lowered = english.casefold()
        found = [marker for marker in FORBIDDEN_TARGET_MARKERS if marker in lowered]
        _require(not found, f"AI marker in target English: {public_id}: {found}")

        static_pin = record["static_arabic_witness"]
        static_record = static_by_url[static_pin["url"]]
        _require(
            canonical_json_sha256(static_record) == static_pin["record_sha256"],
            f"Static record changed: {public_id}",
        )
        published_pdf = record["published_pdf"]
        witness = published_pdf["text_layer_witness"] if published_pdf else None
        if witness is not None:
            scan_record = scan_by_key[(int(record["volume"]), int(witness["hadith_number"]))]
            _require(scan_record["marker"] == witness["marker"], f"PDF marker changed: {public_id}")
            _require(
                witness["english_sha256"]
                in {
                    exact_text_sha256(str(scan_record["english"])),
                    exact_text_sha256(str(scan_record["english"]).strip()),
                },
                f"PDF text-layer extent changed: {public_id}",
            )


def _upsert(
    db,
    hadith: Hadith,
    translation: HadithTranslation,
    segment: TranslationSegment | None,
    record: dict[str, Any],
    now: dt.datetime,
) -> tuple[HadithTranslation, TranslationSegment]:
    english = record["target"]["english"]
    values = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": (
            sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
        ),
        "source_matn_sha256": sha256_text(hadith.matn_raw),
        "rendered_isnad_en": None,
        "matn_translation": english,
        "full_translation": None,
        "status": "published",
        "risk_level": "green",
        "risk_flags": _risk_flags(),
        "provider": record["target"]["provider"],
        "model": record["target"]["model"],
        "prompt_version": IMPORT_VERSION,
        "glossary_version": None,
        "qa_version": QA_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_estimate_usd": 0.0,
        "provenance_json": _provenance(record),
        "updated_at": now,
    }
    for field, value in values.items():
        setattr(translation, field, value)
    db.flush()

    segment_values = {
        "translation_id": translation.id,
        "source_text": hadith.matn_raw,
        "translation_text": english,
        "status": "published",
        "risk_level": "green",
        "risk_flags": _risk_flags(),
        "metadata_json": _segment_metadata(record, hadith),
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
        segment.source_sha256 = sha256_text(hadith.matn_raw)
        for field, value in segment_values.items():
            setattr(segment, field, value)
    db.flush()
    return translation, segment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--api-snapshot", type=Path, default=DEFAULT_API)
    parser.add_argument("--static-snapshot", type=Path, default=DEFAULT_STATIC)
    parser.add_argument("--scan-manifest", type=Path, default=DEFAULT_SCAN_MANIFEST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest = _load_manifest(args.manifest)
    _validate_external_sources(
        manifest,
        args.dossier,
        args.api_snapshot,
        args.static_snapshot,
        args.scan_manifest,
    )
    records = {record["public_id"]: record for record in manifest["records"]}

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        hadiths = {
            value.public_id: value
            for value in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_(list(records)),
                )
            ).scalars()
        }
        _require(set(hadiths) == set(records), "Local target membership changed")
        translations = {
            value.hadith_id: value
            for value in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.hadith_id.in_(
                        [hadith.id for hadith in hadiths.values()]
                    ),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        }
        reviewed = []
        selected = []
        for public_id, record in records.items():
            hadith = hadiths[public_id]
            _require(hadith.id == record["hadith_id"], f"Hadith ID changed: {public_id}")
            _require(
                record["source_full_sha256"] == sha256_text(hadith.full_text_raw)
                and record["source_isnad_sha256"]
                == (sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None)
                and record["source_matn_sha256"] == sha256_text(hadith.matn_raw),
                f"Local Arabic source changed: {public_id}",
            )
            translation = translations.get(hadith.id)
            _require(translation is not None, f"Missing translation: {public_id}")
            segment = _whole_matn_segment(db, hadith)
            item = (record, hadith, translation, segment)
            reviewed.append(item)
            if not _target_is_present(translation, segment, hadith, record):
                selected.append(item)

        _require(
            len(selected) in {0, EXPECTED_COUNT},
            f"Refusing partial state: {len(selected)} of {EXPECTED_COUNT}",
        )
        for record, _, translation, segment in selected:
            _require(
                _translation_payload(translation) == record["current_translation"],
                f"Current translation changed: {record['public_id']}",
            )
            _require(
                _segment_payload(segment) == record["current_segment"],
                f"Current segment changed: {record['public_id']}",
            )

        existing_job = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)
        ).scalar_one_or_none()
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "manifest_sha256": MANIFEST_SHA256,
                    "selected": len(selected),
                    "assertion": "53-or-0",
                    "translator": "Muhammad Sarwar",
                    "provider": JOB_PROVIDER,
                    "model": MODEL,
                    "codex_translations": 0,
                    "hubeali_target_fields": 0,
                    "quarantined_weak_rows_unchanged": EXPECTED_QUARANTINED,
                },
                indent=2,
            )
        )
        if not args.apply:
            db.rollback()
            return
        if not selected:
            _require(
                existing_job is not None
                and existing_job.status == "completed"
                and existing_job.hadith_count == EXPECTED_COUNT
                and existing_job.segment_count == EXPECTED_COUNT,
                "Target state exists without completed import job",
            )
            db.rollback()
            print(f"already_applied={EXPECTED_COUNT}")
            return
        _require(existing_job is None, "Import job already exists")

        now = dt.datetime.now(dt.timezone.utc)
        job = TranslationJob(
            job_key=JOB_KEY,
            source_book_id=SOURCE_BOOK_ID,
            language="en",
            status="running",
            provider=JOB_PROVIDER,
            model=MODEL,
            prompt_version=IMPORT_VERSION,
            glossary_version=None,
            scope_json={
                "manifest_sha256": MANIFEST_SHA256,
                "dossier_sha256": DOSSIER_SHA256,
                "public_ids": list(records),
                "classification": CLASSIFICATION,
            },
            batch_policy_json={
                "source": "checksum-pinned Muhammad Sarwar human text",
                "translation_generation": "none",
                "atomic_cardinality": "53-or-0",
                "unavailable_or_unproven_rows": "remain quarantined",
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
            translation, segment = _upsert(
                db, hadith, translation, segment, record, now
            )
            _require(
                _target_is_present(translation, segment, hadith, record),
                f"Post-upsert target validation failed: {hadith.public_id}",
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
                    provider=record["target"]["provider"],
                    model=record["target"]["model"],
                    status="completed",
                    request_json={
                        "translation_generation": "none",
                        "api_source": record["api_source"],
                        "source_matn_sha256": record["source_matn_sha256"],
                    },
                    response_json={
                        "published": True,
                        "human_source_only": True,
                        "english_sha256": record["target"]["english_sha256"],
                        "manifest_sha256": MANIFEST_SHA256,
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
