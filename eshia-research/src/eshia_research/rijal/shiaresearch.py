"""Offline import of external rijal catalogue witnesses.

The remote service is used only by the explicit crawl command.  The web/API
runtime reads local rows and never contacts, redirects to, or embeds links to
the source service. Source-specific entries remain evidence documents. When a
genuinely missing, single-person identity has no local match, the linker may
bootstrap a local ``Narrator``/``Person`` while keeping its external origin
explicit and rebuildable.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import re
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Narrator,
    NarratorAlias,
    Person,
    PersonEntryLink,
    PersonRelation,
    PersonSurfaceForm,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.name_grammar import parse_name, surface_forms


SOURCE_BASE_URL = "https://shiaresearch.org"
SOURCE_KEY = "shiaresearch-rijal-index-v1"
SNAPSHOT_FORMAT = "usul16.external-rijal.v1"
ENTRY_KIND = "external_rijal_index_entry"
PARSER_VERSION = "external_rijal_v1"
SOURCE_BOOK_PREFIX = "ext-rijal-"
DEFAULT_WORK_SLUGS = (
    "al-najashi",
    "al-kashshi",
    "al-tusi",
    "al-fihrist",
    "al-hilli",
)
EXTERNAL_LINK_TYPES = (
    "external_exact_subject",
    "external_full_form_subject",
    "external_name_variant_subject",
    "external_alias_subject",
    "external_equivalent_subject",
    "external_source_number_subject",
    "external_text_witness_subject",
    "external_fuzzy_subject",
    "external_created_subject",
    "external_multi_subject",
    "external_subject_candidate",
)

ProgressCallback = Callable[[str, int, int], None]
_CITATION_TITLE_RE = re.compile(r"\bno\.\s*\d+\s*\((.*)\)\s*$", re.IGNORECASE | re.DOTALL)
_CITATION_NUMBER_RE = re.compile(r"\bno\.\s*(\d+)", re.IGNORECASE)
_UID_NUMBER_RE = re.compile(r"(\d+)$")
_FOOTNOTE_MARKER_RE = re.compile(r"\[\s*\d+\s*\]")
_DISCUSSION_PREFIX_RE = re.compile(
    r"^\s*(?:ما\s+رو[يی]\s+)?ف[يی]\s+", re.IGNORECASE
)
_BRACKET_RE = re.compile(r"[\[\]()]|‌")
_TRAILING_CONTEXT_RE = re.compile(
    r"\s+(?:رض[يی]\s+الله\s+عنه|رحمه\s+الله|عل[يی]ه(?:ما|م)?\s+السلام"
    r"|صلوات\s+الله\s+عل[يی]ه(?:ما|م)?|قدس\s+سره|من\s+اصحاب\b"
    r"|و\s+(?:كان|هو|ذكر|سبب|دعوة|احتجاج|كم)\b).*$",
    re.IGNORECASE,
)
_NON_PERSON_MARKERS = tuple(normalise_arabic_persian(value) for value in (
    "معرفة قدر الرواة",
    "تسمية الفقهاء",
    "الزهاد الثمانية",
    "السبعين رجلا",
    "ما روي فيه من الذم",
    "الفطحية",
    "الزيدية",
    "الاشاعثة",
    "العبسيان",
    "اصل",
))
_NON_PERSON_PREFIXES = tuple(
    normalise_arabic_persian(value)
    for value in ("بنو ", "بني ", "اصحاب ", "تسمية ")
)
_EXTERNAL_NARRATOR_NOTE_PREFIX = "external_rijal_identity_v2:"
_FULL_TEXT_KEYS = ("text_raw", "text", "content", "arabic", "body", "excerpt")
_RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class CrawlStats:
    works: int = 0
    entries: int = 0
    requests: int = 0
    resumed_works: int = 0


@dataclass
class LinkStats:
    exact: int = 0
    full_form: int = 0
    name_variant: int = 0
    alias: int = 0
    equivalent: int = 0
    source_number: int = 0
    text_witness: int = 0
    fuzzy: int = 0
    created: int = 0
    created_entries: int = 0
    headings: int = 0
    multi_subject: int = 0
    ambiguous: int = 0
    unmatched: int = 0
    candidate_links: int = 0
    manual: int = 0


@dataclass
class ImportStats:
    works: int = 0
    created: int = 0
    updated: int = 0
    metadata_only: int = 0
    full_text: int = 0
    exact: int = 0
    full_form: int = 0
    name_variant: int = 0
    alias: int = 0
    equivalent: int = 0
    source_number: int = 0
    text_witness: int = 0
    fuzzy: int = 0
    identities_created: int = 0
    external_identity_entries: int = 0
    headings: int = 0
    multi_subject: int = 0
    ambiguous: int = 0
    unmatched: int = 0
    candidate_links: int = 0


@dataclass
class AuditStats:
    entries: int
    metadata_only: int
    exact: int
    full_form: int
    name_variant: int
    alias: int
    equivalent: int
    source_number: int
    text_witness: int
    fuzzy: int
    created: int
    headings: int
    multi_subject: int
    ambiguous: int
    unmatched: int
    per_source: dict[str, int]


def _utcnow_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def source_book_id(slug: str) -> str:
    return f"{SOURCE_BOOK_PREFIX}{slug}"


def _snapshot_bytes(snapshot: dict[str, Any]) -> bytes:
    return json.dumps(
        snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def snapshot_sha256(snapshot: dict[str, Any]) -> str:
    return hashlib.sha256(_snapshot_bytes(snapshot)).hexdigest()


def write_snapshot(snapshot: dict[str, Any], path: str | Path) -> Path:
    """Atomically write UTF-8 JSON, optionally gzip-compressed."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    if target.suffix == ".gz":
        with gzip.open(temporary, "wb", compresslevel=6) as handle:
            handle.write(payload)
    else:
        temporary.write_bytes(payload)
    temporary.replace(target)
    return target


def load_snapshot(
    path: str | Path, *, require_complete: bool = True
) -> dict[str, Any]:
    source = Path(path)
    if source.suffix == ".gz":
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            snapshot = json.load(handle)
    else:
        snapshot = json.loads(source.read_text(encoding="utf-8"))
    validate_snapshot(snapshot, require_complete=require_complete)
    return snapshot


def validate_snapshot(
    snapshot: dict[str, Any], *, require_complete: bool = True
) -> None:
    if snapshot.get("format") != SNAPSHOT_FORMAT:
        raise ValueError(f"Unsupported snapshot format: {snapshot.get('format')!r}")
    works = snapshot.get("works")
    if not isinstance(works, list):
        raise ValueError("Snapshot works must be a list")
    seen_slugs: set[str] = set()
    for work in works:
        slug = work.get("slug")
        entries = work.get("entries")
        if not slug or slug in seen_slugs or not isinstance(entries, list):
            raise ValueError(f"Invalid or duplicate snapshot work: {slug!r}")
        seen_slugs.add(slug)
        expected = work.get("expected_passages")
        complete = work.get("complete", True)
        if require_complete and not complete:
            raise ValueError(f"{slug}: snapshot work is incomplete")
        if expected is not None and complete and len(entries) != int(expected):
            raise ValueError(
                f"{slug}: snapshot has {len(entries)} entries, expected {expected}"
            )
        uids = [entry.get("uid") for entry in entries]
        if any(not uid for uid in uids) or len(set(uids)) != len(uids):
            raise ValueError(f"{slug}: missing or duplicate entry UID")


def _catalogue_works(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for group in payload.get("groups", []):
        for book in group.get("books", []):
            slug = book.get("slug")
            if slug:
                found[slug] = book
    return found


def _extract_title(citation: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    match = _CITATION_TITLE_RE.search(citation or "")
    if match:
        title = match.group(1).strip()
    else:
        title = (citation or "").strip()
        flags.append("missing_parenthesized_title")
    if title.startswith("[") and title.endswith("]"):
        flags.append("non_person_heading")
        title = title[1:-1].strip()
    if not title:
        title = "Untitled catalogue record"
        flags.extend(("missing_title", "non_person_heading"))
    if len(title) > 512:
        title = title[:512]
        flags.append("title_truncated")
    return title, flags


def _extract_full_text(passage: dict[str, Any]) -> str | None:
    for key in _FULL_TEXT_KEYS:
        value = passage.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _canonical_name(title: str) -> str:
    """Remove citation apparatus without changing the displayed source title."""

    name = _FOOTNOTE_MARKER_RE.sub("", title)
    name = _DISCUSSION_PREFIX_RE.sub("", name)
    name = _BRACKET_RE.sub("", name)
    return name.strip(" ،,;؛-")


def _subject_normalised(title: str) -> str:
    """Extract the single-subject portion used for identity matching."""

    subject = normalise_arabic_persian(_FOOTNOTE_MARKER_RE.sub("", title))
    subject = _BRACKET_RE.sub("", subject).strip(" ،,;؛-")
    subject = re.sub(r"^و(?=[\u0600-\u06ff])", "", subject).strip()
    subject = _DISCUSSION_PREFIX_RE.sub("", subject)
    # A few Kashshi runs prefix the actual heading with an Imam-era label.
    if subject.startswith("اصحاب ") and " فی " in subject:
        subject = subject.rsplit(" فی ", 1)[-1]
    subject = _TRAILING_CONTEXT_RE.sub("", subject)
    return subject.strip(" ،,;؛-")


def _identity_variants(title: str) -> list[tuple[str, str, int]]:
    """Strongest-to-weakest legal identity forms extracted from a heading."""

    subject = _subject_normalised(title)
    if not subject:
        return []
    variants: list[tuple[str, str, int]] = [(subject, "exact", 95)]
    parsed = parse_name(subject)
    generated = surface_forms(parsed)
    # Prefer the most specific generated forms. This turns headings such as
    # «هشام بن الحكم أبو محمد ...» into their actual nasab without jumping
    # immediately to a bare first name.
    priority = {"full": 0, "nasab_truncation": 1, "kunya": 2, "ibn_form": 3}
    for form in sorted(
        (form for form in generated if form.derivation in priority),
        key=lambda form: (priority[form.derivation], -len(form.form_norm)),
    ):
        if form.derivation == "nasab_truncation" and " بن " not in form.form_norm:
            continue
        confidence = {
            "full": 88,
            "nasab_truncation": 82,
            "kunya": 78,
            "ibn_form": 76,
        }[form.derivation]
        variants.append((form.form_norm, "name_variant", confidence))
    seen: set[str] = set()
    return [item for item in variants if not (item[0] in seen or seen.add(item[0]))]


def _subject_kind(title: str, flags: set[str]) -> str:
    """Return person, multi, or heading for an external catalogue title."""

    if "non_person_heading" in flags or "missing_title" in flags:
        return "heading"
    subject = _subject_normalised(title)
    if not subject or not re.search(r"[\u0600-\u06ff]", subject):
        return "heading"
    if any(marker in subject for marker in _NON_PERSON_MARKERS) or "الهتنا" in subject:
        return "heading"
    if subject.startswith(_NON_PERSON_PREFIXES):
        return "heading"
    if re.search(r"\sو\s*[؀-ۿ]", subject) or re.search(
        r"\b(?:اخوته|اخوتهما|ابن[يی]ه|ابناءه|بن[يی]ه|منهم)\b", subject
    ):
        return "multi"
    return "person"


def _source_number(uid: str, citation: str) -> int | None:
    uid_match = _UID_NUMBER_RE.search(uid)
    if uid_match:
        return int(uid_match.group(1))
    citation_match = re.search(r"\bno\.\s*(\d+)\b", citation, re.IGNORECASE)
    return int(citation_match.group(1)) if citation_match else None


def _snapshot_entry(passage: dict[str, Any], ordinal: int) -> dict[str, Any]:
    uid = str(passage.get("uid") or "")
    citation = str(passage.get("citation") or "")
    title, flags = _extract_title(citation)
    full_text = _extract_full_text(passage)
    if passage.get("locked") or full_text is None:
        flags.append("metadata_only")
    return {
        "ordinal": ordinal,
        "uid": uid,
        "source_entry_number": _source_number(uid, citation),
        "citation": citation,
        "title_raw": title,
        "text_raw": full_text,
        "grade": passage.get("grade") or None,
        "section": passage.get("section") or None,
        "unit": passage.get("unit") or None,
        "parts": passage.get("parts") or [],
        "flags": sorted(set(flags)),
    }


def _get_json(
    client: httpx.Client,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 10,
) -> tuple[dict[str, Any], int]:
    attempts = 0
    while True:
        attempts += 1
        try:
            response = client.get(path, params=params)
        except httpx.TransportError:
            if attempts > max_retries:
                raise
            time.sleep(min(2 ** (attempts - 1), 10))
            continue
        if response.status_code not in _RETRY_STATUSES:
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError(f"Expected an object from {path}")
            return payload, attempts
        if attempts > max_retries:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            delay = min(float(retry_after), 60)
        elif response.status_code == 429:
            # The long al-Khui index can cross a rolling source limit. A
            # meaningful cool-down is kinder and more effective than rapidly
            # spending the retry budget on guaranteed 429 responses.
            delay = min(attempts * 10, 60)
        else:
            delay = min(2 ** (attempts - 1), 10)
        time.sleep(delay)


def crawl_external_rijal(
    output_path: str | Path,
    *,
    work_slugs: Iterable[str] = DEFAULT_WORK_SLUGS,
    delay_seconds: float = 0.05,
    resume: bool = True,
    client: httpx.Client | None = None,
    on_progress: ProgressCallback | None = None,
) -> CrawlStats:
    """Create a complete, resumable local snapshot of selected rijal works."""

    target = Path(output_path)
    requested = tuple(dict.fromkeys(work_slugs))
    if not requested:
        raise ValueError("At least one work slug is required")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    if resume and target.exists():
        snapshot = load_snapshot(target, require_complete=False)
    else:
        snapshot = {
            "format": SNAPSHOT_FORMAT,
            "source": {
                "key": SOURCE_KEY,
                "retrieved_at": _utcnow_iso(),
                "base_url": SOURCE_BASE_URL,
                "content_mode": "metadata_or_full_text_when_exposed",
            },
            "works": [],
        }
    completed = {work["slug"]: work for work in snapshot["works"]}
    stats = CrawlStats()

    owns_client = client is None
    if client is None:
        client = httpx.Client(
            base_url=SOURCE_BASE_URL,
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "Usul16ResearchIndexer/1.0 (permission granted by site owner)"},
        )
    try:
        catalogue, requests_used = _get_json(client, "/api/books")
        stats.requests += requests_used
        catalogue_by_slug = _catalogue_works(catalogue)
        missing = [slug for slug in requested if slug not in catalogue_by_slug]
        if missing:
            raise ValueError(f"Works not found in source catalogue: {', '.join(missing)}")

        for work_index, slug in enumerate(requested, start=1):
            book = catalogue_by_slug[slug]
            expected = int(book.get("passages") or 0)
            existing = completed.get(slug)
            if (
                existing
                and existing.get("complete", True)
                and len(existing.get("entries", [])) == expected
            ):
                stats.resumed_works += 1
                stats.works += 1
                stats.entries += expected
                if on_progress:
                    on_progress(slug, expected, expected)
                continue

            opens_at = book.get("opens_at")
            if not opens_at:
                raise ValueError(f"{slug}: source catalogue has no opens_at UID")
            entries = list(existing.get("entries", [])) if existing else []
            seen_uids = {entry["uid"] for entry in entries}
            after_value = existing.get("after_cursor") if existing else None
            after: int | None = int(after_value) if after_value is not None else None
            pages_since_checkpoint = 0
            while True:
                params: dict[str, Any] = {"uid": opens_at}
                if after is not None:
                    params["after"] = after
                page, requests_used = _get_json(client, "/api/read", params=params)
                stats.requests += requests_used
                for passage in page.get("passages", []):
                    uid = passage.get("uid")
                    if not uid or uid in seen_uids:
                        continue
                    seen_uids.add(uid)
                    entries.append(_snapshot_entry(passage, len(entries) + 1))
                if on_progress:
                    on_progress(slug, len(entries), expected)
                if not page.get("has_after"):
                    break
                next_after = page.get("last_id")
                if next_after is None or next_after == after:
                    raise ValueError(f"{slug}: pagination cursor stalled at {after}")
                after = int(next_after)
                pages_since_checkpoint += 1
                if pages_since_checkpoint >= 10:
                    completed[slug] = {
                        "slug": slug,
                        "title": book.get("title") or slug,
                        "arabic_title": book.get("arabic") or None,
                        "group": book.get("group") or None,
                        "opens_at": opens_at,
                        "expected_passages": expected,
                        "complete": False,
                        "after_cursor": after,
                        "entries": entries,
                    }
                    snapshot["works"] = [
                        completed[s] for s in requested if s in completed
                    ]
                    write_snapshot(snapshot, target)
                    pages_since_checkpoint = 0
                if delay_seconds:
                    time.sleep(delay_seconds)

            if len(entries) != expected:
                raise ValueError(f"{slug}: crawled {len(entries)} records, expected {expected}")
            work = {
                "slug": slug,
                "title": book.get("title") or slug,
                "arabic_title": book.get("arabic") or None,
                "group": book.get("group") or None,
                "opens_at": opens_at,
                "expected_passages": expected,
                "complete": True,
                "after_cursor": None,
                "entries": entries,
            }
            completed[slug] = work
            snapshot["works"] = [completed[s] for s in requested if s in completed]
            write_snapshot(snapshot, target)
            stats.works += 1
            stats.entries += len(entries)
            if work_index < len(requested) and delay_seconds:
                time.sleep(delay_seconds)
    finally:
        if owns_client:
            client.close()
    validate_snapshot(snapshot)
    return stats


def _flags(entry: dict[str, Any]) -> list[str]:
    flags = {str(flag) for flag in entry.get("flags", []) if flag}
    flags.add("external_catalogue")
    uid = entry.get("uid")
    if uid:
        flags.add(f"source_uid={uid}")
    return sorted(flags)


def _ensure_book(
    db: Session, work: dict[str, Any], snapshot_hash: str
) -> Book:
    slug = work["slug"]
    book = db.execute(
        select(Book).where(Book.source_book_id == source_book_id(slug))
    ).scalar_one_or_none()
    metadata = {
        "source_key": SOURCE_KEY,
        "snapshot_format": SNAPSHOT_FORMAT,
        "snapshot_sha256": snapshot_hash,
        "work_slug": slug,
        "expected_passages": work["expected_passages"],
        "arabic_title": work.get("arabic_title"),
        "content_mode": "offline_snapshot",
    }
    title = work.get("title") or slug
    if book is None:
        book = Book(
            source_book_id=source_book_id(slug),
            title_original=title,
            title_normalised=normalise_arabic_persian(title),
            language="ar",
            source_url=f"urn:usul16:external-rijal:{slug}",
            metadata_json=metadata,
        )
        db.add(book)
        db.flush()
    else:
        book.title_original = title
        book.title_normalised = normalise_arabic_persian(title)
        book.language = "ar"
        book.source_url = f"urn:usul16:external-rijal:{slug}"
        book.metadata_json = metadata
    return book


def import_external_rijal(db: Session, snapshot: dict[str, Any]) -> ImportStats:
    """Idempotently upsert snapshot records and conservatively link identities."""

    validate_snapshot(snapshot)
    stats = ImportStats()
    digest = snapshot_sha256(snapshot)
    for work in snapshot["works"]:
        stats.works += 1
        book = _ensure_book(db, work, digest)
        existing = {
            row.entry_number: row
            for row in db.execute(
                select(RijalEntry).where(
                    RijalEntry.book_id == book.id,
                    RijalEntry.entry_kind == ENTRY_KIND,
                )
            ).scalars()
        }
        for source_entry in work["entries"]:
            ordinal = int(source_entry["ordinal"])
            citation = str(
                source_entry.get("citation") or source_entry.get("title_raw") or ""
            )
            title, parsed_flags = _extract_title(citation)
            canonical_name = _canonical_name(title)
            canonical_name_normalised = _subject_normalised(title)
            full_text = source_entry.get("text_raw")
            text = str(full_text).strip() if full_text else citation
            flags = sorted(set(_flags(source_entry)) | set(parsed_flags))
            metadata_only = "metadata_only" in flags or not full_text
            values = {
                "narrator_id": None,
                "title_raw": title,
                "title_normalised": normalise_arabic_persian(title),
                "canonical_name_raw": canonical_name,
                "canonical_name_normalised": canonical_name_normalised,
                "text_raw": text,
                "text_normalised": normalise_arabic_persian(text),
                "source_url": None,
                "parser_version": PARSER_VERSION,
                "flags": ",".join(flags),
                "review_status": "metadata_only" if metadata_only else "pending",
            }
            row = existing.get(ordinal)
            if row is None:
                row = RijalEntry(
                    book_id=book.id,
                    entry_kind=ENTRY_KIND,
                    entry_number=ordinal,
                    **values,
                )
                db.add(row)
                existing[ordinal] = row
                stats.created += 1
            else:
                for key, value in values.items():
                    if key == "narrator_id":
                        continue
                    setattr(row, key, value)
                stats.updated += 1
            if metadata_only:
                stats.metadata_only += 1
            else:
                stats.full_text += 1
    db.flush()
    linked = link_external_rijal_entries(db)
    stats.exact = linked.exact
    stats.full_form = linked.full_form
    stats.name_variant = linked.name_variant
    stats.alias = linked.alias
    stats.equivalent = linked.equivalent
    stats.source_number = linked.source_number
    stats.text_witness = linked.text_witness
    stats.fuzzy = linked.fuzzy
    stats.identities_created = linked.created
    stats.external_identity_entries = linked.created_entries
    stats.headings = linked.headings
    stats.multi_subject = linked.multi_subject
    stats.ambiguous = linked.ambiguous
    stats.unmatched = linked.unmatched
    stats.candidate_links = linked.candidate_links
    return stats


def _external_entries(db: Session) -> list[RijalEntry]:
    return list(
        db.execute(
            select(RijalEntry)
            .join(Book, Book.id == RijalEntry.book_id)
            .where(
                Book.source_book_id.like(f"{SOURCE_BOOK_PREFIX}%"),
                RijalEntry.entry_kind == ENTRY_KIND,
            )
            .order_by(RijalEntry.book_id, RijalEntry.entry_number)
        ).scalars()
    )


@dataclass
class _Match:
    candidates: set[int]
    link_type: str
    confidence: int
    ambiguous: bool = False


@dataclass
class _IdentityIndex:
    person_by_id: dict[int, Person]
    narrator_by_person: dict[int, int | None]
    canonical: defaultdict[str, set[int]]
    external_canonical: defaultdict[str, set[int]]
    forms: defaultdict[str, set[int]]
    aliases: defaultdict[str, set[int]]
    strings_by_person: defaultdict[int, set[str]]
    fuzzy_by_first: defaultdict[str, set[int]]
    primary_text_by_person: dict[int, str]
    roots: dict[int, int]


def _find_root(roots: dict[int, int], person_id: int) -> int:
    roots.setdefault(person_id, person_id)
    if roots[person_id] != person_id:
        roots[person_id] = _find_root(roots, roots[person_id])
    return roots[person_id]


def _match_from_candidates(
    index: _IdentityIndex,
    candidates: set[int],
    link_type: str,
    confidence: int,
) -> _Match:
    components = {_find_root(index.roots, person_id) for person_id in candidates}
    if len(components) > 1:
        return _Match(candidates, "external_subject_candidate", 60, ambiguous=True)
    if len(candidates) > 1:
        return _Match(candidates, "external_equivalent_subject", min(confidence, 90))
    person_id = next(iter(candidates))
    if index.person_by_id[person_id].origin == "external_rijal":
        link_type = "external_created_subject"
        confidence = min(confidence, 85)
    return _Match(candidates, link_type, confidence)


def _build_identity_index(db: Session) -> _IdentityIndex:
    persons = list(
        db.execute(select(Person).where(Person.kind != "bare_form_proxy")).scalars()
    )
    person_by_id = {person.id: person for person in persons}
    narrator_by_person: dict[int, int | None] = {}
    primary_text_by_person: dict[int, str] = {}
    for person_id, narrator_id, primary_text in db.execute(
        select(Person.id, RijalEntry.narrator_id, RijalEntry.text_raw).outerjoin(
            RijalEntry, RijalEntry.id == Person.primary_entry_id
        )
    ):
        narrator_by_person[person_id] = narrator_id
        primary_text_by_person[person_id] = primary_text or ""

    roots = {person_id: person_id for person_id in person_by_id}
    for left, right in db.execute(
        select(PersonRelation.person_id, PersonRelation.related_person_id).where(
            PersonRelation.relation_kind == "same_person_as",
            PersonRelation.related_person_id.isnot(None),
        )
    ):
        if left not in roots or right not in roots:
            continue
        left_root, right_root = _find_root(roots, left), _find_root(roots, right)
        if left_root != right_root:
            roots[max(left_root, right_root)] = min(left_root, right_root)

    canonical: defaultdict[str, set[int]] = defaultdict(set)
    external_canonical: defaultdict[str, set[int]] = defaultdict(set)
    forms: defaultdict[str, set[int]] = defaultdict(set)
    aliases: defaultdict[str, set[int]] = defaultdict(set)
    strings_by_person: defaultdict[int, set[str]] = defaultdict(set)
    fuzzy_by_first: defaultdict[str, set[int]] = defaultdict(set)
    for person in persons:
        if person.origin == "external_rijal":
            external_canonical[person.canonical_name_norm].add(person.id)
            continue
        canonical[person.canonical_name_norm].add(person.id)
        strings_by_person[person.id].add(person.canonical_name_norm)
    for person_id, form_norm in db.execute(
        select(PersonSurfaceForm.person_id, PersonSurfaceForm.form_norm).where(
            PersonSurfaceForm.person_id.in_(person_by_id)
        )
    ):
        if person_by_id[person_id].origin == "external_rijal":
            continue
        forms[form_norm].add(person_id)
        strings_by_person[person_id].add(form_norm)
    persons_by_narrator: defaultdict[int, set[int]] = defaultdict(set)
    for person_id, narrator_id in narrator_by_person.items():
        if narrator_id is not None:
            persons_by_narrator[narrator_id].add(person_id)
    for narrator_id, alias_norm in db.execute(
        select(NarratorAlias.narrator_id, NarratorAlias.alias_normalised)
    ):
        aliases[alias_norm].update(persons_by_narrator.get(narrator_id, set()))
    for person_id, strings in strings_by_person.items():
        for value in strings:
            first = value.split(" ", 1)[0]
            if first:
                fuzzy_by_first[first].add(person_id)
    return _IdentityIndex(
        person_by_id=person_by_id,
        narrator_by_person=narrator_by_person,
        canonical=canonical,
        external_canonical=external_canonical,
        forms=forms,
        aliases=aliases,
        strings_by_person=strings_by_person,
        fuzzy_by_first=fuzzy_by_first,
        primary_text_by_person=primary_text_by_person,
        roots=roots,
    )


def _match_identity(index: _IdentityIndex, title: str) -> _Match | None:
    for variant, variant_kind, confidence in _identity_variants(title):
        lookups = (
            (index.canonical.get(variant, set()), "external_exact_subject"),
            (index.aliases.get(variant, set()), "external_alias_subject"),
            (index.forms.get(variant, set()), "external_full_form_subject"),
        )
        for candidates, base_type in lookups:
            if not candidates:
                continue
            if variant_kind != "exact" and base_type != "external_alias_subject":
                base_type = "external_name_variant_subject"
            match = _match_from_candidates(index, set(candidates), base_type, confidence)
            # A rich external heading must not inherit a giant ambiguity cloud
            # merely because one of its shorter legal truncations is shared.
            # If the weaker form is unique it is useful evidence; if it is not,
            # continue and let the precise heading bootstrap its own identity.
            if variant_kind != "exact" and match.ambiguous:
                continue
            return match
    return None


def _match_external_identity(index: _IdentityIndex, title: str) -> _Match | None:
    """Reuse an external identity only for the same complete source heading."""

    candidates = index.external_canonical.get(_subject_normalised(title), set())
    if not candidates:
        return None
    return _match_from_candidates(
        index, set(candidates), "external_created_subject", 85
    )


def _fuzzy_match(index: _IdentityIndex, title: str) -> _Match | None:
    subject = _subject_normalised(title)
    if len(subject) < 8 or len(subject.split()) < 2:
        return None
    first = subject.split(" ", 1)[0]
    pool = index.fuzzy_by_first.get(first, set())
    if not pool or len(pool) > 400:
        return None
    scores_by_root: defaultdict[int, float] = defaultdict(float)
    persons_by_root: defaultdict[int, set[int]] = defaultdict(set)
    for person_id in pool:
        score = max(
            SequenceMatcher(None, subject, candidate).ratio()
            for candidate in index.strings_by_person[person_id]
        )
        root = _find_root(index.roots, person_id)
        scores_by_root[root] = max(scores_by_root[root], score)
        persons_by_root[root].add(person_id)
    ranked = sorted(scores_by_root.items(), key=lambda item: (-item[1], item[0]))
    best_root, best_score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    threshold = 0.88 if len(subject) >= 24 else 0.91
    if best_score < threshold or best_score - runner_up < 0.05:
        return None
    # Similar-looking Arabic names are not identity evidence by themselves:
    # one letter can distinguish a different father or nisba. Accept the
    # near-spelling only when that exact external form is also quoted inside
    # the candidate's local Mu'jam biography.
    corroborated = {
        person_id
        for person_id in persons_by_root[best_root]
        if subject
        in normalise_arabic_persian(index.primary_text_by_person.get(person_id, ""))
    }
    if not corroborated:
        return None
    return _match_from_candidates(
        index,
        corroborated,
        "external_text_witness_subject",
        96,
    )


def _source_number_match(
    index: _IdentityIndex,
    entry: RijalEntry,
    match: _Match | None,
) -> _Match | None:
    """Refine a Fihrist homonym collision using its citation in Mu'jam.

    Fihrist numbering is global and is quoted verbatim in local primary entries
    as ``قال الشيخ (N)``. Tusi's narrator numbering resets by section, while
    the current snapshot has no compatible section key, so this deliberately
    remains specific to Fihrist.
    """

    if match is None or not match.ambiguous:
        return match
    if entry.book.source_book_id != source_book_id("al-fihrist"):
        return match
    citation_number = _CITATION_NUMBER_RE.search(entry.text_raw or "")
    number = citation_number.group(1) if citation_number else str(entry.entry_number)
    citation = re.compile(rf"قال\s+الشيخ\s*\(\s*{re.escape(number)}\s*\)")
    cited = {
        person_id
        for person_id in match.candidates
        if citation.search(index.primary_text_by_person.get(person_id, ""))
    }
    if len(cited) != 1:
        return match
    return _Match(cited, "external_source_number_subject", 98)


def _surface_values(name: str) -> list[tuple[str, str]]:
    parsed = parse_name(name)
    values = [(normalise_arabic_persian(name), "entry_title")]
    values.extend((form.form_norm, form.derivation) for form in surface_forms(parsed))
    seen: set[str] = set()
    return [item for item in values if not (item[0] in seen or seen.add(item[0]))]


def _create_external_person(
    db: Session,
    index: _IdentityIndex,
    entry: RijalEntry,
) -> Person:
    name_norm = _subject_normalised(entry.title_raw)
    parsed = parse_name(name_norm)
    narrator = Narrator(
        canonical_name_ar=name_norm,
        canonical_name_norm=name_norm,
        kunya=parsed.kunya,
        nisba=" ".join(parsed.nisba_parts) or None,
        father_name=parsed.father_norm,
        notes=f"{_EXTERNAL_NARRATOR_NOTE_PREFIX}{name_norm}",
    )
    db.add(narrator)
    db.flush()
    entry.narrator_id = narrator.id
    person = Person(
        canonical_name_ar=name_norm,
        canonical_name_norm=name_norm,
        kunya=parsed.kunya,
        nisba=" ".join(parsed.nisba_parts) or None,
        father_name_norm=parsed.father_norm,
        kind="individual",
        origin="external_rijal",
        primary_entry_id=entry.id,
        notes="Identity bootstrapped from an offline external rijal title witness.",
    )
    db.add(person)
    db.flush()
    surface_values = _surface_values(name_norm)
    for form_norm, derivation in surface_values:
        db.add(
            PersonSurfaceForm(
                person_id=person.id,
                form_raw=form_norm,
                form_norm=form_norm,
                derivation=derivation,
                shared_count=1,
            )
        )
    db.flush()
    index.person_by_id[person.id] = person
    index.narrator_by_person[person.id] = narrator.id
    index.primary_text_by_person[person.id] = entry.text_raw or ""
    index.roots[person.id] = person.id
    index.external_canonical[name_norm].add(person.id)
    return person


def _rehydrate_external_persons(db: Session) -> int:
    represented_narrators = {
        narrator_id
        for narrator_id, in db.execute(
            select(RijalEntry.narrator_id)
            .join(Person, Person.primary_entry_id == RijalEntry.id)
            .where(RijalEntry.narrator_id.isnot(None))
        )
    }
    created = 0
    narrators = list(
        db.execute(
            select(Narrator).where(
                Narrator.notes.like(f"{_EXTERNAL_NARRATOR_NOTE_PREFIX}%")
            )
        ).scalars()
    )
    for narrator in narrators:
        if narrator.id in represented_narrators:
            continue
        entry = db.execute(
            select(RijalEntry)
            .where(
                RijalEntry.narrator_id == narrator.id,
                RijalEntry.entry_kind == ENTRY_KIND,
            )
            .order_by(RijalEntry.id)
        ).scalars().first()
        if entry is None:
            continue
        parsed = parse_name(narrator.canonical_name_norm)
        person = Person(
            canonical_name_ar=narrator.canonical_name_ar,
            canonical_name_norm=narrator.canonical_name_norm,
            kunya=parsed.kunya,
            nisba=" ".join(parsed.nisba_parts) or None,
            father_name_norm=parsed.father_norm,
            kind="individual",
            origin="external_rijal",
            primary_entry_id=entry.id,
            notes="Rehydrated external rijal identity after person-layer rebuild.",
        )
        db.add(person)
        db.flush()
        for form_norm, derivation in _surface_values(narrator.canonical_name_norm):
            db.add(
                PersonSurfaceForm(
                    person_id=person.id,
                    form_raw=form_norm,
                    form_norm=form_norm,
                    derivation=derivation,
                    shared_count=1,
                )
            )
        represented_narrators.add(narrator.id)
        created += 1
    db.flush()
    return created


def _refresh_surface_shared_counts(db: Session) -> None:
    rows = list(db.execute(select(PersonSurfaceForm)).scalars())
    claims: defaultdict[str, set[int]] = defaultdict(set)
    for row in rows:
        claims[row.form_norm].add(row.person_id)
    db.bulk_update_mappings(
        PersonSurfaceForm,
        [{"id": row.id, "shared_count": len(claims[row.form_norm])} for row in rows],
    )


def _add_flag(entry: RijalEntry, flag: str) -> None:
    flags = {item for item in (entry.flags or "").split(",") if item}
    flags.add(flag)
    entry.flags = ",".join(sorted(flags))


def link_external_rijal_entries(db: Session) -> LinkStats:
    """Resolve every defensible witness and create identities that are truly absent."""

    entries = _external_entries(db)
    stats = LinkStats()
    if not entries:
        return stats
    stats.created += _rehydrate_external_persons(db)
    entry_ids = [entry.id for entry in entries]
    db.execute(
        delete(PersonEntryLink).where(
            PersonEntryLink.entry_id.in_(entry_ids),
            PersonEntryLink.link_type.in_(EXTERNAL_LINK_TYPES),
        )
    )
    index = _build_identity_index(db)
    manual_subjects: defaultdict[int, list[int]] = defaultdict(list)
    for entry_id, person_id in db.execute(
        select(PersonEntryLink.entry_id, PersonEntryLink.person_id).where(
            PersonEntryLink.entry_id.in_(entry_ids),
            PersonEntryLink.link_type == "is_subject",
        )
    ):
        manual_subjects[entry_id].append(person_id)

    new_links: list[dict[str, Any]] = []
    seen_links: set[tuple[int, int, str]] = set()

    def add_link(person_id: int, entry_id: int, link_type: str, confidence: int) -> None:
        key = (person_id, entry_id, link_type)
        if key in seen_links:
            return
        seen_links.add(key)
        new_links.append(
            {
                "person_id": person_id,
                "entry_id": entry_id,
                "link_type": link_type,
                "confidence": confidence,
            }
        )

    def apply_match(entry: RijalEntry, match: _Match) -> None:
        if match.ambiguous:
            entry.narrator_id = None
            stats.ambiguous += 1
            # Hyper-generic forms can claim hundreds of people. Forty is
            # enough to expose the collision without materialising a useless
            # all-corpus fan-out.
            for person_id in sorted(match.candidates)[:40]:
                add_link(person_id, entry.id, "external_subject_candidate", match.confidence)
                stats.candidate_links += 1
            return
        representative = min(match.candidates)
        for person_id in sorted(match.candidates):
            add_link(person_id, entry.id, match.link_type, match.confidence)
        entry.narrator_id = index.narrator_by_person.get(representative)
        if match.link_type == "external_exact_subject":
            stats.exact += 1
        elif match.link_type == "external_full_form_subject":
            stats.full_form += 1
        elif match.link_type == "external_name_variant_subject":
            stats.name_variant += 1
        elif match.link_type == "external_alias_subject":
            stats.alias += 1
        elif match.link_type == "external_equivalent_subject":
            stats.equivalent += 1
        elif match.link_type == "external_source_number_subject":
            stats.source_number += 1
        elif match.link_type == "external_text_witness_subject":
            stats.text_witness += 1
        elif match.link_type == "external_fuzzy_subject":
            stats.fuzzy += 1
        elif match.link_type == "external_created_subject":
            stats.created_entries += 1

    unresolved: list[RijalEntry] = []
    multi_entries: list[RijalEntry] = []
    for entry in entries:
        flags = {item for item in (entry.flags or "").split(",") if item}
        kind = _subject_kind(entry.title_raw, flags)
        if kind == "heading":
            _add_flag(entry, "non_person_heading")
            entry.narrator_id = None
            stats.headings += 1
            continue
        if kind == "multi":
            _add_flag(entry, "multi_person_heading")
            entry.narrator_id = None
            multi_entries.append(entry)
            stats.multi_subject += 1
            continue
        manual = sorted(set(manual_subjects.get(entry.id, [])))
        if len(manual) == 1 and manual[0] in index.person_by_id:
            entry.narrator_id = index.narrator_by_person.get(manual[0])
            stats.manual += 1
            continue
        match = _match_identity(index, entry.title_raw) or _fuzzy_match(index, entry.title_raw)
        match = _source_number_match(index, entry, match)
        if match is None:
            unresolved.append(entry)
        else:
            apply_match(entry, match)

    # Richest headings first: a later short form can attach to an identity
    # just created from a fuller nasab, while two distinct full names make the
    # shared short form honestly ambiguous.
    groups: defaultdict[str, list[RijalEntry]] = defaultdict(list)
    for entry in unresolved:
        groups[_subject_normalised(entry.title_raw)].append(entry)
    for _, group in sorted(
        groups.items(),
        key=lambda item: (-max(len(_subject_normalised(e.title_raw)) for e in item[1]), item[0]),
    ):
        representative_entry = max(group, key=lambda entry: len(entry.title_raw))
        match = _match_identity(index, representative_entry.title_raw)
        if match is None:
            match = _fuzzy_match(index, representative_entry.title_raw)
        match = _source_number_match(index, representative_entry, match)
        if match is None:
            match = _match_external_identity(index, representative_entry.title_raw)
        if match is None:
            person = _create_external_person(db, index, representative_entry)
            stats.created += 1
            match = _Match({person.id}, "external_created_subject", 80)
        for entry in group:
            apply_match(entry, match)

    # Multi-person headings are not identity ambiguity. Attach every part we
    # can resolve, but never force the whole document onto one narrator_id.
    for entry in multi_entries:
        subject = _subject_normalised(entry.title_raw)
        matched_people: set[int] = set()
        for part in re.split(r"\sو\s*", subject):
            match = _match_identity(index, part.strip()) or _match_external_identity(
                index, part.strip()
            )
            if match is None or match.ambiguous:
                continue
            matched_people.update(match.candidates)
        for person_id in sorted(matched_people):
            add_link(person_id, entry.id, "external_multi_subject", 75)

    if new_links:
        db.bulk_insert_mappings(PersonEntryLink, new_links)
    _refresh_surface_shared_counts(db)
    db.flush()
    # A single-person heading reaches this point only if a future classifier
    # adds a type the resolver does not understand.
    linked_entry_ids = {link["entry_id"] for link in new_links}
    stats.unmatched = sum(
        1
        for entry in entries
        if _subject_kind(
            entry.title_raw,
            {item for item in (entry.flags or "").split(",") if item},
        )
        == "person"
        and entry.narrator_id is None
        and entry.id not in linked_entry_ids
    )
    return stats


def _legacy_narrator_id(db: Session, person: Person) -> int | None:
    if person.primary_entry_id is None:
        return None
    return db.execute(
        select(RijalEntry.narrator_id).where(RijalEntry.id == person.primary_entry_id)
    ).scalar_one_or_none()


def audit_external_rijal(db: Session) -> AuditStats:
    entries = _external_entries(db)
    entry_ids = [entry.id for entry in entries]
    link_by_entry: defaultdict[int, set[str]] = defaultdict(set)
    if entry_ids:
        for entry_id, link_type in db.execute(
            select(PersonEntryLink.entry_id, PersonEntryLink.link_type).where(
                PersonEntryLink.entry_id.in_(entry_ids),
                PersonEntryLink.link_type.in_(EXTERNAL_LINK_TYPES),
            )
        ):
            link_by_entry[entry_id].add(link_type)
    per_source: defaultdict[str, int] = defaultdict(int)
    metadata_only = exact = full_form = name_variant = alias = equivalent = 0
    source_number = text_witness = 0
    fuzzy = created = headings = multi_subject = ambiguous = unmatched = 0
    for entry in entries:
        per_source[entry.book.source_book_id] += 1
        flags = set((entry.flags or "").split(","))
        if "metadata_only" in flags:
            metadata_only += 1
        types = link_by_entry.get(entry.id, set())
        if "external_exact_subject" in types:
            exact += 1
        elif "external_full_form_subject" in types:
            full_form += 1
        elif "external_name_variant_subject" in types:
            name_variant += 1
        elif "external_alias_subject" in types:
            alias += 1
        elif "external_equivalent_subject" in types:
            equivalent += 1
        elif "external_source_number_subject" in types:
            source_number += 1
        elif "external_text_witness_subject" in types:
            text_witness += 1
        elif "external_fuzzy_subject" in types:
            fuzzy += 1
        elif "external_created_subject" in types:
            created += 1
        elif "external_subject_candidate" in types:
            ambiguous += 1
        elif "multi_person_heading" in flags:
            multi_subject += 1
        elif "non_person_heading" in flags:
            headings += 1
        else:
            unmatched += 1
    return AuditStats(
        entries=len(entries),
        metadata_only=metadata_only,
        exact=exact,
        full_form=full_form,
        name_variant=name_variant,
        alias=alias,
        equivalent=equivalent,
        source_number=source_number,
        text_witness=text_witness,
        fuzzy=fuzzy,
        created=created,
        headings=headings,
        multi_subject=multi_subject,
        ambiguous=ambiguous,
        unmatched=unmatched,
        per_source=dict(sorted(per_source.items())),
    )
