"""Read-only generation-lattice audit for the person-resolution pipeline.

The eval harness (`eval_resolution`) reports *how many* generation violations
and Mu'jam contradictions exist, but caps its samples at 25 and identifies them
only as "chain {id}". Before we can act on the ~500 generation violations and
~7,000 Mu'jam contradictions, we need the *full* list with stable identifiers
(node id, person id, hadith public_id, chain position) and, crucially, a triage
verdict for each: is the *generation number* wrong, is the *identity resolution*
wrong, or is the *chain text itself* anomalous (a dropped/garbled link)?

This module produces that full export and auto-classifies every case into one of
three buckets, in priority order:

* ``suspect_generation`` — the tabaqa number is the untrustworthy factor: an
  anchor built from an ambiguous Imam honorific (bare «الحسن»/«علي», «أبي الحسن»),
  a person that is the common factor in many violations, or an endpoint pinned
  only by propagation through a single edge.
* ``suspect_identity`` — the resolver's person pick is the untrustworthy factor:
  weak context/roster method, first-name/kunya derivation, low margin, a highly
  shared surface form, an exact-full-name homonym (the 901/902 split pattern), or
  a raw resolution that an admin already demoted.
* ``suspect_text`` — neither: a singleton strong-method edge with anchored
  generations three or more layers apart smells like a dropped or corrupted link
  (Phase E / tashif-saqt territory). Annotate only.

Everything here is read-only. Nothing writes to the database.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

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
    PersonResolutionDecision,
    PersonSurfaceForm,
    RijalEntry,
    RijalStatement,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.effective_resolution import ADMIN_REVIEWER
from eshia_research.rijal.eval_resolution import (
    CONFIDENT_STATUSES,
    WELL_ATTESTED_MIN_OCCURRENCES,
    _classify_corroboration,
    _load_occurrence_edges,
    _load_surface_forms,
)
from eshia_research.rijal.machine_review import _STRONG_METHODS
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION
from eshia_research.rijal.tabaqat import _IMAM_KEYWORDS, imam_generation_from_raw
from eshia_research.rijal.identity_links import same_person_clusters

_REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"
_AL_KAFI_SOURCE_BOOK_ID = "11005"

# Generation methods whose interval is anchor-derived (trustworthy enough to make
# a large gap look like a text anomaly rather than a bad generation number).
_ANCHOR_GEN_METHODS = frozenset({"imam_fixed", "ashab_anchor", "anchor_and_propagated"})

# Imam honorifics that are ambiguous when they appear bare: «الحسن» maps to layer
# 2 (al-Mujtaba) but is also the ism of al-Askari (10); «علي» maps to layer 1 but
# is shared by al-Sajjad (3), al-Rida (7), al-Hadi (9). Detected by re-running the
# keyword scan and seeing which keyword actually fired.
_AMBIGUOUS_IMAM_KEYWORDS = frozenset({normalise_arabic_persian(k) for k in ("الحسن", "علي")})
# «أبي الحسن» is a kunya shared by al-Kazim/al-Rida/al-Hadi; the current keyword
# table has no entry for it, so it falls through to «الحسن» -> layer 2, which is
# always wrong. Flagged explicitly.
_ABU_AL_HASAN_NORM = normalise_arabic_persian("ابي الحسن")

# Resolution methods / derivations that make an *identity* pick suspect.
_WEAK_CONTEXT_METHODS = frozenset({"collective_context", "collective_roster_after_context"})
_WEAK_DERIVATIONS = frozenset({"first_name", "kunya"})
_LOW_MARGIN = 25
_SHARED_SURFACE = 40
_VIOLATION_CONCENTRATION = 5  # a person in >= this many violations is the common factor

# Admin decision types that DEMOTE a raw resolution — if the raw rank-1 is still
# confidently resolved while an admin said otherwise, the edge is suspect.
_DEMOTING_ADMIN_DECISIONS = frozenset({"keep_ambiguous", "flag_text_or_chain_issue"})

BUCKET_SUSPECT_GENERATION = "suspect_generation"
BUCKET_SUSPECT_IDENTITY = "suspect_identity"
BUCKET_SUSPECT_TEXT = "suspect_text"
BUCKET_UNCLASSIFIED = "unclassified"


def _norm(text: str | None) -> str:
    return normalise_arabic_persian(text or "").strip()


def _fired_imam_keyword(imam_raw: str | None) -> str | None:
    """Which keyword in `_IMAM_KEYWORDS` actually fires for this imam_raw."""
    if not imam_raw:
        return None
    norm = _norm(imam_raw)
    for keyword, _generation in _IMAM_KEYWORDS:
        if keyword in norm:
            return keyword
    return None


@dataclasses.dataclass
class GenerationAuditReport:
    source_book_id: str
    resolver_version: str

    violation_edges: list[dict]      # ALL generation-monotonicity violations, uncapped
    conflict_persons: list[dict]     # ALL method='conflict' persons + contradicting edges
    contradicted_edges: list[dict]   # ALL Mu'jam-contradicted edges, uncapped

    bucket_counts: Counter[str]
    conflict_person_count: int
    contradicted_edge_count: int
    gen_edges_checked: int
    admin_disagreements: list[dict]  # audit says demote, but an admin approved it

    def summary_dict(self) -> dict:
        return {
            "source_book_id": self.source_book_id,
            "resolver_version": self.resolver_version,
            "gen_edges_checked": self.gen_edges_checked,
            "gen_violations": len(self.violation_edges),
            "violation_bucket_counts": dict(self.bucket_counts),
            "conflict_persons": self.conflict_person_count,
            "contradicted_edges": self.contradicted_edge_count,
            "admin_disagreements": len(self.admin_disagreements),
        }

    def format_text(self) -> str:
        lines: list[str] = []
        a = lines.append
        a(f"Generation-lattice audit — source_book_id={self.source_book_id} "
          f"(resolver_version={self.resolver_version})")
        a("")
        a(f"Generation violations: {len(self.violation_edges)} of "
          f"{self.gen_edges_checked} gen-checkable edges")
        for bucket, count in self.bucket_counts.most_common():
            a(f"    {bucket:<22} {count:>6}")
        a("")
        a(f"Conflict-method persons: {self.conflict_person_count}")
        a(f"Mu'jam-contradicted edges: {self.contradicted_edge_count}")
        a(f"Admin disagreements (audit-demote vs admin-approve): {len(self.admin_disagreements)}")
        return "\n".join(lines)


def _load_nodes_full(db: Session, source_book_id: str, resolver_version: str) -> list[dict]:
    """rank-1 person resolution for every non-rejected chain node, with the
    hadith public_id and the resolution method/evidence needed for triage."""
    stmt = (
        select(
            ChainNode.id,
            ChainNode.chain_id,
            ChainNode.position,
            ChainNode.node_type,
            ChainNode.raw_token,
            Hadith.public_id,
            MentionResolution.status,
            MentionResolution.person_id,
            MentionResolution.method,
            MentionResolution.evidence_json,
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
    nodes: list[dict] = []
    for (node_id, chain_id, pos, ntype, token, public_id,
         status, person_id, method, evidence) in db.execute(stmt):
        ev = evidence if isinstance(evidence, dict) else {}
        nodes.append({
            "id": node_id,
            "chain_id": chain_id,
            "position": pos,
            "node_type": ntype,
            "token": token,
            "public_id": public_id,
            "status": status or "missing",
            "person_id": person_id,
            "method": method,
            "score": ev.get("score"),
            "margin": ev.get("margin"),
            "derivation": ev.get("derivation"),
            "shared_count": ev.get("shared_count"),
        })
    return nodes


def _load_person_index(db: Session, person_ids: set[int]) -> dict[int, dict]:
    if not person_ids:
        return {}
    index: dict[int, dict] = {}
    stmt = (
        select(Person.id, Person.kind, Person.canonical_name_ar,
               Person.canonical_name_norm, Person.primary_entry_id, RijalEntry.narrator_id)
        .select_from(Person)
        .outerjoin(RijalEntry, RijalEntry.id == Person.primary_entry_id)
        .where(Person.id.in_(person_ids))
    )
    for pid, kind, name_ar, name_norm, primary_entry_id, narrator_id in db.execute(stmt):
        index[pid] = {
            "kind": kind,
            "name": name_ar,
            "name_norm": name_norm,
            "primary_entry_id": primary_entry_id,
            "narrator_id": narrator_id,
        }
    return index


def _load_generation_rows(db: Session, person_ids: set[int]) -> dict[int, dict]:
    """Full generation rows (including conflict) keyed by person id."""
    if not person_ids:
        return {}
    out: dict[int, dict] = {}
    stmt = select(
        PersonGeneration.person_id, PersonGeneration.gen_lo, PersonGeneration.gen_hi,
        PersonGeneration.gen_point, PersonGeneration.method, PersonGeneration.evidence_summary,
    ).where(PersonGeneration.person_id.in_(person_ids))
    for pid, lo, hi, point, method, summary in db.execute(stmt):
        out[pid] = {"lo": lo, "hi": hi, "point": point, "method": method, "summary": summary}
    return out


def _load_anchor_keywords(db: Session, entry_ids: set[int]) -> dict[int, list[str]]:
    """entry_id -> the imam-honorific keywords that fired for its anchors."""
    if not entry_ids:
        return {}
    out: dict[int, list[str]] = defaultdict(list)
    stmt = (
        select(RijalStatement.entry_id, RijalStatement.metadata_json)
        .where(
            RijalStatement.statement_type == "tabaqah_membership",
            RijalStatement.entry_id.in_(entry_ids),
        )
    )
    for entry_id, meta in db.execute(stmt):
        imam_raw = (meta or {}).get("imam_raw") if isinstance(meta, dict) else None
        keyword = _fired_imam_keyword(imam_raw)
        if keyword is not None:
            out[entry_id].append(imam_raw)
    return out


def _load_admin_decisions(db: Session, resolver_version: str) -> dict[int, str]:
    """chain_node_id -> admin decision_type (current resolver version only)."""
    stmt = select(
        PersonResolutionDecision.chain_node_id, PersonResolutionDecision.decision_type
    ).where(
        PersonResolutionDecision.reviewer == ADMIN_REVIEWER,
        PersonResolutionDecision.resolver_version == resolver_version,
    )
    return {node_id: decision for node_id, decision in db.execute(stmt)}


def audit_generations(
    db: Session,
    *,
    source_book_id: str = _AL_KAFI_SOURCE_BOOK_ID,
    resolver_version: str = PERSON_RESOLVER_VERSION,
) -> GenerationAuditReport:
    nodes = _load_nodes_full(db, source_book_id, resolver_version)

    person_ids = {n["person_id"] for n in nodes if n["person_id"] is not None}
    clusters = same_person_clusters(db, person_ids)
    cluster_person_ids = set(person_ids)
    for members in clusters.values():
        cluster_person_ids.update(members)

    person_index = _load_person_index(db, cluster_person_ids)
    gen_rows = _load_generation_rows(db, cluster_person_ids)
    surface_forms = _load_surface_forms(db, cluster_person_ids)
    narrator_ids = {p["narrator_id"] for p in person_index.values() if p["narrator_id"] is not None}
    narrates_from, narrated_by = _load_occurrence_edges(db, narrator_ids)
    entry_ids = {p["primary_entry_id"] for p in person_index.values() if p["primary_entry_id"]}
    anchor_keywords = _load_anchor_keywords(db, entry_ids)
    admin_decisions = _load_admin_decisions(db, resolver_version)

    def members_of(pid: int) -> set[int]:
        return clusters.get(pid, {pid})

    def root_of(pid: int) -> int:
        return min(members_of(pid))

    def clean_interval(pid: int) -> tuple[int, int] | None:
        ranges = [
            (gen_rows[m]["lo"], gen_rows[m]["hi"])
            for m in members_of(pid)
            if m in gen_rows and gen_rows[m]["method"] != "conflict"
        ]
        if not ranges:
            return None
        return min(lo for lo, _ in ranges), max(hi for _, hi in ranges)

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

    def gen_method(pid: int) -> str | None:
        row = gen_rows.get(pid)
        return row["method"] if row else None

    def anchor_is_ambiguous(pid: int) -> bool:
        """The person's tabaqa anchor came from a bare/ambiguous Imam honorific."""
        pinfo = person_index.get(pid)
        if not pinfo or not pinfo.get("primary_entry_id"):
            return False
        for imam_raw in anchor_keywords.get(pinfo["primary_entry_id"], []):
            norm = _norm(imam_raw)
            if _ABU_AL_HASAN_NORM in norm:
                return True
            fired = _fired_imam_keyword(imam_raw)
            if fired in _AMBIGUOUS_IMAM_KEYWORDS:
                return True
        return False

    def person_name(pid: int) -> str:
        return person_index.get(pid, {}).get("name") or str(pid)

    # ---- Exact-full-name homonyms (the split/merge risk) over endpoint persons ----
    full_form_owners: dict[str, set[int]] = defaultdict(set)
    for pid in cluster_person_ids:
        pinfo = person_index.get(pid)
        if pinfo and pinfo["name_norm"]:
            full_form_owners[pinfo["name_norm"]].add(root_of(pid))

    def has_full_name_homonym(pid: int) -> bool:
        pinfo = person_index.get(pid)
        if not pinfo or not pinfo["name_norm"]:
            return False
        return len(full_form_owners.get(pinfo["name_norm"], set())) > 1

    # ---- Confident adjacent (student -> teacher) edges ----
    by_chain: dict[int, dict[int, dict]] = defaultdict(dict)
    for n in nodes:
        by_chain[n["chain_id"]][n["position"]] = n

    def confident(node: dict | None) -> bool:
        return bool(node and node["status"] in CONFIDENT_STATUSES and node["person_id"] is not None)

    edges: list[tuple[dict, dict]] = []
    edge_support: Counter[tuple[int, int]] = Counter()
    for positions in by_chain.values():
        for pos, student in positions.items():
            teacher = positions.get(pos + 1)
            if confident(student) and confident(teacher):
                edges.append((student, teacher))
                edge_support[(root_of(student["person_id"]), root_of(teacher["person_id"]))] += 1

    # ---- Pass 1: find violations, count per-person concentration ----
    gen_edges_checked = 0
    raw_violations: list[tuple[dict, dict, tuple[int, int], tuple[int, int]]] = []
    concentration: Counter[int] = Counter()
    for student, teacher in edges:
        sg = clean_interval(student["person_id"])
        tg = clean_interval(teacher["person_id"])
        if not sg or not tg:
            continue
        gen_edges_checked += 1
        if tg[0] > sg[1]:  # teacher strictly later than student — impossible
            raw_violations.append((student, teacher, sg, tg))
            concentration[root_of(student["person_id"])] += 1
            concentration[root_of(teacher["person_id"])] += 1

    def classify_edge(student: dict, teacher: dict, sg: tuple[int, int],
                      tg: tuple[int, int]) -> tuple[str, list[str]]:
        s_pid, t_pid = student["person_id"], teacher["person_id"]
        buckets: list[str] = []

        # --- suspect_generation ---
        gen_signals: list[str] = []
        if anchor_is_ambiguous(s_pid) or anchor_is_ambiguous(t_pid):
            gen_signals.append("anchor_keyword_ambiguous")
        if (concentration[root_of(s_pid)] >= _VIOLATION_CONCENTRATION
                or concentration[root_of(t_pid)] >= _VIOLATION_CONCENTRATION):
            gen_signals.append("violation_concentration")
        for pid, iv in ((s_pid, sg), (t_pid, tg)):
            if gen_method(pid) == "propagated" and iv[0] == iv[1]:
                gen_signals.append("propagated_only_endpoint")
                break
        if gen_signals:
            buckets.append(BUCKET_SUSPECT_GENERATION)

        # --- suspect_identity ---
        id_signals: list[str] = []
        for node in (student, teacher):
            if node["method"] in _WEAK_CONTEXT_METHODS:
                id_signals.append("weak_context_method")
            if node["derivation"] in _WEAK_DERIVATIONS:
                id_signals.append("weak_derivation")
            if isinstance(node["margin"], int) and node["margin"] < _LOW_MARGIN:
                id_signals.append("low_margin")
            if isinstance(node["shared_count"], int) and node["shared_count"] >= _SHARED_SURFACE:
                id_signals.append("shared_surface")
            if admin_decisions.get(node["id"]) in _DEMOTING_ADMIN_DECISIONS:
                id_signals.append("admin_demoted")
        if has_full_name_homonym(s_pid) or has_full_name_homonym(t_pid):
            id_signals.append("full_name_homonym")
        if id_signals:
            buckets.append(BUCKET_SUSPECT_IDENTITY)

        # --- suspect_text ---
        gap = tg[0] - sg[1]
        if (edge_support[(root_of(s_pid), root_of(t_pid))] == 1
                and student["method"] in _STRONG_METHODS
                and teacher["method"] in _STRONG_METHODS
                and gen_method(s_pid) in _ANCHOR_GEN_METHODS
                and gen_method(t_pid) in _ANCHOR_GEN_METHODS
                and gap >= 3):
            buckets.append(BUCKET_SUSPECT_TEXT)

        if not buckets:
            return BUCKET_UNCLASSIFIED, ["unclassified"]
        # Priority order: generation > identity > text.
        for primary in (BUCKET_SUSPECT_GENERATION, BUCKET_SUSPECT_IDENTITY, BUCKET_SUSPECT_TEXT):
            if primary in buckets:
                return primary, gen_signals + id_signals
        return BUCKET_UNCLASSIFIED, ["unclassified"]

    def edge_endpoint(node: dict, iv: tuple[int, int]) -> dict:
        pid = node["person_id"]
        return {
            "node_id": node["id"],
            "position": node["position"],
            "raw_token": node["token"],
            "person_id": pid,
            "cluster_root": root_of(pid),
            "person_name": person_name(pid),
            "gen_lo": iv[0],
            "gen_hi": iv[1],
            "gen_method": gen_method(pid),
            "resolution_method": node["method"],
            "score": node["score"],
            "margin": node["margin"],
            "derivation": node["derivation"],
            "shared_count": node["shared_count"],
            "has_admin_decision": admin_decisions.get(node["id"]),
        }

    bucket_counts: Counter[str] = Counter()
    admin_disagreements: list[dict] = []
    violation_edges: list[dict] = []
    for student, teacher, sg, tg in raw_violations:
        primary, signals = classify_edge(student, teacher, sg, tg)
        bucket_counts[primary] += 1
        record = {
            "hadith_public_id": student["public_id"],
            "chain_id": student["chain_id"],
            "gap": tg[0] - sg[1],
            "edge_chain_support": edge_support[(root_of(student["person_id"]),
                                                root_of(teacher["person_id"]))],
            "primary_bucket": primary,
            "signals": sorted(set(signals)),
            "student": edge_endpoint(student, sg),
            "teacher": edge_endpoint(teacher, tg),
        }
        violation_edges.append(record)
        # An audit-demote intent that collides with an admin approval is logged,
        # never acted on: the admin verdict wins.
        for node in (student, teacher):
            if (primary == BUCKET_SUSPECT_IDENTITY
                    and admin_decisions.get(node["id"]) in ("approve_current",
                                                            "approve_external_override")):
                admin_disagreements.append({
                    "hadith_public_id": student["public_id"],
                    "node_id": node["id"],
                    "person_name": person_name(node["person_id"]),
                    "admin_decision": admin_decisions.get(node["id"]),
                })

    # ---- Conflict-method persons + their contradicting edges ----
    conflict_pids = {pid for pid, row in gen_rows.items() if row["method"] == "conflict"}
    mentions_per_person: Counter[int] = Counter()
    for n in nodes:
        if n["status"] in CONFIDENT_STATUSES and n["person_id"] is not None:
            mentions_per_person[root_of(n["person_id"])] += 1
    partner_edges: dict[int, list[dict]] = defaultdict(list)
    for student, teacher in edges:
        s_pid, t_pid = student["person_id"], teacher["person_id"]
        if s_pid in conflict_pids or root_of(s_pid) in conflict_pids:
            partner_edges[root_of(s_pid)].append(
                {"partner": person_name(t_pid), "direction": "teacher",
                 "public_id": student["public_id"]})
        if t_pid in conflict_pids or root_of(t_pid) in conflict_pids:
            partner_edges[root_of(t_pid)].append(
                {"partner": person_name(s_pid), "direction": "student",
                 "public_id": student["public_id"]})
    conflict_persons: list[dict] = []
    for pid in sorted(conflict_pids):
        row = gen_rows[pid]
        conflict_persons.append({
            "person_id": pid,
            "person_name": person_name(pid),
            "gen_lo": row["lo"],
            "gen_hi": row["hi"],
            "evidence_summary": row["summary"],
            "resolved_mentions": mentions_per_person.get(root_of(pid), 0),
            "sample_edges": partner_edges.get(root_of(pid), [])[:5],
        })

    # ---- Mu'jam-contradicted edges (uncapped) ----
    contradicted_edges: list[dict] = []
    for student, teacher in edges:
        s_pid, t_pid = student["person_id"], teacher["person_id"]
        s_narrators = cluster_narrators(s_pid)
        t_narrators = cluster_narrators(t_pid)
        if not s_narrators or not t_narrators:
            continue
        verdict, teacher_doc, student_doc = _classify_corroboration(
            cluster_forms(s_pid), cluster_forms(t_pid),
            s_narrators, t_narrators, narrates_from, narrated_by,
        )
        if verdict != "contradicted":
            continue
        contradicted_edges.append({
            "hadith_public_id": student["public_id"],
            "chain_id": student["chain_id"],
            "student": {"node_id": student["id"], "person_id": s_pid,
                        "person_name": person_name(s_pid), "doc_count": student_doc,
                        "resolution_method": student["method"]},
            "teacher": {"node_id": teacher["id"], "person_id": t_pid,
                        "person_name": person_name(t_pid), "doc_count": teacher_doc,
                        "resolution_method": teacher["method"]},
            "split_identity_hint": has_full_name_homonym(s_pid) or has_full_name_homonym(t_pid),
        })

    return GenerationAuditReport(
        source_book_id=source_book_id,
        resolver_version=resolver_version,
        violation_edges=violation_edges,
        conflict_persons=conflict_persons,
        contradicted_edges=contradicted_edges,
        bucket_counts=bucket_counts,
        conflict_person_count=len(conflict_persons),
        contradicted_edge_count=len(contradicted_edges),
        gen_edges_checked=gen_edges_checked,
        admin_disagreements=admin_disagreements,
    )


def write_audit_exports(report: GenerationAuditReport, output_dir: str | Path) -> tuple[Path, Path]:
    """Write a human-readable markdown summary and a full JSONL of every case."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"generation_audit_{report.source_book_id}_{stamp}"
    md_path = out / f"{base}.md"
    jsonl_path = out / f"{base}.jsonl"

    lines: list[str] = []
    a = lines.append
    a(f"# Generation-lattice audit — Al-Kafi ({report.source_book_id})")
    a("")
    a(f"- resolver_version: `{report.resolver_version}`")
    a(f"- generation violations: **{len(report.violation_edges)}** of "
      f"{report.gen_edges_checked} gen-checkable edges")
    a(f"- conflict-method persons: **{report.conflict_person_count}**")
    a(f"- Mu'jam-contradicted edges: **{report.contradicted_edge_count}**")
    a(f"- admin disagreements (logged, never auto-acted): **{len(report.admin_disagreements)}**")
    a("")
    a("## Violation buckets")
    a("")
    a("| bucket | count |")
    a("| --- | ---: |")
    for bucket, count in report.bucket_counts.most_common():
        a(f"| {bucket} | {count} |")
    a("")
    for bucket in (BUCKET_SUSPECT_GENERATION, BUCKET_SUSPECT_IDENTITY,
                   BUCKET_SUSPECT_TEXT, BUCKET_UNCLASSIFIED):
        samples = [v for v in report.violation_edges if v["primary_bucket"] == bucket][:20]
        if not samples:
            continue
        a(f"## Sample: {bucket} ({report.bucket_counts.get(bucket, 0)} total)")
        a("")
        for v in samples:
            a(f"- `{v['hadith_public_id']}` gap={v['gap']} "
              f"support={v['edge_chain_support']} signals={','.join(v['signals'])}")
            a(f"  - student `{v['student']['person_name']}` "
              f"gen{v['student']['gen_lo']}-{v['student']['gen_hi']} "
              f"({v['student']['gen_method']}, res={v['student']['resolution_method']})")
            a(f"  - teacher `{v['teacher']['person_name']}` "
              f"gen{v['teacher']['gen_lo']}-{v['teacher']['gen_hi']} "
              f"({v['teacher']['gen_method']}, res={v['teacher']['resolution_method']})")
        a("")
    if report.conflict_persons:
        a("## Conflict-method persons (top 20 by resolved mentions)")
        a("")
        for p in sorted(report.conflict_persons,
                        key=lambda r: -r["resolved_mentions"])[:20]:
            a(f"- `{p['person_name']}` (person {p['person_id']}) "
              f"gen{p['gen_lo']}-{p['gen_hi']}, {p['resolved_mentions']} mentions")
        a("")
    if report.admin_disagreements:
        a("## Admin disagreements (audit would demote, admin approved — NOT acted on)")
        a("")
        for d in report.admin_disagreements[:40]:
            a(f"- `{d['hadith_public_id']}` node {d['node_id']} "
              f"`{d['person_name']}` — admin `{d['admin_decision']}`")
        a("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for record in report.violation_edges:
            fh.write(json.dumps({"kind": "violation", **record}, ensure_ascii=False) + "\n")
        for record in report.conflict_persons:
            fh.write(json.dumps({"kind": "conflict_person", **record}, ensure_ascii=False) + "\n")
        for record in report.contradicted_edges:
            fh.write(json.dumps({"kind": "contradicted", **record}, ensure_ascii=False) + "\n")
    return md_path, jsonl_path
