"""Re-pin translation source hashes that were written with a non-canonical hasher.

Background
----------
``apply_alkafi_extent33_sarwar_republication.py`` (and a sibling quarantine
script) define a local ``sha256_text`` that shadows
``eshia_research.translation.text.sha256_text``.  The canonical function hashes
*whitespace-collapsed* text (``clean_ws``); the local one hashes the raw string.

Rows whose Arabic happened to be whitespace-clean are unaffected, because both
conventions agree there.  Rows carrying a stray double space or newline got a
hash the public gate can never reproduce, so ``source_hashes_are_current``
fails and the translation is hidden forever despite being a published, green,
correctly attributed human translation.

This repair recomputes those hashes with the canonical function.  It is safe
precisely because it is a no-op on the text: a row is only touched when its
stored hash equals the *raw* hash of the current Arabic, which proves the
Arabic has not changed since pinning.  Any row whose stored hash matches
neither convention is genuine text drift and is reported, never rewritten.

Writes only ``source_*_sha256`` and a provenance note.  Changes zero Arabic and
zero English characters.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.db import engine
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.publication import (
    is_public_english_translation,
)
from eshia_research.translation.text import sha256_text

REPAIR_NOTE_KEY = "source_hash_convention_repair"
REPAIR_NOTE_VALUE = "repinned_with_canonical_sha256_text"


def raw_sha256(value: str | None) -> str | None:
    """The non-canonical convention: hash of the raw, uncollapsed string."""

    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def classify(stored: str | None, raw: str | None) -> str:
    """Compare a stored hash against both conventions for the current text."""

    canonical = sha256_text(raw) if raw else None
    non_canonical = raw_sha256(raw) if raw else None
    if stored == canonical:
        return "canonical"
    if stored == non_canonical:
        return "non_canonical"
    return "drift"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-book-id", default="11005")
    parser.add_argument("--apply", action="store_true", help="write changes")
    args = parser.parse_args()

    with Session(engine) as session:
        book_id = session.execute(
            select(Book.id).where(Book.source_book_id == args.source_book_id)
        ).scalar_one()

        rows = session.execute(
            select(HadithTranslation, Hadith)
            .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
            .where(
                Hadith.book_id == book_id,
                HadithTranslation.language == "en",
                HadithTranslation.translation_version == TRANSLATION_VERSION,
            )
        ).all()

        selected: list[tuple[HadithTranslation, Hadith, list[str]]] = []
        drifted: list[str] = []

        for translation, hadith in rows:
            fields = (
                ("source_full_sha256", hadith.full_text_raw),
                ("source_isnad_sha256", hadith.isnad_raw),
                ("source_matn_sha256", hadith.matn_raw),
            )
            verdicts = {
                name: classify(getattr(translation, name), raw) for name, raw in fields
            }
            if any(v == "drift" for v in verdicts.values()):
                drifted.append(hadith.public_id)
                continue
            to_fix = [n for n, v in verdicts.items() if v == "non_canonical"]
            if to_fix:
                selected.append((translation, hadith, to_fix))

        print(f"al-kafi en translation rows examined : {len(rows)}")
        print(f"rows with non-canonical hashes       : {len(selected)}")
        print(f"rows with genuine text drift (skipped): {len(drifted)}")
        if drifted:
            print(f"  drifted: {sorted(drifted)[:20]}")

        hidden_before = [
            h.public_id
            for t, h, _ in selected
            if not is_public_english_translation(t, h)
        ]
        print(f"of those, currently hidden from readers: {len(hidden_before)}")
        for pid in sorted(hidden_before):
            print(f"    {pid}")

        if not args.apply:
            print("\nDRY RUN - no changes written. Re-run with --apply.")
            return 0

        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for translation, hadith, to_fix in selected:
            for name, raw in (
                ("source_full_sha256", hadith.full_text_raw),
                ("source_isnad_sha256", hadith.isnad_raw),
                ("source_matn_sha256", hadith.matn_raw),
            ):
                if name in to_fix:
                    setattr(translation, name, sha256_text(raw) if raw else None)
            provenance = dict(translation.provenance_json or {})
            provenance[REPAIR_NOTE_KEY] = f"{REPAIR_NOTE_VALUE}:{stamp}"
            translation.provenance_json = provenance

        session.commit()
        print(f"\nAPPLIED: re-pinned {len(selected)} rows.")

        # Re-verify through the real gate, on fresh objects.
        session.expire_all()
        recheck = session.execute(
            select(HadithTranslation, Hadith)
            .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
            .where(
                Hadith.book_id == book_id,
                HadithTranslation.language == "en",
                HadithTranslation.translation_version == TRANSLATION_VERSION,
            )
        ).all()
        now_public = sum(1 for t, h in recheck if is_public_english_translation(t, h))
        print(f"public english translations after repair: {now_public}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
