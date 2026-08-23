import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from eshia_research.db import Base, make_engine
from eshia_research.models import (
    Book,
    Narrator,
    Person,
    PersonEntryLink,
    PersonSurfaceForm,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.person_builder import build_person_layer
from eshia_research.rijal.shiaresearch import (
    ENTRY_KIND,
    SNAPSHOT_FORMAT,
    _extract_title,
    _subject_kind,
    _subject_normalised,
    crawl_external_rijal,
    import_external_rijal,
    link_external_rijal_entries,
    load_snapshot,
)


def test_title_and_heading_classification_survives_arabic_normalisation():
    person = "\u0641\u064a \u062d\u0631\u064a\u0632"
    jurists = "\u062a\u0633\u0645\u064a\u0629 \u0627\u0644\u0641\u0642\u0647\u0627\u0621"
    clan = "\u0628\u0646\u064a \u0631\u0628\u0627\u0637"
    pair = "\u0627\u0644\u0641\u0636\u0644 \u0648\u0625\u0628\u0631\u0627\u0647\u064a\u0645"

    assert _subject_normalised(person) == normalise_arabic_persian("\u062d\u0631\u064a\u0632")
    assert _subject_kind(person, set()) == "person"
    assert _subject_kind(jurists, set()) == "heading"
    assert _subject_kind(clan, set()) == "heading"
    assert _subject_kind(pair, set()) == "multi"
    assert _extract_title(f"Fihrist, no. 2 ({pair})")[0] == pair


def _snapshot() -> dict:
    return {
        "format": SNAPSHOT_FORMAT,
        "source": {
            "key": "shiaresearch-rijal-index-v1",
            "retrieved_at": "2026-08-23T00:00:00+00:00",
            "base_url": "https://shiaresearch.org",
            "content_mode": "metadata_or_full_text_when_exposed",
        },
        "works": [
            {
                "slug": "al-najashi",
                "title": "Rijāl al-Najāshī",
                "arabic_title": "رجال النجاشي",
                "group": "Rijāl",
                "opens_at": "rijal:al-najashi:0001",
                "expected_passages": 2,
                "entries": [
                    {
                        "ordinal": 1,
                        "uid": "rijal:al-najashi:0001",
                        "source_entry_number": 1,
                        "citation": "Rijāl al-Najāshī, no. 1 (زرارة بن أعين)",
                        "title_raw": "زرارة بن أعين",
                        "text_raw": None,
                        "grade": None,
                        "section": None,
                        "unit": None,
                        "parts": [],
                        "flags": ["metadata_only"],
                    },
                    {
                        "ordinal": 2,
                        "uid": "rijal:al-najashi:0002",
                        "source_entry_number": 2,
                        "citation": "Rijāl al-Najāshī, no. 2 (راو جديد)",
                        "title_raw": "راو جديد",
                        "text_raw": None,
                        "grade": None,
                        "section": None,
                        "unit": None,
                        "parts": [],
                        "flags": ["metadata_only"],
                    },
                ],
            }
        ],
    }


def test_crawl_paginates_validates_and_round_trips_gzip(tmp_path):
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/api/books":
            return httpx.Response(
                200,
                json={
                    "groups": [
                        {
                            "books": [
                                {
                                    "slug": "al-najashi",
                                    "title": "Rijāl al-Najāshī",
                                    "arabic": "رجال النجاشي",
                                    "group": "Rijāl",
                                    "opens_at": "rijal:al-najashi:0001",
                                    "passages": 2,
                                }
                            ]
                        }
                    ]
                },
            )
        after = request.url.params.get("after")
        if after is None:
            return httpx.Response(
                200,
                json={
                    "has_after": True,
                    "last_id": 10,
                    "passages": [
                        {
                            "uid": "rijal:al-najashi:0001",
                            "citation": "Rijāl al-Najāshī, no. 1 (زرارة بن أعين)",
                            "locked": True,
                        }
                    ],
                },
            )
        assert after == "10"
        return httpx.Response(
            200,
            json={
                "has_after": False,
                "last_id": 11,
                "passages": [
                    {
                        "uid": "rijal:al-najashi:0002",
                        "citation": "Rijāl al-Najāshī, no. 2 (راو جديد)",
                        "locked": True,
                    }
                ],
            },
        )

    output = tmp_path / "snapshot.json.gz"
    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://example.test"
    ) as client:
        stats = crawl_external_rijal(
            output,
            work_slugs=("al-najashi",),
            delay_seconds=0,
            client=client,
        )

    loaded = load_snapshot(output)
    assert stats.entries == 2
    assert stats.requests == 3
    assert len(calls) == 3
    assert loaded["works"][0]["entries"][0]["title_raw"] == "زرارة بن أعين"
    assert loaded["works"][0]["entries"][0]["flags"] == ["metadata_only"]


def test_import_links_exact_match_and_bootstraps_genuinely_missing_person():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db: Session = sessionmaker(bind=engine)()
    try:
        mujam = Book(
            source_book_id="14036",
            title_original="Muʿjam Rijāl al-Ḥadīth",
            title_normalised="mujam",
            source_url="urn:test:mujam",
        )
        narrator = Narrator(
            canonical_name_ar="زرارة بن أعين",
            canonical_name_norm=normalise_arabic_persian("زرارة بن أعين"),
        )
        db.add_all((mujam, narrator))
        db.flush()
        primary = RijalEntry(
            narrator_id=narrator.id,
            book_id=mujam.id,
            entry_kind="mujam_numbered_entry",
            entry_number=1,
            title_raw="زرارة بن أعين",
            title_normalised=normalise_arabic_persian("زرارة بن أعين"),
            canonical_name_raw="زرارة بن أعين",
            canonical_name_normalised=normalise_arabic_persian("زرارة بن أعين"),
            text_raw="زرارة بن أعين",
            text_normalised=normalise_arabic_persian("زرارة بن أعين"),
        )
        db.add(primary)
        db.flush()
        build_person_layer(db)

        stats = import_external_rijal(db, _snapshot())
        assert stats.created == 2
        assert stats.exact == 1
        assert stats.unmatched == 0
        assert stats.identities_created == 1
        assert db.scalar(select(func.count(Person.id))) == 16

        rows = list(
            db.execute(
                select(RijalEntry).where(RijalEntry.entry_kind == ENTRY_KIND)
            ).scalars()
        )
        exact = next(row for row in rows if row.title_raw == "زرارة بن أعين")
        missing = next(row for row in rows if row.title_raw == "راو جديد")
        assert exact.narrator_id == narrator.id
        assert exact.source_url is None
        assert exact.review_status == "metadata_only"
        assert missing.narrator_id is not None
        assert db.scalar(
            select(func.count(PersonEntryLink.id)).where(
                PersonEntryLink.entry_id == exact.id,
                PersonEntryLink.link_type == "external_exact_subject",
            )
        ) == 1
        assert db.scalar(
            select(func.count(PersonEntryLink.id)).where(
                PersonEntryLink.entry_id == missing.id,
                PersonEntryLink.link_type == "external_created_subject",
            )
        ) == 1

        rerun = import_external_rijal(db, _snapshot())
        assert rerun.created == 0
        assert rerun.updated == 2
        assert db.scalar(
            select(func.count(RijalEntry.id)).where(RijalEntry.entry_kind == ENTRY_KIND)
        ) == 2

        # Rebuilding derived persons must not mint a person for either external
        # witness, and it must regenerate the exact evidence link it deletes.
        rebuilt = build_person_layer(db)
        assert rebuilt["persons"] == 16
        assert rebuilt["external_exact_links"] == 1
        assert db.scalar(select(func.count(Person.id))) == 16
    finally:
        db.close()


def test_non_unique_exact_name_cannot_be_overridden_by_weaker_full_form():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db: Session = sessionmaker(bind=engine)()
    try:
        norm = normalise_arabic_persian("محمد بن أحمد")
        book = Book(
            source_book_id="ext-rijal-al-najashi",
            title_original="Rijāl al-Najāshī",
            title_normalised="rijal",
            source_url="urn:usul16:external-rijal:al-najashi",
        )
        first = Person(canonical_name_ar="محمد بن أحمد", canonical_name_norm=norm)
        second = Person(canonical_name_ar="محمد بن أحمد", canonical_name_norm=norm)
        db.add_all((book, first, second))
        db.flush()
        # Deliberately give only one duplicate the weaker full-form claim. The
        # two exact identities must still win as evidence of ambiguity.
        db.add(
            PersonSurfaceForm(
                person_id=first.id,
                form_raw="محمد بن أحمد",
                form_norm=norm,
                derivation="full",
                shared_count=1,
            )
        )
        entry = RijalEntry(
            book_id=book.id,
            entry_kind=ENTRY_KIND,
            entry_number=1,
            title_raw="محمد بن أحمد",
            title_normalised=norm,
            canonical_name_raw="محمد بن أحمد",
            canonical_name_normalised=norm,
            text_raw="citation",
            text_normalised="citation",
            flags="metadata_only",
        )
        db.add(entry)
        db.flush()

        stats = link_external_rijal_entries(db)

        assert stats.exact == 0
        assert stats.full_form == 0
        assert stats.ambiguous == 1
        assert stats.candidate_links == 2
        assert entry.narrator_id is None
    finally:
        db.close()


def test_fihrist_number_disambiguates_exact_homonyms():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db: Session = sessionmaker(bind=engine)()
    try:
        name = "\u0625\u0628\u0631\u0627\u0647\u064a\u0645 \u0628\u0646 \u0635\u0627\u0644\u062d \u0627\u0644\u0623\u0646\u0645\u0627\u0637\u064a"
        norm = normalise_arabic_persian(name)
        mujam = Book(
            source_book_id="14036",
            title_original="Mujam",
            title_normalised="mujam",
            source_url="urn:test:mujam",
        )
        fihrist = Book(
            source_book_id="ext-rijal-al-fihrist",
            title_original="Fihrist",
            title_normalised="fihrist",
            source_url="urn:usul16:external-rijal:al-fihrist",
        )
        db.add_all((mujam, fihrist))
        db.flush()
        first = Person(canonical_name_ar=name, canonical_name_norm=norm)
        second = Person(canonical_name_ar=name, canonical_name_norm=norm)
        db.add_all((first, second))
        db.flush()
        first_entry = RijalEntry(
            book_id=mujam.id,
            entry_kind="mujam_numbered_entry",
            entry_number=181,
            title_raw=name,
            title_normalised=norm,
            canonical_name_raw=name,
            canonical_name_normalised=norm,
            text_raw="\u0642\u0627\u0644 \u0627\u0644\u0634\u064a\u062e (3): " + name,
            text_normalised=norm,
        )
        second_entry = RijalEntry(
            book_id=mujam.id,
            entry_kind="mujam_numbered_entry",
            entry_number=182,
            title_raw=name,
            title_normalised=norm,
            canonical_name_raw=name,
            canonical_name_normalised=norm,
            text_raw="\u0642\u0627\u0644 \u0627\u0644\u0634\u064a\u062e (2): " + name,
            text_normalised=norm,
        )
        db.add_all((first_entry, second_entry))
        db.flush()
        first.primary_entry_id = first_entry.id
        second.primary_entry_id = second_entry.id
        external = RijalEntry(
            book_id=fihrist.id,
            entry_kind=ENTRY_KIND,
            entry_number=2,
            title_raw=name,
            title_normalised=norm,
            canonical_name_raw=name,
            canonical_name_normalised=norm,
            text_raw=f"Fihrist, no. 2 ({name})",
            text_normalised=norm,
            flags="metadata_only",
        )
        db.add(external)
        db.flush()

        stats = link_external_rijal_entries(db)

        assert stats.source_number == 1
        assert stats.ambiguous == 0
        links = list(
            db.execute(
                select(PersonEntryLink).where(PersonEntryLink.entry_id == external.id)
            ).scalars()
        )
        assert [(link.person_id, link.link_type, link.confidence) for link in links] == [
            (second.id, "external_source_number_subject", 98)
        ]
    finally:
        db.close()
