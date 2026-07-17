import hashlib

import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    HadithTranslation,
    MentionResolution,
    Narrator,
    Person,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.isnad_renderer import render_hadith_isnad
from eshia_research.translation.planner import build_translation_plan, persist_translation_plan
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.publication import source_hashes_are_current
from eshia_research.translation.text import sha256_text
from eshia_research.translation.thaqalayn_importer import (
    ThaqalaynRecord,
    build_matches,
    import_thaqalayn_al_kafi,
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


def add_book(db: Session, source_book_id: str = "11005") -> Book:
    book = Book(
        source_book_id=source_book_id,
        title_original="al-kafi",
        title_normalised="al-kafi",
        source_url=f"https://lib.eshia.ir/{source_book_id}",
    )
    db.add(book)
    db.flush()
    return book


def add_hadith(
    db: Session,
    book: Book,
    public_id: str,
    seq: int,
    matn: str,
    *,
    isnad: str = "محمد بن يعقوب عن علي بن إبراهيم",
    review_status: str = "pending",
    volume_start: int = 1,
) -> Hadith:
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        sequence_in_book=seq,
        sequence_in_page=seq,
        printed_number=str(seq),
        volume_start=volume_start,
        volume_end=volume_start,
        page_start=1,
        page_end=1,
        full_text_raw=f"{isnad} {matn}",
        full_text_normalised=normalise_arabic_persian(f"{isnad} {matn}"),
        isnad_raw=isnad,
        isnad_normalised=normalise_arabic_persian(isnad),
        matn_raw=matn,
        matn_normalised=normalise_arabic_persian(matn),
        source_url="https://lib.eshia.ir/11005/1/1",
        review_status=review_status,
    )
    db.add(hadith)
    db.flush()
    return hadith


def test_translation_plan_counts_visible_pending_rows_and_buckets(db: Session):
    book = add_book(db)
    add_hadith(db, book, "alkafi-1", 1, "قال أبو عبد الله ع: العلم نور.")
    add_hadith(db, book, "alkafi-2", 2, "x" * 400)
    add_hadith(
        db,
        book,
        "alkafi-fragment",
        3,
        "editorial",
        review_status="rejected_non_hadith_fragment",
    )

    plan = build_translation_plan(db, source_book_id="11005")

    assert plan.total_hadiths == 2
    assert plan.planned_hadiths == 2
    assert plan.bucket_counts["short_160"] == 1
    assert plan.bucket_counts["long_640"] == 1
    assert plan.estimated_input_tokens > 0
    assert plan.estimated_output_tokens > 0


def test_translation_plan_skips_current_matching_source_hash(db: Session):
    book = add_book(db)
    current = add_hadith(db, book, "alkafi-1", 1, "قال أبو عبد الله ع: العلم نور.")
    add_hadith(db, book, "alkafi-2", 2, "قال: نعم.")
    db.add(
        HadithTranslation(
            hadith_id=current.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            source_full_sha256=sha256_text(current.full_text_raw),
            source_isnad_sha256=sha256_text(current.isnad_raw),
            source_matn_sha256=sha256_text(current.matn_raw),
            matn_translation="Knowledge is light.",
            status="published",
            risk_level="green",
        )
    )
    db.flush()

    plan = build_translation_plan(db, source_book_id="11005")

    assert plan.skipped_current == 1
    assert [item.public_id for item in plan.items] == ["alkafi-2"]


def test_translation_pilot_is_stratified_not_first_n(db: Session):
    book = add_book(db)
    lengths = [20, 30, 220, 240, 500, 520]
    for seq, length in enumerate(lengths, start=1):
        add_hadith(db, book, f"alkafi-{seq}", seq, "x" * length, volume_start=1 + seq % 2)

    plan = build_translation_plan(db, source_book_id="11005", pilot_size=4)

    assert plan.planned_hadiths == 4
    assert plan.bucket_counts["short_160"] == 2
    assert plan.bucket_counts["medium_320"] == 1
    assert plan.bucket_counts["long_640"] == 1
    assert [item.public_id for item in plan.items] == ["alkafi-1", "alkafi-2", "alkafi-4", "alkafi-6"]


def test_persist_translation_plan_creates_job_segments_and_translation_rows(db: Session):
    book = add_book(db)
    hadith = add_hadith(db, book, "alkafi-1", 1, "قال أبو عبد الله ع: العلم نور.")
    plan = build_translation_plan(db, source_book_id="11005")

    job = persist_translation_plan(db, plan, provider="dry", model="none")
    db.commit()

    assert job.id is not None
    assert job.hadith_count == 1
    assert job.segment_count == 1
    assert job.items[0].hadith_id == hadith.id
    translation = db.query(HadithTranslation).filter_by(hadith_id=hadith.id).one()
    assert translation.source_matn_sha256 == sha256_text(hadith.matn_raw)
    assert translation.status == "planned"
    assert translation.segments[0].source_text == hadith.matn_raw


def test_translation_qa_flags_empty_numbers_and_markers():
    empty = assess_translation("قال: واحد [1].", "")
    assert empty.risk_level == "red"
    assert "empty_translation" in empty.flag_codes

    report = assess_translation("قال: 12 [3].", "He said: thirteen.")
    assert report.risk_level == "red"
    assert "number_mismatch" in report.flag_codes
    assert "missing_placeholder" in report.flag_codes


def test_translation_qa_allows_clean_simple_translation():
    report = assess_translation("قال أبو عبد الله ع: العلم نور.", "Abu Abd Allah said: knowledge is light.")

    assert report.risk_level == "green"
    assert report.flags == []


def test_isnad_renderer_uses_curated_english_name_when_available(db: Session):
    kafi = add_book(db)
    mujam = add_book(db, "14036")
    hadith = add_hadith(db, kafi, "alkafi-1", 1, "قال: نعم.")
    narrator = Narrator(
        canonical_name_ar="محمد بن يعقوب",
        canonical_name_norm=normalise_arabic_persian("محمد بن يعقوب"),
        canonical_name_en="Muhammad ibn Ya'qub",
    )
    db.add(narrator)
    db.flush()
    entry = RijalEntry(
        narrator_id=narrator.id,
        book_id=mujam.id,
        entry_kind="mujam_numbered_entry",
        entry_number=1,
        title_raw="محمد بن يعقوب",
        title_normalised=normalise_arabic_persian("محمد بن يعقوب"),
        canonical_name_raw="محمد بن يعقوب",
        canonical_name_normalised=normalise_arabic_persian("محمد بن يعقوب"),
        text_raw="محمد بن يعقوب",
        text_normalised=normalise_arabic_persian("محمد بن يعقوب"),
    )
    db.add(entry)
    db.flush()
    person = Person(
        canonical_name_ar="محمد بن يعقوب",
        canonical_name_norm=normalise_arabic_persian("محمد بن يعقوب"),
        primary_entry_id=entry.id,
    )
    db.add(person)
    db.flush()
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw or "")
    db.add(chain)
    db.flush()
    node = ChainNode(
        chain_id=chain.id,
        position=0,
        raw_token="محمد بن يعقوب",
        token_normalised=normalise_arabic_persian("محمد بن يعقوب"),
        node_type="named_narrator",
    )
    db.add(node)
    db.flush()
    db.add(
        MentionResolution(
            chain_node_id=node.id,
            person_id=person.id,
            rank=1,
            status="resolved",
            method="test",
            resolver_version="tamyiz_b1",
        )
    )
    db.flush()

    rendered = render_hadith_isnad(db, hadith.id)

    assert rendered.text == "Chain 1: Muhammad ibn Ya'qub."
    assert rendered.risk_flags == []


def test_isnad_renderer_preserves_arabic_name_when_uncurated(db: Session):
    book = add_book(db)
    hadith = add_hadith(db, book, "alkafi-1", 1, "قال: نعم.")
    chain = Chain(hadith_id=hadith.id, chain_number=1, raw_isnad=hadith.isnad_raw or "")
    db.add(chain)
    db.flush()
    db.add(
        ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token="عدة من أصحابنا",
            token_normalised=normalise_arabic_persian("عدة من أصحابنا"),
            node_type="collective_phrase",
        )
    )
    db.flush()

    rendered = render_hadith_isnad(db, hadith.id)

    assert rendered.text == "Chain 1: عدة من أصحابنا."
    assert "name_preserved_arabic" in rendered.risk_flags
    assert "unresolved_name:missing_rank1" in rendered.risk_flags


def test_source_hashes_are_current_requires_the_canonical_hasher(db: Session):
    """Source hashes must come from sha256_text, which collapses whitespace.

    A raw hashlib.sha256 of the same text agrees with sha256_text whenever the
    text is already whitespace-clean, so a writer using the wrong hasher looks
    correct until it meets text carrying a stray double space or newline. That
    is how ten published Sarwar translations were pinned unverifiably and went
    invisible on 2026-07-16; see the source-hash repair note in AGENT_HANDOFF.
    """

    book = add_book(db)
    # Irregular whitespace is the trigger: a double space inside the matn.
    hadith = add_hadith(db, book, "alkafi-1", 1, "قال أبو عبد الله ع:  العلم نور.")

    def pin(hasher) -> HadithTranslation:
        return HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            source_full_sha256=hasher(hadith.full_text_raw),
            source_isnad_sha256=hasher(hadith.isnad_raw),
            source_matn_sha256=hasher(hadith.matn_raw),
            matn_translation="Knowledge is light.",
            status="published",
            risk_level="green",
        )

    raw_sha256 = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()  # noqa: E731

    assert raw_sha256(hadith.matn_raw) != sha256_text(hadith.matn_raw)
    assert source_hashes_are_current(pin(sha256_text), hadith) is True
    assert source_hashes_are_current(pin(raw_sha256), hadith) is False
