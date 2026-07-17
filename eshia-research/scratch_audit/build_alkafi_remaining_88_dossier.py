"""Build an Arabic-first forensic dossier for the remaining 88 Al-Kafi rows."""

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
from eshia_research.translation.thaqalayn_importer import (
    IMPORT_BLOCKING_QA_CODES,
    build_matches,
    match_norm,
    match_score_parts,
    match_words,
    static_records_from_rows,
)


PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
FORBIDDEN = ("hubeali.com", "(azwj)", "(saww)", "(asws)")
NON_TRANSLATIONS = (
    "not a hadith",
    "not translated",
    "fatwah best explains",
)


def public_translation(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC_STATUSES
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def source_assessment(matn: str, english: str) -> dict[str, object]:
    english = clean_ws(english)
    qa = assess_translation(matn, english) if english else None
    flags = [] if qa is None else [asdict(flag) for flag in qa.flags]
    blocking = [
        flag["code"] for flag in flags if flag["code"] in IMPORT_BLOCKING_QA_CODES
    ]
    lowered = english.casefold()
    purity = [marker for marker in FORBIDDEN if marker in lowered]
    non_translation = [phrase for phrase in NON_TRANSLATIONS if phrase in lowered]
    return {
        "english": english or None,
        "english_chars": len(english),
        "qa_risk": None if qa is None else qa.risk_level,
        "qa_flags": flags,
        "blocking_qa": blocking,
        "forbidden_markers": purity,
        "non_translation_markers": non_translation,
        "clean_candidate": bool(english and not blocking and not purity and not non_translation),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("static_cache", type=Path)
    parser.add_argument("prior_dossier", type=Path)
    parser.add_argument("api_audit", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pdf-records", type=Path, action="append", required=True)
    args = parser.parse_args()

    static_rows = json.loads(args.static_cache.read_text(encoding="utf-8"))
    remote_by_volume = static_records_from_rows(static_rows)
    remote_by_key = {
        (remote.volume, remote.id): remote
        for rows in remote_by_volume.values()
        for remote in rows
    }
    pdf_by_h: dict[int, dict[str, object]] = {}
    pdf_manifests: list[dict[str, object]] = []
    for path in args.pdf_records:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pdf_manifests.extend(payload["manifest"])
        for record in payload["records"]:
            if record.get("hadith_suffix"):
                continue
            number = int(record["hadith_number"])
            # First file wins, allowing high-resolution v1-4 and the previously
            # reviewed high-resolution v5-7 set to be supplied in priority order.
            pdf_by_h.setdefault(number, record)

    prior_payload = json.loads(args.prior_dossier.read_text(encoding="utf-8"))
    prior = {record["public_id"]: record for record in prior_payload["records"]}
    deferred = set(prior_payload["summary"]["deferred_strong_cases"])
    api_audit = {
        record["public_id"]: record
        for record in json.loads(args.api_audit.read_text(encoding="utf-8"))
        if record.get("public_id") in deferred
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
        missing = [
            row for row in hadiths if not public_translation(translations.get(row.id), row)
        ]
        if len(missing) != 88:
            raise RuntimeError(f"Expected 88 missing visible reports; found {len(missing)}")

        direct_matches, direct_stats = build_matches(
            db, source_book_id="11005", remote_by_volume=remote_by_volume
        )
        direct = {match.public_id: match for match in direct_matches}
        index = {row.public_id: position for position, row in enumerate(hadiths)}

        records: list[dict[str, object]] = []
        for row in missing:
            position = index[row.public_id]
            direct_match = direct.get(row.public_id)
            identity: dict[str, object] | None = None
            remote = None
            if direct_match:
                remote = remote_by_key[(direct_match.volume, direct_match.thaqalayn_id)]
                identity = {
                    "method": "direct_arabic_match",
                    "remote_id": direct_match.thaqalayn_id,
                    "score": direct_match.score,
                    "matcher_version": direct_match.matcher_version,
                }
            elif row.public_id in prior and prior[row.public_id].get("identity"):
                identity = prior[row.public_id]["identity"]
                remote_id = int(identity["remote_id"])
                remote = remote_by_key.get((row.volume_start or 0, remote_id))

            previous = next(
                (
                    direct[hadiths[i].public_id]
                    for i in range(position - 1, -1, -1)
                    if hadiths[i].volume_start == row.volume_start
                    and hadiths[i].public_id in direct
                ),
                None,
            )
            following = next(
                (
                    direct[hadiths[i].public_id]
                    for i in range(position + 1, len(hadiths))
                    if hadiths[i].volume_start == row.volume_start
                    and hadiths[i].public_id in direct
                ),
                None,
            )
            anchor_context = {
                "previous": None
                if previous is None
                else {
                    "public_id": previous.public_id,
                    "remote_id": previous.thaqalayn_id,
                    "score": previous.score,
                    "local_distance": position - index[previous.public_id],
                },
                "next": None
                if following is None
                else {
                    "public_id": following.public_id,
                    "remote_id": following.thaqalayn_id,
                    "score": following.score,
                    "local_distance": index[following.public_id] - position,
                },
            }

            local_full = match_norm(row.full_text_raw)
            local_matn = match_norm(row.matn_raw)
            local_full_words = match_words(row.full_text_raw)
            local_matn_words = match_words(row.matn_raw)
            nearby = [
                candidate
                for candidate in remote_by_volume[row.volume_start or 0]
                if abs(candidate.id - row.sequence_in_book) <= 80
            ]
            ranked = sorted(
                (
                    (
                        match_score_parts(
                            local_full=local_full,
                            local_matn=local_matn,
                            local_full_words=local_full_words,
                            local_matn_words=local_matn_words,
                            remote=candidate,
                        ),
                        candidate,
                    )
                    for candidate in nearby
                ),
                key=lambda item: item[0],
                reverse=True,
            )[:5]
            ranked_payload = [
                {
                    "remote_id": candidate.id,
                    "score": score,
                    "translator": candidate.translator,
                    "source_url": candidate.url,
                    "arabic_chars": len(candidate.match_norm),
                    "has_published_pdf_record": candidate.id in pdf_by_h,
                }
                for score, candidate in ranked
            ]

            sources: list[dict[str, object]] = []
            if remote is not None and remote.translator == "Muhammad Sarwar":
                sources.append(
                    {
                        "kind": "thaqalayn_static_sarwar",
                        "remote_id": remote.id,
                        "source_url": remote.url,
                        **source_assessment(row.matn_raw, remote.usable_translation),
                    }
                )
            if remote is not None and remote.id in pdf_by_h:
                pdf = pdf_by_h[remote.id]
                sources.append(
                    {
                        "kind": "published_sarwar_pdf",
                        "remote_id": remote.id,
                        "physical_volume": pdf["physical_volume"],
                        "pdf_page": pdf["pdf_page"],
                        "source_url": pdf["source_url"],
                        "source_sha256": pdf["source_sha256"],
                        "marker": pdf["marker"],
                        **source_assessment(row.matn_raw, str(pdf["english"])),
                    }
                )
            if row.public_id in api_audit:
                audit = api_audit[row.public_id]
                sources.append(
                    {
                        "kind": "thaqalayn_api_sarwar_candidate",
                        "remote_id": audit["best_id"],
                        "source_url": audit["url"],
                        "arabic_score": audit["best_score"],
                        "runner_up_margin": audit["margin"],
                        "remote_arabic": audit["remote_arabic"],
                        **source_assessment(row.matn_raw, audit["english"]),
                    }
                )

            clean_sources = [source for source in sources if source["clean_candidate"]]
            if identity and clean_sources:
                decision = "review_candidate"
            elif identity:
                decision = "identified_but_no_clean_source"
            elif ranked and ranked[0][0] >= 0.75:
                decision = "ambiguous_similarity_candidate"
            else:
                decision = "unresolved_no_identity"

            records.append(
                {
                    "public_id": row.public_id,
                    "sequence": row.sequence_in_book,
                    "volume": row.volume_start,
                    "page_start": row.page_start,
                    "page_end": row.page_end,
                    "printed_number": row.printed_number,
                    "source_url": row.source_url,
                    "arabic": row.full_text_raw,
                    "matn": row.matn_raw,
                    "prior_bucket": "deferred" if row.public_id in deferred else prior[row.public_id]["decision"],
                    "identity": identity,
                    "anchor_context": anchor_context,
                    "ranked_nearby": ranked_payload,
                    "sources": sources,
                    "decision": decision,
                }
            )

    decisions: dict[str, int] = {}
    volumes: dict[str, int] = {}
    for record in records:
        decisions[record["decision"]] = decisions.get(record["decision"], 0) + 1
        volume = str(record["volume"])
        volumes[volume] = volumes.get(volume, 0) + 1
    summary = {
        "target": len(records),
        "direct_static_matches_all_visible": direct_stats.matched,
        "decisions": decisions,
        "by_volume": volumes,
        "pdf_manifests": pdf_manifests,
    }
    args.output.write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
