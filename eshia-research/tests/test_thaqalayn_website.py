import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import Book, Hadith, HadithSplitReview
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.thaqalayn_website import (
    FAQIH_CORPUS,
    _add_residual_split_candidates,
    _plain_website_arabic,
    audit_thaqalayn_website,
    canonical_hadith_path,
    extract_website_matn,
    parse_alkafi_sitemap_paths,
    parse_book_chapter_paths,
    parse_sitemap_paths,
    parse_chapter_page,
    repair_website_arabic_boundaries,
    render_audit_markdown,
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


def _faqih_hadith(db: Session, *, printed_number: str, text: str) -> Hadith:
    book = Book(
        source_book_id="11021",
        title_original="Man la yahduruhu al-faqih",
        title_normalised="man la yahduruhu al-faqih",
        source_url="https://lib.eshia.ir/11021",
    )
    db.add(book)
    db.flush()
    hadith = Hadith(
        public_id="faqih-1",
        book_id=book.id,
        sequence_in_book=1,
        sequence_in_page=1,
        printed_number=printed_number,
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw=text,
        full_text_normalised=normalise_arabic_persian(text),
        isnad_raw=None,
        isnad_normalised=None,
        matn_raw=text,
        matn_normalised=normalise_arabic_persian(text),
        source_url="https://lib.eshia.ir/11021/1/1",
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    return hadith


def test_canonical_hadith_path_accepts_current_and_legacy_urls():
    assert (
        canonical_hadith_path("https://thaqalayn.net/hadith/2/1/3/4")
        == "/hadith/2/1/3/4"
    )
    assert (
        canonical_hadith_path("https://thaqalayn.net/books/al-kafi:2:1:3:4")
        == "/hadith/2/1/3/4"
    )
    assert canonical_hadith_path("https://example.com/not-a-hadith") is None


def test_extract_website_matn_uses_existing_text_only_as_exact_boundary():
    full = (
        "1. A narrator from another narrator who has said the following: "
        "The rendered website wording is authoritative."
    )
    matn, method = extract_website_matn(
        full,
        existing_matn_candidates=["The rendered website wording is authoritative."],
    )
    assert matn == "The rendered website wording is authoritative."
    assert method == "exact_existing_boundary"


def test_extract_website_matn_never_copies_nonwebsite_candidate():
    full = "2. A narrator who has said the following: Website wording only."
    matn, method = extract_website_matn(
        full,
        existing_matn_candidates=["Incorrect API wording."],
    )
    assert matn == "Website wording only."
    assert "Incorrect API wording" not in matn
    assert method == "narration_marker"


def test_plain_website_arabic_rejects_english_field_anomaly():
    assert _plain_website_arabic("Hadith. 1 - English in the wrong field.") == ""
    assert _plain_website_arabic("1 - \u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642") == "\u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642"


def test_residual_combination_rejects_distant_repeated_report():
    report = "\u0631\u0648\u0649 \u0635\u0641\u0648\u0627\u0646 \u0639\u0646 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"

    def row(row_id: int, sequence: int, text: str) -> Hadith:
        return Hadith(
            id=row_id,
            public_id=f"faqih-{row_id}",
            book_id=1,
            sequence_in_book=sequence,
            sequence_in_page=1,
            printed_number=str(sequence),
            volume_start=1,
            volume_end=1,
            page_start=1,
            page_end=1,
            full_text_raw=text,
            full_text_normalised=normalise_arabic_persian(text),
            isnad_raw=None,
            isnad_normalised=None,
            matn_raw=text,
            matn_normalised=normalise_arabic_persian(text),
            source_url="https://lib.eshia.ir/11021/1/1",
        )

    local_rows = [row(1, 1, report)] + [
        row(index, index, f"\u0646\u0635 \u0645\u062e\u062a\u0644\u0641 {index}") for index in range(2, 5)
    ] + [row(5, 5, report)]
    path = "/hadith/34/1/1/1"
    remote_rows = [{"path": path, "volume": 1, "arabic_text": report}]
    candidates = {
        (1, path): {
            "local_id": 1,
            "public_id": "faqih-1",
            "website_path": path,
            "method": "structure_map",
            "score": 1.0,
        }
    }

    _add_residual_split_candidates(
        local_rows=local_rows,
        remote_rows=remote_rows,
        candidates=candidates,
        min_score=0.88,
    )

    assert (5, path) not in candidates


def test_parse_book_chapter_paths_is_deduplicated_and_ordered():
    html = """
    <a href="/chapter/1/2/10">ten</a>
    <a href="/chapter/1/2/2">two</a>
    <a href="/chapter/1/2/2">duplicate</a>
    <a href="/chapter/2/1/1">other volume</a>
    """
    assert parse_book_chapter_paths(html, volume=1) == [
        "/chapter/1/2/2",
        "/chapter/1/2/10",
    ]


def test_parse_alkafi_sitemap_paths_filters_and_orders_routes():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://thaqalayn.net/hadith/2/1/3/4</loc></url>
      <url><loc>https://thaqalayn.net/hadith/1/2/10/2</loc></url>
      <url><loc>https://thaqalayn.net/hadith/9/1/1/1</loc></url>
      <url><loc>https://thaqalayn.net/chapter/1/2/10</loc></url>
    </urlset>
    """
    assert parse_alkafi_sitemap_paths(xml) == [
        "/hadith/1/2/10/2",
        "/hadith/2/1/3/4",
    ]


def test_parse_sitemap_paths_supports_faqih_remote_book_ids():
    xml = """<urlset>
      <url><loc>https://thaqalayn.net/hadith/34/1/2/3</loc></url>
      <url><loc>https://thaqalayn.net/hadith/37/1/4/5</loc></url>
      <url><loc>https://thaqalayn.net/hadith/1/1/2/3</loc></url>
    </urlset>"""
    assert parse_sitemap_paths(
        xml, website_book_ids=FAQIH_CORPUS.website_book_ids
    ) == ["/hadith/34/1/2/3", "/hadith/37/1/4/5"]


def test_parse_chapter_page_reads_rendered_arabic_and_english():
    html = """
    <main>
      <article>
        <a href="/hadith/1/2/1/1">Hadith 1</a>
        <p dir="rtl" lang="ar">١ـ عَنْ أَبِي عَبْدِ الله</p>
        <p>From Abu Abdillah.</p>
      </article>
      <article>
        <a href="/hadith/1/2/1/2">Hadith 2</a>
        <p dir="rtl" lang="ar">٢ـ قَالَ</p>
      </article>
    </main>
    """
    rows = parse_chapter_page(html, chapter_path="/chapter/1/2/1")
    assert [row.path for row in rows] == [
        "/hadith/1/2/1/1",
        "/hadith/1/2/1/2",
    ]
    assert rows[0].arabic_text == "١ـ عَنْ أَبِي عَبْدِ الله"
    assert rows[0].english_text == "From Abu Abdillah."
    assert rows[1].english_text == ""


def test_parse_chapter_page_synthesizes_path_for_heading_only_articles():
    html = """
    <article>
      <h3>Ḥadīth 6</h3>
      <p dir="rtl" lang="ar">٦ـ قَالَ</p>
      <p>He said.</p>
    </article>
    """
    rows = parse_chapter_page(html, chapter_path="/chapter/1/1/0")
    assert [row.path for row in rows] == ["/hadith/1/1/0/6"]
    assert rows[0].arabic_text == "٦ـ قَالَ"
    assert rows[0].english_text == "He said."


def test_parse_chapter_page_records_previous_chapter_placeholder():
    html = """
    <article>
      <a href="/hadith/1/4/87/0">Hadith 0</a>
      <p>Part of Previous Chapter</p>
    </article>
    <article>
      <a href="/hadith/1/4/87/1">Hadith 1</a>
      <p dir="rtl" lang="ar">١ـ قَالَ</p>
    </article>
    """
    non_reports = []
    rows = parse_chapter_page(
        html,
        chapter_path="/chapter/1/4/87",
        non_report_entries=non_reports,
    )
    assert [row.path for row in rows] == ["/hadith/1/4/87/1"]
    assert non_reports == [
        {
            "path": "/hadith/1/4/87/0",
            "classification": "non_report_placeholder",
            "label": "Hadith 0 Part of Previous Chapter",
        }
    ]


def test_parse_chapter_page_records_missing_and_combined_arabic_anomalies():
    html = """
    <article>
      <a href="/hadith/1/4/108/71">Hadith 71</a>
      <p>71ـ عَنْ أَبِي عَبْدِ الله 71. From Abu Abdillah.</p>
    </article>
    <article>
      <a href="/hadith/1/4/108/72">Hadith 72</a>
      <p>72. English only.</p>
    </article>
    """
    anomalies = []
    rows = parse_chapter_page(
        html,
        chapter_path="/chapter/1/4/108",
        anomalies=anomalies,
    )
    assert rows[0].arabic_text == "71ـ عَنْ أَبِي عَبْدِ الله"
    assert rows[0].english_text == "71. From Abu Abdillah."
    assert rows[1].arabic_text == ""
    assert [entry["classification"] for entry in anomalies] == [
        "combined_arabic_english_paragraph",
        "website_missing_arabic",
    ]


def test_parse_chapter_page_merges_split_arabic_and_english_articles():
    html = """
    <article>
      <a href="/hadith/34/1/19/177">Hadith 177</a>
      <p dir="rtl" lang="ar">Arabic report</p>
    </article>
    <article>
      <a href="/hadith/34/1/19/177">Hadith 177</a>
      <p>English report.</p>
    </article>
    """
    anomalies = []
    rows = parse_chapter_page(
        html,
        chapter_path="/chapter/34/1/19",
        volume=1,
        anomalies=anomalies,
    )
    assert len(rows) == 1
    assert rows[0].volume == 1
    assert rows[0].remote_book_id == 34
    assert rows[0].arabic_text == "Arabic report"
    assert rows[0].english_text == "English report."
    assert any(
        row["classification"] == "duplicate_website_articles_merged"
        for row in anomalies
    )


def test_audit_does_not_confirm_uncorroborated_printed_number(db: Session):
    matching_arabic = "\u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    unrelated_arabic = "\u0647\u0630\u0627 \u0646\u0635 \u0622\u062e\u0631 \u0644\u0627 \u064a\u0637\u0627\u0628\u0642 \u0627\u0644\u0631\u0648\u0627\u064a\u0629"
    hadith = _faqih_hadith(db, printed_number="1", text=matching_arabic)
    rows = [
        {
            "path": "/hadith/34/1/1/1",
            "chapter_path": "/chapter/34/1/1",
            "volume": 1,
            "remote_book_id": 34,
            "kitab_id": 1,
            "kitab_name_en": "Content",
            "chapter_id": 1,
            "chapter_name_en": "One",
            "number_in_chapter": 1,
            "arabic_text": unrelated_arabic,
            "english_text": "Hadith. 1 - Unrelated text.",
            "arabic_sha256": "wrong",
        },
        {
            "path": "/hadith/34/1/1/2",
            "chapter_path": "/chapter/34/1/1",
            "volume": 1,
            "remote_book_id": 34,
            "kitab_id": 1,
            "kitab_name_en": "Content",
            "chapter_id": 1,
            "chapter_name_en": "One",
            "number_in_chapter": 2,
            "arabic_text": matching_arabic,
            "english_text": "Hadith. 2 - Matching text.",
            "arabic_sha256": "right",
        },
    ]
    inventory = {
        "corpus_key": "faqih",
        "source_book_id": "11021",
        "chapter_count": 1,
        "hadith_sitemap": {"path_count": 2},
        "chapters": [{"rows": rows}],
        "non_report_entries": [],
        "anomalies": [],
    }

    audit = audit_thaqalayn_website(db, inventory=inventory)

    relation = audit["confirmed_relations"][0]
    assert relation["local_id"] == hadith.id
    assert relation["website_path"] == "/hadith/34/1/1/2"
    assert relation["method"] == "unique_exact_arabic"
    assert audit["summary"]["unaccounted_website"] == 1


def test_audit_inventory_match_does_not_imply_publication_quality(db: Session):
    report = "\u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    compiler_material = (
        " \u0648\u0647\u0630\u0627 \u0643\u0644\u0627\u0645 \u0637\u0648\u064a\u0644 \u0644\u0644\u0645\u0635\u0646\u0641 \u0644\u064a\u0633 \u0645\u0646 \u0646\u0635 \u0627\u0644\u0631\u0648\u0627\u064a\u0629" * 4
    )
    _faqih_hadith(db, printed_number="1", text=report + compiler_material)
    remote = {
        "path": "/hadith/34/1/1/1",
        "chapter_path": "/chapter/34/1/1",
        "volume": 1,
        "remote_book_id": 34,
        "kitab_id": 1,
        "kitab_name_en": "Content",
        "chapter_id": 1,
        "chapter_name_en": "One",
        "number_in_chapter": 1,
        "arabic_text": report,
        "english_text": "Hadith. 1 - Water is pure.",
        "arabic_sha256": "remote",
    }
    inventory = {
        "corpus_key": "faqih",
        "source_book_id": "11021",
        "chapter_count": 1,
        "hadith_sitemap": {"path_count": 1},
        "chapters": [{"rows": [remote]}],
        "non_report_entries": [],
        "anomalies": [],
    }

    audit = audit_thaqalayn_website(db, inventory=inventory)

    assert audit["summary"]["confirmed_local"] == 1
    assert audit["summary"]["publication_ready"] is False
    quality = audit["publication_quality"]
    assert quality["summary"]["mapped_records_below_90_percent"] == 1
    assert quality["summary"]["blocking_records"] == 1
    assert "website_arabic_covers_less_than_90_percent" in quality["issues"][0]["flags"]
    assert "Public release ready: **NO**" in render_audit_markdown(audit)


def test_boundary_repair_splits_two_website_reports_and_preserves_source(db: Session):
    first = "1 - \u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    second = "2 - \u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u062a\u0631\u0627\u0628 \u0637\u0627\u0647\u0631"
    source = f"{first} {second}"
    original = _faqih_hadith(db, printed_number="1", text=source)
    rows = [
        {
            "path": f"/hadith/34/1/2/{number}",
            "chapter_path": "/chapter/34/1/2",
            "volume": 1,
            "remote_book_id": 34,
            "kitab_id": 1,
            "kitab_name_en": "Content",
            "chapter_id": 2,
            "chapter_name_en": "Water",
            "number_in_chapter": number,
            "arabic_text": arabic,
            "english_text": f"Hadith. {number} - Translation {number}.",
            "arabic_sha256": f"remote-{number}",
        }
        for number, arabic in ((1, first), (2, second))
    ]
    inventory = {
        "corpus_key": "faqih",
        "source_book_id": "11021",
        "chapter_count": 1,
        "hadith_sitemap": {"path_count": 2},
        "chapters": [{"rows": rows}],
        "non_report_entries": [],
        "anomalies": [],
    }
    audit = audit_thaqalayn_website(db, inventory=inventory)
    assert {edge["relation"] for edge in audit["confirmed_relations"]} == {
        "website_splits_local"
    }

    stats = repair_website_arabic_boundaries(
        db,
        inventory=inventory,
        audit=audit,
        chapter_path="/chapter/34/1/2",
        dry_run=False,
    )
    db.flush()

    repaired = db.execute(select(Hadith).order_by(Hadith.sequence_in_book)).scalars().all()
    assert stats.boundaries_repaired == 1
    assert stats.split_records_created == 1
    assert [row.public_id for row in repaired] == ["faqih-1", "faqih-web-2"]
    assert repaired[0].full_text_raw == source
    assert repaired[0].matn_raw == "\u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    assert repaired[1].matn_raw == "\u0642\u0627\u0644 \u0627\u0644\u0635\u0627\u062f\u0642 \u0627\u0644\u062a\u0631\u0627\u0628 \u0637\u0627\u0647\u0631"
    assert original.full_text_raw == source


def test_boundary_repair_preserves_a_detectable_isnad(db: Session):
    arabic = (
        "1 - \u0631\u0648\u0649 \u0632\u0631\u0627\u0631\u0629 \u0639\u0646 \u0623\u0628\u064a \u0639\u0628\u062f \u0627\u0644\u0644\u0647 \u0639\u0644\u064a\u0647 \u0627\u0644\u0633\u0644\u0627\u0645 \u0642\u0627\u0644 "
        "\u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    )
    hadith = _faqih_hadith(db, printed_number="1", text=arabic)
    remote = {
        "path": "/hadith/34/1/1/1",
        "chapter_path": "/chapter/34/1/1",
        "volume": 1,
        "remote_book_id": 34,
        "kitab_id": 1,
        "kitab_name_en": "Content",
        "chapter_id": 1,
        "chapter_name_en": "Water",
        "number_in_chapter": 1,
        "arabic_text": arabic,
        "english_text": "Hadith. 1 - Water is pure.",
        "arabic_sha256": "remote-1",
    }
    inventory = {
        "corpus_key": "faqih",
        "source_book_id": "11021",
        "chapter_count": 1,
        "hadith_sitemap": {"path_count": 1},
        "chapters": [{"rows": [remote]}],
        "non_report_entries": [],
        "anomalies": [],
    }
    audit = audit_thaqalayn_website(db, inventory=inventory)

    repair_website_arabic_boundaries(
        db, inventory=inventory, audit=audit, dry_run=False
    )
    db.flush()
    review = db.execute(
        select(HadithSplitReview).where(HadithSplitReview.hadith_id == hadith.id)
    ).scalar_one()

    assert hadith.isnad_raw is not None
    assert "\u0632\u0631\u0627\u0631\u0629" in hadith.isnad_raw
    assert hadith.matn_raw == "\u0627\u0644\u0645\u0627\u0621 \u0637\u0627\u0647\u0631"
    assert review.approved_isnad_raw == hadith.isnad_raw
    assert review.approved_matn_raw == hadith.matn_raw
