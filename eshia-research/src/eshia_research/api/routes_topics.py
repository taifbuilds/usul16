from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from eshia_research.db import get_db
from eshia_research.models import (
    Hadith,
    HadithTopicAssignment,
    HadithTranslation,
    Topic,
)
from eshia_research.schemas import (
    HadithTopicRead,
    TopicHadithItem,
    TopicHadithPage,
    TopicSummaryRead,
)
from eshia_research.translation.publication import (
    PUBLIC_TRANSLATION_VERSIONS,
    is_public_english_translation,
    public_english_translation_candidate_filters,
)


router = APIRouter(prefix="/topics", tags=["topics"])
_VISIBLE_HADITH = Hadith.review_status != "rejected_non_hadith_fragment"
_SEMANTIC_KINDS = ("mood", "life", "practice", "virtue", "belief", "person")


def _summary(topic: Topic, count: int) -> TopicSummaryRead:
    return TopicSummaryRead(
        id=topic.id,
        slug=topic.slug,
        hashtag=topic.hashtag,
        name_en=topic.name_en,
        name_ar=topic.name_ar,
        kind=topic.kind,
        hadith_count=count,
    )


def _topic_counts(db: Session, topic_ids: list[int]) -> dict[int, int]:
    if not topic_ids:
        return {}
    return dict(
        db.query(HadithTopicAssignment.topic_id, func.count(HadithTopicAssignment.id))
        .join(Hadith, Hadith.id == HadithTopicAssignment.hadith_id)
        .filter(HadithTopicAssignment.topic_id.in_(topic_ids), _VISIBLE_HADITH)
        .group_by(HadithTopicAssignment.topic_id)
        .all()
    )


def _hadith_topics(
    db: Session, hadith_ids: list[int]
) -> dict[int, list[HadithTopicRead]]:
    result: dict[int, list[HadithTopicRead]] = {}
    if not hadith_ids:
        return result
    rows = (
        db.query(HadithTopicAssignment, Topic)
        .join(Topic, Topic.id == HadithTopicAssignment.topic_id)
        .filter(HadithTopicAssignment.hadith_id.in_(hadith_ids))
        .order_by(HadithTopicAssignment.relevance.desc(), Topic.name_en)
        .all()
    )
    for assignment, topic in rows:
        result.setdefault(assignment.hadith_id, []).append(
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
    return result


@router.get("", response_model=list[TopicSummaryRead])
def list_topics(
    q: str | None = None,
    kind: str | None = Query(
        None,
        pattern="^(kitab|chapter|mood|life|practice|virtue|belief|person)$",
    ),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TopicSummaryRead]:
    query = (
        db.query(Topic, func.count(HadithTopicAssignment.id).label("hadith_count"))
        .join(HadithTopicAssignment, HadithTopicAssignment.topic_id == Topic.id)
        .join(Hadith, Hadith.id == HadithTopicAssignment.hadith_id)
        .filter(_VISIBLE_HADITH)
    )
    if kind:
        query = query.filter(Topic.kind == kind)
    if q and (needle := q.strip().removeprefix("#")):
        normalized = needle.replace("-", " ")
        query = query.filter(
            or_(
                Topic.name_en.ilike(f"%{needle}%"),
                Topic.search_text.ilike(f"%{normalized}%"),
            )
        )
    rows = (
        query.group_by(Topic.id)
        .order_by(
            case(
                (Topic.kind == "mood", 0),
                (Topic.kind == "life", 1),
                (Topic.kind == "practice", 2),
                (Topic.kind == "virtue", 3),
                (Topic.kind == "belief", 4),
                (Topic.kind == "person", 5),
                (Topic.kind == "kitab", 6),
                else_=7,
            ),
            Topic.name_en,
        )
        .limit(limit)
        .all()
    )
    return [_summary(topic, count) for topic, count in rows]


@router.get("/{slug}/hadiths", response_model=TopicHadithPage)
def get_topic_hadiths(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TopicHadithPage:
    topic = db.query(Topic).filter(Topic.slug == slug).one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    base = (
        db.query(Hadith)
        .join(
            HadithTopicAssignment,
            HadithTopicAssignment.hadith_id == Hadith.id,
        )
        .filter(HadithTopicAssignment.topic_id == topic.id, _VISIBLE_HADITH)
    )
    total = base.count()
    hadiths = (
        base.order_by(Hadith.book_id, Hadith.sequence_in_book)
        .offset(skip)
        .limit(limit)
        .all()
    )
    hadith_ids = [hadith.id for hadith in hadiths]
    topics_by_hadith = _hadith_topics(db, hadith_ids)

    translations_by_hadith: dict[int, HadithTranslation] = {}
    if hadith_ids:
        candidates = (
            db.query(HadithTranslation)
            .filter(
                HadithTranslation.hadith_id.in_(hadith_ids),
                *public_english_translation_candidate_filters(),
            )
            .all()
        )
        hadith_by_id = {hadith.id: hadith for hadith in hadiths}
        version_rank = {
            version: index for index, version in enumerate(PUBLIC_TRANSLATION_VERSIONS)
        }
        for translation in sorted(
            candidates,
            key=lambda row: version_rank.get(
                row.translation_version, len(version_rank)
            ),
        ):
            hadith = hadith_by_id[translation.hadith_id]
            if (
                translation.hadith_id not in translations_by_hadith
                and is_public_english_translation(translation, hadith)
            ):
                translations_by_hadith[translation.hadith_id] = translation

    parent = db.get(Topic, topic.parent_id) if topic.parent_id else None
    related_counts: dict[int, int]
    if topic.kind in _SEMANTIC_KINDS:
        topic_hadith_ids = select(HadithTopicAssignment.hadith_id).where(
            HadithTopicAssignment.topic_id == topic.id
        )
        related_rows = (
            db.query(
                Topic,
                func.count(HadithTopicAssignment.id).label("shared_count"),
            )
            .join(
                HadithTopicAssignment,
                HadithTopicAssignment.topic_id == Topic.id,
            )
            .filter(
                HadithTopicAssignment.hadith_id.in_(topic_hadith_ids),
                Topic.id != topic.id,
                Topic.kind.in_(_SEMANTIC_KINDS),
            )
            .group_by(Topic.id)
            .order_by(func.count(HadithTopicAssignment.id).desc(), Topic.name_en)
            .limit(12)
            .all()
        )
        related = [row for row, _ in related_rows]
        related_counts = _topic_counts(db, [row.id for row in related])
    elif topic.kind == "kitab":
        related = (
            db.query(Topic)
            .filter(Topic.parent_id == topic.id)
            .order_by(Topic.source_key)
            .limit(12)
            .all()
        )
        related_counts = _topic_counts(db, [row.id for row in related])
    else:
        related = (
            db.query(Topic)
            .filter(Topic.parent_id == topic.parent_id, Topic.id != topic.id)
            .order_by(Topic.source_key)
            .limit(12)
            .all()
        )
        related_counts = _topic_counts(db, [row.id for row in related])
    parent_counts = _topic_counts(db, [parent.id] if parent else [])
    topic_count = _topic_counts(db, [topic.id]).get(topic.id, total)

    items = []
    for hadith in hadiths:
        translation = translations_by_hadith.get(hadith.id)
        items.append(
            TopicHadithItem(
                public_id=hadith.public_id,
                book_id=hadith.book_id,
                printed_number=hadith.printed_number,
                volume_start=hadith.volume_start,
                page_start=hadith.page_start,
                page_end=hadith.page_end,
                matn_excerpt_ar=" ".join(hadith.matn_raw.split())[:420],
                translation_excerpt_en=(
                    " ".join(translation.matn_translation.split())[:320]
                    if translation
                    else None
                ),
                topics=topics_by_hadith.get(hadith.id, []),
            )
        )

    return TopicHadithPage(
        topic=_summary(topic, topic_count),
        parent=_summary(parent, parent_counts.get(parent.id, 0)) if parent else None,
        related_topics=[_summary(row, related_counts.get(row.id, 0)) for row in related],
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )
