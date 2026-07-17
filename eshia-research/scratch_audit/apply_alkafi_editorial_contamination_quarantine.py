"""Fail-closed quarantine applier for the frozen 27-row Al-Kafi packet.

The default and ``--dry-run`` modes open SQLite read-only.  ``--apply`` is an
explicit opt-in and performs one atomic 27-or-0 transition.  The applier never
updates ``hadiths`` (or any Arabic-bearing column): it only removes public
English from the current translation and fails the linked public/green segment
and verified/green job-item states.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "eshia_research.db"
DEFAULT_MANIFEST = (
    ROOT
    / "scratch_audit"
    / "alkafi_public_editorial_contamination_quarantine_manifest_20260716.json"
)
SOURCE_AUDIT = ROOT / "scratch_audit" / "alkafi_public_extent_blockers_20260716.json"

MANIFEST_SHA256 = "f7c7e1e7260feb492e66d757c0bafeda1c3a8af62b15a7cce987ab3f8c274774"
MANIFEST_PAYLOAD_SHA256 = "e072fbaff134fe4a89c98db1e57704ff27814b5fe56b36bb9ca3c2cf68ff980a"
SOURCE_AUDIT_SHA256 = "546f7f870f9da8bd269c7bf7b5903f1008f62058e0d5da0b2404781b5b044622"
SOURCE_AUDIT_PAYLOAD_SHA256 = "ee8669fefcb7fbb41d935b603d82624b9860efe6f516f10b8d7715aefc092730"

EXPECTED_IDS = (
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
)
EXPECTED_EXCLUDED_IDS = (
    "alkafi-211",
    "alkafi-426",
    "alkafi-934",
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
    "alkafi-12112",
    "alkafi-12933",
    "alkafi-13279",
    "alkafi-13592",
    "alkafi-14040",
    "alkafi-14529",
    "alkafi-14607",
    "alkafi-14751",
)

EXPECTED_COUNT = 27
EXPECTED_PUBLIC_SEGMENTS = 27
EXPECTED_VERIFIED_ITEMS = 28
BOOK_ID = 1178
LANGUAGE = "en"
TRANSLATION_VERSION = "matn_en_v1"
AUDIT_VERSION = "alkafi_editorial_contamination_quarantine_v1"
AUDIT_KEY = "editorial_extent_contamination_audit"
FLAG_CODE = "confirmed_editorial_extent_contamination"
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
OVERWRITTEN_PROVENANCE_KEYS = (
    "publication_status",
    "reason",
    "translation_classification",
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


def clean_ws(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256_text(value: str | None) -> str:
    return hashlib.sha256(clean_ws(value).encode("utf-8")).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def parse_json(value: Any, *, kind: type, label: str) -> Any:
    if isinstance(value, kind):
        return value
    require(value is not None, f"Missing JSON: {label}")
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid JSON in {label}: {exc}") from exc
    require(isinstance(parsed, kind), f"Wrong JSON type in {label}")
    return parsed


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def source_pins(provenance: Any) -> dict[str, Any]:
    """Reproduce the source-pin extraction used by the frozen audit."""

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


def validate_embedded_payload(document: dict[str, Any], expected: str, label: str) -> None:
    stated = document.get("payload_sha256")
    require(stated == expected, f"{label} payload pin changed")
    payload = dict(document)
    payload.pop("payload_sha256", None)
    require(canonical_sha256(payload) == expected, f"{label} payload checksum failed")


def validate_manifest(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing manifest: {path}")
    require(file_sha256(path) == MANIFEST_SHA256, "27-row manifest checksum changed")
    manifest = parse_json(path.read_text(encoding="utf-8"), kind=dict, label="manifest")
    validate_embedded_payload(manifest, MANIFEST_PAYLOAD_SHA256, "manifest")
    require(
        manifest.get("schema_version") == AUDIT_VERSION,
        "Manifest schema version changed",
    )
    require(manifest.get("counts", {}).get("records") == EXPECTED_COUNT, "Bad record count")
    require(
        manifest.get("counts", {}).get("excluded_structural_records")
        == len(EXPECTED_EXCLUDED_IDS),
        "Bad structural exclusion count",
    )
    require(
        manifest.get("publication_action", {}).get("translation")
        == {"status": "rejected", "risk_level": "red"},
        "Translation action changed",
    )
    require(
        manifest.get("publication_action", {}).get("segments")
        == {"status": "qa_failed", "risk_level": "red"},
        "Segment action changed",
    )
    require(
        manifest.get("publication_action", {}).get("job_items")
        == {"status": "qa_failed", "risk_level": "red"},
        "Job-item action changed",
    )
    require(
        manifest.get("publication_action", {}).get("required_flag")
        == {"code": FLAG_CODE, "severity": "critical"},
        "Required flag changed",
    )

    boundary = manifest.get("coordination_boundary", {})
    require(
        tuple(boundary.get("excluded_public_ids") or ()) == EXPECTED_EXCLUDED_IDS,
        "Structural-package exclusion boundary changed",
    )
    require(not set(EXPECTED_IDS) & set(EXPECTED_EXCLUDED_IDS), "Owner sets overlap")

    require(file_sha256(SOURCE_AUDIT) == SOURCE_AUDIT_SHA256, "Source audit changed")
    source_audit = parse_json(
        SOURCE_AUDIT.read_text(encoding="utf-8"), kind=dict, label="source audit"
    )
    validate_embedded_payload(
        source_audit, SOURCE_AUDIT_PAYLOAD_SHA256, "source audit"
    )
    source_pin = manifest.get("source_audit_artifact", {})
    require(
        source_pin.get("file_sha256") == SOURCE_AUDIT_SHA256
        and source_pin.get("payload_sha256") == SOURCE_AUDIT_PAYLOAD_SHA256,
        "Manifest-to-source-audit pins changed",
    )

    records = manifest.get("records")
    require(isinstance(records, list), "Manifest records are not a list")
    ids = tuple(record.get("public_id") for record in records)
    require(ids == EXPECTED_IDS, "The frozen 27-row ID/order set changed")
    require(len(set(ids)) == EXPECTED_COUNT, "Duplicate target public IDs")
    source_records = {record["public_id"]: record for record in source_audit["records"]}

    segment_ids: set[int] = set()
    item_ids: set[int] = set()
    public_segment_count = 0
    verified_item_count = 0
    for record in records:
        public_id = record["public_id"]
        require(
            record.get("category") == "inline_or_appended_editorial_contamination"
            and record.get("disposition") == "definite_blocker",
            f"Wrong category/disposition: {public_id}",
        )
        require(bool(str(record.get("reason") or "").strip()), f"Missing reason: {public_id}")
        record_payload = dict(record)
        stated_record_sha = record_payload.pop("record_sha256", None)
        require(
            stated_record_sha and canonical_sha256(record_payload) == stated_record_sha,
            f"Record checksum failed: {public_id}",
        )
        require(
            record == source_records.get(public_id),
            f"27-row record no longer equals source audit: {public_id}",
        )
        hadith = record.get("hadith", {})
        translation = record.get("translation", {})
        require(
            isinstance(hadith.get("sequence_in_book"), int)
            and int(hadith["sequence_in_book"]) > 0,
            f"Missing sequence coordinate: {public_id}",
        )
        require(
            translation.get("source_hashes_current") is True
            and translation.get("stored_source_hashes") == hadith.get("current_arabic_hashes"),
            f"Frozen source hashes were not current: {public_id}",
        )
        require(
            isinstance(translation.get("source_pins"), dict)
            and translation["source_pins"],
            f"Missing source pins: {public_id}",
        )
        segments = record.get("translation_segments")
        items = record.get("translation_job_items")
        require(isinstance(segments, list) and segments, f"Missing segments: {public_id}")
        require(isinstance(items, list) and items, f"Missing job items: {public_id}")
        local_segment_ids = [int(segment["id"]) for segment in segments]
        local_item_ids = [int(item["id"]) for item in items]
        require(len(set(local_segment_ids)) == len(local_segment_ids), f"Duplicate segment: {public_id}")
        require(len(set(local_item_ids)) == len(local_item_ids), f"Duplicate item: {public_id}")
        require(not segment_ids.intersection(local_segment_ids), f"Cross-record segment overlap: {public_id}")
        require(not item_ids.intersection(local_item_ids), f"Cross-record item overlap: {public_id}")
        segment_ids.update(local_segment_ids)
        item_ids.update(local_item_ids)
        action_segments = [
            segment for segment in segments
            if segment["status"] in PUBLIC_STATUSES and segment["risk_level"] == "green"
        ]
        require(len(action_segments) == 1, f"Expected one current public segment: {public_id}")
        public_segment_count += len(action_segments)
        verified_item_count += sum(
            item["status"] == "verified" and item["risk_level"] == "green"
            for item in items
        )

    require(public_segment_count == EXPECTED_PUBLIC_SEGMENTS, "Public segment total changed")
    require(verified_item_count == EXPECTED_VERIFIED_ITEMS, "Verified item total changed")
    return manifest


def connect(path: Path, *, writable: bool) -> sqlite3.Connection:
    if writable:
        connection = sqlite3.connect(path, timeout=30)
    else:
        uri = f"file:{path.resolve().as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    if not writable:
        connection.execute("PRAGMA query_only=ON")
    return connection


def rows_by_id(rows: list[sqlite3.Row]) -> dict[int, sqlite3.Row]:
    return {int(row["id"]): row for row in rows}


def public_rendered_hash(row: sqlite3.Row) -> str:
    rendered = clean_ws(
        row["full_translation"]
        or " ".join(
            part
            for part in (row["rendered_isnad_en"], row["matn_translation"])
            if clean_ws(part)
        )
    )
    return sha256_text(rendered)


def matching_quarantine_flags(flags: list[Any], *, record_sha: str, object_id: int) -> list[dict[str, Any]]:
    return [
        flag
        for flag in flags
        if isinstance(flag, dict)
        and flag.get("code") == FLAG_CODE
        and flag.get("audit_version") == AUDIT_VERSION
        and flag.get("manifest_sha256") == MANIFEST_SHA256
        and flag.get("record_sha256") == record_sha
        and int(flag.get("object_id", -1)) == int(object_id)
    ]


def without_quarantine_flag(flags: list[Any], *, record_sha: str, object_id: int) -> list[Any]:
    return [
        flag
        for flag in flags
        if flag not in matching_quarantine_flags(flags, record_sha=record_sha, object_id=object_id)
    ]


def flag_payload(record: dict[str, Any], *, object_type: str, object_id: int) -> dict[str, Any]:
    return {
        "code": FLAG_CODE,
        "severity": "critical",
        "detail": record["reason"],
        "audit_version": AUDIT_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "record_sha256": record["record_sha256"],
        "object_type": object_type,
        "object_id": int(object_id),
    }


def append_flag(flags: list[Any], record: dict[str, Any], *, object_type: str, object_id: int) -> list[Any]:
    require(
        not matching_quarantine_flags(
            flags, record_sha=record["record_sha256"], object_id=object_id
        ),
        f"Quarantine flag already exists on original {object_type} {object_id}",
    )
    return flags + [flag_payload(record, object_type=object_type, object_id=object_id)]


def common_audit(record: dict[str, Any], quarantined_at: str) -> dict[str, Any]:
    translation = record["translation"]
    return {
        "version": AUDIT_VERSION,
        "manifest": "scratch_audit/alkafi_public_editorial_contamination_quarantine_manifest_20260716.json",
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_payload_sha256": MANIFEST_PAYLOAD_SHA256,
        "source_audit_sha256": SOURCE_AUDIT_SHA256,
        "source_audit_payload_sha256": SOURCE_AUDIT_PAYLOAD_SHA256,
        "record_sha256": record["record_sha256"],
        "public_id": record["public_id"],
        "category": record["category"],
        "reason": record["reason"],
        "original_english_hashes": {
            "rendered_isnad_en_sha256": translation["rendered_isnad_en_sha256"],
            "matn_translation_sha256": translation["matn_translation_sha256"],
            "full_translation_sha256": translation["full_translation_sha256"],
            "public_rendered_english_sha256": translation["public_rendered_english_sha256"],
        },
        "original_risk_flags_sha256": translation["risk_flags_sha256"],
        "original_provenance_sha256": translation["provenance_sha256"],
        "quarantined_at": quarantined_at,
    }


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def expected_common_audit(record: dict[str, Any], audit: dict[str, Any]) -> bool:
    if not valid_timestamp(audit.get("quarantined_at")):
        return False
    expected = common_audit(record, audit["quarantined_at"])
    return all(audit.get(key) == value for key, value in expected.items())


def restore_original_provenance(provenance: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any] | None:
    overwritten = audit.get("overwritten_provenance")
    if not isinstance(overwritten, dict) or set(overwritten) != set(OVERWRITTEN_PROVENANCE_KEYS):
        return None
    restored = dict(provenance)
    restored.pop(AUDIT_KEY, None)
    for key in OVERWRITTEN_PROVENANCE_KEYS:
        snapshot = overwritten.get(key)
        if not isinstance(snapshot, dict) or set(snapshot) != {"present", "value"}:
            return None
        if snapshot["present"]:
            restored[key] = snapshot["value"]
        else:
            restored.pop(key, None)
    return restored


def validate_common_objects(
    connection: sqlite3.Connection, record: dict[str, Any]
) -> tuple[sqlite3.Row, sqlite3.Row, dict[int, sqlite3.Row], dict[int, sqlite3.Row]]:
    public_id = record["public_id"]
    hadith_spec = record["hadith"]
    translation_spec = record["translation"]

    hadiths = connection.execute(
        "SELECT * FROM hadiths WHERE public_id=?", (public_id,)
    ).fetchall()
    require(len(hadiths) == 1, f"Expected one hadith: {public_id}")
    hadith = hadiths[0]
    require(
        int(hadith["id"]) == int(hadith_spec["id"])
        and int(hadith["book_id"]) == BOOK_ID
        and int(hadith["sequence_in_book"]) == int(hadith_spec["sequence_in_book"])
        and hadith["volume_start"] == hadith_spec["volume"]
        and hadith["page_start"] == hadith_spec["page_start"]
        and hadith["page_end"] == hadith_spec["page_end"]
        and hadith["printed_number"] == hadith_spec["printed_number"],
        f"Hadith identity/coordinate changed: {public_id}",
    )
    actual_arabic = {
        "full_sha256": sha256_text(hadith["full_text_raw"]),
        "isnad_sha256": sha256_text(hadith["isnad_raw"]) if hadith["isnad_raw"] else None,
        "matn_sha256": sha256_text(hadith["matn_raw"]),
    }
    require(
        actual_arabic == hadith_spec["current_arabic_hashes"],
        f"Arabic source changed: {public_id}",
    )

    translations = connection.execute(
        """
        SELECT * FROM hadith_translations
        WHERE hadith_id=? AND language=? AND translation_version=?
        """,
        (hadith["id"], LANGUAGE, TRANSLATION_VERSION),
    ).fetchall()
    require(len(translations) == 1, f"Expected one current English translation: {public_id}")
    translation = translations[0]
    require(
        int(translation["id"]) == int(translation_spec["id"])
        and int(translation["hadith_id"]) == int(hadith["id"])
        and translation["language"] == LANGUAGE
        and translation["translation_version"] == TRANSLATION_VERSION
        and translation["provider"] == translation_spec["provider"]
        and translation["model"] == translation_spec["model"],
        f"Translation identity/source label changed: {public_id}",
    )
    stored_source = {
        "full_sha256": translation["source_full_sha256"],
        "isnad_sha256": translation["source_isnad_sha256"],
        "matn_sha256": translation["source_matn_sha256"],
    }
    require(
        stored_source == translation_spec["stored_source_hashes"] == actual_arabic,
        f"Translation source hashes are stale/changed: {public_id}",
    )

    segment_rows = connection.execute(
        "SELECT * FROM translation_segments WHERE translation_id=? ORDER BY id",
        (translation["id"],),
    ).fetchall()
    segment_map = rows_by_id(segment_rows)
    expected_segment_ids = {int(segment["id"]) for segment in record["translation_segments"]}
    require(set(segment_map) == expected_segment_ids, f"Segment object set changed: {public_id}")
    for spec in record["translation_segments"]:
        segment = segment_map[int(spec["id"])]
        require(
            int(segment["hadith_id"]) == int(hadith["id"])
            and int(segment["translation_id"]) == int(translation["id"])
            and segment["language"] == LANGUAGE
            and segment["translation_version"] == TRANSLATION_VERSION
            and segment["source_sha256"] == spec["source_sha256"]
            and sha256_text(segment["source_text"]) == spec["source_sha256"],
            f"Segment identity/source changed: {public_id}/{spec['id']}",
        )

    item_rows = connection.execute(
        "SELECT * FROM translation_job_items WHERE hadith_id=? ORDER BY id",
        (hadith["id"],),
    ).fetchall()
    item_map = rows_by_id(item_rows)
    expected_item_ids = {int(item["id"]) for item in record["translation_job_items"]}
    require(set(item_map) == expected_item_ids, f"Job-item object set changed: {public_id}")
    for spec in record["translation_job_items"]:
        item = item_map[int(spec["id"])]
        require(
            int(item["hadith_id"]) == int(hadith["id"])
            and int(item["job_id"]) == int(spec["job_id"])
            and item["segment_id"] == spec["segment_id"]
            and item["source_sha256"] == spec["source_sha256"],
            f"Job-item identity/source changed: {public_id}/{spec['id']}",
        )
        if item["segment_id"] is not None:
            linked = connection.execute(
                "SELECT hadith_id, source_sha256 FROM translation_segments WHERE id=?",
                (item["segment_id"],),
            ).fetchone()
            require(
                linked is not None and int(linked["hadith_id"]) == int(hadith["id"]),
                f"Job-item segment link changed: {public_id}/{spec['id']}",
            )
    return hadith, translation, segment_map, item_map


def translation_is_original(record: dict[str, Any], row: sqlite3.Row) -> bool:
    spec = record["translation"]
    try:
        risk_flags = parse_json(row["risk_flags"], kind=list, label=f"{record['public_id']} flags")
        provenance = parse_json(
            row["provenance_json"], kind=dict, label=f"{record['public_id']} provenance"
        )
    except RuntimeError:
        return False
    classification = provenance.get("translation_classification") or provenance.get("classification")
    haystack = " ".join(
        (
            str(row["provider"] or ""),
            str(row["model"] or ""),
            json.dumps(provenance, ensure_ascii=False, sort_keys=True),
        )
    ).casefold()
    return bool(
        row["status"] == spec["status"] in PUBLIC_STATUSES
        and row["risk_level"] == spec["risk_level"] == "green"
        and sha256_text(row["rendered_isnad_en"]) == spec["rendered_isnad_en_sha256"]
        and sha256_text(row["matn_translation"]) == spec["matn_translation_sha256"]
        and sha256_text(row["full_translation"]) == spec["full_translation_sha256"]
        and public_rendered_hash(row) == spec["public_rendered_english_sha256"]
        and canonical_sha256(risk_flags) == spec["risk_flags_sha256"]
        and canonical_sha256(provenance) == spec["provenance_sha256"]
        and source_pins(provenance) == spec["source_pins"]
        and bool(clean_ws(row["matn_translation"]))
        and not any(isinstance(flag, dict) and flag.get("severity") == "critical" for flag in risk_flags)
        and str(provenance.get("translator") or "").strip()
        and classification in PUBLIC_CLASSES
        and not any(marker in haystack for marker in FORBIDDEN_AI_MARKERS)
    )


def translation_is_target(record: dict[str, Any], row: sqlite3.Row) -> bool:
    if not (
        row["status"] == "rejected"
        and row["risk_level"] == "red"
        and row["rendered_isnad_en"] is None
        and row["matn_translation"] is None
        and row["full_translation"] is None
    ):
        return False
    try:
        flags = parse_json(row["risk_flags"], kind=list, label="target translation flags")
        provenance = parse_json(row["provenance_json"], kind=dict, label="target provenance")
    except RuntimeError:
        return False
    matches = matching_quarantine_flags(
        flags, record_sha=record["record_sha256"], object_id=int(row["id"])
    )
    if len(matches) != 1 or matches[0] != flag_payload(
        record, object_type="hadith_translation", object_id=int(row["id"])
    ):
        return False
    if canonical_sha256(
        without_quarantine_flag(
            flags, record_sha=record["record_sha256"], object_id=int(row["id"])
        )
    ) != record["translation"]["risk_flags_sha256"]:
        return False
    audit = provenance.get(AUDIT_KEY)
    if not isinstance(audit, dict) or not expected_common_audit(record, audit):
        return False
    restored = restore_original_provenance(provenance, audit)
    return bool(
        restored is not None
        and canonical_sha256(restored) == record["translation"]["provenance_sha256"]
        and provenance.get("publication_status") == "rejected"
        and provenance.get("reason") == FLAG_CODE
        and provenance.get("translation_classification")
        == "quarantined_source_extent_blocker"
    )


def segment_is_original(spec: dict[str, Any], row: sqlite3.Row) -> bool:
    return bool(
        row["status"] == spec["status"]
        and row["risk_level"] == spec["risk_level"]
        and sha256_text(row["translation_text"]) == spec["translation_sha256"]
    )


def segment_is_target(record: dict[str, Any], spec: dict[str, Any], row: sqlite3.Row) -> bool:
    if not (
        spec["status"] in PUBLIC_STATUSES
        and spec["risk_level"] == "green"
        and row["status"] == "qa_failed"
        and row["risk_level"] == "red"
        and row["translation_text"] is None
    ):
        return False
    try:
        flags = parse_json(row["risk_flags"], kind=list, label="target segment flags")
        metadata = parse_json(row["metadata_json"], kind=dict, label="target segment metadata")
    except RuntimeError:
        return False
    matches = matching_quarantine_flags(
        flags, record_sha=record["record_sha256"], object_id=int(row["id"])
    )
    if len(matches) != 1 or matches[0] != flag_payload(
        record, object_type="translation_segment", object_id=int(row["id"])
    ):
        return False
    audit = metadata.get(AUDIT_KEY)
    if not isinstance(audit, dict) or not expected_common_audit(record, audit):
        return False
    if audit.get("segment_id") != int(row["id"]):
        return False
    if audit.get("original_translation_sha256") != spec["translation_sha256"]:
        return False
    stripped_flags = without_quarantine_flag(
        flags, record_sha=record["record_sha256"], object_id=int(row["id"])
    )
    if canonical_sha256(stripped_flags) != audit.get("original_segment_risk_flags_sha256"):
        return False
    restored_metadata = dict(metadata)
    restored_metadata.pop(AUDIT_KEY, None)
    previous = audit.get("overwritten_metadata")
    if not isinstance(previous, dict) or set(previous) != {"present", "value"}:
        return False
    if previous["present"]:
        restored_metadata[AUDIT_KEY] = previous["value"]
    return canonical_sha256(restored_metadata) == audit.get("original_metadata_sha256")


def item_is_original(spec: dict[str, Any], row: sqlite3.Row) -> bool:
    return row["status"] == spec["status"] and row["risk_level"] == spec["risk_level"]


def item_is_target(spec: dict[str, Any], row: sqlite3.Row) -> bool:
    if spec["status"] == "verified" and spec["risk_level"] == "green":
        return row["status"] == "qa_failed" and row["risk_level"] == "red"
    return item_is_original(spec, row)


def classify_record(connection: sqlite3.Connection, record: dict[str, Any]) -> str:
    _, translation, segments, items = validate_common_objects(connection, record)
    original = translation_is_original(record, translation)
    target = translation_is_target(record, translation)
    for spec in record["translation_segments"]:
        row = segments[int(spec["id"])]
        action = spec["status"] in PUBLIC_STATUSES and spec["risk_level"] == "green"
        original = original and segment_is_original(spec, row)
        target = target and (
            segment_is_target(record, spec, row) if action else segment_is_original(spec, row)
        )
    for spec in record["translation_job_items"]:
        row = items[int(spec["id"])]
        original = original and item_is_original(spec, row)
        target = target and item_is_target(spec, row)
    require(original != target, f"Neither exact original nor exact target state: {record['public_id']}")
    return "original" if original else "target"


def validate_all(connection: sqlite3.Connection, manifest: dict[str, Any]) -> dict[str, int]:
    states = {"original": 0, "target": 0}
    for record in manifest["records"]:
        states[classify_record(connection, record)] += 1
    require(
        states in (
            {"original": EXPECTED_COUNT, "target": 0},
            {"original": 0, "target": EXPECTED_COUNT},
        ),
        f"Refusing partial quarantine state: {states}",
    )
    return states


def original_key_snapshot(provenance: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        key: {"present": key in provenance, "value": provenance.get(key)}
        for key in OVERWRITTEN_PROVENANCE_KEYS
    }


def mutate_record(connection: sqlite3.Connection, record: dict[str, Any], now: str) -> tuple[int, int, int]:
    _, translation, segments, items = validate_common_objects(connection, record)
    require(translation_is_original(record, translation), f"Lost original state: {record['public_id']}")

    flags = parse_json(translation["risk_flags"], kind=list, label="translation flags")
    provenance = parse_json(translation["provenance_json"], kind=dict, label="translation provenance")
    audit = common_audit(record, now)
    audit["overwritten_provenance"] = original_key_snapshot(provenance)
    provenance[AUDIT_KEY] = audit
    provenance["publication_status"] = "rejected"
    provenance["reason"] = FLAG_CODE
    provenance["translation_classification"] = "quarantined_source_extent_blocker"
    new_flags = append_flag(
        flags, record, object_type="hadith_translation", object_id=int(translation["id"])
    )
    qa_version = str(translation["qa_version"] or "").strip()
    if AUDIT_VERSION not in qa_version.split("+"):
        qa_version = "+".join(part for part in (qa_version, AUDIT_VERSION) if part)
    cursor = connection.execute(
        """
        UPDATE hadith_translations
        SET rendered_isnad_en=NULL,
            matn_translation=NULL,
            full_translation=NULL,
            status='rejected',
            risk_level='red',
            risk_flags=?,
            provenance_json=?,
            qa_version=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=? AND hadith_id=? AND status=? AND risk_level='green'
        """,
        (
            json_dump(new_flags),
            json_dump(provenance),
            qa_version,
            translation["id"],
            translation["hadith_id"],
            record["translation"]["status"],
        ),
    )
    require(cursor.rowcount == 1, f"Translation update failed: {record['public_id']}")

    segment_updates = 0
    for spec in record["translation_segments"]:
        if not (spec["status"] in PUBLIC_STATUSES and spec["risk_level"] == "green"):
            continue
        segment = segments[int(spec["id"])]
        require(segment_is_original(spec, segment), f"Lost segment state: {record['public_id']}/{spec['id']}")
        segment_flags = parse_json(segment["risk_flags"], kind=list, label="segment flags")
        metadata = parse_json(segment["metadata_json"], kind=dict, label="segment metadata")
        segment_audit = common_audit(record, now)
        segment_audit.update(
            {
                "segment_id": int(segment["id"]),
                "original_translation_sha256": spec["translation_sha256"],
                "original_segment_risk_flags_sha256": canonical_sha256(segment_flags),
                "original_metadata_sha256": canonical_sha256(metadata),
                "overwritten_metadata": {
                    "present": AUDIT_KEY in metadata,
                    "value": metadata.get(AUDIT_KEY),
                },
            }
        )
        metadata[AUDIT_KEY] = segment_audit
        cursor = connection.execute(
            """
            UPDATE translation_segments
            SET translation_text=NULL,
                status='qa_failed',
                risk_level='red',
                risk_flags=?,
                metadata_json=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND hadith_id=? AND translation_id=?
              AND status=? AND risk_level='green'
            """,
            (
                json_dump(
                    append_flag(
                        segment_flags,
                        record,
                        object_type="translation_segment",
                        object_id=int(segment["id"]),
                    )
                ),
                json_dump(metadata),
                segment["id"],
                segment["hadith_id"],
                segment["translation_id"],
                spec["status"],
            ),
        )
        require(cursor.rowcount == 1, f"Segment update failed: {record['public_id']}/{spec['id']}")
        segment_updates += 1

    item_updates = 0
    for spec in record["translation_job_items"]:
        if not (spec["status"] == "verified" and spec["risk_level"] == "green"):
            continue
        item = items[int(spec["id"])]
        require(item_is_original(spec, item), f"Lost job-item state: {record['public_id']}/{spec['id']}")
        cursor = connection.execute(
            """
            UPDATE translation_job_items
            SET status='qa_failed', risk_level='red', updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND hadith_id=? AND segment_id=?
              AND status='verified' AND risk_level='green'
            """,
            (item["id"], item["hadith_id"], item["segment_id"]),
        )
        require(cursor.rowcount == 1, f"Job-item update failed: {record['public_id']}/{spec['id']}")
        item_updates += 1
    return 1, segment_updates, item_updates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate read-only (default)")
    mode.add_argument("--apply", action="store_true", help="Apply the atomic 27-row quarantine")
    args = parser.parse_args()

    manifest = validate_manifest(args.manifest.resolve())
    db_path = args.db.resolve()
    require(db_path.is_file(), f"Missing database: {db_path}")
    connection = connect(db_path, writable=args.apply)
    try:
        # All manifest, object, Arabic/source, relationship and mutable-state
        # preconditions are checked before BEGIN IMMEDIATE by design.
        pre_states = validate_all(connection, manifest)
        result: dict[str, Any] = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "database": str(db_path),
            "manifest": str(args.manifest.resolve()),
            "manifest_sha256": MANIFEST_SHA256,
            "manifest_payload_sha256": MANIFEST_PAYLOAD_SHA256,
            "source_audit_sha256": SOURCE_AUDIT_SHA256,
            "assertion": "exact-27-or-0",
            "pre_state": pre_states,
            "translations_to_quarantine": pre_states["original"],
            "public_segments_to_fail": EXPECTED_PUBLIC_SEGMENTS if pre_states["original"] else 0,
            "verified_job_items_to_fail": EXPECTED_VERIFIED_ITEMS if pre_states["original"] else 0,
            "arabic_rows_to_change": 0,
        }
        if not args.apply:
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        if pre_states["target"] == EXPECTED_COUNT:
            result["result"] = "already_quarantined"
            print(json.dumps(result, indent=2, sort_keys=True))
            return

        connection.execute("BEGIN IMMEDIATE")
        # Recheck under the write lock so validation and mutation cannot race.
        locked_states = validate_all(connection, manifest)
        require(
            locked_states == {"original": EXPECTED_COUNT, "target": 0},
            f"State changed before write lock: {locked_states}",
        )
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        translation_updates = 0
        segment_updates = 0
        item_updates = 0
        for record in manifest["records"]:
            changed = mutate_record(connection, record, now)
            translation_updates += changed[0]
            segment_updates += changed[1]
            item_updates += changed[2]
        require(translation_updates == EXPECTED_COUNT, "Translation update count changed")
        require(segment_updates == EXPECTED_PUBLIC_SEGMENTS, "Segment update count changed")
        require(item_updates == EXPECTED_VERIFIED_ITEMS, "Job-item update count changed")
        post_states = validate_all(connection, manifest)
        require(
            post_states == {"original": 0, "target": EXPECTED_COUNT},
            f"Post-state validation failed: {post_states}",
        )
        require(
            not connection.execute("PRAGMA foreign_key_check").fetchall(),
            "Foreign-key violations detected",
        )
        connection.commit()
        result.update(
            {
                "result": "committed",
                "post_state": post_states,
                "translations_quarantined": translation_updates,
                "public_segments_failed": segment_updates,
                "verified_job_items_failed": item_updates,
                "arabic_rows_changed": 0,
            }
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception:
        if args.apply and connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
