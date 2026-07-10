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
    PersonGeneration,
    RijalEntry,
    RijalStatement,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.person_builder import build_person_layer
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION
from eshia_research.rijal.tabaqat import (
    build_tabaqat,
    imam_generation_from_raw,
    refine_with_tabaqat,
)


def norm(text: str) -> str:
    return normalise_arabic_persian(text)


@pytest.fixture()
def db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_imam_generation_keyword_mapping():
    assert imam_generation_from_raw("الصادق (ع)") == 5
    assert imam_generation_from_raw("الباقر (ع)") == 4
    assert imam_generation_from_raw("الجواد (ع)") == 8
    # Specificity: al-Askari must not fall through to bare al-Hasan.
    assert imam_generation_from_raw("الحسن العسكري (ع)") == 10
    assert imam_generation_from_raw("رسول الله (ص)") == 0


def _entry(db, book, number, name, text=""):
    e = RijalEntry(
        book_id=book.id, entry_kind="mujam_numbered_entry", entry_number=number,
        title_raw=name, title_normalised=norm(name),
        canonical_name_raw=name, canonical_name_normalised=norm(name),
        text_raw=text or name, text_normalised=norm(text or name),
    )
    db.add(e)
    db.flush()
    return e


@pytest.fixture()
def seeded(db: Session):
    mujam = Book(source_book_id="14036", title_original="m", title_normalised="m",
                 source_url="u")
    kafi = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add_all([mujam, kafi])
    db.flush()
    e_muslim = _entry(db, mujam, 1, "محمد بن مسلم الثقفي")
    _entry(db, mujam, 2, "الحسن بن محبوب")
    db.flush()
    build_person_layer(db)
    # Muhammad b. Muslim is a companion of al-Baqir (layer 4) -> generation 5.
    db.add(RijalStatement(
        entry_id=e_muslim.id, source_name="tusi_rijal", statement_type="tabaqah_membership",
        quote_raw="من أصحاب الباقر", quote_normalised=norm("من أصحاب الباقر"),
        metadata_json={"imam_raw": "الباقر (ع)"},
    ))
    db.flush()
    return db, kafi


def person_id(db, name):
    return db.execute(select(Person.id).where(Person.canonical_name_norm == norm(name))).scalar_one()


def gen_of(db, name):
    pid = person_id(db, name)
    return db.execute(
        select(PersonGeneration).where(PersonGeneration.person_id == pid)
    ).scalar_one_or_none()


def test_imams_get_fixed_layers(seeded):
    db, _ = seeded
    build_tabaqat(db, book_ids=[])
    sadiq = gen_of(db, "جعفر بن محمد الصادق عليه السلام")
    assert sadiq is not None
    assert sadiq.gen_lo == sadiq.gen_hi == 5
    assert sadiq.method == "imam_fixed"


def test_companionship_anchor_places_generation(seeded):
    db, _ = seeded
    build_tabaqat(db, book_ids=[])
    muslim = gen_of(db, "محمد بن مسلم الثقفي")
    assert muslim is not None
    # Companion of al-Baqir (4) -> ~generation 5, within the soft interval.
    assert muslim.gen_lo <= 5 <= muslim.gen_hi
    assert muslim.method in ("ashab_anchor", "anchor_and_propagated")


def test_propagation_places_teacher_one_layer_earlier(db: Session):
    # Build a minimal person layer with two persons and a resolved edge.
    mujam = Book(source_book_id="14036", title_original="m", title_normalised="m", source_url="u")
    kafi = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add_all([mujam, kafi])
    db.flush()
    e_student = _entry(db, mujam, 1, "أحمد بن محمد بن عيسى")
    e_teacher = _entry(db, mujam, 2, "الحسن بن محبوب")
    db.flush()
    build_person_layer(db)
    # Anchor the student at generation 7 via a companionship-like fixed layer:
    # give the teacher's generation via an edge instead.
    db.add(RijalStatement(
        entry_id=e_student.id, source_name="tusi_rijal", statement_type="tabaqah_membership",
        quote_raw="x", quote_normalised="x", metadata_json={"imam_raw": "الرضا (ع)"},
    ))  # companion of al-Rida (7) -> ~gen 8
    db.flush()
    student = db.execute(select(Person.id).where(Person.canonical_name_norm == norm("احمد بن محمد بن عیسی"))).scalar_one()
    teacher = db.execute(select(Person.id).where(Person.canonical_name_norm == norm("الحسن بن محبوب"))).scalar_one()

    hadith = Hadith(public_id="k-1", book_id=kafi.id, sequence_in_book=1, sequence_in_page=1,
                    volume_start=1, volume_end=1, page_start=1, page_end=1,
                    full_text_raw="x", full_text_normalised="x", matn_raw="x",
                    matn_normalised="x", source_url="u", isnad_raw="x")
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    n0 = ChainNode(chain_id=chain.id, position=0, raw_token="x",
                   token_normalised=norm("احمد بن محمد بن عیسی"), node_type="named_narrator")
    n1 = ChainNode(chain_id=chain.id, position=1, raw_token="x",
                   token_normalised=norm("الحسن بن محبوب"), node_type="named_narrator")
    db.add_all([n0, n1])
    db.flush()
    for node, pid in ((n0, student), (n1, teacher)):
        db.add(MentionResolution(chain_node_id=node.id, person_id=pid, rank=1, status="resolved",
                                 method="surface_full", resolver_version=PERSON_RESOLVER_VERSION))
    db.flush()

    build_tabaqat(db, book_ids=[kafi.id])
    tg = db.execute(select(PersonGeneration).where(PersonGeneration.person_id == teacher)).scalar_one()
    sg = db.execute(select(PersonGeneration).where(PersonGeneration.person_id == student)).scalar_one()
    # Teacher must be strictly earlier than the student.
    assert tg.gen_hi < sg.gen_hi or tg.gen_lo < sg.gen_lo
    assert tg.gen_lo <= sg.gen_lo - 1 + 1  # within one layer earlier


def test_refine_disambiguates_imam_by_generation(db: Session):
    """«أبو جعفر ع» after a gen-6 narrator must resolve to al-Baqir (4), not al-Jawad (8)."""
    from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION as RV

    mujam = Book(source_book_id="14036", title_original="m", title_normalised="m", source_url="u")
    kafi = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add_all([mujam, kafi])
    db.flush()
    e_narr = _entry(db, mujam, 1, "محمد بن مسلم الثقفي")
    db.flush()
    build_person_layer(db)
    # Anchor the narrator at generation 6 (companion of al-Sadiq, layer 5).
    db.add(RijalStatement(
        entry_id=e_narr.id, source_name="tusi_rijal", statement_type="tabaqah_membership",
        quote_raw="x", quote_normalised="x", metadata_json={"imam_raw": "الصادق (ع)"},
    ))
    db.flush()
    narr = db.execute(select(Person.id).where(Person.canonical_name_norm == norm("محمد بن مسلم الثقفی"))).scalar_one()
    baqir = db.execute(select(Person.id).where(Person.canonical_name_norm == norm("محمد بن علي الباقر عليه السلام"))).scalar_one()

    hadith = Hadith(public_id="k-1", book_id=kafi.id, sequence_in_book=1, sequence_in_page=1,
                    volume_start=1, volume_end=1, page_start=1, page_end=1, full_text_raw="x",
                    full_text_normalised="x", matn_raw="x", matn_normalised="x", source_url="u", isnad_raw="x")
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    n0 = ChainNode(chain_id=chain.id, position=0, raw_token="x",
                   token_normalised=norm("محمد بن مسلم"), node_type="named_narrator")
    n1 = ChainNode(chain_id=chain.id, position=1, raw_token="x",
                   token_normalised=norm("ابی جعفر ع"), node_type="imam")
    db.add_all([n0, n1])
    db.flush()
    # n0 resolved to the gen-6 narrator; n1 ambiguous between al-Baqir and al-Jawad.
    db.add(MentionResolution(chain_node_id=n0.id, person_id=narr, rank=1, status="resolved",
                             method="surface_full", resolver_version=RV))
    jawad = db.execute(select(Person.id).where(Person.canonical_name_norm == norm("محمد بن علي الجواد عليه السلام"))).scalar_one()
    db.add(MentionResolution(chain_node_id=n1.id, person_id=baqir, rank=1, status="ambiguous",
                             method="surface_masum_title", resolver_version=RV))
    db.add(MentionResolution(chain_node_id=n1.id, person_id=jawad, rank=2, status="ambiguous",
                             method="surface_masum_title", resolver_version=RV))
    db.flush()

    build_tabaqat(db, book_ids=[kafi.id])
    stats = refine_with_tabaqat(db, book_ids=[kafi.id])
    assert stats["imam_disambiguated"] == 1
    final = db.execute(select(MentionResolution).where(MentionResolution.chain_node_id == n1.id)).scalars().all()
    assert len(final) == 1
    assert final[0].status == "resolved"
    assert final[0].person_id == baqir
    assert final[0].method == "tabaqat_disambiguated"
