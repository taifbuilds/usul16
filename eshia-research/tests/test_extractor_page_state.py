"""Cross-page extraction regressions found by the 2026-07-06 full scan."""

from eshia_research.hadith_extractor import parse_page_state, parse_page_text


def kinds(units):
    return [u.kind for u in units]


def test_mid_hadith_page_yields_continuations_when_seeded():
    # A page entirely inside a long hadith: no number anywhere on it.
    text = "وَ اعْلَمْ أَنَّ الصَّبْرَ مِنَ الْإِيمَانِ بِمَنْزِلَةِ الرَّأْسِ مِنَ الْجَسَدِ فَاصْبِرُوا"
    units, _ = parse_page_state(text, initial_saw_hadith=True)
    assert kinds(units) == ["continuation"]
    # Without seeding (previous page ended in commentary), same text is NOT
    # a continuation.
    units2, _ = parse_page_state(text, initial_saw_hadith=False)
    assert kinds(units2) == ["text"]


def test_takhrij_star_line_is_footnote_not_matn():
    text = (
        "١ ـ مُحَمَّدُ بْنُ يَحْيَى عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ عَنْ حَمَّادٍ "
        "عَنْ زُرَارَةَ عَنْ أَبِي جَعْفَرٍ ع قَالَ: لَا صَلَاةَ إِلَّا بِطَهُورٍ.\n"
        "* (٢٢) الاستبصار ج ١ ص ٨٢ الكافي ج ١ ص ١٢ الفقيه ج ١ ص ٣٧."
    )
    units = parse_page_text(text)
    assert kinds(units) == ["hadith", "footnote"]
    assert units[1].number == "٢٢"
    assert "الاستبصار" in units[1].text


def test_inline_takhrij_mid_hadith_is_stripped_and_continuation_kept():
    # Real Tahdhib shape: the takhrij run interrupts the isnad at a page
    # break; the hadith resumes right after it on the same line.
    text = (
        "١ ـ أخبرني أبو القاسم جعفر بن محمد عن محمد بن يعقوب عن الوشا "
        "* (٣٩) (٣٨) (٤٠) الاستبصار ج ١ ص ٩١ واخرج الاول الكليني في الكافي "
        "ج ١ ص ١٢ بتفاوت يسير. عن أبان عن عنبسة قال : سمعت أبا عبد الله "
        "عليه‌السلام يقول : كذا."
    )
    units = parse_page_text(text)
    hadiths = [u for u in units if u.kind == "hadith"]
    footnotes = [u for u in units if u.kind == "footnote"]
    assert len(hadiths) == 1 and len(footnotes) == 1
    assert "الاستبصار" not in hadiths[0].text
    assert "عن أبان عن عنبسة" in hadiths[0].text  # continuation preserved
    assert "الاستبصار" in footnotes[0].text
    assert footnotes[0].number == "٣٩"


def test_fihrist_lines_are_not_hadiths():
    text = (
        "فهرس ما في هذا الجزء\n"
        "٥ ـ طهور الماء.\n"
        "١٤ ـ الآبار و أحكامها.\n"
        "١٧ ـ منزوحات البئر."
    )
    units, parser = parse_page_state(text)
    assert parser.in_fihrist
    assert all(u.kind != "hadith" for u in units)
    # Carried onto the next index page: still no hadiths.
    units2, _ = parse_page_state("٢٢ ـ ارتياد المكان للحدث.", initial_in_fihrist=True)
    assert all(u.kind != "hadith" for u in units2)


def test_section_title_carries_across_pages():
    page1 = (
        "١ ـ بَابُ حُدُوثِ الْعَالَمِ\n"
        "١ ـ عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ أَبِيهِ عَنِ ابْنِ أَبِي عُمَيْرٍ "
        "عَنْ أَبِي عَبْدِ اللَّهِ ع قَالَ: الْحَمْدُ لِلَّهِ."
    )
    units1, parser1 = parse_page_state(page1)
    section = parser1.current_section
    assert section and "حدوث" in section.replace("ُ", "").replace("ْ", "").replace("َ", "").replace("ِ", "")
    page2 = (
        "٢ ـ مُحَمَّدُ بْنُ يَحْيَى عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ عَنْ زُرَارَةَ "
        "عَنْ أَبِي جَعْفَرٍ ع قَالَ: كَذَا."
    )
    units2, _ = parse_page_state(page2, initial_section=section)
    hadiths = [u for u in units2 if u.kind == "hadith"]
    assert hadiths and hadiths[0].section_title == section


def test_heading_stops_continuation_marking():
    # Page opens with a new bab heading; the prose after it must not be
    # glued to the previous page's hadith.
    text = (
        "بَابُ النَّوَادِرِ\n"
        "١ ـ عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ أَبِيهِ عَنْ حَمَّادٍ عَنْ أَبِي "
        "عَبْدِ اللَّهِ ع قَالَ: كَذَا."
    )
    units, _ = parse_page_state(text, initial_saw_hadith=True)
    assert kinds(units)[0] == "heading"
    assert "continuation" not in kinds(units)


def test_inline_footnote_body_is_split_from_hadith_text():
    text = (
        "١٢ ـ ثو ، يد : أبي ، عن سعد ، عن ابن عيسى ، عن الحسين بن سيف ، "
        "عن أخيه [١]بالباء المفتوحة والطاء المهملة ، هو علي بن أبي حمزة. "
        "[٢]هو البطائني المتقدم."
    )

    units = parse_page_text(text)

    assert kinds(units) == ["hadith", "footnote", "footnote"]
    assert units[0].text.endswith("[١]")
    assert units[1].number == "١"
    assert "بالباء المفتوحة" in units[1].text


def test_footnote_marker_before_next_hadith_does_not_swallow_hadith():
    text = (
        "١٢ ـ يد : أحمد عن علي : قال : قال رسول الله 9 : ما جزاء من أنعم عليه بالتوحيد إلا الجنة. "
        "[٣] ١٣ ـ يد : وبهذا الاسناد قال : قال رسول الله 9 : أن لا إله إلا الله كلمة عظيمة."
    )

    units = parse_page_text(text)
    hadiths = [u for u in units if u.kind == "hadith"]

    assert [h.number for h in hadiths] == ["١٢", "١٣"]
    assert hadiths[1].text.startswith("يد : وبهذا الاسناد")


def test_midline_chapter_heading_and_next_hadith_are_split():
    text = (
        "١٢ ـ كنز الكراجكي : قال الصادق 7 : أحسنوا النظر. "
        "باب ٦ *(العلوم التي امر الناس بتحصيلها)* الايات ، البقرة : يؤتي الحكمة ٢٦٩ "
        "١ ـ ل : ماجيلويه ، عن محمد العطار ، عن علي قال : سمعت عليا 7 يقول لأبي الطفيل."
    )

    units = parse_page_text(text)

    assert [u.kind for u in units] == ["hadith", "heading", "hadith"]
    assert units[2].number == "١"
