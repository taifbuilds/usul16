import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    CollectiveRoster,
    Person,
    PersonEntryLink,
    PersonRelation,
    PersonSurfaceForm,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.identity_links import materialize_same_person_relations
from eshia_research.rijal.person_builder import build_person_layer


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def norm(text: str) -> str:
    return normalise_arabic_persian(text)


def add_entry(db: Session, book: Book, number: int, name: str, text: str = "") -> RijalEntry:
    entry = RijalEntry(
        book_id=book.id,
        entry_kind="mujam_numbered_entry",
        entry_number=number,
        title_raw=name,
        title_normalised=norm(name),
        canonical_name_raw=name,
        canonical_name_normalised=norm(name),
        text_raw=text or name,
        text_normalised=norm(text or name),
    )
    db.add(entry)
    db.flush()
    return entry


@pytest.fixture()
def seeded(db: Session) -> Session:
    book = Book(
        source_book_id="14036",
        title_original="mujam",
        title_normalised="mujam",
        source_url="https://lib.eshia.ir/14036",
    )
    db.add(book)
    db.flush()
    add_entry(db, book, 1, "أحمد بن محمد بن عيسى الأشعري")
    add_entry(db, book, 2, "أحمد بن محمد بن خالد البرقي")
    add_entry(
        db,
        book,
        3,
        "أحمد بن محمد",
        "أقول: هذا العنوان مشترك بين جماعة، والتمييز إنما يكون بالراوي والمروي عنه.",
    )
    add_entry(db, book, 4, "علي بن إبراهيم بن هاشم", "متحد مع من تقدم.")
    # Real Mu'jam titles carry kunya/nisba tails; the plain nasab must still match.
    add_entry(db, book, 5, "إبراهيم بن هاشم أبو إسحاق القمي")
    add_entry(db, book, 6, "الحسن بن محبوب")
    add_entry(db, book, 7, "محمد بن يحيى العطار")
    build_person_layer(db)
    return db


def person_by_name(db: Session, name: str) -> Person:
    return db.execute(
        select(Person).where(Person.canonical_name_norm == norm(name))
    ).scalar_one()


def test_persons_seeded_one_per_entry_plus_masumin(seeded: Session):
    persons = seeded.execute(select(Person)).scalars().all()
    mujam = [p for p in persons if p.origin == "mujam_entry"]
    masum = [p for p in persons if p.kind == "masum"]
    assert len(mujam) == 7
    assert len(masum) == 14


def test_bare_form_entry_marked_proxy_with_evidence_links(seeded: Session):
    bare = person_by_name(seeded, "أحمد بن محمد")
    assert bare.kind == "bare_form_proxy"
    links = seeded.execute(
        select(PersonEntryLink).where(
            PersonEntryLink.entry_id == bare.primary_entry_id,
            PersonEntryLink.link_type == "bare_form_evidence",
        )
    ).scalars().all()
    linked_persons = {
        seeded.get(Person, link.person_id).canonical_name_norm for link in links
    }
    assert norm("احمد بن محمد بن عیسی الاشعری") in linked_persons
    assert norm("احمد بن محمد بن خالد البرقی") in linked_persons


def test_full_named_persons_stay_individual(seeded: Session):
    assert person_by_name(seeded, "أحمد بن محمد بن عيسى الأشعري").kind == "individual"


def test_father_relation_uniquely_matched(seeded: Session):
    ali = person_by_name(seeded, "علي بن إبراهيم بن هاشم")
    relation = seeded.execute(
        select(PersonRelation).where(
            PersonRelation.person_id == ali.id, PersonRelation.relation_kind == "father"
        )
    ).scalar_one()
    assert relation.related_name_norm == norm("ابراهیم بن هاشم")
    father = seeded.get(Person, relation.related_person_id)
    assert father.canonical_name_norm == norm("ابراهیم بن هاشم ابو اسحاق القمی")


def test_tamyiz_cross_references_captured(seeded: Session):
    ali = person_by_name(seeded, "علي بن إبراهيم بن هاشم")
    link = seeded.execute(
        select(PersonEntryLink).where(
            PersonEntryLink.person_id == ali.id,
            PersonEntryLink.link_type == "tamyiz_discussion",
        )
    ).scalar_one()
    assert norm("متحد مع") in link.evidence_quote


def test_surface_forms_shared_count_marks_ambiguity(seeded: Session):
    # Both Ibn Isa and al-Barqi (and the bare entry itself) claim «احمد بن محمد».
    rows = seeded.execute(
        select(PersonSurfaceForm).where(
            PersonSurfaceForm.form_norm == norm("احمد بن محمد")
        )
    ).scalars().all()
    assert len(rows) >= 3
    assert all(row.shared_count == len(rows) for row in rows)


def test_masum_kunya_forms_are_shared_between_claimants(seeded: Session):
    # «ابو جعفر ع» belongs to both al-Baqir and al-Jawad — ambiguity preserved.
    rows = seeded.execute(
        select(PersonSurfaceForm).where(
            PersonSurfaceForm.form_norm == norm("ابو جعفر ع")
        )
    ).scalars().all()
    assert len(rows) == 2
    genitive = seeded.execute(
        select(PersonSurfaceForm).where(
            PersonSurfaceForm.form_norm == norm("ابی عبد الله علیه السلام")
        )
    ).scalars().all()
    assert len(genitive) == 2  # al-Husayn and al-Sadiq


def test_idda_roster_seeded_and_member_matched(seeded: Session):
    rows = seeded.execute(
        select(CollectiveRoster).where(
            CollectiveRoster.keyed_by_norm == norm("احمد بن محمد بن عیسی")
        )
    ).scalars().all()
    assert len(rows) == 5
    attar = next(r for r in rows if r.member_name_norm == norm("محمد بن یحیی العطار"))
    member = seeded.get(Person, attar.member_person_id)
    assert member.canonical_name_norm == norm("محمد بن یحیی العطار")


def test_rebuild_is_idempotent(seeded: Session):
    first = seeded.execute(select(Person)).scalars().all()
    stats = build_person_layer(seeded)
    second = seeded.execute(select(Person)).scalars().all()
    assert len(first) == len(second) == stats["persons"]


def test_same_person_links_materialized_from_next_entry_reference(db: Session):
    book = Book(
        source_book_id="14036",
        title_original="mujam",
        title_normalised="mujam",
        source_url="https://lib.eshia.ir/14036",
    )
    db.add(book)
    db.flush()
    add_entry(db, book, 1, "زيد بن علي", "متحد مع ما بعده.")
    add_entry(db, book, 2, "زيد بن علي الكوفي")
    build_person_layer(db)

    stats = materialize_same_person_relations(db, commit=False)

    assert stats.pairs_created == 1
    assert stats.relation_rows_created == 2
    zayd = person_by_name(db, "زيد بن علي")
    kufi = person_by_name(db, "زيد بن علي الكوفي")
    rows = db.execute(
        select(PersonRelation).where(PersonRelation.relation_kind == "same_person_as")
    ).scalars().all()
    assert {(r.person_id, r.related_person_id) for r in rows} == {
        (zayd.id, kufi.id),
        (kufi.id, zayd.id),
    }


def test_same_person_links_skip_mushtarak_discussions(db: Session):
    book = Book(
        source_book_id="14036",
        title_original="mujam",
        title_normalised="mujam",
        source_url="https://lib.eshia.ir/14036",
    )
    db.add(book)
    db.flush()
    add_entry(db, book, 1, "جعفر بن محمد", "مشترك بين جماعة، والتمييز بالراوي والمروي عنه.")
    build_person_layer(db)

    stats = materialize_same_person_relations(db, commit=False)
    person = person_by_name(db, "جعفر بن محمد")
    rows = db.execute(
        select(PersonRelation).where(
            PersonRelation.relation_kind == "same_person_as",
            PersonRelation.person_id == person.id,
        )
    ).scalars().all()
    assert stats.skipped_mushtarak >= 1
    assert rows == []


def test_same_person_exact_match_ignores_later_transmission_path_names(db: Session):
    book = Book(
        source_book_id="14036",
        title_original="mujam",
        title_normalised="mujam",
        source_url="https://lib.eshia.ir/14036",
    )
    db.add(book)
    db.flush()
    add_entry(
        db,
        book,
        1,
        "أحمد بن إسحاق بن عبد الله بن سعد",
        "يأتي بعنوان أحمد بن إسحاق القمي أيضا. وطريق الشيخ إليه ضعيف، بأحمد بن محمد بن يحيى العطار.",
    )
    add_entry(db, book, 2, "أحمد بن محمد بن يحيى العطار")
    build_person_layer(db)

    stats = materialize_same_person_relations(db, commit=False)

    current = person_by_name(db, "أحمد بن إسحاق بن عبد الله بن سعد")
    false_target = person_by_name(db, "أحمد بن محمد بن يحيى العطار")
    rows = db.execute(
        select(PersonRelation).where(
            PersonRelation.relation_kind == "same_person_as",
            PersonRelation.person_id == current.id,
            PersonRelation.related_person_id == false_target.id,
        )
    ).scalars().all()
    assert stats.pairs_created == 0
    assert rows == []
