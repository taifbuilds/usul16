import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.db import Base, get_db
from eshia_research.models import (
    Book,
    Hadith,
    HadithTopicAssignment,
    Page,
    Topic,
)


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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


@pytest.fixture()
def topic_record(db: Session) -> tuple[Hadith, Topic]:
    book = Book(
        source_book_id="11005",
        title_original="Al-Kafi",
        title_normalised="al-kafi",
        source_url="https://example.test/book",
    )
    db.add(book)
    db.flush()
    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=10,
        text_raw="source",
        text_normalised="source",
        source_url="https://example.test/page",
        checksum="page",
    )
    db.add(page)
    db.flush()
    hadith = Hadith(
        public_id="alkafi-topic-api-1",
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
        full_text_raw="Arabic source report",
        full_text_normalised="Arabic source report",
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw="Arabic matn about seeking knowledge",
        matn_normalised="Arabic matn about seeking knowledge",
        source_url="https://example.test/hadith",
        review_status="pending",
    )
    topic = Topic(
        slug="al-kafi-v1-k2",
        hashtag="#knowledge-and-ignorance",
        name_en="The Book of Knowledge and Ignorance",
        kind="kitab",
        source="thaqalayn-structure",
        source_key="v:1:k:2",
        search_text=(
            "the book of knowledge and ignorance knowledge and ignorance "
            "#knowledge-and-ignorance"
        ),
    )
    db.add_all([hadith, topic])
    db.flush()
    db.add(
        HadithTopicAssignment(
            hadith_id=hadith.id,
            topic_id=topic.id,
            relevance=100,
            confidence=0.96,
            assignment_method="structure_matched",
        )
    )
    db.commit()
    return hadith, topic


def test_topic_endpoints_return_hadiths_and_counts(
    client: TestClient, topic_record: tuple[Hadith, Topic]
):
    _, topic = topic_record
    topics = client.get("/topics", params={"q": "knowledge"})
    assert topics.status_code == 200
    assert topics.json()[0]["hadith_count"] == 1

    response = client.get(f"/topics/{topic.slug}/hadiths")
    assert response.status_code == 200
    body = response.json()
    assert body["topic"]["hashtag"] == "#knowledge-and-ignorance"
    assert body["total"] == 1
    assert body["items"][0]["public_id"] == "alkafi-topic-api-1"


def test_hashtag_search_returns_topic_hadith(
    client: TestClient, topic_record: tuple[Hadith, Topic]
):
    response = client.get("/search", params={"q": "#knowledge"})
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["match_type"] == "topic"
    assert result["hadith_public_id"] == "alkafi-topic-api-1"
    assert result["matched_topic"]["slug"] == "al-kafi-v1-k2"


def test_natural_language_search_uses_meaningful_topic_terms(
    client: TestClient, topic_record: tuple[Hadith, Topic]
):
    response = client.get(
        "/search", params={"q": "hadiths about seeking knowledge"}
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["match_type"] == "topic"
    assert result["hadith_public_id"] == "alkafi-topic-api-1"


def test_topic_search_ignores_question_words_and_prioritizes_exact_hashtag(
    client: TestClient,
    db: Session,
    topic_record: tuple[Hadith, Topic],
):
    hadith, _ = topic_record
    prayer = Topic(
        slug="al-kafi-practice-prayer",
        hashtag="#prayer",
        name_en="Prayer",
        kind="practice",
        source="alkafi-semantic",
        source_key="semantic:practice:prayer",
        search_text="prayer pray how to pray #prayer",
    )
    dua = Topic(
        slug="al-kafi-practice-dua",
        hashtag="#dua",
        name_en="Supplication",
        kind="practice",
        source="alkafi-semantic",
        source_key="semantic:practice:dua",
        search_text="supplication personal prayer asking allah #dua",
    )
    forgiveness = Topic(
        slug="al-kafi-virtue-forgiveness",
        hashtag="#forgiveness",
        name_en="Forgiveness",
        kind="virtue",
        source="alkafi-semantic",
        source_key="semantic:virtue:forgiveness",
        search_text="forgiveness forgive pardoning letting go #forgiveness",
    )
    repentance = Topic(
        slug="al-kafi-practice-repentance",
        hashtag="#repentance",
        name_en="Repentance",
        kind="practice",
        source="alkafi-semantic",
        source_key="semantic:practice:repentance",
        search_text="repentance asking forgiveness returning to allah #repentance",
    )
    db.add_all([prayer, dua, forgiveness, repentance])
    db.flush()
    db.add_all(
        [
            HadithTopicAssignment(
                hadith_id=hadith.id,
                topic_id=topic.id,
                relevance=relevance,
                confidence=0.9,
                assignment_method="semantic_translation",
            )
            for topic, relevance in (
                (prayer, 60),
                (dua, 100),
                (forgiveness, 50),
                (repentance, 100),
            )
        ]
    )
    db.commit()

    hashtag_result = client.get("/search", params={"q": "#prayer"}).json()[
        "results"
    ][0]
    assert hashtag_result["matched_topic"]["hashtag"] == "#prayer"

    natural_result = client.get(
        "/search", params={"q": "how can I forgive someone"}
    ).json()["results"][0]
    assert natural_result["matched_topic"]["hashtag"] == "#forgiveness"


def test_hadith_response_includes_topic_assignments(
    client: TestClient, topic_record: tuple[Hadith, Topic]
):
    hadith, _ = topic_record
    response = client.get(f"/hadiths/{hadith.public_id}")
    assert response.status_code == 200
    assert response.json()["topics"][0]["hashtag"] == (
        "#knowledge-and-ignorance"
    )
