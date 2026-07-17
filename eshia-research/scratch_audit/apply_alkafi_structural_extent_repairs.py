"""Apply the 2026-07-16 source-pinned Al-Kafi structural repairs.

Dry-run is the default.  The script never writes or republishes English.  It
refuses to proceed if any affected English row/segment is public or green, if
the source snapshots drift, or if a local Arabic/page/chain assertion drifts.

Examples:
    python scratch_audit/apply_alkafi_structural_extent_repairs.py
    python scratch_audit/apply_alkafi_structural_extent_repairs.py \
        --apply --confirm APPLY-13-STRUCTURAL-REPAIRS \
        --backup-output eshia_research.before-structural-repair.db
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eshia_research.normalise import normalise_arabic_persian  # noqa: E402


DEFAULT_MANIFEST = Path(__file__).with_name(
    "alkafi_structural_extent_repair_manifest_20260716.json"
)
DEFAULT_DB = ROOT / "eshia_research.db"
APPLY_CONFIRMATION = "APPLY-13-STRUCTURAL-REPAIRS"
PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
TARGET_FIELDS = (
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
HASH_FIELDS = {
    "full_text_raw": "full_sha256",
    "full_text_normalised": "full_normalised_sha256",
    "isnad_raw": "isnad_sha256",
    "isnad_normalised": "isnad_normalised_sha256",
    "matn_raw": "matn_sha256",
    "matn_normalised": "matn_normalised_sha256",
}
REVIEWER = "usul16-source-structural-repair"
SPLIT_VERSION = "alkafi_structural_source_v1"


class RepairError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RepairError(message)


def sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clean_ws(value: str | None) -> str:
    return " ".join((value or "").split())


def normalise_arabic_identity(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = re.sub(r"\[[^\]]*\]", " ", text).replace("ـ", "")
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
                "ك": "ک",
            }
        )
    )
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )
    return "".join(re.findall(r"[\u0600-\u06ff]+", text))


def arabic_identity_score(left: str | None, right: str | None) -> float:
    left_norm = normalise_arabic_identity(left)
    right_norm = normalise_arabic_identity(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(
        None, left_norm, right_norm, autojunk=False
    ).ratio()


def resolve_path(raw: str, *, relative_to: Path = ROOT) -> Path:
    expanded = Path(os.path.expandvars(raw)).expanduser()
    return expanded if expanded.is_absolute() else relative_to / expanded


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_file_pin(spec: dict[str, Any], label: str) -> Path:
    path = resolve_path(str(spec["path"]))
    require(path.is_file(), f"missing {label}: {path}")
    actual = sha256_file(path)
    require(
        actual.casefold() == str(spec["sha256"]).casefold(),
        f"{label} SHA-256 drift: expected={spec['sha256']} actual={actual}",
    )
    return path


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


def create_online_backup(source: Path, destination: Path) -> None:
    """Create a consistent SQLite backup, including any committed WAL pages."""

    source_connection = connect(source, writable=False)
    destination_connection = sqlite3.connect(str(destination))
    try:
        source_connection.backup(destination_connection)
        integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()
        require(
            integrity is not None and integrity[0] == "ok",
            f"pre-apply backup integrity check failed: {integrity}",
        )
        source_geometry = source_connection.execute(
            "SELECT (SELECT page_count FROM pragma_page_count), "
            "(SELECT page_size FROM pragma_page_size)"
        ).fetchone()
        destination_geometry = destination_connection.execute(
            "SELECT (SELECT page_count FROM pragma_page_count), "
            "(SELECT page_size FROM pragma_page_size)"
        ).fetchone()
        require(
            tuple(source_geometry) == tuple(destination_geometry),
            "pre-apply online-backup page geometry mismatch",
        )
    finally:
        destination_connection.close()
        source_connection.close()


def row_dict(row: sqlite3.Row | None, label: str) -> dict[str, Any]:
    require(row is not None, f"missing {label}")
    return dict(row)


def get_hadith(connection: sqlite3.Connection, public_id: str) -> dict[str, Any]:
    return row_dict(
        connection.execute(
            "SELECT * FROM hadiths WHERE public_id=?", (public_id,)
        ).fetchone(),
        f"hadith {public_id}",
    )


def validate_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require(
        manifest.get("schema_version") == "alkafi_structural_extent_repair_v1",
        "unsupported manifest schema",
    )
    entries = manifest.get("entries") or []
    require(len(entries) == 18, f"manifest must contain 18 entries, got {len(entries)}")
    by_id = {entry["public_id"]: entry for entry in entries}
    require(len(by_id) == 18, "manifest public IDs are not unique")
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["bucket"]] = counts.get(entry["bucket"], 0) + 1
    require(
        counts
        == {
            "deterministic_repair": 13,
            "new_row_policy_required": 4,
            "translation_only": 1,
        },
        f"unexpected manifest buckets: {counts}",
    )
    return by_id


def validate_dossier(
    manifest: dict[str, Any], entries: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    path = assert_file_pin(manifest["inputs"]["dossier"], "blocker dossier")
    dossier = read_json(path)
    columns = dossier["record_columns"]
    structural = {
        dict(zip(columns, record))["public_id"]: dict(zip(columns, record))
        for record in dossier["records"]
        if dict(zip(columns, record))["category_key"] == "S"
    }
    require(
        set(structural) == set(entries),
        "manifest IDs differ from the dossier's exact 18 structural IDs",
    )
    for public_id, entry in entries.items():
        record = structural[public_id]
        require(
            int(record["hadith_id"]) == int(entry["hadith_id"]),
            f"{public_id}: dossier hadith ID drift",
        )
        require(
            int(record["translation_id"])
            == int(entry["translation"]["translation_id"]),
            f"{public_id}: dossier translation ID drift",
        )
    return structural


def validate_page(
    connection: sqlite3.Connection, spec: dict[str, Any], public_id: str
) -> dict[str, Any]:
    page = row_dict(
        connection.execute("SELECT * FROM pages WHERE id=?", (spec["id"],)).fetchone(),
        f"{public_id} page {spec['id']}",
    )
    for key, column in (("volume", "volume_number"), ("page", "page_number")):
        require(
            int(page[column]) == int(spec[key]),
            f"{public_id}: page {spec['id']} {column} drift",
        )
    require(
        page["checksum"] == spec["checksum"],
        f"{public_id}: page {spec['id']} checksum drift",
    )
    if spec.get("text_sha256"):
        require(
            sha256_text(page["text_raw"]) == spec["text_sha256"],
            f"{public_id}: page {spec['id']} text SHA drift",
        )
    return page


def validate_target(entry: dict[str, Any], target: dict[str, Any]) -> None:
    public_id = entry["public_id"]
    spec = entry["target"]
    require(
        len(target["full_text_raw"]) == int(spec["full_len"]),
        f"{public_id}: target full length drift",
    )
    for field, hash_key in HASH_FIELDS.items():
        require(
            sha256_text(target[field]) == spec[hash_key],
            f"{public_id}: target {field} SHA drift",
        )
    for field in (
        "volume_end",
        "page_end",
        "page_end_id",
        "extraction_confidence",
    ):
        require(
            target[field] == spec[field],
            f"{public_id}: target {field} drift",
        )
    require(
        target["full_text_normalised"]
        == normalise_arabic_persian(target["full_text_raw"]),
        f"{public_id}: target full normalization is stale",
    )
    expected_isnad_norm = (
        normalise_arabic_persian(target["isnad_raw"])
        if target["isnad_raw"] is not None
        else None
    )
    require(
        target["isnad_normalised"] == expected_isnad_norm,
        f"{public_id}: target isnad normalization is stale",
    )
    require(
        target["matn_normalised"]
        == normalise_arabic_persian(target["matn_raw"]),
        f"{public_id}: target matn normalization is stale",
    )
    if target["isnad_raw"] is not None:
        require(
            clean_ws(target["full_text_raw"])
            == clean_ws(f"{target['isnad_raw']} {target['matn_raw']}"),
            f"{public_id}: target full/isnad/matn boundary differs beyond whitespace",
        )


def target_already_present(entry: dict[str, Any], current: dict[str, Any]) -> bool:
    spec = entry["target"]
    return all(
        sha256_text(current[field]) == spec[hash_key]
        for field, hash_key in HASH_FIELDS.items()
    ) and all(
        current[field] == spec[field]
        for field in (
            "volume_end",
            "page_end",
            "page_end_id",
            "extraction_confidence",
        )
    )


def hadith_source_state_fingerprint(row: dict[str, Any]) -> str:
    fields = (
        "id",
        "public_id",
        "sequence_in_book",
        "review_status",
        *TARGET_FIELDS,
    )
    return canonical_json_sha256({field: row[field] for field in fields})


def build_target(
    connection: sqlite3.Connection,
    backup: sqlite3.Connection,
    entry: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    public_id = entry["public_id"]
    current = get_hadith(connection, public_id)
    require(
        int(current["id"]) == int(entry["hadith_id"]),
        f"{public_id}: live hadith ID drift",
    )
    if target_already_present(entry, current):
        target = dict(current)
        validate_target(entry, target)
        return current, target, True

    require(
        sha256_text(current["full_text_raw"]) == entry["current_full_sha256"],
        f"{public_id}: current full Arabic SHA is neither source nor target",
    )
    target = dict(current)
    action = entry["action"]
    if action in {
        "restore_from_pinned_backup",
        "restore_from_pinned_backup_and_reactivate_neighbor",
        "restore_split_and_retire_parser_artifact",
    }:
        source = get_hadith(backup, public_id)
        require(
            int(source["id"]) == int(entry["hadith_id"]),
            f"{public_id}: backup hadith ID drift",
        )
        for field in TARGET_FIELDS:
            target[field] = source[field]
    elif action == "trim_full_text_prefix":
        prefix = current["full_text_raw"][: int(entry["prefix_chars"])]
        require(
            current["isnad_raw"] is not None,
            f"{public_id}: trim target unexpectedly has no isnad",
        )
        delimiter = len(current["isnad_raw"])
        require(prefix[delimiter : delimiter + 1] == " ", f"{public_id}: split delimiter drift")
        target["full_text_raw"] = prefix
        target["full_text_normalised"] = normalise_arabic_persian(prefix)
        target["matn_raw"] = prefix[delimiter + 1 :]
        target["matn_normalised"] = normalise_arabic_persian(target["matn_raw"])
    elif action == "append_pinned_page_prefixes":
        bodies: list[str] = []
        for page_spec in entry["page_prefixes"]:
            page = validate_page(connection, page_spec, public_id)
            lines = (page["text_raw"] or "").splitlines()
            matches = [
                index
                for index, line in enumerate(lines)
                if re.match(page_spec["stop_regex"], line)
            ]
            require(
                bool(matches),
                f"{public_id}: page {page_spec['id']} has no stop marker",
            )
            body = "\n".join(lines[: matches[0]]).rstrip()
            require(
                sha256_text(body) == page_spec["body_sha256"],
                f"{public_id}: page {page_spec['id']} body SHA drift",
            )
            bodies.append(body)
        continuation = " " + " ".join(bodies)
        target["full_text_raw"] = current["full_text_raw"] + continuation
        target["full_text_normalised"] = normalise_arabic_persian(
            target["full_text_raw"]
        )
        target["matn_raw"] = current["matn_raw"] + continuation
        target["matn_normalised"] = normalise_arabic_persian(target["matn_raw"])
    else:
        raise RepairError(f"{public_id}: unsupported deterministic action {action}")

    for field in (
        "volume_end",
        "page_end",
        "page_end_id",
        "extraction_confidence",
    ):
        target[field] = entry["target"][field]
    validate_target(entry, target)
    page = row_dict(
        connection.execute(
            "SELECT id, volume_number, page_number FROM pages WHERE id=?",
            (target["page_end_id"],),
        ).fetchone(),
        f"{public_id} target end page",
    )
    require(
        int(page["volume_number"]) == int(target["volume_end"])
        and int(page["page_number"]) == int(target["page_end"]),
        f"{public_id}: target end-page foreign key does not match volume/page",
    )
    return current, target, False


def load_external_sources(
    manifest: dict[str, Any], entries: Iterable[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    inputs = manifest["inputs"]
    static_path = assert_file_pin(
        inputs["thaqalayn_static_snapshot"], "ThaqalaynData static snapshot"
    )
    api_path = assert_file_pin(
        inputs["thaqalayn_api_snapshot"], "Thaqalayn API snapshot"
    )
    static_rows = read_json(static_path)
    api_payload = read_json(api_path)
    static = {str(row["path"]): row for row in static_rows}
    api = {
        (int(volume), int(row["id"])): row
        for volume, rows in api_payload.items()
        for row in rows
    }
    for entry in entries:
        spec = entry["external_source"]
        public_id = entry["public_id"]
        if spec["kind"] == "static":
            row = static.get(spec["locator"])
            require(row is not None, f"{public_id}: missing static external record")
            arabic = row.get("arabic_text") or ""
            english = clean_ws(row.get("en_sarwar"))
            require(english, f"{public_id}: pinned static Sarwar English is empty")
        elif spec["kind"] == "api":
            row = api.get((int(spec["volume"]), int(spec["remote_id"])))
            require(row is not None, f"{public_id}: missing API external record")
            require(
                clean_ws(row.get("translator")).casefold() == "muhammad sarwar",
                f"{public_id}: API source is not attributed to Muhammad Sarwar",
            )
            arabic = row.get("arabicText") or ""
            english = clean_ws(row.get("thaqalaynMatn") or row.get("englishText"))
        else:
            raise RepairError(f"{public_id}: unsupported external source kind")
        require(
            canonical_json_sha256(row) == spec["record_sha256"],
            f"{public_id}: external record SHA drift",
        )
        require(
            sha256_text(arabic) == spec["arabic_sha256"],
            f"{public_id}: external Arabic SHA drift",
        )
        require(
            sha256_text(english) == spec["english_sha256"],
            f"{public_id}: external Sarwar English SHA drift",
        )
    return static, api


def validate_external_identity(
    entry: dict[str, Any], target: dict[str, Any], static: dict[str, Any], api: dict[Any, Any]
) -> None:
    spec = entry["external_source"]
    if spec["kind"] == "static":
        source_arabic = static[spec["locator"]]["arabic_text"]
    else:
        source_arabic = api[(int(spec["volume"]), int(spec["remote_id"]))][
            "arabicText"
        ]
    score = arabic_identity_score(target[spec["arabic_identity_field"]], source_arabic)
    require(
        abs(score - float(spec["arabic_identity_score"])) <= 0.00000002,
        f"{entry['public_id']}: external Arabic identity score drift: {score:.8f}",
    )


def validate_sarwar_1151(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    path = assert_file_pin(manifest["inputs"]["sarwar_scan_records"], "Sarwar scan records")
    payload = read_json(path)
    spec = entry["exact_sarwar_replacement"]
    matches = [
        row
        for row in payload["records"]
        if int(row["physical_volume"]) == int(spec["physical_volume"])
        and int(row["hadith_number"]) == int(spec["hadith_number"])
        and str(row["chapter_number"]) == str(spec["chapter_number"])
        and str(row["number_in_chapter"]) == str(spec["number_in_chapter"])
    ]
    require(len(matches) == 1, f"alkafi-1151: exact Sarwar record count={len(matches)}")
    row = matches[0]
    require(int(row["pdf_page"]) == int(spec["pdf_page"]), "alkafi-1151: PDF page drift")
    require(row["marker"] == spec["marker"], "alkafi-1151: PDF marker drift")
    require(row["source_sha256"] == spec["pdf_sha256"], "alkafi-1151: PDF SHA drift")
    require(
        sha256_text(row["english"]) == spec["english_sha256"]
        and len(row["english"]) == int(spec["english_len"]),
        "alkafi-1151: exact Sarwar replacement text drift",
    )


def validate_quarantine(
    connection: sqlite3.Connection,
    entries: dict[str, dict[str, Any]],
    dossier: dict[str, dict[str, Any]],
) -> int:
    checked = 0
    for public_id, entry in entries.items():
        translations = connection.execute(
            "SELECT * FROM hadith_translations WHERE hadith_id=? AND language='en'",
            (entry["hadith_id"],),
        ).fetchall()
        require(translations, f"{public_id}: no English translation row exists")
        expected_id = int(entry["translation"]["translation_id"])
        require(
            expected_id in {int(row["id"]) for row in translations},
            f"{public_id}: expected translation {expected_id} is missing",
        )
        for row in translations:
            require(
                row["status"] not in PUBLIC_STATUSES and row["risk_level"] != "green",
                f"{public_id}: translation {row['id']} is not quarantined "
                f"({row['status']}/{row['risk_level']})",
            )
            checked += 1
        segments = connection.execute(
            "SELECT * FROM translation_segments WHERE hadith_id=? AND language='en'",
            (entry["hadith_id"],),
        ).fetchall()
        for row in segments:
            require(
                row["status"] not in PUBLIC_STATUSES and row["risk_level"] != "green",
                f"{public_id}: segment {row['id']} is not quarantined "
                f"({row['status']}/{row['risk_level']})",
            )
        require(
            dossier[public_id]["english_sha256"],
            f"{public_id}: dossier lost its removed-English SHA",
        )
    return checked


def rows_fingerprint(
    connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...]
) -> str:
    rows = [dict(row) for row in connection.execute(query, parameters).fetchall()]
    return canonical_json_sha256(rows)


def chain_fingerprint(connection: sqlite3.Connection, hadith_id: int) -> str:
    chains = connection.execute(
        "SELECT id FROM chains WHERE hadith_id=? ORDER BY id", (hadith_id,)
    ).fetchall()
    chain_ids = [int(row["id"]) for row in chains]
    if not chain_ids:
        return canonical_json_sha256([])
    placeholders = ",".join("?" for _ in chain_ids)
    nodes = connection.execute(
        f"SELECT id FROM chain_nodes WHERE chain_id IN ({placeholders}) ORDER BY id",
        tuple(chain_ids),
    ).fetchall()
    node_ids = [int(row["id"]) for row in nodes]
    payload: dict[str, Any] = {
        "chains": [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM chains WHERE id IN ({placeholders}) ORDER BY id",
                tuple(chain_ids),
            )
        ],
        "nodes": [],
        "candidates": [],
        "mentions": [],
        "decisions": [],
        "external": [],
    }
    if node_ids:
        node_placeholders = ",".join("?" for _ in node_ids)
        payload["nodes"] = [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM chain_nodes WHERE id IN ({node_placeholders}) ORDER BY id",
                tuple(node_ids),
            )
        ]
        for key, table in (
            ("candidates", "chain_node_candidates"),
            ("mentions", "mention_resolutions"),
            ("decisions", "person_resolution_decisions"),
            ("external", "person_resolution_external_reviews"),
        ):
            payload[key] = [
                dict(row)
                for row in connection.execute(
                    f"SELECT * FROM {table} WHERE chain_node_id IN ({node_placeholders}) ORDER BY id",
                    tuple(node_ids),
                )
            ]
    return canonical_json_sha256(payload)


def preserved_2695_fingerprint(
    connection: sqlite3.Connection, node_ids: list[int]
) -> str:
    placeholders = ",".join("?" for _ in node_ids)
    payload: dict[str, Any] = {
        "nodes": [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM chain_nodes WHERE id IN ({placeholders}) ORDER BY id",
                tuple(node_ids),
            )
        ]
    }
    for key, table in (
        ("candidates", "chain_node_candidates"),
        ("mentions", "mention_resolutions"),
        ("decisions", "person_resolution_decisions"),
        ("external", "person_resolution_external_reviews"),
    ):
        payload[key] = [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM {table} WHERE chain_node_id IN ({placeholders}) ORDER BY id",
                tuple(node_ids),
            )
        ]
    return canonical_json_sha256(payload)


def validate_2695_cleanup_state(
    connection: sqlite3.Connection, entry: dict[str, Any]
) -> bool:
    spec = entry["chain_cleanup"]
    chain = row_dict(
        connection.execute("SELECT * FROM chains WHERE id=?", (spec["chain_id"],)).fetchone(),
        "alkafi-2695 chain",
    )
    require(int(chain["hadith_id"]) == int(entry["hadith_id"]), "alkafi-2695 chain owner drift")
    nodes = connection.execute(
        "SELECT id, position FROM chain_nodes WHERE chain_id=? ORDER BY position",
        (spec["chain_id"],),
    ).fetchall()
    actual_ids = [int(row["id"]) for row in nodes]
    target_ids = [int(value) for value in spec["preserve_node_ids"]]
    if actual_ids == target_ids:
        require(
            chain["raw_isnad"] is not None
            and sha256_text(chain["raw_isnad"])
            == entry["target"]["isnad_sha256"],
            "alkafi-2695: cleaned chain has wrong raw isnad",
        )
        require(
            int(chain["node_count"]) == int(spec["target_node_count"])
            and chain["flags"] == spec["target_flags"]
            and chain["review_status"] == spec["target_review_status"],
            "alkafi-2695: cleaned chain metadata drift",
        )
        return True
    require(
        actual_ids == target_ids + [int(spec["retire_node_id"])],
        f"alkafi-2695: unexpected chain node IDs {actual_ids}",
    )
    require(
        [int(row["position"]) for row in nodes] == list(range(7)),
        "alkafi-2695: chain positions drift",
    )
    checks = (
        ("mention_resolutions", "retire_mention_resolution_ids"),
        ("person_resolution_decisions", "retire_person_decision_ids"),
        ("person_resolution_external_reviews", "retire_external_review_ids"),
        ("chain_node_candidates", "expected_candidate_ids"),
    )
    for table, key in checks:
        ids = [
            int(row["id"])
            for row in connection.execute(
                f"SELECT id FROM {table} WHERE chain_node_id=? ORDER BY id",
                (spec["retire_node_id"],),
            )
        ]
        require(ids == [int(value) for value in spec[key]], f"alkafi-2695: {table} IDs drift: {ids}")
    return False


def upsert_split_review(
    connection: sqlite3.Connection,
    hadith_id: int,
    isnad_raw: str | None,
    matn_raw: str,
    notes: str,
) -> None:
    connection.execute(
        """
        INSERT INTO hadith_split_reviews (
            hadith_id, approved_isnad_raw, approved_matn_raw, review_status,
            reviewer, notes, split_version, created_at, updated_at
        ) VALUES (?, ?, ?, 'approved', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(hadith_id) DO UPDATE SET
            approved_isnad_raw=excluded.approved_isnad_raw,
            approved_matn_raw=excluded.approved_matn_raw,
            review_status='approved',
            reviewer=excluded.reviewer,
            notes=excluded.notes,
            split_version=excluded.split_version,
            updated_at=CURRENT_TIMESTAMP
        """,
        (hadith_id, isnad_raw, matn_raw, REVIEWER, notes, SPLIT_VERSION),
    )


def apply_target(
    connection: sqlite3.Connection, entry: dict[str, Any], target: dict[str, Any]
) -> None:
    assignments = ", ".join(f"{field}=?" for field in TARGET_FIELDS)
    values = [target[field] for field in TARGET_FIELDS]
    cursor = connection.execute(
        f"UPDATE hadiths SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=? AND public_id=?",
        (*values, entry["hadith_id"], entry["public_id"]),
    )
    require(cursor.rowcount == 1, f"{entry['public_id']}: hadith update count={cursor.rowcount}")
    upsert_split_review(
        connection,
        int(entry["hadith_id"]),
        target["isnad_raw"],
        target["matn_raw"],
        "Source-pinned structural/extent repair; English remains quarantined pending the separate republication manifest.",
    )


def apply_2695_cleanup(
    connection: sqlite3.Connection,
    entry: dict[str, Any],
    target: dict[str, Any],
    already_clean: bool,
) -> None:
    spec = entry["chain_cleanup"]
    if not already_clean:
        for table, key in (
            ("person_resolution_external_reviews", "retire_external_review_ids"),
            ("person_resolution_decisions", "retire_person_decision_ids"),
            ("mention_resolutions", "retire_mention_resolution_ids"),
            ("chain_node_candidates", "expected_candidate_ids"),
        ):
            ids = [int(value) for value in spec[key]]
            if not ids:
                continue
            placeholders = ",".join("?" for _ in ids)
            cursor = connection.execute(
                f"DELETE FROM {table} WHERE id IN ({placeholders})", tuple(ids)
            )
            require(cursor.rowcount == len(ids), f"alkafi-2695: delete count drift in {table}")
        cursor = connection.execute(
            "DELETE FROM chain_nodes WHERE id=? AND chain_id=?",
            (spec["retire_node_id"], spec["chain_id"]),
        )
        require(cursor.rowcount == 1, "alkafi-2695: parser-artifact node was not deleted")
    cursor = connection.execute(
        """
        UPDATE chains SET raw_isnad=?, node_count=?, flags=?, review_status=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=? AND hadith_id=?
        """,
        (
            target["isnad_raw"],
            spec["target_node_count"],
            spec["target_flags"],
            spec["target_review_status"],
            spec["chain_id"],
            entry["hadith_id"],
        ),
    )
    require(cursor.rowcount == 1, "alkafi-2695: chain update count drift")


def validate_or_apply_neighbor(
    connection: sqlite3.Connection, entry: dict[str, Any], *, apply: bool
) -> None:
    spec = entry["neighbor"]
    neighbor = get_hadith(connection, spec["public_id"])
    require(int(neighbor["id"]) == int(spec["hadith_id"]), "alkafi-2862: ID drift")
    require(
        sha256_text(neighbor["full_text_raw"]) == spec["full_sha256"]
        and sha256_text(neighbor["matn_raw"]) == spec["matn_sha256"],
        "alkafi-2862: continuation text drift",
    )
    for key in ("page_start", "page_end", "page_start_id", "page_end_id"):
        require(neighbor[key] == spec[key], f"alkafi-2862: {key} drift")
    require(
        connection.execute(
            "SELECT COUNT(*) FROM chains WHERE hadith_id=?", (spec["hadith_id"],)
        ).fetchone()[0]
        == 0,
        "alkafi-2862: implicit continuation unexpectedly has a parsed chain",
    )
    public_english = connection.execute(
        """
        SELECT COUNT(*) FROM hadith_translations
        WHERE hadith_id=? AND language='en'
          AND (status IN ('machine_verified','human_reviewed','published') OR risk_level='green')
        """,
        (spec["hadith_id"],),
    ).fetchone()[0]
    require(public_english == 0, "alkafi-2862: public/green English blocks reactivation")
    if apply:
        cursor = connection.execute(
            "UPDATE hadiths SET review_status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (spec["target_review_status"], spec["hadith_id"]),
        )
        require(cursor.rowcount == 1, "alkafi-2862: reactivation update count drift")
        upsert_split_review(
            connection,
            int(spec["hadith_id"]),
            None,
            neighbor["matn_raw"],
            "Approved as the source-attested implicit continuation/report following alkafi-2861; it is not a non-hadith fragment.",
        )


def verify_post_apply(
    connection: sqlite3.Connection,
    direct: list[dict[str, Any]],
    targets: dict[str, dict[str, Any]],
) -> None:
    for entry in direct:
        row = get_hadith(connection, entry["public_id"])
        validate_target(entry, row)
        review = row_dict(
            connection.execute(
                "SELECT * FROM hadith_split_reviews WHERE hadith_id=?",
                (entry["hadith_id"],),
            ).fetchone(),
            f"{entry['public_id']} split review",
        )
        require(
            review["review_status"] == "approved"
            and review["reviewer"] == REVIEWER
            and review["split_version"] == SPLIT_VERSION
            and review["approved_isnad_raw"] == targets[entry["public_id"]]["isnad_raw"]
            and review["approved_matn_raw"] == targets[entry["public_id"]]["matn_raw"],
            f"{entry['public_id']}: split review did not follow repaired boundary",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--apply", action="store_true", help="Commit the 13 deterministic repairs")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--backup-output", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    require(manifest_path.is_file(), f"missing manifest: {manifest_path}")
    manifest_sha = sha256_file(manifest_path)
    manifest = read_json(manifest_path)
    entries = validate_manifest(manifest)
    dossier = validate_dossier(manifest, entries)

    db_path = args.db.resolve()
    require(db_path.is_file() and db_path.stat().st_size > 0, f"missing/non-database DB: {db_path}")
    backup_db = assert_file_pin(manifest["inputs"]["pre_pagebreak_backup"], "pre-pagebreak backup")

    if args.apply:
        require(args.confirm == APPLY_CONFIRMATION, f"--apply requires --confirm {APPLY_CONFIRMATION}")
        require(args.backup_output is not None, "--apply requires --backup-output")
        backup_output = args.backup_output.resolve()
        require(backup_output != db_path, "backup output cannot equal the live DB")
        require(not backup_output.exists(), f"backup output already exists: {backup_output}")
        backup_output.parent.mkdir(parents=True, exist_ok=True)
        create_online_backup(db_path, backup_output)

    connection = connect(db_path, writable=args.apply)
    backup = connect(backup_db, writable=False)
    direct = [entry for entry in entries.values() if entry["bucket"] == "deterministic_repair"]
    policy = [entry for entry in entries.values() if entry["bucket"] == "new_row_policy_required"]
    translation_only = [entry for entry in entries.values() if entry["bucket"] == "translation_only"]

    try:
        quarantined = validate_quarantine(connection, entries, dossier)
        static, api = load_external_sources(manifest, direct)
        validate_sarwar_1151(manifest, translation_only[0])

        for entry in policy + translation_only:
            current = get_hadith(connection, entry["public_id"])
            require(
                sha256_text(current["full_text_raw"]) == entry["current_full_sha256"],
                f"{entry['public_id']}: no-op source row drift",
            )
            require(
                int(current["id"]) == int(entry["hadith_id"]),
                f"{entry['public_id']}: no-op hadith ID drift",
            )

        targets: dict[str, dict[str, Any]] = {}
        already_present: list[str] = []
        needs_update: list[str] = []
        source_state_before: dict[str, str] = {}
        unchanged_chain_before: dict[str, str] = {}
        for entry in direct:
            current, target, already = build_target(connection, backup, entry)
            validate_external_identity(entry, target, static, api)
            targets[entry["public_id"]] = target
            source_state_before[entry["public_id"]] = hadith_source_state_fingerprint(
                current
            )
            (already_present if already else needs_update).append(entry["public_id"])
            if entry["public_id"] != "alkafi-2695":
                require(
                    current["isnad_raw"] == target["isnad_raw"],
                    f"{entry['public_id']}: repair would change isnad without a chain plan",
                )
                unchanged_chain_before[entry["public_id"]] = chain_fingerprint(
                    connection, int(entry["hadith_id"])
                )

        entry_2695 = entries["alkafi-2695"]
        cleanup_already = validate_2695_cleanup_state(connection, entry_2695)
        preserved_nodes = [int(value) for value in entry_2695["chain_cleanup"]["preserve_node_ids"]]
        preserved_2695_before = preserved_2695_fingerprint(connection, preserved_nodes)
        validate_or_apply_neighbor(connection, entries["alkafi-2861"], apply=False)

        if args.apply:
            connection.execute("BEGIN IMMEDIATE")
            # Recheck the publication gate after acquiring the write lock; a
            # concurrent process must not be able to publish English between
            # the initial audit and these Arabic mutations.
            validate_quarantine(connection, entries, dossier)
            for entry in direct:
                require(
                    hadith_source_state_fingerprint(
                        get_hadith(connection, entry["public_id"])
                    )
                    == source_state_before[entry["public_id"]],
                    f"{entry['public_id']}: source row changed before write lock",
                )
            for entry in direct:
                apply_target(connection, entry, targets[entry["public_id"]])
                if entry["public_id"] == "alkafi-2695":
                    apply_2695_cleanup(connection, entry, targets[entry["public_id"]], cleanup_already)
                if entry["public_id"] == "alkafi-2861":
                    validate_or_apply_neighbor(connection, entry, apply=True)

            verify_post_apply(connection, direct, targets)
            require(
                validate_2695_cleanup_state(connection, entry_2695),
                "alkafi-2695: chain cleanup did not reach target state",
            )
            require(
                preserved_2695_fingerprint(connection, preserved_nodes) == preserved_2695_before,
                "alkafi-2695: preserved chain nodes/resolutions changed",
            )
            for entry in direct:
                if entry["public_id"] == "alkafi-2695":
                    continue
                require(
                    chain_fingerprint(connection, int(entry["hadith_id"]))
                    == unchanged_chain_before[entry["public_id"]],
                    f"{entry['public_id']}: chain/resolution data changed",
                )
            validate_quarantine(connection, entries, dossier)
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            require(not foreign_keys, f"foreign-key violations: {foreign_keys[:5]}")
            connection.commit()

        report = {
            "mode": "apply" if args.apply else "dry_run",
            "manifest": str(manifest_path),
            "manifest_sha256": manifest_sha,
            "database": str(db_path),
            "deterministic_repairs": len(direct),
            "source_rows_needing_update": needs_update,
            "source_rows_already_target": already_present,
            "new_row_policy_no_ops": [entry["public_id"] for entry in policy],
            "translation_only_no_ops": [entry["public_id"] for entry in translation_only],
            "quarantined_translation_rows_checked": quarantined,
            "external_human_sources_verified": len(direct) + 1,
            "existing_source_valid_after_repair": [
                entry["public_id"]
                for entry in direct
                if entry["translation"]["valid_after_repair"] is True
            ],
            "replacement_source_required_after_repair": [
                entry["public_id"]
                for entry in direct
                if entry["translation"]["valid_after_repair"] is False
            ],
            "english_written_or_published": 0,
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception:
        if args.apply:
            connection.rollback()
        raise
    finally:
        backup.close()
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepairError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
