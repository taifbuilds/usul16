"""Phase D of the Tamyiz Engine: conservative collective disambiguation.

This pass refines Phase B/C ``mention_resolutions`` in place. It does not edit
source text, chain nodes, or person identity tables except for a narrowly
marked compiler-prior latent person if the DB lacks an al-Kulayni person.

The idea is deliberately small and auditable:

* build person->person edge statistics from already-resolved adjacent chain
  nodes;
* add Mu'jam mashyakha support from ``rijal_occurrences``;
* add generation compatibility from ``person_generations``;
* add compiler-convention priors for al-Kafi's opening ``Abu Ja'far Muhammad
  b. Ya'qub``;
* add narrow al-Kafi source-opening priors learned from external review:
  ``Muhammad b. Yahya`` and ``Ali b. Ibrahim`` at chain opening, plus opening
  ``anhu`` back-reference to the previous hadith source;
* expand documented ``'iddah`` rosters after a following bare narrator becomes
  resolved.

Only high-margin winners are written. Weak cases stay ambiguous.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, aliased

from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID, CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    CollectiveRoster,
    Hadith,
    MentionResolution,
    Person,
    PersonGeneration,
    PersonSurfaceForm,
    RijalEntry,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.eval_resolution import RELIABLE_GEN_METHODS
from eshia_research.rijal.name_grammar import parse_name
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION
from eshia_research.rijal.review_priors import AL_KAFI_REVIEW_PRIORS, target_person_for_spec

ProgressCallback = Callable[[str, int, int], None]

COLLECTIVE_REFINER_VERSION = "tamyiz_d1"

DERIVATION_RANK = {
    "full": 0,
    "masum_title": 0,
    "entry_title": 1,
    "nasab_truncation": 2,
    "ibn_form": 3,
    "nisba_form": 4,
    "kunya": 5,
    "first_name": 6,
}
DERIVATION_BASE = {
    "full": 32,
    "masum_title": 32,
    "entry_title": 30,
    "nasab_truncation": 24,
    "ibn_form": 22,
    "nisba_form": 18,
    "kunya": 18,
    "first_name": 12,
}

MAX_EXPANDED_CANDIDATES = 300
MAX_STORED_ALTERNATES = 5
MIN_WIN_SCORE = 65
MIN_WIN_MARGIN = 18
# A candidate is vetoed when its anchor-derived generation is at least this many
# layers away from an anchor-derived neighbour's expectation. Only anchor-vs-anchor
# comparisons veto; propagated-only generations remain a soft score term.
GENERATION_VETO_GAP = 3

REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


ABU_VARIANTS = tuple(_n(w) for w in ("ابو", "ابی", "ابا"))
IBN = _n("ابن")
BIN = _n("بن")
BARE_JOIN = f" {BIN} "
IDDAH = _n("عدة من اصحابنا")
JAMAAH = _n("جماعة")
AL_KULAYNI = _n("الكليني")
MUHAMMAD_B_YAQUB = _n("محمد بن يعقوب")
ABU_JAFAR = _n("ابو جعفر")
MUHAMMAD_B_YAHYA = _n("محمد بن يحيى")
MUHAMMAD_B_YAHYA_ABU_JAFAR_ATTAR = _n("محمد بن يحيى أبو جعفر العطار")
MUHAMMAD_B_YAHYA_ATTAR = _n("محمد بن يحيى العطار")
ALI_B_IBRAHIM = _n("علي بن إبراهيم")
ALI_B_IBRAHIM_B_HASHIM = _n("علي بن إبراهيم بن هاشم")
ANHU = _n("عنه")

# --- Imam-kunya isnad-convention priors (Phase D) ---------------------------
# In the Four Books' asanid a bare Imam kunya carrying the ع honorific denotes
# the conventional Imam. Two kunyas are shared by two Ma'sumin and so leave the
# Phase-B resolver honestly ambiguous:
#   «أبو عبد الله ع» -> al-Sadiq, but al-Husayn (Sayyid al-Shuhada) shares the kunya;
#   «أبو جعفر ع»     -> al-Baqir,  but al-Jawad («أبو جعفر الثاني») shares the kunya.
# The alternate Ma'sum is a naming coincidence, not a transmission source: when
# he is actually meant he is named explicitly (al-Husayn b. Ali / Sayyid al-Shuhada;
# al-Jawad / Abu Ja'far al-Thani), which the resolver already resolves via
# `imam_explicit_identity`. So a bare, still-ambiguous kunya node is the
# conventional Imam. We break the tie ONLY when the ambiguous Ma'sum candidate
# set is exactly the shared-kunya pair, keeping the alternate as a ranked
# alternative so the (rare) genuine exception stays visible.
SADIQ_NORM = _n("جعفر بن محمد الصادق عليه السلام")
HUSAYN_NORM = _n("الحسين بن علي سيد الشهداء عليه السلام")
BAQIR_NORM = _n("محمد بن علي الباقر عليه السلام")
JAWAD_NORM = _n("محمد بن علي الجواد عليه السلام")


def token_case_variants(norm: str) -> list[str]:
    variants = [norm]
    for head in ABU_VARIANTS:
        if norm.startswith(head + " "):
            rest = norm[len(head) + 1 :]
            variants.extend(f"{variant} {rest}" for variant in ABU_VARIANTS)
            break
    if f" {IBN} " in norm:
        variants.append(norm.replace(f" {IBN} ", f" {BIN} "))

    out: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant and variant not in seen:
            out.append(variant)
            seen.add(variant)
    return out


@dataclass(frozen=True)
class Candidate:
    person_id: int
    derivation: str
    shared_count: int
    matched_form: str


@dataclass
class CandidateScore:
    person_id: int
    score: int
    evidence: list[str] = field(default_factory=list)
    evidence_json: dict = field(default_factory=dict)


@dataclass
class ChainNodeState:
    id: int
    chain_id: int
    position: int
    token_norm: str
    node_type: str
    relation_kind: str | None
    rows: list[MentionResolution]

    @property
    def is_ambiguous(self) -> bool:
        return len(self.rows) > 1 and all(row.status == "ambiguous" for row in self.rows)

    @property
    def is_collective(self) -> bool:
        return self.node_type == "collective_phrase"

    @property
    def resolved_people(self) -> list[int]:
        return [
            row.person_id
            for row in self.rows
            if row.person_id is not None and row.status in {"resolved", "via_collective", "latent"}
        ]


@dataclass
class CollectiveRefinementStats:
    nodes_examined: int = 0
    nodes_resolved: int = 0
    compiler_priors: int = 0
    source_priors: int = 0
    anaphora_priors: int = 0
    review_priors: int = 0
    context_resolved: int = 0
    roster_expanded_nodes: int = 0
    roster_rows_added: int = 0
    skipped_weak_margin: int = 0
    method_counts: Counter = field(default_factory=Counter)


@dataclass
class ContextLookup:
    person_name_ar: dict[int, str]
    person_name_norm: dict[int, str]
    person_kind: dict[int, str]
    person_generation: dict[int, int]
    form_index: dict[str, list[Candidate]]
    surface_norms_by_person: dict[int, set[str]]
    narrator_by_person: dict[int, int]
    person_by_narrator: dict[int, int]
    occurrence_from: dict[int, Counter[str]]
    occurrence_by: dict[int, Counter[str]]
    roster_keys_by_person: dict[int, list[str]]
    roster_members_by_key_person: dict[int, list[tuple[int, str, str, int]]]
    kulayni_person_id: int | None = None
    # Anchor-derived generation intervals only (imam_fixed/ashab/anchor_and_prop).
    # A HARD generation veto may fire only when BOTH the candidate and the
    # neighbour have one of these — propagated-only generations stay advisory.
    reliable_generation: dict[int, tuple[int, int]] = field(default_factory=dict)


def _select_book_ids(db: Session, source_book_ids, book_ids) -> list[int]:
    query = db.query(Book.id)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        selected = tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)
        query = query.filter(Book.source_book_id.in_(selected))
    return [row[0] for row in query.all()]


def _selected_book_source_ids(db: Session, book_ids: list[int]) -> set[str]:
    return {
        source_book_id
        for (source_book_id,) in db.execute(
            select(Book.source_book_id).where(Book.id.in_(book_ids))
        )
    }


def _query_forms(token_norm: str) -> list[str]:
    forms = list(token_case_variants(token_norm))
    parsed = parse_name(token_norm)
    if parsed.units and not parsed.is_ibn_form:
        bare_nasab = BARE_JOIN.join(parsed.units)
        if parsed.nisba_parts:
            bare_nasab = f"{bare_nasab} {parsed.nisba_parts[0]}"
        for variant in token_case_variants(bare_nasab):
            if variant not in forms:
                forms.append(variant)
    return forms


def _dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    best: dict[int, Candidate] = {}
    for candidate in candidates:
        current = best.get(candidate.person_id)
        if current is None:
            best[candidate.person_id] = candidate
            continue
        current_key = (DERIVATION_RANK.get(current.derivation, 9), current.shared_count)
        next_key = (DERIVATION_RANK.get(candidate.derivation, 9), candidate.shared_count)
        if next_key < current_key:
            best[candidate.person_id] = candidate
    return sorted(
        best.values(),
        key=lambda c: (DERIVATION_RANK.get(c.derivation, 9), c.shared_count, c.person_id),
    )


def expanded_candidates(token_norm: str, lookup: ContextLookup) -> list[Candidate]:
    hits: list[Candidate] = []
    matched_any = False
    for form in _query_forms(token_norm):
        entries = lookup.form_index.get(form)
        if not entries:
            continue
        matched_any = True
        hits.extend(entries)
        # Preserve specificity: if exact token form hits, do not mix in a later
        # parsed fallback form.
        if hits:
            break
    if not matched_any:
        return []
    ranked = _dedupe_candidates(hits)
    if len(ranked) > MAX_EXPANDED_CANDIDATES:
        return []
    return ranked


def _person_norms(lookup: ContextLookup, person_id: int | None) -> set[str]:
    if person_id is None:
        return set()
    norms = set(lookup.surface_norms_by_person.get(person_id, set()))
    name = lookup.person_name_norm.get(person_id)
    if name:
        norms.add(name)
    return norms


def _occurrence_count(
    occurrence_index: dict[int, Counter[str]],
    lookup: ContextLookup,
    candidate_id: int,
    related_person_id: int,
) -> int:
    narrator_id = lookup.narrator_by_person.get(candidate_id)
    if narrator_id is None:
        return 0
    counter = occurrence_index.get(narrator_id, Counter())
    if not counter:
        return 0
    return sum(counter.get(norm, 0) for norm in _person_norms(lookup, related_person_id))


def _build_context_lookup(db: Session) -> ContextLookup:
    person_name_ar: dict[int, str] = {}
    person_name_norm: dict[int, str] = {}
    person_kind: dict[int, str] = {}
    narrator_by_person: dict[int, int] = {}
    person_by_narrator: dict[int, int] = {}

    for pid, name_ar, name_norm, kind, primary_entry_id, narrator_id in db.execute(
        select(
            Person.id,
            Person.canonical_name_ar,
            Person.canonical_name_norm,
            Person.kind,
            Person.primary_entry_id,
            RijalEntry.narrator_id,
        ).outerjoin(RijalEntry, RijalEntry.id == Person.primary_entry_id)
    ):
        person_name_ar[pid] = name_ar
        person_name_norm[pid] = name_norm
        person_kind[pid] = kind
        if narrator_id is not None:
            narrator_by_person[pid] = narrator_id
            person_by_narrator.setdefault(narrator_id, pid)

    person_generation = {
        pid: gen
        for pid, gen in db.execute(
            select(PersonGeneration.person_id, PersonGeneration.gen_point).where(
                PersonGeneration.gen_point.isnot(None),
                # Conflict-method rows have self-contradictory generation evidence;
                # they must not earn or pay generation score in context resolution.
                PersonGeneration.method != "conflict",
            )
        )
    }
    reliable_generation = {
        pid: (lo, hi)
        for pid, lo, hi in db.execute(
            select(
                PersonGeneration.person_id, PersonGeneration.gen_lo, PersonGeneration.gen_hi
            ).where(PersonGeneration.method.in_(RELIABLE_GEN_METHODS))
        )
    }

    form_index: dict[str, list[Candidate]] = defaultdict(list)
    surface_norms_by_person: dict[int, set[str]] = defaultdict(set)
    for person_id, form_norm, derivation, shared_count in db.execute(
        select(
            PersonSurfaceForm.person_id,
            PersonSurfaceForm.form_norm,
            PersonSurfaceForm.derivation,
            PersonSurfaceForm.shared_count,
        )
    ):
        surface_norms_by_person[person_id].add(form_norm)
        if person_kind.get(person_id) == "bare_form_proxy":
            continue
        form_index[form_norm].append(
            Candidate(
                person_id=person_id,
                derivation=derivation,
                shared_count=shared_count,
                matched_form=form_norm,
            )
        )

    occurrence_from: dict[int, Counter[str]] = defaultdict(Counter)
    occurrence_by: dict[int, Counter[str]] = defaultdict(Counter)
    for narrator_id, direction, related_norm in db.execute(
        select(
            RijalOccurrence.narrator_id,
            RijalOccurrence.direction,
            RijalOccurrence.related_name_normalised,
        ).where(RijalOccurrence.narrator_id.isnot(None))
    ):
        if not related_norm:
            continue
        if direction == "narrates_from":
            occurrence_from[narrator_id][related_norm] += 1
        elif direction == "narrated_by":
            occurrence_by[narrator_id][related_norm] += 1

    roster_keys_by_person: dict[int, list[str]] = defaultdict(list)
    roster_members_by_key_person: dict[int, list[tuple[int, str, str, int]]] = defaultdict(list)
    roster_rows = db.execute(
        select(
            CollectiveRoster.keyed_by_norm,
            CollectiveRoster.member_person_id,
            CollectiveRoster.member_name_ar,
            CollectiveRoster.source_citation,
            CollectiveRoster.confidence,
        )
    ).all()
    for keyed_by_norm, member_pid, member_name_ar, citation, confidence in roster_rows:
        key_candidates = _dedupe_candidates(form_index.get(keyed_by_norm, []))
        for candidate in key_candidates:
            if keyed_by_norm not in roster_keys_by_person[candidate.person_id]:
                roster_keys_by_person[candidate.person_id].append(keyed_by_norm)
            if member_pid is not None:
                roster_members_by_key_person[candidate.person_id].append(
                    (member_pid, member_name_ar, citation, confidence)
                )

    kulayni_person_id = _find_kulayni_person(
        db,
        person_name_norm=person_name_norm,
        person_name_ar=person_name_ar,
        person_kind=person_kind,
        surface_norms_by_person=surface_norms_by_person,
    )
    if kulayni_person_id is not None:
        surface_norms_by_person[kulayni_person_id].add(MUHAMMAD_B_YAQUB)
        surface_norms_by_person[kulayni_person_id].add(AL_KULAYNI)

    return ContextLookup(
        person_name_ar=person_name_ar,
        person_name_norm=person_name_norm,
        person_kind=person_kind,
        person_generation=person_generation,
        form_index=dict(form_index),
        surface_norms_by_person=dict(surface_norms_by_person),
        narrator_by_person=narrator_by_person,
        person_by_narrator=person_by_narrator,
        occurrence_from=dict(occurrence_from),
        occurrence_by=dict(occurrence_by),
        roster_keys_by_person=dict(roster_keys_by_person),
        roster_members_by_key_person=dict(roster_members_by_key_person),
        kulayni_person_id=kulayni_person_id,
        reliable_generation=reliable_generation,
    )


def _find_kulayni_person(
    db: Session,
    *,
    person_name_norm: dict[int, str],
    person_name_ar: dict[int, str],
    person_kind: dict[int, str],
    surface_norms_by_person: dict[int, set[str]],
) -> int | None:
    for pid, norm in person_name_norm.items():
        if norm == AL_KULAYNI:
            return pid

    # If the person layer is missing the al-Kulayni entry, mint a clearly
    # labelled latent person for the compiler prior. This mirrors Phase B's
    # latent-kinship policy: the gap stays visible.
    person = Person(
        canonical_name_ar="محمد بن يعقوب الكليني",
        canonical_name_norm=_n("محمد بن يعقوب الكليني"),
        kind="latent",
        origin="compiler_prior",
        notes="Minted by Tamyiz Phase D compiler prior for al-Kafi chain openings.",
    )
    db.add(person)
    db.flush()
    person_name_norm[person.id] = person.canonical_name_norm
    person_name_ar[person.id] = person.canonical_name_ar
    person_kind[person.id] = person.kind
    surface_norms_by_person[person.id].update({person.canonical_name_norm, MUHAMMAD_B_YAQUB, AL_KULAYNI})
    return person.id


def _find_person_by_norms(lookup: ContextLookup, norms: list[str]) -> int | None:
    for wanted in norms:
        exact = [pid for pid, name_norm in lookup.person_name_norm.items() if name_norm == wanted]
        if len(exact) == 1:
            return exact[0]
        form_hits = {
            candidate.person_id
            for candidate in lookup.form_index.get(wanted, [])
            if lookup.person_kind.get(candidate.person_id) != "bare_form_proxy"
        }
        if len(form_hits) == 1:
            return next(iter(form_hits))
    return None


def _chain_states(db: Session, book_ids: list[int]) -> list[list[ChainNodeState]]:
    rows = db.execute(
        select(Chain.id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(Hadith.book_id.in_(book_ids), Hadith.review_status != REJECTED_HADITH_STATUS)
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number)
    ).scalars().all()
    if not rows:
        return []

    node_rows = db.execute(
        select(
            ChainNode.id,
            ChainNode.chain_id,
            ChainNode.position,
            ChainNode.token_normalised,
            ChainNode.node_type,
            ChainNode.relation_kind,
        )
        .where(ChainNode.chain_id.in_(rows))
        .order_by(ChainNode.chain_id, ChainNode.position)
    ).all()
    resolutions: dict[int, list[MentionResolution]] = defaultdict(list)
    for resolution in db.execute(
        select(MentionResolution)
        .join(ChainNode, ChainNode.id == MentionResolution.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(
            Hadith.book_id.in_(book_ids),
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        )
        .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
    ).scalars():
        resolutions[resolution.chain_node_id].append(resolution)

    by_chain: dict[int, list[ChainNodeState]] = defaultdict(list)
    for row in node_rows:
        by_chain[row.chain_id].append(
            ChainNodeState(
                id=row.id,
                chain_id=row.chain_id,
                position=row.position,
                token_norm=row.token_normalised,
                node_type=row.node_type,
                relation_kind=row.relation_kind,
                rows=resolutions.get(row.id, []),
            )
        )
    return [by_chain[chain_id] for chain_id in rows]


def _edge_counts(chains: list[list[ChainNodeState]]) -> Counter[tuple[int, int]]:
    counts: Counter[tuple[int, int]] = Counter()
    for nodes in chains:
        for left, right in zip(nodes, nodes[1:]):
            for student in left.resolved_people:
                for teacher in right.resolved_people:
                    if student != teacher:
                        counts[(student, teacher)] += 1
    return counts


def _edge_support_indexes(
    edge_counts: Counter[tuple[int, int]],
) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    teachers_by_student: dict[int, set[int]] = defaultdict(set)
    students_by_teacher: dict[int, set[int]] = defaultdict(set)
    for (student, teacher), _count in edge_counts.items():
        teachers_by_student[student].add(teacher)
        students_by_teacher[teacher].add(student)
    return dict(teachers_by_student), dict(students_by_teacher)


def _base_score(candidate: Candidate) -> int:
    base = DERIVATION_BASE.get(candidate.derivation, 8)
    if candidate.shared_count <= 1:
        base += 8
    elif candidate.shared_count <= 4:
        base += 4
    elif candidate.shared_count > 80:
        base -= 8
    return base


def _score_candidate(
    candidate: Candidate,
    *,
    previous_people: list[int],
    next_people: list[int],
    previous_node: ChainNodeState | None,
    node: ChainNodeState,
    edge_counts: Counter[tuple[int, int]],
    lookup: ContextLookup,
    source_book_ids: set[str],
) -> CandidateScore:
    score = _base_score(candidate)
    evidence: list[str] = [
        f"surface {candidate.derivation} matched «{candidate.matched_form}» (shared {candidate.shared_count})"
    ]
    evidence_json: dict = {
        "phase": COLLECTIVE_REFINER_VERSION,
        "surface": {
            "form": candidate.matched_form,
            "derivation": candidate.derivation,
            "shared_count": candidate.shared_count,
        },
    }

    edge_support = 0
    for previous in previous_people:
        count = edge_counts.get((previous, candidate.person_id), 0)
        if count > edge_support:
            edge_support = count
    if edge_support:
        bonus = min(55, 28 + edge_support)
        score += bonus
        evidence.append(f"corpus edge from previous narrator supported x{edge_support}")
        evidence_json["previous_edge_count"] = edge_support

    next_edge_support = 0
    for nxt in next_people:
        count = edge_counts.get((candidate.person_id, nxt), 0)
        if count > next_edge_support:
            next_edge_support = count
    if next_edge_support:
        bonus = min(55, 28 + next_edge_support)
        score += bonus
        evidence.append(f"corpus edge to next narrator supported x{next_edge_support}")
        evidence_json["next_edge_count"] = next_edge_support

    previous_occ = 0
    for previous in previous_people:
        previous_occ = max(
            previous_occ,
            _occurrence_count(lookup.occurrence_by, lookup, candidate.person_id, previous),
        )
    if previous_occ:
        score += min(38, 22 + previous_occ)
        evidence.append(f"Mu'jam lists previous narrator among students x{previous_occ}")
        evidence_json["previous_mujam_occurrences"] = previous_occ

    next_occ = 0
    for nxt in next_people:
        next_occ = max(
            next_occ,
            _occurrence_count(lookup.occurrence_from, lookup, candidate.person_id, nxt),
        )
    if next_occ:
        score += min(38, 22 + next_occ)
        evidence.append(f"Mu'jam lists next narrator among teachers x{next_occ}")
        evidence_json["next_mujam_occurrences"] = next_occ

    gen = lookup.person_generation.get(candidate.person_id)
    if gen is not None:
        gen_bonus = 0
        gen_notes: list[str] = []
        for previous in previous_people:
            prev_gen = lookup.person_generation.get(previous)
            if prev_gen is None:
                continue
            expected = prev_gen - 1
            delta = abs(gen - expected)
            if delta == 0:
                gen_bonus = max(gen_bonus, 18)
                gen_notes.append(f"generation {gen} fits previous gen {prev_gen}")
            elif delta == 1:
                gen_bonus = max(gen_bonus, 8)
                gen_notes.append(f"generation {gen} near previous-derived {expected}")
            elif delta >= 3:
                score -= 20
                gen_notes.append(f"generation {gen} far from previous-derived {expected}")
        for nxt in next_people:
            next_gen = lookup.person_generation.get(nxt)
            if next_gen is None:
                continue
            expected = next_gen + 1
            delta = abs(gen - expected)
            if delta == 0:
                gen_bonus = max(gen_bonus, 18)
                gen_notes.append(f"generation {gen} fits next gen {next_gen}")
            elif delta == 1:
                gen_bonus = max(gen_bonus, 8)
                gen_notes.append(f"generation {gen} near next-derived {expected}")
            elif delta >= 3:
                score -= 20
                gen_notes.append(f"generation {gen} far from next-derived {expected}")
        if gen_bonus:
            score += gen_bonus
        if gen_notes:
            evidence.extend(gen_notes[:2])
            evidence_json["generation"] = {"person": gen, "notes": gen_notes[:4]}

    # Hard generation veto — only anchor-vs-anchor, so it cannot fire on the
    # unreliable propagated hubs. A candidate whose anchored generation is >= 3
    # layers from an anchored neighbour's expectation is chronologically
    # impossible and must never win, however strong its surface/edge score.
    cand_iv = lookup.reliable_generation.get(candidate.person_id)
    if cand_iv is not None:
        vetoed_notes: list[str] = []
        for previous in previous_people:
            prev_iv = lookup.reliable_generation.get(previous)
            if prev_iv is None:
                continue
            expected = (prev_iv[0] - 1, prev_iv[1] - 1)  # candidate is one layer earlier
            if _interval_gap(cand_iv, expected) >= GENERATION_VETO_GAP:
                vetoed_notes.append(
                    f"generation {cand_iv} incompatible with previous-anchored {prev_iv}"
                )
        for nxt in next_people:
            next_iv = lookup.reliable_generation.get(nxt)
            if next_iv is None:
                continue
            expected = (next_iv[0] + 1, next_iv[1] + 1)  # candidate is one layer later
            if _interval_gap(cand_iv, expected) >= GENERATION_VETO_GAP:
                vetoed_notes.append(
                    f"generation {cand_iv} incompatible with next-anchored {next_iv}"
                )
        if vetoed_notes:
            evidence_json["generation_vetoed"] = True
            evidence.append(vetoed_notes[0])

    if previous_node and previous_node.is_collective and candidate.person_id in lookup.roster_keys_by_person:
        if IDDAH in previous_node.token_norm or JAMAAH in previous_node.token_norm:
            score += 36
            keys = lookup.roster_keys_by_person[candidate.person_id]
            evidence.append(f"documented 'iddah roster key matches candidate ({', '.join(keys[:2])})")
            evidence_json["iddah_roster_keys"] = keys

    if (
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID in source_book_ids
        and node.position == 0
        and lookup.kulayni_person_id == candidate.person_id
        and MUHAMMAD_B_YAQUB in node.token_norm
        and ABU_JAFAR in node.token_norm
    ):
        score += 120
        evidence.append("al-Kafi compiler convention: Abu Ja'far Muhammad b. Ya'qub is al-Kulayni")
        evidence_json["compiler_prior"] = "al_kafi_opening_kulayni"

    return CandidateScore(
        person_id=candidate.person_id,
        score=score,
        evidence=evidence,
        evidence_json=evidence_json,
    )


def _inject_compiler_candidate(
    node: ChainNodeState,
    candidates: list[Candidate],
    lookup: ContextLookup,
    source_book_ids: set[str],
) -> list[Candidate]:
    if (
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID not in source_book_ids
        or node.position != 0
        or lookup.kulayni_person_id is None
        or MUHAMMAD_B_YAQUB not in node.token_norm
        or ABU_JAFAR not in node.token_norm
    ):
        return candidates
    if any(candidate.person_id == lookup.kulayni_person_id for candidate in candidates):
        return candidates
    return [
        Candidate(
            person_id=lookup.kulayni_person_id,
            derivation="compiler_prior",
            shared_count=1,
            matched_form=MUHAMMAD_B_YAQUB,
        )
    ] + candidates


def _interval_gap(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Layers separating two closed intervals; <= 0 when they overlap."""
    return max(a[0] - b[1], b[0] - a[1])


def _choose_winner(scores: list[CandidateScore]) -> CandidateScore | None:
    if not scores:
        return None
    # A generation-vetoed candidate is chronologically impossible — drop it
    # entirely before ranking, so it can neither win nor block a valid winner.
    scores = [s for s in scores if not s.evidence_json.get("generation_vetoed")]
    if not scores:
        return None
    scores.sort(key=lambda item: (-item.score, item.person_id))
    top = scores[0]
    second = scores[1].score if len(scores) > 1 else 0
    has_context = any(
        key in top.evidence_json
        for key in (
            "previous_edge_count",
            "next_edge_count",
            "previous_mujam_occurrences",
            "next_mujam_occurrences",
            "iddah_roster_keys",
            "compiler_prior",
        )
    )
    if has_context and top.score >= MIN_WIN_SCORE and top.score - second >= MIN_WIN_MARGIN:
        surface = top.evidence_json.get("surface") or {}
        derivation = surface.get("derivation")
        if derivation in {"first_name", "kunya"}:
            max_edge = max(
                top.evidence_json.get("previous_edge_count") or 0,
                top.evidence_json.get("next_edge_count") or 0,
            )
            mujam_support = (
                (top.evidence_json.get("previous_mujam_occurrences") or 0)
                + (top.evidence_json.get("next_mujam_occurrences") or 0)
            )
            if max_edge < 2 and mujam_support == 0:
                return None
        return top
    return None


def _replace_with_context_resolution(
    db: Session,
    node: ChainNodeState,
    winner: CandidateScore,
    scores: list[CandidateScore],
    lookup: ContextLookup,
) -> None:
    db.execute(
        delete(MentionResolution).where(
            MentionResolution.chain_node_id == node.id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        ).execution_options(synchronize_session=False)
    )
    sorted_scores = sorted(scores, key=lambda item: (-item.score, item.person_id))
    top_score = sorted_scores[0].score if sorted_scores else winner.score
    second_score = sorted_scores[1].score if len(sorted_scores) > 1 else 0
    winner_evidence_json = dict(winner.evidence_json)
    winner_evidence_json.update(
        {
            "score": winner.score,
            "second_score": second_score,
            "margin": top_score - second_score,
            "alternatives_considered": len(sorted_scores),
        }
    )
    db.add(
        MentionResolution(
            chain_node_id=node.id,
            person_id=winner.person_id,
            rank=1,
            status="resolved",
            method="collective_context",
            evidence_summary=(
                f"Resolved to {lookup.person_name_ar.get(winner.person_id)} by Phase D context: "
                + "; ".join(winner.evidence)
                + "."
            ),
            evidence_json=winner_evidence_json,
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    rank = 2
    for score in sorted_scores:
        if score.person_id == winner.person_id:
            continue
        if rank > MAX_STORED_ALTERNATES + 1:
            break
        db.add(
            MentionResolution(
                chain_node_id=node.id,
                person_id=score.person_id,
                rank=rank,
                status="ambiguous",
                method="collective_context_alternative",
                evidence_summary=(
                    f"Alternative candidate {lookup.person_name_ar.get(score.person_id)} scored {score.score}: "
                    + "; ".join(score.evidence)
                    + "."
                ),
                evidence_json={
                    **score.evidence_json,
                    "score": score.score,
                    "winner_score": winner.score,
                    "margin_to_winner": winner.score - score.score,
                },
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
        rank += 1


def _compiler_prior_target_nodes(db: Session, book_ids: list[int]):
    kafi_book_ids = [
        book_id
        for book_id, source_book_id in db.execute(
            select(Book.id, Book.source_book_id).where(Book.id.in_(book_ids))
        )
        if source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
    ]
    if not kafi_book_ids:
        return []

    return db.execute(
        select(
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token_norm"),
        )
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(
            Hadith.book_id.in_(kafi_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            ChainNode.position == 0,
            ChainNode.token_normalised.isnot(None),
            ChainNode.token_normalised.contains(ABU_JAFAR),
            ChainNode.token_normalised.contains(MUHAMMAD_B_YAQUB),
        )
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number)
    ).all()


def _resolution_rows_for_nodes(
    db: Session, node_ids: list[int]
) -> dict[int, list[MentionResolution]]:
    rows_by_node: dict[int, list[MentionResolution]] = defaultdict(list)
    for start in range(0, len(node_ids), 900):
        chunk = node_ids[start : start + 900]
        for resolution in db.execute(
            select(MentionResolution)
            .where(
                MentionResolution.chain_node_id.in_(chunk),
                MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            )
            .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
        ).scalars():
            rows_by_node[resolution.chain_node_id].append(resolution)
    return rows_by_node


def _replace_with_compiler_prior(
    db: Session,
    *,
    node_id: int,
    token_norm: str,
    existing_rows: list[MentionResolution],
    lookup: ContextLookup,
) -> None:
    kulayni_id = lookup.kulayni_person_id
    if kulayni_id is None:
        return

    db.execute(
        delete(MentionResolution).where(
            MentionResolution.chain_node_id == node_id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        ).execution_options(synchronize_session=False)
    )
    db.add(
        MentionResolution(
            chain_node_id=node_id,
            person_id=kulayni_id,
            rank=1,
            status="resolved",
            method="compiler_prior_kulayni",
            evidence_summary=(
                f"Resolved to {lookup.person_name_ar.get(kulayni_id)} by Phase D compiler prior: "
                "in al-Kafi chain openings, Abu Ja'far Muhammad b. Ya'qub is al-Kulayni."
            ),
            evidence_json={
                "phase": COLLECTIVE_REFINER_VERSION,
                "compiler_prior": "al_kafi_opening_kulayni",
                "source_book_id": AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
                "token_norm": token_norm,
            },
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )

    rank = 2
    seen = {kulayni_id}
    for row in existing_rows:
        if row.person_id is None or row.person_id in seen:
            continue
        if rank > MAX_STORED_ALTERNATES + 1:
            break
        seen.add(row.person_id)
        db.add(
            MentionResolution(
                chain_node_id=node_id,
                person_id=row.person_id,
                rank=rank,
                status="ambiguous",
                method="compiler_prior_alternative",
                evidence_summary=(
                    f"Alternative retained after al-Kafi compiler prior: "
                    f"{lookup.person_name_ar.get(row.person_id)}."
                ),
                evidence_json={
                    "phase": COLLECTIVE_REFINER_VERSION,
                    "compiler_prior": "alternative_after_kulayni_prior",
                    "previous_rank": row.rank,
                    "previous_status": row.status,
                    "previous_method": row.method,
                },
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
        rank += 1


def _replace_with_source_prior(
    db: Session,
    *,
    node_id: int,
    person_id: int,
    existing_rows: list[MentionResolution],
    lookup: ContextLookup,
    method: str,
    summary: str,
    evidence_json: dict,
) -> None:
    db.execute(
        delete(MentionResolution).where(
            MentionResolution.chain_node_id == node_id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        ).execution_options(synchronize_session=False)
    )
    db.add(
        MentionResolution(
            chain_node_id=node_id,
            person_id=person_id,
            rank=1,
            status="resolved",
            method=method,
            evidence_summary=summary,
            evidence_json=evidence_json,
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )

    rank = 2
    seen = {person_id}
    for row in existing_rows:
        if row.person_id is None or row.person_id in seen:
            continue
        if rank > MAX_STORED_ALTERNATES + 1:
            break
        seen.add(row.person_id)
        db.add(
            MentionResolution(
                chain_node_id=node_id,
                person_id=row.person_id,
                rank=rank,
                status="ambiguous",
                method=f"{method}_alternative",
                evidence_summary=(
                    f"Alternative retained after al-Kafi source prior: "
                    f"{lookup.person_name_ar.get(row.person_id)}."
                ),
                evidence_json={
                    "phase": COLLECTIVE_REFINER_VERSION,
                    "source_prior": "alternative_after_kafi_source_prior",
                    "previous_rank": row.rank,
                    "previous_status": row.status,
                    "previous_method": row.method,
                },
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
        rank += 1


def _kafi_opening_source_prior_specs(lookup: ContextLookup) -> dict[str, tuple[int, str, str]]:
    specs: dict[str, tuple[int, str, str]] = {}
    muhammad_yahya_id = _find_person_by_norms(
        lookup,
        [MUHAMMAD_B_YAHYA_ABU_JAFAR_ATTAR, MUHAMMAD_B_YAHYA_ATTAR],
    )
    if muhammad_yahya_id is not None:
        specs[MUHAMMAD_B_YAHYA] = (
            muhammad_yahya_id,
            "kafi_opening_muhammad_yahya",
            "al_kafi_opening_muhammad_yahya_attar",
        )

    ali_ibrahim_id = _find_person_by_norms(lookup, [ALI_B_IBRAHIM_B_HASHIM])
    if ali_ibrahim_id is not None:
        specs[ALI_B_IBRAHIM] = (
            ali_ibrahim_id,
            "kafi_opening_ali_ibrahim",
            "al_kafi_opening_ali_ibrahim_b_hashim",
        )
    return specs


def _kafi_opening_source_prior_target_nodes(
    db: Session,
    book_ids: list[int],
    specs: dict[str, tuple[int, str, str]],
):
    if not specs:
        return []
    kafi_book_ids = [
        book_id
        for book_id, source_book_id in db.execute(
            select(Book.id, Book.source_book_id).where(Book.id.in_(book_ids))
        )
        if source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
    ]
    if not kafi_book_ids:
        return []
    return db.execute(
        select(
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token_norm"),
        )
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(
            Hadith.book_id.in_(kafi_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            Chain.chain_number == 1,
            ChainNode.position == 0,
            ChainNode.token_normalised.in_(tuple(specs.keys())),
        )
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number)
    ).all()


def _apply_kafi_opening_source_priors(
    db: Session,
    *,
    selected_book_ids: list[int],
    lookup: ContextLookup,
    stats: CollectiveRefinementStats,
) -> None:
    specs = _kafi_opening_source_prior_specs(lookup)
    targets = _kafi_opening_source_prior_target_nodes(db, selected_book_ids, specs)
    stats.nodes_examined += len(targets)
    if not targets:
        return

    rows_by_node = _resolution_rows_for_nodes(db, [row.node_id for row in targets])
    for target in targets:
        person_id, method, prior_key = specs[target.token_norm]
        existing_rows = rows_by_node.get(target.node_id, [])
        if (
            existing_rows
            and existing_rows[0].person_id == person_id
            and existing_rows[0].status == "resolved"
            and existing_rows[0].method == method
        ):
            continue
        _replace_with_source_prior(
            db,
            node_id=target.node_id,
            person_id=person_id,
            existing_rows=existing_rows,
            lookup=lookup,
            method=method,
            summary=(
                f"Resolved to {lookup.person_name_ar.get(person_id)} by narrow al-Kafi "
                f"source-opening prior for «{target.token_norm}»."
            ),
            evidence_json={
                "phase": COLLECTIVE_REFINER_VERSION,
                "source_prior": prior_key,
                "source_book_id": AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
                "token_norm": target.token_norm,
            },
        )
        stats.nodes_resolved += 1
        stats.source_priors += 1
        stats.method_counts[method] += 1


def _apply_kafi_opening_anaphora_priors(
    db: Session,
    *,
    selected_book_ids: list[int],
    lookup: ContextLookup,
    stats: CollectiveRefinementStats,
) -> None:
    kafi_book_ids = [
        book_id
        for book_id, source_book_id in db.execute(
            select(Book.id, Book.source_book_id).where(Book.id.in_(selected_book_ids))
        )
        if source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
    ]
    if not kafi_book_ids:
        return

    rows = db.execute(
        select(
            Hadith.id.label("hadith_id"),
            Hadith.sequence_in_book.label("sequence_in_book"),
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token_norm"),
            MentionResolution.person_id.label("top_person_id"),
            MentionResolution.status.label("top_status"),
            MentionResolution.method.label("top_method"),
        )
        .join(Chain, Chain.hadith_id == Hadith.id)
        .join(ChainNode, ChainNode.chain_id == Chain.id)
        .outerjoin(
            MentionResolution,
            (
                (MentionResolution.chain_node_id == ChainNode.id)
                & (MentionResolution.resolver_version == PERSON_RESOLVER_VERSION)
                & (MentionResolution.rank == 1)
            ),
        )
        .where(
            Hadith.book_id.in_(kafi_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            Chain.chain_number == 1,
            ChainNode.position == 0,
        )
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.id)
    ).all()

    anhu_node_ids = [row.node_id for row in rows if row.token_norm == ANHU]
    stats.nodes_examined += len(anhu_node_ids)
    if not anhu_node_ids:
        return
    rows_by_node = _resolution_rows_for_nodes(db, anhu_node_ids)

    last_source_person_id: int | None = None
    for row in rows:
        if row.token_norm == ANHU:
            if last_source_person_id is None:
                continue
            existing_rows = rows_by_node.get(row.node_id, [])
            if (
                existing_rows
                and existing_rows[0].person_id == last_source_person_id
                and existing_rows[0].status == "resolved"
                and existing_rows[0].method == "kafi_opening_anaphora_previous_hadith"
            ):
                continue
            _replace_with_source_prior(
                db,
                node_id=row.node_id,
                person_id=last_source_person_id,
                existing_rows=existing_rows,
                lookup=lookup,
                method="kafi_opening_anaphora_previous_hadith",
                summary=(
                    f"Resolved opening «{ANHU}» by al-Kafi source-continuation prior: "
                    f"same opening source as the previous hadith, "
                    f"{lookup.person_name_ar.get(last_source_person_id)}."
                ),
                evidence_json={
                    "phase": COLLECTIVE_REFINER_VERSION,
                    "source_prior": "al_kafi_opening_anhu_previous_hadith",
                    "source_book_id": AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
                    "previous_source_person_id": last_source_person_id,
                },
            )
            stats.nodes_resolved += 1
            stats.anaphora_priors += 1
            stats.method_counts["kafi_opening_anaphora_previous_hadith"] += 1
            continue

        if row.top_person_id is not None and row.top_status in {"resolved", "via_collective", "latent"}:
            last_source_person_id = row.top_person_id
        else:
            last_source_person_id = None


def _apply_kafi_review_priors(
    db: Session,
    *,
    selected_book_ids: list[int],
    lookup: ContextLookup,
    stats: CollectiveRefinementStats,
) -> None:
    kafi_book_ids = [
        book_id
        for book_id, source_book_id in db.execute(
            select(Book.id, Book.source_book_id).where(Book.id.in_(selected_book_ids))
        )
        if source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
    ]
    if not kafi_book_ids:
        return

    target_ids: dict[str, int] = {}
    for spec in AL_KAFI_REVIEW_PRIORS:
        person = target_person_for_spec(db, spec)
        if person is not None:
            target_ids[spec.key] = person.id
    if not target_ids:
        return

    prior_tokens = tuple({token for spec in AL_KAFI_REVIEW_PRIORS for token in spec.tokens})
    previous = aliased(ChainNode)
    following = aliased(ChainNode)
    rows = db.execute(
        select(
            ChainNode.id.label("node_id"),
            ChainNode.token_normalised.label("token_norm"),
            ChainNode.position.label("position"),
            previous.token_normalised.label("previous_token"),
            following.token_normalised.label("next_token"),
        )
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .outerjoin(
            previous,
            (previous.chain_id == ChainNode.chain_id)
            & (previous.position == ChainNode.position - 1),
        )
        .outerjoin(
            following,
            (following.chain_id == ChainNode.chain_id)
            & (following.position == ChainNode.position + 1),
        )
        .where(
            Hadith.book_id.in_(kafi_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            ChainNode.token_normalised.in_(prior_tokens),
        )
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number, ChainNode.position)
    ).all()

    matches = []
    for row in rows:
        spec = next(
            (
                candidate
                for candidate in AL_KAFI_REVIEW_PRIORS
                if candidate.key in target_ids
                and candidate.matches(
                    token=row.token_norm,
                    position=row.position,
                    previous_token=row.previous_token,
                    next_token=row.next_token,
                )
            ),
            None,
        )
        if spec is not None:
            matches.append((row, spec))

    stats.nodes_examined += len(matches)
    rows_by_node = _resolution_rows_for_nodes(db, [row.node_id for row, _spec in matches])
    for row, spec in matches:
        person_id = target_ids[spec.key]
        existing_rows = rows_by_node.get(row.node_id, [])
        if (
            existing_rows
            and existing_rows[0].person_id == person_id
            and existing_rows[0].status == "resolved"
            and existing_rows[0].method == spec.method
        ):
            continue
        _replace_with_source_prior(
            db,
            node_id=row.node_id,
            person_id=person_id,
            existing_rows=existing_rows,
            lookup=lookup,
            method=spec.method,
            summary=(
                f"Resolved to {lookup.person_name_ar.get(person_id)} by validated "
                f"Al-Kafi external-review prior: {spec.rationale}"
            ),
            evidence_json={
                "phase": COLLECTIVE_REFINER_VERSION,
                "review_prior": spec.key,
                "source_book_id": AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
                "token_norm": row.token_norm,
                "previous_token": row.previous_token,
                "next_token": row.next_token,
                "validation": "deterministic_80_20_external_review_holdout",
            },
        )
        stats.nodes_resolved += 1
        stats.review_priors += 1
        stats.method_counts[spec.method] += 1


def refine_compiler_priors(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    commit: bool = True,
) -> CollectiveRefinementStats:
    """Apply narrow Phase D compiler-convention priors.

    This is the fast first slice of Phase D. It targets only al-Kafi opening
    nodes whose text is the known compiler convention "Abu Ja'far Muhammad b.
    Ya'qub", resolving the mention to al-Kulayni and retaining prior ranked
    candidates as alternatives. It avoids the heavier global context loop.
    """
    stats = CollectiveRefinementStats()
    selected_book_ids = _select_book_ids(
        db,
        source_book_ids or [AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID],
        book_ids,
    )
    if not selected_book_ids:
        return stats

    lookup = _build_context_lookup(db)

    targets = _compiler_prior_target_nodes(db, selected_book_ids)
    stats.nodes_examined = len(targets)
    target_ids = [row.node_id for row in targets]
    rows_by_node = _resolution_rows_for_nodes(db, target_ids)
    if lookup.kulayni_person_id is not None:
        for target in targets:
            existing_rows = rows_by_node.get(target.node_id, [])
            if (
                existing_rows
                and existing_rows[0].person_id == lookup.kulayni_person_id
                and existing_rows[0].status == "resolved"
                and existing_rows[0].method == "compiler_prior_kulayni"
            ):
                continue
            _replace_with_compiler_prior(
                db,
                node_id=target.node_id,
                token_norm=target.token_norm,
                existing_rows=existing_rows,
                lookup=lookup,
            )
            stats.nodes_resolved += 1
            stats.compiler_priors += 1
            stats.method_counts["compiler_prior_kulayni"] += 1

    _apply_kafi_opening_source_priors(
        db,
        selected_book_ids=selected_book_ids,
        lookup=lookup,
        stats=stats,
    )
    db.flush()
    _apply_kafi_review_priors(
        db,
        selected_book_ids=selected_book_ids,
        lookup=lookup,
        stats=stats,
    )
    db.flush()
    _apply_kafi_opening_anaphora_priors(
        db,
        selected_book_ids=selected_book_ids,
        lookup=lookup,
        stats=stats,
    )

    if commit:
        db.commit()
    return stats


@dataclass(frozen=True)
class ImamKunyaPrior:
    """A shared-kunya Ma'sum tie-break grounded in isnad convention."""

    key: str  # evidence key, e.g. "abu_abdallah_sadiq"
    target_norm: str  # canonical_name_norm of the conventional Imam
    alternate_norms: tuple[str, ...]  # same-kunya Ma'sum(in), kept ranked
    blocker_substrings: tuple[str, ...]  # normalised laqab that routes elsewhere -> abstain
    kunya_label: str  # human-readable kunya, for the dalil
    rationale: str


IMAM_KUNYA_PRIORS: tuple[ImamKunyaPrior, ...] = (
    ImamKunyaPrior(
        key="abu_abdallah_sadiq",
        target_norm=SADIQ_NORM,
        alternate_norms=(HUSAYN_NORM,),
        blocker_substrings=(_n("الحسين"), _n("سيد الشهداء")),
        kunya_label="أبو عبد الله ع",
        rationale=(
            "in the Four Books' asanid a bare «أبو عبد الله ع» is Imam Ja'far "
            "al-Sadiq; al-Husayn (Sayyid al-Shuhada) is named explicitly when meant"
        ),
    ),
    ImamKunyaPrior(
        key="abu_jafar_baqir",
        target_norm=BAQIR_NORM,
        alternate_norms=(JAWAD_NORM,),
        blocker_substrings=(_n("الجواد"), _n("الثاني")),
        kunya_label="أبو جعفر ع",
        rationale=(
            "in the Four Books' asanid a bare «أبو جعفر ع» is Imam Muhammad "
            "al-Baqir; al-Jawad is distinguished as «أبو جعفر الثاني»"
        ),
    ),
)


def _load_masum_person_index(db: Session) -> tuple[dict[str, int], dict[int, str]]:
    """(canonical_name_norm -> person_id, person_id -> canonical_name_ar) for Ma'sumin."""
    id_by_norm: dict[str, int] = {}
    name_ar: dict[int, str] = {}
    for pid, norm, ar in db.execute(
        select(Person.id, Person.canonical_name_norm, Person.canonical_name_ar).where(
            Person.kind == "masum"
        )
    ):
        id_by_norm[norm] = pid
        name_ar[pid] = ar
    return id_by_norm, name_ar


def _replace_with_imam_kunya_prior(
    db: Session,
    *,
    node_id: int,
    target_id: int,
    spec: ImamKunyaPrior,
    existing_rows: list[MentionResolution],
    name_ar: dict[int, str],
) -> None:
    """Resolve an imam node to the conventional Imam, keeping same-kunya alternates ranked."""
    db.execute(
        delete(MentionResolution)
        .where(
            MentionResolution.chain_node_id == node_id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        )
        .execution_options(synchronize_session=False)
    )
    db.add(
        MentionResolution(
            chain_node_id=node_id,
            person_id=target_id,
            rank=1,
            status="resolved",
            method="imam_kunya_prior",
            evidence_summary=(
                f"Resolved «{spec.kunya_label}» to {name_ar.get(target_id)} by "
                f"isnad-convention prior: {spec.rationale}."
            ),
            evidence_json={
                "phase": COLLECTIVE_REFINER_VERSION,
                "imam_kunya_prior": spec.key,
                "kunya": spec.kunya_label,
            },
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    rank = 2
    seen = {target_id}
    for row in existing_rows:
        if row.person_id is None or row.person_id in seen:
            continue
        if rank > MAX_STORED_ALTERNATES + 1:
            break
        seen.add(row.person_id)
        db.add(
            MentionResolution(
                chain_node_id=node_id,
                person_id=row.person_id,
                rank=rank,
                status="ambiguous",
                method="imam_kunya_prior_alternative",
                evidence_summary=(
                    f"Alternative retained after isnad-convention prior "
                    f"«{spec.kunya_label}»: {name_ar.get(row.person_id)} shares the kunya "
                    f"but is not the conventional isnad source."
                ),
                evidence_json={
                    "phase": COLLECTIVE_REFINER_VERSION,
                    "imam_kunya_prior": f"alternative_after_{spec.key}",
                    "previous_rank": row.rank,
                    "previous_status": row.status,
                    "previous_method": row.method,
                },
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
        rank += 1


def refine_imam_kunya_priors(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    commit: bool = True,
) -> CollectiveRefinementStats:
    """Break shared-kunya Ma'sum ambiguity by isnad convention (Phase D).

    Targets imam-type nodes still ambiguous between exactly the two Ma'sumin who
    share a kunya («أبو عبد الله ع» = al-Sadiq vs al-Husayn; «أبو جعفر ع» =
    al-Baqir vs al-Jawad) and resolves them to the conventional Imam, retaining
    the same-kunya alternate as a ranked alternative. This is lattice-independent
    — it does not consult ``person_generations`` — so it is unaffected by noisy
    propagated generation points that mis-drive the tabaqat disambiguator. It
    edits only ``mention_resolutions`` for the selected books.
    """
    stats = CollectiveRefinementStats()
    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    if not selected_book_ids:
        return stats

    id_by_norm, name_ar = _load_masum_person_index(db)
    resolved_specs: list[tuple[ImamKunyaPrior, int, frozenset[int]]] = []
    for spec in IMAM_KUNYA_PRIORS:
        target_id = id_by_norm.get(spec.target_norm)
        if target_id is None:
            continue
        alt_ids = [id_by_norm[a] for a in spec.alternate_norms if a in id_by_norm]
        expected = frozenset({target_id, *alt_ids})
        resolved_specs.append((spec, target_id, expected))
    if not resolved_specs:
        return stats

    node_rows = db.execute(
        select(ChainNode.id, ChainNode.token_normalised)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(
            Hadith.book_id.in_(selected_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            ChainNode.node_type == "imam",
        )
        .order_by(Hadith.book_id, Hadith.sequence_in_book, Chain.chain_number, ChainNode.position)
    ).all()
    if not node_rows:
        return stats

    node_ids = [row.id for row in node_rows]
    token_by_node = {row.id: row.token_normalised or "" for row in node_rows}
    rows_by_node = _resolution_rows_for_nodes(db, node_ids)

    for node_id in node_ids:
        rows = rows_by_node.get(node_id, [])
        if len(rows) < 2 or not all(row.status == "ambiguous" for row in rows):
            continue
        masum_cands = frozenset(row.person_id for row in rows if row.person_id in name_ar)
        for spec, target_id, expected in resolved_specs:
            if masum_cands != expected:
                continue
            stats.nodes_examined += 1
            token_norm = _n(token_by_node.get(node_id, ""))
            if any(blocker in token_norm for blocker in spec.blocker_substrings):
                break
            _replace_with_imam_kunya_prior(
                db,
                node_id=node_id,
                target_id=target_id,
                spec=spec,
                existing_rows=rows,
                name_ar=name_ar,
            )
            stats.nodes_resolved += 1
            stats.method_counts["imam_kunya_prior"] += 1
            stats.method_counts[spec.key] += 1
            break

    # Flush so a following pass in the same session (SessionLocal has
    # autoflush=False) sees these resolutions — the anaphora propagation depends
    # on each report's terminal Imam being visible.
    db.flush()
    if commit:
        db.commit()
    return stats


def _resolve_anaphora_imam_node(
    db: Session,
    *,
    node_id: int,
    imam_id: int,
    name_ar: dict[int, str],
    previous_hadith_id: int | None,
) -> None:
    db.execute(
        delete(MentionResolution)
        .where(
            MentionResolution.chain_node_id == node_id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        )
        .execution_options(synchronize_session=False)
    )
    db.add(
        MentionResolution(
            chain_node_id=node_id,
            person_id=imam_id,
            rank=1,
            status="resolved",
            method="anaphora_imam_after_kunya_prior",
            evidence_summary=(
                f"Pronoun refers to the Imam of the preceding report, now resolved by "
                f"the kunya prior: {name_ar.get(imam_id)}."
            ),
            evidence_json={
                "phase": COLLECTIVE_REFINER_VERSION,
                "anaphora": "previous_hadith_imam_after_kunya_prior",
                "previous_hadith_id": previous_hadith_id,
            },
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )


def refine_previous_hadith_imam_anaphora(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    commit: bool = True,
) -> CollectiveRefinementStats:
    """Resolve «previous_hadith_imam» pronouns to the preceding report's Imam.

    Faqih's serial direct-question form («وَ سَأَلَهُ فلان عن كذا فقال ...») names
    the questioner but leaves the Imam as the object pronoun «ـه», tokenized as a
    `previous_hadith_imam` pronoun. Phase B could not resolve it while the
    preceding report's «أبو عبد الله ع» was still ambiguous; run this AFTER
    `refine_imam_kunya_priors` so the chain of Imams propagates report to report.
    Only fires on a chain-terminal pronoun whose preceding report has a uniquely
    resolved terminal Imam. Edits `mention_resolutions` for the selected books only.
    """
    stats = CollectiveRefinementStats()
    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    if not selected_book_ids:
        return stats

    _, name_ar = _load_masum_person_index(db)
    masum_ids = set(name_ar)

    ordered_hadith_ids = [
        hid
        for (hid,) in db.execute(
            select(Hadith.id)
            .where(
                Hadith.book_id.in_(selected_book_ids),
                Hadith.review_status != REJECTED_HADITH_STATUS,
            )
            .order_by(Hadith.book_id, Hadith.sequence_in_book, Hadith.id)
        )
    ]
    if not ordered_hadith_ids:
        return stats

    # Terminal (max-position) node of every chain, with its rank-1 resolution.
    rows = db.execute(
        select(
            Chain.hadith_id,
            Chain.id,
            ChainNode.id,
            ChainNode.position,
            ChainNode.node_type,
            ChainNode.relation_kind,
            MentionResolution.person_id,
            MentionResolution.status,
        )
        .join(ChainNode, ChainNode.chain_id == Chain.id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .outerjoin(
            MentionResolution,
            (MentionResolution.chain_node_id == ChainNode.id)
            & (MentionResolution.rank == 1)
            & (MentionResolution.resolver_version == PERSON_RESOLVER_VERSION),
        )
        .where(Hadith.book_id.in_(selected_book_ids))
        .order_by(Chain.id, ChainNode.position)
    ).all()

    # Per chain keep only the terminal node.
    terminal_by_chain: dict[int, tuple] = {}
    for hadith_id, chain_id, node_id, position, ntype, rel, person_id, status in rows:
        cur = terminal_by_chain.get(chain_id)
        if cur is None or position > cur[1]:
            terminal_by_chain[chain_id] = (hadith_id, position, node_id, ntype, rel, person_id, status)
    terminals_by_hadith: dict[int, list[tuple]] = defaultdict(list)
    for hadith_id, position, node_id, ntype, rel, person_id, status in terminal_by_chain.values():
        terminals_by_hadith[hadith_id].append((node_id, ntype, rel, person_id, status))

    terminal_imam: dict[int, int | None] = {}
    previous_hid: int | None = None
    for hid in ordered_hadith_ids:
        chosen: set[int] = set()
        for node_id, ntype, rel, person_id, status in terminals_by_hadith.get(hid, []):
            if rel == "previous_hadith_imam" and status != "resolved":
                stats.nodes_examined += 1
                anchor = terminal_imam.get(previous_hid) if previous_hid is not None else None
                if anchor is not None:
                    _resolve_anaphora_imam_node(
                        db,
                        node_id=node_id,
                        imam_id=anchor,
                        name_ar=name_ar,
                        previous_hadith_id=previous_hid,
                    )
                    stats.nodes_resolved += 1
                    stats.method_counts["anaphora_imam_after_kunya_prior"] += 1
                    chosen.add(anchor)
            elif (
                (ntype == "imam" or rel == "previous_hadith_imam")
                and status == "resolved"
                and person_id in masum_ids
            ):
                chosen.add(person_id)
        terminal_imam[hid] = next(iter(chosen)) if len(chosen) == 1 else None
        previous_hid = hid

    if commit:
        db.commit()
    return stats


def _expand_roster_for_node(
    db: Session,
    *,
    node: ChainNodeState,
    next_people: list[int],
    lookup: ContextLookup,
) -> int:
    if not node.is_collective or not next_people:
        return 0
    if IDDAH not in node.token_norm and JAMAAH not in node.token_norm:
        return 0

    members: list[tuple[int, str, str, int, int]] = []
    for key_person in next_people:
        for member_pid, member_name_ar, citation, confidence in lookup.roster_members_by_key_person.get(key_person, []):
            members.append((member_pid, member_name_ar, citation, confidence, key_person))
    if not members:
        return 0

    existing_people = {row.person_id for row in node.rows if row.person_id is not None}
    new_members = [member for member in members if member[0] not in existing_people]
    if not new_members:
        return 0

    # Keep existing named-member rows, remove unresolved placeholder rows.
    for row in list(node.rows):
        if row.status == "unresolved":
            db.delete(row)
    db.flush()

    rank_start = max((row.rank for row in node.rows), default=0) + 1
    for offset, (member_pid, member_name_ar, citation, confidence, key_person) in enumerate(new_members):
        db.add(
            MentionResolution(
                chain_node_id=node.id,
                person_id=member_pid,
                rank=rank_start + offset,
                status="via_collective",
                method="collective_roster_after_context",
                evidence_summary=(
                    f"Documented 'iddah roster member after Phase D keyed by "
                    f"{lookup.person_name_ar.get(key_person)}: {member_name_ar}. Source: {citation}."
                ),
                evidence_json={
                    "phase": COLLECTIVE_REFINER_VERSION,
                    "roster_key_person_id": key_person,
                    "source": citation,
                    "confidence": confidence,
                },
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
    return len(new_members)


def refine_with_collective_context(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    on_progress: ProgressCallback | None = None,
    commit: bool = True,
) -> CollectiveRefinementStats:
    """Refine ambiguous person mentions using global corpus context.

    Run after ``build-person-layer -> resolve-persons -> build-tabaqat ->
    refine-tabaqat``. Mutates ``mention_resolutions`` for the selected books
    only, keeping the public resolver version constant so the API/UI sees the
    latest person-level result.
    """
    stats = CollectiveRefinementStats()
    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    if not selected_book_ids:
        return stats

    source_ids = _selected_book_source_ids(db, selected_book_ids)
    lookup = _build_context_lookup(db)
    chains = _chain_states(db, selected_book_ids)
    edge_counts = _edge_counts(chains)
    teachers_by_student, students_by_teacher = _edge_support_indexes(edge_counts)
    candidate_cache: dict[str, list[Candidate]] = {}

    total = sum(len(nodes) for nodes in chains)
    seen = 0
    for nodes in chains:
        for index, node in enumerate(nodes):
            seen += 1
            if on_progress and seen % 2000 == 0:
                on_progress("phase-d refine", seen, total)
            if not node.is_ambiguous:
                continue
            stats.nodes_examined += 1
            previous_node = nodes[index - 1] if index > 0 else None
            next_node = nodes[index + 1] if index + 1 < len(nodes) else None
            previous_people = previous_node.resolved_people if previous_node else []
            next_people = next_node.resolved_people if next_node else []
            supported_ids: set[int] = set()
            for previous in previous_people:
                supported_ids.update(teachers_by_student.get(previous, set()))
            for nxt in next_people:
                supported_ids.update(students_by_teacher.get(nxt, set()))

            compiler_case = (
                AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID in source_ids
                and node.position == 0
                and lookup.kulayni_person_id is not None
                and MUHAMMAD_B_YAQUB in node.token_norm
                and ABU_JAFAR in node.token_norm
            )
            roster_case = bool(
                previous_node
                and previous_node.is_collective
                and (IDDAH in previous_node.token_norm or JAMAAH in previous_node.token_norm)
            )
            if not supported_ids and not compiler_case and not roster_case:
                stats.skipped_weak_margin += 1
                continue

            if node.token_norm not in candidate_cache:
                candidate_cache[node.token_norm] = expanded_candidates(node.token_norm, lookup)
            candidates = candidate_cache[node.token_norm]
            candidates = _inject_compiler_candidate(node, candidates, lookup, source_ids)
            if supported_ids or roster_case or compiler_case:
                candidates = [
                    candidate for candidate in candidates
                    if candidate.person_id in supported_ids
                    or (compiler_case and candidate.person_id == lookup.kulayni_person_id)
                    or (roster_case and candidate.person_id in lookup.roster_keys_by_person)
                ]
            if not candidates:
                stats.skipped_weak_margin += 1
                continue

            scores = [
                _score_candidate(
                    candidate,
                    previous_people=previous_people,
                    next_people=next_people,
                    previous_node=previous_node,
                    node=node,
                    edge_counts=edge_counts,
                    lookup=lookup,
                    source_book_ids=source_ids,
                )
                for candidate in candidates
            ]
            winner = _choose_winner(scores)
            if winner is None:
                stats.skipped_weak_margin += 1
                continue
            _replace_with_context_resolution(db, node, winner, scores, lookup)
            stats.nodes_resolved += 1
            if winner.evidence_json.get("compiler_prior"):
                stats.compiler_priors += 1
                stats.method_counts["compiler_prior"] += 1
            else:
                stats.context_resolved += 1
                stats.method_counts["collective_context"] += 1
            # Keep in-memory state useful for following collective nodes in the
            # same run.
            node.rows = [
                MentionResolution(
                    chain_node_id=node.id,
                    person_id=winner.person_id,
                    rank=1,
                    status="resolved",
                    method="collective_context",
                    evidence_summary="",
                    resolver_version=PERSON_RESOLVER_VERSION,
                )
            ]

    # Second pass: expand collective rosters now that some following bare
    # narrators may have a resolved person.
    for nodes in chains:
        for index, node in enumerate(nodes):
            if not node.is_collective or index + 1 >= len(nodes):
                continue
            next_people = nodes[index + 1].resolved_people
            added = _expand_roster_for_node(db, node=node, next_people=next_people, lookup=lookup)
            if added:
                stats.roster_expanded_nodes += 1
                stats.roster_rows_added += added
                stats.method_counts["collective_roster_after_context"] += added

    if commit:
        db.commit()
    return stats
