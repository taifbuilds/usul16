import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.db import Base, get_db
from eshia_research.models import Book, Hadith, HadithTranslation, Page
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import sha256_text


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


def test_search_returns_public_english_translation_with_hadith_link(
    client: TestClient, db: Session
):
    book = Book(
        source_book_id="11005",
        title_original="al-Kafi",
        title_normalised="al-kafi",
        source_url="u",
    )
    db.add(book)
    db.flush()
    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=10,
        text_raw="arabic",
        text_normalised="arabic",
        source_url="u/1/10",
        checksum="page",
    )
    db.add(page)
    db.flush()
    hadith = Hadith(
        public_id="alkafi-search-1",
        book_id=book.id,
        page_start_id=page.id,
        page_end_id=page.id,
        sequence_in_book=1,
        sequence_in_page=1,
        printed_number="1",
        volume_start=1,
        volume_end=1,
        page_start=10,
        page_end=10,
        full_text_raw="arabic",
        full_text_normalised="arabic",
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw="arabic",
        matn_normalised="arabic",
        source_url="u/1/10",
        extraction_method="test",
        extraction_confidence=100,
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    db.add(
        HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            source_full_sha256=sha256_text(hadith.full_text_raw),
            source_matn_sha256=sha256_text(hadith.matn_raw),
            matn_translation="Knowledge is a light placed in the heart.",
            status="published",
            risk_level="green",
            provider="thaqalayn-api",
            model="muhammad-sarwar",
            provenance_json={
                "translator": "Muhammad Sarwar",
                "translation_classification": "external_source_normalized",
            },
        )
    )
    db.commit()

    response = client.get("/search", params={"q": "knowledge"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["match_type"] == "english"
    assert body["results"][0]["hadith_public_id"] == "alkafi-search-1"
    assert "Knowledge" in body["results"][0]["snippet"]
    assert body["results"][0]["translation_evidence"] == {
        "status": "published",
        "risk_level": "green",
        "risk_flags": None,
        "provider": "thaqalayn-api",
        "model": "muhammad-sarwar",
        "provenance_json": {
            "translator": "Muhammad Sarwar",
            "translation_classification": "external_source_normalized",
        },
    }


def test_english_search_uses_fail_closed_public_translation_policy(
    client: TestClient, db: Session
):
    book = Book(
        source_book_id="11005",
        title_original="al-Kafi",
        title_normalised="al-kafi",
        source_url="u",
    )
    db.add(book)
    db.flush()
    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=10,
        text_raw="arabic",
        text_normalised="arabic",
        source_url="u/1/10",
        checksum="page",
    )
    db.add(page)
    db.flush()

    def add_translation(
        public_id: str,
        sequence: int,
        phrase: str,
        *,
        status: str = "published",
        provider: str = "external-human-edition",
        model: str = "muhammad-sarwar",
        provenance: dict | None = None,
        stale: bool = False,
        risk_flags: list | None = None,
    ) -> None:
        hadith = Hadith(
            public_id=public_id,
            book_id=book.id,
            page_start_id=page.id,
            page_end_id=page.id,
            sequence_in_book=sequence,
            sequence_in_page=sequence,
            printed_number=str(sequence),
            volume_start=1,
            volume_end=1,
            page_start=10,
            page_end=10,
            full_text_raw=f"full {sequence}",
            full_text_normalised=f"full {sequence}",
            isnad_raw=None,
            isnad_normalised=None,
            matn_raw=f"matn {sequence}",
            matn_normalised=f"matn {sequence}",
            source_url=f"u/{sequence}",
            extraction_method="test",
            extraction_confidence=100,
            review_status="pending",
        )
        db.add(hadith)
        db.flush()
        db.add(
            HadithTranslation(
                hadith_id=hadith.id,
                language="en",
                translation_version=TRANSLATION_VERSION,
                source_full_sha256=sha256_text(hadith.full_text_raw),
                source_isnad_sha256=None,
                source_matn_sha256=(
                    sha256_text("old matn") if stale else sha256_text(hadith.matn_raw)
                ),
                matn_translation=phrase,
                status=status,
                risk_level="green",
                risk_flags=risk_flags,
                provider=provider,
                model=model,
                provenance_json=(
                    provenance
                    if provenance is not None
                    else {
                        "translator": "Muhammad Sarwar",
                        "translation_classification": "external_source_normalized",
                    }
                ),
            )
        )

    add_translation("search-external", 1, "Externalpolicy visible wording")
    add_translation(
        "search-machine", 2, "Machinepolicy hidden wording", status="machine_verified"
    )
    add_translation(
        "search-codex", 3, "Codexpolicy hidden wording", provider="codex-direct"
    )
    add_translation(
        "search-model", 4, "Modelpolicy hidden wording", model="OpenAI GPT-5"
    )
    add_translation(
        "search-provenance",
        5,
        "Provenancepolicy hidden wording",
        provenance={"method": "LLM translation"},
    )
    add_translation("search-stale", 6, "Stalepolicy hidden wording", stale=True)
    add_translation(
        "search-unattributed",
        7,
        "Unattributedpolicy hidden wording",
        provenance={"translation_classification": "external_source_normalized"},
    )
    add_translation(
        "search-project-authored",
        8,
        "Projectauthoredpolicy hidden wording",
        provenance={
            "translator": "Muhammad Sarwar",
            "translation_classification": "project_authored_prohibited",
        },
    )
    add_translation(
        "search-green-critical",
        9,
        "Criticalflagpolicy hidden wording",
        risk_flags=[{"code": "unexpected", "severity": "critical"}],
    )
    db.commit()

    visible = client.get("/search", params={"q": "Externalpolicy"}).json()
    assert visible["count"] == 1
    assert visible["results"][0]["hadith_public_id"] == "search-external"

    for query in (
        "Machinepolicy",
        "Codexpolicy",
        "Modelpolicy",
        "Provenancepolicy",
        "Stalepolicy",
        "Unattributedpolicy",
        "Projectauthoredpolicy",
        "Criticalflagpolicy",
    ):
        body = client.get("/search", params={"q": query}).json()
        assert body["count"] == 0


def test_unpublished_books_are_not_searchable(client: TestClient, db: Session):
    # A book hidden from the catalogue must not be reachable by searching its
    # text either, or hiding it only moves the door rather than closing it.
    hidden = Book(
        source_book_id="10926",
        title_original="الوهابيون",
        title_normalised="الوهابيون",
        source_url="u",
    )
    shown = Book(
        source_book_id="11005",
        title_original="الكافي",
        title_normalised="الكافي",
        source_url="u2",
    )
    db.add_all([hidden, shown])
    db.flush()
    for book in (hidden, shown):
        db.add(
            Page(
                book_id=book.id,
                page_number=1,
                text_raw="x",
                text_normalised="مرفوعة",
                source_url=f"u/{book.id}",
                checksum=f"c{book.id}",
            )
        )
    db.commit()

    body = client.get("/search", params={"q": "مرفوعة"}).json()

    assert [r["book"]["source_book_id"] for r in body["results"]] == ["11005"]
