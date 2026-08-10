"""Source-preserving import and coverage audit for Faqih's Mashyakha.

Al-Saduq commonly abbreviates *Man la yahduruhu al-Faqih* at the first named
narrator.  The separate Mashyakha records his path to that narrator.  This
module records that witness independently before any later expansion can add a
virtual preface to a chain.  It therefore never overwrites the printed Faqih
isnad and it never turns an unreviewed textual match into a graph edge.

Matching is tiered by the strength of the evidence, and every tier is labelled
on the proposal it creates.  Only tiers that leave exactly one source witness
standing are proposed; anything with a surviving alternative is recorded as
ranked candidates for review rather than being forced into a winner.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MashyakhaExpansion,
    MashyakhaPath,
)
from eshia_research.normalise import normalise_arabic_persian, strip_diacritics
from eshia_research.translation.text import clean_ws, sha256_text
from eshia_research.translation.thaqalayn_website import (
    BASE_URL,
    ROBOTS_URL,
    USER_AGENT,
    parse_book_chapter_paths,
)


FAQIH_SOURCE_BOOK_ID = "11021"
FAQIH_MASHYAKHA_REMOTE_BOOK_ID = 38
FAQIH_MASHYAKHA_SOURCE_KEY = "thaqalayn-faqih-mashaykha-v1"
MASHYAKHA_PARSER_VERSION = "faqih_mashyakha_v2"

# Match methods, strongest first.  The first four leave a single source witness
# standing and are proposed; PARTIAL_NAME_CANDIDATE never is.
MATCH_EXACT = "exact_first_narrator"
MATCH_CANONICAL = "canonical_first_narrator"
MATCH_NAME_EXTENSION = "unique_name_extension"
MATCH_ISM_NISBA_ELISION = "ism_nisba_elision"
MATCH_PARTIAL_CANDIDATE = "partial_name_candidate"

SINGLE_CANDIDATE_METHODS = (
    MATCH_EXACT,
    MATCH_CANONICAL,
    MATCH_NAME_EXTENSION,
    MATCH_ISM_NISBA_ELISION,
)

# --- source-side parsing (operates on the printed Arabic, diacritics and all) ---

# al-Saduq writes the same formula several ways: "و ما كان فيه عن X فقد رويته",
# "كل ما كان في هذا الكتاب عن X فقد رويته", and once "فقد حدثني به".  The
# edition also punctuates it inconsistently ("ما كان فيه، عن X فقد رويته، عن").
_TARGET_AND_PATH_RE = re.compile(
    r"(?:^|\s)(?:و\s+)?(?:كل\s+)?ما\s+كان\s+(?:في\s+هذا\s+الكتاب|فيه|فيها)\s*[،,]?\s*"
    r"عن\s+(?P<target>.+?)\s*[،,]?\s*"
    r"فقد\s+(?:رويته|رويتها|حدثني\s+به)\s*[،,]?\s*(?P<path>.+)$",
    re.DOTALL,
)
# "ما كان فيه من حديث/خبر/وصية …", "ما كان فيه مما كتبه …", "متفرقا من قضايا …".
# These entries key on a subject, not on a narrator, so they have no target form
# to match against and are not parser failures.
_TOPIC_ENTRY_RE = re.compile(
    r"ما\s+كان\s+(?:في\s+هذا\s+الكتاب|فيه|فيها)\s*[،,]?\s*(?:من|مما|متفرقا)\s"
)
_PATH_COMMENTARY_RE = re.compile(
    r"\s*[،,]\s*(?:و\s+(?:هو|هي|كان|كانت|قد|هذا)|قال(?:ت)?\b).*$",
    re.DOTALL,
)
# One entry may cover several narrators sharing a path: "عن محمد بن حمران؛ و
# جميل بن دراج فقد رويته …".
_TARGET_ALTERNATIVES_RE = re.compile(r"\s*(?:؛|;)\s*و\s+|\s*[،,]\s*و\s+")
# "عن زرعة، عن سماعة" names a two-step opening; the first step is itself a
# target form, because that is the token a report opens with.
_TARGET_STEP_RE = re.compile(r"\s*[،,]?\s*عن\s+")
# "سعدان بن مسلم و اسمه عبد الرحمن بن مسلم" — an editorial gloss on the name,
# not another narrator and not part of the form.
_TARGET_GLOSS_RE = re.compile(r"\s+و\s+اسمه\s+.*$", re.DOTALL)
_NARRATION_SPLIT_RE = re.compile(r"\s+عن\s+")
_PATH_PREFIX_RE = re.compile(r"^عن\s+")
_ZERO_WIDTH_RE = re.compile("[​-‏⁠﻿]")

# --- report-side canonicalisation (operates on *_normalised text) ---

# The chain tokenizer sometimes keeps the preposition that introduced the
# narrator, and the printed page sometimes keeps a following honorific or
# "بإسناده".  None of that is part of the name.
_OPENING_LEAD_RE = re.compile(r"^(?:و\s+|عنه\s+|عن\s+)+")
_OPENING_TRAIL_RE = re.compile(
    r"\s+(?:باسناده"
    r"|بهذا\s+الاسناد"
    r"|عنه\s+ع(?![ء-ۿ])(?:\s.*)?"
    r"|رضی\s+الله\s+عنهم?ا?"
    r"|رحمة?\s+الله\s+علیه"
    r"|رحمه\s+الله"
    r"|قدس\s+الله\s+روحه"
    r"|علیه(?:ما|م)?\s+السلام"
    r"|عن\s+ابیه"
    r")\s*$"
)
# The Mashyakha names its target in the genitive after "عن" (أبي بصير); the
# report prints it in whatever case its own sentence needs (أبو/أبا بصير).
_KUNYA_CASE_RE = re.compile(r"(?<![ء-ۿ])اب[وا](?=\s)")
# The edition brackets its honorifics with dashes ("الأشعري- رضي الله عنه-"),
# which have to go before the trailing-honorific rule can see them.
_OPENING_PUNCT_RE = re.compile(r"[()\[\].\-‐-―\"“”]")
# Some entries name a narrator but cover only one subject: "شعيب بن واقد في
# المناهي", "الفضل بن شاذان من العلل التي ذكرها".  Such an entry vouches for
# that subject alone, so it must never be the sole candidate for a bare name.
_TARGET_SUBJECT_SCOPE_RE = re.compile(r"\s+(?:فی|من)\s+")


@dataclass(frozen=True)
class MashyakhaSourceEntry:
    source_chapter: int
    source_hadith_number: int | None
    source_url: str
    source_text_ar: str
    source_text_en: str | None = None


@dataclass(frozen=True)
class ParsedMashyakhaPath:
    target_raw: str | None
    target_normalised: str | None
    path_nodes: list[str]
    review_status: str
    target_forms: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(frozen=True)
class OpeningCandidate:
    path: MashyakhaPath
    # Which of the entry's target forms the opening matched.  An entry that
    # covers several narrators has a primary ``target_normalised`` that is often
    # not the one that matched, so recording only that would misreport the
    # evidence.
    matched_form: str


@dataclass(frozen=True)
class OpeningMatch:
    method: str
    candidates: list[OpeningCandidate]


@dataclass
class MashyakhaImportStats:
    created: int = 0
    updated: int = 0
    parsed: int = 0
    topic_entries: int = 0
    needs_review: int = 0


@dataclass
class MashyakhaExpansionStats:
    created: int = 0
    updated: int = 0
    removed: int = 0
    proposed: int = 0
    needs_review: int = 0


def _normalise(value: str | None) -> str:
    return normalise_arabic_persian(clean_ws(value or ""))


def _parseable_text(value: str) -> str:
    """Diacritic-free working copy of the printed entry.

    The pristine Arabic stays in ``MashyakhaPath.source_text_ar``; matching the
    formula through shadda and madda marks is not worth the regex.
    """
    return clean_ws(_ZERO_WIDTH_RE.sub("", strip_diacritics(value or "")))


def _without_path_commentary(value: str) -> str:
    return clean_ws(_PATH_COMMENTARY_RE.sub("", value).rstrip(".؛،,"))


def _target_forms(target: str) -> list[str]:
    """Every narrator form one Mashyakha entry vouches for, in printed order."""
    forms: list[str] = []
    for alternative in _TARGET_ALTERNATIVES_RE.split(target):
        for step in _TARGET_STEP_RE.split(clean_ws(alternative)):
            step = clean_ws(_TARGET_GLOSS_RE.sub("", step).strip("،, "))
            if step and step not in forms:
                forms.append(step)
    return forms


def parse_faqih_mashyakha_path(source_text_ar: str) -> ParsedMashyakhaPath:
    """Conservatively extract target forms and path nodes from one entry.

    The full Arabic entry remains stored as the source witness.  An entry keyed
    on a subject rather than a narrator is returned as ``topic_entry``; one that
    matches no known construction is returned as ``needs_review``.  Neither is
    forced into a guessed path.
    """
    text = _parseable_text(source_text_ar)
    if _TOPIC_ENTRY_RE.search(text):
        return ParsedMashyakhaPath(
            target_raw=None,
            target_normalised=None,
            path_nodes=[],
            review_status="topic_entry",
            notes="The entry is keyed on a subject, not on a narrator.",
        )

    match = _TARGET_AND_PATH_RE.search(text)
    if match is None:
        return ParsedMashyakhaPath(
            target_raw=None,
            target_normalised=None,
            path_nodes=[],
            review_status="needs_review",
            notes="No standard Mashyakha target/path construction found.",
        )

    target_raw = clean_ws(match.group("target").strip("،, "))
    forms = _target_forms(target_raw)
    path_raw = _without_path_commentary(_PATH_PREFIX_RE.sub("", match.group("path")))
    nodes = [
        clean_ws(part.strip("،, "))
        for part in _NARRATION_SPLIT_RE.split(path_raw)
        if clean_ws(part.strip("،, "))
    ]
    if not nodes or not forms:
        return ParsedMashyakhaPath(
            target_raw=target_raw or None,
            target_normalised=_normalise(target_raw) or None,
            path_nodes=[],
            review_status="needs_review",
            notes="The source names a target but no path nodes were parsed.",
        )
    return ParsedMashyakhaPath(
        target_raw=target_raw,
        target_normalised=_normalise(forms[0]),
        path_nodes=nodes,
        review_status="parsed",
        target_forms=[_normalise(form) for form in forms],
    )


@lru_cache(maxsize=8192)
def canonical_opening(value: str | None) -> str:
    """Strip what a chain opening carries but a Mashyakha target never does.

    Prepositions the tokenizer kept, a trailing honorific or ``بإسناده``, and
    the kunya's grammatical case.  All of this is orthography, not identity, so
    removing it is not a relaxed threshold.
    """
    text = clean_ws(_OPENING_PUNCT_RE.sub(" ", value or "")).strip(" ،,-")
    previous = None
    while previous != text:
        previous = text
        text = _OPENING_LEAD_RE.sub("", text)
        text = _OPENING_TRAIL_RE.sub("", text)
        text = text.strip(" ،,-")
    return clean_ws(_KUNYA_CASE_RE.sub("ابی", text))


@lru_cache(maxsize=8192)
def opening_key(value: str | None) -> tuple[str, ...]:
    """Word key used for comparison only; ``ابن`` and ``بن`` are one word."""
    return tuple("بن" if word == "ابن" else word for word in canonical_opening(value).split())


def _is_ordered_subset(needle: tuple[str, ...], haystack: tuple[str, ...]) -> bool:
    remaining = iter(haystack)
    return all(word in remaining for word in needle)


def _contains_run(haystack: tuple[str, ...], needle: tuple[str, ...], *, start: int) -> bool:
    return any(
        haystack[index : index + len(needle)] == needle
        for index in range(start, len(haystack) - len(needle) + 1)
    )


def classify_opening(
    opening_normalised: str | None,
    paths_by_form: dict[str, list[MashyakhaPath]],
) -> OpeningMatch | None:
    """Rank the Mashyakha witnesses that could supply this opening's preface.

    Returns ``None`` when the Mashyakha names no candidate at all — which is a
    real and expected answer, because al-Saduq did not write an entry for every
    narrator he abbreviates.
    """
    if opening_normalised and opening_normalised in paths_by_form:
        return OpeningMatch(MATCH_EXACT, _paths_for([opening_normalised], paths_by_form))

    key = opening_key(opening_normalised)
    if not key:
        return None

    keys_by_form = {form: opening_key(form) for form in paths_by_form}
    canonical = sorted(form for form, form_key in keys_by_form.items() if form_key == key)
    if canonical:
        return OpeningMatch(MATCH_CANONICAL, _paths_for(canonical, paths_by_form))

    # An opening that is the *opening* of a longer target agrees on the ism and
    # contradicts nothing; the target merely adds a patronymic or nisba.
    extensions: list[str] = []
    # An opening that appears further inside a target shares only its tail —
    # "ابن محبوب" against "محمد بن علي بن محبوب" is a different man.
    interior: list[str] = []
    # "عمار الساباطي" for "عمار بن موسى الساباطي": ism and nisba both agree and
    # only the patronymic is elided.
    elisions: list[str] = []
    for form, form_key in keys_by_form.items():
        if len(key) >= len(form_key):
            continue
        if form_key[: len(key)] == key:
            extensions.append(form)
        elif _contains_run(form_key, key, start=1):
            interior.append(form)
        elif (
            len(key) >= 2
            and form_key[0] == key[0]
            and form_key[-1] == key[-1]
            and _is_ordered_subset(key, form_key)
        ):
            elisions.append(form)

    unscoped_extensions = [
        form for form in extensions if not _TARGET_SUBJECT_SCOPE_RE.search(form)
    ]
    unscoped_elisions = [form for form in elisions if not _TARGET_SUBJECT_SCOPE_RE.search(form)]

    # "ابن X" declares that the ism is elided, so a target merely ending in
    # "بن X" is not evidence that it is *this* Ibn X — the Mashyakha roster is
    # not the whole tradition, and the intended man may simply be absent.
    declares_elided_ism = key[0] == "بن"
    if len(unscoped_extensions) == 1 and not declares_elided_ism:
        return OpeningMatch(MATCH_NAME_EXTENSION, _paths_for(unscoped_extensions, paths_by_form))
    if not unscoped_extensions and len(unscoped_elisions) == 1:
        return OpeningMatch(MATCH_ISM_NISBA_ELISION, _paths_for(unscoped_elisions, paths_by_form))

    candidates = sorted(set(extensions) | set(interior) | set(elisions))
    if not candidates:
        return None
    return OpeningMatch(MATCH_PARTIAL_CANDIDATE, _paths_for(candidates, paths_by_form))


def _paths_for(
    forms: list[str], paths_by_form: dict[str, list[MashyakhaPath]]
) -> list[OpeningCandidate]:
    seen: dict[int, OpeningCandidate] = {}
    for form in forms:
        for path in paths_by_form.get(form, []):
            seen.setdefault(path.id, OpeningCandidate(path=path, matched_form=form))
    return [seen[path_id] for path_id in sorted(seen)]


def crawl_faqih_mashyakha(
    *,
    delay_seconds: float = 0.25,
    timeout_seconds: float = 30.0,
) -> list[MashyakhaSourceEntry]:
    """Fetch the public Thaqalayn Mashyakha volume with robots enforcement."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
        robots = client.get(ROBOTS_URL)
        robots.raise_for_status()
        if re.search(r"(?im)^Disallow:\s*/\s*$", robots.text):
            raise RuntimeError("Thaqalayn robots.txt disallows crawling")

        book_url = f"{BASE_URL}/book/{FAQIH_MASHYAKHA_REMOTE_BOOK_ID}"
        book_response = client.get(book_url)
        book_response.raise_for_status()
        chapter_paths = parse_book_chapter_paths(
            book_response.text,
            volume=5,
            remote_book_id=FAQIH_MASHYAKHA_REMOTE_BOOK_ID,
        )
        if len(chapter_paths) < 200:
            raise RuntimeError(
                f"Expected the complete Mashyakha, found only {len(chapter_paths)} chapter paths"
            )

        entries: list[MashyakhaSourceEntry] = []
        for index, chapter_path in enumerate(chapter_paths):
            if index:
                time.sleep(delay_seconds)
            response = client.get(f"{BASE_URL}{chapter_path}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            article = soup.find("article")
            arabic = article.find(attrs={"dir": "rtl", "lang": "ar"}) if article else None
            if arabic is None:
                raise RuntimeError(f"No Arabic Mashyakha text on {chapter_path}")
            match = re.fullmatch(r"/chapter/38/1/(\d+)", chapter_path)
            if match is None:
                raise RuntimeError(f"Unexpected Mashyakha chapter path: {chapter_path}")
            entries.append(
                MashyakhaSourceEntry(
                    source_chapter=int(match.group(1)),
                    source_hadith_number=None,
                    source_url=f"{BASE_URL}{chapter_path}",
                    source_text_ar=clean_ws(arabic.get_text(" ", strip=True)),
                )
            )
    return entries


def write_mashyakha_snapshot(entries: list[MashyakhaSourceEntry], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "faqih-mashyakha-snapshot-v1",
        "source_key": FAQIH_MASHYAKHA_SOURCE_KEY,
        "source_book_id": FAQIH_SOURCE_BOOK_ID,
        "entries": [asdict(entry) for entry in entries],
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def load_mashyakha_snapshot(path: str | Path) -> list[MashyakhaSourceEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "faqih-mashyakha-snapshot-v1":
        raise ValueError("Unsupported Mashyakha snapshot schema")
    if payload.get("source_key") != FAQIH_MASHYAKHA_SOURCE_KEY:
        raise ValueError("Snapshot is not the Faqih Thaqalayn Mashyakha")
    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) < 200:
        raise ValueError("Snapshot is incomplete: expected at least 200 Mashyakha entries")
    return [MashyakhaSourceEntry(**entry) for entry in entries]


def import_faqih_mashyakha_paths(
    db: Session,
    entries: list[MashyakhaSourceEntry],
) -> MashyakhaImportStats:
    """Idempotently import source witnesses without touching report chains."""
    stats = MashyakhaImportStats()
    now = dt.datetime.now(dt.timezone.utc)
    for entry in entries:
        parsed = parse_faqih_mashyakha_path(entry.source_text_ar)
        existing = db.scalar(
            select(MashyakhaPath).where(
                MashyakhaPath.source_key == FAQIH_MASHYAKHA_SOURCE_KEY,
                MashyakhaPath.source_chapter == entry.source_chapter,
            )
        )
        values: dict[str, Any] = {
            "source_book_id": FAQIH_SOURCE_BOOK_ID,
            "source_key": FAQIH_MASHYAKHA_SOURCE_KEY,
            "source_chapter": entry.source_chapter,
            "source_hadith_number": entry.source_hadith_number,
            "source_url": entry.source_url,
            "target_raw": parsed.target_raw,
            "target_normalised": parsed.target_normalised,
            "target_forms_json": parsed.target_forms or None,
            "source_text_ar": clean_ws(entry.source_text_ar),
            "source_text_en": clean_ws(entry.source_text_en) or None,
            "source_sha256": sha256_text(entry.source_text_ar),
            "parsed_path_json": parsed.path_nodes or None,
            "parser_version": MASHYAKHA_PARSER_VERSION,
            "review_status": parsed.review_status,
            "notes": parsed.notes,
            "updated_at": now,
        }
        if existing is None:
            db.add(MashyakhaPath(created_at=now, **values))
            stats.created += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            stats.updated += 1
        if parsed.review_status == "parsed":
            stats.parsed += 1
        elif parsed.review_status == "topic_entry":
            stats.topic_entries += 1
        else:
            stats.needs_review += 1
    db.flush()
    return stats


def _parsed_paths_by_target_form(db: Session) -> dict[str, list[MashyakhaPath]]:
    """Index every narrator form the parsed witnesses vouch for."""
    paths_by_form: dict[str, list[MashyakhaPath]] = defaultdict(list)
    for path in db.scalars(
        select(MashyakhaPath)
        .where(
            MashyakhaPath.source_key == FAQIH_MASHYAKHA_SOURCE_KEY,
            MashyakhaPath.review_status == "parsed",
        )
        .order_by(MashyakhaPath.source_chapter)
    ):
        forms = list(path.target_forms_json or [])
        if path.target_normalised and path.target_normalised not in forms:
            forms.insert(0, path.target_normalised)
        for form in forms:
            if form:
                paths_by_form[form].append(path)
    return paths_by_form


def _faqih_mursal_openings(db: Session, book: Book) -> list[tuple[int, str | None, str | None]]:
    return [
        (chain_id, raw, normalised)
        for chain_id, raw, normalised in db.execute(
            select(Chain.id, ChainNode.raw_token, ChainNode.token_normalised)
            .join(Hadith, Hadith.id == Chain.hadith_id)
            .join(ChainNode, ChainNode.chain_id == Chain.id)
            .where(
                Hadith.book_id == book.id,
                Chain.flags.contains("mursal_opening"),
                ChainNode.position == 0,
            )
            .order_by(Chain.id)
        ).all()
    ]


def _require_faqih(db: Session) -> Book:
    book = db.scalar(select(Book).where(Book.source_book_id == FAQIH_SOURCE_BOOK_ID))
    if book is None:
        raise ValueError(f"No Faqih book with source_book_id={FAQIH_SOURCE_BOOK_ID}")
    return book


def materialize_faqih_mashyakha_expansions(db: Session) -> MashyakhaExpansionStats:
    """Create source-linked virtual-preface proposals, ranked by evidence tier.

    A proposal says that a Faqih ``mursal_opening`` chain's first token names a
    narrator for whom this Mashyakha entry supplies a path, and it records which
    tier of evidence says so.  The source path stays in ``MashyakhaPath``; no
    ``ChainNode`` is inserted and no review status on the original chain is
    changed.  A tier that leaves more than one witness standing — or that rests
    on a partial name — is stored as ranked ``needs_review`` candidates.
    """
    book = _require_faqih(db)
    paths_by_form = _parsed_paths_by_target_form(db)

    stats = MashyakhaExpansionStats()
    now = dt.datetime.now(dt.timezone.utc)
    cache: dict[str | None, OpeningMatch | None] = {}
    chain_ids: set[int] = set()
    supported: set[tuple[int, int]] = set()
    for chain_id, opening_raw, opening_normalised in _faqih_mursal_openings(db, book):
        chain_ids.add(chain_id)
        if opening_normalised not in cache:
            cache[opening_normalised] = classify_opening(opening_normalised, paths_by_form)
        match = cache[opening_normalised]
        if match is None:
            continue
        single = match.method in SINGLE_CANDIDATE_METHODS and len(match.candidates) == 1
        proposal_status = "proposed" if single else "needs_review"
        for rank, candidate in enumerate(match.candidates, start=1):
            path = candidate.path
            supported.add((chain_id, path.id))
            evidence = {
                "opening_raw": opening_raw,
                "opening_normalised": opening_normalised,
                "opening_canonical": canonical_opening(opening_normalised),
                "matched_target_form": candidate.matched_form,
                "path_target_raw": path.target_raw,
                "path_target_normalised": path.target_normalised,
                "path_target_forms": list(path.target_forms_json or []),
                "path_source_chapter": path.source_chapter,
                "path_source_sha256": path.source_sha256,
                "candidate_rank": rank,
                "candidate_count": len(match.candidates),
            }
            existing = db.scalar(
                select(MashyakhaExpansion).where(
                    MashyakhaExpansion.chain_id == chain_id,
                    MashyakhaExpansion.mashyakha_path_id == path.id,
                )
            )
            if existing is None:
                db.add(
                    MashyakhaExpansion(
                        chain_id=chain_id,
                        mashyakha_path_id=path.id,
                        match_method=match.method,
                        match_evidence_json=evidence,
                        review_status=proposal_status,
                        created_at=now,
                        updated_at=now,
                    )
                )
                stats.created += 1
            else:
                existing.match_method = match.method
                existing.match_evidence_json = evidence
                if existing.review_status in {"proposed", "needs_review"}:
                    existing.review_status = proposal_status
                existing.updated_at = now
                stats.updated += 1
            if proposal_status == "proposed":
                stats.proposed += 1
            else:
                stats.needs_review += 1

    # A proposal the current rules no longer make must not survive a re-run, or
    # the table accumulates evidence no code will defend.  Rows a human has
    # already ruled on are decisions, not output, and are kept.
    if chain_ids:
        for expansion in db.scalars(
            select(MashyakhaExpansion).where(
                MashyakhaExpansion.chain_id.in_(chain_ids),
                MashyakhaExpansion.review_status.in_(("proposed", "needs_review")),
            )
        ):
            if (expansion.chain_id, expansion.mashyakha_path_id) not in supported:
                db.delete(expansion)
                stats.removed += 1
    db.flush()
    return stats


def audit_faqih_mashyakha_coverage(db: Session) -> dict[str, int]:
    """Measure how far the Mashyakha reaches Faqih's abbreviated openings.

    A coverage hit says only that a source witness names this narrator at the
    recorded evidence tier.  It does not claim the source path has been grafted
    into the report or that its identities have been resolved.
    """
    book = _require_faqih(db)
    paths_by_form = _parsed_paths_by_target_form(db)
    openings = [
        normalised for _, _, normalised in _faqih_mursal_openings(db, book) if normalised
    ]

    cache: dict[str, OpeningMatch | None] = {}
    tiers: dict[str, int] = {method: 0 for method in (*SINGLE_CANDIDATE_METHODS, MATCH_PARTIAL_CANDIDATE)}
    without_witness = 0
    for opening in openings:
        if opening not in cache:
            cache[opening] = classify_opening(opening, paths_by_form)
        match = cache[opening]
        if match is None:
            without_witness += 1
        else:
            tiers[match.method] += 1
    single_candidate = sum(tiers[method] for method in SINGLE_CANDIDATE_METHODS)

    def count(model: Any, *where: Any) -> int:
        return db.scalar(select(func.count()).select_from(model).where(*where)) or 0

    source_scope = (MashyakhaPath.source_key == FAQIH_MASHYAKHA_SOURCE_KEY,)
    return {
        "source_paths": count(MashyakhaPath, *source_scope),
        "parsed_paths": count(MashyakhaPath, *source_scope, MashyakhaPath.review_status == "parsed"),
        "topic_entry_paths": count(
            MashyakhaPath, *source_scope, MashyakhaPath.review_status == "topic_entry"
        ),
        "needs_review_paths": count(
            MashyakhaPath, *source_scope, MashyakhaPath.review_status == "needs_review"
        ),
        "target_forms": len(paths_by_form),
        "mursal_openings": len(openings),
        **{f"openings_{method}": tiers[method] for method in tiers},
        "openings_with_single_candidate": single_candidate,
        "openings_with_any_witness": single_candidate + tiers[MATCH_PARTIAL_CANDIDATE],
        "openings_without_source_witness": without_witness,
        "expansion_proposals": count(MashyakhaExpansion),
        "expansion_proposed": count(
            MashyakhaExpansion, MashyakhaExpansion.review_status == "proposed"
        ),
        "expansion_needs_review": count(
            MashyakhaExpansion, MashyakhaExpansion.review_status == "needs_review"
        ),
    }
