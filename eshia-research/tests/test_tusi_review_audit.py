import json

from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.isnad.review_audit import build_tusi_chain_review, write_tusi_chain_review
from eshia_research.models import Book, Chain, ChainNode, Hadith


def _chain(db: Session, source_book_id: str, public_id: str, raw: str, flags: str) -> None:
    book = db.query(Book).filter_by(source_book_id=source_book_id).one_or_none()
    if book is None:
        book = Book(
            source_book_id=source_book_id,
            title_original=source_book_id,
            title_normalised=source_book_id,
            source_url=f"https://lib.eshia.ir/{source_book_id}",
        )
        db.add(book)
        db.flush()
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        sequence_in_book=db.query(Hadith).filter_by(book_id=book.id).count() + 1,
        sequence_in_page=1,
        page_start=1,
        page_end=1,
        full_text_raw=raw,
        full_text_normalised=raw,
        isnad_raw=raw,
        isnad_normalised=raw,
        matn_raw="متن",
        matn_normalised="متن",
        source_url=f"https://lib.eshia.ir/{source_book_id}/1/1",
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(
        hadith_id=hadith.id,
        chain_number=1,
        raw_isnad=raw,
        flags=flags,
        review_status="needs_review",
    )
    db.add(chain)
    db.flush()
    db.add(
        ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token=raw,
            token_normalised=raw,
            node_type="named_narrator",
        )
    )


def test_tusi_review_ledger_is_exhaustive_and_preserves_overlap(tmp_path):
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        _chain(
            db,
            "10083",
            "tahdhib-1",
            "محمد بسم الله الرحمن الرحيم بن أحمد",
            "multi_route,no_imam_terminal,suspicious_token",
        )
        _chain(db, "11002", "istibsar-1", "محمد عن أحمد", "multi_route")
        db.flush()

        report = build_tusi_chain_review(db, audit_date="2026-10-05")
    finally:
        db.close()

    assert report["summary"]["suspicious_chains"] == 1
    assert report["summary"]["multi_route_chains"] == 2
    assert report["suspicious_cases"][0]["classification"] == "suspect_text"
    assert report["multi_route_cases"][0]["classification"] == (
        "multi_route_with_suspicious_overlap"
    )

    json_path = tmp_path / "review.json"
    markdown_path = tmp_path / "review.md"
    write_tusi_chain_review(report, json_path, markdown_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["schema_version"] == (
        "tusi-chain-review-v1"
    )
    assert "tahdhib-1" in markdown_path.read_text(encoding="utf-8")
