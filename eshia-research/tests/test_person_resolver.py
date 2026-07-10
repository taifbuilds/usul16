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
    Person,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.person_builder import build_person_layer
from eshia_research.rijal.person_resolver import (
    build_person_lookup,
    rebuild_person_resolutions,
    split_collective_members,
)


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


def add_entry(db: Session, book: Book, number: int, name: str, text: str = "") -> None:
    db.add(
        RijalEntry(
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
    )
    db.flush()


def make_chain(db: Session, book: Book, public_id: str, seq: int, nodes: list[dict]) -> Chain:
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        sequence_in_book=seq,
        sequence_in_page=seq,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw="x",
        full_text_normalised="x",
        matn_raw="x",
        matn_normalised="x",
        source_url="u",
        isnad_raw="x",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    for pos, spec in enumerate(nodes):
        db.add(
            ChainNode(
                chain_id=chain.id,
                position=pos,
                raw_token=spec["norm"],
                token_normalised=spec["norm"],
                node_type=spec["type"],
                relation_kind=spec.get("relation"),
            )
        )
    db.flush()
    return chain


@pytest.fixture()
def seeded(db: Session) -> tuple[Session, Book]:
    mujam = Book(
        source_book_id="14036", title_original="m", title_normalised="m",
        source_url="https://lib.eshia.ir/14036",
    )
    kafi = Book(
        source_book_id="11005", title_original="k", title_normalised="k",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add_all([mujam, kafi])
    db.flush()
    add_entry(db, mujam, 1, "أحمد بن محمد بن عيسى الأشعري")
    add_entry(db, mujam, 2, "أحمد بن محمد بن خالد البرقي")
    add_entry(db, mujam, 3, "أحمد بن محمد", "مشترک بین جماعة.")
    add_entry(db, mujam, 4, "الحسن بن محبوب")
    add_entry(db, mujam, 5, "العلاء بن رزين")
    add_entry(db, mujam, 6, "محمد بن يحيى العطار")
    add_entry(db, mujam, 7, "إبراهيم بن هاشم القمي")
    add_entry(db, mujam, 8, "علي بن إبراهيم بن هاشم")
    build_person_layer(db)
    return db, kafi


def person_id(db: Session, name: str) -> int:
    return db.execute(
        select(Person.id).where(Person.canonical_name_norm == norm(name))
    ).scalar_one()


def resolutions_for(db: Session, chain: Chain, position: int) -> list[MentionResolution]:
    node = db.execute(
        select(ChainNode).where(
            ChainNode.chain_id == chain.id, ChainNode.position == position
        )
    ).scalar_one()
    return db.execute(
        select(MentionResolution)
        .where(MentionResolution.chain_node_id == node.id)
        .order_by(MentionResolution.rank)
    ).scalars().all()


def test_unique_surface_form_resolves(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-1", 1, [
        {"norm": norm("الحسن بن محبوب"), "type": "named_narrator"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)
    assert len(rows) == 1
    assert rows[0].status == "resolved"
    assert rows[0].person_id == person_id(db, "الحسن بن محبوب")


def test_bare_form_is_ambiguous_not_falsely_resolved(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-2", 2, [
        {"norm": norm("احمد بن محمد"), "type": "named_narrator"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)
    assert len(rows) >= 2
    assert all(r.status == "ambiguous" for r in rows)
    # The bare-form proxy is not offered as an identity; real persons are.
    kinds = {db.get(Person, r.person_id).kind for r in rows}
    assert "bare_form_proxy" not in kinds


def test_ibn_form_resolves_to_hasan_ibn_mahbub(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-3", 3, [
        {"norm": norm("ابن محبوب"), "type": "named_narrator"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)
    assert len(rows) == 1
    assert rows[0].person_id == person_id(db, "الحسن بن محبوب")


def test_father_reference_resolves_via_person_relation(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-4", 4, [
        {"norm": norm("علی بن ابراهیم بن هاشم"), "type": "named_narrator"},
        {"norm": norm("ابیه"), "type": "pronoun_relation", "relation": "father"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 1)
    assert len(rows) == 1
    assert rows[0].status == "resolved"
    assert rows[0].person_id == person_id(db, "ابراهیم بن هاشم القمی")
    assert "father" in rows[0].method


def test_father_reference_mints_latent_when_unmatched(seeded):
    db, kafi = seeded
    # «سعد بن خلف» has no Mu'jam entry; father عن أبيه must mint a latent person.
    chain = make_chain(db, kafi, "k-5", 5, [
        {"norm": norm("محمد بن سعد بن خلف"), "type": "named_narrator"},
        {"norm": norm("ابیه"), "type": "pronoun_relation", "relation": "father"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 1)
    assert len(rows) == 1
    assert rows[0].status == "latent"
    latent = db.get(Person, rows[0].person_id)
    assert latent.kind == "latent"
    assert latent.canonical_name_norm == norm("سعد بن خلف")


def test_collective_named_member_via_collective(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-6", 6, [
        {"norm": norm("عدة من اصحابنا منهم محمد بن یحیی العطار"), "type": "collective_phrase"},
        {"norm": norm("احمد بن محمد"), "type": "named_narrator"},
    ])
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)
    member_ids = {r.person_id for r in rows if r.status == "via_collective"}
    assert person_id(db, "محمد بن يحيى العطار") in member_ids


def test_split_collective_members_handles_waw_joined(seeded):
    db, _ = seeded
    lookup = build_person_lookup(db)
    members = split_collective_members(
        norm("عدة من اصحابنا منهم محمد بن یحیی العطار والحسن بن محبوب"), lookup
    )
    forms = {m for m, _ in members}
    assert norm("محمد بن یحیی العطار") in forms
    assert norm("الحسن بن محبوب") in forms


def test_every_node_gets_a_resolution_row(seeded):
    db, kafi = seeded
    chain = make_chain(db, kafi, "k-7", 7, [
        {"norm": norm("عدة من اصحابنا منهم محمد بن یحیی العطار"), "type": "collective_phrase"},
        {"norm": norm("احمد بن محمد بن عیسی الاشعری"), "type": "named_narrator"},
        {"norm": norm("الحسن بن محبوب"), "type": "named_narrator"},
        {"norm": norm("ابی عبد الله ع"), "type": "imam"},
    ])
    stats = rebuild_person_resolutions(db, book_ids=[kafi.id])
    for pos in range(4):
        assert resolutions_for(db, chain, pos), f"position {pos} missing a resolution"
    assert stats.resolution_rows >= 4
