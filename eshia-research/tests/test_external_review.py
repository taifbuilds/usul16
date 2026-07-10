from pathlib import Path

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
    PersonResolutionDecision,
    PersonResolutionExternalReview,
    PersonSurfaceForm,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.external_review import (
    import_external_review_file,
    parse_external_review_text,
    promote_external_reviews_to_admin_decisions,
)
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


def _case_db(db: Session) -> tuple[ChainNode, Person]:
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    hadith = Hadith(
        public_id="alkafi-test-1",
        book_id=book.id,
        sequence_in_book=1,
        sequence_in_page=1,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw="حدثنا الحسن بن محبوب قال",
        full_text_normalised="x",
        isnad_raw="حدثنا الحسن بن محبوب",
        isnad_normalised="x",
        matn_raw="قال",
        matn_normalised="x",
        source_url="u",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw)
    db.add(chain)
    db.flush()
    node = ChainNode(
        id=605166,
        chain_id=chain.id,
        position=0,
        raw_token="الحسن بن محبوب",
        token_normalised=norm("الحسن بن محبوب"),
        node_type="named_narrator",
    )
    db.add(node)
    person = Person(canonical_name_ar="الحسن بن محبوب", canonical_name_norm=norm("الحسن بن محبوب"))
    db.add(person)
    db.flush()
    db.add(PersonSurfaceForm(person_id=person.id, form_raw=person.canonical_name_ar, form_norm=person.canonical_name_norm, derivation="full"))
    db.add(MentionResolution(
        chain_node_id=node.id,
        person_id=person.id,
        rank=1,
        status="resolved",
        method="surface_full",
        resolver_version=PERSON_RESOLVER_VERSION,
    ))
    db.add(PersonResolutionDecision(
        chain_node_id=node.id,
        selected_person_id=person.id,
        decision_type="needs_external_review",
        confidence_tier="medium",
        reviewer="codex-machine-v1",
        resolver_version=PERSON_RESOLVER_VERSION,
    ))
    db.commit()
    return node, person


def test_parse_external_review_repairs_mojibake():
    clean = """Case ID: Case 001 — alkafi-1:chain1:pos0:node605166
Verdict: approve_current
Correct person, if any: الحسن بن محبوب
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A
"""
    mojibake = clean.encode("utf-8").decode("cp1252")
    cases = parse_external_review_text(mojibake)
    assert len(cases) == 1
    assert cases[0].correct_person_text == "الحسن بن محبوب"
    assert cases[0].confidence_tier == "high"


def test_parse_external_review_keeps_case_heading_out_of_source_reference():
    text = """### Case 001: alkafi-1:chain1:pos0:node605166
Case ID: alkafi-1:chain1:pos0:node605166
Verdict: approve_current
Correct person, if any: \u0627\u0644\u062d\u0633\u0646
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A

### Case 002: alkafi-2:chain1:pos0:node605167
Case ID: alkafi-2:chain1:pos0:node605167
Verdict: keep_ambiguous
Correct person, if any: N/A
Confidence: low
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A
"""
    cases = parse_external_review_text(text)

    assert len(cases) == 2
    assert cases[0].source_reference == "N/A"
    assert "### Case" not in cases[0].raw_case_text


def test_import_external_review_matches_current_top_person(db: Session):
    _node, person = _case_db(db)
    text = """Case ID: Case 001 — alkafi-1:chain1:pos0:node605166
Verdict: approve_current
Correct person, if any: الحسن بن محبوب
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A
"""
    path = Path(db._tmp_path) / "result.md"
    path.write_text(text, encoding="utf-8")

    stats = import_external_review_file(db, path)

    assert stats.rows_written == 1
    assert stats.matched_person == 1
    review = db.execute(select(PersonResolutionExternalReview)).scalar_one()
    assert review.matched_person_id == person.id
    assert review.verdict == "approve_current"


def test_import_external_review_matches_specific_override_names(db: Session):
    node, _current_person = _case_db(db)
    targets = [
        Person(
            canonical_name_ar="المفضل بن صالح الأسدي النخاس",
            canonical_name_norm=norm("المفضل بن صالح الأسدي النخاس"),
        ),
        Person(
            canonical_name_ar="محمد بن يحيى أبو جعفر العطار",
            canonical_name_norm=norm("محمد بن يحيى أبو جعفر العطار"),
        ),
        Person(
            canonical_name_ar="علي بن إبراهيم بن هاشم",
            canonical_name_norm=norm("علي بن إبراهيم بن هاشم"),
        ),
    ]
    distractors = [
        Person(
            canonical_name_ar="المفضل بن صالح الأسدي",
            canonical_name_norm=norm("المفضل بن صالح الأسدي"),
        ),
        Person(
            canonical_name_ar="محمد بن يحيى أبو حنيفة",
            canonical_name_norm=norm("محمد بن يحيى أبو حنيفة"),
        ),
        Person(
            canonical_name_ar="أحمد بن علي بن إبراهيم بن هاشم",
            canonical_name_norm=norm("أحمد بن علي بن إبراهيم بن هاشم"),
        ),
    ]
    db.add_all(targets + distractors)
    db.flush()
    for person in targets + distractors:
        db.add(
            PersonSurfaceForm(
                person_id=person.id,
                form_raw=person.canonical_name_ar,
                form_norm=person.canonical_name_norm,
                derivation="full",
            )
        )
    db.commit()

    text = f"""Case ID: Case 006 — alkafi-2:chain1:pos3:node{node.id}
Verdict: override_person
Correct person, if any: أبو جميلة المفضل بن صالح الأسدي النخاس
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: أبو جميلة المفضل بن صالح الأسدي النخاس — Muʿjam Rijāl al-Ḥadīth, vol. 19, p. 311.

Case ID: Case 014 — alkafi-5:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: محمد بن يحيى أبو جعفر العطار القمي
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: محمد بن يحيى أبو جعفر العطار القمي — Muʿjam Rijāl al-Ḥadīth, vol. 19, p. 33.

Case ID: Case 023 — alkafi-9:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: علي بن إبراهيم بن هاشم أبو الحسن القمي
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: علي بن إبراهيم بن هاشم أبو الحسن القمي — Rijāl al-Najāshī, p. 260.
"""
    path = Path(db._tmp_path) / "override-result.md"
    path.write_text(text, encoding="utf-8")

    stats = import_external_review_file(db, path)

    assert stats.rows_written == 3
    assert stats.matched_person == 3
    reviews = db.execute(
        select(PersonResolutionExternalReview).order_by(PersonResolutionExternalReview.case_id)
    ).scalars().all()
    assert [review.matched_person_id for review in reviews] == [person.id for person in targets]


def test_import_external_review_matches_corrected_large_packet_variants(db: Session):
    node, _current_person = _case_db(db)
    chain = db.get(Chain, node.chain_id)
    unresolved_node = ChainNode(
        id=605167,
        chain_id=chain.id,
        position=1,
        raw_token="\u0628\u0631\u064a\u062f \u0627\u0644\u0639\u062c\u0644\u064a",
        token_normalised=norm("\u0628\u0631\u064a\u062f \u0627\u0644\u0639\u062c\u0644\u064a"),
        node_type="named_narrator",
    )
    db.add(unresolved_node)

    target_names = [
        "\u0627\u0644\u062d\u0633\u0646 \u0628\u0646 \u0645\u062d\u0628\u0648\u0628 \u0627\u0644\u0632\u0631\u0627\u062f",
        "\u0645\u062d\u0645\u062f \u0628\u0646 \u0639\u064a\u0633\u0649 \u0628\u0646 \u0639\u0628\u064a\u062f \u0628\u0646 \u064a\u0642\u0637\u064a\u0646",
        "\u064a\u0648\u0646\u0633 \u0628\u0646 \u0639\u0628\u062f \u0627\u0644\u0631\u062d\u0645\u0646",
        "\u0628\u0631\u064a\u062f \u0628\u0646 \u0645\u0639\u0627\u0648\u064a\u0629",
    ]
    targets = [
        Person(canonical_name_ar=name, canonical_name_norm=norm(name))
        for name in target_names
    ]
    db.add_all(targets)
    db.flush()
    for person in targets:
        db.add(
            PersonSurfaceForm(
                person_id=person.id,
                form_raw=person.canonical_name_ar,
                form_norm=person.canonical_name_norm,
                derivation="full",
            )
        )
    db.add(
        MentionResolution(
            chain_node_id=unresolved_node.id,
            person_id=None,
            rank=1,
            status="unresolved",
            method="no_surface_form",
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    db.add(
        PersonResolutionDecision(
            chain_node_id=unresolved_node.id,
            selected_person_id=None,
            decision_type="needs_external_review",
            confidence_tier="low",
            reviewer="codex-machine-v1",
            resolver_version=PERSON_RESOLVER_VERSION,
        )
    )
    db.commit()

    slash_name = "\u0627\u0644\u062d\u0633\u0646 \u0628\u0646 \u0645\u062d\u0628\u0648\u0628 \u0627\u0644\u0633\u0631\u0627\u062f / \u0627\u0644\u0632\u0631\u0627\u062f"
    yaqtini_name = "\u0645\u062d\u0645\u062f \u0628\u0646 \u0639\u064a\u0633\u0649 \u0628\u0646 \u0639\u0628\u064a\u062f \u0627\u0644\u064a\u0642\u0637\u064a\u0646\u064a"
    yunus_mawla = "\u064a\u0648\u0646\u0633 \u0628\u0646 \u0639\u0628\u062f \u0627\u0644\u0631\u062d\u0645\u0646 \u0645\u0648\u0644\u0649 \u0622\u0644 \u064a\u0642\u0637\u064a\u0646"
    burayd_ijli = "\u0628\u0631\u064a\u062f \u0628\u0646 \u0645\u0639\u0627\u0648\u064a\u0629 \u0627\u0644\u0639\u062c\u0644\u064a"
    text = f"""Case ID: Case 010 - alkafi-10:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: {slash_name}
Confidence: medium
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: {slash_name} - source.

Case ID: Case 011 - alkafi-11:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: {yaqtini_name}
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: {yaqtini_name} - source.

Case ID: Case 012 - alkafi-12:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: {yunus_mawla}
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: {yunus_mawla} - source.

Case ID: Case 013 - alkafi-13:chain1:pos1:node{unresolved_node.id}
Verdict: approve_current
Correct person, if any: {burayd_ijli}
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A
"""
    path = Path(db._tmp_path) / "large-corrected-result.md"
    path.write_text(text, encoding="utf-8")

    stats = import_external_review_file(db, path)

    assert stats.rows_written == 4
    assert stats.matched_person == 4
    reviews = db.execute(
        select(PersonResolutionExternalReview).order_by(PersonResolutionExternalReview.case_id)
    ).scalars().all()
    assert [review.matched_person_id for review in reviews] == [person.id for person in targets]

    promote_external_reviews_to_admin_decisions(db, source_book_id="11005")
    fallback_decision = db.execute(
        select(PersonResolutionDecision).where(
            PersonResolutionDecision.chain_node_id == unresolved_node.id,
            PersonResolutionDecision.reviewer == "codex-admin-external-v1",
        )
    ).scalar_one()
    assert fallback_decision.selected_person_id == targets[-1].id
    assert fallback_decision.decision_type == "approve_external_override"


def test_promote_external_review_writes_separate_admin_decision(db: Session):
    node, _current_person = _case_db(db)
    target = Person(
        canonical_name_ar="محمد بن يحيى أبو جعفر العطار",
        canonical_name_norm=norm("محمد بن يحيى أبو جعفر العطار"),
    )
    db.add(target)
    db.flush()
    text = f"""Case ID: Case 014 — alkafi-5:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: محمد بن يحيى أبو جعفر العطار القمي
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: محمد بن يحيى أبو جعفر العطار القمي — Muʿjam Rijāl al-Ḥadīth, vol. 19, p. 33.
"""
    path = Path(db._tmp_path) / "promote-result.md"
    path.write_text(text, encoding="utf-8")
    import_external_review_file(db, path)

    stats = promote_external_reviews_to_admin_decisions(db, source_book_id="11005")

    assert stats.decisions_written == 1
    assert stats.decision_counts["approve_external_override"] == 1
    decision = db.execute(
        select(PersonResolutionDecision).where(
            PersonResolutionDecision.reviewer == "codex-admin-external-v1"
        )
    ).scalar_one()
    assert decision.chain_node_id == node.id
    assert decision.selected_person_id == target.id
    assert decision.decision_type == "approve_external_override"


def test_promote_external_review_uses_latest_review_per_node(db: Session):
    node, current_person = _case_db(db)
    target_name = "\u0645\u062d\u0645\u062f \u0628\u0646 \u064a\u062d\u064a\u0649 \u0623\u0628\u0648 \u062c\u0639\u0641\u0631 \u0627\u0644\u0639\u0637\u0627\u0631"
    target = Person(canonical_name_ar=target_name, canonical_name_norm=norm(target_name))
    db.add(target)
    db.flush()

    first = f"""Case ID: Case 001 - alkafi-1:chain1:pos0:node{node.id}
Verdict: approve_current
Correct person, if any: {current_person.canonical_name_ar}
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: N/A
"""
    second = f"""Case ID: Case 001 - alkafi-1:chain1:pos0:node{node.id}
Verdict: override_person
Correct person, if any: {target_name}
Confidence: high
Evidence consulted: source
Reasoning: clear
If override_person: canonical Arabic name and source reference: {target_name} - source.
"""
    first_path = Path(db._tmp_path) / "first-result.md"
    second_path = Path(db._tmp_path) / "second-result.md"
    first_path.write_text(first, encoding="utf-8")
    second_path.write_text(second, encoding="utf-8")
    import_external_review_file(db, first_path, source_label="first")
    import_external_review_file(db, second_path, source_label="second")

    stats = promote_external_reviews_to_admin_decisions(db, source_book_id="11005")

    assert stats.reviews_seen == 2
    assert stats.decisions_written == 1
    decision = db.execute(
        select(PersonResolutionDecision).where(
            PersonResolutionDecision.reviewer == "codex-admin-external-v1"
        )
    ).scalar_one()
    assert decision.selected_person_id == target.id
    assert decision.decision_type == "approve_external_override"
