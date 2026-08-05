"""Tests for the Thaqalayn structure/gradings/live-English pipeline."""
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
    HadithGrading,
    HadithTranslation,
    Page,
    ThaqalaynStructureMap,
)
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.publication import (
    PUBLIC_TRANSLATION_VERSIONS,
    is_public_english_translation,
)
from eshia_research.translation.text import sha256_text
from eshia_research.translation.thaqalayn_structure import (
    LIVE_TRANSLATION_VERSION,
    _grader_key,
    _reclassify_number_apparatus,
)
from eshia_research.translation.thaqalayn_website import WEBSITE_TRANSLATION_VERSION


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


# --- pure-function tests -------------------------------------------------


def test_grader_key_maps_known_authors():
    assert _grader_key("Allamah Baqir al-Majlisi") == "majlisi"
    assert _grader_key("Shaykh Baqir al-Behbudi") == "behbudi"
    assert _grader_key("Someone Else") == "other:someone-else"


def test_footnote_marker_number_mismatch_is_downgraded():
    # eShia footnote marker [2] in the Arabic; clean English omits it.
    flags = [{"code": "number_mismatch", "severity": "critical", "detail": "..."}]
    out, reason = _reclassify_number_apparatus(
        flags,
        qa_text="The translated matn.",
        matn_raw="متن الحديث [2] بقية",
        number_in_chapter=5,
        used_full_fallback=False,
    )
    assert reason == "footnote_marker"
    assert out[0]["code"] == "external_source_number_apparatus"
    assert out[0]["severity"] == "info"


def test_leading_index_number_mismatch_is_downgraded_on_full_fallback():
    flags = [{"code": "number_mismatch", "severity": "critical", "detail": "..."}]
    out, reason = _reclassify_number_apparatus(
        flags,
        qa_text="7. Someone narrated the matn.",
        matn_raw="متن بلا أرقام",
        number_in_chapter=7,
        used_full_fallback=True,
    )
    assert reason and "leading_index" in reason
    assert out[0]["code"] == "external_source_number_apparatus"


def test_real_number_difference_stays_blocking():
    # English introduces a content number the Arabic does not have.
    flags = [{"code": "number_mismatch", "severity": "critical", "detail": "..."}]
    out, reason = _reclassify_number_apparatus(
        flags,
        qa_text="He lived 56 years.",
        matn_raw="عاش سنوات",
        number_in_chapter=3,
        used_full_fallback=False,
    )
    assert reason is None
    assert out[0]["code"] == "number_mismatch"


# --- integration: version priority + endpoints ---------------------------


def _kafi(db: Session) -> Book:
    book = Book(
        source_book_id="11005", title_original="al-kafi", title_normalised="al-kafi", source_url="u"
    )
    db.add(book)
    db.flush()
    return book


def _hadith(db: Session, book: Book, public_id: str, seq: int) -> Hadith:
    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=10 + seq,
        text_raw="t",
        source_url=f"u/1/{10 + seq}",
        checksum=f"c-{public_id}",
    )
    db.add(page)
    db.flush()
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        page_start_id=page.id,
        page_end_id=page.id,
        sequence_in_book=seq,
        sequence_in_page=1,
        printed_number=str(seq),
        volume_start=1,
        volume_end=1,
        page_start=10 + seq,
        page_end=10 + seq,
        full_text_raw="chain matn",
        full_text_normalised="chain matn",
        isnad_raw="chain",
        isnad_normalised="chain",
        matn_raw="matn",
        matn_normalised="matn",
        source_url="u/1/10",
        extraction_method="regex_v1",
        extraction_confidence=90,
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    return hadith


def _translation(db: Session, hadith: Hadith, version: str, text: str, full: str | None = None):
    db.add(
        HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=version,
            source_full_sha256=sha256_text(hadith.full_text_raw),
            source_isnad_sha256=sha256_text(hadith.isnad_raw),
            source_matn_sha256=sha256_text(hadith.matn_raw),
            rendered_isnad_en=None,
            matn_translation=text,
            full_translation=full,
            status="published",
            risk_level="green",
            risk_flags=None,
            provider="thaqalayn-api",
            model="muhammad-sarwar",
            provenance_json={
                "translator": "Muhammad Sarwar",
                "translation_classification": "external_source_normalized",
            },
        )
    )


def test_live_version_wins_over_matn_en_v1(client: TestClient, db: Session):
    book = _kafi(db)
    h = _hadith(db, book, "alkafi-1", 1)
    _translation(db, h, TRANSLATION_VERSION, "old matn text")
    _translation(db, h, LIVE_TRANSLATION_VERSION, "new matn text", full="1. Full verbatim text.")
    db.commit()

    body = client.get("/hadiths/alkafi-1").json()
    assert body["translation"]["translation_version"] == LIVE_TRANSLATION_VERSION
    assert body["translation"]["full_translation"] == "1. Full verbatim text."


def test_website_version_wins_over_api_live_version(client: TestClient, db: Session):
    book = _kafi(db)
    h = _hadith(db, book, "alkafi-website", 3)
    _translation(db, h, LIVE_TRANSLATION_VERSION, "API live text")
    _translation(db, h, WEBSITE_TRANSLATION_VERSION, "Rendered website text")
    db.commit()

    body = client.get("/hadiths/alkafi-website").json()
    assert body["translation"]["translation_version"] == WEBSITE_TRANSLATION_VERSION
    assert body["translation"]["matn_translation"] == "Rendered website text"


def test_matn_en_v1_serves_when_no_live_row(client: TestClient, db: Session):
    book = _kafi(db)
    h = _hadith(db, book, "alkafi-2", 2)
    _translation(db, h, TRANSLATION_VERSION, "only old text")
    db.commit()

    body = client.get("/hadiths/alkafi-2").json()
    assert body["translation"]["translation_version"] == TRANSLATION_VERSION
    assert body["translation"]["matn_translation"] == "only old text"


def test_kitab_and_chapter_endpoints(client: TestClient, db: Session):
    book = _kafi(db)
    h1 = _hadith(db, book, "alkafi-1", 1)
    h2 = _hadith(db, book, "alkafi-2", 2)
    for h, num in ((h1, 1), (h2, 2)):
        db.add(
            ThaqalaynStructureMap(
                hadith_id=h.id,
                source="thaqalayn-api",
                remote_book_id="Al-Kafi-Volume-1-Kulayni",
                remote_id=num,
                volume=1,
                kitab_id="1",
                kitab_name_en="The Book of Intelligence and Ignorance",
                chapter_id=0,
                chapter_name_en="The Book of Intelligence and Ignorance",
                number_in_chapter=num,
                mapping_status="matched",
                match_method="windowed_arabic",
                match_score=0.95,
                matcher_version="thaqalayn_struct_v1",
            )
        )
    db.add(
        HadithGrading(
            hadith_id=h1.id,
            source="thaqalayn-api",
            grader_key="majlisi",
            author_name_en="Allamah Baqir al-Majlisi",
            grade_ar="صحيح",
            grade_en=None,
            reference_en="Mirʾāt al-ʿUqūl (1/25)",
            display_order=0,
        )
    )
    db.commit()

    kitabs = client.get(f"/books/{book.id}/kitabs").json()
    assert len(kitabs) == 1
    assert kitabs[0]["kitab_id"] == "1"
    assert kitabs[0]["hadith_count"] == 2

    chapters = client.get(f"/books/{book.id}/kitabs/1/chapters").json()
    assert chapters[0]["chapter_id"] == 0
    assert chapters[0]["hadith_count"] == 2

    hadiths = client.get(f"/books/{book.id}/kitabs/1/chapters/0/hadiths").json()
    assert [h["public_id"] for h in hadiths] == ["alkafi-1", "alkafi-2"]
    assert hadiths[0]["structure"]["number_in_chapter"] == 1
    assert hadiths[0]["gradings"][0]["grade_ar"] == "صحيح"
    assert hadiths[0]["gradings"][0]["reference_en"] == "Mirʾāt al-ʿUqūl (1/25)"


def test_kitab_endpoints_disambiguate_by_volume(client: TestClient, db: Session):
    """Kitab ids restart every printed volume — vol 3 kitab "1" is Taharat while
    vol 4 kitab "1" is Zakat. Without a volume filter both merge into one bogus
    chapter list, and clicking a chapter opens a different kitab's text."""
    book = _kafi(db)
    rows = [
        # (public_id, seq, volume, chapter_name, hadith count position)
        ("alkafi-100", 1, 3, "The Cleansing Quality of Water"),
        ("alkafi-200", 2, 4, "Virtue of Charity"),
    ]
    for public_id, seq, volume, chapter_name in rows:
        h = _hadith(db, book, public_id, seq)
        db.add(
            ThaqalaynStructureMap(
                hadith_id=h.id,
                source="thaqalayn-website",
                remote_book_id=f"Al-Kafi-Volume-{volume}-Kulayni",
                remote_id=seq,
                volume=volume,
                kitab_id="1",  # same id, different volume, different kitab
                kitab_name_en=f"Kitab of volume {volume}",
                chapter_id=1,  # same chapter number too
                chapter_name_en=chapter_name,
                number_in_chapter=1,
                mapping_status="matched",
                match_method="windowed_arabic",
                match_score=0.95,
                matcher_version="thaqalayn_struct_v1",
            )
        )
    db.commit()

    # Each volume resolves to its own kitab...
    for volume, expected_chapter, expected_hadith in (
        (3, "The Cleansing Quality of Water", "alkafi-100"),
        (4, "Virtue of Charity", "alkafi-200"),
    ):
        chapters = client.get(f"/books/{book.id}/kitabs/1/chapters?volume={volume}").json()
        assert [c["name_en"] for c in chapters] == [expected_chapter]
        hadiths = client.get(
            f"/books/{book.id}/kitabs/1/chapters/1/hadiths?volume={volume}"
        ).json()
        assert [h["public_id"] for h in hadiths] == [expected_hadith]

    # ...and the structure payload carries the volume so links can round-trip.
    body = client.get("/hadiths/alkafi-200").json()
    assert body["structure"]["volume"] == 4


def test_public_translation_versions_ordered():
    # Rendered website text outranks API-live text, which outranks legacy text.
    assert PUBLIC_TRANSLATION_VERSIONS.index(WEBSITE_TRANSLATION_VERSION) < (
        PUBLIC_TRANSLATION_VERSIONS.index(LIVE_TRANSLATION_VERSION)
    )
    assert PUBLIC_TRANSLATION_VERSIONS.index(LIVE_TRANSLATION_VERSION) < (
        PUBLIC_TRANSLATION_VERSIONS.index(TRANSLATION_VERSION)
    )
