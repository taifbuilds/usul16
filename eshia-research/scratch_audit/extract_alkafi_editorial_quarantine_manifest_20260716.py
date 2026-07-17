"""Extract the non-overlapping 27-row editorial quarantine packet.

The 26 colophon rows are owned by the structural repair package.  This script
derives a checksum-pinned subset from the already-frozen 53-row audit artifact
without opening or mutating SQLite.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scratch_audit" / "alkafi_public_extent_blockers_20260716.json"
OUTPUT = (
    ROOT
    / "scratch_audit"
    / "alkafi_public_editorial_contamination_quarantine_manifest_20260716.json"
)
EXPECTED_SOURCE_SHA256 = (
    "546f7f870f9da8bd269c7bf7b5903f1008f62058e0d5da0b2404781b5b044622"
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    source_sha256 = sha256(source_bytes)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"Frozen source changed: {source_sha256} != {EXPECTED_SOURCE_SHA256}"
        )
    source = json.loads(source_bytes)
    records = [
        record
        for record in source["records"]
        if record["category"] == "inline_or_appended_editorial_contamination"
        and record["disposition"] == "definite_blocker"
    ]
    records.sort(key=lambda record: int(record["public_id"].rsplit("-", 1)[1]))
    if len(records) != 27:
        raise RuntimeError(f"Expected 27 editorial blockers, found {len(records)}")

    excluded = [
        record["public_id"]
        for record in source["records"]
        if record not in records
    ]
    payload: dict[str, Any] = {
        "schema_version": "alkafi_editorial_contamination_quarantine_v1",
        "purpose": (
            "Fail-closed quarantine packet for the 27 additional public "
            "inline/appended editorial or truncation contaminants only"
        ),
        "database_snapshot": source["database_snapshot"],
        "source_audit_artifact": {
            "path": str(SOURCE),
            "file_sha256": source_sha256,
            "payload_sha256": source["payload_sha256"],
        },
        "coordination_boundary": {
            "included_owner": "editorial_contamination_quarantine",
            "excluded_owner": "33-row structural package",
            "excluded_public_ids": excluded,
            "rule": (
                "Do not mutate excluded rows from this packet; their preconditions "
                "belong to the structural repair workflow."
            ),
        },
        "publication_action": {
            "translation": {"status": "rejected", "risk_level": "red"},
            "segments": {"status": "qa_failed", "risk_level": "red"},
            "job_items": {"status": "qa_failed", "risk_level": "red"},
            "required_flag": {
                "code": "confirmed_editorial_extent_contamination",
                "severity": "critical",
            },
            "policy": "atomic, idempotent, exact precondition hashes, fail closed",
        },
        "counts": {
            "records": len(records),
            "excluded_structural_records": len(excluded),
        },
        "records": records,
    }
    payload["payload_sha256"] = sha256(canonical_bytes(payload))
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "file_sha256": sha256(OUTPUT.read_bytes()),
                "payload_sha256": payload["payload_sha256"],
                "records": len(records),
                "excluded": len(excluded),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
