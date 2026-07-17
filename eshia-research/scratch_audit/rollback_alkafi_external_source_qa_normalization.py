"""Restore pre-normalization QA metadata from the recorded SQLite backup."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


EXPECTED_ROWS = 7176
VERSION = "alkafi_external_source_qa_normalization_v1"
DEFAULT_BACKUP = Path(
    "eshia_research.before-external-source-finalization.20260716-130630.db"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    parser.add_argument("--db", type=Path, default=Path("eshia_research.db"))
    args = parser.parse_args()

    db_path = args.db.resolve()
    backup_path = args.backup.resolve()
    if not db_path.exists() or not backup_path.exists():
        raise RuntimeError("Main database or recorded backup is missing")

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("ATTACH DATABASE ? AS before_db", (str(backup_path),))
        translation_ids = [
            row[0]
            for row in connection.execute(
                """
                SELECT id
                FROM hadith_translations
                WHERE json_extract(provenance_json, '$.qa_flag_normalization.version') = ?
                ORDER BY id
                """,
                (VERSION,),
            )
        ]
        segment_ids = [
            row[0]
            for row in connection.execute(
                """
                SELECT id
                FROM translation_segments
                WHERE json_extract(metadata_json, '$.qa_flag_normalization.version') = ?
                ORDER BY id
                """,
                (VERSION,),
            )
        ]
        if len(translation_ids) not in {0, EXPECTED_ROWS}:
            raise RuntimeError(
                f"Unexpected normalized translation count: {len(translation_ids)}"
            )
        if len(segment_ids) not in {0, EXPECTED_ROWS}:
            raise RuntimeError(f"Unexpected normalized segment count: {len(segment_ids)}")

        missing_translation_backups = connection.execute(
            """
            SELECT count(*)
            FROM hadith_translations current
            LEFT JOIN before_db.hadith_translations old ON old.id = current.id
            WHERE json_extract(current.provenance_json, '$.qa_flag_normalization.version') = ?
              AND old.id IS NULL
            """,
            (VERSION,),
        ).fetchone()[0]
        missing_segment_backups = connection.execute(
            """
            SELECT count(*)
            FROM translation_segments current
            LEFT JOIN before_db.translation_segments old ON old.id = current.id
            WHERE json_extract(current.metadata_json, '$.qa_flag_normalization.version') = ?
              AND old.id IS NULL
            """,
            (VERSION,),
        ).fetchone()[0]
        if missing_translation_backups or missing_segment_backups:
            raise RuntimeError("Backup does not contain every normalization target")

        summary = {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "translation_rows": len(translation_ids),
            "segment_rows": len(segment_ids),
            "restored_columns": {
                "hadith_translations": [
                    "risk_flags",
                    "provenance_json",
                    "qa_version",
                    "updated_at",
                ],
                "translation_segments": [
                    "risk_flags",
                    "metadata_json",
                    "updated_at",
                ],
            },
            "text_columns_changed": 0,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not args.apply or not translation_ids:
            connection.rollback()
            return

        connection.execute(
            """
            UPDATE hadith_translations AS current
            SET risk_flags = (SELECT old.risk_flags FROM before_db.hadith_translations old WHERE old.id = current.id),
                provenance_json = (SELECT old.provenance_json FROM before_db.hadith_translations old WHERE old.id = current.id),
                qa_version = (SELECT old.qa_version FROM before_db.hadith_translations old WHERE old.id = current.id),
                updated_at = (SELECT old.updated_at FROM before_db.hadith_translations old WHERE old.id = current.id)
            WHERE json_extract(current.provenance_json, '$.qa_flag_normalization.version') = ?
            """,
            (VERSION,),
        )
        connection.execute(
            """
            UPDATE translation_segments AS current
            SET risk_flags = (SELECT old.risk_flags FROM before_db.translation_segments old WHERE old.id = current.id),
                metadata_json = (SELECT old.metadata_json FROM before_db.translation_segments old WHERE old.id = current.id),
                updated_at = (SELECT old.updated_at FROM before_db.translation_segments old WHERE old.id = current.id)
            WHERE json_extract(current.metadata_json, '$.qa_flag_normalization.version') = ?
            """,
            (VERSION,),
        )
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
