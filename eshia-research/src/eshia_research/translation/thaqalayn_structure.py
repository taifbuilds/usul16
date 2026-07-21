"""Import Thaqalayn kitab/chapter structure and hadith gradings for Al-Kafi.

Two independent, read-additive passes over ``thaqalayn_structure_maps`` and
``hadith_gradings``. Neither touches ``hadiths`` or existing translation rows;
both are droppable/rebuildable. See ``thaqalayn_importer.py`` for the sibling
English-text import, which depends on the mapping rows written here.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Hadith,
    HadithGrading,
    HadithTranslation,
    ThaqalaynStructureMap,
    TranslationAttempt,
    TranslationJob,
    TranslationJobItem,
    TranslationSegment,
)
from eshia_research.translation import QA_VERSION
from eshia_research.translation.qa import assess_translation
from eshia_research.translation.text import (
    FOOTNOTE_MARKER_RE,
    clean_ws,
    normalise_digits,
    number_tokens,
    sha256_text,
    source_norm,
)
from eshia_research.translation.thaqalayn_importer import (
    IMPORT_BLOCKING_QA_CODES,
    KNOWN_HUMAN_TRANSLATORS,
    MIN_MATCH_SCORE,
    THAQALAYN_AL_KAFI_BOOK_IDS,
    ThaqalaynRecord,
    WINDOW_BACK,
    WINDOW_FORWARD,
    match_norm,
    match_score_parts,
    match_words,
    parse_record,
    source_import_publication_flags,
)

MATCHER_VERSION = "thaqalayn_struct_v1"
LIVE_TRANSLATION_VERSION = "thaqalayn_live_v1"
LIVE_JOB_KEY = "alkafi-thaqalayn-live-v1-import-v1"
LIVE_PROVIDER = "thaqalayn-api"
LIVE_QA_VERSION = f"{QA_VERSION}+thaqalayn_live_v1"
_URL_INDEX_RE = re.compile(r"/hadith/\d+/\d+/\d+/(\d+)")
_PREFIX_RE = re.compile(r"^\s*(\d+)\s*[.]")


def load_snapshot_records(snapshot_dir: str | Path) -> dict[int, list[ThaqalaynRecord]]:
    """Load the tq_v{1..8}.json API snapshots into ThaqalaynRecord objects.

    Lets structure/English imports run reproducibly from a pinned snapshot
    instead of hitting the live API each time.
    """
    base = Path(snapshot_dir)
    by_volume: dict[int, list[ThaqalaynRecord]] = {}
    for volume in THAQALAYN_AL_KAFI_BOOK_IDS:
        path = base / f"tq_v{volume}.json"
        if not path.exists():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        by_volume[volume] = [parse_record(row) for row in rows]
    return by_volume


@dataclass
class StructureStats:
    fetched: int = 0
    local_visible: int = 0
    matched_provenance_rekey: int = 0
    matched_windowed_arabic: int = 0
    interpolated: int = 0
    unmapped: int = 0
    numbering_flagged: int = 0
    gradings_rows: int = 0
    gradings_hadiths: int = 0
    by_volume: dict[int, dict[str, int]] = field(default_factory=dict)
    manifest: list[dict[str, Any]] = field(default_factory=list)


def _url_index(url: str | None) -> int | None:
    if not url:
        return None
    m = _URL_INDEX_RE.search(url)
    return int(m.group(1)) if m else None


def _prefix_number(english_text: str | None) -> int | None:
    if not english_text:
        return None
    m = _PREFIX_RE.match(english_text)
    return int(m.group(1)) if m else None


def _grader_key(author_name_en: str | None) -> str:
    name = (author_name_en or "").casefold()
    if "majlisi" in name:
        return "majlisi"
    if "behbudi" in name or "behbud" in name:
        return "behbudi"
    if "mohseni" in name or "mohsen" in name:
        return "mohseni"
    slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "unknown"
    return f"other:{slug}"


def build_structure_matches(
    db: Session,
    *,
    source_book_id: str,
    remote_by_volume: dict[int, list[ThaqalaynRecord]],
    min_score: float = MIN_MATCH_SCORE,
) -> tuple[list[dict[str, Any]], StructureStats]:
    """Match local Al-Kafi hadiths to remote Thaqalayn rows for structure only.

    Priority: (1) existing translation provenance re-key, Arabic-reverified;
    (2) windowed Arabic matcher over the remainder. Returns row dicts ready to
    upsert into ThaqalaynStructureMap, plus interpolation for edition gaps.
    """
    from eshia_research.models import HadithTranslation
    from eshia_research.translation import TRANSLATION_VERSION

    book = db.execute(select(Book).where(Book.source_book_id == source_book_id)).scalar_one()
    hadiths = list(
        db.execute(
            select(Hadith)
            .where(Hadith.book_id == book.id, Hadith.review_status != "rejected_non_hadith_fragment")
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    stats = StructureStats(
        fetched=sum(len(v) for v in remote_by_volume.values()), local_visible=len(hadiths)
    )

    remote_by_id: dict[tuple[int, int], ThaqalaynRecord] = {}
    for vol, rows in remote_by_volume.items():
        for r in rows:
            remote_by_id[(vol, r.id)] = r

    existing_prov: dict[int, HadithTranslation] = {}
    for t in db.execute(
        select(HadithTranslation).where(
            HadithTranslation.language == "en",
            HadithTranslation.translation_version == TRANSLATION_VERSION,
        )
    ).scalars():
        existing_prov.setdefault(t.hadith_id, t)

    results: list[dict[str, Any]] = []
    claimed: set[tuple[int, int]] = set()
    matched_hadith_ids: set[int] = set()

    def record_row(hadith: Hadith, remote: ThaqalaynRecord, score: float | None, method: str) -> None:
        url_idx = _url_index(remote.url)
        prefix = _prefix_number(remote.english_text)
        flags: list[dict[str, str]] = []
        if prefix is not None and url_idx is not None and prefix != url_idx:
            flags.append({"code": "prefix_disagrees_with_url_index", "prefix": str(prefix), "url_index": str(url_idx)})
        row = {
            "hadith_id": hadith.id,
            "public_id": hadith.public_id,
            "volume": remote.volume,
            "remote_book_id": remote.book_id,
            "remote_id": remote.id,
            "kitab_id": str((remote.raw or {}).get("categoryId") or ""),
            "kitab_name_en": remote.category or "",
            "chapter_id": int((remote.raw or {}).get("chapterInCategoryId") or 0),
            "chapter_name_en": remote.chapter or "",
            "number_in_chapter": url_idx,
            "number_prefix_en": prefix,
            "position_computed": None,
            "numbering_flags": flags or None,
            "thaqalayn_url": remote.url,
            "mapping_status": "matched",
            "match_method": method,
            "match_score": score,
            "remote_arabic_sha256": sha256_text(remote.arabic_text),
            "raw_ref_json": {"gradingsFull": (remote.raw or {}).get("gradingsFull")},
        }
        results.append(row)
        claimed.add((remote.volume, remote.id))
        matched_hadith_ids.add(hadith.id)
        stats.by_volume.setdefault(remote.volume, {"matched": 0, "interpolated": 0, "unmapped": 0})
        stats.by_volume[remote.volume]["matched"] += 1
        if flags:
            stats.numbering_flagged += 1

    # Pass 1: provenance re-key, Arabic-reverified.
    for hadith in hadiths:
        t = existing_prov.get(hadith.id)
        if t is None:
            continue
        prov = t.provenance_json or {}
        tid = prov.get("thaqalayn_id")
        vol = prov.get("volume")
        if not isinstance(tid, int) or not isinstance(vol, int):
            continue
        remote = remote_by_id.get((vol, tid))
        if remote is None:
            continue
        if (vol, tid) in claimed:
            continue
        eng_match = sha256_text(remote.english_text) == prov.get("source_english_sha256")
        arabic_score = match_score_parts(
            local_full=match_norm(hadith.full_text_raw),
            local_matn=match_norm(hadith.matn_raw),
            local_full_words=match_words(hadith.full_text_raw),
            local_matn_words=match_words(hadith.matn_raw),
            remote=remote,
        )
        if eng_match or arabic_score >= min_score:
            record_row(hadith, remote, arabic_score, "provenance_rekey")
            stats.matched_provenance_rekey += 1

    # Pass 2: windowed Arabic matcher over the remainder, per volume.
    for vol, remote_rows in remote_by_volume.items():
        local_vol = [h for h in hadiths if h.volume_start == vol and h.id not in matched_hadith_ids]
        cursor = 0
        remote_indexes = {id(r): i for i, r in enumerate(remote_rows)}
        for hadith in local_vol:
            start = max(0, cursor - WINDOW_BACK)
            end = min(len(remote_rows), cursor + WINDOW_FORWARD)
            candidates = [r for r in remote_rows[start:end] if (vol, r.id) not in claimed]
            if not candidates:
                continue
            local_full = match_norm(hadith.full_text_raw)
            local_matn = match_norm(hadith.matn_raw)
            local_full_words = match_words(hadith.full_text_raw)
            local_matn_words = match_words(hadith.matn_raw)
            scored = [
                (
                    match_score_parts(
                        local_full=local_full, local_matn=local_matn,
                        local_full_words=local_full_words, local_matn_words=local_matn_words,
                        remote=r,
                    ),
                    r,
                )
                for r in candidates
            ]
            scored = [(s, r) for s, r in scored if s >= min_score]
            if not scored:
                continue
            score, best = max(
                scored,
                key=lambda item: (item[0], -abs(remote_indexes[id(item[1])] - cursor)),
            )
            cursor = max(cursor, remote_indexes[id(best)] + 1)
            record_row(hadith, best, score, "windowed_arabic")
            stats.matched_windowed_arabic += 1

    # Pass 3: interpolation for edition gaps between two matched neighbors in
    # the same (kitab_id, chapter_id), and explicit unmapped otherwise.
    by_hadith_id = {r["hadith_id"]: r for r in results}
    seq_index = {h.id: i for i, h in enumerate(hadiths)}
    matched_seq = sorted(seq_index[hid] for hid in by_hadith_id)
    for i, hadith in enumerate(hadiths):
        if hadith.id in by_hadith_id:
            continue
        prev_row = next(
            (by_hadith_id[hadiths[j].id] for j in range(i - 1, -1, -1) if hadiths[j].id in by_hadith_id),
            None,
        )
        next_row = next(
            (by_hadith_id[hadiths[j].id] for j in range(i + 1, len(hadiths)) if hadiths[j].id in by_hadith_id),
            None,
        )
        vol = hadith.volume_start or 0
        if (
            prev_row and next_row
            and prev_row["kitab_id"] == next_row["kitab_id"]
            and prev_row["chapter_id"] == next_row["chapter_id"]
        ):
            row = {
                "hadith_id": hadith.id,
                "public_id": hadith.public_id,
                "volume": vol,
                "remote_book_id": None,
                "remote_id": None,
                "kitab_id": prev_row["kitab_id"],
                "kitab_name_en": prev_row["kitab_name_en"],
                "chapter_id": prev_row["chapter_id"],
                "chapter_name_en": prev_row["chapter_name_en"],
                "number_in_chapter": None,
                "number_prefix_en": None,
                "position_computed": None,
                "numbering_flags": None,
                "thaqalayn_url": None,
                "mapping_status": "interpolated_unmapped",
                "match_method": "interpolated",
                "match_score": None,
                "remote_arabic_sha256": None,
                "raw_ref_json": None,
            }
            results.append(row)
            stats.interpolated += 1
            stats.by_volume.setdefault(vol, {"matched": 0, "interpolated": 0, "unmapped": 0})
            stats.by_volume[vol]["interpolated"] += 1
        else:
            stats.unmapped += 1
            stats.by_volume.setdefault(vol, {"matched": 0, "interpolated": 0, "unmapped": 0})
            stats.by_volume[vol]["unmapped"] += 1

    stats.manifest = [
        {
            "public_id": r["public_id"],
            "mapping_status": r["mapping_status"],
            "match_method": r["match_method"],
            "match_score": r["match_score"],
            "kitab_name_en": r["kitab_name_en"],
            "chapter_name_en": r["chapter_name_en"],
            "number_in_chapter": r["number_in_chapter"],
            "numbering_flags": r["numbering_flags"],
        }
        for r in results
    ]
    return results, stats


def apply_structure_matches(db: Session, rows: list[dict[str, Any]]) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    written = 0
    for row in rows:
        existing = db.execute(
            select(ThaqalaynStructureMap).where(
                ThaqalaynStructureMap.hadith_id == row["hadith_id"],
                ThaqalaynStructureMap.source == "thaqalayn-api",
            )
        ).scalar_one_or_none()
        values = {k: v for k, v in row.items() if k not in ("hadith_id", "public_id")}
        values["updated_at"] = now
        if existing is None:
            db.add(
                ThaqalaynStructureMap(
                    hadith_id=row["hadith_id"],
                    source="thaqalayn-api",
                    matcher_version=MATCHER_VERSION,
                    created_at=now,
                    **values,
                )
            )
        else:
            for k, v in values.items():
                setattr(existing, k, v)
            existing.matcher_version = MATCHER_VERSION
        written += 1
    db.flush()
    return written


def import_gradings(
    db: Session,
    *,
    source_book_id: str,
    remote_by_volume: dict[int, list[ThaqalaynRecord]],
    structure_matches: list[dict[str, Any]],
) -> StructureStats:
    """Replace-per-hadith import of gradingsFull, keyed by the structure map.

    Only matched rows carry gradings; interpolated/unmapped rows have no
    remote counterpart to grade.
    """
    now = dt.datetime.now(dt.timezone.utc)
    remote_by_id: dict[tuple[int, int], ThaqalaynRecord] = {}
    for vol, rows in remote_by_volume.items():
        for r in rows:
            remote_by_id[(vol, r.id)] = r

    stats = StructureStats()
    for row in structure_matches:
        if row["mapping_status"] != "matched" or row["remote_id"] is None:
            continue
        remote = remote_by_id.get((row["volume"], row["remote_id"]))
        if remote is None:
            continue
        gradings_full = (remote.raw or {}).get("gradingsFull") or []
        if not isinstance(gradings_full, list) or not gradings_full:
            continue
        db.query(HadithGrading).filter(
            HadithGrading.hadith_id == row["hadith_id"],
            HadithGrading.source == "thaqalayn-api",
        ).delete(synchronize_session=False)
        for i, entry in enumerate(gradings_full):
            if not isinstance(entry, dict):
                continue
            author = entry.get("author") or {}
            author_name = (author.get("name_en") or "").strip()
            grade_ar = (entry.get("grade_ar") or "").strip()
            if not grade_ar and not author_name:
                continue
            db.add(
                HadithGrading(
                    hadith_id=row["hadith_id"],
                    source="thaqalayn-api",
                    grader_key=_grader_key(author_name),
                    author_name_en=author_name or "Unknown",
                    grade_ar=grade_ar or "",
                    grade_en=(entry.get("grade_en") or None),
                    reference_en=(entry.get("reference_en") or None),
                    display_order=i,
                    raw_json=entry,
                    created_at=now,
                    updated_at=now,
                )
            )
        stats.gradings_rows += len(gradings_full)
        stats.gradings_hadiths += 1
    db.flush()
    return stats


@dataclass
class LiveEnglishStats:
    considered: int = 0
    imported: int = 0
    skipped_qa: int = 0
    skipped_low_confidence: int = 0
    skipped_unknown_translator: int = 0
    number_prefix_downgraded: int = 0
    errors: list[str] = field(default_factory=list)
    by_volume: dict[int, dict[str, int]] = field(default_factory=dict)
    manifest: list[dict[str, Any]] = field(default_factory=list)


def _footnote_marker_multiset(text: str | None) -> Counter:
    return Counter(
        normalise_digits(m.group(1)) for m in FOOTNOTE_MARKER_RE.finditer(text or "")
    )


def _reclassify_number_apparatus(
    flags: list[dict[str, str]],
    *,
    qa_text: str,
    matn_raw: str,
    number_in_chapter: int | None,
    used_full_fallback: bool,
) -> tuple[list[dict[str, str]], str | None]:
    """Reclassify a number_mismatch when the difference is pure edition apparatus.

    Two apparatus sources make the digit-only number check fire without any real
    numeric disagreement:

    1. eShia footnote markers ("[2]", "[3][4]") sit inside the local Arabic matn
       and are counted as numbers; the clean external English omits them.
    2. When the matn split is absent and QA runs on the full English, that text
       begins with the report's own chapter index ("1. ..."), absent from the
       Arabic.

    Remove exactly those two apparatus contributions. Only when the remaining
    number multisets then agree is the flag reclassified to an info diagnostic;
    every other numeric difference stays blocking. This mirrors the existing
    missing_placeholder -> external_source_footnote_marker_difference handling
    and never clears a genuine content-number conflict.
    """
    if not any(f.get("code") == "number_mismatch" for f in flags):
        return flags, None

    source_content = Counter(number_tokens(matn_raw)) - _footnote_marker_multiset(matn_raw)
    trans_text = qa_text or ""
    reason = "footnote_marker"
    if used_full_fallback and number_in_chapter is not None:
        m = _PREFIX_RE.match(trans_text)
        if m and int(m.group(1)) == number_in_chapter:
            trans_text = _PREFIX_RE.sub("", trans_text, count=1)
            reason = "leading_index+footnote_marker"
    trans_content = Counter(number_tokens(trans_text))

    if source_content != trans_content:
        return flags, None

    downgraded: list[dict[str, str]] = []
    for f in flags:
        if f.get("code") == "number_mismatch":
            downgraded.append(
                {
                    "code": "external_source_number_apparatus",
                    "severity": "info",
                    "detail": (
                        "The only numeric differences are edition apparatus "
                        "(eShia footnote markers and/or the report's own chapter "
                        "index); all content numbers agree."
                    ),
                    **({"original_diagnostic": f["detail"]} if f.get("detail") else {}),
                }
            )
        else:
            downgraded.append(dict(f))
    return downgraded, reason


def import_live_english(
    db: Session,
    *,
    source_book_id: str,
    remote_by_volume: dict[int, list[ThaqalaynRecord]],
    dry_run: bool = True,
    min_score: float = MIN_MATCH_SCORE,
) -> LiveEnglishStats:
    """Import the current Thaqalayn English verbatim for matched hadiths.

    Writes new ``translation_version="thaqalayn_live_v1"`` rows; never touches
    ``matn_en_v1`` history. ``full_translation`` holds the full English
    (numbered isnad + matn, exactly as displayed upstream); ``matn_translation``
    holds the matn-only English (or the full text where the matn split is
    absent). Only rows with a matched structure map are considered; QA-failing
    rows are skipped, not written, so unmatched/failing hadiths keep serving
    their existing translation.
    """
    stats = LiveEnglishStats()
    remote_by_id: dict[tuple[int, int], ThaqalaynRecord] = {}
    for vol, rows in remote_by_volume.items():
        for r in rows:
            remote_by_id[(vol, r.id)] = r

    book = db.execute(select(Book).where(Book.source_book_id == source_book_id)).scalar_one()
    maps = list(
        db.execute(
            select(ThaqalaynStructureMap)
            .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
            .where(
                Hadith.book_id == book.id,
                ThaqalaynStructureMap.mapping_status == "matched",
                ThaqalaynStructureMap.source == "thaqalayn-api",
            )
        ).scalars()
    )
    stats.considered = len(maps)

    now = dt.datetime.now(dt.timezone.utc)
    job = None
    next_item_index = 1
    if not dry_run:
        job = _get_or_create_live_job(db, source_book_id=source_book_id, now=now)
        next_item_index = len(job.items) + 1

    for smap in maps:
        remote = remote_by_id.get((smap.volume, smap.remote_id)) if smap.remote_id else None
        if remote is None:
            continue
        hadith = db.get(Hadith, smap.hadith_id)
        if hadith is None:
            stats.errors.append(f"Hadith id {smap.hadith_id} disappeared during import")
            continue

        english_full = clean_ws(remote.english_text)
        matn_english = clean_ws(remote.thaqalayn_matn or remote.english_text)
        sanad_english = remote.thaqalayn_sanad
        translator_key = clean_ws(remote.translator).casefold()

        vol_stats = stats.by_volume.setdefault(
            smap.volume, {"imported": 0, "skipped_qa": 0, "skipped_low_confidence": 0}
        )

        if translator_key not in KNOWN_HUMAN_TRANSLATORS:
            stats.skipped_unknown_translator += 1
            continue

        score = smap.match_score if smap.match_score is not None else 1.0
        if score < min_score:
            stats.skipped_low_confidence += 1
            vol_stats["skipped_low_confidence"] += 1
            continue

        # QA on the matn-to-matn pair; fall back to full English (which carries
        # the leading index + isnad) only when the matn split is absent.
        used_full_fallback = not clean_ws(remote.thaqalayn_matn)
        qa_text = matn_english
        qa = assess_translation(hadith.matn_raw, qa_text)
        flags = [f.__dict__ if hasattr(f, "__dict__") else dict(f) for f in qa.flags]
        flags, downgrade_reason = _reclassify_number_apparatus(
            flags,
            qa_text=qa_text,
            matn_raw=hadith.matn_raw,
            number_in_chapter=smap.number_in_chapter,
            used_full_fallback=used_full_fallback,
        )
        if downgrade_reason:
            stats.number_prefix_downgraded += 1

        blocking = any(f.get("code") in IMPORT_BLOCKING_QA_CODES for f in flags)
        publishable = not blocking and bool(matn_english)
        if not publishable:
            stats.skipped_qa += 1
            vol_stats["skipped_qa"] += 1
            stats.manifest.append(
                {
                    "public_id": hadith.public_id,
                    "outcome": "skipped_qa",
                    "flags": [f.get("code") for f in flags],
                }
            )
            continue

        if not dry_run:
            translation = _upsert_live_translation(
                db,
                hadith=hadith,
                smap=smap,
                remote=remote,
                english_full=english_full,
                matn_english=matn_english,
                sanad_english=sanad_english,
                score=score,
                flags=flags,
                qa_risk_level=qa.risk_level,
                now=now,
            )
            segment = _upsert_live_segment(
                db,
                translation=translation,
                hadith=hadith,
                matn_english=matn_english,
                remote=remote,
                score=score,
                flags=flags,
                now=now,
            )
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
                    provider=LIVE_PROVIDER,
                    model=KNOWN_HUMAN_TRANSLATORS[translator_key],
                    status="completed",
                    request_json={"url": remote.url, "thaqalayn_id": remote.id, "volume": smap.volume},
                    response_json={
                        "match_score": score,
                        "match_method": smap.match_method,
                        "qa_flags": flags,
                        "source_english_sha256": sha256_text(english_full),
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
        vol_stats["imported"] += 1

    if not dry_run and job is not None:
        job.hadith_count = stats.imported
        job.segment_count = stats.imported
        job.status = "completed"
        job.completed_at = now
        job.updated_at = now
        db.flush()
    return stats


def _get_or_create_live_job(
    db: Session, *, source_book_id: str, now: dt.datetime
) -> TranslationJob:
    job = db.execute(
        select(TranslationJob).where(TranslationJob.job_key == LIVE_JOB_KEY)
    ).scalar_one_or_none()
    if job is not None:
        job.status = "running"
        job.started_at = job.started_at or now
        job.updated_at = now
        return job
    job = TranslationJob(
        job_key=LIVE_JOB_KEY,
        source_book_id=source_book_id,
        language="en",
        status="running",
        provider=LIVE_PROVIDER,
        model="muhammad-sarwar",
        prompt_version=MATCHER_VERSION,
        glossary_version=None,
        scope_json={
            "source": "https://www.thaqalayn-api.net/",
            "book_ids": THAQALAYN_AL_KAFI_BOOK_IDS,
            "translation_version": LIVE_TRANSLATION_VERSION,
        },
        batch_policy_json={"mode": "thaqalayn_live_verbatim"},
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


def _upsert_live_translation(
    db: Session,
    *,
    hadith: Hadith,
    smap: ThaqalaynStructureMap,
    remote: ThaqalaynRecord,
    english_full: str,
    matn_english: str,
    sanad_english: str | None,
    score: float,
    flags: list[dict[str, str]],
    qa_risk_level: str,
    now: dt.datetime,
) -> HadithTranslation:
    translation = db.execute(
        select(HadithTranslation).where(
            HadithTranslation.hadith_id == hadith.id,
            HadithTranslation.language == "en",
            HadithTranslation.translation_version == LIVE_TRANSLATION_VERSION,
        )
    ).scalar_one_or_none()
    values = {
        "source_full_sha256": sha256_text(hadith.full_text_raw),
        "source_isnad_sha256": sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None,
        "source_matn_sha256": sha256_text(hadith.matn_raw),
        "rendered_isnad_en": sanad_english,
        "matn_translation": matn_english,
        "full_translation": english_full,
        "status": "published",
        "risk_level": "green",
        "risk_flags": source_import_publication_flags(flags),
        "provider": LIVE_PROVIDER,
        "model": KNOWN_HUMAN_TRANSLATORS.get(clean_ws(remote.translator).casefold()),
        "prompt_version": MATCHER_VERSION,
        "glossary_version": None,
        "qa_version": LIVE_QA_VERSION,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_estimate_usd": 0.0,
        "provenance_json": {
            "source": "thaqalayn-api",
            "source_url": remote.url,
            "thaqalayn_id": remote.id,
            "volume": smap.volume,
            "kitab_id": smap.kitab_id,
            "chapter_id": smap.chapter_id,
            "number_in_chapter": smap.number_in_chapter,
            "translator": remote.translator,
            "translator_attribution": "upstream-metadata",
            "source_english_sha256": sha256_text(english_full),
            "translation_classification": "external_source_normalized",
            "match_score": score,
            "match_method": smap.match_method,
            "matcher_version": MATCHER_VERSION,
        },
        "updated_at": now,
    }
    if translation is None:
        translation = HadithTranslation(
            hadith_id=hadith.id,
            language="en",
            translation_version=LIVE_TRANSLATION_VERSION,
            created_at=now,
            **values,
        )
        db.add(translation)
    else:
        for key, value in values.items():
            setattr(translation, key, value)
    db.flush()
    return translation


def _upsert_live_segment(
    db: Session,
    *,
    translation: HadithTranslation,
    hadith: Hadith,
    matn_english: str,
    remote: ThaqalaynRecord,
    score: float,
    flags: list[dict[str, str]],
    now: dt.datetime,
) -> TranslationSegment:
    source_hash = sha256_text(hadith.matn_raw)
    segment = db.execute(
        select(TranslationSegment).where(
            TranslationSegment.hadith_id == hadith.id,
            TranslationSegment.language == "en",
            TranslationSegment.translation_version == LIVE_TRANSLATION_VERSION,
            TranslationSegment.segment_kind == "matn",
            TranslationSegment.segment_index == 0,
            TranslationSegment.source_sha256 == source_hash,
        )
    ).scalar_one_or_none()
    values = {
        "translation_id": translation.id,
        "source_text": hadith.matn_raw,
        "translation_text": matn_english,
        "status": "published",
        "risk_level": "green",
        "risk_flags": source_import_publication_flags(flags),
        "metadata_json": {
            "source_norm": source_norm(hadith.matn_raw),
            "source": "thaqalayn-api",
            "provider": LIVE_PROVIDER,
            "source_url": remote.url,
            "thaqalayn_id": remote.id,
            "match_score": score,
            "translator": remote.translator,
            "source_english_sha256": sha256_text(clean_ws(remote.english_text)),
            "translation_classification": "external_source_normalized",
        },
        "updated_at": now,
    }
    if segment is None:
        segment = TranslationSegment(
            hadith_id=hadith.id,
            language="en",
            translation_version=LIVE_TRANSLATION_VERSION,
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
