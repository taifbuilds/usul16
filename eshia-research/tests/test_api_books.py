import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.api.security import require_admin_api_token
from eshia_research.db import Base, get_db
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    HadithTranslation,
    MentionResolution,
    Narrator,
    NarratorAlias,
    Page,
    Person,
    PersonResolutionDecision,
    RijalEntry,
    RijalOccurrence,
    RijalStatement,
    ThaqalaynStructureMap,
)
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import sha256_text


@pytest.fixture()
def db() -> Session:
    # FastAPI runs sync route handlers in a worker thread, so the test's
    # in-memory SQLite connection must survive across threads — StaticPool
    # keeps the single connection alive instead of each checkout getting its
    # own throwaway ":memory:" database (the default behaviour that made
    # "no such table" errors show up here despite create_all having run).
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
    app.dependency_overrides[require_admin_api_token] = lambda: None
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_split_review_write_fails_closed_without_admin_configuration(db: Session):
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = TestClient(app).put(
            "/hadith-split-reviews/not-present",
            json={
                "approved_isnad_raw": None,
                "approved_matn_raw": "text",
                "review_status": "approved",
                "reviewer": "test",
                "notes": None,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Editorial writes are disabled on this deployment."


def _book(db: Session, source_book_id: str = "10009", title: str = "X") -> Book:
    book = Book(source_book_id=source_book_id, title_original=title, title_normalised=title, source_url="u")
    db.add(book)
    db.flush()
    return book


def _page(
    db: Session,
    book: Book,
    page_number: int = 1,
    volume_number: int = 1,
    text: str | None = "text",
    html: str | None = None,
) -> Page:
    page = Page(
        book_id=book.id,
        volume_number=volume_number,
        page_number=page_number,
        text_raw=text,
        html_raw=html,
        source_url=f"u/{volume_number}/{page_number}",
        checksum=f"x-{book.id}-{volume_number}-{page_number}",
    )
    db.add(page)
    return page


def test_list_books_reports_has_content_true_when_pages_exist(client: TestClient, db: Session):
    book = _book(db)
    _page(db, book, page_number=1)
    _page(db, book, page_number=2)
    db.commit()

    response = client.get("/books")

    assert response.status_code == 200
    assert response.json()[0]["has_content"] is True


def test_list_books_reports_has_content_false_when_no_pages(client: TestClient, db: Session):
    _book(db)
    db.commit()

    response = client.get("/books")

    assert response.status_code == 200
    assert response.json()[0]["has_content"] is False


def test_list_books_orders_by_page_count_descending(client: TestClient, db: Session):
    few_pages = _book(db, source_book_id="10009", title="few pages")
    many_pages = _book(db, source_book_id="20002", title="many pages")
    _page(db, few_pages, page_number=1)
    _page(db, few_pages, page_number=2)
    for n in range(1, 5):
        _page(db, many_pages, page_number=n)
    db.commit()

    response = client.get("/books")

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["many pages", "few pages"]


def test_list_books_excludes_titles_with_persian_only_letters(client: TestClient, db: Session):
    # Book.language is never populated by the crawler, so this is a
    # heuristic (see _PERSIAN_ONLY_LETTERS) rather than a real field filter.
    _book(db, source_book_id="10009", title="احکام ویژه بانوان")  # contains ژ
    _book(db, source_book_id="20002", title="بحار الأنوار")

    response = client.get("/books")

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["بحار الأنوار"]


def test_list_books_excludes_common_persian_titles_without_persian_only_letters(client: TestClient, db: Session):
    _book(db, source_book_id="10009", title="\u0627\u062d\u06a9\u0627\u0645 \u0627\u0642\u062a\u0635\u0627\u062f\u06cc")
    _book(db, source_book_id="20002", title="\u0622\u0634\u0646\u0627\u06cc\u06cc \u0628\u0627 \u0627\u0628\u0648\u0627\u0628 \u0641\u0642\u0647")
    _book(db, source_book_id="30003", title="\u0622\u064a\u0627\u062a \u0627\u0644\u0623\u062d\u0643\u0627\u0645")
    db.commit()

    response = client.get("/books")

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["\u0622\u064a\u0627\u062a \u0627\u0644\u0623\u062d\u0643\u0627\u0645"]


def test_list_books_excludes_duplicate_al_kafi_dar_al_hadith(client: TestClient, db: Session):
    _book(db, source_book_id="27311", title="الکافی- ط دار الحدیث")
    _book(db, source_book_id="11005", title="الكافي- ط الاسلامية")
    db.commit()

    response = client.get("/books")

    source_ids = [b["source_book_id"] for b in response.json()]
    assert source_ids == ["11005"]


def test_list_books_does_not_count_volume_scan_stubs_as_content(client: TestClient, db: Session):
    stub = _book(db, source_book_id="10009", title="scan stub")
    readable = _book(db, source_book_id="20002", title="readable")
    _page(db, stub, page_number=1, volume_number=1)
    _page(db, stub, page_number=1, volume_number=2)
    _page(db, readable, page_number=1)
    _page(db, readable, page_number=2)
    db.commit()

    response = client.get("/books", params={"has_content": "true"})

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["readable"]


def test_list_books_filters_by_has_content_true(client: TestClient, db: Session):
    with_pages = _book(db, source_book_id="10009", title="has pages")
    _book(db, source_book_id="20002", title="no pages")
    _page(db, with_pages, page_number=1)
    _page(db, with_pages, page_number=2)
    db.commit()

    response = client.get("/books", params={"has_content": "true"})

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["has pages"]


def test_list_books_filters_by_has_content_false(client: TestClient, db: Session):
    with_pages = _book(db, source_book_id="10009", title="has pages")
    _book(db, source_book_id="20002", title="no pages")
    _page(db, with_pages, page_number=1)
    _page(db, with_pages, page_number=2)
    db.commit()

    response = client.get("/books", params={"has_content": "false"})

    titles = [b["title_original"] for b in response.json()]
    assert titles == ["no pages"]


def test_get_book_reports_has_content(client: TestClient, db: Session):
    book = _book(db)
    _page(db, book, page_number=1)
    _page(db, book, page_number=2)
    db.commit()

    response = client.get(f"/books/{book.id}")

    assert response.status_code == 200
    assert response.json()["has_content"] is True


def test_get_book_does_not_count_volume_scan_stub_as_content(client: TestClient, db: Session):
    book = _book(db)
    _page(db, book, page_number=1, volume_number=1)
    _page(db, book, page_number=1, volume_number=2)
    db.commit()

    response = client.get(f"/books/{book.id}")

    assert response.status_code == 200
    assert response.json()["has_content"] is False


def test_get_page_includes_structured_text_blocks_from_html(client: TestClient, db: Session):
    book = _book(db)
    page = _page(
        db,
        book,
        page_number=2,
        html="""
        <table><tr><td class="book-page-show">
          <p class="Titr2">بسم الله الرحمن الرحيم</p>
          <p>الحمد لله رب العالمين</p>
          <hr>
          <span class="FootNote">[١] حاشية الصفحة</span>
        </td></tr></table>
        """,
    )
    db.commit()

    response = client.get(f"/pages/{page.id}")

    assert response.status_code == 200
    assert response.json()["text_blocks"] == [
        {"kind": "heading", "text": "بسم الله الرحمن الرحيم"},
        {"kind": "paragraph", "text": "الحمد لله رب العالمين"},
        {"kind": "divider", "text": None},
        {"kind": "footnote", "text": "[١] حاشية الصفحة"},
    ]


def test_list_book_page_index_returns_navigation_fields_without_text(client: TestClient, db: Session):
    book = _book(db)
    _page(db, book, page_number=1, text="large page text")
    _page(db, book, page_number=2, text="another large page text")
    db.commit()

    response = client.get(f"/books/{book.id}/page-index", params={"volume": 1})

    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["page_number"] == 1
    assert rows[1]["page_number"] == 2
    assert "text_raw" not in rows[0]


def test_list_book_hadiths_returns_indexed_hadiths(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    hadith = Hadith(
        public_id="eshia-11005-v01-p0010-u01",
        book_id=book.id,
        page_start_id=page.id,
        page_end_id=page.id,
        sequence_in_book=1,
        sequence_in_page=1,
        printed_number="١",
        volume_start=1,
        volume_end=1,
        page_start=10,
        page_end=10,
        full_text_raw="chain said matn",
        full_text_normalised="chain said matn",
        matn_raw="matn",
        matn_normalised="matn",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(hadith)
    db.commit()

    response = client.get(f"/books/{book.id}/hadiths")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["public_id"] == "eshia-11005-v01-p0010-u01"
    assert body[0]["matn_raw"] == "matn"


def test_list_book_hadiths_filters_to_starting_page(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page_10 = _page(db, book, page_number=10)
    page_11 = _page(db, book, page_number=11)
    common = {
        "book_id": book.id,
        "volume_start": 1,
        "volume_end": 1,
        "full_text_raw": "chain said matn",
        "full_text_normalised": "chain said matn",
        "matn_raw": "matn",
        "matn_normalised": "matn",
        "source_url": page_10.source_url,
        "extraction_method": "regex_v1",
        "extraction_confidence": 90,
        "review_status": "pending",
    }
    db.add_all(
        [
            Hadith(
                **common,
                public_id="eshia-11005-v01-p0010-u01",
                page_start_id=page_10.id,
                page_end_id=page_11.id,
                sequence_in_book=1,
                sequence_in_page=1,
                printed_number="١",
                page_start=10,
                page_end=11,
            ),
            Hadith(
                **{**common, "source_url": page_11.source_url},
                public_id="eshia-11005-v01-p0011-u01",
                page_start_id=page_11.id,
                page_end_id=page_11.id,
                sequence_in_book=2,
                sequence_in_page=1,
                printed_number="٢",
                page_start=11,
                page_end=11,
            ),
        ]
    )
    db.commit()

    response = client.get(f"/books/{book.id}/hadiths", params={"volume": 1, "page": 10})

    assert response.status_code == 200
    assert [row["public_id"] for row in response.json()] == ["eshia-11005-v01-p0010-u01"]

    response = client.get(f"/books/{book.id}/hadiths", params={"volume": 1, "page": 11})

    assert response.status_code == 200
    assert [row["public_id"] for row in response.json()] == [
        "eshia-11005-v01-p0010-u01",
        "eshia-11005-v01-p0011-u01",
    ]


def test_get_hadith_by_public_id(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add(
        Hadith(
            public_id="eshia-11005-v01-p0010-u01",
            book_id=book.id,
            page_start_id=page.id,
            page_end_id=page.id,
            sequence_in_book=1,
            sequence_in_page=1,
            printed_number="١",
            volume_start=1,
            volume_end=1,
            page_start=10,
            page_end=10,
            full_text_raw="chain said matn",
            full_text_normalised="chain said matn",
            matn_raw="matn",
            matn_normalised="matn",
            source_url=page.source_url,
            extraction_method="regex_v1",
            extraction_confidence=90,
            review_status="pending",
        )
    )
    db.commit()

    response = client.get("/hadiths/eshia-11005-v01-p0010-u01")

    assert response.status_code == 200
    assert response.json()["printed_number"] == "١"


def test_get_hadith_exposes_only_current_green_complete_translation(
    client: TestClient, db: Session
):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    hadith = Hadith(
        public_id="alkafi-translated",
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
        full_text_raw="chain matn",
        full_text_normalised="chain matn",
        isnad_raw="chain",
        isnad_normalised="chain",
        matn_raw="matn",
        matn_normalised="matn",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
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
            source_isnad_sha256=sha256_text(hadith.isnad_raw),
            source_matn_sha256=sha256_text(hadith.matn_raw),
            rendered_isnad_en="From chain",
            matn_translation="The translated text.",
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

    response = client.get("/hadiths/alkafi-translated")

    assert response.status_code == 200
    assert response.json()["translation"] == {
        "language": "en",
        "translation_version": TRANSLATION_VERSION,
        "rendered_isnad_en": "From chain",
        "matn_translation": "The translated text.",
        "full_translation": None,
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

    no_isnad = Hadith(
        public_id="alkafi-translated-no-isnad",
        book_id=book.id,
        page_start_id=page.id,
        page_end_id=page.id,
        sequence_in_book=2,
        sequence_in_page=2,
        printed_number="2",
        volume_start=1,
        volume_end=1,
        page_start=10,
        page_end=10,
        full_text_raw="matn only",
        full_text_normalised="matn only",
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw="matn only",
        matn_normalised="matn only",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(no_isnad)
    db.flush()
    db.add(
        HadithTranslation(
            hadith_id=no_isnad.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            source_full_sha256=sha256_text(no_isnad.full_text_raw),
            source_isnad_sha256=None,
            source_matn_sha256=sha256_text(no_isnad.matn_raw),
            rendered_isnad_en=None,
            matn_translation="The matn-only translated text.",
            status="human_reviewed",
            risk_level="green",
            provider="external-human-edition",
            provenance_json={
                "translator": "Reviewed human source",
                "translation_classification": "external_source_normalized",
            },
        )
    )
    db.commit()

    no_isnad_response = client.get("/hadiths/alkafi-translated-no-isnad")
    assert no_isnad_response.status_code == 200
    assert no_isnad_response.json()["translation"]["matn_translation"] == "The matn-only translated text."

    hadith.matn_raw = "changed after translation"
    db.commit()

    stale_response = client.get("/hadiths/alkafi-translated")
    assert stale_response.status_code == 200
    assert stale_response.json()["translation"] is None


def test_public_translation_policy_is_consistent_for_reader_and_corpus_status(
    client: TestClient, db: Session
):
    book = _book(db, source_book_id="11005", title="al-Kafi")
    page = _page(db, book, page_number=10)

    def add_translation(
        public_id: str,
        sequence: int,
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
            full_text_raw=f"chain matn {sequence}",
            full_text_normalised=f"chain matn {sequence}",
            isnad_raw="chain",
            isnad_normalised="chain",
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
                source_isnad_sha256=sha256_text(hadith.isnad_raw),
                source_matn_sha256=(
                    sha256_text("outdated matn") if stale else sha256_text(hadith.matn_raw)
                ),
                matn_translation=f"Public policy example {sequence}.",
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

    add_translation("policy-external", 1)
    add_translation("policy-machine", 2, status="machine_verified")
    add_translation("policy-codex-provider", 3, provider="codex-direct")
    add_translation("policy-openai-model", 4, model="OpenAI GPT-5")
    add_translation(
        "policy-ai-provenance",
        5,
        provenance={"translation_method": "AI-generated draft"},
    )
    add_translation("policy-stale", 6, stale=True)
    add_translation(
        "policy-unattributed",
        7,
        provenance={"translation_classification": "external_source_normalized"},
    )
    add_translation(
        "policy-project-authored",
        8,
        provenance={
            "translator": "Muhammad Sarwar",
            "translation_classification": "project_authored_prohibited",
        },
    )
    add_translation(
        "policy-green-critical",
        9,
        risk_flags=[{"code": "unexpected", "severity": "critical"}],
    )
    db.commit()

    assert client.get("/hadiths/policy-external").json()["translation"] is not None
    for public_id in (
        "policy-machine",
        "policy-codex-provider",
        "policy-openai-model",
        "policy-ai-provenance",
        "policy-stale",
        "policy-unattributed",
        "policy-project-authored",
        "policy-green-critical",
    ):
        assert client.get(f"/hadiths/{public_id}").json()["translation"] is None

    corpus = client.get("/corpus-status")
    assert corpus.status_code == 200
    al_kafi = next(
        row for row in corpus.json()["books"] if row["source_book_id"] == "11005"
    )
    assert al_kafi["public_english_translations"] == 1


def test_get_hadith_chains_returns_nodes_and_ranked_candidates(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    hadith = Hadith(
        public_id="alkafi-1",
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
        full_text_raw="raw",
        full_text_normalised="raw",
        isnad_raw="محمد بن يحيى عن أحمد بن محمد",
        isnad_normalised="محمد بن يحيى عن احمد بن محمد",
        matn_raw="matn",
        matn_normalised="matn",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    narrator = Narrator(canonical_name_ar="أحمد بن محمد", canonical_name_norm="احمد بن محمد")
    other = Narrator(canonical_name_ar="أحمد بن محمد بن خالد", canonical_name_norm="احمد بن محمد بن خالد")
    db.add_all([hadith, narrator, other])
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw, node_count=2)
    db.add(chain)
    db.flush()
    first = ChainNode(
        chain_id=chain.id,
        position=0,
        raw_token="محمد بن يحيى",
        token_normalised="محمد بن يحيى",
        transmission_phrase=None,
        node_type="named_narrator",
        review_status="unresolved",
    )
    second = ChainNode(
        chain_id=chain.id,
        position=1,
        raw_token="أحمد بن محمد",
        token_normalised="احمد بن محمد",
        transmission_phrase="عن",
        node_type="named_narrator",
        canonical_narrator_id=narrator.id,
        confidence=97,
        resolution_method="context_score",
        resolution_reason="next teacher supported",
        review_status="resolved",
    )
    db.add_all([first, second])
    db.flush()
    db.add_all(
        [
            ChainNodeCandidate(
                chain_node_id=second.id,
                narrator_id=narrator.id,
                rank=1,
                score=97,
                match_type="exact_name",
                evidence_summary="context support",
            ),
            ChainNodeCandidate(
                chain_node_id=second.id,
                narrator_id=other.id,
                rank=2,
                score=80,
                match_type="prefix_name",
                evidence_summary="weaker alternative",
            ),
        ]
    )
    db.commit()

    response = client.get("/hadiths/alkafi-1/chains")

    assert response.status_code == 200
    body = response.json()
    assert body["public_id"] == "alkafi-1"
    assert body["chains"][0]["raw_isnad"] == "محمد بن يحيى عن أحمد بن محمد"
    nodes = body["chains"][0]["nodes"]
    assert [node["raw_token"] for node in nodes] == ["محمد بن يحيى", "أحمد بن محمد"]
    assert nodes[1]["narrator"]["canonical_name_ar"] == "أحمد بن محمد"
    assert [candidate["rank"] for candidate in nodes[1]["candidates"]] == [1, 2]
    assert nodes[1]["candidates"][0]["narrator"]["id"] == narrator.id


def test_get_hadith_chains_reflects_admin_override(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    hadith = Hadith(
        public_id="alkafi-ov", book_id=book.id, page_start_id=page.id, page_end_id=page.id,
        sequence_in_book=1, sequence_in_page=1, volume_start=1, volume_end=1,
        page_start=10, page_end=10, full_text_raw="raw", full_text_normalised="raw",
        isnad_raw="x", isnad_normalised="x", matn_raw="m", matn_normalised="m",
        source_url=page.source_url, review_status="pending",
    )
    machine_p = Person(canonical_name_ar="أحمد بن محمد", canonical_name_norm="احمد بن محمد",
                       kind="individual")
    override_p = Person(canonical_name_ar="أحمد بن محمد بن عيسى", canonical_name_norm="احمد بن محمد بن عیسی",
                        kind="individual")
    db.add_all([hadith, machine_p, override_p])
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x", node_count=1)
    db.add(chain)
    db.flush()
    node = ChainNode(chain_id=chain.id, position=0, raw_token="أحمد بن محمد",
                     token_normalised="احمد بن محمد", node_type="named_narrator")
    db.add(node)
    db.flush()
    db.add(MentionResolution(chain_node_id=node.id, person_id=machine_p.id, rank=1,
                             status="ambiguous", method="surface_full",
                             resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonResolutionDecision(
        chain_node_id=node.id, selected_person_id=override_p.id,
        decision_type="approve_external_override", confidence_tier="high",
        reviewer="codex-admin-external-v1", resolver_version=PERSON_RESOLVER_VERSION,
        decision_summary="reviewer picked Ibn Isa",
    ))
    db.commit()

    body = client.get("/hadiths/alkafi-ov/chains").json()
    pr = body["chains"][0]["nodes"][0]["person_resolution"]
    assert pr["effective"]["source"] == "admin"
    assert pr["effective"]["status"] == "approved_override"
    # The correction is surfaced as the headline person, not the machine pick.
    assert pr["resolved_person"]["id"] == override_p.id
    assert pr["status"] == "approved_override"


def test_person_audit_queue_filters_by_machine_decision(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)

    def _node_with_machine_decision(seq: int, decision_type: str) -> None:
        hadith = Hadith(
            public_id=f"alkafi-md-{seq}", book_id=book.id, page_start_id=page.id,
            page_end_id=page.id, sequence_in_book=seq, sequence_in_page=1,
            volume_start=1, volume_end=1, page_start=10, page_end=10,
            full_text_raw="raw", full_text_normalised="raw", isnad_raw="x",
            isnad_normalised="x", matn_raw="m", matn_normalised="m",
            source_url=page.source_url, review_status="pending",
        )
        db.add(hadith)
        db.flush()
        chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x", node_count=1)
        db.add(chain)
        db.flush()
        node = ChainNode(chain_id=chain.id, position=0, raw_token="أحمد بن محمد",
                         token_normalised="احمد بن محمد", node_type="named_narrator")
        db.add(node)
        db.flush()
        db.add(MentionResolution(chain_node_id=node.id, person_id=None, rank=1,
                                 status="ambiguous", method="surface_full",
                                 resolver_version=PERSON_RESOLVER_VERSION))
        db.add(PersonResolutionDecision(
            chain_node_id=node.id, decision_type=decision_type, confidence_tier="low",
            reviewer="codex-machine-v1", resolver_version=PERSON_RESOLVER_VERSION,
        ))

    _node_with_machine_decision(1, "flag_contradiction")
    _node_with_machine_decision(2, "needs_external_review")
    db.commit()

    body = client.get(
        "/person-resolution-audit/queue"
        "?source_book_id=11005&status=all&machine_decision=flag_contradiction"
    ).json()
    assert body["total"] == 1
    assert body["items"][0]["public_id"] == "alkafi-md-1"

    # An unsupported value is rejected.
    bad = client.get(
        "/person-resolution-audit/queue?source_book_id=11005&machine_decision=nonsense"
    )
    assert bad.status_code == 400


def test_get_hadith_chains_hides_rejected_fragments(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add(
        Hadith(
            public_id="alkafi-rejected",
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
            full_text_raw="raw",
            full_text_normalised="raw",
            isnad_raw="chain",
            isnad_normalised="chain",
            matn_raw="matn",
            matn_normalised="matn",
            source_url=page.source_url,
            extraction_method="regex_v1",
            extraction_confidence=90,
            review_status="rejected_non_hadith_fragment",
        )
    )
    db.commit()

    response = client.get("/hadiths/alkafi-rejected/chains")

    assert response.status_code == 404


def test_get_narrator_returns_rijal_profile_slices(client: TestClient, db: Session):
    book = _book(db, source_book_id="14036", title="Mu'jam")
    page = _page(db, book, page_number=12)
    hadith_book = _book(db, source_book_id="11005", title="al-kafi")
    hadith_page = _page(db, hadith_book, page_number=10)
    narrator = Narrator(
        canonical_name_ar="زرارة بن أعين",
        canonical_name_norm="زرارة بن اعين",
        kunya="أبو الحسن",
        summary_status="thiqa",
    )
    db.add(narrator)
    db.flush()
    entry = RijalEntry(
        narrator_id=narrator.id,
        book_id=book.id,
        page_start_id=page.id,
        page_end_id=page.id,
        entry_kind="mujam_numbered_entry",
        entry_number=5000,
        title_raw="زرارة بن أعين",
        title_normalised="زرارة بن اعين",
        canonical_name_raw="زرارة بن أعين",
        canonical_name_normalised="زرارة بن اعين",
        volume_start=7,
        page_start=12,
        volume_end=7,
        page_end=13,
        text_raw="entry text",
        text_normalised="entry text",
        source_url=page.source_url,
    )
    db.add(entry)
    db.flush()
    db.add_all(
        [
            NarratorAlias(
                narrator_id=narrator.id,
                source_entry_id=entry.id,
                alias_raw="زرارة",
                alias_normalised="زرارة",
                alias_type="short_name",
            ),
            RijalStatement(
                entry_id=entry.id,
                narrator_id=narrator.id,
                source_name="najashi",
                statement_type="tawthiq",
                quote_raw="ثقة",
                quote_normalised="ثقة",
                confidence=90,
            ),
            RijalOccurrence(
                entry_id=entry.id,
                narrator_id=narrator.id,
                direction="narrates_from",
                related_name_raw="أبي جعفر",
                related_name_normalised="ابي جعفر",
                evidence_text_raw="روى عن أبي جعفر",
            ),
        ]
    )
    hadith = Hadith(
        public_id="alkafi-1",
        book_id=hadith_book.id,
        page_start_id=hadith_page.id,
        page_end_id=hadith_page.id,
        sequence_in_book=1,
        sequence_in_page=1,
        printed_number="1",
        volume_start=1,
        volume_end=1,
        page_start=10,
        page_end=10,
        full_text_raw="raw",
        full_text_normalised="raw",
        isnad_raw="زرارة عن أبي جعفر",
        isnad_normalised="زرارة عن ابي جعفر",
        matn_raw="قال كذا",
        matn_normalised="قال كذا",
        source_url=hadith_page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw, node_count=1)
    db.add(chain)
    db.flush()
    db.add(
        ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token="زرارة",
            token_normalised="زرارة",
            transmission_phrase=None,
            node_type="named_narrator",
            canonical_narrator_id=narrator.id,
            confidence=99,
            resolution_method="exact_unique",
            review_status="resolved",
        )
    )
    db.commit()

    response = client.get(f"/narrators/{narrator.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["canonical_name_ar"] == "زرارة بن أعين"
    assert body["aliases"][0]["alias_raw"] == "زرارة"
    assert body["rijal_entries"][0]["entry_number"] == 5000
    assert body["statements"][0]["quote_raw"] == "ثقة"
    assert body["occurrences"][0]["related_name_raw"] == "أبي جعفر"
    assert body["occurrences_total"] == 1
    assert body["appearance_counts"] == [
        {
            "book_id": hadith_book.id,
            "source_book_id": "11005",
            "title_original": "al-kafi",
            "total": 1,
        }
    ]
    assert body["appearances_total"] == 1
    assert body["appearances"][0]["public_id"] == "alkafi-1"
    assert body["appearances"][0]["matn_excerpt"] == "قال كذا"


def test_list_narrator_hadith_appearances_filters_by_source_book(client: TestClient, db: Session):
    kafi = _book(db, source_book_id="11005", title="al-kafi")
    tahdhib = _book(db, source_book_id="10083", title="tahdhib")
    kafi_page = _page(db, kafi, page_number=10)
    tahdhib_page = _page(db, tahdhib, page_number=20)
    narrator = Narrator(canonical_name_ar="زرارة", canonical_name_norm="زرارة")
    db.add(narrator)
    db.flush()
    for index, (book, page, public_id) in enumerate(
        [(kafi, kafi_page, "alkafi-1"), (tahdhib, tahdhib_page, "tahdhib-1")],
        start=1,
    ):
        hadith = Hadith(
            public_id=public_id,
            book_id=book.id,
            page_start_id=page.id,
            page_end_id=page.id,
            sequence_in_book=index,
            sequence_in_page=1,
            printed_number=str(index),
            volume_start=1,
            volume_end=1,
            page_start=page.page_number,
            page_end=page.page_number,
            full_text_raw="raw",
            full_text_normalised="raw",
            isnad_raw="زرارة",
            isnad_normalised="زرارة",
            matn_raw=f"matn {index}",
            matn_normalised=f"matn {index}",
            source_url=page.source_url,
            extraction_method="regex_v1",
            extraction_confidence=90,
            review_status="pending",
        )
        db.add(hadith)
        db.flush()
        chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="زرارة", node_count=1)
        db.add(chain)
        db.flush()
        db.add(
            ChainNode(
                chain_id=chain.id,
                position=0,
                raw_token="زرارة",
                token_normalised="زرارة",
                transmission_phrase=None,
                node_type="named_narrator",
                canonical_narrator_id=narrator.id,
                confidence=99,
                resolution_method="exact_unique",
                review_status="resolved",
            )
        )
    db.commit()

    response = client.get(
        f"/narrators/{narrator.id}/hadith-appearances",
        params={"source_book_id": "11005"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["source_book_id"] == "11005"
    assert [item["public_id"] for item in body["appearances"]] == ["alkafi-1"]


def test_list_narrator_transmission_edges_returns_adjacent_teachers_and_students(
    client: TestClient, db: Session
):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.flush()
    student = Narrator(canonical_name_ar="Student", canonical_name_norm="student")
    target = Narrator(canonical_name_ar="Target", canonical_name_norm="target")
    teacher = Narrator(canonical_name_ar="Teacher", canonical_name_norm="teacher")
    db.add_all([student, target, teacher])
    db.flush()
    hadith = Hadith(
        public_id="alkafi-edge-1",
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
        full_text_raw="raw",
        full_text_normalised="raw",
        isnad_raw="Student from Target from Teacher",
        isnad_normalised="student from target from teacher",
        matn_raw="edge matn",
        matn_normalised="edge matn",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw, node_count=3)
    db.add(chain)
    db.flush()
    db.add_all(
        [
            ChainNode(
                chain_id=chain.id,
                position=0,
                raw_token="Student",
                token_normalised="student",
                transmission_phrase=None,
                node_type="named_narrator",
                canonical_narrator_id=student.id,
                confidence=99,
                review_status="resolved",
            ),
            ChainNode(
                chain_id=chain.id,
                position=1,
                raw_token="Target",
                token_normalised="target",
                transmission_phrase="from",
                node_type="named_narrator",
                canonical_narrator_id=target.id,
                confidence=98,
                review_status="resolved",
            ),
            ChainNode(
                chain_id=chain.id,
                position=2,
                raw_token="Teacher",
                token_normalised="teacher",
                transmission_phrase="from",
                node_type="named_narrator",
                canonical_narrator_id=teacher.id,
                confidence=97,
                review_status="resolved",
            ),
        ]
    )
    db.commit()

    response = client.get(
        f"/narrators/{target.id}/transmission-edges",
        params={"source_book_id": "11005", "limit": 10, "sample_limit": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_book_id"] == "11005"
    assert body["teachers"][0]["related_narrator"]["id"] == teacher.id
    assert body["teachers"][0]["total"] == 1
    assert body["teachers"][0]["samples"][0]["public_id"] == "alkafi-edge-1"
    assert body["teachers"][0]["samples"][0]["related_raw_token"] == "Teacher"
    assert body["students"][0]["related_narrator"]["id"] == student.id
    assert body["students"][0]["total"] == 1
    assert body["students"][0]["samples"][0]["related_raw_token"] == "Student"


def test_rejected_non_hadith_fragments_are_hidden_from_reader_routes(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    common = {
        "book_id": book.id,
        "page_start_id": page.id,
        "page_end_id": page.id,
        "sequence_in_page": 1,
        "printed_number": "1",
        "volume_start": 1,
        "volume_end": 1,
        "page_start": 10,
        "page_end": 10,
        "section_title": "chapter",
        "full_text_raw": "full",
        "full_text_normalised": "full",
        "matn_raw": "matn",
        "matn_normalised": "matn",
        "source_url": page.source_url,
        "extraction_method": "regex_v1",
        "extraction_confidence": 90,
    }
    db.add_all(
        [
            Hadith(**common, public_id="alkafi-visible-1", sequence_in_book=1, review_status="pending"),
            Hadith(
                **common,
                public_id="alkafi-rejected",
                sequence_in_book=2,
                review_status="rejected_non_hadith_fragment",
            ),
            Hadith(**common, public_id="alkafi-visible-2", sequence_in_book=3, review_status="pending"),
        ]
    )
    db.commit()

    response = client.get(f"/books/{book.id}/hadiths")
    assert response.status_code == 200
    assert [row["public_id"] for row in response.json()] == ["alkafi-visible-1", "alkafi-visible-2"]

    response = client.get(f"/books/{book.id}/chapters")
    assert response.status_code == 200
    assert response.json()[0]["hadith_count"] == 2

    response = client.get(f"/books/{book.id}/chapters/1/hadiths")
    assert response.status_code == 200
    assert [row["public_id"] for row in response.json()] == ["alkafi-visible-1", "alkafi-visible-2"]

    response = client.get("/hadiths/alkafi-rejected")
    assert response.status_code == 404


def test_printed_page_hadiths_include_verified_chapter_context(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    hadith = Hadith(
        public_id="alkafi-structured-page",
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
        full_text_raw="full",
        full_text_normalised="full",
        matn_raw="matn",
        matn_normalised="matn",
        source_url=page.source_url,
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    db.add(
        ThaqalaynStructureMap(
            hadith_id=hadith.id,
            source="thaqalayn-api",
            remote_book_id="Al-Kafi-Volume-1-Kulayni",
            remote_id=1,
            volume=1,
            kitab_id="2",
            kitab_name_en="The Book on Virtue of Knowledge",
            chapter_id=3,
            chapter_name_en="Chapter on Seeking Knowledge",
            number_in_chapter=1,
            mapping_status="matched",
            match_method="windowed_arabic",
        )
    )
    db.commit()

    response = client.get(f"/books/{book.id}/hadiths", params={"volume": 1, "page": 10})

    assert response.status_code == 200
    structure = response.json()[0]["structure"]
    assert structure["kitab_id"] == "2"
    assert structure["chapter_id"] == 3
    assert structure["chapter_name_en"] == "Chapter on Seeking Knowledge"


def test_split_review_queue_flags_chain_leaking_into_matn(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add(
        Hadith(
            public_id="alkafi-1",
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
            full_text_raw=(
                "\u0623\u062e\u0628\u0631\u0646\u0627 \u0623\u0628\u0648 "
                "\u062c\u0639\u0641\u0631 \u0645\u062d\u0645\u062f \u0628\u0646 "
                "\u064a\u0639\u0642\u0648\u0628 \u0642\u0627\u0644 "
                "\u062d\u062f\u062b\u0646\u064a \u0639\u062f\u0629 \u0645\u0646 "
                "\u0623\u0635\u062d\u0627\u0628\u0646\u0627 \u0639\u0646 "
                "\u0623\u062d\u0645\u062f \u0628\u0646 \u0645\u062d\u0645\u062f "
                "\u0639\u0646 \u0623\u0628\u064a \u062c\u0639\u0641\u0631 "
                "\u0642\u0627\u0644 \u0644\u0645\u0627 \u062e\u0644\u0642 "
                "\u0627\u0644\u0644\u0647 \u0627\u0644\u0639\u0642\u0644"
            ),
            full_text_normalised="",
            isnad_raw=(
                "\u0623\u062e\u0628\u0631\u0646\u0627 \u0623\u0628\u0648 "
                "\u062c\u0639\u0641\u0631 \u0645\u062d\u0645\u062f \u0628\u0646 "
                "\u064a\u0639\u0642\u0648\u0628 \u0642\u0627\u0644"
            ),
            isnad_normalised="",
            matn_raw=(
                "\u062d\u062f\u062b\u0646\u064a \u0639\u062f\u0629 \u0645\u0646 "
                "\u0623\u0635\u062d\u0627\u0628\u0646\u0627 \u0639\u0646 "
                "\u0623\u062d\u0645\u062f \u0628\u0646 \u0645\u062d\u0645\u062f "
                "\u0639\u0646 \u0623\u0628\u064a \u062c\u0639\u0641\u0631 "
                "\u0642\u0627\u0644 \u0644\u0645\u0627 \u062e\u0644\u0642 "
                "\u0627\u0644\u0644\u0647 \u0627\u0644\u0639\u0642\u0644"
            ),
            matn_normalised="",
            source_url=page.source_url,
            extraction_method="regex_v1",
            extraction_confidence=70,
            review_status="pending",
        )
    )
    db.commit()

    response = client.get("/hadith-split-reviews/queue", params={"source_book_id": "11005"})

    assert response.status_code == 200
    item = response.json()[0]
    assert item["hadith"]["public_id"] == "alkafi-1"
    assert "matn_starts_like_chain" in item["suspicion_flags"]
    assert "known_alkafi_h1_chain_leak" in item["suspicion_flags"]


def test_split_review_queue_filters_by_flag(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add_all(
        [
            Hadith(
                public_id="alkafi-missing",
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
                full_text_raw="no detected chain",
                full_text_normalised="no detected chain",
                isnad_raw=None,
                matn_raw="plain matn",
                matn_normalised="plain matn",
                source_url=page.source_url,
                extraction_method="regex_v1",
                extraction_confidence=70,
                review_status="pending",
            ),
            Hadith(
                public_id="alkafi-chainy",
                book_id=book.id,
                page_start_id=page.id,
                page_end_id=page.id,
                sequence_in_book=2,
                sequence_in_page=2,
                printed_number="2",
                volume_start=1,
                volume_end=1,
                page_start=10,
                page_end=10,
                full_text_raw="chainy",
                full_text_normalised="chainy",
                isnad_raw="short",
                isnad_normalised="short",
                matn_raw="\u062d\u062f\u062b\u0646\u064a \u0641\u0644\u0627\u0646 \u0639\u0646 \u0641\u0644\u0627\u0646",
                matn_normalised="",
                source_url=page.source_url,
                extraction_method="regex_v1",
                extraction_confidence=70,
                review_status="pending",
            ),
        ]
    )
    db.commit()

    response = client.get(
        "/hadith-split-reviews/queue",
        params={"source_book_id": "11005", "flag": "missing_isnad"},
    )

    assert response.status_code == 200
    assert [item["hadith"]["public_id"] for item in response.json()] == ["alkafi-missing"]


def test_split_review_audit_counts_flags(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add_all(
        [
            Hadith(
                public_id="alkafi-missing",
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
                full_text_raw="no detected chain",
                full_text_normalised="no detected chain",
                isnad_raw=None,
                matn_raw="plain matn",
                matn_normalised="plain matn",
                source_url=page.source_url,
                extraction_method="regex_v1",
                extraction_confidence=70,
                review_status="pending",
            ),
            Hadith(
                public_id="alkafi-chainy",
                book_id=book.id,
                page_start_id=page.id,
                page_end_id=page.id,
                sequence_in_book=2,
                sequence_in_page=2,
                printed_number="2",
                volume_start=1,
                volume_end=1,
                page_start=10,
                page_end=10,
                full_text_raw="chainy",
                full_text_normalised="chainy",
                isnad_raw="short",
                isnad_normalised="short",
                matn_raw="\u062d\u062f\u062b\u0646\u064a \u0641\u0644\u0627\u0646 \u0639\u0646 \u0641\u0644\u0627\u0646",
                matn_normalised="",
                source_url=page.source_url,
                extraction_method="regex_v1",
                extraction_confidence=70,
                review_status="pending",
            ),
        ]
    )
    db.commit()

    response = client.get("/hadith-split-reviews/audit", params={"source_book_id": "11005"})

    assert response.status_code == 200
    flags = {item["flag"]: item for item in response.json()["flags"]}
    assert flags["missing_isnad"]["unreviewed"] == 1
    assert flags["matn_starts_like_chain"]["examples"] == ["alkafi-chainy"]


def test_save_split_review_returns_manual_split_as_active(client: TestClient, db: Session):
    book = _book(db, source_book_id="11005", title="al-kafi")
    page = _page(db, book, page_number=10)
    db.add(
        Hadith(
            public_id="alkafi-1",
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
            full_text_raw="draft full text",
            full_text_normalised="draft full text",
            isnad_raw="bad short isnad",
            isnad_normalised="bad short isnad",
            matn_raw="bad matn",
            matn_normalised="bad matn",
            source_url=page.source_url,
            extraction_method="regex_v1",
            extraction_confidence=70,
            review_status="pending",
        )
    )
    db.commit()

    response = client.put(
        "/hadith-split-reviews/alkafi-1",
        json={
            "approved_isnad_raw": "manual isnad",
            "approved_matn_raw": "manual matn",
            "review_status": "approved",
            "reviewer": "test",
            "notes": "checked against source",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["active_isnad_raw"] == "manual isnad"
    assert body["active_matn_raw"] == "manual matn"
    assert body["review"]["review_status"] == "approved"

    response = client.get("/hadith-split-reviews/alkafi-1")
    assert response.status_code == 200
    assert response.json()["active_matn_raw"] == "manual matn"

    response = client.get("/hadiths/alkafi-1")
    assert response.status_code == 200
    assert response.json()["isnad_raw"] == "manual isnad"
    assert response.json()["matn_raw"] == "manual matn"


def test_get_book_404_for_missing_book(client: TestClient):
    response = client.get("/books/999999")
    assert response.status_code == 404
