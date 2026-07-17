"""Republish 30 repaired Al-Kafi rows from exact Muhammad Sarwar records.

Dry-run is the default.  Apply is refused until all 32 structural targets are
present and all 30 selected English rows are quarantined.  The three rows for
which the pinned snapshots expose only HubeAli remain quarantined.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "eshia_research.db"
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_extent33_sarwar_republication_manifest_20260716.json"
)
MANIFEST_SHA256 = "f477fdc65689484b83e00e32b1da6b8fd18333307b461f6c1780b0e57fa1f3d8"
STRUCTURAL_SHA256 = "6186515b5d4e02e532f8ef9d278db2c92608fd71cadf88e8993ad6802a435cd6"
API_SHA256 = "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
EXPECTED_COUNT = 30
EXPECTED_WITHHELD = 3
CONFIRMATION = "PUBLISH-30-EXACT-SARWAR"
GATE_VERSION = "alkafi_extent33_exact_sarwar_republication_v1"
PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def json_value(value: str | Any | None) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def connect(path: Path, *, writable: bool) -> sqlite3.Connection:
    if writable:
        connection = sqlite3.connect(str(path))
    else:
        connection = sqlite3.connect(
            f"file:{path.resolve().as_posix()}?mode=ro", uri=True
        )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def online_backup(source: Path, destination: Path) -> None:
    source_connection = connect(source, writable=False)
    destination_connection = sqlite3.connect(str(destination))
    try:
        source_connection.backup(destination_connection)
        result = destination_connection.execute("PRAGMA integrity_check").fetchone()
        require(result is not None and result[0] == "ok", "Backup integrity check failed")
    finally:
        destination_connection.close()
        source_connection.close()


def is_quarantined(translation: sqlite3.Row) -> bool:
    return bool(
        translation["status"] == "rejected"
        and translation["risk_level"] == "red"
        and translation["rendered_isnad_en"] is None
        and translation["matn_translation"] is None
        and translation["full_translation"] is None
    )


def target_translation_state(translation: sqlite3.Row, record: dict[str, Any]) -> bool:
    provenance = json_value(translation["provenance_json"]) or {}
    source = record["target_source"]
    arabic = record["target_arabic"]
    return bool(
        translation["status"] == "published"
        and translation["risk_level"] == "green"
        and translation["provider"] == "thaqalayn-api"
        and translation["model"] == "muhammad-sarwar"
        and translation["rendered_isnad_en"] is None
        and translation["full_translation"] is None
        and sha256_text(translation["matn_translation"]) == source["target_english_sha256"]
        and translation["source_full_sha256"] == arabic["full_sha256"]
        and translation["source_isnad_sha256"] == arabic["isnad_sha256"]
        and translation["source_matn_sha256"] == arabic["matn_sha256"]
        and (provenance.get("extent33_sarwar_republication") or {}).get("manifest_sha256")
        == MANIFEST_SHA256
    )


def load_translation_bundle(
    connection: sqlite3.Connection, record: dict[str, Any]
) -> tuple[sqlite3.Row, list[sqlite3.Row], list[sqlite3.Row]]:
    translation = connection.execute(
        "SELECT * FROM hadith_translations WHERE id=? AND hadith_id=?",
        (record["translation_id"], record["hadith_id"]),
    ).fetchone()
    require(translation is not None, f"{record['public_id']}: translation missing")
    segments = list(
        connection.execute(
            "SELECT * FROM translation_segments WHERE hadith_id=? ORDER BY id",
            (record["hadith_id"],),
        )
    )
    require(
        [int(row["id"]) for row in segments] == record["segment_ids"] and len(segments) == 1,
        f"{record['public_id']}: segment set changed",
    )
    jobs = list(
        connection.execute(
            "SELECT * FROM translation_job_items WHERE segment_id=? ORDER BY id",
            (segments[0]["id"],),
        )
    )
    require(
        [int(row["id"]) for row in jobs] == record["job_item_ids"] and len(jobs) == 1,
        f"{record['public_id']}: job set changed",
    )
    return translation, segments, jobs


def target_segment_state(segment: sqlite3.Row, record: dict[str, Any]) -> bool:
    metadata = json_value(segment["metadata_json"]) or {}
    return bool(
        segment["status"] == "published"
        and segment["risk_level"] == "green"
        and segment["source_sha256"] == record["target_arabic"]["matn_sha256"]
        and sha256_text(segment["translation_text"])
        == record["target_source"]["target_english_sha256"]
        and (metadata.get("extent33_sarwar_republication") or {}).get("manifest_sha256")
        == MANIFEST_SHA256
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--backup-output", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    require(sha256_file(manifest_path) == MANIFEST_SHA256, "Manifest checksum changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.get("records") or []
    withheld = manifest.get("withheld") or []
    require(
        manifest.get("schema_version") == "alkafi_extent33_sarwar_republication_v1"
        and len(records) == EXPECTED_COUNT
        and len(withheld) == EXPECTED_WITHHELD,
        "Manifest shape changed",
    )
    structural_path = manifest_path.with_name(manifest["inputs"]["structural_manifest"]["path"])
    require(
        sha256_file(structural_path) == STRUCTURAL_SHA256
        == manifest["inputs"]["structural_manifest"]["sha256"],
        "Structural manifest changed",
    )
    structural = json.loads(structural_path.read_text(encoding="utf-8"))
    structural_by_id = {entry["public_id"]: entry for entry in structural["entries"]}
    api_path = Path(os.path.expandvars(manifest["inputs"]["thaqalayn_api"]["path"]))
    require(
        sha256_file(api_path) == API_SHA256 == manifest["inputs"]["thaqalayn_api"]["sha256"],
        "API snapshot changed",
    )
    api = json.loads(api_path.read_text(encoding="utf-8"))
    for record in records:
        source = record["target_source"]
        rows = [
            row
            for row in api[str(source["volume"])]
            if int(row.get("id") or -1) == int(source["remote_id"])
        ]
        require(
            len(rows) == 1
            and rows[0].get("translator") == "Muhammad Sarwar"
            and canonical_json_sha256(rows[0]) == source["record_sha256"]
            and sha256_text(record["target_english"]) == source["target_english_sha256"],
            f"{record['public_id']}: target source changed",
        )
        require(
            not any(
                marker in record["target_english"].casefold()
                for marker in ("codex", "openai", "chatgpt", "hubeali")
            ),
            f"{record['public_id']}: forbidden target marker",
        )

    db_path = args.db.resolve()
    if args.apply:
        require(args.confirm == CONFIRMATION, f"--apply requires --confirm {CONFIRMATION}")
        require(args.backup_output is not None, "--apply requires --backup-output")
        backup_output = args.backup_output.resolve()
        require(not backup_output.exists(), f"Backup output exists: {backup_output}")
        require(backup_output != db_path, "Backup output equals live DB")
        online_backup(db_path, backup_output)

    connection = connect(db_path, writable=args.apply)
    try:
        waiting_arabic = 0
        waiting_quarantine = 0
        selected: list[tuple[dict[str, Any], sqlite3.Row, sqlite3.Row, sqlite3.Row]] = []
        published = 0
        for record in records:
            structural_entry = structural_by_id[record["public_id"]]
            hadith = connection.execute(
                "SELECT * FROM hadiths WHERE id=? AND public_id=?",
                (record["hadith_id"], record["public_id"]),
            ).fetchone()
            require(hadith is not None, f"{record['public_id']}: hadith missing")
            target = structural_entry["target"]
            arabic_ready = bool(
                sha256_text(hadith["full_text_raw"]) == record["target_arabic"]["full_sha256"]
                and sha256_text(hadith["isnad_raw"]) == record["target_arabic"]["isnad_sha256"]
                and sha256_text(hadith["matn_raw"]) == record["target_arabic"]["matn_sha256"]
                and hadith["page_end"] == target["page_end"]
                and hadith["page_end_id"] == target["page_end_id"]
            )
            if not arabic_ready:
                require(
                    sha256_text(hadith["full_text_raw"])
                    == structural_entry["current"]["full_sha256"],
                    f"{record['public_id']}: Arabic is neither pre-repair nor target",
                )
                waiting_arabic += 1

            translation, segments, jobs = load_translation_bundle(connection, record)
            if target_translation_state(translation, record):
                require(
                    target_segment_state(segments[0], record)
                    and jobs[0]["status"] == "verified"
                    and jobs[0]["risk_level"] == "green",
                    f"{record['public_id']}: partial published state",
                )
                published += 1
            elif is_quarantined(translation):
                require(
                    segments[0]["translation_text"] is None
                    and segments[0]["status"] == "qa_failed"
                    and segments[0]["risk_level"] == "red",
                    f"{record['public_id']}: quarantine segment differs",
                )
                if arabic_ready:
                    selected.append((record, translation, segments[0], jobs[0]))
            else:
                require(
                    translation["status"] in PUBLIC_STATUSES
                    and translation["risk_level"] == "green",
                    f"{record['public_id']}: unexpected translation state",
                )
                waiting_quarantine += 1

        require(
            (published == 0 or published == EXPECTED_COUNT)
            and not (published and (waiting_arabic or waiting_quarantine or selected)),
            "Refusing partial republication state",
        )
        print(
            json.dumps(
                {
                    "mode": "APPLY" if args.apply else "DRY-RUN",
                    "manifest_sha256": MANIFEST_SHA256,
                    "source_targets_verified": EXPECTED_COUNT,
                    "waiting_for_arabic_repairs": waiting_arabic,
                    "waiting_for_quarantine": waiting_quarantine,
                    "ready_to_publish": len(selected),
                    "already_published": published,
                    "withheld_no_sarwar": EXPECTED_WITHHELD,
                    "codex_targets": 0,
                    "hubeali_targets": 0,
                },
                indent=2,
            )
        )
        if not args.apply or published == EXPECTED_COUNT:
            return
        require(
            len(selected) == EXPECTED_COUNT
            and waiting_arabic == 0
            and waiting_quarantine == 0,
            "Apply is blocked until structural repair and quarantine complete",
        )

        connection.execute("BEGIN IMMEDIATE")
        for record, translation, segment, job in selected:
            source = record["target_source"]
            arabic = record["target_arabic"]
            gate = {
                "version": GATE_VERSION,
                "manifest": "scratch_audit/alkafi_extent33_sarwar_republication_manifest_20260716.json",
                "manifest_sha256": MANIFEST_SHA256,
                "structural_manifest_sha256": STRUCTURAL_SHA256,
                "source_record_sha256": source["record_sha256"],
                "source_english_sha256": source["target_english_sha256"],
                "bounded_prefix": source["bounded_prefix"],
            }
            provenance = {
                "source": "Thaqalayn API checksum-pinned human edition",
                "source_url": source["url"],
                "remote_id": source["remote_id"],
                "volume": source["volume"],
                "translator": "Muhammad Sarwar",
                "translator_attribution": "upstream-metadata",
                "source_snapshot_sha256": source["snapshot_sha256"],
                "source_record_sha256": source["record_sha256"],
                "source_english_sha256": source["target_english_sha256"],
                "source_plaintext_english_sha256": source["plaintext_english_sha256"],
                "translation_classification": "external_source_normalized",
                "publication_status": "published",
                "extent33_sarwar_republication": gate,
            }
            info_flag = [
                {
                    "code": "exact_human_source_republication",
                    "severity": "info",
                    "detail": "Exact Muhammad Sarwar text aligned after checksum-pinned Arabic extent repair.",
                    "manifest_sha256": MANIFEST_SHA256,
                }
            ]
            cursor = connection.execute(
                """
                UPDATE hadith_translations
                SET source_full_sha256=?, source_isnad_sha256=?, source_matn_sha256=?,
                    rendered_isnad_en=NULL, matn_translation=?, full_translation=NULL,
                    status='published', risk_level='green', risk_flags=?,
                    provider='thaqalayn-api', model='muhammad-sarwar',
                    provenance_json=?, qa_version=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (
                    arabic["full_sha256"],
                    arabic["isnad_sha256"],
                    arabic["matn_sha256"],
                    record["target_english"],
                    json_dump(info_flag),
                    json_dump(provenance),
                    GATE_VERSION,
                    translation["id"],
                    record["hadith_id"],
                ),
            )
            require(cursor.rowcount == 1, f"{record['public_id']}: translation publish failed")
            metadata = {
                "source": "Thaqalayn API checksum-pinned human edition",
                "source_url": source["url"],
                "translator": "Muhammad Sarwar",
                "extent33_sarwar_republication": gate,
            }
            cursor = connection.execute(
                """
                UPDATE translation_segments
                SET source_text=?, source_sha256=?, translation_text=?,
                    status='published', risk_level='green', risk_flags=?,
                    metadata_json=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (
                    structural_by_id[record["public_id"]]["target"]["matn_raw"],
                    arabic["matn_sha256"],
                    record["target_english"],
                    json_dump(info_flag),
                    json_dump(metadata),
                    segment["id"],
                    record["hadith_id"],
                ),
            )
            require(cursor.rowcount == 1, f"{record['public_id']}: segment publish failed")
            cursor = connection.execute(
                """
                UPDATE translation_job_items
                SET status='verified', risk_level='green', updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (job["id"], record["hadith_id"]),
            )
            require(cursor.rowcount == 1, f"{record['public_id']}: job publish failed")

        for record in records:
            translation, segments, jobs = load_translation_bundle(connection, record)
            require(
                target_translation_state(translation, record)
                and target_segment_state(segments[0], record)
                and jobs[0]["status"] == "verified"
                and jobs[0]["risk_level"] == "green",
                f"{record['public_id']}: post-publication gate failed",
            )
        for withheld_record in withheld:
            translation = connection.execute(
                "SELECT * FROM hadith_translations WHERE hadith_id=?",
                (withheld_record["hadith_id"],),
            ).fetchone()
            require(is_quarantined(translation), f"{withheld_record['public_id']}: withheld row became public")
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "Foreign-key violations")
        connection.commit()
        print(f"published_exact_sarwar={EXPECTED_COUNT} withheld={EXPECTED_WITHHELD}")
    except Exception:
        if args.apply:
            connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
