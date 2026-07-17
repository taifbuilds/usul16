"""Quarantine the 75 source-alignment blockers found in the Al-Kafi audit.

The audit distinguishes human-source provenance from correct source alignment:
an English field can be verbatim Muhammad Sarwar (or another named human
edition) and still belong to the wrong Arabic report.  Dry-run is the default.
The apply path is atomic and accepts only an exact 75-row pre-audit state or an
exact 75-row already-quarantined state.
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
from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationJobItem,
    TranslationMemory,
)
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.publication import is_public_english_translation
from eshia_research.translation.text import sha256_text


SOURCE_BOOK_ID = "11005"
DEFAULT_DOSSIER = Path(
    "scratch_audit/alkafi_translation_extent_pairing_blockers_20260716.json"
)
DOSSIER_SHA256 = "d7744e88ecf8632500073be4c4f685d7737e9978ec04ca5d5810ef96929c5a94"
SNAPSHOT_SHA256 = "14259bd9629af43d1166c7e413429f8414564814e95acdd0e270d73dccf7d4f7"
SCHEMA_VERSION = "alkafi_translation_extent_pairing_blockers_v2_compact"
AUDIT_VERSION = "alkafi_translation_extent_pairing_quarantine_v1"
EXPECTED_TOTAL = 75
EXPECTED_CATEGORIES = Counter(
    {"wrong_english_pairing": 57, "structural_or_extent_defect": 18}
)
FLAG_CODE = "confirmed_source_alignment_blocker"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _flattened(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _add_flag(flags: object, detail: str) -> list[dict[str, Any]]:
    result = [dict(flag) for flag in flags or [] if isinstance(flag, dict)]
    if not any(flag.get("code") == FLAG_CODE for flag in result):
        result.append(
            {
                "code": FLAG_CODE,
                "severity": "critical",
                "detail": detail,
                "audit_version": AUDIT_VERSION,
                "dossier_sha256": DOSSIER_SHA256,
            }
        )
    return result


def _load_dossier(path: Path) -> tuple[list[dict[str, Any]], str]:
    if not path.exists():
        raise RuntimeError(f"Audit dossier is missing: {path}")
    dossier_sha256 = _sha256_file(path)
    if dossier_sha256 != DOSSIER_SHA256:
        raise RuntimeError(
            f"Audit dossier checksum changed: {dossier_sha256} != {DOSSIER_SHA256}"
        )
    payload = json.loads(path.read_bytes())
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Unexpected audit dossier schema")
    if (payload.get("database_snapshot") or {}).get("sha256") != SNAPSHOT_SHA256:
        raise RuntimeError("Unexpected source database snapshot")
    if payload.get("publication_rule") != (
        "Quarantine all 75; do not blanket-normalize their QA flags and do not auto-remap."
    ):
        raise RuntimeError("Audit publication rule changed")

    columns = payload.get("record_columns")
    rows = payload.get("records")
    category_keys = payload.get("category_keys") or {}
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise RuntimeError("Malformed compact audit records")
    if len(rows) != EXPECTED_TOTAL:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL} audit rows; found {len(rows)}")
    records: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) != len(columns):
            raise RuntimeError("Malformed compact audit row")
        record = dict(zip(columns, row, strict=True))
        record["category"] = category_keys.get(record.pop("category_key"))
        records.append(record)

    public_ids = [record["public_id"] for record in records]
    categories = Counter(record["category"] for record in records)
    if len(set(public_ids)) != EXPECTED_TOTAL or categories != EXPECTED_CATEGORIES:
        raise RuntimeError(
            f"Unexpected blocker set: unique={len(set(public_ids))}, "
            f"categories={dict(categories)}"
        )
    if any(record.get("replacement_coordinate") is not None for record in records):
        raise RuntimeError("Dossier unexpectedly approves an automatic replacement")
    if any(
        not record.get(field)
        for record in records
        for field in (
            "public_id",
            "hadith_id",
            "translation_id",
            "english_sha256",
            "source_record_sha256",
            "source_url",
            "evidence_key",
            "action_key",
        )
    ):
        raise RuntimeError("Dossier omits required row evidence")
    return records, dossier_sha256


def _is_quarantined(
    translation: HadithTranslation,
    record: dict[str, Any],
) -> bool:
    provenance = translation.provenance_json or {}
    segments = list(translation.segments)
    return bool(
        translation.status == "rejected"
        and translation.risk_level == "red"
        and translation.rendered_isnad_en is None
        and translation.matn_translation is None
        and translation.full_translation is None
        and any(
            isinstance(flag, dict) and flag.get("code") == FLAG_CODE
            for flag in translation.risk_flags or []
        )
        and isinstance(provenance, dict)
        and provenance.get("publication_status") == "rejected"
        and provenance.get("removed_english_sha256") == record["english_sha256"]
        and (provenance.get("source_alignment_audit") or {}).get("dossier_sha256")
        == DOSSIER_SHA256
        and len(segments) == 1
        and all(
            segment.translation_text is None
            and segment.status == "qa_failed"
            and segment.risk_level == "red"
            and any(
                isinstance(flag, dict) and flag.get("code") == FLAG_CODE
                for flag in segment.risk_flags or []
            )
            for segment in segments
        )
    )


def _validate_active(
    translation: HadithTranslation,
    hadith: Hadith,
    record: dict[str, Any],
) -> None:
    expected = {
        "hadith_id": hadith.id,
        "translation_id": translation.id,
        "provider": translation.provider,
        "status": translation.status,
        "risk_level": translation.risk_level,
        "translation_version": translation.translation_version,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(
                f"Snapshot metadata changed for {hadith.public_id}: "
                f"{key}={value!r} expected {record.get(key)!r}"
            )
    if translation.status != "published" or translation.risk_level != "green":
        raise RuntimeError(f"Unexpected active state for {hadith.public_id}")
    if not translation.matn_translation:
        raise RuntimeError(f"Missing active English for {hadith.public_id}")
    if sha256_text(translation.matn_translation) != record["english_sha256"]:
        raise RuntimeError(f"English checksum changed for {hadith.public_id}")
    if translation.source_full_sha256 != sha256_text(hadith.full_text_raw):
        raise RuntimeError(f"Full Arabic checksum is stale for {hadith.public_id}")
    if translation.source_isnad_sha256 != (
        sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
    ):
        raise RuntimeError(f"Isnad checksum is stale for {hadith.public_id}")
    if translation.source_matn_sha256 != sha256_text(hadith.matn_raw):
        raise RuntimeError(f"Matn checksum is stale for {hadith.public_id}")

    provenance_text = _flattened(translation.provenance_json or {})
    for evidence in (
        record["source_record_sha256"],
        record["source_url"],
        record["translator"],
    ):
        if str(evidence) not in provenance_text:
            raise RuntimeError(
                f"Pinned source evidence is missing for {hadith.public_id}: {evidence}"
            )
    if len(translation.segments) != 1:
        raise RuntimeError(
            f"Expected one active segment for {hadith.public_id}; "
            f"found {len(translation.segments)}"
        )
    segment = translation.segments[0]
    if (
        segment.translation_text != translation.matn_translation
        or segment.status != "published"
        or segment.risk_level != "green"
    ):
        raise RuntimeError(f"Active segment changed for {hadith.public_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    records, dossier_sha256 = _load_dossier(args.dossier)
    records_by_id = {record["public_id"]: record for record in records}
    now = dt.datetime.now(dt.timezone.utc)

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        rows = list(
            db.execute(
                select(HadithTranslation)
                .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_(records_by_id),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
                .options(
                    selectinload(HadithTranslation.hadith),
                    selectinload(HadithTranslation.segments),
                )
            ).scalars()
        )
        translations_by_id = {row.hadith.public_id: row for row in rows}
        if set(translations_by_id) != set(records_by_id):
            raise RuntimeError("Live blocker set does not equal the reviewed dossier set")

        target_state = [
            _is_quarantined(translation, records_by_id[public_id])
            for public_id, translation in translations_by_id.items()
        ]
        if any(target_state) and not all(target_state):
            raise RuntimeError(
                f"Refusing partial quarantine state: {sum(target_state)} of {EXPECTED_TOTAL}"
            )

        selected: list[tuple[dict[str, Any], Hadith, HadithTranslation]] = []
        if not all(target_state):
            for public_id in sorted(
                records_by_id,
                key=lambda value: records_by_id[value]["sequence_in_book"],
            ):
                record = records_by_id[public_id]
                translation = translations_by_id[public_id]
                hadith = translation.hadith
                _validate_active(translation, hadith, record)
                selected.append((record, hadith, translation))

        source_hashes = [
            translation.source_matn_sha256
            for translation in translations_by_id.values()
        ]
        memory_rows = list(
            db.execute(
                select(TranslationMemory).where(
                    TranslationMemory.language == "en",
                    TranslationMemory.source_sha256.in_(source_hashes),
                )
            ).scalars()
        )
        if memory_rows:
            raise RuntimeError(
                f"Translation memory contains {len(memory_rows)} blocker source(s); "
                "quarantine those explicitly before continuing"
            )

        segment_ids = [
            segment.id
            for _, _, translation in selected
            for segment in translation.segments
        ]
        item_rows = (
            list(
                db.execute(
                    select(TranslationJobItem).where(
                        TranslationJobItem.segment_id.in_(segment_ids)
                    )
                ).scalars()
            )
            if segment_ids
            else []
        )
        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "dossier_sha256": dossier_sha256,
            "selected_rows": len(selected),
            "assertion": f"{EXPECTED_TOTAL}-or-0",
            "categories": dict(
                sorted(Counter(record["category"] for record, _, _ in selected).items())
            ),
            "providers": dict(
                sorted(
                    Counter(
                        translation.provider or "unknown"
                        for _, _, translation in selected
                    ).items()
                )
            ),
            "segments": len(segment_ids),
            "job_items": len(item_rows),
            "translation_memory_rows": len(memory_rows),
            "english_replacements": 0,
            "arabic_text_changes": 0,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        if not args.apply:
            db.rollback()
            return
        if not selected:
            db.rollback()
            print(f"already_quarantined={EXPECTED_TOTAL}")
            return

        item_ids_by_segment: dict[int, list[TranslationJobItem]] = {}
        for item in item_rows:
            if item.segment_id is not None:
                item_ids_by_segment.setdefault(item.segment_id, []).append(item)

        for record, hadith, translation in selected:
            category = record["category"]
            detail = (
                "The attached human-source English belongs to a different Arabic "
                "report and is withheld pending an exact rematch."
                if category == "wrong_english_pairing"
                else "The Arabic report extent or isnad/matn split is defective; "
                "English is withheld until the source structure is repaired and rematched."
            )
            provenance = dict(translation.provenance_json or {})
            previous_classification = provenance.get("translation_classification") or provenance.get(
                "classification"
            )
            provenance.update(
                {
                    "publication_status": "rejected",
                    "reason": FLAG_CODE,
                    "removed_english_sha256": record["english_sha256"],
                    "quarantined_previous_classification": previous_classification,
                    "translation_classification": "quarantined_source_alignment_blocker",
                    "source_alignment_audit": {
                        "version": AUDIT_VERSION,
                        "dossier": args.dossier.as_posix(),
                        "dossier_sha256": dossier_sha256,
                        "category": category,
                        "subcategory": record["subcategory_key"],
                        "evidence_key": record["evidence_key"],
                        "action_key": record["action_key"],
                        "source_record_sha256": record["source_record_sha256"],
                        "source_url": record["source_url"],
                    },
                    "audited_at": now.isoformat(),
                }
            )
            translation.provenance_json = provenance
            translation.rendered_isnad_en = None
            translation.matn_translation = None
            translation.full_translation = None
            translation.status = "rejected"
            translation.risk_level = "red"
            translation.risk_flags = _add_flag(translation.risk_flags, detail)
            translation.updated_at = now

            for segment in translation.segments:
                segment.translation_text = None
                segment.status = "qa_failed"
                segment.risk_level = "red"
                segment.risk_flags = _add_flag(segment.risk_flags, detail)
                metadata = dict(segment.metadata_json or {})
                metadata.update(
                    {
                        "publication_status": "rejected",
                        "translation_text_redacted": True,
                        "reason": FLAG_CODE,
                        "source_alignment_audit": provenance["source_alignment_audit"],
                    }
                )
                segment.metadata_json = metadata
                segment.updated_at = now
                for item in item_ids_by_segment.get(segment.id, []):
                    item.status = "qa_failed"
                    item.risk_level = "red"
                    item.updated_at = now

            if is_public_english_translation(translation, hadith):
                raise RuntimeError(f"Quarantined row remains public: {hadith.public_id}")

        db.commit()
        print(f"committed={EXPECTED_TOTAL}")


if __name__ == "__main__":
    main()
