"""Re-split Faqih «رَوَى …» reports whose isnad/matn split failed because a
zero-width non-joiner glued to «قَالَ» defeated the speech-boundary regex
(fixed in hadith_extractor.ZERO_WIDTH_RE, 2026-07-24).

Scope (user-approved "clean subset"): Faqih (book_id 1294) rows that currently
have NO isnad_raw, whose text opens with «رَوَى/رُوِيَ», and whose corrected
split ends the isnad exactly at a speech verb (قال/فقال/يقول/…). Rows that only
split at a weaker «أن/في» boundary, or not at all, are left untouched for a
later reviewed pass. full_text_raw is never modified.

Run:  python scratch_audit/apply_faqih_rawa_resplit_20260724.py [--apply]
Default is dry-run.
"""

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select  # noqa: E402

from eshia_research.db import SessionLocal  # noqa: E402
from eshia_research.hadith_extractor import split_isnad_matn  # noqa: E402
from eshia_research.models import Hadith  # noqa: E402
from eshia_research.normalise import normalise_arabic_persian  # noqa: E402

FAQIH_BOOK_ID = 1294

_HARAKAT = re.compile(r"[ً-ْٰـ]")


def _strip(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = _HARAKAT.sub("", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ی", "ي"), ("ك", "ک")):
        s = s.replace(a, b)
    return s.strip()


# Speech verbs that legitimately end an isnad (matn is what was said).
SPEECH_TERMINAL = {
    "قال", "قالت", "قالوا", "قالا", "فقال", "فقالت", "فقالوا",
    "يقول", "تقول", "سمعت", "سالت", "کتبت", "قلت", "قلنا", "سالته",
}

RAWA_LEAD = ("رو",)  # روى / رُوِيَ / روينا


def main(apply: bool) -> None:
    db = SessionLocal()
    accepted, skipped_boundary, skipped_none, not_rawa = [], [], [], 0
    try:
        rows = db.execute(
            select(Hadith.id, Hadith.public_id, Hadith.full_text_raw)
            .where(
                Hadith.book_id == FAQIH_BOOK_ID,
                (Hadith.isnad_raw.is_(None)) | (Hadith.isnad_raw == ""),
                Hadith.review_status != "rejected_non_hadith_fragment",
            )
            .order_by(Hadith.sequence_in_book)
        ).all()

        for hid, pub, full in rows:
            if not full:
                continue
            stripped_full = _strip(full)
            if not stripped_full.split() or not stripped_full.split()[0].startswith(RAWA_LEAD):
                not_rawa += 1
                continue
            isnad, matn = split_isnad_matn(full)
            if isnad is None or not matn:
                skipped_none.append(pub)
                continue
            last = _strip(isnad).split()[-1] if _strip(isnad).split() else ""
            if last not in SPEECH_TERMINAL:
                skipped_boundary.append(pub)
                continue
            accepted.append((hid, pub, isnad, matn))

        print(f"Faqih unsplit rows scanned: {len(rows)}")
        print(f"  non-«روى» leading (ignored): {not_rawa}")
        print(f"  ACCEPTED (clean speech-terminal split): {len(accepted)}")
        print(f"  skipped — weak/other boundary: {len(skipped_boundary)}")
        print(f"  skipped — no split at all: {len(skipped_none)}")
        print("\n  sample accepted:")
        for hid, pub, isnad, matn in accepted[:6]:
            print(f"    {pub}: isnad …{isnad[-40:]!r} | matn {matn[:34]!r}")

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "faqih_rawa_zwnj_resplit",
            "book_id": FAQIH_BOOK_ID,
            "accepted": [p for _, p, _, _ in accepted],
            "skipped_weak_boundary": skipped_boundary,
            "skipped_no_split": skipped_none,
        }
        out = Path(__file__).resolve().parent / "faqih_rawa_resplit_manifest_20260724.json"
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote manifest: {out}")

        if not apply:
            print("\nDRY-RUN — no database changes. Re-run with --apply to write.")
            return

        for hid, pub, isnad, matn in accepted:
            h = db.get(Hadith, hid)
            h.isnad_raw = isnad
            h.isnad_normalised = normalise_arabic_persian(isnad)
            h.matn_raw = matn
            h.matn_normalised = normalise_arabic_persian(matn)
        db.commit()
        print(f"\nAPPLIED: updated isnad/matn on {len(accepted)} Faqih rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
