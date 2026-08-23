"""Tests for GET /transmission-graph — the corpus-wide narrator network."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.api.routes_books import clear_transmission_graph_cache
from eshia_research.db import Base, get_db
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Narrator,
    Person,
    PersonGeneration,
    PersonRelation,
    PersonResolutionDecision,
    RijalEntry,
    RijalOccurrence,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.effective_resolution import ADMIN_REVIEWER
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION


@pytest.fixture(autouse=True)
def _clear_graph_cache():
    # The pair-aggregation TTL cache is module-level and lives across the
    # shared test process; without this, a later test's identical cache key
    # (same book/version/no-decisions) would serve a prior test's DB.
    clear_transmission_graph_cache()
    yield
    clear_transmission_graph_cache()


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


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
    person._narrator_id = narrator.id  # test-only handle for occurrence seeding
    return person


def _edge(db: Session, book: Book, seq: int, student: Person, teacher: Person,
          *, student_status: str = "resolved", teacher_status: str = "resolved"):
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
    made = {}
    for pos, person, status in ((0, student, student_status), (1, teacher, teacher_status)):
        node = ChainNode(chain_id=chain.id, position=pos, raw_token=person.canonical_name_ar,
                         token_normalised=person.canonical_name_norm, node_type="named_narrator")
        db.add(node)
        db.flush()
        db.add(MentionResolution(chain_node_id=node.id, person_id=person.id, rank=1,
                                 status=status, method="surface_full",
                                 resolver_version=PERSON_RESOLVER_VERSION))
        made[pos] = node
    db.flush()
    return made[0], made[1]  # (student_node, teacher_node)


def _decide(db: Session, chain_node, decision_type: str, *, selected_person=None,
            reviewer: str = ADMIN_REVIEWER, version: str = PERSON_RESOLVER_VERSION) -> None:
    db.add(PersonResolutionDecision(
        chain_node_id=chain_node.id,
        selected_person_id=selected_person.id if selected_person is not None else None,
        decision_type=decision_type, confidence_tier="high",
        reviewer=reviewer, resolver_version=version,
    ))
    db.flush()


@pytest.fixture()
def seeded(db: Session):
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    attar = _person(db, "محمد بن يحيى العطار")
    ashari = _person(db, "أحمد بن محمد بن عيسى الأشعري")
    qumi = _person(db, "أحمد بن محمد بن عيسى الأشعري القمي")
    # al-Khoei rules 'the Ash'ari and the Qumi entries are one man'.
    db.add(PersonRelation(person_id=ashari.id, related_person_id=qumi.id,
                          relation_kind="same_person_as", source_note="test"))
    sadiq = _person(db, "جعفر بن محمد الصادق عليه السلام", kind="masum")
    for seq in range(1, 4):
        _edge(db, book, seq, attar, ashari)
    _edge(db, book, 4, attar, qumi)  # split identity: must merge into the same edge
    _edge(db, book, 5, ashari, sadiq)  # weak edge (1 hadith)
    db.commit()
    return attar, ashari, qumi, sadiq


def test_graph_merges_same_person_clusters(client: TestClient, seeded):
    attar, ashari, qumi, _ = seeded
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    root = min(ashari.id, qumi.id)
    edge = next(e for e in body["edges"] if e["source"] == attar.id)
    # The 3 ashari hadiths + 1 qumi hadith collapse into one weighted edge.
    assert edge["target"] == root
    assert edge["count"] == 4
    merged_node = next(n for n in body["nodes"] if n["id"] == root)
    assert sorted(merged_node["merged_person_ids"]) == sorted([ashari.id, qumi.id])


def test_graph_min_count_prunes_weak_edges(client: TestClient, seeded):
    attar, ashari, qumi, sadiq = seeded
    body = client.get("/transmission-graph?source_book_id=11005&min_count=2").json()
    # The 1-hadith edge to al-Sadiq is pruned; the x4 edge survives.
    assert all(e["target"] != sadiq.id for e in body["edges"])
    assert len(body["edges"]) == 1
    assert body["total_edges_unfiltered"] == 2
    # Pruned imam is no longer a node either.
    assert all(n["id"] != sadiq.id for n in body["nodes"])


def test_graph_marks_imams_and_links_narrators(client: TestClient, seeded):
    attar, _, _, sadiq = seeded
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    imam = next(n for n in body["nodes"] if n["id"] == sadiq.id)
    assert imam["kind"] == "imam"
    attar_node = next(n for n in body["nodes"] if n["id"] == attar.id)
    assert attar_node["kind"] == "narrator"
    assert attar_node["narrator_id"] is not None


# --- decision-aware graph (Tamyiz review corrections flow into the graph) ---


@pytest.fixture()
def two_person_book(db: Session):
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    student = _person(db, "زرارة بن أعين")
    teacher = _person(db, "أحمد بن محمد بن عيسى")
    other = _person(db, "الحسن بن محبوب")
    return book, student, teacher, other


def test_override_remaps_edge_target(client: TestClient, db: Session, two_person_book):
    book, student, teacher, other = two_person_book
    _, teacher_node = _edge(db, book, 1, student, teacher)
    _decide(db, teacher_node, "approve_external_override", selected_person=other)
    db.commit()

    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["decisions_applied"] == 1
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["target"] == other.id  # override redirected the teacher


def test_keep_ambiguous_removes_edge(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _, teacher_node = _edge(db, book, 1, student, teacher)
    _decide(db, teacher_node, "keep_ambiguous")
    db.commit()

    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["edges"] == []
    assert all(n["id"] != teacher.id for n in body["nodes"])


def test_override_promotes_ambiguous_node(client: TestClient, db: Session, two_person_book):
    book, student, teacher, other = two_person_book
    # Teacher is only ambiguous at rank 1 -> normally excluded from the graph.
    _, teacher_node = _edge(db, book, 1, student, teacher, teacher_status="ambiguous")
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["edges"] == []  # ambiguous teacher, no edge yet

    _decide(db, teacher_node, "approve_external_override", selected_person=other)
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["target"] == other.id  # the override PROMOTED an ambiguous node


def test_approve_current_is_a_noop(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _, teacher_node = _edge(db, book, 1, student, teacher)
    _decide(db, teacher_node, "approve_current")
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["target"] == teacher.id


def test_wrong_reviewer_decision_is_ignored(client: TestClient, db: Session, two_person_book):
    book, student, teacher, other = two_person_book
    _, teacher_node = _edge(db, book, 1, student, teacher)
    _decide(db, teacher_node, "approve_external_override", selected_person=other,
            reviewer="codex-machine-v1")  # not the admin reviewer
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["decisions_applied"] == 0
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["target"] == teacher.id


def test_stale_resolver_version_decision_is_ignored(client: TestClient, db: Session, two_person_book):
    book, student, teacher, other = two_person_book
    _, teacher_node = _edge(db, book, 1, student, teacher)
    _decide(db, teacher_node, "approve_external_override", selected_person=other,
            version="tamyiz_OLD")
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["target"] == teacher.id


def test_response_has_computed_at(client: TestClient, seeded):
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["computed_at"] is not None


# --- Phase 1: book-set seam + per-node footprint + narrator directory ---


def test_graph_reports_book_footprint_and_ids(client: TestClient, seeded):
    attar, _, _, _ = seeded
    body = client.get("/transmission-graph?min_count=1").json()
    assert body["book_ids"] == ["11005"]
    attar_node = next(n for n in body["nodes"] if n["id"] == attar.id)
    # This fixture only contains al-Kafi, so its footprint mirrors the count.
    assert attar_node["books"] == {"11005": attar_node["hadith_count"]}
    assert attar_node["reliability"] is None


def test_graph_accepts_polished_faqih_without_fallback(client: TestClient, seeded):
    # Faqih passed the graph gate: an explicit request must retain its book id
    # rather than silently substituting al-Kafi. This fixture has no Faqih rows,
    # so an empty graph is the honest result.
    body = client.get("/transmission-graph?books=11021&min_count=1").json()
    assert body["book_ids"] == ["11021"]
    assert body["nodes"] == []


def test_narrator_directory_search_and_charted_count(client: TestClient, db: Session, seeded):
    attar, _, _, _ = seeded
    # A findable narrator with no charted transmission edge.
    lonely = _person(db, "راو غير مذكور في الأسانيد")
    db.commit()

    page = client.get("/narrators?query=العطار").json()
    hit = next(e for e in page["entries"] if e["narrator_id"] == attar._narrator_id)
    assert hit["charted_hadith_count"] == 4  # 3 al-Ash'ari + 1 al-Qumi hadiths

    page2 = client.get("/narrators?query=غير مذكور").json()
    entry = next(e for e in page2["entries"] if e["narrator_id"] == lonely._narrator_id)
    # Findable and openable, but honestly reported as not yet charted.
    assert entry["charted_hadith_count"] == 0
    assert page2["total"] >= 1


def test_paths_finds_directed_isnad(client: TestClient, seeded):
    attar, ashari, qumi, sadiq = seeded
    root = min(ashari.id, qumi.id)
    res = client.get(
        f"/transmission-graph/paths?from_person={attar.id}&to_person={sadiq.id}"
    ).json()
    assert res["found"] is True
    assert res["reversed"] is False
    path = res["paths"][0]
    assert [n["id"] for n in path["nodes"]] == [attar.id, root, sadiq.id]
    assert path["length"] == 2
    assert path["hops"][0]["count"] == 4  # attar->ashari, 3 ashari + 1 qumi merged
    assert path["hops"][1]["count"] == 1  # ashari-root -> al-Sadiq


def test_paths_reversed_when_picked_backwards(client: TestClient, seeded):
    attar, _, _, sadiq = seeded
    # No isnad runs al-Sadiq -> al-Attar, but the reverse exists; return it
    # oriented in transmission order and flag reversed.
    res = client.get(
        f"/transmission-graph/paths?from_person={sadiq.id}&to_person={attar.id}"
    ).json()
    assert res["found"] is True
    assert res["reversed"] is True
    assert res["paths"][0]["nodes"][0]["id"] == attar.id
    assert res["paths"][0]["nodes"][-1]["id"] == sadiq.id


def test_paths_none_when_disconnected(client: TestClient, db: Session, two_person_book):
    book, student, teacher, other = two_person_book
    _edge(db, book, 1, student, teacher)
    db.commit()
    # `other` sits in no chain — no path either way.
    res = client.get(
        f"/transmission-graph/paths?from_person={student.id}&to_person={other.id}"
    ).json()
    assert res["found"] is False
    assert res["paths"] == []


def test_include_uncertain_surfaces_marked_best_guesses(
    client: TestClient, db: Session, two_person_book
):
    book, student, teacher, _ = two_person_book
    # Teacher only ever resolves ambiguously — the resolver's rank-1 best guess.
    _edge(db, book, 1, student, teacher, teacher_status="ambiguous")
    db.commit()

    # Default (confident-only): the ambiguous teacher produces no edge.
    base = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert base["edges"] == []

    # With include_uncertain the best-guess edge appears — clearly flagged, so it
    # is never mistaken for a confirmed transmission.
    unc = client.get(
        "/transmission-graph?source_book_id=11005&min_count=1&include_uncertain=1"
    ).json()
    assert unc["include_uncertain"] is True
    edge = next(e for e in unc["edges"] if e["source"] == student.id)
    assert edge["target"] == teacher.id
    assert edge["uncertain"] is True
    teacher_node = next(n for n in unc["nodes"] if n["id"] == teacher.id)
    student_node = next(n for n in unc["nodes"] if n["id"] == student.id)
    assert teacher_node["uncertain"] is True
    assert student_node["uncertain"] is False  # a confident mention isn't provisional


# --- quality overlay (Mu'jam corroboration per edge) ---


def _occ(db: Session, narrator_id: int, direction: str, related: str) -> None:
    db.add(RijalOccurrence(
        entry_id=1, narrator_id=narrator_id, direction=direction,
        related_name_raw=related, related_name_normalised=norm(related),
        evidence_text_raw=related,
    ))


def test_quality_off_leaves_fields_null(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    assert body["quality"] is False
    assert body["edges"][0]["quality"] is None


def test_quality_marks_corroborated_edge(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    # al-Khoei documents the teacher is narrated by the student, well past threshold.
    _occ(db, teacher._narrator_id, "narrated_by", "زرارة بن أعين")
    for i in range(6):
        _occ(db, teacher._narrator_id, "narrated_by", f"فلان {i}")
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    assert body["quality"] is True
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["quality"] == "corroborated"


def test_quality_marks_contradicted_edge(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    # Teacher well attested, but the student is not among the documented narrators.
    for i in range(7):
        _occ(db, teacher._narrator_id, "narrated_by", f"شخص {i}")
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["quality"] == "contradicted"


def test_quality_flags_generation_violation(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    # Teacher a strictly LATER generation than the student -> impossible.
    db.add(PersonGeneration(person_id=student.id, gen_lo=2, gen_hi=2, gen_point=2,
                            method="imam_fixed", resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=7, gen_hi=7, gen_point=7,
                            method="imam_fixed", resolver_version=PERSON_RESOLVER_VERSION))
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["gen_violation"] is True


def test_quality_ignores_propagated_only_generation(client: TestClient, db: Session, two_person_book):
    """A propagated-only generation is advisory and must NOT declare an edge
    impossible, even when inverted (the unanchored-hub false-positive case)."""
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    db.add(PersonGeneration(person_id=student.id, gen_lo=6, gen_hi=6, gen_point=6,
                            method="propagated", resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=7, gen_hi=7, gen_point=7,
                            method="propagated", resolver_version=PERSON_RESOLVER_VERSION))
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["gen_violation"] is None


def test_quality_gap_of_one_is_within_tolerance(client: TestClient, db: Session, two_person_book):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    db.add(PersonGeneration(person_id=student.id, gen_lo=4, gen_hi=4, gen_point=4,
                            method="ashab_anchor", resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=5, gen_hi=5, gen_point=5,
                            method="imam_fixed", resolver_version=PERSON_RESOLVER_VERSION))
    db.commit()
    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["gen_violation"] is False


def test_quality_ignores_generation_rows_already_marked_conflict(
    client: TestClient, db: Session, two_person_book
):
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    db.add(PersonGeneration(person_id=student.id, gen_lo=2, gen_hi=2, gen_point=2,
                            method="conflict", resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=7, gen_hi=7, gen_point=7,
                            method="conflict", resolver_version=PERSON_RESOLVER_VERSION))
    db.commit()

    body = client.get("/transmission-graph?source_book_id=11005&min_count=1&quality=1").json()
    edge = next(e for e in body["edges"] if e["source"] == student.id)
    assert edge["gen_violation"] is None


def test_node_generation_excludes_conflict_rows(client: TestClient, db: Session, two_person_book):
    """A conflict-method person renders as undated (generation None) in the layout,
    not confidently banded at a bogus layer."""
    book, student, teacher, _ = two_person_book
    _edge(db, book, 1, student, teacher)
    # Student has a clean generation; teacher's is self-contradictory.
    db.add(PersonGeneration(person_id=student.id, gen_lo=5, gen_hi=5, gen_point=5,
                            method="ashab_anchor", resolver_version=PERSON_RESOLVER_VERSION))
    db.add(PersonGeneration(person_id=teacher.id, gen_lo=2, gen_hi=8, gen_point=4,
                            method="conflict", resolver_version=PERSON_RESOLVER_VERSION))
    db.commit()

    body = client.get("/transmission-graph?source_book_id=11005&min_count=1").json()
    student_node = next(n for n in body["nodes"] if n["id"] == student.id)
    teacher_node = next(n for n in body["nodes"] if n["id"] == teacher.id)
    assert student_node["generation"] == 5
    assert teacher_node["generation"] is None
