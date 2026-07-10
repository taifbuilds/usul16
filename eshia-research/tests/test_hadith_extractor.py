import pytest
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.hadith_extractor import (
    parse_page_state,
    parse_page_text,
    rebuild_hadith_index,
    split_isnad_matn,
)
from eshia_research.models import Book, Hadith, Page


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


def test_parse_page_text_does_not_index_numbered_bab_heading_as_hadith():
    units = parse_page_text(
        "١ ـ باب الاحداث الموجبة للطهارة\n"
        "ذكر الشيخ أيده الله تعالى ان جميع ما يوجب الطهارة عشرة أشياء.\n"
        "١ ـ محمد بن يعقوب عن علي بن إبراهيم عن أبيه قال: قال أبو عبد الله عليه السلام متن."
    )

    assert units[0].kind == "heading"
    assert [unit.number for unit in units if unit.kind == "hadith"] == ["١"]


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
