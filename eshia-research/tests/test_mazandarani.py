"""Reading al-Mazandarani's Sharh Usul al-Kafi out of eShia 13033."""

from eshia_research.commentary.mazandarani import (
    MazandaraniUnit,
    extract_units,
    fill_missing_ordinals,
    split_gloss,
)
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from eshia_research.db import Base
from eshia_research.models import Page
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


def _unit(sequence: int, number: int | None, occurrence: int = 1) -> MazandaraniUnit:
    return MazandaraniUnit(
        source_sequence=sequence,
        section_title="باب",
        section_occurrence=occurrence,
        printed_number=number,
        report="report",
        commentary="sharh",
        gloss="",
        gloss_uncertain=False,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
    )


def test_missing_ordinal_between_numbered_neighbours_is_filled():
    """«الأصل: - …» with no number, bracketed by 4 and 6, must be 5."""
    units = [_unit(1, 4), _unit(2, None), _unit(3, 6)]

    assert fill_missing_ordinals(units) == 1
    assert [u.printed_number for u in units] == [4, 5, 6]


def test_a_gap_that_does_not_add_up_is_left_unnumbered():
    """Two missing between 4 and 6 cannot both be 5 — guessing would misplace them."""
    units = [_unit(1, 4), _unit(2, None), _unit(3, None), _unit(4, 6)]

    assert fill_missing_ordinals(units) == 0
    assert [u.printed_number for u in units] == [4, None, None, 6]


def test_leading_gap_counts_back_from_the_first_number():
    units = [_unit(1, None), _unit(2, 2), _unit(3, 3)]

    assert fill_missing_ordinals(units) == 1
    assert [u.printed_number for u in units] == [1, 2, 3]


def test_leading_gap_is_refused_when_it_would_go_below_one():
    units = [_unit(1, None), _unit(2, 1)]

    assert fill_missing_ordinals(units) == 0
    assert units[0].printed_number is None


def test_ordinal_corroboration_publishes_an_unambiguous_near_miss(db: Session):
    """A 0.92 text match with no rival, whose ordinal also agrees, is published.

    The 0.985 bar exists to separate near-ties. Where a second independent
    witness agrees — the hadith carries the same number inside its chapter as
    the unit does — that ambiguity is absent and the pair identifies itself.
    """
    from eshia_research.commentary.mazandarani import index_sharh_al_mazandarani
    from eshia_research.models import Book, Hadith, HadithCommentary

    kafi = Book(source_book_id="11005", title_original="الكافي",
                title_normalised="الكافي", source_url="https://lib.eshia.ir/11005")
    maz = Book(source_book_id="13033", title_original="شرح أصول الكافي",
               title_normalised="شرح أصول الكافي", source_url="https://lib.eshia.ir/13033/1/1")
    db.add_all([kafi, maz])
    db.flush()

    # The quote must land *between* the two bars: neither text contains the
    # other, so it cannot score 1.0, but they overlap heavily. Dropping one word
    # and adding one puts coverage at 19/20 on both sides.
    shared = ("علي محمد سهل زياد رفعه امير المؤمنين العقل غطاء ستير والفضل جمال "
              "ظاهر فاستر خلل خلقك بفضلك وقاتل هواك").split()
    kafi_text = " ".join(shared + ["بعقلك"])
    quoted = " ".join(shared + ["زيادة"])
    db.add(Hadith(
        public_id="alkafi-corrob-13", book_id=kafi.id, sequence_in_book=13,
        sequence_in_page=1, printed_number="13", volume_start=1, volume_end=1,
        page_start=1, page_end=1, section_title="كتاب العقل والجهل",
        full_text_raw=kafi_text, full_text_normalised=normalise_arabic_persian(kafi_text),
        isnad_raw=None, isnad_normalised=None, matn_raw=kafi_text,
        matn_normalised=normalise_arabic_persian(kafi_text),
        source_url="https://lib.eshia.ir/11005/1/1", extraction_method="test",
        extraction_confidence=100, review_status="approved",
    ))
    db.add(Page(
        book_id=maz.id, volume_number=1, page_number=200,
        source_url="https://lib.eshia.ir/13033/1/200", checksum="corrob",
        html_raw=(
            '<td class="book-page-show">كتاب العقل والجهل '
            f"* الأصل: 13 - {quoted}. "
            "الشرح: (العقل غطاء ستير) أي ساتر للعيوب.</td>"
        ),
    ))
    db.commit()

    stats = index_sharh_al_mazandarani(db)
    row = db.query(HadithCommentary).one()

    assert stats.matched == 1
    assert row.match_method == "text_and_ordinal"
    assert row.match_score < 0.985          # would have failed on text alone
    assert row.match_score >= 0.90
    assert row.match_evidence_json["ordinal_corroborates"] is True


def test_contested_hadith_goes_to_the_best_evidenced_claimant():
    """Not to whichever unit the loop happened to reach first."""
    from eshia_research.commentary.mazandarani import _UnitDecision, _settle_contention

    class FakeHadith:
        id = 7
        public_id = "alkafi-7"

    weak = _UnitDecision(_unit(1, 3), FakeHadith(), "matched", "text_only", 0.99, {})
    strong = _UnitDecision(_unit(2, 3), FakeHadith(), "matched", "text_and_ordinal", 0.93, {})
    # Same target for both; the corroborated one must win despite a lower score.
    strong.hadith = weak.hadith

    claimed = _settle_contention([weak, strong])

    assert claimed == {7}
    assert strong.match_status == "matched"
    assert weak.match_status == "needs_review"
    assert weak.match_method == "duplicate_candidate"
    assert weak.evidence["lost_to_source_sequence"] == 2


def test_source_runs_split_when_the_numbering_restarts():
    """A merged chapter reads 1..3,1..2; without splitting, the second 1 and 2
    share an ordinal with the first and drop out of the run entirely."""
    from eshia_research.commentary.mazandarani import build_source_runs

    units = [
        _unit(1, 1), _unit(2, 2), _unit(3, 3),
        _unit(4, 1), _unit(5, 2),
    ]

    runs = build_source_runs(units)

    assert [sorted(r.units_by_ordinal) for r in runs] == [[1, 2, 3], [1, 2]]
    # every unit is reachable by position, none silently dropped
    placed = [u for r in runs for u in r.units_by_ordinal.values()]
    assert len(placed) == 5


def test_ordinals_are_filled_within_a_run_not_across_runs():
    units = [_unit(1, 5, occurrence=1), _unit(2, None, occurrence=2), _unit(3, 2, occurrence=2)]

    fill_missing_ordinals(units)

    # The gap sits at the head of run 2, so it counts back from 2, not from 5.
    assert units[1].printed_number == 1


def _page(number: int, body: str, volume: int = 2) -> Page:
    return Page(
        book_id=1,
        volume_number=volume,
        page_number=number,
        source_url=f"https://lib.eshia.ir/13033/{volume}/{number}",
        checksum=f"maz-{volume}-{number}",
        html_raw=f'<td class="book-page-show">{body}</td>',
    )


def test_gloss_is_separated_from_the_commentary():
    """The real shape from v2 p26: body breaks off, gloss follows unmarked."""
    text = (
        "سواء سبقوه بالزمان أو لحقوه (1) ولا شك أن النسبة الثانية آكد كما في "
        "1 - كأنه أراد بالعلماء الراسخين علماء الشريعة"
    )

    body, gloss, uncertain = split_gloss(text)

    assert not uncertain
    assert body.endswith("كما في")
    assert gloss.startswith("1 -")
    assert "كأنه أراد" in gloss
    assert "كأنه أراد" not in body


def test_text_without_references_is_left_alone():
    text = "قوله عليه السلام العلم نور وليس فيه تعليق على الهامش"

    body, gloss, uncertain = split_gloss(text)

    assert (body, gloss, uncertain) == (text, "", False)


def test_unresolved_reference_is_reported_as_uncertain_not_guessed():
    """A reference whose note never appears must not cut the commentary."""
    text = "وقد مر بيانه (2) في الباب السابق وليس هنا هامش مرقم"

    body, gloss, uncertain = split_gloss(text)

    assert uncertain is True
    assert body == text
    assert gloss == ""


def test_digit_dash_inside_prose_does_not_start_the_gloss():
    """Searching from the start of the page would cut the commentary in half."""
    text = "ذكر 1 - الوجه الأول ثم قال (1) وبعده 1 - كأنه أراد الشريعة"

    body, gloss, _uncertain = split_gloss(text)

    # The gloss run is found after the reference, not at the earlier "1 -".
    assert "الوجه الأول" in body
    assert gloss.startswith("1 -")
    assert "كأنه أراد" in gloss


def test_units_carry_report_commentary_and_chapter_ordinal():
    page = _page(
        21,
        "باب صفة العلم باب صفة العلم وفضله وفضل العلماء "
        "* الأصل: 1 - محمد بن الحسن عن سهل بن زياد قال العلم نور. "
        "الشرح: (العلم نور) أي كاشف عن الحقائق. "
        "* الأصل: 2 - محمد بن يحيى عن أحمد بن محمد قال العلماء ورثة الأنبياء. "
        "الشرح: (ورثة الأنبياء) لأنهم يحفظون الشريعة.",
    )

    units = extract_units([page])

    assert [u.printed_number for u in units] == [1, 2]
    assert units[0].section_title == "باب صفة العلم وفضله وفضل العلماء"
    assert units[0].report.endswith("العلم نور.")
    assert units[0].commentary.startswith("(العلم نور)")
    assert "الأصل" not in units[0].commentary
    assert all(u.publishable for u in units)


def test_markers_without_a_colon_are_recognised():
    """Volume 8 writes «* الأصل 1 - …» and «* الشرح قوله …», no colons."""
    page = _page(
        2,
        "باب طينة المؤمن والكافر "
        "* الأصل 1 - علي بن إبراهيم، عن أبيه، عن حماد قال العلم نور. "
        "* الشرح قوله (العلم نور) أي كاشف عن الحقائق.",
    )

    units = extract_units([page])

    assert len(units) == 1
    assert units[0].printed_number == 1
    assert units[0].report.endswith("العلم نور.")
    assert units[0].commentary.startswith("قوله (العلم نور)")


def test_the_words_alone_do_not_open_a_unit():
    """«الأصل» and «الشرح» are ordinary words in the commentator's prose."""
    page = _page(
        3,
        "* الأصل: 1 - علي بن إبراهيم قال شيئا. "
        "الشرح: قدم الايمان لأنه الأصل والأهم وهذا الشرح واضح بلا علامة.",
    )

    units = extract_units([page])

    assert len(units) == 1
    assert "لأنه الأصل والأهم" in units[0].commentary


def test_running_header_is_not_mistaken_for_the_chapter_title():
    """The edition prints a truncated header before the full title."""
    page = _page(
        39,
        "باب أصناف الناس باب أصناف الناس وفضل العلماء منهم "
        "* الأصل: 1 - علي بن محمد عن سهل قال الناس ثلاثة. "
        "الشرح: (الناس ثلاثة) بيان للأصناف.",
    )

    units = extract_units([page])

    assert units[0].section_title == "باب أصناف الناس وفضل العلماء منهم"


def test_chapter_title_stops_where_the_commentary_starts():
    """A chapter can open with no «الأصل» on the page, the sharh running on.

    Swallowing that prose into the title destroys the title agreement the
    alignment layer relies on to pair the chapter.
    """
    page = _page(
        3,
        "كتاب فرض العلم (ووجوب طلبه) العطف للتفسير والتكرير للتأكيد (والحث عليه).",
    )

    read = extract_units([page])
    from eshia_research.commentary.mazandarani import opening_chapter_title

    assert opening_chapter_title(
        "كتاب فرض العلم (ووجوب طلبه) العطف للتفسير والتكرير للتأكيد."
    ) == "كتاب فرض العلم"
    assert read == []  # no الأصل marker on this page, so no unit yet


def test_a_unit_with_an_unresolved_gloss_is_not_publishable():
    page = _page(
        50,
        "باب حق العالم * الأصل: 1 - علي بن محمد قال للعالم حق. "
        "الشرح: (للعالم حق) وقد مر (3) بيانه بلا هامش مرقم هنا.",
    )

    units = extract_units([page])

    assert units[0].gloss_uncertain is True
    assert units[0].publishable is False


def test_chapter_runs_increment_only_when_the_title_changes():
    first = _page(
        21,
        "باب الأول * الأصل: 1 - نص أول قال شيئا. الشرح: بيان أول.",
    )
    second = _page(
        22,
        "باب الأول * الأصل: 2 - نص ثان قال شيئا. الشرح: بيان ثان.",
    )
    third = _page(
        23,
        "باب الثاني * الأصل: 1 - نص ثالث قال شيئا. الشرح: بيان ثالث.",
    )

    units = extract_units([first, second, third])

    assert [u.section_occurrence for u in units] == [1, 1, 2]


def test_a_unit_without_an_ordinal_is_still_publishable_by_text():
    """The edition omits the number in its group stretches.

    An ordinal places a unit by position; text identification does not need one,
    so a missing number must not exclude the unit from matching entirely.
    """
    page = _page(
        81,
        "باب الحجة * الأصل: - علي بن إبراهيم، عن أحمد بن محمد، عن محمد بن خالد قال العلم نور. "
        "الشرح: (العلم نور) أي كاشف.",
    )

    units = extract_units([page])

    assert units[0].printed_number is None
    assert units[0].publishable is True


def test_report_without_a_sharh_marker_yields_no_commentary():
    page = _page(
        60,
        "باب النوادر * الأصل: 1 - علي بن محمد قال شيئا ولم يشرحه المصنف.",
    )

    units = extract_units([page])

    assert units[0].report.startswith("علي بن محمد")
    assert units[0].commentary == ""
    assert units[0].publishable is False


def test_unit_spanning_a_page_break_reports_its_true_extent():
    first = _page(
        70,
        "باب البذل * الأصل: 1 - محمد بن يحيى عن أحمد قال ابذل العلم. الشرح: (ابذل العلم) أي",
    )
    second = _page(71, "لا تكتمه عن أهله فإن كتمانه مذموم.")

    units = extract_units([first, second])

    assert units[0].page_start == 70
    assert units[0].page_end == 71
    assert "لا تكتمه" in units[0].commentary
