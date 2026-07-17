"""Quarantine English, then apply 32 source-pinned Al-Kafi extent repairs.

Dry-run is the default.  The apply path writes no English and will not mutate
Arabic until every affected translation is non-public and redacted.  It is
atomic and requires a consistent SQLite backup destination.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eshia_research.normalise import normalise_arabic_persian  # noqa: E402


DEFAULT_DB = ROOT / "eshia_research.db"
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_extent33_source_repair_manifest_20260716.json"
)
MANIFEST_SHA256 = "6186515b5d4e02e532f8ef9d278db2c92608fd71cadf88e8993ad6802a435cd6"
EXPECTED_COUNT = 33
EXPECTED_REPAIRS = 32
EXPECTED_PREQUARANTINED = 7
EXPECTED_PUBLIC = 26
CONFIRMATION = "APPLY-32-EXTENT-REPAIRS"
AUDIT_VERSION = "alkafi_extent33_source_repair_v1"
FLAG_CODE = "confirmed_source_extent_paratext_or_apparatus"
REVIEWER = "usul16-source-extent-repair"
SPLIT_VERSION = "alkafi_source_extent_v1"
PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
MUTATION_FIELDS = (
    "full_text_raw",
    "full_text_normalised",
    "isnad_raw",
    "isnad_normalised",
    "matn_raw",
    "matn_normalised",
    "volume_end",
    "page_end",
    "page_end_id",
    "extraction_confidence",
)


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


def json_value(value: str | Any | None) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
        source_geometry = source_connection.execute(
            "SELECT (SELECT page_count FROM pragma_page_count), "
            "(SELECT page_size FROM pragma_page_size)"
        ).fetchone()
        destination_geometry = destination_connection.execute(
            "SELECT (SELECT page_count FROM pragma_page_count), "
            "(SELECT page_size FROM pragma_page_size)"
        ).fetchone()
        require(tuple(source_geometry) == tuple(destination_geometry), "Backup geometry differs")
    finally:
        destination_connection.close()
        source_connection.close()


def add_flag(value: Any, detail: str, manifest_sha256: str) -> list[Any]:
    flags = list(json_value(value) or [])
    if not any(isinstance(flag, dict) and flag.get("code") == FLAG_CODE for flag in flags):
        flags.append(
            {
                "code": FLAG_CODE,
                "severity": "critical",
                "detail": detail,
                "audit_version": AUDIT_VERSION,
                "manifest_sha256": manifest_sha256,
            }
        )
    return flags


def hadith_row_fingerprint(row: sqlite3.Row) -> str:
    fields = (
        "id",
        "public_id",
        "sequence_in_book",
        "full_text_raw",
        "full_text_normalised",
        "isnad_raw",
        "isnad_normalised",
        "matn_raw",
        "matn_normalised",
        "volume_end",
        "page_end",
        "page_end_id",
        "extraction_confidence",
        "review_status",
    )
    return canonical_json_sha256({field: row[field] for field in fields})


def chain_fingerprint(connection: sqlite3.Connection, hadith_id: int) -> str:
    chains = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM chains WHERE hadith_id=? ORDER BY id", (hadith_id,)
        )
    ]
    chain_ids = [int(row["id"]) for row in chains]
    nodes: list[dict[str, Any]] = []
    if chain_ids:
        placeholders = ",".join("?" for _ in chain_ids)
        nodes = [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM chain_nodes WHERE chain_id IN ({placeholders}) ORDER BY id",
                tuple(chain_ids),
            )
        ]
    return canonical_json_sha256({"chains": chains, "nodes": nodes})


def target_present(entry: dict[str, Any], hadith: sqlite3.Row) -> bool:
    target = entry["target"]
    return all(hadith[field] == target[field] for field in MUTATION_FIELDS)


def validate_target(entry: dict[str, Any]) -> None:
    target = entry["target"]
    require(len(target["full_text_raw"]) == target["full_len"], "Target length changed")
    for field in (
        "full_text_raw",
        "full_text_normalised",
        "isnad_raw",
        "isnad_normalised",
        "matn_raw",
        "matn_normalised",
    ):
        require(
            sha256_text(target[field]) == target[f"{field}_sha256"],
            f"{entry['public_id']}: target {field} checksum changed",
        )
    require(
        target["full_text_normalised"] == normalise_arabic_persian(target["full_text_raw"])
        and target["matn_normalised"] == normalise_arabic_persian(target["matn_raw"]),
        f"{entry['public_id']}: target normalization changed",
    )
    if entry["bucket"] == "deterministic_repair":
        require(
            target["full_text_raw"].startswith((target["isnad_raw"] or "") + " ")
            and target["full_text_raw"][len(target["isnad_raw"] or "") + 1 :]
            == target["matn_raw"],
            f"{entry['public_id']}: target split is not lossless",
        )


def validate_source_pages(
    connection: sqlite3.Connection, entry: dict[str, Any]
) -> None:
    for spec in entry["source_pages"]:
        page = connection.execute(
            "SELECT * FROM pages WHERE id=?", (spec["id"],)
        ).fetchone()
        require(page is not None, f"{entry['public_id']}: source page missing")
        require(
            int(page["volume_number"]) == int(spec["volume"])
            and int(page["page_number"]) == int(spec["page"])
            and page["checksum"] == spec["checksum"]
            and sha256_text(page["text_raw"]) == spec["text_sha256"],
            f"{entry['public_id']}: source page changed",
        )


def translation_rows(
    connection: sqlite3.Connection, entry: dict[str, Any]
) -> tuple[sqlite3.Row, list[sqlite3.Row], list[sqlite3.Row]]:
    spec = entry["translation"]
    translation = connection.execute(
        "SELECT * FROM hadith_translations WHERE id=? AND hadith_id=?",
        (spec["translation_id"], entry["hadith_id"]),
    ).fetchone()
    require(translation is not None, f"{entry['public_id']}: translation missing")
    segments = list(
        connection.execute(
            "SELECT * FROM translation_segments WHERE hadith_id=? ORDER BY id",
            (entry["hadith_id"],),
        )
    )
    require(
        [int(row["id"]) for row in segments] == spec["segment_ids"],
        f"{entry['public_id']}: segment IDs changed",
    )
    jobs: list[sqlite3.Row] = []
    if segments:
        placeholders = ",".join("?" for _ in segments)
        jobs = list(
            connection.execute(
                f"SELECT * FROM translation_job_items WHERE segment_id IN ({placeholders}) ORDER BY id",
                tuple(int(row["id"]) for row in segments),
            )
        )
    require(
        [int(row["id"]) for row in jobs] == spec["job_item_ids"],
        f"{entry['public_id']}: job IDs changed",
    )
    return translation, segments, jobs


def is_public(translation: sqlite3.Row) -> bool:
    return bool(
        translation["status"] in PUBLIC_STATUSES
        or translation["risk_level"] == "green"
        or translation["rendered_isnad_en"]
        or translation["matn_translation"]
        or translation["full_translation"]
    )


def is_this_quarantine(translation: sqlite3.Row) -> bool:
    provenance = json_value(translation["provenance_json"]) or {}
    return bool(
        translation["status"] == "rejected"
        and translation["risk_level"] == "red"
        and translation["rendered_isnad_en"] is None
        and translation["matn_translation"] is None
        and translation["full_translation"] is None
        and (provenance.get("extent33_source_repair") or {}).get("manifest_sha256")
        == MANIFEST_SHA256
    )


def validate_external_sources(manifest: dict[str, Any]) -> None:
    for key in ("thaqalayn_static", "thaqalayn_api", "pre_pagebreak_backup"):
        spec = manifest["inputs"][key]
        raw = Path(os.path.expandvars(spec["path"]))
        path = raw if raw.is_absolute() else ROOT / raw
        require(path.is_file(), f"Missing pinned input: {path}")
        require(sha256_file(path) == spec["sha256"], f"Pinned input changed: {path}")
    static_path = Path(os.path.expandvars(manifest["inputs"]["thaqalayn_static"]["path"]))
    api_path = Path(os.path.expandvars(manifest["inputs"]["thaqalayn_api"]["path"]))
    static_by_id = {
        int(row["index"]): row
        for row in json.loads(static_path.read_text(encoding="utf-8"))
    }
    api = json.loads(api_path.read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        source = entry["sarwar_source"]
        if source["available"]:
            rows = [
                row
                for row in api[str(source["volume"])]
                if int(row.get("id") or -1) == int(source["remote_id"])
            ]
            require(len(rows) == 1, f"{entry['public_id']}: Sarwar record missing")
            require(
                rows[0].get("translator") == "Muhammad Sarwar"
                and canonical_json_sha256(rows[0]) == source["record_sha256"]
                and sha256_text(rows[0].get("englishText")) == source["english_sha256"],
                f"{entry['public_id']}: Sarwar record changed",
            )
            target_text = rows[0].get("englishText") or ""
            require(
                not any(
                    marker in target_text.casefold()
                    for marker in ("codex", "openai", "chatgpt", "hubeali")
                ),
                f"{entry['public_id']}: forbidden English source marker",
            )
        else:
            witness = entry["arabic_witness"]
            require(witness is not None, f"{entry['public_id']}: Arabic witness missing")
            record = static_by_id[int(witness["remote_id"])]
            require(
                canonical_json_sha256(record) == witness["record_sha256"],
                f"{entry['public_id']}: Arabic witness changed",
            )


def upsert_split_review(connection: sqlite3.Connection, entry: dict[str, Any]) -> None:
    target = entry["target"]
    connection.execute(
        """
        INSERT INTO hadith_split_reviews (
            hadith_id, approved_isnad_raw, approved_matn_raw, review_status,
            reviewer, notes, split_version, created_at, updated_at
        ) VALUES (?, ?, ?, 'approved', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(hadith_id) DO UPDATE SET
            approved_isnad_raw=excluded.approved_isnad_raw,
            approved_matn_raw=excluded.approved_matn_raw,
            review_status='approved', reviewer=excluded.reviewer,
            notes=excluded.notes, split_version=excluded.split_version,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            entry["hadith_id"],
            target["isnad_raw"],
            target["matn_raw"],
            REVIEWER,
            "Checksum-pinned removal of source paratext/editorial apparatus; English remains quarantined pending a separate exact-human-source gate.",
            SPLIT_VERSION,
        ),
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
    entries = manifest.get("entries") or []
    require(
        manifest.get("schema_version") == "alkafi_extent33_source_repair_v1"
        and len(entries) == EXPECTED_COUNT
        and len({entry["public_id"] for entry in entries}) == EXPECTED_COUNT,
        "Manifest shape changed",
    )
    require(
        sum(entry["bucket"] == "deterministic_repair" for entry in entries)
        == EXPECTED_REPAIRS,
        "Repair count changed",
    )
    validate_external_sources(manifest)
    for entry in entries:
        validate_target(entry)

    db_path = args.db.resolve()
    if args.apply:
        require(args.confirm == CONFIRMATION, f"--apply requires --confirm {CONFIRMATION}")
        require(args.backup_output is not None, "--apply requires --backup-output")
        backup_output = args.backup_output.resolve()
        require(backup_output != db_path, "Backup output equals live DB")
        require(not backup_output.exists(), f"Backup output exists: {backup_output}")
        online_backup(db_path, backup_output)

    connection = connect(db_path, writable=args.apply)
    try:
        public: list[tuple[dict[str, Any], sqlite3.Row, list[sqlite3.Row], list[sqlite3.Row]]] = []
        existing_other_quarantine = 0
        existing_this_quarantine = 0
        repairs_needed: list[tuple[dict[str, Any], sqlite3.Row]] = []
        repairs_done = 0
        chain_before: dict[str, str] = {}
        for entry in entries:
            hadith = connection.execute(
                "SELECT * FROM hadiths WHERE id=? AND public_id=?",
                (entry["hadith_id"], entry["public_id"]),
            ).fetchone()
            require(hadith is not None, f"{entry['public_id']}: hadith missing")
            validate_source_pages(connection, entry)
            already_target = target_present(entry, hadith)
            if not already_target:
                require(
                    hadith_row_fingerprint(hadith) == entry["current"]["row_fingerprint"],
                    f"{entry['public_id']}: Arabic state changed",
                )
            chain = chain_fingerprint(connection, int(entry["hadith_id"]))
            require(chain == entry["chain_fingerprint"], f"{entry['public_id']}: chain changed")
            chain_before[entry["public_id"]] = chain
            if entry["bucket"] == "deterministic_repair":
                if already_target:
                    repairs_done += 1
                else:
                    repairs_needed.append((entry, hadith))

            translation, segments, jobs = translation_rows(connection, entry)
            if is_public(translation):
                require(
                    translation["status"] == entry["translation"]["status"]
                    and translation["risk_level"] == entry["translation"]["risk_level"]
                    and canonical_json_sha256(json_value(translation["provenance_json"]) or {})
                    == entry["translation"]["provenance_sha256"]
                    and canonical_json_sha256([dict(row) for row in segments])
                    == entry["translation"]["segment_state_sha256"]
                    and canonical_json_sha256([dict(row) for row in jobs])
                    == entry["translation"]["job_state_sha256"],
                    f"{entry['public_id']}: public translation state changed",
                )
                live = translation["matn_translation"] or translation["full_translation"]
                require(
                    sha256_text(live) == entry["translation"]["live_english_sha256"],
                    f"{entry['public_id']}: public English changed",
                )
                public.append((entry, translation, segments, jobs))
            elif is_this_quarantine(translation):
                existing_this_quarantine += 1
            else:
                require(
                    translation["status"] == "rejected"
                    and translation["risk_level"] == "red"
                    and translation["rendered_isnad_en"] is None
                    and translation["matn_translation"] is None
                    and translation["full_translation"] is None,
                    f"{entry['public_id']}: unexpected non-public state",
                )
                existing_other_quarantine += 1

        initial = (
            len(public) == EXPECTED_PUBLIC
            and existing_other_quarantine == EXPECTED_PREQUARANTINED
            and existing_this_quarantine == 0
            and len(repairs_needed) == EXPECTED_REPAIRS
        )
        complete = (
            len(public) == 0
            and existing_other_quarantine == EXPECTED_PREQUARANTINED
            and existing_this_quarantine == EXPECTED_PUBLIC
            and repairs_done == EXPECTED_REPAIRS
        )
        require(initial or complete, "Refusing partial extent-33 repair state")
        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "manifest_sha256": MANIFEST_SHA256,
            "records": EXPECTED_COUNT,
            "public_english_to_quarantine": len(public),
            "already_quarantined": existing_other_quarantine + existing_this_quarantine,
            "arabic_repairs_needed": len(repairs_needed),
            "arabic_repairs_already_present": repairs_done,
            "english_replacements": 0,
            "hubeali_targets": 0,
            "codex_targets": 0,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not args.apply or complete:
            return

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        connection.execute("BEGIN IMMEDIATE")
        for entry, translation, segments, jobs in public:
            source = entry["sarwar_source"]
            audit = {
                "version": AUDIT_VERSION,
                "manifest": "scratch_audit/alkafi_extent33_source_repair_manifest_20260716.json",
                "manifest_sha256": MANIFEST_SHA256,
                "reason": entry["action"],
                "sarwar_republication_available": bool(source["available"]),
                "quarantined_at": now,
            }
            provenance = dict(json_value(translation["provenance_json"]) or {})
            live = translation["matn_translation"] or translation["full_translation"]
            provenance.update(
                {
                    "publication_status": "rejected",
                    "reason": FLAG_CODE,
                    "removed_english_sha256": sha256_text(live),
                    "translation_classification": "quarantined_source_extent_blocker",
                    "extent33_source_repair": audit,
                }
            )
            detail = "Arabic source paratext/editorial apparatus must be removed before exact human-source English can be aligned."
            cursor = connection.execute(
                """
                UPDATE hadith_translations
                SET rendered_isnad_en=NULL, matn_translation=NULL, full_translation=NULL,
                    status='rejected', risk_level='red', risk_flags=?, provenance_json=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND hadith_id=?
                """,
                (
                    json_dump(add_flag(translation["risk_flags"], detail, MANIFEST_SHA256)),
                    json_dump(provenance),
                    translation["id"],
                    entry["hadith_id"],
                ),
            )
            require(cursor.rowcount == 1, f"{entry['public_id']}: translation quarantine failed")
            for segment in segments:
                metadata = dict(json_value(segment["metadata_json"]) or {})
                metadata["extent33_source_repair"] = audit
                cursor = connection.execute(
                    """
                    UPDATE translation_segments
                    SET translation_text=NULL, status='qa_failed', risk_level='red',
                        risk_flags=?, metadata_json=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=? AND hadith_id=?
                    """,
                    (
                        json_dump(add_flag(segment["risk_flags"], detail, MANIFEST_SHA256)),
                        json_dump(metadata),
                        segment["id"],
                        entry["hadith_id"],
                    ),
                )
                require(cursor.rowcount == 1, f"{entry['public_id']}: segment quarantine failed")
            for job in jobs:
                cursor = connection.execute(
                    """
                    UPDATE translation_job_items
                    SET status='qa_failed', risk_level='red', updated_at=CURRENT_TIMESTAMP
                    WHERE id=? AND hadith_id=?
                    """,
                    (job["id"], entry["hadith_id"]),
                )
                require(cursor.rowcount == 1, f"{entry['public_id']}: job quarantine failed")

        for entry in entries:
            translation, _, _ = translation_rows(connection, entry)
            require(not is_public(translation), f"{entry['public_id']}: English is still public")

        assignments = ", ".join(f"{field}=?" for field in MUTATION_FIELDS)
        for entry, _ in repairs_needed:
            target = entry["target"]
            cursor = connection.execute(
                f"UPDATE hadiths SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=? AND public_id=?",
                (
                    *(target[field] for field in MUTATION_FIELDS),
                    entry["hadith_id"],
                    entry["public_id"],
                ),
            )
            require(cursor.rowcount == 1, f"{entry['public_id']}: Arabic update failed")
            upsert_split_review(connection, entry)

        for entry in entries:
            hadith = connection.execute(
                "SELECT * FROM hadiths WHERE id=?", (entry["hadith_id"],)
            ).fetchone()
            require(target_present(entry, hadith), f"{entry['public_id']}: target not present")
            require(
                chain_fingerprint(connection, int(entry["hadith_id"]))
                == chain_before[entry["public_id"]],
                f"{entry['public_id']}: chain changed during repair",
            )
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "Foreign-key violations")
        connection.commit()
        print(f"committed_repairs={EXPECTED_REPAIRS} quarantined_english={EXPECTED_PUBLIC}")
    except Exception:
        if args.apply:
            connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
