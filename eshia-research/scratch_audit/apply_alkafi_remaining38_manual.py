import datetime as dt

from eshia_research.db import SessionLocal
from eshia_research.models import Hadith, HadithSplitReview
from eshia_research.normalise import normalise_arabic_persian

REVIEWER = "codex-alkafi-manual-remaining38"
VERSION = "alkafi_manual_remaining38_v1"

split_before_map = {
    "alkafi-647": ("وَ قَالَ رَجُلٌ", "Abbreviated inherited-chain opening: split leading qal as isnad marker."),
    "alkafi-648": ("لَمَا تَرَوْنَ", "Abbreviated inherited-chain opening with terminal Abu Ja'far marker."),
    "alkafi-2883": ("مَنْ شَكَّ", "Source marker fi wasiyyat al-Mufaddal before matn."),
    "alkafi-3393": ("يَا حَيُّ", "Chain ends at Umar b. Yazid before du'a text."),
    "alkafi-3430": ("كَانَ أَبُو عَبْدِ اللَّهِ", "Abbreviated qal opening before du'a report."),
    "alkafi-3612": ("حُبُّ الْأَبْرَارِ", "Abbreviated heard-from-Imam opening before matn."),
    "alkafi-3753": ("فَكَانَ بَعْدَ ذَلِكَ", "Variant-report marker before matn."),
    "alkafi-5475": ("أَنَّ مَنْ قَالَهَا", "Ruwiya marker without named chain; split as source/report marker."),
    "alkafi-6703": ("وَ لَوْ أَرَادَ اللَّهُ", "Ruwiya an Amir al-Mu'minin said in a khutba before khutba matn."),
    "alkafi-7432": ("إِذَا أَصَابَ", "Ibn Abi Umayr chain before legal matn."),
    "alkafi-10458": ("حَنِّكُوا", "Variant-report marker before matn."),
    "alkafi-10588": ("أَنَّ أَكْيَسَ", "Ruwiya marker without named chain; split as source/report marker."),
    "alkafi-11139": ("فِي الْمُدَبَّرِ", "Yunus chain before legal topic matn."),
    "alkafi-13178": ("مَيِّتٌ أَوْصَى", "Letter/report opening before legal question matn."),
    "alkafi-13215": ("رَجُلٌ أَوْصَى", "Muhammad qal kataba opening before legal question matn."),
    "alkafi-13462": ("قَضَى أَمِيرُ", "Anaphoric anhu qal opening before matn."),
    "alkafi-14123": ("قُلْتُ", "Anaphoric anhu qal opening before narrator's question."),
    "alkafi-15191": ("وَ إِذا تَوَلَّى", "Chain leaked into matn; split before Qur'anic matn."),
}

source_less_approved = {
    "alkafi-8098": "Liturgical ziyara text printed without explicit isnad in this row; approved as source-less/implicit.",
    "alkafi-8124": "Second ziyara/du'a text printed after du'a akhar heading without explicit isnad; approved as source-less/implicit.",
}

pure_rejects = {
    "alkafi-1111": "Editorial/variant note, not a hadith row.",
    "alkafi-2058": "Editorial gloss on previous hadith, not a hadith row.",
    "alkafi-2725": "Editorial fiqh/commentary note, not a hadith row.",
    "alkafi-2843": "Editorial tafsir/commentary note, not a hadith row.",
    "alkafi-3052": "Editorial tafsir/commentary note, not a hadith row.",
    "alkafi-4802": "Editorial gloss, not a hadith row.",
    "alkafi-5987": "Editorial tafsir/commentary note, not a hadith row.",
    "alkafi-7180": "Editorial tafsir/commentary note, not a hadith row.",
    "alkafi-15190": "Editorial pronoun/gloss note, not a hadith row.",
    "alkafi-15242": "Editorial tafsir/commentary note, not a hadith row.",
}

merge_map = {
    ("alkafi-1690", "alkafi-1689"): ("فَمَنْ أَعْطَى", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-2059", "alkafi-2057"): ("عَاقِبَتَنَا فَمَنْ", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-2862", "alkafi-2861"): (None, "Same printed report split across page boundary; append continuation to previous hadith."),
    ("alkafi-3250", "alkafi-3249"): ("فَلَمْ أَدَعْ", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-7169", "alkafi-7168"): ("أَوْ نَافِلَةٍ", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-8191", "alkafi-8189"): ("صِفَتِهِمْ", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-8268", "alkafi-8267"): ("فَطَلَبَ الْعَدُوَّ", "Continuation after editorial gloss; append resumed matn to previous hadith."),
    ("alkafi-13403", "alkafi-13402"): (None, "Continuation of previous inheritance discussion; append to previous hadith."),
    ("alkafi-14845", "alkafi-14843"): ("وَ اللَّهُ عَزَّ وَ جَلَّ مُهْلِكُهُمْ", "Continuation after editorial source note; append resumed matn to previous hadith."),
}


def get(db, public_id: str) -> Hadith:
    hadith = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if hadith is None:
        raise RuntimeError(f"missing hadith {public_id}")
    return hadith


def upsert_review(db, hadith: Hadith) -> HadithSplitReview:
    review = db.query(HadithSplitReview).filter(HadithSplitReview.hadith_id == hadith.id).one_or_none()
    if review is None:
        review = HadithSplitReview(hadith_id=hadith.id)
        db.add(review)
    return review


def sync_text_fields(hadith: Hadith, isnad: str | None, matn: str, now: dt.datetime) -> None:
    hadith.isnad_raw = isnad or None
    hadith.isnad_normalised = normalise_arabic_persian(isnad) if isnad else None
    hadith.matn_raw = matn.strip()
    hadith.matn_normalised = normalise_arabic_persian(hadith.matn_raw)
    hadith.full_text_raw = ((isnad.strip() + " ") if isnad else "") + hadith.matn_raw
    hadith.full_text_normalised = normalise_arabic_persian(hadith.full_text_raw)
    hadith.updated_at = now


def approve(db, hadith: Hadith, isnad: str | None, matn: str, note: str, now: dt.datetime) -> None:
    sync_text_fields(hadith, isnad, matn, now)
    hadith.extraction_confidence = max(hadith.extraction_confidence or 0, 96)
    review = upsert_review(db, hadith)
    review.approved_isnad_raw = isnad or None
    review.approved_matn_raw = matn.strip()
    review.review_status = "approved"
    review.reviewer = REVIEWER
    review.notes = note
    review.split_version = VERSION
    review.updated_at = now


def reject(db, hadith: Hadith, note: str, now: dt.datetime) -> None:
    hadith.review_status = "rejected_non_hadith_fragment"
    hadith.updated_at = now
    review = upsert_review(db, hadith)
    review.approved_isnad_raw = hadith.isnad_raw
    review.approved_matn_raw = hadith.matn_raw
    review.review_status = "rejected"
    review.reviewer = REVIEWER
    review.notes = note
    review.split_version = VERSION
    review.updated_at = now


def split_before(db, public_id: str, matn_start: str, note: str, now: dt.datetime) -> None:
    hadith = get(db, public_id)
    text = hadith.full_text_raw or hadith.matn_raw or ""
    idx = text.find(matn_start)
    if idx <= 0:
        raise RuntimeError(f"could not split {public_id}; missing boundary {matn_start!r}")
    approve(db, hadith, text[:idx].strip(), text[idx:].strip(), note, now)


def append_continuation(
    db,
    source_id: str,
    target_id: str,
    start: str | None,
    note: str,
    now: dt.datetime,
) -> None:
    source = get(db, source_id)
    target = get(db, target_id)
    text = source.full_text_raw or source.matn_raw or ""
    if start is not None:
        idx = text.find(start)
        if idx < 0:
            raise RuntimeError(f"could not merge {source_id}; missing continuation {start!r}")
        text = text[idx:]
    continuation = text.strip()
    if not continuation:
        raise RuntimeError(f"empty continuation for {source_id}")
    merged_matn = (target.matn_raw or "").rstrip() + " " + continuation
    approve(db, target, target.isnad_raw, merged_matn, note, now)
    if source.page_end and (target.page_end is None or source.page_end > target.page_end):
        target.page_end = source.page_end
        target.page_end_id = source.page_end_id
        target.volume_end = source.volume_end
    reject(db, source, note, now)


def fix_15262_15263(db, now: dt.datetime) -> None:
    head = get(db, "alkafi-15262")
    tail = get(db, "alkafi-15263")
    tail_isnad = tail.isnad_raw or ""
    boundary = "أَبِي يَزِيدَ"
    idx = tail_isnad.find(boundary)
    if idx < 0:
        raise RuntimeError("could not find 15263 chain continuation")
    isnad = (head.matn_raw or "").strip() + " " + tail_isnad[idx:].strip()
    matn = (tail.matn_raw or "").strip()
    approve(db, head, isnad, matn, "Chopped chain repaired across adjacent rows; editorial gloss removed from chain.", now)
    head.page_end = tail.page_end
    head.page_end_id = tail.page_end_id
    head.volume_end = tail.volume_end
    reject(db, tail, "Continuation half of alkafi-15262 after chopped chain repair; hidden from Hadith View.", now)


def main() -> None:
    with SessionLocal() as db:
        now = dt.datetime.now(dt.timezone.utc)
        for public_id, (boundary, note) in split_before_map.items():
            split_before(db, public_id, boundary, note, now)
        for public_id, note in source_less_approved.items():
            hadith = get(db, public_id)
            approve(db, hadith, None, hadith.matn_raw or hadith.full_text_raw or "", note, now)
        for public_id, note in pure_rejects.items():
            reject(db, get(db, public_id), note, now)
        for (source_id, target_id), (start, note) in merge_map.items():
            append_continuation(db, source_id, target_id, start, note, now)
        fix_15262_15263(db, now)
        db.commit()
        print(
            "applied "
            f"{len(split_before_map)} splits, "
            f"{len(source_less_approved)} source-less approvals, "
            f"{len(pure_rejects)} pure rejects, "
            f"{len(merge_map)} merges, "
            "1 chopped-chain repair"
        )


if __name__ == "__main__":
    main()
