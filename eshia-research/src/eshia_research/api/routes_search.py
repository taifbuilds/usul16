from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from eshia_research.db import get_db
from eshia_research.schemas import SearchResponse, SearchResult
from eshia_research.search import search_pages

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search query (normalised before matching)"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    hits = search_pages(db, q, limit=limit)
    results = []
    for hit in hits:
        # search_pages() inner-joins Page and Book, so every hit's book is
        # guaranteed to have at least the matched Page row — has_content is
        # always true here by construction, unlike list_books/get_book which
        # need a real EXISTS check since most books have none.
        hit.book.has_content = True
        results.append(SearchResult(page=hit.page, book=hit.book, snippet=hit.snippet))
    return SearchResponse(query=q, count=len(results), results=results)
