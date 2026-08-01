"""Shipping commentary rows between two copies of the corpus."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.commentary.transfer import (
    build_manifest,
    export_delta,
    import_delta,
    read_delta,
    validate_delta,
    verify_target,
    write_delta,
)
from eshia_research.db import Base
from eshia_research.models import Book, Hadith, HadithCommentary
from eshia_research.normalise import normalise_arabic_persian

SOURCE_KEY = "mirat-al-uqul"


def _session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _corpus(db: Session, public_ids: list[str], *, id_offset: int = 0) -> Book:
    """A corpus copy. `id_offset` shifts hadith ids so the two copies disagree."""
    kafi = Book(
        source_book_id="11005", title_original="الكافي", title_normalised="الكافي",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add(kafi)
    db.flush()
    for index, public_id in enumerate(public_ids):
        text = f"نص الحديث رقم {index}"
        db.add(Hadith(
            id=1000 + id_offset + index,
            public_id=public_id, book_id=kafi.id, sequence_in_book=index + 1,
            sequence_in_page=1, printed_number=str(index + 1), volume_start=1, volume_end=1,
            page_start=1, page_end=1, section_title="باب", full_text_raw=text,
            full_text_normalised=normalise_arabic_persian(text), isnad_raw=None,
            isnad_normalised=None, matn_raw=text, matn_normalised=normalise_arabic_persian(text),
            source_url="https://lib.eshia.ir/11005/1/1", extraction_method="test",
            extraction_confidence=100, review_status="approved",
        ))
    db.commit()
    return kafi


def _commentary_book(db: Session) -> Book:
    book = Book(
        source_book_id="71429", title_original="مرآة العقول", title_normalised="مرآة العقول",
        source_url="https://lib.eshia.ir/71429/1/1",
    )
    db.add(book)
    db.flush()
    return book


def _add_row(db: Session, book: Book, sequence: int, public_id: str | None, text: str) -> None:
    hadith_id = None
    if public_id:
        hadith_id = db.query(Hadith).filter_by(public_id=public_id).one().id
    db.add(HadithCommentary(
        commentary_book_id=book.id, hadith_id=hadith_id, source_key=SOURCE_KEY,
        source_sequence=sequence, source_label=f"الحديث {sequence}", section_title="باب",
        report_raw="report", report_normalised="report", commentary_raw=text,
        commentary_normalised=text, volume_start=1, volume_end=1, page_start=10, page_end=10,
        source_url="https://lib.eshia.ir/71429/1/10", match_status="matched",
        match_method="text_only", match_score=1.0, matcher_version="test_v1",
        match_evidence_json={"note": "test"},
    ))
    db.commit()


def test_rows_travel_by_public_id_not_hadith_id():
    """The whole point: the two copies number their hadiths differently.

    A delta carrying raw `hadith_id` would attach commentary to the wrong
    report on the target, silently.
    """
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-2", "شرح الحديث الثاني")

    delta = export_delta(source, SOURCE_KEY)
    assert delta["rows"][0]["public_id"] == "alkafi-2"
    assert "hadith_id" not in delta["rows"][0]

    # The target numbers the same hadiths 500 higher.
    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2"], id_offset=500)
    import_delta(target, delta)

    row = target.query(HadithCommentary).one()
    linked = target.query(Hadith).filter_by(id=row.hadith_id).one()
    assert linked.public_id == "alkafi-2"


def test_only_changed_rows_are_exported():
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2", "alkafi-3"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح أول")
    _add_row(source, book, 2, "alkafi-2", "شرح ثان")

    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2", "alkafi-3"], id_offset=500)
    import_delta(target, export_delta(source, SOURCE_KEY))

    # One row's text changes; a third passage appears.
    source.query(HadithCommentary).filter_by(source_sequence=2).one().commentary_raw = "شرح منقح"
    source.commit()
    _add_row(source, book, 3, "alkafi-3", "شرح ثالث")

    delta = export_delta(source, SOURCE_KEY, build_manifest(target, SOURCE_KEY))

    assert delta["summary"]["unchanged"] == 1
    assert sorted(r["source_sequence"] for r in delta["rows"]) == [2, 3]


def test_a_passage_moving_to_another_hadith_ships():
    """Same text, different target — the move must not look unchanged."""
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح")

    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2"], id_offset=500)
    import_delta(target, export_delta(source, SOURCE_KEY))

    row = source.query(HadithCommentary).one()
    row.hadith_id = source.query(Hadith).filter_by(public_id="alkafi-2").one().id
    source.commit()

    delta = export_delta(source, SOURCE_KEY, build_manifest(target, SOURCE_KEY))
    assert len(delta["rows"]) == 1

    import_delta(target, delta)
    moved = target.query(HadithCommentary).one()
    assert target.query(Hadith).filter_by(id=moved.hadith_id).one().public_id == "alkafi-2"


def test_import_refuses_a_delta_referencing_unknown_hadiths():
    """Better to abort than attach commentary to nothing."""
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-99"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-99", "شرح")
    delta = export_delta(source, SOURCE_KEY)

    target = _session()
    _corpus(target, ["alkafi-1"], id_offset=500)  # no alkafi-99 here

    assert validate_delta(target, delta) == ["alkafi-99"]
    with pytest.raises(ValueError, match="do not exist"):
        import_delta(target, delta)
    assert target.query(HadithCommentary).count() == 0


def test_nothing_is_written_when_validation_fails_midway():
    """One bad row must not leave the good ones half-applied."""
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2", "alkafi-3"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح أول")
    _add_row(source, book, 2, "alkafi-3", "شرح ثالث")
    delta = export_delta(source, SOURCE_KEY)

    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2"], id_offset=500)  # alkafi-3 absent

    with pytest.raises(ValueError):
        import_delta(target, delta)
    assert target.query(HadithCommentary).count() == 0


def test_dry_run_writes_nothing():
    source = _session()
    _corpus(source, ["alkafi-1"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح")

    target = _session()
    _corpus(target, ["alkafi-1"], id_offset=500)
    import_delta(target, export_delta(source, SOURCE_KEY), dry_run=True)

    assert target.query(HadithCommentary).count() == 0


def test_removed_passages_are_deleted_on_the_target():
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح أول")
    _add_row(source, book, 2, "alkafi-2", "شرح ثان")

    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2"], id_offset=500)
    import_delta(target, export_delta(source, SOURCE_KEY))
    assert target.query(HadithCommentary).count() == 2

    source.query(HadithCommentary).filter_by(source_sequence=2).delete()
    source.commit()

    delta = export_delta(source, SOURCE_KEY, build_manifest(target, SOURCE_KEY))
    assert delta["removed_source_sequences"] == [2]

    stats = import_delta(target, delta)
    assert stats.deleted == 1
    assert target.query(HadithCommentary).count() == 1


def test_target_without_the_commentary_book_gets_one():
    """A first deployment has never seen this work."""
    source = _session()
    _corpus(source, ["alkafi-1"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح")

    target = _session()
    _corpus(target, ["alkafi-1"], id_offset=500)
    assert target.query(Book).filter_by(source_book_id="71429").count() == 0

    import_delta(target, export_delta(source, SOURCE_KEY))

    created = target.query(Book).filter_by(source_book_id="71429").one()
    assert created.title_original == "مرآة العقول"
    assert verify_target(target, SOURCE_KEY) == {
        "rows": 1, "matched": 1, "linked_hadiths": 1,
    }


def test_two_passages_cannot_both_claim_one_hadith():
    """`(source_key, hadith_id)` is unique; a re-index moving a passage onto a
    hadith another passage holds must detach the incumbent, not crash."""
    source = _session()
    _corpus(source, ["alkafi-1", "alkafi-2"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح أول")
    _add_row(source, book, 2, "alkafi-2", "شرح ثان")

    target = _session()
    _corpus(target, ["alkafi-1", "alkafi-2"], id_offset=500)
    import_delta(target, export_delta(source, SOURCE_KEY))

    # Passage 2 now explains alkafi-1; passage 1 loses its link.
    source.query(HadithCommentary).filter_by(source_sequence=1).one().hadith_id = None
    source.query(HadithCommentary).filter_by(source_sequence=2).one().hadith_id = (
        source.query(Hadith).filter_by(public_id="alkafi-1").one().id
    )
    source.commit()

    import_delta(target, export_delta(source, SOURCE_KEY, build_manifest(target, SOURCE_KEY)))

    rows = {r.source_sequence: r for r in target.query(HadithCommentary).all()}
    assert rows[1].hadith_id is None
    assert target.query(Hadith).filter_by(id=rows[2].hadith_id).one().public_id == "alkafi-1"


def test_delta_round_trips_through_a_file(tmp_path):
    source = _session()
    _corpus(source, ["alkafi-1"])
    book = _commentary_book(source)
    _add_row(source, book, 1, "alkafi-1", "شرح فيه نص عربي")

    path = str(tmp_path / "delta.json.gz")
    write_delta(export_delta(source, SOURCE_KEY), path)

    target = _session()
    _corpus(target, ["alkafi-1"], id_offset=500)
    import_delta(target, read_delta(path))

    assert target.query(HadithCommentary).one().commentary_raw == "شرح فيه نص عربي"


def test_unrecognised_format_is_rejected(tmp_path):
    import gzip, json

    path = str(tmp_path / "bad.json.gz")
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump({"format": "something-else", "rows": []}, handle)

    with pytest.raises(ValueError, match="Unrecognised delta format"):
        read_delta(path)
