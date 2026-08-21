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


# eShia's library is not only Arabic. Persian works are real books, but they
# are not what Usul16 publishes, and a reader searching «الصلاة» should not be
# handed a Persian fiqh primer. Titles are the signal we have.
# kaf/yeh are not used here as broad signals because eShia also uses those
# glyphs in many otherwise-Arabic titles (e.g. al-Kafi, al-Bayt editions).
PERSIAN_ONLY_LETTERS = ("\u067e", "\u0686", "\u0698", "\u06af")
PERSIAN_TITLE_MARKERS = (
    "\u0622\u0634\u0646\u0627\u06cc\u06cc",  # آشنایی
    "\u0627\u062d\u06a9\u0627\u0645",  # احکام (Persian kaf)
    "\u062e\u0627\u0646\u0648\u0627\u062f\u0647",  # خانواده
    "\u0646\u0645\u0627\u0632",  # نماز
    "\u0631\u0648\u0632\u0647",  # روزه
    "\u0628\u0627\u0646\u0648\u0627\u0646",  # بانوان
    "\u0628\u06cc\u0645\u0627\u0631\u0627\u0646",  # بیماران
    "\u0627\u0646\u062f\u06cc\u0634\u0647",  # اندیشه
    "\u0633\u06cc\u0627\u0633\u06cc",  # سیاسی
    "\u062a\u0631\u062c\u0645\u0647",  # ترجمه
    "\u0641\u0627\u0631\u0633",  # فارس/فارسی/فارسى
    "\u0634\u0646\u0627\u0633\u06cc",  # شناسی
    "\u06af\u0632\u06cc\u062f\u0647",  # گزیده
    "\u0645\u062c\u0645\u0648\u0639\u0647",  # مجموعه
    "\u062f\u0627\u0646\u0634",  # دانش...
    "\u0646\u06af\u0627\u0647",  # نگاه/نگاهی
)
PERSIAN_TITLE_PHRASES = (
    " \u062f\u0631 ",  # در
    " \u0628\u0627 ",  # با
)

PERSIAN_TITLE_EXCLUSION_MARKERS = (
    *PERSIAN_ONLY_LETTERS,
    *PERSIAN_TITLE_MARKERS,
    *PERSIAN_TITLE_PHRASES,
)


def public_catalog_filters():
    """What a reader is allowed to be shown, as SQLAlchemy clauses.

    The catalogue, the stat tiles and search must answer the same question
    the same way. When only the listing applied these, search happily
    returned books the library refused to name.
    """
    from eshia_research.models import Book

    clauses = []
    if HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS:
        clauses.append(~Book.source_book_id.in_(HIDDEN_FROM_PUBLIC_SOURCE_BOOK_IDS))
    clauses.extend(
        ~Book.title_original.contains(marker)
        for marker in PERSIAN_TITLE_EXCLUSION_MARKERS
    )
    return clauses
