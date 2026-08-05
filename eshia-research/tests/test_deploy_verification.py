"""Stage 8 of deploy-db.sh: is the deployed commentary actually being served?

The bug these guard against reported failure on a deployment that had entirely
succeeded, and printed a rollback command for it. A false negative here is worse
than no check, so the payload-shape cases matter as much as the happy path.
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.commentary.verification import (
    VerificationError,
    pick_linked_public_id,
    verify_payload,
)
from eshia_research.db import Base
from eshia_research.models import Book, Hadith, HadithCommentary
from eshia_research.normalise import normalise_arabic_persian


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


def _corpus(db: Session) -> tuple[Book, Book]:
    kafi = Book(source_book_id="11005", title_original="الكافي",
                title_normalised="الكافي", source_url="https://lib.eshia.ir/11005")
    sharh = Book(source_book_id="71429", title_original="مرآة العقول",
                 title_normalised="مرآة العقول", source_url="https://lib.eshia.ir/71429/1/1")
    db.add_all([kafi, sharh])
    db.flush()
    return kafi, sharh


def _hadith(db: Session, kafi: Book, public_id: str, sequence: int) -> Hadith:
    text = f"نص الحديث رقم {sequence}"
    hadith = Hadith(
        public_id=public_id, book_id=kafi.id, sequence_in_book=sequence,
        sequence_in_page=1, printed_number=str(sequence), volume_start=1, volume_end=1,
        page_start=1, page_end=1, section_title="باب",
        full_text_raw=text, full_text_normalised=normalise_arabic_persian(text),
        isnad_raw=None, isnad_normalised=None, matn_raw=text,
        matn_normalised=normalise_arabic_persian(text),
        source_url="https://lib.eshia.ir/11005/1/1", extraction_method="test",
        extraction_confidence=100, review_status="approved",
    )
    db.add(hadith)
    db.flush()
    return hadith


def _commentary(
    db: Session, sharh: Book, hadith: Hadith | None, source_key: str, *,
    sequence: int = 1, match_status: str = "matched",
) -> HadithCommentary:
    row = HadithCommentary(
        commentary_book_id=sharh.id,
        hadith_id=hadith.id if hadith is not None else None,
        source_key=source_key, source_sequence=sequence, source_label="الحديث الأول",
        section_title="باب", report_raw=None, report_normalised=None,
        commentary_raw="شرح", commentary_normalised="شرح",
        volume_start=1, volume_end=1, page_start=1, page_end=1,
        source_url="https://lib.eshia.ir/71429/1/1",
        match_status=match_status, match_method="text_only", match_score=1.0,
        matcher_version="test", match_evidence_json={},
    )
    db.add(row)
    db.flush()
    return row


def _payload(source_keys: list[str], *, padding: int = 0, public_id: str = "alkafi-2") -> str:
    """An API response shaped like the real one, with `commentaries` last."""
    document: dict = {
        "public_id": public_id,
        "isnad_raw": "ع" * padding,
        "matn_raw": "م" * padding,
        "footnotes": [{"marker": str(i), "text": "ه" * 50} for i in range(padding // 500)],
        "translation": {"matn_translation": "t" * padding},
        "commentaries": [
            {"source_key": key, "title_ar": "شرح", "author_ar": "مؤلف", "evidence": "text"}
            for key in source_keys
        ],
    }
    return json.dumps(document, ensure_ascii=False)


# --- the regression that motivated the rewrite ----------------------------

def test_commentaries_after_4000_bytes_still_verifies():
    """The original bug: the field simply sat past the truncation boundary.

    `alkafi-2` carries a long isnad, matn, footnotes and translation before its
    commentaries, so `head -c 4000` cut the payload short and the check reported
    failure for a deployment that had succeeded.
    """
    payload = _payload(["mirat-al-uqul"], padding=4000)

    assert len(payload) > 4000
    assert "commentaries" not in payload[:4000]  # the old check would have failed

    entry = verify_payload(payload, "mirat-al-uqul")

    assert entry["source_key"] == "mirat-al-uqul"


def test_very_large_payload_is_read_whole():
    payload = _payload(["sharh-al-mazandarani"], padding=60000)

    assert len(payload) > 120000
    assert verify_payload(payload, "sharh-al-mazandarani")["source_key"] == "sharh-al-mazandarani"


# --- success -------------------------------------------------------------

def test_verifies_when_the_deployed_source_is_present():
    entry = verify_payload(_payload(["mirat-al-uqul"]), "mirat-al-uqul")
    assert entry["source_key"] == "mirat-al-uqul"


def test_verifies_the_requested_source_among_several():
    payload = _payload(["mirat-al-uqul", "sharh-al-mazandarani"])
    assert verify_payload(payload, "sharh-al-mazandarani")["source_key"] == "sharh-al-mazandarani"


# --- genuine failures ----------------------------------------------------

def test_fails_when_the_deployed_source_is_absent():
    """Another commentary being served is not evidence that this one arrived."""
    payload = _payload(["mirat-al-uqul"])

    with pytest.raises(VerificationError) as error:
        verify_payload(payload, "sharh-al-mazandarani")

    assert "sharh-al-mazandarani" in str(error.value)
    assert "mirat-al-uqul" in str(error.value)  # names what *was* served


def test_fails_when_commentaries_is_empty():
    with pytest.raises(VerificationError, match="empty"):
        verify_payload(_payload([]), "mirat-al-uqul")


def test_fails_when_the_field_is_missing_entirely():
    payload = json.dumps({"public_id": "alkafi-2", "matn_raw": "نص"})

    with pytest.raises(VerificationError, match="no 'commentaries' field"):
        verify_payload(payload, "mirat-al-uqul")


def test_fails_on_invalid_json_rather_than_scanning_text():
    """A truncated or HTML error page must fail as JSON, not by substring luck."""
    truncated = _payload(["mirat-al-uqul"], padding=4000)[:4000]

    with pytest.raises(VerificationError, match="not valid JSON"):
        verify_payload(truncated, "mirat-al-uqul")


def test_fails_when_the_response_is_not_an_object():
    with pytest.raises(VerificationError, match="expected an object"):
        verify_payload(json.dumps([1, 2, 3]), "mirat-al-uqul")


def test_fails_when_commentaries_is_not_a_list():
    payload = json.dumps({"commentaries": {"source_key": "mirat-al-uqul"}})

    with pytest.raises(VerificationError, match="expected a list"):
        verify_payload(payload, "mirat-al-uqul")


# --- choosing which hadith to ask about ----------------------------------

def test_picks_a_hadith_actually_linked_to_the_source(db: Session):
    """Not a hardcoded one — verifying alkafi-2 says nothing about a source
    that never touches alkafi-2."""
    kafi, sharh = _corpus(db)
    _hadith(db, kafi, "alkafi-1", 1)                      # linked to nothing
    second = _hadith(db, kafi, "alkafi-2", 2)
    _commentary(db, sharh, second, "sharh-al-mazandarani", sequence=1)
    db.commit()

    assert pick_linked_public_id(db, "sharh-al-mazandarani") == "alkafi-2"


def test_returns_none_when_no_hadith_is_linked(db: Session):
    """Drives the clean 'nothing to verify' failure rather than a crash."""
    kafi, sharh = _corpus(db)
    hadith = _hadith(db, kafi, "alkafi-1", 1)
    _commentary(db, sharh, hadith, "mirat-al-uqul", sequence=1)
    db.commit()

    assert pick_linked_public_id(db, "sharh-al-mazandarani") is None


def test_ignores_rows_that_are_not_published(db: Session):
    """needs_review rows exist as internal evidence and never reach the API, so
    verifying against one would ask the API for something it will not serve."""
    kafi, sharh = _corpus(db)
    hadith = _hadith(db, kafi, "alkafi-1", 1)
    _commentary(db, sharh, hadith, "mirat-al-uqul", sequence=1, match_status="needs_review")
    db.commit()

    assert pick_linked_public_id(db, "mirat-al-uqul") is None


def test_ignores_unlinked_rows(db: Session):
    kafi, sharh = _corpus(db)
    _hadith(db, kafi, "alkafi-1", 1)
    _commentary(db, sharh, None, "mirat-al-uqul", sequence=1)
    db.commit()

    assert pick_linked_public_id(db, "mirat-al-uqul") is None
