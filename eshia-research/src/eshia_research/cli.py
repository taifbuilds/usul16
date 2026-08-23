"""Typer CLI entry point.

    python -m eshia_research.cli <command> ...
"""

import logging
import sys

import typer
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

# Windows terminals often default stdout/stderr to a non-UTF-8 codepage
# (e.g. cp1252), which can't encode Arabic/Persian text. Force UTF-8 so
# titles, search results, and page text print correctly everywhere.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

from eshia_research.cloudstore import make_object_store
from eshia_research.commentary.mirat_al_uqul import (
    MIRAT_AL_UQUL_SOURCE_BOOK_ID,
    index_mirat_al_uqul,
)
from eshia_research.commentary.sources import get_commentary_source
from eshia_research.config import get_settings
from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID, CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.crawler.client import AdaptiveThrottle, Checkpoint, PoliteClient
from eshia_research.crawler.jobs import (
    DEFAULT_CHECKPOINT_PATH,
    ProgressCallback,
    crawl_book,
    crawl_book_concurrent,
    crawl_full_library,
    crawl_metadata,
    crawl_single_page,
    crawl_to_cloud_buffer,
    drain_cloud_buffer,
    enrich_uncategorized_books,
)
from eshia_research.db import SessionLocal, init_db as _init_db
from eshia_research.hadith_extractor import rebuild_hadith_index
from eshia_research.rijal.mashyakha import (
    audit_faqih_mashyakha_coverage,
    crawl_faqih_mashyakha,
    import_faqih_mashyakha_paths,
    load_mashyakha_snapshot,
    materialize_faqih_mashyakha_expansions,
    write_mashyakha_snapshot,
)
from eshia_research.search import search_pages

app = typer.Typer(help="eshia_research crawler/search CLI")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# httpx logs one INFO line per request — with the live progress bars below,
# that's the same information shown twice and visually fights the bar's
# in-place redraw. Our own crawler logs (eshia_research.*) stay at INFO.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _progress_columns() -> tuple:
    """Columns for the live terminal progress bars used by long-running
    crawl commands: a bar, an N/total count, elapsed time, and an ETA
    estimated from the current throughput (rich.progress.TimeRemainingColumn)."""
    return (
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("elapsed"),
        TimeElapsedColumn(),
        TextColumn("ETA"),
        TimeRemainingColumn(),
    )


def _make_on_progress(progress: Progress) -> ProgressCallback:
    """Adapts crawl_*'s on_progress(phase, done, total) callback into rich
    Progress task updates, creating a new bar the first time a phase name
    is seen (crawl_full_library reports two phases in sequence: "volume
    scan" then "full text")."""
    tasks: dict[str, TaskID] = {}

    def on_progress(phase: str, done: int, total: int) -> None:
        if phase not in tasks:
            tasks[phase] = progress.add_task(phase, total=total, completed=done)
        else:
            progress.update(tasks[phase], total=total, completed=done)

    return on_progress


@app.command("init-db")
def init_db() -> None:
    """Create all tables (quick start for local dev; use Alembic for real migrations)."""
    _init_db()
    typer.echo("Database initialised.")


@app.command("crawl-faqih-mashyakha")
def crawl_faqih_mashyakha_cmd(
    output_path: str = typer.Option(..., "--output-path", help="Path for the source-preserved JSON snapshot."),
    delay_seconds: float = typer.Option(0.25, "--delay-seconds", min=0.0),
) -> None:
    """Fetch Faqih's public Mashyakha volume into a reviewable snapshot."""
    entries = crawl_faqih_mashyakha(delay_seconds=delay_seconds)
    destination = write_mashyakha_snapshot(entries, output_path)
    typer.echo(f"Wrote {len(entries)} source entries to {destination}")


@app.command("import-faqih-mashyakha")
def import_faqih_mashyakha_cmd(
    snapshot_path: str = typer.Option(..., "--snapshot-path", help="Snapshot made by crawl-faqih-mashyakha."),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import Mashyakha source witnesses without rewriting Faqih chains."""
    entries = load_mashyakha_snapshot(snapshot_path)
    db = SessionLocal()
    try:
        stats = import_faqih_mashyakha_paths(db, entries)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    finally:
        db.close()
    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}created {stats.created}, updated {stats.updated}; "
        f"parsed {stats.parsed}, topic entries {stats.topic_entries}, "
        f"needs review {stats.needs_review}."
    )


@app.command("audit-faqih-mashyakha")
def audit_faqih_mashyakha_cmd() -> None:
    """Report strict Mashyakha coverage of Faqih's abbreviated openings."""
    db = SessionLocal()
    try:
        report = audit_faqih_mashyakha_coverage(db)
    finally:
        db.close()
    for key, value in report.items():
        typer.echo(f"{key}={value}")


@app.command("materialize-faqih-mashyakha-expansions")
def materialize_faqih_mashyakha_expansions_cmd(
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Create exact source-linked expansion proposals without rewriting chains."""
    db = SessionLocal()
    try:
        stats = materialize_faqih_mashyakha_expansions(db)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    finally:
        db.close()
    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}created {stats.created}, updated {stats.updated}, removed {stats.removed}; "
        f"proposed {stats.proposed}, needs review {stats.needs_review}."
    )


@app.command("crawl-metadata")
def crawl_metadata_cmd(
    category_url: list[str] = typer.Option(
        ..., "--category-url", help="One or more category URLs to crawl, e.g. https://lib.eshia.ir/فقه"
    ),
    limit: int = typer.Option(20, "--limit", help="Max number of books to upsert across all categories"),
) -> None:
    """Crawl metadata from one or more category listing pages."""
    settings = get_settings()
    db = SessionLocal()
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    try:
        with PoliteClient(settings) as client:
            books = crawl_metadata(db, category_url, limit=limit, client=client, checkpoint=checkpoint, settings=settings)
        typer.echo(f"Upserted {len(books)} book(s).")
    finally:
        db.close()


@app.command("crawl-book")
def crawl_book_cmd(
    book_url: str = typer.Option(..., "--book-url", help="Book URL, e.g. https://lib.eshia.ir/26395"),
    max_pages: int = typer.Option(10, "--max-pages", help="Max number of pages to crawl"),
    concurrency: int | None = typer.Option(
        None,
        "--concurrency",
        help=(
            "Parallel workers for fetching pages after the first. Defaults to "
            "CRAWL_CONCURRENCY from settings/.env. >1 switches to "
            "crawl_book_concurrent (fetches the volume's page range in parallel "
            "instead of following next-page links one at a time). See README's "
            "'Fast crawling' section before raising this."
        ),
    ),
) -> None:
    """Crawl up to --max-pages pages of a single book, starting from page 1."""
    settings = get_settings()
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    concurrency = settings.crawl_concurrency if concurrency is None else concurrency

    if concurrency > 1:
        throttle = AdaptiveThrottle(
            window=settings.crawl_throttle_window,
            error_threshold=settings.crawl_throttle_error_rate,
            cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
        )
        with PoliteClient(settings, throttle=throttle) as client, Progress(*_progress_columns()) as progress:
            pages = crawl_book_concurrent(
                book_url,
                max_pages=max_pages,
                concurrency=concurrency,
                client=client,
                checkpoint=checkpoint,
                settings=settings,
                on_progress=_make_on_progress(progress),
            )
        typer.echo(f"Crawled {len(pages)} page(s) with {concurrency} workers.")
        return

    db = SessionLocal()
    try:
        with PoliteClient(settings) as client:
            pages = crawl_book(db, book_url, max_pages=max_pages, client=client, checkpoint=checkpoint, settings=settings)
        typer.echo(f"Crawled {len(pages)} page(s).")
    finally:
        db.close()


@app.command("crawl-mirat-al-uqul")
def crawl_mirat_al_uqul_cmd(
    start_volume: int = typer.Option(1, "--start-volume", min=1, max=26),
    end_volume: int = typer.Option(26, "--end-volume", min=1, max=26),
    max_pages_per_volume: int = typer.Option(5000, "--max-pages-per-volume", min=1),
    concurrency: int | None = typer.Option(None, "--concurrency", min=1),
) -> None:
    """Download the complete eShia edition of Mir'at al-'Uqul (book 71429).

    The standard crawler checkpoint makes this safe to interrupt and rerun.
    Raw source HTML is required because the commentary spans are distinct from
    the copied al-Kafi reports only in the original eShia markup.
    """
    if end_volume < start_volume:
        raise typer.BadParameter("--end-volume must be at least --start-volume")
    settings = get_settings()
    if settings.store_raw_html_r2 or not settings.store_raw_html:
        raise typer.BadParameter(
            "Mir'at al-'Uqul needs STORE_RAW_HTML=true and STORE_RAW_HTML_R2=false so its FootNote markup can be indexed."
        )
    worker_count = settings.crawl_concurrency if concurrency is None else concurrency
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    throttle = AdaptiveThrottle(
        window=settings.crawl_throttle_window,
        error_threshold=settings.crawl_throttle_error_rate,
        cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
    )
    total_pages = 0
    with PoliteClient(settings, throttle=throttle) as client, Progress(*_progress_columns()) as progress:
        for volume in range(start_volume, end_volume + 1):
            task = progress.add_task(f"Mir'at vol. {volume}", total=1)

            def on_progress(_phase: str, done: int, total: int, task_id: TaskID = task) -> None:
                progress.update(task_id, completed=done, total=total)

            pages = crawl_book_concurrent(
                f"{settings.crawl_base_url}/{MIRAT_AL_UQUL_SOURCE_BOOK_ID}/{volume}/1",
                max_pages=max_pages_per_volume,
                concurrency=worker_count,
                client=client,
                checkpoint=checkpoint,
                settings=settings,
                on_progress=on_progress,
            )
            total_pages += len(pages)
    typer.echo(f"Mir'at al-'Uqul crawl complete: {total_pages} fetched page(s) this run.")


@app.command("index-sharh-al-mazandarani")
def index_sharh_al_mazandarani_cmd() -> None:
    """Index al-Mazandarani's Sharh Usul al-Kafi against the Usul and Rawda."""
    from eshia_research.commentary.mazandarani import index_sharh_al_mazandarani

    db = SessionLocal()
    try:
        stats = index_sharh_al_mazandarani(db)
    finally:
        db.close()
    covered = f"{stats.matched}/{stats.target_hadiths}"
    share = 100 * stats.matched / stats.target_hadiths if stats.target_hadiths else 0.0
    # Reports the commentator passed over are not a shortfall, so the rate that
    # measures the pipeline is taken against the units that carry commentary.
    commented = stats.units - stats.no_commentary_in_source
    placed = 100 * stats.matched / commented if commented else 0.0
    typer.echo(
        "Sharh al-Mazandarani index: "
        f"pages={stats.pages_seen}, units={stats.units}, publishable={stats.publishable}, "
        f"matched={stats.matched} (of which {stats.aligned} by chapter position), "
        f"needs_review={stats.needs_review}, unmatched={stats.unmatched}, "
        f"withheld_for_attribution={stats.withheld_attribution}, "
        f"no_commentary_in_source={stats.no_commentary_in_source}. "
        f"Placed {stats.matched}/{commented} of the units that carry commentary "
        f"({placed:.1f}%). Coverage of the Usul+Rawda it addresses: {covered} ({share:.1f}%)."
    )


@app.command("crawl-commentary")
def crawl_commentary_cmd(
    source_key: str = typer.Argument(..., help="e.g. sharh-al-mazandarani"),
    start_volume: int = typer.Option(1, "--start-volume", min=1),
    end_volume: int | None = typer.Option(None, "--end-volume", min=1),
    max_pages_per_volume: int = typer.Option(5000, "--max-pages-per-volume", min=1),
    concurrency: int | None = typer.Option(None, "--concurrency", min=1),
) -> None:
    """Download any registered commentary from eShia, keeping its raw HTML.

    Generic over the source so a new sharh is a descriptor plus this command,
    not another bespoke crawler. Raw HTML is mandatory: the commentary spans
    are distinguishable from the copied reports only in the original markup.
    """
    source = get_commentary_source(source_key)
    source.require_crawlable()
    last_volume = end_volume or source.volume_count
    if not last_volume:
        raise typer.BadParameter(f"{source.key} has no volume count; pass --end-volume")
    if last_volume < start_volume:
        raise typer.BadParameter("--end-volume must be at least --start-volume")
    settings = get_settings()
    if settings.store_raw_html_r2 or not settings.store_raw_html:
        raise typer.BadParameter(
            f"{source.key} needs STORE_RAW_HTML=true and STORE_RAW_HTML_R2=false "
            "so its commentary markup can be indexed."
        )
    worker_count = settings.crawl_concurrency if concurrency is None else concurrency
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    throttle = AdaptiveThrottle(
        window=settings.crawl_throttle_window,
        error_threshold=settings.crawl_throttle_error_rate,
        cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
    )
    total_pages = 0
    with PoliteClient(settings, throttle=throttle) as client, Progress(*_progress_columns()) as progress:
        for volume in range(start_volume, last_volume + 1):
            task = progress.add_task(f"{source.title_en} vol. {volume}", total=1)

            def on_progress(_phase: str, done: int, total: int, task_id: TaskID = task) -> None:
                progress.update(task_id, completed=done, total=total)

            pages = crawl_book_concurrent(
                f"{settings.crawl_base_url}/{source.source_book_id}/{volume}/1",
                max_pages=max_pages_per_volume,
                concurrency=worker_count,
                client=client,
                checkpoint=checkpoint,
                settings=settings,
                on_progress=on_progress,
            )
            total_pages += len(pages)
    typer.echo(f"{source.title_en} crawl complete: {total_pages} fetched page(s) this run.")


@app.command("index-mirat-al-uqul")
def index_mirat_al_uqul_cmd() -> None:
    """Extract Mir'at al-'Uqul sharh blocks and match high-confidence al-Kafi rows."""
    db = SessionLocal()
    try:
        stats = index_mirat_al_uqul(db)
    finally:
        db.close()
    typer.echo(
        "Mir'at al-'Uqul index: "
        f"pages={stats.pages_seen}, reports={stats.source_reports}, extracted={stats.extracted}, "
        f"matched={stats.matched} (of which {stats.aligned} by chapter position), "
        f"needs_review={stats.needs_review}, "
        f"unmatched={stats.unmatched}, malformed={stats.malformed}."
    )


@app.command("crawl-library")
def crawl_library_cmd(
    concurrency: int | None = typer.Option(None, "--concurrency", help="Defaults to CRAWL_CONCURRENCY"),
    max_pages_per_volume: int = typer.Option(5000, "--max-pages-per-volume", help="Safety cap per volume"),
    category: str | None = typer.Option(
        None, "--category", help="Restrict to one category name (e.g. فقه). Default: every book in the DB."
    ),
    limit_books: int | None = typer.Option(None, "--limit-books", help="Cap number of books (for testing)"),
    priority_only: bool | None = typer.Option(
        None,
        "--priority-only/--no-priority-only",
        help="Crawl only books with crawl_priority set (see set-priority). Defaults to CRAWL_PRIORITY_ONLY.",
    ),
) -> None:
    """Crawl full text for every book in the DB (or one --category), using
    stored Book.volume_count to know how many volumes each book has. Books
    are processed in crawl_priority order (lower first, unset last).

    Long-running by design — safe to interrupt (Ctrl+C) and re-run; already
    -fetched pages are skipped via the checkpoint. See README's 'Crawling
    the full library' section for how to run this unattended for the hours
    it takes."""
    settings = get_settings()
    concurrency = settings.crawl_concurrency if concurrency is None else concurrency
    priority_only = settings.crawl_priority_only if priority_only is None else priority_only
    throttle = AdaptiveThrottle(
        window=settings.crawl_throttle_window,
        error_threshold=settings.crawl_throttle_error_rate,
        cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
    )
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    with PoliteClient(settings, throttle=throttle) as client, Progress(*_progress_columns()) as progress:
        stats = crawl_full_library(
            concurrency=concurrency,
            max_pages_per_volume=max_pages_per_volume,
            category_name=category,
            limit_books=limit_books,
            priority_only=priority_only,
            client=client,
            checkpoint=checkpoint,
            settings=settings,
            on_progress=_make_on_progress(progress),
        )
    typer.echo(
        f"Books: {stats['books']}, volumes: {stats['volumes']}, "
        f"first pages done: {stats['first_pages_done']}, "
        f"remaining pages done: {stats['remaining_pages_done']}/{stats['remaining_pages_total']}."
    )


@app.command("set-priority")
def set_priority_cmd(
    title_contains: str | None = typer.Option(
        None, "--title-contains", help="Substring match against Book.title_original"
    ),
    book_id: list[int] = typer.Option(
        [], "--book-id", help="Exact Book.id to target (repeatable). Use when --title-contains is ambiguous."
    ),
    priority: int | None = typer.Option(None, "--priority", help="Lower = crawled sooner by crawl-library"),
    clear: bool = typer.Option(False, "--clear", help="Unset crawl_priority (set to NULL) instead of assigning one"),
) -> None:
    """Set or clear crawl_priority on books matched by --title-contains
    and/or --book-id. Prints each matched book so you can confirm before
    it's used to drive a crawl — eShia often has multiple editions of the
    same work under similar titles, so --title-contains alone can
    over-match."""
    from eshia_research.models import Book

    if not title_contains and not book_id:
        typer.echo("Provide --title-contains and/or --book-id.", err=True)
        raise typer.Exit(1)
    if not clear and priority is None:
        typer.echo("Provide --priority, or pass --clear to unset it.", err=True)
        raise typer.Exit(1)

    db = SessionLocal()
    try:
        query = db.query(Book)
        if title_contains and book_id:
            query = query.filter(Book.title_original.contains(title_contains) | Book.id.in_(book_id))
        elif title_contains:
            query = query.filter(Book.title_original.contains(title_contains))
        else:
            query = query.filter(Book.id.in_(book_id))
        matches = query.all()
        if not matches:
            typer.echo("No books matched.", err=True)
            raise typer.Exit(1)
        new_value = None if clear else priority
        for book in matches:
            book.crawl_priority = new_value
            typer.echo(f"  [{book.id}] {book.title_original} (priority={new_value})")
        db.commit()
        typer.echo(f"Updated {len(matches)} book(s).")
    finally:
        db.close()


@app.command("enrich-categories")
def enrich_categories_cmd(
    concurrency: int | None = typer.Option(None, "--concurrency", help="Defaults to CRAWL_CONCURRENCY"),
) -> None:
    """Fill in Category for currently-uncategorized books via each book's
    own "Subject" field (not every book has one — see jobs.enrich_uncategorized_books)."""
    settings = get_settings()
    concurrency = settings.crawl_concurrency if concurrency is None else concurrency
    throttle = AdaptiveThrottle(
        window=settings.crawl_throttle_window,
        error_threshold=settings.crawl_throttle_error_rate,
        cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
    )
    with PoliteClient(settings, throttle=throttle) as client:
        counts = enrich_uncategorized_books(concurrency=concurrency, client=client, settings=settings)
    typer.echo(
        f"Checked {counts['checked']}, newly categorized {counts['categorized']}, "
        f"no subject field found {counts['no_subject_found']}."
    )


@app.command("crawl-page")
def crawl_page_cmd(
    url: str = typer.Option(..., "--url", help="Exact content page URL, e.g. https://lib.eshia.ir/26395/1/1"),
) -> None:
    """Crawl exactly one content page."""
    settings = get_settings()
    db = SessionLocal()
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    try:
        with PoliteClient(settings) as client:
            page = crawl_single_page(db, url, client=client, checkpoint=checkpoint, settings=settings)
        if page is None:
            typer.echo("Failed to crawl page (see crawl_logs table for details).", err=True)
            raise typer.Exit(1)
        typer.echo(f"Stored page {page.id} (book_id={page.book_id}, page_number={page.page_number}).")
    finally:
        db.close()


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """Search stored page text and book titles."""
    db = SessionLocal()
    try:
        hits = search_pages(db, query, limit=limit)
        if not hits:
            typer.echo("No results.")
            return
        for hit in hits:
            typer.echo(f"[{hit.book.title_original}] p.{hit.page.page_number}: {hit.snippet}")
    finally:
        db.close()


@app.command("show-page")
def show_page_cmd(
    book_id: int = typer.Option(..., "--book-id"),
    volume: int = typer.Option(..., "--volume"),
    page: int = typer.Option(..., "--page"),
) -> None:
    """Print the stored text of a specific book/volume/page."""
    from eshia_research.models import Page  # local import to keep CLI import time low

    db = SessionLocal()
    try:
        row = (
            db.query(Page)
            .filter(Page.book_id == book_id, Page.volume_number == volume, Page.page_number == page)
            .one_or_none()
        )
        if row is None:
            typer.echo("Page not found.", err=True)
            raise typer.Exit(1)
        typer.echo(row.text_raw or "(no text — possibly an image-only scanned page)")
    finally:
        db.close()


@app.command("rebuild-hadith-index")
def rebuild_hadith_index_cmd(
    source_book_id: list[str] = typer.Option(
        [],
        "--source-book-id",
        help=(
            "eShia source_book_id to index (repeatable). Defaults to the canonical Four Books: "
            + ", ".join(CANONICAL_FOUR_BOOK_SOURCE_IDS)
        ),
    ),
    book_id: list[int] = typer.Option(
        [], "--book-id", help="Local Book.id to index (repeatable). Overrides the default canonical set."
    ),
    include_excluded_editions: bool = typer.Option(
        False,
        "--include-excluded-editions",
        help="Allow duplicate/deprioritized editions such as al-Kafi Dar al-Hadith.",
    ),
) -> None:
    """Rebuild persistent hadith rows from stored page text.

    By default this indexes the canonical Four Books and excludes the
    duplicate al-Kafi Dar al-Hadith edition from the research layer.
    """
    db = SessionLocal()
    try:
        stats = rebuild_hadith_index(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
            include_excluded_editions=include_excluded_editions,
        )
    finally:
        db.close()

    typer.echo(
        f"Indexed {stats.hadiths} hadith(s) from {stats.pages} page(s) "
        f"across {stats.books} book(s); merged {stats.continuations_merged} continuation(s)."
    )


@app.command("rebuild-chain-index")
def rebuild_chain_index_cmd(
    source_book_id: list[str] = typer.Option(
        [],
        "--source-book-id",
        help=(
            "eShia source_book_id to index (repeatable). Defaults to the canonical Four Books: "
            + ", ".join(CANONICAL_FOUR_BOOK_SOURCE_IDS)
        ),
    ),
    book_id: list[int] = typer.Option(
        [], "--book-id", help="Local Book.id to index (repeatable). Overrides the default canonical set."
    ),
) -> None:
    """Rebuild isnad chains (chains/chain_nodes) from hadiths.isnad_raw.

    Stage-1 tokenization only — no narrator identity resolution. Chains the
    tokenizer could not parse confidently are stored with
    review_status='needs_review' and machine-readable flags.
    """
    from eshia_research.isnad.indexer import rebuild_chain_index

    db = SessionLocal()
    try:
        stats = rebuild_chain_index(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
        )
    finally:
        db.close()

    typer.echo(
        f"Tokenized {stats.hadiths} isnad(s) into {stats.chains} chain(s) / "
        f"{stats.nodes} node(s); {stats.needs_review} chain(s) need review "
        f"({stats.clean_ratio:.1%} clean)."
    )
    for flag, count in stats.flag_counts.most_common():
        typer.echo(f"  flag {flag}: {count}")


@app.command("rebuild-mujam-index")
def rebuild_mujam_index_cmd(
    source_book_id: str = typer.Option(
        "14036",
        "--source-book-id",
        help="eShia source_book_id for Mu'jam Rijal al-Hadith.",
    ),
) -> None:
    """Parse Mu'jam Rijal al-Hadith entries into narrator/rijal tables.

    This is Phase 2A/2B of the isnad graph: numbered Mu'jam entries become
    canonical narrator identities plus source-entry text, quoted statements,
    title aliases, and occurrence notes used later by the resolver.
    """
    from eshia_research.rijal.indexer import rebuild_mujam_index

    db = SessionLocal()
    try:
        stats = rebuild_mujam_index(db, source_book_id=source_book_id)
    finally:
        db.close()

    typer.echo(
        f"Indexed {stats.entries} Mu'jam entries from {stats.pages} page(s); "
        f"created {stats.narrators_created} narrator(s), updated {stats.narrators_updated}."
    )
    typer.echo(
        f"Extracted {stats.aliases} alias(es), {stats.statements} statement(s), "
        f"{stats.occurrences} occurrence note(s)."
    )
    typer.echo(
        f"Headers seen {stats.headers_seen}, ignored {stats.headers_ignored}, "
        f"sequence gaps {stats.sequence_gaps}, last entry {stats.last_entry_number}; "
        f"{stats.needs_review} entries need review."
    )
    for flag, count in stats.flag_counts.most_common():
        typer.echo(f"  flag {flag}: {count}")


@app.command("build-person-layer")
def build_person_layer_cmd() -> None:
    """Bootstrap the Tamyiz Engine person layer (Phase A).

    Creates persons, surface forms (via the name grammar), bare-form proxy
    flags, entry links (including al-Khoei's own tamyiz cross-references),
    nasab-asserted father relations, the 14 Ma'sumin, and Kulayni's
    documented 'iddah rosters. Rebuild-style: person tables are wiped and
    repopulated; chain and rijal source tables are never touched.
    """
    from eshia_research.rijal.person_builder import build_person_layer

    _init_db()  # create the new person tables if missing
    db = SessionLocal()
    try:
        with Progress(*_progress_columns()) as progress:
            stats = build_person_layer(db, on_progress=_make_on_progress(progress))
        db.commit()
    finally:
        db.close()

    typer.echo(
        f"Created {stats['persons']} person(s) "
        f"({stats['masum_persons']} Ma'sumin, {stats['bare_form_persons']} bare-form proxies)."
    )
    typer.echo(
        f"Generated {stats['surface_forms']} surface form(s); "
        f"{stats['entry_links']} entry link(s) of which {stats['tamyiz_links']} tamyiz "
        f"cross-references and {stats['bare_form_links']} bare-form evidence links."
    )
    typer.echo(
        f"Father relations: {stats['father_relations']} asserted by nasab, "
        f"{stats['father_relations_matched']} uniquely matched to a person."
    )
    typer.echo(f"Collective roster members seeded: {stats['roster_members']}.")
    typer.echo(
        "External rijal witnesses relinked: "
        f"{stats['external_exact_links']} exact, "
        f"{stats['external_full_form_links']} unique full-form; "
        f"{stats['external_ambiguous_entries']} ambiguous and "
        f"{stats['external_unmatched_entries']} unmatched."
    )


@app.command("crawl-external-rijal")
def crawl_external_rijal_cmd(
    output_path: str = typer.Option(
        "scratch_audit/shiaresearch_rijal_snapshot.json.gz",
        "--output-path",
        help="Local JSON or JSON.GZ snapshot path.",
    ),
    delay_seconds: float = typer.Option(
        0.05,
        "--delay-seconds",
        min=0.0,
        help="Delay between source pages.",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Reuse already-complete works in an existing snapshot.",
    ),
) -> None:
    """Snapshot permitted external rijal indexes for offline import."""
    from eshia_research.rijal.shiaresearch import crawl_external_rijal

    with Progress(*_progress_columns()) as progress:
        stats = crawl_external_rijal(
            output_path,
            delay_seconds=delay_seconds,
            resume=resume,
            on_progress=_make_on_progress(progress),
        )
    typer.echo(
        f"Snapshot complete: {stats.entries} records across {stats.works} works "
        f"({stats.requests} HTTP requests; {stats.resumed_works} works resumed)."
    )
    typer.echo(f"Saved locally to {output_path}.")


@app.command("import-external-rijal")
def import_external_rijal_cmd(
    snapshot_path: str = typer.Option(
        "scratch_audit/shiaresearch_rijal_snapshot.json.gz",
        "--snapshot-path",
        help="Snapshot produced by crawl-external-rijal.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Commit the import. Without this flag the command is a dry run.",
    ),
) -> None:
    """Upsert witnesses, resolve identities, and bootstrap genuinely missing people."""
    from eshia_research.rijal.shiaresearch import import_external_rijal, load_snapshot

    _init_db()
    snapshot = load_snapshot(snapshot_path)
    db = SessionLocal()
    try:
        stats = import_external_rijal(db, snapshot)
        if apply:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()
    prefix = "" if apply else "DRY-RUN: "
    typer.echo(
        f"{prefix}{stats.created} records created, {stats.updated} updated across "
        f"{stats.works} works; {stats.metadata_only} metadata-only, "
        f"{stats.full_text} with full text."
    )
    typer.echo(
        f"Identity links: {stats.exact} exact, {stats.full_form} full-form, "
        f"{stats.name_variant} name-variant, {stats.alias} alias, "
        f"{stats.equivalent} same-person-equivalent, "
        f"{stats.source_number} source-number, "
        f"{stats.text_witness} text-witness, {stats.fuzzy} clear fuzzy."
    )
    typer.echo(
        f"External identities: {stats.identities_created} created/rehydrated covering "
        f"{stats.external_identity_entries} records; {stats.headings} non-person headings, "
        f"{stats.multi_subject} multi-person headings."
    )
    typer.echo(
        f"{stats.ambiguous} ambiguous ({stats.candidate_links} candidate links), "
        f"{stats.unmatched} unmatched."
    )


@app.command("audit-external-rijal")
def audit_external_rijal_cmd() -> None:
    """Report local external witness coverage without changing the database."""
    from eshia_research.rijal.shiaresearch import audit_external_rijal

    db = SessionLocal()
    try:
        stats = audit_external_rijal(db)
    finally:
        db.close()
    typer.echo(
        f"External rijal: {stats.entries} records; {stats.metadata_only} metadata-only."
    )
    typer.echo(
        f"Links: {stats.exact} exact, {stats.full_form} full-form, "
        f"{stats.name_variant} name-variant, {stats.alias} alias, "
        f"{stats.equivalent} equivalent, {stats.source_number} source-number, "
        f"{stats.text_witness} text-witness, {stats.fuzzy} fuzzy, "
        f"{stats.created} external-created."
    )
    typer.echo(
        f"Classified: {stats.headings} non-person headings, "
        f"{stats.multi_subject} multi-person headings; "
        f"{stats.ambiguous} ambiguous, {stats.unmatched} unmatched."
    )
    for source_id, count in stats.per_source.items():
        typer.echo(f"  {source_id}: {count}")


@app.command("materialize-same-person-links")
def materialize_same_person_links_cmd(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without committing database changes."),
) -> None:
    """Materialize al-Khoei tamyiz snippets into same-person relations.

    This is a non-destructive Phase A.2 pass: it reads the existing
    `person_entry_links.tamyiz_discussion` evidence and writes auditable
    `person_relations.same_person_as` rows for the conservative subset
    (previous/next entry references and exact named targets). It never merges
    or deletes person rows.
    """
    from eshia_research.rijal.identity_links import materialize_same_person_relations

    db = SessionLocal()
    try:
        stats = materialize_same_person_relations(db, commit=not dry_run)
        if dry_run:
            db.rollback()
    finally:
        db.close()

    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}examined {stats.tamyiz_links_examined} tamyiz link(s); "
        f"created {stats.relation_rows_created} same-person relation row(s) "
        f"across {stats.pairs_created} pair(s)."
    )
    typer.echo(
        f"Skipped: mushtarak {stats.skipped_mushtarak}, proxy {stats.skipped_proxy}, "
        f"explicit negation {stats.skipped_negated}, ambiguous target {stats.skipped_ambiguous_target}, "
        f"no target {stats.skipped_no_target}; existing relation rows {stats.existing_relations}; "
        f"removed stale negated rows {stats.negated_relations_removed}."
    )
    for method, count in stats.method_counts.most_common(12):
        typer.echo(f"  {method}: {count}")


@app.command("build-tabaqat")
def build_tabaqat_cmd(
    source_book_id: list[str] = typer.Option(
        [], "--source-book-id",
        help="eShia source_book_id whose resolved edges feed propagation (repeatable).",
    ),
    book_id: list[int] = typer.Option([], "--book-id", help="Local Book.id (repeatable)."),
) -> None:
    """Build the tabaqat (generation) lattice (Tamyiz Engine Phase C).

    Anchors persons from the 14 fixed Imam layers and Imam-companionship
    statements, then propagates generation intervals over confident resolved
    transmission edges. Writes person_generations. Requires build-person-layer
    and resolve-persons to have run first.
    """
    from eshia_research.rijal.tabaqat import build_tabaqat

    db = SessionLocal()
    try:
        with Progress(*_progress_columns()) as progress:
            stats = build_tabaqat(
                db,
                source_book_ids=source_book_id or None,
                book_ids=book_id or None,
                on_progress=_make_on_progress(progress),
            )
    finally:
        db.close()

    typer.echo(
        f"Constrained {stats['persons_constrained']} person(s): "
        f"{stats['imam_fixed']} fixed Imams, {stats['ashab_anchors']} companionship anchors, "
        f"{stats['propagated_only']} propagated-only."
    )
    typer.echo(
        f"Propagation over {stats['edges']} confident edge(s); "
        f"{stats['tight_points']} persons pinned to a single layer; "
        f"{stats['conflicts']} conflict(s) flagged."
    )


@app.command("refine-tabaqat")
def refine_tabaqat_cmd(
    source_book_id: list[str] = typer.Option([], "--source-book-id", help="eShia source_book_id (repeatable)."),
    book_id: list[int] = typer.Option([], "--book-id", help="Local Book.id (repeatable)."),
    tolerance: int = typer.Option(1, "--tolerance", help="Allowed generation slack (layers)."),
) -> None:
    """Disambiguate ambiguous mentions by generation (Tamyiz Engine Phase C).

    Uses person_generations to pick the one candidate that fits the chain's
    generation walk (e.g. «أبو جعفر ع» -> al-Baqir vs al-Jawad). Upgrades those
    mention_resolutions to resolved with a tabaqa dalil. Run after build-tabaqat.
    """
    from eshia_research.rijal.tabaqat import refine_with_tabaqat

    db = SessionLocal()
    try:
        with Progress(*_progress_columns()) as progress:
            stats = refine_with_tabaqat(
                db,
                source_book_ids=source_book_id or None,
                book_ids=book_id or None,
                tolerance=tolerance,
                on_progress=_make_on_progress(progress),
            )
    finally:
        db.close()

    typer.echo(
        f"Examined {stats['nodes_examined']} ambiguous node(s); disambiguated "
        f"{stats['imam_disambiguated']} imam(s) and {stats['narrator_disambiguated']} narrator(s) by generation."
    )


@app.command("refine-compiler-priors")
def refine_compiler_priors_cmd(
    source_book_id: list[str] = typer.Option([], "--source-book-id", help="eShia source_book_id (repeatable)."),
    book_id: list[int] = typer.Option([], "--book-id", help="Local Book.id (repeatable)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without committing database changes."),
) -> None:
    """Apply fast source and externally validated priors (Tamyiz Phase D).

    This pins narrow al-Kafi source conventions such as chain-opening "Abu
    Ja'far Muhammad b. Ya'qub", "Muhammad b. Yahya", "Ali b. Ibrahim", and
    opening "anhu" continuations, plus narrow priors validated against the
    imported external-review holdout, while retaining ranked alternatives. Run
    after build-person-layer -> resolve-persons -> build-tabaqat ->
    refine-tabaqat.
    """
    from eshia_research.rijal.collective_resolver import refine_compiler_priors

    db = SessionLocal()
    try:
        stats = refine_compiler_priors(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
            commit=not dry_run,
        )
        if dry_run:
            db.rollback()
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(
        f"{mode}: examined {stats.nodes_examined} source-prior target node(s); "
        f"resolved {stats.nodes_resolved} "
        f"({stats.compiler_priors} Kulayni, {stats.source_priors} source openings, "
        f"{stats.review_priors} review priors, {stats.anaphora_priors} anaphora)."
    )
    for method, count in stats.method_counts.most_common(12):
        typer.echo(f"  {method}: {count}")


@app.command("refine-imam-priors")
def refine_imam_priors_cmd(
    source_book_id: list[str] = typer.Option([], "--source-book-id", help="eShia source_book_id (repeatable)."),
    book_id: list[int] = typer.Option([], "--book-id", help="Local Book.id (repeatable)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without committing database changes."),
) -> None:
    """Break shared-kunya Ma'sum ambiguity by isnad convention (Tamyiz Phase D).

    Resolves imam nodes still ambiguous between the two Ma'sumin who share a
    kunya — «أبو عبد الله ع» (al-Sadiq vs al-Husayn) and «أبو جعفر ع» (al-Baqir
    vs al-Jawad) — to the conventional Imam, keeping the same-kunya alternate as
    a ranked alternative. Lattice-independent: it does not read person_generations,
    so noisy propagated generations cannot mis-drive it (unlike refine-tabaqat).
    """
    from eshia_research.rijal.collective_resolver import (
        refine_imam_kunya_priors,
        refine_previous_hadith_imam_anaphora,
    )

    db = SessionLocal()
    try:
        stats = refine_imam_kunya_priors(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
            commit=False,
        )
        # Now that terminal «أبو عبد الله ع» Imams are resolved, propagate them to
        # the «سأله»/«previous_hadith_imam» pronouns of following serial reports.
        anaphora = refine_previous_hadith_imam_anaphora(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
            commit=not dry_run,
        )
        if dry_run:
            db.rollback()
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(
        f"{mode}: examined {stats.nodes_examined} shared-kunya imam node(s); "
        f"resolved {stats.nodes_resolved} to the conventional Imam. "
        f"Anaphora: examined {anaphora.nodes_examined} «previous_hadith_imam» "
        f"pronoun(s); resolved {anaphora.nodes_resolved}."
    )
    for method, count in (stats.method_counts + anaphora.method_counts).most_common(12):
        typer.echo(f"  {method}: {count}")


@app.command("validate-review-priors")
def validate_review_priors_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
        "--source-book-id",
        help="eShia source_book_id whose imported review decisions should be scored.",
    ),
) -> None:
    """Read-only 80/20 holdout validation for checked-in review priors."""
    from eshia_research.rijal.review_priors import (
        format_review_prior_validation,
        validate_review_priors,
    )

    _init_db()
    db = SessionLocal()
    try:
        results = validate_review_priors(db, source_book_id=source_book_id)
    finally:
        db.close()

    typer.echo(format_review_prior_validation(results))
    if not all(result.passed for result in results):
        raise typer.Exit(1)


@app.command("refine-collective-context")
def refine_collective_context_cmd(
    source_book_id: list[str] = typer.Option([], "--source-book-id", help="eShia source_book_id (repeatable)."),
    book_id: list[int] = typer.Option([], "--book-id", help="Local Book.id (repeatable)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without committing database changes."),
) -> None:
    """Refine ambiguous person mentions with global context (Tamyiz Phase D).

    Uses already-resolved person mentions to build edge statistics, folds in
    Mu'jam teacher/student occurrence evidence, compiler priors, generation
    compatibility, and post-context 'iddah roster keying. Only high-margin
    winners are upgraded; weak cases remain ambiguous with ranked candidates.
    Run after build-person-layer -> resolve-persons -> build-tabaqat ->
    refine-tabaqat.
    """
    from eshia_research.rijal.collective_resolver import refine_with_collective_context

    _init_db()
    db = SessionLocal()
    try:
        with Progress(*_progress_columns()) as progress:
            stats = refine_with_collective_context(
                db,
                source_book_ids=source_book_id or None,
                book_ids=book_id or None,
                on_progress=_make_on_progress(progress),
                commit=not dry_run,
            )
        if dry_run:
            db.rollback()
    finally:
        db.close()

    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}Examined {stats.nodes_examined} ambiguous node(s); resolved {stats.nodes_resolved} "
        f"({stats.compiler_priors} compiler prior, {stats.source_priors} source-opening context, "
        f"{stats.context_resolved} total context)."
    )
    typer.echo(
        f"Expanded {stats.roster_expanded_nodes} collective node(s) with "
        f"{stats.roster_rows_added} roster member row(s); skipped {stats.skipped_weak_margin} weak cases."
    )
    for method, count in stats.method_counts.most_common(12):
        typer.echo(f"  {method}: {count}")


@app.command("resolve-persons")
def resolve_persons_cmd(
    source_book_id: list[str] = typer.Option(
        [],
        "--source-book-id",
        help=(
            "eShia source_book_id to resolve (repeatable). Defaults to the canonical Four Books: "
            + ", ".join(CANONICAL_FOUR_BOOK_SOURCE_IDS)
        ),
    ),
    book_id: list[int] = typer.Option(
        [], "--book-id", help="Local Book.id to resolve (repeatable). Overrides the default set."
    ),
    include_needs_review: bool = typer.Option(
        False,
        "--include-needs-review",
        help="Also resolve chains flagged needs_review. They are skipped by default.",
    ),
) -> None:
    """Resolve chain mentions to PERSONS (Tamyiz Engine Phase B).

    The reference calculus: surface-form person lookup (bare forms stay
    honestly ambiguous), «عن أبيه»/«عن جده»/«عنه» reference resolution with
    latent-person minting, and 'iddah collective member expansion. Writes
    mention_resolutions; never edits chain text or Phase A tables. Requires
    `build-person-layer` to have been run first.
    """
    from eshia_research.rijal.person_resolver import rebuild_person_resolutions

    _init_db()
    db = SessionLocal()
    try:
        with Progress(*_progress_columns()) as progress:
            stats = rebuild_person_resolutions(
                db,
                source_book_ids=source_book_id or None,
                book_ids=book_id or None,
                include_needs_review=include_needs_review,
                on_progress=_make_on_progress(progress),
            )
    finally:
        db.close()

    typer.echo(
        f"Saw {stats.nodes_seen} node(s); resolved {stats.resolved}, ambiguous {stats.ambiguous}, "
        f"via-collective {stats.via_collective}, unresolved {stats.unresolved}."
    )
    if stats.skipped_review_chains:
        typer.echo(
            f"Deferred {stats.skipped_review_chains} needs_review chain(s) "
            f"containing {stats.skipped_review_nodes} node(s)."
        )
    typer.echo(
        f"Reference calculus: {stats.father_resolved} father/grandfather, "
        f"{stats.anaphora_resolved} anaphora, {stats.latent_minted} latent persons minted."
    )
    typer.echo(
        f"Collective members seen {stats.collective_members}; "
        f"wrote {stats.resolution_rows} mention_resolution row(s)."
    )
    for method, count in stats.method_counts.most_common(12):
        typer.echo(f"  {method}: {count}")


@app.command("resolve-chain-narrators")
def resolve_chain_narrators_cmd(
    source_book_id: list[str] = typer.Option(
        [],
        "--source-book-id",
        help=(
            "eShia source_book_id to resolve (repeatable). Defaults to the canonical Four Books: "
            + ", ".join(CANONICAL_FOUR_BOOK_SOURCE_IDS)
        ),
    ),
    book_id: list[int] = typer.Option(
        [], "--book-id", help="Local Book.id to resolve (repeatable). Overrides the default canonical set."
    ),
) -> None:
    """Resolve named isnad chain nodes to canonical Mu'jam narrators.

    Phase 3A only resolves named narrator tokens. Ambiguous tokens keep ranked
    candidates in chain_node_candidates and are not forced into false certainty.
    """
    from eshia_research.rijal.resolver import rebuild_chain_node_resolutions

    db = SessionLocal()
    try:
        stats = rebuild_chain_node_resolutions(
            db,
            source_book_ids=source_book_id or None,
            book_ids=book_id or None,
        )
    finally:
        db.close()

    typer.echo(
        f"Resolved {stats.resolved_nodes}/{stats.named_nodes} named chain node(s) "
        f"({stats.resolution_ratio:.1%}); {stats.ambiguous_nodes} ambiguous, "
        f"{stats.unresolved_nodes} unresolved."
    )
    typer.echo(
        f"Stored {stats.candidate_rows} candidate row(s) for {stats.nodes_with_candidates} node(s); "
        f"{stats.exact_unique_resolved} exact-unique, {stats.prefix_unique_resolved} prefix-unique, "
        f"{stats.context_resolved} context-scored."
    )
    typer.echo(
        f"Resolved {stats.relation_resolved}/{stats.pronoun_nodes} pronoun/relation node(s); "
        f"{stats.relation_ambiguous} ambiguous, {stats.relation_unresolved} unresolved."
    )
    for method, count in stats.method_counts.most_common():
        typer.echo(f"  {method}: {count}")
    for method, count in stats.relation_method_counts.most_common():
        typer.echo(f"  relation {method}: {count}")


@app.command("audit-hadith-splits")
def audit_hadith_splits_cmd(
    source_book_id: str = typer.Option(
        "11005",
        "--source-book-id",
        help="eShia source_book_id to audit. Defaults to al-Kafi al-Islamiyya.",
    ),
    include_chain_index: bool = typer.Option(
        True,
        "--include-chain-index/--no-chain-index",
        help="Also flag stale/missing derived chain rows for hadiths that have isnad text.",
    ),
    max_flags: int = typer.Option(30, "--max-flags", help="Maximum number of flag buckets to print."),
) -> None:
    """Audit hadith boundary and isnad/matn split quality for one book.

    This is the shared "what needs attention next?" report. It uses approved
    split reviews as the active text, while optionally checking whether the
    derived chain index has caught up with those edits.
    """
    from eshia_research.hadith_split_audit import build_hadith_split_audit_report

    db = SessionLocal()
    try:
        report = build_hadith_split_audit_report(
            db,
            source_book_id=source_book_id,
            include_chain_index=include_chain_index,
        )
    finally:
        db.close()

    typer.echo(f"{report.title} ({report.source_book_id})")
    typer.echo(
        f"hadiths={report.total_hadiths}; reviewed={report.reviewed}; "
        f"approved={report.approved}; needs_review={report.needs_review}; "
        f"rejected={report.rejected}; unreviewed={report.unreviewed}"
    )
    typer.echo(
        f"flagged_hadiths={report.flagged_hadiths}; "
        f"suspicious_unreviewed={report.suspicious_unreviewed}"
    )
    for bucket in report.flags[:max_flags]:
        examples = ", ".join(bucket.examples)
        typer.echo(
            f"  {bucket.flag}: total={bucket.total}, unreviewed={bucket.unreviewed}, "
            f"approved={bucket.approved}, needs_review={bucket.needs_review}, "
            f"rejected={bucket.rejected}; examples={examples}"
        )


@app.command("repair-missing-isnad-splits")
def repair_missing_isnad_splits_cmd(
    source_book_id: str = typer.Option(
        "11005",
        "--source-book-id",
        help="eShia source_book_id to repair. Defaults to al-Kafi al-Islamiyya.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Write approved repairs to hadiths and hadith_split_reviews. Omit for dry-run.",
    ),
) -> None:
    """Repair high-confidence rows where the full chain leaked into matn_raw.

    This command is intentionally narrow. It fixes rows with missing isnad
    only when the split boundary matches a known safe pattern; commentary,
    continuations, and ambiguous rows are skipped for manual inspection.
    """
    from eshia_research.hadith_split_repair import repair_missing_isnad_splits

    db = SessionLocal()
    try:
        stats = repair_missing_isnad_splits(db, source_book_id=source_book_id, apply=apply)
    finally:
        db.close()

    mode = "APPLIED" if apply else "DRY-RUN"
    typer.echo(
        f"{mode}: rows_seen={stats.rows_seen}; proposed={stats.proposed}; "
        f"applied={stats.applied}; skipped={stats.skipped}"
    )
    for method, count in stats.method_counts.most_common():
        typer.echo(f"  method {method}: {count}")
    for reason, count in stats.skip_counts.most_common():
        typer.echo(f"  skip {reason}: {count}")


@app.command("show-archived-html")
def show_archived_html_cmd(
    book_id: int = typer.Option(..., "--book-id"),
    volume: int = typer.Option(..., "--volume"),
    page: int = typer.Option(..., "--page"),
    chars: int = typer.Option(500, "--chars", help="How many characters of the archived HTML to print"),
) -> None:
    """Fetch a page's raw HTML from the configured ObjectStore (see
    STORE_RAW_HTML_R2) and print a snippet — a sanity check that the
    archive actually has what Page.html_raw no longer does."""
    import gzip

    from eshia_research.crawler.jobs import html_archive_key
    from eshia_research.models import Book

    settings = get_settings()
    db = SessionLocal()
    try:
        source_book_id = db.query(Book.source_book_id).filter(Book.id == book_id).scalar()
    finally:
        db.close()
    if source_book_id is None:
        typer.echo(f"No book with id={book_id}.", err=True)
        raise typer.Exit(1)

    store = make_object_store(settings)
    key = html_archive_key(source_book_id, volume, page)
    try:
        data = store.get_bytes(key)
    except Exception as exc:  # noqa: BLE001 - surfacing the backend's own error is the point here
        typer.echo(f"Not found at {key}: {exc}", err=True)
        raise typer.Exit(1)

    html = gzip.decompress(data).decode("utf-8")
    typer.echo(f"{key} ({len(html)} chars):")
    typer.echo(html[:chars])


@app.command("export-book-list")
def export_book_list_cmd(
    output: str = typer.Option("book_list.json", "--output", help="Path to write the JSON export"),
) -> None:
    """Export {source_book_id, volume_count} for every book in the local DB.

    Ship the resulting file with a cloud-worker deploy so it can run
    crawl-to-cloud without needing any database of its own — see README's
    'Cloud-buffer crawling' section."""
    import json

    from eshia_research.models import Book

    db = SessionLocal()
    try:
        rows = db.query(Book.source_book_id, Book.volume_count).all()
    finally:
        db.close()

    book_list = [{"source_book_id": sbid, "volume_count": vc} for sbid, vc in rows]
    with open(output, "w", encoding="utf-8") as f:
        json.dump(book_list, f, ensure_ascii=False)
    typer.echo(f"Exported {len(book_list)} book(s) to {output}.")


@app.command("crawl-to-cloud")
def crawl_to_cloud_cmd(
    book_list_path: str = typer.Option(..., "--book-list", help="Path to book_list.json from export-book-list"),
    concurrency: int | None = typer.Option(None, "--concurrency", help="Defaults to CRAWL_CONCURRENCY"),
    batch_size: int | None = typer.Option(None, "--batch-size", help="Defaults to CLOUD_BATCH_SIZE"),
    max_pages_per_volume: int = typer.Option(5000, "--max-pages-per-volume", help="Safety cap per volume"),
) -> None:
    """Cloud-side half of the buffer pipeline: crawl full text and push
    batches to the configured object store (CLOUD_STORE_BACKEND=local|r2)
    instead of a database. Meant to run on a cloud worker (e.g. Railway)
    with no database of its own — see README's 'Cloud-buffer crawling'."""
    import json

    settings = get_settings()
    concurrency = settings.crawl_concurrency if concurrency is None else concurrency
    batch_size = settings.cloud_batch_size if batch_size is None else batch_size

    with open(book_list_path, encoding="utf-8") as f:
        book_list = json.load(f)

    store = make_object_store(settings)
    throttle = AdaptiveThrottle(
        window=settings.crawl_throttle_window,
        error_threshold=settings.crawl_throttle_error_rate,
        cooldown_seconds=settings.crawl_throttle_cooldown_seconds,
    )
    checkpoint = Checkpoint(DEFAULT_CHECKPOINT_PATH)
    with PoliteClient(settings, throttle=throttle) as client:
        stats = crawl_to_cloud_buffer(
            book_list,
            store,
            batch_size=batch_size,
            batch_prefix=settings.cloud_batch_prefix,
            concurrency=concurrency,
            max_pages_per_volume=max_pages_per_volume,
            client=client,
            checkpoint=checkpoint,
            settings=settings,
        )
    typer.echo(
        f"Books: {stats['books']}, volumes: {stats['volumes']}, "
        f"first pages done: {stats['first_pages_done']}, "
        f"remaining pages done: {stats['remaining_pages_done']}/{stats['remaining_pages_total']}, "
        f"batches uploaded: {stats['batches_uploaded']}."
    )


@app.command("drain-cloud")
def drain_cloud_cmd(
    checkpoint_path: str = typer.Option(
        "data/checkpoints/drain.json", "--checkpoint", help="Separate checkpoint file from the main crawl one"
    ),
) -> None:
    """Local-side half of the buffer pipeline: pull batches pushed by
    crawl-to-cloud, upsert into the local DB, delete from the object store.
    Safe to run repeatedly (e.g. every few minutes via a scheduled task) —
    only processes batches not already marked done in --checkpoint."""
    from pathlib import Path

    settings = get_settings()
    store = make_object_store(settings)
    drain_checkpoint = Checkpoint(Path(checkpoint_path))
    stats = drain_cloud_buffer(store, drain_checkpoint, batch_prefix=settings.cloud_batch_prefix, settings=settings)
    typer.echo(
        f"Batches seen: {stats['batches_seen']}, drained: {stats['batches_drained']}, "
        f"pages upserted: {stats['pages_upserted']}."
    )


@app.command("eval-resolution")
def eval_resolution_cmd(
    source_book_id: str = typer.Option(
        "11005", "--source-book-id", help="eShia source_book_id to evaluate (default Al-Kafi)."
    ),
    resolver_version: str = typer.Option(
        "tamyiz_b1", "--resolver-version", help="mention_resolutions resolver_version to score."
    ),
    json_out: bool = typer.Option(False, "--json", help="Emit the full report as JSON instead of text."),
) -> None:
    """Score person-resolution quality against independent gold signals.

    Read-only. Reports coverage, the hard bare-form-leak invariant, generation
    monotonicity of resolved edges, and — the core — how well the resolver's
    confident person edges agree with al-Khoei's own rijal_occurrences. The
    corroboration rate is a floor (exact-match); the contradiction and
    generation-violation samples are concrete candidate mis-resolutions to review.
    """
    from eshia_research.rijal.eval_resolution import evaluate_resolution

    _init_db()
    db = SessionLocal()
    try:
        report = evaluate_resolution(db, source_book_id, resolver_version=resolver_version)
    finally:
        db.close()

    if json_out:
        import dataclasses as _dc
        import json as _json

        typer.echo(_json.dumps(_dc.asdict(report), ensure_ascii=False, indent=2))
    else:
        typer.echo(report.format_text())


@app.command("audit-generations")
def audit_generations_cmd(
    source_book_id: str = typer.Option(
        "11005", "--source-book-id", help="eShia source_book_id to audit (default Al-Kafi)."
    ),
    resolver_version: str = typer.Option(
        "tamyiz_b1", "--resolver-version", help="mention_resolutions resolver_version to audit."
    ),
    output_dir: str = typer.Option(
        "scratch_audit", "--output-dir", help="Directory for the markdown + JSONL exports."
    ),
    json_out: bool = typer.Option(False, "--json", help="Print the summary JSON to stdout."),
    no_write: bool = typer.Option(False, "--no-write", help="Compute only; do not write export files."),
) -> None:
    """Full generation-lattice audit with per-case triage buckets (read-only).

    Exports EVERY generation-monotonicity violation, conflict-method person, and
    Mu'jam-contradicted edge with stable identifiers, each violation classified
    into suspect_generation | suspect_identity | suspect_text | unclassified.
    """
    from eshia_research.rijal.generation_audit import audit_generations, write_audit_exports

    _init_db()
    db = SessionLocal()
    try:
        report = audit_generations(
            db, source_book_id=source_book_id, resolver_version=resolver_version
        )
    finally:
        db.close()

    if json_out:
        import json as _json

        typer.echo(_json.dumps(report.summary_dict(), ensure_ascii=False, indent=2))
    else:
        typer.echo(report.format_text())

    if not no_write:
        md_path, jsonl_path = write_audit_exports(report, output_dir)
        typer.echo(f"Wrote {md_path}")
        typer.echo(f"Wrote {jsonl_path}")


@app.command("machine-review-person-resolutions")
def machine_review_person_resolutions_cmd(
    source_book_id: str = typer.Option(
        "11005", "--source-book-id", help="eShia source_book_id to review (default Al-Kafi)."
    ),
    reviewer: str = typer.Option("codex-machine-v1", "--reviewer", help="Machine reviewer identifier."),
    limit: int | None = typer.Option(None, "--limit", help="Only process the first N chain nodes."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without committing database changes."),
) -> None:
    """Write conservative machine-admin decisions for person resolutions.

    Decisions are stored separately from `mention_resolutions`: approve strong
    low-risk current winners, flag hard contradictions, and route ambiguous or
    risky cases to external review.
    """
    from eshia_research.rijal.machine_review import run_machine_review

    _init_db()
    db = SessionLocal()
    try:
        stats = run_machine_review(
            db,
            source_book_id=source_book_id,
            reviewer=reviewer,
            limit=limit,
            commit=not dry_run,
        )
        if dry_run:
            db.rollback()
    finally:
        db.close()

    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}examined {stats.nodes_examined} node(s); "
        f"wrote {stats.decisions_written} decision(s)."
    )
    typer.echo("Decisions:")
    for decision, count in stats.decision_counts.most_common():
        typer.echo(f"  {decision}: {count}")
    typer.echo("Confidence:")
    for tier, count in stats.confidence_counts.most_common():
        typer.echo(f"  {tier}: {count}")
    if stats.risk_counts:
        typer.echo("Top risk flags:")
        for flag, count in stats.risk_counts.most_common(12):
            typer.echo(f"  {flag}: {count}")


@app.command("export-person-review-packet")
def export_person_review_packet_cmd(
    source_book_id: str = typer.Option(
        "11005", "--source-book-id", help="eShia source_book_id to export (default Al-Kafi)."
    ),
    reviewer: str = typer.Option("codex-machine-v1", "--reviewer", help="Machine reviewer identifier."),
    output_dir: str = typer.Option(
        "scratch_audit", "--output-dir", help="Directory for Markdown and JSONL exports."
    ),
    decision_type: list[str] = typer.Option(
        ["needs_external_review", "flag_contradiction"],
        "--decision-type",
        help="Decision type to include; repeatable.",
    ),
    skip: int = typer.Option(0, "--skip", help="Skip N matching cases."),
    limit: int = typer.Option(25, "--limit", help="Number of cases to export."),
) -> None:
    """Export a stable Markdown + JSONL packet for external LLM/source review."""
    from eshia_research.rijal.machine_review import export_external_review_packet

    _init_db()
    db = SessionLocal()
    try:
        stats = export_external_review_packet(
            db,
            output_dir=output_dir,
            source_book_id=source_book_id,
            reviewer=reviewer,
            decision_types=set(decision_type),
            skip=skip,
            limit=limit,
        )
    finally:
        db.close()

    typer.echo(f"Wrote {stats.cases_written} case(s).")
    typer.echo(f"Markdown: {stats.markdown_path}")
    typer.echo(f"JSONL: {stats.jsonl_path}")


@app.command("import-person-review-results")
def import_person_review_results_cmd(
    path: list[str] = typer.Argument(..., help="Filled external-review result file(s)."),
    external_reviewer: str = typer.Option("external-llm", "--external-reviewer"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parse and match without committing."),
) -> None:
    """Import filled external-review templates back into the local database."""
    from eshia_research.rijal.external_review import import_external_review_files

    _init_db()
    db = SessionLocal()
    try:
        stats = import_external_review_files(
            db,
            path,
            external_reviewer=external_reviewer,
            commit=not dry_run,
        )
    finally:
        db.close()

    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}files {stats.files_seen}; parsed {stats.cases_parsed} case(s); "
        f"wrote {stats.rows_written} external-review row(s)."
    )
    typer.echo(
        f"Matched persons: {stats.matched_person}; unmatched actionable persons: "
        f"{stats.unmatched_person}; missing nodes: {stats.missing_nodes}."
    )
    typer.echo("Verdicts:")
    for verdict, count in stats.verdict_counts.most_common():
        typer.echo(f"  {verdict}: {count}")
    if stats.confidence_counts:
        typer.echo("Confidence:")
        for tier, count in stats.confidence_counts.most_common():
            typer.echo(f"  {tier}: {count}")


@app.command("promote-person-review-results")
def promote_person_review_results_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
        "--source-book-id",
        help="Source book ID to promote imported external reviews for.",
    ),
    reviewer: str = typer.Option("codex-admin-external-v1", "--reviewer"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview admin decisions without committing."),
) -> None:
    """Promote imported external-review rows into explicit admin decisions."""
    from eshia_research.rijal.external_review import promote_external_reviews_to_admin_decisions

    _init_db()
    db = SessionLocal()
    try:
        stats = promote_external_reviews_to_admin_decisions(
            db,
            source_book_id=source_book_id,
            reviewer=reviewer,
            commit=not dry_run,
            write=not dry_run,
        )
    finally:
        db.close()

    mode = "DRY-RUN: " if dry_run else ""
    typer.echo(
        f"{mode}review rows {stats.reviews_seen}; wrote {stats.decisions_written} "
        f"admin decision(s)."
    )
    typer.echo(
        f"Skipped unmatched actionable: {stats.skipped_unmatched}; "
        f"unknown verdicts: {stats.skipped_unknown_verdict}."
    )
    typer.echo("External verdicts promoted:")
    for verdict, count in stats.verdict_counts.most_common():
        typer.echo(f"  {verdict}: {count}")
    typer.echo("Admin decisions:")
    for decision_type, count in stats.decision_counts.most_common():
        typer.echo(f"  {decision_type}: {count}")


@app.command("plan-translation-jobs")
def plan_translation_jobs_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
        "--source-book-id",
        help="Source book ID to plan translation work for.",
    ),
    language: str = typer.Option("en", "--language", help="Target language code."),
    limit: int | None = typer.Option(None, "--limit", help="Plan only the first N pending hadiths."),
    pilot_size: int | None = typer.Option(
        None,
        "--pilot-size",
        help="Plan a stratified pilot of this size instead of the first N rows.",
    ),
    include_existing: bool = typer.Option(
        False,
        "--include-existing",
        help="Include rows that already have a current translation hash.",
    ),
    input_usd_per_mtok: float | None = typer.Option(
        None,
        "--input-usd-per-mtok",
        help="Optional model input price per 1M tokens for cost estimates.",
    ),
    output_usd_per_mtok: float | None = typer.Option(
        None,
        "--output-usd-per-mtok",
        help="Optional model output price per 1M tokens for cost estimates.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Persist a planned translation job and segment rows. Omit for dry-run.",
    ),
    provider: str | None = typer.Option(None, "--provider", help="Provider name to record on the job."),
    model: str | None = typer.Option(None, "--model", help="Model name to record on the job."),
    job_key: str | None = typer.Option(None, "--job-key", help="Explicit job key; otherwise deterministic."),
) -> None:
    """Plan token-efficient English translation batches without making model calls."""
    from eshia_research.translation.planner import (
        build_translation_plan,
        format_plan,
        persist_translation_plan,
    )

    _init_db()
    db = SessionLocal()
    try:
        plan = build_translation_plan(
            db,
            source_book_id=source_book_id,
            language=language,
            limit=limit,
            pilot_size=pilot_size,
            skip_existing=not include_existing,
            input_usd_per_mtok=input_usd_per_mtok,
            output_usd_per_mtok=output_usd_per_mtok,
        )
        typer.echo(format_plan(plan))
        if apply:
            job = persist_translation_plan(
                db,
                plan,
                provider=provider,
                model=model,
                job_key=job_key,
            )
            db.commit()
            typer.echo(f"APPLIED: translation_job id={job.id}; job_key={job.job_key}")
        else:
            typer.echo("DRY-RUN: no translation job rows written.")
    finally:
        db.close()


@app.command("render-english-isnad")
def render_english_isnad_cmd(
    public_id: str | None = typer.Option(None, "--public-id", help="Public hadith ID, e.g. alkafi-1."),
    hadith_id: int | None = typer.Option(None, "--hadith-id", help="Internal hadith row ID."),
) -> None:
    """Render a hadith's chain with deterministic English transmission formulae."""
    from eshia_research.models import Hadith
    from eshia_research.translation.isnad_renderer import render_hadith_isnad

    if public_id is None and hadith_id is None:
        typer.echo("Provide --public-id or --hadith-id.", err=True)
        raise typer.Exit(1)

    _init_db()
    db = SessionLocal()
    try:
        target_id = hadith_id
        if target_id is None:
            target_id = db.query(Hadith.id).filter(Hadith.public_id == public_id).scalar()
        if target_id is None:
            typer.echo("Hadith not found.", err=True)
            raise typer.Exit(1)
        rendered = render_hadith_isnad(db, target_id)
    finally:
        db.close()

    typer.echo(rendered.text or "(no rendered chain)")
    if rendered.risk_flags:
        typer.echo("Risk flags:")
        for flag in rendered.risk_flags:
            typer.echo(f"  {flag}")


@app.command("qa-translations")
def qa_translations_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
        "--source-book-id",
        help="Source book ID whose stored translations should be checked.",
    ),
    language: str = typer.Option("en", "--language", help="Target language code."),
    limit: int | None = typer.Option(None, "--limit", help="Only check the first N translations."),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Write QA risk flags back to hadith_translations. Omit for dry-run.",
    ),
) -> None:
    """Run deterministic QA against stored draft translations."""
    from collections import Counter

    from sqlalchemy import select

    from eshia_research.models import Book, Hadith, HadithTranslation
    from eshia_research.translation.qa import assess_translation

    _init_db()
    db = SessionLocal()
    counts: Counter = Counter()
    try:
        stmt = (
            select(HadithTranslation, Hadith)
            .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
            .join(Book, Book.id == Hadith.book_id)
            .where(
                Book.source_book_id == source_book_id,
                HadithTranslation.language == language,
                HadithTranslation.matn_translation.isnot(None),
            )
            .order_by(Hadith.sequence_in_book)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        for translation, hadith in db.execute(stmt):
            report = assess_translation(hadith.matn_raw, translation.matn_translation)
            counts[report.risk_level] += 1
            for code in report.flag_codes:
                counts[f"flag:{code}"] += 1
            if apply:
                translation.risk_level = report.risk_level
                translation.risk_flags = [
                    {"code": flag.code, "severity": flag.severity, "detail": flag.detail}
                    for flag in report.flags
                ]
                translation.qa_version = report.qa_version
                if report.risk_level == "green" and translation.status == "draft":
                    translation.status = "machine_verified"
        if apply:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()

    mode = "APPLIED" if apply else "DRY-RUN"
    typer.echo(f"{mode}: checked={sum(v for k, v in counts.items() if not k.startswith('flag:'))}")
    for key, count in counts.most_common():
        typer.echo(f"  {key}: {count}")


@app.command("import-thaqalayn-alkafi")
def import_thaqalayn_alkafi_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID,
        "--source-book-id",
        help="Local/eShia source_book_id for Al-Kafi.",
    ),
    source: str = typer.Option(
        "api",
        "--source",
        help="Translation source to import: api or static.",
    ),
    static_cache_path: str | None = typer.Option(
        None,
        "--static-cache-path",
        help="Read/write normalized ThaqalaynData static rows at this JSON path.",
    ),
    static_workers: int = typer.Option(
        16,
        "--static-workers",
        help="Concurrent workers for fetching ThaqalaynData static detail JSON.",
    ),
    min_score: float = typer.Option(
        0.88,
        "--min-score",
        help="Minimum Arabic similarity score required before a Thaqalayn row can match.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Preview matches by default. Use --apply to write publishable imports.",
    ),
    overwrite_current: bool = typer.Option(
        False,
        "--overwrite-current",
        help="Replace existing green current translations instead of skipping them.",
    ),
    replace_provider: list[str] = typer.Option(
        [],
        "--replace-provider",
        help="Replace existing green current translations only when their provider matches this value.",
    ),
) -> None:
    """Match and import Muhammad Sarwar's Al-Kafi English text from Thaqalayn."""
    from eshia_research.translation.thaqalayn_importer import (
        STATIC_JOB_KEY,
        fetch_al_kafi_static_records,
        format_import_stats,
        import_thaqalayn_al_kafi,
    )

    _init_db()
    db = SessionLocal()
    try:
        remote_by_volume = None
        job_key = None
        if source == "static":
            remote_by_volume = fetch_al_kafi_static_records(
                cache_path=static_cache_path,
                max_workers=static_workers,
            )
            job_key = STATIC_JOB_KEY
        elif source != "api":
            raise typer.BadParameter("--source must be either 'api' or 'static'")
        stats = import_thaqalayn_al_kafi(
            db,
            source_book_id=source_book_id,
            remote_by_volume=remote_by_volume,
            dry_run=dry_run,
            overwrite_current=overwrite_current,
            min_score=min_score,
            replace_providers=set(replace_provider),
            **({"job_key": job_key} if job_key else {}),
        )
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn Al-Kafi import")
    typer.echo(format_import_stats(stats))


@app.command("import-thaqalayn-structure")
def import_thaqalayn_structure_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID, "--source-book-id"
    ),
    snapshot_dir: str | None = typer.Option(
        None, "--snapshot-dir", help="Directory of tq_v{1..8}.json API snapshots."
    ),
    min_score: float = typer.Option(0.88, "--min-score"),
    manifest_path: str | None = typer.Option(
        None, "--manifest-path", help="Write the match manifest JSON here."
    ),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import Thaqalayn kitab/chapter structure and gradings for Al-Kafi."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_importer import fetch_al_kafi_records
    from eshia_research.translation.thaqalayn_structure import (
        apply_structure_matches,
        build_structure_matches,
        import_gradings,
        load_snapshot_records,
    )

    _init_db()
    db = SessionLocal()
    try:
        if snapshot_dir:
            remote_by_volume = load_snapshot_records(snapshot_dir)
        else:
            remote_by_volume = fetch_al_kafi_records()
        rows, stats = build_structure_matches(
            db,
            source_book_id=source_book_id,
            remote_by_volume=remote_by_volume,
            min_score=min_score,
        )
        if manifest_path:
            Path(manifest_path).write_text(
                _json.dumps(stats.manifest, ensure_ascii=False, indent=1), encoding="utf-8"
            )
        if not dry_run:
            written = apply_structure_matches(db, rows)
            grade_stats = import_gradings(
                db,
                source_book_id=source_book_id,
                remote_by_volume=remote_by_volume,
                structure_matches=rows,
            )
            stats.gradings_rows = grade_stats.gradings_rows
            stats.gradings_hadiths = grade_stats.gradings_hadiths
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn structure import")
    typer.echo(f"  fetched remote rows      : {stats.fetched}")
    typer.echo(f"  local visible hadiths    : {stats.local_visible}")
    typer.echo(f"  matched (provenance rekey): {stats.matched_provenance_rekey}")
    typer.echo(f"  matched (windowed arabic) : {stats.matched_windowed_arabic}")
    typer.echo(f"  interpolated (edition gap): {stats.interpolated}")
    typer.echo(f"  unmapped                 : {stats.unmapped}")
    typer.echo(f"  numbering-flagged        : {stats.numbering_flagged}")
    typer.echo(f"  gradings rows / hadiths  : {stats.gradings_rows} / {stats.gradings_hadiths}")


@app.command("import-thaqalayn-live-english")
def import_thaqalayn_live_english_cmd(
    source_book_id: str = typer.Option(
        AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID, "--source-book-id"
    ),
    snapshot_dir: str | None = typer.Option(None, "--snapshot-dir"),
    min_score: float = typer.Option(0.88, "--min-score"),
    manifest_path: str | None = typer.Option(None, "--manifest-path"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import the current Thaqalayn English verbatim for structure-matched Al-Kafi rows."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_importer import fetch_al_kafi_records
    from eshia_research.translation.thaqalayn_structure import (
        import_live_english,
        load_snapshot_records,
    )

    _init_db()
    db = SessionLocal()
    try:
        if snapshot_dir:
            remote_by_volume = load_snapshot_records(snapshot_dir)
        else:
            remote_by_volume = fetch_al_kafi_records()
        stats = import_live_english(
            db,
            source_book_id=source_book_id,
            remote_by_volume=remote_by_volume,
            dry_run=dry_run,
            min_score=min_score,
        )
        if manifest_path:
            Path(manifest_path).write_text(
                _json.dumps(stats.manifest, ensure_ascii=False, indent=1), encoding="utf-8"
            )
        if not dry_run:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn live-English import")
    typer.echo(f"  considered (matched maps): {stats.considered}")
    typer.echo(f"  imported                 : {stats.imported}")
    typer.echo(f"  skipped (QA)             : {stats.skipped_qa}")
    typer.echo(f"  skipped (low confidence) : {stats.skipped_low_confidence}")
    typer.echo(f"  skipped (unknown transl.): {stats.skipped_unknown_translator}")
    typer.echo(f"  leading-index downgraded : {stats.number_prefix_downgraded}")
    if stats.errors:
        typer.echo(f"  errors: {stats.errors[:5]}")


@app.command("audit-thaqalayn-website")
def audit_thaqalayn_website_cmd(
    corpus: str = typer.Option("alkafi", "--corpus", help="Corpus key: alkafi or faqih."),
    inventory_path: str = typer.Option(..., "--inventory-path"),
    audit_path: str = typer.Option(..., "--audit-path"),
    markdown_path: str | None = typer.Option(None, "--markdown-path"),
    cache_dir: str = typer.Option(..., "--cache-dir"),
    workers: int = typer.Option(4, "--workers", min=1, max=8),
    delay_seconds: float = typer.Option(0.2, "--delay-seconds", min=0.05),
    timeout_seconds: float = typer.Option(30.0, "--timeout-seconds", min=5.0),
    min_score: float = typer.Option(0.88, "--min-score", min=0.5, max=1.0),
    review_manifest_path: str | None = typer.Option(None, "--review-manifest-path"),
    reuse_inventory: bool = typer.Option(False, "--reuse-inventory"),
    refresh: bool = typer.Option(False, "--refresh"),
) -> None:
    """Compare one corpus bidirectionally with rendered Thaqalayn pages."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_website import (
        audit_thaqalayn_website,
        crawl_thaqalayn_website,
        get_website_corpus,
        render_audit_markdown,
    )

    corpus_config = get_website_corpus(corpus)

    inventory_file = Path(inventory_path)
    audit_file = Path(audit_path)
    markdown_file = Path(markdown_path) if markdown_path else None
    review_manifest = (
        _json.loads(Path(review_manifest_path).read_text(encoding="utf-8"))
        if review_manifest_path
        else None
    )
    last_reported = -1

    def progress(done: int, total: int) -> None:
        nonlocal last_reported
        if done == total or done - last_reported >= 50:
            typer.echo(f"  website chapters: {done:,}/{total:,}")
            last_reported = done

    if reuse_inventory:
        inventory = _json.loads(inventory_file.read_text(encoding="utf-8"))
    else:
        inventory = crawl_thaqalayn_website(
            corpus=corpus_config,
            inventory_path=inventory_file,
            cache_dir=Path(cache_dir),
            workers=workers,
            delay_seconds=delay_seconds,
            timeout_seconds=timeout_seconds,
            refresh=refresh,
            on_progress=progress,
        )
    db = SessionLocal()
    try:
        audit = audit_thaqalayn_website(
            db,
            inventory=inventory,
            min_score=min_score,
            review_manifest=review_manifest,
        )
    finally:
        db.close()

    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(
        _json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    if markdown_file:
        markdown_file.parent.mkdir(parents=True, exist_ok=True)
        markdown_file.write_text(render_audit_markdown(audit), encoding="utf-8")

    summary = audit["summary"]
    typer.echo(f"Website-first {corpus_config.title} completeness audit")
    typer.echo(f"  local visible            : {summary['local_visible']:,}")
    typer.echo(f"  website reports          : {summary['website_hadiths']:,}")
    typer.echo(f"  confirmed local / website: {summary['confirmed_local']:,} / {summary['confirmed_website']:,}")
    typer.echo(f"  unaccounted local        : {summary['unaccounted_local']:,}")
    typer.echo(f"  unaccounted website      : {summary['unaccounted_website']:,}")
    typer.echo(f"  candidate split/merge    : {summary['candidate_split_merge_blocks']:,}")
    typer.echo(f"  inventory ready          : {summary['inventory_ready']}")
    typer.echo(f"  rijal boundary ready     : {summary['rijal_ready']}")
    typer.echo(f"  public release ready     : {summary['publication_ready']}")
    quality = audit["publication_quality"]["summary"]
    typer.echo(f"  blocking local records   : {quality['blocking_records']:,}")


@app.command("repair-thaqalayn-website-boundaries")
def repair_thaqalayn_website_boundaries_cmd(
    inventory_path: str = typer.Option(..., "--inventory-path"),
    audit_path: str = typer.Option(..., "--audit-path"),
    chapter_path: str | None = typer.Option(None, "--chapter-path"),
    quality_blockers_only: bool = typer.Option(
        False, "--quality-blockers-only"
    ),
    simple_splits_only: bool = typer.Option(False, "--simple-splits-only"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Repair one reviewed Faqih chapter from rendered website Arabic."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_website import (
        repair_website_arabic_boundaries,
    )

    inventory = _json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    audit = _json.loads(Path(audit_path).read_text(encoding="utf-8"))
    _init_db()
    db = SessionLocal()
    try:
        stats = repair_website_arabic_boundaries(
            db,
            inventory=inventory,
            audit=audit,
            chapter_path=chapter_path,
            quality_blockers_only=quality_blockers_only,
            simple_splits_only=simple_splits_only,
            dry_run=dry_run,
        )
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn website Arabic boundary repair")
    typer.echo(f"  local records considered : {stats.considered:,}")
    typer.echo(f"  boundaries repaired      : {stats.boundaries_repaired:,}")
    typer.echo(f"  split records created    : {stats.split_records_created:,}")
    typer.echo(f"  unchanged                : {stats.unchanged:,}")
    typer.echo(f"  skipped complex relations: {stats.skipped_complex_relations:,}")


@app.command("import-thaqalayn-website-numbered-gaps")
def import_thaqalayn_website_numbered_gaps_cmd(
    inventory_path: str = typer.Option(..., "--inventory-path"),
    audit_path: str = typer.Option(..., "--audit-path"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import reviewed numbered Faqih reports missing from local edition rows."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_website import (
        import_website_numbered_gaps,
    )

    inventory = _json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    audit = _json.loads(Path(audit_path).read_text(encoding="utf-8"))
    _init_db()
    db = SessionLocal()
    try:
        stats = import_website_numbered_gaps(
            db, inventory=inventory, audit=audit, dry_run=dry_run
        )
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: reviewed website numbered-gap import")
    typer.echo(f"  considered           : {stats.considered:,}")
    typer.echo(f"  hadiths created      : {stats.created_hadiths:,}")
    typer.echo(f"  translations created : {stats.created_translations:,}")
    typer.echo(f"  skipped existing     : {stats.skipped_existing:,}")


@app.command("import-thaqalayn-website-english")
def import_thaqalayn_website_english_cmd(
    inventory_path: str = typer.Option(..., "--inventory-path"),
    audit_path: str = typer.Option(..., "--audit-path"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import rendered website English for Arabic-verified one-to-one rows."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_website import import_website_english

    inventory = _json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    audit = _json.loads(Path(audit_path).read_text(encoding="utf-8"))
    _init_db()
    db = SessionLocal()
    try:
        stats = import_website_english(
            db,
            inventory=inventory,
            audit=audit,
            dry_run=dry_run,
        )
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn website-English import")
    typer.echo(f"  confirmed relations      : {stats.considered}")
    typer.echo(f"  imported                 : {stats.imported}")
    typer.echo(f"  created / updated        : {stats.created} / {stats.updated}")
    typer.echo(f"  unchanged                : {stats.unchanged}")
    typer.echo(f"  skipped non-one-to-one   : {stats.skipped_non_one_to_one}")
    typer.echo(f"  skipped missing English  : {stats.skipped_missing_english}")
    typer.echo(f"  skipped stale Arabic     : {stats.skipped_stale_arabic_match}")
    typer.echo(f"  skipped no translator    : {stats.skipped_unknown_translator}")
    typer.echo(
        "  matn boundaries          : "
        f"exact={stats.boundary_exact}, marker={stats.boundary_marker}, "
        f"full={stats.boundary_full_fallback}"
    )
    if stats.errors:
        typer.echo(f"  errors: {stats.errors[:5]}")


@app.command("import-thaqalayn-website-structure")
def import_thaqalayn_website_structure_cmd(
    inventory_path: str = typer.Option(..., "--inventory-path"),
    audit_path: str = typer.Option(..., "--audit-path"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
) -> None:
    """Import website-confirmed kitab/chapter placement for one corpus."""
    import json as _json
    from pathlib import Path

    from eshia_research.translation.thaqalayn_website import import_website_structure

    inventory = _json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    audit = _json.loads(Path(audit_path).read_text(encoding="utf-8"))
    _init_db()
    db = SessionLocal()
    try:
        stats = import_website_structure(
            db, inventory=inventory, audit=audit, dry_run=dry_run
        )
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "DRY-RUN" if dry_run else "APPLIED"
    typer.echo(f"{mode}: Thaqalayn website structure import")
    typer.echo(f"  confirmed relations : {stats.confirmed:,}")
    typer.echo(f"  matched placements  : {stats.matched:,}")
    typer.echo(f"  interpolated        : {stats.interpolated:,}")
    typer.echo(f"  unmapped            : {stats.unmapped:,}")
    typer.echo(f"  rows written        : {stats.written:,}")


@app.command("rebuild-book-topics")
def rebuild_book_topics_cmd(
    source_book_id: str = typer.Option(..., "--source-book-id"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Rebuild source and semantic topics for a configured collection."""
    from eshia_research.topics import rebuild_book_topics

    db = SessionLocal()
    try:
        stats = rebuild_book_topics(db, source_book_id=source_book_id)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    typer.echo(f"Topic taxonomy for source book {source_book_id}")
    typer.echo(f"  hadiths categorized : {stats.hadiths:,}")
    typer.echo(f"  topics              : {stats.topics:,}")
    typer.echo(f"  semantic topics     : {stats.semantic_topics:,}")
    typer.echo(f"  assignments         : {stats.assignments:,}")
    typer.echo(f"  semantic assignments: {stats.semantic_assignments:,}")
    typer.echo(f"  directly placed     : {stats.directly_placed:,}")
    typer.echo(f"  inherited placement : {stats.inherited_placed:,}")
    typer.echo(f"  saved               : {not dry_run}")


@app.command("rebuild-alkafi-topics")
def rebuild_alkafi_topics_cmd(
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Rebuild source-derived topic and hashtag assignments for all Al-Kafi hadiths."""
    from eshia_research.topics import rebuild_alkafi_topics

    db = SessionLocal()
    try:
        stats = rebuild_alkafi_topics(db)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    typer.echo("Al-Kafi topic taxonomy")
    typer.echo(f"  hadiths categorized : {stats.hadiths:,}")
    typer.echo(f"  topics              : {stats.topics:,}")
    typer.echo(f"  semantic topics     : {stats.semantic_topics:,}")
    typer.echo(f"  assignments         : {stats.assignments:,}")
    typer.echo(f"  semantic assignments: {stats.semantic_assignments:,}")
    typer.echo(f"  directly placed     : {stats.directly_placed:,}")
    typer.echo(f"  inherited placement : {stats.inherited_placed:,}")
    typer.echo(f"  methods             : {stats.method_counts}")
    typer.echo(f"  saved               : {not dry_run}")




@app.command("commentary-manifest")
def commentary_manifest_cmd(
    source_key: str = typer.Argument(..., help="e.g. mirat-al-uqul"),
    output: str = typer.Option(..., "--output", help="Where to write the manifest JSON"),
) -> None:
    """Fingerprint what THIS database already holds for a commentary.

    Run on the deployment target. The result is small and is what makes the
    export a real delta instead of a full dump.
    """
    import json

    from eshia_research.commentary.transfer import build_manifest

    db = SessionLocal()
    try:
        manifest = build_manifest(db, source_key)
    finally:
        db.close()
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False)
    typer.echo(f"Manifest for {source_key}: {len(manifest['entries'])} row(s) -> {output}")


@app.command("export-commentary-delta")
def export_commentary_delta_cmd(
    source_key: str = typer.Argument(..., help="e.g. mirat-al-uqul"),
    output: str = typer.Option(..., "--output", help="Destination .json.gz"),
    manifest: str | None = typer.Option(
        None, "--manifest", help="Target's manifest; omit to export every row"
    ),
) -> None:
    """Export only the commentary rows that differ from the target's manifest."""
    import json

    from eshia_research.commentary.transfer import export_delta, write_delta

    loaded = None
    if manifest:
        with open(manifest, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)

    db = SessionLocal()
    try:
        delta = export_delta(db, source_key, loaded)
    finally:
        db.close()
    write_delta(delta, output)
    summary = delta["summary"]
    typer.echo(
        f"Delta for {source_key}: changed={summary['changed']} "
        f"unchanged={summary['unchanged']} removed={summary['removed']} "
        f"(of {summary['total_local_rows']} local rows) -> {output}"
    )


@app.command("verify-commentary-deployment")
def verify_commentary_deployment_cmd(
    source_key: str = typer.Argument(..., help="e.g. mirat-al-uqul"),
    base_url: str = typer.Option(
        "http://localhost:8000", "--base-url", help="The API to ask"
    ),
    timeout: int = typer.Option(30, "--timeout", help="Seconds per request"),
) -> None:
    """Prove the API is actually serving a commentary that was just deployed.

    Run on the deployment target, after the API has restarted. Picks a hadith
    this source is genuinely linked to, fetches the whole response, parses it,
    and requires the source to be present — rather than searching truncated text
    for a substring, which is what this replaced.
    """
    from eshia_research.commentary.verification import (
        VerificationError,
        verify_deployment,
    )

    db = SessionLocal()
    try:
        public_id, entry = verify_deployment(
            db, source_key, base_url=base_url, timeout=timeout
        )
    except VerificationError as error:
        typer.echo(f"VERIFICATION FAILED: {error}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

    evidence = entry.get("evidence", "?")
    typer.echo(
        f"Verified '{source_key}' is served: {public_id} returns it "
        f"(evidence={evidence})."
    )


@app.command("import-commentary-delta")
def import_commentary_delta_cmd(
    input_path: str = typer.Argument(..., help="The .json.gz produced by export"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Validate and roll back without writing"
    ),
) -> None:
    """Validate every public_id, then apply the delta in one transaction."""
    from eshia_research.commentary.transfer import read_delta, import_delta, verify_target

    delta = read_delta(input_path)
    db = SessionLocal()
    try:
        stats = import_delta(db, delta, dry_run=dry_run)
        counts = verify_target(db, delta["source_key"])
    except ValueError as error:
        db.rollback()
        typer.echo(f"REFUSED: {error}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
    prefix = "DRY RUN — no changes written. " if dry_run else ""
    typer.echo(
        f"{prefix}{delta['source_key']}: inserted={stats.inserted} updated={stats.updated} "
        f"deleted={stats.deleted} unchanged={stats.unchanged}. "
        f"Target now holds rows={counts['rows']} matched={counts['matched']} "
        f"linked_hadiths={counts['linked_hadiths']}."
    )


@app.command("chain-manifest")
def chain_manifest_cmd(
    source_book_id: str = typer.Argument(..., help="e.g. 11021 for Faqih"),
    output: str = typer.Option(..., "--output", help="Where to write the manifest JSON"),
) -> None:
    """Fingerprint the parsed chains THIS database holds for a book.

    Run on the deployment target. The result is what makes the export a real
    delta instead of a full dump.
    """
    import json

    from eshia_research.isnad.transfer import build_manifest

    db = SessionLocal()
    try:
        manifest = build_manifest(db, source_book_id)
    except ValueError as error:
        typer.echo(f"REFUSED: {error}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False)
    typer.echo(
        f"Manifest for {source_book_id}: {len(manifest['entries'])} hadith(s) -> {output}"
    )


@app.command("export-chain-delta")
def export_chain_delta_cmd(
    source_book_id: str = typer.Argument(..., help="e.g. 11021 for Faqih"),
    output: str = typer.Option(..., "--output", help="Destination .json.gz"),
    manifest: str | None = typer.Option(
        None, "--manifest", help="Target's manifest; omit to export every hadith"
    ),
) -> None:
    """Export only the hadiths whose split or chains differ from the target."""
    import json

    from eshia_research.isnad.transfer import export_delta, write_delta

    loaded = None
    if manifest:
        with open(manifest, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)

    db = SessionLocal()
    try:
        delta = export_delta(db, source_book_id, loaded)
    except ValueError as error:
        typer.echo(f"REFUSED: {error}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
    write_delta(delta, output)
    summary = delta["summary"]
    typer.echo(
        f"Delta for {source_book_id}: changed={summary['changed']} "
        f"unchanged={summary['unchanged']} "
        f"(of {summary['total_local_hadiths']} local hadiths) -> {output}"
    )
    stranded = summary["present_on_target_only"]
    if stranded:
        typer.echo(
            f"NOTE: {len(stranded)} hadith(s) exist on the target but not here; "
            "they are left alone, never deleted: "
            + ", ".join(stranded[:5])
            + ("..." if len(stranded) > 5 else "")
        )


@app.command("import-chain-delta")
def import_chain_delta_cmd(
    input_path: str = typer.Argument(..., help="The .json.gz produced by export"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Validate and roll back without writing"
    ),
) -> None:
    """Validate every public_id and identity, then apply in one transaction."""
    from eshia_research.isnad.transfer import read_delta, import_delta, verify_target

    delta = read_delta(input_path)
    db = SessionLocal()
    try:
        stats = import_delta(db, delta, dry_run=dry_run)
        counts = verify_target(db, delta["source_book_id"])
    except ValueError as error:
        db.rollback()
        typer.echo(f"REFUSED: {error}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
    prefix = "DRY RUN - nothing written. " if dry_run else ""
    typer.echo(
        f"{prefix}{delta['source_book_id']}: hadiths={stats['hadiths']} "
        f"chains={stats['chains']} nodes={stats['nodes']} "
        f"resolutions={stats['resolutions']} "
        f"persons_created={stats['persons_created']} "
        f"narrators_created={stats['narrators_created']}."
    )
    typer.echo(
        f"Target now holds chains={counts['chains']} nodes={counts['nodes']} "
        f"resolutions={counts['resolutions']} needs_review={counts['needs_review']}."
    )



if __name__ == "__main__":
    app()
