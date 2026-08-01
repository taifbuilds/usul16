"""Move commentary rows between two copies of the corpus, as a delta.

The research database is ~3 GB and the commentary rows are ~45 MB of it, so
shipping the whole file to publish a commentary is absurd — and destructive,
because it would overwrite everything else on the target. This module ships
only the rows that differ.

**Rows travel keyed by `public_id`, never by `hadith_id`.** Production is a
separate copy of the corpus, and nothing guarantees its `hadiths.id` sequence
matches the local one. A row carrying `hadith_id=19479` would silently attach
al-Majlisi's commentary to whatever hadith happens to hold that id there. That
is not a hypothetical: the local sync script needed the same guard, and the
identity check caught a mismatch class once already. `public_id` is stable by
construction, so it is the only safe join key across copies.

The flow is three steps, each with its own CLI command:

  1. *target*  ``commentary-manifest``      -> what the target already has
  2. *source*  ``export-commentary-delta``  -> only what differs, + deletions
  3. *target*  ``import-commentary-delta``  -> validate, then one transaction

Step 1 is what makes it a delta on the wire rather than a full dump that is
diffed after arrival.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import Book, Hadith, HadithCommentary

TRANSFER_FORMAT = "usul16.commentary-delta.v1"

# Everything that defines a row's content. `id`, `hadith_id` and the timestamps
# are deliberately excluded: the first two are local identifiers that must not
# cross the wire, and timestamps would make every row look changed.
_CONTENT_FIELDS = (
    "source_key",
    "source_sequence",
    "source_label",
    "section_title",
    "report_raw",
    "report_normalised",
    "commentary_raw",
    "commentary_normalised",
    "volume_start",
    "volume_end",
    "page_start",
    "page_end",
    "source_url",
    "match_status",
    "match_method",
    "match_score",
    "matcher_version",
)


def row_fingerprint(payload: dict[str, Any]) -> str:
    """Stable hash of a row's content, including which hadith it points at.

    The target hadith is part of the identity: re-running the indexer can move
    a passage from one hadith to another without changing a character of its
    text, and that move must ship.
    """
    material = {key: payload.get(key) for key in _CONTENT_FIELDS}
    material["public_id"] = payload.get("public_id")
    canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def _row_payload(row: HadithCommentary, public_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {key: getattr(row, key) for key in _CONTENT_FIELDS}
    payload["public_id"] = public_id
    payload["match_evidence_json"] = row.match_evidence_json
    return payload


@dataclass
class SourceBook:
    """Enough to find — or create — the commentary's own book row on a target."""

    source_book_id: str
    title_original: str
    title_normalised: str
    source_url: str
    volume_count: int | None = None


@dataclass
class DeltaStats:
    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    missing_public_ids: list[str] = field(default_factory=list)


def build_manifest(db: Session, source_key: str) -> dict[str, Any]:
    """What the target already holds: one fingerprint per passage.

    Small by design — a few hundred KB for 18k rows — so it can be pulled back
    from production before deciding what to send.
    """
    rows = db.execute(
        select(HadithCommentary, Hadith.public_id)
        .outerjoin(Hadith, Hadith.id == HadithCommentary.hadith_id)
        .where(HadithCommentary.source_key == source_key)
    ).all()
    entries = {
        str(row.source_sequence): row_fingerprint(_row_payload(row, public_id))
        for row, public_id in rows
    }
    return {"format": TRANSFER_FORMAT, "source_key": source_key, "entries": entries}


def export_delta(
    db: Session,
    source_key: str,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rows whose content differs from the manifest, plus sequences to remove.

    With no manifest every row is exported, which is the correct behaviour for
    a first deployment.
    """
    known: dict[str, str] = dict((manifest or {}).get("entries", {}))

    book = db.execute(
        select(Book)
        .join(HadithCommentary, HadithCommentary.commentary_book_id == Book.id)
        .where(HadithCommentary.source_key == source_key)
        .limit(1)
    ).scalar_one_or_none()
    if book is None:
        raise ValueError(f"No commentary rows found locally for source_key={source_key!r}.")

    rows = db.execute(
        select(HadithCommentary, Hadith.public_id)
        .outerjoin(Hadith, Hadith.id == HadithCommentary.hadith_id)
        .where(HadithCommentary.source_key == source_key)
        .order_by(HadithCommentary.source_sequence)
    ).all()

    changed: list[dict[str, Any]] = []
    seen: set[str] = set()
    unchanged = 0
    for row, public_id in rows:
        payload = _row_payload(row, public_id)
        fingerprint = row_fingerprint(payload)
        key = str(row.source_sequence)
        seen.add(key)
        if known.get(key) == fingerprint:
            unchanged += 1
            continue
        payload["fingerprint"] = fingerprint
        changed.append(payload)

    # Passages the target still has but this build no longer produces.
    removed = sorted(int(key) for key in known.keys() - seen)

    return {
        "format": TRANSFER_FORMAT,
        "source_key": source_key,
        "book": {
            "source_book_id": book.source_book_id,
            "title_original": book.title_original,
            "title_normalised": book.title_normalised,
            "source_url": book.source_url,
            "volume_count": book.volume_count,
        },
        "rows": changed,
        "removed_source_sequences": removed,
        "summary": {
            "total_local_rows": len(rows),
            "changed": len(changed),
            "unchanged": unchanged,
            "removed": len(removed),
        },
    }


def write_delta(delta: dict[str, Any], path: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(delta, handle, ensure_ascii=False)


def read_delta(path: str) -> dict[str, Any]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[operator]
        delta = json.load(handle)
    if delta.get("format") != TRANSFER_FORMAT:
        raise ValueError(
            f"Unrecognised delta format {delta.get('format')!r}; expected {TRANSFER_FORMAT!r}."
        )
    return delta


def _resolve_book(db: Session, spec: dict[str, Any]) -> Book:
    book = db.execute(
        select(Book).where(Book.source_book_id == spec["source_book_id"])
    ).scalar_one_or_none()
    if book is not None:
        return book
    # A target that has never seen this commentary has no row for it. Creating
    # one from the exported metadata keeps the delta self-contained; it carries
    # no pages, so nothing else on the target is affected.
    book = Book(
        source_book_id=spec["source_book_id"],
        title_original=spec["title_original"],
        title_normalised=spec["title_normalised"],
        source_url=spec["source_url"],
        volume_count=spec.get("volume_count"),
    )
    db.add(book)
    db.flush()
    return book


def validate_delta(db: Session, delta: dict[str, Any]) -> list[str]:
    """Every `public_id` a row points at must exist here. Returns the missing.

    Run before any write. A delta that references hadiths this corpus does not
    have is not a delta for this corpus, and importing it would either fail
    halfway or attach commentary to nothing.
    """
    wanted = {row["public_id"] for row in delta["rows"] if row.get("public_id")}
    if not wanted:
        return []
    found = {
        public_id
        for (public_id,) in db.execute(
            select(Hadith.public_id).where(Hadith.public_id.in_(wanted))
        ).all()
    }
    return sorted(wanted - found)


def import_delta(db: Session, delta: dict[str, Any], *, dry_run: bool = False) -> DeltaStats:
    """Apply a delta inside a single transaction. Nothing partial is left.

    Validation runs first and aborts before any write, so a bad delta cannot
    leave the target half-updated.
    """
    stats = DeltaStats()
    source_key = delta["source_key"]

    missing = validate_delta(db, delta)
    if missing:
        stats.missing_public_ids = missing
        raise ValueError(
            f"{len(missing)} public_id(s) in the delta do not exist in this corpus "
            f"(first few: {missing[:5]}). Refusing to import."
        )

    hadith_ids = {
        public_id: hadith_id
        for hadith_id, public_id in db.execute(
            select(Hadith.id, Hadith.public_id).where(
                Hadith.public_id.in_({r["public_id"] for r in delta["rows"] if r.get("public_id")})
            )
        ).all()
    }

    book = _resolve_book(db, delta["book"])

    existing = {
        row.source_sequence: row
        for row in db.execute(
            select(HadithCommentary).where(
                HadithCommentary.commentary_book_id == book.id,
                HadithCommentary.source_key == source_key,
            )
        ).scalars()
    }

    # `(source_key, hadith_id)` is unique, so a passage moving onto a hadith
    # another passage currently holds would collide. Detach the incumbent
    # first; if it is not itself in this delta it simply loses its link, which
    # is what a re-index moving the passage means.
    incoming_targets = {
        hadith_ids[row["public_id"]] for row in delta["rows"] if row.get("public_id")
    }
    if incoming_targets:
        incoming_sequences = {row["source_sequence"] for row in delta["rows"]}
        for row in db.execute(
            select(HadithCommentary).where(
                HadithCommentary.source_key == source_key,
                HadithCommentary.hadith_id.in_(incoming_targets),
            )
        ).scalars():
            if row.source_sequence not in incoming_sequences:
                row.hadith_id = None

    for payload in delta["rows"]:
        target_id = hadith_ids.get(payload["public_id"]) if payload.get("public_id") else None
        row = existing.get(payload["source_sequence"])
        if row is None:
            row = HadithCommentary(
                commentary_book_id=book.id,
                source_key=source_key,
                source_sequence=payload["source_sequence"],
            )
            db.add(row)
            stats.inserted += 1
        else:
            stats.updated += 1
        for key in _CONTENT_FIELDS:
            if key in ("source_key", "source_sequence"):
                continue
            setattr(row, key, payload.get(key))
        row.match_evidence_json = payload.get("match_evidence_json")
        row.hadith_id = target_id

    for sequence in delta.get("removed_source_sequences", []):
        row = existing.get(sequence)
        if row is not None:
            db.delete(row)
            stats.deleted += 1

    stats.unchanged = delta.get("summary", {}).get("unchanged", 0)

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return stats


def verify_target(db: Session, source_key: str) -> dict[str, int]:
    """Counts a deploy can assert on after importing."""
    rows = db.execute(
        select(HadithCommentary).where(HadithCommentary.source_key == source_key)
    ).scalars().all()
    linked = {row.hadith_id for row in rows if row.hadith_id is not None}
    return {
        "rows": len(rows),
        "matched": sum(1 for row in rows if row.match_status == "matched"),
        "linked_hadiths": len(linked),
    }
