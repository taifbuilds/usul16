"""Freeze the final public Al-Kafi extent/editorial blocker set.

This is deliberately read-only with respect to SQLite.  It records the exact
green rows observed by the exhaustive public-translation audit before they are
quarantined, together with enough hashes and object IDs to reproduce the
decision without trusting mutable display text.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "eshia_research.db"
OUTPUT_PATH = ROOT / "scratch_audit" / "alkafi_public_extent_blockers_20260716.json"

DEFINITE_COLOPHON_IDS = {
    "alkafi-211",
    "alkafi-4134",
    "alkafi-4227",
    "alkafi-4772",
    "alkafi-5698",
    "alkafi-6228",
    "alkafi-6681",
    "alkafi-8169",
    "alkafi-8321",
    "alkafi-9383",
    "alkafi-10373",
    "alkafi-10596",
    "alkafi-11096",
    "alkafi-11210",
    "alkafi-11329",
    "alkafi-11403",
    "alkafi-12933",
    "alkafi-13279",
    "alkafi-13592",
    "alkafi-14040",
    "alkafi-14529",
    "alkafi-14607",
    "alkafi-14751",
}

DEFINITE_EDITORIAL_IDS = {
    "alkafi-12",
    "alkafi-164",
    "alkafi-270",
    "alkafi-302",
    "alkafi-467",
    "alkafi-632",
    "alkafi-932",
    "alkafi-2275",
    "alkafi-2861",
    "alkafi-3057",
    "alkafi-4167",
    "alkafi-4177",
    "alkafi-5842",
    "alkafi-6296",
    "alkafi-6703",
    "alkafi-8104",
    "alkafi-8122",
    "alkafi-8189",
    "alkafi-8230",
    "alkafi-10287",
    "alkafi-14758",
    "alkafi-14759",
    "alkafi-14773",
    "alkafi-14856",
    "alkafi-14946",
    "alkafi-14967",
    "alkafi-15308",
}

MALFORMED_TRANSLATED_COLOPHON_IDS = {
    "alkafi-426",
    "alkafi-934",
    "alkafi-12112",
}

SPECIAL_REASONS = {
    "alkafi-302": (
        "Large unvocalized doctrinal commentary is spliced between the short "
        "report and its vocalized continuation."
    ),
    "alkafi-632": (
        "Editorial notes are appended to the Arabic and the local Arabic ends "
        "before the published English report does."
    ),
    "alkafi-3057": (
        "End-of-book colophon plus Persian/Arabic printed-blank-page notice is "
        "stored inside the hadith matn but omitted in English."
    ),
    "alkafi-4167": (
        "Long lexicographical commentary is spliced into the report and the "
        "local Arabic truncates mid-sentence while the published English continues."
    ),
    "alkafi-8104": (
        "A modern verse/editorial citation to a later reference work is appended "
        "to the Arabic but omitted in English."
    ),
    "alkafi-8122": (
        "A long Majlisi marginal commentary, including page-continuation labels, "
        "is appended to the Arabic but omitted in English."
    ),
}

PUBLIC_STATUSES = {"human_reviewed", "published"}
PUBLIC_CLASSES = {
    "external_source_normalized",
    "verbatim_external_matn_excerpt",
    "bounded_external_excerpt",
}
FORBIDDEN_AI_MARKERS = (
    "codex",
    "openai",
    "gpt",
    "llm",
    "ai-generated",
    "ai_generated",
    "ai generated",
    "machine-generated",
    "machine_generated",
    "machine generated",
    "artificial intelligence",
    "project_authored",
    "project-authored",
    "project authored",
)


def clean_ws(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256_text(value: str | None) -> str:
    return hashlib.sha256(clean_ws(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def parse_json(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def is_public(row: sqlite3.Row) -> bool:
    if row["language"] != "en" or row["translation_version"] != "matn_en_v1":
        return False
    if row["status"] not in PUBLIC_STATUSES or row["risk_level"] != "green":
        return False
    if not clean_ws(row["matn_translation"]):
        return False
    risk_flags = parse_json(row["risk_flags"], [])
    if isinstance(risk_flags, list) and any(
        isinstance(flag, dict) and flag.get("severity") == "critical"
        for flag in risk_flags
    ):
        return False
    provenance = parse_json(row["provenance_json"], {})
    haystack = " ".join(
        (
            str(row["provider"] or ""),
            str(row["model"] or ""),
            json.dumps(provenance, ensure_ascii=False, sort_keys=True),
        )
    ).casefold()
    if any(marker in haystack for marker in FORBIDDEN_AI_MARKERS):
        return False
    if not isinstance(provenance, dict):
        return False
    classification = provenance.get("translation_classification") or provenance.get(
        "classification"
    )
    if not str(provenance.get("translator") or "").strip():
        return False
    if classification not in PUBLIC_CLASSES:
        return False
    expected_isnad = sha256_text(row["isnad_raw"]) if row["isnad_raw"] else None
    return bool(
        row["source_full_sha256"] == sha256_text(row["full_text_raw"])
        and row["source_isnad_sha256"] == expected_isnad
        and row["source_matn_sha256"] == sha256_text(row["matn_raw"])
    )


def source_pins(provenance: Any) -> dict[str, Any]:
    """Extract compact scalar source identifiers/checksums from provenance."""

    pins: dict[str, Any] = {}
    scalar_keys = {
        "source",
        "source_url",
        "source_kind",
        "source_coordinate",
        "translator",
        "translation_classification",
        "classification",
        "remote_id",
        "thaqalayn_id",
        "source_hadith_id",
        "source_record_id",
        "api_id",
        "static_index",
        "record_id",
        "id",
        "url",
        "field",
    }

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                child_path = f"{path}.{key}" if path else key
                if isinstance(child, (str, int, float, bool)) and (
                    "sha256" in key.casefold()
                    or key in scalar_keys
                    or key.casefold().endswith("_url")
                ):
                    pins[child_path] = child
                elif isinstance(child, (dict, list)):
                    walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, (dict, list)):
                    walk(child, f"{path}[{index}]")

    walk(provenance, "")
    return pins


def artifact_pin(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    data = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def numeric_public_id(public_id: str) -> int:
    return int(public_id.rsplit("-", 1)[1])


def main() -> None:
    all_ids = (
        DEFINITE_COLOPHON_IDS
        | DEFINITE_EDITORIAL_IDS
        | MALFORMED_TRANSLATED_COLOPHON_IDS
    )
    assert len(DEFINITE_COLOPHON_IDS) == 23
    assert len(DEFINITE_EDITORIAL_IDS) == 27
    assert len(MALFORMED_TRANSLATED_COLOPHON_IDS) == 3
    assert len(all_ids) == 53

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")

    placeholders = ",".join("?" for _ in all_ids)
    rows = connection.execute(
        f"""
        SELECT
            h.id AS hadith_id,
            h.public_id,
            h.sequence_in_book,
            h.volume_start,
            h.page_start,
            h.page_end,
            h.printed_number,
            h.full_text_raw,
            h.isnad_raw,
            h.matn_raw,
            t.id AS translation_id,
            t.language,
            t.translation_version,
            t.source_full_sha256,
            t.source_isnad_sha256,
            t.source_matn_sha256,
            t.rendered_isnad_en,
            t.matn_translation,
            t.full_translation,
            t.status,
            t.risk_level,
            t.risk_flags,
            t.provider,
            t.model,
            t.provenance_json
        FROM hadiths AS h
        JOIN hadith_translations AS t ON t.hadith_id = h.id
        WHERE h.book_id = 1178
          AND h.public_id IN ({placeholders})
          AND t.language = 'en'
          AND t.translation_version = 'matn_en_v1'
        """,
        tuple(sorted(all_ids, key=numeric_public_id)),
    ).fetchall()
    by_id = {row["public_id"]: row for row in rows}
    missing = sorted(all_ids - set(by_id), key=numeric_public_id)
    if missing:
        raise RuntimeError(f"Missing target translations: {missing}")

    public_failures = [public_id for public_id, row in by_id.items() if not is_public(row)]
    if public_failures:
        raise RuntimeError(
            "Targets changed before freeze and are no longer public: "
            + ", ".join(sorted(public_failures, key=numeric_public_id))
        )

    records: list[dict[str, Any]] = []
    for public_id in sorted(all_ids, key=numeric_public_id):
        row = by_id[public_id]
        provenance = parse_json(row["provenance_json"], {})
        risk_flags = parse_json(row["risk_flags"], [])
        segments = connection.execute(
            """
            SELECT id, status, risk_level, source_sha256, translation_text
            FROM translation_segments
            WHERE translation_id = ?
            ORDER BY id
            """,
            (row["translation_id"],),
        ).fetchall()
        job_items = connection.execute(
            """
            SELECT id, job_id, segment_id, status, risk_level, source_sha256
            FROM translation_job_items
            WHERE hadith_id = ?
            ORDER BY id
            """,
            (row["hadith_id"],),
        ).fetchall()

        if public_id in DEFINITE_COLOPHON_IDS:
            disposition = "definite_blocker"
            category = "untranslated_colophon_or_next_book_heading"
            reason = (
                "A book/part colophon or next-book heading is embedded in matn_raw "
                "but absent from the published English extent."
            )
        elif public_id in DEFINITE_EDITORIAL_IDS:
            disposition = "definite_blocker"
            category = "inline_or_appended_editorial_contamination"
            reason = SPECIAL_REASONS.get(
                public_id,
                "Editorial footnote/commentary text is embedded in the Arabic "
                "hadith extent but absent from the published English extent.",
            )
        else:
            disposition = "malformed_boundary_nonblocking"
            category = "translated_colophon_inside_hadith_boundary"
            reason = (
                "The external English includes at least the colophon, so this is "
                "not a wrong-pair blocker; however the paratext is incorrectly "
                "stored inside the hadith boundary and should be trimmed on both sides."
            )

        rendered_public = clean_ws(
            row["full_translation"]
            or " ".join(
                part
                for part in (
                    row["rendered_isnad_en"],
                    row["matn_translation"],
                )
                if clean_ws(part)
            )
        )
        actual_source_hashes = {
            "full_sha256": sha256_text(row["full_text_raw"]),
            "isnad_sha256": sha256_text(row["isnad_raw"])
            if row["isnad_raw"]
            else None,
            "matn_sha256": sha256_text(row["matn_raw"]),
        }
        stored_source_hashes = {
            "full_sha256": row["source_full_sha256"],
            "isnad_sha256": row["source_isnad_sha256"],
            "matn_sha256": row["source_matn_sha256"],
        }
        record = {
            "public_id": public_id,
            "disposition": disposition,
            "category": category,
            "reason": reason,
            "hadith": {
                "id": row["hadith_id"],
                "sequence_in_book": row["sequence_in_book"],
                "volume": row["volume_start"],
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "printed_number": row["printed_number"],
                "current_arabic_hashes": actual_source_hashes,
            },
            "translation": {
                "id": row["translation_id"],
                "status": row["status"],
                "risk_level": row["risk_level"],
                "provider": row["provider"],
                "model": row["model"],
                "translation_version": row["translation_version"],
                "stored_source_hashes": stored_source_hashes,
                "source_hashes_current": stored_source_hashes == actual_source_hashes,
                "rendered_isnad_en_sha256": sha256_text(row["rendered_isnad_en"]),
                "matn_translation_sha256": sha256_text(row["matn_translation"]),
                "full_translation_sha256": sha256_text(row["full_translation"]),
                "public_rendered_english_sha256": sha256_text(rendered_public),
                "risk_flags_sha256": sha256_bytes(canonical_bytes(risk_flags)),
                "provenance_sha256": sha256_bytes(canonical_bytes(provenance)),
                "source_pins": source_pins(provenance),
            },
            "translation_segments": [
                {
                    "id": segment["id"],
                    "status": segment["status"],
                    "risk_level": segment["risk_level"],
                    "source_sha256": segment["source_sha256"],
                    "translation_sha256": sha256_text(segment["translation_text"]),
                }
                for segment in segments
            ],
            "translation_job_items": [dict(item) for item in job_items],
        }
        record["record_sha256"] = sha256_bytes(canonical_bytes(record))
        records.append(record)

    # Pin the complete fail-closed public set at the instant of the freeze.
    public_rows = connection.execute(
        """
        SELECT
            h.public_id, h.full_text_raw, h.isnad_raw, h.matn_raw,
            t.language, t.translation_version, t.source_full_sha256,
            t.source_isnad_sha256, t.source_matn_sha256,
            t.rendered_isnad_en, t.matn_translation, t.full_translation,
            t.status, t.risk_level, t.risk_flags, t.provider, t.model,
            t.provenance_json
        FROM hadiths AS h
        JOIN hadith_translations AS t ON t.hadith_id = h.id
        WHERE h.book_id = 1178
          AND t.language = 'en'
          AND t.translation_version = 'matn_en_v1'
        ORDER BY h.sequence_in_book
        """
    ).fetchall()
    public_fingerprint_rows = []
    for row in public_rows:
        if not is_public(row):
            continue
        provenance = parse_json(row["provenance_json"], {})
        rendered = clean_ws(
            row["full_translation"]
            or " ".join(
                part
                for part in (row["rendered_isnad_en"], row["matn_translation"])
                if clean_ws(part)
            )
        )
        public_fingerprint_rows.append(
            {
                "public_id": row["public_id"],
                "arabic_full_sha256": sha256_text(row["full_text_raw"]),
                "arabic_isnad_sha256": sha256_text(row["isnad_raw"])
                if row["isnad_raw"]
                else None,
                "arabic_matn_sha256": sha256_text(row["matn_raw"]),
                "english_sha256": sha256_text(rendered),
                "provenance_sha256": sha256_bytes(canonical_bytes(provenance)),
            }
        )

    temp = Path(tempfile.gettempdir())
    artifacts = [
        ROOT / "scratch_audit" / "alkafi_opening_sarwar_pdf_manifest_20260716.json",
        ROOT / "scratch_audit" / "alkafi_remaining_sarwar_pdf_manifest_20260716.json",
        ROOT / "scratch_audit" / "alkafi_wrong_pair_sarwar_repair_manifest_20260716.json",
        ROOT / "scratch_audit" / "alkafi_structural_translation_republication_manifest_20260716.json",
        temp / "sarwar-alkafi-audit" / "thaqalayn-api-alkafi.json",
        temp / "thaqalayn-al-kafi-static-full-fromzip.json",
    ]
    stat = DB_PATH.stat()
    payload: dict[str, Any] = {
        "schema_version": "alkafi_public_extent_blockers_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "book_id": 1178,
            "book": "Al-Kafi",
            "policy": "fail_closed_public_english",
            "database_mode": "read_only",
            "audit_method": (
                "Unicode-normalized whole-corpus colophon/editorial marker scan, "
                "Arabic diacritic-transition scan, manual Arabic-English extent "
                "confirmation, and current source/provenance hash capture"
            ),
        },
        "database_snapshot": {
            "path": str(DB_PATH),
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sqlite_data_version": connection.execute("PRAGMA data_version").fetchone()[0],
            "fail_closed_public_count": len(public_fingerprint_rows),
            "fail_closed_public_set_sha256": sha256_bytes(
                canonical_bytes(public_fingerprint_rows)
            ),
        },
        "source_artifact_pins": [artifact_pin(path) for path in artifacts],
        "counts": {
            "records": len(records),
            "definite_blockers": sum(
                record["disposition"] == "definite_blocker" for record in records
            ),
            "untranslated_colophon_or_heading": len(DEFINITE_COLOPHON_IDS),
            "editorial_or_truncation_contamination": len(DEFINITE_EDITORIAL_IDS),
            "malformed_translated_colophon_boundary": len(
                MALFORMED_TRANSLATED_COLOPHON_IDS
            ),
            "targets_public_at_freeze": sum(is_public(row) for row in by_id.values()),
        },
        "records": records,
    }
    payload["payload_sha256"] = sha256_bytes(canonical_bytes(payload))
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT_PATH),
                "file_sha256": sha256_bytes(OUTPUT_PATH.read_bytes()),
                "payload_sha256": payload["payload_sha256"],
                "counts": payload["counts"],
                "database_snapshot": payload["database_snapshot"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
