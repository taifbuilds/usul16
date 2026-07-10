from eshia_research.rijal.mujam_parser import (
    MujamPage,
    extract_occurrences,
    extract_statements,
    parse_mujam_entries,
)


def page(id_, volume, page_number, text):
    return MujamPage(
        id=id_,
        volume_number=volume,
        page_number=page_number,
        text_raw=text,
        source_url=f"https://lib.eshia.ir/14036/{volume}/{page_number}",
    )


def test_main_sequence_ignores_embedded_numbered_lists():
    pages = [
        page(
            1,
            1,
            107,
            "باب الألف\n"
            "1- آدم الأول:\n"
            "ترجمة قصيرة.\n"
            "2- آدم الثاني:\n"
            "هذا مدخل طويل يذكر قائمة داخلية.",
        ),
        page(
            2,
            1,
            108,
            "1- أبو الحسن الداخلي: [محمد بن فلان]. في ترجمة غيره.\n"
            "2- أبو عبد الله الداخلي: في ترجمة غيره.\n"
            "3- آدم الثالث:\n"
            "ترجمة ثالثة.",
        ),
    ]

    entries, stats = parse_mujam_entries(pages)

    assert [entry.entry_number for entry in entries] == [1, 2, 3]
    assert stats.headers_seen == 5
    assert stats.headers_ignored == 2
    assert entries[1].page_start == 107
    assert entries[1].page_end == 108
    assert "أبو الحسن الداخلي" in entries[1].text_raw


def test_final_entry_stops_at_its_start_page():
    pages = [
        page(1, 1, 107, "1- آدم الأول:\nترجمة قصيرة."),
        page(2, 1, 108, "2- آدم الثاني:\nآخر ترجمة في المتن."),
        page(3, 1, 109, "فهرس لاحق لا ينبغي أن يدخل في الترجمة."),
    ]

    entries, _stats = parse_mujam_entries(pages)

    assert [entry.entry_number for entry in entries] == [1, 2]
    assert entries[-1].page_start == 108
    assert entries[-1].page_end == 108
    assert "فهرس لاحق" not in entries[-1].text_raw


def test_extracts_quoted_source_statements_and_khui_comments():
    text = (
        "قال النجاشي: «عيسى بن حمزة المدائني الثقفي، روى عن أبي عبد الله (ع)، "
        "له كتاب يرويه جماعة». "
        "من أصحاب الصادق (ع)، رجال الشيخ (583). "
        "أقول: الظاهر اتحاد هذه العناوين بحسب القرائن المذكورة في الباب."
    )

    statements = extract_statements(text)

    assert {statement.statement_type for statement in statements} == {
        "quoted_statement",
        "tabaqah_membership",
        "compiler_comment",
    }
    assert statements[0].source_name == "najashi"
    assert any(statement.source_name == "tusi_rijal" for statement in statements)
    assert any(statement.source_name == "khui" for statement in statements)


def test_extracts_occurrence_notes_with_raw_references():
    text = (
        "روى عن أبي عبد الله\n(ع)\n، و روى عنه أبو مخلد السراج. "
        "الكافي: الجزء 2، كتاب الإيمان و الكفر 1، باب الكذب 139، الحديث 18. "
        "و روى عنه شعيب. التهذيب: الجزء 9، باب الذبائح، الحديث 349."
    )

    occurrences = extract_occurrences(text)

    assert [occurrence.direction for occurrence in occurrences] == [
        "narrates_from",
        "narrated_by",
        "narrated_by",
    ]
    assert occurrences[0].related_name_raw == "أبي عبد الله"
    assert occurrences[1].related_name_raw == "أبو مخلد السراج"
    assert "الكافي" in (occurrences[1].source_ref_raw or "")
    assert occurrences[2].related_name_raw == "شعيب"


def test_occurrence_reference_does_not_jump_to_next_sentence():
    text = (
        "و ذكر قبل ذلك عيسى بن حسان، روى عنه علي بن النعمان (567)، "
        "و لا يبعد اتحاد الجميع. "
        "روى عن أبي عبد الله (ع)، و روى عنه أبو مخلد السراج. "
        "الكافي: الجزء 2، كتاب الإيمان و الكفر 1، باب الكذب 139، الحديث 18."
    )

    occurrences = extract_occurrences(text)

    assert [occurrence.related_name_raw for occurrence in occurrences] == [
        "أبي عبد الله",
        "أبو مخلد السراج",
    ]
