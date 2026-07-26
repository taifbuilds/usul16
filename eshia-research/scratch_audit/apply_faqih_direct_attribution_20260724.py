"""Give Man La Yahduruhu al-Faqih's mursal direct-attribution reports a
clickable Imam. al-Saduq attributes many reports straight to an Imam with no
chain — «(وَ) قَالَ الصَّادِقُ ع …», «قَالَ رَسُولُ اللَّهِ ص …» — which left them
with isnad_raw=NULL and no chain. `split_direct_attribution` surfaces the Imam as
a one-node attribution; the tokenizer turns it into a single Imam node.

Scope: Faqih (book_id 1294) rows with NO isnad whose text is a clean single-Imam
direct attribution (verified by re-tokenizing the extracted isnad). Chains, bare
«قال ع», nested speech and narrative clauses are refused. full_text_raw is never
modified.

Run:  python scratch_audit/apply_faqih_direct_attribution_20260724.py [--apply]
Default is dry-run.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select  # noqa: E402

from eshia_research.db import SessionLocal  # noqa: E402
from eshia_research.hadith_extractor import split_direct_attribution  # noqa: E402
from eshia_research.isnad.tokenizer import tokenize_isnad  # noqa: E402
from eshia_research.models import Hadith  # noqa: E402
from eshia_research.normalise import normalise_arabic_persian  # noqa: E402

FAQIH_BOOK_ID = 1294

_HON_WORDS = {
    normalise_arabic_persian(w)
    for w in ("ع", "ص", "علیه", "علیها", "علیهم", "علیهما", "السلام", "صلی",
              "الله", "و", "آله", "اله", "وسلم", "سلم", "صلوات", "رضی", "عنه")
}


def _single_imam_name(isnad: str) -> bool:
    """The extracted isnad tokenizes to exactly one Imam node with a real name."""
    result = tokenize_isnad(isnad)
    chains = result if isinstance(result, list) else [result]
    nodes = [n for ch in chains for n in (getattr(ch, "tokens", None) or getattr(ch, "nodes", None) or ch)]
    if len(nodes) != 1 or getattr(nodes[0], "node_type", None) != "imam":
        return False
    norm = getattr(nodes[0], "norm", "") or ""
    return any(w not in _HON_WORDS for w in norm.split())


def main(apply: bool) -> None:
    db = SessionLocal()
    accepted, refused_tokenize = [], []
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
            split = split_direct_attribution(full)
            if split is None:
                continue
            isnad, matn = split
            if not _single_imam_name(isnad):
                refused_tokenize.append(pub)
                continue
            accepted.append((hid, pub, isnad, matn))

        print(f"Faqih no-isnad rows scanned: {len(rows)}")
        print(f"  ACCEPTED clean single-Imam mursals: {len(accepted)}")
        print(f"  refused by tokenize-check: {len(refused_tokenize)}")
        print("\n  sample accepted:")
        for hid, pub, isnad, matn in accepted[:8]:
            print(f"    {pub}: isnad {isnad[:30]!r} | matn {matn[:34]!r}")

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "faqih_direct_attribution_mursal",
            "book_id": FAQIH_BOOK_ID,
            "accepted": [p for _, p, _, _ in accepted],
            "refused_tokenize": refused_tokenize,
        }
        out = Path(__file__).resolve().parent / "faqih_direct_attribution_manifest_20260724.json"
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
        print(f"\nAPPLIED: set isnad/matn on {len(accepted)} Faqih mursal rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
