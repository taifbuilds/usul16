from pathlib import Path

from eshia_research.crawler.parser import (
    extract_book_id,
    parse_book_subject,
    parse_category_page,
    parse_page,
    split_author_names,
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_split_author_names_splits_combined_scholar_and_compiler():
    assert split_author_names("الخوئي، السيد أبوالقاسم - ميرزا علي الغروي") == [
        "الخوئي، السيد أبوالقاسم",
        "ميرزا علي الغروي",
    ]


def test_split_author_names_does_not_split_on_intra_name_comma():
    assert split_author_names("الأسترآبادي، محمد بن علي") == ["الأسترآبادي، محمد بن علي"]


def test_split_author_names_handles_single_name_with_no_separator():
    assert split_author_names("نوری، محمد اسماعیل") == ["نوری، محمد اسماعیل"]


def test_split_author_names_handles_empty_input():
    assert split_author_names("") == []
    assert split_author_names(None) == []


def test_extract_book_id_from_book_url():
    assert extract_book_id("https://lib.eshia.ir/26395") == "26395"


def test_extract_book_id_from_page_url():
    assert extract_book_id("https://lib.eshia.ir/10009/1/1") == "10009"


def test_extract_book_id_returns_none_for_non_matching_url():
    assert extract_book_id("https://lib.eshia.ir/فقه") is None


def test_parse_category_page_extracts_book_rows():
    html = (SAMPLES_DIR / "category_listing_sample.html").read_text(encoding="utf-8")
    entries = parse_category_page(html, "https://lib.eshia.ir/فقه")

    assert len(entries) > 0
    first = entries[0]
    assert first.source_book_id == "26395"
    assert first.title_original == "آشنایی با ابواب فقه"
    assert first.source_url == "https://lib.eshia.ir/26395"
    assert first.author_name == "نوری، محمد اسماعیل"
    assert first.volume_count == 1


def test_parse_page_extracts_title_author_and_text():
    html = (SAMPLES_DIR / "page_text_sample.html").read_text(encoding="utf-8")
    parsed = parse_page(html, "https://lib.eshia.ir/10009/1/1")

    assert parsed.source_book_id == "10009"
    assert parsed.book_title == "التنقيح في شرح العروة الوثقى"
    assert parsed.author_name == "الخوئي، السيد أبوالقاسم - ميرزا علي الغروي"
    assert parsed.volume_number == 1
    assert parsed.page_number == 1
    assert parsed.is_image_only is False
    assert parsed.text is not None
    assert "بسم الله" in parsed.text
    assert parsed.next_page_url == "https://lib.eshia.ir/10009/1/2"
    assert parsed.last_page_url == "https://lib.eshia.ir/10009/1/370"


def test_parse_page_cover_page_has_text_despite_embedded_cover_image():
    # The cover/TOC page (.../26395/1/0) embeds a cover image but also has
    # real selectable metadata text around it, so it must NOT be flagged
    # image-only.
    html = (SAMPLES_DIR / "book_detail_sample.html").read_text(encoding="utf-8")
    parsed = parse_page(html, "https://lib.eshia.ir/26395/1/0")

    assert parsed.source_book_id == "26395"
    assert parsed.book_title == "آشنایی با ابواب فقه"
    assert parsed.is_image_only is False
    assert parsed.text is not None
    assert "تأليف" in parsed.text


def test_parse_book_subject_extracts_value_after_label():
    html = (SAMPLES_DIR / "book_detail_sample.html").read_text(encoding="utf-8")
    assert parse_book_subject(html) == "رساله ها و مجموعه فتاوا"


def test_parse_book_subject_returns_none_when_absent():
    html = (SAMPLES_DIR / "image_only_page_sample.html").read_text(encoding="utf-8")
    assert parse_book_subject(html) is None


def test_parse_book_subject_ignores_word_appearing_without_label_colon():
    # Regression: a <p> can contain "موضوع" as a substring (e.g. mid-sentence)
    # without the "موضوع:" label pattern actually matching — this crashed a
    # real 1500-book enrichment run when the code assumed a match existed
    # just because the substring did.
    html = """
    <table><tr><td class="book-page-show">
    <p>این کتاب موضوع جدیدی را بررسی می کند بدون نقطه دو نقطه</p>
    <p>موضوع: فقه</p>
    </td></tr></table>
    """
    assert parse_book_subject(html) == "فقه"


def test_parse_book_subject_handles_alternate_label_formats():
    from eshia_research.crawler.parser import _SUBJECT_LABEL_RE

    for label in ["موضوع:", "الموضوع:", "الموضوع :"]:
        text = f"{label} فقه"
        _, value = _SUBJECT_LABEL_RE.split(text, maxsplit=1)
        assert value.strip() == "فقه"


def test_parse_page_detects_image_only_scanned_book():
    # .../26395/1/1 is a genuine scanned page: the whole page body is a
    # single <img>, no selectable text at all.
    html = (SAMPLES_DIR / "image_only_page_sample.html").read_text(encoding="utf-8")
    parsed = parse_page(html, "https://lib.eshia.ir/26395/1/1")

    assert parsed.source_book_id == "26395"
    assert parsed.is_image_only is True
    assert parsed.text is None
