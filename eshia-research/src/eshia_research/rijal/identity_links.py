"""Materialise al-Khoei's explicit same-person evidence.

Phase A stored Mu'jam tamyiz snippets as `person_entry_links` rows, but left
them as inert evidence. This pass turns the conservative, machine-readable
subset into `person_relations.same_person_as` edges. It never deletes or
merges person rows; the relation is an auditable cluster hint for later eval,
UI, and resolver passes.
"""

from __future__ import annotations

import dataclasses
from collections import Counter, defaultdict
from collections.abc import Iterable

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from eshia_research.models import Person, PersonEntryLink, PersonRelation, RijalEntry
from eshia_research.normalise import normalise_arabic_persian


def _n(text: str | None) -> str:
    return normalise_arabic_persian(text or "").strip()


_MUSHTARAK_MARKERS = {_n("مشترك"), _n("مشترک")}
_NEXT_MARKERS = {_n("ما بعده"), _n("من بعده")}
_PREV_MARKERS = {_n("ما قبله"), _n("من قبله"), _n("سابقه")}
_SAME_PERSON_MARKERS = {
    _n("متحد مع"),
    _n("اتحاده مع"),
    _n("يأتي بعنوان"),
    _n("یاتی بعنوان"),
    _n("تقدم بعنوان"),
}
_NEGATED_SAME_PERSON_MARKERS = {
    _n("لكن الأمر على خلافه"),
    _n("ولكن الأمر على خلافه"),
    _n("لكن الامر على خلافه"),
    _n("ولكن الامر على خلافه"),
    _n("فكيف يمكن اتحادهما"),
    _n("لا يمكن اتحادهما"),
    # Al-Khoei often opens by reporting an earlier proposed identification,
    # then rejects it with one of these evidentiary/chronological formulas.
    # The opening «اتحاده مع» is not an assertion when the same note says the
    # union has no witness or is historically remote.
    _n("لا شاهد عليه"),
    _n("لا شاهد عليها"),
    _n("لا شاهد على اتحاده"),
    _n("لا دليل عليه"),
    _n("لا دليل على اتحاده"),
    _n("يبعد الاتحاد"),
    _n("بعيد الاتحاد"),
    _n("لا وجه للاتحاد"),
    _n("لا وجه لاتحاده"),
}
_TARGET_STOP_MARKERS = tuple(
    _n(s)
    for s in (
        ".",
        "۔",
        " اختلاف الكتب",
        " اختلاف الکتب",
        " طريق الشيخ",
        " طریق الشیخ",
        " طريق الصدوق",
        " طریق الصدوق",
        " روى الشيخ",
        " روی الشیخ",
    )
)


@dataclasses.dataclass
class SamePersonLinkStats:
    tamyiz_links_examined: int = 0
    relation_rows_created: int = 0
    pairs_created: int = 0
    skipped_mushtarak: int = 0
    skipped_no_target: int = 0
    skipped_ambiguous_target: int = 0
    skipped_proxy: int = 0
    skipped_negated: int = 0
    negated_relations_removed: int = 0
    existing_relations: int = 0
    method_counts: Counter[str] = dataclasses.field(default_factory=Counter)


@dataclasses.dataclass(frozen=True)
class _PersonLite:
    id: int
    name_norm: str
    kind: str
    primary_entry_id: int | None
    entry_number: int | None
    book_id: int | None


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker and marker in text for marker in markers)


def _relative_direction(quote_norm: str) -> int | None:
    has_next = _contains_any(quote_norm, _NEXT_MARKERS)
    has_prev = _contains_any(quote_norm, _PREV_MARKERS)
    if has_next == has_prev:
        return None
    return 1 if has_next else -1


def _relation_note(method: str, quote: str | None) -> str:
    clean = " ".join((quote or "").split())
    if len(clean) > 430:
        clean = clean[:427] + "..."
    return f"al-Khoei tamyiz:{method}: {clean}"


def _target_segment(quote_norm: str) -> str:
    starts: list[int] = []
    for marker in _SAME_PERSON_MARKERS:
        pos = quote_norm.find(marker)
        if pos >= 0:
            starts.append(pos + len(marker))
    if not starts:
        return quote_norm

    segment = quote_norm[min(starts) :].strip(" :،؛")
    end = len(segment)
    for marker in _TARGET_STOP_MARKERS:
        pos = segment.find(marker)
        if pos >= 0:
            end = min(end, pos)
    return segment[:end].strip(" :،؛")


def _build_person_indexes(db: Session) -> tuple[
    dict[int, _PersonLite],
    dict[int, int],
    dict[tuple[int | None, int], int],
    list[tuple[str, int]],
]:
    """Return person/entry/name indexes over non-proxy Mu'jam persons."""

    rows = db.execute(
        select(
            Person.id,
            Person.canonical_name_norm,
            Person.kind,
            Person.primary_entry_id,
            RijalEntry.entry_number,
            RijalEntry.book_id,
        )
        .select_from(Person)
        .outerjoin(RijalEntry, RijalEntry.id == Person.primary_entry_id)
        .where(Person.origin == "mujam_entry")
    ).all()

    people: dict[int, _PersonLite] = {}
    entry_to_person: dict[int, int] = {}
    entry_number_to_person: dict[tuple[int | None, int], int] = {}
    name_to_people: defaultdict[str, set[int]] = defaultdict(set)

    for pid, name_norm, kind, entry_id, entry_number, book_id in rows:
        person = _PersonLite(
            id=pid,
            name_norm=_n(name_norm),
            kind=kind,
            primary_entry_id=entry_id,
            entry_number=entry_number,
            book_id=book_id,
        )
        people[pid] = person
        if entry_id is not None:
            entry_to_person[entry_id] = pid
        if entry_number is not None:
            entry_number_to_person[(book_id, entry_number)] = pid
        if person.kind != "bare_form_proxy" and person.name_norm:
            name_to_people[person.name_norm].add(pid)

    # Longest names first prevents a short embedded title from stealing an
    # explicit longer target in quotes like "X bin Y al-Z".
    exact_name_targets = sorted(
        (
            (name, next(iter(pids)))
            for name, pids in name_to_people.items()
            if len(pids) == 1 and len(name) >= 8
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    return people, entry_to_person, entry_number_to_person, exact_name_targets


def _target_from_relative(
    current: _PersonLite,
    direction: int,
    people: dict[int, _PersonLite],
    entry_number_to_person: dict[tuple[int | None, int], int],
) -> tuple[int | None, str]:
    if current.entry_number is None:
        return None, "missing-entry-number"

    target_pid = entry_number_to_person.get((current.book_id, current.entry_number + direction))
    if target_pid is None:
        return None, "missing-neighbour"
    target = people[target_pid]
    if target.kind == "bare_form_proxy":
        return None, "proxy-neighbour"
    return target_pid, "relative_next" if direction > 0 else "relative_previous"


def _target_from_exact_name(
    target_segment: str,
    current: _PersonLite,
    exact_name_targets: list[tuple[str, int]],
) -> tuple[int | None, str]:
    hits: list[int] = []
    longest_len = 0
    for name_norm, pid in exact_name_targets:
        if pid == current.id or name_norm not in target_segment:
            continue
        name_len = len(name_norm)
        if name_len < longest_len:
            break
        if name_len > longest_len:
            hits = []
            longest_len = name_len
        hits.append(pid)

    unique_hits = sorted(set(hits))
    if len(unique_hits) == 1:
        return unique_hits[0], "exact_name_in_quote"
    if len(unique_hits) > 1:
        return None, "ambiguous-exact-name"
    return None, "no-exact-name"


def materialize_same_person_relations(
    db: Session,
    *,
    commit: bool = True,
) -> SamePersonLinkStats:
    """Create bidirectional `same_person_as` relations from safe tamyiz snippets.

    Conservative rules only:
    - skip "mushtarak/shared between several people" snippets;
    - link "ma ba'dahu / man ba'dahu" to the next Mu'jam numbered entry;
    - link "ma qablahu / sabiqahu" to the previous Mu'jam numbered entry;
    - otherwise link only when exactly one non-proxy canonical person name is
      explicitly present in the quote.
    """

    stats = SamePersonLinkStats()
    people, entry_to_person, entry_number_to_person, exact_name_targets = _build_person_indexes(db)

    # Earlier versions saw ``اتحاده مع`` but ignored the explicit rebuttal
    # later in the same quotation. Remove only tool-owned relations whose own
    # stored evidence says the proposed identity is impossible.
    generated_relations = db.execute(
        select(PersonRelation).where(
            PersonRelation.relation_kind == "same_person_as",
            PersonRelation.source_note.like("al-Khoei tamyiz:%"),
        )
    ).scalars()
    for relation in generated_relations:
        if _contains_any(_n(relation.source_note), _NEGATED_SAME_PERSON_MARKERS):
            db.delete(relation)
            stats.negated_relations_removed += 1
    if stats.negated_relations_removed:
        db.flush()

    existing: set[tuple[int, str]] = {
        (pid, _n(related_name))
        for pid, related_name in db.execute(
            select(PersonRelation.person_id, PersonRelation.related_name_norm).where(
                PersonRelation.relation_kind == "same_person_as"
            )
        )
    }

    links = db.execute(
        select(
            PersonEntryLink.person_id,
            PersonEntryLink.evidence_quote,
            PersonEntryLink.entry_id,
        ).where(PersonEntryLink.link_type == "tamyiz_discussion")
    ).all()

    for current_pid, quote, entry_id in links:
        stats.tamyiz_links_examined += 1
        current = people.get(current_pid)
        if current is None and entry_id is not None:
            mapped_pid = entry_to_person.get(entry_id)
            current = people.get(mapped_pid) if mapped_pid is not None else None
        if current is None:
            stats.skipped_no_target += 1
            continue
        if current.kind == "bare_form_proxy":
            stats.skipped_proxy += 1
            continue

        quote_norm = _n(quote)
        if _contains_any(quote_norm, _MUSHTARAK_MARKERS):
            stats.skipped_mushtarak += 1
            continue
        if _contains_any(quote_norm, _NEGATED_SAME_PERSON_MARKERS):
            stats.skipped_negated += 1
            stats.method_counts["skipped:explicit-negation"] += 1
            continue
        if not _contains_any(quote_norm, _SAME_PERSON_MARKERS):
            stats.skipped_no_target += 1
            continue

        target_pid: int | None = None
        method = ""
        direction = _relative_direction(quote_norm)
        if direction is not None:
            target_pid, method = _target_from_relative(
                current, direction, people, entry_number_to_person
            )
        if target_pid is None:
            target_pid, method = _target_from_exact_name(
                _target_segment(quote_norm), current, exact_name_targets
            )

        if target_pid is None:
            if method == "ambiguous-exact-name":
                stats.skipped_ambiguous_target += 1
            elif method == "proxy-neighbour":
                stats.skipped_proxy += 1
            else:
                stats.skipped_no_target += 1
            stats.method_counts[f"skipped:{method or 'no-target'}"] += 1
            continue
        if target_pid == current.id:
            stats.skipped_no_target += 1
            stats.method_counts["skipped:self"] += 1
            continue

        target = people[target_pid]
        if target.kind == "bare_form_proxy":
            stats.skipped_proxy += 1
            stats.method_counts["skipped:target-proxy"] += 1
            continue

        rows_created_for_pair = 0
        for src, dst in ((current, target), (target, current)):
            key = (src.id, dst.name_norm)
            if key in existing:
                stats.existing_relations += 1
                continue
            db.add(
                PersonRelation(
                    person_id=src.id,
                    related_person_id=dst.id,
                    relation_kind="same_person_as",
                    related_name_norm=dst.name_norm,
                    source_note=_relation_note(method, quote),
                    confidence=90 if method.startswith("relative") else 85,
                )
            )
            existing.add(key)
            rows_created_for_pair += 1

        if rows_created_for_pair:
            stats.pairs_created += 1
            stats.relation_rows_created += rows_created_for_pair
            stats.method_counts[method] += 1

    if commit:
        db.commit()
    else:
        db.flush()

    return stats


def same_person_clusters(db: Session, person_ids: set[int] | None = None) -> dict[int, set[int]]:
    """Return transitive same-person clusters touching `person_ids`.

    The returned mapping includes every requested person id. If `person_ids` is
    None, all persons participating in same-person relations are returned.
    """

    stmt = select(PersonRelation.person_id, PersonRelation.related_person_id).where(
        and_(
            PersonRelation.relation_kind == "same_person_as",
            PersonRelation.related_person_id.isnot(None),
        )
    )
    edges = [(a, b) for a, b in db.execute(stmt) if a is not None and b is not None]

    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for a, b in edges:
        union(a, b)
    if person_ids is not None:
        for pid in person_ids:
            find(pid)

    grouped: defaultdict[int, set[int]] = defaultdict(set)
    for pid in list(parent):
        grouped[find(pid)].add(pid)

    if person_ids is None:
        return {pid: grouped[find(pid)] for pid in parent}
    return {pid: grouped[find(pid)] for pid in person_ids}
