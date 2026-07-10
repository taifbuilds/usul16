"""Tests for the person-resolution eval harness.

Each test builds a minimal corpus + gold graph in memory and asserts one of
the four metrics: coverage, the bare-form-leak invariant, generation
monotonicity, and Mu'jam edge corroboration (both a corroborated and a
contradicted edge).
"""

import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Narrator,
    Person,
    PersonGeneration,
    PersonRelation,
    PersonSurfaceForm,
    RijalEntry,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.eval_resolution import (
    DEFAULT_RESOLVER_VERSION,
    WELL_ATTESTED_MIN_OCCURRENCES,
    evaluate_resolution,
)

RV = DEFAULT_RESOLVER_VERSION


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _kafi(db: Session) -> Book:
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    return book


def _person(db: Session, name: str, *, kind: str = "individual") -> Person:
    """A person backed by a Mu'jam narrator entry, plus a full surface form."""
    narrator = Narrator(canonical_name_ar=name, canonical_name_norm=norm(name))
    db.add(narrator)
    db.flush()
    entry = RijalEntry(
        narrator_id=narrator.id, book_id=1, entry_kind="mujam_numbered_entry",
        title_raw=name, title_normalised=norm(name),
        canonical_name_raw=name, canonical_name_normalised=norm(name),
        text_raw=name, text_normalised=norm(name),
    )
    db.add(entry)
    db.flush()
    person = Person(
        canonical_name_ar=name, canonical_name_norm=norm(name), kind=kind,
        primary_entry_id=entry.id,
    )
    db.add(person)
    db.flush()
    db.add(PersonSurfaceForm(
        person_id=person.id, form_raw=name, form_norm=norm(name), derivation="full",
    ))
    db.flush()
    person._narrator_id = narrator.id  # test-only convenience handle
    return person


def _occurrence(db: Session, narrator_id: int, direction: str, related: str) -> None:
    db.add(RijalOccurrence(
        entry_id=1, narrator_id=narrator_id, direction=direction,
        related_name_raw=related, related_name_normalised=norm(related),
        evidence_text_raw=related,
    ))


def _edge_chain(db: Session, book: Book, seq: int, student: Person, teacher: Person,
                *, student_status: str = "resolved", teacher_status: str = "resolved") -> Chain:
    """One hadith/chain with student at position 0 and teacher at position 1."""
    hadith = Hadith(
        public_id=f"k-{seq}", book_id=book.id, sequence_in_book=seq, sequence_in_page=1,
        volume_start=1, volume_end=1, page_start=1, page_end=1,
        full_text_raw="x", full_text_normalised="x", matn_raw="x", matn_normalised="x",
        source_url="u", isnad_raw="x",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    n0 = ChainNode(chain_id=chain.id, position=0, raw_token=student.canonical_name_ar,
                   token_normalised=student.canonical_name_norm, node_type="named_narrator")
    n1 = ChainNode(chain_id=chain.id, position=1, raw_token=teacher.canonical_name_ar,
                   token_normalised=teacher.canonical_name_norm, node_type="named_narrator")
    db.add_all([n0, n1])
    db.flush()
    db.add(MentionResolution(chain_node_id=n0.id, person_id=student.id, rank=1,
                             status=student_status, method="surface_full", resolver_version=RV))
    db.add(MentionResolution(chain_node_id=n1.id, person_id=teacher.id, rank=1,
                             status=teacher_status, method="surface_full", resolver_version=RV))
    db.flush()
    return chain


def test_coverage_counts_statuses(db: Session):
    book = _kafi(db)
    s = _person(db, "محمد بن يحيى العطار")
    t = _person(db, "أحمد بن محمد بن عيسى")
    _edge_chain(db, book, 1, s, t, teacher_status="ambiguous")
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.total_nodes == 2
    assert report.status_counts["resolved"] == 1
    assert report.status_counts["ambiguous"] == 1


def test_bareform_leak_is_flagged(db: Session):
    book = _kafi(db)
    s = _person(db, "الحسن بن محبوب")
    proxy = _person(db, "أحمد بن محمد", kind="bare_form_proxy")
    # A resolved mention pointing at a bare_form_proxy is a hard invariant breach.
    _edge_chain(db, book, 1, s, proxy)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.bareform_leaks == 1
    assert report.bareform_leak_samples[0]["person_id"] == proxy.id


def test_corroborated_edge_counts(db: Session):
    book = _kafi(db)
    student = _person(db, "محمد بن يحيى العطار")
    teacher = _person(db, "أحمد بن محمد بن عيسى")
    # al-Khoei documents (well past the threshold) that the teacher is narrated
    # by the student — plus filler edges so the endpoint is "well attested".
    _occurrence(db, teacher._narrator_id, "narrated_by", "محمد بن يحيى العطار")
    for i in range(WELL_ATTESTED_MIN_OCCURRENCES):
        _occurrence(db, teacher._narrator_id, "narrated_by", f"فلان بن فلان {i}")
    _edge_chain(db, book, 1, student, teacher)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.corroborated == 1
    assert report.contradicted == 0


def test_contradicted_edge_when_wellattested_but_unmatched(db: Session):
    book = _kafi(db)
    student = _person(db, "زرارة بن أعين")
    teacher = _person(db, "أحمد بن محمد بن عيسى")
    # Teacher is well attested, but none of the documented students is ours.
    for i in range(WELL_ATTESTED_MIN_OCCURRENCES + 1):
        _occurrence(db, teacher._narrator_id, "narrated_by", f"شخص آخر {i}")
    _edge_chain(db, book, 1, student, teacher)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.contradicted == 1
    assert report.corroborated == 0


def test_under_documented_edge_is_set_aside(db: Session):
    book = _kafi(db)
    student = _person(db, "زرارة بن أعين")
    teacher = _person(db, "أحمد بن محمد بن عيسى")
    # Only one documented edge -> below threshold -> absence of evidence, not a
    # contradiction.
    _occurrence(db, teacher._narrator_id, "narrated_by", "شخص آخر")
    _edge_chain(db, book, 1, student, teacher)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.contradicted == 0
    assert report.corroborated == 0
    assert report.under_documented == 1


def test_generation_violation_is_flagged(db: Session):
    book = _kafi(db)
    student = _person(db, "حماد بن عيسى")
    teacher = _person(db, "ربعي بن عبد الله")
    # Teacher placed in a strictly LATER generation than the student -> impossible.
    db.add(PersonGeneration(person_id=student.id, gen_lo=2, gen_hi=2, method="imam_fixed",
                            resolver_version=RV))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=7, gen_hi=7, method="imam_fixed",
                            resolver_version=RV))
    _edge_chain(db, book, 1, student, teacher)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.gen_edges_checked == 1
    assert report.gen_violations == 1


def test_same_person_cluster_corroborates_duplicate_identity(db: Session):
    book = _kafi(db)
    documented_student = _person(db, "Ù…Ø­Ù…Ø¯ Ø¨Ù† ÙŠØ­ÙŠÙ‰ Ø§Ù„Ø¹Ø·Ø§Ø±")
    chosen_duplicate = _person(db, "Ù…Ø­Ù…Ø¯ Ø¨Ù† ÙŠØ­ÙŠÙ‰")
    teacher = _person(db, "Ø£Ø­Ù…Ø¯ Ø¨Ù† Ù…Ø­Ù…Ø¯ Ø¨Ù† Ø¹ÙŠØ³Ù‰")

    _occurrence(db, teacher._narrator_id, "narrated_by", "Ù…Ø­Ù…Ø¯ Ø¨Ù† ÙŠØ­ÙŠÙ‰ Ø§Ù„Ø¹Ø·Ø§Ø±")
    for i in range(WELL_ATTESTED_MIN_OCCURRENCES):
        _occurrence(db, teacher._narrator_id, "narrated_by", f"Ø´Ø®Øµ Ø¢Ø®Ø± {i}")

    db.add(PersonRelation(
        person_id=chosen_duplicate.id,
        related_person_id=documented_student.id,
        relation_kind="same_person_as",
        related_name_norm=documented_student.canonical_name_norm,
        source_note="test same-person evidence",
        confidence=90,
    ))
    db.add(PersonRelation(
        person_id=documented_student.id,
        related_person_id=chosen_duplicate.id,
        relation_kind="same_person_as",
        related_name_norm=chosen_duplicate.canonical_name_norm,
        source_note="test same-person evidence",
        confidence=90,
    ))
    _edge_chain(db, book, 1, chosen_duplicate, teacher)
    db.commit()

    report = evaluate_resolution(db, "11005")
    assert report.corroborated == 1
    assert report.contradicted == 0
