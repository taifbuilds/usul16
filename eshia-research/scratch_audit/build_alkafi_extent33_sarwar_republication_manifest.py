"""Build exact Muhammad Sarwar republication records for extent-33 repairs.

No English is generated.  Targets are verbatim plaintext from the pinned
Thaqalayn API snapshot.  Two records whose source includes an English colophon
use a checksum-pinned contiguous prefix; the removed source suffix is retained
as evidence in the manifest.  Three rows with only HubeAli evidence are
excluded and must remain quarantined.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eshia_research.translation.thaqalayn_importer import strip_html_text  # noqa: E402


STRUCTURAL_MANIFEST = Path(__file__).with_name(
    "alkafi_extent33_source_repair_manifest_20260716.json"
)
STRUCTURAL_SHA256 = "6186515b5d4e02e532f8ef9d278db2c92608fd71cadf88e8993ad6802a435cd6"
API_SNAPSHOT = Path(
    os.path.expandvars(r"%TEMP%\sarwar-alkafi-audit\thaqalayn-api-alkafi.json")
)
API_SHA256 = "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
DEFAULT_OUTPUT = Path(__file__).with_name(
    "alkafi_extent33_sarwar_republication_manifest_20260716.json"
)
BOUNDARY_PHRASES = {
    "alkafi-426": "This is the end of the Book on the Oneness of Allah of al-Kafi.",
    "alkafi-12112": "End of the Book of Foods followed by the Book of Drinks",
}
EXPECTED_REPUBLISH = 30
EXPECTED_WITHHELD = {"alkafi-11096", "alkafi-11210", "alkafi-14040"}


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
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    require(sha256_file(STRUCTURAL_MANIFEST) == STRUCTURAL_SHA256, "Structural manifest changed")
    require(sha256_file(API_SNAPSHOT) == API_SHA256, "API snapshot changed")
    structural = json.loads(STRUCTURAL_MANIFEST.read_text(encoding="utf-8"))
    api = json.loads(API_SNAPSHOT.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []
    for entry in structural["entries"]:
        source = entry["sarwar_source"]
        if not source["available"]:
            withheld.append(
                {
                    "public_id": entry["public_id"],
                    "hadith_id": entry["hadith_id"],
                    "reason": source["reason"],
                    "disposition": "remain_quarantined_no_hubeali_target",
                }
            )
            continue
        candidates = [
            row
            for row in api[str(source["volume"])]
            if int(row.get("id") or -1) == int(source["remote_id"])
        ]
        require(len(candidates) == 1, f"{entry['public_id']}: API record missing")
        api_record = candidates[0]
        require(
            api_record.get("translator") == "Muhammad Sarwar"
            and canonical_json_sha256(api_record) == source["record_sha256"],
            f"{entry['public_id']}: API record changed",
        )
        raw_english = api_record.get("englishText") or ""
        plaintext = strip_html_text(raw_english)
        require(plaintext, f"{entry['public_id']}: source English is empty")
        boundary = BOUNDARY_PHRASES.get(entry["public_id"])
        removed_suffix = ""
        if boundary:
            position = plaintext.find(boundary)
            require(position > 0, f"{entry['public_id']}: English colophon boundary missing")
            removed_suffix = plaintext[position:].strip()
            target_english = plaintext[:position].rstrip()
        else:
            target_english = plaintext
        require(target_english, f"{entry['public_id']}: bounded source English is empty")
        lower = target_english.casefold()
        require(
            not any(marker in lower for marker in ("codex", "openai", "chatgpt", "hubeali")),
            f"{entry['public_id']}: forbidden target marker",
        )
        require(
            "end of the book" not in lower and "translation muhammad sarwar" not in lower,
            f"{entry['public_id']}: English paratext remains",
        )
        records.append(
            {
                "public_id": entry["public_id"],
                "hadith_id": entry["hadith_id"],
                "sequence_in_book": entry["sequence_in_book"],
                "translation_id": entry["translation"]["translation_id"],
                "segment_ids": entry["translation"]["segment_ids"],
                "job_item_ids": entry["translation"]["job_item_ids"],
                "target_source": {
                    "provider": "thaqalayn-api",
                    "model": "muhammad-sarwar",
                    "translator": "Muhammad Sarwar",
                    "volume": source["volume"],
                    "remote_id": source["remote_id"],
                    "url": source["url"],
                    "snapshot_sha256": API_SHA256,
                    "record_sha256": source["record_sha256"],
                    "raw_english_sha256": sha256_text(raw_english),
                    "plaintext_english_sha256": sha256_text(plaintext),
                    "target_english_sha256": sha256_text(target_english),
                    "bounded_prefix": bool(boundary),
                    "boundary_phrase": boundary,
                    "removed_suffix_sha256": sha256_text(removed_suffix) if removed_suffix else None,
                },
                "target_arabic": {
                    "full_sha256": entry["target"]["full_text_raw_sha256"],
                    "isnad_sha256": entry["target"]["isnad_raw_sha256"],
                    "matn_sha256": entry["target"]["matn_raw_sha256"],
                },
                "target_english": target_english,
            }
        )

    require(len(records) == EXPECTED_REPUBLISH, "Sarwar republication count changed")
    require({row["public_id"] for row in withheld} == EXPECTED_WITHHELD, "Withheld set changed")
    payload = {
        "schema_version": "alkafi_extent33_sarwar_republication_v1",
        "created_at": "2026-07-16",
        "publication_policy": (
            "Exact Muhammad Sarwar source text only; no generated English, no HubeAli, "
            "and no publication until the 32 Arabic targets are present."
        ),
        "inputs": {
            "structural_manifest": {
                "path": STRUCTURAL_MANIFEST.name,
                "sha256": STRUCTURAL_SHA256,
            },
            "thaqalayn_api": {"path": str(API_SNAPSHOT), "sha256": API_SHA256},
        },
        "records": sorted(records, key=lambda row: row["sequence_in_book"]),
        "withheld": sorted(withheld, key=lambda row: row["public_id"]),
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records": len(records),
                "withheld": len(withheld),
                "bounded_prefixes": sum(
                    row["target_source"]["bounded_prefix"] for row in records
                ),
                "manifest_sha256": sha256_file(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
