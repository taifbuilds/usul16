"""Import external person-resolution review results.

The review packets ask another verifier/LLM to return a fixed template per
case. This module parses those filled templates, repairs common mojibake from
copy/paste, stores the external judgement, and tries to match the named person
back to existing person rows without applying silent resolver overrides.
"""

from __future__ import annotations

import dataclasses
import re
from collections import Counter
from pathlib import Path

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    ChainNode,
    MentionResolution,
    Person,
    PersonResolutionDecision,
    PersonResolutionExternalReview,
    PersonSurfaceForm,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

PARSER_VERSION = "external_review_v1"
MACHINE_REVIEWER = "codex-machine-v1"
ADMIN_REVIEWER = "codex-admin-external-v1"
ACTIONABLE_VERDICTS = {"approve_current", "override_person", "keep_ambiguous", "flag_text_or_chain_issue"}


@dataclasses.dataclass
class ExternalReviewCase:
    case_id: str
    public_id: str
    chain_number: int
    position: int
    node_id: int
    verdict: str
    correct_person_text: str | None
    confidence_raw: str | None
    confidence_tier: str | None
    evidence_consulted: str | None
    reasoning: str | None
    source_reference: str | None
    raw_case_text: str


@dataclasses.dataclass
class ExternalReviewImportStats:
    files_seen: int = 0
    cases_parsed: int = 0
    rows_written: int = 0
    matched_person: int = 0
    unmatched_person: int = 0
    missing_nodes: int = 0
    verdict_counts: Counter[str] = dataclasses.field(default_factory=Counter)
    confidence_counts: Counter[str] = dataclasses.field(default_factory=Counter)


@dataclasses.dataclass
class ExternalReviewPromotionStats:
    reviews_seen: int = 0
    decisions_written: int = 0
    skipped_unmatched: int = 0
    skipped_unknown_verdict: int = 0
    verdict_counts: Counter[str] = dataclasses.field(default_factory=Counter)
    decision_counts: Counter[str] = dataclasses.field(default_factory=Counter)


_CASE_ID_RE = re.compile(
    r"(alkafi-\d+):chain(\d+):pos(\d+):node(\d+)",
    re.IGNORECASE,
)
_LABELS = (
    "Case ID",
    "Verdict",
    "Correct person, if any",
    "Confidence",
    "Evidence consulted",
    "Reasoning",
    "If override_person: canonical Arabic name and source reference",
)
_LABEL_LOOKAHEAD = "|".join(re.escape(label) for label in _LABELS)
_CASE_HEADING_RE = re.compile(r"^###\s+Case\s+\d+:[^\n]*\n[ \t\r\n]*(?=Case ID:)", re.MULTILINE)
_NEXT_CASE_HEADING_RE = re.compile(r"^###\s+Case\s+\d+:", re.MULTILINE)
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_NAME_PART_SPLIT_RE = re.compile(r"\s*(?:/|;|\u061b|\u060c|\u2014|\u2013|--|\s-\s|\n)\s*")
_BIBLIO_START_RE = re.compile(
    r"\s+(?:\u0645\u0639\u062c\u0645|\u0631\u062c\u0627\u0644|rijal|mu.?jam|vol\.|p\.)\b",
    re.IGNORECASE,
)
_TRAILING_NISBA_RE = re.compile(r"^(?:ال|ا)[^\s]+$")


def repair_mojibake(text: str) -> str:
    """Repair common UTF-8-as-cp1252 mojibake when it is clearly better."""

    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text
    arabic_before = sum("\u0600" <= ch <= "\u06ff" for ch in text)
    arabic_after = sum("\u0600" <= ch <= "\u06ff" for ch in repaired)
    replacement_after = repaired.count("\ufffd")
    if arabic_after > arabic_before and replacement_after < 10:
        return repaired
    return text


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _field(block: str, label: str) -> str | None:
    pattern = rf"^{re.escape(label)}:\s*(.*?)(?=^(?:{_LABEL_LOOKAHEAD}):|{_NEXT_CASE_HEADING_RE.pattern}|\Z)"
    match = re.search(pattern, block, flags=re.MULTILINE | re.DOTALL)
    return _clean(match.group(1)) if match else None


def _confidence_tier(raw: str | None) -> str | None:
    if not raw:
        return None
    first = raw.strip().split()[0].lower().strip(":;,.")
    if first in {"high", "medium", "low"}:
        return first
    return None


def parse_external_review_text(text: str) -> list[ExternalReviewCase]:
    text = repair_mojibake(text)
    text = _CASE_HEADING_RE.sub("", text)
    blocks = re.split(r"(?=^Case ID:)", text, flags=re.MULTILINE)
    cases: list[ExternalReviewCase] = []
    for block in blocks:
        if not block.strip().startswith("Case ID:"):
            continue
        case_id = _field(block, "Case ID") or ""
        match = _CASE_ID_RE.search(case_id)
        if not match:
            continue
        public_id, chain_number, position, node_id = match.groups()
        verdict = (_field(block, "Verdict") or "").strip()
        confidence = _field(block, "Confidence")
        cases.append(
            ExternalReviewCase(
                case_id=case_id,
                public_id=public_id,
                chain_number=int(chain_number),
                position=int(position),
                node_id=int(node_id),
                verdict=verdict,
                correct_person_text=_field(block, "Correct person, if any"),
                confidence_raw=confidence,
                confidence_tier=_confidence_tier(confidence),
                evidence_consulted=_field(block, "Evidence consulted"),
                reasoning=_field(block, "Reasoning"),
                source_reference=_field(
                    block,
                    "If override_person: canonical Arabic name and source reference",
                ),
                raw_case_text=block.strip(),
            )
        )
    return cases


def _norm(text: str | None) -> str:
    return normalise_arabic_persian(text or "").strip()


def _person_text_candidates(case: ExternalReviewCase) -> list[str]:
    candidates: list[str] = []

    def add_candidate(raw_value: str) -> None:
        if len(_ARABIC_RE.findall(raw_value)) < 2:
            return
        cleaned = _norm(raw_value)
        if not cleaned or cleaned.lower() in {"n/a", "none"}:
            return
        # Drop common trailing bibliographic fragments while keeping the Arabic name.
        cleaned = _BIBLIO_START_RE.split(cleaned, maxsplit=1)[0].strip()
        if len(cleaned) >= 5 and cleaned not in candidates:
            candidates.append(cleaned)

    for value in (case.source_reference, case.correct_person_text):
        if not value or value.lower().strip() in {"n/a", "none"}:
            continue
        value = re.sub(r"\([^)]*\)", " ", value)
        value = re.sub(r"\[[^\]]*\]", " ", value)
        parts = _NAME_PART_SPLIT_RE.split(value)
        for index, part in enumerate(parts):
            add_candidate(part)
            if index + 1 >= len(parts):
                continue
            # Handle slash alternatives where the right side is only the last
            # laqab/nisba, e.g. "الحسن بن محبوب السراد / الزراد".
            left_words = _norm(part).split()
            right_words = _norm(parts[index + 1]).split()
            if left_words and 0 < len(right_words) <= 2:
                add_candidate(" ".join(left_words[: -len(right_words)] + right_words))
    return candidates


def _expanded_name_variants(normalised_name: str, *, include_broad: bool = True) -> list[str]:
    """Conservative aliases for external-review names not present verbatim."""

    variants = [normalised_name]
    words = normalised_name.split()

    if words[-2:] == [_norm("آل"), _norm("يقطين")]:
        # "مولى آل يقطين" is an identifying note for names like
        # "يونس بن عبد الرحمن", not part of the local canonical name.
        mawla = _norm("مولى")
        if mawla in words:
            index = words.index(mawla)
            variants.append(" ".join(words[:index]))

    if words[-1:] == [_norm("اليقطيني")] and len(words) >= 2:
        # The catalogue has "بن يقطين" for some people where the verifier wrote
        # the nisba "اليقطيني"; prefer that fuller nasab before stripping nisbas.
        variants.append(" ".join(words[:-1] + [_norm("بن"), _norm("يقطين")]))

    if words[-1:] == [_norm("السراد")] and len(words) >= 2:
        variants.append(" ".join(words[:-1] + [_norm("الزراد")]))

    if include_broad and len(words) >= 4 and _TRAILING_NISBA_RE.match(words[-1]):
        variants.append(" ".join(words[:-1]))

    return [variant for variant in dict.fromkeys(variants) if variant]


def _name_search_terms(normalised_name: str) -> list[str]:
    """Return specific name fragments suitable for a safe unique-prefix lookup."""

    words = normalised_name.split()
    terms: list[str] = []
    # Longest windows first. Three words is the lower bound; two-word terms like
    # "ابو جعفر" or "بن هاشم" are too broad for automatic overrides.
    max_size = min(6, len(words))
    for size in range(max_size, 2, -1):
        terms.append(" ".join(words[:size]))
    for size in range(max_size, 2, -1):
        for start in range(1, len(words) - size + 1):
            terms.append(" ".join(words[start : start + size]))
    return list(dict.fromkeys(terms))


def _unique_person_for_prefix(db: Session, term: str) -> int | None:
    person_ids = set(
        db.execute(
            select(Person.id).where(Person.canonical_name_norm.startswith(term))
        ).scalars()
    )
    person_ids.update(
        db.execute(
            select(PersonSurfaceForm.person_id).where(PersonSurfaceForm.form_norm == term)
        ).scalars()
    )
    if len(person_ids) == 1:
        return next(iter(person_ids))
    return None


def _top_person_for_node(db: Session, node_id: int) -> int | None:
    row = (
        db.query(MentionResolution)
        .filter(
            MentionResolution.chain_node_id == node_id,
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            MentionResolution.rank == 1,
        )
        .one_or_none()
    )
    return row.person_id if row else None


def _match_person_by_text(db: Session, case: ExternalReviewCase) -> int | None:
    candidates = _person_text_candidates(case)
    if not candidates:
        return None

    # First prefer candidates already emitted by the resolver for this node.
    node_person_ids = [
        pid
        for (pid,) in db.execute(
            select(MentionResolution.person_id).where(
                MentionResolution.chain_node_id == case.node_id,
                MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
                MentionResolution.person_id.isnot(None),
            )
        )
        if pid is not None
    ]
    if node_person_ids:
        rows = db.execute(
            select(Person.id, Person.canonical_name_norm).where(Person.id.in_(node_person_ids))
        ).all()
        for wanted in candidates:
            for variant in _expanded_name_variants(wanted, include_broad=False):
                hits = [
                    pid
                    for pid, name_norm in rows
                    if variant == _norm(name_norm) or _norm(name_norm).startswith(variant)
                ]
                if len(set(hits)) == 1:
                    return hits[0]

    for wanted in candidates:
        for variant in _expanded_name_variants(wanted):
            exact = db.execute(
                select(Person.id).where(Person.canonical_name_norm == variant)
            ).scalars().all()
            if len(exact) == 1:
                return exact[0]
            form_hits = db.execute(
                select(PersonSurfaceForm.person_id).where(PersonSurfaceForm.form_norm == variant)
            ).scalars().all()
            if len(set(form_hits)) == 1:
                return next(iter(set(form_hits)))
            for term in _name_search_terms(variant):
                matched_id = _unique_person_for_prefix(db, term)
                if matched_id is not None:
                    return matched_id
    return None


def _match_person(db: Session, case: ExternalReviewCase) -> int | None:
    if case.verdict == "approve_current":
        top_person_id = _top_person_for_node(db, case.node_id)
        return top_person_id if top_person_id is not None else _match_person_by_text(db, case)
    if case.verdict == "override_person":
        return _match_person_by_text(db, case)
    return None


def import_external_review_file(
    db: Session,
    path: str | Path,
    *,
    source_label: str | None = None,
    external_reviewer: str = "external-llm",
    commit: bool = True,
    write: bool = True,
) -> ExternalReviewImportStats:
    path = Path(path)
    source_label = source_label or path.stem
    text = path.read_text(encoding="utf-8")
    cases = parse_external_review_text(text)
    stats = ExternalReviewImportStats(files_seen=1, cases_parsed=len(cases))

    for case in cases:
        node = db.get(ChainNode, case.node_id)
        if node is None:
            stats.missing_nodes += 1
            continue
        decision = (
            db.query(PersonResolutionDecision)
            .filter(
                PersonResolutionDecision.chain_node_id == case.node_id,
                PersonResolutionDecision.reviewer == MACHINE_REVIEWER,
                PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
            )
            .one_or_none()
        )
        matched_person_id = _match_person(db, case)
        if matched_person_id is not None:
            stats.matched_person += 1
        elif case.verdict in {"approve_current", "override_person"}:
            stats.unmatched_person += 1

        if write:
            db.execute(
                delete(PersonResolutionExternalReview).where(
                    PersonResolutionExternalReview.chain_node_id == case.node_id,
                    PersonResolutionExternalReview.source_label == source_label,
                    PersonResolutionExternalReview.case_id == case.case_id,
                )
            )
            db.add(
                PersonResolutionExternalReview(
                    decision_id=decision.id if decision else None,
                    chain_node_id=case.node_id,
                    matched_person_id=matched_person_id,
                    case_id=case.case_id,
                    source_label=source_label,
                    external_reviewer=external_reviewer,
                    verdict=case.verdict,
                    confidence_raw=case.confidence_raw,
                    confidence_tier=case.confidence_tier,
                    correct_person_text=case.correct_person_text,
                    evidence_consulted=case.evidence_consulted,
                    reasoning=case.reasoning,
                    source_reference=case.source_reference,
                    raw_case_text=case.raw_case_text,
                    parser_version=PARSER_VERSION,
                )
            )
        stats.rows_written += 1
        stats.verdict_counts[case.verdict] += 1
        if case.confidence_tier:
            stats.confidence_counts[case.confidence_tier] += 1

    if write:
        if commit:
            db.commit()
        else:
            db.flush()
    return stats


def import_external_review_files(
    db: Session,
    paths: list[str | Path],
    *,
    external_reviewer: str = "external-llm",
    commit: bool = True,
) -> ExternalReviewImportStats:
    total = ExternalReviewImportStats()
    for path in paths:
        stats = import_external_review_file(
            db,
            path,
            source_label=Path(path).stem,
            external_reviewer=external_reviewer,
            commit=False,
            write=commit,
        )
        total.files_seen += stats.files_seen
        total.cases_parsed += stats.cases_parsed
        total.rows_written += stats.rows_written
        total.matched_person += stats.matched_person
        total.unmatched_person += stats.unmatched_person
        total.missing_nodes += stats.missing_nodes
        total.verdict_counts.update(stats.verdict_counts)
        total.confidence_counts.update(stats.confidence_counts)
    if commit:
        db.commit()
    return total


def _admin_decision_type(review: PersonResolutionExternalReview) -> str | None:
    if review.verdict == "approve_current":
        return "approve_current"
    if review.verdict == "override_person":
        return "approve_external_override"
    if review.verdict == "keep_ambiguous":
        return "keep_ambiguous"
    if review.verdict == "flag_text_or_chain_issue":
        return "flag_text_or_chain_issue"
    return None


def promote_external_reviews_to_admin_decisions(
    db: Session,
    *,
    source_book_id: str | None = None,
    reviewer: str = ADMIN_REVIEWER,
    commit: bool = True,
    write: bool = True,
) -> ExternalReviewPromotionStats:
    """Promote imported external reviews into explicit admin decisions."""

    query = (
        db.query(PersonResolutionExternalReview, PersonResolutionDecision)
        .outerjoin(
            PersonResolutionDecision,
            and_(
                PersonResolutionDecision.id == PersonResolutionExternalReview.decision_id,
            ),
        )
    )
    if source_book_id:
        from eshia_research.models import Book, Chain, Hadith

        query = (
            db.query(PersonResolutionExternalReview, PersonResolutionDecision)
            .join(ChainNode, ChainNode.id == PersonResolutionExternalReview.chain_node_id)
            .join(Chain, Chain.id == ChainNode.chain_id)
            .join(Hadith, Hadith.id == Chain.hadith_id)
            .join(Book, Book.id == Hadith.book_id)
            .outerjoin(
                PersonResolutionDecision,
                PersonResolutionDecision.id == PersonResolutionExternalReview.decision_id,
            )
            .filter(Book.source_book_id == source_book_id)
        )

    rows = query.order_by(PersonResolutionExternalReview.id).all()
    stats = ExternalReviewPromotionStats(reviews_seen=len(rows))
    # More than one packet can review the same node. Admin decisions are unique
    # per node/reviewer/resolver, so promote only the latest imported review.
    latest_by_node: dict[int, tuple[PersonResolutionExternalReview, PersonResolutionDecision | None]] = {}
    for review, machine_decision in rows:
        latest_by_node[review.chain_node_id] = (review, machine_decision)
    decision_rows: list[dict] = []
    node_ids: list[int] = []

    for review, machine_decision in latest_by_node.values():
        if review.verdict not in ACTIONABLE_VERDICTS:
            stats.skipped_unknown_verdict += 1
            continue
        decision_type = _admin_decision_type(review)
        if decision_type is None:
            stats.skipped_unknown_verdict += 1
            continue
        if review.verdict in {"approve_current", "override_person"} and review.matched_person_id is None:
            stats.skipped_unmatched += 1
            continue
        if (
            review.verdict == "approve_current"
            and review.matched_person_id is not None
            and (
                machine_decision is None
                or machine_decision.selected_person_id != review.matched_person_id
            )
        ):
            decision_type = "approve_external_override"

        selected_person_id = review.matched_person_id if review.verdict in {"approve_current", "override_person"} else None
        summary = {
            "approve_current": "External review approved the current top person.",
            "approve_external_override": "External review selected a different person than the machine decision.",
            "keep_ambiguous": "External review kept the mention ambiguous.",
            "flag_text_or_chain_issue": "External review flagged a text or chain issue.",
        }[decision_type]
        evidence = {
            "source": "external_review_import",
            "external_review_id": review.id,
            "case_id": review.case_id,
            "source_label": review.source_label,
            "external_reviewer": review.external_reviewer,
            "external_verdict": review.verdict,
            "external_confidence": review.confidence_raw,
            "correct_person_text": review.correct_person_text,
            "source_reference": review.source_reference,
            "reasoning": review.reasoning,
            "machine_decision": (
                {
                    "id": machine_decision.id,
                    "decision_type": machine_decision.decision_type,
                    "selected_person_id": machine_decision.selected_person_id,
                    "confidence_tier": machine_decision.confidence_tier,
                }
                if machine_decision
                else None
            ),
        }
        decision_rows.append(
            {
                "chain_node_id": review.chain_node_id,
                "selected_person_id": selected_person_id,
                "decision_type": decision_type,
                "confidence_tier": review.confidence_tier or "low",
                "reviewer": reviewer,
                "resolver_version": PERSON_RESOLVER_VERSION,
                "question_text": machine_decision.question_text if machine_decision else None,
                "decision_summary": summary,
                "evidence_json": evidence,
            }
        )
        node_ids.append(review.chain_node_id)
        stats.decisions_written += 1
        stats.verdict_counts[review.verdict] += 1
        stats.decision_counts[decision_type] += 1

    if write and node_ids:
        db.execute(
            delete(PersonResolutionDecision).where(
                PersonResolutionDecision.chain_node_id.in_(node_ids),
                PersonResolutionDecision.reviewer == reviewer,
                PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
            )
        )
        db.bulk_insert_mappings(PersonResolutionDecision, decision_rows)
        if commit:
            db.commit()
        else:
            db.flush()
    return stats
