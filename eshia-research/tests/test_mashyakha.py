import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MashyakhaExpansion,
    MashyakhaPath,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.mashyakha import (
    MATCH_CANONICAL,
    MATCH_EXACT,
    MATCH_ISM_NISBA_ELISION,
    MATCH_NAME_EXTENSION,
    MATCH_PARTIAL_CANDIDATE,
    MashyakhaSourceEntry,
    audit_faqih_mashyakha_coverage,
    canonical_opening,
    classify_opening,
    import_faqih_mashyakha_paths,
    load_mashyakha_snapshot,
    materialize_faqih_mashyakha_expansions,
    parse_faqih_mashyakha_path,
    write_mashyakha_snapshot,
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


def _faqih_chain_opening(db: Session, opening: str) -> Chain:
    """A minimal Faqih report whose chain opens, abbreviated, at ``opening``."""
    book = db.query(Book).filter_by(source_book_id="11021").one_or_none()
    if book is None:
        book = Book(
            source_book_id="11021",
            title_original="Man la yahduruhu al-faqih",
            title_normalised="man la yahduruhu al-faqih",
            source_url="https://lib.eshia.ir/11021",
        )
        db.add(book)
        db.flush()
    sequence = db.query(Hadith).filter_by(book_id=book.id).count() + 1
    hadith = Hadith(
        public_id=f"faqih-test-{sequence}",
        book_id=book.id,
        sequence_in_book=sequence,
        sequence_in_page=1,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw=f"روي عن {opening}",
        full_text_normalised=normalise_arabic_persian(f"روي عن {opening}"),
        isnad_raw=f"روي عن {opening}",
        isnad_normalised=normalise_arabic_persian(f"روي عن {opening}"),
        matn_raw="متن",
        matn_normalised=normalise_arabic_persian("متن"),
        source_url=f"https://lib.eshia.ir/11021/1/{sequence}",
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(
        hadith_id=hadith.id,
        chain_number=1,
        raw_isnad=hadith.isnad_raw,
        flags="mursal_opening",
        review_status="needs_review",
    )
    db.add(chain)
    db.flush()
    db.add(
        ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token=opening,
            token_normalised=normalise_arabic_persian(opening),
            node_type="named_narrator",
        )
    )
    db.flush()
    return chain


def test_parse_standard_faqih_mashyakha_path():
    parsed = parse_faqih_mashyakha_path(
        "و ما كان فيه عن عبد الله بن سنان فقد رويته عن أبي، عن عبد الله بن جعفر الحميري، "
        "عن أيوب بن نوح، عن محمد بن أبي عمير، عن عبد الله بن سنان، و هو الذي ذكر عند الصادق عليه السلام."
    )

    assert parsed.review_status == "parsed"
    assert parsed.target_raw == "عبد الله بن سنان"
    assert parsed.target_normalised == normalise_arabic_persian("عبد الله بن سنان")
    assert parsed.path_nodes == [
        "أبي",
        "عبد الله بن جعفر الحميري",
        "أيوب بن نوح",
        "محمد بن أبي عمير",
        "عبد الله بن سنان",
    ]


def test_unrecognised_entry_is_preserved_for_review():
    parsed = parse_faqih_mashyakha_path("بيان طرق الصدوق إلى من نقل عنهم بالواسطة")

    assert parsed.review_status == "needs_review"
    assert parsed.target_raw is None
    assert parsed.path_nodes == []


def test_snapshot_round_trip(tmp_path):
    entries = [
        MashyakhaSourceEntry(
            source_chapter=chapter,
            source_hadith_number=None,
            source_url=f"https://thaqalayn.net/chapter/38/1/{chapter}",
            source_text_ar="source text",
        )
        for chapter in range(1, 201)
    ]
    snapshot = write_mashyakha_snapshot(entries, tmp_path / "mashyakha.json")

    assert load_mashyakha_snapshot(snapshot) == entries


def test_import_is_idempotent_and_audits_exact_mursal_coverage(db: Session):
    entry = MashyakhaSourceEntry(
        source_chapter=32,
        source_hadith_number=33,
        source_url="https://thaqalayn.net/chapter/38/1/32",
        source_text_ar=(
            "و ما كان فيه عن عبد الله بن سنان فقد رويته عن أبي، عن عبد الله بن جعفر الحميري، "
            "عن أيوب بن نوح، عن محمد بن أبي عمير، عن عبد الله بن سنان."
        ),
    )
    first = import_faqih_mashyakha_paths(db, [entry])
    second = import_faqih_mashyakha_paths(db, [entry])

    assert (first.created, first.updated, first.parsed) == (1, 0, 1)
    assert (second.created, second.updated, second.parsed) == (0, 1, 1)
    assert db.query(MashyakhaPath).count() == 1

    book = Book(
        source_book_id="11021",
        title_original="Man la yahduruhu al-faqih",
        title_normalised="man la yahduruhu al-faqih",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(book)
    db.flush()
    hadith = Hadith(
        public_id="faqih-test-1",
        book_id=book.id,
        sequence_in_book=1,
        sequence_in_page=1,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw="روي عن عبد الله بن سنان",
        full_text_normalised=normalise_arabic_persian("روي عن عبد الله بن سنان"),
        isnad_raw="روي عن عبد الله بن سنان",
        isnad_normalised=normalise_arabic_persian("روي عن عبد الله بن سنان"),
        matn_raw="متن",
        matn_normalised=normalise_arabic_persian("متن"),
        source_url="https://lib.eshia.ir/11021/1/1",
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    chain = Chain(
        hadith_id=hadith.id,
        chain_number=1,
        raw_isnad=hadith.isnad_raw,
        flags="mursal_opening",
        review_status="needs_review",
    )
    db.add(chain)
    db.flush()
    db.add(
        ChainNode(
            chain_id=chain.id,
            position=0,
            raw_token="عبد الله بن سنان",
            token_normalised=normalise_arabic_persian("عبد الله بن سنان"),
            node_type="named_narrator",
        )
    )
    db.flush()

    before_expansion = audit_faqih_mashyakha_coverage(db)
    assert before_expansion == {
        "source_paths": 1,
        "parsed_paths": 1,
        "topic_entry_paths": 0,
        "needs_review_paths": 0,
        "target_forms": 1,
        "mursal_openings": 1,
        "openings_exact_first_narrator": 1,
        "openings_canonical_first_narrator": 0,
        "openings_unique_name_extension": 0,
        "openings_ism_nisba_elision": 0,
        "openings_partial_name_candidate": 0,
        "openings_with_single_candidate": 1,
        "openings_with_any_witness": 1,
        "openings_without_source_witness": 0,
        "expansion_proposals": 0,
        "expansion_proposed": 0,
        "expansion_needs_review": 0,
    }

    node_count_before = db.query(ChainNode).count()
    expansion_stats = materialize_faqih_mashyakha_expansions(db)
    expansion = db.query(MashyakhaExpansion).one()

    assert (expansion_stats.created, expansion_stats.proposed, expansion_stats.needs_review) == (1, 1, 0)
    assert expansion.chain_id == chain.id
    assert expansion.mashyakha_path_id == db.query(MashyakhaPath).one().id
    assert expansion.review_status == "proposed"
    assert db.query(ChainNode).count() == node_count_before
    assert db.get(Chain, chain.id).review_status == "needs_review"

    assert audit_faqih_mashyakha_coverage(db)["expansion_proposals"] == 1


def test_parse_accepts_the_editions_other_printed_formulas():
    """The formula varies in wording and punctuation; the construction does not."""
    whole_book = parse_faqih_mashyakha_path(
        "و كلّ ما كان في هذا الكتاب عن عليّ بن جعفر فقد رويته عن أبي- رضي اللّه عنه- "
        "عن محمّد بن يحيى العطّار، عن العمركيّ بن عليّ البوفكيّ، عن عليّ بن جعفر."
    )
    assert whole_book.review_status == "parsed"
    assert whole_book.target_normalised == normalise_arabic_persian("علي بن جعفر")

    # A comma after "فيه" and after "رويته" is typesetting, not a different formula.
    comma = parse_faqih_mashyakha_path(
        "و ما كان فيه، عن حمّاد بن عثمان فقد رويته عن أبي- رضي اللّه عنه- عن سعد بن عبد اللّه؛ "
        "و الحميريّ جميعا عن يعقوب بن يزيد، عن محمّد بن أبي عمير، عن حمّاد بن عثمان."
    )
    assert comma.review_status == "parsed"
    assert comma.target_normalised == normalise_arabic_persian("حماد بن عثمان")

    dictated = parse_faqih_mashyakha_path(
        "و ما كان فيه عن النعمان بن سعد فقد حدّثني به محمّد بن موسى بن المتوكّل- رضي اللّه عنه- "
        "عن عليّ بن الحسين السعدآبادي، عن أحمد بن أبي عبد اللّه البرقيّ."
    )
    assert dictated.review_status == "parsed"
    assert dictated.target_normalised == normalise_arabic_persian("النعمان بن سعد")


def test_parse_records_every_narrator_form_one_entry_vouches_for():
    shared_path = parse_faqih_mashyakha_path(
        "و ما كان فيه عن محمّد بن حمران؛ و جميل بن دراج فقد رويته عن أبي، عن سعد بن عبد اللّه، "
        "عن أحمد بن محمّد بن عيسى، عن محمّد بن حمران؛ و جميل بن دراج."
    )
    assert shared_path.review_status == "parsed"
    assert shared_path.target_forms == [
        normalise_arabic_persian("محمد بن حمران"),
        normalise_arabic_persian("جميل بن دراج"),
    ]

    # A two-step opening: a report opens at Zur'a, so Zur'a is a target form too.
    two_step = parse_faqih_mashyakha_path(
        "و ما كان فيه عن زرعة، عن سماعة فقد رويته عن أبي- رضي اللّه عنه- عن سعد بن عبد اللّه، "
        "عن أحمد بن محمّد بن عيسى، عن الحسين بن سعيد، عن أخيه الحسن، عن زرعة بن محمّد الحضرميّ."
    )
    assert two_step.target_forms == [
        normalise_arabic_persian("زرعة"),
        normalise_arabic_persian("سماعة"),
    ]


def test_subject_keyed_entries_are_not_parser_failures():
    parsed = parse_faqih_mashyakha_path(
        "و ما كان فيه من خبر بلال و ثواب المؤذّنين بطوله فقد رويته عن أحمد بن زياد بن جعفر "
        "الهمدانيّ- رضي اللّه عنه- عن عليّ بن إبراهيم بن هاشم، عن أبيه."
    )

    assert parsed.review_status == "topic_entry"
    assert parsed.target_raw is None
    assert parsed.target_forms == []


@pytest.mark.parametrize(
    ("opening", "expected"),
    [
        # The tokenizer kept the preposition that introduced the narrator.
        ("عن معاوية بن عمار", "معاویة بن عمار"),
        ("عنه زرارة", "زرارة"),
        # "بإسناده" and a trailing honorific are apparatus, not part of the name.
        ("السكوني بإسناده", "السکونی"),
        ("الحلبي عنه ع", "الحلبی"),
        # The Mashyakha names its target in the genitive after "عن"; the report
        # prints whatever case its own sentence needs.
        ("أبو بصير", "ابی بصیر"),
        ("أبا حمزة الثمالي", "ابی حمزة الثمالی"),
        # A name that needs nothing removed is returned unchanged.
        ("محمد بن مسلم", "محمد بن مسلم"),
    ],
)
def test_canonical_opening_strips_orthography_not_identity(opening: str, expected: str):
    assert canonical_opening(normalise_arabic_persian(opening)) == expected


def _forms(*entries: tuple[str, list[str]]) -> dict[str, list[MashyakhaPath]]:
    paths_by_form: dict[str, list[MashyakhaPath]] = {}
    for index, (chapter_label, forms) in enumerate(entries, start=1):
        path = MashyakhaPath(
            id=index,
            source_key="thaqalayn-faqih-mashaykha-v1",
            source_chapter=index,
            source_url=chapter_label,
            source_text_ar=chapter_label,
            source_sha256=f"sha{index}",
            review_status="parsed",
            target_raw=forms[0],
            target_normalised=normalise_arabic_persian(forms[0]),
            target_forms_json=[normalise_arabic_persian(form) for form in forms],
        )
        for form in forms:
            paths_by_form.setdefault(normalise_arabic_persian(form), []).append(path)
    return paths_by_form


def test_classify_opening_ranks_evidence_and_refuses_to_pick_a_winner():
    paths = _forms(
        ("ch1", ["محمد بن مسلم الثقفي"]),
        ("ch2", ["أبي بصير"]),
        ("ch3", ["حماد بن عيسى"]),
        ("ch4", ["حماد بن عثمان"]),
        ("ch5", ["عمار بن موسى الساباطي"]),
        ("ch6", ["محمد بن علي بن محبوب"]),
    )

    def classify(opening: str):
        return classify_opening(normalise_arabic_persian(opening), paths)

    # Exact, then exact-after-canonicalisation.
    assert classify("حماد بن عثمان").method == MATCH_EXACT
    assert classify("عن أبو بصير").method == MATCH_CANONICAL

    # The target only adds a nisba, so the ism agrees and nothing contradicts.
    extension = classify("محمد بن مسلم")
    assert extension.method == MATCH_NAME_EXTENSION
    assert [c.path.source_chapter for c in extension.candidates] == [1]

    # Ism and nisba both agree; only the patronymic is elided.
    assert classify("عمار الساباطي").method == MATCH_ISM_NISBA_ELISION

    # Two men named Hammad: ranked candidates, never a forced winner.
    ambiguous = classify("حماد")
    assert ambiguous.method == MATCH_PARTIAL_CANDIDATE
    assert [c.path.source_chapter for c in ambiguous.candidates] == [3, 4]

    # "ابن محبوب" declares an elided ism.  The only entry ending in "بن محبوب"
    # is Muhammad b. Ali b. Mahbub, which is a different man from the Ibn
    # Mahbub of the isnads — uniqueness inside this roster is not uniqueness in
    # the tradition, so this stays a candidate.
    patronymic = classify("ابن محبوب")
    assert patronymic.method == MATCH_PARTIAL_CANDIDATE
    assert [c.path.source_chapter for c in patronymic.candidates] == [6]

    # Al-Saduq wrote no entry for this narrator, which is a real answer.
    assert classify("يونس بن عبد الرحمن") is None


def test_rerun_drops_unsupported_proposals_but_keeps_human_rulings(db: Session):
    entry = MashyakhaSourceEntry(
        source_chapter=32,
        source_hadith_number=None,
        source_url="https://thaqalayn.net/chapter/38/1/32",
        source_text_ar=(
            "و ما كان فيه عن عبد الله بن سنان فقد رويته عن أبي، عن عبد الله بن جعفر الحميري، "
            "عن أيوب بن نوح، عن محمد بن أبي عمير، عن عبد الله بن سنان."
        ),
    )
    import_faqih_mashyakha_paths(db, [entry])
    chain = _faqih_chain_opening(db, "عبد الله بن سنان")
    materialize_faqih_mashyakha_expansions(db)

    stale = MashyakhaPath(
        source_book_id="11021",
        source_key="thaqalayn-faqih-mashaykha-v1",
        source_chapter=99,
        source_url="https://thaqalayn.net/chapter/38/1/99",
        source_text_ar="stale witness",
        source_sha256="stale",
        review_status="parsed",
        target_raw="زرارة بن أعين",
        target_normalised=normalise_arabic_persian("زرارة بن أعين"),
    )
    db.add(stale)
    db.flush()
    now = db.query(MashyakhaExpansion).one().created_at
    db.add_all(
        [
            MashyakhaExpansion(
                chain_id=chain.id,
                mashyakha_path_id=stale.id,
                match_method="exact_first_narrator",
                review_status="proposed",
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    db.flush()
    assert db.query(MashyakhaExpansion).count() == 2

    stats = materialize_faqih_mashyakha_expansions(db)

    assert stats.removed == 1
    assert [e.mashyakha_path_id for e in db.query(MashyakhaExpansion)] != [stale.id]
    assert db.query(MashyakhaExpansion).count() == 1

    # A ruling a human already made is a decision, not regenerable output.
    ruled = MashyakhaExpansion(
        chain_id=chain.id,
        mashyakha_path_id=stale.id,
        match_method="exact_first_narrator",
        review_status="rejected",
        created_at=now,
        updated_at=now,
    )
    db.add(ruled)
    db.flush()

    assert materialize_faqih_mashyakha_expansions(db).removed == 0
    assert db.get(MashyakhaExpansion, ruled.id) is not None


@pytest.mark.parametrize(
    "scoped",
    ["شعيب بن واقد في المناهي", "الفضل بن شاذان من العلل التي ذكرها"],
)
def test_subject_scoped_target_is_never_the_sole_candidate(scoped: str):
    """Such an entry vouches for one subject, not for everything the man narrated."""
    paths = _forms(("ch1", [scoped]), ("ch2", ["يعقوب بن شعيب"]))
    bare = normalise_arabic_persian(scoped.split()[0])

    match = classify_opening(bare, paths)

    assert match.method == MATCH_PARTIAL_CANDIDATE


def test_evidence_names_the_form_that_matched_not_the_entrys_first_target(db: Session):
    """One entry covers two narrators; its primary target is the other one."""
    entry = MashyakhaSourceEntry(
        source_chapter=31,
        source_hadith_number=None,
        source_url="https://thaqalayn.net/chapter/38/1/31",
        source_text_ar=(
            "و ما كان فيه عن محمّد بن حمران؛ و جميل بن دراج فقد رويته عن أبي، "
            "عن سعد بن عبد اللّه، عن أحمد بن محمّد بن عيسى، عن محمّد بن حمران؛ و جميل بن دراج."
        ),
    )
    import_faqih_mashyakha_paths(db, [entry])
    _faqih_chain_opening(db, "جميل")
    materialize_faqih_mashyakha_expansions(db)

    evidence = db.query(MashyakhaExpansion).one().match_evidence_json

    assert evidence["matched_target_form"] == normalise_arabic_persian("جميل بن دراج")
    assert evidence["path_target_normalised"] == normalise_arabic_persian("محمد بن حمران")


def test_bracketed_honorifics_are_stripped_from_both_sides():
    """"محمد بن يعقوب الكليني- رحمة الله عليه-" is the same name without the dua."""
    paths = _forms(("ch1", ["محمد بن يعقوب الكليني- رحمة الله عليه-"]))

    match = classify_opening(normalise_arabic_persian("محمد بن يعقوب الكليني"), paths)

    assert match.method == MATCH_CANONICAL
    assert len(match.candidates) == 1
