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

from sqlalchemy import or_
from sqlalchemy.orm import Session

from eshia_research.models import Book, Hadith, HadithTranslation, Page
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.publication import (
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


@dataclass
class SearchHit:
    page: Page
    book: Book
    snippet: str
    match_type: str = "arabic"
    hadith_public_id: str | None = None
    hadith_printed_number: str | None = None
    translation_evidence: dict | None = None


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


def search_pages(db: Session, query: str, limit: int = 20) -> list[SearchHit]:
    query = query.strip()
    normalised_query = normalise_arabic_persian(query)
    if not normalised_query:
        return []

    has_arabic = bool(_ARABIC_RE.search(query))
    if has_arabic:
        rows = (
            db.query(Page, Book)
            .join(Book, Page.book_id == Book.id)
            .filter(
                or_(
                    Page.text_normalised.ilike(f"%{normalised_query}%"),
                    Book.title_normalised.ilike(f"%{normalised_query}%"),
                )
            )
            .order_by(Book.id, Page.volume_number, Page.page_number)
            .limit(limit)
            .all()
        )
    else:
        rows = []
        folded_query = query.casefold()
        matching_source_ids = [
            source_id for source_id, aliases in _BOOK_ALIASES.items() if folded_query in aliases
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

    translation_rows = (
        db.query(HadithTranslation, Hadith, Page, Book)
        .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
        .join(Page, Page.id == Hadith.page_start_id)
        .join(Book, Book.id == Hadith.book_id)
        .filter(
            *public_english_translation_candidate_filters(),
            HadithTranslation.matn_translation.ilike(f"%{query}%"),
            Hadith.review_status != "rejected",
        )
        .order_by(Book.id, Hadith.sequence_in_book)
        .yield_per(100)
    )
    for translation, hadith, page, book in translation_rows:
        if not is_public_english_translation(translation, hadith):
            continue
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
