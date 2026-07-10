import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    Narrator,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.resolver import rebuild_chain_node_resolutions, token_variants


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


def add_book_hadith_chain(db: Session, token_norms: list[str]) -> list[ChainNode]:
    book = Book(
        source_book_id="11005",
        title_original="al-kafi",
        title_normalised="al-kafi",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add(book)
    db.flush()
    hadith = Hadith(
        public_id=f"h-{len(token_norms)}",
        book_id=book.id,
        sequence_in_book=1,
        sequence_in_page=1,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw="x",
        full_text_normalised="x",
        matn_raw="x",
        matn_normalised="x",
        source_url="u",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    nodes = []
    for position, token_norm in enumerate(token_norms):
        node = ChainNode(
            chain_id=chain.id,
            position=position,
            raw_token=token_norm,
            token_normalised=token_norm,
            node_type="named_narrator",
        )
        db.add(node)
        nodes.append(node)
    db.flush()
    return nodes


def add_chain(
    db: Session,
    *,
    book: Book,
    public_id: str,
    sequence: int,
    nodes_spec: list[tuple[str, str, str | None]],
) -> list[ChainNode]:
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        sequence_in_book=sequence,
        sequence_in_page=sequence,
        volume_start=1,
        volume_end=1,
        page_start=sequence,
        page_end=sequence,
        full_text_raw="x",
        full_text_normalised="x",
        matn_raw="x",
        matn_normalised="x",
        source_url="u",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    nodes = []
    for position, (token_norm, node_type, relation_kind) in enumerate(nodes_spec):
        node = ChainNode(
            chain_id=chain.id,
            position=position,
            raw_token=token_norm,
            token_normalised=token_norm,
            node_type=node_type,
            relation_kind=relation_kind,
        )
        db.add(node)
        nodes.append(node)
    db.flush()
    return nodes


def add_book(db: Session) -> Book:
    book = Book(
        source_book_id="11005",
        title_original="al-kafi",
        title_normalised="al-kafi",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add(book)
    db.flush()
    return book


def add_narrator(db: Session, name: str) -> Narrator:
    narrator = Narrator(canonical_name_ar=name, canonical_name_norm=norm(name))
    db.add(narrator)
    db.flush()
    return narrator


def add_occurrence(db: Session, narrator: Narrator, direction: str, related_name: str) -> None:
    db.add(
        RijalOccurrence(
            entry_id=1,
            narrator_id=narrator.id,
            direction=direction,
            related_name_raw=related_name,
            related_name_normalised=norm(related_name),
            source_ref_raw="الكافي: ج 1، ح 1.",
            evidence_text_raw="evidence",
        )
    )


def test_token_variants_handles_word_initial_abi_case():
    variants = token_variants(norm("أبي بصير"))

    assert norm("أبي بصير") in variants
    assert norm("أبو بصير") in variants


def test_token_variants_handles_internal_ibn_spelling():
    variants = token_variants(norm("محمد ابن مسلم"))

    assert norm("محمد بن مسلم") in variants


def test_unique_exact_match_resolves_node(db: Session):
    nodes = add_book_hadith_chain(db, [norm("زرارة")])
    narrator = add_narrator(db, "زرارة")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[0])

    assert stats.resolved_nodes == 1
    assert nodes[0].canonical_narrator_id == narrator.id
    assert nodes[0].resolution_method == "exact_unique"
    assert db.query(ChainNodeCandidate).count() == 1


def test_unique_prefix_match_resolves_shortened_name(db: Session):
    nodes = add_book_hadith_chain(db, [norm("زرارة")])
    narrator = add_narrator(db, "زرارة بن أعين")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[0])

    assert stats.prefix_unique_resolved == 1
    assert nodes[0].canonical_narrator_id == narrator.id
    assert nodes[0].resolution_method == "prefix_unique"


def test_ambiguous_exact_match_keeps_candidates_without_winner(db: Session):
    nodes = add_book_hadith_chain(db, [norm("أحمد بن محمد")])
    add_narrator(db, "أحمد بن محمد")
    add_narrator(db, "أحمد بن محمد")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[0])

    assert stats.ambiguous_nodes == 1
    assert nodes[0].canonical_narrator_id is None
    assert nodes[0].review_status == "ambiguous"
    assert db.query(ChainNodeCandidate).count() == 2


def test_context_occurrence_selects_ambiguous_winner(db: Session):
    nodes = add_book_hadith_chain(
        db,
        [norm("محمد بن يحيى"), norm("أحمد بن محمد"), norm("صفوان")],
    )
    add_narrator(db, "محمد بن يحيى")
    weak_candidate = add_narrator(db, "أحمد بن محمد")
    strong_candidate = add_narrator(db, "أحمد بن محمد")
    add_narrator(db, "صفوان")
    add_occurrence(db, strong_candidate, "narrated_by", "محمد بن يحيى")
    add_occurrence(db, strong_candidate, "narrates_from", "صفوان")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[1])

    assert stats.context_resolved == 1
    assert nodes[1].canonical_narrator_id == strong_candidate.id
    assert nodes[1].canonical_narrator_id != weak_candidate.id
    assert nodes[1].resolution_method == "context_score"


def test_father_relation_resolves_from_son_and_chain_context(db: Session):
    book = add_book(db)
    nodes = add_chain(
        db,
        book=book,
        public_id="father",
        sequence=1,
        nodes_spec=[
            (norm("علي بن إبراهيم"), "named_narrator", None),
            (norm("أبيه"), "pronoun_relation", "father"),
            (norm("حماد بن عيسى"), "named_narrator", None),
        ],
    )
    add_narrator(db, "علي بن إبراهيم")
    father = add_narrator(db, "إبراهيم بن هاشم")
    add_narrator(db, "حماد بن عيسى")
    add_occurrence(db, father, "narrated_by", "علي بن إبراهيم")
    add_occurrence(db, father, "narrates_from", "حماد بن عيسى")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[1])

    assert stats.relation_resolved == 1
    assert nodes[1].canonical_narrator_id == father.id
    assert nodes[1].resolution_method == "relation_context"


def test_father_relation_can_use_ambiguous_previous_node_candidates(db: Session):
    book = add_book(db)
    nodes = add_chain(
        db,
        book=book,
        public_id="ambiguous-father",
        sequence=1,
        nodes_spec=[
            (norm("علي بن إبراهيم"), "named_narrator", None),
            (norm("أبيه"), "pronoun_relation", "father"),
            (norm("حماد بن عيسى"), "named_narrator", None),
        ],
    )
    add_narrator(db, "علي بن إبراهيم")
    add_narrator(db, "علي بن إبراهيم")
    father = add_narrator(db, "إبراهيم بن هاشم")
    add_narrator(db, "حماد بن عيسى")
    add_occurrence(db, father, "narrated_by", "علي بن إبراهيم")
    add_occurrence(db, father, "narrates_from", "حماد بن عيسى")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[0])
    db.refresh(nodes[1])

    assert nodes[0].review_status == "ambiguous"
    assert stats.relation_resolved == 1
    assert nodes[1].canonical_narrator_id == father.id
    assert "antecedent was an unresolved candidate" in (nodes[1].resolution_reason or "")


def test_known_ali_ibrahim_father_override_resolves_to_ibrahim_hashim(db: Session):
    book = add_book(db)
    nodes = add_chain(
        db,
        book=book,
        public_id="known-father",
        sequence=1,
        nodes_spec=[
            (norm("\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645"), "named_narrator", None),
            (norm("\u0623\u0628\u064a\u0647"), "pronoun_relation", "father"),
            (norm("\u0627\u0628\u0646 \u0623\u0628\u064a \u0639\u0645\u064a\u0631"), "named_narrator", None),
        ],
    )
    add_narrator(db, "\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645")
    add_narrator(db, "\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645")
    add_narrator(db, "\u0639\u0644\u064a \u0628\u0646 \u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0627\u0644\u062d\u0636\u0631\u0645\u064a")
    add_narrator(db, "\u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0627\u0644\u062d\u0636\u0631\u0645\u064a")
    add_narrator(db, "\u0625\u0628\u0631\u0627\u0647\u064a\u0645")
    father = add_narrator(
        db,
        "\u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0628\u0646 \u0647\u0627\u0634\u0645 "
        "\u0623\u0628\u0648 \u0625\u0633\u062d\u0627\u0642 \u0627\u0644\u0642\u0645\u064a",
    )
    add_narrator(db, "\u0627\u0628\u0646 \u0623\u0628\u064a \u0639\u0645\u064a\u0631")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[0])
    db.refresh(nodes[1])

    assert nodes[0].review_status == "ambiguous"
    assert stats.relation_resolved == 1
    assert nodes[1].canonical_narrator_id == father.id
    assert nodes[1].resolution_method == "relation_context"
    assert "Common Four Books chain pattern" in (nodes[1].resolution_reason or "")
    assert (
        db.query(ChainNodeCandidate)
        .filter(ChainNodeCandidate.chain_node_id == nodes[1].id, ChainNodeCandidate.match_type == "father_override")
        .count()
        == 1
    )


def test_bare_father_given_name_does_not_resolve_without_context(db: Session):
    book = add_book(db)
    nodes = add_chain(
        db,
        book=book,
        public_id="bare-father",
        sequence=1,
        nodes_spec=[
            (norm("\u062c\u0639\u0641\u0631 \u0628\u0646 \u0645\u062d\u0645\u062f"), "named_narrator", None),
            (norm("\u0623\u0628\u064a\u0647"), "pronoun_relation", "father"),
        ],
    )
    add_narrator(db, "\u062c\u0639\u0641\u0631 \u0628\u0646 \u0645\u062d\u0645\u062f")
    add_narrator(db, "\u0645\u062d\u0645\u062f")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[1])

    assert stats.relation_resolved == 0
    assert nodes[1].canonical_narrator_id is None
    assert nodes[1].review_status == "unresolved"


def test_chain_opening_anaphora_resolves_to_previous_chain_opening(db: Session):
    book = add_book(db)
    first_nodes = add_chain(
        db,
        book=book,
        public_id="first",
        sequence=1,
        nodes_spec=[(norm("علي بن إبراهيم"), "named_narrator", None)],
    )
    second_nodes = add_chain(
        db,
        book=book,
        public_id="second",
        sequence=2,
        nodes_spec=[
            (norm("عنه"), "pronoun_relation", "anaphora"),
            (norm("سهل بن زياد"), "named_narrator", None),
        ],
    )
    ali = add_narrator(db, "علي بن إبراهيم")
    add_narrator(db, "سهل بن زياد")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(first_nodes[0])
    db.refresh(second_nodes[0])

    assert first_nodes[0].canonical_narrator_id == ali.id
    assert stats.relation_resolved == 1
    assert second_nodes[0].canonical_narrator_id == ali.id
    assert second_nodes[0].resolution_method == "anaphora_previous_chain"


def test_grandfather_relation_can_resolve_after_father_node(db: Session):
    book = add_book(db)
    nodes = add_chain(
        db,
        book=book,
        public_id="grandfather",
        sequence=1,
        nodes_spec=[
            (norm("عيسى بن عبد الله بن محمد"), "named_narrator", None),
            (norm("أبيه"), "pronoun_relation", "father"),
            (norm("جده"), "pronoun_relation", "grandfather"),
            (norm("علي"), "named_narrator", None),
        ],
    )
    son = add_narrator(db, "عيسى بن عبد الله بن محمد")
    father = add_narrator(db, "عبد الله بن محمد")
    grandfather = add_narrator(db, "محمد بن علي")
    add_narrator(db, "علي")
    add_occurrence(db, father, "narrated_by", son.canonical_name_ar)
    add_occurrence(db, grandfather, "narrated_by", father.canonical_name_ar)
    add_occurrence(db, grandfather, "narrates_from", "علي")
    db.commit()

    stats = rebuild_chain_node_resolutions(db, source_book_ids=["11005"])
    db.refresh(nodes[1])
    db.refresh(nodes[2])

    assert stats.relation_resolved == 2
    assert nodes[1].canonical_narrator_id == father.id
    assert nodes[2].canonical_narrator_id == grandfather.id
