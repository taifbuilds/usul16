"""Machine-admin review layer for person-resolution decisions.

The resolver writes ranked claims in `mention_resolutions`. This module writes
review decisions *about* those claims without mutating them. It is conservative:
approve strong, low-risk resolved cases; route ambiguous/risky/contradictory
cases into a stable external-review packet.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
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
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.identity_links import same_person_clusters
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION
from eshia_research.rijal.review_priors import REVIEW_PRIOR_METHODS

REVIEWER = "codex-machine-v1"
_REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"
_CONFIDENT_STATUSES = {"resolved", "via_collective"}
_STRONG_METHODS = {
    "surface_full",
    "tabaqat_disambiguated",
    "father_relation_matched",
    "father_nasab_unique",
    "grandfather_two_step",
    "collective_roster_member",
    "collective_named_member",
    "kafi_opening_muhammad_yahya",
    "kafi_opening_ali_ibrahim",
    "kafi_opening_anaphora_previous_hadith",
} | set(REVIEW_PRIOR_METHODS)
_SOURCE_PRIOR_METHODS = {
    "compiler_prior_kulayni",
    "kafi_opening_muhammad_yahya",
    "kafi_opening_ali_ibrahim",
    "kafi_opening_anaphora_previous_hadith",
} | set(REVIEW_PRIOR_METHODS)
_SQLITE_CHUNK = 800


@dataclasses.dataclass
class MachineReviewStats:
    nodes_examined: int = 0
    decisions_written: int = 0
    decision_counts: Counter[str] = dataclasses.field(default_factory=Counter)
    confidence_counts: Counter[str] = dataclasses.field(default_factory=Counter)
    risk_counts: Counter[str] = dataclasses.field(default_factory=Counter)


@dataclasses.dataclass
class ExportStats:
    markdown_path: str
    jsonl_path: str
    cases_written: int


def _norm(text: str | None) -> str:
    return normalise_arabic_persian(text or "").strip()


def _compact(text: str | None, limit: int = 500) -> str:
    value = " ".join((text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def _chunks(values, size: int = _SQLITE_CHUNK):
    seq = list(values)
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _score(evidence: dict | None) -> int | None:
    if not evidence:
        return None
    value = evidence.get("score")
    return value if isinstance(value, int) else None


def _margin(evidence: dict | None) -> int | None:
    if not evidence:
        return None
    value = evidence.get("margin")
    return value if isinstance(value, int) else None


def _risk_flags(top: MentionResolution | None, candidate_count: int) -> list[str]:
    if top is None:
        return ["missing_rank1"]
    flags: list[str] = []
    if top.status in {"ambiguous", "unresolved", "latent"}:
        flags.append(top.status)
    if top.method in {"collective_context", "compiler_prior_kulayni", "collective_roster_after_context"}:
        flags.append("phase_d_context")
    if candidate_count >= 6 and top.method not in _SOURCE_PRIOR_METHODS:
        flags.append("many_candidates")
    evidence = top.evidence_json or {}
    surface = evidence.get("surface") or {}
    derivation = surface.get("derivation")
    shared_count = surface.get("shared_count")
    if derivation in {"first_name", "kunya"}:
        flags.append("weak_surface")
    if isinstance(shared_count, int) and shared_count >= 40:
        flags.append("shared_surface")
    margin = _margin(evidence)
    if margin is not None and margin < 25:
        flags.append("low_margin")
    return flags


def _load_book_nodes(db: Session, source_book_id: str) -> tuple[Book, list[tuple[ChainNode, Chain, Hadith]]]:
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise ValueError(f"Book not found: {source_book_id}")
    rows = (
        db.query(ChainNode, Chain, Hadith)
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(Hadith.book_id == book.id, Hadith.review_status != _REJECTED_HADITH_STATUS)
        .order_by(Hadith.sequence_in_book, Chain.chain_number, ChainNode.position)
        .all()
    )
    return book, rows


def _load_resolutions(db: Session, node_ids: list[int]) -> dict[int, list[MentionResolution]]:
    rows_by_node: dict[int, list[MentionResolution]] = defaultdict(list)
    if not node_ids:
        return rows_by_node
    for chunk in _chunks(node_ids):
        for row in (
            db.query(MentionResolution)
            .filter(
                MentionResolution.chain_node_id.in_(chunk),
                MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            )
            .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
            .all()
        ):
            rows_by_node[row.chain_node_id].append(row)
    return rows_by_node


def _load_person_context(db: Session, person_ids: set[int]) -> dict:
    clusters = same_person_clusters(db, person_ids)
    all_person_ids = set(person_ids)
    for members in clusters.values():
        all_person_ids.update(members)

    persons = {}
    generations = {}
    if all_person_ids:
        for chunk in _chunks(all_person_ids):
            persons.update({p.id: p for p in db.query(Person).filter(Person.id.in_(chunk)).all()})
            generations.update(
                {
                    g.person_id: (g.gen_lo, g.gen_hi, g.gen_point, g.method)
                    for g in db.query(PersonGeneration).filter(PersonGeneration.person_id.in_(chunk)).all()
                }
            )
    forms: dict[int, set[str]] = defaultdict(set)
    if all_person_ids:
        for chunk in _chunks(all_person_ids):
            for pid, form_norm in db.execute(
                select(PersonSurfaceForm.person_id, PersonSurfaceForm.form_norm).where(
                    PersonSurfaceForm.person_id.in_(chunk)
                )
            ):
                forms[pid].add(_norm(form_norm))

    entry_ids = {p.primary_entry_id for p in persons.values() if p.primary_entry_id}
    narrator_by_entry = {}
    if entry_ids:
        for chunk in _chunks(entry_ids):
            narrator_by_entry.update(
                {
                    entry_id: narrator_id
                    for entry_id, narrator_id in db.execute(
                        select(RijalEntry.id, RijalEntry.narrator_id).where(RijalEntry.id.in_(chunk))
                    )
                }
            )
    narrator_ids = {nid for nid in narrator_by_entry.values() if nid is not None}
    narrates_from: dict[int, set[str]] = defaultdict(set)
    narrated_by: dict[int, set[str]] = defaultdict(set)
    if narrator_ids:
        for chunk in _chunks(narrator_ids):
            for narrator_id, direction, related in db.execute(
                select(
                    RijalOccurrence.narrator_id,
                    RijalOccurrence.direction,
                    RijalOccurrence.related_name_normalised,
                ).where(RijalOccurrence.narrator_id.in_(chunk))
            ):
                if direction == "narrates_from":
                    narrates_from[narrator_id].add(_norm(related))
                elif direction == "narrated_by":
                    narrated_by[narrator_id].add(_norm(related))

    return {
        "clusters": clusters,
        "persons": persons,
        "generations": generations,
        "forms": forms,
        "narrator_by_entry": narrator_by_entry,
        "narrates_from": narrates_from,
        "narrated_by": narrated_by,
    }


def _cluster_members(context: dict, person_id: int) -> set[int]:
    return context["clusters"].get(person_id, {person_id})


def _cluster_generation(context: dict, person_id: int | None) -> tuple[int, int] | None:
    if person_id is None:
        return None
    ranges = [
        context["generations"][pid][:2]
        for pid in _cluster_members(context, person_id)
        if pid in context["generations"]
        and context["generations"][pid][3] != "conflict"
    ]
    if not ranges:
        return None
    return min(lo for lo, _ in ranges), max(hi for _, hi in ranges)


def _cluster_forms(context: dict, person_id: int | None) -> set[str]:
    if person_id is None:
        return set()
    forms: set[str] = set()
    for pid in _cluster_members(context, person_id):
        forms.update(context["forms"].get(pid, set()))
        person = context["persons"].get(pid)
        if person is not None:
            forms.add(person.canonical_name_norm)
    return forms


def _cluster_narrators(context: dict, person_id: int | None) -> set[int]:
    if person_id is None:
        return set()
    narrators: set[int] = set()
    for pid in _cluster_members(context, person_id):
        person = context["persons"].get(pid)
        if person is None or person.primary_entry_id is None:
            continue
        narrator_id = context["narrator_by_entry"].get(person.primary_entry_id)
        if narrator_id is not None:
            narrators.add(narrator_id)
    return narrators


def _edge_corroborated(context: dict, student_pid: int | None, teacher_pid: int | None) -> bool:
    if student_pid is None or teacher_pid is None:
        return False
    student_forms = _cluster_forms(context, student_pid)
    teacher_forms = _cluster_forms(context, teacher_pid)
    if not student_forms or not teacher_forms:
        return False
    student_narrators = _cluster_narrators(context, student_pid)
    teacher_narrators = _cluster_narrators(context, teacher_pid)
    for teacher_narrator in teacher_narrators:
        if student_forms & context["narrated_by"].get(teacher_narrator, set()):
            return True
    for student_narrator in student_narrators:
        if teacher_forms & context["narrates_from"].get(student_narrator, set()):
            return True
    return False


def _generation_violation(context: dict, student_pid: int | None, teacher_pid: int | None) -> bool:
    student_gen = _cluster_generation(context, student_pid)
    teacher_gen = _cluster_generation(context, teacher_pid)
    if not student_gen or not teacher_gen:
        return False
    return teacher_gen[0] > student_gen[1]


def _candidate_payload(context: dict, rows: list[MentionResolution]) -> list[dict]:
    payload = []
    for row in rows[:8]:
        person = context["persons"].get(row.person_id) if row.person_id else None
        gen = _cluster_generation(context, row.person_id)
        payload.append(
            {
                "rank": row.rank,
                "status": row.status,
                "method": row.method,
                "person_id": row.person_id,
                "person_name": person.canonical_name_ar if person else None,
                "person_kind": person.kind if person else None,
                "generation": f"{gen[0]}-{gen[1]}" if gen else None,
                "score": _score(row.evidence_json),
                "margin": _margin(row.evidence_json),
                "evidence_summary": row.evidence_summary,
            }
        )
    return payload


def _question(node: ChainNode, top: MentionResolution | None, context: dict) -> str:
    if top and top.person_id:
        person = context["persons"].get(top.person_id)
        name = person.canonical_name_ar if person else f"person {top.person_id}"
        return (
            f"Who is the chain mention «{node.raw_token}» at this position? "
            f"Is the current top candidate «{name}» the correct historical person here?"
        )
    return f"Who is the chain mention «{node.raw_token}» at this position?"


def _classify_decision(
    *,
    node: ChainNode,
    top: MentionResolution | None,
    candidates: list[MentionResolution],
    context: dict,
    prev_top: MentionResolution | None,
    next_top: MentionResolution | None,
) -> tuple[str, str, str, dict]:
    candidate_count = len(candidates)
    flags = _risk_flags(top, candidate_count)
    edge_hits = []
    gen_violations = []

    if top is not None and top.person_id is not None and top.status in _CONFIDENT_STATUSES:
        person = context["persons"].get(top.person_id)
        if person is not None and person.kind == "bare_form_proxy":
            flags.append("bare_form_proxy")
        if next_top and next_top.status in _CONFIDENT_STATUSES:
            if _edge_corroborated(context, top.person_id, next_top.person_id):
                edge_hits.append("teacher_edge_corroborated")
            if _generation_violation(context, top.person_id, next_top.person_id):
                gen_violations.append("teacher_later_than_student")
        if prev_top and prev_top.status in _CONFIDENT_STATUSES:
            if _edge_corroborated(context, prev_top.person_id, top.person_id):
                edge_hits.append("student_edge_corroborated")
            if _generation_violation(context, prev_top.person_id, top.person_id):
                gen_violations.append("this_teacher_later_than_student")

    flags.extend(gen_violations)
    evidence = {
        "top_status": top.status if top else "missing_rank1",
        "top_method": top.method if top else None,
        "risk_flags": sorted(set(flags)),
        "edge_corroboration": edge_hits,
        "candidate_count": candidate_count,
        "top_score": _score(top.evidence_json) if top else None,
        "top_margin": _margin(top.evidence_json) if top else None,
        "candidates": _candidate_payload(context, candidates),
    }

    if top is None:
        return "needs_external_review", "low", "No rank-1 person-resolution row exists.", evidence
    if gen_violations or "bare_form_proxy" in flags:
        return "flag_contradiction", "blocked", "Resolved candidate has a hard audit flag.", evidence
    if top.status in _CONFIDENT_STATUSES and top.person_id is not None:
        high_risk = {"weak_surface", "shared_surface", "low_margin", "many_candidates"}
        phase_d_only = "phase_d_context" in flags and not edge_hits
        if high_risk & set(flags) or phase_d_only:
            return "needs_external_review", "medium", "Resolved but risky enough for outside verification.", evidence
        if top.method in _STRONG_METHODS or edge_hits:
            tier = "high" if top.method in _STRONG_METHODS and candidate_count <= 2 else "medium"
            return "approve_current", tier, "Current top person is supported by low-risk resolver evidence.", evidence
        return "needs_external_review", "medium", "Resolved, but not enough independent support for machine approval.", evidence
    if top.status == "ambiguous":
        return "needs_external_review", "low", "Resolver intentionally kept this mention ambiguous.", evidence
    if top.status == "latent":
        return "needs_external_review", "low", "Resolver minted or used a latent person; needs source verification.", evidence
    return "needs_external_review", "low", "No person identity could be safely resolved.", evidence


def run_machine_review(
    db: Session,
    *,
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    reviewer: str = REVIEWER,
    limit: int | None = None,
    commit: bool = True,
) -> MachineReviewStats:
    _book, rows = _load_book_nodes(db, source_book_id)
    if limit is not None:
        rows = rows[: max(0, limit)]
    node_ids = [node.id for node, _chain, _hadith in rows]
    rows_by_node = _load_resolutions(db, node_ids)
    person_ids = {
        row.person_id
        for node_rows in rows_by_node.values()
        for row in node_rows
        if row.person_id is not None
    }
    context = _load_person_context(db, person_ids)

    top_by_node = {
        node_id: sorted(node_rows, key=lambda row: row.rank)[0]
        for node_id, node_rows in rows_by_node.items()
        if node_rows
    }
    node_by_chain_pos = {
        (chain.id, node.position): node.id
        for node, chain, _hadith in rows
    }

    decision_rows: list[dict] = []
    if commit and node_ids:
        for chunk in _chunks(node_ids):
            db.execute(
                delete(PersonResolutionDecision).where(
                    PersonResolutionDecision.chain_node_id.in_(chunk),
                    PersonResolutionDecision.reviewer == reviewer,
                    PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
                )
            )

    stats = MachineReviewStats(nodes_examined=len(rows))
    for node, chain, hadith in rows:
        candidates = sorted(rows_by_node.get(node.id, []), key=lambda row: row.rank)
        top = candidates[0] if candidates else None
        prev_top = top_by_node.get(node_by_chain_pos.get((chain.id, node.position - 1)))
        next_top = top_by_node.get(node_by_chain_pos.get((chain.id, node.position + 1)))
        decision_type, tier, summary, evidence = _classify_decision(
            node=node,
            top=top,
            candidates=candidates,
            context=context,
            prev_top=prev_top,
            next_top=next_top,
        )
        evidence.update(
            {
                "source_book_id": source_book_id,
                "public_id": hadith.public_id,
                "chain_id": chain.id,
                "chain_number": chain.chain_number,
                "node_position": node.position,
                "node_type": node.node_type,
                "raw_token": node.raw_token,
            }
        )

        if commit:
            decision_rows.append(
                {
                    "chain_node_id": node.id,
                    "selected_person_id": (
                        top.person_id if top and decision_type == "approve_current" else None
                    ),
                    "decision_type": decision_type,
                    "confidence_tier": tier,
                    "reviewer": reviewer,
                    "resolver_version": PERSON_RESOLVER_VERSION,
                    "question_text": _question(node, top, context),
                    "decision_summary": summary,
                    "evidence_json": evidence,
                }
            )
        stats.decisions_written += 1
        stats.decision_counts[decision_type] += 1
        stats.confidence_counts[tier] += 1
        for flag in evidence["risk_flags"]:
            stats.risk_counts[flag] += 1

    if commit:
        for chunk in _chunks(decision_rows):
            db.bulk_insert_mappings(PersonResolutionDecision, chunk)
        db.commit()
    return stats


def _person_label(context: dict, person_id: int | None) -> str:
    if person_id is None:
        return ""
    person = context["persons"].get(person_id)
    if person is None:
        return f"person {person_id}"
    gen = _cluster_generation(context, person_id)
    gen_text = f" | generation {gen[0]}-{gen[1]}" if gen else ""
    return f"{person.canonical_name_ar} (person_id={person_id}, kind={person.kind}{gen_text})"


def _decision_cases(
    db: Session,
    *,
    source_book_id: str,
    reviewer: str,
    decision_types: set[str],
    skip: int,
    limit: int,
) -> list[tuple[PersonResolutionDecision, ChainNode, Chain, Hadith]]:
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise ValueError(f"Book not found: {source_book_id}")
    return (
        db.query(PersonResolutionDecision, ChainNode, Chain, Hadith)
        .join(ChainNode, ChainNode.id == PersonResolutionDecision.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(
            Hadith.book_id == book.id,
            Hadith.review_status != _REJECTED_HADITH_STATUS,
            PersonResolutionDecision.reviewer == reviewer,
            PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
            PersonResolutionDecision.decision_type.in_(tuple(decision_types)),
        )
        .order_by(Hadith.sequence_in_book, Chain.chain_number, ChainNode.position)
        .offset(max(skip, 0))
        .limit(max(1, limit))
        .all()
    )


def _case_json(
    db: Session,
    decision: PersonResolutionDecision,
    node: ChainNode,
    chain: Chain,
    hadith: Hadith,
) -> dict:
    rows_by_node = _load_resolutions(db, [node.id])
    candidates = rows_by_node.get(node.id, [])
    person_ids = {
        row.person_id for row in candidates if row.person_id is not None
    }
    context = _load_person_context(db, person_ids)
    chain_nodes = (
        db.query(ChainNode)
        .filter(ChainNode.chain_id == chain.id)
        .order_by(ChainNode.position)
        .all()
    )
    return {
        "case_id": f"{hadith.public_id}:chain{chain.chain_number}:pos{node.position}:node{node.id}",
        "decision": {
            "type": decision.decision_type,
            "confidence_tier": decision.confidence_tier,
            "summary": decision.decision_summary,
            "question": decision.question_text,
            "evidence": decision.evidence_json or {},
        },
        "hadith": {
            "public_id": hadith.public_id,
            "sequence_in_book": hadith.sequence_in_book,
            "section_title": hadith.section_title,
            "volume_start": hadith.volume_start,
            "page_start": hadith.page_start,
            "page_end": hadith.page_end,
            "source_url": hadith.source_url,
            "full_text_arabic": hadith.full_text_raw,
            "isnad_arabic": hadith.isnad_raw,
            "matn_arabic": hadith.matn_raw,
        },
        "target_mention": {
            "chain_id": chain.id,
            "chain_number": chain.chain_number,
            "node_id": node.id,
            "position": node.position,
            "raw_token": node.raw_token,
            "token_normalised": node.token_normalised,
            "node_type": node.node_type,
            "relation_kind": node.relation_kind,
        },
        "chain_nodes": [
            {
                "position": n.position,
                "raw_token": n.raw_token,
                "node_type": n.node_type,
                "relation_kind": n.relation_kind,
            }
            for n in chain_nodes
        ],
        "candidates": _candidate_payload(context, candidates),
    }


def _case_markdown(case: dict, index: int) -> str:
    target = case["target_mention"]
    decision = case["decision"]
    hadith = case["hadith"]
    lines: list[str] = []
    a = lines.append
    a(f"## Case {index:03d}: {case['case_id']}")
    a("")
    a("### Review Question")
    a(decision["question"] or "")
    a("")
    a("### Machine Suspicion / Current Decision")
    a(f"- Decision type: `{decision['type']}`")
    a(f"- Confidence tier: `{decision['confidence_tier']}`")
    a(f"- Summary: {decision['summary'] or ''}")
    flags = decision.get("evidence", {}).get("risk_flags", [])
    a(f"- Risk flags: {', '.join(flags) if flags else 'none'}")
    a("")
    a("### Hadith Context")
    a(f"- Hadith ID: `{hadith['public_id']}`")
    a(f"- Sequence: `{hadith['sequence_in_book']}`")
    a(f"- Location: vol. `{hadith['volume_start']}`, pp. `{hadith['page_start']}-{hadith['page_end']}`")
    if hadith.get("section_title"):
        a(f"- Section: {hadith['section_title']}")
    a("")
    a("#### Full Arabic Hadith")
    a("```arabic")
    a(hadith["full_text_arabic"] or "")
    a("```")
    a("")
    a("#### Isnad Arabic")
    a("```arabic")
    a(hadith["isnad_arabic"] or "")
    a("```")
    a("")
    a("### Target Mention")
    a(f"- Chain: `{target['chain_number']}`")
    a(f"- Position: `{target['position']}`")
    a(f"- Node ID: `{target['node_id']}`")
    a(f"- Token: `{target['raw_token']}`")
    a(f"- Node type: `{target['node_type']}`")
    if target.get("relation_kind"):
        a(f"- Relation kind: `{target['relation_kind']}`")
    a("")
    a("### Parsed Chain")
    a("| Position | Token | Type | Relation |")
    a("|---:|---|---|---|")
    for node in case["chain_nodes"]:
        a(
            f"| {node['position']} | {node['raw_token']} | "
            f"{node['node_type']} | {node.get('relation_kind') or ''} |"
        )
    a("")
    a("### Candidate Persons")
    if case["candidates"]:
        a("| Rank | Status | Method | Person | Score | Margin | Evidence |")
        a("|---:|---|---|---|---:|---:|---|")
        for cand in case["candidates"]:
            person = cand["person_name"] or ""
            if cand["person_id"] is not None:
                person = f"{person} (person_id={cand['person_id']})"
            evidence = _compact(cand.get("evidence_summary"), 220).replace("|", "/")
            a(
                f"| {cand['rank']} | {cand['status']} | {cand.get('method') or ''} | "
                f"{person} | {cand.get('score') or ''} | {cand.get('margin') or ''} | {evidence} |"
            )
    else:
        a("No candidate rows exist for this mention.")
    a("")
    a("### External Reviewer Task")
    a("Please verify this case using external rijal/hadith sources. Answer in exactly this structure:")
    a("")
    a("```text")
    a("Case ID:")
    a("Verdict: approve_current / override_person / keep_ambiguous / flag_text_or_chain_issue")
    a("Correct person, if any:")
    a("Confidence: high / medium / low")
    a("Evidence consulted:")
    a("Reasoning:")
    a("If override_person: canonical Arabic name and source reference:")
    a("```")
    return "\n".join(lines)


def export_external_review_packet(
    db: Session,
    *,
    output_dir: str | Path,
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    reviewer: str = REVIEWER,
    decision_types: set[str] | None = None,
    skip: int = 0,
    limit: int = 25,
) -> ExportStats:
    decision_types = decision_types or {"needs_external_review", "flag_contradiction"}
    cases = _decision_cases(
        db,
        source_book_id=source_book_id,
        reviewer=reviewer,
        decision_types=decision_types,
        skip=skip,
        limit=limit,
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = out_dir / f"person_review_packet_{source_book_id}_{stamp}.md"
    jsonl_path = out_dir / f"person_review_packet_{source_book_id}_{stamp}.jsonl"

    case_payloads = [
        _case_json(db, decision, node, chain, hadith)
        for decision, node, chain, hadith in cases
    ]
    header = [
        "# Person-Resolution External Review Packet",
        "",
        f"- Source book ID: `{source_book_id}`",
        f"- Generated: `{stamp}`",
        f"- Reviewer decisions included: `{', '.join(sorted(decision_types))}`",
        f"- Cases: `{len(case_payloads)}`",
        "",
        "Use this packet to verify person identity in isnad nodes. The machine decision is a hypothesis, not an authority.",
        "",
    ]
    md_body = "\n".join(header + [_case_markdown(case, idx) for idx, case in enumerate(case_payloads, 1)])
    md_path.write_text(md_body, encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as f:
        for case in case_payloads:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    return ExportStats(str(md_path), str(jsonl_path), len(case_payloads))
