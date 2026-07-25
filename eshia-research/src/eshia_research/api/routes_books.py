import dataclasses
import datetime as dt
import time

from fastapi import APIRouter, Depends, HTTPException
from bs4 import BeautifulSoup, Tag
from sqlalchemy import Integer, and_, case, cast, exists, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from eshia_research.db import get_db
from eshia_research.api.security import require_admin_api_token
from eshia_research.corpus import (
    AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    CATALOG_EXCLUDED_SOURCE_BOOK_IDS,
    POLISHED_TRANSMISSION_BOOK_IDS,
)
from eshia_research.hadith_split_audit import (
    active_split_texts,
    build_hadith_split_audit_report,
    review_status_key,
    split_suspicion_flags,
)
from eshia_research.models import (
    Author,
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    HadithGrading,
    HadithSplitReview,
    HadithTranslation,
    HadithTopicAssignment,
    MentionResolution,
    Narrator,
    NarratorAlias,
    Page,
    Person,
    PersonGeneration,
    PersonResolutionDecision,
    RijalEntry,
    RijalOccurrence,
    RijalStatement,
    ThaqalaynStructureMap,
    Topic,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.schemas import (
    BookRead,
    BookSummary,
    ChapterSummary,
    HadithGradingRead,
    HadithStructureRead,
    HadithTopicRead,
    KitabSummary,
    ThaqalaynChapterSummary,
    CorpusBookStatus,
    CorpusStatusResponse,
    HadithSplitAudit,
    HadithSplitFlagCount,
    HadithSplitReviewItem,
    HadithSplitReviewSave,
    HadithSplitReviewStats,
    HadithChainsRead,
    HadithRead,
    LibraryStats,
    NarratorDetailRead,
    NarratorDirectoryEntry,
    NarratorDirectoryPage,
    NarratorHadithAppearancePage,
    NarratorSummaryRead,
    NarratorTransmissionEdgesRead,
    PageIndexEntry,
    PageRead,
    PersonResolutionAuditCandidate,
    PersonResolutionAdminDecisionRead,
    PersonResolutionEffectiveRead,
    PersonResolutionAuditItem,
    PersonResolutionAuditPage,
    PersonResolutionAuditSummary,
    PersonResolutionDecisionCount,
    PersonResolutionDecisionSummary,
    PersonResolutionMethodCount,
    PersonResolutionNodeTypeCount,
    PersonResolutionStatusCount,
    TransmissionEdgeEvidenceItem,
    TransmissionEdgeEvidenceRead,
    TransmissionGraphEdge,
    TransmissionGraphNode,
    TransmissionGraphRead,
    TransmissionPath,
    TransmissionPathHop,
    TransmissionPathNode,
    TransmissionPathsRead,
)
from eshia_research.translation.publication import (
    PUBLIC_TRANSLATION_VERSIONS,
    has_blocking_risk_flag,
    has_public_human_source_metadata,
    is_public_english_translation,
    public_english_translation_candidate_filters,
    source_hash_values_are_current,
)

router = APIRouter(tags=["books"])

# Book.language is never populated by the crawler (see models.py), so the
# public catalog has to keep Persian-only works out heuristically. Persian
# kaf/yeh are not used here as broad signals because eShia also uses those
# glyphs in many otherwise-Arabic titles (e.g. al-Kafi, al-Bayt editions).
_PERSIAN_ONLY_LETTERS = ("\u067e", "\u0686", "\u0698", "\u06af")
_PERSIAN_TITLE_MARKERS = (
    "\u0622\u0634\u0646\u0627\u06cc\u06cc",  # آشنایی
    "\u0627\u062d\u06a9\u0627\u0645",  # احکام (Persian kaf)
    "\u062e\u0627\u0646\u0648\u0627\u062f\u0647",  # خانواده
    "\u0646\u0645\u0627\u0632",  # نماز
    "\u0631\u0648\u0632\u0647",  # روزه
    "\u0628\u0627\u0646\u0648\u0627\u0646",  # بانوان
    "\u0628\u06cc\u0645\u0627\u0631\u0627\u0646",  # بیماران
    "\u0627\u0646\u062f\u06cc\u0634\u0647",  # اندیشه
    "\u0633\u06cc\u0627\u0633\u06cc",  # سیاسی
    "\u062a\u0631\u062c\u0645\u0647",  # ترجمه
    "\u0641\u0627\u0631\u0633",  # فارس/فارسی/فارسى
    "\u0634\u0646\u0627\u0633\u06cc",  # شناسی
    "\u06af\u0632\u06cc\u062f\u0647",  # گزیده
    "\u0645\u062c\u0645\u0648\u0639\u0647",  # مجموعه
    "\u062f\u0627\u0646\u0634",  # دانش...
    "\u0646\u06af\u0627\u0647",  # نگاه/نگاهی
)
_PERSIAN_TITLE_PHRASES = (
    " \u062f\u0631 ",  # در
    " \u0628\u0627 ",  # با
)
_SPLIT_REVIEW_STATUSES = {"approved", "needs_review", "rejected"}
_REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"
_NARRATOR_APPEARANCE_BOOK_PRIORITY = {
    "11005": 0,  # al-Kafi
    "10083": 1,  # Tahdhib al-Ahkam
    "11002": 2,  # al-Istibsar
    "11021": 3,  # Man La Yahduruhu al-Faqih
    "71860": 4,  # Bihar al-Anwar
}


def _readable_content_exists():
    """A book is readable only once more than first-page scan stubs exist.

    The crawler's full-library phase first scans page 1 of every volume to
    learn volume lengths. Interrupted runs therefore leave many books with
    exactly one stored page per volume. Those are useful crawl state, but
    they should not be advertised as "Full text available" in the UI.
    """
    return exists().where(
        Page.book_id == Book.id,
        Page.page_number > 1,
        Page.text_raw.isnot(None),
    )


def _readable_page_count():
    return (
        select(func.count(Page.id))
        .where(
            Page.book_id == Book.id,
            Page.page_number > 1,
            Page.text_raw.isnot(None),
        )
        .correlate(Book)
        .scalar_subquery()
    )


def _apply_arabic_catalog_filters(query):
    if CATALOG_EXCLUDED_SOURCE_BOOK_IDS:
        query = query.filter(~Book.source_book_id.in_(CATALOG_EXCLUDED_SOURCE_BOOK_IDS))
    for marker in (*_PERSIAN_ONLY_LETTERS, *_PERSIAN_TITLE_MARKERS, *_PERSIAN_TITLE_PHRASES):
        query = query.filter(~Book.title_original.contains(marker))
    return query


def _active_split(hadith: Hadith, review: HadithSplitReview | None) -> tuple[str | None, str]:
    split = active_split_texts(hadith, review)
    return split.isnad_raw, split.matn_raw


def _split_suspicion_flags(hadith: Hadith, review: HadithSplitReview | None = None) -> list[str]:
    return split_suspicion_flags(hadith, review)


def _review_item(hadith: Hadith, review: HadithSplitReview | None) -> HadithSplitReviewItem:
    active_isnad, active_matn = _active_split(hadith, review)
    return HadithSplitReviewItem(
        hadith=hadith,
        review=review,
        active_isnad_raw=active_isnad,
        active_matn_raw=active_matn,
        suspicion_flags=_split_suspicion_flags(hadith, review),
    )


def _apply_approved_split(hadith: Hadith, review: HadithSplitReview | None) -> Hadith:
    if review and review.review_status == "approved" and review.approved_matn_raw is not None:
        hadith.isnad_raw = review.approved_isnad_raw
        hadith.matn_raw = review.approved_matn_raw
    return hadith


def _apply_approved_splits(db: Session, hadiths: list[Hadith]) -> list[Hadith]:
    hadith_ids = [hadith.id for hadith in hadiths]
    if not hadith_ids:
        return hadiths
    reviews = (
        db.query(HadithSplitReview)
        .filter(
            HadithSplitReview.hadith_id.in_(hadith_ids),
            HadithSplitReview.review_status == "approved",
            HadithSplitReview.approved_matn_raw.isnot(None),
        )
        .all()
    )
    reviews_by_hadith_id = {review.hadith_id: review for review in reviews}
    for hadith in hadiths:
        _apply_approved_split(hadith, reviews_by_hadith_id.get(hadith.id))
    return hadiths


def _attach_public_translations(db: Session, hadiths: list[Hadith]) -> list[Hadith]:
    """Attach only complete, green translations that still match the Arabic.

    Planned, partial, risky, and source-stale rows never cross the public API
    boundary. The attribute is response-only and is not persisted on Hadith.
    """
    hadith_ids = [hadith.id for hadith in hadiths]
    if not hadith_ids:
        return hadiths
    rows = (
        db.query(HadithTranslation)
        .filter(
            HadithTranslation.hadith_id.in_(hadith_ids),
            *public_english_translation_candidate_filters(),
        )
        .all()
    )
    # A hadith may now have more than one candidate version; prefer the earliest
    # entry in PUBLIC_TRANSLATION_VERSIONS, and only attach it if it still passes
    # the full fail-closed check (which includes the source-hash currency test).
    version_rank = {v: i for i, v in enumerate(PUBLIC_TRANSLATION_VERSIONS)}
    by_hadith_id: dict[int, list[HadithTranslation]] = {}
    for row in rows:
        by_hadith_id.setdefault(row.hadith_id, []).append(row)
    for hadith in hadiths:
        candidates = sorted(
            by_hadith_id.get(hadith.id, []),
            key=lambda r: version_rank.get(r.translation_version, len(version_rank)),
        )
        chosen = next(
            (c for c in candidates if is_public_english_translation(c, hadith)), None
        )
        hadith.translation = chosen
    return hadiths


def _attach_structure_and_gradings(db: Session, hadiths: list[Hadith]) -> list[Hadith]:
    """Attach Thaqalayn kitab/chapter placement and gradings (response-only)."""
    hadith_ids = [h.id for h in hadiths]
    if not hadith_ids:
        return hadiths
    structure_by_id = {
        s.hadith_id: s
        for s in db.query(ThaqalaynStructureMap)
        .filter(
            ThaqalaynStructureMap.hadith_id.in_(hadith_ids),
            ThaqalaynStructureMap.source.in_(("thaqalayn-website", "thaqalayn-api")),
        )
        .all()
    }
    gradings_by_id: dict[int, list[HadithGrading]] = {}
    for g in (
        db.query(HadithGrading)
        .filter(
            HadithGrading.hadith_id.in_(hadith_ids),
            HadithGrading.source == "thaqalayn-api",
        )
        .order_by(HadithGrading.display_order)
        .all()
    ):
        gradings_by_id.setdefault(g.hadith_id, []).append(g)
    for hadith in hadiths:
        smap = structure_by_id.get(hadith.id)
        hadith.structure = (
            HadithStructureRead.model_validate(smap) if smap is not None else None
        )
        rows = gradings_by_id.get(hadith.id)
        hadith.gradings = (
            [HadithGradingRead.model_validate(g) for g in rows] if rows else None
        )
    return hadiths


def _attach_topics(db: Session, hadiths: list[Hadith]) -> list[Hadith]:
    """Attach ordered public topic metadata to hadith responses."""
    hadith_ids = [hadith.id for hadith in hadiths]
    if not hadith_ids:
        return hadiths
    by_hadith_id: dict[int, list[HadithTopicRead]] = {}
    rows = (
        db.query(HadithTopicAssignment, Topic)
        .join(Topic, Topic.id == HadithTopicAssignment.topic_id)
        .filter(HadithTopicAssignment.hadith_id.in_(hadith_ids))
        .order_by(
            HadithTopicAssignment.hadith_id,
            HadithTopicAssignment.relevance.desc(),
            Topic.name_en,
        )
        .all()
    )
    for assignment, topic in rows:
        by_hadith_id.setdefault(assignment.hadith_id, []).append(
            HadithTopicRead(
                slug=topic.slug,
                hashtag=topic.hashtag,
                name_en=topic.name_en,
                name_ar=topic.name_ar,
                kind=topic.kind,
                relevance=assignment.relevance,
                confidence=assignment.confidence,
                assignment_method=assignment.assignment_method,
            )
        )
    for hadith in hadiths:
        hadith.topics = by_hadith_id.get(hadith.id, [])
    return hadiths


def _person_resolution_map(db: Session, node_ids: list[int]) -> dict[int, dict]:
    """node_id -> person-level resolution dict (Tamyiz Engine mention_resolutions).

    Returns the resolved person or ranked candidates with generation and dalil,
    reusing the underlying Mu'jam narrator page link when the person came from
    an entry. Empty for nodes with no person resolution yet.
    """
    from eshia_research.rijal.effective_resolution import load_admin_decisions
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

    if not node_ids:
        return {}
    rows = (
        db.query(MentionResolution)
        .filter(
            MentionResolution.chain_node_id.in_(node_ids),
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        )
        .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
        .all()
    )
    if not rows:
        return {}

    # Admin review corrections overlaid below, so the popover agrees with the graph.
    admin_decisions = load_admin_decisions(
        db, resolver_version=PERSON_RESOLVER_VERSION, chain_node_ids=node_ids
    )

    person_ids = {row.person_id for row in rows if row.person_id is not None}
    # Override targets may name a person not among the raw candidates.
    person_ids.update(
        d.selected_person_id for d in admin_decisions.values() if d.selected_person_id is not None
    )
    persons = {
        p.id: p
        for p in db.query(
            Person.id, Person.canonical_name_ar, Person.kind, Person.primary_entry_id
        ).filter(Person.id.in_(person_ids)).all()
    } if person_ids else {}
    # person primary_entry -> Mu'jam narrator id, for the existing narrator page.
    entry_ids = {p.primary_entry_id for p in persons.values() if p.primary_entry_id}
    narrator_by_entry = {
        e.id: e.narrator_id
        for e in db.query(RijalEntry.id, RijalEntry.narrator_id)
        .filter(RijalEntry.id.in_(entry_ids)).all()
    } if entry_ids else {}
    generations = {
        g.person_id: (g.gen_point, g.method)
        for g in db.query(
            PersonGeneration.person_id, PersonGeneration.gen_point, PersonGeneration.method
        ).filter(PersonGeneration.person_id.in_(person_ids)).all()
    } if person_ids else {}

    def person_ref(pid: int | None) -> dict | None:
        if pid is None or pid not in persons:
            return None
        p = persons[pid]
        gen, gen_method = generations.get(pid, (None, None))
        return {
            "id": p.id,
            "canonical_name_ar": p.canonical_name_ar,
            "kind": p.kind,
            "narrator_id": narrator_by_entry.get(p.primary_entry_id),
            "generation": gen,
            "generation_method": gen_method,
        }

    # Person-id -> ref dict, for the effective-resolution overlay (override
    # targets included via the widened person_ids above).
    persons_by_id_ref = {pid: person_ref(pid) for pid in persons}

    by_node: dict[int, list[MentionResolution]] = {}
    for row in rows:
        by_node.setdefault(row.chain_node_id, []).append(row)

    result: dict[int, dict] = {}
    for node_id, node_rows in by_node.items():
        node_rows.sort(key=lambda r: r.rank)
        top = node_rows[0]
        candidates = [
            {
                "rank": r.rank,
                "status": r.status,
                "method": r.method,
                "person": person_ref(r.person_id),
                "evidence_summary": r.evidence_summary,
            }
            for r in node_rows
        ]
        status = "via_collective" if any(r.status == "via_collective" for r in node_rows) else top.status
        resolved_person = (
            person_ref(top.person_id)
            if top.status in ("resolved", "latent", "via_collective")
            else None
        )
        effective = _effective_resolution_read(
            top_row=top,
            resolved_person=resolved_person,
            admin_decision=admin_decisions.get(node_id),
            person_refs=persons_by_id_ref,
        )
        # An admin decision is authoritative: surface it as the headline status
        # and person so the existing popover UI shows the correction unchanged.
        if effective.source == "admin":
            status = effective.status
            resolved_person = effective.person.model_dump() if effective.person else None
        result[node_id] = {
            "status": status,
            "resolved_person": resolved_person,
            "primary_dalil": top.evidence_summary,
            "candidates": candidates,
            "effective": effective,
        }
    return result


_OPEN_PERSON_RESOLUTION_STATUSES = {"ambiguous", "unresolved", "latent"}
_PERSON_AUDIT_STATUSES = {
    "all",
    "open",
    "resolved",
    "ambiguous",
    "unresolved",
    "latent",
    "via_collective",
    "missing_rank1",
}
_PERSON_AUDIT_RISKS = {
    "any",
    "phase_d_context",
    "weak_surface",
    "shared_surface",
    "low_margin",
    "many_candidates",
}
from eshia_research.rijal.effective_resolution import ADMIN_REVIEWER as _ADMIN_PERSON_REVIEWER
from eshia_research.rijal.machine_review import REVIEWER as _MACHINE_PERSON_REVIEWER

_PERSON_AUDIT_MACHINE_DECISIONS = {
    "approve_current",
    "needs_external_review",
    "flag_contradiction",
}


def _admin_decision_read(
    decision: PersonResolutionDecision | None,
    person_refs: dict[int, dict],
) -> PersonResolutionAdminDecisionRead | None:
    if decision is None:
        return None
    evidence = decision.evidence_json if isinstance(decision.evidence_json, dict) else {}
    return PersonResolutionAdminDecisionRead(
        decision_type=decision.decision_type,
        confidence_tier=decision.confidence_tier,
        reviewer=decision.reviewer,
        selected_person=person_refs.get(decision.selected_person_id),
        summary=decision.decision_summary,
        external_verdict=evidence.get("external_verdict"),
        external_case_id=evidence.get("case_id"),
        source_reference=evidence.get("source_reference"),
    )


# Human-readable labels for each effective status (kept identical to the
# pre-refactor strings so the audit UI is unchanged).
_EFFECTIVE_STATUS_LABELS = {
    "approved_current": "admin approved current",
    "approved_override": "admin override",
    "kept_ambiguous": "admin kept ambiguous",
    "text_or_chain_issue": "admin flagged text/chain",
    "missing_rank1": "machine missing rank 1",
}


def _effective_resolution_read(
    *,
    top_row: MentionResolution | None,
    resolved_person: dict | None,
    admin_decision: PersonResolutionDecision | None,
    person_refs: dict[int, dict],
) -> PersonResolutionEffectiveRead:
    """Schema view of the shared `apply_admin_decision` overlay.

    The identity logic lives in `rijal.effective_resolution`; this only maps the
    result onto person refs + display labels so the graph, chain popovers, and
    audit queue can never disagree.
    """
    from eshia_research.rijal.effective_resolution import apply_admin_decision

    raw_status = top_row.status if top_row is not None else None
    raw_person_id = top_row.person_id if top_row is not None else None
    eff = apply_admin_decision(raw_status, raw_person_id, admin_decision)

    if eff.source == "admin":
        # approve_current keeps the machine person when no explicit target.
        person = person_refs.get(eff.person_id) if eff.person_id is not None else None
        if person is None and eff.status == "approved_current":
            person = resolved_person
        reason = admin_decision.decision_summary if admin_decision is not None else None
    else:
        person = resolved_person
        reason = top_row.evidence_summary if top_row is not None else None

    label = _EFFECTIVE_STATUS_LABELS.get(eff.status, f"machine {eff.status}")
    return PersonResolutionEffectiveRead(
        source=eff.source,
        status=eff.status,
        label=label,
        person=person,
        reason=reason,
    )


def _person_refs(db: Session, person_ids: set[int]) -> dict[int, dict]:
    if not person_ids:
        return {}
    persons = {
        p.id: p
        for p in db.query(
            Person.id, Person.canonical_name_ar, Person.kind, Person.primary_entry_id
        ).filter(Person.id.in_(person_ids)).all()
    }
    entry_ids = {p.primary_entry_id for p in persons.values() if p.primary_entry_id}
    narrator_by_entry = {
        e.id: e.narrator_id
        for e in db.query(RijalEntry.id, RijalEntry.narrator_id)
        .filter(RijalEntry.id.in_(entry_ids)).all()
    } if entry_ids else {}
    generations = {
        g.person_id: (g.gen_point, g.method)
        for g in db.query(
            PersonGeneration.person_id, PersonGeneration.gen_point, PersonGeneration.method
        ).filter(PersonGeneration.person_id.in_(person_ids)).all()
    }

    refs: dict[int, dict] = {}
    for pid, person in persons.items():
        gen, gen_method = generations.get(pid, (None, None))
        refs[pid] = {
            "id": person.id,
            "canonical_name_ar": person.canonical_name_ar,
            "kind": person.kind,
            "narrator_id": narrator_by_entry.get(person.primary_entry_id),
            "generation": gen,
            "generation_method": gen_method,
        }
    return refs


def _score_from_evidence(evidence_json: dict | None) -> int | None:
    if not evidence_json:
        return None
    score = evidence_json.get("score")
    return score if isinstance(score, int) else None


def _margin_from_evidence(evidence_json: dict | None) -> int | None:
    if not evidence_json:
        return None
    margin = evidence_json.get("margin")
    return margin if isinstance(margin, int) else None


def _audit_risk_flags(
    *,
    status: str,
    node_type: str,
    method: str | None,
    candidate_count: int,
    evidence_json: dict | None,
    has_rank1: bool,
) -> list[str]:
    flags: list[str] = []
    if not has_rank1:
        flags.append("missing_rank1")
    if status == "ambiguous":
        flags.append("ambiguous")
    elif status == "unresolved":
        flags.append("unresolved")
    elif status == "latent":
        flags.append("latent")
    if node_type == "collective_phrase" and status == "unresolved":
        flags.append("unexpanded_collective")
    if method in {"collective_context", "compiler_prior_kulayni", "collective_roster_after_context"}:
        flags.append("phase_d_context")
    if candidate_count >= 6:
        flags.append("many_candidates")
    if evidence_json:
        surface = evidence_json.get("surface") or {}
        derivation = surface.get("derivation")
        shared_count = surface.get("shared_count")
        if derivation in {"first_name", "kunya"}:
            flags.append("weak_surface")
        if isinstance(shared_count, int) and shared_count >= 40:
            flags.append("shared_surface")
        margin = _margin_from_evidence(evidence_json)
        if margin is not None and margin < 25:
            flags.append("low_margin")
    return flags


def _narrator_summary(narrator: Narrator | None) -> NarratorSummaryRead | None:
    if narrator is None:
        return None
    return NarratorSummaryRead(
        id=narrator.id,
        canonical_name_ar=narrator.canonical_name_ar,
        canonical_name_en=narrator.canonical_name_en,
        kunya=narrator.kunya,
        laqab=narrator.laqab,
        nisba=narrator.nisba,
        father_name=narrator.father_name,
        death_year_note=narrator.death_year_note,
        generation_layer=narrator.generation_layer,
        school_or_sect=narrator.school_or_sect,
        summary_status=narrator.summary_status,
    )


def _narrator_book_priority():
    return case(
        *(
            (Book.source_book_id == source_book_id, priority)
            for source_book_id, priority in _NARRATOR_APPEARANCE_BOOK_PRIORITY.items()
        ),
        else_=99,
    )


def _narrator_appearance_counts(db: Session, narrator_id: int) -> list[dict]:
    rows = (
        db.query(
            Book.id,
            Book.source_book_id,
            Book.title_original,
            func.count(func.distinct(Hadith.id)).label("total"),
        )
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            ChainNode.canonical_narrator_id == narrator_id,
            Hadith.review_status != _REJECTED_HADITH_STATUS,
        )
        .group_by(Book.id, Book.source_book_id, Book.title_original)
        .order_by(_narrator_book_priority(), Book.title_original)
        .all()
    )
    return [
        {
            "book_id": book_id,
            "source_book_id": source_book_id,
            "title_original": title_original,
            "total": total,
        }
        for book_id, source_book_id, title_original, total in rows
    ]


def _narrator_hadith_appearances(
    db: Session,
    narrator_id: int,
    *,
    source_book_id: str | None = None,
    skip: int = 0,
    limit: int = 120,
) -> tuple[int, list[dict]]:
    """Return one representative resolved chain node per hadith.

    A narrator can appear through more than one expanded route in the same
    hadith. The UI wants "hadiths where this narrator appears", so we group
    by hadith and keep the earliest resolved node as the representative.
    """

    filters = [
        ChainNode.canonical_narrator_id == narrator_id,
        Hadith.review_status != _REJECTED_HADITH_STATUS,
    ]
    if source_book_id is not None:
        filters.append(Book.source_book_id == source_book_id)

    representative_nodes = (
        db.query(func.min(ChainNode.id).label("node_id"))
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(*filters)
        .group_by(Hadith.id)
        .subquery()
    )
    total = db.query(func.count()).select_from(representative_nodes).scalar() or 0
    rows = (
        db.query(ChainNode, Chain, Hadith, Book)
        .join(representative_nodes, ChainNode.id == representative_nodes.c.node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .order_by(_narrator_book_priority(), Hadith.sequence_in_book)
        .offset(skip)
        .limit(limit)
        .all()
    )
    appearances = [
        {
            "hadith_id": hadith.id,
            "public_id": hadith.public_id,
            "book_id": book.id,
            "source_book_id": book.source_book_id,
            "book_title": book.title_original,
            "section_title": hadith.section_title,
            "sequence_in_book": hadith.sequence_in_book,
            "printed_number": hadith.printed_number,
            "volume_start": hadith.volume_start,
            "page_start": hadith.page_start,
            "page_end": hadith.page_end,
            "chain_id": chain.id,
            "chain_number": chain.chain_number,
            "node_id": node.id,
            "node_position": node.position,
            "raw_token": node.raw_token,
            "confidence": node.confidence,
            "resolution_method": node.resolution_method,
            "matn_excerpt": " ".join((hadith.matn_raw or "").split())[:240],
        }
        for node, chain, hadith, book in rows
    ]
    return total, appearances


def _transmission_position_predicate(target_node, related_node, direction: str):
    if direction == "teachers":
        return related_node.position == target_node.position + 1
    if direction == "students":
        return related_node.position == target_node.position - 1
    raise ValueError(f"Unsupported transmission direction: {direction}")


def _transmission_filters(
    target_node,
    related_node,
    narrator_id: int,
    *,
    source_book_id: str | None = None,
    related_narrator_id: int | None = None,
) -> list:
    filters = [
        target_node.canonical_narrator_id == narrator_id,
        related_node.canonical_narrator_id.isnot(None),
        Hadith.review_status != _REJECTED_HADITH_STATUS,
    ]
    if source_book_id is not None:
        filters.append(Book.source_book_id == source_book_id)
    if related_narrator_id is not None:
        filters.append(related_node.canonical_narrator_id == related_narrator_id)
    return filters


def _narrator_transmission_book_counts(
    db: Session,
    narrator_id: int,
    related_narrator_id: int,
    *,
    direction: str,
    source_book_id: str | None = None,
) -> list[dict]:
    target_node = aliased(ChainNode)
    related_node = aliased(ChainNode)
    total = func.count(func.distinct(Hadith.id))
    rows = (
        db.query(
            Book.id,
            Book.source_book_id,
            Book.title_original,
            total.label("total"),
        )
        .select_from(target_node)
        .join(
            related_node,
            and_(
                related_node.chain_id == target_node.chain_id,
                _transmission_position_predicate(target_node, related_node, direction),
            ),
        )
        .join(Chain, Chain.id == target_node.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            *_transmission_filters(
                target_node,
                related_node,
                narrator_id,
                source_book_id=source_book_id,
                related_narrator_id=related_narrator_id,
            )
        )
        .group_by(Book.id, Book.source_book_id, Book.title_original)
        .order_by(_narrator_book_priority(), Book.title_original)
        .all()
    )
    return [
        {
            "book_id": book_id,
            "source_book_id": row_source_book_id,
            "title_original": title_original,
            "total": row_total,
        }
        for book_id, row_source_book_id, title_original, row_total in rows
    ]


def _narrator_transmission_samples(
    db: Session,
    narrator_id: int,
    related_narrator_id: int,
    *,
    direction: str,
    source_book_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    target_node = aliased(ChainNode)
    related_node = aliased(ChainNode)
    rows = (
        db.query(target_node, related_node, Chain, Hadith, Book)
        .select_from(target_node)
        .join(
            related_node,
            and_(
                related_node.chain_id == target_node.chain_id,
                _transmission_position_predicate(target_node, related_node, direction),
            ),
        )
        .join(Chain, Chain.id == target_node.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            *_transmission_filters(
                target_node,
                related_node,
                narrator_id,
                source_book_id=source_book_id,
                related_narrator_id=related_narrator_id,
            )
        )
        .order_by(_narrator_book_priority(), Hadith.sequence_in_book, Chain.chain_number)
        .limit(limit * 8)
        .all()
    )
    samples = []
    seen_hadith_ids: set[int] = set()
    for node, related, chain, hadith, book in rows:
        if hadith.id in seen_hadith_ids:
            continue
        seen_hadith_ids.add(hadith.id)
        samples.append(
            {
                "hadith_id": hadith.id,
                "public_id": hadith.public_id,
                "book_id": book.id,
                "source_book_id": book.source_book_id,
                "book_title": book.title_original,
                "section_title": hadith.section_title,
                "sequence_in_book": hadith.sequence_in_book,
                "printed_number": hadith.printed_number,
                "volume_start": hadith.volume_start,
                "page_start": hadith.page_start,
                "page_end": hadith.page_end,
                "chain_id": chain.id,
                "chain_number": chain.chain_number,
                "node_id": node.id,
                "node_position": node.position,
                "related_node_id": related.id,
                "related_node_position": related.position,
                "raw_token": node.raw_token,
                "related_raw_token": related.raw_token,
                "confidence": node.confidence,
                "related_confidence": related.confidence,
                "matn_excerpt": " ".join((hadith.matn_raw or "").split())[:220],
            }
        )
        if len(samples) >= limit:
            break
    return samples


def _narrator_transmission_edges(
    db: Session,
    narrator_id: int,
    *,
    direction: str,
    source_book_id: str | None = None,
    limit: int = 50,
    sample_limit: int = 5,
) -> list[dict]:
    target_node = aliased(ChainNode)
    related_node = aliased(ChainNode)
    total = func.count(func.distinct(Hadith.id))
    rows = (
        db.query(
            related_node.canonical_narrator_id.label("related_narrator_id"),
            total.label("total"),
        )
        .select_from(target_node)
        .join(
            related_node,
            and_(
                related_node.chain_id == target_node.chain_id,
                _transmission_position_predicate(target_node, related_node, direction),
            ),
        )
        .join(Chain, Chain.id == target_node.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            *_transmission_filters(
                target_node,
                related_node,
                narrator_id,
                source_book_id=source_book_id,
            )
        )
        .group_by(related_node.canonical_narrator_id)
        .order_by(total.desc())
        .limit(limit)
        .all()
    )
    related_ids = [related_id for related_id, _ in rows if related_id is not None]
    narrators_by_id = {
        narrator.id: narrator
        for narrator in db.query(Narrator).filter(Narrator.id.in_(related_ids)).all()
    }
    edges = []
    for related_id, row_total in rows:
        related_narrator = narrators_by_id.get(related_id)
        if related_narrator is None:
            continue
        edges.append(
            {
                "related_narrator": _narrator_summary(related_narrator),
                "total": row_total,
                "book_counts": _narrator_transmission_book_counts(
                    db,
                    narrator_id,
                    related_id,
                    direction=direction,
                    source_book_id=source_book_id,
                ),
                "samples": _narrator_transmission_samples(
                    db,
                    narrator_id,
                    related_id,
                    direction=direction,
                    source_book_id=source_book_id,
                    limit=sample_limit,
                ),
            }
        )
    return edges


def _book_by_source_id(db: Session, source_book_id: str) -> Book:
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


def _reviewed_status(review: HadithSplitReview | None) -> str:
    return review_status_key(review)


def _split_review_rows(
    db: Session,
    source_book_id: str,
    status: str,
) -> list[tuple[Hadith, HadithSplitReview | None]]:
    book = _book_by_source_id(db, source_book_id)
    query = db.query(Hadith, HadithSplitReview).outerjoin(
        HadithSplitReview,
        HadithSplitReview.hadith_id == Hadith.id,
    )
    query = query.filter(Hadith.book_id == book.id)
    if status == "unreviewed":
        query = query.filter(
            (HadithSplitReview.id.is_(None))
            | (HadithSplitReview.review_status == "unreviewed")
        )
    elif status != "all":
        if status not in _SPLIT_REVIEW_STATUSES:
            raise HTTPException(status_code=400, detail="Unsupported review status")
        query = query.filter(HadithSplitReview.review_status == status)
    return query.order_by(Hadith.sequence_in_book).all()


def _visible_hadith_query(db: Session, book_id: int):
    return db.query(Hadith).filter(
        Hadith.book_id == book_id,
        Hadith.review_status != _REJECTED_HADITH_STATUS,
    )


def _page_text_blocks_from_html(html: str | None) -> list[dict[str, str | None]] | None:
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")
    content_cell = soup.find("td", class_="book-page-show")
    if content_cell is None:
        return None

    blocks: list[dict[str, str | None]] = []
    for menu in content_cell.find_all("div", class_="sticky-menue"):
        menu.extract()

    candidates = [
        child
        for child in content_cell.children
        if isinstance(child, Tag) and child.name in {"p", "hr", "span"}
    ]
    if not candidates:
        candidates = content_cell.find_all(["p", "hr", "span"], recursive=True)

    for child in candidates:
        if child.name == "hr":
            blocks.append({"kind": "divider", "text": None})
            continue

        classes = set(child.get("class") or [])
        if child.name == "span" and "FootNote" not in classes:
            continue

        separator = "\n" if "FootNote" in classes else " "
        text = child.get_text(separator, strip=True)
        if not text:
            continue

        if "FootNote" in classes:
            blocks.append({"kind": "footnote", "text": text})
        elif any(class_name.startswith("Titr") for class_name in classes):
            blocks.append({"kind": "heading", "text": text})
        else:
            blocks.append({"kind": "paragraph", "text": text})

    return blocks or None


def _attach_text_blocks(page: Page) -> Page:
    page.text_blocks = _page_text_blocks_from_html(page.html_raw)
    return page


@router.get("/books", response_model=list[BookSummary])
def list_books(
    skip: int = 0,
    limit: int = 50,
    has_content: bool | None = None,
    db: Session = Depends(get_db),
) -> list[Book]:
    content_exists = _readable_content_exists()
    page_count = _readable_page_count()
    query = db.query(Book, content_exists.label("has_content"))
    if has_content is not None:
        query = query.filter(content_exists if has_content else ~content_exists)
    query = _apply_arabic_catalog_filters(query)
    rows = query.order_by(page_count.desc(), Book.id).offset(skip).limit(limit).all()

    books = []
    for book, has_content_value in rows:
        book.has_content = has_content_value
        books.append(book)
    return books


@router.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    book.has_content = (
        db.query(Page.id)
        .filter(Page.book_id == book.id, Page.page_number > 1, Page.text_raw.isnot(None))
        .first()
        is not None
    )
    return book


@router.get("/books/{book_id}/page-index", response_model=list[PageIndexEntry])
def list_book_page_index(
    book_id: int,
    volume: int | None = None,
    db: Session = Depends(get_db),
) -> list[Page]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    query = db.query(Page).filter(Page.book_id == book_id)
    if volume is not None:
        query = query.filter(Page.volume_number == volume)
    return query.order_by(Page.volume_number, Page.page_number).all()


@router.get("/books/{book_id}/pages", response_model=list[PageRead])
def list_book_pages(
    book_id: int,
    volume: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Page]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    query = db.query(Page).filter(Page.book_id == book_id)
    if volume is not None:
        query = query.filter(Page.volume_number == volume)
    return query.order_by(Page.volume_number, Page.page_number).offset(skip).limit(limit).all()


@router.get("/books/{book_id}/hadiths", response_model=list[HadithRead])
def list_book_hadiths(
    book_id: int,
    volume: int | None = None,
    page: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Hadith]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    query = _visible_hadith_query(db, book_id)
    if volume is not None and page is not None:
        query = query.filter(
            and_(
                Hadith.volume_start == volume,
                Hadith.page_start <= page,
                Hadith.page_end >= page,
            )
        )
    elif volume is not None:
        query = query.filter(Hadith.volume_start == volume)
    elif page is not None:
        query = query.filter(Hadith.page_start == page)
    hadiths = query.order_by(Hadith.sequence_in_book).offset(skip).limit(limit).all()
    hadiths = _attach_public_translations(db, _apply_approved_splits(db, hadiths))
    return _attach_topics(db, hadiths)


@router.get("/person-resolution-audit/summary", response_model=PersonResolutionAuditSummary)
def get_person_resolution_audit_summary(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    db: Session = Depends(get_db),
) -> PersonResolutionAuditSummary:
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    top_resolution = aliased(MentionResolution)
    status_expr = case(
        (top_resolution.id.is_(None), "missing_rank1"),
        else_=top_resolution.status,
    )
    base_filters = (Hadith.book_id == book.id, Hadith.review_status != _REJECTED_HADITH_STATUS)
    total_nodes = (
        db.query(func.count(ChainNode.id))
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(*base_filters)
        .scalar()
        or 0
    )

    status_rows = (
        db.query(status_expr.label("status"), func.count(ChainNode.id))
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .outerjoin(
            top_resolution,
            and_(
                top_resolution.chain_node_id == ChainNode.id,
                top_resolution.resolver_version == PERSON_RESOLVER_VERSION,
                top_resolution.rank == 1,
            ),
        )
        .filter(*base_filters)
        .group_by(status_expr)
        .order_by(status_expr)
        .all()
    )
    status_counts = [
        PersonResolutionStatusCount(status=status, total=count)
        for status, count in status_rows
    ]
    status_total_by_name = {row.status: row.total for row in status_counts}
    without_rank1 = status_total_by_name.get("missing_rank1", 0)
    with_rank1 = total_nodes - without_rank1
    open_nodes = without_rank1 + sum(
        status_total_by_name.get(status, 0) for status in _OPEN_PERSON_RESOLUTION_STATUSES
    )

    node_type_rows = (
        db.query(ChainNode.node_type, status_expr.label("status"), func.count(ChainNode.id))
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .outerjoin(
            top_resolution,
            and_(
                top_resolution.chain_node_id == ChainNode.id,
                top_resolution.resolver_version == PERSON_RESOLVER_VERSION,
                top_resolution.rank == 1,
            ),
        )
        .filter(*base_filters)
        .group_by(ChainNode.node_type, status_expr)
        .order_by(ChainNode.node_type, status_expr)
        .all()
    )
    method_rows = (
        db.query(top_resolution.method, top_resolution.status, func.count(ChainNode.id))
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .join(
            top_resolution,
            and_(
                top_resolution.chain_node_id == ChainNode.id,
                top_resolution.resolver_version == PERSON_RESOLVER_VERSION,
                top_resolution.rank == 1,
            ),
        )
        .filter(*base_filters)
        .group_by(top_resolution.method, top_resolution.status)
        .order_by(func.count(ChainNode.id).desc())
        .limit(40)
        .all()
    )

    return PersonResolutionAuditSummary(
        source_book_id=source_book_id,
        total_nodes=total_nodes,
        with_rank1_resolution=with_rank1,
        without_rank1_resolution=without_rank1,
        open_nodes=open_nodes,
        status_counts=status_counts,
        node_type_counts=[
            PersonResolutionNodeTypeCount(node_type=node_type, status=status, total=count)
            for node_type, status, count in node_type_rows
        ],
        method_counts=[
            PersonResolutionMethodCount(method=method, status=status, total=count)
            for method, status, count in method_rows
        ],
    )


@router.get("/person-resolution-audit/queue", response_model=PersonResolutionAuditPage)
def list_person_resolution_audit_queue(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    status: str = "open",
    node_type: str | None = None,
    risk: str | None = None,
    machine_decision: str | None = None,
    q: str | None = None,
    admin_reviewed: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> PersonResolutionAuditPage:
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

    status = status.strip() if status else "open"
    if status not in _PERSON_AUDIT_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported person resolution status")
    risk = risk.strip() if risk else None
    if risk and risk not in _PERSON_AUDIT_RISKS:
        raise HTTPException(status_code=400, detail="Unsupported person resolution risk")
    machine_decision = machine_decision.strip() if machine_decision else None
    if machine_decision and machine_decision not in _PERSON_AUDIT_MACHINE_DECISIONS:
        raise HTTPException(status_code=400, detail="Unsupported machine decision filter")
    limit = max(1, min(limit, 200))
    skip = max(skip, 0)

    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    top_resolution = aliased(MentionResolution)
    candidate_counts = None
    if risk in {"any", "many_candidates"}:
        candidate_counts = (
            db.query(
                MentionResolution.chain_node_id.label("node_id"),
                func.count(MentionResolution.id).label("candidate_count"),
            )
            .filter(MentionResolution.resolver_version == PERSON_RESOLVER_VERSION)
            .group_by(MentionResolution.chain_node_id)
            .subquery()
        )

    query = (
        db.query(ChainNode, Chain, Hadith, top_resolution)
        .select_from(ChainNode)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .outerjoin(
            top_resolution,
            and_(
                top_resolution.chain_node_id == ChainNode.id,
                top_resolution.resolver_version == PERSON_RESOLVER_VERSION,
                top_resolution.rank == 1,
            ),
        )
        .filter(Hadith.book_id == book.id, Hadith.review_status != _REJECTED_HADITH_STATUS)
    )
    if candidate_counts is not None:
        query = query.outerjoin(candidate_counts, candidate_counts.c.node_id == ChainNode.id)

    if status == "open":
        query = query.filter(
            or_(
                top_resolution.id.is_(None),
                top_resolution.status.in_(tuple(_OPEN_PERSON_RESOLUTION_STATUSES)),
            )
        )
    elif status == "missing_rank1":
        query = query.filter(top_resolution.id.is_(None))
    elif status != "all":
        query = query.filter(top_resolution.status == status)
    if node_type:
        query = query.filter(ChainNode.node_type == node_type)
    if q:
        token_query = normalise_arabic_persian(q)
        query = query.filter(
            or_(ChainNode.raw_token.contains(q), ChainNode.token_normalised.contains(token_query))
        )
    if admin_reviewed:
        query = query.filter(
            exists().where(
                and_(
                    PersonResolutionDecision.chain_node_id == ChainNode.id,
                    PersonResolutionDecision.reviewer == _ADMIN_PERSON_REVIEWER,
                    PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
                )
            )
        )
    if machine_decision:
        query = query.filter(
            exists().where(
                and_(
                    PersonResolutionDecision.chain_node_id == ChainNode.id,
                    PersonResolutionDecision.reviewer == _MACHINE_PERSON_REVIEWER,
                    PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
                    PersonResolutionDecision.decision_type == machine_decision,
                )
            )
        )
    if risk:
        surface_derivation = func.json_extract(top_resolution.evidence_json, "$.surface.derivation")
        shared_count = cast(
            func.coalesce(func.json_extract(top_resolution.evidence_json, "$.surface.shared_count"), 0),
            Integer,
        )
        margin = cast(
            func.coalesce(func.json_extract(top_resolution.evidence_json, "$.margin"), 999999),
            Integer,
        )
        weak_surface = surface_derivation.in_(("first_name", "kunya"))
        shared_surface = shared_count >= 40
        low_margin = margin < 25
        phase_d_context = top_resolution.method.in_(
            (
                "collective_context",
                "compiler_prior_kulayni",
                "collective_roster_after_context",
            )
        )
        many_candidates = (
            func.coalesce(candidate_counts.c.candidate_count, 0) >= 6
            if candidate_counts is not None
            else False
        )
        if risk == "phase_d_context":
            query = query.filter(phase_d_context)
        elif risk == "weak_surface":
            query = query.filter(weak_surface)
        elif risk == "shared_surface":
            query = query.filter(shared_surface)
        elif risk == "low_margin":
            query = query.filter(low_margin)
        elif risk == "many_candidates":
            query = query.filter(many_candidates)
        elif risk == "any":
            query = query.filter(
                or_(
                    phase_d_context,
                    weak_surface,
                    shared_surface,
                    low_margin,
                    many_candidates,
                )
            )

    total = query.with_entities(func.count(ChainNode.id)).scalar() or 0
    rows = (
        query.order_by(Hadith.sequence_in_book, Chain.chain_number, ChainNode.position)
        .offset(skip)
        .limit(limit)
        .all()
    )
    node_ids = [node.id for node, _chain, _hadith, _top in rows]
    resolution_rows: dict[int, list[MentionResolution]] = {}
    if node_ids:
        for resolution in (
            db.query(MentionResolution)
            .filter(
                MentionResolution.chain_node_id.in_(node_ids),
                MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            )
            .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
            .all()
        ):
            resolution_rows.setdefault(resolution.chain_node_id, []).append(resolution)

    person_ids = {
        resolution.person_id
        for node_rows in resolution_rows.values()
        for resolution in node_rows
        if resolution.person_id is not None
    }
    admin_decisions_by_node: dict[int, PersonResolutionDecision] = {}
    if node_ids:
        for decision in (
            db.query(PersonResolutionDecision)
            .filter(
                PersonResolutionDecision.chain_node_id.in_(node_ids),
                PersonResolutionDecision.reviewer == _ADMIN_PERSON_REVIEWER,
                PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
            )
            .all()
        ):
            admin_decisions_by_node[decision.chain_node_id] = decision
            if decision.selected_person_id is not None:
                person_ids.add(decision.selected_person_id)
    person_refs = _person_refs(db, person_ids)
    items: list[PersonResolutionAuditItem] = []
    for node, chain, hadith, top in rows:
        node_resolution_rows = resolution_rows.get(node.id, [])
        node_resolution_rows.sort(key=lambda row: row.rank)
        top_row = top or (node_resolution_rows[0] if node_resolution_rows else None)
        effective_status = top_row.status if top_row else "missing_rank1"
        evidence_json = top_row.evidence_json if top_row else None
        candidates = [
            PersonResolutionAuditCandidate(
                rank=resolution.rank,
                status=resolution.status,
                method=resolution.method,
                person=person_refs.get(resolution.person_id),
                evidence_summary=resolution.evidence_summary,
                score=_score_from_evidence(resolution.evidence_json),
                winner_score=(
                    resolution.evidence_json.get("winner_score")
                    if isinstance(resolution.evidence_json, dict)
                    and isinstance(resolution.evidence_json.get("winner_score"), int)
                    else None
                ),
                margin_to_winner=(
                    resolution.evidence_json.get("margin_to_winner")
                    if isinstance(resolution.evidence_json, dict)
                    and isinstance(resolution.evidence_json.get("margin_to_winner"), int)
                    else None
                ),
            )
            for resolution in node_resolution_rows
        ]
        resolved_person = (
            person_refs.get(top_row.person_id)
            if top_row is not None and top_row.status in {"resolved", "latent", "via_collective"}
            else None
        )
        admin_decision = admin_decisions_by_node.get(node.id)
        items.append(
            PersonResolutionAuditItem(
                hadith_id=hadith.id,
                public_id=hadith.public_id,
                sequence_in_book=hadith.sequence_in_book,
                section_title=hadith.section_title,
                volume_start=hadith.volume_start,
                page_start=hadith.page_start,
                page_end=hadith.page_end,
                chain_id=chain.id,
                chain_number=chain.chain_number,
                node_id=node.id,
                position=node.position,
                raw_token=node.raw_token,
                token_normalised=node.token_normalised,
                node_type=node.node_type,
                relation_kind=node.relation_kind,
                status=effective_status,
                method=top_row.method if top_row else None,
                resolved_person=resolved_person,
                admin_decision=_admin_decision_read(admin_decision, person_refs),
                effective_resolution=_effective_resolution_read(
                    top_row=top_row,
                    resolved_person=resolved_person,
                    admin_decision=admin_decision,
                    person_refs=person_refs,
                ),
                primary_dalil=top_row.evidence_summary if top_row else None,
                candidates=candidates,
                candidate_count=len(candidates),
                top_score=_score_from_evidence(evidence_json),
                top_margin=_margin_from_evidence(evidence_json),
                risk_flags=_audit_risk_flags(
                    status=effective_status,
                    node_type=node.node_type,
                    method=top_row.method if top_row else None,
                    candidate_count=len(candidates),
                    evidence_json=evidence_json,
                    has_rank1=top_row is not None,
                ),
                isnad_excerpt=" ".join((hadith.isnad_raw or "").split())[:260] or None,
                matn_excerpt=" ".join((hadith.matn_raw or "").split())[:260],
            )
        )

    return PersonResolutionAuditPage(
        source_book_id=source_book_id,
        status=status,
        node_type=node_type,
        risk=risk,
        q=q,
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get("/person-resolution-decisions/summary", response_model=PersonResolutionDecisionSummary)
def get_person_resolution_decision_summary(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    reviewer: str = "codex-machine-v1",
    db: Session = Depends(get_db),
) -> PersonResolutionDecisionSummary:
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    base = (
        db.query(PersonResolutionDecision)
        .join(ChainNode, ChainNode.id == PersonResolutionDecision.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(
            Hadith.book_id == book.id,
            Hadith.review_status != _REJECTED_HADITH_STATUS,
            PersonResolutionDecision.reviewer == reviewer,
            PersonResolutionDecision.resolver_version == PERSON_RESOLVER_VERSION,
        )
    )
    total = base.with_entities(func.count(PersonResolutionDecision.id)).scalar() or 0
    decision_rows = (
        base.with_entities(PersonResolutionDecision.decision_type, func.count(PersonResolutionDecision.id))
        .group_by(PersonResolutionDecision.decision_type)
        .order_by(func.count(PersonResolutionDecision.id).desc())
        .all()
    )
    confidence_rows = (
        base.with_entities(PersonResolutionDecision.confidence_tier, func.count(PersonResolutionDecision.id))
        .group_by(PersonResolutionDecision.confidence_tier)
        .order_by(func.count(PersonResolutionDecision.id).desc())
        .all()
    )
    return PersonResolutionDecisionSummary(
        source_book_id=source_book_id,
        reviewer=reviewer,
        total_decisions=total,
        decision_counts=[
            PersonResolutionDecisionCount(key=decision_type, total=count)
            for decision_type, count in decision_rows
        ],
        confidence_counts=[
            PersonResolutionDecisionCount(key=confidence_tier, total=count)
            for confidence_tier, count in confidence_rows
        ],
    )


@router.get("/hadith-split-reviews/stats", response_model=HadithSplitReviewStats)
def get_hadith_split_review_stats(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    db: Session = Depends(get_db),
) -> HadithSplitReviewStats:
    report = build_hadith_split_audit_report(
        db,
        source_book_id=source_book_id,
        include_chain_index=False,
    )
    return HadithSplitReviewStats(
        source_book_id=source_book_id,
        total_hadiths=report.total_hadiths,
        reviewed=report.reviewed,
        approved=report.approved,
        needs_review=report.needs_review,
        rejected=report.rejected,
        unreviewed=report.unreviewed,
        suspicious_unreviewed=report.suspicious_unreviewed,
    )


@router.get("/hadith-split-reviews/queue", response_model=list[HadithSplitReviewItem])
def list_hadith_split_review_queue(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    status: str = "unreviewed",
    flag: str | None = None,
    suspicious_only: bool = True,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
) -> list[HadithSplitReviewItem]:
    limit = max(1, min(limit, 100))
    skip = max(skip, 0)

    items: list[HadithSplitReviewItem] = []
    matched = 0
    for hadith, review in _split_review_rows(db, source_book_id, status):
        flags = _split_suspicion_flags(hadith, review)
        if suspicious_only and not flags:
            continue
        if flag and flag not in flags:
            continue
        if matched < skip:
            matched += 1
            continue
        active_isnad, active_matn = _active_split(hadith, review)
        items.append(
            HadithSplitReviewItem(
                hadith=hadith,
                review=review,
                active_isnad_raw=active_isnad,
                active_matn_raw=active_matn,
                suspicion_flags=flags,
            )
        )
        if len(items) >= limit:
            break
    return items


@router.get("/hadith-split-reviews/audit", response_model=HadithSplitAudit)
def get_hadith_split_audit(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    db: Session = Depends(get_db),
) -> HadithSplitAudit:
    report = build_hadith_split_audit_report(
        db,
        source_book_id=source_book_id,
        include_chain_index=False,
    )
    flags = [
        HadithSplitFlagCount(
            flag=bucket.flag,
            total=bucket.total,
            unreviewed=bucket.unreviewed,
            approved=bucket.approved,
            needs_review=bucket.needs_review,
            rejected=bucket.rejected,
            examples=bucket.examples[:5],
        )
        for bucket in report.flags
    ]
    return HadithSplitAudit(
        source_book_id=source_book_id,
        total_hadiths=report.total_hadiths,
        flagged_hadiths=report.flagged_hadiths,
        flags=flags,
    )


@router.get("/hadith-split-reviews/{public_id}", response_model=HadithSplitReviewItem)
def get_hadith_split_review(public_id: str, db: Session = Depends(get_db)) -> HadithSplitReviewItem:
    hadith = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if hadith is None:
        raise HTTPException(status_code=404, detail="Hadith not found")
    review = (
        db.query(HadithSplitReview)
        .filter(HadithSplitReview.hadith_id == hadith.id)
        .one_or_none()
    )
    return _review_item(hadith, review)


@router.put("/hadith-split-reviews/{public_id}", response_model=HadithSplitReviewItem)
def save_hadith_split_review(
    public_id: str,
    payload: HadithSplitReviewSave,
    _: None = Depends(require_admin_api_token),
    db: Session = Depends(get_db),
) -> HadithSplitReviewItem:
    if payload.review_status not in _SPLIT_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported review status")

    hadith = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if hadith is None:
        raise HTTPException(status_code=404, detail="Hadith not found")

    review = (
        db.query(HadithSplitReview)
        .filter(HadithSplitReview.hadith_id == hadith.id)
        .one_or_none()
    )
    if review is None:
        review = HadithSplitReview(hadith_id=hadith.id)
        db.add(review)

    review.approved_isnad_raw = payload.approved_isnad_raw
    review.approved_matn_raw = payload.approved_matn_raw
    review.review_status = payload.review_status
    review.reviewer = payload.reviewer
    review.notes = payload.notes
    if payload.review_status == "approved":
        hadith.isnad_raw = payload.approved_isnad_raw
        hadith.isnad_normalised = (
            normalise_arabic_persian(payload.approved_isnad_raw)
            if payload.approved_isnad_raw
            else None
        )
        hadith.matn_raw = payload.approved_matn_raw
        hadith.matn_normalised = normalise_arabic_persian(payload.approved_matn_raw)
    db.commit()
    db.refresh(review)
    return _review_item(hadith, review)


def _chapter_runs(db: Session, book_id: int) -> list[ChapterSummary]:
    """Group the book's hadiths into contiguous section-title runs.

    A hadith with section_title=None continues the current chapter (section
    titles are only recorded on the page where the heading appears).
    """
    rows = (
        db.query(
            Hadith.sequence_in_book,
            Hadith.section_title,
            Hadith.volume_start,
            Hadith.page_start,
        )
        .filter(Hadith.book_id == book_id, Hadith.review_status != _REJECTED_HADITH_STATUS)
        .order_by(Hadith.sequence_in_book)
        .all()
    )
    runs: list[ChapterSummary] = []
    for sequence, title, volume, page_start in rows:
        current = runs[-1] if runs else None
        starts_new = current is None or (title is not None and title != current.title)
        if starts_new:
            runs.append(
                ChapterSummary(
                    index=len(runs) + 1,
                    title=title,
                    volume=volume,
                    page_start=page_start,
                    hadith_count=1,
                    start_sequence=sequence,
                    end_sequence=sequence,
                )
            )
        else:
            current.end_sequence = sequence
            current.hadith_count += 1
    return runs


@router.get("/books/{book_id}/chapters", response_model=list[ChapterSummary])
def list_book_chapters(book_id: int, db: Session = Depends(get_db)) -> list[ChapterSummary]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return _chapter_runs(db, book_id)


@router.get("/books/{book_id}/chapters/{chapter_index}/hadiths", response_model=list[HadithRead])
def list_chapter_hadiths(
    book_id: int,
    chapter_index: int,
    db: Session = Depends(get_db),
) -> list[Hadith]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    runs = _chapter_runs(db, book_id)
    if chapter_index < 1 or chapter_index > len(runs):
        raise HTTPException(status_code=404, detail="Chapter not found")
    run = runs[chapter_index - 1]
    hadiths = (
        _visible_hadith_query(db, book_id)
        .filter(
            Hadith.sequence_in_book >= run.start_sequence,
            Hadith.sequence_in_book <= run.end_sequence,
        )
        .order_by(Hadith.sequence_in_book)
        .all()
    )
    hadiths = _attach_public_translations(db, _apply_approved_splits(db, hadiths))
    return _attach_topics(db, hadiths)


def _kitab_order_key(volume: int, kitab_id: str) -> tuple[int, int, str]:
    """Sort kitabs by volume, then numerically by their Thaqalayn category id."""
    try:
        return (volume, int(kitab_id), kitab_id)
    except (TypeError, ValueError):
        return (volume, 1 << 30, kitab_id)


@router.get("/books/{book_id}/kitabs", response_model=list[KitabSummary])
def list_book_kitabs(book_id: int, db: Session = Depends(get_db)) -> list[KitabSummary]:
    """Thaqalayn kitab (book-section) index for a structured book."""
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    rows = (
        db.query(
            ThaqalaynStructureMap.volume,
            ThaqalaynStructureMap.kitab_id,
            ThaqalaynStructureMap.kitab_name_en,
            ThaqalaynStructureMap.chapter_id,
        )
        .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
        .filter(
            Hadith.book_id == book_id,
            ThaqalaynStructureMap.source.in_(("thaqalayn-website", "thaqalayn-api")),
        )
        .all()
    )
    agg: dict[tuple[int, str], dict] = {}
    for volume, kitab_id, kitab_name_en, chapter_id in rows:
        key = (volume, kitab_id)
        entry = agg.setdefault(
            key,
            {
                "volume": volume,
                "kitab_id": kitab_id,
                "name_en": kitab_name_en,
                "chapters": set(),
                "hadith_count": 0,
            },
        )
        entry["chapters"].add(chapter_id)
        entry["hadith_count"] += 1
    result = [
        KitabSummary(
            kitab_id=e["kitab_id"],
            name_en=e["name_en"],
            volume=e["volume"],
            chapter_count=len(e["chapters"]),
            hadith_count=e["hadith_count"],
            first_chapter_id=min(e["chapters"]),
        )
        for e in agg.values()
    ]
    result.sort(key=lambda k: _kitab_order_key(k.volume, k.kitab_id))
    return result


@router.get(
    "/books/{book_id}/kitabs/{kitab_id}/chapters",
    response_model=list[ThaqalaynChapterSummary],
)
def list_kitab_chapters(
    book_id: int, kitab_id: str, db: Session = Depends(get_db)
) -> list[ThaqalaynChapterSummary]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    rows = (
        db.query(
            ThaqalaynStructureMap.chapter_id,
            ThaqalaynStructureMap.chapter_name_en,
            ThaqalaynStructureMap.number_in_chapter,
        )
        .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
        .filter(
            Hadith.book_id == book_id,
            ThaqalaynStructureMap.source.in_(("thaqalayn-website", "thaqalayn-api")),
            ThaqalaynStructureMap.kitab_id == kitab_id,
        )
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Kitab not found")
    agg: dict[int, dict] = {}
    for chapter_id, chapter_name_en, number_in_chapter in rows:
        entry = agg.setdefault(
            chapter_id,
            {"chapter_id": chapter_id, "name_en": chapter_name_en, "count": 0, "nums": []},
        )
        entry["count"] += 1
        if number_in_chapter is not None:
            entry["nums"].append(number_in_chapter)
    result = [
        ThaqalaynChapterSummary(
            chapter_id=e["chapter_id"],
            name_en=e["name_en"],
            hadith_count=e["count"],
            number_min=min(e["nums"]) if e["nums"] else None,
            number_max=max(e["nums"]) if e["nums"] else None,
        )
        for e in agg.values()
    ]
    result.sort(key=lambda c: c.chapter_id)
    return result


@router.get(
    "/books/{book_id}/kitabs/{kitab_id}/chapters/{chapter_id}/hadiths",
    response_model=list[HadithRead],
)
def list_kitab_chapter_hadiths(
    book_id: int,
    kitab_id: str,
    chapter_id: int,
    db: Session = Depends(get_db),
) -> list[Hadith]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    maps = (
        db.query(ThaqalaynStructureMap.hadith_id, ThaqalaynStructureMap.number_in_chapter)
        .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
        .filter(
            Hadith.book_id == book_id,
            ThaqalaynStructureMap.source.in_(("thaqalayn-website", "thaqalayn-api")),
            ThaqalaynStructureMap.kitab_id == kitab_id,
            ThaqalaynStructureMap.chapter_id == chapter_id,
        )
        .all()
    )
    if not maps:
        raise HTTPException(status_code=404, detail="Chapter not found")
    order = {
        hid: (num if num is not None else 1 << 30, i)
        for i, (hid, num) in enumerate(maps)
    }
    hadiths = (
        _visible_hadith_query(db, book_id)
        .filter(Hadith.id.in_(list(order)))
        .all()
    )
    hadiths.sort(key=lambda h: order.get(h.id, (1 << 30, 0)))
    hadiths = _attach_public_translations(db, _apply_approved_splits(db, hadiths))
    hadiths = _attach_structure_and_gradings(db, hadiths)
    return _attach_topics(db, hadiths)


@router.get("/hadiths/{public_id}", response_model=HadithRead)
def get_hadith(public_id: str, db: Session = Depends(get_db)) -> Hadith:
    hadith = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if hadith is None:
        raise HTTPException(status_code=404, detail="Hadith not found")
    if hadith.review_status == _REJECTED_HADITH_STATUS:
        raise HTTPException(status_code=404, detail="Hadith not found")
    review = (
        db.query(HadithSplitReview)
        .filter(
            HadithSplitReview.hadith_id == hadith.id,
            HadithSplitReview.review_status == "approved",
        )
        .one_or_none()
    )
    hadith = _apply_approved_split(hadith, review)
    hadith = _attach_public_translations(db, [hadith])[0]
    hadith = _attach_structure_and_gradings(db, [hadith])[0]
    return _attach_topics(db, [hadith])[0]


@router.get("/hadiths/{public_id}/chains", response_model=HadithChainsRead)
def get_hadith_chains(public_id: str, db: Session = Depends(get_db)) -> HadithChainsRead:
    hadith = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if hadith is None or hadith.review_status == _REJECTED_HADITH_STATUS:
        raise HTTPException(status_code=404, detail="Hadith not found")

    chains = (
        db.query(Chain)
        .options(
            selectinload(Chain.nodes).selectinload(ChainNode.narrator),
            selectinload(Chain.nodes)
            .selectinload(ChainNode.candidates)
            .selectinload(ChainNodeCandidate.narrator),
        )
        .filter(Chain.hadith_id == hadith.id)
        .order_by(Chain.chain_number)
        .all()
    )
    all_node_ids = [node.id for chain in chains for node in chain.nodes]
    person_resolutions = _person_resolution_map(db, all_node_ids)

    chain_items = []
    for chain in chains:
        nodes = []
        for node in sorted(chain.nodes, key=lambda item: item.position):
            candidates = [
                {
                    "rank": candidate.rank,
                    "score": candidate.score,
                    "match_type": candidate.match_type,
                    "evidence_summary": candidate.evidence_summary,
                    "narrator": _narrator_summary(candidate.narrator),
                }
                for candidate in sorted(node.candidates, key=lambda item: item.rank)[:5]
                if candidate.narrator is not None
            ]
            nodes.append(
                {
                    "id": node.id,
                    "position": node.position,
                    "raw_token": node.raw_token,
                    "token_normalised": node.token_normalised,
                    "transmission_phrase": node.transmission_phrase,
                    "node_type": node.node_type,
                    "relation_kind": node.relation_kind,
                    "narrator": _narrator_summary(node.narrator),
                    "confidence": node.confidence,
                    "resolution_method": node.resolution_method,
                    "resolution_reason": node.resolution_reason,
                    "review_status": node.review_status,
                    "candidates": candidates,
                    "person_resolution": person_resolutions.get(node.id),
                }
            )
        chain_items.append(
            {
                "id": chain.id,
                "chain_number": chain.chain_number,
                "raw_isnad": chain.raw_isnad,
                "parser_version": chain.parser_version,
                "node_count": chain.node_count,
                "flags": chain.flags,
                "review_status": chain.review_status,
                "nodes": nodes,
            }
        )
    return HadithChainsRead(hadith_id=hadith.id, public_id=hadith.public_id, chains=chain_items)


@router.get("/narrators", response_model=NarratorDirectoryPage)
def list_narrators(
    query: str | None = None,
    limit: int = 40,
    offset: int = 0,
    sort: str = "charted",
    db: Session = Depends(get_db),
) -> NarratorDirectoryPage:
    """The searchable directory of every Mu'jam narrator — the "everyone exists"
    index. Findability does not depend on edges: a narrator with no charted
    transmissions still returns (charted_hadith_count=0) and opens a real bio.

    `query` matches the canonical name OR any alias (Arabic-normalised).
    `sort=charted` surfaces the most-charted narrators first; `sort=name` is
    alphabetical.
    """
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    columns = (
        Narrator.id,
        Narrator.canonical_name_ar,
        Narrator.kunya,
        Narrator.laqab,
        Narrator.nisba,
        Narrator.generation_layer,
    )
    stmt = select(*columns)
    q_norm = normalise_arabic_persian(query).strip() if query else ""
    if q_norm:
        like = f"%{q_norm}%"
        alias_ids = select(NarratorAlias.narrator_id).where(
            NarratorAlias.alias_normalised.like(like)
        )
        stmt = stmt.where(
            or_(Narrator.canonical_name_norm.like(like), Narrator.id.in_(alias_ids))
        )
    rows = db.execute(stmt).all()

    charted = _narrator_charted_counts(db, list(POLISHED_TRANSMISSION_BOOK_IDS))
    if sort == "name":
        rows.sort(key=lambda r: r.canonical_name_ar or "")
    else:
        rows.sort(key=lambda r: (-charted.get(r.id, 0), r.canonical_name_ar or ""))

    total = len(rows)
    page = rows[offset : offset + limit]
    entries = [
        NarratorDirectoryEntry(
            narrator_id=r.id,
            canonical_name_ar=r.canonical_name_ar,
            kunya=r.kunya,
            laqab=r.laqab,
            nisba=r.nisba,
            generation=r.generation_layer,
            reliability=None,  # filled by the Phase 2 reliability layer
            charted_hadith_count=charted.get(r.id, 0),
        )
        for r in page
    ]
    return NarratorDirectoryPage(
        query=query, total=total, limit=limit, offset=offset, entries=entries
    )


@router.get("/narrators/{narrator_id}", response_model=NarratorDetailRead)
def get_narrator(narrator_id: int, db: Session = Depends(get_db)) -> NarratorDetailRead:
    narrator = db.get(Narrator, narrator_id)
    if narrator is None:
        raise HTTPException(status_code=404, detail="Narrator not found")

    aliases = (
        db.query(NarratorAlias)
        .filter(NarratorAlias.narrator_id == narrator.id)
        .order_by(NarratorAlias.alias_type, NarratorAlias.alias_raw)
        .all()
    )
    entries = (
        db.query(RijalEntry)
        .filter(RijalEntry.narrator_id == narrator.id)
        .order_by(RijalEntry.volume_start, RijalEntry.page_start, RijalEntry.entry_number)
        .all()
    )
    statements = (
        db.query(RijalStatement)
        .filter(RijalStatement.narrator_id == narrator.id)
        .order_by(RijalStatement.source_name, RijalStatement.id)
        .limit(100)
        .all()
    )
    occurrences_total = (
        db.query(func.count(RijalOccurrence.id))
        .filter(RijalOccurrence.narrator_id == narrator.id)
        .scalar()
        or 0
    )
    occurrences = (
        db.query(RijalOccurrence)
        .filter(RijalOccurrence.narrator_id == narrator.id)
        .order_by(RijalOccurrence.direction, RijalOccurrence.related_name_raw)
        .limit(40)
        .all()
    )
    appearance_counts = _narrator_appearance_counts(db, narrator.id)
    appearances_total, appearances = _narrator_hadith_appearances(db, narrator.id, limit=15)

    return NarratorDetailRead(
        **_narrator_summary(narrator).model_dump(),
        aliases=[
            {
                "id": alias.id,
                "alias_raw": alias.alias_raw,
                "alias_type": alias.alias_type,
                "source_note": alias.source_note,
                "confidence": alias.confidence,
            }
            for alias in aliases
        ],
        rijal_entries=[
            {
                "id": entry.id,
                "entry_kind": entry.entry_kind,
                "entry_number": entry.entry_number,
                "title_raw": entry.title_raw,
                "volume_start": entry.volume_start,
                "page_start": entry.page_start,
                "volume_end": entry.volume_end,
                "page_end": entry.page_end,
                "text_raw": (
                    entry.text_raw
                    if len(entry.text_raw) <= 6000
                    else entry.text_raw[:6000]
                    + "\n\n[Entry preview truncated in the API response. Open the source link for the complete text.]"
                ),
                "source_url": entry.source_url,
                "review_status": entry.review_status,
            }
            for entry in entries
        ],
        statements=[
            {
                "id": statement.id,
                "source_name": statement.source_name,
                "statement_type": statement.statement_type,
                "quote_raw": statement.quote_raw,
                "evidence_text_raw": statement.evidence_text_raw,
                "confidence": statement.confidence,
            }
            for statement in statements
        ],
        occurrences=[
            {
                "id": occurrence.id,
                "direction": occurrence.direction,
                "related_name_raw": occurrence.related_name_raw,
                "source_ref_raw": occurrence.source_ref_raw,
                "evidence_text_raw": occurrence.evidence_text_raw,
                "confidence": occurrence.confidence,
            }
            for occurrence in occurrences
        ],
        occurrences_total=occurrences_total,
        appearance_counts=appearance_counts,
        appearances=appearances,
        appearances_total=appearances_total,
    )


@router.get("/narrators/{narrator_id}/transmission-edges", response_model=NarratorTransmissionEdgesRead)
def list_narrator_transmission_edges(
    narrator_id: int,
    source_book_id: str | None = None,
    limit: int = 50,
    sample_limit: int = 5,
    db: Session = Depends(get_db),
) -> NarratorTransmissionEdgesRead:
    narrator = db.get(Narrator, narrator_id)
    if narrator is None:
        raise HTTPException(status_code=404, detail="Narrator not found")
    limit = max(1, min(limit, 100))
    sample_limit = max(1, min(sample_limit, 10))
    return NarratorTransmissionEdgesRead(
        narrator_id=narrator.id,
        source_book_id=source_book_id,
        teachers=_narrator_transmission_edges(
            db,
            narrator.id,
            direction="teachers",
            source_book_id=source_book_id,
            limit=limit,
            sample_limit=sample_limit,
        ),
        students=_narrator_transmission_edges(
            db,
            narrator.id,
            direction="students",
            source_book_id=source_book_id,
            limit=limit,
            sample_limit=sample_limit,
        ),
    )


@router.get("/narrators/{narrator_id}/hadith-appearances", response_model=NarratorHadithAppearancePage)
def list_narrator_hadith_appearances(
    narrator_id: int,
    source_book_id: str | None = None,
    skip: int = 0,
    limit: int = 120,
    db: Session = Depends(get_db),
) -> NarratorHadithAppearancePage:
    narrator = db.get(Narrator, narrator_id)
    if narrator is None:
        raise HTTPException(status_code=404, detail="Narrator not found")
    skip = max(skip, 0)
    limit = max(1, min(limit, 500))
    total, appearances = _narrator_hadith_appearances(
        db,
        narrator.id,
        source_book_id=source_book_id,
        skip=skip,
        limit=limit,
    )
    return NarratorHadithAppearancePage(
        narrator_id=narrator.id,
        total=total,
        skip=skip,
        limit=limit,
        source_book_id=source_book_id,
        appearances=appearances,
    )


# ---- Transmission-graph pair aggregation: shared, decision-aware, TTL-cached ----

_TRANSMISSION_GRAPH_TTL_SECONDS = 3600.0


@dataclasses.dataclass
class _TransmissionPairs:
    """Cluster-rooted edge/node aggregation for one book, pre-pruning.

    Reused by the graph endpoint (all min_count/max_nodes/quality combos apply
    on top of this cached stage) and the edge-evidence endpoint (which needs the
    identical rooting to match a requested edge back to its hadiths).
    """

    edge_hadiths: dict[tuple[int, int], set[int]]
    node_hadiths: dict[int, set[int]]
    clusters: dict[int, set[int]]
    root_of: dict[int, int]
    decisions_applied: int
    computed_at: "dt.datetime"
    # Confidence tags (populated when include_uncertain surfaces best-guesses):
    # a cluster root is confident if any of its mentions is confident; an edge is
    # confident if it has at least one both-confident instance. Empty == all
    # confident (the default confident-only aggregation).
    edge_confident: set[tuple[int, int]] = dataclasses.field(default_factory=set)
    node_confident: dict[int, bool] = dataclasses.field(default_factory=dict)


# key: (source_book_id, resolver_version, include_uncertain, decisions_fingerprint)
_transmission_pairs_cache: dict[
    tuple[str, str, bool, tuple[int, str]], tuple[float, _TransmissionPairs]
] = {}


def clear_transmission_graph_cache() -> None:
    """Drop the cached pair aggregations (tests + after data mutations)."""
    _transmission_pairs_cache.clear()
    _narrator_charted_cache.clear()


def _admin_decisions_fingerprint(db: Session, resolver_version: str) -> tuple[int, str]:
    """(count, max updated_at) of admin decisions — folded into the cache key so
    a review promotion invalidates the graph immediately, not after the TTL."""
    row = db.execute(
        select(
            func.count(PersonResolutionDecision.id),
            func.max(PersonResolutionDecision.updated_at),
        ).where(
            PersonResolutionDecision.reviewer == _ADMIN_PERSON_REVIEWER,
            PersonResolutionDecision.resolver_version == resolver_version,
        )
    ).one()
    return int(row[0] or 0), str(row[1] or "")


def _compute_transmission_pairs(
    db: Session,
    source_book_id: str,
    resolver_version: str,
    include_uncertain: bool = False,
) -> _TransmissionPairs:
    from eshia_research.rijal.effective_resolution import (
        adjacent_pairs,
        load_graph_nodes,
    )
    from eshia_research.rijal.identity_links import same_person_clusters

    nodes = load_graph_nodes(
        db, source_book_id, resolver_version, include_uncertain=include_uncertain
    )
    decisions_applied = sum(1 for n in nodes if n.source == "admin")

    person_ids = {n.person_id for n in nodes}
    clusters = same_person_clusters(db, person_ids)
    root_of = {pid: min(members) for pid, members in clusters.items()}

    # A cluster root counts as confident if ANY of its mentions is confident.
    node_confident: dict[int, bool] = {}
    for n in nodes:
        root = root_of.get(n.person_id, n.person_id)
        if n.confident:
            node_confident[root] = True
        else:
            node_confident.setdefault(root, False)

    edge_hadiths: dict[tuple[int, int], set[int]] = {}
    node_hadiths: dict[int, set[int]] = {}
    edge_confident: set[tuple[int, int]] = set()
    for student, teacher in adjacent_pairs(nodes):
        s_root = root_of.get(student.person_id, student.person_id)
        t_root = root_of.get(teacher.person_id, teacher.person_id)
        if s_root == t_root:
            # An override can collapse a real edge into a self-loop — drop it.
            continue
        edge_hadiths.setdefault((s_root, t_root), set()).add(student.hadith_id)
        node_hadiths.setdefault(s_root, set()).add(student.hadith_id)
        node_hadiths.setdefault(t_root, set()).add(student.hadith_id)
        if student.confident and teacher.confident:
            edge_confident.add((s_root, t_root))

    return _TransmissionPairs(
        edge_hadiths=edge_hadiths,
        node_hadiths=node_hadiths,
        clusters=clusters,
        root_of=root_of,
        decisions_applied=decisions_applied,
        computed_at=dt.datetime.now(dt.timezone.utc),
        edge_confident=edge_confident,
        node_confident=node_confident,
    )


def _get_transmission_pairs(
    db: Session, source_book_id: str, include_uncertain: bool = False
) -> _TransmissionPairs:
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

    fingerprint = _admin_decisions_fingerprint(db, PERSON_RESOLVER_VERSION)
    key = (source_book_id, PERSON_RESOLVER_VERSION, include_uncertain, fingerprint)
    now = time.monotonic()
    hit = _transmission_pairs_cache.get(key)
    if hit is not None and hit[0] > now:
        return hit[1]
    pairs = _compute_transmission_pairs(
        db, source_book_id, PERSON_RESOLVER_VERSION, include_uncertain=include_uncertain
    )
    _transmission_pairs_cache[key] = (now + _TRANSMISSION_GRAPH_TTL_SECONDS, pairs)
    return pairs


def _resolve_book_set(source_book_id: str, books: str | None) -> list[str]:
    """Requested books -> only the polished (charted) ones, deduped in order.

    This is the book-set seam: adding a book to POLISHED_TRANSMISSION_BOOK_IDS is
    the only change needed to let it be charted. A request for an unpolished book
    is silently dropped (never half-drawn); an empty result falls back to Al-Kafi.
    """
    requested = (
        [b.strip() for b in books.split(",") if b.strip()]
        if books
        else [source_book_id]
    )
    polished = [b for b in dict.fromkeys(requested) if b in POLISHED_TRANSMISSION_BOOK_IDS]
    return polished or [AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID]


def _merged_transmission_pairs(
    db: Session, book_ids: list[str], include_uncertain: bool = False
) -> tuple[_TransmissionPairs, dict[int, dict[str, int]]]:
    """Union the per-book cached aggregations into one graph + a per-node
    {book: distinct-hadith count} footprint. Cluster roots are globally
    consistent (`same_person_clusters` is a global union-find), so a plain union
    is correct across books — a narrator in two books collapses to one node.
    """
    per_book = [(b, _get_transmission_pairs(db, b, include_uncertain)) for b in book_ids]
    if len(per_book) == 1:
        book_id, pairs = per_book[0]
        node_books = {root: {book_id: len(h)} for root, h in pairs.node_hadiths.items()}
        return pairs, node_books

    edge_hadiths: dict[tuple[int, int], set[int]] = {}
    node_hadiths: dict[int, set[int]] = {}
    node_books: dict[int, dict[str, int]] = {}
    clusters: dict[int, set[int]] = {}
    root_of: dict[int, int] = {}
    edge_confident: set[tuple[int, int]] = set()
    node_confident: dict[int, bool] = {}
    decisions_applied = 0
    computed_ats: list[dt.datetime] = []
    for book_id, pairs in per_book:
        for pair, h in pairs.edge_hadiths.items():
            edge_hadiths.setdefault(pair, set()).update(h)
        for root, h in pairs.node_hadiths.items():
            node_hadiths.setdefault(root, set()).update(h)
            node_books.setdefault(root, {})[book_id] = len(h)
        edge_confident |= pairs.edge_confident
        for root, conf in pairs.node_confident.items():
            node_confident[root] = node_confident.get(root, False) or conf
        clusters.update(pairs.clusters)
        root_of.update(pairs.root_of)
        decisions_applied += pairs.decisions_applied
        computed_ats.append(pairs.computed_at)
    merged = _TransmissionPairs(
        edge_hadiths=edge_hadiths,
        node_hadiths=node_hadiths,
        clusters=clusters,
        root_of=root_of,
        decisions_applied=decisions_applied,
        computed_at=min(computed_ats) if computed_ats else dt.datetime.now(dt.timezone.utc),
        edge_confident=edge_confident,
        node_confident=node_confident,
    )
    return merged, node_books


# narrator_id -> distinct charted hadiths, keyed by book set. Cheap map over the
# already-cached pairs; TTL-cached so the directory endpoint stays fast.
_narrator_charted_cache: dict[tuple[str, ...], tuple[float, dict[int, int]]] = {}


def _narrator_charted_counts(db: Session, book_ids: list[str]) -> dict[int, int]:
    """narrator_id -> distinct charted hadiths across `book_ids` (person-level,
    matching the graph). A narrator absent from this map is findable but not yet
    charted (count 0)."""
    key = tuple(book_ids)
    now = time.monotonic()
    hit = _narrator_charted_cache.get(key)
    if hit is not None and hit[0] > now:
        return hit[1]

    pairs, _ = _merged_transmission_pairs(db, book_ids)
    node_hadiths = pairs.node_hadiths
    clusters = pairs.clusters
    member_to_root: dict[int, int] = {}
    for root in node_hadiths:
        for member in clusters.get(root, {root}):
            member_to_root.setdefault(member, root)

    counts: dict[int, int] = {}
    if member_to_root:
        # The Mu'jam person/entry tables are ~15.6k rows — load them whole rather
        # than an IN() over thousands of ids (SQLite variable-limit safe).
        entry_to_narr = {
            entry_id: narr
            for entry_id, narr in db.execute(
                select(RijalEntry.id, RijalEntry.narrator_id).where(
                    RijalEntry.narrator_id.isnot(None)
                )
            )
        }
        for pid, entry_id in db.execute(select(Person.id, Person.primary_entry_id)):
            root = member_to_root.get(pid)
            if root is None:
                continue
            narr = entry_to_narr.get(entry_id)
            if narr is None:
                continue
            counts[narr] = max(counts.get(narr, 0), len(node_hadiths[root]))

    _narrator_charted_cache[key] = (now + _TRANSMISSION_GRAPH_TTL_SECONDS, counts)
    return counts


@router.get("/transmission-graph", response_model=TransmissionGraphRead)
def get_transmission_graph(
    source_book_id: str = AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    books: str | None = None,
    min_count: int = 3,
    max_nodes: int = 400,
    quality: bool = False,
    include_uncertain: bool = False,
    db: Session = Depends(get_db),
) -> TransmissionGraphRead:
    """The corpus-wide narrator network: confident person-level student->teacher
    edges aggregated across every chain in one book.

    "Confident" is the *effective* resolution — the resolver's rank-1 pick with
    any admin review decision applied (overrides can promote an otherwise
    ambiguous node; keep-ambiguous/flag demote one), so review corrections flow
    into the graph. Person identities are collapsed through same_person_as
    clusters so a split identity renders as one node. Weights are distinct-hadith
    counts. `min_count` prunes incidental edges; `max_nodes` keeps the strongest
    nodes so the client never receives an unrenderable hairball. `quality=1`
    annotates each surviving edge with the Mu'jam-corroboration verdict.
    """
    min_count = max(1, min_count)
    # Cap headroom for the whole confident al-Kāfī network (~2,000 nodes); the
    # client renders it with a Barnes–Hut layout so the full graph stays smooth.
    max_nodes = max(10, min(max_nodes, 3000))

    book_ids = _resolve_book_set(source_book_id, books)
    pairs, node_books = _merged_transmission_pairs(db, book_ids, include_uncertain)
    edge_hadiths = pairs.edge_hadiths
    node_hadiths = pairs.node_hadiths
    clusters = pairs.clusters

    total_nodes_unfiltered = len(node_hadiths)
    total_edges_unfiltered = len(edge_hadiths)

    kept_edges = {pair: h for pair, h in edge_hadiths.items() if len(h) >= min_count}
    touched = {pid for pair in kept_edges for pid in pair}
    top_nodes = sorted(touched, key=lambda pid: -len(node_hadiths[pid]))[:max_nodes]
    kept_node_set = set(top_nodes)
    kept_edges = {
        (s, t): h for (s, t), h in kept_edges.items()
        if s in kept_node_set and t in kept_node_set
    }
    # Dropping capped nodes can orphan the rest of a weak component.
    kept_node_set = {pid for pair in kept_edges for pid in pair}

    # Node metadata: label/kind from the cluster root, imam-ness and the
    # narrator link from ANY member (the root of a masum cluster may be a
    # plain entry-person).
    member_ids = {m for pid in kept_node_set for m in clusters.get(pid, {pid})}
    person_rows = {
        p.id: p
        for p in db.execute(select(Person).where(Person.id.in_(member_ids))).scalars()
    }
    narrator_by_entry = dict(
        db.execute(
            select(RijalEntry.id, RijalEntry.narrator_id).where(
                RijalEntry.id.in_(
                    {
                        p.primary_entry_id
                        for p in person_rows.values()
                        if p.primary_entry_id is not None
                    }
                )
            )
        ).all()
    )
    generations = dict(
        db.execute(
            select(PersonGeneration.person_id, func.coalesce(PersonGeneration.gen_point, PersonGeneration.gen_lo))
            .where(
                PersonGeneration.person_id.in_(member_ids),
                # Exclude conflict-method rows: a person whose generation evidence
                # is self-contradictory should render as undated in the ṭabaqāt
                # layout rather than be confidently banded at a bogus layer. This
                # matches the quality overlay, which also excludes conflict rows.
                PersonGeneration.method != "conflict",
            )
        ).all()
    )

    nodes: list[TransmissionGraphNode] = []
    for pid in sorted(kept_node_set, key=lambda p: -len(node_hadiths[p])):
        members = sorted(clusters.get(pid, {pid}))
        member_persons = [person_rows[m] for m in members if m in person_rows]
        root = person_rows.get(pid)
        label = root.canonical_name_ar if root else str(pid)
        kind = "imam" if any(p.kind == "masum" for p in member_persons) else "narrator"
        narrator_id = next(
            (
                narrator_by_entry.get(p.primary_entry_id)
                for p in member_persons
                if p.primary_entry_id is not None
                and narrator_by_entry.get(p.primary_entry_id) is not None
            ),
            None,
        )
        generation = next((generations[m] for m in members if m in generations), None)
        nodes.append(
            TransmissionGraphNode(
                id=pid,
                label=label,
                kind=kind,
                generation=generation,
                narrator_id=narrator_id,
                hadith_count=len(node_hadiths[pid]),
                merged_person_ids=members,
                books=node_books.get(pid, {}),
                uncertain=not pairs.node_confident.get(pid, True),
            )
        )

    # Optional Mu'jam-corroboration verdict per surviving edge (small set, so
    # the eval scorer's occurrence/surface-form loads stay cheap).
    edge_quality: dict[tuple[int, int], object] = {}
    if quality and kept_edges:
        from eshia_research.rijal.eval_resolution import score_person_edges

        edge_quality = score_person_edges(db, set(kept_edges.keys()), clusters=clusters)

    edges = []
    for (s, t), h in sorted(kept_edges.items(), key=lambda kv: -len(kv[1])):
        q = edge_quality.get((s, t))
        edges.append(
            TransmissionGraphEdge(
                source=s,
                target=t,
                count=len(h),
                quality=q.corroboration if q is not None else None,
                gen_violation=q.gen_violation if q is not None else None,
                uncertain=(s, t) not in pairs.edge_confident,
            )
        )

    return TransmissionGraphRead(
        source_book_id=",".join(book_ids),
        book_ids=book_ids,
        min_count=min_count,
        max_nodes=max_nodes,
        total_nodes_unfiltered=total_nodes_unfiltered,
        total_edges_unfiltered=total_edges_unfiltered,
        decisions_applied=pairs.decisions_applied,
        computed_at=pairs.computed_at,
        quality=quality,
        include_uncertain=include_uncertain,
        nodes=nodes,
        edges=edges,
    )


@router.get("/transmission-graph/edge-evidence", response_model=TransmissionEdgeEvidenceRead)
def get_transmission_edge_evidence(
    source_person_id: int,
    target_person_id: int,
    source_book_id: str = "11005",
    limit: int = 25,
    db: Session = Depends(get_db),
) -> TransmissionEdgeEvidenceRead:
    """The actual hadiths that jointly attest one student->teacher graph edge.

    `source_person_id`/`target_person_id` are cluster-root person ids exactly as
    the graph reports them (a node id). The edge's distinct-hadith set comes from
    the same cached, decision-aware pair aggregation the graph uses, so the
    evidence always matches the drawn edge. Passing a merged (non-root) member id
    returns nothing — the graph never exposes those as node ids.
    """
    limit = max(1, min(limit, 100))
    pairs = _get_transmission_pairs(db, source_book_id)
    hadith_ids = pairs.edge_hadiths.get((source_person_id, target_person_id), set())

    items: list[TransmissionEdgeEvidenceItem] = []
    if hadith_ids:
        rows = (
            db.query(
                Hadith.public_id,
                Hadith.sequence_in_book,
                Hadith.volume_start,
                Hadith.page_start,
                Hadith.isnad_raw,
            )
            .filter(Hadith.id.in_(hadith_ids))
            .order_by(Hadith.sequence_in_book)
            .limit(limit)
            .all()
        )
        for public_id, seq, vol, page, isnad_raw in rows:
            excerpt = " ".join((isnad_raw or "").split())[:260] or None
            items.append(
                TransmissionEdgeEvidenceItem(
                    public_id=public_id,
                    sequence_in_book=seq,
                    volume_start=vol,
                    page_start=page,
                    isnad_excerpt=excerpt,
                )
            )

    return TransmissionEdgeEvidenceRead(
        source_person_id=source_person_id,
        target_person_id=target_person_id,
        source_book_id=source_book_id,
        total=len(hadith_ids),
        items=items,
    )


def _enumerate_simple_paths(
    adj: dict[int, list[tuple[int, int]]],
    start: int,
    goal: int,
    max_len: int,
    budget: int = 40000,
) -> list[tuple[list[int], list[int]]]:
    """All simple directed paths start->goal up to `max_len` hops, each as
    (node_ids, hop_counts). Bounded by `budget` node expansions so a dense hub
    can't blow up. Isnads are short, so this terminates fast in practice.
    """
    if start == goal:
        return []
    results: list[tuple[list[int], list[int]]] = []
    visited = {start}
    path = [start]
    hops: list[int] = []
    counter = [budget]

    def dfs(node: int) -> None:
        if counter[0] <= 0 or len(hops) >= max_len:
            return
        for nxt, cnt in adj.get(node, ()):
            if counter[0] <= 0:
                return
            if nxt in visited:
                continue
            counter[0] -= 1
            visited.add(nxt)
            path.append(nxt)
            hops.append(cnt)
            if nxt == goal:
                results.append((list(path), list(hops)))
            else:
                dfs(nxt)
            visited.discard(nxt)
            path.pop()
            hops.pop()

    dfs(start)
    return results


@router.get("/transmission-graph/paths", response_model=TransmissionPathsRead)
def get_transmission_paths(
    from_person: int,
    to_person: int,
    books: str | None = None,
    max_len: int = 8,
    k: int = 5,
    db: Session = Depends(get_db),
) -> TransmissionPathsRead:
    """Up to `k` shortest confident isnad paths between two narrators.

    Edges are directed student->teacher, so a path from a narrator to an Imam
    walks in the transmission direction. If nothing chains `from`->`to` but a
    path exists the other way, it is returned oriented correctly with
    `reversed=True`. Only confident (attested) edges are used — paths are honest.
    """
    max_len = max(2, min(max_len, 12))
    k = max(1, min(k, 10))
    book_ids = _resolve_book_set(AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID, books)
    pairs, _ = _merged_transmission_pairs(db, book_ids)

    adj: dict[int, list[tuple[int, int]]] = {}
    for (s, t), h in pairs.edge_hadiths.items():
        adj.setdefault(s, []).append((t, len(h)))

    fr = pairs.root_of.get(from_person, from_person)
    to = pairs.root_of.get(to_person, to_person)

    reversed_ = False
    raw = _enumerate_simple_paths(adj, fr, to, max_len)
    if not raw:
        rev = _enumerate_simple_paths(adj, to, fr, max_len)
        if rev:
            raw, reversed_ = rev, True

    # Rank: fewest hops, then strongest bottleneck, then strongest total.
    raw.sort(key=lambda p: (len(p[0]), -(min(p[1]) if p[1] else 0), -sum(p[1])))
    raw = raw[:k]

    # Node metadata for every person on a surviving path.
    root_pids = {pid for nodes, _ in raw for pid in nodes}
    member_ids = {m for pid in root_pids for m in pairs.clusters.get(pid, {pid})}
    person_rows = {
        p.id: p
        for p in db.execute(select(Person).where(Person.id.in_(member_ids))).scalars()
    }
    narrator_by_entry = dict(
        db.execute(
            select(RijalEntry.id, RijalEntry.narrator_id).where(
                RijalEntry.id.in_(
                    {p.primary_entry_id for p in person_rows.values() if p.primary_entry_id}
                )
            )
        ).all()
    )
    generations = dict(
        db.execute(
            select(
                PersonGeneration.person_id,
                func.coalesce(PersonGeneration.gen_point, PersonGeneration.gen_lo),
            ).where(
                PersonGeneration.person_id.in_(member_ids),
                PersonGeneration.method != "conflict",
            )
        ).all()
    )

    def node_meta(pid: int) -> TransmissionPathNode:
        members = sorted(pairs.clusters.get(pid, {pid}))
        member_persons = [person_rows[m] for m in members if m in person_rows]
        root = person_rows.get(pid)
        kind = "imam" if any(p.kind == "masum" for p in member_persons) else "narrator"
        narrator_id = next(
            (
                narrator_by_entry.get(p.primary_entry_id)
                for p in member_persons
                if p.primary_entry_id is not None
                and narrator_by_entry.get(p.primary_entry_id) is not None
            ),
            None,
        )
        generation = next((generations[m] for m in members if m in generations), None)
        return TransmissionPathNode(
            id=pid,
            label=root.canonical_name_ar if root else str(pid),
            kind=kind,
            generation=generation,
            narrator_id=narrator_id,
        )

    meta = {pid: node_meta(pid) for pid in root_pids}
    paths: list[TransmissionPath] = []
    for nodes, hopcounts in raw:
        paths.append(
            TransmissionPath(
                nodes=[meta[pid] for pid in nodes],
                hops=[
                    TransmissionPathHop(
                        source=nodes[i], target=nodes[i + 1], count=hopcounts[i]
                    )
                    for i in range(len(hopcounts))
                ],
                length=len(hopcounts),
                min_count=min(hopcounts) if hopcounts else 0,
            )
        )

    return TransmissionPathsRead(
        from_person_id=fr,
        to_person_id=to,
        book_ids=book_ids,
        found=bool(paths),
        reversed=reversed_,
        paths=paths,
    )


@router.get("/pages/{page_id}", response_model=PageRead)
def get_page(page_id: int, db: Session = Depends(get_db)) -> Page:
    page = db.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return _attach_text_blocks(page)


@router.get("/stats", response_model=LibraryStats)
def get_stats(db: Session = Depends(get_db)) -> LibraryStats:
    """Real, cheap-to-compute counts for the homepage/about stat tiles.

    Deliberately page/book-level (not hadith- or narrator-level) — the
    schema has no per-tradition or isnad entities yet, so those numbers
    would have to be invented rather than counted.
    """
    catalog_query = _apply_arabic_catalog_filters(db.query(Book))
    books_catalogued = catalog_query.count()
    books_readable = catalog_query.filter(_readable_content_exists()).count()
    pages_digitized = (
        db.query(func.count(Page.id))
        .filter(Page.page_number > 1, Page.text_raw.isnot(None))
        .scalar()
    )
    authors = db.query(func.count(Author.id)).scalar()

    return LibraryStats(
        books_readable=books_readable,
        books_catalogued=books_catalogued,
        pages_digitized=pages_digitized or 0,
        authors=authors or 0,
    )


@router.get("/corpus-status", response_model=CorpusStatusResponse)
def get_corpus_status(db: Session = Depends(get_db)) -> CorpusStatusResponse:
    """Transparent maturity counts for the project's principal collections."""

    source_ids = ("11005", "11021", "10083", "11002", "71860", "11025", "14036")
    books = db.query(Book).filter(Book.source_book_id.in_(source_ids)).all()
    by_source_id = {book.source_book_id: book for book in books}
    book_ids = [book.id for book in books]
    page_counts = dict(
        db.query(Page.book_id, func.count(Page.id))
        .filter(Page.book_id.in_(book_ids))
        .group_by(Page.book_id)
        .all()
    )
    hadith_counts = dict(
        db.query(Hadith.book_id, func.count(Hadith.id))
        .filter(
            Hadith.book_id.in_(book_ids),
            Hadith.review_status != _REJECTED_HADITH_STATUS,
        )
        .group_by(Hadith.book_id)
        .all()
    )
    chain_counts = {
        book_id: (total, flagged or 0)
        for book_id, total, flagged in (
            db.query(
                Hadith.book_id,
                func.count(Chain.id),
                func.sum(case((Chain.review_status == "needs_review", 1), else_=0)),
            )
            .join(Hadith, Hadith.id == Chain.hadith_id)
            .filter(
                Hadith.book_id.in_(book_ids),
                Hadith.review_status != _REJECTED_HADITH_STATUS,
            )
            .group_by(Hadith.book_id)
            .all()
        )
    }
    translation_counts: dict[int, int] = {}
    # A hadith can now carry more than one publishable version; count each
    # translated hadith once, not once per row.
    counted_hadith_ids: set[int] = set()
    translation_rows = (
        db.query(
            Hadith.book_id,
            HadithTranslation.hadith_id,
            HadithTranslation.source_full_sha256,
            HadithTranslation.source_isnad_sha256,
            HadithTranslation.source_matn_sha256,
            HadithTranslation.provenance_json,
            HadithTranslation.risk_flags,
            Hadith.full_text_raw,
            Hadith.isnad_raw,
            Hadith.matn_raw,
        )
        .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
        .filter(
            Hadith.book_id.in_(book_ids),
            Hadith.review_status != _REJECTED_HADITH_STATUS,
            *public_english_translation_candidate_filters(),
        )
        .yield_per(500)
    )
    for row in translation_rows:
        if row.hadith_id in counted_hadith_ids:
            continue
        if (
            has_public_human_source_metadata(row.provenance_json)
            and not has_blocking_risk_flag(row.risk_flags)
            and source_hash_values_are_current(
                source_full_sha256=row.source_full_sha256,
                source_isnad_sha256=row.source_isnad_sha256,
                source_matn_sha256=row.source_matn_sha256,
                full_text_raw=row.full_text_raw,
                isnad_raw=row.isnad_raw,
                matn_raw=row.matn_raw,
            )
        ):
            counted_hadith_ids.add(row.hadith_id)
            translation_counts[row.book_id] = translation_counts.get(row.book_id, 0) + 1
    approved_split_counts = dict(
        db.query(Hadith.book_id, func.count(HadithSplitReview.id))
        .join(Hadith, Hadith.id == HadithSplitReview.hadith_id)
        .filter(
            Hadith.book_id.in_(book_ids),
            HadithSplitReview.review_status == "approved",
        )
        .group_by(Hadith.book_id)
        .all()
    )
    rows: list[CorpusBookStatus] = []
    for source_id in source_ids:
        book = by_source_id.get(source_id)
        if book is None:
            continue
        parsed_chains, flagged_chains = chain_counts.get(book.id, (0, 0))
        rows.append(
            CorpusBookStatus(
                book_id=book.id,
                source_book_id=source_id,
                title_original=book.title_original,
                pages_digitized=page_counts.get(book.id, 0),
                visible_hadiths=hadith_counts.get(book.id, 0),
                parsed_chains=parsed_chains,
                chains_needing_review=flagged_chains,
                public_english_translations=translation_counts.get(book.id, 0),
                approved_split_reviews=approved_split_counts.get(book.id, 0),
            )
        )
    return CorpusStatusResponse(books=rows)
