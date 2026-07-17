"""Build the definitive Sarwar-first dossier for the 179-report Al-Kafi pass.

The important rule is that static-edition anchors come only from direct Arabic
matching.  API URL components are not treated as static chapter identifiers.
"""

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
    ThaqalaynRecord,
    build_matches,
    match_score,
    static_records_from_rows,
)


PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
DEFERRED_STRONG_CASES = {
    "alkafi-1160", "alkafi-1173", "alkafi-2695", "alkafi-2782",
    "alkafi-4734", "alkafi-5669", "alkafi-6959", "alkafi-8322",
    "alkafi-8963", "alkafi-9558", "alkafi-10372", "alkafi-11166",
    "alkafi-11169", "alkafi-13307", "alkafi-13394", "alkafi-13498",
    "alkafi-14527", "alkafi-14755",
}

# These editorial abbreviations are characteristic of the HubeAli edition and
# do not occur in Muhammad Sarwar's translation convention.  Some upstream
# static rows are mislabeled as Sarwar, so translator metadata alone is not a
# sufficient source-purity check.
HUBEALI_STYLE_MARKERS = {
    "hubeali.com": "hubeali_url",
    "(azwj)": "hubeali_honorific_azwj",
    "(saww)": "hubeali_honorific_saww",
    "(asws)": "hubeali_honorific_asws",
}


def source_purity_flags(english: str) -> list[str]:
    lowered = english.casefold()
    return [code for marker, code in HUBEALI_STYLE_MARKERS.items() if marker in lowered]


def public_translation(translation: HadithTranslation | None, hadith: Hadith) -> bool:
    return bool(
        translation
        and translation.status in PUBLIC_STATUSES
        and translation.risk_level == "green"
        and clean_ws(translation.matn_translation)
        and translation.source_full_sha256 == sha256_text(hadith.full_text_raw)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("static_cache", type=Path)
    parser.add_argument("pdf_records", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-dir", type=Path, required=True)
    args = parser.parse_args()

    static_rows = json.loads(args.static_cache.read_text(encoding="utf-8"))
    remote_by_volume = static_records_from_rows(static_rows)
    remote_by_key = {
        (remote.volume, remote.id): remote
        for rows in remote_by_volume.values()
        for remote in rows
    }
    pdf_payload = json.loads(args.pdf_records.read_text(encoding="utf-8"))
    pdf_by_h = {
        int(record["hadith_number"]): record
        for record in pdf_payload["records"]
        if not record.get("hadith_suffix") and len(record.get("english") or "") < 40_000
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
            row
            for row in hadiths
            if not public_translation(translations.get(row.id), row)
        ]
        target = [row for row in missing if row.public_id not in DEFERRED_STRONG_CASES]
        if len(missing) != 197 or len(target) != 179:
            raise RuntimeError(
                f"Expected 197 missing and 179 target rows; found {len(missing)} and {len(target)}"
            )

        direct_matches, direct_stats = build_matches(
            db,
            source_book_id="11005",
            remote_by_volume=remote_by_volume,
        )
        direct_by_public = {match.public_id: match for match in direct_matches}
        local_index = {row.public_id: index for index, row in enumerate(hadiths)}
        direct_anchor = {
            local_index[match.public_id]: match
            for match in direct_matches
            if match.public_id in local_index
        }

        # Map unmatched local intervals only between direct Arabic anchors.
        interval_assignment: dict[str, tuple[ThaqalaynRecord, dict[str, object]]] = {}
        volume_indexes: dict[int, list[int]] = {}
        for index, row in enumerate(hadiths):
            volume_indexes.setdefault(row.volume_start or 0, []).append(index)
        for volume, indexes in volume_indexes.items():
            anchors = [index for index in indexes if index in direct_anchor]
            for before_index, after_index in zip(anchors, anchors[1:]):
                local_gap = [
                    hadiths[index]
                    for index in range(before_index + 1, after_index)
                    if index not in direct_anchor
                ]
                if not local_gap:
                    continue
                before = direct_anchor[before_index]
                after = direct_anchor[after_index]
                if before.thaqalayn_id >= after.thaqalayn_id:
                    continue
                remote_gap = [
                    remote_by_key[(volume, remote_id)]
                    for remote_id in range(before.thaqalayn_id + 1, after.thaqalayn_id)
                    if (volume, remote_id) in remote_by_key
                ]
                if len(local_gap) != len(remote_gap):
                    continue
                for local, remote in zip(local_gap, remote_gap, strict=True):
                    interval_assignment[local.public_id] = (
                        remote,
                        {
                            "method": "one_to_one_between_direct_arabic_anchors",
                            "before": {
                                "public_id": before.public_id,
                                "remote_id": before.thaqalayn_id,
                                "score": before.score,
                            },
                            "after": {
                                "public_id": after.public_id,
                                "remote_id": after.thaqalayn_id,
                                "score": after.score,
                            },
                            "local_gap_count": len(local_gap),
                            "remote_gap_count": len(remote_gap),
                        },
                    )

        records: list[dict[str, object]] = []
        ready_batches: dict[int, list[dict[str, object]]] = {}
        for row in target:
            direct = direct_by_public.get(row.public_id)
            interval = interval_assignment.get(row.public_id)
            remote: ThaqalaynRecord | None = None
            identity: dict[str, object] | None = None
            identity_score = 0.0
            if direct is not None:
                remote = remote_by_key[(direct.volume, direct.thaqalayn_id)]
                identity_score = direct.score
                identity = {
                    "method": "direct_arabic_match",
                    "score": direct.score,
                    "remote_id": direct.thaqalayn_id,
                    "matcher_version": direct.matcher_version,
                }
            elif interval is not None:
                remote, identity = interval
                identity_score = match_score(row, remote)
                identity["score"] = identity_score
                identity["remote_id"] = remote.id

            source: dict[str, object] | None = None
            english = ""
            if remote is not None and remote.translator == "Muhammad Sarwar":
                english = remote.usable_translation
                source = {
                    "kind": "thaqalayn_static_sarwar",
                    "translator": "Muhammad Sarwar",
                    "source_url": remote.url,
                    "remote_id": remote.id,
                }
                pdf = pdf_by_h.get(remote.id)
                if pdf:
                    source["pdf_confirmation"] = {
                        key: pdf[key]
                        for key in (
                            "physical_volume", "hadith_number", "pdf_page",
                            "source_url", "source_sha256", "marker",
                        )
                    }
            elif remote is not None and remote.id in pdf_by_h:
                pdf = pdf_by_h[remote.id]
                english = str(pdf["english"])
                source = {
                    "kind": "published_sarwar_pdf_recovery",
                    "translator": "Muhammad Sarwar",
                    "remote_id": remote.id,
                    "physical_volume": pdf["physical_volume"],
                    "pdf_page": pdf["pdf_page"],
                    "source_url": pdf["source_url"],
                    "source_sha256": pdf["source_sha256"],
                    "marker": pdf["marker"],
                }

            qa = assess_translation(row.matn_raw, english) if english else None
            qa_flags = [] if qa is None else [asdict(flag) for flag in qa.flags]
            blocking = [
                flag["code"] for flag in qa_flags if flag["code"] in IMPORT_BLOCKING_QA_CODES
            ]
            blocking.extend(source_purity_flags(english))
            if remote is None:
                decision = "unresolved_alignment"
            elif source is None:
                decision = "sarwar_not_available_in_verified_sources"
            elif blocking:
                decision = "sarwar_candidate_blocked_qa"
            else:
                decision = "ready_sarwar"

            payload = {
                "public_id": row.public_id,
                "sequence": row.sequence_in_book,
                "volume": row.volume_start,
                "page_start": row.page_start,
                "page_end": row.page_end,
                "printed_number": row.printed_number,
                "local_source_url": row.source_url,
                "arabic": row.full_text_raw,
                "matn": row.matn_raw,
                "decision": decision,
                "identity": identity,
                "source": source,
                "english": english or None,
                "qa_risk": None if qa is None else qa.risk_level,
                "qa_flags": qa_flags,
                "blocking_qa": blocking,
            }
            records.append(payload)
            if decision == "ready_sarwar":
                ready_batches.setdefault(row.volume_start or 0, []).append(payload)

    counts: dict[str, int] = {}
    for record in records:
        decision = str(record["decision"])
        counts[decision] = counts.get(decision, 0) + 1
    summary = {
        "target": 179,
        "deferred_strong_cases": sorted(DEFERRED_STRONG_CASES),
        "direct_static_matches_all_visible": direct_stats.matched,
        "decisions": counts,
        "by_volume": {
            str(volume): {
                "target": sum(record["volume"] == volume for record in records),
                "ready_sarwar": len(ready_batches.get(volume, [])),
            }
            for volume in range(1, 9)
        },
        "processing_order": [6, 5, 7, 8, 1, 2, 3, 4],
        "source_manifests": pdf_payload["manifest"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.batch_dir.mkdir(parents=True, exist_ok=True)
    for volume in [6, 5, 7, 8, 1, 2, 3, 4]:
        batch = ready_batches.get(volume, [])
        (args.batch_dir / f"volume_{volume}_ready.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"output={args.output} batch_dir={args.batch_dir}")


if __name__ == "__main__":
    main()
