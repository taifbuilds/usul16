from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationSegment,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.thaqalayn_importer import (
    STATIC_PROVIDER,
    ThaqalaynRecord,
    build_matches,
    import_thaqalayn_al_kafi,
    parse_record,
    parse_static_row,
    match_score_parts,
    match_words,
    static_records_from_rows,
    strip_html_text,
)


def test_parse_record_repairs_legacy_api_volume_url():
    record = parse_record(
        {
            "id": 437,
            "bookId": "Al-Kafi-Volume-7-Kulayni",
            "volume": 7,
            "arabicText": "قال أبو عبد الله عليه السلام",
            "englishText": "Abu Abd Allah has said the following.",
            "thaqalaynSanad": "",
            "thaqalaynMatn": "Abu Abd Allah has said the following.",
            "URL": "https://thaqalayn.net/hadith/1/2/36/10",
            "translator": "Muhammad Sarwar",
        }
    )

    assert record.url == "https://thaqalayn.net/hadith/7/2/36/10"
    assert record.model == "muhammad-sarwar"


def test_parse_record_never_invents_missing_translator_attribution():
    record = parse_record(
        {
            "id": 1,
            "bookId": "Al-Kafi-Volume-1-Kulayni",
            "volume": 1,
            "arabicText": "قال أبو عبد الله عليه السلام",
            "englishText": "Abu Abd Allah has said the following.",
            "thaqalaynMatn": "Abu Abd Allah has said the following.",
            "URL": "https://thaqalayn.net/hadith/1/1/0/1",
        }
    )

    assert record.translator is None
    assert record.model == "unknown-translator"


def test_matcher_rejects_degenerate_one_word_containment():
    remote = thaqalayn_record(
        1,
        arabic_text="لا .",
        english_text="An unrelated long translation.",
        matn="An unrelated long translation.",
        url="https://thaqalayn.net/hadith/1/1/1/1",
    )
    local = "قال أبو عبد الله عليه السلام لا يجوز ذلك في هذا الأمر"

    score = match_score_parts(
        local_full=local,
        local_matn=local,
        local_full_words=match_words(local),
        local_matn_words=match_words(local),
        remote=remote,
    )

    assert score < 0.88


def make_db() -> Session:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def add_book(db: Session) -> Book:
    book = Book(
        source_book_id="11005",
        title_original="al-kafi",
        title_normalised="al-kafi",
        source_url="https://lib.eshia.ir/11005",
    )
    db.add(book)
    db.flush()
    return book


def add_hadith(
    db: Session,
    book: Book,
    *,
    matn: str,
    isnad: str,
    public_id: str = "alkafi-1",
    sequence: int = 1,
) -> Hadith:
    hadith = Hadith(
        public_id=public_id,
        book_id=book.id,
        sequence_in_book=sequence,
        sequence_in_page=sequence,
        printed_number=str(sequence),
        volume_start=1,
        volume_end=1,
        page_start=1,
        page_end=1,
        full_text_raw=f"{isnad} {matn}",
        full_text_normalised=normalise_arabic_persian(f"{isnad} {matn}"),
        isnad_raw=isnad,
        isnad_normalised=normalise_arabic_persian(isnad),
        matn_raw=matn,
        matn_normalised=normalise_arabic_persian(matn),
        source_url="https://lib.eshia.ir/11005/1/1",
        review_status="pending",
    )
    db.add(hadith)
    db.flush()
    return hadith


def test_thaqalayn_importer_matches_by_arabic_text_not_offset():
    db = make_db()
    try:
        book = add_book(db)
        add_hadith(
            db,
            book,
            matn="لما خلق الله العقل استنطقه ثم قال له اقبل فاقبل.",
            isnad="اخبرنا ابو جعفر محمد بن يعقوب عن محمد بن يحيى",
        )
        remote = {
            1: [
                thaqalayn_record(
                    1,
                    arabic_text="مقدمة لا تطابق الخبر",
                    english_text="Introduction.",
                    matn=None,
                    url="https://thaqalayn.net/hadith/1/0/1/1",
                ),
                thaqalayn_record(
                    2,
                    arabic_text="1- اخبرنا ابو جعفر محمد بن يعقوب عن محمد بن يحيى قال لما خلق الله العقل استنطقه ثم قال له اقبل فاقبل.",
                    english_text="When Allah created the intellect, He made it speak.",
                    matn="When Allah created the intellect, He made it speak.",
                    url="https://thaqalayn.net/hadith/1/1/0/1",
                ),
            ]
        }

        matches, stats = build_matches(db, source_book_id="11005", remote_by_volume=remote)

        assert stats.matched == 1
        assert matches[0].public_id == "alkafi-1"
        assert matches[0].thaqalayn_id == 2
        assert matches[0].score >= 0.88
    finally:
        db.close()


def test_thaqalayn_importer_writes_green_translation_and_skips_existing():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قال ابو عبد الله عليه السلام العلم نور.",
            isnad="محمد بن يعقوب عن علي بن ابراهيم",
        )
        remote = {
            1: [
                thaqalayn_record(
                    2,
                    arabic_text="1- محمد بن يعقوب عن علي بن ابراهيم قال ابو عبد الله عليه السلام العلم نور.",
                    english_text="Abu Abd Allah has said: Knowledge is light.",
                    matn="Abu Abd Allah has said: Knowledge is light.",
                    url="https://thaqalayn.net/hadith/1/1/0/1",
                )
            ]
        }

        stats = import_thaqalayn_al_kafi(db, remote_by_volume=remote, dry_run=False)
        db.commit()

        assert stats.imported == 1
        translation = db.query(HadithTranslation).filter_by(hadith_id=hadith.id).one()
        assert translation.status == "published"
        assert translation.risk_level == "green"
        assert translation.provider == "thaqalayn-api"
        assert translation.model == "muhammad-sarwar"
        assert translation.provenance_json["thaqalayn_id"] == 2
        assert translation.provenance_json["translator"] == "Muhammad Sarwar"
        assert translation.provenance_json["source_english_sha256"]
        assert (
            translation.provenance_json["translation_classification"]
            == "external_source_normalized"
        )

        second = import_thaqalayn_al_kafi(db, remote_by_volume=remote, dry_run=False)
        db.commit()

        assert second.imported == 0
        assert second.skipped_existing == 1
    finally:
        db.close()


def test_source_import_blocks_number_mismatch_pending_bounded_source_review():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قال أبو عبد الله لا يستطيع أن يوفر النفقة [1]",
            isnad="محمد بن يعقوب عن علي بن إبراهيم",
        )
        remote = {
            1: [
                thaqalayn_record(
                    2,
                    arabic_text=hadith.full_text_raw,
                    english_text="He cannot provide the maintenance.",
                    matn="He cannot provide the maintenance.",
                    url="https://thaqalayn.net/hadith/1/1/0/1",
                )
            ]
        }

        matches, _ = build_matches(
            db, source_book_id="11005", remote_by_volume=remote
        )
        stats = import_thaqalayn_al_kafi(
            db, remote_by_volume=remote, dry_run=False
        )

        assert len(matches) == 1
        assert matches[0].publishable is False
        assert {flag["code"] for flag in matches[0].publication_flags} == {
            "number_mismatch",
            "external_source_footnote_marker_difference",
            "external_source_literal_phrase",
        }
        assert next(
            flag
            for flag in matches[0].publication_flags
            if flag["code"] == "number_mismatch"
        )["severity"] == "critical"
        assert stats.imported == 0
        assert stats.skipped_qa == 1
        assert db.query(HadithTranslation).count() == 0
    finally:
        db.close()


def test_source_import_normalizes_source_literal_false_positives():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قال أبو عبد الله لا يستطيع أن يوفر النفقة [1]",
            isnad="محمد بن يعقوب عن علي بن إبراهيم",
        )
        remote = {
            1: [
                thaqalayn_record(
                    2,
                    arabic_text=hadith.full_text_raw,
                    # Preserve the number but deliberately omit bracketed
                    # source apparatus; "cannot provide" is narrative text.
                    english_text="He cannot provide the maintenance, 1.",
                    matn="He cannot provide the maintenance, 1.",
                    url="https://thaqalayn.net/hadith/1/1/0/1",
                )
            ]
        }

        stats = import_thaqalayn_al_kafi(
            db, remote_by_volume=remote, dry_run=False
        )
        db.commit()

        assert stats.imported == 1
        translation = db.query(HadithTranslation).filter_by(hadith_id=hadith.id).one()
        assert translation.risk_level == "green"
        assert {flag["code"] for flag in translation.risk_flags} == {
            "external_source_footnote_marker_difference",
            "external_source_literal_phrase",
        }
        assert {flag["severity"] for flag in translation.risk_flags} == {"info"}

        attempt = db.query(TranslationAttempt).one()
        assert {
            flag["code"] for flag in attempt.response_json["qa_flags"]
        } == {"missing_placeholder", "provider_refusal_text"}
    finally:
        db.close()


def test_thaqalayn_importer_prefers_best_match_not_first_adequate_match():
    db = make_db()
    try:
        book = add_book(db)
        add_hadith(
            db,
            book,
            matn="قال أبو عبد الله العلم نور يهدي المؤمن إلى الحق",
            isnad="محمد بن يعقوب عن علي بن إبراهيم",
        )
        remote = {
            1: [
                thaqalayn_record(
                    1,
                    arabic_text="قال أبو عبد الله العلم نور يهدي المؤمن إلى الطريق",
                    english_text="An adequate but inexact candidate.",
                    matn="An adequate but inexact candidate.",
                    url="https://thaqalayn.net/hadith/1/1/0/1",
                ),
                thaqalayn_record(
                    2,
                    arabic_text="محمد بن يعقوب عن علي بن إبراهيم قال أبو عبد الله العلم نور يهدي المؤمن إلى الحق",
                    english_text="The exact candidate.",
                    matn="The exact candidate.",
                    url="https://thaqalayn.net/hadith/1/1/0/2",
                ),
            ]
        }

        matches, _ = build_matches(db, source_book_id="11005", remote_by_volume=remote)

        assert len(matches) == 1
        assert matches[0].thaqalayn_id == 2
        assert matches[0].score == 1.0
    finally:
        db.close()


def test_thaqalayn_importer_blocks_unknown_translator():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قال أبو عبد الله عليه السلام العلم نور يهدي المؤمن إلى الحق",
            isnad="محمد بن يعقوب عن علي بن إبراهيم",
        )
        unknown = parse_record(
            {
                "id": 2,
                "bookId": "Al-Kafi-Volume-1-Kulayni",
                "volume": 1,
                "arabicText": hadith.full_text_raw,
                "englishText": "Knowledge is light.",
                "thaqalaynMatn": "Knowledge is light.",
                "URL": "https://thaqalayn.net/hadith/1/1/0/1",
            }
        )

        stats = import_thaqalayn_al_kafi(
            db, remote_by_volume={1: [unknown]}, dry_run=False
        )

        assert stats.imported == 0
        assert stats.skipped_qa == 1
        assert db.query(HadithTranslation).count() == 0
    finally:
        db.close()


def test_thaqalayn_importer_recovers_small_cross_edition_reordering():
    db = make_db()
    try:
        book = add_book(db)
        isnad = "محمد بن يعقوب عن علي بن إبراهيم"
        add_hadith(
            db,
            book,
            public_id="alkafi-1",
            sequence=1,
            matn="قال الإمام الصدق نور القلب وطريق النجاة",
            isnad=isnad,
        )
        add_hadith(
            db,
            book,
            public_id="alkafi-2",
            sequence=2,
            matn="قال الإمام العلم حياة القلوب ومفتاح الرحمة",
            isnad=isnad,
        )
        remote = {
            1: [
                thaqalayn_record(
                    10,
                    arabic_text=f"{isnad} قال الإمام العلم حياة القلوب ومفتاح الرحمة",
                    english_text="Knowledge is the life of hearts.",
                    matn="Knowledge is the life of hearts.",
                    url="https://thaqalayn.net/hadith/1/1/0/10",
                ),
                thaqalayn_record(
                    11,
                    arabic_text=f"{isnad} قال الإمام الصدق نور القلب وطريق النجاة",
                    english_text="Truthfulness is the light of the heart.",
                    matn="Truthfulness is the light of the heart.",
                    url="https://thaqalayn.net/hadith/1/1/0/11",
                ),
            ]
        }

        matches, _ = build_matches(db, source_book_id="11005", remote_by_volume=remote)

        assert [(match.public_id, match.thaqalayn_id) for match in matches] == [
            ("alkafi-1", 11),
            ("alkafi-2", 10),
        ]
    finally:
        db.close()


def test_static_parser_prefers_sarwar_and_strips_html():
    row = {
        "volume": 7,
        "index": 13055,
        "path": "/books/al-kafi:7:1:1:1",
        "arabic_text": [" قَالَ أَبُو عَبْدِ اللَّهِ ( عليه السلام ) الْعِلْمُ نُورٌ ."],
        "en_sarwar": [
            'Abu Abd Allah (a.s.) has said, "Knowledge is light." '
            '<a href="/books/quran:1#h1">[1:1]</a>'
        ],
        "en_hubeali": "Abu Abdullah<sup>asws</sup> said: Knowledge is light.",
        "source_url": "https://thaqalayn.net/books/al-kafi:7:1:1:1",
    }

    record = parse_static_row(row)

    assert record is not None
    assert record.provider == STATIC_PROVIDER
    assert record.model == "muhammad-sarwar"
    assert record.translator == "Muhammad Sarwar"
    assert "<a" not in record.english_text
    assert "[1:1]" in record.english_text


def test_static_parser_uses_hubeali_when_sarwar_is_missing():
    row = {
        "volume": 7,
        "index": 14000,
        "path": "/books/al-kafi:7:4:1:1",
        "arabic_text": "قَالَ أَبُو عَبْدِ اللَّهِ ( عليه السلام ) الْعِلْمُ نُورٌ .",
        "en_sarwar": "",
        "en_hubeali": "Abu Abdullah<sup>asws</sup> said: Knowledge is light.",
        "source_url": "https://thaqalayn.net/books/al-kafi:7:4:1:1",
    }

    record = parse_static_row(row)

    assert record is not None
    assert record.model == "hubeali"
    assert record.translator == "HubeAli"
    assert record.english_text == "Abu Abdullah asws said: Knowledge is light."


def test_static_import_writes_per_translator_provenance():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قَالَ أَبُو عَبْدِ اللَّهِ عليه السلام الْعِلْمُ نُورٌ يَهْدِي إِلَى الْحَقِّ",
            isnad="مُحَمَّدُ بْنُ يَعْقُوبَ عَنْ عَلِيِّ بْنِ إِبْرَاهِيمَ",
        )
        remote = static_records_from_rows(
            [
                {
                    "volume": 1,
                    "index": 1,
                    "path": "/books/al-kafi:1:1:1:1",
                    "arabic_text": (
                        "قَالَ أَبُو عَبْدِ اللَّهِ عليه السلام "
                        "الْعِلْمُ نُورٌ يَهْدِي إِلَى الْحَقِّ"
                    ),
                    "en_hubeali": "Abu Abdullah asws said: Knowledge is light guiding to the truth.",
                    "source_url": "https://thaqalayn.net/books/al-kafi:1:1:1:1",
                }
            ]
        )

        stats = import_thaqalayn_al_kafi(db, remote_by_volume=remote, dry_run=False)
        db.commit()

        assert stats.imported == 1
        translation = db.query(HadithTranslation).filter_by(hadith_id=hadith.id).one()
        assert translation.provider == STATIC_PROVIDER
        assert translation.model == "hubeali"
        assert translation.provenance_json["translator"] == "HubeAli"
        assert translation.provenance_json["source"] == "thaqalayn-data"
        assert translation.provenance_json["source_english_sha256"]
        segment = db.query(TranslationSegment).filter_by(hadith_id=hadith.id).one()
        assert segment.metadata_json["source"] == "thaqalayn-data"
    finally:
        db.close()


def test_import_can_replace_only_selected_existing_provider():
    db = make_db()
    try:
        book = add_book(db)
        hadith = add_hadith(
            db,
            book,
            matn="قَالَ أَبُو عَبْدِ اللَّهِ عليه السلام الْعِلْمُ نُورٌ يَهْدِي إِلَى الْحَقِّ",
            isnad="مُحَمَّدُ بْنُ يَعْقُوبَ عَنْ عَلِيِّ بْنِ إِبْرَاهِيمَ",
        )
        db.add(
            HadithTranslation(
                hadith_id=hadith.id,
                language="en",
                translation_version="matn_en_v1",
                source_full_sha256="old",
                source_matn_sha256="old",
                matn_translation="Existing model text.",
                status="machine_verified",
                risk_level="green",
                provider="codex-direct",
                model="gpt-5-codex-direct",
            )
        )
        db.flush()
        remote = static_records_from_rows(
            [
                {
                    "volume": 1,
                    "index": 1,
                    "path": "/books/al-kafi:1:1:1:1",
                    "arabic_text": hadith.matn_raw,
                    "en_sarwar": "Abu Abd Allah has said: Knowledge is light guiding to the truth.",
                    "source_url": "https://thaqalayn.net/books/al-kafi:1:1:1:1",
                }
            ]
        )

        skipped = import_thaqalayn_al_kafi(db, remote_by_volume=remote, dry_run=False)
        assert skipped.imported == 0
        assert skipped.skipped_existing == 1

        replaced = import_thaqalayn_al_kafi(
            db,
            remote_by_volume=remote,
            dry_run=False,
            replace_providers={"codex-direct"},
        )

        assert replaced.imported == 1
        translation = db.query(HadithTranslation).filter_by(hadith_id=hadith.id).one()
        assert translation.provider == STATIC_PROVIDER
        assert translation.provenance_json["translator"] == "Muhammad Sarwar"
    finally:
        db.close()


def test_strip_html_text_keeps_superscript_marker_readable():
    assert strip_html_text("Abu Abdullah<sup>asws</sup> said") == "Abu Abdullah asws said"


def thaqalayn_record(
    record_id: int,
    *,
    arabic_text: str,
    english_text: str,
    matn: str | None,
    url: str,
) -> ThaqalaynRecord:
    return ThaqalaynRecord(
        id=record_id,
        book_id="Al-Kafi-Volume-1-Kulayni",
        volume=1,
        arabic_text=arabic_text,
        english_text=english_text,
        thaqalayn_sanad="Muhammad b. Ya'qub has narrated:",
        thaqalayn_matn=matn,
        url=url,
        translator="Muhammad Sarwar",
        category="Knowledge",
        chapter="Knowledge",
        raw={},
    )
