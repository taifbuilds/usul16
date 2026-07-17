"""Retire prohibited Codex text and harden Al-Kafi translation provenance.

Dry-run is the default.  The write pass is deliberately narrow and asserts
the known pilot-job residue before changing it.  External Thaqalayn rows are
matched back to checksum-pinned API/static snapshots, their exact English is
verified, and legacy source URLs are repaired.  Project-authored English is
removed from publication instead of being passed off as a sourced translation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_importer import (
    ThaqalaynRecord,
    parse_record,
    static_records_from_rows,
    strip_html_text,
)


SOURCE_BOOK_ID = "11005"
PILOT_JOB_KEY = "alkafi-en-pilot-300-v1"
EXPECTED_PILOT_ITEMS = 303
EXPECTED_CODEX_ATTEMPTS = 47
EXPECTED_CODEX_SEGMENT_ID = 12
EXPECTED_CODEX_PUBLIC_ID = "alkafi-12"
EXPECTED_API_SNAPSHOT_SHA256 = (
    "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
)
EXPECTED_STATIC_SNAPSHOT_SHA256 = (
    "a0e57d41ae653a9f8d2b88dca4c0a3e149ce0a25b07ba3a880ffb461db920d43"
)
QUARANTINE_PROJECT_ENGLISH = {
    "alkafi-10724",
    "alkafi-11166",
    "alkafi-11167",
    "alkafi-11168",
    "alkafi-11169",
    "alkafi-11277",
    "alkafi-11999",
    "alkafi-12739",
}
RETAINED_BOUNDED_EXCERPT = "alkafi-1160"
RETAINED_NUMERIC_CORRECTIONS = {"alkafi-1282", "alkafi-1292"}
AI_MARKERS = re.compile(
    r"(?:\bcodex\b|\bopenai\b|\bchatgpt\b|\bgpt(?:[-_ ]?\d|\b)|"
    r"\bmachine[-_ ]generated\b|\bai[-_ ]generated\b|\bllm\b)",
    re.IGNORECASE,
)
URL_VOLUME_RE = re.compile(r"(/hadith/)\d+(/)")

CODEX_FLAG = {
    "code": "prohibited_codex_translation",
    "severity": "critical",
    "detail": "Codex-generated English is prohibited from the Al-Kafi corpus.",
}
PROJECT_ENGLISH_FLAG = {
    "code": "requires_external_human_translation",
    "severity": "critical",
    "detail": (
        "This English included project-authored wording and was unpublished "
        "until an aligned external human translation can replace it."
    ),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def add_flag(flags: list | None, flag: dict[str, str]) -> list:
    result = list(flags or [])
    if not any(
        isinstance(existing, dict) and existing.get("code") == flag["code"]
        for existing in result
    ):
        result.append(flag)
    return result


def canonical_url(url: str | None, volume: int) -> str | None:
    if not url:
        return None
    return URL_VOLUME_RE.sub(rf"\g<1>{volume}\g<2>", url, count=1)


def load_api_records(path: Path) -> tuple[dict[tuple[int, int], ThaqalaynRecord], dict[str, ThaqalaynRecord]]:
    rows_by_volume = json.loads(path.read_text(encoding="utf-8"))
    by_key: dict[tuple[int, int], ThaqalaynRecord] = {}
    by_url: dict[str, ThaqalaynRecord] = {}
    for volume_text, rows in rows_by_volume.items():
        volume = int(volume_text)
        for raw in rows:
            record = parse_record(raw)
            if record.volume != volume:
                raise RuntimeError(
                    f"API snapshot volume mismatch for record {record.id}: "
                    f"{record.volume} != {volume}"
                )
            by_key[(volume, record.id)] = record
            if record.url:
                by_url[record.url] = record
    return by_key, by_url


def load_static_records(path: Path) -> tuple[dict[tuple[int, int], ThaqalaynRecord], dict[str, ThaqalaynRecord]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    by_volume = static_records_from_rows(rows)
    by_key: dict[tuple[int, int], ThaqalaynRecord] = {}
    by_url: dict[str, ThaqalaynRecord] = {}
    for volume, records in by_volume.items():
        for record in records:
            by_key[(volume, record.id)] = record
            if record.url:
                by_url[record.url] = record
    return by_key, by_url


def remote_id(provenance: dict) -> int | None:
    value = provenance.get("thaqalayn_id") or provenance.get("remote_id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def external_english_variants(record: ThaqalaynRecord) -> set[str]:
    """Exact normalized forms allowed without changing source meaning.

    Legacy API imports sometimes retained ``<br>`` while the deep recovery
    pass converted the same upstream HTML to plain text.  Both are source
    transformations, not locally authored wording.
    """

    return {
        value
        for value in (
            clean_ws(record.usable_translation),
            strip_html_text(record.usable_translation),
        )
        if value
    }


def find_record(
    *,
    translation: HadithTranslation,
    hadith: Hadith,
    by_key: dict[tuple[int, int], ThaqalaynRecord],
    by_url: dict[str, ThaqalaynRecord],
    by_text: dict[tuple[int, str], list[ThaqalaynRecord]],
) -> ThaqalaynRecord:
    provenance = dict(translation.provenance_json or {})
    volume = int(provenance.get("volume") or hadith.volume_start or 0)
    candidate = by_key.get((volume, remote_id(provenance) or -1))
    source_url = canonical_url(provenance.get("source_url"), volume)
    if candidate is None and source_url:
        candidate = by_url.get(source_url)
    current_hash = sha256_text(translation.matn_translation)
    if candidate is None or (
        translation.model not in {
            "muhammad-sarwar-editorially-corrected",
            "muhammad-sarwar-scoped-editorial",
        }
        and current_hash
        not in {sha256_text(value) for value in external_english_variants(candidate)}
    ):
        exact = by_text.get((volume, current_hash), [])
        if len(exact) == 1:
            candidate = exact[0]
    if candidate is None:
        raise RuntimeError(f"No source snapshot record for {hadith.public_id}")
    return candidate


def source_metadata(
    record: ThaqalaynRecord,
    *,
    snapshot_sha256: str,
    classification: str,
) -> dict[str, object]:
    return {
        "source_url": record.url,
        "thaqalayn_id": record.id,
        "volume": record.volume,
        "translator": record.translator,
        "translator_attribution": "upstream-metadata",
        "source_english_sha256": sha256_text(record.usable_translation),
        "source_plaintext_english_sha256": sha256_text(
            strip_html_text(record.usable_translation)
        ),
        "source_arabic_sha256": sha256_text(record.arabic_text),
        "source_record_sha256": json_sha256(record.raw),
        "source_snapshot_sha256": snapshot_sha256,
        "translation_classification": classification,
    }


def update_current_segment_metadata(
    translation: HadithTranslation,
    metadata: dict[str, object],
    *,
    now: dt.datetime,
) -> int:
    updated = 0
    for segment in translation.segments:
        if (
            segment.source_sha256 == translation.source_matn_sha256
            and clean_ws(segment.translation_text)
            == clean_ws(translation.matn_translation)
        ):
            current = dict(segment.metadata_json or {})
            current.update(metadata)
            segment.metadata_json = current
            segment.updated_at = now
            updated += 1
    return updated


def main() -> None:
    temp = Path(os.environ.get("TEMP") or os.environ.get("TMP") or ".")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-snapshot",
        type=Path,
        default=temp / "sarwar-alkafi-audit" / "thaqalayn-api-alkafi.json",
    )
    parser.add_argument(
        "--static-snapshot",
        type=Path,
        default=temp / "thaqalayn-al-kafi-static-full-fromzip.json",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    api_sha = file_sha256(args.api_snapshot)
    static_sha = file_sha256(args.static_snapshot)
    if api_sha != EXPECTED_API_SNAPSHOT_SHA256:
        raise RuntimeError(f"Unexpected API snapshot SHA-256: {api_sha}")
    if static_sha != EXPECTED_STATIC_SNAPSHOT_SHA256:
        raise RuntimeError(f"Unexpected static snapshot SHA-256: {static_sha}")

    api_by_key, api_by_url = load_api_records(args.api_snapshot)
    static_by_key, static_by_url = load_static_records(args.static_snapshot)
    api_by_text: dict[tuple[int, str], list[ThaqalaynRecord]] = defaultdict(list)
    static_by_text: dict[tuple[int, str], list[ThaqalaynRecord]] = defaultdict(list)
    for (volume, _), record in api_by_key.items():
        for value in external_english_variants(record):
            api_by_text[(volume, sha256_text(value))].append(record)
    for (volume, _), record in static_by_key.items():
        for value in external_english_variants(record):
            static_by_text[(volume, sha256_text(value))].append(record)

    with SessionLocal() as db:
        book = db.execute(
            select(Book).where(Book.source_book_id == SOURCE_BOOK_ID)
        ).scalar_one()
        hadiths = {
            row.id: row
            for row in db.execute(
                select(Hadith).where(Hadith.book_id == book.id)
            ).scalars()
        }
        public_ids = {row.public_id: row for row in hadiths.values()}
        translations = list(
            db.execute(
                select(HadithTranslation)
                .options(selectinload(HadithTranslation.segments))
                .where(
                    HadithTranslation.hadith_id.in_(hadiths),
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        )
        public_codex = [
            row
            for row in translations
            if row.status in {"human_reviewed", "published"}
            and row.risk_level == "green"
            and AI_MARKERS.search(
                " ".join(
                    [
                        row.provider or "",
                        row.model or "",
                        json.dumps(row.provenance_json or {}, ensure_ascii=False),
                    ]
                )
            )
        ]
        if public_codex:
            raise RuntimeError(
                f"Unexpected public Codex-marked translations: {[row.id for row in public_codex]}"
            )

        pilot = db.execute(
            select(TranslationJob).where(TranslationJob.job_key == PILOT_JOB_KEY)
        ).scalar_one()
        pilot_items = list(
            db.execute(
                select(TranslationJobItem).where(TranslationJobItem.job_id == pilot.id)
            ).scalars()
        )
        codex_attempts = list(
            db.execute(
                select(TranslationAttempt).where(
                    TranslationAttempt.job_id == pilot.id,
                    TranslationAttempt.provider == "codex-direct",
                )
            ).scalars()
        )
        if len(pilot_items) != EXPECTED_PILOT_ITEMS:
            raise RuntimeError(f"Expected {EXPECTED_PILOT_ITEMS} pilot items; found {len(pilot_items)}")
        if len(codex_attempts) != EXPECTED_CODEX_ATTEMPTS:
            raise RuntimeError(
                f"Expected {EXPECTED_CODEX_ATTEMPTS} Codex attempts; found {len(codex_attempts)}"
            )
        codex_segment = db.get(TranslationSegment, EXPECTED_CODEX_SEGMENT_ID)
        if codex_segment is None:
            raise RuntimeError("Expected residual Codex segment is missing")
        codex_hadith = hadiths.get(codex_segment.hadith_id)
        if codex_hadith is None or codex_hadith.public_id != EXPECTED_CODEX_PUBLIC_ID:
            raise RuntimeError("Residual Codex segment identity changed")
        codex_attempt_texts = {
            clean_ws((attempt.response_json or {}).get("translation_text"))
            for attempt in codex_attempts
        }
        residual_text = clean_ws(codex_segment.translation_text)
        if residual_text and residual_text not in codex_attempt_texts:
            raise RuntimeError("Residual segment no longer matches a Codex attempt")

        now = dt.datetime.now(dt.timezone.utc)
        provenance_updates = Counter()
        segment_metadata_updates = 0
        for translation in translations:
            if translation.provider not in {"thaqalayn-api", "thaqalayn-data"}:
                continue
            hadith = hadiths[translation.hadith_id]
            is_api = translation.provider == "thaqalayn-api"
            by_key = api_by_key if is_api else static_by_key
            by_url = api_by_url if is_api else static_by_url
            by_text = api_by_text if is_api else static_by_text
            snapshot_sha = api_sha if is_api else static_sha
            record = find_record(
                translation=translation,
                hadith=hadith,
                by_key=by_key,
                by_url=by_url,
                by_text=by_text,
            )
            if not clean_ws(record.translator):
                raise RuntimeError(f"Missing external translator for {hadith.public_id}")
            exact = sha256_text(translation.matn_translation) in {
                sha256_text(value) for value in external_english_variants(record)
            }
            corrected = hadith.public_id in RETAINED_NUMERIC_CORRECTIONS
            if not exact and not corrected and hadith.public_id != "alkafi-11999":
                raise RuntimeError(
                    f"Current text is not exact to pinned source: {hadith.public_id}"
                )
            classification = (
                "externally_sourced_numeric_correction"
                if corrected
                else "external_source_normalized"
            )
            metadata = source_metadata(
                record,
                snapshot_sha256=snapshot_sha,
                classification=classification,
            )
            if corrected:
                metadata["rendered_english_sha256"] = sha256_text(
                    translation.matn_translation
                )
            provenance = dict(translation.provenance_json or {})
            before_url = provenance.get("source_url")
            provenance.update(metadata)
            translation.provenance_json = provenance
            translation.updated_at = now
            provenance_updates["api" if is_api else "static"] += 1
            if before_url != provenance.get("source_url"):
                provenance_updates["source_urls_repaired"] += 1
            segment_metadata_updates += update_current_segment_metadata(
                translation, metadata, now=now
            )

        retained = public_ids[RETAINED_BOUNDED_EXCERPT]
        retained_translation = next(
            row for row in translations if row.hadith_id == retained.id
        )
        retained_provenance = dict(retained_translation.provenance_json or {})
        retained_provenance.update(
            {
                "translation_classification": "bounded_external_excerpt",
                "rendered_english_sha256": sha256_text(
                    retained_translation.matn_translation
                ),
                "translator_attribution": "upstream-metadata",
            }
        )
        retained_translation.provenance_json = retained_provenance
        retained_translation.updated_at = now

        quarantine_rows: list[tuple[Hadith, HadithTranslation]] = []
        for public_id in sorted(QUARANTINE_PROJECT_ENGLISH):
            hadith = public_ids[public_id]
            translation = next(
                row for row in translations if row.hadith_id == hadith.id
            )
            if translation.status == "rejected" and not translation.matn_translation:
                continue
            quarantine_rows.append((hadith, translation))
        if len(quarantine_rows) not in {0, len(QUARANTINE_PROJECT_ENGLISH)}:
            raise RuntimeError(
                f"Refusing partial editorial quarantine: {len(quarantine_rows)}"
            )

        redacted_attempts = 0
        for attempt in codex_attempts:
            response = dict(attempt.response_json or {})
            original = clean_ws(response.pop("translation_text", None))
            if original:
                response["redacted_translation_sha256"] = sha256_text(original)
                response["redacted_translation_chars"] = len(original)
                redacted_attempts += 1
            response.update(
                {
                    "redacted": True,
                    "publication_status": "prohibited",
                    "reason": CODEX_FLAG["code"],
                }
            )
            attempt.response_json = response
            attempt.status = "rejected"
            attempt.error_text = CODEX_FLAG["detail"]

        codex_segment.translation_text = None
        codex_segment.status = "qa_failed"
        codex_segment.risk_level = "red"
        codex_segment.risk_flags = add_flag(codex_segment.risk_flags, CODEX_FLAG)
        codex_metadata = dict(codex_segment.metadata_json or {})
        codex_metadata.update(
            {
                "publication_status": "prohibited",
                "translation_text_redacted": True,
                "reason": CODEX_FLAG["code"],
            }
        )
        codex_segment.metadata_json = codex_metadata
        codex_segment.updated_at = now
        for item in pilot_items:
            item.status = "skipped"
            item.risk_level = "red"
            item.updated_at = now
        pilot.status = "cancelled"
        pilot.completed_at = pilot.completed_at or now
        pilot.updated_at = now
        pilot_scope = dict(pilot.scope_json or {})
        pilot_scope["retirement_audit"] = {
            "status": "cancelled",
            "reason": CODEX_FLAG["code"],
            "attempts_redacted": EXPECTED_CODEX_ATTEMPTS,
            "retired_at": now.isoformat(),
        }
        pilot.scope_json = pilot_scope

        quarantined_segments = 0
        quarantined_items = 0
        for hadith, translation in quarantine_rows:
            removed_hash = sha256_text(translation.matn_translation)
            provenance = dict(translation.provenance_json or {})
            provenance.update(
                {
                    "publication_status": "rejected",
                    "reason": PROJECT_ENGLISH_FLAG["code"],
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
            translation.risk_flags = add_flag(
                translation.risk_flags, PROJECT_ENGLISH_FLAG
            )
            translation.updated_at = now
            for segment in translation.segments:
                if segment.translation_text:
                    segment.translation_text = None
                segment.status = "qa_failed"
                segment.risk_level = "red"
                segment.risk_flags = add_flag(
                    segment.risk_flags, PROJECT_ENGLISH_FLAG
                )
                metadata = dict(segment.metadata_json or {})
                metadata.update(
                    {
                        "publication_status": "rejected",
                        "translation_text_redacted": True,
                        "reason": PROJECT_ENGLISH_FLAG["code"],
                    }
                )
                segment.metadata_json = metadata
                segment.updated_at = now
                quarantined_segments += 1
            items = list(
                db.execute(
                    select(TranslationJobItem).where(
                        TranslationJobItem.hadith_id == hadith.id,
                        TranslationJobItem.segment_id.in_(
                            [segment.id for segment in translation.segments]
                        ),
                    )
                ).scalars()
            )
            for item in items:
                if item.job_id == pilot.id:
                    continue
                item.status = "qa_failed"
                item.risk_level = "red"
                item.updated_at = now
                quarantined_items += 1

        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "api_snapshot_sha256": api_sha,
            "static_snapshot_sha256": static_sha,
            "public_codex_rows_before": len(public_codex),
            "pilot_job_id": pilot.id,
            "pilot_items_retired": len(pilot_items),
            "codex_attempts": len(codex_attempts),
            "codex_attempt_payloads_redacted": redacted_attempts,
            "residual_codex_segment": codex_segment.id,
            "project_english_rows_quarantined": len(quarantine_rows),
            "project_segments_quarantined": quarantined_segments,
            "project_job_items_quarantined": quarantined_items,
            "provenance_rows_verified": dict(provenance_updates),
            "segment_metadata_rows_verified": segment_metadata_updates,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not args.apply:
            db.rollback()
            return
        db.commit()
        print("committed=true")


if __name__ == "__main__":
    main()
