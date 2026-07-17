"""Import matched English translations from public Thaqalayn sources."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Hadith,
    HadithTranslation,
    TranslationAttempt,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation import QA_VERSION, TRANSLATION_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import clean_ws, sha256_text, source_norm


THAQALAYN_API_BASE_URL = "https://www.thaqalayn-api.net/api/v2"
THAQALAYN_STATIC_BASE_URL = "https://thaqalayndata.netlify.app"
THAQALAYN_AL_KAFI_BOOK_IDS = {
    volume: f"Al-Kafi-Volume-{volume}-Kulayni" for volume in range(1, 9)
}
PROVIDER = "thaqalayn-api"
MODEL = "muhammad-sarwar"
UNKNOWN_TRANSLATOR_MODEL = "unknown-translator"
JOB_KEY = "alkafi-thaqalayn-sarwar-import-v1"
STATIC_PROVIDER = "thaqalayn-data"
STATIC_MODEL_MIXED = "sarwar-hubeali-human"
STATIC_JOB_KEY = "alkafi-thaqalayn-data-import-v1"
MATCHER_VERSION = "thaqalayn_match_v2"
STATIC_MATCHER_VERSION = "thaqalayn_static_match_v2"
SOURCE_IMPORT_QA_VERSION = f"{QA_VERSION}+source_import_v1"
MIN_MATCH_SCORE = 0.88
WINDOW_BACK = 64
WINDOW_FORWARD = 128
IMPORT_BLOCKING_QA_CODES = {
    "empty_translation",
    # A mismatch can be harmless edition apparatus, but it can also expose an
    # adjacent-report or wrong-record match.  It therefore requires a bounded
    # source review before publication and must never be auto-downgraded.
    "number_mismatch",
    "translation_too_short",
    "translation_too_long",
    "untranslated_arabic_block",
}

# The generic QA pass is designed for newly generated drafts.  Exact text
# imported from a checksum-pinned human edition legitimately differs from the
# local Arabic edition's footnote/verse numbering, and narrative wording such
# as "cannot provide" is not a model refusal.  Preserve those diagnostics, but
# classify them honestly as source-edition information rather than critical
# translation failures.
SOURCE_IMPORT_DIAGNOSTIC_FLAGS = {
    "missing_placeholder": (
        "external_source_footnote_marker_difference",
        "Local Arabic editorial footnote markers are not interpolated into the "
        "published English source.",
    ),
    "provider_refusal_text": (
        "external_source_literal_phrase",
        "A refusal-like phrase occurs inside the checksum-pinned published "
        "narrative; it is source text, not a provider response.",
    ),
}

# Attribution is a publication claim, not a convenience default.  New source
# translators must be reviewed and added explicitly before their rows can be
# imported as public English.
KNOWN_HUMAN_TRANSLATORS = {
    "muhammad sarwar": "muhammad-sarwar",
    "hubeali": "hubeali",
}

_ARABIC_ONLY_RE = re.compile(r"[^\u0600-\u06ff]+")
_ARABIC_WORD_RE = re.compile(r"[\u0600-\u06ff]{2,}")


class _PlainTextHTMLParser(HTMLParser):
    """Small HTML-to-text helper for Thaqalayn translation fragments."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "span", "sup", "a"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "span", "sup", "a"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def strip_html_text(value: Any) -> str:
    if value is None:
        return ""
    parser = _PlainTextHTMLParser()
    parser.feed(str(value))
    return clean_ws(html.unescape(parser.text()))


def _join_static_text(value: Any) -> str:
    if isinstance(value, list):
        return clean_ws(" ".join(strip_html_text(part) for part in value))
    return strip_html_text(value)


@dataclass(frozen=True)
class ThaqalaynRecord:
    id: int
    book_id: str
    volume: int
    arabic_text: str
    english_text: str
    thaqalayn_sanad: str | None
    thaqalayn_matn: str | None
    url: str | None
    translator: str | None
    category: str | None
    chapter: str | None
    raw: dict[str, Any]
    provider: str = PROVIDER
    model: str = MODEL
    source_name: str = "thaqalayn-api"
    matcher_version: str = MATCHER_VERSION
    match_norm: str = field(init=False)
    match_words: set[str] = field(init=False)

    def __post_init__(self) -> None:
        normalised = match_norm(self.arabic_text)
        object.__setattr__(self, "match_norm", normalised)
        object.__setattr__(self, "match_words", match_words(self.arabic_text))

    @property
    def usable_translation(self) -> str:
        return clean_ws(self.thaqalayn_matn or self.english_text)


@dataclass(frozen=True)
class TranslationMatch:
    hadith_id: int
    public_id: str
    volume: int
    thaqalayn_id: int
    score: float
    url: str | None
    english_text: str
    rendered_isnad_en: str | None
    provider: str
    model: str
    source_name: str
    translator: str | None
    matcher_version: str
    qa_risk_level: str
    qa_flags: list[dict[str, str]]

    @property
    def publishable(self) -> bool:
        translator_key = clean_ws(self.translator).casefold()
        return (
            self.score >= MIN_MATCH_SCORE
            and translator_key in KNOWN_HUMAN_TRANSLATORS
            and not any(
                flag["code"] in IMPORT_BLOCKING_QA_CODES for flag in self.qa_flags
            )
        )

    @property
    def import_risk_level(self) -> str:
        return "green" if self.publishable else self.qa_risk_level

    @property
    def publication_flags(self) -> list[dict[str, str]]:
        return source_import_publication_flags(self.qa_flags)


def source_import_publication_flags(
    qa_flags: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    """Convert draft-oriented diagnostics into source-import audit metadata."""

    publication_flags: list[dict[str, str]] = []
    for flag in qa_flags or []:
        mapped = SOURCE_IMPORT_DIAGNOSTIC_FLAGS.get(flag.get("code", ""))
        if mapped is None:
            publication_flags.append(dict(flag))
            continue
        code, detail = mapped
        original_detail = flag.get("detail")
        publication_flags.append(
            {
                "code": code,
                "severity": "info",
                "detail": detail,
                **(
                    {"original_diagnostic": original_detail}
                    if original_detail
                    else {}
                ),
            }
        )
    return publication_flags


@dataclass
class ImportStats:
    fetched: int = 0
    local_hadiths: int = 0
    matched: int = 0
    imported: int = 0
    skipped_existing: int = 0
    skipped_low_confidence: int = 0
    skipped_qa: int = 0
    relabelled_published: int = 0
    unmatched_local: int = 0
    unmatched_remote: int = 0
    errors: list[str] = field(default_factory=list)
    by_volume: dict[int, dict[str, int]] = field(default_factory=dict)
    sample_matches: list[TranslationMatch] = field(default_factory=list)


def fetch_al_kafi_records(
    *,
    base_url: str = THAQALAYN_API_BASE_URL,
    timeout_seconds: int = 60,
) -> dict[int, list[ThaqalaynRecord]]:
    by_volume: dict[int, list[ThaqalaynRecord]] = {}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        for volume, book_id in THAQALAYN_AL_KAFI_BOOK_IDS.items():
            response = client.get(f"{base_url.rstrip('/')}/{book_id}")
            response.raise_for_status()
            rows = response.json()
            by_volume[volume] = [parse_record(row) for row in rows]
    return by_volume


def fetch_al_kafi_static_records(
    *,
    base_url: str = THAQALAYN_STATIC_BASE_URL,
    cache_path: str | Path | None = None,
    timeout_seconds: int = 60,
    max_workers: int = 16,
) -> dict[int, list[ThaqalaynRecord]]:
    """Fetch Al-Kafi detail JSON from the CC0 ThaqalaynData static dataset.

    The complete-book endpoint contains only references, so we fetch the
    individual hadith JSON files and cache the normalized rows for repeatable
    dry-runs. AI-generated fields in the source are intentionally ignored.
    """

    cache = Path(cache_path) if cache_path else None
    if cache and cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        return static_records_from_rows(payload)

    base = base_url.rstrip("/")
    manifest_url = f"{base}/books/complete/al-kafi.json"
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        manifest_response = client.get(manifest_url)
        manifest_response.raise_for_status()
        paths = _static_hadith_paths(manifest_response.json())

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_fetch_static_detail_row, base, path, timeout_seconds)
            for path in paths
        ]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (int(row.get("volume") or 0), int(row.get("index") or 0)))
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return static_records_from_rows(rows)


def _fetch_static_detail_row(base_url: str, path: str, timeout_seconds: int) -> dict[str, Any]:
    url = f"{base_url}{path.replace(':', '/')}.json"
    try:
        with httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "Usul16 translation importer"},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return static_row_from_detail(response.json(), fallback_path=path)
    except Exception as exc:  # pragma: no cover - exercised only during live fetches
        volume = _volume_from_static_path(path)
        return {"volume": volume, "path": path, "source_url": _thaqalayn_public_url(path), "error": str(exc)}


def _static_hadith_paths(node: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(node, dict):
        part_type = node.get("part_type")
        path = node.get("path")
        if part_type == "Hadith" and isinstance(path, str):
            paths.append(path)
        for key in ("chapters", "verse_refs"):
            for child in node.get(key) or []:
                paths.extend(_static_hadith_paths(child))
    elif isinstance(node, list):
        for child in node:
            paths.extend(_static_hadith_paths(child))
    return paths


def static_records_from_rows(rows: list[dict[str, Any]]) -> dict[int, list[ThaqalaynRecord]]:
    by_volume: dict[int, list[ThaqalaynRecord]] = {}
    for row in rows:
        record = parse_static_row(row)
        if record is None:
            continue
        by_volume.setdefault(record.volume, []).append(record)
    for volume_rows in by_volume.values():
        volume_rows.sort(key=lambda record: record.id)
    return by_volume


def static_row_from_detail(detail: dict[str, Any], *, fallback_path: str | None = None) -> dict[str, Any]:
    verse = ((detail.get("data") or {}).get("verse") or {})
    path = str(verse.get("path") or fallback_path or "")
    translations = verse.get("translations") or {}
    return {
        "volume": _volume_from_static_path(path),
        "path": path,
        "index": int(verse.get("index") or 0),
        "arabic_text": _join_static_text(verse.get("text")),
        "en_sarwar": _join_static_text(translations.get("en.sarwar")),
        "en_hubeali": _join_static_text(translations.get("en.hubeali")),
        "source_url": _thaqalayn_public_url(path),
    }


def parse_static_row(row: dict[str, Any]) -> ThaqalaynRecord | None:
    arabic_text = _join_static_text(row.get("arabic_text"))
    english_text, translator, model = _choose_static_translation(row)
    if not arabic_text or not english_text:
        return None
    path = str(row.get("path") or "")
    record_id = int(row.get("index") or row.get("position") or 0)
    if record_id <= 0:
        return None
    return ThaqalaynRecord(
        id=record_id,
        book_id="ThaqalaynData-al-kafi",
        volume=int(row.get("volume") or _volume_from_static_path(path)),
        arabic_text=arabic_text,
        english_text=english_text,
        thaqalayn_sanad=None,
        thaqalayn_matn=english_text,
        url=clean_ws(row.get("source_url")) or _thaqalayn_public_url(path),
        translator=translator,
        category=None,
        chapter=None,
        provider=STATIC_PROVIDER,
        model=model,
        source_name="thaqalayn-data",
        matcher_version=STATIC_MATCHER_VERSION,
        raw=row,
    )


def _choose_static_translation(row: dict[str, Any]) -> tuple[str, str | None, str]:
    sarwar = _join_static_text(row.get("en_sarwar"))
    if sarwar:
        return sarwar, "Muhammad Sarwar", "muhammad-sarwar"
    hubeali = _join_static_text(row.get("en_hubeali"))
    if hubeali:
        return hubeali, "HubeAli", "hubeali"
    return "", None, STATIC_MODEL_MIXED


def _volume_from_static_path(path: str) -> int:
    match = re.search(r"/books/al-kafi:(\d+)", path or "")
    if match:
        return int(match.group(1))
    return 0


def _thaqalayn_public_url(path: str) -> str | None:
    if not path:
        return None
    return f"https://thaqalayn.net{path}"


def parse_record(row: dict[str, Any]) -> ThaqalaynRecord:
    volume = int(row.get("volume") or 0)
    translator = clean_ws(row.get("translator")) or None
    model = KNOWN_HUMAN_TRANSLATORS.get(
        clean_ws(translator).casefold(), UNKNOWN_TRANSLATOR_MODEL
    )
    return ThaqalaynRecord(
        id=int(row["id"]),
        book_id=str(row["bookId"]),
        volume=volume,
        arabic_text=str(row.get("arabicText") or ""),
        english_text=str(row.get("englishText") or ""),
        thaqalayn_sanad=clean_ws(row.get("thaqalaynSanad")) or None,
        thaqalayn_matn=clean_ws(row.get("thaqalaynMatn")) or None,
        url=_canonical_api_hadith_url(clean_ws(row.get("URL")), volume=volume),
        translator=translator,
        category=clean_ws(row.get("category")) or None,
        chapter=clean_ws(row.get("chapter")) or None,
        provider=PROVIDER,
        model=model,
        source_name="thaqalayn-api",
        matcher_version=MATCHER_VERSION,
        raw=row,
    )


def _canonical_api_hadith_url(value: str, *, volume: int) -> str | None:
    """Repair the volume component in legacy Thaqalayn API URLs.

    Some API payloads correctly identify their Al-Kafi volume in ``volume``
    and ``bookId`` but still emit a URL beginning with ``/hadith/1/``.  The
    live site uses the real volume as the first route component.
    """

    if not value:
        return None
    if volume <= 0:
        return value
    return re.sub(r"(/hadith/)\d+(/)", rf"\g<1>{volume}\g<2>", value, count=1)


def match_norm(text: str | None) -> str:
    normalised = normalise_arabic_persian(clean_ws(text or ""))
    return _ARABIC_ONLY_RE.sub("", normalised)


def match_words(text: str | None) -> set[str]:
    return set(_ARABIC_WORD_RE.findall(normalise_arabic_persian(clean_ws(text or ""))))


def word_coverage(needle: set[str], haystack: set[str]) -> float:
    if not needle:
        return 0.0
    return len(needle & haystack) / len(needle)


def match_score(local: Hadith, remote: ThaqalaynRecord) -> float:
    local_full = match_norm(local.full_text_raw)
    local_matn = match_norm(local.matn_raw)
    return match_score_parts(
        local_full=local_full,
        local_matn=local_matn,
        local_full_words=match_words(local.full_text_raw),
        local_matn_words=match_words(local.matn_raw),
        remote=remote,
    )


def match_score_parts(
    *,
    local_full: str,
    local_matn: str,
    local_full_words: set[str],
    local_matn_words: set[str],
    remote: ThaqalaynRecord,
) -> float:
    remote_text = remote.match_norm
    if not remote_text:
        return 0.0
    if _safe_exact_or_containment(local_matn, remote_text):
        return 1.0
    if _safe_exact_or_containment(remote_text, local_full):
        return 1.0
    return max(
        word_coverage(local_matn_words, remote.match_words),
        word_coverage(local_full_words, remote.match_words),
    )


def _safe_exact_or_containment(needle: str, haystack: str) -> bool:
    """Avoid treating malformed one-word source rows as exact matches.

    A few upstream rows contain only text such as ``لا .`` while retaining an
    unrelated English translation.  Equality is still reliable for genuinely
    short reports; substring containment requires enough Arabic signal to be
    distinctive.
    """

    if not needle or not haystack or needle not in haystack:
        return False
    if needle == haystack:
        return True
    return len(needle) >= 12 and len(_ARABIC_WORD_RE.findall(needle)) >= 3


def build_matches(
    db: Session,
    *,
    source_book_id: str,
    remote_by_volume: dict[int, list[ThaqalaynRecord]],
    min_score: float = MIN_MATCH_SCORE,
) -> tuple[list[TranslationMatch], ImportStats]:
    book = db.execute(select(Book).where(Book.source_book_id == source_book_id)).scalar_one()
    local_by_volume: dict[int, list[Hadith]] = {}
    rows = (
        db.execute(
            select(Hadith)
            .where(Hadith.book_id == book.id, Hadith.review_status != "rejected_non_hadith_fragment")
            .order_by(Hadith.sequence_in_book)
        )
        .scalars()
        .all()
    )
    for hadith in rows:
        if hadith.volume_start is not None:
            local_by_volume.setdefault(hadith.volume_start, []).append(hadith)

    stats = ImportStats(
        fetched=sum(len(rows) for rows in remote_by_volume.values()),
        local_hadiths=sum(len(rows) for rows in local_by_volume.values()),
    )
    matches: list[TranslationMatch] = []
    for volume in sorted(remote_by_volume):
        local_rows = local_by_volume.get(volume, [])
        remote_rows = remote_by_volume.get(volume, [])
        volume_matches = _match_volume(db, local_rows, remote_rows, min_score=min_score)
        used_remote = {match.thaqalayn_id for match in volume_matches}
        stats.by_volume[volume] = {
            "local": len(local_rows),
            "remote": len(remote_rows),
            "matched": len(volume_matches),
            "unmatched_local": max(0, len(local_rows) - len(volume_matches)),
            "unmatched_remote": max(0, len(remote_rows) - len(used_remote)),
        }
        stats.matched += len(volume_matches)
        stats.unmatched_local += stats.by_volume[volume]["unmatched_local"]
        stats.unmatched_remote += stats.by_volume[volume]["unmatched_remote"]
        matches.extend(volume_matches)
    stats.sample_matches = matches[:10]
    return matches, stats


def _match_volume(
    db: Session,
    local_rows: list[Hadith],
    remote_rows: list[ThaqalaynRecord],
    *,
    min_score: float,
) -> list[TranslationMatch]:
    matches: list[TranslationMatch] = []
    remote_cursor = 0
    used_remote: set[int] = set()
    remote_indexes = {id(row): index for index, row in enumerate(remote_rows)}
    for hadith in local_rows:
        # The two editions occasionally reorder a nearby report or insert
        # material absent from the other source. A bounded look-back recovers
        # those cases without falling back to an unsafe volume-wide search.
        start = max(0, remote_cursor - WINDOW_BACK)
        end = min(len(remote_rows), remote_cursor + WINDOW_FORWARD)
        candidates = [row for row in remote_rows[start:end] if row.id not in used_remote]
        if not candidates:
            continue
        local_full = match_norm(hadith.full_text_raw)
        local_matn = match_norm(hadith.matn_raw)
        local_full_words = match_words(hadith.full_text_raw)
        local_matn_words = match_words(hadith.matn_raw)

        def score_candidate(row: ThaqalaynRecord) -> float:
            return match_score_parts(
                local_full=local_full,
                local_matn=local_matn,
                local_full_words=local_full_words,
                local_matn_words=local_matn_words,
                remote=row,
            )

        eligible = [
            (score_candidate(candidate), candidate)
            for candidate in candidates
        ]
        eligible = [item for item in eligible if item[0] >= min_score]
        if eligible:
            # Choose the strongest Arabic match, not merely the first match
            # above the threshold. Sequence proximity breaks equal-score ties
            # so repeated short reports remain locally aligned.
            score, best = max(
                eligible,
                key=lambda item: (
                    item[0],
                    -abs(remote_indexes[id(item[1])] - remote_cursor),
                    -remote_indexes[id(item[1])],
                ),
            )
        else:
            best = None
            score = 0.0
        if best is None:
            continue
        if not best.usable_translation:
            continue
        used_remote.add(best.id)
        best_index = remote_indexes[id(best)]
        remote_cursor = max(remote_cursor, best_index + 1)
        qa = assess_translation(hadith.matn_raw, best.usable_translation)
        matches.append(
            TranslationMatch(
                hadith_id=hadith.id,
                public_id=hadith.public_id,
                volume=hadith.volume_start or 0,
                thaqalayn_id=best.id,
                score=score,
                url=best.url,
                english_text=best.usable_translation,
                rendered_isnad_en=best.thaqalayn_sanad,
                provider=best.provider,
                model=best.model,
                source_name=best.source_name,
                translator=best.translator,
                matcher_version=best.matcher_version,
                qa_risk_level=qa.risk_level,
                qa_flags=[flag.__dict__ for flag in qa.flags],
            )
        )
    return matches


def import_thaqalayn_al_kafi(
    db: Session,
    *,
    source_book_id: str = "11005",
    remote_by_volume: dict[int, list[ThaqalaynRecord]] | None = None,
    dry_run: bool = True,
    overwrite_current: bool = False,
    min_score: float = MIN_MATCH_SCORE,
    job_key: str = JOB_KEY,
    replace_providers: set[str] | None = None,
    matches: list[TranslationMatch] | None = None,
) -> ImportStats:
    """Import Thaqalayn English into local Al-Kafi reports.

    ``matches`` lets a caller supply pairings established by another method and
    reuse this function's QA, publishability, hashing and provenance rules
    unchanged.  ``_match_volume`` only ever compares a bounded window of remote
    rows, so a counterpart sitting far from the running cursor is never scored;
    a caller that has identified such a pair by an unbounded, symmetric search
    passes it here rather than re-implementing the write path.  Supplied
    matches still face every publishability and QA gate below.
    """

    if matches is not None:
        stats = ImportStats(
            fetched=sum(len(rows) for rows in (remote_by_volume or {}).values()),
            local_hadiths=len(matches),
            matched=len(matches),
        )
        for match in matches:
            stats.by_volume.setdefault(
                match.volume,
                {"local": 0, "remote": 0, "matched": 0, "unmatched_local": 0, "unmatched_remote": 0},
            )
            stats.by_volume[match.volume]["matched"] += 1
        stats.sample_matches = matches[:10]
    else:
        remote_by_volume = (
            remote_by_volume if remote_by_volume is not None else fetch_al_kafi_records()
        )
        matches, stats = build_matches(
            db,
            source_book_id=source_book_id,
            remote_by_volume=remote_by_volume,
            min_score=min_score,
        )
    if dry_run:
        stats.skipped_qa = len([match for match in matches if not match.publishable])
        stats.skipped_low_confidence = len([match for match in matches if match.score < min_score])
        return stats

    now = dt.datetime.now(dt.timezone.utc)
    legacy_thaqalayn_ids = select(HadithTranslation.id).where(
        HadithTranslation.provider == PROVIDER,
        HadithTranslation.status == "machine_verified",
    )
    db.query(TranslationSegment).filter(
        TranslationSegment.translation_id.in_(legacy_thaqalayn_ids),
        TranslationSegment.status == "machine_verified",
    ).update({TranslationSegment.status: "published"}, synchronize_session=False)
    stats.relabelled_published = (
        db.query(HadithTranslation)
        .filter(
            HadithTranslation.provider == PROVIDER,
            HadithTranslation.status == "machine_verified",
        )
        .update({HadithTranslation.status: "published"}, synchronize_session=False)
    )
    job = _get_or_create_job(
        db,
        source_book_id=source_book_id,
        match_count=len(matches),
        now=now,
        job_key=job_key,
        provider=STATIC_PROVIDER if job_key == STATIC_JOB_KEY else PROVIDER,
        model=STATIC_MODEL_MIXED if job_key == STATIC_JOB_KEY else MODEL,
    )
    replace_providers = replace_providers or set()
    next_item_index = len(job.items) + 1
    for match in matches:
        translation = db.execute(
            select(HadithTranslation).where(
                HadithTranslation.hadith_id == match.hadith_id,
                HadithTranslation.language == "en",
                HadithTranslation.translation_version == TRANSLATION_VERSION,
            )
        ).scalar_one_or_none()
        if (
            translation is not None
            and not overwrite_current
            and translation.provider not in replace_providers
            and translation.status in {"machine_verified", "human_reviewed", "published"}
            and translation.risk_level == "green"
            and translation.matn_translation
        ):
            stats.skipped_existing += 1
            continue
        if not match.publishable:
            if match.score < min_score:
                stats.skipped_low_confidence += 1
            else:
                stats.skipped_qa += 1
            continue
        hadith = db.get(Hadith, match.hadith_id)
        if hadith is None:
            stats.errors.append(f"Hadith id {match.hadith_id} disappeared during import")
            continue
        translation = _upsert_translation(db, hadith, match, now=now)
        segment = _upsert_segment(db, translation, hadith, match, now=now)
        item = TranslationJobItem(
            job_id=job.id,
            hadith_id=hadith.id,
            segment_id=segment.id,
            item_index=next_item_index,
            source_sha256=sha256_text(hadith.matn_raw),
            status="verified",
            risk_level="green",
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        db.flush()
        db.add(
            TranslationAttempt(
                job_id=job.id,
                item_id=item.id,
                provider=match.provider,
                model=match.model,
                status="completed",
                request_json={"url": match.url, "thaqalayn_id": match.thaqalayn_id},
                response_json={
                    "match_score": match.score,
                    "qa_risk_level": match.qa_risk_level,
                    "qa_flags": match.qa_flags,
                    "source_english_sha256": sha256_text(match.english_text),
                    "translation_classification": "external_source_normalized",
                },
                input_tokens=0,
                output_tokens=0,
                cost_estimate_usd=0.0,
                created_at=now,
            )
        )
        next_item_index += 1
        stats.imported += 1

    job.hadith_count = stats.imported
    job.segment_count = stats.imported
    job.status = "completed"
    job.completed_at = now
    job.updated_at = now
    db.flush()
    return stats


def _get_or_create_job(
    db: Session,
    *,
    source_book_id: str,
    match_count: int,
    now: dt.datetime,
    job_key: str = JOB_KEY,
    provider: str = PROVIDER,
    model: str = MODEL,
) -> TranslationJob:
    job = db.execute(select(TranslationJob).where(TranslationJob.job_key == job_key)).scalar_one_or_none()
    if job is not None:
        job.status = "running"
        job.started_at = job.started_at or now
        job.updated_at = now
        return job
    job = TranslationJob(
        job_key=job_key,
        source_book_id=source_book_id,
        language="en",
        status="running",
        provider=provider,
        model=model,
        prompt_version=STATIC_MATCHER_VERSION if job_key == STATIC_JOB_KEY else MATCHER_VERSION,
        glossary_version=None,
        scope_json={
            "source": "https://github.com/narmafraz/ThaqalaynData"
            if job_key == STATIC_JOB_KEY
            else "https://www.thaqalayn-api.net/",
            "book_ids": THAQALAYN_AL_KAFI_BOOK_IDS,
            "translation_version": TRANSLATION_VERSION,
            "candidate_matches": match_count,
        },
        batch_policy_json={"mode": "arabic_similarity_match"},
        hadith_count=0,
        segment_count=0,
        input_chars=0,
        estimated_input_tokens=0,
        estimated_output_tokens=0,
        estimated_cost_usd=0.0,
        created_at=now,
        updated_at=now,
        started_at=now,
    )
    db.add(job)
    db.flush()
    return job


def _upsert_translation(
    db: Session,
    hadith: Hadith,
    match: TranslationMatch,
    *,
    now: dt.datetime,
) -> HadithTranslation:
    translation = db.execute(
        select(HadithTranslation).where(
            HadithTranslation.hadith_id == hadith.id,
            HadithTranslation.language == "en",
            HadithTranslation.translation_version == TRANSLATION_VERSION,
        )
    ).scalar_one_or_none()
    values = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None,
        "source_matn_sha256": sha256_text(hadith.matn_raw),
        "rendered_isnad_en": match.rendered_isnad_en,
        "matn_translation": match.english_text,
        "full_translation": None,
        # Muhammad Sarwar is a human translator and Thaqalayn is the
        # publication source. This is not a machine-generated draft.
        "status": "published",
        "risk_level": match.import_risk_level,
        "risk_flags": match.publication_flags,
        "provider": match.provider,
        "model": match.model,
        "prompt_version": match.matcher_version,
        "glossary_version": None,
        "qa_version": SOURCE_IMPORT_QA_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_estimate_usd": 0.0,
        "provenance_json": {
            "source": match.source_name,
            "source_url": match.url,
            "thaqalayn_id": match.thaqalayn_id,
            "volume": match.volume,
            "translator": match.translator,
            "translator_attribution": "upstream-metadata",
            "source_english_sha256": sha256_text(match.english_text),
            "translation_classification": "external_source_normalized",
            "match_score": match.score,
            "matcher_version": match.matcher_version,
        },
        "updated_at": now,
    }
    if translation is None:
        translation = HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            created_at=now,
            **values,
        )
        db.add(translation)
    else:
        for key, value in values.items():
            setattr(translation, key, value)
    db.flush()
    return translation


def _upsert_segment(
    db: Session,
    translation: HadithTranslation,
    hadith: Hadith,
    match: TranslationMatch,
    *,
    now: dt.datetime,
) -> TranslationSegment:
    source_hash = sha256_text(hadith.matn_raw)
    segment = db.execute(
        select(TranslationSegment).where(
            TranslationSegment.hadith_id == hadith.id,
            TranslationSegment.language == "en",
            TranslationSegment.translation_version == TRANSLATION_VERSION,
            TranslationSegment.segment_kind == "matn",
            TranslationSegment.segment_index == 0,
            TranslationSegment.source_sha256 == source_hash,
        )
    ).scalar_one_or_none()
    values = {
        "translation_id": translation.id,
        "source_text": hadith.matn_raw,
        "translation_text": match.english_text,
        "status": "published",
        "risk_level": match.import_risk_level,
        "risk_flags": match.publication_flags,
        "metadata_json": {
            "source_norm": source_norm(hadith.matn_raw),
            "source": match.source_name,
            "provider": match.provider,
            "source_url": match.url,
            "thaqalayn_id": match.thaqalayn_id,
            "match_score": match.score,
            "translator": match.translator,
            "source_english_sha256": sha256_text(match.english_text),
            "translation_classification": "external_source_normalized",
        },
        "updated_at": now,
    }
    if segment is None:
        segment = TranslationSegment(
            hadith_id=hadith.id,
            language="en",
            translation_version=TRANSLATION_VERSION,
            segment_kind="matn",
            segment_index=0,
            source_sha256=source_hash,
            created_at=now,
            **values,
        )
        db.add(segment)
    else:
        for key, value in values.items():
            setattr(segment, key, value)
    db.flush()
    return segment


def format_import_stats(stats: ImportStats) -> str:
    volume_lines = [
        f"  v{volume}: local={row['local']} remote={row['remote']} matched={row['matched']} "
        f"unmatched_local={row['unmatched_local']} unmatched_remote={row['unmatched_remote']}"
        for volume, row in sorted(stats.by_volume.items())
    ]
    sample_lines = [
        f"  {match.public_id} -> v{match.volume}/{match.thaqalayn_id} "
        f"score={match.score:.3f} qa={match.qa_risk_level}"
        for match in stats.sample_matches[:10]
    ]
    return "\n".join(
        [
            f"fetched={stats.fetched}; local={stats.local_hadiths}; matched={stats.matched}; imported={stats.imported}",
            f"skipped_existing={stats.skipped_existing}; skipped_low_confidence={stats.skipped_low_confidence}; "
            f"skipped_qa={stats.skipped_qa}; relabelled_published={stats.relabelled_published}",
            f"unmatched_local={stats.unmatched_local}; unmatched_remote={stats.unmatched_remote}; errors={len(stats.errors)}",
            "by volume:",
            *volume_lines,
            "sample matches:",
            *(sample_lines or ["  none"]),
        ]
    )
