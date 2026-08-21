import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.isnad.indexer import rebuild_chain_index
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MashyakhaExpansion,
    MashyakhaPath,
    MentionResolution,
    PersonResolutionDecision,
    PersonResolutionExternalReview,
)


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_rebuild_chain_index_removes_dependent_resolution_rows(db: Session):
    book = Book(
        source_book_id="test-book",
        title_original="Test",
        title_normalised="test",
        source_url="https://example.test/book",
    )
    db.add(book)
    db.flush()
    db.add(
        Hadith(
            public_id="test-1",
            book_id=book.id,
            sequence_in_book=1,
            sequence_in_page=1,
            volume_start=1,
            volume_end=1,
            page_start=1,
            page_end=1,
            full_text_raw="x",
            full_text_normalised="x",
            matn_raw="x",
            matn_normalised="x",
            source_url="https://example.test/hadith",
            isnad_raw="الحسن بن محبوب عن أبي عبد الله عليه السلام",
        )
    )
    db.commit()

    rebuild_chain_index(db, book_ids=[book.id])
    old_node = db.query(ChainNode).order_by(ChainNode.id).first()
    resolution = MentionResolution(
        chain_node_id=old_node.id,
        person_id=None,
        rank=1,
        status="unresolved",
        resolver_version="test",
    )
    decision = PersonResolutionDecision(
        chain_node_id=old_node.id,
        selected_person_id=None,
        decision_type="keep_ambiguous",
        confidence_tier="blocked",
        reviewer="test",
        resolver_version="test",
    )
    db.add_all([resolution, decision])
    db.flush()
    db.add(
        PersonResolutionExternalReview(
            decision_id=decision.id,
            chain_node_id=old_node.id,
            matched_person_id=None,
            case_id="test-case",
            source_label="test",
            verdict="unresolved",
            raw_case_text="test",
        )
    )
    db.commit()

    rebuild_chain_index(db, book_ids=[book.id])

    assert db.query(MentionResolution).count() == 0
    assert db.query(PersonResolutionDecision).count() == 0
    assert db.query(PersonResolutionExternalReview).count() == 0
    assert db.query(ChainNode).count() > 0


def test_rebuild_chain_index_removes_orphaned_mashyakha_proposals(db: Session):
    # A proposal is keyed on chains.id, and a rebuild issues new ids. The
    # materializer only sweeps proposals for chains it can still see, so a
    # survivor here would be evidence pointing at nothing, forever.
    book = Book(
        source_book_id="test-book",
        title_original="Test",
        title_normalised="test",
        source_url="https://example.test/book",
    )
    db.add(book)
    db.flush()
    db.add(
        Hadith(
            public_id="test-1",
            book_id=book.id,
            sequence_in_book=1,
            sequence_in_page=1,
            volume_start=1,
            volume_end=1,
            page_start=1,
            page_end=1,
            full_text_raw="x",
            full_text_normalised="x",
            matn_raw="x",
            matn_normalised="x",
            source_url="https://example.test/hadith",
            isnad_raw="و روى الحسن بن محبوب عن أبي عبد الله عليه السلام",
        )
    )
    path = MashyakhaPath(
        source_book_id="test-book",
        source_key="test",
        source_chapter=1,
        source_url="https://example.test/mashyakha/1",
        source_text_ar="ما كان فيه عن الحسن بن محبوب",
        source_sha256="0" * 64,
    )
    db.add(path)
    db.commit()

    rebuild_chain_index(db, book_ids=[book.id])
    chain = db.query(Chain).order_by(Chain.id).first()
    db.add(MashyakhaExpansion(chain_id=chain.id, mashyakha_path_id=path.id))
    db.commit()
    assert db.query(MashyakhaExpansion).count() == 1

    rebuild_chain_index(db, book_ids=[book.id])

    assert db.query(MashyakhaExpansion).count() == 0
    assert db.query(MashyakhaPath).count() == 1  # the witness itself survives
