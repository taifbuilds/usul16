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

# Works the crawler collected that Usul16 does not publish. These are not part
# of the hadith corpus or the rijal reference shelf — they arrived as crawl
# spill and appeared in the public library with no English title, no cover and
# no editorial stage. The crawl rows stay as source evidence; this constant
# only decides what the public surfaces show.
UNPUBLISHED_SOURCE_BOOK_IDS = (
    "10926",  # الوهّابيّون والبيوت المرفوعة
    "86645",  # إيمان أبي طالب وسيرته
    "10798",  # الي المجمع العلمي بدمشق
)

# Every source id hidden from readers, for whatever reason. The catalogue, the
# book pages, search and the stat tiles must all agree: a book the catalogue
# refuses to list should not be reachable by searching for it either.
HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS = (
    *CATALOG_EXCLUDED_SOURCE_BOOK_IDS,
    *UNPUBLISHED_SOURCE_BOOK_IDS,
)

BIHAR_DAR_IHYA_SOURCE_BOOK_ID = "71860"

# Books whose chains are resolved and *polished* enough to chart in the public
# transmission graph. This is the single seam that lights a book up across the
# graph, dossiers, path-finding and reliability (see the graph plan): once a
# book's chains are resolved + chain-indexed, add its id here and it inherits
# every feature — no schema change, no client rewrite. Al-Kafi is the only
# polished book today; Faqih is nearing completion and joins next.
POLISHED_TRANSMISSION_BOOK_IDS: tuple[str, ...] = (AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,)

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
