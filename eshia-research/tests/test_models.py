import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import Author, Book, BookAuthor, Category, CrawlLog, Hadith, Page, Volume


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_create_category(db: Session):
    category = Category(name_original="فقه", source_url="https://lib.eshia.ir/فقه")
    db.add(category)
    db.commit()

    assert category.id is not None
    assert category.created_at is not None


def test_create_author(db: Session):
    author = Author(name_original="الخوئي", name_normalised="الخوئی")
    db.add(author)
    db.commit()

    assert author.id is not None


def test_create_book_with_relationships(db: Session):
    category = Category(name_original="فقه", source_url="https://lib.eshia.ir/فقه")
    author = Author(name_original="الخوئي", name_normalised="الخوئی")
    db.add_all([category, author])
    db.flush()

    book = Book(
        source_book_id="10009",
        title_original="التنقيح",
        title_normalised="التنقیح",
        source_url="https://lib.eshia.ir/10009",
        category=category,
    )
    book.author_links.append(BookAuthor(author=author, position=0))
    db.add(book)
    db.commit()

    assert book.id is not None
    assert [a.name_original for a in book.authors] == ["الخوئي"]
    assert book.category.name_original == "فقه"


def test_book_authors_preserve_source_order(db: Session):
    book = Book(
        source_book_id="10009",
        title_original="التنقيح",
        title_normalised="التنقیح",
        source_url="https://lib.eshia.ir/10009",
    )
    scholar = Author(name_original="الخوئي، السيد أبوالقاسم", name_normalised="الخوئی، السید ابوالقاسم")
    compiler = Author(name_original="ميرزا علي الغروي", name_normalised="میرزا علی الغروی")
    db.add_all([book, scholar, compiler])
    db.flush()

    book.author_links.append(BookAuthor(author=scholar, position=0))
    book.author_links.append(BookAuthor(author=compiler, position=1))
    db.commit()

    assert [a.name_original for a in book.authors] == ["الخوئي، السيد أبوالقاسم", "ميرزا علي الغروي"]


def test_clearing_author_links_does_not_delete_the_authors_themselves(db: Session):
    book = Book(
        source_book_id="10009",
        title_original="التنقيح",
        title_normalised="التنقیح",
        source_url="https://lib.eshia.ir/10009",
    )
    author = Author(name_original="الخوئي", name_normalised="الخوئی")
    db.add_all([book, author])
    db.flush()
    book.author_links.append(BookAuthor(author=author, position=0))
    db.commit()

    book.author_links.clear()
    db.commit()

    assert book.authors == []
    assert db.get(Author, author.id) is not None


def test_create_volume_and_page(db: Session):
    book = Book(
        source_book_id="10009",
        title_original="التنقيح",
        title_normalised="التنقیح",
        source_url="https://lib.eshia.ir/10009",
    )
    db.add(book)
    db.flush()

    volume = Volume(book_id=book.id, volume_number=1)
    db.add(volume)
    db.flush()

    page = Page(
        book_id=book.id,
        volume_id=volume.id,
        volume_number=1,
        page_number=1,
        text_raw="بسم الله",
        source_url="https://lib.eshia.ir/10009/1/1",
        checksum="deadbeef",
    )
    db.add(page)
    db.commit()

    assert page.id is not None
    assert page.book.title_original == "التنقيح"


def test_page_unique_constraint_per_book_volume_page(db: Session):
    book = Book(
        source_book_id="10009",
        title_original="التنقيح",
        title_normalised="التنقیح",
        source_url="https://lib.eshia.ir/10009",
    )
    db.add(book)
    db.flush()

    db.add(Page(book_id=book.id, volume_number=1, page_number=1, source_url="u1", checksum="a"))
    db.commit()

    db.add(Page(book_id=book.id, volume_number=1, page_number=1, source_url="u2", checksum="b"))
    with pytest.raises(Exception):
        db.commit()


def test_create_crawl_log(db: Session):
    log = CrawlLog(url="https://lib.eshia.ir/26395", status="ok", http_status=200, checksum="abc123")
    db.add(log)
    db.commit()

    assert log.id is not None
    assert log.scraped_at is not None


def test_create_hadith(db: Session):
    book = Book(
        source_book_id="11005",
        title_original="al-kafi",
        title_normalised="al-kafi",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add(book)
    db.flush()

    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=10,
        text_raw="1- chain said: matn",
        source_url="https://lib.eshia.ir/11005/1/10",
        checksum="abc",
    )
    db.add(page)
    db.flush()

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
        full_text_raw="chain said: matn",
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

    assert hadith.id is not None
    assert hadith.book.source_book_id == "11005"
    assert hadith.page_start_ref.page_number == 10
