import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.api.main import app
from eshia_research.commentary.mirat_al_uqul import (
    CommentaryIndexStats,
    CommentaryPassage,
    MIRAT_AL_UQUL_SOURCE_KEY,
    SourceReport,
    TextPart,
    extract_mirat_passages,
    index_mirat_al_uqul,
    parse_ordinal_header,
)
from eshia_research.db import Base, get_db
from eshia_research.models import Book, Hadith, HadithCommentary, Page
from eshia_research.normalise import normalise_arabic_persian


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


def _page(number: int, html: str) -> Page:
    return Page(
        book_id=1,
        volume_number=1,
        page_number=number,
        source_url=f"https://lib.eshia.ir/71429/1/{number}",
        checksum=f"page-{number}",
        html_raw=html,
    )


def test_indexer_keeps_duplicate_candidates_unlinked_for_review(db: Session, monkeypatch: pytest.MonkeyPatch):
    from eshia_research.commentary import mirat_al_uqul as mirat

    kafi = Book(source_book_id="11005", title_original="Kafi", title_normalised="Kafi", source_url="https://example.test/kafi")
    commentary_book = Book(
        source_book_id="71429",
        title_original="Mirat",
        title_normalised="Mirat",
        source_url="https://example.test/mirat/1/1",
    )
    db.add_all([kafi, commentary_book])
    db.flush()
    report_text = "\u0648\u0627\u062d\u062f \u0627\u062b\u0646\u0627\u0646 \u062b\u0644\u0627\u062b\u0629 \u0627\u0631\u0628\u0639\u0629 \u062e\u0645\u0633\u0629"
    hadith = Hadith(
        public_id="alkafi-duplicate-test",
        book_id=kafi.id,
        sequence_in_book=1,
        sequence_in_page=1,
        printed_number="1",
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        section_title="section",
        full_text_raw=report_text,
        full_text_normalised=normalise_arabic_persian(report_text),
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw=report_text,
        matn_normalised=normalise_arabic_persian(report_text),
        source_url="https://example.test/kafi/1/1",
        extraction_method="test",
        extraction_confidence=100,
        review_status="approved",
    )
    db.add_all([
        hadith,
        Page(
            book_id=commentary_book.id,
            volume_number=1,
            page_number=1,
            source_url="https://example.test/mirat/1/1",
            checksum="duplicate-test",
            html_raw="<p>placeholder</p>",
        ),
    ])
    db.commit()

    report = SourceReport("section", 1, [TextPart(report_text, 1, 1)])
    passages = [
        CommentaryPassage(1, "first", "section", 1, [TextPart("first commentary", 1, 1)]),
        CommentaryPassage(2, "second", "section", 1, [TextPart("second commentary", 1, 2)]),
    ]
    monkeypatch.setattr(
        mirat,
        "extract_mirat_passages",
        lambda _pages, **_kwargs: (passages, {("section", 1, 1): report}, CommentaryIndexStats(pages_seen=1, source_reports=1, extracted=2)),
    )

    stats = index_mirat_al_uqul(db)
    rows = list(db.query(HadithCommentary).order_by(HadithCommentary.source_sequence))

    assert stats.matched == 1
    assert stats.needs_review == 1
    assert [row.hadith_id for row in rows] == [hadith.id, None]
    assert rows[1].match_method == "duplicate_candidate"


def test_indexer_realigns_number_shift_with_same_section_text_proof(db: Session, monkeypatch: pytest.MonkeyPatch):
    from eshia_research.commentary import mirat_al_uqul as mirat

    kafi = Book(source_book_id="11005", title_original="Kafi", title_normalised="Kafi", source_url="https://example.test/kafi")
    commentary_book = Book(
        source_book_id="71429",
        title_original="Mirat",
        title_normalised="Mirat",
        source_url="https://example.test/mirat/1/1",
    )
    db.add_all([kafi, commentary_book])
    db.flush()
    source_text = "\u0648\u0627\u062d\u062f \u0627\u062b\u0646\u0627\u0646 \u062b\u0644\u0627\u062b\u0629 \u0627\u0631\u0628\u0639\u0629 \u062e\u0645\u0633\u0629 \u0633\u062a\u0629 \u0633\u0628\u0639\u0629 \u062b\u0645\u0627\u0646\u064a\u0629"
    other_text = "\u062a\u0633\u0639\u0629 \u0639\u0634\u0631\u0629 \u0645\u0627\u0626\u0629 \u0623\u0644\u0641 \u0645\u0644\u064a\u0648\u0646 \u0643\u062a\u0627\u0628 \u0628\u0627\u0628 \u0641\u0635\u0644"

    def make_hadith(public_id: str, printed_number: str, text: str) -> Hadith:
        return Hadith(
            public_id=public_id,
            book_id=kafi.id,
            sequence_in_book=int(printed_number),
            sequence_in_page=1,
            printed_number=printed_number,
            volume_start=1,
            volume_end=1,
            page_start=1,
            page_end=1,
            section_title="section",
            full_text_raw=text,
            full_text_normalised=normalise_arabic_persian(text),
            isnad_raw=None,
            isnad_normalised=None,
            matn_raw=text,
            matn_normalised=normalise_arabic_persian(text),
            source_url=f"https://example.test/kafi/1/{printed_number}",
            extraction_method="test",
            extraction_confidence=100,
            review_status="approved",
        )

    direct_hadith = make_hadith("alkafi-direct", "1", other_text)
    realigned_hadith = make_hadith("alkafi-realigned", "2", source_text)
    db.add_all([
        direct_hadith,
        realigned_hadith,
        Page(
            book_id=commentary_book.id,
            volume_number=1,
            page_number=1,
            source_url="https://example.test/mirat/1/1",
            checksum="realign-test",
            html_raw="<p>placeholder</p>",
        ),
    ])
    db.commit()

    report = SourceReport("section", 1, [TextPart(source_text, 1, 1)])
    passage = CommentaryPassage(1, "first", "section", 1, [TextPart("commentary", 1, 1)])
    monkeypatch.setattr(
        mirat,
        "extract_mirat_passages",
        lambda _pages, **_kwargs: ([passage], {("section", 1, 1): report}, CommentaryIndexStats(pages_seen=1, source_reports=1, extracted=1)),
    )

    stats = index_mirat_al_uqul(db)
    row = db.query(HadithCommentary).one()

    assert stats.matched == 1
    assert row.hadith_id == realigned_hadith.id
    assert row.match_method == "section_and_text_realigned"


def test_unquoted_commentary_is_placed_by_chapter_position(db: Session):
    """The whole point of the alignment layer.

    Al-Majlisi comments on hadith 2 without reprinting it. Nothing in that
    passage can ever be text-matched; it is placed because hadiths 1 and 3 of
    the same chapter were text-verified, pinning the chapter.
    """
    kafi = Book(source_book_id="11005", title_original="الكافي", title_normalised="الكافي",
                source_url="https://lib.eshia.ir/11005")
    mirat = Book(source_book_id="71429", title_original="مرآة العقول",
                 title_normalised="مرآة العقول", source_url="https://lib.eshia.ir/71429/1/1")
    db.add_all([kafi, mirat])
    db.flush()

    texts = {
        1: "محمد بن يحيى عن احمد بن محمد عن الحسن بن محبوب قال العقل نور عظيم.",
        2: "علي بن ابراهيم عن ابيه عن ابن ابي عمير قال الجهل ظلمة شديدة جدا.",
        3: "احمد بن ادريس عن محمد بن عبد الجبار عن بعض اصحابنا قال الصدق نجاة كبيرة.",
    }
    for number, text in texts.items():
        db.add(Hadith(
            public_id=f"alkafi-align-{number}", book_id=kafi.id, sequence_in_book=number,
            sequence_in_page=1, printed_number=str(number), volume_start=1, volume_end=1,
            page_start=1, page_end=1, section_title="باب العقل",
            full_text_raw=text, full_text_normalised=normalise_arabic_persian(text),
            isnad_raw=None, isnad_normalised=None, matn_raw=text,
            matn_normalised=normalise_arabic_persian(text),
            source_url=f"https://lib.eshia.ir/11005/1/{number}", extraction_method="test",
            extraction_confidence=100, review_status="approved",
        ))

    # Hadiths 1 and 3 are reprinted; hadith 2 is commented on but never quoted.
    db.add(Page(
        book_id=mirat.id, volume_number=1, page_number=1,
        source_url="https://lib.eshia.ir/71429/1/1", checksum="align-page",
        html_raw=f"""
        <td class="book-page-show">
          <h2>باب</h2>
          <h2>العقل</h2>
          <p>١ ـ {texts[1]}</p>
          <span class="FootNote">الحديث الأول صحيح. شرح الاول.</span>
          <span class="FootNote">الحديث الثاني ضعيف. شرح الثاني بلا نص منقول.</span>
          <p>٣ ـ {texts[3]}</p>
          <span class="FootNote">الحديث الثالث حسن. شرح الثالث.</span>
        </td>
        """,
    ))
    db.commit()

    stats = index_mirat_al_uqul(db)
    rows = {r.source_label: r for r in db.query(HadithCommentary).all()}
    second = rows["الحديث الثاني"]

    assert stats.aligned == 1
    assert second.match_status == "matched"
    assert second.match_method == "chapter_sequence_aligned"
    assert second.hadith_id == db.query(Hadith).filter_by(public_id="alkafi-align-2").one().id
    assert second.report_raw is None  # nothing was ever quoted for it
    assert second.match_evidence_json["alignment_ordinal"] == 2


def test_alignment_never_double_claims_a_hadith(db: Session):
    """A hadith already carrying a text-verified sharh is not re-linked."""
    kafi = Book(source_book_id="11005", title_original="الكافي", title_normalised="الكافي",
                source_url="https://lib.eshia.ir/11005")
    mirat = Book(source_book_id="71429", title_original="مرآة العقول",
                 title_normalised="مرآة العقول", source_url="https://lib.eshia.ir/71429/1/1")
    db.add_all([kafi, mirat])
    db.flush()
    text = "محمد بن يحيى عن احمد بن محمد عن الحسن بن محبوب قال العقل نور عظيم."
    db.add(Hadith(
        public_id="alkafi-solo-1", book_id=kafi.id, sequence_in_book=1, sequence_in_page=1,
        printed_number="1", volume_start=1, volume_end=1, page_start=1, page_end=1,
        section_title="باب العقل", full_text_raw=text,
        full_text_normalised=normalise_arabic_persian(text), isnad_raw=None,
        isnad_normalised=None, matn_raw=text, matn_normalised=normalise_arabic_persian(text),
        source_url="https://lib.eshia.ir/11005/1/1", extraction_method="test",
        extraction_confidence=100, review_status="approved",
    ))
    db.add(Page(
        book_id=mirat.id, volume_number=1, page_number=1,
        source_url="https://lib.eshia.ir/71429/1/1", checksum="solo-page",
        html_raw=f"""
        <td class="book-page-show">
          <h2>باب العقل</h2>
          <p>١ ـ {text}</p>
          <span class="FootNote">الحديث الأول صحيح. شرح.</span>
        </td>
        """,
    ))
    db.commit()

    index_mirat_al_uqul(db)
    linked = [r for r in db.query(HadithCommentary).all() if r.hadith_id is not None]

    assert len(linked) == 1
    assert len({r.hadith_id for r in linked}) == 1


def test_extractor_uses_h2_chapter_heading_for_following_commentary():
    section = "\u0628\u0627\u0628 \u0627\u0644\u063a\u0646\u0627\u0621"
    page = _page(
        1,
        f"""
        <td class="book-page-show">
          <h2>({section})</h2>
          <p>\u0661 - \u0648\u0627\u062d\u062f \u0627\u062b\u0646\u0627\u0646 \u062b\u0644\u0627\u062b\u0629 \u0627\u0631\u0628\u0639\u0629 \u062e\u0645\u0633\u0629.</p>
          <span class="FootNote">\u0627\u0644\u062d\u062f\u064a\u062b \u0627\u0644\u0623\u0648\u0644 \u0635\u062d\u064a\u062d. \u0634\u0631\u062d.</span>
        </td>
        """,
    )

    passages, reports, _stats = extract_mirat_passages([page])

    assert reports[(normalise_arabic_persian(section), 1, 1)].section_title == section
    assert passages[0].section_title == section


def test_repeated_chapter_titles_do_not_merge_into_one_report():
    """"باب نادر" recurs across the book; each run keeps its own report.

    Merging them concatenated every same-numbered report in the book into a
    single blob, which no local hadith could ever match.
    """
    first = _page(
        10,
        """
        <td class="book-page-show">
          <h2>باب نادر</h2>
          <p>١ ـ واحد اثنان ثلاثة اربعة خمسة.</p>
          <span class="FootNote">الحديث الأول صحيح.</span>
        </td>
        """,
    )
    between = _page(
        11,
        """
        <td class="book-page-show">
          <h2>باب العلم</h2>
          <p>١ ـ ستة سبعة ثمانية تسعة عشرة.</p>
          <span class="FootNote">الحديث الأول حسن.</span>
        </td>
        """,
    )
    again = _page(
        12,
        """
        <td class="book-page-show">
          <h2>باب نادر</h2>
          <p>١ ـ مائة ألف مليون كتاب فصل.</p>
          <span class="FootNote">الحديث الأول ضعيف.</span>
        </td>
        """,
    )

    _passages, reports, stats = extract_mirat_passages([first, between, again])

    assert stats.source_reports == 3
    nadir = normalise_arabic_persian("باب نادر")
    assert reports[(nadir, 1, 1)].text.endswith("خمسة.")
    assert reports[(nadir, 3, 1)].text.endswith("فصل.")
    # The decisive property: neither run absorbed the other's text.
    assert "مائة" not in reports[(nadir, 1, 1)].text
    assert "واحد" not in reports[(nadir, 3, 1)].text


def test_repeated_report_number_starts_a_new_run_instead_of_gluing():
    """A number that recurs in one run means an unmarked chapter change.

    Appending the second report to the first produced a blob no hadith could
    match, which is what left most passages unpublishable.
    """
    page = _page(
        30,
        """
        <td class="book-page-show">
          <h2>باب الصدق</h2>
          <p>١ ـ واحد اثنان ثلاثة اربعة خمسة.</p>
          <span class="FootNote">الحديث الأول صحيح.</span>
          <p>١ ـ مائة ألف مليون كتاب فصل.</p>
          <span class="FootNote">الحديث الأول ضعيف.</span>
        </td>
        """,
    )

    _passages, reports, stats = extract_mirat_passages([page])

    assert stats.source_reports == 2
    texts = [report.text for report in reports.values()]
    assert any(text.endswith("خمسة.") for text in texts)
    assert any(text.endswith("فصل.") for text in texts)
    assert all("مائة" not in t or "واحد" not in t for t in texts)


def test_running_page_header_does_not_open_a_new_chapter_run():
    """eShia reprints the chapter title on each page; that is one chapter."""
    first = _page(
        20,
        """
        <td class="book-page-show">
          <h2>باب النوادر</h2>
          <p>١ ـ واحد اثنان ثلاثة اربعة خمسة.</p>
        </td>
        """,
    )
    second = _page(
        21,
        """
        <td class="book-page-show">
          <h2>باب النوادر</h2>
          <p>٢ ـ ستة سبعة ثمانية تسعة عشرة.</p>
          <span class="FootNote">الحديث الثاني صحيح.</span>
        </td>
        """,
    )

    passages, reports, _stats = extract_mirat_passages([first, second])

    nawadir = normalise_arabic_persian("باب النوادر")
    assert set(reports) == {(nawadir, 1, 1), (nawadir, 1, 2)}
    assert passages[0].section_occurrence == 1


def test_header_running_out_of_a_chapter_title_is_still_a_new_passage():
    """eShia runs the chapter title straight into the header with no full stop.

    These passages were being swallowed as continuations of the previous
    sharh, which is a large part of why passages trailed reports.
    """
    page = _page(
        1,
        """
        <td class="book-page-show">
          <span class="FootNote">باب أن المتوسمين هم الأئمة والسبيل فيهم مقيم الحديث الأول : ضعيف وقال في المغرب.</span>
        </td>
        """,
    )

    passages, _reports, _stats = extract_mirat_passages([page])

    assert len(passages) == 1
    assert passages[0].printed_number == 1
    assert passages[0].text.startswith("الحديث الأول")


def test_back_reference_inside_prose_does_not_open_a_passage():
    """«كما مر في الحديث الأول» is al-Majlisi citing, not a new header."""
    page = _page(
        1,
        """
        <td class="book-page-show">
          <span class="FootNote">الحديث الثاني : صحيح وقد مر بيانه في الحديث الأول من هذا الباب فتأمل.</span>
        </td>
        """,
    )

    passages, _reports, _stats = extract_mirat_passages([page])

    assert [p.printed_number for p in passages] == [2]


def test_sharh_below_a_new_chapter_heading_stays_with_the_previous_chapter():
    """The footnote area lags the main text by up to a page.

    Without this, the trailing «الحديث التاسع» of the old chapter is filed
    under the new one, takes the new chapter's ninth report, and beats the
    real ninth passage to the claim — publishing the wrong sharh.
    """
    first = _page(
        10,
        """
        <td class="book-page-show">
          <h2>باب الاول</h2>
          <p>٩ ـ واحد اثنان ثلاثة اربعة خمسة ستة سبعة.</p>
        </td>
        """,
    )
    second = _page(
        11,
        """
        <td class="book-page-show">
          <h2>باب الثاني</h2>
          <p>١ ـ مائة الف مليون كتاب فصل باب حرف.</p>
          <span class="FootNote">الحديث التاسع : شرح الباب الاول.</span>
          <span class="FootNote">الحديث الأول : شرح الباب الثاني.</span>
        </td>
        """,
    )

    passages, _reports, _stats = extract_mirat_passages([first, second])
    by_label = {p.source_label: p for p in passages}

    assert by_label["الحديث التاسع"].section_title == "باب الاول"
    assert by_label["الحديث الأول"].section_title == "باب الثاني"
    assert (
        by_label["الحديث التاسع"].section_occurrence
        < by_label["الحديث الأول"].section_occurrence
    )


def test_a_chapter_that_simply_starts_late_is_not_reassigned():
    """A run whose numbering never reaches 1 is not a carry-over case."""
    page = _page(
        20,
        """
        <td class="book-page-show">
          <h2>باب النوادر</h2>
          <p>٤ ـ واحد اثنان ثلاثة اربعة خمسة.</p>
          <span class="FootNote">الحديث الرابع : شرح.</span>
          <span class="FootNote">الحديث الخامس : شرح اخر.</span>
        </td>
        """,
    )

    passages, _reports, _stats = extract_mirat_passages([page])

    assert {p.section_title for p in passages} == {"باب النوادر"}


def test_parse_ordinal_header_handles_compound_arabic_ordinals():
    label, value = parse_ordinal_header("الحديث الحادي والعشرون ضعيف على المشهور.")

    assert label == "الحديث الحادي والعشرون"
    assert value == 21


def test_extractor_keeps_source_reports_out_of_footnote_commentary():
    first = _page(
        80,
        """
        <td class="book-page-show">
          <p>كتاب العقل والجهل</p>
          <p>٢١ ـ محمد بن يحيى قال العقل نور.</p>
          <span class="FootNote">الحديث الحادي والعشرون صحيح. قوله: أول الشرح.</span>
        </td>
        """,
    )
    second = _page(
        81,
        """
        <td class="book-page-show">
          <p>٢٢ ـ محمد بن يحيى قال العقل بصيرة.</p>
          <span class="FootNote">تتمة شرح الحديث الحادي والعشرون. الحديث الثاني والعشرون ضعيف. شرح آخر.</span>
        </td>
        """,
    )

    passages, reports, stats = extract_mirat_passages([first, second])

    assert stats.source_reports == 2
    assert reports[(normalise_arabic_persian("كتاب العقل والجهل"), 1, 21)].text.startswith("٢١")
    assert [(passage.printed_number, passage.page_start, passage.page_end) for passage in passages] == [
        (21, 80, 81),
        (22, 81, 81),
    ]
    assert "تتمة شرح" in passages[0].text
    assert "٢٢" not in passages[0].text


def test_indexer_and_api_publish_only_text_verified_mirat_match(db: Session, client: TestClient):
    kafi = Book(
        source_book_id="11005",
        title_original="الكافي",
        title_normalised="الكافي",
        source_url="https://lib.eshia.ir/11005",
    )
    mirat = Book(
        source_book_id="71429",
        title_original="مرآة العقول",
        title_normalised="مرآة العقول",
        source_url="https://lib.eshia.ir/71429/1/1",
    )
    db.add_all([kafi, mirat])
    db.flush()
    source_report = "محمد بن يحيى عن أحمد بن محمد قال العقل نور."
    hadith = Hadith(
        public_id="alkafi-test-21",
        book_id=kafi.id,
        sequence_in_book=21,
        sequence_in_page=1,
        printed_number="٢١",
        volume_start=1,
        volume_end=1,
        page_start=80,
        page_end=80,
        section_title="كتاب العقل والجهل",
        full_text_raw=source_report,
        full_text_normalised=normalise_arabic_persian(source_report),
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw=source_report,
        matn_normalised=normalise_arabic_persian(source_report),
        source_url="https://lib.eshia.ir/11005/1/80",
        extraction_method="test",
        extraction_confidence=100,
        review_status="approved",
    )
    page = Page(
        book_id=mirat.id,
        volume_number=1,
        page_number=80,
        source_url="https://lib.eshia.ir/71429/1/80",
        checksum="mirat-page-80",
        html_raw=f"""
        <td class="book-page-show">
          <p>كتاب العقل والجهل</p>
          <p>٢١ ـ {source_report}</p>
          <span class="FootNote">الحديث الحادي والعشرون صحيح. قوله: شرح محفوظ.</span>
        </td>
        """,
    )
    db.add_all([hadith, page])
    db.commit()

    stats = index_mirat_al_uqul(db)

    assert stats.matched == 1
    summary = client.get("/hadiths/alkafi-test-21")
    assert summary.status_code == 200
    assert summary.json()["commentaries"][0]["source_key"] == MIRAT_AL_UQUL_SOURCE_KEY

    commentary = client.get("/hadiths/alkafi-test-21/commentaries")
    assert commentary.status_code == 200
    assert commentary.json()[0]["commentary_raw"].endswith("شرح محفوظ.")
