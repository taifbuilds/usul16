"""The single source of truth for a chain node's *effective* person identity.

The Tamyiz resolver writes ranked `mention_resolutions`; a human/LLM review
layer writes `PersonResolutionDecision` rows (reviewer `codex-admin-external-v1`)
that approve, override, or demote the resolver's rank-1 pick. Historically only
the audit queue honored those decisions — the public graph and the hadith chain
popovers read raw rank-1 rows and were blind to corrections.

This module computes the effective resolution (raw rank-1 overlaid with the
admin decision) once, so every read surface agrees. `apply_admin_decision`
mirrors `routes_books._effective_resolution_read` exactly; that function is
refactored to build its schema on top of this, so the logic lives here alone.

Only decisions by `ADMIN_REVIEWER` at the matching `resolver_version` count.
Unknown decision types pass through to the machine pick — never silently demote.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    PersonResolutionDecision,
)

# The reviewer whose decisions are authoritative for the public read surface.
# Kept here so routes_books._ADMIN_PERSON_REVIEWER imports one definition.
ADMIN_REVIEWER = "codex-admin-external-v1"

# A node participates in the confident graph/edge set only in these states.
CONFIDENT_STATUSES = ("resolved", "via_collective")

_REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"


@dataclasses.dataclass(frozen=True)
class EffectiveResolution:
    """The identity a node should be shown/counted as after review."""

    person_id: int | None
    status: str
    source: str  # "machine" | "admin"
    confident: bool


def apply_admin_decision(
    raw_status: str | None,
    raw_person_id: int | None,
    decision: PersonResolutionDecision | None,
) -> EffectiveResolution:
    """Overlay one admin decision on a node's raw rank-1 resolution.

    `decision` must already be filtered to the admin reviewer + matching
    resolver version by the caller (see `load_admin_decisions`).
    """
    machine_confident = raw_status in CONFIDENT_STATUSES and raw_person_id is not None
    machine = EffectiveResolution(
        person_id=raw_person_id,
        status=raw_status or "missing_rank1",
        source="machine",
        confident=machine_confident,
    )
    if decision is None:
        return machine

    dtype = decision.decision_type
    if dtype == "approve_current":
        person_id = decision.selected_person_id or raw_person_id
        return EffectiveResolution(
            person_id=person_id,
            status="approved_current",
            source="admin",
            confident=person_id is not None,
        )
    if dtype == "approve_external_override":
        # A NULL override target is a malformed decision; stay non-confident
        # rather than inventing an edge to nobody.
        return EffectiveResolution(
            person_id=decision.selected_person_id,
            status="approved_override",
            source="admin",
            confident=decision.selected_person_id is not None,
        )
    if dtype == "keep_ambiguous":
        return EffectiveResolution(
            person_id=None, status="kept_ambiguous", source="admin", confident=False
        )
    if dtype == "flag_text_or_chain_issue":
        return EffectiveResolution(
            person_id=None, status="text_or_chain_issue", source="admin", confident=False
        )

    # Unknown/other decision types (needs_external_review, flag_contradiction,
    # ...) are advisory only — fall through to the machine pick.
    return machine


def load_admin_decisions(
    db: Session,
    *,
    resolver_version: str,
    chain_node_ids: Iterable[int] | None = None,
    reviewer: str = ADMIN_REVIEWER,
) -> dict[int, PersonResolutionDecision]:
    """chain_node_id -> the authoritative admin decision for that node.

    `chain_node_ids=None` loads every admin decision at this version (fine — the
    decisions table is small); pass an id list for narrow scopes (one hadith).
    """
    query = db.query(PersonResolutionDecision).filter(
        PersonResolutionDecision.reviewer == reviewer,
        PersonResolutionDecision.resolver_version == resolver_version,
    )
    if chain_node_ids is not None:
        ids = list(chain_node_ids)
        if not ids:
            return {}
        query = query.filter(PersonResolutionDecision.chain_node_id.in_(ids))
    return {d.chain_node_id: d for d in query.all()}


@dataclasses.dataclass(frozen=True)
class EffectiveNode:
    """A confident chain-node mention after the decision overlay."""

    chain_node_id: int
    chain_id: int
    position: int
    hadith_id: int
    person_id: int
    source: str  # "machine" | "admin"


def load_confident_nodes(
    db: Session, source_book_id: str, resolver_version: str
) -> list[EffectiveNode]:
    """Every non-rejected chain node in a book that is confident *after review*.

    An admin override can PROMOTE an otherwise-ambiguous node into the confident
    set (and change which person it points at); keep_ambiguous / text-issue
    flags DEMOTE a machine-resolved node out of it. Raw-only reads can do
    neither, which is exactly the correction path this enables.
    """
    stmt = (
        select(
            ChainNode.id,
            ChainNode.chain_id,
            ChainNode.position,
            Hadith.id,
            MentionResolution.status,
            MentionResolution.person_id,
        )
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .outerjoin(
            MentionResolution,
            and_(
                MentionResolution.chain_node_id == ChainNode.id,
                MentionResolution.rank == 1,
                MentionResolution.resolver_version == resolver_version,
            ),
        )
        .where(
            Book.source_book_id == source_book_id,
            Hadith.review_status != _REJECTED_HADITH_STATUS,
        )
    )
    decisions = load_admin_decisions(db, resolver_version=resolver_version)

    out: list[EffectiveNode] = []
    for node_id, chain_id, position, hadith_id, status, person_id in db.execute(stmt):
        eff = apply_admin_decision(status, person_id, decisions.get(node_id))
        if eff.confident and eff.person_id is not None:
            out.append(
                EffectiveNode(
                    chain_node_id=node_id,
                    chain_id=chain_id,
                    position=position,
                    hadith_id=hadith_id,
                    person_id=eff.person_id,
                    source=eff.source,
                )
            )
    return out


def adjacent_pairs(
    nodes: Iterable[EffectiveNode],
) -> Iterator[tuple[EffectiveNode, EffectiveNode]]:
    """Yield (student, teacher) for strictly adjacent confident nodes.

    Position p is the student of position p+1 (closer to the compiler). Because
    only confident nodes are passed in, a gap at p+1 correctly yields no edge —
    matching the original SQL join's `position + 1` + confident predicate.
    """
    by_chain: dict[int, dict[int, EffectiveNode]] = {}
    for node in nodes:
        by_chain.setdefault(node.chain_id, {})[node.position] = node
    for positions in by_chain.values():
        for pos, student in positions.items():
            teacher = positions.get(pos + 1)
            if teacher is not None:
                yield student, teacher
