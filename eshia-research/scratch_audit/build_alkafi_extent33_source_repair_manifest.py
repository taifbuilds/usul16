"""Build the source-pinned Al-Kafi extent-33 repair manifest.

The batch contains 32 deterministic Arabic extent repairs and one
translation-only correction (alkafi-1073).  It never writes to the database
and never generates or edits English.  Every proposed Arabic target is
checked against the local eShia page text and an exact Muhammad Sarwar record
in the pinned Thaqalayn API snapshot.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
import sys

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eshia_research.normalise import normalise_arabic_persian  # noqa: E402


DEFAULT_DB = ROOT / "eshia_research.db"
DEFAULT_OUTPUT = Path(__file__).with_name(
    "alkafi_extent33_source_repair_manifest_20260716.json"
)
STATIC_SNAPSHOT = Path(
    os.path.expandvars(r"%TEMP%\thaqalayn-al-kafi-static-full-fromzip.json")
)
API_SNAPSHOT = Path(
    os.path.expandvars(r"%TEMP%\sarwar-alkafi-audit\thaqalayn-api-alkafi.json")
)
PRE_PAGEBREAK_BACKUP = ROOT / "eshia_research.before-279-pagebreak-apply.20260707-144825.db"
ADDITIONAL_QUARANTINE_MANIFEST = Path(__file__).with_name(
    "alkafi_additional_extent_blockers_20260716.json"
)

STATIC_SHA256 = "a0e57d41ae653a9f8d2b88dca4c0a3e149ce0a25b07ba3a880ffb461db920d43"
API_SHA256 = "1b9b0628d6057797f74c59277b1b5e7eba8a4889c8fb06f71f5b8ed7f1feede2"
BACKUP_SHA256 = "a9d29b53767ce8ed81f03035cb543e61a1de46cb984be1f2706c7a690537fb9c"
ADDITIONAL_QUARANTINE_SHA256 = (
    "4795926fc7748515e6b752382e7f107ffcaf0b08ae3415b14d402e90c9d25813"
)

TRANSLATION_ONLY = {1073}
FOOTNOTE_SUFFIX_TRIMS = {4474, 6283}
FOOTNOTE_MID_REMOVALS = {
    4295: "وَ أَمِيرُ الْمُؤْمِنِينَ",
    5743: "فَجَعَلَ مِنْ كُلِّ أَلْفِ",
}
PARATEXT_TRIMS = {
    3591,
    12380,
    6681,
    10373,
    11329,
    11403,
    13279,
    14751,
    8169,
    8321,
    11096,
    11210,
    12933,
    14040,
    211,
    4227,
    10596,
    13592,
    9383,
    14607,
    14529,
    6228,
    4134,
    4772,
    5698,
    426,
    12112,
    934,
}
ALL_NUMERIC_IDS = sorted(
    TRANSLATION_ONLY
    | FOOTNOTE_SUFFIX_TRIMS
    | set(FOOTNOTE_MID_REMOVALS)
    | PARATEXT_TRIMS
)
EXPECTED_COUNT = 33


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


def json_value(value: str | Any | None) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def normalise_identity(value: str | None) -> str:
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ئ": "ي",
                "ؤ": "و",
                "ـ": "",
                "\u200c": "",
                "\u200d": "",
            }
        )
    )
    return "".join(re.findall(r"[\u0600-\u06ff]+", text))


def identity_score(left: str | None, right: str | None) -> float:
    left_norm = normalise_identity(left)
    right_norm = normalise_identity(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(
        None, left_norm, right_norm, autojunk=False
    ).ratio()


def normalised_with_map(value: str) -> tuple[str, list[int]]:
    output: list[str] = []
    offsets: list[int] = []
    replacements = {
        ord("أ"): ord("ا"),
        ord("إ"): ord("ا"),
        ord("آ"): ord("ا"),
        ord("ٱ"): ord("ا"),
        ord("ى"): ord("ي"),
        ord("ئ"): ord("ي"),
        ord("ؤ"): ord("و"),
    }
    for original_index, original in enumerate(value):
        for character in unicodedata.normalize("NFD", original):
            if unicodedata.category(character) == "Mn" or character in "ـ\u200c\u200d":
                continue
            output.append(chr(replacements.get(ord(character), ord(character))))
            offsets.append(original_index)
    return "".join(output), offsets


def paratext_boundary(value: str) -> int:
    normalised, offsets = normalised_with_map(value)
    needles = (
        "\nتم ",
        "\nهذا اخر",
        " هذا اخر كتاب",
        " تم كتاب",
        "\nتم الجزء",
    )
    matches: list[int] = []
    for needle in needles:
        start = 0
        while True:
            position = normalised.find(needle, start)
            if position < 0:
                break
            matches.append(offsets[position])
            start = position + 1
    require(matches, "No paratext boundary found")
    return min(matches)


def source_target(hadith: sqlite3.Row) -> tuple[str, str, dict[str, Any]]:
    public_number = int(str(hadith["public_id"]).split("-")[-1])
    current = hadith["full_text_raw"]
    if public_number in TRANSLATION_ONLY:
        return current, "translation_only_no_arabic_change", {}
    if public_number in PARATEXT_TRIMS:
        boundary = paratext_boundary(current)
        target = current[:boundary].rstrip()
        return target, "trim_paratext_suffix", {
            "prefix_chars": len(target),
            "removed_suffix_sha256": sha256_text(current[len(target) :]),
        }
    if public_number in FOOTNOTE_SUFFIX_TRIMS:
        marker = "\n______________________________"
        boundary = current.find(marker)
        require(boundary > 0, f"{hadith['public_id']}: footnote delimiter missing")
        target = current[:boundary].rstrip()
        return target, "trim_editorial_footnote_suffix", {
            "prefix_chars": len(target),
            "removed_suffix_sha256": sha256_text(current[len(target) :]),
        }
    if public_number in FOOTNOTE_MID_REMOVALS:
        marker = "\n______________________________\n"
        start = current.find(marker)
        require(start > 0, f"{hadith['public_id']}: mid-footnote delimiter missing")
        continuation = FOOTNOTE_MID_REMOVALS[public_number]
        end = current.find("\n" + continuation, start + len(marker))
        require(end > start, f"{hadith['public_id']}: continuation marker missing")
        target = current[:start].rstrip() + "\n" + current[end + 1 :].lstrip()
        return target, "remove_bounded_editorial_block", {
            "prefix_chars": start,
            "suffix_start_chars": end + 1,
            "removed_block_sha256": sha256_text(current[start : end + 1]),
            "continuation_sha256": sha256_text(current[end + 1 :]),
        }
    raise RuntimeError(f"Unhandled source target: {hadith['public_id']}")


def row_fingerprint(row: sqlite3.Row) -> str:
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


def page_evidence(
    connection: sqlite3.Connection, hadith: sqlite3.Row, target_full: str
) -> tuple[int, int, list[dict[str, Any]]]:
    pages = list(
        connection.execute(
            """
            SELECT id, volume_number, page_number, checksum, text_raw
            FROM pages
            WHERE book_id=? AND volume_number=? AND page_number BETWEEN ? AND ?
            ORDER BY page_number
            """,
            (
                hadith["book_id"],
                hadith["volume_start"],
                hadith["page_start"],
                hadith["page_end"],
            ),
        )
    )
    target_normalised = normalise_identity(target_full)
    matches: list[sqlite3.Row] = []
    matched_tail_chars = 0
    for tail_chars in (80, 60, 40, 25):
        target_tail = target_normalised[-tail_chars:]
        matches = [
            page
            for page in pages
            if target_tail and target_tail in normalise_identity(page["text_raw"])
        ]
        if matches:
            matched_tail_chars = tail_chars
            break
    require(matches, f"{hadith['public_id']}: target tail absent from source pages")
    target_end = matches[-1]
    evidence = [
        {
            "id": int(page["id"]),
            "volume": int(page["volume_number"]),
            "page": int(page["page_number"]),
            "checksum": page["checksum"],
            "text_sha256": sha256_text(page["text_raw"]),
        }
        for page in pages
    ]
    for page_spec in evidence:
        if page_spec["id"] == int(target_end["id"]):
            page_spec["target_tail_match_chars"] = matched_tail_chars
    return int(target_end["page_number"]), int(target_end["id"]), evidence


def api_sarwar_record(
    hadith: sqlite3.Row,
    target_full: str,
    static_record: dict[str, Any] | None,
    api_by_volume: dict[str, list[dict[str, Any]]],
    preferred_api_id: int | None,
) -> tuple[dict[str, Any], float]:
    rows = [
        row
        for row in api_by_volume[str(hadith["volume_start"])]
        if row.get("translator") == "Muhammad Sarwar"
    ]
    direct = False
    if preferred_api_id is not None:
        exact = [row for row in rows if int(row.get("id") or -1) == preferred_api_id]
        require(exact, f"{hadith['public_id']}: pinned Sarwar API id is absent")
        rows = exact
        direct = True
    elif static_record is not None:
        locator = str(static_record.get("path") or "")
        parts = locator.rsplit(":", 2)
        if len(parts) == 3:
            suffix = f"/{parts[-2]}/{parts[-1]}"
            narrowed = [row for row in rows if str(row.get("URL") or "").endswith(suffix)]
            if narrowed:
                rows = narrowed
        static_arabic = normalise_identity(static_record.get("arabic_text"))
        contained = [
            row
            for row in rows
            if static_arabic
            and static_arabic in normalise_identity(row.get("arabicText"))
        ]
        if contained:
            rows = contained
    scored = sorted(
        (
            (identity_score(target_full, row.get("arabicText")), row)
            for row in rows
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    require(scored, f"{hadith['public_id']}: no Muhammad Sarwar API candidates")
    score, record = scored[0]
    threshold = 0.35 if direct else 0.55
    require(score >= threshold, f"{hadith['public_id']}: weak Sarwar Arabic score {score}")
    if not direct and len(scored) > 1:
        require(
            score - scored[1][0] >= 0.015 or score >= 0.985,
            f"{hadith['public_id']}: ambiguous Sarwar source {score}/{scored[1][0]}",
        )
    return record, score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    for path, expected, label in (
        (STATIC_SNAPSHOT, STATIC_SHA256, "static snapshot"),
        (API_SNAPSHOT, API_SHA256, "API snapshot"),
        (PRE_PAGEBREAK_BACKUP, BACKUP_SHA256, "pre-pagebreak backup"),
        (
            ADDITIONAL_QUARANTINE_MANIFEST,
            ADDITIONAL_QUARANTINE_SHA256,
            "seven-row quarantine manifest",
        ),
    ):
        require(path.is_file(), f"Missing {label}: {path}")
        require(sha256_file(path) == expected, f"{label} checksum changed")

    static_rows = json.loads(STATIC_SNAPSHOT.read_text(encoding="utf-8"))
    static_by_index = {int(row["index"]): row for row in static_rows}
    api_by_volume = json.loads(API_SNAPSHOT.read_text(encoding="utf-8"))

    db_path = args.db.resolve()
    connection = sqlite3.connect(
        f"file:{db_path.as_posix()}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    entries: list[dict[str, Any]] = []
    try:
        for numeric_id in ALL_NUMERIC_IDS:
            public_id = f"alkafi-{numeric_id}"
            hadith = connection.execute(
                "SELECT * FROM hadiths WHERE public_id=?", (public_id,)
            ).fetchone()
            require(hadith is not None, f"Missing hadith {public_id}")
            translation = connection.execute(
                """
                SELECT * FROM hadith_translations
                WHERE hadith_id=? AND language='en'
                ORDER BY id DESC LIMIT 1
                """,
                (hadith["id"],),
            ).fetchone()
            require(translation is not None, f"Missing translation {public_id}")
            provenance = json_value(translation["provenance_json"]) or {}
            remote_id = provenance.get("remote_id") or provenance.get("thaqalayn_id")
            static_record = (
                static_by_index.get(int(remote_id))
                if translation["provider"] == "thaqalayn-data" and remote_id is not None
                else None
            )

            target_full, action, action_evidence = source_target(hadith)
            require(
                target_full.startswith((hadith["isnad_raw"] or "") + " "),
                f"{public_id}: target no longer begins with the pinned isnad",
            )
            target_matn = (
                hadith["matn_raw"]
                if numeric_id in TRANSLATION_ONLY
                else target_full[len(hadith["isnad_raw"] or "") + 1 :]
            )
            target_end_page, target_end_id, pages = page_evidence(
                connection, hadith, target_full
            )
            current_hubeali = "hubeali" in str(translation["model"] or "").casefold()
            api_record: dict[str, Any] | None = None
            score: float | None = None
            if not current_hubeali:
                api_record, score = api_sarwar_record(
                    hadith,
                    target_full,
                    static_record,
                    api_by_volume,
                    (
                        int(remote_id)
                        if translation["provider"] == "thaqalayn-api"
                        and translation["model"] == "muhammad-sarwar"
                        and remote_id is not None
                        else None
                    ),
                )
                api_arabic = api_record.get("arabicText") or ""
                api_english = api_record.get("englishText") or ""
                require(api_english.strip(), f"{public_id}: Sarwar API English is empty")
                forbidden = ("codex", "openai", "chatgpt", "hubeali")
                require(
                    not any(marker in api_english.casefold() for marker in forbidden),
                    f"{public_id}: forbidden target-English marker",
                )
            else:
                require(static_record is not None, f"{public_id}: HubeAli Arabic witness is absent")
                static_score = identity_score(target_matn, static_record.get("arabic_text"))
                require(static_score >= 0.75, f"{public_id}: weak pinned Arabic witness {static_score}")
                api_arabic = ""
                api_english = ""

            target = {
                "full_text_raw": target_full,
                "full_text_normalised": normalise_arabic_persian(target_full),
                "isnad_raw": hadith["isnad_raw"],
                "isnad_normalised": hadith["isnad_normalised"],
                "matn_raw": target_matn,
                "matn_normalised": normalise_arabic_persian(target_matn),
                "volume_end": hadith["volume_start"],
                "page_end": target_end_page,
                "page_end_id": target_end_id,
                "extraction_confidence": hadith["extraction_confidence"],
            }
            target_hashes = {
                f"{field}_sha256": sha256_text(target[field])
                for field in (
                    "full_text_raw",
                    "full_text_normalised",
                    "isnad_raw",
                    "isnad_normalised",
                    "matn_raw",
                    "matn_normalised",
                )
            }
            segment_rows = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM translation_segments WHERE hadith_id=? ORDER BY id",
                    (hadith["id"],),
                )
            ]
            segment_ids = [int(row["id"]) for row in segment_rows]
            job_rows: list[dict[str, Any]] = []
            if segment_ids:
                placeholders = ",".join("?" for _ in segment_ids)
                job_rows = [
                    dict(row)
                    for row in connection.execute(
                        f"SELECT * FROM translation_job_items WHERE segment_id IN ({placeholders}) ORDER BY id",
                        tuple(segment_ids),
                    )
                ]
            removed_english_sha = provenance.get("removed_english_sha256")
            live_english = translation["matn_translation"] or translation["full_translation"]
            entries.append(
                {
                    "public_id": public_id,
                    "hadith_id": int(hadith["id"]),
                    "sequence_in_book": int(hadith["sequence_in_book"]),
                    "bucket": (
                        "translation_only" if numeric_id in TRANSLATION_ONLY else "deterministic_repair"
                    ),
                    "action": action,
                    "action_evidence": action_evidence,
                    "current": {
                        "row_fingerprint": row_fingerprint(hadith),
                        "full_sha256": sha256_text(hadith["full_text_raw"]),
                        "isnad_sha256": sha256_text(hadith["isnad_raw"]),
                        "matn_sha256": sha256_text(hadith["matn_raw"]),
                        "full_len": len(hadith["full_text_raw"]),
                        "page_end": int(hadith["page_end"]),
                        "page_end_id": int(hadith["page_end_id"]),
                    },
                    "target": {**target, **target_hashes, "full_len": len(target_full)},
                    "source_pages": pages,
                    "chain_fingerprint": chain_fingerprint(connection, int(hadith["id"])),
                    "sarwar_source": (
                        {
                            "available": True,
                            "snapshot": "thaqalayn-api",
                            "volume": int(hadith["volume_start"]),
                            "remote_id": int(api_record["id"]),
                            "url": api_record.get("URL"),
                            "translator": api_record.get("translator"),
                            "record_sha256": canonical_json_sha256(api_record),
                            "arabic_sha256": sha256_text(api_arabic),
                            "english_sha256": sha256_text(api_english),
                            "arabic_identity_score": round(float(score), 8),
                            "target_norm_in_source_norm": normalise_identity(target_full)
                            in normalise_identity(api_arabic),
                            "source_norm_in_target_norm": normalise_identity(api_arabic)
                            in normalise_identity(target_full),
                        }
                        if api_record is not None
                        else {
                            "available": False,
                            "reason": "No exact Muhammad Sarwar record was found in the pinned API snapshot; HubeAli is not an approved target.",
                        }
                    ),
                    "arabic_witness": (
                        {
                            "snapshot": "thaqalayn-static",
                            "remote_id": int(static_record["index"]),
                            "url": static_record.get("source_url"),
                            "record_sha256": canonical_json_sha256(static_record),
                            "arabic_sha256": sha256_text(static_record.get("arabic_text")),
                            "target_matn_identity_score": round(
                                identity_score(target_matn, static_record.get("arabic_text")), 8
                            ),
                        }
                        if static_record is not None
                        else None
                    ),
                    "translation": {
                        "translation_id": int(translation["id"]),
                        "provider": translation["provider"],
                        "model": translation["model"],
                        "status": translation["status"],
                        "risk_level": translation["risk_level"],
                        "live_english_sha256": sha256_text(live_english),
                        "removed_english_sha256": removed_english_sha,
                        "provenance_sha256": canonical_json_sha256(provenance),
                        "segment_state_sha256": canonical_json_sha256(segment_rows),
                        "job_state_sha256": canonical_json_sha256(job_rows),
                        "segment_ids": segment_ids,
                        "job_item_ids": [int(row["id"]) for row in job_rows],
                        "current_hubeali": current_hubeali,
                        "republication_requires_separate_gate": True,
                    },
                }
            )
    finally:
        connection.close()

    require(len(entries) == EXPECTED_COUNT, f"Expected {EXPECTED_COUNT} entries")
    require(
        sum(entry["bucket"] == "deterministic_repair" for entry in entries) == 32,
        "Deterministic repair count changed",
    )
    payload = {
        "schema_version": "alkafi_extent33_source_repair_v1",
        "created_at": "2026-07-16",
        "scope": {
            "book": "Al-Kafi",
            "records": 33,
            "deterministic_arabic_repairs": 32,
            "translation_only": 1,
            "current_hubeali_rows_to_quarantine_without_republication": 3,
        },
        "publication_policy": (
            "English must be quarantined before Arabic mutation. No English is written by "
            "this batch; exact Muhammad Sarwar republication requires a separate source-only gate."
        ),
        "inputs": {
            "thaqalayn_static": {"path": str(STATIC_SNAPSHOT), "sha256": STATIC_SHA256},
            "thaqalayn_api": {"path": str(API_SNAPSHOT), "sha256": API_SHA256},
            "pre_pagebreak_backup": {
                "path": PRE_PAGEBREAK_BACKUP.relative_to(ROOT).as_posix(),
                "sha256": BACKUP_SHA256,
            },
            "additional_quarantine_manifest": {
                "path": ADDITIONAL_QUARANTINE_MANIFEST.name,
                "sha256": ADDITIONAL_QUARANTINE_SHA256,
            },
        },
        "entries": sorted(entries, key=lambda entry: entry["sequence_in_book"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records": len(entries),
                "manifest_sha256": sha256_file(args.output),
                "hubeali_current": sum(
                    entry["translation"]["current_hubeali"] for entry in entries
                ),
                "minimum_sarwar_identity_score": min(
                    entry["sarwar_source"]["arabic_identity_score"]
                    for entry in entries
                    if entry["sarwar_source"]["available"]
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
