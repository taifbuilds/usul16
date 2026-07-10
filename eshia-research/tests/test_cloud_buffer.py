from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.cloudstore import LocalFileStore
from eshia_research.crawler.client import Checkpoint
from eshia_research.crawler.jobs import (
    _deserialize_batch,
    _serialize_batch,
    _upsert_page_record,
    drain_cloud_buffer,
)
from eshia_research.db import Base, make_engine
from eshia_research.models import Book, Page, Volume


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _record(book_id: str = "10009", volume: int = 1, page: int = 1, text: str = "بسم الله") -> dict:
    return {
        "source_book_id": book_id,
        "volume_number": volume,
        "page_number": page,
        "text_raw": text,
        "html_raw": None,
        "source_url": f"https://lib.eshia.ir/{book_id}/{volume}/{page}",
        "checksum": "deadbeef",
    }


def test_serialize_deserialize_round_trip():
    records = [_record(page=1), _record(page=2, text="الحمد لله")]
    data = _serialize_batch(records)
    assert isinstance(data, bytes)
    assert _deserialize_batch(data) == records


def test_serialize_deserialize_preserves_arabic_text():
    records = [_record(text="بسم الله الرّحمن الرّحيم")]
    data = _serialize_batch(records)
    assert _deserialize_batch(data)[0]["text_raw"] == "بسم الله الرّحمن الرّحيم"


def test_upsert_page_record_creates_book_volume_page_when_missing(db: Session):
    book = Book(source_book_id="10009", title_original="X", title_normalised="X", source_url="u")
    db.add(book)
    db.flush()

    page = _upsert_page_record(db, _record())
    db.commit()

    assert page.id is not None
    assert page.text_raw == "بسم الله"
    assert db.query(Volume).filter(Volume.book_id == book.id, Volume.volume_number == 1).count() == 1


def test_upsert_page_record_is_idempotent(db: Session):
    book = Book(source_book_id="10009", title_original="X", title_normalised="X", source_url="u")
    db.add(book)
    db.flush()

    _upsert_page_record(db, _record(text="version one"))
    db.commit()
    _upsert_page_record(db, _record(text="version two"))
    db.commit()

    pages = db.query(Page).filter(Page.book_id == book.id, Page.volume_number == 1, Page.page_number == 1).all()
    assert len(pages) == 1
    assert pages[0].text_raw == "version two"


def test_upsert_page_record_creates_placeholder_book_for_unknown_id(db: Session):
    page = _upsert_page_record(db, _record(book_id="99999"))
    db.commit()
    assert page.book.source_book_id == "99999"


def test_drain_cloud_buffer_upserts_and_cleans_up(db: Session, tmp_path: Path, monkeypatch):
    store = LocalFileStore(tmp_path / "buffer")
    store.put_bytes("pages/batch1.jsonl.gz", _serialize_batch([_record(page=1), _record(page=2)]))
    drain_checkpoint = Checkpoint(tmp_path / "drain_checkpoint.json")

    stats = drain_cloud_buffer(store, drain_checkpoint, session_factory=lambda: db)

    assert stats == {"batches_seen": 1, "batches_drained": 1, "pages_upserted": 2}
    assert store.list_keys("pages/") == []
    assert drain_checkpoint.is_done("pages/batch1.jsonl.gz")
    assert db.query(Page).count() == 2


def test_drain_cloud_buffer_skips_already_drained_batches(db: Session, tmp_path: Path):
    store = LocalFileStore(tmp_path / "buffer")
    store.put_bytes("pages/batch1.jsonl.gz", _serialize_batch([_record(page=1)]))
    drain_checkpoint = Checkpoint(tmp_path / "drain_checkpoint.json")
    drain_checkpoint.mark_done("pages/batch1.jsonl.gz", checksum="1")

    stats = drain_cloud_buffer(store, drain_checkpoint, session_factory=lambda: db)

    assert stats == {"batches_seen": 1, "batches_drained": 0, "pages_upserted": 0}
    # Already-drained batches are left alone, not re-deleted or re-processed.
    assert store.list_keys("pages/") == ["pages/batch1.jsonl.gz"]
