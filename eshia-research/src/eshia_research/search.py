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

from sqlalchemy import or_
from sqlalchemy.orm import Session

from eshia_research.models import Book, Page
from eshia_research.normalise import normalise_arabic_persian

SNIPPET_RADIUS = 80


@dataclass
class SearchHit:
    page: Page
    book: Book
    snippet: str


def _make_snippet(text: str, query: str) -> str:
    idx = text.find(query)
    if idx == -1:
        return text[: SNIPPET_RADIUS * 2].strip()
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + len(query) + SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def search_pages(db: Session, query: str, limit: int = 20) -> list[SearchHit]:
    normalised_query = normalise_arabic_persian(query)
    if not normalised_query:
        return []

    rows = (
        db.query(Page, Book)
        .join(Book, Page.book_id == Book.id)
        .filter(
            or_(
                Page.text_normalised.ilike(f"%{normalised_query}%"),
                Book.title_normalised.ilike(f"%{normalised_query}%"),
            )
        )
        .limit(limit)
        .all()
    )

    hits: list[SearchHit] = []
    for page, book in rows:
        haystack = page.text_normalised or book.title_normalised
        hits.append(SearchHit(page=page, book=book, snippet=_make_snippet(haystack, normalised_query)))
    return hits
