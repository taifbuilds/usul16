"""Tests for the generation-lattice audit triage tool.

Each test builds a minimal corpus and asserts the primary bucket a violating
edge is classified into, plus the uncapped-export and conflict-person behaviour.
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
    RijalEntry,
    RijalStatement,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.generation_audit import (
    BUCKET_SUSPECT_GENERATION,
    BUCKET_SUSPECT_IDENTITY,
    BUCKET_SUSPECT_TEXT,
    audit_generations,
    write_audit_exports,
)
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

RV = PERSON_RESOLVER_VERSION


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
    person._entry_id = entry.id
    return person


def _gen(db: Session, person: Person, lo: int, hi: int, method: str) -> None:
    db.add(PersonGeneration(person_id=person.id, gen_lo=lo, gen_hi=hi, gen_point=lo,
                            method=method, resolver_version="tabaqat_c1"))
    db.flush()


def _companionship(db: Session, person: Person, imam_raw: str) -> None:
    db.add(RijalStatement(
        entry_id=person._entry_id, source_name="tusi_rijal",
        statement_type="tabaqah_membership", quote_raw="x", quote_normalised="x",
        metadata_json={"imam_raw": imam_raw},
    ))
    db.flush()


def _edge(db: Session, book: Book, seq: int, student: Person, teacher: Person, *,
          student_method: str = "surface_full", teacher_method: str = "surface_full",
          student_ev: dict | None = None, teacher_ev: dict | None = None) -> Chain:
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
    db.add(MentionResolution(chain_node_id=n0.id, person_id=student.id, rank=1, status="resolved",
                             method=student_method, evidence_json=student_ev, resolver_version=RV))
    db.add(MentionResolution(chain_node_id=n1.id, person_id=teacher.id, rank=1, status="resolved",
                             method=teacher_method, evidence_json=teacher_ev, resolver_version=RV))
    db.flush()
    return chain


def test_weak_context_method_violation_is_suspect_identity(db: Session):
    book = _kafi(db)
    student = _person(db, "حماد بن عيسى")
    teacher = _person(db, "ربعي بن عبد الله")
    # Clean anchored generations, but teacher later than student -> violation.
    _gen(db, student, 2, 2, "imam_fixed")
    _gen(db, teacher, 7, 7, "imam_fixed")
    # The teacher identity was a weak Phase-D context pick.
    _edge(db, book, 1, student, teacher, teacher_method="collective_context")
    db.commit()

    report = audit_generations(db)
    assert len(report.violation_edges) == 1
    v = report.violation_edges[0]
    assert v["primary_bucket"] == BUCKET_SUSPECT_IDENTITY
    assert "weak_context_method" in v["signals"]


def test_ambiguous_imam_anchor_violation_is_suspect_generation(db: Session):
    book = _kafi(db)
    student = _person(db, "معاوية بن عمار")
    teacher = _person(db, "أبو بصير")
    # The student was anchored from a bare «الحسن» honorific -> wrongly pinned at
    # layer 2, while the teacher is legitimately later (7). teacher_lo(7) >
    # student_hi(2) is a monotonicity violation, but the untrustworthy factor is
    # the student's ambiguous generation number, not either identity.
    _companionship(db, student, "الحسن (ع)")
    _gen(db, student, 2, 2, "ashab_anchor")
    _gen(db, teacher, 7, 7, "imam_fixed")
    _edge(db, book, 1, student, teacher)
    db.commit()

    report = audit_generations(db)
    assert len(report.violation_edges) == 1
    v = report.violation_edges[0]
    assert v["primary_bucket"] == BUCKET_SUSPECT_GENERATION
    assert "anchor_keyword_ambiguous" in v["signals"]


def test_singleton_strong_anchored_gap_is_suspect_text(db: Session):
    book = _kafi(db)
    student = _person(db, "الحسن بن علي")   # rasm near-twin risk
    teacher = _person(db, "الحسين بن علي")
    _gen(db, student, 2, 2, "imam_fixed")
    _gen(db, teacher, 7, 7, "imam_fixed")
    # single chain, strong method both sides, anchored gens, gap 5 -> text anomaly.
    _edge(db, book, 1, student, teacher)
    db.commit()

    report = audit_generations(db)
    assert len(report.violation_edges) == 1
    assert report.violation_edges[0]["primary_bucket"] == BUCKET_SUSPECT_TEXT


def test_conflict_person_is_reported(db: Session):
    book = _kafi(db)
    student = _person(db, "زرارة بن أعين")
    teacher = _person(db, "محمد بن مسلم")
    _gen(db, student, 5, 5, "imam_fixed")
    _gen(db, teacher, 2, 8, "conflict")  # self-contradictory generation evidence
    _edge(db, book, 1, student, teacher)
    db.commit()

    report = audit_generations(db)
    # The conflict endpoint has no clean interval, so it is NOT a violation edge...
    assert report.violation_edges == []
    # ...but it IS surfaced in the conflict-person list with its partner edge.
    assert report.conflict_person_count == 1
    row = report.conflict_persons[0]
    assert row["person_id"] == teacher.id
    assert row["sample_edges"]


def test_export_is_uncapped(db: Session, tmp_path):
    book = _kafi(db)
    student = _person(db, "حماد بن عيسى")
    teacher = _person(db, "ربعي بن عبد الله")
    _gen(db, student, 2, 2, "imam_fixed")
    _gen(db, teacher, 7, 7, "imam_fixed")
    # 30 violating chains between the same pair — the old 25-sample cap must not apply.
    for seq in range(30):
        _edge(db, book, seq, student, teacher)
    db.commit()

    report = audit_generations(db)
    assert len(report.violation_edges) == 30

    md_path, jsonl_path = write_audit_exports(report, tmp_path)
    assert md_path.exists() and jsonl_path.exists()
    lines = [ln for ln in jsonl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    violation_lines = [ln for ln in lines if '"kind": "violation"' in ln]
    assert len(violation_lines) == 30
