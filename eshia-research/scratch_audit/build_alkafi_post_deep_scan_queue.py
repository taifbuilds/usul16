"""Create the reason-coded queue after the Al-Kafi deep-scan recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_importer import match_norm


PUBLIC = {"machine_verified", "human_reviewed", "published"}
CONTENT_MISMATCH = {"alkafi-2782"}


def is_public(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def reason(hadith: Hadith, audit: dict | None) -> tuple[str, str]:
    if hadith.volume_start == 8:
        return "no_verified_sarwar_volume8", "Only HubeAli-derived or attribution-uncertain English was found."
    if audit is None:
        return "no_api_candidate", "No candidate exists in the cached full-corpus API scan."
    english = str(audit.get("english") or "")
    lowered = english.casefold()
    local_chars = len(match_norm(audit["local_arabic"]))
    remote_chars = len(match_norm(audit["remote_arabic"]))
    extent_ratio = remote_chars / max(1, local_chars)
    score = float(audit["best_score"])
    margin = float(audit["margin"])
    if score >= 0.82 and margin >= 0.03:
        if hadith.public_id in CONTENT_MISMATCH:
            return "english_arabic_content_mismatch", "High Arabic identity but the attached English describes another report."
        if any(phrase in lowered for phrase in ("not translated", "not a hadith", "fatwah best explains")):
            return "source_explicitly_not_translated", "The source explicitly declines or substitutes for a translation."
        if any(marker in lowered for marker in ("hubeali.com", "(azwj)", "(saww)", "(asws)")):
            return "source_purity_rejected", "The candidate uses HubeAli source conventions."
        if not 0.75 <= extent_ratio <= 1.35:
            return "edition_split_or_merge", "Strong Arabic overlap but local and source report extents differ materially."
    if score < 0.50 or margin < 0.02:
        return "no_reliable_alignment", "Arabic similarity or runner-up separation is insufficient."
    return "ambiguous_alignment", "A possible candidate exists but does not meet the reviewed publication threshold."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("api_audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit = {
        row["public_id"]: row
        for row in json.loads(args.api_audit.read_text(encoding="utf-8"))
    }
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
        translations = {
            row.hadith_id: row
            for row in db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        }
        missing = [row for row in hadiths if not is_public(translations.get(row.id), row)]
        if len(missing) != 124:
            raise RuntimeError(f"Expected 124 remaining reports; found {len(missing)}")
        records = []
        for hadith in missing:
            candidate = audit.get(hadith.public_id)
            code, detail = reason(hadith, candidate)
            records.append(
                {
                    "public_id": hadith.public_id,
                    "sequence": hadith.sequence_in_book,
                    "volume": hadith.volume_start,
                    "page_start": hadith.page_start,
                    "printed_number": hadith.printed_number,
                    "source_url": hadith.source_url,
                    "reason": code,
                    "detail": detail,
                    "best_candidate": None
                    if candidate is None
                    else {
                        "remote_id": candidate["best_id"],
                        "score": candidate["best_score"],
                        "margin": candidate["margin"],
                        "source_url": candidate["url"],
                    },
                }
            )
    counts: dict[str, int] = {}
    volumes: dict[str, int] = {}
    for record in records:
        counts[record["reason"]] = counts.get(record["reason"], 0) + 1
        volume = str(record["volume"])
        volumes[volume] = volumes.get(volume, 0) + 1
    summary = {"remaining": len(records), "reasons": counts, "by_volume": volumes}
    args.output.write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
