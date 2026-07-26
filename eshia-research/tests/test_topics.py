import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Hadith,
    HadithTopicAssignment,
    ThaqalaynStructureMap,
    Topic,
)
from eshia_research.topics import rebuild_alkafi_topics, topic_hashtag


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _hadith(book_id: int, sequence: int) -> Hadith:
    return Hadith(
        public_id=f"alkafi-topic-{sequence}",
        book_id=book_id,
        sequence_in_book=sequence,
        sequence_in_page=1,
        printed_number=str(sequence),
        volume_start=1,
        volume_end=1,
        page_start=sequence,
        page_end=sequence,
        full_text_raw=f"full {sequence}",
        full_text_normalised=f"full {sequence}",
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw=f"matn {sequence}",
        matn_normalised=f"matn {sequence}",
        source_url=f"https://example.test/{sequence}",
        review_status="pending",
    )


def _mapping(hadith_id: int, remote_id: int) -> ThaqalaynStructureMap:
    return ThaqalaynStructureMap(
        hadith_id=hadith_id,
        source="thaqalayn-api",
        remote_book_id="1",
        remote_id=remote_id,
        volume=1,
        kitab_id="2",
        kitab_name_en="The Book of Knowledge and Ignorance",
        chapter_id=3,
        chapter_name_en="Chapter on Seeking Knowledge",
        number_in_chapter=remote_id,
        mapping_status="matched",
        match_method="windowed_arabic",
        match_score=0.96,
        matcher_version="test",
    )


def test_topic_hashtag_removes_structural_prefixes():
    assert topic_hashtag("The Book of Knowledge and Ignorance") == (
        "#knowledge-and-ignorance"
    )
    assert topic_hashtag("Chapter on Seeking Knowledge") == "#seeking-knowledge"
    assert len(topic_hashtag("Chapter on " + "a very long subject " * 8)) <= 49


def test_rebuild_topics_covers_mapped_and_bounded_gap_hadiths(db: Session):
    book = Book(
        source_book_id="11005",
        title_original="Al-Kafi",
        title_normalised="al-kafi",
        source_url="https://example.test/book",
    )
    db.add(book)
    db.flush()
    hadiths = [_hadith(book.id, sequence) for sequence in (1, 2, 3)]
    db.add_all(hadiths)
    db.flush()
    db.add_all([_mapping(hadiths[0].id, 1), _mapping(hadiths[2].id, 3)])
    db.commit()

    stats = rebuild_alkafi_topics(db)
    db.commit()

    assert stats.hadiths == 3
    assert stats.topics == 3
    assert stats.semantic_topics == 1
    assert stats.assignments == 9
    assert stats.semantic_assignments == 3
    assert stats.directly_placed == 2
    assert stats.inherited_placed == 1
    assert stats.method_counts == {
        "bounded_same_chapter": 1,
        "semantic_structure": 3,
        "structure_matched": 2,
    }
    assert db.scalar(select(func.count()).select_from(Topic)) == 3
    assert (
        db.scalar(select(func.count()).select_from(HadithTopicAssignment)) == 9
    )
    middle_methods = set(
        db.execute(
            select(HadithTopicAssignment.assignment_method).where(
                HadithTopicAssignment.hadith_id == hadiths[1].id
            )
        ).scalars()
    )
    assert middle_methods == {"bounded_same_chapter", "semantic_structure"}

    rerun = rebuild_alkafi_topics(db)
    db.commit()
    assert rerun.to_dict() == stats.to_dict()
    assert db.scalar(select(func.count()).select_from(Topic)) == 3
    assert (
        db.scalar(select(func.count()).select_from(HadithTopicAssignment)) == 9
    )


def test_rebuild_topics_removes_generated_assignments_from_rejected_rows(db: Session):
    book = Book(
        source_book_id="11005",
        title_original="Al-Kafi",
        title_normalised="al-kafi",
        source_url="https://example.test/book",
    )
    db.add(book)
    db.flush()
    rejected = _hadith(book.id, 1)
    rejected.review_status = "rejected_non_hadith_fragment"
    db.add(rejected)
    db.flush()
    stale_topic = Topic(
        slug="al-kafi-stale",
        hashtag="#stale",
        name_en="Stale",
        kind="chapter",
        source="thaqalayn-structure",
        source_key="stale",
        search_text="stale",
    )
    db.add(stale_topic)
    db.flush()
    db.add(
        HadithTopicAssignment(
            hadith_id=rejected.id,
            topic_id=stale_topic.id,
            relevance=100,
            confidence=1.0,
            assignment_method="single_sided_structure",
        )
    )
    db.commit()

    rebuild_alkafi_topics(db)
    db.commit()

    assert db.scalar(select(func.count()).select_from(HadithTopicAssignment)) == 0
    assert db.scalar(select(func.count()).select_from(Topic)) == 0
