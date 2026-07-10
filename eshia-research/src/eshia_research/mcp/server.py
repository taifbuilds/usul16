"""MCP server scaffold for the eShia research library.

Scope right now: the four planned tool functions are implemented against the
local DB (so they're directly testable/callable from Python), but this
module does NOT yet wire them up to the actual MCP protocol — no `Server`
instance, no stdio/SSE transport, no tool-schema registration. That's
deliberate: the storage layer and citation shape need to stabilize first.

TODO before this is a real MCP server:
  - pip install the `mcp` SDK and wrap each function below in an
    `@server.tool()`-style registration (exact API depends on SDK version).
  - Decide transport (stdio for local Claude Desktop / Claude Code use is
    the obvious first target).
  - Tighten the citation format returned by each tool — callers need a
    stable (book title, author, volume, page, source_url) tuple they can
    quote verbatim.
  - Add pagination/limits consistent with the REST API (see api/routes_*.py).
"""

from dataclasses import dataclass

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Page
from eshia_research.search import search_pages


@dataclass
class Citation:
    book_title: str
    authors: list[str]
    volume_number: int | None
    page_number: int
    source_url: str


def search_library(query: str, filters: dict | None = None) -> list[dict]:
    """Search the mirrored library for `query`, returning citable snippets.

    `filters` is reserved for future use (e.g. category, author, language)
    and is currently ignored.

    TODO: support `filters` once Category/Author filtering is needed by a
    real client; for now it's accepted so the tool signature is stable.
    """
    db = SessionLocal()
    try:
        hits = search_pages(db, query)
        return [
            {
                "snippet": hit.snippet,
                "citation": Citation(
                    book_title=hit.book.title_original,
                    authors=[a.name_original for a in hit.book.authors],
                    volume_number=hit.page.volume_number,
                    page_number=hit.page.page_number,
                    source_url=hit.page.source_url,
                ).__dict__,
            }
            for hit in hits
        ]
    finally:
        db.close()


def get_page(book_id: int, volume: int, page: int) -> dict | None:
    """Fetch the exact text of one book/volume/page, with its citation."""
    db = SessionLocal()
    try:
        row = (
            db.query(Page)
            .filter(Page.book_id == book_id, Page.volume_number == volume, Page.page_number == page)
            .one_or_none()
        )
        if row is None:
            return None
        return {
            "text": row.text_raw,
            "citation": Citation(
                book_title=row.book.title_original,
                authors=[a.name_original for a in row.book.authors],
                volume_number=row.volume_number,
                page_number=row.page_number,
                source_url=row.source_url,
            ).__dict__,
        }
    finally:
        db.close()


def get_book_metadata(book_id: int) -> dict | None:
    """Fetch a book's metadata (title, authors, category, volume count, source URL)."""
    db = SessionLocal()
    try:
        book = db.get(Book, book_id)
        if book is None:
            return None
        return {
            "id": book.id,
            "title": book.title_original,
            "authors": [a.name_original for a in book.authors],
            "category": book.category.name_original if book.category else None,
            "volume_count": book.volume_count,
            "source_url": book.source_url,
        }
    finally:
        db.close()


def search_exact_phrase(phrase: str) -> list[dict]:
    """Search for an exact phrase match (case/diacritic-insensitive via normalisation).

    TODO: this currently reuses the same ILIKE substring search as
    search_library. A true "exact phrase" guarantee needs either a phrase
    query against a real search engine (Meilisearch/OpenSearch) or stricter
    boundary checks here once normalisation rules are finalized.
    """
    return search_library(phrase)
