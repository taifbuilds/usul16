"""Audit hadith boundary and isnad/matn split quality.

The audit is deliberately conservative. It does not decide how to fix a row;
it classifies rows that need attention before derived layers such as chain
tokenization and narrator resolution can be trusted.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from eshia_research.models import Book, Chain, Hadith, HadithSplitReview
from eshia_research.normalise import normalise_arabic_persian, strip_diacritics

CHAIN_START_RE = re.compile(
    r"^(?:حدث|حدثني|حدثنا|أخبر|اخبر|عدة\s+من|عن\s+|و\s*عن|بإسناده)"
)
EARLY_CHAIN_RE = re.compile(r"(?:حدث|حدثني|حدثنا|أخبر|اخبر|عن\s+[\u0621-\u064a]{2,})")
TERMINAL_SPEECH_RE = re.compile(
    r"عن\s+(?:أبي\s+جعفر|أبي\s+عبد\s+الله|أبي\s+الحسن|الباقر|الصادق)"
    r"[^.]{0,80}\s+قال"
)

REVIEW_STATUSES = {"approved", "needs_review", "rejected"}


@dataclass
class SplitTexts:
    isnad_raw: str | None
    matn_raw: str
    source: str


@dataclass
class FlagBucket:
    flag: str
    total: int = 0
    unreviewed: int = 0
    approved: int = 0
    needs_review: int = 0
    rejected: int = 0
    examples: list[str] = field(default_factory=list)

    def add(self, status: str, public_id: str, *, max_examples: int = 8) -> None:
        self.total += 1
        if status == "approved":
            self.approved += 1
        elif status == "needs_review":
            self.needs_review += 1
        elif status == "rejected":
            self.rejected += 1
        else:
            self.unreviewed += 1
        if len(self.examples) < max_examples:
            self.examples.append(public_id)


@dataclass
class HadithSplitAuditReport:
    source_book_id: str
    title: str
    total_hadiths: int
    reviewed: int
    approved: int
    needs_review: int
    rejected: int
    unreviewed: int
    suspicious_unreviewed: int
    flagged_hadiths: int
    flags: list[FlagBucket]


def active_split_texts(hadith: Hadith, review: HadithSplitReview | None) -> SplitTexts:
    if review and review.review_status == "approved" and review.approved_matn_raw is not None:
        return SplitTexts(
            isnad_raw=review.approved_isnad_raw,
            matn_raw=review.approved_matn_raw,
            source="review",
        )
    return SplitTexts(isnad_raw=hadith.isnad_raw, matn_raw=hadith.matn_raw, source="hadith")


def review_status_key(review: HadithSplitReview | None) -> str:
    status = review.review_status if review else "unreviewed"
    return status if status in REVIEW_STATUSES else "unreviewed"


def split_suspicion_flags(
    hadith: Hadith,
    review: HadithSplitReview | None = None,
    *,
    chain_raws: list[str] | None = None,
) -> list[str]:
    """Return quality flags for the currently active split.

    ``chain_raws`` is optional derived-data context. When provided, the audit
    can detect rows that need chain-index rebuilding after split edits.
    """
    split = active_split_texts(hadith, review)
    flags: list[str] = []
    matn = strip_diacritics(split.matn_raw or "").strip()
    isnad = strip_diacritics(split.isnad_raw or "").strip()
    raw_matn = " ".join((split.matn_raw or "").split())

    rejected_fragment = (
        hadith.review_status == "rejected_non_hadith_fragment"
        or (review is not None and review.review_status == "rejected")
    )
    if rejected_fragment:
        flags.append("rejected_non_hadith_fragment")
        return flags

    if not isnad:
        flags.append("missing_isnad")
    if not matn:
        flags.append("missing_matn")
    elif len(raw_matn) <= 30:
        flags.append("very_short_matn")

    if CHAIN_START_RE.search(matn[:180]):
        flags.append("matn_starts_like_chain")
    if TERMINAL_SPEECH_RE.search(matn[:450]):
        flags.append("terminal_speech_inside_matn")
    if isnad and len(isnad) < 90 and CHAIN_START_RE.search(matn[:180]):
        flags.append("short_isnad_then_chainy_matn")
    if hadith.public_id == "alkafi-1" and EARLY_CHAIN_RE.search(matn[:250]):
        flags.append("known_alkafi_h1_chain_leak")

    if chain_raws is not None and isnad:
        if not chain_raws:
            flags.append("has_isnad_no_chain")
        else:
            active_norm = normalise_arabic_persian(split.isnad_raw or "")
            chain_norms = {normalise_arabic_persian(raw or "") for raw in chain_raws}
            if active_norm not in chain_norms:
                flags.append("chain_raw_mismatch")

    return flags


def build_hadith_split_audit_report(
    db: Session,
    *,
    source_book_id: str,
    include_chain_index: bool = True,
) -> HadithSplitAuditReport:
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one()
    total_hadiths = db.query(func.count(Hadith.id)).filter(Hadith.book_id == book.id).scalar() or 0

    review_counts = Counter(
        {
            status: count
            for status, count in db.query(HadithSplitReview.review_status, func.count(HadithSplitReview.id))
            .join(Hadith, Hadith.id == HadithSplitReview.hadith_id)
            .filter(Hadith.book_id == book.id)
            .group_by(HadithSplitReview.review_status)
            .all()
        }
    )
    reviewed = sum(review_counts.values())
    approved = review_counts.get("approved", 0)
    needs_review = review_counts.get("needs_review", 0)
    rejected = review_counts.get("rejected", 0)
    unreviewed = max(total_hadiths - reviewed, 0) + review_counts.get("unreviewed", 0)

    chain_raws_by_hadith_id: dict[int, list[str]] | None = None
    if include_chain_index:
        chain_raws_by_hadith_id = defaultdict(list)
        for hadith_id, raw_isnad in (
            db.query(Chain.hadith_id, Chain.raw_isnad)
            .join(Hadith, Hadith.id == Chain.hadith_id)
            .filter(Hadith.book_id == book.id)
            .all()
        ):
            chain_raws_by_hadith_id[hadith_id].append(raw_isnad)

    buckets: dict[str, FlagBucket] = {}
    flagged_hadith_ids: set[int] = set()
    suspicious_unreviewed_ids: set[int] = set()
    rows = (
        db.query(Hadith, HadithSplitReview)
        .outerjoin(HadithSplitReview, HadithSplitReview.hadith_id == Hadith.id)
        .filter(Hadith.book_id == book.id)
        .order_by(Hadith.sequence_in_book)
        .all()
    )
    for hadith, review in rows:
        chain_raws = None
        if chain_raws_by_hadith_id is not None:
            chain_raws = chain_raws_by_hadith_id.get(hadith.id, [])
        flags = split_suspicion_flags(hadith, review, chain_raws=chain_raws)
        if not flags:
            continue
        flagged_hadith_ids.add(hadith.id)
        status = review_status_key(review)
        if status == "unreviewed":
            suspicious_unreviewed_ids.add(hadith.id)
        for flag in flags:
            bucket = buckets.setdefault(flag, FlagBucket(flag=flag))
            bucket.add(status, hadith.public_id)

    flags = sorted(
        buckets.values(),
        key=lambda bucket: (bucket.unreviewed, bucket.total, bucket.flag),
        reverse=True,
    )
    return HadithSplitAuditReport(
        source_book_id=source_book_id,
        title=book.title_original,
        total_hadiths=total_hadiths,
        reviewed=reviewed,
        approved=approved,
        needs_review=needs_review,
        rejected=rejected,
        unreviewed=unreviewed,
        suspicious_unreviewed=len(suspicious_unreviewed_ids),
        flagged_hadiths=len(flagged_hadith_ids),
        flags=flags,
    )
