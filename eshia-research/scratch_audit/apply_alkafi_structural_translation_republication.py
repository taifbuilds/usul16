"""Republish 14 source-pinned Sarwar translations after Arabic structure repair.

Dry-run is the default.  ``--apply`` commits exactly 14 rows or none.  Every
English string is reconstructed from a checksum-pinned API/static/PDF record;
this script never calls or accepts a translation model.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sqlalchemy import select  # noqa: E402

from eshia_research.db import SessionLocal  # noqa: E402
from eshia_research.models import (  # noqa: E402
    Book,
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)
from eshia_research.translation import TRANSLATION_VERSION  # noqa: E402
from eshia_research.translation.text import clean_ws, sha256_text  # noqa: E402


SOURCE_BOOK_ID = "11005"
EXPECTED_COUNT = 14
MANIFEST_SHA256 = (
    "a6bbc979f4424321e7043c4edd780ab0e851bcf938c70be960970d2b60d9b9f5"
)
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_structural_translation_republication_manifest_20260716.json"
)
IMPORT_VERSION = "alkafi_structural_source_republication_v1"
QA_VERSION = "alkafi_structural_source_republication_qa_v1"
JOB_KEY = f"alkafi-structural-source-republication-v1-{MANIFEST_SHA256[:16]}"
JOB_PROVIDER = "sarwar-human-source"
FORBIDDEN_MARKERS = (
    "codex",
    "openai",
    "chatgpt",
    "gpt-",
    "machine-verified draft",
    "machine-generated translation",
    "project-authored",
    "hubeali.com",
    "(asws)",
    "(saww)",
    "(azwj)",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def raw_text_sha256(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def resolve_path(raw: str) -> Path:
    expanded = Path(os.path.expandvars(raw)).expanduser()
    return expanded if expanded.is_absolute() else ROOT / expanded


def load_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing manifest: {path}")
    require(file_sha256(path) == MANIFEST_SHA256, "Manifest checksum changed")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(
        manifest.get("schema_version")
        == "alkafi_structural_translation_republication_v5",
        "Manifest schema changed",
    )
    records = manifest.get("records") or []
    require(len(records) == EXPECTED_COUNT, f"Expected 14 records, got {len(records)}")
    ids = [record["public_id"] for record in records]
    require(len(ids) == len(set(ids)), "Duplicate public IDs in manifest")
    require(
        manifest.get("counts", {}).get("republication_total") == EXPECTED_COUNT,
        "Manifest count declaration changed",
    )
    require(
        manifest.get("counts", {}).get("quarantine_followup") == 1,
        "Manifest quarantine count changed",
    )
    prerequisite = manifest["prerequisite"]
    prerequisite_path = resolve_path(prerequisite["manifest"])
    require(
        file_sha256(prerequisite_path) == prerequisite["sha256"],
        "Structural repair manifest checksum changed",
    )
    return manifest


def risk_flags() -> list[dict[str, str]]:
    return [
        {
            "code": "source_alignment_repaired",
            "severity": "info",
            "detail": (
                "Arabic extent and English source alignment were repaired and "
                "verified against a checksum-pinned Muhammad Sarwar source."
            ),
        }
    ]


def source_configuration(record: dict[str, Any]) -> tuple[str, str, str]:
    kind = record["source_kind"]
    if kind == "api":
        return "thaqalayn-api", "muhammad-sarwar", "external_source_normalized"
    if kind == "static":
        return "thaqalayn-data", "muhammad-sarwar", "external_source_normalized"
    if kind == "sarwar_published_scan":
        return (
            "sarwar-published-scan",
            "muhammad-sarwar-published",
            "verbatim_external_matn_excerpt",
        )
    raise RuntimeError(f"Unsupported source kind: {record['public_id']}: {kind}")


def provenance(record: dict[str, Any]) -> dict[str, Any]:
    provider, _, classification = source_configuration(record)
    payload: dict[str, Any] = {
        "source": provider,
        "source_url": record["source_url"],
        "source_coordinate": record["source_coordinate"],
        "translator": "Muhammad Sarwar",
        "translator_attribution": "checksum-pinned human source",
        "source_english_sha256": record["source_english_sha256"],
        "translation_classification": classification,
        "translation_method": (
            "verbatim checksum-pinned human source import; no model translation"
        ),
        "manifest_sha256": MANIFEST_SHA256,
        "structural_repair_manifest_sha256": (
            "8a27621a0fb5b9b5deebed6eff2ff19c439fd8fba4fd7f2acb208f30b6b235e1"
        ),
        "source_alignment_action": record["action"],
    }
    for key in (
        "snapshot_url",
        "source_record_sha256",
        "source_arabic_sha256",
        "source_pdf_sha256",
        "source_marker",
        "identity_gate",
        "neighbor_policy",
    ):
        if key in record:
            payload[key] = record[key]
    return payload


def segment_metadata(record: dict[str, Any], hadith: Hadith) -> dict[str, Any]:
    provider, model, classification = source_configuration(record)
    return {
        "extent": "whole_matn",
        "source_norm_sha256": sha256_text(hadith.matn_normalised),
        "provider": provider,
        "model": model,
        "translator": "Muhammad Sarwar",
        "classification": classification,
        "provenance": provenance(record),
    }


def validate_sources(
    manifest: dict[str, Any],
) -> dict[str, tuple[str, str | None]]:
    pins = manifest["source_snapshots"]
    loaded: dict[str, Any] = {}
    for key, pin in pins.items():
        path = resolve_path(pin["path"])
        require(path.is_file(), f"Missing {key} source snapshot: {path}")
        require(file_sha256(path) == pin["sha256"], f"{key} snapshot changed")
        loaded[key] = json.loads(path.read_text(encoding="utf-8"))

    static_by_path = {row["path"]: row for row in loaded["static"]}
    api_by_key = {
        (int(volume), int(row["id"])): row
        for volume, rows in loaded["api"].items()
        for row in rows
    }
    scan_rows = loaded["scan_records"]["records"]
    scan_manifest = {
        int(row["volume"]): row for row in loaded["scan_records"]["manifest"]
    }
    result: dict[str, tuple[str, str | None]] = {}

    for record in manifest["records"]:
        public_id = record["public_id"]
        require(record["translator"] == "Muhammad Sarwar", f"Translator changed: {public_id}")
        rendered_isnad: str | None = None
        if record["source_kind"] == "static":
            source = static_by_path.get(record["source_coordinate"])
            require(source is not None, f"Static source missing: {public_id}")
            require(
                canonical_json_sha256(source) == record["source_record_sha256"],
                f"Static source record changed: {public_id}",
            )
            require(source["source_url"] == record["source_url"], f"Static URL changed: {public_id}")
            english = clean_ws(source.get("en_sarwar"))
        elif record["source_kind"] == "api":
            match = re.fullmatch(r"volume=(\d+),id=(\d+)", record["source_coordinate"])
            require(match is not None, f"Bad API coordinate: {public_id}")
            key = (int(match.group(1)), int(match.group(2)))
            source = api_by_key.get(key)
            require(source is not None, f"API source missing: {public_id}")
            require(source.get("translator") == "Muhammad Sarwar", f"API translator changed: {public_id}")
            require(
                canonical_json_sha256(source) == record["source_record_sha256"],
                f"API source record changed: {public_id}",
            )
            require(
                source.get("URL") == record.get("snapshot_url"),
                f"Pinned API snapshot URL changed: {public_id}",
            )
            snapshot_path = str(record["snapshot_url"]).split("/hadith/", 1)[1]
            snapshot_parts = snapshot_path.split("/", 1)
            expected_live_url = (
                f"https://thaqalayn.net/hadith/{key[0]}/{snapshot_parts[1]}"
            )
            require(
                record["source_url"] == expected_live_url,
                f"Canonical physical-volume source URL changed: {public_id}",
            )
            english = clean_ws(source.get("thaqalaynMatn") or source.get("englishText"))
            expected_rendered_hash = record.get("source_rendered_isnad_sha256")
            if expected_rendered_hash:
                rendered_isnad = clean_ws(source.get("thaqalaynSanad"))
                require(
                    sha256_text(rendered_isnad) == expected_rendered_hash,
                    f"API rendered isnad changed: {public_id}",
                )
        else:
            matches = [
                row
                for row in scan_rows
                if int(row["physical_volume"]) == 1
                and int(row["hadith_number"]) == 1146
                and str(row["chapter_number"]) == "108"
                and str(row["number_in_chapter"]) == "69"
            ]
            require(len(matches) == 1, f"Published scan record count changed: {public_id}")
            source = matches[0]
            require(source["marker"] == record["source_marker"], f"Scan marker changed: {public_id}")
            require(source["source_sha256"] == record["source_pdf_sha256"], f"Scan PDF pin changed: {public_id}")
            pdf = scan_manifest[1]
            require(pdf["sha256"] == record["source_pdf_sha256"], "Scan manifest PDF pin changed")
            require(file_sha256(Path(pdf["path"])) == pdf["sha256"], "Published Sarwar PDF bytes changed")
            english = clean_ws(source["english"])
            require(english == clean_ws(record["source_english_text"]), f"Scan English changed: {public_id}")

        require(english, f"Empty source English: {public_id}")
        require(sha256_text(english) == record["source_english_sha256"], f"English hash changed: {public_id}")
        lowered = english.casefold()
        found = [marker for marker in FORBIDDEN_MARKERS if marker in lowered]
        require(not found, f"Forbidden target marker: {public_id}: {found}")
        result[public_id] = (english, rendered_isnad)

    for followup in manifest["quarantine_followup"]:
        public_id = followup["public_id"]
        match = re.fullmatch(
            r"volume=(\d+),id=(\d+)", followup["candidate_source_coordinate"]
        )
        require(match is not None, f"Bad quarantine coordinate: {public_id}")
        source = api_by_key.get((int(match.group(1)), int(match.group(2))))
        require(source is not None, f"Quarantine source missing: {public_id}")
        require(
            canonical_json_sha256(source)
            == followup["candidate_source_record_sha256"],
            f"Quarantine source record changed: {public_id}",
        )
        candidate_english = clean_ws(
            source.get("thaqalaynMatn") or source.get("englishText")
        )
        require(
            sha256_text(candidate_english)
            == followup["candidate_source_english_sha256"],
            f"Quarantine source English changed: {public_id}",
        )
        contradictory_markers = [
            marker for marker in FORBIDDEN_MARKERS if marker in candidate_english.casefold()
        ]
        require(
            contradictory_markers,
            f"Quarantine source no longer exhibits the pinned attribution contradiction: {public_id}",
        )
    return result


def validate_quarantine_followup(db, manifest: dict[str, Any], book_id: int) -> int:
    followups = manifest["quarantine_followup"]
    require(len(followups) == 1, "Quarantine follow-up cardinality changed")
    followup = followups[0]
    public_id = followup["public_id"]
    hadith = db.execute(
        select(Hadith).where(
            Hadith.book_id == book_id,
            Hadith.public_id == public_id,
        )
    ).scalar_one()
    require(hadith.id == followup["hadith_id"], f"Follow-up hadith ID changed: {public_id}")
    rows = list(
        db.execute(
            select(HadithTranslation).where(
                HadithTranslation.hadith_id == hadith.id,
                HadithTranslation.language == "en",
                HadithTranslation.translation_version == TRANSLATION_VERSION,
            )
        ).scalars()
    )
    require(len(rows) == 1, f"Follow-up translation cardinality changed: {public_id}")
    translation = rows[0]
    require(
        translation.id == followup["translation_id"]
        and translation.status == "rejected"
        and translation.risk_level == "red"
        and translation.rendered_isnad_en is None
        and translation.matn_translation is None
        and translation.full_translation is None,
        f"Unproven Volume 8 row is no longer quarantined: {public_id}",
    )
    segment = get_whole_segment(db, hadith.id)
    require(
        segment is not None
        and segment.id == followup["segment_id"]
        and segment.translation_id == translation.id
        and segment.status == "qa_failed"
        and segment.risk_level == "red"
        and segment.translation_text is None,
        f"Unproven Volume 8 segment is no longer quarantined: {public_id}",
    )
    return 1


def get_whole_segment(db, hadith_id: int) -> TranslationSegment | None:
    rows = list(
        db.execute(
            select(TranslationSegment).where(
                TranslationSegment.hadith_id == hadith_id,
                TranslationSegment.language == "en",
                TranslationSegment.translation_version == TRANSLATION_VERSION,
                TranslationSegment.segment_kind == "matn",
                TranslationSegment.segment_index == 0,
            )
        ).scalars()
    )
    require(len(rows) <= 1, f"Multiple whole-matn segments for hadith {hadith_id}")
    return rows[0] if rows else None


def target_present(
    hadith: Hadith,
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    record: dict[str, Any],
    english: str,
    rendered_isnad: str | None,
) -> bool:
    if translation is None or segment is None:
        return False
    provider, model, _ = source_configuration(record)
    expected_isnad = sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
    return bool(
        translation.language == "en"
        and translation.translation_version == TRANSLATION_VERSION
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
        and translation.source_isnad_sha256 == expected_isnad
        and translation.source_matn_sha256 == sha256_text(hadith.matn_raw)
        and translation.rendered_isnad_en == rendered_isnad
        and translation.matn_translation == english
        and translation.full_translation is None
        and translation.status == "published"
        and translation.risk_level == "green"
        and translation.risk_flags == risk_flags()
        and translation.provider == provider
        and translation.model == model
        and translation.prompt_version == IMPORT_VERSION
        and translation.qa_version == QA_VERSION
        and translation.input_tokens == 0
        and translation.output_tokens == 0
        and translation.cost_estimate_usd == 0.0
        and translation.provenance_json == provenance(record)
        and segment.translation_id == translation.id
        and segment.source_text == hadith.matn_raw
        and segment.source_sha256 == sha256_text(hadith.matn_raw)
        and segment.translation_text == english
        and segment.status == "published"
        and segment.risk_level == "green"
        and segment.risk_flags == risk_flags()
        and segment.metadata_json == segment_metadata(record, hadith)
    )


def assert_preapply_state(
    record: dict[str, Any],
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
) -> None:
    public_id = record["public_id"]
    if record["action"] == "create_new_translation":
        require(translation is None and segment is None, f"Unexpected existing target: {public_id}")
        return
    require(translation is not None, f"Missing quarantined translation: {public_id}")
    require(translation.id == record["translation_id"], f"Translation ID changed: {public_id}")
    require(
        translation.status == "rejected"
        and translation.risk_level == "red"
        and translation.rendered_isnad_en is None
        and translation.matn_translation is None
        and translation.full_translation is None,
        f"Translation is not in exact quarantined state: {public_id}",
    )
    require(segment is not None, f"Missing quarantined segment: {public_id}")
    require(
        segment.translation_id == translation.id
        and segment.status == "qa_failed"
        and segment.risk_level == "red"
        and segment.translation_text is None,
        f"Segment is not in exact quarantined state: {public_id}",
    )


def upsert(
    db,
    hadith: Hadith,
    translation: HadithTranslation | None,
    segment: TranslationSegment | None,
    record: dict[str, Any],
    english: str,
    rendered_isnad: str | None,
    now: dt.datetime,
) -> tuple[HadithTranslation, TranslationSegment]:
    provider, model, _ = source_configuration(record)
    if translation is None:
        translation = HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            created_at=now,
        )
        db.add(translation)
    values = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None,
        "source_matn_sha256": sha256_text(hadith.matn_raw),
        "rendered_isnad_en": rendered_isnad,
        "matn_translation": english,
        "full_translation": None,
        "status": "published",
        "risk_level": "green",
        "risk_flags": risk_flags(),
        "provider": provider,
        "model": model,
        "prompt_version": IMPORT_VERSION,
        "glossary_version": None,
        "qa_version": QA_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_estimate_usd": 0.0,
        "provenance_json": provenance(record),
        "updated_at": now,
    }
    for field, value in values.items():
        setattr(translation, field, value)
    db.flush()

    if segment is None:
        segment = TranslationSegment(
            hadith_id=hadith.id,
            translation_id=translation.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            segment_kind="matn",
            segment_index=0,
            created_at=now,
        )
        db.add(segment)
    segment.translation_id = translation.id
    segment.source_text = hadith.matn_raw
    segment.source_sha256 = sha256_text(hadith.matn_raw)
    segment.translation_text = english
    segment.status = "published"
    segment.risk_level = "green"
    segment.risk_flags = risk_flags()
    segment.metadata_json = segment_metadata(record, hadith)
    segment.updated_at = now
    db.flush()
    return translation, segment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    sources = validate_sources(manifest)
    records = {record["public_id"]: record for record in manifest["records"]}

    with SessionLocal() as db:
        book = db.execute(select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)).scalar_one()
        quarantined_followups = validate_quarantine_followup(db, manifest, book.id)
        hadiths = {
            row.public_id: row
            for row in db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.public_id.in_(list(records)),
                )
            ).scalars()
        }
        require(set(hadiths) == set(records), "Target hadith membership changed")
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.hadith_id.in_([h.id for h in hadiths.values()]),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        }
        require(len(translations) in {13, 14}, "Unexpected translation cardinality")
        reviewed = []
        selected = []
        for public_id, record in records.items():
            hadith = hadiths[public_id]
            require(hadith.review_status != "rejected_non_hadith_fragment", f"Inactive target: {public_id}")
            require(
                raw_text_sha256(hadith.full_text_raw) == record["target_source_full_sha256"]
                and raw_text_sha256(hadith.isnad_raw)
                == record["target_source_isnad_sha256"]
                and raw_text_sha256(hadith.matn_raw) == record["target_source_matn_sha256"],
                f"Repaired Arabic hashes changed: {public_id}",
            )
            translation = translations.get(hadith.id)
            segment = get_whole_segment(db, hadith.id)
            english, rendered_isnad = sources[public_id]
            item = (record, hadith, translation, segment, english, rendered_isnad)
            reviewed.append(item)
            if not target_present(hadith, translation, segment, record, english, rendered_isnad):
                selected.append(item)

        require(
            len(selected) in {0, EXPECTED_COUNT},
            f"Refusing partial state: selected {len(selected)} of {EXPECTED_COUNT}",
        )
        for record, _, translation, segment, _, _ in selected:
            assert_preapply_state(record, translation, segment)

        existing_job = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)
        ).scalar_one_or_none()
        report = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "manifest_sha256": MANIFEST_SHA256,
            "selected": len(selected),
            "assertion": "14-or-0",
            "human_source_records_verified": len(sources),
            "translator": "Muhammad Sarwar",
            "codex_translations": 0,
            "hubeali_targets": 0,
            "unproven_volume8_rows_quarantined": quarantined_followups,
        }
        print(json.dumps(report, indent=2))
        if not args.apply:
            db.rollback()
            return
        if not selected:
            require(
                existing_job is not None
                and existing_job.status == "completed"
                and existing_job.hadith_count == EXPECTED_COUNT
                and existing_job.segment_count == EXPECTED_COUNT,
                "Target state exists without a completed source-import job",
            )
            db.rollback()
            print(f"already_applied={EXPECTED_COUNT}")
            return
        require(existing_job is None, "Source-import job already exists")

        now = dt.datetime.now(dt.timezone.utc)
        job = TranslationJob(
            job_key=JOB_KEY,
            source_book_id=SOURCE_BOOK_ID,
            language="en",
            status="running",
            provider=JOB_PROVIDER,
            model="muhammad-sarwar",
            prompt_version=IMPORT_VERSION,
            glossary_version=None,
            scope_json={
                "manifest_sha256": MANIFEST_SHA256,
                "public_ids": list(records),
                "translation_generation": "none",
            },
            batch_policy_json={
                "source": "checksum-pinned Muhammad Sarwar human text",
                "atomic_cardinality": "14-or-0",
                "translation_generation": "none",
            },
            hadith_count=0,
            segment_count=0,
            input_chars=sum(len(item[1].matn_raw) for item in selected),
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            estimated_cost_usd=0.0,
            created_at=now,
            updated_at=now,
            started_at=now,
        )
        db.add(job)
        db.flush()
        for index, (record, hadith, translation, segment, english, rendered_isnad) in enumerate(
            selected, start=1
        ):
            translation, segment = upsert(
                db,
                hadith,
                translation,
                segment,
                record,
                english,
                rendered_isnad,
                now,
            )
            require(
                target_present(hadith, translation, segment, record, english, rendered_isnad),
                f"Post-write validation failed: {hadith.public_id}",
            )
            item = TranslationJobItem(
                job_id=job.id,
                hadith_id=hadith.id,
                segment_id=segment.id,
                item_index=index,
                source_sha256=sha256_text(hadith.matn_raw),
                status="verified",
                risk_level="green",
                created_at=now,
                updated_at=now,
            )
            db.add(item)
            db.flush()
            provider, model, _ = source_configuration(record)
            db.add(
                TranslationAttempt(
                    job_id=job.id,
                    item_id=item.id,
                    provider=provider,
                    model=model,
                    status="completed",
                    request_json={
                        "translation_generation": "none",
                        "source_coordinate": record["source_coordinate"],
                        "source_matn_sha256": record["target_source_matn_sha256"],
                    },
                    response_json={
                        "published": True,
                        "human_source_only": True,
                        "english_sha256": record["source_english_sha256"],
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
