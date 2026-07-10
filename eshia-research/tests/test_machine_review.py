import json

import pytest
from sqlalchemy import select
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
    PersonResolutionDecision,
    PersonSurfaceForm,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.machine_review import export_external_review_packet, run_machine_review
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION


@pytest.fixture()
def db(tmp_path) -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session._tmp_path = tmp_path
    try:
        yield session
    finally:
        session.close()


def _book(db: Session) -> Book:
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    return book


def _person(db: Session, name: str, *, kind: str = "individual") -> Person:
    narrator = Narrator(canonical_name_ar=name, canonical_name_norm=norm(name))
    db.add(narrator)
    db.flush()
    entry = RijalEntry(
        narrator_id=narrator.id,
        book_id=1,
        entry_kind="mujam_numbered_entry",
        title_raw=name,
        title_normalised=norm(name),
        canonical_name_raw=name,
        canonical_name_normalised=norm(name),
        text_raw=name,
        text_normalised=norm(name),
    )
    db.add(entry)
    db.flush()
    person = Person(
        canonical_name_ar=name,
        canonical_name_norm=norm(name),
        kind=kind,
        primary_entry_id=entry.id,
    )
    db.add(person)
    db.flush()
    db.add(PersonSurfaceForm(person_id=person.id, form_raw=name, form_norm=norm(name), derivation="full"))
    db.flush()
    return person


def _chain_case(db: Session, book: Book, seq: int, token: str) -> ChainNode:
    hadith = Hadith(
        public_id=f"alkafi-test-{seq}",
        book_id=book.id,
        sequence_in_book=seq,
        sequence_in_page=1,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw=f"علي بن إبراهيم عن {token} قال متن",
        full_text_normalised="x",
        isnad_raw=f"علي بن إبراهيم عن {token}",
        isnad_normalised="x",
        matn_raw="قال متن",
        matn_normalised="x",
        source_url="u",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw)
    db.add(chain)
    db.flush()
    node = ChainNode(
        chain_id=chain.id,
        position=0,
        raw_token=token,
        token_normalised=norm(token),
        node_type="named_narrator",
    )
    db.add(node)
    db.flush()
    return node


def test_machine_review_approves_strong_resolved_case(db: Session):
    book = _book(db)
    person = _person(db, "الحسن بن محبوب")
    node = _chain_case(db, book, 1, "الحسن بن محبوب")
    db.add(
        MentionResolution(
            chain_node_id=node.id,
            person_id=person.id,
            rank=1,
            status="resolved",
            method="surface_full",
            evidence_summary="exact full surface match",
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    db.commit()

    stats = run_machine_review(db, source_book_id="11005", commit=True)

    assert stats.decision_counts["approve_current"] == 1
    decision = db.execute(select(PersonResolutionDecision)).scalar_one()
    assert decision.selected_person_id == person.id
    assert decision.confidence_tier == "high"


def test_machine_review_does_not_hard_flag_conflicted_generation_rows(db: Session):
    book = _book(db)
    student = _person(db, "حماد بن عيسى")
    teacher = _person(db, "ربعي بن عبد الله")
    student_node = _chain_case(db, book, 1, "حماد بن عيسى")
    chain_id = student_node.chain_id
    teacher_node = ChainNode(
        chain_id=chain_id,
        position=1,
        raw_token="ربعي بن عبد الله",
        token_normalised=norm("ربعي بن عبد الله"),
        node_type="named_narrator",
    )
    db.add(teacher_node)
    db.flush()
    db.add_all([
        MentionResolution(
            chain_node_id=student_node.id,
            person_id=student.id,
            rank=1,
            status="resolved",
            method="surface_full",
            resolver_version=PERSON_RESOLVER_VERSION,
        ),
        MentionResolution(
            chain_node_id=teacher_node.id,
            person_id=teacher.id,
            rank=1,
            status="resolved",
            method="surface_full",
            resolver_version=PERSON_RESOLVER_VERSION,
        ),
        PersonGeneration(
            person_id=student.id,
            gen_lo=2,
            gen_hi=2,
            method="conflict",
            resolver_version=PERSON_RESOLVER_VERSION,
        ),
        PersonGeneration(
            person_id=teacher.id,
            gen_lo=7,
            gen_hi=7,
            method="conflict",
            resolver_version=PERSON_RESOLVER_VERSION,
        ),
    ])
    db.commit()

    stats = run_machine_review(db, source_book_id="11005", commit=False)
    assert stats.decision_counts["flag_contradiction"] == 0
    assert stats.decision_counts["approve_current"] == 2


def test_machine_review_approves_kafi_source_prior_with_retained_alternatives(db: Session):
    book = _book(db)
    winner = _person(db, "محمد بن يحيى أبو جعفر العطار")
    alternatives = [_person(db, f"محمد بن يحيى البديل {index}") for index in range(5)]
    node = _chain_case(db, book, 1, "محمد بن يحيى")
    db.add(
        MentionResolution(
            chain_node_id=node.id,
            person_id=winner.id,
            rank=1,
            status="resolved",
            method="kafi_opening_muhammad_yahya",
            evidence_summary="al-Kafi source-opening prior",
            evidence_json={"source_prior": "al_kafi_opening_muhammad_yahya_attar"},
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    for offset, person in enumerate(alternatives, start=2):
        db.add(
            MentionResolution(
                chain_node_id=node.id,
                person_id=person.id,
                rank=offset,
                status="ambiguous",
                method="kafi_opening_muhammad_yahya_alternative",
                evidence_summary="retained audit alternative",
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )
    db.commit()

    stats = run_machine_review(db, source_book_id="11005", commit=True)

    assert stats.decision_counts["approve_current"] == 1
    decision = db.execute(select(PersonResolutionDecision)).scalar_one()
    assert decision.selected_person_id == winner.id
    assert decision.confidence_tier == "medium"


def test_machine_review_exports_ambiguous_case_packet(db: Session):
    book = _book(db)
    p1 = _person(db, "محمد بن مسلم")
    p2 = _person(db, "محمد بن مسلم الثقفي")
    node = _chain_case(db, book, 1, "محمد بن مسلم")
    db.add_all(
        [
            MentionResolution(
                chain_node_id=node.id,
                person_id=p1.id,
                rank=1,
                status="ambiguous",
                method="surface_full",
                evidence_summary="shared surface form",
                resolver_version=PERSON_RESOLVER_VERSION,
            ),
            MentionResolution(
                chain_node_id=node.id,
                person_id=p2.id,
                rank=2,
                status="ambiguous",
                method="surface_full",
                evidence_summary="shared surface form",
                resolver_version=PERSON_RESOLVER_VERSION,
            ),
        ]
    )
    db.commit()
    run_machine_review(db, source_book_id="11005", commit=True)

    stats = export_external_review_packet(
        db,
        output_dir=db._tmp_path,
        source_book_id="11005",
        limit=5,
    )

    markdown = open(stats.markdown_path, encoding="utf-8").read()
    jsonl = open(stats.jsonl_path, encoding="utf-8").read().splitlines()
    assert stats.cases_written == 1
    assert "### Review Question" in markdown
    assert "محمد بن مسلم" in markdown
    assert json.loads(jsonl[0])["target_mention"]["raw_token"] == "محمد بن مسلم"
