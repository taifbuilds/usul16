"""Tests for GET /transmission-graph/edge-evidence."""

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
    PersonRelation,
    PersonResolutionDecision,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian as norm
from eshia_research.rijal.effective_resolution import ADMIN_REVIEWER
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION


@pytest.fixture(autouse=True)
def _clear_graph_cache():
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


def _person(db: Session, name: str) -> Person:
    person = Person(canonical_name_ar=name, canonical_name_norm=norm(name), kind="individual")
    db.add(person)
    db.flush()
    return person


def _edge(db: Session, book: Book, seq: int, student: Person, teacher: Person):
    hadith = Hadith(
        public_id=f"k-{seq}", book_id=book.id, sequence_in_book=seq, sequence_in_page=1,
        volume_start=1, volume_end=1, page_start=seq, page_end=seq,
        full_text_raw="x", full_text_normalised="x", matn_raw="x", matn_normalised="x",
        source_url="u", isnad_raw=f"{student.canonical_name_ar} عن {teacher.canonical_name_ar}",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad="x")
    db.add(chain)
    db.flush()
    nodes = {}
    for pos, person in ((0, student), (1, teacher)):
        node = ChainNode(chain_id=chain.id, position=pos, raw_token=person.canonical_name_ar,
                         token_normalised=person.canonical_name_norm, node_type="named_narrator")
        db.add(node)
        db.flush()
        db.add(MentionResolution(chain_node_id=node.id, person_id=person.id, rank=1,
                                 status="resolved", method="surface_full",
                                 resolver_version=PERSON_RESOLVER_VERSION))
        nodes[pos] = node
    db.flush()
    return nodes[0], nodes[1]


@pytest.fixture()
def seeded(db: Session):
    book = Book(source_book_id="11005", title_original="k", title_normalised="k", source_url="u")
    db.add(book)
    db.flush()
    attar = _person(db, "محمد بن يحيى العطار")
    ashari = _person(db, "أحمد بن محمد بن عيسى الأشعري")
    qumi = _person(db, "أحمد بن محمد بن عيسى الأشعري القمي")
    db.add(PersonRelation(person_id=ashari.id, related_person_id=qumi.id,
                          relation_kind="same_person_as", source_note="test"))
    for seq in range(1, 4):
        _edge(db, book, seq, attar, ashari)
    _edge(db, book, 4, attar, qumi)  # split identity merges into the same edge
    db.commit()
    return book, attar, ashari, qumi


def test_edge_evidence_returns_cluster_hadiths_ordered(client: TestClient, seeded):
    _, attar, ashari, qumi = seeded
    root = min(ashari.id, qumi.id)
    body = client.get(
        f"/transmission-graph/edge-evidence?source_person_id={attar.id}&target_person_id={root}"
    ).json()
    # 3 ashari + 1 qumi hadith collapse into the one merged edge.
    assert body["total"] == 4
    seqs = [item["sequence_in_book"] for item in body["items"]]
    assert seqs == sorted(seqs)
    assert body["items"][0]["public_id"] == "k-1"
    assert body["items"][0]["isnad_excerpt"]


def test_edge_evidence_member_id_returns_nothing(client: TestClient, seeded):
    # The non-root member id is never a graph node; it resolves to no edge.
    _, attar, ashari, qumi = seeded
    non_root = max(ashari.id, qumi.id)
    body = client.get(
        f"/transmission-graph/edge-evidence?source_person_id={attar.id}&target_person_id={non_root}"
    ).json()
    assert body["total"] == 0
    assert body["items"] == []


def test_edge_evidence_respects_limit(client: TestClient, seeded):
    _, attar, ashari, qumi = seeded
    root = min(ashari.id, qumi.id)
    body = client.get(
        f"/transmission-graph/edge-evidence?source_person_id={attar.id}&target_person_id={root}&limit=2"
    ).json()
    assert body["total"] == 4  # total is the full distinct count
    assert len(body["items"]) == 2  # but only `limit` are returned


def test_edge_evidence_reflects_demoting_decision(client: TestClient, db: Session, seeded):
    # A keep-ambiguous decision on a teacher node drops its hadith from evidence,
    # agreeing with the graph.
    book, attar, ashari, qumi = seeded
    # Add a fresh single-hadith edge we can demote cleanly.
    other = _person(db, "الحسن بن محبوب")
    _, teacher_node = _edge(db, book, 99, attar, other)
    db.commit()
    before = client.get(
        f"/transmission-graph/edge-evidence?source_person_id={attar.id}&target_person_id={other.id}"
    ).json()
    assert before["total"] == 1

    db.add(PersonResolutionDecision(
        chain_node_id=teacher_node.id, decision_type="keep_ambiguous",
        confidence_tier="high", reviewer=ADMIN_REVIEWER, resolver_version=PERSON_RESOLVER_VERSION,
    ))
    db.commit()
    after = client.get(
        f"/transmission-graph/edge-evidence?source_person_id={attar.id}&target_person_id={other.id}"
    ).json()
    assert after["total"] == 0
