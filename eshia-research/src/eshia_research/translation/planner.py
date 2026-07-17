"""Plan token-efficient hadith translation jobs."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)
from eshia_research.translation import GLOSSARY_VERSION, PROMPT_VERSION, TRANSLATION_VERSION
from eshia_research.translation.text import approx_tokens_from_chars, clean_ws, sha256_text, source_norm


REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"
CURRENT_TRANSLATION_STATUSES = {"planned", "draft", "machine_verified", "human_reviewed", "published"}
LONG_SEGMENT_CHARS = 2200
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.؟?!؛،])\s+")


@dataclass(frozen=True)
class BucketPolicy:
    label: str
    max_chars: int | None
    batch_size: int


BUCKETS = (
    BucketPolicy("short_160", 160, 20),
    BucketPolicy("medium_320", 320, 14),
    BucketPolicy("long_640", 640, 8),
    BucketPolicy("very_long_1280", 1280, 4),
    BucketPolicy("oversize", None, 1),
)


@dataclass(frozen=True)
class TranslationPlanItem:
    hadith_id: int
    public_id: str
    sequence_in_book: int
    volume_start: int | None
    source_chars: int
    segment_count: int
    source_matn_sha256: str
    bucket: str
    batch_size: int
    estimated_input_tokens: int
    estimated_output_tokens: int


@dataclass
class TranslationPlan:
    source_book_id: str
    language: str
    translation_version: str
    total_hadiths: int
    skipped_current: int
    items: list[TranslationPlanItem] = field(default_factory=list)
    bucket_counts: dict[str, int] = field(default_factory=dict)
    total_input_chars: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float | None = None

    @property
    def planned_hadiths(self) -> int:
        return len(self.items)

    @property
    def planned_segments(self) -> int:
        return sum(item.segment_count for item in self.items)


def bucket_for_chars(chars: int) -> BucketPolicy:
    for bucket in BUCKETS:
        if bucket.max_chars is None or chars <= bucket.max_chars:
            return bucket
    return BUCKETS[-1]


def segment_matn(text: str, *, max_chars: int = LONG_SEGMENT_CHARS) -> list[str]:
    cleaned = clean_ws(text)
    if len(cleaned) <= max_chars:
        return [cleaned] if cleaned else []

    pieces = SENTENCE_SPLIT_RE.split(cleaned)
    segments: list[str] = []
    current: list[str] = []
    current_len = 0
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if current and current_len + len(piece) + 1 > max_chars:
            segments.append(" ".join(current))
            current = [piece]
            current_len = len(piece)
        else:
            current.append(piece)
            current_len += len(piece) + (1 if current_len else 0)
    if current:
        segments.append(" ".join(current))
    return segments or [cleaned]


def build_translation_plan(
    db: Session,
    *,
    source_book_id: str,
    language: str = "en",
    translation_version: str = TRANSLATION_VERSION,
    limit: int | None = None,
    pilot_size: int | None = None,
    skip_existing: bool = True,
    input_usd_per_mtok: float | None = None,
    output_usd_per_mtok: float | None = None,
) -> TranslationPlan:
    if limit is not None and pilot_size is not None:
        raise ValueError("Use either limit or pilot_size, not both")
    book = db.execute(select(Book).where(Book.source_book_id == source_book_id)).scalar_one_or_none()
    if book is None:
        raise ValueError(f"No book found for source_book_id={source_book_id}")

    rows = (
        db.execute(
            select(Hadith)
            .where(Hadith.book_id == book.id, Hadith.review_status != REJECTED_HADITH_STATUS)
            .order_by(Hadith.sequence_in_book)
        )
        .scalars()
        .all()
    )
    total_hadiths = len(rows)

    current_hashes: dict[int, str] = {}
    if skip_existing:
        current_hashes = {
            hadith_id: source_hash
            for hadith_id, source_hash in db.execute(
                select(HadithTranslation.hadith_id, HadithTranslation.source_matn_sha256).where(
                    HadithTranslation.language == language,
                    HadithTranslation.translation_version == translation_version,
                    HadithTranslation.status.in_(CURRENT_TRANSLATION_STATUSES),
                )
            )
        }

    plan = TranslationPlan(
        source_book_id=source_book_id,
        language=language,
        translation_version=translation_version,
        total_hadiths=total_hadiths,
        skipped_current=0,
    )

    candidates: list[TranslationPlanItem] = []
    for hadith in rows:
        matn = clean_ws(hadith.matn_raw)
        matn_hash = sha256_text(matn)
        if current_hashes.get(hadith.id) == matn_hash:
            plan.skipped_current += 1
            continue
        segments = segment_matn(matn)
        chars = len(matn)
        bucket = bucket_for_chars(chars)
        input_tokens = approx_tokens_from_chars(chars) + 65
        output_tokens = approx_tokens_from_chars(max(chars, 1), chars_per_token=4.0) + 30
        item = TranslationPlanItem(
            hadith_id=hadith.id,
            public_id=hadith.public_id,
            sequence_in_book=hadith.sequence_in_book,
            volume_start=hadith.volume_start,
            source_chars=chars,
            segment_count=len(segments),
            source_matn_sha256=matn_hash,
            bucket=bucket.label,
            batch_size=bucket.batch_size,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
        )
        candidates.append(item)

    if pilot_size is not None:
        selected = select_stratified_pilot(candidates, pilot_size)
    elif limit is not None:
        selected = candidates[:limit]
    else:
        selected = candidates

    for item in selected:
        plan.items.append(item)
        plan.bucket_counts[item.bucket] = plan.bucket_counts.get(item.bucket, 0) + 1
        plan.total_input_chars += item.source_chars
        plan.estimated_input_tokens += item.estimated_input_tokens
        plan.estimated_output_tokens += item.estimated_output_tokens

    if input_usd_per_mtok is not None and output_usd_per_mtok is not None:
        plan.estimated_cost_usd = (
            plan.estimated_input_tokens / 1_000_000 * input_usd_per_mtok
            + plan.estimated_output_tokens / 1_000_000 * output_usd_per_mtok
        )
    return plan


def select_stratified_pilot(items: list[TranslationPlanItem], size: int) -> list[TranslationPlanItem]:
    if size <= 0 or not items:
        return []
    if size >= len(items):
        return list(items)

    targets = _pilot_targets(size)
    groups = {
        "short": [item for item in items if item.bucket == "short_160"],
        "medium": [item for item in items if item.bucket == "medium_320"],
        "long": [item for item in items if item.bucket in {"long_640", "very_long_1280"}],
        "difficult": [
            item
            for item in items
            if item.bucket == "oversize" or item.segment_count > 1 or item.source_chars > 1280
        ],
    }

    selected: list[TranslationPlanItem] = []
    selected_ids: set[int] = set()
    for group_name in ("short", "medium", "long", "difficult"):
        for item in _round_robin_by_volume(groups[group_name]):
            if len([i for i in selected if _pilot_group(i) == group_name]) >= targets[group_name]:
                break
            if item.hadith_id in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item.hadith_id)

    if len(selected) < size:
        for item in items:
            if item.hadith_id not in selected_ids:
                selected.append(item)
                selected_ids.add(item.hadith_id)
            if len(selected) >= size:
                break

    return sorted(selected[:size], key=lambda item: item.sequence_in_book)


def _pilot_targets(size: int) -> dict[str, int]:
    if size == 300:
        return {"short": 150, "medium": 90, "long": 40, "difficult": 20}
    short = round(size * 0.50)
    medium = round(size * 0.30)
    long = round(size * 0.13)
    difficult = max(0, size - short - medium - long)
    return {"short": short, "medium": medium, "long": long, "difficult": difficult}


def _pilot_group(item: TranslationPlanItem) -> str:
    if item.bucket == "short_160":
        return "short"
    if item.bucket == "medium_320":
        return "medium"
    if item.bucket in {"long_640", "very_long_1280"}:
        return "long"
    return "difficult"


def _round_robin_by_volume(items: list[TranslationPlanItem]) -> list[TranslationPlanItem]:
    by_volume: dict[int, list[TranslationPlanItem]] = {}
    for item in sorted(items, key=lambda i: i.sequence_in_book):
        by_volume.setdefault(item.volume_start or 0, []).append(item)
    out: list[TranslationPlanItem] = []
    volumes = sorted(by_volume)
    while any(by_volume.values()):
        for volume in volumes:
            if by_volume[volume]:
                out.append(by_volume[volume].pop(0))
    return out


def persist_translation_plan(
    db: Session,
    plan: TranslationPlan,
    *,
    provider: str | None = None,
    model: str | None = None,
    prompt_version: str = PROMPT_VERSION,
    glossary_version: str = GLOSSARY_VERSION,
    job_key: str | None = None,
) -> TranslationJob:
    if not plan.items:
        raise ValueError("Cannot persist an empty translation plan")

    fingerprint = sha256_text(
        "|".join(f"{item.hadith_id}:{item.source_matn_sha256}" for item in plan.items)
    )[:16]
    key = job_key or f"{plan.source_book_id}-{plan.language}-{plan.translation_version}-{fingerprint}"
    existing = db.execute(select(TranslationJob).where(TranslationJob.job_key == key)).scalar_one_or_none()
    if existing is not None:
        return existing

    now = dt.datetime.now(dt.timezone.utc)
    job = TranslationJob(
        job_key=key,
        source_book_id=plan.source_book_id,
        language=plan.language,
        status="planned",
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        glossary_version=glossary_version,
        scope_json={
            "source_book_id": plan.source_book_id,
            "translation_version": plan.translation_version,
            "planned_public_ids": [item.public_id for item in plan.items],
        },
        batch_policy_json={bucket.label: bucket.batch_size for bucket in BUCKETS},
        hadith_count=plan.planned_hadiths,
        segment_count=plan.planned_segments,
        input_chars=plan.total_input_chars,
        estimated_input_tokens=plan.estimated_input_tokens,
        estimated_output_tokens=plan.estimated_output_tokens,
        estimated_cost_usd=plan.estimated_cost_usd,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.flush()

    hadiths = {
        h.id: h
        for h in db.execute(
            select(Hadith).where(Hadith.id.in_([item.hadith_id for item in plan.items]))
        ).scalars()
    }
    job_item_index = 1
    for _, item in enumerate(plan.items, start=1):
        hadith = hadiths[item.hadith_id]
        translation = _get_or_create_planned_translation(
            db,
            hadith,
            language=plan.language,
            translation_version=plan.translation_version,
            prompt_version=prompt_version,
            glossary_version=glossary_version,
        )
        segments = segment_matn(hadith.matn_raw)
        for segment_index, segment_text in enumerate(segments):
            segment_hash = sha256_text(segment_text)
            segment = _get_or_create_segment(
                db,
                hadith_id=hadith.id,
                translation_id=translation.id,
                language=plan.language,
                translation_version=plan.translation_version,
                segment_index=segment_index,
                source_text=segment_text,
                source_sha256=segment_hash,
            )
            db.add(
                TranslationJobItem(
                    job_id=job.id,
                    hadith_id=hadith.id,
                    segment_id=segment.id,
                    item_index=job_item_index,
                    source_sha256=segment_hash,
                    status="planned",
                    risk_level="unscored",
                    created_at=now,
                    updated_at=now,
                )
            )
            job_item_index += 1
    db.flush()
    return job


def _get_or_create_planned_translation(
    db: Session,
    hadith: Hadith,
    *,
    language: str,
    translation_version: str,
    prompt_version: str,
    glossary_version: str,
) -> HadithTranslation:
    row = db.execute(
        select(HadithTranslation).where(
            HadithTranslation.hadith_id == hadith.id,
            HadithTranslation.language == language,
            HadithTranslation.translation_version == translation_version,
        )
    ).scalar_one_or_none()
    full_hash = sha256_text(hadith.full_text_raw)
    isnad_hash = sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
    matn_hash = sha256_text(hadith.matn_raw)
    if row is not None:
        row.source_full_sha256 = full_hash
        row.source_isnad_sha256 = isnad_hash
        row.source_matn_sha256 = matn_hash
        row.prompt_version = prompt_version
        row.glossary_version = glossary_version
        row.status = "planned"
        return row

    row = HadithTranslation(
        hadith_id=hadith.id,
        language=language,
        translation_version=translation_version,
        source_full_sha256=full_hash,
        source_isnad_sha256=isnad_hash,
        source_matn_sha256=matn_hash,
        status="planned",
        risk_level="unscored",
        prompt_version=prompt_version,
        glossary_version=glossary_version,
        provenance_json={"source": "planned_translation_job"},
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_segment(
    db: Session,
    *,
    hadith_id: int,
    translation_id: int,
    language: str,
    translation_version: str,
    segment_index: int,
    source_text: str,
    source_sha256: str,
) -> TranslationSegment:
    row = db.execute(
        select(TranslationSegment).where(
            TranslationSegment.hadith_id == hadith_id,
            TranslationSegment.language == language,
            TranslationSegment.translation_version == translation_version,
            TranslationSegment.segment_kind == "matn",
            TranslationSegment.segment_index == segment_index,
            TranslationSegment.source_sha256 == source_sha256,
        )
    ).scalar_one_or_none()
    if row is not None:
        row.translation_id = translation_id
        row.source_text = source_text
        row.status = "planned"
        return row
    row = TranslationSegment(
        hadith_id=hadith_id,
        translation_id=translation_id,
        language=language,
        translation_version=translation_version,
        segment_kind="matn",
        segment_index=segment_index,
        source_text=source_text,
        source_sha256=source_sha256,
        status="planned",
        risk_level="unscored",
        metadata_json={"source_norm": source_norm(source_text)},
    )
    db.add(row)
    db.flush()
    return row


def format_plan(plan: TranslationPlan) -> str:
    cost = "not estimated"
    if plan.estimated_cost_usd is not None:
        cost = f"${plan.estimated_cost_usd:.4f}"
    buckets = ", ".join(f"{key}={value}" for key, value in sorted(plan.bucket_counts.items()))
    return "\n".join(
        [
            f"source_book_id={plan.source_book_id}; language={plan.language}; version={plan.translation_version}",
            f"total_hadiths={plan.total_hadiths}; planned={plan.planned_hadiths}; skipped_current={plan.skipped_current}",
            f"segments={plan.planned_segments}; input_chars={plan.total_input_chars}",
            f"estimated_input_tokens={plan.estimated_input_tokens}; estimated_output_tokens={plan.estimated_output_tokens}; cost={cost}",
            f"buckets: {buckets or 'none'}",
        ]
    )
