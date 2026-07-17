"""Restore validated pre-repair resolutions for unchanged chain-node IDs.

The count reconciliation preserves genuine node IDs but adds/removes a small
number of nodes. A full resolver rebuild currently scores worse than the
validated pre-repair state, so this script restores the validated evidence for
the shared IDs while retaining fresh resolution rows for new IDs.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "eshia_research.db"
BACKUP = ROOT / "eshia_research.before-alkafi-count-reconciliation.20260711-175031.db"

MENTION_COLUMNS = (
    "chain_node_id, person_id, rank, status, method, evidence_json, "
    "evidence_summary, resolver_version, created_at"
)
GENERATION_COLUMNS = (
    "person_id, gen_lo, gen_hi, gen_point, method, evidence_summary, "
    "evidence_json, resolver_version, created_at"
)


def scalar(con: sqlite3.Connection, sql: str) -> int:
    return int(con.execute(sql).fetchone()[0])


def stats(con: sqlite3.Connection) -> dict[str, int]:
    return {
        "shared_nodes": scalar(con, "SELECT count(*) FROM main.chain_nodes m JOIN old.chain_nodes o ON o.id=m.id"),
        "stable_shared_nodes": scalar(con, "SELECT count(*) FROM main.chain_nodes m JOIN old.chain_nodes o ON o.id=m.id AND o.token_normalised=m.token_normalised"),
        "changed_shared_nodes": scalar(con, "SELECT count(*) FROM main.chain_nodes m JOIN old.chain_nodes o ON o.id=m.id WHERE o.token_normalised<>m.token_normalised"),
        "new_nodes": scalar(con, "SELECT count(*) FROM main.chain_nodes m LEFT JOIN old.chain_nodes o ON o.id=m.id WHERE o.id IS NULL"),
        "removed_nodes": scalar(con, "SELECT count(*) FROM old.chain_nodes o LEFT JOIN main.chain_nodes m ON m.id=o.id WHERE m.id IS NULL"),
        "current_mentions": scalar(con, "SELECT count(*) FROM main.mention_resolutions"),
        "restorable_mentions": scalar(con, "SELECT count(*) FROM old.mention_resolutions r JOIN old.chain_nodes o ON o.id=r.chain_node_id JOIN main.chain_nodes n ON n.id=r.chain_node_id AND n.token_normalised=o.token_normalised"),
        "fresh_mentions": scalar(con, "SELECT count(*) FROM main.mention_resolutions r JOIN main.chain_nodes n ON n.id=r.chain_node_id LEFT JOIN old.chain_nodes o ON o.id=n.id AND o.token_normalised=n.token_normalised WHERE o.id IS NULL"),
        "current_generations": scalar(con, "SELECT count(*) FROM main.person_generations"),
        "validated_generations": scalar(con, "SELECT count(*) FROM old.person_generations"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--main", type=Path, default=MAIN)
    parser.add_argument("--backup", type=Path, default=BACKUP)
    args = parser.parse_args()

    main_path = args.main.resolve()
    backup_path = args.backup.resolve()
    if not main_path.is_file() or not backup_path.is_file():
        raise RuntimeError("main database or recorded backup is missing")
    if main_path == backup_path:
        raise RuntimeError("main database and backup must be different files")
    con = sqlite3.connect(main_path)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("ATTACH DATABASE ? AS old", (str(backup_path),))
        before = stats(con)
        print("BEFORE", before)
        if not args.apply:
            print("DRY RUN: shared-node resolutions and validated person generations would be restored.")
            return

        con.execute("BEGIN IMMEDIATE")
        con.execute(
            "DELETE FROM main.mention_resolutions "
            "WHERE chain_node_id IN ("
            "SELECT m.id FROM main.chain_nodes m JOIN old.chain_nodes o "
            "ON o.id=m.id AND o.token_normalised=m.token_normalised)"
        )
        con.execute(
            f"INSERT INTO main.mention_resolutions ({MENTION_COLUMNS}) "
            f"SELECT {MENTION_COLUMNS} FROM old.mention_resolutions r "
            "JOIN old.chain_nodes o ON o.id=r.chain_node_id "
            "JOIN main.chain_nodes n ON n.id=r.chain_node_id "
            "AND n.token_normalised=o.token_normalised"
        )
        con.execute("DELETE FROM main.person_generations")
        con.execute(
            f"INSERT INTO main.person_generations ({GENERATION_COLUMNS}) "
            f"SELECT {GENERATION_COLUMNS} FROM old.person_generations"
        )

        orphan_mentions = scalar(
            con,
            "SELECT count(*) FROM main.mention_resolutions r "
            "LEFT JOIN main.chain_nodes n ON n.id=r.chain_node_id WHERE n.id IS NULL",
        )
        if orphan_mentions:
            raise RuntimeError(f"restore produced {orphan_mentions} orphan mention rows")
        expected_mentions = before["restorable_mentions"] + before["fresh_mentions"]
        actual_mentions = scalar(con, "SELECT count(*) FROM main.mention_resolutions")
        if actual_mentions != expected_mentions:
            raise RuntimeError(f"mention count {actual_mentions} != expected {expected_mentions}")
        if scalar(con, "SELECT count(*) FROM main.person_generations") != before["validated_generations"]:
            raise RuntimeError("person-generation restore count mismatch")
        con.commit()
        print("AFTER", stats(con))
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
