import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.hadith_extractor import (
    parse_page_state,
    parse_page_text,
    rebuild_hadith_index,
    split_direct_attribution,
    split_isnad_matn,
)
from eshia_research.models import Book, Hadith, Page


@pytest.mark.parametrize(
    ("text", "expected_isnad", "expected_matn_start"),
    [
        ("وَ قَالَ الصَّادِقُ ع‌ إِذَا كَانَ الْمَاءُ قَدْرَ قُلَّتَيْنِ", "و قال الصادق ع", "إِذَا كَانَ"),
        ("وَ قَالَ رَسُولُ اللَّهِ ص كُلُّ شَيْءٍ يَجْتَرُّ", "و قال رسول الله ص", "كُلُّ شَيْءٍ"),
        ("قَالَ الصَّادِقُ ع- كَانَ رَسُولُ اللَّهِ ص أَشَدَّ", "قال الصادق ع", "كَانَ رَسُولُ"),
        ("وَ قَالَ أَبُو جَعْفَرٍ ع إِذَا بَالَ الرَّجُلُ", "و قال ابو جعفر ع", "إِذَا بَالَ"),
    ],
)
def test_split_direct_attribution_mursal(text, expected_isnad, expected_matn_start):
    result = split_direct_attribution(text)
    assert result is not None
    isnad, matn = result
    assert normalise(isnad) == normalise(expected_isnad)
    assert matn.startswith(expected_matn_start)


@pytest.mark.parametrize(
    "text",
    [
        # A real chain, not a mursal attribution.
        "رَوَى ابْنُ مُسْكَانَ عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ لَا يُذْبَحُ",
        # Bare «قال ع» — no Imam named.
        "وَ قَالَ ع إِنَّ رَسُولَ اللَّهِ ص",
        # Nested speech — a narrator quotes the Imam (belongs to a chain).
        "وَ قَالَ زُرَارَةُ قَالَ أَبُو جَعْفَرٍ ع كَذَا",
        # Not an attribution opening at all.
        "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
    ],
)
def test_split_direct_attribution_refuses_non_mursal(text):
    assert split_direct_attribution(text) is None


def normalise(text: str) -> str:
    from eshia_research.normalise import normalise_arabic_persian

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


def _book(db: Session, source_book_id: str = "11005") -> Book:
    book = Book(
        source_book_id=source_book_id,
        title_original="الكافي",
        title_normalised="الكافي",
        source_url=f"https://lib.eshia.ir/{source_book_id}",
    )
    db.add(book)
    db.flush()
    return book


def _page(db: Session, book: Book, page_number: int, text: str) -> Page:
    page = Page(
        book_id=book.id,
        volume_number=1,
        page_number=page_number,
        text_raw=text,
        source_url=f"https://lib.eshia.ir/{book.source_book_id}/1/{page_number}",
        checksum=f"{book.id}-{page_number}",
    )
    db.add(page)
    db.flush()
    return page


def test_parse_page_text_detects_printed_hadith_numbers():
    units = parse_page_text(
        "1- محمد بن يعقوب عن علي بن إبراهيم عن أبيه قال: قال أبو عبد الله عليه السلام متن أول.\n"
        "2- عدة من أصحابنا عن أحمد بن محمد قال: سألت أبا الحسن عليه السلام عن العلم فقال متن ثان."
    )

    hadiths = [unit for unit in units if unit.kind == "hadith"]

    assert [unit.number for unit in hadiths] == ["١", "٢"]
    assert hadiths[0].sequence_in_page == 1
    assert "متن أول" in hadiths[0].text


def test_parse_page_text_restores_number_after_flattened_page_number():
    units = parse_page_text(
        "2- عدة من أصحابنا عن أحمد قال: متن. "
        "65 3- علي بن إبراهيم عن أبيه قال: متن آخر."
    )

    hadiths = [unit for unit in units if unit.kind == "hadith"]

    assert [unit.number for unit in hadiths] == ["٢", "٣"]
    assert not hadiths[1].text.startswith("65")


def test_parse_page_text_discards_outer_number_before_real_marker():
    units = parse_page_text(
        "8- عدة من أصحابنا عن أحمد قال: متن. "
        "15- 9- محمد بن يحيى عن أحمد قال: التالي."
    )

    hadiths = [unit for unit in units if unit.kind == "hadith"]

    assert [unit.number for unit in hadiths] == ["٨", "٩"]
    assert not hadiths[1].text.startswith("9-")


def test_parse_page_text_detects_numbered_variant_without_dash():
    units = parse_page_text(
        "5- علي عن أبيه قال: متن. "
        "6 ورواه- عن زرارة قال: متن ثان."
    )

    hadiths = [unit for unit in units if unit.kind == "hadith"]

    assert [unit.number for unit in hadiths] == ["٥", "٦"]
    assert hadiths[1].text.startswith("ورواه")


def test_parse_page_text_detects_numbered_fi_riwaya_without_dash():
    units = parse_page_text(
        "1- عدة من أصحابنا عن أحمد قال: متن. "
        "2 و في رواية- عبد الأعلى عن أبي عبد الله قال: متن ثان."
    )

    hadiths = [unit for unit in units if unit.kind == "hadith"]

    assert [unit.number for unit in hadiths] == ["١", "٢"]
    assert hadiths[1].text.startswith("و في رواية")


def test_citation_page_before_fi_riwaya_is_not_a_hadith_boundary():
    units = parse_page_text(
        "1- محمد بن يحيى عن أحمد قال: متن[2].\n"
        "[2] المحاسن ص 414 في رواية أخرى عن عبد الرحمن قال: شرح النسخة."
    )

    assert [unit.number for unit in units if unit.kind == "hadith"] == ["١"]


def test_parse_page_text_keeps_numbered_editorial_note_out_of_hadiths():
    units, parser = parse_page_state(
        "1- علي عن أبيه قال: متن[2].\n"
        "[2] الحج: 28. قوله: شرح الآية."
    )

    assert [unit.number for unit in units if unit.kind == "hadith"] == ["١"]
    assert any(unit.kind == "footnote" for unit in units)
    assert parser.saw_hadith is True


def test_multiline_trailing_footnote_does_not_close_cross_page_hadith():
    units, _parser = parse_page_state(
        "1- علي عن أبيه قال: متن ينتهي في الصفحة التالية[2].\n"
        "[2] قوله: شرح أول.\n"
        "وتتمة الشرح في السطر التالي."
    )

    assert [unit.kind for unit in units] == ["hadith", "footnote"]
    assert "وتتمة الشرح" in units[1].text
    last_main = next(unit for unit in reversed(units) if unit.kind != "footnote")
    assert last_main.kind == "hadith"


def test_bare_dotted_footnote_marker_does_not_prefix_next_hadith_number():
    units = parse_page_text(
        "564- علي عن أبيه قال: متن طويل[3].\n"
        "[3].\n"
        "565- أبان عن أبي بصير عن أبي عبد الله قال: متن تال."
    )

    assert [unit.number for unit in units if unit.kind == "hadith"] == ["٥٦٤", "٥٦٥"]


def test_small_bracketed_footnote_marker_is_not_outer_large_hadith_serial():
    units = parse_page_text("[3] 565- أبان عن أبي بصير عن أبي عبد الله قال: متن.")

    assert [unit.number for unit in units if unit.kind == "hadith"] == ["٥٦٥"]


def test_parse_page_text_does_not_index_numbered_bab_heading_as_hadith():
    units = parse_page_text(
        "١ ـ باب الاحداث الموجبة للطهارة\n"
        "ذكر الشيخ أيده الله تعالى ان جميع ما يوجب الطهارة عشرة أشياء.\n"
        "١ ـ محمد بن يعقوب عن علي بن إبراهيم عن أبيه قال: قال أبو عبد الله عليه السلام متن."
    )

    assert units[0].kind == "heading"
    assert [unit.number for unit in units if unit.kind == "hadith"] == ["١"]


def test_parse_page_text_treats_standalone_hadith_title_as_heading():
    units = parse_page_text(
        "منكم ثم قال تتمة الحديث السابق.\n"
        "حَدِيثُ قَوْمِ صَالِحٍ ع\n"
        "213- علي بن إبراهيم عن أبيه قال: متن جديد."
    )

    assert [unit.kind for unit in units] == ["continuation", "heading", "hadith"]
    assert units[1].text == "حَدِيثُ قَوْمِ صَالِحٍ ع"


def test_parse_page_text_does_not_index_reference_list_as_hadith():
    units = parse_page_text(
        "مراجعنا في التعليق و رموزها\n"
        "1- مرآة العقول، للمجلسيّ- ره- [آت]\n"
        "2- الوافي؛ للفيض الكاشاني- ره- [فى]"
    )

    assert [unit.kind for unit in units] == ["commentary", "commentary", "commentary"]


def test_split_isnad_matn_preserves_raw_matn():
    isnad, matn = split_isnad_matn(
        "محمد بن يحيى عن أحمد بن محمد عن ابن محبوب قال: قال أبو عبد الله عليه السلام طلب العلم فريضة."
    )

    assert isnad == "محمد بن يحيى عن أحمد بن محمد عن ابن محبوب قال:"
    assert matn == "قال أبو عبد الله عليه السلام طلب العلم فريضة."


def test_split_isnad_matn_handles_dual_qala_boundary():
    isnad, matn = split_isnad_matn(
        "محمد بن يعقوب عن علي عن أبيه عن زرارة ومحمد بن مسلم عن أبي جعفر وأبي عبد الله عليهما السلام قالا : "
        "في صدقة الإبل في كل خمس شاة. قال قلت : تتمة داخل المتن."
    )

    assert isnad == "محمد بن يعقوب عن علي عن أبيه عن زرارة ومحمد بن مسلم عن أبي جعفر وأبي عبد الله عليهما السلام قالا :"
    assert matn.startswith("في صدقة الإبل")
    assert "قال قلت" in matn


def test_split_isnad_matn_prefers_terminal_narrator_speech_over_compiler_qala():
    isnad, matn = split_isnad_matn(
        "أخبرنا أبو جعفر محمد بن يعقوب قال حدثني عدة من أصحابنا منهم محمد بن يحيى العطار "
        "عن أحمد بن محمد عن الحسن بن محبوب عن العلاء بن رزين عن محمد بن مسلم "
        "عن أبي جعفر ع قال: لما خلق الله العقل استنطقه ثم قال له أقبل."
    )

    assert isnad == (
        "أخبرنا أبو جعفر محمد بن يعقوب قال حدثني عدة من أصحابنا منهم محمد بن يحيى العطار "
        "عن أحمد بن محمد عن الحسن بن محبوب عن العلاء بن رزين عن محمد بن مسلم "
        "عن أبي جعفر ع قال:"
    )
    assert matn.startswith("لما خلق الله العقل")
    assert "حدثني عدة من أصحابنا" not in matn


def test_split_isnad_matn_handles_an_report_without_qala():
    isnad, matn = split_isnad_matn(
        "الحسين بن سعيد عن ابن أبي عمير عن عمر بن أذينة عن رهط عن كليهما عليهما السلام "
        "ان صلاة كسوف الشمس والقمر عشر ركعات وأربع سجدات."
    )

    assert isnad == "الحسين بن سعيد عن ابن أبي عمير عن عمر بن أذينة عن رهط عن كليهما عليهما السلام"
    assert matn.startswith("ان صلاة كسوف")


def test_split_isnad_matn_handles_terminal_colon_report():
    isnad, matn = split_isnad_matn(
        "علي بن حاتم عن محمد بن عبد الله عن أبان بن تغلب عن أبي عبد الله عليه السلام : "
        "(اللهم إني أسألك باسمك المكتوب في سرادق المجد)."
    )

    assert isnad == "علي بن حاتم عن محمد بن عبد الله عن أبان بن تغلب عن أبي عبد الله عليه السلام :"
    assert matn.startswith("(اللهم")


def test_split_isnad_matn_handles_terminal_fi_report():
    isnad, matn = split_isnad_matn(
        "محمد بن يعقوب عن علي عن أبيه عن حريز عن زرارة عن أبي جعفر وأبي عبد الله عليهما السلام "
        "في الشاة في كل أربعين شاة شاة."
    )

    assert isnad == "محمد بن يعقوب عن علي عن أبيه عن حريز عن زرارة عن أبي جعفر وأبي عبد الله عليهما السلام"
    assert matn.startswith("في الشاة")


def test_split_isnad_matn_handles_vocalised_fi_after_imam_marker():
    isnad, matn = split_isnad_matn(
        "\u0623\u064e\u0628\u064f\u0648 \u0639\u064e\u0644\u0650\u064a\u0651\u064d \u0627\u0644\u0652\u0623\u064e\u0634\u0652\u0639\u064e\u0631\u0650\u064a\u0651\u064f \u0639\u064e\u0646\u0652 \u0645\u064f\u062d\u064e\u0645\u0651\u064e\u062f\u0650 \u0628\u0652\u0646\u0650 \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0652\u062c\u064e\u0628\u0651\u064e\u0627\u0631\u0650 "
        "\u0639\u064e\u0646\u0652 \u0635\u064e\u0641\u0652\u0648\u064e\u0627\u0646\u064e \u0628\u0652\u0646\u0650 \u064a\u064e\u062d\u0652\u064a\u064e\u0649 \u0639\u064e\u0646\u0652 \u0639\u0650\u064a\u0635\u0650 \u0628\u0652\u0646\u0650 \u0627\u0644\u0652\u0642\u064e\u0627\u0633\u0650\u0645\u0650 "
        "\u0639\u064e\u0646\u0652 \u0623\u064e\u0628\u0650\u064a \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0639 \u0641\u0650\u064a \u0627\u0644\u0652\u0647\u064e\u0631\u0650\u0645\u0650 \u0627\u0644\u0651\u064e\u0630\u0650\u064a \u0648\u064e\u0642\u064e\u0639\u064e\u062a\u0652 \u062b\u064e\u0646\u064e\u0627\u064a\u064e\u0627\u0647\u064f."
    )

    assert isnad is not None
    assert isnad.endswith("\u0623\u064e\u0628\u0650\u064a \u0639\u064e\u0628\u0652\u062f\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0639")
    assert matn.startswith("\u0641\u0650\u064a \u0627\u0644\u0652\u0647\u064e\u0631\u0650\u0645\u0650")


def test_split_isnad_matn_does_not_split_deep_matn_an_as_chain():
    isnad, matn = split_isnad_matn(
        "وقال الرضا عليه السلام : قال علي بن الحسين عليه السلام : إذا رأيتم الرجل يعف عن المال الحرام "
        "فرويداً لا يغركم فإن في الناس من يرى أن لذة الرئاسة الباطلة أفضل."
    )

    assert isnad is None
    assert matn.startswith("وقال الرضا")


def test_rebuild_hadith_index_persists_ids_and_merges_page_continuations(db: Session):
    book = _book(db)
    _page(
        db,
        book,
        10,
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام بداية المتن.",
    )
    _page(
        db,
        book,
        11,
        "وتكملة المتن من الصفحة التالية.\n"
        "2- علي بن إبراهيم عن أبيه قال: قال أبو جعفر عليه السلام متن آخر.",
    )
    db.commit()

    stats = rebuild_hadith_index(db, source_book_ids=["11005"], commit=True)

    rows = db.query(Hadith).order_by(Hadith.sequence_in_book).all()
    assert stats.hadiths == 2
    assert rows[0].public_id == "alkafi-1"
    assert rows[1].public_id == "alkafi-2"
    assert rows[0].page_end == 11
    assert "وتكملة المتن" in rows[0].matn_raw
    assert rows[1].printed_number == "٢"
    assert rows[1].isnad_raw is not None


def test_rebuild_hadith_index_does_not_merge_continuation_across_volumes(db: Session):
    book = _book(db)
    db.add(
        Page(
            book_id=book.id,
            volume_number=1,
            page_number=20,
            text_raw="1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام خاتمة المجلد.",
            source_url=f"https://lib.eshia.ir/{book.source_book_id}/1/20",
            checksum="v1",
        )
    )
    db.add(
        Page(
            book_id=book.id,
            volume_number=2,
            page_number=1,
            text_raw="مقدمة المجلد التالي وليست تتمة الحديث.",
            source_url=f"https://lib.eshia.ir/{book.source_book_id}/2/1",
            checksum="v2",
        )
    )
    db.commit()

    rebuild_hadith_index(db, source_book_ids=["11005"], commit=True)

    hadith = db.query(Hadith).one()
    assert hadith.volume_end == 1
    assert hadith.page_end == 20


def test_rebuild_hadith_index_excludes_duplicate_al_kafi_by_default(db: Session):
    duplicate = _book(db, source_book_id="27311")
    _page(
        db,
        duplicate,
        1,
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام متن.",
    )
    db.commit()

    stats = rebuild_hadith_index(db, source_book_ids=["27311"], commit=True)

    assert stats.hadiths == 0
    assert db.query(Hadith).count() == 0


def test_parse_page_text_splits_inline_commentary_after_marker():
    units = parse_page_text(
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام أصل المتن [١] بيان : شرح المحقق.\n"
        "2- علي بن إبراهيم عن أبيه قال: قال أبو جعفر عليه السلام متن ثان."
    )

    assert [unit.kind for unit in units] == ["hadith", "commentary", "hadith"]
    assert "بيان" not in units[0].text
    assert units[0].text.endswith("[١]")
    assert units[1].text.startswith("بيان")


def test_parse_page_text_splits_inline_commentary_after_colon():
    units = parse_page_text(
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام منهوم علم ومنهوم مال : بيان : شرح المحقق.\n"
        "2- علي بن إبراهيم عن أبيه قال: قال أبو جعفر عليه السلام متن ثان."
    )

    assert [unit.kind for unit in units] == ["hadith", "commentary", "hadith"]
    assert "بيان" not in units[0].text
    assert units[0].text.endswith(":")


def test_parse_page_text_splits_unpunctuated_bayan_commentary():
    units = parse_page_text(
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام البيت الخرب لاعامر له بيان : شرح المحقق.\n"
        "2- علي بن إبراهيم عن أبيه قال: قال أبو جعفر عليه السلام متن ثان."
    )

    assert [unit.kind for unit in units] == ["hadith", "commentary", "hadith"]
    assert units[0].text.endswith("لاعامر له")
    assert units[1].text.startswith("بيان")


def test_parse_page_text_splits_parenthesized_bab_heading_after_hadith():
    units = parse_page_text(
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام العلم مقرون إلى العمل. "
        "(باب ١٠) *(حق العالم)* الآيات ، الكهف : قال له موسى هل أتبعك.\n"
        "2- علي بن إبراهيم عن أبيه قال: قال أبو جعفر عليه السلام متن ثان."
    )

    assert [unit.kind for unit in units] == ["hadith", "heading", "hadith"]
    assert "(باب" not in units[0].text
    assert units[1].text.startswith("(باب")


def test_parse_page_text_treats_subject_page_table_as_fihrist():
    units = parse_page_text(
        "الموضوع الصفحة باب ١٤ من رفع عنه القلم ؛ وفيه ٢٩ حديثا ٢٩٨ ـ ٣٠٨ "
        "باب ١٥ علة خلق العباد ؛ وفيه ١٨ حديثا ٣٠٩ ـ ٣١٨"
    )

    assert units
    assert all(unit.kind in {"heading", "commentary"} for unit in units)
    assert not [unit for unit in units if unit.kind == "hadith"]


def test_parse_page_state_splits_end_of_part_note_from_continuation():
    units, _parser = parse_page_state(
        "وتتمة الحديث الحقيقي. إلى هنا تم الجزء الأول من بحار الأنوار.",
        initial_saw_hadith=True,
    )

    assert [unit.kind for unit in units] == ["continuation", "commentary"]
    assert "إلى هنا" not in units[0].text
    assert units[1].text.startswith("إلى هنا تم")


def test_rebuild_hadith_index_skips_bihar_intro_abbreviation_pages(db: Session):
    book = _book(db, source_book_id="71860")
    _page(
        db,
        book,
        47,
        "7- ع : لعلل الشرائع. ك : لإكمال الدين. عم : لإعلام الورى. ضه : لروضة الواعظين.",
    )
    _page(
        db,
        book,
        82,
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام متن.",
    )
    db.commit()

    stats = rebuild_hadith_index(db, source_book_ids=["71860"], commit=True)

    rows = db.query(Hadith).order_by(Hadith.sequence_in_book).all()
    assert stats.hadiths == 1
    assert len(rows) == 1
    assert rows[0].public_id == "bihar-1"
    assert rows[0].page_start == 82
    assert "لعلل الشرائع" not in rows[0].full_text_raw


def test_rebuild_hadith_index_does_not_append_bihar_apparatus_pages(db: Session):
    book = _book(db, source_book_id="71860")
    _page(
        db,
        book,
        82,
        "1- محمد بن يحيى عن أحمد بن محمد قال: قال أبو عبد الله عليه السلام متن.",
    )
    _page(
        db,
        book,
        83,
        "رموز الكتاب ب : لقرب الاسناد. ع : للعلل الشرائع. عم : لإعلام الورى.",
    )
    _page(
        db,
        book,
        84,
        "الموضوع الصحيفة باب ١ أحوال البرزخ وفيه ٥٦ حديثا ١٧٣ ـ ٢٠٢.",
    )
    db.commit()

    stats = rebuild_hadith_index(db, source_book_ids=["71860"], commit=True)

    rows = db.query(Hadith).order_by(Hadith.sequence_in_book).all()
    assert stats.hadiths == 1
    assert rows[0].page_end == 82
    assert "رموز الكتاب" not in rows[0].full_text_raw
    assert "الموضوع الصحيفة" not in rows[0].full_text_raw
