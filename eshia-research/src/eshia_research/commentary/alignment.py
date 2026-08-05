"""Chapter-sequence alignment between a commentary and the book it explains.

Text matching can only reach a passage when the commentator reprinted the
report he is explaining. Al-Majlisi frequently does not: he writes «الحديث
الرابع» and comments, leaving the reader to hold the al-Kafi page open. Those
passages carry no quotable text, so no amount of scoring will ever place them.

What they do carry is *position*. Both works walk the same chapters in the same
order, and within a chapter both number from one. So a passage is identified by
where it sits, provided the chapter it sits in has been pinned independently.

The engine is deliberately generic over the unit types: it aligns two ordered
sequences of numbered runs, given a set of already-trusted pairs to anchor on.
Nothing here knows about Mir'at, al-Kafi, or eShia markup.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Generic, Hashable, Iterable, Sequence, TypeVar

Unit = TypeVar("Unit")


@dataclass
class ChapterRun(Generic[Unit]):
    """A contiguous run of units printed under one chapter heading."""

    index: int
    """Position in reading order. Alignment is monotonic in this."""

    title: str
    units_by_ordinal: dict[int, Unit] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.units_by_ordinal)


@dataclass
class ChapterLink:
    """One aligned chapter pair and the evidence that justified it."""

    source_index: int
    target_index: int
    anchor_support: int
    """Independently text-verified units agreeing on this pair. 0 = inferred."""

    title_similarity: float
    method: str
    """``anchored`` (text-verified) or ``interpolated`` (position + title)."""

    ordinal_delta: int = 0
    """Editions do not always number a chapter alike.

    Where the two works disagree — al-Kafi's «باب البداء» runs one behind the
    sharh's numbering throughout — every positional placement in that chapter
    would land on the neighbouring report. The offset is *learned* from the
    chapter's own text-verified anchors rather than assumed to be zero.
    """

    ordinal_delta_confidence: float = 1.0
    """Share of the chapter's anchors that agree on ``ordinal_delta``."""


def title_similarity(left: Sequence[str], right: Sequence[str]) -> float:
    """Symmetric token overlap of two chapter titles, 0.0-1.0."""
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _weighted_monotonic_subset(pairs: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Heaviest strictly-increasing subsequence of (source, target, weight).

    Chapter order is shared by both works, so any anchor that would require the
    alignment to run backwards is a mis-anchor. Maximising total support rather
    than count keeps a well-evidenced pair over a chain of thin ones.
    """
    if not pairs:
        return []
    ordered = sorted(pairs, key=lambda item: (item[0], item[1]))
    best: list[int] = [0] * len(ordered)
    prev: list[int] = [-1] * len(ordered)
    for i, (_si, ti, wi) in enumerate(ordered):
        best[i] = wi
        for j in range(i):
            _sj, tj, _wj = ordered[j]
            if tj < ti and best[j] + wi > best[i]:
                best[i] = best[j] + wi
                prev[i] = j
    end = max(range(len(ordered)), key=lambda i: best[i])
    chain: list[tuple[int, int, int]] = []
    while end != -1:
        chain.append(ordered[end])
        end = prev[end]
    chain.reverse()
    # Anchors on the same source run must not survive twice.
    seen_source: set[int] = set()
    unique: list[tuple[int, int, int]] = []
    for si, ti, wi in chain:
        if si in seen_source:
            continue
        seen_source.add(si)
        unique.append((si, ti, wi))
    return unique


def align_chapters(
    source_runs: Sequence[ChapterRun],
    target_runs: Sequence[ChapterRun],
    confirmed: dict[Hashable, int],
    source_unit_key: "callable",
    *,
    source_titles: Sequence[Sequence[str]],
    target_titles: Sequence[Sequence[str]],
    min_interpolated_similarity: float = 0.5,
) -> list[ChapterLink]:
    """Pair commentary chapters with the chapters they explain.

    ``confirmed`` maps a source unit key to the index of the target run holding
    the unit it was independently text-matched to. Those votes anchor the
    alignment; everything else is interpolated between anchors and only kept
    when the chapter titles also agree.
    """
    # --- 1. anchors: let text-verified units vote for their chapter pair ----
    votes: dict[int, Counter] = defaultdict(Counter)
    deltas: dict[tuple[int, int], Counter] = defaultdict(Counter)
    for source_run in source_runs:
        for source_ordinal, unit in source_run.units_by_ordinal.items():
            resolved = confirmed.get(source_unit_key(unit))
            if resolved is None:
                continue
            target_index, target_ordinal = resolved
            votes[source_run.index][target_index] += 1
            deltas[(source_run.index, target_index)][target_ordinal - source_ordinal] += 1

    candidates: list[tuple[int, int, int]] = []
    for source_index, counter in votes.items():
        target_index, support = counter.most_common(1)[0]
        candidates.append((source_index, target_index, support))

    anchors = _weighted_monotonic_subset(candidates)
    links: list[ChapterLink] = []
    for si, ti, support in anchors:
        delta_counter = deltas.get((si, ti), Counter())
        if delta_counter:
            delta, agreeing = delta_counter.most_common(1)[0]
            confidence = agreeing / sum(delta_counter.values())
        else:
            delta, confidence = 0, 1.0
        links.append(
            ChapterLink(
                source_index=si,
                target_index=ti,
                anchor_support=support,
                title_similarity=title_similarity(source_titles[si], target_titles[ti]),
                method="anchored",
                ordinal_delta=delta,
                ordinal_delta_confidence=confidence,
            )
        )

    # --- 2. interpolate the runs between consecutive anchors ---------------
    anchored_pairs = [(link.source_index, link.target_index) for link in links]
    bounds = (
        [(-1, -1)] + anchored_pairs + [(len(source_runs), len(target_runs))]
    )
    for (s_lo, t_lo), (s_hi, t_hi) in zip(bounds, bounds[1:]):
        gap_sources = list(range(s_lo + 1, s_hi))
        gap_targets = list(range(t_lo + 1, t_hi))
        if not gap_sources or not gap_targets:
            continue
        links.extend(
            _interpolate_gap(
                gap_sources,
                gap_targets,
                source_titles,
                target_titles,
                min_interpolated_similarity,
            )
        )

    links.sort(key=lambda link: link.source_index)
    return links


def _interpolate_gap(
    gap_sources: list[int],
    gap_targets: list[int],
    source_titles: Sequence[Sequence[str]],
    target_titles: Sequence[Sequence[str]],
    min_similarity: float,
) -> list[ChapterLink]:
    """Align the unanchored runs strictly between two anchored pairs.

    Equal-length gaps are the common case — both works simply carried on
    through the same chapters — and are taken in order. Unequal gaps mean one
    side has chapters the other lacks, so pairs must earn their place on title
    agreement alone.
    """
    if len(gap_sources) == len(gap_targets):
        produced: list[ChapterLink] = []
        for si, ti in zip(gap_sources, gap_targets):
            similarity = title_similarity(source_titles[si], target_titles[ti])
            produced.append(
                ChapterLink(
                    source_index=si,
                    target_index=ti,
                    anchor_support=0,
                    title_similarity=similarity,
                    method="interpolated",
                )
            )
        return produced

    # Unequal gap: greedy monotonic walk keeping only confident title pairs.
    produced = []
    ti_cursor = 0
    for si in gap_sources:
        best_index: int | None = None
        best_similarity = min_similarity
        for offset in range(ti_cursor, len(gap_targets)):
            similarity = title_similarity(source_titles[si], target_titles[gap_targets[offset]])
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = offset
        if best_index is None:
            continue
        produced.append(
            ChapterLink(
                source_index=si,
                target_index=gap_targets[best_index],
                anchor_support=0,
                title_similarity=best_similarity,
                method="interpolated",
            )
        )
        ti_cursor = best_index + 1
    return produced


@dataclass
class OrdinalProposal:
    """A positional identification awaiting the caller's publication rules."""

    source_unit: object
    target_unit: object
    link: ChapterLink
    ordinal: int


def propose_by_ordinal(
    source_runs: Sequence[ChapterRun],
    target_runs: Sequence[ChapterRun],
    links: Iterable[ChapterLink],
) -> list[OrdinalProposal]:
    """Within each aligned chapter, unit *k* explains unit *k*.

    Only proposes where both sides actually carry that ordinal; a commentary
    that skips a report must not shift every later report by one.
    """
    source_by_index = {run.index: run for run in source_runs}
    target_by_index = {run.index: run for run in target_runs}
    proposals: list[OrdinalProposal] = []
    for link in links:
        source_run = source_by_index.get(link.source_index)
        target_run = target_by_index.get(link.target_index)
        if source_run is None or target_run is None:
            continue
        for ordinal, unit in source_run.units_by_ordinal.items():
            target_ordinal = ordinal + link.ordinal_delta
            target_unit = target_run.units_by_ordinal.get(target_ordinal)
            if target_unit is None:
                continue
            proposals.append(
                OrdinalProposal(
                    source_unit=unit,
                    target_unit=target_unit,
                    link=link,
                    ordinal=target_ordinal,
                )
            )
    return proposals
