# Architecture

## Current pieces

```text
lib.eshia.ir  --(httpx, polite client)-->  crawler/jobs.py  --(SQLAlchemy)-->  Postgres/SQLite
                                                  |
                                            crawler/parser.py (BeautifulSoup/lxml)
                                                  |
                                            normalise.py (Arabic/Persian)

FastAPI (api/) and CLI (cli.py) share the SQLAlchemy model and research layers
against the same database. The sibling Next.js app (`../web`) consumes the API
for reading, split review, narrator profiles, and the transmission graph.

Hadith text -> hadith_extractor.py -> isnad/tokenizer.py -> chains/chain_nodes
                                                        |
                                                        v
Mu'jam pages -> rijal/ person layer -> mention resolutions -> review decisions
                                                        |
                                                        v
                         reader + narrator profiles + transmission network

mcp/server.py implements the same read path for future AI-tool access,
behind a not-yet-wired MCP transport.
```

## Data flow

1. `crawl-metadata` fetches a category listing page, parses book rows
   (`crawler/parser.parse_category_page`), and upserts `Category`/`Author`/
   `Book` rows (`crawler/jobs.upsert_book_from_entry`).
2. `crawl-book` / `crawl-page` fetch one or more `.../{book_id}/{volume}/{page}`
   URLs, parse page text + metadata (`crawler/parser.parse_page`), and
   upsert `Volume`/`Page` rows. Every fetch — success or failure — is logged
   to `CrawlLog`, and successful fetches are recorded in the on-disk
   `Checkpoint` so interrupted crawls resume without re-fetching.
3. Both `*_original` and `*_normalised` text variants are stored. Search
   matches against the normalised variant; display/citation uses the
   original.

## Why a normalised + original pair instead of one column

Arabic/Persian sources are inconsistent about diacritics (tashkīl) and which
glyph variant is used for yeh (ي vs ی) and kaf (ك vs ک) — the same word can
appear several different ways across volumes or even within one page (see
`normalise.py`). Normalising for search means a query in one variant still
matches text written in another, without destroying the original text that
citations need to quote verbatim.

## Next.js UI

The sibling `web/` application is a separate deployable. It provides book,
page, chapter, and hadith readers; split/person review screens; narrator
profiles and appearances; inline isnad linking; and a decision-aware
transmission network with edge evidence and quality overlays.

The API overlays externally verified admin decisions on machine resolution at
read time through `rijal/effective_resolution.py`, so the reader, review queue,
and graph agree on the effective person without destroying resolver evidence.

## Planned: MCP server

`mcp/server.py` already implements `search_library`, `get_page`,
`get_book_metadata`, and `search_exact_phrase` against the local DB and
returns a `Citation` (title, author, volume, page, source_url) alongside
every result. What's missing is the actual MCP protocol wiring (transport,
tool-schema registration) — see TODOs in that file for the next steps.

## Swapping search backends later

`search.search_pages` is the only place that knows how search is currently
implemented (SQL `ILIKE` over `text_normalised`). Replacing it with
Meilisearch/OpenSearch means changing that one function's body and adding an
indexing step after crawls — callers (CLI, API, MCP scaffold) don't need to
change as long as the returned shape (page, book, snippet) stays the same.
