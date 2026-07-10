import gzip
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.cloudstore import LocalFileStore
from eshia_research.config import Settings
from eshia_research.crawler.client import Checkpoint
from eshia_research.crawler.jobs import (
    _fetch_and_store_page,
    _serialize_batch,
    _upsert_page_record,
    archive_html,
    drain_cloud_buffer,
    html_archive_key,
    resolve_html_store,
)
from eshia_research.db import Base, make_engine
from eshia_research.models import Book, Page, Volume

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
SAMPLE_PAGE_URL = "https://lib.eshia.ir/10009/1/1"
SAMPLE_PAGE_LAST_PAGE_URL = "https://lib.eshia.ir/10009/1/370"


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _record(book_id: str = "10009", volume: int = 1, page: int = 1, html: str | None = "<html>x</html>") -> dict:
    return {
        "source_book_id": book_id,
        "volume_number": volume,
        "page_number": page,
        "text_raw": "بسم الله",
        "html_raw": html,
        "source_url": f"https://lib.eshia.ir/{book_id}/{volume}/{page}",
        "checksum": "deadbeef",
    }


def test_html_archive_key_is_deterministic():
    assert html_archive_key("10009", 1, 5) == "html/10009/1/5.html.gz"


def test_html_archive_key_falls_back_to_zero_for_missing_volume_or_page():
    assert html_archive_key("10009", None, None) == "html/10009/0/0.html.gz"


def test_archive_html_round_trips_through_gzip(tmp_path: Path):
    store = LocalFileStore(tmp_path / "archive")
    archive_html(store, "10009", 1, 5, "<html>محتوى الصفحة</html>")

    raw = store.get_bytes("html/10009/1/5.html.gz")
    assert gzip.decompress(raw).decode("utf-8") == "<html>محتوى الصفحة</html>"


def test_resolve_html_store_returns_none_when_disabled():
    settings = Settings(store_raw_html_r2=False)
    assert resolve_html_store(settings, None) is None


def test_resolve_html_store_prefers_explicit_store_over_settings(tmp_path: Path):
    settings = Settings(store_raw_html_r2=False)
    explicit = LocalFileStore(tmp_path / "explicit")
    assert resolve_html_store(settings, explicit) is explicit


def test_upsert_page_record_archives_html_instead_of_storing_column(db: Session, tmp_path: Path):
    store = LocalFileStore(tmp_path / "archive")
    book = Book(source_book_id="10009", title_original="X", title_normalised="X", source_url="u")
    db.add(book)
    db.flush()

    page = _upsert_page_record(db, _record(html="<html>raw page html</html>"), html_store=store)
    db.commit()

    assert page.html_raw is None
    archived = gzip.decompress(store.get_bytes("html/10009/1/1.html.gz")).decode("utf-8")
    assert archived == "<html>raw page html</html>"


def test_upsert_page_record_without_html_store_keeps_old_column_behaviour(db: Session):
    book = Book(source_book_id="10009", title_original="X", title_normalised="X", source_url="u")
    db.add(book)
    db.flush()

    page = _upsert_page_record(db, _record(html="<html>raw page html</html>"))
    db.commit()

    assert page.html_raw == "<html>raw page html</html>"


def test_drain_cloud_buffer_archives_html_when_store_raw_html_r2_enabled(db: Session, tmp_path: Path):
    store = LocalFileStore(tmp_path / "buffer")
    store.put_bytes("pages/batch1.jsonl.gz", _serialize_batch([_record(page=1, html="<html>p1</html>")]))
    drain_checkpoint = Checkpoint(tmp_path / "drain_checkpoint.json")
    settings = Settings(store_raw_html_r2=True)

    drain_cloud_buffer(store, drain_checkpoint, session_factory=lambda: db, settings=settings)

    page = db.query(Page).one()
    assert page.html_raw is None
    archived = gzip.decompress(store.get_bytes("html/10009/1/1.html.gz")).decode("utf-8")
    assert archived == "<html>p1</html>"


def test_drain_cloud_buffer_keeps_html_in_db_when_store_raw_html_r2_disabled(db: Session, tmp_path: Path):
    store = LocalFileStore(tmp_path / "buffer")
    store.put_bytes("pages/batch1.jsonl.gz", _serialize_batch([_record(page=1, html="<html>p1</html>")]))
    drain_checkpoint = Checkpoint(tmp_path / "drain_checkpoint.json")
    settings = Settings(store_raw_html_r2=False)

    drain_cloud_buffer(store, drain_checkpoint, session_factory=lambda: db, settings=settings)

    page = db.query(Page).one()
    assert page.html_raw == "<html>p1</html>"
    assert store.list_keys("html/") == []


# --- Regression: resuming a crawl must not lose pagination info ----------
#
# A checkpoint hit means "don't re-fetch this page", not "this volume has no
# more pages" — but _fetch_and_store_page used to return no ParsedPage at
# all on a checkpoint hit, so crawl_book/crawl_book_concurrent/
# crawl_full_library had no way to learn a volume's last-page number for any
# volume whose page 1 happened to already be checkpointed from an earlier
# run. That silently truncated resumed crawls to just their already-fetched
# pages. The fix: re-derive pagination from cached HTML (DB column or R2
# archive) instead of giving up.


def _seed_page(db: Session, html_raw: str | None) -> Page:
    book = Book(source_book_id="10009", title_original="X", title_normalised="X", source_url="u")
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
        html_raw=html_raw,
        source_url=SAMPLE_PAGE_URL,
        checksum="x",
    )
    db.add(page)
    db.flush()
    return page


def test_checkpoint_hit_recovers_pagination_from_db_html_raw(db: Session, tmp_path: Path):
    _seed_page(db, html_raw=(SAMPLES_DIR / "page_text_sample.html").read_text(encoding="utf-8"))
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    checkpoint.mark_done(SAMPLE_PAGE_URL, checksum="x")

    page, parsed = _fetch_and_store_page(db, SAMPLE_PAGE_URL, client=None, checkpoint=checkpoint, settings=Settings())

    assert page is not None
    assert parsed is not None
    assert parsed.last_page_url == SAMPLE_PAGE_LAST_PAGE_URL


def test_checkpoint_hit_skips_cache_lookup_entirely_when_pagination_not_needed(db: Session, tmp_path: Path):
    # Regression: callers that discard the returned ParsedPage anyway (e.g.
    # crawl_full_library's remaining-pages phase) used to still pay for a
    # cache lookup + re-parse on every single skip — on a crawl resumed
    # after ~70k pages were already fetched, that made re-skipping them
    # almost as slow as fetching them the first time. need_pagination=False
    # must skip the lookup outright, not just discard its result.
    _seed_page(db, html_raw=(SAMPLES_DIR / "page_text_sample.html").read_text(encoding="utf-8"))
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    checkpoint.mark_done(SAMPLE_PAGE_URL, checksum="x")

    page, parsed = _fetch_and_store_page(
        db, SAMPLE_PAGE_URL, client=None, checkpoint=checkpoint, settings=Settings(), need_pagination=False
    )

    assert page is not None
    assert parsed is None


def test_checkpoint_hit_recovers_pagination_from_r2_archive_when_db_column_empty(db: Session, tmp_path: Path):
    _seed_page(db, html_raw=None)
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    checkpoint.mark_done(SAMPLE_PAGE_URL, checksum="x")
    store = LocalFileStore(tmp_path / "archive")
    archive_html(store, "10009", 1, 1, (SAMPLES_DIR / "page_text_sample.html").read_text(encoding="utf-8"))

    page, parsed = _fetch_and_store_page(
        db, SAMPLE_PAGE_URL, client=None, checkpoint=checkpoint, settings=Settings(), html_store=store
    )

    assert page is not None
    assert parsed is not None
    assert parsed.last_page_url == SAMPLE_PAGE_LAST_PAGE_URL


def test_checkpoint_hit_with_no_cached_html_anywhere_falls_back_to_no_pagination(db: Session, tmp_path: Path):
    _seed_page(db, html_raw=None)
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    checkpoint.mark_done(SAMPLE_PAGE_URL, checksum="x")

    page, parsed = _fetch_and_store_page(db, SAMPLE_PAGE_URL, client=None, checkpoint=checkpoint, settings=Settings())

    assert page is not None
    assert parsed is None
