"""Backfill canonical narrators and Mu'jam rijal entries from crawled pages."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Narrator,
    NarratorAlias,
    Page,
    RijalEntry,
    RijalOccurrence,
    RijalStatement,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.mujam_parser import (
    MUJAM_ENTRY_KIND,
    MUJAM_PARSER_VERSION,
    MUJAM_SOURCE_BOOK_ID,
    MujamPage,
    ParsedMujamEntry,
    parse_mujam_entries,
)


@dataclass
class MujamIndexStats:
    pages: int = 0
    entries: int = 0
    narrators_created: int = 0
    narrators_updated: int = 0
    aliases: int = 0
    statements: int = 0
    occurrences: int = 0
    needs_review: int = 0
    headers_seen: int = 0
    headers_ignored: int = 0
    sequence_gaps: int = 0
    last_entry_number: int | None = None
    flag_counts: Counter = field(default_factory=Counter)


def _to_mujam_page(page: Page) -> MujamPage:
    return MujamPage(
        id=page.id,
        volume_number=page.volume_number or 0,
        page_number=page.page_number,
        text_raw=page.text_raw or "",
        source_url=page.source_url,
    )


def _entry_flags(flags: set[str]) -> str | None:
    return ",".join(sorted(flags)) or None


def _update_narrator(narrator: Narrator, parsed: ParsedMujamEntry) -> None:
    narrator.canonical_name_ar = parsed.canonical_name_raw
    narrator.canonical_name_norm = normalise_arabic_persian(parsed.canonical_name_raw)[:512]
    narrator.notes = f"Imported from Mu'jam Rijal al-Hadith entry {parsed.entry_number}."


def rebuild_mujam_index(
    db: Session,
    *,
    source_book_id: str = MUJAM_SOURCE_BOOK_ID,
    parser_version: str = MUJAM_PARSER_VERSION,
    commit: bool = True,
) -> MujamIndexStats:
    """Parse Mu'jam's numbered entries and upsert derived rijal rows.

    The crawled `pages.text_raw` rows remain the source of truth. Existing
    entries are updated in place so narrator IDs stay stable across rebuilds.
    Statements, aliases attached to Mu'jam entries, and occurrence notes are
    rebuilt because they are parser-derived evidence.
    """
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one_or_none()
    if book is None:
        raise ValueError(f"Book source_book_id={source_book_id!r} not found")

    pages = (
        db.query(Page)
        .filter(Page.book_id == book.id, Page.text_raw.isnot(None))
        .order_by(Page.volume_number, Page.page_number)
        .all()
    )
    parsed_entries, parse_stats = parse_mujam_entries([_to_mujam_page(page) for page in pages])

    stats = MujamIndexStats(
        pages=len(pages),
        headers_seen=parse_stats.headers_seen,
        headers_ignored=parse_stats.headers_ignored,
        sequence_gaps=parse_stats.sequence_gaps,
        last_entry_number=parse_stats.last_entry_number,
    )

    existing_entries = (
        db.query(RijalEntry)
        .filter(RijalEntry.book_id == book.id, RijalEntry.entry_kind == MUJAM_ENTRY_KIND)
        .all()
    )
    existing_by_number = {entry.entry_number: entry for entry in existing_entries}
    existing_ids = [entry.id for entry in existing_entries if entry.id is not None]
    if existing_ids:
        db.execute(delete(RijalOccurrence).where(RijalOccurrence.entry_id.in_(existing_ids)))
        db.execute(delete(RijalStatement).where(RijalStatement.entry_id.in_(existing_ids)))
        db.execute(delete(NarratorAlias).where(NarratorAlias.source_entry_id.in_(existing_ids)))
        db.flush()

    parsed_numbers = {entry.entry_number for entry in parsed_entries}
    stale_entries = [entry for entry in existing_entries if entry.entry_number not in parsed_numbers]
    stale_ids = [entry.id for entry in stale_entries if entry.id is not None]
    if stale_ids:
        db.execute(delete(RijalEntry).where(RijalEntry.id.in_(stale_ids)))
        db.flush()

    for parsed in parsed_entries:
        entry = existing_by_number.get(parsed.entry_number)
        narrator: Narrator | None = None
        if entry is not None and entry.narrator_id is not None:
            narrator = db.get(Narrator, entry.narrator_id)

        if narrator is None:
            narrator = Narrator(
                canonical_name_ar=parsed.canonical_name_raw,
                canonical_name_norm=normalise_arabic_persian(parsed.canonical_name_raw)[:512],
                notes=f"Imported from Mu'jam Rijal al-Hadith entry {parsed.entry_number}.",
            )
            db.add(narrator)
            db.flush()
            stats.narrators_created += 1
        else:
            _update_narrator(narrator, parsed)
            stats.narrators_updated += 1

        if entry is None:
            entry = RijalEntry(
                book_id=book.id,
                entry_kind=MUJAM_ENTRY_KIND,
                entry_number=parsed.entry_number,
                narrator_id=narrator.id,
                title_raw=parsed.title_raw,
                title_normalised=normalise_arabic_persian(parsed.title_raw)[:512],
                canonical_name_raw=parsed.canonical_name_raw,
                canonical_name_normalised=normalise_arabic_persian(parsed.canonical_name_raw)[:512],
                text_raw=parsed.text_raw,
                text_normalised=normalise_arabic_persian(parsed.text_raw),
                parser_version=parser_version,
                review_status=parsed.review_status,
            )
            db.add(entry)
            db.flush()
        else:
            entry.narrator_id = narrator.id
            entry.title_raw = parsed.title_raw
            entry.title_normalised = normalise_arabic_persian(parsed.title_raw)[:512]
            entry.canonical_name_raw = parsed.canonical_name_raw
            entry.canonical_name_normalised = normalise_arabic_persian(parsed.canonical_name_raw)[:512]
            entry.text_raw = parsed.text_raw
            entry.text_normalised = normalise_arabic_persian(parsed.text_raw)
            entry.parser_version = parser_version
            entry.review_status = parsed.review_status

        entry.page_start_id = parsed.page_start_id
        entry.page_end_id = parsed.page_end_id
        entry.volume_start = parsed.volume_start
        entry.page_start = parsed.page_start
        entry.volume_end = parsed.volume_end
        entry.page_end = parsed.page_end
        entry.source_url = parsed.source_url
        entry.flags = _entry_flags(parsed.flags)

        stats.needs_review += int(parsed.review_status == "needs_review")
        stats.flag_counts.update(parsed.flags)

        for alias in parsed.aliases:
            db.add(
                NarratorAlias(
                    narrator_id=narrator.id,
                    source_entry_id=entry.id,
                    alias_raw=alias.alias_raw,
                    alias_normalised=normalise_arabic_persian(alias.alias_raw)[:512],
                    alias_type=alias.alias_type,
                    source_note=alias.source_note,
                    confidence=alias.confidence,
                )
            )
            stats.aliases += 1

        for statement in parsed.statements:
            db.add(
                RijalStatement(
                    entry_id=entry.id,
                    narrator_id=narrator.id,
                    source_name=statement.source_name,
                    statement_type=statement.statement_type,
                    quote_raw=statement.quote_raw,
                    quote_normalised=normalise_arabic_persian(statement.quote_raw),
                    evidence_text_raw=statement.evidence_text_raw,
                    metadata_json=statement.metadata,
                    confidence=statement.confidence,
                )
            )
            stats.statements += 1

        for occurrence in parsed.occurrences:
            db.add(
                RijalOccurrence(
                    entry_id=entry.id,
                    narrator_id=narrator.id,
                    direction=occurrence.direction,
                    related_name_raw=occurrence.related_name_raw,
                    related_name_normalised=normalise_arabic_persian(occurrence.related_name_raw)[:512],
                    source_ref_raw=occurrence.source_ref_raw,
                    evidence_text_raw=occurrence.evidence_text_raw,
                    metadata_json=occurrence.metadata,
                    confidence=occurrence.confidence,
                )
            )
            stats.occurrences += 1

        if commit and stats.entries % 500 == 0 and stats.entries:
            db.commit()

        stats.entries += 1

    if commit:
        db.commit()
    return stats


def count_mujam_entries(db: Session, *, source_book_id: str = MUJAM_SOURCE_BOOK_ID) -> int:
    book_id = select(Book.id).where(Book.source_book_id == source_book_id).scalar_subquery()
    return (
        db.query(RijalEntry)
        .filter(RijalEntry.book_id == book_id, RijalEntry.entry_kind == MUJAM_ENTRY_KIND)
        .count()
    )
