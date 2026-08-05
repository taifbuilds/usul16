"""Descriptors for the printed commentaries indexed against a base collection.

Everything that differs between one sharh and another lives here; the
extraction, matching and alignment engines are deliberately source-agnostic so
a second commentary (Sharh al-Mazandarani) is a descriptor plus a crawl, not a
second pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID


@dataclass(frozen=True)
class CommentarySource:
    """One printed commentary and the collection it comments on."""

    key: str
    """Stable public identifier, e.g. ``mirat-al-uqul``. Used by the reader."""

    source_book_id: str
    """eShia book id of the commentary itself."""

    target_source_book_id: str
    """eShia book id of the collection being commented on."""

    title_ar: str
    author_ar: str
    title_en: str
    author_en: str

    disclosure_label_ar: str
    """Short Arabic label the reader shows on the disclosure.

    Separate from ``title_ar`` because a full printed title
    («مرآة العقول في شرح أخبار آل الرسول») is too long for a collapsed row.
    """

    matcher_version: str
    """Bumped whenever extraction or matching changes, so rows are traceable."""

    covers_whole_target: bool = True
    """False when the sharh covers only part of the collection (e.g. Usul only).

    Coverage is reported against the covered part, so a partial commentary is
    never scored as though it had failed on volumes it never addressed.
    """

    volume_count: int = 0
    """Printed volumes, used to bound a crawl. 0 means "ask the source"."""

    def require_crawlable(self) -> None:
        if not self.source_book_id:
            raise ValueError(
                f"{self.key} has no eShia book id recorded yet, so it cannot be crawled."
            )


MIRAT_AL_UQUL = CommentarySource(
    key="mirat-al-uqul",
    source_book_id="71429",
    target_source_book_id=AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    title_ar="مرآة العقول في شرح أخبار آل الرسول",
    author_ar="العلامة المجلسي",
    title_en="Mir'at al-'Uqul",
    author_en="al-'Allama al-Majlisi",
    disclosure_label_ar="شرح مرآة العقول",
    matcher_version="mirat_al_uqul_v5",
    volume_count=26,
)

# eShia 13033, 12 volumes, confirmed from its own title page:
#   «شرح الكافي الجامع للمولى محمد صالح المازندراني المتوفى 1081 ه‌
#    مع تعاليق الميرزا أبو الحسن الشعراني»
# Two cautions that follow from that line:
#   * it covers the Usul (and Rawda), not the whole Kafi — hence
#     covers_whole_target=False;
#   * the edition interleaves al-Sha'rani's glosses with al-Mazandarani's
#     commentary, so extraction must keep them apart. Attributing a gloss to
#     al-Mazandarani would be a false attribution, not a formatting slip.
SHARH_AL_MAZANDARANI = CommentarySource(
    key="sharh-al-mazandarani",
    source_book_id="13033",
    target_source_book_id=AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    title_ar="شرح أصول الكافي",
    author_ar="المولى صالح المازندراني",
    title_en="Sharh Usul al-Kafi",
    author_en="Mulla Salih al-Mazandarani",
    disclosure_label_ar="شرح أصول الكافي",
    matcher_version="mazandarani_v1",
    covers_whole_target=False,
    volume_count=12,
)

COMMENTARY_SOURCES: dict[str, CommentarySource] = {
    source.key: source for source in (MIRAT_AL_UQUL, SHARH_AL_MAZANDARANI)
}


def get_commentary_source(key: str) -> CommentarySource:
    try:
        return COMMENTARY_SOURCES[key]
    except KeyError:
        known = ", ".join(sorted(COMMENTARY_SOURCES))
        raise ValueError(f"Unknown commentary source {key!r}. Known: {known}") from None
