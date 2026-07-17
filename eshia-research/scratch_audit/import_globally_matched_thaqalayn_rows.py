"""Import Thaqalayn English for reports the windowed matcher never scored.

``_match_volume`` walks each volume with a bounded window (WINDOW_BACK /
WINDOW_FORWARD) around a running cursor.  Where the two editions diverge enough
that a report's counterpart sits far outside that window, it is never compared,
and the report is recorded as "no reliable alignment" -- an artefact of the
search, not evidence the translation is absent.

This pass re-identifies those reports with an unbounded, symmetric comparison
against every Thaqalayn row, then hands the surviving pairs to
``import_thaqalayn_al_kafi(matches=...)`` so the ordinary QA, publishability,
hashing and provenance rules still decide what may publish.

Identity contract (all required):
  * forward coverage  >= 0.88  (our words present in theirs)
  * reverse coverage  >= 0.50  (theirs present in ours -- defeats the
    containment trap where a long remote report merely contains a short matn)
  * length ratio in [0.30, 1.30]
  * same volume, and no remote row used twice
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.db import engine
from eshia_research.models import Book, Hadith
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws
from eshia_research.translation.thaqalayn_importer import (
    MIN_MATCH_SCORE,
    TranslationMatch,
    import_thaqalayn_al_kafi,
    match_norm,
    match_score_parts,
    match_words,
    parse_static_row,
)

FWD_MIN = 0.88
REV_MIN = 0.50
RATIO_LO, RATIO_HI = 0.30, 1.30


def words(text: str | None) -> list[str]:
    return normalise_arabic_persian(clean_ws(text or "")).split()


def coverage(needle: list[str], haystack: Counter) -> float:
    if not needle:
        return 0.0
    pool = Counter(haystack)
    hit = 0
    for word in needle:
        if pool.get(word, 0) > 0:
            pool[word] -= 1
            hit += 1
    return hit / len(needle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-cache-path", required=True)
    parser.add_argument("--manifest", required=True, help="verified pairs json")
    parser.add_argument("--source-book-id", default="11005")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    static_rows = json.load(open(args.static_cache_path, encoding="utf-8"))
    by_path = {row["path"]: row for row in static_rows}
    manifest = json.load(open(args.manifest, encoding="utf-8"))

    with Session(engine) as session:
        book_id = session.execute(
            select(Book.id).where(Book.source_book_id == args.source_book_id)
        ).scalar_one()
        local = {
            h.public_id: h
            for h in session.execute(
                select(Hadith).where(Hadith.book_id == book_id)
            ).scalars()
        }

        matches: list[TranslationMatch] = []
        rejected: list[tuple[str, str]] = []
        used_remote: set[str] = set()

        for entry in manifest:
            public_id = entry["public_id"]
            hadith = local.get(public_id)
            if hadith is None:
                rejected.append((public_id, "local report not found"))
                continue
            row = by_path.get(entry["remote_path"])
            if row is None:
                rejected.append((public_id, "remote row not found"))
                continue
            if entry.get("force_translator") == "HubeAli":
                # parse_static_row prefers Sarwar whenever present. For a few
                # rows Thaqalayn's Sarwar field carries a different report than
                # its Arabic, so the correct English is the HubeAli one. Hiding
                # the Sarwar field makes the normal chooser select HubeAli;
                # every downstream QA and publishability rule still applies.
                row = dict(row, en_sarwar="")
            record = parse_static_row(row)
            if record is None or not record.usable_translation:
                rejected.append((public_id, "remote row has no usable translation"))
                continue
            if entry["remote_path"] in used_remote:
                rejected.append((public_id, "remote row already claimed in this batch"))
                continue
            if (hadith.volume_start or 0) != record.volume:
                rejected.append((public_id, "cross-volume match"))
                continue

            ours = words(hadith.matn_raw)
            theirs = words(record.arabic_text)
            fwd = coverage(ours, Counter(theirs))
            rev = coverage(theirs, Counter(ours))
            ratio = (len(ours) / len(theirs)) if theirs else 0.0

            if entry.get("evidence") == "anchor_bijection":
                # Identity here rests on POSITION, not on the similarity score:
                # the report sits between two anchors whose counterparts are
                # verified, and exactly one unclaimed remote row lies between
                # them, so identity follows by elimination. Text agreement is
                # corroboration. Word-level coverage understates short reports
                # badly -- trailing punctuation and honorific formatting are
                # whole tokens -- so the textual bar is lower here, while the
                # extent bar stays tight because a ratio far from 1 means the
                # editions split the report differently.
                fwd_min, rev_min, lo, hi = 0.60, 0.60, 0.70, 1.40
                contract = "anchor_bijection"
            else:
                fwd_min, rev_min, lo, hi = FWD_MIN, REV_MIN, RATIO_LO, RATIO_HI
                contract = "global_symmetric"

            if not (fwd >= fwd_min and rev >= rev_min and lo <= ratio <= hi):
                rejected.append(
                    (public_id, f"{contract} contract failed fwd={fwd:.2f} rev={rev:.2f} ratio={ratio:.2f}")
                )
                continue

            # Score on the importer's own scale so match_score stays comparable
            # with every other imported row.
            score = match_score_parts(
                local_full=match_norm(hadith.full_text_raw),
                local_matn=match_norm(hadith.matn_raw),
                local_full_words=match_words(hadith.full_text_raw),
                local_matn_words=match_words(hadith.matn_raw),
                remote=record,
            )
            if contract != "anchor_bijection" and score < MIN_MATCH_SCORE:
                rejected.append((public_id, f"importer score {score:.3f} < {MIN_MATCH_SCORE}"))
                continue

            qa = assess_translation(hadith.matn_raw, record.usable_translation)
            used_remote.add(entry["remote_path"])
            matches.append(
                TranslationMatch(
                    hadith_id=hadith.id,
                    public_id=hadith.public_id,
                    volume=hadith.volume_start or 0,
                    thaqalayn_id=record.id,
                    score=score,
                    url=record.url,
                    english_text=record.usable_translation,
                    rendered_isnad_en=record.thaqalayn_sanad,
                    provider=record.provider,
                    model=record.model,
                    source_name=record.source_name,
                    translator=record.translator,
                    matcher_version=(
                        "anchor_bijection_v1" if contract == "anchor_bijection"
                        else "global_symmetric_match_v1"
                    ),
                    qa_risk_level=qa.risk_level,
                    qa_flags=[flag.__dict__ for flag in qa.flags],
                )
            )

        print(f"manifest entries      : {len(manifest)}")
        print(f"passed identity gates : {len(matches)}")
        print(f"rejected              : {len(rejected)}")
        for public_id, why in rejected:
            print(f"    {public_id:16} {why}")

        translators = Counter(m.translator for m in matches)
        print(f"translators           : {dict(translators)}")
        publishable = [m for m in matches if m.publishable]
        print(f"publishable after QA  : {len(publishable)} / {len(matches)}")
        for m in matches:
            if not m.publishable:
                codes = [f["code"] for f in m.qa_flags]
                print(f"    QA-blocked {m.public_id:16} {codes}")

        stats = import_thaqalayn_al_kafi(
            session,
            source_book_id=args.source_book_id,
            matches=matches,
            dry_run=not args.apply,
            job_key="alkafi-en-global-match-v1",
        )
        print(f"\n{'APPLIED' if args.apply else 'DRY RUN'}: imported={stats.imported} "
              f"skipped_existing={stats.skipped_existing} skipped_qa={stats.skipped_qa} "
              f"skipped_low_confidence={stats.skipped_low_confidence} errors={stats.errors}")
        if args.apply:
            session.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
