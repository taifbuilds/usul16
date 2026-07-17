"""Plan a source-anchored completion of Al-Kafi's English coverage.

The plan is read-only. Existing published translations provide Thaqalayn path
anchors. Missing local reports are aligned only to the human translations that
occur between those anchors in the canonical ThaqalaynData order.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.thaqalayn_importer import (
    ThaqalaynRecord,
    match_norm,
    match_score_parts,
    match_words,
    static_records_from_rows,
)
from eshia_research.translation.text import clean_ws, sha256_text


PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
HADITH_URL_RE = re.compile(r"/hadith/(\d+)/(\d+)/(\d+)/(\d+)(?:$|[/?#])")
STATIC_URL_RE = re.compile(r"al-kafi:(\d+):(\d+):(\d+):(\d+)(?:$|[/?#])")


@dataclass(frozen=True)
class Anchor:
    local_index: int
    remote_id: int
    public_id: str
    source_url: str


def source_key(
    url: str | None, *, volume_override: int | None = None
) -> tuple[int, int, int, int] | None:
    if not url:
        return None
    match = HADITH_URL_RE.search(url) or STATIC_URL_RE.search(url)
    if not match:
        return None
    parts = tuple(int(part) for part in match.groups())
    if volume_override is not None:
        parts = (volume_override, *parts[1:])
    return parts  # type: ignore[return-value]


def score(local: Hadith, remote: ThaqalaynRecord) -> float:
    return match_score_parts(
        local_full=match_norm(local.full_text_raw),
        local_matn=match_norm(local.matn_raw),
        local_full_words=match_words(local.full_text_raw),
        local_matn_words=match_words(local.matn_raw),
        remote=remote,
    )


def choose_monotonic(
    local_rows: list[Hadith], remote_rows: list[ThaqalaynRecord]
) -> list[tuple[Hadith, ThaqalaynRecord, float]]:
    """Choose an ordered subset of remote rows with Arabic and position evidence."""

    m, n = len(local_rows), len(remote_rows)
    if m == 0 or n < m:
        return []
    scores = [[score(local, remote) for remote in remote_rows] for local in local_rows]
    negative = -10**9
    dp = [[negative] * (n + 1) for _ in range(m + 1)]
    take = [[False] * (n + 1) for _ in range(m + 1)]
    for j in range(n + 1):
        dp[0][j] = 0.0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            skip_value = dp[i][j - 1]
            expected = i * (n + 1) / (m + 1)
            position_penalty = 0.015 * abs(j - expected)
            take_value = dp[i - 1][j - 1] + scores[i - 1][j - 1] - position_penalty
            if take_value > skip_value:
                dp[i][j] = take_value
                take[i][j] = True
            else:
                dp[i][j] = skip_value
    chosen: list[tuple[Hadith, ThaqalaynRecord, float]] = []
    i, j = m, n
    while i > 0 and j > 0:
        if take[i][j]:
            chosen.append((local_rows[i - 1], remote_rows[j - 1], scores[i - 1][j - 1]))
            i -= 1
            j -= 1
        else:
            j -= 1
    chosen.reverse()
    return chosen if len(chosen) == m else []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cache", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    remote_by_volume = static_records_from_rows(
        json.loads(args.cache.read_text(encoding="utf-8"))
    )
    remote_by_key = {
        source_key(remote.url): remote
        for rows in remote_by_volume.values()
        for remote in rows
        if source_key(remote.url)
    }
    remote_by_id = {
        remote.id: remote for rows in remote_by_volume.values() for remote in rows
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
        hadith_by_id = {row.id: row for row in hadiths}
        local_index_by_id = {row.id: index for index, row in enumerate(hadiths)}
        translations = list(
            db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        )
        current: dict[int, HadithTranslation] = {}
        anchors: dict[int, Anchor] = {}
        for translation in translations:
            hadith = hadith_by_id.get(translation.hadith_id)
            if (
                not hadith
                or translation.status not in PUBLIC_STATUSES
                or translation.risk_level != "green"
                or not clean_ws(translation.matn_translation)
                or translation.source_full_sha256 != sha256_text(hadith.full_text_raw)
            ):
                continue
            current[hadith.id] = translation
            provenance = translation.provenance_json or {}
            url = clean_ws(provenance.get("source_url"))
            remote = remote_by_key.get(
                source_key(url, volume_override=hadith.volume_start or None)
            )
            if remote:
                local_index = local_index_by_id[hadith.id]
                anchors[local_index] = Anchor(
                    local_index=local_index,
                    remote_id=remote.id,
                    public_id=hadith.public_id,
                    source_url=url,
                )

        missing_indexes = [i for i, row in enumerate(hadiths) if row.id not in current]
        blocks: list[list[int]] = []
        for index in missing_indexes:
            if (
                not blocks
                or index != blocks[-1][-1] + 1
                or hadiths[index].volume_start != hadiths[blocks[-1][-1]].volume_start
            ):
                blocks.append([index])
            else:
                blocks[-1].append(index)

        output_blocks: list[dict[str, object]] = []
        planned = 0
        volume_bounds: dict[int, tuple[int, int]] = {}
        for index, hadith in enumerate(hadiths):
            volume = hadith.volume_start or 0
            if volume not in volume_bounds:
                volume_bounds[volume] = (index, index)
            else:
                volume_bounds[volume] = (volume_bounds[volume][0], index)
        for block in blocks:
            local_rows = [hadiths[index] for index in block]
            volume = local_rows[0].volume_start or 0
            volume_start, volume_end = volume_bounds[volume]
            remote_volume_rows = remote_by_volume[volume]
            virtual_before = Anchor(
                local_index=volume_start - 1,
                remote_id=remote_volume_rows[0].id - 1,
                public_id=f"volume-{volume}-start",
                source_url="",
            )
            virtual_after = Anchor(
                local_index=volume_end + 1,
                remote_id=remote_volume_rows[-1].id + 1,
                public_id=f"volume-{volume}-end",
                source_url="",
            )
            before_options = sorted(
                [
                anchor
                for index, anchor in anchors.items()
                if index < block[0] and hadiths[index].volume_start == volume
                ],
                key=lambda anchor: anchor.local_index,
            )[-64:]
            after_options = sorted(
                [
                anchor
                for index, anchor in anchors.items()
                if index > block[-1] and hadiths[index].volume_start == volume
                ],
                key=lambda anchor: anchor.local_index,
            )[:64]
            before_options.insert(0, virtual_before)
            after_options.append(virtual_after)
            viable_pairs = [
                (before_anchor, after_anchor)
                for before_anchor in before_options
                for after_anchor in after_options
                if before_anchor.remote_id < after_anchor.remote_id
            ]
            if viable_pairs:
                before_anchor, after_anchor = min(
                    viable_pairs,
                    key=lambda pair: (
                        3
                        * abs(
                            (pair[1].remote_id - pair[0].remote_id)
                            - (pair[1].local_index - pair[0].local_index)
                        )
                        + (pair[1].local_index - pair[0].local_index),
                        pair[1].local_index - pair[0].local_index,
                    ),
                )
            else:
                before_anchor = None
                after_anchor = None
            classification = "missing_anchor"
            candidates: list[ThaqalaynRecord] = []
            chosen: list[tuple[Hadith, ThaqalaynRecord, float]] = []
            if (
                before_anchor
                and after_anchor
            ):
                start, end = before_anchor.remote_id + 1, after_anchor.remote_id
                if start <= end:
                    candidates = [
                        remote_by_id[index]
                        for index in range(start, end)
                        if index in remote_by_id and remote_by_id[index].volume == volume
                    ]
                    if len(candidates) == len(local_rows):
                        classification = "one_to_one_between_anchors"
                        chosen = [
                            (local, remote, score(local, remote))
                            for local, remote in zip(local_rows, candidates, strict=True)
                        ]
                    elif len(candidates) > len(local_rows):
                        classification = "source_has_extra_rows"
                        chosen = choose_monotonic(local_rows, candidates)
                    else:
                        classification = "local_has_extra_rows"
                else:
                    classification = "reordered_anchors"
            if chosen:
                planned += len(chosen)
            output_blocks.append(
                {
                    "classification": classification,
                    "volume": volume,
                    "local_count": len(local_rows),
                    "candidate_count": len(candidates),
                    "before": None if not before_anchor else before_anchor.__dict__,
                    "after": None if not after_anchor else after_anchor.__dict__,
                    "assignments": [
                        {
                            "public_id": local.public_id,
                            "remote_id": remote.id,
                            "source_url": remote.url,
                            "score": match_score,
                            "translator": remote.translator,
                            "english": remote.usable_translation,
                            "local_arabic": local.full_text_raw,
                            "remote_arabic": remote.arabic_text,
                        }
                        for local, remote, match_score in chosen
                    ],
                    "unassigned_public_ids": []
                    if chosen
                    else [local.public_id for local in local_rows],
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output_blocks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts: dict[str, int] = {}
    for block in output_blocks:
        key = str(block["classification"])
        counts[key] = counts.get(key, 0) + int(block["local_count"])
    print(
        f"missing={len(missing_indexes)} planned={planned} blocks={len(blocks)} "
        f"classifications={counts} output={args.output}"
    )


if __name__ == "__main__":
    main()
