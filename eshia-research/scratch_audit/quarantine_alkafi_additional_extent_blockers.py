"""Quarantine seven newly proven Al-Kafi extent/alignment blockers.

Dry-run is the default. ``--apply`` clears public English atomically for all
seven rows while preserving source/audit history. Arabic text is never changed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "eshia_research.db"
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_additional_extent_blockers_20260716.json"
)
MANIFEST_SHA256 = (
    "4795926fc7748515e6b752382e7f107ffcaf0b08ae3415b14d402e90c9d25813"
)
EXPECTED_COUNT = 7
AUDIT_VERSION = "alkafi_additional_extent_quarantine_v1"
PUBLIC_STATUSES = {"human_reviewed", "published"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_sha256(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_value(value: str | Any | None) -> Any:
    if value is None or not isinstance(value, str):
        return value
    return json.loads(value)


def canonical_json_sha256(value: str | Any | None) -> str:
    payload = json.dumps(
        json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def add_flag(flags: Any, detail: str) -> list[Any]:
    result = list(json_value(flags) or [])
    if not any(
        isinstance(flag, dict)
        and flag.get("code") == "confirmed_additional_extent_blocker"
        for flag in result
    ):
        result.append(
            {
                "code": "confirmed_additional_extent_blocker",
                "severity": "critical",
                "detail": detail,
                "audit_version": AUDIT_VERSION,
                "manifest_sha256": MANIFEST_SHA256,
            }
        )
    return result


def connect(path: Path, *, writable: bool) -> sqlite3.Connection:
    if writable:
        connection = sqlite3.connect(path)
    else:
        connection = sqlite3.connect(
            f"file:{path.resolve().as_posix()}?mode=ro", uri=True
        )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def target_state(
    translation: sqlite3.Row,
    segment: sqlite3.Row,
    item: sqlite3.Row,
) -> bool:
    provenance = json_value(translation["provenance_json"]) or {}
    metadata = json_value(segment["metadata_json"]) or {}
    return bool(
        translation["status"] == "rejected"
        and translation["risk_level"] == "red"
        and translation["rendered_isnad_en"] is None
        and translation["matn_translation"] is None
        and translation["full_translation"] is None
        and provenance.get("publication_status") == "rejected"
        and provenance.get("additional_extent_audit", {}).get("manifest_sha256")
        == MANIFEST_SHA256
        and segment["status"] == "qa_failed"
        and segment["risk_level"] == "red"
        and segment["translation_text"] is None
        and metadata.get("additional_extent_audit", {}).get("manifest_sha256")
        == MANIFEST_SHA256
        and item["status"] == "qa_failed"
        and item["risk_level"] == "red"
    )


def load_rows(
    connection: sqlite3.Connection, record: dict[str, Any]
) -> tuple[sqlite3.Row, sqlite3.Row, sqlite3.Row, sqlite3.Row]:
    public_id = record["public_id"]
    hadith = connection.execute(
        "SELECT * FROM hadiths WHERE public_id=?", (public_id,)
    ).fetchone()
    require(hadith is not None, f"Missing hadith: {public_id}")
    require(int(hadith["id"]) == int(record["hadith_id"]), f"Hadith ID changed: {public_id}")
    require(
        raw_sha256(hadith["full_text_raw"]) == record["current_full_sha256"]
        and raw_sha256(hadith["isnad_raw"]) == record["current_isnad_sha256"]
        and raw_sha256(hadith["matn_raw"]) == record["current_matn_sha256"],
        f"Arabic source changed: {public_id}",
    )
    translation = connection.execute(
        "SELECT * FROM hadith_translations WHERE id=? AND hadith_id=?",
        (record["translation_id"], record["hadith_id"]),
    ).fetchone()
    require(translation is not None, f"Missing translation: {public_id}")
    segment = connection.execute(
        "SELECT * FROM translation_segments WHERE id=? AND hadith_id=?",
        (record["segment_id"], record["hadith_id"]),
    ).fetchone()
    require(segment is not None, f"Missing segment: {public_id}")
    item = connection.execute(
        "SELECT * FROM translation_job_items WHERE id=? AND hadith_id=?",
        (record["job_item_id"], record["hadith_id"]),
    ).fetchone()
    require(item is not None, f"Missing job item: {public_id}")
    return hadith, translation, segment, item


def assert_public_source_state(
    record: dict[str, Any],
    translation: sqlite3.Row,
    segment: sqlite3.Row,
    item: sqlite3.Row,
) -> None:
    public_id = record["public_id"]
    require(
        translation["status"] in PUBLIC_STATUSES
        and translation["risk_level"] == "green",
        f"Translation is not public/green: {public_id}",
    )
    require(
        raw_sha256(translation["matn_translation"]) == record["english_sha256"]
        and canonical_json_sha256(translation["provenance_json"])
        == record["provenance_sha256"],
        f"Translation text/provenance changed: {public_id}",
    )
    require(
        segment["translation_id"] == translation["id"]
        and segment["status"] in PUBLIC_STATUSES
        and segment["risk_level"] == "green"
        and raw_sha256(segment["translation_text"]) == record["english_sha256"],
        f"Segment changed: {public_id}",
    )
    require(
        item["segment_id"] == segment["id"]
        and item["status"] == "verified"
        and item["risk_level"] == "green",
        f"Job item changed: {public_id}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    require(file_sha256(manifest_path) == MANIFEST_SHA256, "Manifest checksum changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.get("records") or []
    require(len(records) == EXPECTED_COUNT, f"Expected seven records, got {len(records)}")
    require(
        len({record["public_id"] for record in records}) == EXPECTED_COUNT,
        "Duplicate public IDs",
    )

    connection = connect(args.db.resolve(), writable=args.apply)
    try:
        reviewed = []
        selected = []
        for record in records:
            rows = load_rows(connection, record)
            reviewed.append((record, *rows))
            if not target_state(rows[1], rows[2], rows[3]):
                selected.append((record, *rows))
        require(
            len(selected) in {0, EXPECTED_COUNT},
            f"Refusing partial state: selected {len(selected)} of {EXPECTED_COUNT}",
        )
        for record, _, translation, segment, item in selected:
            assert_public_source_state(record, translation, segment, item)

        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "manifest_sha256": MANIFEST_SHA256,
                    "selected": len(selected),
                    "assertion": "7-or-0",
                    "arabic_rows_changed": 0,
                    "english_rows_quarantined": len(selected),
                },
                indent=2,
            )
        )
        if not args.apply:
            return
        if not selected:
            print(f"already_quarantined={EXPECTED_COUNT}")
            return

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        connection.execute("BEGIN IMMEDIATE")
        for record, _, translation, segment, item in selected:
            audit = {
                "version": AUDIT_VERSION,
                "manifest": "scratch_audit/alkafi_additional_extent_blockers_20260716.json",
                "manifest_sha256": MANIFEST_SHA256,
                "reason": record["reason"],
                "source_url": record["source_url"],
                "source_record_sha256": record["source_record_sha256"],
                "quarantined_at": now,
            }
            provenance = dict(json_value(translation["provenance_json"]) or {})
            provenance.update(
                {
                    "publication_status": "rejected",
                    "reason": "confirmed_additional_extent_blocker",
                    "removed_english_sha256": record["english_sha256"],
                    "quarantined_previous_classification": provenance.get(
                        "translation_classification"
                    ),
                    "translation_classification": "quarantined_source_alignment_blocker",
                    "additional_extent_audit": audit,
                }
            )
            flags = add_flag(translation["risk_flags"], record["reason"])
            cursor = connection.execute(
                """
                UPDATE hadith_translations
                SET rendered_isnad_en=NULL, matn_translation=NULL,
                    full_translation=NULL, status='rejected', risk_level='red',
                    risk_flags=?, provenance_json=?,
                    qa_version=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (
                    json_dump(flags),
                    json_dump(provenance),
                    f"{translation['qa_version']}+{AUDIT_VERSION}",
                    translation["id"],
                    record["hadith_id"],
                ),
            )
            require(cursor.rowcount == 1, f"Translation update failed: {record['public_id']}")
            metadata = dict(json_value(segment["metadata_json"]) or {})
            metadata["additional_extent_audit"] = audit
            cursor = connection.execute(
                """
                UPDATE translation_segments
                SET translation_text=NULL, status='qa_failed', risk_level='red',
                    risk_flags=?, metadata_json=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (
                    json_dump(add_flag(segment["risk_flags"], record["reason"])),
                    json_dump(metadata),
                    segment["id"],
                    record["hadith_id"],
                ),
            )
            require(cursor.rowcount == 1, f"Segment update failed: {record['public_id']}")
            cursor = connection.execute(
                """
                UPDATE translation_job_items
                SET status='qa_failed', risk_level='red', updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (item["id"], record["hadith_id"]),
            )
            require(cursor.rowcount == 1, f"Job-item update failed: {record['public_id']}")

        for record in records:
            _, translation, segment, item = load_rows(connection, record)
            require(
                target_state(translation, segment, item),
                f"Post-quarantine state failed: {record['public_id']}",
            )
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "Foreign-key violations")
        connection.commit()
        print(f"committed={EXPECTED_COUNT}")
    except Exception:
        if args.apply:
            connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
