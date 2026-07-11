"""Evaluate person-resolution quality against independent gold signals.

The Tamyiz Engine (Phases A-D) produces person-level identity claims in
`mention_resolutions`. Every phase so far closed with an `alkafi-1`
spot-check and a green test suite, but nobody has *measured* whether the
resolver's person assignments agree with the masters. This module is that
measurement. It is read-only.

It scores four things, each honest about what it can and cannot prove:

1. Coverage. Status distribution of rank-1 person resolutions by node type.
   Descriptive, not a quality claim on its own.

2. Bare-form leak invariant (HARD). The plan forbids ever presenting a
   `bare_form_proxy` person («أحمد بن محمد») as a resolved identity — a bare
   mention must surface its fuller-named claimants, never the proxy. Any
   rank-1 `resolved` row pointing at a proxy person is a real bug. Target: 0.

3. Generation monotonicity. A chain is a descending walk from the compiler to
   the Imam, so for an adjacent (student -> teacher) edge the teacher must not
   sit in a strictly *later* generation than the student. Interval-incompatible
   edges (teacher gen_lo > student gen_hi) are suspect resolutions.

4. Mu'jam edge corroboration (the core). al-Khoei's `rijal_occurrences` list,
   per narrator, who they narrated from and who narrated from them — an
   independent attestation of teacher/student edges. For each confident
   adjacent person edge the resolver asserts in this book, we ask whether
   al-Khoei documents it. Because his lists are not exhaustive, absence of a
   match is only counted against us when the endpoint is well attested;
   otherwise it is set aside as under-documented. The reported rate is a floor:
   matching is exact-normalised-string, so it under-counts, never inflates.

The actionable output is the list of *contradicted* edges (well-attested
endpoint, no documented match) and generation violations — concrete candidate
mis-resolutions to review, not just a headline number.
"""

from __future__ import annotations

import dataclasses
from collections import Counter, defaultdict

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Person,
    PersonGeneration,
    PersonSurfaceForm,
    RijalEntry,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.identity_links import same_person_clusters

_REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"
DEFAULT_RESOLVER_VERSION = "tamyiz_b1"
CONFIDENT_STATUSES = ("resolved", "via_collective")

# An endpoint with at least this many documented Mu'jam occurrences is treated
# as "well attested", so a missing edge counts as a contradiction rather than
# mere absence of evidence.
WELL_ATTESTED_MIN_OCCURRENCES = 6
_SAMPLE_CAP = 25

# Generation methods whose interval is derived from a real anchor (a fixed Imam
# layer or an Imam-companionship statement) rather than pure propagation. Only
# these are trustworthy enough to declare an edge chronologically *impossible*.
# A generation-lattice audit (2026-07-11) showed 493 of 496 raw violations were
# propagation noise on unanchored hub narrators (e.g. Ibn Abi Umayr), not wrong
# identities — so propagated-only intervals are advisory, never a hard verdict.
RELIABLE_GEN_METHODS = frozenset({"imam_fixed", "ashab_anchor", "anchor_and_propagated"})
# Anchors carry a soft +/-1 width, so a one-layer overshoot (a companion who
# narrated from two adjacent Imams) is boundary noise, not a real violation.
GEN_VIOLATION_TOLERANCE = 1


@dataclasses.dataclass
class EvalReport:
    source_book_id: str
    resolver_version: str

    # Coverage
    total_nodes: int
    status_counts: dict[str, int]
    node_type_status: dict[str, dict[str, int]]

    # Invariant 2: bare-form leaks
    bareform_leaks: int
    bareform_leak_samples: list[dict]

    # Metric 3: generation monotonicity
    gen_edges_checked: int
    gen_violations: int
    gen_violation_samples: list[dict]
    # Reliable subset: only anchor-derived generations, with soft tolerance.
    reliable_gen_edges_checked: int
    reliable_gen_violations: int
    reliable_gen_violation_samples: list[dict]

    # Metric 4: Mu'jam edge corroboration
    edges_confident: int
    edges_both_mujam: int
    corroborated: int
    contradicted: int
    under_documented: int
    corroboration_rate: float | None
    contradiction_samples: list[dict]

    def format_text(self) -> str:
        lines: list[str] = []
        a = lines.append
        a(f"Person-resolution eval — source_book_id={self.source_book_id} "
          f"(resolver_version={self.resolver_version})")
        a("")
        a(f"[1] Coverage — {self.total_nodes} chain nodes")
        for status, count in sorted(self.status_counts.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * count / self.total_nodes if self.total_nodes else 0.0
            a(f"    {status:<14} {count:>7}  ({pct:4.1f}%)")
        a("    by node_type (resolved / confident-total / all):")
        for ntype in sorted(self.node_type_status):
            row = self.node_type_status[ntype]
            confident = row.get("resolved", 0) + row.get("via_collective", 0)
            total = sum(row.values())
            a(f"      {ntype:<18} {row.get('resolved', 0):>6} / {confident:>6} / {total:>6}")
        a("")
        verdict = "PASS" if self.bareform_leaks == 0 else "FAIL"
        a(f"[2] Bare-form leak invariant: {self.bareform_leaks} leak(s)  [{verdict}]")
        for s in self.bareform_leak_samples[:8]:
            a(f"      node {s['chain_node_id']} '{s['token']}' -> proxy person "
              f"{s['person_id']} '{s['person_name']}'")
        a("")
        a(f"[3] Generation monotonicity: {self.gen_violations} raw violation(s) "
          f"of {self.gen_edges_checked} gen-checkable edge(s)")
        a(f"      RELIABLE (anchor-derived only): {self.reliable_gen_violations} "
          f"violation(s) of {self.reliable_gen_edges_checked} edge(s)  <-- the gate")
        for s in self.reliable_gen_violation_samples[:8]:
            a(f"      {s['hadith']}: student '{s['student']}' gen{s['student_gen']} "
              f"<- teacher '{s['teacher']}' gen{s['teacher_gen']} (teacher later than student)")
        a("")
        rate = ("n/a" if self.corroboration_rate is None
                else f"{100.0 * self.corroboration_rate:.1f}%")
        a(f"[4] Mu'jam edge corroboration (floor): {rate}")
        a(f"      confident adjacent edges: {self.edges_confident}")
        a(f"      both endpoints have Mu'jam entry: {self.edges_both_mujam}")
        a(f"      corroborated: {self.corroborated}")
        a(f"      contradicted (well-attested, unmatched): {self.contradicted}")
        a(f"      set aside (endpoint under-documented): {self.under_documented}")
        a("      sample contradicted edges (candidate mis-resolutions):")
        for s in self.contradiction_samples[:12]:
            a(f"        {s['hadith']}: '{s['student']}' -> '{s['teacher']}'  "
              f"(teacher documents {s['teacher_doc']} edges, student {s['student_doc']})")
        return "\n".join(lines)


def _norm(text: str | None) -> str:
    return normalise_arabic_persian(text or "").strip()


def _classify_corroboration(
    s_forms: set[str],
    t_forms: set[str],
    s_narrators: set[int],
    t_narrators: set[int],
    narrates_from: dict[int, set[str]],
    narrated_by: dict[int, set[str]],
) -> tuple[str, int, int]:
    """The Mu'jam verdict for one student->teacher edge.

    Shared by the standalone eval report and the graph's `quality=1` overlay so
    the two can't disagree. Returns (verdict, teacher_doc_count, student_doc_count)
    where verdict is corroborated | contradicted | under_documented | no_mujam.
    """
    if not s_narrators or not t_narrators:
        return "no_mujam", 0, 0
    t_students: set[str] = set()  # who narrates FROM the teacher
    t_teachers: set[str] = set()
    for narrator_id in t_narrators:
        t_students.update(narrated_by.get(narrator_id, set()))
        t_teachers.update(narrates_from.get(narrator_id, set()))
    s_teachers: set[str] = set()  # who the student narrates FROM
    s_students: set[str] = set()
    for narrator_id in s_narrators:
        s_teachers.update(narrates_from.get(narrator_id, set()))
        s_students.update(narrated_by.get(narrator_id, set()))

    teacher_doc = len(t_students) + len(t_teachers)
    student_doc = len(s_teachers) + len(s_students)
    matched = bool(s_forms & t_students) or bool(t_forms & s_teachers)
    if matched:
        return "corroborated", teacher_doc, student_doc
    if teacher_doc >= WELL_ATTESTED_MIN_OCCURRENCES or student_doc >= WELL_ATTESTED_MIN_OCCURRENCES:
        return "contradicted", teacher_doc, student_doc
    return "under_documented", teacher_doc, student_doc


@dataclasses.dataclass(frozen=True)
class EdgeQuality:
    """Per-edge evidence verdict for the graph quality overlay."""

    corroboration: str  # corroborated | contradicted | under_documented | no_mujam
    gen_violation: bool | None  # None when neither endpoint has a known generation


def score_person_edges(
    db: Session,
    pairs: set[tuple[int, int]],
    *,
    clusters: dict[int, set[int]] | None = None,
) -> dict[tuple[int, int], EdgeQuality]:
    """Score a set of (student_person_id, teacher_person_id) edges.

    `pairs` are cluster-root person ids as the graph reports them. Clusters are
    re-derived from the endpoints (cheap: a few hundred) so each root expands to
    its full same-person cluster for surface-form/narrator/generation lookup —
    the `clusters` argument is accepted for symmetry but the closure is always
    recomputed to stay correct even when a root is a non-mention person.
    """
    if not pairs:
        return {}
    endpoint_ids = {pid for pair in pairs for pid in pair}
    clusters = same_person_clusters(db, endpoint_ids)
    member_ids = set(endpoint_ids)
    for members in clusters.values():
        member_ids.update(members)

    person_index = _load_person_index(db, member_ids)
    surface_forms = _load_surface_forms(db, member_ids)
    # Only anchor-derived generations may declare an edge impossible on the graph.
    generations = _load_generations(db, member_ids, reliable_only=True)
    narrator_ids = {
        p["narrator_id"] for p in person_index.values() if p["narrator_id"] is not None
    }
    narrates_from, narrated_by = _load_occurrence_edges(db, narrator_ids)

    def members_of(pid: int) -> set[int]:
        return clusters.get(pid, {pid})

    def cluster_forms(pid: int) -> set[str]:
        forms: set[str] = set()
        for member in members_of(pid):
            forms.update(surface_forms.get(member, set()))
            pinfo = person_index.get(member)
            if pinfo:
                forms.add(pinfo["name_norm"])
        return forms

    def cluster_narrators(pid: int) -> set[int]:
        out: set[int] = set()
        for member in members_of(pid):
            narrator_id = person_index.get(member, {}).get("narrator_id")
            if narrator_id is not None:
                out.add(narrator_id)
        return out

    def cluster_generation(pid: int) -> tuple[int, int] | None:
        ranges = [generations[m] for m in members_of(pid) if m in generations]
        if not ranges:
            return None
        return min(lo for lo, _ in ranges), max(hi for _, hi in ranges)

    result: dict[tuple[int, int], EdgeQuality] = {}
    for s_pid, t_pid in pairs:
        sg = cluster_generation(s_pid)
        tg = cluster_generation(t_pid)
        edge_gen_violation = gen_violation(sg, tg)
        verdict, _, _ = _classify_corroboration(
            cluster_forms(s_pid),
            cluster_forms(t_pid),
            cluster_narrators(s_pid),
            cluster_narrators(t_pid),
            narrates_from,
            narrated_by,
        )
        result[(s_pid, t_pid)] = EdgeQuality(corroboration=verdict, gen_violation=edge_gen_violation)
    return result


def _load_nodes(db: Session, source_book_id: str, resolver_version: str) -> list[dict]:
    """rank-1 person resolution for every non-rejected chain node in the book."""
    stmt = (
        select(
            ChainNode.id,
            ChainNode.chain_id,
            ChainNode.position,
            ChainNode.node_type,
            ChainNode.raw_token,
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
    nodes = []
    for node_id, chain_id, pos, ntype, token, status, person_id in db.execute(stmt):
        nodes.append(
            {
                "id": node_id,
                "chain_id": chain_id,
                "position": pos,
                "node_type": ntype,
                "token": token,
                "status": status or "missing",
                "person_id": person_id,
            }
        )
    return nodes


def _load_person_index(db: Session, person_ids: set[int]) -> dict[int, dict]:
    """kind, canonical name, and the Mu'jam narrator_id (via primary entry)."""
    if not person_ids:
        return {}
    index: dict[int, dict] = {}
    stmt = (
        select(Person.id, Person.kind, Person.canonical_name_ar, Person.canonical_name_norm,
               RijalEntry.narrator_id)
        .select_from(Person)
        .outerjoin(RijalEntry, RijalEntry.id == Person.primary_entry_id)
        .where(Person.id.in_(person_ids))
    )
    for pid, kind, name_ar, name_norm, narrator_id in db.execute(stmt):
        index[pid] = {
            "kind": kind,
            "name": name_ar,
            "name_norm": name_norm,
            "narrator_id": narrator_id,
        }
    return index


def _load_surface_forms(db: Session, person_ids: set[int]) -> dict[int, set[str]]:
    forms: dict[int, set[str]] = defaultdict(set)
    if not person_ids:
        return forms
    stmt = select(PersonSurfaceForm.person_id, PersonSurfaceForm.form_norm).where(
        PersonSurfaceForm.person_id.in_(person_ids)
    )
    for pid, form_norm in db.execute(stmt):
        forms[pid].add(_norm(form_norm))
    return forms


def _load_occurrence_edges(
    db: Session, narrator_ids: set[int]
) -> tuple[dict[int, set[str]], dict[int, set[str]]]:
    """Per narrator: normalised names they narrate FROM and are narrated BY."""
    narrates_from: dict[int, set[str]] = defaultdict(set)
    narrated_by: dict[int, set[str]] = defaultdict(set)
    if not narrator_ids:
        return narrates_from, narrated_by
    stmt = select(
        RijalOccurrence.narrator_id,
        RijalOccurrence.direction,
        RijalOccurrence.related_name_normalised,
    ).where(RijalOccurrence.narrator_id.in_(narrator_ids))
    for narrator_id, direction, related_norm in db.execute(stmt):
        if narrator_id is None:
            continue
        name = _norm(related_norm)
        if not name:
            continue
        if direction == "narrates_from":
            narrates_from[narrator_id].add(name)
        elif direction == "narrated_by":
            narrated_by[narrator_id].add(name)
    return narrates_from, narrated_by


def _load_generations(
    db: Session, person_ids: set[int], *, reliable_only: bool = False
) -> dict[int, tuple[int, int]]:
    """Person -> (gen_lo, gen_hi).

    Always excludes self-contradictory (`conflict`) rows. With `reliable_only`,
    restricts further to anchor-derived methods (`RELIABLE_GEN_METHODS`) so the
    caller can make a HARD chronological-impossibility claim; propagated-only
    intervals are advisory and must not drive such a claim.
    """
    gens: dict[int, tuple[int, int]] = {}
    if not person_ids:
        return gens
    method_filter = (
        PersonGeneration.method.in_(RELIABLE_GEN_METHODS)
        if reliable_only
        else PersonGeneration.method != "conflict"
    )
    stmt = select(
        PersonGeneration.person_id, PersonGeneration.gen_lo, PersonGeneration.gen_hi
    ).where(
        PersonGeneration.person_id.in_(person_ids),
        method_filter,
    )
    for pid, lo, hi in db.execute(stmt):
        gens[pid] = (lo, hi)
    return gens


def gen_violation(student_gen: tuple[int, int] | None, teacher_gen: tuple[int, int] | None) -> bool | None:
    """Is this a chronology violation? teacher strictly later than student, past
    the soft-anchor tolerance. None when either endpoint has no usable generation."""
    if not student_gen or not teacher_gen:
        return None
    return teacher_gen[0] > student_gen[1] + GEN_VIOLATION_TOLERANCE


def evaluate_resolution(
    db: Session,
    source_book_id: str,
    *,
    resolver_version: str = DEFAULT_RESOLVER_VERSION,
) -> EvalReport:
    nodes = _load_nodes(db, source_book_id, resolver_version)
    total_nodes = len(nodes)

    status_counts: Counter[str] = Counter()
    node_type_status: dict[str, Counter[str]] = defaultdict(Counter)
    for n in nodes:
        status_counts[n["status"]] += 1
        node_type_status[n["node_type"]][n["status"]] += 1

    person_ids = {n["person_id"] for n in nodes if n["person_id"] is not None}
    clusters = same_person_clusters(db, person_ids)
    cluster_person_ids = set(person_ids)
    for members in clusters.values():
        cluster_person_ids.update(members)

    person_index = _load_person_index(db, cluster_person_ids)
    surface_forms = _load_surface_forms(db, cluster_person_ids)
    generations = _load_generations(db, cluster_person_ids)
    generations_reliable = _load_generations(db, cluster_person_ids, reliable_only=True)

    narrator_ids = {
        p["narrator_id"] for p in person_index.values() if p["narrator_id"] is not None
    }
    narrates_from, narrated_by = _load_occurrence_edges(db, narrator_ids)

    def _cluster_members(person_id: int) -> set[int]:
        return clusters.get(person_id, {person_id})

    def _cluster_forms(person_id: int) -> set[str]:
        forms: set[str] = set()
        for pid in _cluster_members(person_id):
            forms.update(surface_forms.get(pid, set()))
            pinfo = person_index.get(pid)
            if pinfo:
                forms.add(pinfo["name_norm"])
        return forms

    def _cluster_narrators(person_id: int) -> set[int]:
        narrators: set[int] = set()
        for pid in _cluster_members(person_id):
            narrator_id = person_index.get(pid, {}).get("narrator_id")
            if narrator_id is not None:
                narrators.add(narrator_id)
        return narrators

    def _cluster_generation(person_id: int) -> tuple[int, int] | None:
        ranges = [
            generations[pid]
            for pid in _cluster_members(person_id)
            if pid in generations
        ]
        if not ranges:
            return None
        return min(lo for lo, _ in ranges), max(hi for _, hi in ranges)

    def _cluster_generation_reliable(person_id: int) -> tuple[int, int] | None:
        ranges = [
            generations_reliable[pid]
            for pid in _cluster_members(person_id)
            if pid in generations_reliable
        ]
        if not ranges:
            return None
        return min(lo for lo, _ in ranges), max(hi for _, hi in ranges)

    # ---- Invariant 2: bare-form leaks ----
    bareform_leak_samples: list[dict] = []
    bareform_leaks = 0
    for n in nodes:
        if n["status"] != "resolved" or n["person_id"] is None:
            continue
        pinfo = person_index.get(n["person_id"])
        if pinfo and pinfo["kind"] == "bare_form_proxy":
            bareform_leaks += 1
            if len(bareform_leak_samples) < _SAMPLE_CAP:
                bareform_leak_samples.append(
                    {
                        "chain_node_id": n["id"],
                        "token": n["token"],
                        "person_id": n["person_id"],
                        "person_name": pinfo["name"],
                    }
                )

    # ---- Build confident adjacent (student -> teacher) edges ----
    by_chain: dict[int, dict[int, dict]] = defaultdict(dict)
    for n in nodes:
        by_chain[n["chain_id"]][n["position"]] = n

    def _confident(node: dict | None) -> bool:
        return bool(
            node
            and node["status"] in CONFIDENT_STATUSES
            and node["person_id"] is not None
        )

    edges: list[tuple[dict, dict]] = []  # (student, teacher)
    for positions in by_chain.values():
        for pos, student in positions.items():
            teacher = positions.get(pos + 1)
            if _confident(student) and _confident(teacher):
                edges.append((student, teacher))
    edges_confident = len(edges)

    # ---- Metric 3: generation monotonicity ----
    # Two counts: the RAW count over all non-conflict generations (mostly
    # propagation noise), and the RELIABLE count over anchor-derived generations
    # only (the honest, actionable signal). The reliable count is the gate.
    gen_edges_checked = 0
    gen_violations = 0
    gen_violation_samples: list[dict] = []
    reliable_gen_edges_checked = 0
    reliable_gen_violations = 0
    reliable_gen_violation_samples: list[dict] = []
    for student, teacher in edges:
        sg = _cluster_generation(student["person_id"])
        tg = _cluster_generation(teacher["person_id"])
        if sg and tg:
            gen_edges_checked += 1
            # teacher must be same/earlier generation: teacher_lo <= student_hi.
            if tg[0] > sg[1]:
                gen_violations += 1
                if len(gen_violation_samples) < _SAMPLE_CAP:
                    gen_violation_samples.append(
                        {
                            "hadith": f"chain {student['chain_id']}",
                            "student": person_index[student["person_id"]]["name"],
                            "teacher": person_index[teacher["person_id"]]["name"],
                            "student_gen": f"{sg[0]}-{sg[1]}",
                            "teacher_gen": f"{tg[0]}-{tg[1]}",
                        }
                    )
        rsg = _cluster_generation_reliable(student["person_id"])
        rtg = _cluster_generation_reliable(teacher["person_id"])
        if rsg and rtg:
            reliable_gen_edges_checked += 1
            if gen_violation(rsg, rtg):
                reliable_gen_violations += 1
                if len(reliable_gen_violation_samples) < _SAMPLE_CAP:
                    reliable_gen_violation_samples.append(
                        {
                            "hadith": f"chain {student['chain_id']}",
                            "student": person_index[student["person_id"]]["name"],
                            "teacher": person_index[teacher["person_id"]]["name"],
                            "student_gen": f"{rsg[0]}-{rsg[1]}",
                            "teacher_gen": f"{rtg[0]}-{rtg[1]}",
                        }
                    )

    # ---- Metric 4: Mu'jam edge corroboration ----
    edges_both_mujam = 0
    corroborated = 0
    contradicted = 0
    under_documented = 0
    contradiction_samples: list[dict] = []

    for student, teacher in edges:
        s_pid, t_pid = student["person_id"], teacher["person_id"]
        s_narrators = _cluster_narrators(s_pid)
        t_narrators = _cluster_narrators(t_pid)
        if not s_narrators or not t_narrators:
            continue
        edges_both_mujam += 1

        verdict, teacher_doc, student_doc = _classify_corroboration(
            _cluster_forms(s_pid),
            _cluster_forms(t_pid),
            s_narrators,
            t_narrators,
            narrates_from,
            narrated_by,
        )
        if verdict == "corroborated":
            corroborated += 1
        elif verdict == "contradicted":
            contradicted += 1
            if len(contradiction_samples) < _SAMPLE_CAP:
                contradiction_samples.append(
                    {
                        "hadith": f"chain {student['chain_id']}",
                        "student": person_index[s_pid]["name"],
                        "teacher": person_index[t_pid]["name"],
                        "teacher_doc": teacher_doc,
                        "student_doc": student_doc,
                    }
                )
        else:
            under_documented += 1

    denom = corroborated + contradicted
    corroboration_rate = (corroborated / denom) if denom else None

    return EvalReport(
        source_book_id=source_book_id,
        resolver_version=resolver_version,
        total_nodes=total_nodes,
        status_counts=dict(status_counts),
        node_type_status={k: dict(v) for k, v in node_type_status.items()},
        bareform_leaks=bareform_leaks,
        bareform_leak_samples=bareform_leak_samples,
        gen_edges_checked=gen_edges_checked,
        gen_violations=gen_violations,
        gen_violation_samples=gen_violation_samples,
        reliable_gen_edges_checked=reliable_gen_edges_checked,
        reliable_gen_violations=reliable_gen_violations,
        reliable_gen_violation_samples=reliable_gen_violation_samples,
        edges_confident=edges_confident,
        edges_both_mujam=edges_both_mujam,
        corroborated=corroborated,
        contradicted=contradicted,
        under_documented=under_documented,
        corroboration_rate=corroboration_rate,
        contradiction_samples=contradiction_samples,
    )
