"""Crawl job orchestration: ties the HTTP client + parsers + DB together.

Each public function here is one CLI command's worth of work and commits its
own CrawlLog row per URL, so a crawl can be interrupted at any point and the
CrawlLog table (plus the on-disk Checkpoint) tell you exactly where it left
off.
"""

import gzip
import hashlib
import json
import logging
import re
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy.orm import Session

from eshia_research.cloudstore import ObjectStore, make_object_store
from eshia_research.config import Settings, get_settings
from eshia_research.crawler.client import AdaptiveThrottle, Checkpoint, CrawlError, PoliteClient
from eshia_research.crawler.parser import (
    CategoryBookEntry,
    ParsedPage,
    last_page_number,
    parse_book_subject,
    parse_category_page,
    parse_page,
    split_author_names,
)
from eshia_research.db import SessionLocal
from eshia_research.models import Author, Book, BookAuthor, Category, CrawlLog, Page, Volume
from eshia_research.normalise import normalise_arabic_persian

logger = logging.getLogger(__name__)

DEFAULT_CHECKPOINT_PATH = Path("data") / "checkpoints" / "crawl.json"
_VOLUME_PAGE_SUFFIX_RE = re.compile(r"/\d+/\d+/\d+/?$")

# Called as on_progress(phase, done, total) by the long-running crawl_*
# functions below. Kept as a plain callback rather than importing a
# progress-bar library here, since this module is also used by
# tests/non-interactive callers — the CLI supplies one backed by rich.
ProgressCallback = Callable[[str, int, int], None]


# --- HTML archive (permanent, separate from the temporary cloud-buffer) ---
#
# Decision: keep raw page HTML out of Postgres/SQLite (it's bulky and almost
# never queried) but don't discard it either — it's the source of truth for
# re-parsing pages later (e.g. once the parser handles more image-only/edge
# cases) without re-crawling lib.eshia.ir from scratch. Archived to whatever
# ObjectStore is configured (see cloudstore.py), keyed deterministically so
# any Page row can find its own archived HTML without a side table.
HTML_ARCHIVE_PREFIX = "html/"


def html_archive_key(source_book_id: str, volume_number: int | None, page_number: int | None) -> str:
    """Deterministic archive key for one page's raw HTML. Falls back to 0
    for an unknown volume/page (e.g. a TOC page) the same way Page itself
    does (Page.page_number defaults to 0 when parsed.page_number is None)."""
    return (
        f"{HTML_ARCHIVE_PREFIX}{source_book_id}/"
        f"{volume_number if volume_number is not None else 0}/"
        f"{page_number or 0}.html.gz"
    )


def archive_html(
    html_store: ObjectStore, source_book_id: str, volume_number: int | None, page_number: int | None, html: str
) -> None:
    key = html_archive_key(source_book_id, volume_number, page_number)
    html_store.put_bytes(key, gzip.compress(html.encode("utf-8")))


def resolve_html_store(settings: Settings, html_store: ObjectStore | None) -> ObjectStore | None:
    """Returns the ObjectStore to archive HTML to, or None if archiving is
    disabled. Callers pass an explicit `html_store` (e.g. tests using
    LocalFileStore) to avoid constructing a fresh one — when None, one is
    built from settings.cloud_store_backend only if store_raw_html_r2 is on,
    so this is a no-op cost when the feature isn't in use."""
    if html_store is not None:
        return html_store
    if settings.store_raw_html_r2:
        return make_object_store(settings)
    return None


def compute_checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log(db: Session, url: str, status: str, http_status: int | None = None, error: str | None = None, checksum: str | None = None) -> None:
    db.add(CrawlLog(url=url, status=status, http_status=http_status, error=error, checksum=checksum))
    db.commit()


def get_or_create_author(db: Session, name: str, url: str | None) -> Author | None:
    if not name:
        return None
    normalised = normalise_arabic_persian(name)
    author = db.query(Author).filter(Author.name_normalised == normalised).one_or_none()
    if author is None:
        author = Author(name_original=name, name_normalised=normalised, source_url=url)
        db.add(author)
        db.flush()
    return author


def set_book_authors(db: Session, book: Book, raw_author_field: str | None, url: str | None) -> None:
    """Split a raw eShia author field into individual Authors and (re)link
    them to `book` in source order via BookAuthor.position.

    Re-crawls call this every time, so existing links for the book are
    cleared first rather than diffed — the author list per book is small,
    and this keeps re-crawl behaviour simple and correct if eShia's listed
    names ever change.
    """
    book.author_links.clear()
    if not raw_author_field:
        return
    for position, name in enumerate(split_author_names(raw_author_field)):
        author = get_or_create_author(db, name, url)
        if author is not None:
            book.author_links.append(BookAuthor(author=author, position=position))


_CATEGORY_URL_NOISE_SEGMENTS = {"all", "authors"}


def category_name_from_url(category_url: str) -> str | None:
    """Derive a display name from a category URL's path segments.

    eShia category URLs are e.g. ".../فقه", ".../فقه/all" (everything under
    فقه including subcategories), or ".../فقه/رسائل_عملیه" (one
    subcategory). Naively taking the last path segment breaks on the "/all"
    and "/authors" variants — they'd all just be named "all" — so those
    segments are stripped first and the last *meaningful* segment is used.

    Returns None for the sitewide listing (".../all" with nothing else in
    the path) — there's no real topical category there, just every book on
    the site, so callers should leave such books uncategorized rather than
    inventing a fake "all" category.
    """
    path = category_url.rstrip("/").split("eshia.ir/", 1)[-1]
    segments = [s for s in path.split("/") if s and s not in _CATEGORY_URL_NOISE_SEGMENTS]
    return segments[-1] if segments else None


def get_or_create_category(db: Session, name: str, source_url: str) -> Category:
    category = db.query(Category).filter(Category.source_url == source_url).one_or_none()
    if category is None:
        category = Category(name_original=name, source_url=source_url)
        db.add(category)
        db.flush()
    return category


_category_by_name_lock = threading.Lock()


def get_or_create_category_by_name(db: Session, name: str) -> Category:
    """Like get_or_create_category, but keyed by name rather than a real
    browsable URL — used for categories discovered via a book's "Subject"
    field, which has no category-listing page of its own.

    Checks for an existing category with this name first (so a Subject
    value that happens to match one of the 15 nav categories, e.g. "فقه",
    reuses that row instead of creating a redundant duplicate) before
    falling back to a synthetic `subject://<name>` source_url.

    Guarded by a lock that wraps check-AND-create-AND-commit: there's no DB
    uniqueness constraint on Category.name_original, so two concurrent
    workers discovering the same new subject name could otherwise both pass
    the "does this exist?" check before either commits, creating duplicate
    rows. Commits *inside* this function (unusual for a get_or_create
    helper) specifically so the row is visible to other threads' sessions
    before the lock is released — a flush alone isn't enough across
    separate DB connections/threads.
    """
    with _category_by_name_lock:
        category = db.query(Category).filter(Category.name_original == name).one_or_none()
        if category is not None:
            return category
        category = get_or_create_category(db, name, f"subject://{name}")
        db.commit()
        return category


def upsert_book_from_entry(db: Session, entry: CategoryBookEntry, category: Category | None) -> Book:
    """Upsert a book row from a category-listing entry.

    `category=None` means "this listing doesn't tell us a real category"
    (e.g. the sitewide /all completeness backstop in crawl_metadata) rather
    than "this book has no category" — so an existing category assignment
    is left alone in that case instead of being wiped out.
    """
    book = db.query(Book).filter(Book.source_book_id == entry.source_book_id).one_or_none()
    if book is None:
        book = Book(source_book_id=entry.source_book_id, title_original="", title_normalised="", source_url="")
        db.add(book)

    book.title_original = entry.title_original
    book.title_normalised = normalise_arabic_persian(entry.title_original)
    book.source_url = entry.source_url
    book.volume_count = entry.volume_count
    if category is not None:
        book.category = category
    db.flush()
    set_book_authors(db, book, entry.author_name, entry.author_url)
    db.flush()
    return book


def crawl_metadata(
    db: Session,
    category_urls: list[str],
    limit: int = 20,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
) -> list[Book]:
    """Crawl one or more category listing pages and upsert book metadata rows.

    `limit` caps the total number of books upserted across all categories —
    meant for small test runs, not a full mirror.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(settings)
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)

    books: list[Book] = []
    try:
        for category_url in category_urls:
            if len(books) >= limit:
                break
            if checkpoint.is_done(category_url):
                logger.info("Skipping already-crawled category %s", category_url)
                continue

            try:
                response = client.get(category_url)
            except CrawlError as exc:
                _log(db, category_url, status="error", http_status=exc.http_status, error=str(exc))
                continue

            if response.status_code != 200:
                _log(db, category_url, status="error", http_status=response.status_code)
                continue

            checksum = compute_checksum(response.text)
            entries = parse_category_page(response.text, category_url)
            category_name = category_name_from_url(category_url)
            category = get_or_create_category(db, category_name, category_url) if category_name is not None else None

            for entry in entries[: max(0, limit - len(books))]:
                books.append(upsert_book_from_entry(db, entry, category))

            _log(db, category_url, status="ok", http_status=response.status_code, checksum=checksum)
            checkpoint.mark_done(category_url, checksum)
    finally:
        if own_client:
            client.close()

    return books


def _load_cached_html(db: Session, page: Page | None, html_store: ObjectStore | None) -> str | None:
    """Recover a checkpoint-hit page's HTML from wherever it's cached
    (Page.html_raw, or the R2 archive) without a live re-fetch — used so a
    resumed crawl can still re-derive pagination (next/last page links) for
    volumes whose page 1 was already crawled in an earlier run. Returns None
    if neither cache has it (e.g. it predates both STORE_RAW_HTML and
    STORE_RAW_HTML_R2), in which case the caller falls back to the old
    behaviour of treating the page as fully done with nothing more to learn.
    """
    if page is None:
        return None
    if page.html_raw:
        return page.html_raw
    if html_store is None:
        return None
    book_source_id = db.query(Book.source_book_id).filter(Book.id == page.book_id).scalar()
    if book_source_id is None:
        return None
    try:
        data = html_store.get_bytes(html_archive_key(book_source_id, page.volume_number, page.page_number))
    except Exception:
        return None
    return gzip.decompress(data).decode("utf-8")


def _fetch_and_store_page(
    db: Session,
    url: str,
    client: PoliteClient,
    checkpoint: Checkpoint,
    settings: Settings,
    html_store: ObjectStore | None = None,
    need_pagination: bool = True,
) -> tuple[Page | None, ParsedPage | None]:
    """Fetch one content page, store it, and return both the DB row and the
    parsed page data (the latter is needed by crawl_book to find the next
    page URL, which isn't persisted on the Page model itself).

    If the URL is already in the checkpoint, no HTTP request is made — but
    pagination info (needed by crawl_book/crawl_book_concurrent/
    crawl_full_library's *volume-scan* phase to know how many pages a volume
    has) is re-derived from cached HTML rather than dropped, so a resumed
    crawl doesn't silently stop after just the already-crawled page (see
    _load_cached_html). `need_pagination=False` skips that cache lookup
    entirely — pass it from callers that discard the returned ParsedPage
    anyway (e.g. crawl_full_library's *remaining-pages* phase), since on a
    crawl resumed after tens of thousands of pages were already fetched,
    doing a cache round-trip just to throw the result away made re-skipping
    them take almost as long as fetching them did the first time.
    """
    if checkpoint.is_done(url):
        page = db.query(Page).filter(Page.source_url == url).one_or_none()
        cached_html = _load_cached_html(db, page, html_store) if need_pagination else None
        if cached_html is None:
            logger.info("Skipping already-crawled page %s", url)
            return page, None
        logger.info("Skipping already-crawled page %s (re-parsed cached HTML for pagination)", url)
        return page, parse_page(cached_html, url)

    try:
        response = client.get(url)
    except CrawlError as exc:
        _log(db, url, status="error", http_status=exc.http_status, error=str(exc))
        return None, None

    if response.status_code != 200:
        _log(db, url, status="error", http_status=response.status_code)
        return None, None

    checksum = compute_checksum(response.text)
    parsed = parse_page(response.text, url)

    book = db.query(Book).filter(Book.source_book_id == parsed.source_book_id).one_or_none()
    if book is None:
        book = Book(
            source_book_id=parsed.source_book_id,
            title_original=parsed.book_title,
            title_normalised=normalise_arabic_persian(parsed.book_title),
            source_url=url,
        )
        db.add(book)
        db.flush()
        set_book_authors(db, book, parsed.author_name, parsed.author_url)
        db.flush()

    volume = None
    if parsed.volume_number is not None:
        volume = (
            db.query(Volume)
            .filter(Volume.book_id == book.id, Volume.volume_number == parsed.volume_number)
            .one_or_none()
        )
        if volume is None:
            volume = Volume(book_id=book.id, volume_number=parsed.volume_number)
            db.add(volume)
            db.flush()

    page = (
        db.query(Page)
        .filter(
            Page.book_id == book.id,
            Page.volume_number == parsed.volume_number,
            Page.page_number == parsed.page_number,
        )
        .one_or_none()
    )
    if page is None:
        page = Page(
            book_id=book.id,
            volume_id=volume.id if volume else None,
            volume_number=parsed.volume_number,
            page_number=parsed.page_number or 0,
            source_url=url,
        )
        db.add(page)

    page.text_raw = parsed.text
    page.text_normalised = normalise_arabic_persian(parsed.text) if parsed.text else None
    if html_store is not None:
        archive_html(html_store, parsed.source_book_id, parsed.volume_number, parsed.page_number, response.text)
        page.html_raw = None
    else:
        page.html_raw = response.text if settings.store_raw_html else None
    page.checksum = checksum
    db.commit()

    _log(db, url, status="ok", http_status=response.status_code, checksum=checksum)
    checkpoint.mark_done(url, checksum)
    return page, parsed


def crawl_single_page(
    db: Session,
    url: str,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
    html_store: ObjectStore | None = None,
) -> Page | None:
    """Crawl exactly one content page (.../{book_id}/{volume}/{page}) and store it."""
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(settings)
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)
    html_store = resolve_html_store(settings, html_store)

    try:
        page, _ = _fetch_and_store_page(db, url, client, checkpoint, settings, html_store, need_pagination=False)
        return page
    finally:
        if own_client:
            client.close()


def crawl_book(
    db: Session,
    book_url: str,
    max_pages: int = 10,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
    html_store: ObjectStore | None = None,
) -> list[Page]:
    """Crawl up to `max_pages` pages of a book starting from its first page.

    Follows `next_page_url` rather than guessing URLs, and stops early if the
    book's own "last page" link reports fewer pages than max_pages, or if a
    page has already been crawled (checkpoint hit) and so yields no fresh
    ParsedPage to continue from.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(settings)
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)
    html_store = resolve_html_store(settings, html_store)

    has_volume_and_page = _VOLUME_PAGE_SUFFIX_RE.search(book_url) is not None
    current_url = book_url if has_volume_and_page else f"{book_url.rstrip('/')}/1/1"

    pages: list[Page] = []
    try:
        for _ in range(max_pages):
            page, parsed = _fetch_and_store_page(db, current_url, client, checkpoint, settings, html_store)
            if page is not None:
                pages.append(page)
            if parsed is None:
                # Either an error (already logged) or a checkpoint hit with
                # no fresh pagination info — nothing more we can learn here.
                break

            last_page = last_page_number(parsed)
            if not parsed.next_page_url or (last_page is not None and (parsed.page_number or 0) >= last_page):
                break
            current_url = parsed.next_page_url
    finally:
        if own_client:
            client.close()

    return pages


def crawl_book_concurrent(
    book_url: str,
    max_pages: int = 1000,
    concurrency: int = 8,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
    on_progress: ProgressCallback | None = None,
    html_store: ObjectStore | None = None,
) -> list[Page]:
    """Like crawl_book, but fetches a volume's remaining pages in parallel.

    crawl_book must fetch one page at a time because it only learns the next
    URL by parsing the current page. This function instead fetches page 1
    first (to learn the book id/volume/last-page from its parsed
    `last_page_url`), then dispatches the rest of the range to `concurrency`
    worker threads — each with its own DB session (SQLAlchemy Session isn't
    thread-safe) but sharing one PoliteClient/httpx.Client, and one
    AdaptiveThrottle that forces every worker into a shared cooldown if the
    site starts erroring a lot. Does not take an externally-owned `db`
    (unlike the other crawl_* functions) since every worker needs its own.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(
        settings,
        throttle=AdaptiveThrottle(
            window=settings.crawl_throttle_window,
            error_threshold=settings.crawl_throttle_error_rate,
            cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
        ),
    )
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)
    html_store = resolve_html_store(settings, html_store)

    has_volume_and_page = _VOLUME_PAGE_SUFFIX_RE.search(book_url) is not None
    first_url = book_url if has_volume_and_page else f"{book_url.rstrip('/')}/1/1"

    pages: list[Page] = []
    try:
        db = SessionLocal()
        try:
            first_page, parsed = _fetch_and_store_page(db, first_url, client, checkpoint, settings, html_store)
        finally:
            db.close()

        if first_page is not None:
            pages.append(first_page)
        if parsed is None or parsed.page_number is None or parsed.volume_number is None:
            # Error (already logged) or a checkpoint hit on page 1 itself —
            # either way we don't know the page range to fan out over.
            return pages

        last_page = last_page_number(parsed) or parsed.page_number
        target_last = min(last_page, parsed.page_number + max_pages - 1)
        urls = [
            f"{settings.crawl_base_url}/{parsed.source_book_id}/{parsed.volume_number}/{n}"
            for n in range(parsed.page_number + 1, target_last + 1)
        ]

        def worker(url: str) -> Page | None:
            worker_db = SessionLocal()
            try:
                page, _ = _fetch_and_store_page(
                    worker_db, url, client, checkpoint, settings, html_store, need_pagination=False
                )
                return page
            finally:
                worker_db.close()

        if urls:
            done = 0
            if on_progress is not None:
                on_progress("pages", done, len(urls))
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                for page in executor.map(worker, urls):
                    if page is not None:
                        pages.append(page)
                    done += 1
                    if on_progress is not None:
                        on_progress("pages", done, len(urls))
    finally:
        if own_client:
            client.close()

    return pages


def enrich_uncategorized_books(
    concurrency: int = 8,
    client: PoliteClient | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    """Fill in Category for books with no category by reading the "Subject"
    field off each book's own cover page (see parser.parse_book_subject).

    Only ~two-thirds of books have this field at all (observed on a random
    sample), so this won't reach 100% coverage on its own — books still
    uncategorized afterward simply don't expose the field. Doesn't use the
    Checkpoint (these are one-off lookups, not part of the resumable page
    crawl), so re-running only retries books still missing a category.

    Returns counts: {"checked": N, "categorized": N, "no_subject_found": N}.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(
        settings,
        throttle=AdaptiveThrottle(
            window=settings.crawl_throttle_window,
            error_threshold=settings.crawl_throttle_error_rate,
            cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
        ),
    )

    db = SessionLocal()
    try:
        uncategorized = db.query(Book.id, Book.source_url).filter(Book.category_id.is_(None)).all()
        urls_by_book_id = dict(uncategorized)
        book_ids = list(urls_by_book_id)
    finally:
        db.close()

    counts = {"checked": 0, "categorized": 0, "no_subject_found": 0}
    counts_lock = threading.Lock()

    def worker(book_id: int) -> None:
        url = urls_by_book_id[book_id]
        try:
            response = client.get(url)
        except CrawlError:
            with counts_lock:
                counts["checked"] += 1
            return

        try:
            subject = parse_book_subject(response.text) if response.status_code == 200 else None
        except Exception:
            # One book's malformed/unexpected markup shouldn't take down the
            # whole batch — log and treat like "no subject found".
            logger.exception("Failed to parse subject for book_id=%s (%s)", book_id, url)
            subject = None

        worker_db = SessionLocal()
        try:
            if subject:
                book = worker_db.get(Book, book_id)
                category = get_or_create_category_by_name(worker_db, subject)
                book.category = category
                worker_db.commit()
            with counts_lock:
                counts["checked"] += 1
                if subject:
                    counts["categorized"] += 1
                else:
                    counts["no_subject_found"] += 1
        finally:
            worker_db.close()

    try:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            list(executor.map(worker, book_ids))
    finally:
        if own_client:
            client.close()

    return counts


def crawl_full_library(
    concurrency: int = 8,
    max_pages_per_volume: int = 5000,
    category_name: str | None = None,
    limit_books: int | None = None,
    priority_only: bool = False,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
    on_progress: ProgressCallback | None = None,
    html_store: ObjectStore | None = None,
) -> dict[str, int]:
    """Crawl full text for every book in the DB (or every book in one
    category, or a capped sample), using Book.volume_count from the
    metadata crawl rather than probing — requesting a volume past a book's
    real count just silently redirects to volume 1 (no clean 404), so
    metadata is the only reliable signal here.

    Books are processed in `crawl_priority` order (lower first, NULLs
    last, see models.Book) so a hand-picked subset (e.g. the core hadith
    collections) finishes before the rest of the library. `priority_only`
    restricts the run to books with a `crawl_priority` set at all — see the
    CLI's `set-priority` command for assigning it.

    `on_progress`, if given, is called as `on_progress(phase, done, total)`
    after every page fetched in either phase (`phase` is "volume scan" or
    "full text") — the CLI uses this to drive a live terminal progress bar.
    Kept as a plain callback rather than importing a progress-bar library
    here, since this module is also used by tests/non-interactive callers.

    Two phases, both sharing one PoliteClient/AdaptiveThrottle/Checkpoint
    for maximum concurrency:
      1. Fetch page 1 of every (book, volume) pair concurrently. This also
         stores page 1 itself and reveals each volume's last page number
         (via the page's own "last page" link), so book-level metadata
         inaccuracies in page *count* don't matter — only volume *count*
         needs to be right.
      2. Fetch every remaining page (2..last_page) across every volume in
         one big concurrent batch.
    Interrupting and re-running this resumes via the Checkpoint —
    already-fetched pages in either phase are skipped, not re-fetched.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(
        settings,
        throttle=AdaptiveThrottle(
            window=settings.crawl_throttle_window,
            error_threshold=settings.crawl_throttle_error_rate,
            cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
        ),
    )
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)
    html_store = resolve_html_store(settings, html_store)

    db = SessionLocal()
    try:
        query = db.query(Book.source_book_id, Book.volume_count)
        if category_name:
            query = query.join(Category).filter(Category.name_original == category_name)
        if priority_only:
            query = query.filter(Book.crawl_priority.isnot(None))
        rows = query.order_by(Book.crawl_priority.is_(None), Book.crawl_priority, Book.id).all()
        if limit_books:
            rows = rows[:limit_books]
    finally:
        db.close()

    first_page_urls = [
        f"{settings.crawl_base_url}/{source_book_id}/{volume}/1"
        for source_book_id, volume_count in rows
        for volume in range(1, (volume_count or 1) + 1)
    ]

    stats = {
        "books": len(rows),
        "volumes": len(first_page_urls),
        "first_pages_done": 0,
        "remaining_pages_done": 0,
        "remaining_pages_total": 0,
    }

    def fetch_first_page(url: str) -> ParsedPage | None:
        worker_db = SessionLocal()
        try:
            _, parsed = _fetch_and_store_page(worker_db, url, client, checkpoint, settings, html_store)
            return parsed
        finally:
            worker_db.close()

    def fetch_remaining_page(url: str) -> None:
        worker_db = SessionLocal()
        try:
            _fetch_and_store_page(worker_db, url, client, checkpoint, settings, html_store, need_pagination=False)
        finally:
            worker_db.close()

    try:
        remaining_urls: list[str] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            for parsed in executor.map(fetch_first_page, first_page_urls):
                stats["first_pages_done"] += 1
                if on_progress is not None:
                    on_progress("volume scan", stats["first_pages_done"], stats["volumes"])
                if stats["first_pages_done"] % 200 == 0:
                    logger.info(
                        "Phase 1/2 (volume scan): %d/%d", stats["first_pages_done"], stats["volumes"]
                    )
                if parsed is None or parsed.volume_number is None or parsed.page_number is None:
                    continue
                last_page = last_page_number(parsed) or parsed.page_number
                target_last = min(last_page, parsed.page_number + max_pages_per_volume - 1)
                remaining_urls.extend(
                    f"{settings.crawl_base_url}/{parsed.source_book_id}/{parsed.volume_number}/{n}"
                    for n in range(parsed.page_number + 1, target_last + 1)
                )

        logger.info(
            "Phase 1/2 complete: %d volumes scanned, %d remaining pages queued",
            stats["first_pages_done"],
            len(remaining_urls),
        )
        stats["remaining_pages_total"] = len(remaining_urls)
        if on_progress is not None:
            on_progress("full text", 0, len(remaining_urls))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            for _ in executor.map(fetch_remaining_page, remaining_urls):
                stats["remaining_pages_done"] += 1
                if on_progress is not None:
                    on_progress("full text", stats["remaining_pages_done"], len(remaining_urls))
                if stats["remaining_pages_done"] % 500 == 0:
                    logger.info(
                        "Phase 2/2 (full text): %d/%d", stats["remaining_pages_done"], len(remaining_urls)
                    )
    finally:
        if own_client:
            client.close()

    return stats


# --- Cloud-buffer pipeline -------------------------------------------------
#
# Lets a cloud worker (e.g. Railway) crawl 24/7 without needing 24/7 storage
# of its own: it batches fetched pages into gzipped NDJSON and pushes them to
# an ObjectStore (see cloudstore.py) instead of a database. A separate
# process running wherever long-term storage actually lives (e.g. a home
# machine, via drain_cloud_buffer) drains the buffer whenever it's online.
#
# Two independent Checkpoint instances give the two-stage durability this
# needs: the cloud-side checkpoint marks a URL done only after its batch is
# uploaded (a crash before upload just re-fetches on restart); the drain-side
# checkpoint marks a batch done only after it's upserted into the real DB
# *and* deleted from the store (a crash mid-batch just re-processes that one
# batch — upserting is idempotent, so reprocessing is harmless).


def _serialize_batch(records: list[dict]) -> bytes:
    ndjson = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    return gzip.compress(ndjson.encode("utf-8"))


def _deserialize_batch(data: bytes) -> list[dict]:
    ndjson = gzip.decompress(data).decode("utf-8")
    return [json.loads(line) for line in ndjson.splitlines() if line.strip()]


def _fetch_page_record(
    url: str, client: PoliteClient, checkpoint: Checkpoint, settings: Settings
) -> tuple[dict | None, ParsedPage | None]:
    """Like _fetch_and_store_page but for the cloud-buffer pipeline: no DB
    access at all, just fetch + parse + return a flat dict ready for NDJSON.
    """
    if checkpoint.is_done(url):
        return None, None

    try:
        response = client.get(url)
    except CrawlError:
        return None, None
    if response.status_code != 200:
        return None, None

    checksum = compute_checksum(response.text)
    parsed = parse_page(response.text, url)
    record = {
        "source_book_id": parsed.source_book_id,
        "volume_number": parsed.volume_number,
        "page_number": parsed.page_number,
        "text_raw": parsed.text,
        "html_raw": response.text if settings.store_raw_html else None,
        "source_url": url,
        "checksum": checksum,
    }
    checkpoint.mark_done(url, checksum)
    return record, parsed


def crawl_to_cloud_buffer(
    book_list: list[dict],
    store: ObjectStore,
    batch_size: int = 500,
    batch_prefix: str = "pages/",
    concurrency: int = 8,
    max_pages_per_volume: int = 5000,
    client: PoliteClient | None = None,
    checkpoint: Checkpoint | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    """Cloud-side half of the buffer pipeline.

    `book_list` is `[{"source_book_id": ..., "volume_count": ...}, ...]` —
    a flat export (see the `export-book-list` CLI command) rather than a DB
    query, so the cloud worker doesn't need any database at all, just this
    file shipped with the deploy.

    The `checkpoint` passed in only needs to survive the *current* run, not
    across restarts: if the worker restarts, some already-uploaded pages get
    re-fetched and re-uploaded as a new batch. That's wasted crawl time, not
    a correctness problem — draining is idempotent.
    """
    settings = settings or get_settings()
    own_client = client is None
    client = client or PoliteClient(
        settings,
        throttle=AdaptiveThrottle(
            window=settings.crawl_throttle_window,
            error_threshold=settings.crawl_throttle_error_rate,
            cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
        ),
    )
    checkpoint = checkpoint or Checkpoint(DEFAULT_CHECKPOINT_PATH)

    first_page_urls = [
        f"{settings.crawl_base_url}/{book['source_book_id']}/{volume}/1"
        for book in book_list
        for volume in range(1, (book.get("volume_count") or 1) + 1)
    ]

    stats = {
        "books": len(book_list),
        "volumes": len(first_page_urls),
        "first_pages_done": 0,
        "remaining_pages_done": 0,
        "remaining_pages_total": 0,
        "batches_uploaded": 0,
    }

    buffer: list[dict] = []
    buffer_lock = threading.Lock()

    def flush_buffer(force: bool = False) -> None:
        with buffer_lock:
            if not buffer or (not force and len(buffer) < batch_size):
                return
            take = len(buffer) if force else batch_size
            batch = buffer[:take]
            del buffer[:take]
        if not batch:
            return
        key = f"{batch_prefix}{uuid.uuid4().hex}.jsonl.gz"
        store.put_bytes(key, _serialize_batch(batch))
        with buffer_lock:
            stats["batches_uploaded"] += 1

    def buffer_record(record: dict | None) -> None:
        if record is None:
            return
        with buffer_lock:
            buffer.append(record)
        flush_buffer()

    def fetch_first_page(url: str) -> ParsedPage | None:
        record, parsed = _fetch_page_record(url, client, checkpoint, settings)
        buffer_record(record)
        return parsed

    def fetch_remaining_page(url: str) -> None:
        record, _ = _fetch_page_record(url, client, checkpoint, settings)
        buffer_record(record)

    try:
        remaining_urls: list[str] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            for parsed in executor.map(fetch_first_page, first_page_urls):
                stats["first_pages_done"] += 1
                if stats["first_pages_done"] % 200 == 0:
                    logger.info(
                        "Cloud phase 1/2 (volume scan): %d/%d", stats["first_pages_done"], stats["volumes"]
                    )
                if parsed is None or parsed.volume_number is None or parsed.page_number is None:
                    continue
                last_page = last_page_number(parsed) or parsed.page_number
                target_last = min(last_page, parsed.page_number + max_pages_per_volume - 1)
                remaining_urls.extend(
                    f"{settings.crawl_base_url}/{parsed.source_book_id}/{parsed.volume_number}/{n}"
                    for n in range(parsed.page_number + 1, target_last + 1)
                )

        logger.info(
            "Cloud phase 1/2 complete: %d volumes scanned, %d remaining pages queued",
            stats["first_pages_done"],
            len(remaining_urls),
        )
        stats["remaining_pages_total"] = len(remaining_urls)

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            for _ in executor.map(fetch_remaining_page, remaining_urls):
                stats["remaining_pages_done"] += 1
                if stats["remaining_pages_done"] % 500 == 0:
                    logger.info(
                        "Cloud phase 2/2 (full text): %d/%d, %d batches uploaded",
                        stats["remaining_pages_done"],
                        len(remaining_urls),
                        stats["batches_uploaded"],
                    )

        flush_buffer(force=True)
    finally:
        if own_client:
            client.close()

    return stats


def _upsert_page_record(db: Session, record: dict, html_store: ObjectStore | None = None) -> Page:
    """Upsert one page-record dict (from a drained cloud batch) into the
    real DB. The book should already exist with full metadata from the
    local metadata crawl — book_list.json is exported from the same catalog
    — so the "book is None" branch here is a defensive fallback, not the
    expected path.
    """
    book = db.query(Book).filter(Book.source_book_id == record["source_book_id"]).one_or_none()
    if book is None:
        logger.warning(
            "Drained a page for unknown book_id=%s — creating a bare placeholder book row",
            record["source_book_id"],
        )
        book = Book(
            source_book_id=record["source_book_id"],
            title_original="",
            title_normalised="",
            source_url=record["source_url"],
        )
        db.add(book)
        db.flush()

    volume = None
    if record["volume_number"] is not None:
        volume = (
            db.query(Volume)
            .filter(Volume.book_id == book.id, Volume.volume_number == record["volume_number"])
            .one_or_none()
        )
        if volume is None:
            volume = Volume(book_id=book.id, volume_number=record["volume_number"])
            db.add(volume)
            db.flush()

    page = (
        db.query(Page)
        .filter(
            Page.book_id == book.id,
            Page.volume_number == record["volume_number"],
            Page.page_number == record["page_number"],
        )
        .one_or_none()
    )
    if page is None:
        page = Page(
            book_id=book.id,
            volume_id=volume.id if volume else None,
            volume_number=record["volume_number"],
            page_number=record["page_number"] or 0,
            source_url=record["source_url"],
        )
        db.add(page)

    page.text_raw = record["text_raw"]
    page.text_normalised = normalise_arabic_persian(record["text_raw"]) if record["text_raw"] else None
    html = record.get("html_raw")
    if html_store is not None and html:
        archive_html(html_store, record["source_book_id"], record["volume_number"], record["page_number"], html)
        page.html_raw = None
    else:
        page.html_raw = html
    page.checksum = record["checksum"]
    db.flush()
    return page


def drain_cloud_buffer(
    store: ObjectStore,
    drain_checkpoint: Checkpoint,
    batch_prefix: str = "pages/",
    session_factory=SessionLocal,
    settings: Settings | None = None,
    html_store: ObjectStore | None = None,
) -> dict[str, int]:
    """Local-side half of the buffer pipeline: pull batches uploaded by
    crawl_to_cloud_buffer, upsert into the real DB, delete from the store.

    When store_raw_html_r2 is on, each page's html_raw is archived (see
    archive_html) instead of written into the DB column. Reuses `store`
    itself for this (same bucket, "html/" key prefix instead of
    `batch_prefix`) unless a different `html_store` is given — no need for a
    second ObjectStore/client just to write under a different prefix.
    """
    settings = settings or get_settings()
    if html_store is None:
        html_store = store if settings.store_raw_html_r2 else None

    stats = {"batches_seen": 0, "batches_drained": 0, "pages_upserted": 0}
    keys = store.list_keys(batch_prefix)
    for key in keys:
        stats["batches_seen"] += 1
        if drain_checkpoint.is_done(key):
            continue

        records = _deserialize_batch(store.get_bytes(key))

        db = session_factory()
        try:
            for record in records:
                _upsert_page_record(db, record, html_store)
            db.commit()
        finally:
            db.close()

        store.delete(key)
        drain_checkpoint.mark_done(key, checksum=str(len(records)))
        stats["batches_drained"] += 1
        stats["pages_upserted"] += len(records)
        logger.info("Drained batch %s (%d pages)", key, len(records))

    return stats
