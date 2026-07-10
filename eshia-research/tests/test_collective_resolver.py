import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import Book, Chain, ChainNode, Hadith, MentionResolution, Person, RijalEntry
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.collective_resolver import refine_compiler_priors, refine_with_collective_context
from eshia_research.rijal.person_builder import build_person_layer
from eshia_research.rijal.person_resolver import rebuild_person_resolutions


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


def make_chain(db: Session, book: Book, public_id: str, seq: int, tokens: list[tuple[str, str]]) -> Chain:
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
    for position, (token, node_type) in enumerate(tokens):
        db.add(
            ChainNode(
                chain_id=chain.id,
                position=position,
                raw_token=norm(token),
                token_normalised=norm(token),
                node_type=node_type,
            )
        )
    db.flush()
    return chain


@pytest.fixture()
def seeded(db: Session) -> tuple[Session, Book]:
    mujam = Book(
        source_book_id="14036",
        title_original="m",
        title_normalised="m",
        source_url="https://lib.eshia.ir/14036",
    )
    kafi = Book(
        source_book_id="11005",
        title_original="k",
        title_normalised="k",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add_all([mujam, kafi])
    db.flush()
    add_entry(db, mujam, 1, "أحمد بن محمد بن عيسى الأشعري")
    add_entry(db, mujam, 2, "أحمد بن محمد بن خالد البرقي")
    add_entry(db, mujam, 3, "أحمد بن محمد أبو بشر السراج")
    add_entry(db, mujam, 4, "أحمد بن محمد أبو جعفر")
    add_entry(db, mujam, 5, "الحسن بن محبوب")
    add_entry(db, mujam, 6, "محمد بن يحيى العطار")
    add_entry(db, mujam, 7, "الكليني", "هو محمد بن يعقوب، وقد تقدمت ترجمته.")
    add_entry(db, mujam, 8, "محمد بن يعقوب بن إسحاق")
    add_entry(db, mujam, 9, "محمد بن يعقوب بن شعيب")
    add_entry(db, mujam, 10, "محمد بن يحيى أبو جعفر العطار")
    add_entry(db, mujam, 11, "محمد بن يحيى أبو حنيفة")
    add_entry(db, mujam, 12, "علي بن إبراهيم بن هاشم")
    add_entry(db, mujam, 13, "علي بن إبراهيم التيملي")
    add_entry(db, mujam, 14, "علي بن إبراهيم بن يعلى")
    build_person_layer(db)
    return db, kafi


def person_id(db: Session, name: str) -> int:
    return db.execute(select(Person.id).where(Person.canonical_name_norm == norm(name))).scalar_one()


def resolutions_for(db: Session, chain: Chain, position: int) -> list[MentionResolution]:
    node = db.execute(
        select(ChainNode).where(ChainNode.chain_id == chain.id, ChainNode.position == position)
    ).scalar_one()
    return db.execute(
        select(MentionResolution)
        .where(MentionResolution.chain_node_id == node.id)
        .order_by(MentionResolution.rank)
    ).scalars().all()


def test_context_edges_disambiguate_bare_name(seeded):
    db, kafi = seeded
    make_chain(
        db,
        kafi,
        "edge-seed",
        1,
        [
            ("محمد بن يحيى العطار", "named_narrator"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    target = make_chain(
        db,
        kafi,
        "target",
        2,
        [
            ("محمد بن يحيى العطار", "named_narrator"),
            ("أحمد بن محمد", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    assert resolutions_for(db, target, 1)[0].status == "ambiguous"

    stats = refine_with_collective_context(db, book_ids=[kafi.id])
    rows = resolutions_for(db, target, 1)

    assert stats.nodes_resolved >= 1
    assert rows[0].status == "resolved"
    assert rows[0].person_id == person_id(db, "أحمد بن محمد بن عيسى الأشعري")
    assert rows[0].method == "collective_context"
    assert "corpus edge" in (rows[0].evidence_summary or "")


def test_compiler_prior_resolves_kulayni_opening(seeded):
    db, kafi = seeded
    chain = make_chain(
        db,
        kafi,
        "compiler",
        1,
        [
            ("أبو جعفر محمد بن يعقوب", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    assert resolutions_for(db, chain, 0)[0].status == "ambiguous"

    stats = refine_with_collective_context(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)

    assert stats.compiler_priors == 1
    assert rows[0].status == "resolved"
    assert rows[0].person_id == person_id(db, "الكليني")
    assert rows[0].evidence_json["compiler_prior"] == "al_kafi_opening_kulayni"


def test_fast_compiler_prior_slice_resolves_kulayni_opening(seeded):
    db, kafi = seeded
    chain = make_chain(
        db,
        kafi,
        "compiler-fast",
        1,
        [
            ("أبو جعفر محمد بن يعقوب", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])

    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)

    assert stats.nodes_examined == 1
    assert stats.compiler_priors == 1
    assert rows[0].status == "resolved"
    assert rows[0].person_id == person_id(db, "الكليني")
    assert rows[0].method == "compiler_prior_kulayni"
    assert rows[0].evidence_json["compiler_prior"] == "al_kafi_opening_kulayni"
    assert all(row.method == "compiler_prior_alternative" for row in rows[1:])


def test_fast_prior_slice_resolves_kafi_muhammad_yahya_opening(seeded):
    db, kafi = seeded
    chain = make_chain(
        db,
        kafi,
        "muhammad-yahya-opening",
        1,
        [
            ("محمد بن يحيى", "named_narrator"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])

    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)

    assert stats.source_priors == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "kafi_opening_muhammad_yahya"
    assert rows[0].person_id == person_id(db, "محمد بن يحيى أبو جعفر العطار")


def test_fast_prior_slice_resolves_kafi_ali_ibrahim_opening(seeded):
    db, kafi = seeded
    chain = make_chain(
        db,
        kafi,
        "ali-ibrahim-opening",
        1,
        [
            ("علي بن إبراهيم", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)

    assert stats.source_priors == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "kafi_opening_ali_ibrahim"
    assert rows[0].person_id == person_id(db, "علي بن إبراهيم بن هاشم")


def test_fast_prior_slice_resolves_opening_anhu_to_previous_hadith_source(seeded):
    db, kafi = seeded
    first = make_chain(
        db,
        kafi,
        "source",
        1,
        [
            ("محمد بن يحيى", "named_narrator"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
        ],
    )
    second = make_chain(
        db,
        kafi,
        "anhu",
        2,
        [
            ("عنه", "pronoun_relation"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    assert resolutions_for(db, second, 0)[0].status == "unresolved"

    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, second, 0)

    assert stats.source_priors == 1
    assert stats.anaphora_priors == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "kafi_opening_anaphora_previous_hadith"
    assert rows[0].person_id == resolutions_for(db, first, 0)[0].person_id


def test_roster_expands_after_context_resolves_next_bare_name(seeded):
    db, kafi = seeded
    make_chain(
        db,
        kafi,
        "edge-seed",
        1,
        [
            ("محمد بن يحيى العطار", "named_narrator"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    target = make_chain(
        db,
        kafi,
        "iddah",
        2,
        [
            ("عدة من أصحابنا", "collective_phrase"),
            ("أحمد بن محمد", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    assert resolutions_for(db, target, 0)[0].status == "unresolved"

    stats = refine_with_collective_context(db, book_ids=[kafi.id])
    rows = resolutions_for(db, target, 0)

    assert stats.roster_rows_added >= 1
    assert any(row.status == "via_collective" for row in rows)
    assert person_id(db, "محمد بن يحيى العطار") in {row.person_id for row in rows}
