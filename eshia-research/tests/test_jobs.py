import threading

import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.crawler.jobs import (
    category_name_from_url,
    get_or_create_category_by_name,
    upsert_book_from_entry,
)
from eshia_research.crawler.parser import CategoryBookEntry
from eshia_research.db import Base, make_engine
from eshia_research.models import Category


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_category_name_from_simple_url():
    assert category_name_from_url("https://lib.eshia.ir/فقه") == "فقه"


def test_category_name_returns_none_for_sitewide_all():
    # Regression: the sitewide "/all" listing (every book on the site) has
    # no real topical category — it must not be mistaken for one named "all".
    assert category_name_from_url("https://lib.eshia.ir/all") is None


def test_category_name_strips_all_suffix():
    # Regression: naively taking the last path segment named every "/all"
    # category "all" instead of its actual topic.
    assert category_name_from_url("https://lib.eshia.ir/فقه/all") == "فقه"
    assert category_name_from_url("https://lib.eshia.ir/اصول_فقه/all") == "اصول_فقه"


def test_category_name_strips_authors_suffix():
    assert category_name_from_url("https://lib.eshia.ir/فقه/authors") == "فقه"


def test_category_name_keeps_subcategory_segment():
    assert category_name_from_url("https://lib.eshia.ir/فقه/رسائل_عملیه") == "رسائل_عملیه"


def test_category_name_handles_trailing_slash():
    assert category_name_from_url("https://lib.eshia.ir/فقه/all/") == "فقه"


def _entry(book_id: str = "10009") -> CategoryBookEntry:
    return CategoryBookEntry(
        source_book_id=book_id,
        title_original="التنقيح",
        source_url=f"https://lib.eshia.ir/{book_id}",
        author_name=None,
        author_url=None,
        volume_count=1,
    )


def test_upsert_book_assigns_given_category(db: Session):
    category = Category(name_original="فقه", source_url="https://lib.eshia.ir/فقه")
    db.add(category)
    db.flush()

    book = upsert_book_from_entry(db, _entry(), category)

    assert book.category_id == category.id


def test_upsert_book_with_no_category_does_not_clobber_existing_assignment(db: Session):
    # Regression: crawling the sitewide /all completeness backstop (which
    # has no real category) must not erase a book's existing category from
    # an earlier, more specific crawl.
    category = Category(name_original="فقه", source_url="https://lib.eshia.ir/فقه")
    db.add(category)
    db.flush()
    upsert_book_from_entry(db, _entry(), category)

    book = upsert_book_from_entry(db, _entry(), None)

    assert book.category_id == category.id


def test_upsert_book_with_no_category_leaves_new_book_uncategorized(db: Session):
    book = upsert_book_from_entry(db, _entry(), None)
    assert book.category_id is None


def test_get_or_create_category_by_name_is_idempotent(db: Session):
    first = get_or_create_category_by_name(db, "فقه فتوايي")
    second = get_or_create_category_by_name(db, "فقه فتوايي")
    assert first.id == second.id
    assert db.query(Category).filter(Category.name_original == "فقه فتوايي").count() == 1


def test_get_or_create_category_by_name_is_safe_under_concurrent_creation(tmp_path):
    # Regression: a real 1500-book concurrent enrichment run produced
    # duplicate Category rows for the same new subject name because two
    # threads' "does this exist?" checks both passed before either
    # committed. Drives many real threads against a real file-backed SQLite
    # DB (in-memory DBs aren't shared across connections) racing to create
    # the same brand-new category name, and asserts only one row survives.
    engine = make_engine(f"sqlite:///{tmp_path / 'race.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def worker():
        db = session_factory()
        try:
            get_or_create_category_by_name(db, "علوم جدید مشترک")
        finally:
            db.close()

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    verify_db = session_factory()
    try:
        matches = verify_db.query(Category).filter(Category.name_original == "علوم جدید مشترک").all()
        assert len(matches) == 1
    finally:
        verify_db.close()
