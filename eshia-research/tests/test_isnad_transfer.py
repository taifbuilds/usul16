import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.db import Base
from eshia_research.isnad.transfer import (
    build_manifest,
    export_delta,
    import_delta,
    verify_target,
)
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Narrator,
    Person,
    PersonResolutionDecision,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _person(db: Session, person_id: int, name: str) -> Person:
    person = Person(id=person_id, canonical_name_ar=name, canonical_name_norm=name)
    db.add(person)
    return person


def _corpus(db: Session, *, with_chain: bool = True, person_name: str = "الحسن بن محبوب"):
    """A one-book, one-hadith corpus, optionally with a resolved chain."""
    book = Book(
        source_book_id="11021",
        title_original="من لا يحضره الفقيه",
        title_normalised="من لا یحضره الفقیه",
        source_url="u",
    )
    db.add(book)
    db.flush()
    hadith = Hadith(
        public_id="faqih-1",
        book_id=book.id,
        sequence_in_book=1,
        sequence_in_page=1,
        page_start=1,
        page_end=1,
        full_text_raw="نص",
        full_text_normalised="نص",
        isnad_raw="عن الحسن بن محبوب" if with_chain else None,
        matn_raw="المتن",
        matn_normalised="المتن",
        source_url="u/1",
    )
    db.add(hadith)
    _person(db, 3063, person_name)
    db.add(Narrator(id=3063, canonical_name_ar=person_name, canonical_name_norm=person_name))
    db.flush()

    if with_chain:
        chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="عن الحسن بن محبوب", node_count=1)
        db.add(chain)
        db.flush()
        node = ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token="الحسن بن محبوب",
            token_normalised="الحسن بن محبوب",
            node_type="named_narrator",
            canonical_narrator_id=3063,
        )
        db.add(node)
        db.flush()
        db.add(
            MentionResolution(
                chain_node_id=node.id,
                person_id=3063,
                rank=1,
                status="resolved",
                resolver_version="v1",
            )
        )
    db.commit()
    return book, hadith


def test_delta_carries_chains_nodes_and_resolutions():
    source = _session()
    _corpus(source)
    target = _session()
    _corpus(target, with_chain=False)

    delta = export_delta(source, "11021", build_manifest(target, "11021"))
    assert delta["summary"]["changed"] == 1

    import_delta(target, delta)
    counts = verify_target(target, "11021")
    assert counts == {"chains": 1, "nodes": 1, "resolutions": 1, "needs_review": 0}
    # The split travels with the chains, so the reader's boundary and the chain
    # layer cannot disagree after a deploy.
    assert target.scalar(select(Hadith.isnad_raw)) == "عن الحسن بن محبوب"


def test_unchanged_hadiths_do_not_travel():
    source = _session()
    _corpus(source)
    target = _session()
    _corpus(target)

    delta = export_delta(source, "11021", build_manifest(target, "11021"))

    assert delta["summary"]["changed"] == 0
    assert delta["summary"]["unchanged"] == 1


def test_import_refuses_when_a_person_id_means_someone_else():
    # The failure this whole module exists to prevent: ids that line up but
    # name different men would silently reassign narrations.
    source = _session()
    _corpus(source, person_name="الحسن بن محبوب")
    target = _session()
    _corpus(target, with_chain=False, person_name="شخص آخر")

    delta = export_delta(source, "11021", build_manifest(target, "11021"))

    with pytest.raises(ValueError, match="misattribute"):
        import_delta(target, delta)
    assert target.scalar(select(func.count()).select_from(Chain)) == 0


def test_import_refuses_an_unknown_public_id():
    source = _session()
    _corpus(source)
    target = _session()
    book = Book(
        source_book_id="11021",
        title_original="من لا يحضره الفقيه",
        title_normalised="من لا یحضره الفقیه",
        source_url="u",
    )
    target.add(book)
    _person(target, 3063, "الحسن بن محبوب")
    target.add(
        Narrator(
            id=3063,
            canonical_name_ar="الحسن بن محبوب",
            canonical_name_norm="الحسن بن محبوب",
        )
    )
    target.commit()

    delta = export_delta(source, "11021", None)

    with pytest.raises(ValueError, match="not in this database"):
        import_delta(target, delta)


def test_dry_run_writes_nothing():
    source = _session()
    _corpus(source)
    target = _session()
    _corpus(target, with_chain=False)

    delta = export_delta(source, "11021", build_manifest(target, "11021"))
    import_delta(target, delta, dry_run=True)

    assert target.scalar(select(func.count()).select_from(Chain)) == 0


def test_import_does_not_touch_another_book(tmp_path):
    # Production holds tens of thousands of human decisions for al-Kafi.
    # Publishing Faqih must not be able to reach them.
    source = _session()
    _corpus(source)

    target = _session()
    _corpus(target, with_chain=False)
    other = Book(
        source_book_id="11005",
        title_original="الكافي",
        title_normalised="الکافی",
        source_url="u2",
    )
    target.add(other)
    target.flush()
    kafi = Hadith(
        public_id="alkafi-1",
        book_id=other.id,
        sequence_in_book=1,
        sequence_in_page=1,
        page_start=1,
        page_end=1,
        full_text_raw="نص",
        full_text_normalised="نص",
        isnad_raw="سند",
        matn_raw="متن",
        matn_normalised="متن",
        source_url="u2/1",
    )
    target.add(kafi)
    target.flush()
    kafi_chain = Chain(hadith_id=kafi.id, chain_number=1, raw_isnad="سند", node_count=1)
    target.add(kafi_chain)
    target.flush()
    kafi_node = ChainNode(
        chain_id=kafi_chain.id,
        position=0,
        raw_token="راو",
        token_normalised="راو",
        node_type="named_narrator",
    )
    target.add(kafi_node)
    target.flush()
    target.add(
        PersonResolutionDecision(
            chain_node_id=kafi_node.id,
            reviewer="codex-machine-v1",
            decision_type="approve_current",
            confidence_tier="high",
            resolver_version="v1",
        )
    )
    target.commit()

    delta = export_delta(source, "11021", build_manifest(target, "11021"))
    import_delta(target, delta)

    assert target.scalar(select(func.count()).select_from(PersonResolutionDecision)) == 1
    assert target.get(Chain, kafi_chain.id) is not None
