import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import Book, Chain, ChainNode, Hadith, MentionResolution, Person, RijalEntry
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.collective_resolver import (
    refine_compiler_priors,
    refine_imam_kunya_priors,
    refine_previous_hadith_imam_anaphora,
    refine_with_collective_context,
)
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


def make_chain(
    db: Session,
    book: Book,
    public_id: str,
    seq: int,
    tokens: list[tuple[str, str]],
    *,
    chain_number: int = 1,
) -> Chain:
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
    chain = Chain(hadith_id=hadith.id, chain_number=chain_number, raw_isnad="x")
    db.add(chain)
    db.flush()
    for position, spec in enumerate(tokens):
        token, node_type = spec[0], spec[1]
        relation_kind = spec[2] if len(spec) > 2 else None
        db.add(
            ChainNode(
                chain_id=chain.id,
                position=position,
                raw_token=norm(token),
                token_normalised=norm(token),
                node_type=node_type,
                relation_kind=relation_kind,
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
    add_entry(db, mujam, 15, "إبراهيم بن هاشم أبو إسحاق القمي")
    add_entry(db, mujam, 16, "أحمد بن أبي عمير")
    add_entry(db, mujam, 17, "محمد بن أبي عمير زياد")
    add_entry(db, mujam, 18, "علي بن محمد بن بندار")
    add_entry(db, mujam, 19, "علي بن محمد الأشعث")
    add_entry(db, mujam, 20, "سهل بن زياد")
    add_entry(db, mujam, 21, "أحمد بن محمد بن خالد")
    add_entry(db, mujam, 22, "محمد بن خالد البرقي")
    add_entry(db, mujam, 23, "المفضل بن صالح الأسدي النخاس")
    add_entry(db, mujam, 24, "زرارة بن أعين")
    add_entry(db, mujam, 25, "الحسين بن محمد الأشعري")
    add_entry(db, mujam, 26, "عبد الله بن سنان")
    add_entry(db, mujam, 27, "الحسين بن سعيد الأهوازي")
    add_entry(db, mujam, 28, "أبو علي الأشعري")
    add_entry(db, mujam, 29, "محمد بن عيسى")
    add_entry(db, mujam, 30, "يونس بن عبد الرحمن")
    add_entry(db, mujam, 31, "محمد بن مسلم الثقفي")
    add_entry(db, mujam, 32, "العلاء بن رزين")
    add_entry(db, mujam, 33, "أحمد بن محمد بن عيسى الأشعري القمي")
    add_entry(db, mujam, 34, "علي بن الحكم")
    add_entry(db, mujam, 35, "محمد بن سنان")
    add_entry(db, mujam, 36, "حريز بن عبد الله")
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


def test_kafi_opening_prior_applies_to_parallel_chain(seeded):
    db, kafi = seeded
    chain = make_chain(
        db,
        kafi,
        "ali-ibrahim-parallel",
        1,
        [
            ("علي بن إبراهيم", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
        chain_number=2,
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])

    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, 0)

    assert stats.review_priors == 1
    assert rows[0].method == "kafi_opening_ali_ibrahim"
    assert rows[0].person_id == person_id(db, "علي بن إبراهيم بن هاشم")


@pytest.mark.parametrize(
    ("tokens", "target_position", "expected_name", "expected_method"),
    [
        (
            [("الحسن بن محبوب", "named_narrator"), ("ابن أبي عمير", "named_narrator")],
            1,
            "محمد بن أبي عمير زياد",
            "kafi_review_ibn_abi_umayr",
        ),
        (
            [("علي بن إبراهيم", "named_narrator"), ("أبيه", "pronoun_relation")],
            1,
            "إبراهيم بن هاشم أبو إسحاق القمي",
            "kafi_review_father_after_ali_ibrahim",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("أبي عبد الله ع", "imam")],
            1,
            "جعفر بن محمد الصادق عليه السلام",
            "kafi_review_terminal_abu_abdullah",
        ),
        (
            [("علي بن محمد", "named_narrator"), ("سهل بن زياد", "named_narrator")],
            0,
            "علي بن محمد بن بندار",
            "kafi_review_opening_ali_muhammad_before_sahl",
        ),
        (
            [("أحمد بن محمد بن خالد", "named_narrator"), ("أبيه", "pronoun_relation")],
            1,
            "محمد بن خالد البرقي",
            "kafi_review_father_after_ahmad_barqi",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("أبي جميلة", "named_narrator")],
            1,
            "المفضل بن صالح الأسدي النخاس",
            "kafi_review_abu_jamila",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("أبي الحسن الرضا ع", "imam")],
            1,
            "علي بن موسى الرضا عليه السلام",
            "kafi_review_terminal_abu_al_hasan_al_rida",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("سهل بن زياد", "named_narrator")],
            1,
            "سهل بن زياد",
            "kafi_review_internal_sahl_ibn_ziyad",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("زرارة", "named_narrator")],
            1,
            "زرارة بن أعين",
            "kafi_review_internal_zurara",
        ),
        (
            [("الحسين بن محمد", "named_narrator"), ("الحسن بن محبوب", "named_narrator")],
            0,
            "الحسين بن محمد الأشعري",
            "kafi_review_opening_husayn_ibn_muhammad",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("عبد الله بن سنان", "named_narrator")],
            1,
            "عبد الله بن سنان",
            "kafi_review_internal_abdullah_ibn_sinan",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("الحسين بن سعيد", "named_narrator")],
            1,
            "الحسين بن سعيد الأهوازي",
            "kafi_review_internal_husayn_ibn_said",
        ),
        (
            [("أبو علي الأشعري", "named_narrator"), ("الحسن بن محبوب", "named_narrator")],
            0,
            "أبو علي الأشعري",
            "kafi_review_opening_abu_ali_al_ashari",
        ),
        (
            [("محمد بن عيسى", "named_narrator"), ("يونس", "named_narrator")],
            1,
            "يونس بن عبد الرحمن",
            "kafi_review_yunus_after_muhammad_ibn_isa",
        ),
        (
            [("العلاء بن رزين", "named_narrator"), ("محمد بن مسلم", "named_narrator")],
            1,
            "محمد بن مسلم الثقفي",
            "kafi_review_muhammad_ibn_muslim_after_al_ala",
        ),
        (
            [
                ("محمد بن يحيى", "named_narrator"),
                ("أحمد بن محمد", "named_narrator"),
                ("علي بن الحكم", "named_narrator"),
            ],
            1,
            "أحمد بن محمد بن عيسى الأشعري القمي",
            "kafi_review_ahmad_ibn_muhammad_between_yahya_and_known_teacher",
        ),
        (
            [("الحسن بن محبوب", "named_narrator"), ("حريز", "named_narrator")],
            1,
            "حريز بن عبد الله",
            "kafi_review_internal_hariz",
        ),
    ],
)
def test_validated_review_priors_resolve_exact_kafi_patterns(
    seeded, tokens, target_position, expected_name, expected_method
):
    db, kafi = seeded
    chain = make_chain(db, kafi, f"review-{expected_method}", 1, tokens)
    rebuild_person_resolutions(db, book_ids=[kafi.id])

    stats = refine_compiler_priors(db, book_ids=[kafi.id])
    rows = resolutions_for(db, chain, target_position)

    assert stats.review_priors >= 1
    assert rows[0].status == "resolved"
    assert rows[0].method == expected_method
    assert rows[0].person_id == person_id(db, expected_name)


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


def test_generation_veto_blocks_chronologically_impossible_context_winner(seeded):
    from eshia_research.models import PersonGeneration
    db, kafi = seeded
    make_chain(
        db, kafi, "edge-seed", 1,
        [
            ("محمد بن يحيى العطار", "named_narrator"),
            ("أحمد بن محمد بن عيسى الأشعري", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    target = make_chain(
        db, kafi, "target", 2,
        [
            ("محمد بن يحيى العطار", "named_narrator"),
            ("أحمد بن محمد", "named_narrator"),
            ("الحسن بن محبوب", "named_narrator"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[kafi.id])
    assert resolutions_for(db, target, 1)[0].status == "ambiguous"

    # Anchor the next neighbour at layer 5 and the would-be winner at layer 1 —
    # four layers off the neighbour-derived expectation (6): impossible.
    ashari = person_id(db, "أحمد بن محمد بن عيسى الأشعري")
    mahbub = person_id(db, "الحسن بن محبوب")
    db.add(PersonGeneration(person_id=ashari, gen_lo=1, gen_hi=1, gen_point=1,
                            method="imam_fixed", resolver_version="tabaqat_c1"))
    db.add(PersonGeneration(person_id=mahbub, gen_lo=5, gen_hi=5, gen_point=5,
                            method="ashab_anchor", resolver_version="tabaqat_c1"))
    db.flush()

    refine_with_collective_context(db, book_ids=[kafi.id])
    # The edge-supported al-Ash'ari pick is vetoed, so the node stays honest.
    assert resolutions_for(db, target, 1)[0].status == "ambiguous"


def test_imam_kunya_prior_resolves_abu_abdallah_to_sadiq(seeded):
    db, kafi = seeded
    faqih = Book(
        source_book_id="11021",
        title_original="f",
        title_normalised="f",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(faqih)
    db.flush()
    chain = make_chain(
        db,
        faqih,
        "abu-abdallah",
        1,
        [
            ("محمد بن مسلم", "named_narrator"),
            ("أبي عبد الله ع", "imam"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[faqih.id])
    before = resolutions_for(db, chain, 1)
    assert before[0].status == "ambiguous"
    candidate_ids = {row.person_id for row in before}
    assert person_id(db, "جعفر بن محمد الصادق عليه السلام") in candidate_ids
    assert person_id(db, "الحسين بن علي سيد الشهداء عليه السلام") in candidate_ids

    stats = refine_imam_kunya_priors(db, book_ids=[faqih.id])
    rows = resolutions_for(db, chain, 1)

    assert stats.nodes_examined == 1
    assert stats.nodes_resolved == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "imam_kunya_prior"
    assert rows[0].person_id == person_id(db, "جعفر بن محمد الصادق عليه السلام")
    assert rows[0].evidence_json["imam_kunya_prior"] == "abu_abdallah_sadiq"
    # al-Husayn is retained as a ranked alternative, never dropped.
    alt = [row for row in rows[1:] if row.person_id == person_id(db, "الحسين بن علي سيد الشهداء عليه السلام")]
    assert len(alt) == 1
    assert alt[0].status == "ambiguous"
    assert alt[0].method == "imam_kunya_prior_alternative"

    # Idempotent: a second run resolves nothing new.
    again = refine_imam_kunya_priors(db, book_ids=[faqih.id])
    assert again.nodes_resolved == 0


def test_imam_kunya_prior_resolves_abu_jafar_to_baqir(seeded):
    db, kafi = seeded
    faqih = Book(
        source_book_id="11021",
        title_original="f",
        title_normalised="f",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(faqih)
    db.flush()
    chain = make_chain(
        db,
        faqih,
        "abu-jafar",
        1,
        [
            ("زرارة", "named_narrator"),
            ("أبي جعفر ع", "imam"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[faqih.id])
    before = resolutions_for(db, chain, 1)
    assert before[0].status == "ambiguous"
    candidate_ids = {row.person_id for row in before}
    assert person_id(db, "محمد بن علي الباقر عليه السلام") in candidate_ids
    assert person_id(db, "محمد بن علي الجواد عليه السلام") in candidate_ids

    stats = refine_imam_kunya_priors(db, book_ids=[faqih.id])
    rows = resolutions_for(db, chain, 1)

    assert stats.nodes_resolved == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "imam_kunya_prior"
    assert rows[0].person_id == person_id(db, "محمد بن علي الباقر عليه السلام")
    assert rows[0].evidence_json["imam_kunya_prior"] == "abu_jafar_baqir"


def test_previous_hadith_imam_anaphora_propagates_after_kunya_prior(seeded):
    db, kafi = seeded
    faqih = Book(
        source_book_id="11021",
        title_original="f",
        title_normalised="f",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(faqih)
    db.flush()
    # Report 1 (seq 1): «... عن أبي عبد الله ع» — terminal Imam, left ambiguous by Phase B.
    make_chain(
        db,
        faqih,
        "serial-1",
        1,
        [("ابن مسكان", "named_narrator"), ("أبي عبد الله ع", "imam")],
    )
    # Report 2 (seq 2): «وسأله معاوية بن عمار عن ...» — questioner + pronoun to the previous Imam.
    second = make_chain(
        db,
        faqih,
        "serial-2",
        2,
        [
            ("معاوية بن عمار", "named_narrator"),
            ("سأله", "pronoun_relation", "previous_hadith_imam"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[faqih.id])
    # Before: the pronoun cannot resolve because report 1's Imam is still ambiguous.
    assert resolutions_for(db, second, 1)[0].status == "unresolved"

    kunya = refine_imam_kunya_priors(db, book_ids=[faqih.id], commit=False)
    anaphora = refine_previous_hadith_imam_anaphora(db, book_ids=[faqih.id])
    rows = resolutions_for(db, second, 1)

    assert kunya.nodes_resolved == 1
    assert anaphora.nodes_resolved == 1
    assert rows[0].status == "resolved"
    assert rows[0].method == "anaphora_imam_after_kunya_prior"
    assert rows[0].person_id == person_id(db, "جعفر بن محمد الصادق عليه السلام")


def test_imam_kunya_prior_leaves_explicit_imam_untouched(seeded):
    db, kafi = seeded
    faqih = Book(
        source_book_id="11021",
        title_original="f",
        title_normalised="f",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(faqih)
    db.flush()
    chain = make_chain(
        db,
        faqih,
        "explicit-husayn",
        1,
        [
            ("محمد بن مسلم", "named_narrator"),
            ("الحسين بن علي ع", "imam"),
        ],
    )
    rebuild_person_resolutions(db, book_ids=[faqih.id])
    # Explicit al-Husayn resolves via imam_explicit_identity, not an ambiguous kunya.
    before = resolutions_for(db, chain, 1)
    assert before[0].status == "resolved"

    stats = refine_imam_kunya_priors(db, book_ids=[faqih.id])
    assert stats.nodes_resolved == 0
    rows = resolutions_for(db, chain, 1)
    assert rows[0].person_id == person_id(db, "الحسين بن علي سيد الشهداء عليه السلام")


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
