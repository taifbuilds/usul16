"""Apply three checksum-pinned Al-Kafi source-alignment cleanups.

Dry-run is the default.  This script never creates or changes English text:
two rows receive stronger multi-source identity provenance, and one row has an
eShia page-footnote divider removed from Arabic before linked source hashes are
refreshed.  All English evidence is attributed to Muhammad Sarwar.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.text import sha256_text, source_norm


MANIFEST_SCHEMA = "alkafi_final_source_outliers_v1"
MANIFEST_SHA256 = "b997822ddb38cfcbe8a2d1d1a88e176b1655654e069e53b49345b1ba2e093954"
CONFIRMATION = "APPLY-3-FINAL-SOURCE-OUTLIERS"
DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_final_source_outliers_manifest_20260716.json"
)
DEFAULT_DATABASE = REPO_ROOT / "eshia_research.db"
SEPARATOR = "______________________________"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def json_object(value: str | None, label: str) -> dict[str, Any]:
    require(bool(value), f"Missing JSON payload: {label}")
    parsed = json.loads(value or "{}")
    require(isinstance(parsed, dict), f"Expected JSON object: {label}")
    return parsed


def canonical_json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing manifest: {path}")
    require(file_sha256(path) == MANIFEST_SHA256, "Manifest checksum mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(payload.get("schema_version") == MANIFEST_SCHEMA, "Manifest schema mismatch")
    require(payload.get("counts", {}).get("records") == 3, "Expected exactly three records")
    require(len(payload.get("records") or []) == 3, "Expected exactly three manifest rows")
    require(payload.get("counts", {}).get("english_replacements") == 0, "English mutation is forbidden")
    require(payload.get("counts", {}).get("quarantine") == 0, "Unexpected quarantine action")
    return payload


def resolve_source_path(value: str) -> Path:
    expanded = Path(os.path.expandvars(value))
    return expanded if expanded.is_absolute() else REPO_ROOT / expanded


def load_and_verify_sources(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    loaded: dict[str, Any] = {}
    for label, evidence in manifest["source_snapshots"].items():
        path = resolve_source_path(evidence["path"])
        require(path.is_file(), f"Missing source snapshot {label}: {path}")
        require(path.stat().st_size == evidence["bytes"], f"Source size mismatch: {label}")
        require(file_sha256(path) == evidence["sha256"], f"Source checksum mismatch: {label}")
        loaded[label] = json.loads(path.read_text(encoding="utf-8"))

    api = loaded["thaqalayn_api"]
    static_rows = loaded["thaqalayn_static"]
    scan_rows = loaded["sarwar_scan_records"]["records"]
    require(isinstance(api, dict), "Invalid API snapshot")
    require(isinstance(static_rows, list), "Invalid static snapshot")
    require(isinstance(scan_rows, list), "Invalid scan snapshot")
    return api, static_rows, scan_rows


def verify_external_evidence(
    manifest: dict[str, Any],
    api: dict[str, Any],
    static_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
) -> None:
    for record in manifest["records"]:
        pid = record["public_id"]

        static_evidence = record.get("static_english_evidence") or record.get(
            "static_identity_evidence"
        )
        if static_evidence:
            row = next(
                (
                    item
                    for item in static_rows
                    if int(item.get("index") or 0) == static_evidence["index"]
                    and str(item.get("path")) == static_evidence["path"]
                ),
                None,
            )
            require(row is not None, f"Missing static evidence for {pid}")
            require(
                canonical_json_sha256(row) == static_evidence["record_sha256"],
                f"Static record checksum mismatch for {pid}",
            )
            require(
                exact_sha256(str(row.get("arabic_text") or ""))
                == static_evidence["arabic_exact_sha256"],
                f"Static Arabic checksum mismatch for {pid}",
            )
            require(
                exact_sha256(str(row.get("en_sarwar") or ""))
                == static_evidence["english_exact_sha256"],
                f"Static Sarwar English checksum mismatch for {pid}",
            )
            require(bool(row.get("en_sarwar")), f"Missing static Sarwar English for {pid}")

        api_evidence = record.get("api_coordinate_evidence") or record.get(
            "api_identity_evidence"
        )
        require(api_evidence is not None, f"Missing API evidence for {pid}")
        rows = api[str(api_evidence["volume"])]
        row = next((item for item in rows if int(item.get("id") or 0) == api_evidence["id"]), None)
        require(row is not None, f"Missing API record for {pid}")
        require(
            canonical_json_sha256(row) == api_evidence["record_sha256"],
            f"API record checksum mismatch for {pid}",
        )
        require(row.get("translator") == "Muhammad Sarwar", f"Non-Sarwar API source for {pid}")
        require(
            exact_sha256(str(row.get("arabicText") or ""))
            == api_evidence["arabic_exact_sha256"],
            f"API Arabic checksum mismatch for {pid}",
        )
        expected_api_english = api_evidence.get("english_exact_sha256") or api_evidence.get(
            "english_full_exact_sha256"
        )
        require(
            exact_sha256(str(row.get("englishText") or "")) == expected_api_english,
            f"API English checksum mismatch for {pid}",
        )

        scan_evidence = record["published_scan_evidence"]
        marker = scan_evidence["marker"]
        scan = next((item for item in scan_rows if item.get("marker") == marker), None)
        require(scan is not None, f"Missing published scan record for {pid}")
        require(
            canonical_json_sha256(scan) == scan_evidence["record_sha256"],
            f"Published scan record checksum mismatch for {pid}",
        )
        require(
            exact_sha256(str(scan.get("english") or ""))
            == scan_evidence["english_exact_sha256"],
            f"Published scan English checksum mismatch for {pid}",
        )
        require(
            scan.get("source_sha256") == scan_evidence["source_pdf_sha256"],
            f"Published PDF checksum mismatch for {pid}",
        )


def fetch_one(connection: sqlite3.Connection, query: str, params: tuple[Any, ...], label: str) -> sqlite3.Row:
    row = connection.execute(query, params).fetchone()
    require(row is not None, f"Missing database row: {label}")
    return row


def current_bundle(connection: sqlite3.Connection, record: dict[str, Any]) -> tuple[sqlite3.Row, sqlite3.Row, sqlite3.Row, sqlite3.Row]:
    pre = record["database_preconditions"]
    hadith = fetch_one(
        connection,
        "SELECT * FROM hadiths WHERE public_id = ?",
        (record["public_id"],),
        record["public_id"],
    )
    translation = fetch_one(
        connection,
        "SELECT * FROM hadith_translations WHERE id = ? AND hadith_id = ?",
        (pre["translation_id"], pre["hadith_id"]),
        f"{record['public_id']} translation",
    )
    segment = fetch_one(
        connection,
        "SELECT * FROM translation_segments WHERE id = ? AND hadith_id = ? AND translation_id = ?",
        (pre["segment_id"], pre["hadith_id"], pre["translation_id"]),
        f"{record['public_id']} segment",
    )
    job_item = fetch_one(
        connection,
        "SELECT * FROM translation_job_items WHERE id = ? AND hadith_id = ? AND segment_id = ?",
        (pre["job_item_id"], pre["hadith_id"], pre["segment_id"]),
        f"{record['public_id']} job item",
    )
    return hadith, translation, segment, job_item


def is_applied(translation: sqlite3.Row) -> bool:
    provenance = json_object(translation["provenance_json"], "translation provenance")
    audit = provenance.get("source_alignment_audit")
    return isinstance(audit, dict) and audit.get("manifest_sha256") == MANIFEST_SHA256


def verify_database_preconditions(
    record: dict[str, Any],
    hadith: sqlite3.Row,
    translation: sqlite3.Row,
    segment: sqlite3.Row,
    job_item: sqlite3.Row,
) -> None:
    pre = record["database_preconditions"]
    pid = record["public_id"]
    for field in ("hadith_id", "sequence_in_book", "printed_number"):
        column = "id" if field == "hadith_id" else field
        require(hadith[column] == pre[field], f"{pid}: hadith {field} changed")
    for field in ("provider", "model", "status", "risk_level"):
        require(translation[field] == pre[field], f"{pid}: translation {field} changed")
    require(sha256_text(hadith["full_text_raw"]) == pre["source_full_sha256"], f"{pid}: full Arabic changed")
    require(sha256_text(hadith["isnad_raw"]) == pre["source_isnad_sha256"], f"{pid}: isnad changed")
    require(sha256_text(hadith["matn_raw"]) == pre["source_matn_sha256"], f"{pid}: matn changed")
    require(translation["source_full_sha256"] == pre["source_full_sha256"], f"{pid}: translation full hash changed")
    require(translation["source_isnad_sha256"] == pre["source_isnad_sha256"], f"{pid}: translation isnad hash changed")
    require(translation["source_matn_sha256"] == pre["source_matn_sha256"], f"{pid}: translation matn hash changed")
    require(exact_sha256(translation["matn_translation"] or "") == pre["english_exact_sha256"], f"{pid}: English changed")
    require(exact_sha256(translation["provenance_json"] or "") == pre["provenance_exact_sha256"], f"{pid}: provenance changed")
    require(exact_sha256(segment["metadata_json"] or "") == pre["segment_metadata_exact_sha256"], f"{pid}: segment metadata changed")
    require(segment["source_sha256"] == pre["source_matn_sha256"], f"{pid}: segment source hash changed")
    require(job_item["source_sha256"] == pre["source_matn_sha256"], f"{pid}: job source hash changed")
    require(translation["rendered_isnad_en"] is None or pid == "alkafi-8844", f"{pid}: unexpected English layout")
    require(translation["full_translation"] is None, f"{pid}: unexpected full English payload")


def audit_payload(record: dict[str, Any]) -> dict[str, Any]:
    pid = record["public_id"]
    api_evidence = record.get("api_coordinate_evidence") or record.get("api_identity_evidence")
    static_evidence = record.get("static_english_evidence") or record.get(
        "static_identity_evidence"
    )
    scan_evidence = record["published_scan_evidence"]
    return {
        "schema_version": MANIFEST_SCHEMA,
        "manifest_sha256": MANIFEST_SHA256,
        "action": record["action"],
        "public_id": pid,
        "english_mutated": False,
        "translator": "Muhammad Sarwar",
        "identity_evidence": {
            "eshia": record["eshia_evidence"],
            "thaqalayn_api": {
                "volume": api_evidence["volume"],
                "id": api_evidence["id"],
                "record_sha256": api_evidence["record_sha256"],
                "arabic_exact_sha256": api_evidence["arabic_exact_sha256"],
            },
            "thaqalayn_static": {
                "index": static_evidence["index"],
                "record_sha256": static_evidence["record_sha256"],
                "english_exact_sha256": static_evidence["english_exact_sha256"],
                "arabic_extent": static_evidence.get("arabic_extent", "complete report"),
            },
            "published_sarwar_scan": {
                "marker": scan_evidence["marker"],
                "pdf_page": scan_evidence["pdf_page"],
                "record_sha256": scan_evidence["record_sha256"],
                "source_pdf_sha256": scan_evidence["source_pdf_sha256"],
                "source_url": scan_evidence["source_url"],
            },
        },
    }


def apply_provenance_repin(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    translation: sqlite3.Row,
    segment: sqlite3.Row,
) -> None:
    provenance = json_object(translation["provenance_json"], "translation provenance")
    audit = audit_payload(record)
    provenance["translator"] = "Muhammad Sarwar"
    provenance["translation_classification"] = "external_source_normalized"
    provenance["translation_method"] = "verbatim external human-source import"
    provenance["source_alignment_audit"] = audit

    metadata = json_object(segment["metadata_json"], "segment metadata")
    metadata["provider"] = translation["provider"]
    metadata["translator"] = "Muhammad Sarwar"
    metadata["provenance"] = provenance
    metadata["source_alignment_audit"] = audit

    qa_version = translation["qa_version"] or "translation_qa_v1"
    if "+source_identity_v1" not in qa_version:
        qa_version += "+source_identity_v1"
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    connection.execute(
        "UPDATE hadith_translations SET provenance_json = ?, qa_version = ?, updated_at = ? WHERE id = ?",
        (canonical_json_text(provenance), qa_version, now, translation["id"]),
    )
    connection.execute(
        "UPDATE translation_segments SET metadata_json = ?, updated_at = ? WHERE id = ?",
        (canonical_json_text(metadata), now, segment["id"]),
    )


def apply_separator_cleanup(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    hadith: sqlite3.Row,
    translation: sqlite3.Row,
    segment: sqlite3.Row,
    job_item: sqlite3.Row,
) -> None:
    require(hadith["full_text_raw"].count(SEPARATOR) == 1, "alkafi-8844: expected one full-text separator")
    require(hadith["matn_raw"].count(SEPARATOR) == 1, "alkafi-8844: expected one matn separator")
    target_full = hadith["full_text_raw"].replace(f"\n{SEPARATOR}\n", "\n")
    target_matn = hadith["matn_raw"].replace(f" {SEPARATOR} ", " ")
    require(SEPARATOR not in target_full and SEPARATOR not in target_matn, "Separator removal failed")
    target_full_norm = normalise_arabic_persian(target_full)
    target_matn_norm = normalise_arabic_persian(target_matn)
    target = record["target_hashes"]
    require(exact_sha256(target_full) == target["full_text_raw_exact_sha256"], "Target full exact hash mismatch")
    require(exact_sha256(target_matn) == target["matn_raw_exact_sha256"], "Target matn exact hash mismatch")
    require(sha256_text(target_full) == target["source_full_sha256"], "Target full source hash mismatch")
    require(sha256_text(target_matn) == target["source_matn_sha256"], "Target matn source hash mismatch")
    require(exact_sha256(target_full_norm) == target["full_text_normalised_exact_sha256"], "Target full normalized hash mismatch")
    require(exact_sha256(target_matn_norm) == target["matn_normalised_exact_sha256"], "Target matn normalized hash mismatch")

    provenance = json_object(translation["provenance_json"], "translation provenance")
    audit = audit_payload(record)
    provenance["translator"] = "Muhammad Sarwar"
    provenance["translation_classification"] = "external_source_normalized"
    provenance["translation_method"] = "verbatim external human-source import"
    provenance["source_alignment_audit"] = audit

    metadata = json_object(segment["metadata_json"], "segment metadata")
    metadata["source_norm"] = source_norm(target_matn)
    require(
        exact_sha256(metadata["source_norm"])
        == target["segment_source_norm_exact_sha256"],
        "Target segment normalization mismatch",
    )
    metadata["provider"] = translation["provider"]
    metadata["translator"] = "Muhammad Sarwar"
    metadata["provenance"] = provenance
    metadata["source_alignment_audit"] = audit

    qa_version = translation["qa_version"] or "translation_qa_v1"
    if "+source_structure_v1" not in qa_version:
        qa_version += "+source_structure_v1"
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    connection.execute(
        """UPDATE hadiths
           SET full_text_raw = ?, full_text_normalised = ?, matn_raw = ?,
               matn_normalised = ?, updated_at = ? WHERE id = ?""",
        (target_full, target_full_norm, target_matn, target_matn_norm, now, hadith["id"]),
    )
    connection.execute(
        """UPDATE hadith_translations
           SET source_full_sha256 = ?, source_isnad_sha256 = ?, source_matn_sha256 = ?,
               provenance_json = ?, qa_version = ?, updated_at = ? WHERE id = ?""",
        (
            target["source_full_sha256"],
            target["source_isnad_sha256"],
            target["source_matn_sha256"],
            canonical_json_text(provenance),
            qa_version,
            now,
            translation["id"],
        ),
    )
    connection.execute(
        """UPDATE translation_segments
           SET source_text = ?, source_sha256 = ?, metadata_json = ?, updated_at = ? WHERE id = ?""",
        (
            target_matn,
            target["source_matn_sha256"],
            canonical_json_text(metadata),
            now,
            segment["id"],
        ),
    )
    connection.execute(
        "UPDATE translation_job_items SET source_sha256 = ?, updated_at = ? WHERE id = ?",
        (target["source_matn_sha256"], now, job_item["id"]),
    )


def verify_postconditions(connection: sqlite3.Connection, manifest: dict[str, Any]) -> None:
    for record in manifest["records"]:
        hadith, translation, segment, job_item = current_bundle(connection, record)
        pid = record["public_id"]
        pre = record["database_preconditions"]
        require(exact_sha256(translation["matn_translation"] or "") == pre["english_exact_sha256"], f"{pid}: English mutated")
        require(translation["status"] == "published" and translation["risk_level"] == "green", f"{pid}: publication state changed")
        require(translation["model"] == "muhammad-sarwar", f"{pid}: translator model changed")
        require(is_applied(translation), f"{pid}: audit provenance missing")
        if pid == "alkafi-8844":
            target = record["target_hashes"]
            require(SEPARATOR not in hadith["full_text_raw"] and SEPARATOR not in hadith["matn_raw"], "alkafi-8844: separator remains")
            require(translation["source_full_sha256"] == target["source_full_sha256"], "alkafi-8844: stale full hash")
            require(translation["source_matn_sha256"] == target["source_matn_sha256"], "alkafi-8844: stale matn hash")
            require(segment["source_sha256"] == target["source_matn_sha256"], "alkafi-8844: stale segment hash")
            require(job_item["source_sha256"] == target["source_matn_sha256"], "alkafi-8844: stale job hash")


def run(database: Path, manifest_path: Path, *, apply: bool) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    api, static_rows, scan_rows = load_and_verify_sources(manifest)
    verify_external_evidence(manifest, api, static_rows, scan_rows)
    require(database.is_file(), f"Missing database: {database}")

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    changed: list[str] = []
    already_applied: list[str] = []
    try:
        connection.execute("BEGIN IMMEDIATE")
        for record in manifest["records"]:
            hadith, translation, segment, job_item = current_bundle(connection, record)
            if is_applied(translation):
                already_applied.append(record["public_id"])
                continue
            verify_database_preconditions(record, hadith, translation, segment, job_item)
            if record["action"] == "repin_multi_source_identity_without_text_change":
                apply_provenance_repin(connection, record, translation, segment)
            elif record["action"] == "remove_page_footnote_separator_and_rehash":
                apply_separator_cleanup(
                    connection,
                    record,
                    hadith,
                    translation,
                    segment,
                    job_item,
                )
            else:
                raise RuntimeError(f"Unexpected action: {record['action']}")
            changed.append(record["public_id"])

        verify_postconditions(connection, manifest)
        # This repair touches only three known FK-bearing tables.  Keep its
        # atomic dry-run bounded; the release audit performs the separate,
        # database-wide foreign-key check across the 2.3 GB corpus.
        foreign_key_errors: list[sqlite3.Row] = []
        for table in (
            "hadith_translations",
            "translation_segments",
            "translation_job_items",
        ):
            foreign_key_errors.extend(
                connection.execute(f"PRAGMA foreign_key_check({table})").fetchall()
            )
        require(not foreign_key_errors, f"Foreign-key errors: {foreign_key_errors[:3]}")
        if apply:
            connection.commit()
        else:
            connection.rollback()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "mode": "apply" if apply else "dry-run",
        "manifest_sha256": MANIFEST_SHA256,
        "changed": changed,
        "already_applied": already_applied,
        "english_replacements": 0,
        "quarantined": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.apply:
        require(args.confirm == CONFIRMATION, f"Apply requires --confirm {CONFIRMATION}")
    result = run(args.database.resolve(), args.manifest.resolve(), apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
