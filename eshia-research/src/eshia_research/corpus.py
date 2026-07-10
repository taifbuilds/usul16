"""Corpus-level policy decisions.

Raw crawl rows are kept as source evidence. These constants define which
editions are treated as canonical for the research/indexing layer.
"""

AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID = "11005"
AL_KAFI_DAR_AL_HADITH_SOURCE_BOOK_ID = "27311"

CANONICAL_FOUR_BOOK_SOURCE_IDS = (
    AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
    "11021",  # Man la yahduruhu al-faqih
    "10083",  # Tahdhib al-ahkam
    "11002",  # al-Istibsar
)

# Dar al-Hadith is a useful critical edition, but keeping both it and the
# classic Islamiyya/Dar al-Kutub al-Islamiyyah al-Kafi in the public corpus
# duplicates the same work and makes IDs/topics noisier.
CATALOG_EXCLUDED_SOURCE_BOOK_IDS = (AL_KAFI_DAR_AL_HADITH_SOURCE_BOOK_ID,)

BIHAR_DAR_IHYA_SOURCE_BOOK_ID = "71860"

# Human-readable slugs used in public hadith IDs («alkafi-2041») — the ID a
# reader cites should speak the tradition's language, not the crawler's.
BOOK_SLUGS = {
    AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID: "alkafi",
    "11021": "faqih",
    "10083": "tahdhib",
    "11002": "istibsar",
    BIHAR_DAR_IHYA_SOURCE_BOOK_ID: "bihar",
}


def book_slug(source_book_id: str) -> str:
    """Slug for public hadith IDs; falls back to a neutral book-N form for
    books that don't have a curated slug yet."""
    return BOOK_SLUGS.get(source_book_id, f"book{source_book_id}")
