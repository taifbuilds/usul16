# eShia Research

A local-first mirror/research toolkit for the [eShia digital library](https://lib.eshia.ir)
(~7,600 book titles, ~17,700 volumes of Shia jurisprudence, hadith, history,
and related texts). The project now combines a resumable crawler, a
Postgres/SQLite-backed hadith corpus, isnad and person-identity resolution,
a FastAPI research API, and the sibling `../web` Next.js reader/review UI.
An MCP query layer remains scaffolded but is not yet wired to a transport.

## Project purpose

1. Preserve eShia source pages and provenance in a local research database.
2. Extract stable hadith records, chains, narrator mentions, and auditable
   person-resolution evidence.
3. Provide a local API, CLI, and web reader/review interface with exact
   citations and explicit ambiguity.

Crawling defaults to fast/concurrent mode — see
[Fast crawling](#fast-crawling) and [Crawl etiquette](#crawl-etiquette) below.

## Repository structure

```text
eshia-research/
  src/eshia_research/
    config.py        # env-driven settings
    db.py             # SQLAlchemy engine/session
    models.py         # Category, Author, Book, Volume, Page, CrawlLog
    schemas.py        # Pydantic response models
    normalise.py       # Arabic/Persian text normalisation
    search.py          # search interface (DB LIKE/ILIKE today)
    cloudstore.py       # object-storage abstraction for cloud-buffer crawling (R2/local)
    crawler/
      client.py        # polite HTTP client: delay, retries, checkpointing
      parser.py         # HTML parsers for category/book/page markup
      jobs.py           # orchestration: client + parser + DB
    api/
      main.py, routes_books.py, routes_search.py
    mcp/
      server.py         # MCP tool scaffold (not yet wired to a transport)
    isnad/              # chain tokenizer and indexer
    rijal/              # Mu'jam, person, tabaqat, eval, and review layers
    cli.py
  migrations/           # Alembic
  tests/
  data/samples/         # saved real HTML fixtures used by tests
  data/checkpoints/      # crawl resume state (created at runtime)
```

## Setup

Requires Python 3.11 or newer. The active local environment and test suite run
on Python 3.11; Python 3.12 is also supported.

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate.bat for cmd.exe
pip install -e ".[dev]"
cp .env.example .env
```

## Running the database

**SQLite (default, zero setup):** `DATABASE_URL=sqlite:///./eshia_research.db`
in `.env` — this is the default, nothing else to do.

**Postgres (optional):**

```bash
docker-compose up -d db
# then in .env:
# DATABASE_URL=postgresql+psycopg2://eshia:eshia@localhost:5432/eshia_research
```

Then apply migrations (works for either backend):

```bash
alembic upgrade head
# or, for a quick local SQLite start without migrations:
python -m eshia_research.cli init-db
```

## Running the crawler

```bash
# Metadata only, capped small for testing:
python -m eshia_research.cli crawl-metadata --category-url "https://lib.eshia.ir/فقه" --limit 5

# A handful of pages from one book:
python -m eshia_research.cli crawl-book --book-url "https://lib.eshia.ir/10009" --max-pages 5

# Exactly one page:
python -m eshia_research.cli crawl-page --url "https://lib.eshia.ir/10009/1/1"
```

Re-running the same command resumes safely — already-fetched URLs are
skipped via the on-disk checkpoint at `data/checkpoints/crawl.json` and the
`crawl_logs` DB table.

## Fast crawling

`crawl-book` defaults to concurrent mode (`CRAWL_CONCURRENCY=10` in
`.env.example`): it fetches page 1 to learn the volume's page count, then
fetches the rest in parallel instead of following next-page links one at a
time. Measured live against `lib.eshia.ir`: 60 pages in ~7.7s with 10
workers vs. ~60s sequentially (`--concurrency 1`).

```bash
# Uses CRAWL_CONCURRENCY from .env
python -m eshia_research.cli crawl-book --book-url "https://lib.eshia.ir/10009" --max-pages 500

# Override per-run
python -m eshia_research.cli crawl-book --book-url "https://lib.eshia.ir/10009" --max-pages 500 --concurrency 20
```

**Why this doesn't just remove all limits and go flat-out:** once you have
multiple workers running, `CRAWL_DELAY_SECONDS` per-worker stops being a
meaningful safety net (N workers each "waiting politely" independently is
still N times the load on the target). What actually protects against
hammering a struggling server is `AdaptiveThrottle`
(`crawler/client.py`) — a shared circuit breaker across all workers: if
`CRAWL_THROTTLE_ERROR_RATE` of the last `CRAWL_THROTTLE_WINDOW` requests
came back as retryable errors (429/500/502/503/504), every worker pauses
for `CRAWL_THROTTLE_COOLDOWN_SECONDS` before sending another request. This
is what lets "fast" degrade gracefully into "backed off" instead of
escalating into something indistinguishable from a denial-of-service
against a small site. Tune the throttle settings before tuning concurrency
up further.

`crawl-metadata` doesn't have a concurrent mode — it only needs ~15-30
requests total (one per category page) since each one returns its whole
book table in a single response, so the speedup wouldn't matter.

## Cloud-buffer crawling

Lets a cloud worker (e.g. Railway) crawl full text 24/7 without needing 24/7
storage of its own — it batches fetched pages to an object store (Cloudflare
R2's free tier: 10GB storage, 1M write-ops/month, zero egress) instead of a
database, and a separate process wherever your real storage lives (e.g. your
own computer) drains the buffer whenever it's online. Neither side needs the
other to be up at the same time.

```bash
# 1. Once, locally: export the book catalog (titles/volume counts) the
#    cloud worker needs — it has no database of its own.
python -m eshia_research.cli export-book-list --output book_list.json
# ship book_list.json with the cloud deploy

# 2. On the cloud worker (set CLOUD_STORE_BACKEND=r2 and the R2_* vars in
#    its environment — see below):
python -m eshia_research.cli crawl-to-cloud --book-list book_list.json

# 3. On your own computer, whenever it's online (e.g. a scheduled task
#    every few minutes) — uses CLOUD_STORE_BACKEND from *your* local .env,
#    so it can point at the same R2 bucket while the cloud worker keeps
#    using its own:
python -m eshia_research.cli drain-cloud
```

R2 setup (free tier is enough for this project's scale — 3.5-4M pages
batched at 500/batch is ~7-8k write operations, well under the 1M/month
free allowance):

1. Create a Cloudflare account, create an R2 bucket.
2. Generate an S3-compatible API token (gives you an Access Key ID + Secret
   Access Key) scoped to that bucket.
3. Set in the cloud worker's environment: `CLOUD_STORE_BACKEND=r2`,
   `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.
4. `pip install -e ".[cloud]"` on the cloud worker (pulls in `boto3`, kept
   out of the base dependency set since it's only needed for this path).

Durability model: two independent `Checkpoint` files give two-stage safety
without any new database tables. The cloud worker's checkpoint marks a URL
done only *after* its batch is uploaded (a crash before upload just
re-fetches that page on restart — no data loss). Your local checkpoint
(`--checkpoint`, separate from the main crawl one) marks a batch done only
after it's upserted into your real DB *and* deleted from the object store
(a crash mid-batch just re-processes that one batch next run — upserting is
idempotent, so reprocessing is harmless, not duplicated).

The cloud worker's own crawl checkpoint (which URLs it's already fetched
*this run*) only needs to survive within one run, not across restarts — if
the worker redeploys/restarts, some already-uploaded pages get re-fetched
into a new batch. Wasted crawl time, not a correctness problem.

`LocalFileStore` (the default, `CLOUD_STORE_BACKEND=local`) is a drop-in
stand-in for R2 backed by a local directory — used by the test suite and
for validating the whole batch/drain pipeline before setting up real R2
credentials.

## Running the API

```bash
uvicorn eshia_research.api.main:app --reload
```

Endpoints: `GET /health`, `GET /books`, `GET /books/{id}`,
`GET /books/{id}/pages`, `GET /pages/{id}`, `GET /search?q=...`.

## Running tests

```bash
pytest
```

Parser tests run against real saved HTML in `data/samples/` (no live
requests), so they're fast and don't depend on the site being reachable.

## Crawl etiquette

- `lib.eshia.ir/robots.txt` allows generic crawlers (`User-agent: *` →
  `Disallow:` empty) but explicitly disallows several named bots, including
  `ClaudeBot`. The default `CRAWL_USER_AGENT` in `.env.example` is a
  standard browser string per project decision; if you want the crawler to
  identify itself transparently instead, change `CRAWL_USER_AGENT` to
  something descriptive (e.g. `EshiaResearchBot/0.1 (contact: you@x.com)`).
- `CRAWL_MAX_RETRIES` bounds retries on 429/500/502/503/504 with exponential
  backoff (and respects `Retry-After` when the server sends one), in
  addition to the shared `AdaptiveThrottle` described above.
- This project's intended use is a personal/private research mirror, not a
  public site republishing eShia's content under a different brand — the
  underlying classical texts are mostly public domain, but eShia's own
  digitization, OCR, and formatting work isn't necessarily yours to
  redistribute just because it was crawled.

## Known limitations / TODOs

- Some books on eShia are scanned-image-only pages with no selectable text
  (`Page.text_raw` will be `None`, see `parser.is_image_only`). OCR is out
  of scope for this MVP.
- Category page parsing covers the simple `table#BooksList` layout seen in
  `فقه`; subcategory nesting and pagination on larger categories aren't
  handled yet — see TODOs in `crawler/parser.py`.
- Search is plain SQL `ILIKE` over `text_normalised`; swappable for
  Meilisearch/OpenSearch later behind `search.search_pages`.
- The MCP server (`mcp/server.py`) implements its four planned tools against
  the local DB but isn't yet wired to an actual MCP transport — see TODOs in
  that file.
- Narrator resolution intentionally leaves weak cases ambiguous. Use
  `eval-resolution` and the person-resolution review UI to monitor coverage
  and contradictions before expanding beyond Al-Kafi.
- The graph UI has backend/unit coverage and build checks, but complex canvas
  interactions still need an end-to-end browser test suite.
