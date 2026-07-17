"""Build the manually reviewed recovery manifest from the remaining-150 scan."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_importer import strip_html_text


PUBLIC = {"machine_verified", "human_reviewed", "published"}
FORBIDDEN = ("hubeali.com", "(azwj)", "(saww)", "(asws)")

# These source records were reviewed Arabic-to-Arabic and English-to-content.
FULL_SOURCE_IDS = {
    "alkafi-1153", "alkafi-1241", "alkafi-1275", "alkafi-1282",
    "alkafi-1292", "alkafi-1325", "alkafi-1399", "alkafi-1417",
    "alkafi-2695", "alkafi-6143", "alkafi-6959", "alkafi-8124",
    "alkafi-8963", "alkafi-9068", "alkafi-9383", "alkafi-9558",
    "alkafi-11999", "alkafi-14527",
}


def is_public(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def editorial_text(public_id: str, source_english: str) -> tuple[str, list[str]]:
    """Return the bounded/corrected text and the explicit editorial operations."""
    if public_id == "alkafi-1282":
        return (
            source_english.replace("fifty bsix", "sixty-five").replace(
                "forty three years", "thirty-four years"
            ),
            ["corrected two obvious number/typographical errors against the Arabic"],
        )
    if public_id == "alkafi-1292":
        return (
            source_english.replace("fifty five", "fifty-four"),
            ["corrected the stated age against the Arabic"],
        )
    if public_id == "alkafi-11999":
        return (
            "Figs remove bad breath (halitosis), strengthen the mouth and bones, "
            "promote hair growth, dispel illness, and with figs no medicine is needed. "
            "He (the Imam) said, ‘The fig most closely resembles the plants of Paradise.’ "
            "Sahl ibn Ziyad has narrated from Ahmad ibn al-Ash‘ath from Ahmad ibn "
            "Muhammad ibn Abu Nasr a similar report.",
            ["corrected OCR/source typos and removed stray footnote numerals"],
        )
    return source_english, []


def bounded_editorial(public_id: str, source: str) -> tuple[str, list[str], list[str]]:
    if public_id == "alkafi-1160":
        text = source.split(" Al-Husayn ibn Muhammad", 1)[0]
        return text, ["bounded the concatenated upstream English field at the next chain"], []
    if public_id == "alkafi-10724":
        text = (
            "I heard Abu Ja‘far (a.s.) say regarding a woman who has reached menopause, "
            "‘She is separated from him and no waiting period is required of her.’ It has "
            "also been narrated that a waiting period is required if the marriage was "
            "consummated. " + source
        )
        return text, ["supplied the omitted opening report directly from the Arabic", "retained Sarwar for the remaining passage"], []
    if public_id == "alkafi-11166":
        return (
            "I once asked Abu Ja‘far (a.s.) about a coerced person’s emancipation of a "
            "slave. He said, ‘The emancipation is not valid.’",
            ["scoped the longer parallel Sarwar report to the local Arabic excerpt"],
            [],
        )
    if public_id == "alkafi-11167":
        return (
            "I asked Abu ‘Abd Allah (a.s.) whether the sale or charitable disposal of the "
            "property of a mentally incapacitated woman who had lost her reason is valid. "
            "He said, ‘No.’ I also asked about the divorce and emancipation of a drunken "
            "person. He said, ‘They are not valid.’",
            ["composed two source-aligned clauses because the local edition combines them"],
            ["https://thaqalayn.net/hadith/1/2/53/4"],
        )
    if public_id == "alkafi-11168":
        return (
            "Abu Ja‘far and Abu ‘Abd Allah (a.s.) have said, ‘The emancipation of a slave "
            "by al-Muwallah (a confused, excited or awestruck person) is not valid.’",
            ["scoped the parallel Sarwar report to the local emancipation clause"],
            [],
        )
    if public_id == "alkafi-11169":
        return (
            "Abu ‘Abd Allah (a.s.) said, ‘The emancipation of a slave by a drunken person "
            "is not valid.’",
            ["scoped the parallel Sarwar report to the local emancipation clause"],
            [],
        )
    if public_id == "alkafi-11277":
        return (
            "I asked al-Rida (a.s.) about approaching birds in their nests at night. He "
            "said, ‘It is not unlawful.’ Ahmad ibn Muhammad ibn ‘Isa has narrated from "
            "Ali ibn Ahmad ibn Ashyam from Safwan ibn Yahya from Abu al-Hassan al-Rida "
            "(a.s.) a similar report.",
            ["restored the question omitted from the upstream English field"],
            [],
        )
    if public_id == "alkafi-12739":
        return (
            "Abu ‘Abd Allah (a.s.) said, ‘A man must not enter a bathhouse with his son "
            "where he can look at his private parts.’",
            ["scoped the longer parallel Sarwar report to the local Arabic excerpt"],
            [],
        )
    raise KeyError(public_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("api_audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit = {
        row["public_id"]: row
        for row in json.loads(args.api_audit.read_text(encoding="utf-8"))
    }
    bounded_ids = {
        "alkafi-1160", "alkafi-10724", "alkafi-11166", "alkafi-11167",
        "alkafi-11168", "alkafi-11169", "alkafi-11277", "alkafi-12739",
    }
    selected_ids = FULL_SOURCE_IDS | bounded_ids
    if len(selected_ids) != 26:
        raise RuntimeError(f"Expected 26 reviewed selections; found {len(selected_ids)}")

    with SessionLocal() as db:
        book = db.execute(select(Book).where(Book.source_book_id == "11005")).scalar_one()
        hadiths = list(
            db.execute(
                select(Hadith).where(
                    Hadith.book_id == book.id,
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
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
        if len(missing) != 150:
            raise RuntimeError(f"Expected 150 missing after correction; found {len(missing)}")
        missing_by_id = {row.public_id: row for row in missing}
        if not selected_ids <= missing_by_id.keys():
            raise RuntimeError("A reviewed selection is no longer in the missing set")

        records = []
        for public_id in sorted(selected_ids, key=lambda value: missing_by_id[value].sequence_in_book):
            hadith = missing_by_id[public_id]
            source = audit[public_id]
            source_english = strip_html_text(source["english"])
            if public_id in bounded_ids:
                english, operations, additional_urls = bounded_editorial(public_id, source_english)
                provider = "usul16-source-aligned-editorial"
                model = "muhammad-sarwar-scoped-editorial"
            else:
                english, operations = editorial_text(public_id, source_english)
                additional_urls = []
                provider = "thaqalayn-api"
                model = "muhammad-sarwar" if not operations else "muhammad-sarwar-editorially-corrected"
            english = clean_ws(english)
            lowered = english.casefold()
            forbidden = [marker for marker in FORBIDDEN if marker in lowered]
            if forbidden:
                raise RuntimeError(f"Forbidden source marker for {public_id}: {forbidden}")
            qa = assess_translation(hadith.matn_raw, english)
            records.append(
                {
                    "public_id": public_id,
                    "sequence": hadith.sequence_in_book,
                    "volume": hadith.volume_start,
                    "arabic": hadith.full_text_raw,
                    "matn": hadith.matn_raw,
                    "source_full_sha256": sha256_text(hadith.full_text_raw),
                    "source_matn_sha256": sha256_text(hadith.matn_raw),
                    "english": english,
                    "provider": provider,
                    "model": model,
                    "source_url": source["url"],
                    "additional_source_urls": additional_urls,
                    "remote_id": source["best_id"],
                    "remote_arabic": source["remote_arabic"],
                    "arabic_match_score": source["best_score"],
                    "runner_up_margin": source["margin"],
                    "editorial_operations": operations,
                    "original_source_english": source_english if operations else None,
                    "qa_risk": qa.risk_level,
                    "qa_flags": [asdict(flag) for flag in qa.flags],
                    "review_basis": "manual Arabic extent and English content review",
                }
            )

    summary = {
        "baseline_missing": 150,
        "selected": len(records),
        "verbatim_or_html_cleaned_sarwar": sum(not row["editorial_operations"] for row in records),
        "editorially_corrected_or_scoped": sum(bool(row["editorial_operations"]) for row in records),
        "by_volume": {
            str(volume): sum(row["volume"] == volume for row in records)
            for volume in range(1, 9)
        },
    }
    args.output.write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
