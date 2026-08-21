"""Search interface.

`search_pages` is the single entry point used by both the CLI and the API.
The current implementation is plain SQL ILIKE/LIKE over `text_normalised`.
It's intentionally isolated behind this one function so a future Meilisearch
or OpenSearch backend can be swapped in without touching callers — just
replace the body (and keep the SearchHit shape, or adjust callers together
with it).

TODO: swap for Meilisearch/OpenSearch once content volume makes substring
scans too slow; index on text_normalised as a starting point.
"""

from dataclasses import dataclass
import re

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from eshia_research.corpus import (
    HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS,
    public_catalog_filters,
)
from eshia_research.models import (
    Book,
    Hadith,
    HadithTopicAssignment,
    HadithTranslation,
    Page,
    Topic,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.publication import (
    PUBLIC_TRANSLATION_VERSIONS,
    is_public_english_translation,
    public_english_translation_candidate_filters,
)

SNIPPET_RADIUS = 80
_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
_BOOK_ALIASES = {
    "11005": "al-kafi alkafi al kafi",
    "11021": "man la yahduruhu al-faqih al faqih faqih",
    "10083": "tahdhib al-ahkam tahdhib",
    "11002": "al-istibsar istibsar",
    "71860": "bihar al-anwar bihar",
    "11025": "wasa'il al-shia wasail al shia",
    "14036": "mu'jam rijal al-hadith mujam rijal",
}
_TOPIC_QUERY_STOPWORDS = {
    "and",
    "are",
    "about",
    "after",
    "against",
    "anyone",
    "can",
    "could",
    "does",
    "feeling",
    "feel",
    "find",
    "for",
    "from",
    "give",
    "hadith",
    "hadiths",
    "help",
    "how",
    "into",
    "looking",
    "more",
    "need",
    "our",
    "please",
    "should",
    "show",
    "someone",
    "something",
    "tell",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "want",
    "you",
    "your",
}


@dataclass
class SearchHit:
    page: Page
    book: Book
    snippet: str
    match_type: str = "arabic"
    hadith_public_id: str | None = None
    hadith_printed_number: str | None = None
    translation_evidence: dict | None = None
    matched_topic: dict | None = None


def _make_snippet(text: str, query: str, *, case_sensitive: bool = True) -> str:
    source = text if case_sensitive else text.casefold()
    needle = query if case_sensitive else query.casefold()
    idx = source.find(needle)
    if idx == -1:
        return text[: SNIPPET_RADIUS * 2].strip()
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + len(query) + SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def _topic_query_terms(query: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", query.casefold().removeprefix("#")).strip()
    if not normalized:
        return []
    words = [
        word
        for word in normalized.split()
        if len(word) >= 3 and word not in _TOPIC_QUERY_STOPWORDS
    ]
    meaningful_phrase = " ".join(words)
    return list(dict.fromkeys([meaningful_phrase, *words]))



# Which collection a reader most likely meant. Ordering by Book.id instead
# ranked by the crawler's arrival order, which is why a search for «الصلاة»
# used to open with a Persian fiqh primer and never reach al-Kafi at all.
_SEARCH_BOOK_PRIORITY = (
    "11005",  # al-Kafi
    "11021",  # Man La Yahduruhu al-Faqih
    "10083",  # Tahdhib al-Ahkam
    "11002",  # al-Istibsar
    "71860",  # Bihar al-Anwar
    "11025",  # Wasa'il al-Shia
)

# A common word occurs on hundreds of pages of the same work, so asking the
# whole corpus at once returned ten rows of whichever book sorted first. Each
# collection is asked separately for a couple of pages at a time instead,
# which both spreads the results and is far quicker: the per-book queries stop
# as soon as they have their handful, where the corpus-wide scan could not.
_MAX_PER_BOOK = 2


def _arabic_rows(db: Session, normalised_query: str, limit: int):
    like = f"%{normalised_query}%"

    def matching(query):
        return query.filter(
            or_(
                Page.text_normalised.ilike(like),
                Book.title_normalised.ilike(like),
            )
        )

    base = (
        db.query(Page, Book)
        .join(Book, Page.book_id == Book.id)
        .filter(*public_catalog_filters())
    )

    rows: list = []
    offsets = {source_id: 0 for source_id in _SEARCH_BOOK_PRIORITY}
    exhausted: set[str] = set()

    # Round-robin, so a second lap tops the page up from the same collections
    # rather than falling through to the corpus-wide scan.
    while len(rows) < limit and len(exhausted) < len(offsets):
        for source_id in _SEARCH_BOOK_PRIORITY:
            if len(rows) >= limit or source_id in exhausted:
                continue
            found = (
                matching(base.filter(Book.source_book_id == source_id))
                .order_by(Page.volume_number, Page.page_number)
                .offset(offsets[source_id])
                .limit(_MAX_PER_BOOK)
                .all()
            )
            if len(found) < _MAX_PER_BOOK:
                exhausted.add(source_id)
            offsets[source_id] += len(found)
            rows.extend(found[: limit - len(rows)])

    # Only now the rest of the shelf — the rijal references and anything else
    # published. This is the expensive scan, and a query answered by the
    # collections above never reaches it.
    if len(rows) < limit:
        rows.extend(
            matching(base.filter(~Book.source_book_id.in_(_SEARCH_BOOK_PRIORITY)))
            .order_by(Book.id, Page.volume_number, Page.page_number)
            .limit(limit - len(rows))
            .all()
        )
    return rows


def search_pages(db: Session, query: str, limit: int = 20) -> list[SearchHit]:
    query = query.strip()
    normalised_query = normalise_arabic_persian(query)
    if not normalised_query:
        return []

    has_arabic = bool(_ARABIC_RE.search(query))
    if has_arabic:
        rows = _arabic_rows(db, normalised_query, limit)
    else:
        rows = []
        folded_query = query.casefold()
        matching_source_ids = [
            source_id
            for source_id, aliases in _BOOK_ALIASES.items()
            if folded_query in aliases
            and source_id not in HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS
        ]
        for source_id in matching_source_ids:
            row = (
                db.query(Page, Book)
                .join(Book, Page.book_id == Book.id)
                .filter(Book.source_book_id == source_id)
                .order_by(Page.volume_number, Page.page_number)
                .first()
            )
            if row is not None:
                rows.append(row)
            if len(rows) >= limit:
                break

    hits: list[SearchHit] = []
    for page, book in rows:
        haystack = (book.title_normalised if not has_arabic else page.text_normalised) or book.title_normalised
        match_type = "book" if not has_arabic or normalised_query in (book.title_normalised or "") else "arabic"
        hits.append(
            SearchHit(
                page=page,
                book=book,
                snippet=_make_snippet(haystack, normalised_query),
                match_type=match_type,
            )
        )

    remaining = limit - len(hits)
    if remaining <= 0:
        return hits

    if has_arabic:
        return hits

    topic_terms = _topic_query_terms(query)
    seen_public_ids: set[str] = set()
    if topic_terms:
        exact_hashtags = [f"#{term.replace(' ', '-')}" for term in topic_terms]
        primary_term = topic_terms[0]
        whole_primary_match = or_(
            Topic.search_text.ilike(primary_term),
            Topic.search_text.ilike(f"{primary_term} %"),
            Topic.search_text.ilike(f"% {primary_term} %"),
            Topic.search_text.ilike(f"% {primary_term}"),
        )
        topic_rows = (
            db.query(HadithTopicAssignment, Topic, Hadith, Page, Book)
            .join(Topic, Topic.id == HadithTopicAssignment.topic_id)
            .join(Hadith, Hadith.id == HadithTopicAssignment.hadith_id)
            .join(Page, Page.id == Hadith.page_start_id)
            .join(Book, Book.id == Hadith.book_id)
            .filter(
                or_(*(Topic.search_text.ilike(f"%{term}%") for term in topic_terms)),
                Hadith.review_status != "rejected_non_hadith_fragment",
                ~Book.source_book_id.in_(HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS),
            )
            .order_by(
                case(
                    (Topic.hashtag.in_(exact_hashtags), 0),
                    (Topic.name_en.ilike(topic_terms[0]), 1),
                    (whole_primary_match, 2),
                    else_=3,
                ),
                case(
                    (Topic.kind == "mood", 0),
                    (Topic.kind == "life", 1),
                    (Topic.kind == "practice", 2),
                    (Topic.kind == "virtue", 3),
                    (Topic.kind == "belief", 4),
                    (Topic.kind == "person", 5),
                    (Topic.kind == "chapter", 6),
                    else_=7,
                ),
                HadithTopicAssignment.relevance.desc(),
                Hadith.sequence_in_book,
            )
            .limit(remaining * 8)
            .all()
        )
        for assignment, topic, hadith, page, book in topic_rows:
            if hadith.public_id in seen_public_ids:
                continue
            seen_public_ids.add(hadith.public_id)
            hits.append(
                SearchHit(
                    page=page,
                    book=book,
                    snippet=" ".join(hadith.matn_raw.split())[: SNIPPET_RADIUS * 2],
                    match_type="topic",
                    hadith_public_id=hadith.public_id,
                    hadith_printed_number=hadith.printed_number,
                    matched_topic={
                        "slug": topic.slug,
                        "hashtag": topic.hashtag,
                        "name_en": topic.name_en,
                        "name_ar": topic.name_ar,
                        "kind": topic.kind,
                        "relevance": assignment.relevance,
                        "confidence": assignment.confidence,
                        "assignment_method": assignment.assignment_method,
                    },
                )
            )
            if len(hits) >= limit:
                return hits

    translation_rows = (
        db.query(HadithTranslation, Hadith, Page, Book)
        .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
        .join(Page, Page.id == Hadith.page_start_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            *public_english_translation_candidate_filters(),
            HadithTranslation.matn_translation.ilike(f"%{query}%"),
            Hadith.review_status != "rejected",
            ~Book.source_book_id.in_(HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS),
        )
        .order_by(
            Book.id,
            Hadith.sequence_in_book,
            case(
                {
                    version: index
                    for index, version in enumerate(PUBLIC_TRANSLATION_VERSIONS)
                },
                value=HadithTranslation.translation_version,
                else_=len(PUBLIC_TRANSLATION_VERSIONS),
            ),
        )
        .yield_per(100)
    )
    for translation, hadith, page, book in translation_rows:
        if not is_public_english_translation(translation, hadith):
            continue
        # A hadith may match under more than one published version; surface it once.
        if hadith.public_id in seen_public_ids:
            continue
        seen_public_ids.add(hadith.public_id)
        text = translation.matn_translation or ""
        hits.append(
            SearchHit(
                page=page,
                book=book,
                snippet=_make_snippet(text, query, case_sensitive=False),
                match_type="english",
                hadith_public_id=hadith.public_id,
                hadith_printed_number=hadith.printed_number,
                translation_evidence={
                    "status": translation.status,
                    "risk_level": translation.risk_level,
                    "risk_flags": translation.risk_flags,
                    "provider": translation.provider,
                    "model": translation.model,
                    "provenance_json": translation.provenance_json,
                },
            )
        )
        if len(hits) >= limit:
            break
    return hits
