"""Audit untranslated Al-Kafi reports against the human ThaqalaynData corpus.

This is deliberately read-only.  It records the sequential matcher outcome and
the strongest volume-wide Arabic candidates so the completion pass can be
reviewed before any database mutation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.thaqalayn_importer import (
    match_norm,
    match_score_parts,
    match_words,
    static_records_from_rows,
)
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text


PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cache", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    remote_by_volume = static_records_from_rows(
        json.loads(args.cache.read_text(encoding="utf-8"))
    )
    with SessionLocal() as db:
        book = db.execute(select(Book).where(Book.source_book_id == "11005")).scalar_one()
        hadiths = list(
            db.execute(
                select(Hadith)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
                .order_by(Hadith.sequence_in_book)
            ).scalars()
        )
        translations = list(
            db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        )
        hadith_by_id = {hadith.id: hadith for hadith in hadiths}
        current = {
            row.hadith_id
            for row in translations
            if row.hadith_id in hadith_by_id
            and row.status in PUBLIC_STATUSES
            and row.risk_level == "green"
            and clean_ws(row.matn_translation)
            and row.source_full_sha256
            == sha256_text(hadith_by_id[row.hadith_id].full_text_raw)
        }
        translation_by_hadith = {row.hadith_id: row for row in translations}
        static_owner: dict[tuple[int, int], str] = {}
        for translation in translations:
            if translation.provider != "thaqalayn-data" or not translation.provenance_json:
                continue
            volume = translation.provenance_json.get("volume")
            remote_id = translation.provenance_json.get("thaqalayn_id")
            hadith = hadith_by_id.get(translation.hadith_id)
            if volume and remote_id and hadith:
                static_owner[(int(volume), int(remote_id))] = hadith.public_id
        missing = [hadith for hadith in hadiths if hadith.id not in current]
        rows: list[dict[str, object]] = []
        local_index = {hadith.id: index for index, hadith in enumerate(hadiths)}
        for hadith in missing:
            local_full = match_norm(hadith.full_text_raw)
            local_matn = match_norm(hadith.matn_raw)
            local_full_words = match_words(hadith.full_text_raw)
            local_matn_words = match_words(hadith.matn_raw)
            candidates = sorted(
                (
                    (
                        match_score_parts(
                            local_full=local_full,
                            local_matn=local_matn,
                            local_full_words=local_full_words,
                            local_matn_words=local_matn_words,
                            remote=remote,
                        ),
                        remote,
                    )
                    for remote in remote_by_volume.get(hadith.volume_start or 0, [])
                ),
                key=lambda item: item[0],
                reverse=True,
            )[:8]
            index = local_index[hadith.id]
            before = next(
                (row for row in reversed(hadiths[:index]) if row.id in current), None
            )
            after = next((row for row in hadiths[index + 1 :] if row.id in current), None)

            def neighbor_payload(row: Hadith | None) -> dict[str, object] | None:
                if row is None:
                    return None
                translation = translation_by_hadith[row.id]
                provenance = translation.provenance_json or {}
                return {
                    "public_id": row.public_id,
                    "sequence": row.sequence_in_book,
                    "provider": translation.provider,
                    "remote_id": provenance.get("thaqalayn_id"),
                    "source_url": provenance.get("source_url"),
                }

            rows.append(
                {
                    "public_id": hadith.public_id,
                    "sequence": hadith.sequence_in_book,
                    "volume": hadith.volume_start,
                    "page_start": hadith.page_start,
                    "page_end": hadith.page_end,
                    "printed_number": hadith.printed_number,
                    "source_url": hadith.source_url,
                    "arabic": hadith.full_text_raw,
                    "matn": hadith.matn_raw,
                    "previous_current": neighbor_payload(before),
                    "next_current": neighbor_payload(after),
                    "top_candidates": [
                        {
                            "remote_id": remote.id,
                            "score": score,
                            "arabic_norm_length": len(remote.match_norm),
                            "arabic_word_count": len(remote.match_words),
                            "used_by_current_static": static_owner.get(
                                (hadith.volume_start or 0, remote.id)
                            ),
                            "qa_risk_level": assess_translation(
                                hadith.matn_raw, remote.usable_translation
                            ).risk_level,
                            "qa_flags": [
                                flag.__dict__
                                for flag in assess_translation(
                                    hadith.matn_raw, remote.usable_translation
                                ).flags
                            ],
                            "translator": remote.translator,
                            "source_url": remote.url,
                            "arabic": remote.arabic_text,
                            "english": remote.usable_translation,
                        }
                        for score, remote in candidates
                    ],
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"missing={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
