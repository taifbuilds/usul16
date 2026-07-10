import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.db import Base, get_db
from eshia_research.models import Book, Page


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_search_returns_results_with_has_content_true(client: TestClient, db: Session):
    # Regression: BookSummary requiring has_content broke /search with a
    # Pydantic ValidationError, because search_pages() returns raw Book ORM
    # objects that (unlike list_books/get_book) never had has_content
    # annotated onto them.
    book = Book(source_book_id="10009", title_original="الكافي", title_normalised="الكافي", source_url="u")
    db.add(book)
    db.flush()
    db.add(Page(book_id=book.id, page_number=1, text_raw="x", text_normalised="بسم الله", source_url="u/1", checksum="x"))
    db.commit()

    response = client.get("/search", params={"q": "بسم"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["book"]["has_content"] is True
