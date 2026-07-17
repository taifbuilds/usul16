"""Apply the reviewed Sarwar recoveries from the 179-report Al-Kafi dossier.

The script is dry-run by default.  It treats the dossier as a reviewed
manifest, revalidates every local row and every source text, verifies the
published PDF checksums, rejects HubeAli-style source markers, and commits the
whole batch in one transaction only with ``--apply``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from dataclasses import asdict
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
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text, source_norm
from eshia_research.translation.thaqalayn_importer import (
    IMPORT_BLOCKING_QA_CODES,
    static_records_from_rows,
)


JOB_KEY = "alkafi-sarwar-179-source-recovery-v1"
MATCHER = "sarwar_179_arabic_anchor_v1"
PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
READY_DECISION = "ready_sarwar"
EXPECTED_TARGET = 179
EXPECTED_READY = 109
FORBIDDEN_SOURCE_MARKERS = ("hubeali.com", "(azwj)", "(saww)", "(asws)")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_public(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC_STATUSES
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def source_values(
    record: dict[str, object],
    *,
    static_by_key: dict[tuple[int, int], object],
    pdf_by_h: dict[int, dict[str, object]],
) -> tuple[str, str, dict[str, object]]:
    source = record["source"]
    if not isinstance(source, dict):
        raise RuntimeError(f"Missing source for {record['public_id']}")
    volume = int(record["volume"])
    remote_id = int(source["remote_id"])
    kind = str(source["kind"])
    if kind == "thaqalayn_static_sarwar":
        remote = static_by_key.get((volume, remote_id))
        if remote is None:
            raise RuntimeError(f"Static source disappeared for {record['public_id']}")
        if remote.translator != "Muhammad Sarwar":
            raise RuntimeError(f"Static translator changed for {record['public_id']}")
        text = clean_ws(remote.usable_translation)
        provider = "thaqalayn-data"
        evidence = {
            "source": "ThaqalaynData static edition",
            "source_url": remote.url,
            "remote_id": remote_id,
        }
    elif kind == "published_sarwar_pdf_recovery":
        pdf = pdf_by_h.get(remote_id)
        if pdf is None:
            raise RuntimeError(f"PDF source disappeared for {record['public_id']}")
        for key in ("physical_volume", "pdf_page", "source_url", "source_sha256", "marker"):
            if pdf.get(key) != source.get(key):
                raise RuntimeError(
                    f"PDF evidence changed for {record['public_id']}: {key}"
                )
        text = clean_ws(str(pdf["english"]))
        provider = "sarwar-published-scan"
        evidence = {
            "source": "published Muhammad Sarwar scan",
            "source_url": pdf["source_url"],
            "remote_id": remote_id,
            "physical_volume": pdf["physical_volume"],
            "pdf_page": pdf["pdf_page"],
            "pdf_sha256": pdf["source_sha256"],
            "source_marker": pdf["marker"],
        }
    else:
        raise RuntimeError(f"Unsupported source kind for {record['public_id']}: {kind}")
    if text != clean_ws(str(record["english"])):
        raise RuntimeError(f"Reviewed source text changed for {record['public_id']}")
    hits = [marker for marker in FORBIDDEN_SOURCE_MARKERS if marker in text.casefold()]
    if hits:
        raise RuntimeError(f"Source-purity failure for {record['public_id']}: {hits}")
    return text, provider, evidence


def upsert_translation(
    db,
    hadith: Hadith,
    existing: HadithTranslation | None,
    *,
    english: str,
    provider: str,
    evidence: dict[str, object],
    identity: dict[str, object],
    qa_flags: list[dict[str, str]],
    dossier_sha256: str,
    now: dt.datetime,
) -> tuple[HadithTranslation, TranslationSegment]:
    provenance = {
        **evidence,
        "translator": "Muhammad Sarwar",
        "identity": identity,
        "matcher_version": MATCHER,
        "reviewed_dossier_sha256": dossier_sha256,
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
        "risk_flags": qa_flags,
        "provider": provider,
        "model": "muhammad-sarwar",
        "prompt_version": MATCHER,
        "glossary_version": None,
        "qa_version": QA_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_estimate_usd": 0.0,
        "provenance_json": provenance,
        "updated_at": now,
    }
    if existing is None:
        translation = HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            created_at=now,
            **values,
        )
        db.add(translation)
    else:
        translation = existing
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
        "risk_flags": qa_flags,
        "metadata_json": {
            "source_norm": source_norm(hadith.matn_raw),
            "provider": provider,
            "translator": "Muhammad Sarwar",
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
    return translation, segment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("static_cache", type=Path)
    parser.add_argument("pdf_records", type=Path)
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    dossier_bytes = args.dossier.read_bytes()
    dossier_sha256 = hashlib.sha256(dossier_bytes).hexdigest()
    dossier = json.loads(dossier_bytes)
    records = dossier["records"]
    ready = [record for record in records if record["decision"] == READY_DECISION]
    if len(records) != EXPECTED_TARGET or len(ready) != EXPECTED_READY:
        raise RuntimeError(
            f"Manifest cardinality changed: target={len(records)} ready={len(ready)}"
        )
    public_ids = [str(record["public_id"]) for record in ready]
    remote_ids = [int(record["source"]["remote_id"]) for record in ready]
    if len(set(public_ids)) != len(public_ids):
        raise RuntimeError("The ready manifest contains duplicate public IDs")
    if len(set(remote_ids)) != len(remote_ids):
        raise RuntimeError("The ready manifest contains duplicate source report IDs")

    static_rows = json.loads(args.static_cache.read_text(encoding="utf-8"))
    static_by_key = {
        (remote.volume, remote.id): remote
        for rows in static_records_from_rows(static_rows).values()
        for remote in rows
    }
    pdf_payload = json.loads(args.pdf_records.read_text(encoding="utf-8"))
    pdf_by_h = {
        int(record["hadith_number"]): record
        for record in pdf_payload["records"]
        if not record.get("hadith_suffix")
    }
    for manifest in dossier["summary"]["source_manifests"]:
        path = Path(str(manifest["path"]))
        if not path.is_file():
            raise RuntimeError(f"Required published scan is missing: {path}")
        actual = file_sha256(path)
        if actual.casefold() != str(manifest["sha256"]).casefold():
            raise RuntimeError(f"Published scan checksum changed: {path}")

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
        for record in ready:
            public_id = str(record["public_id"])
            hadith = hadiths.get(public_id)
            if hadith is None:
                raise RuntimeError(f"Reviewed local report disappeared: {public_id}")
            if hadith.full_text_raw != record["arabic"] or hadith.matn_raw != record["matn"]:
                raise RuntimeError(f"Reviewed Arabic changed for {public_id}")
            if hadith.volume_start != record["volume"]:
                raise RuntimeError(f"Reviewed volume changed for {public_id}")
            existing = translations.get(hadith.id)
            if is_public(existing, hadith):
                # A completed rerun is deliberately a no-op; a partial state is
                # rejected below so the reviewed batch cannot be half-applied.
                continue
            english, provider, evidence = source_values(
                record, static_by_key=static_by_key, pdf_by_h=pdf_by_h
            )
            qa = assess_translation(hadith.matn_raw, english)
            qa_flags = [asdict(flag) for flag in qa.flags]
            blocking = [
                flag["code"]
                for flag in qa_flags
                if flag["code"] in IMPORT_BLOCKING_QA_CODES
            ]
            if blocking or blocking != record["blocking_qa"]:
                raise RuntimeError(f"Blocking QA changed for {public_id}: {blocking}")
            selected.append((record, hadith, existing, english, provider, evidence, qa_flags))

        if len(selected) not in {0, EXPECTED_READY}:
            raise RuntimeError(
                f"Refusing partial batch: {len(selected)} of {EXPECTED_READY} reports need import"
            )
        source_counts: dict[str, int] = {}
        volume_counts: dict[int, int] = {}
        for record, _, _, _, provider, _, _ in selected:
            source_counts[provider] = source_counts.get(provider, 0) + 1
            volume = int(record["volume"])
            volume_counts[volume] = volume_counts.get(volume, 0) + 1
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "dossier_sha256": dossier_sha256,
                    "selected": len(selected),
                    "source_counts": source_counts,
                    "volume_counts": volume_counts,
                },
                indent=2,
            )
        )
        if not args.apply or not selected:
            db.rollback()
            return

        existing_job = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == JOB_KEY)
        ).scalar_one_or_none()
        if existing_job is not None:
            raise RuntimeError(f"Audit job already exists while batch is incomplete: {JOB_KEY}")
        now = dt.datetime.now(dt.timezone.utc)
        job = TranslationJob(
            job_key=JOB_KEY,
            source_book_id="11005",
            language="en",
            status="running",
            provider="source-recovery",
            model="muhammad-sarwar",
            prompt_version=MATCHER,
            glossary_version=None,
            scope_json={
                "reviewed_dossier_sha256": dossier_sha256,
                "target": EXPECTED_TARGET,
                "selected": EXPECTED_READY,
                "public_ids": public_ids,
            },
            batch_policy_json={
                "mode": "direct_arabic_or_one_to_one_between_direct_anchors",
                "source_priority": "Muhammad Sarwar only",
                "forbidden_markers": list(FORBIDDEN_SOURCE_MARKERS),
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
        for item_index, (record, hadith, existing, english, provider, evidence, qa_flags) in enumerate(
            selected, start=1
        ):
            _, segment = upsert_translation(
                db,
                hadith,
                existing,
                english=english,
                provider=provider,
                evidence=evidence,
                identity=record["identity"],
                qa_flags=qa_flags,
                dossier_sha256=dossier_sha256,
                now=now,
            )
            job_item = TranslationJobItem(
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
            db.add(job_item)
            db.flush()
            db.add(
                TranslationAttempt(
                    job_id=job.id,
                    item_id=job_item.id,
                    provider=provider,
                    model="muhammad-sarwar",
                    status="completed",
                    request_json={**evidence, "identity": record["identity"]},
                    response_json={"qa_flags": qa_flags, "published": True},
                    input_tokens=0,
                    output_tokens=0,
                    cost_estimate_usd=0.0,
                    created_at=now,
                )
            )
        job.hadith_count = EXPECTED_READY
        job.segment_count = EXPECTED_READY
        job.status = "completed"
        job.completed_at = now
        job.updated_at = now
        db.commit()
        print(f"committed={EXPECTED_READY}")


if __name__ == "__main__":
    main()
