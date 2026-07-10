"""Resolve chain nodes to canonical narrator identities.

Phase 3 is deliberately conservative:

* named narrator tokens get candidate identities from Mu'jam names/aliases;
* strong unique matches are written to ChainNode;
* ambiguous matches keep ranked candidates and only choose a winner when
  Mu'jam occurrence evidence supports the surrounding chain context;
* relational tokens such as ``عن أبيه`` and chain-opening ``عنه`` are resolved
  only when the neighbouring chain context identifies a plausible narrator.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from eshia_research.corpus import CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    Narrator,
    NarratorAlias,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian

RESOLVER_VERSION = "resolver_v1"
MAX_CANDIDATES_PER_NODE = 5

NAMED_NODE = "named_narrator"
PRONOUN_NODE = "pronoun_relation"
CONTEXT_NODE_TYPES = {"named_narrator", "imam"}

ABI = "\u0627\u0628\u06cc "
ABA = "\u0627\u0628\u0627 "
ABU = "\u0627\u0628\u0648 "
IBN_WORD = " \u0627\u0628\u0646 "
BIN_WORD = " \u0628\u0646 "
INCOMPLETE_NASAB_WORDS = {"\u0628\u0646", "\u0627\u0628\u0646"}


@dataclass(frozen=True)
class CandidateSeed:
    narrator_id: int
    match_type: str
    base_score: int
    matched_norm: str


@dataclass
class CandidateScore:
    narrator_id: int
    score: int
    match_types: set[str] = field(default_factory=set)
    evidence: dict = field(default_factory=dict)
    summary_parts: list[str] = field(default_factory=list)

    @property
    def match_type(self) -> str:
        return "+".join(sorted(self.match_types))

    @property
    def evidence_summary(self) -> str:
        return "; ".join(self.summary_parts)


@dataclass(frozen=True)
class RelationOverride:
    relation_kind: str
    antecedent_norm: str
    target_norm: str
    score: int
    source_note: str


RELATION_OVERRIDES = (
    RelationOverride(
        relation_kind="father",
        antecedent_norm=normalise_arabic_persian("\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645"),
        target_norm=normalise_arabic_persian(
            "\u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0628\u0646 \u0647\u0627\u0634\u0645 "
            "\u0623\u0628\u0648 \u0625\u0633\u062d\u0627\u0642 \u0627\u0644\u0642\u0645\u064a"
        ),
        score=97,
        source_note=(
            "Common Four Books chain pattern; Mu'jam/Najashi route identifies "
            "Ali b. Ibrahim's father as Ibrahim b. Hashim al-Qummi."
        ),
    ),
    RelationOverride(
        relation_kind="father",
        antecedent_norm=normalise_arabic_persian(
            "\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0628\u0646 \u0647\u0627\u0634\u0645"
        ),
        target_norm=normalise_arabic_persian(
            "\u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0628\u0646 \u0647\u0627\u0634\u0645 "
            "\u0623\u0628\u0648 \u0625\u0633\u062d\u0627\u0642 \u0627\u0644\u0642\u0645\u064a"
        ),
        score=98,
        source_note="Explicit patronymic: Ali b. Ibrahim b. Hashim -> father is Ibrahim b. Hashim al-Qummi.",
    ),
)


@dataclass
class ResolverLookup:
    narrator_norm_by_id: dict[int, str]
    canonical_by_norm: dict[str, list[int]]
    alias_by_norm: dict[str, list[int]]
    prefix_by_norm: dict[str, list[int]]
    narrates_from: dict[int, Counter[str]]
    narrated_by: dict[int, Counter[str]]


@dataclass
class ResolutionStats:
    nodes_seen: int = 0
    named_nodes: int = 0
    nodes_with_candidates: int = 0
    candidate_rows: int = 0
    resolved_nodes: int = 0
    ambiguous_nodes: int = 0
    unresolved_nodes: int = 0
    exact_unique_resolved: int = 0
    prefix_unique_resolved: int = 0
    context_resolved: int = 0
    pronoun_nodes: int = 0
    relation_resolved: int = 0
    relation_ambiguous: int = 0
    relation_unresolved: int = 0
    method_counts: Counter = field(default_factory=Counter)
    relation_method_counts: Counter = field(default_factory=Counter)

    @property
    def resolution_ratio(self) -> float:
        return 0.0 if not self.named_nodes else self.resolved_nodes / self.named_nodes


def token_variants(norm: str | None) -> list[str]:
    """Return safe orthographic variants for a normalised token.

    Word-initial Abu/Abi/Aba case alternation is handled for kunyas. Internal
    ``ibn`` is normalised to ``bin`` for occasional chain-token spelling drift.
    """
    if not norm:
        return []
    variants = [norm]
    if norm.startswith(ABI):
        variants.append(ABU + norm[len(ABI) :])
    elif norm.startswith(ABA):
        variants.append(ABU + norm[len(ABA) :])
    elif norm.startswith(ABU):
        variants.append(ABI + norm[len(ABU) :])
    if IBN_WORD in norm:
        variants.append(norm.replace(IBN_WORD, BIN_WORD))

    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant and variant not in seen:
            deduped.append(variant)
            seen.add(variant)
    return deduped


def name_prefixes(canonical_norm: str) -> list[str]:
    parts = canonical_norm.split()
    prefixes: list[str] = []
    seen: set[str] = set()
    for end in range(1, min(len(parts), 7)):
        if parts[end - 1] in INCOMPLETE_NASAB_WORDS:
            continue
        prefix = " ".join(parts[:end])
        if len(prefix) < 4 or prefix == canonical_norm or prefix in seen:
            continue
        prefixes.append(prefix)
        seen.add(prefix)
    return prefixes


def build_resolver_lookup(db: Session) -> ResolverLookup:
    narrator_norm_by_id: dict[int, str] = {}
    canonical_by_norm: dict[str, list[int]] = defaultdict(list)
    prefix_by_norm: dict[str, list[int]] = defaultdict(list)
    for narrator_id, norm in db.query(Narrator.id, Narrator.canonical_name_norm).all():
        narrator_norm_by_id[narrator_id] = norm
        canonical_by_norm[norm].append(narrator_id)
        for prefix in name_prefixes(norm):
            prefix_by_norm[prefix].append(narrator_id)

    alias_by_norm: dict[str, list[int]] = defaultdict(list)
    for narrator_id, norm in db.query(NarratorAlias.narrator_id, NarratorAlias.alias_normalised).all():
        alias_by_norm[norm].append(narrator_id)

    narrates_from: dict[int, Counter[str]] = defaultdict(Counter)
    narrated_by: dict[int, Counter[str]] = defaultdict(Counter)
    for narrator_id, direction, related_norm in db.query(
        RijalOccurrence.narrator_id,
        RijalOccurrence.direction,
        RijalOccurrence.related_name_normalised,
    ).filter(RijalOccurrence.narrator_id.isnot(None)):
        if direction == "narrates_from":
            narrates_from[narrator_id][related_norm] += 1
        elif direction == "narrated_by":
            narrated_by[narrator_id][related_norm] += 1

    return ResolverLookup(
        narrator_norm_by_id=narrator_norm_by_id,
        canonical_by_norm=dict(canonical_by_norm),
        alias_by_norm=dict(alias_by_norm),
        prefix_by_norm=dict(prefix_by_norm),
        narrates_from=dict(narrates_from),
        narrated_by=dict(narrated_by),
    )


def generate_candidate_seeds(token_norm: str, lookup: ResolverLookup) -> list[CandidateSeed]:
    by_narrator: dict[int, CandidateSeed] = {}
    for variant in token_variants(token_norm):
        is_original = variant == token_norm
        for narrator_id in lookup.canonical_by_norm.get(variant, []):
            seed = CandidateSeed(
                narrator_id=narrator_id,
                match_type="exact_name" if is_original else "case_variant_name",
                base_score=88 if is_original else 82,
                matched_norm=variant,
            )
            current = by_narrator.get(narrator_id)
            if current is None or seed.base_score > current.base_score:
                by_narrator[narrator_id] = seed
        for narrator_id in lookup.alias_by_norm.get(variant, []):
            seed = CandidateSeed(
                narrator_id=narrator_id,
                match_type="exact_alias" if is_original else "case_variant_alias",
                base_score=82 if is_original else 76,
                matched_norm=variant,
            )
            current = by_narrator.get(narrator_id)
            if current is None or seed.base_score > current.base_score:
                by_narrator[narrator_id] = seed

    if by_narrator:
        return list(by_narrator.values())

    for variant in token_variants(token_norm):
        prefix_matches = lookup.prefix_by_norm.get(variant, [])
        if len(prefix_matches) > 25:
            continue
        for narrator_id in prefix_matches:
            seed = CandidateSeed(
                narrator_id=narrator_id,
                match_type="name_prefix",
                base_score=78,
                matched_norm=variant,
            )
            current = by_narrator.get(narrator_id)
            if current is None or seed.base_score > current.base_score:
                by_narrator[narrator_id] = seed

    return list(by_narrator.values())


def _context_count(counter: Counter[str], neighbour_norm: str | None) -> int:
    total = 0
    for variant in token_variants(neighbour_norm):
        total += counter.get(variant, 0)
    return total


def score_candidates(
    token_norm: str,
    *,
    previous_norm: str | None,
    next_norm: str | None,
    lookup: ResolverLookup,
) -> list[CandidateScore]:
    scores: dict[int, CandidateScore] = {}
    for seed in generate_candidate_seeds(token_norm, lookup):
        scored = scores.setdefault(seed.narrator_id, CandidateScore(seed.narrator_id, seed.base_score))
        scored.score = max(scored.score, seed.base_score)
        scored.match_types.add(seed.match_type)
        scored.evidence.setdefault("matched_norms", []).append(seed.matched_norm)
        scored.summary_parts.append(f"{seed.match_type}:{seed.matched_norm}")

        from_count = _context_count(lookup.narrates_from.get(seed.narrator_id, Counter()), next_norm)
        if from_count:
            bonus = min(22, 14 + from_count)
            scored.score += bonus
            scored.evidence["next_teacher_occurrences"] = from_count
            scored.summary_parts.append(f"next teacher supported x{from_count}")

        by_count = _context_count(lookup.narrated_by.get(seed.narrator_id, Counter()), previous_norm)
        if by_count:
            bonus = min(22, 14 + by_count)
            scored.score += bonus
            scored.evidence["previous_student_occurrences"] = by_count
            scored.summary_parts.append(f"previous student supported x{by_count}")

    return sorted(
        scores.values(),
        key=lambda candidate: (-min(candidate.score, 99), candidate.narrator_id),
    )


def choose_winner(candidates: list[CandidateScore]) -> tuple[CandidateScore | None, str]:
    if not candidates:
        return None, "unresolved"

    top = candidates[0]
    second_score = candidates[1].score if len(candidates) > 1 else None
    if len(candidates) == 1:
        if top.match_types == {"name_prefix"}:
            return top, "prefix_unique"
        return top, "exact_unique"

    if top.score >= 98 and second_score is not None and top.score - second_score >= 8:
        return top, "context_score"

    return None, "ambiguous"


def _first_nasab_tail(name_norm: str | None) -> str | None:
    if not name_norm:
        return None
    parts = name_norm.split()
    for index, part in enumerate(parts):
        if part in {"\u0628\u0646", "\u0627\u0628\u0646", "\u0628\u0646\u062a"} and index + 1 < len(parts):
            return " ".join(parts[index + 1 :])
    return None


def _father_short_name(father_tail: str | None) -> str | None:
    if not father_tail:
        return None
    parts = father_tail.split()
    if not parts:
        return None
    if parts[0] in {"\u0627\u0628\u0648", "\u0627\u0628\u06cc", "\u0627\u0628\u0627"} and len(parts) > 1:
        return " ".join(parts[:2])
    return parts[0]


def _is_specific_relation_tail(father_tail: str | None) -> bool:
    """A bare given name is not enough to be treated as a full father identity."""
    if not father_tail:
        return False
    return len(father_tail.split()) > 1


def _make_relation_score(
    *,
    narrator_id: int,
    base_score: int,
    match_type: str,
    matched_norm: str,
    previous_norm: str | None,
    next_norm: str | None,
    lookup: ResolverLookup,
) -> CandidateScore:
    scored = CandidateScore(narrator_id=narrator_id, score=base_score)
    scored.match_types.add(match_type)
    scored.evidence["matched_norms"] = [matched_norm]
    scored.summary_parts.append(f"{match_type}:{matched_norm}")

    by_count = _context_count(lookup.narrated_by.get(narrator_id, Counter()), previous_norm)
    if by_count:
        bonus = min(24, 16 + by_count)
        scored.score += bonus
        scored.evidence["previous_student_occurrences"] = by_count
        scored.summary_parts.append(f"son/student supported x{by_count}")

    from_count = _context_count(lookup.narrates_from.get(narrator_id, Counter()), next_norm)
    if from_count:
        bonus = min(22, 14 + from_count)
        scored.score += bonus
        scored.evidence["next_teacher_occurrences"] = from_count
        scored.summary_parts.append(f"next teacher supported x{from_count}")

    return scored


def relation_override_candidates(
    *,
    relation_kind: str,
    antecedent_norm: str | None,
    lookup: ResolverLookup,
) -> list[CandidateScore]:
    if not antecedent_norm:
        return []

    candidates: list[CandidateScore] = []
    for override in RELATION_OVERRIDES:
        if override.relation_kind != relation_kind or override.antecedent_norm != antecedent_norm:
            continue

        narrator_ids = list(lookup.canonical_by_norm.get(override.target_norm, []))
        if not narrator_ids:
            narrator_ids = list(lookup.alias_by_norm.get(override.target_norm, []))
        if not narrator_ids:
            narrator_ids = list(lookup.prefix_by_norm.get(override.target_norm, []))

        for narrator_id in narrator_ids[:MAX_CANDIDATES_PER_NODE]:
            candidates.append(
                CandidateScore(
                    narrator_id=narrator_id,
                    score=override.score,
                    match_types={f"{relation_kind}_override"},
                    evidence={
                        "antecedent_norm": antecedent_norm,
                        "target_norm": override.target_norm,
                        "source_note": override.source_note,
                    },
                    summary_parts=[override.source_note],
                )
            )

    return candidates


def father_relation_candidates(
    *,
    antecedent_norm: str | None,
    next_norm: str | None,
    lookup: ResolverLookup,
    relation_kind: str = "father",
) -> list[CandidateScore]:
    father_tail = _first_nasab_tail(antecedent_norm)
    father_short = _father_short_name(father_tail)
    tail_is_specific = _is_specific_relation_tail(father_tail)
    by_narrator: dict[int, CandidateScore] = {}

    for candidate in relation_override_candidates(
        relation_kind=relation_kind,
        antecedent_norm=antecedent_norm,
        lookup=lookup,
    ):
        by_narrator[candidate.narrator_id] = candidate

    if father_tail and tail_is_specific:
        for seed in generate_candidate_seeds(father_tail, lookup):
            is_full_match = seed.match_type != "name_prefix"
            match_type = f"{relation_kind}_full_name" if is_full_match else f"{relation_kind}_name_prefix"
            scored = _make_relation_score(
                narrator_id=seed.narrator_id,
                base_score=max(88, seed.base_score) if is_full_match else max(84, seed.base_score),
                match_type=match_type,
                matched_norm=seed.matched_norm,
                previous_norm=antecedent_norm,
                next_norm=next_norm,
                lookup=lookup,
            )
            current = by_narrator.get(scored.narrator_id)
            if current is None or scored.score > current.score:
                by_narrator[scored.narrator_id] = scored

    if father_short and (not by_narrator or father_tail == father_short):
        for variant in token_variants(father_short):
            for narrator_id in lookup.prefix_by_norm.get(variant, [])[:300]:
                scored = _make_relation_score(
                    narrator_id=narrator_id,
                    base_score=58,
                    match_type=f"{relation_kind}_name_prefix",
                    matched_norm=variant,
                    previous_norm=antecedent_norm,
                    next_norm=next_norm,
                    lookup=lookup,
                )
                # Prefix-only father matches are useful only when external
                # chain evidence supports them.
                if scored.score < 78:
                    continue
                current = by_narrator.get(narrator_id)
                if current is None or scored.score > current.score:
                    by_narrator[narrator_id] = scored

    return sorted(
        by_narrator.values(),
        key=lambda candidate: (-min(candidate.score, 99), candidate.narrator_id),
    )


def choose_relation_winner(candidates: list[CandidateScore]) -> tuple[CandidateScore | None, str]:
    if not candidates:
        return None, "relation_unresolved"

    top = candidates[0]
    second_score = candidates[1].score if len(candidates) > 1 else None
    if len(candidates) == 1 and top.score >= 82:
        if top.match_types & {"father_full_name", "grandfather_full_name"}:
            return top, "relation_full_name"
        return top, "relation_context"

    if top.score >= 92 and second_score is not None and top.score - second_score >= 8:
        return top, "relation_context"

    return None, "relation_ambiguous"


def _neighbour_norm(nodes: list[ChainNode], index: int) -> str | None:
    if index < 0 or index >= len(nodes):
        return None
    node = nodes[index]
    if node.node_type not in CONTEXT_NODE_TYPES:
        return None
    return node.token_normalised


def _selected_chain_subquery(
    db: Session,
    *,
    source_book_ids: tuple[str, ...] | list[str] | None,
    book_ids: list[int] | None,
):
    query = db.query(Book.id)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        query = query.filter(Book.source_book_id.in_(tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)))
    selected_book_ids = [row[0] for row in query.all()]
    if not selected_book_ids:
        return None

    hadith_ids_subq = select(Hadith.id).where(Hadith.book_id.in_(selected_book_ids))
    return select(Chain.id).where(Chain.hadith_id.in_(hadith_ids_subq))


def _chain_order_rows(db: Session, chain_ids_subq):
    return (
        db.query(Chain.id, Hadith.book_id)
        .join(Hadith, Chain.hadith_id == Hadith.id)
        .filter(Chain.id.in_(chain_ids_subq))
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number)
        .all()
    )


def _resolved_norm(node: ChainNode, lookup: ResolverLookup) -> str | None:
    if node.canonical_narrator_id is None:
        return None
    return lookup.narrator_norm_by_id.get(node.canonical_narrator_id)


def _antecedent_norm_options(
    node: ChainNode,
    lookup: ResolverLookup,
    candidate_norms_by_node_id: dict[int, list[str]],
) -> tuple[list[tuple[str, bool]], str | None]:
    def add_option(
        options: list[tuple[str, bool]],
        seen: set[str],
        norm: str | None,
        *,
        from_candidate: bool,
    ) -> None:
        if norm and norm not in seen:
            options.append((norm, from_candidate))
            seen.add(norm)

    resolved = _resolved_norm(node, lookup)
    if resolved is not None:
        return [(resolved, False)], None

    options: list[tuple[str, bool]] = []
    seen: set[str] = set()
    candidate_norms = candidate_norms_by_node_id.get(node.id, [])
    for norm in candidate_norms:
        add_option(options, seen, norm, from_candidate=True)

    for narrator_id in lookup.prefix_by_norm.get(node.token_normalised, [])[:25]:
        add_option(
            options,
            seen,
            lookup.narrator_norm_by_id.get(narrator_id),
            from_candidate=True,
        )

    if options:
        return options, "antecedent_candidate"

    return [], None


def _add_candidate_row(
    db: Session,
    *,
    node: ChainNode,
    candidate: CandidateScore,
    rank: int,
    resolver_version: str,
) -> None:
    db.add(
        ChainNodeCandidate(
            chain_node_id=node.id,
            narrator_id=candidate.narrator_id,
            rank=rank,
            score=min(candidate.score, 99),
            match_type=candidate.match_type,
            evidence_json=candidate.evidence,
            evidence_summary=candidate.evidence_summary,
            resolver_version=resolver_version,
        )
    )


def _set_resolved_node(
    node: ChainNode,
    *,
    narrator_id: int,
    confidence: int,
    method: str,
    reason: str,
) -> None:
    node.canonical_narrator_id = narrator_id
    node.confidence = confidence
    node.resolution_method = method
    node.resolution_reason = reason
    node.review_status = "resolved"


def _first_resolved_node(nodes: list[ChainNode]) -> ChainNode | None:
    for node in nodes:
        if node.canonical_narrator_id is not None:
            return node
    return None


def resolve_relation_node(
    db: Session,
    *,
    node: ChainNode,
    chain_nodes: list[ChainNode],
    index: int,
    lookup: ResolverLookup,
    candidate_norms_by_node_id: dict[int, list[str]],
    previous_chain_opening_id: int | None,
    resolver_version: str,
    max_candidates_per_node: int,
) -> tuple[str, int]:
    """Resolve one pronoun node and return (method, candidate_rows_added)."""
    relation = node.relation_kind
    candidates_written = 0

    if relation == "anaphora":
        if index == 0:
            narrator_id = previous_chain_opening_id
            method = "anaphora_previous_chain"
            reason = "Resolved to the previous chain opening narrator."
        elif chain_nodes[index - 1].canonical_narrator_id is not None:
            narrator_id = chain_nodes[index - 1].canonical_narrator_id
            method = "anaphora_previous_node"
            reason = "Resolved to the previous resolved node in the same chain."
        else:
            narrator_id = None
            method = "anaphora_unresolved"
            reason = "No resolved antecedent was available."

        if narrator_id is not None:
            candidate = CandidateScore(
                narrator_id=narrator_id,
                score=92 if index == 0 else 84,
                match_types={method},
                evidence={"antecedent": "previous_chain" if index == 0 else "previous_node"},
                summary_parts=[reason],
            )
            _add_candidate_row(
                db,
                node=node,
                candidate=candidate,
                rank=1,
                resolver_version=resolver_version,
            )
            _set_resolved_node(
                node,
                narrator_id=narrator_id,
                confidence=candidate.score,
                method=method,
                reason=reason,
            )
            return method, 1

        node.review_status = "unresolved"
        node.resolution_method = method
        node.resolution_reason = reason
        return method, 0

    if relation in {"father", "grandfather"}:
        if index == 0:
            node.review_status = "unresolved"
            node.resolution_method = f"{relation}_unresolved"
            node.resolution_reason = "Relationship token has no previous node in this chain."
            return node.resolution_method, 0

        antecedent_options, _antecedent_source = _antecedent_norm_options(
            chain_nodes[index - 1],
            lookup,
            candidate_norms_by_node_id,
        )
        if not antecedent_options:
            node.review_status = "unresolved"
            node.resolution_method = f"{relation}_unresolved"
            node.resolution_reason = "Previous node is not resolved, so the relationship cannot be grounded."
            return node.resolution_method, 0

        next_norm = _neighbour_norm(chain_nodes, index + 1)
        merged_candidates: dict[int, CandidateScore] = {}
        for antecedent_norm, from_candidate in antecedent_options:
            for candidate in father_relation_candidates(
                antecedent_norm=antecedent_norm,
                next_norm=next_norm,
                lookup=lookup,
                relation_kind=relation,
            ):
                if from_candidate:
                    if not any(match_type.endswith("_override") for match_type in candidate.match_types):
                        candidate.score -= 8
                    candidate.evidence["antecedent_candidate_norm"] = antecedent_norm
                    candidate.summary_parts.append("antecedent was an unresolved candidate")
                current = merged_candidates.get(candidate.narrator_id)
                if current is None or candidate.score > current.score:
                    merged_candidates[candidate.narrator_id] = candidate

        candidates = sorted(
            merged_candidates.values(),
            key=lambda candidate: (-min(candidate.score, 99), candidate.narrator_id),
        )
        winner, method = choose_relation_winner(candidates)
        for rank, candidate in enumerate(candidates[:max_candidates_per_node], start=1):
            _add_candidate_row(
                db,
                node=node,
                candidate=candidate,
                rank=rank,
                resolver_version=resolver_version,
            )
            candidates_written += 1

        if winner is not None:
            _set_resolved_node(
                node,
                narrator_id=winner.narrator_id,
                confidence=min(winner.score, 99),
                method=method,
                reason=winner.evidence_summary,
            )
        elif candidates:
            node.review_status = "ambiguous"
            node.resolution_method = "relation_ambiguous"
            node.resolution_reason = f"{len(candidates)} candidate(s); top score {min(candidates[0].score, 99)}"
        else:
            node.review_status = "unresolved"
            node.resolution_method = "relation_unresolved"
            node.resolution_reason = "No father/grandfather candidate had enough Mu'jam evidence."
        return node.resolution_method or method, candidates_written

    node.review_status = "unresolved"
    node.resolution_method = f"{relation or 'pronoun'}_unsupported"
    node.resolution_reason = "This relationship token needs a later specialised rule."
    return node.resolution_method, 0


def rebuild_chain_node_resolutions(
    db: Session,
    *,
    source_book_ids: tuple[str, ...] | list[str] | None = None,
    book_ids: list[int] | None = None,
    resolver_version: str = RESOLVER_VERSION,
    max_candidates_per_node: int = MAX_CANDIDATES_PER_NODE,
    commit: bool = True,
) -> ResolutionStats:
    chain_ids_subq = _selected_chain_subquery(
        db,
        source_book_ids=source_book_ids,
        book_ids=book_ids,
    )
    stats = ResolutionStats()
    if chain_ids_subq is None:
        return stats

    node_ids_subq = select(ChainNode.id).where(ChainNode.chain_id.in_(chain_ids_subq))
    db.execute(delete(ChainNodeCandidate).where(ChainNodeCandidate.chain_node_id.in_(node_ids_subq)))
    db.execute(
        update(ChainNode)
        .where(ChainNode.chain_id.in_(chain_ids_subq), ChainNode.node_type.in_([NAMED_NODE, PRONOUN_NODE]))
        .values(
            canonical_narrator_id=None,
            confidence=None,
            resolution_method=None,
            resolution_reason=None,
            review_status="pending",
        )
    )
    db.flush()

    lookup = build_resolver_lookup(db)
    chain_rows = _chain_order_rows(db, chain_ids_subq)
    nodes = (
        db.query(ChainNode)
        .filter(ChainNode.chain_id.in_(chain_ids_subq))
        .order_by(ChainNode.chain_id, ChainNode.position)
        .all()
    )
    stats.nodes_seen = len(nodes)
    nodes_by_chain: dict[int, list[ChainNode]] = defaultdict(list)
    for node in nodes:
        nodes_by_chain[node.chain_id].append(node)

    candidate_norms_by_node_id: dict[int, list[str]] = {}
    previous_opening_by_book: dict[int, int] = {}
    for chain_id, book_id in chain_rows:
        chain_nodes = nodes_by_chain.get(chain_id, [])
        for index, node in enumerate(chain_nodes):
            if node.node_type != NAMED_NODE:
                continue

            stats.named_nodes += 1
            candidates = score_candidates(
                node.token_normalised,
                previous_norm=_neighbour_norm(chain_nodes, index - 1),
                next_norm=_neighbour_norm(chain_nodes, index + 1),
                lookup=lookup,
            )

            if candidates:
                stats.nodes_with_candidates += 1
                candidate_norms_by_node_id[node.id] = [
                    lookup.narrator_norm_by_id[candidate.narrator_id]
                    for candidate in candidates[:max_candidates_per_node]
                    if candidate.narrator_id in lookup.narrator_norm_by_id
                ]
            winner, method = choose_winner(candidates)
            stats.method_counts[method] += 1

            for rank, candidate in enumerate(candidates[:max_candidates_per_node], start=1):
                _add_candidate_row(
                    db,
                    node=node,
                    candidate=candidate,
                    rank=rank,
                    resolver_version=resolver_version,
                )
                stats.candidate_rows += 1

            if winner is not None:
                _set_resolved_node(
                    node,
                    narrator_id=winner.narrator_id,
                    confidence=min(winner.score, 99),
                    method=method,
                    reason=winner.evidence_summary,
                )
                stats.resolved_nodes += 1
                if method == "exact_unique":
                    stats.exact_unique_resolved += 1
                elif method == "prefix_unique":
                    stats.prefix_unique_resolved += 1
                elif method == "context_score":
                    stats.context_resolved += 1
            elif candidates:
                node.review_status = "ambiguous"
                node.resolution_method = "ambiguous_candidates"
                node.resolution_reason = f"{len(candidates)} candidate(s); top score {min(candidates[0].score, 99)}"
                stats.ambiguous_nodes += 1
            else:
                node.review_status = "unresolved"
                node.resolution_method = "no_candidate"
                node.resolution_reason = "No Mu'jam name or sourced alias matched this token."
                stats.unresolved_nodes += 1

        for index, node in enumerate(chain_nodes):
            if node.node_type != PRONOUN_NODE:
                continue
            stats.pronoun_nodes += 1
            method, candidate_rows_added = resolve_relation_node(
                db,
                node=node,
                chain_nodes=chain_nodes,
                index=index,
                lookup=lookup,
                candidate_norms_by_node_id=candidate_norms_by_node_id,
                previous_chain_opening_id=previous_opening_by_book.get(book_id),
                resolver_version=resolver_version,
                max_candidates_per_node=max_candidates_per_node,
            )
            stats.candidate_rows += candidate_rows_added
            stats.relation_method_counts[method] += 1
            if node.review_status == "resolved":
                stats.relation_resolved += 1
            elif node.review_status == "ambiguous":
                stats.relation_ambiguous += 1
            else:
                stats.relation_unresolved += 1

        opening_node = _first_resolved_node(chain_nodes)
        if opening_node is not None and opening_node.canonical_narrator_id is not None:
            previous_opening_by_book[book_id] = opening_node.canonical_narrator_id

        if commit and stats.named_nodes and stats.named_nodes % 10000 == 0:
            db.commit()

    if commit:
        db.commit()
    return stats
