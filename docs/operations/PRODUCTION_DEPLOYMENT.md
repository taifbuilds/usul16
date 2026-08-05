# Production Deployment — Architecture and Operations

Canonical reference for how Usul16 production actually works: what runs, where
it lives, how each kind of change reaches it, and why it is built this way.

Written for engineers who did not build it. It assumes you can read Python,
TypeScript and a systemd unit, and assumes nothing about this project's history.

**If you change how production is deployed, change this document in the same
commit.** The single most expensive class of failure here is documentation that
has quietly stopped describing the machine (see [Bug 1](#bug-1--wrong-application-root)).

---

## 0. Provenance of this document

Operational docs rot when they mix what was observed with what was assumed, so
this is stated up front:

**Verified by direct inspection at the time of writing**

- Production responds on `https://usul16.com/api/health` → `200 {"status":"ok"}`.
- Commentary is live: `alkafi-2`, `alkafi-6`, `alkafi-54` each return two
  commentaries (`mirat-al-uqul`, `sharh-al-mazandarani`); `alkafi-3761` returns
  one (Mir'at only — it is outside the Usul, which Mazandarani does not cover).
- `origin/main` is at `21e339e "Updating Pipeline (#4)"` (2026-08-05, 39 files,
  +6,038/−2,990) and contains the whole commentary system: `commentary/`,
  `transfer.py`, `deploy-db.sh`, migration `e4c91f7b2d68`, `ApparatusShelf.tsx`.
- Every `/home/deploy` path in `origin/main:infra/` reads `/home/deploy/app`.
- `infra/deploy/deploy-db.sh:161` still contains the `head -c 4000` truncation
  described in [Bug 4](#bug-4--false-deployment-failure-architectural).

**Reported by the operator, consistent with the repository, not independently
inspected**

- Server type Hetzner CX23. `AGENT_HANDOFF.md` §1 independently records
  "Ubuntu 24.04, 2 vCPU, 3.7 GB RAM, 2 GB swap, ~22 GB free", which is
  consistent with a CX-class instance.
- The order and detail of the first-deployment bootstrap steps (firewall, swap,
  `deploy` user creation).
- The exact row counts now in production. They match the delta sizes measured
  locally at export time, and production behaviour is consistent with them.

Where a fact could not be confirmed it is marked inline. Do not silently promote
a marked fact to unmarked; re-verify it and cite how.

---

## 1. What is true today

One Hetzner VPS running Ubuntu 24.04. Four moving parts: Caddy, a FastAPI
process, a Next.js process, and a SQLite file. No containers, no orchestrator,
no database server, no queue, no cache.

```
                       Internet (HTTPS :443)
                              │
                    ┌─────────▼─────────┐
                    │       Caddy       │  TLS termination, Let's Encrypt
                    │   (system unit)   │  the only public listener
                    └────┬─────────┬────┘
              /api/*     │         │    everything else
        (prefix stripped)│         │
             ┌───────────▼──┐   ┌──▼─────────────┐
             │   FastAPI    │   │    Next.js     │
             │ 127.0.0.1:   │   │ 127.0.0.1:3000 │
             │    8000      │   │  (npm start)   │
             │ usul16-api   │   │  usul16-web    │
             └───────┬──────┘   └────────────────┘
                     │ read-only
             ┌───────▼────────────────────────────┐
             │ /home/deploy/app/eshia-research/   │
             │        eshia_research.db           │
             │        (SQLite, ~3 GB)             │
             └────────────────────────────────────┘
```

**Application root is `/home/deploy/app`.** Not `/home/deploy/usul16` — see
[Bug 1](#bug-1--wrong-application-root).

```
/home/deploy/app                     git checkout, tracks origin/main
├── eshia-research/
│   ├── .venv/                       backend virtualenv
│   ├── .env                         server-only, never committed
│   └── eshia_research.db            SQLite corpus + commentary
├── web/
│   └── .env.local                   server-only, never committed
└── infra/                           source of truth for units and scripts

/home/deploy/deploy-usul16.sh        what CI executes (a copy, see §5.1)
/home/deploy/incoming/               staging for uploaded deltas
```

### Explicitly not used

Documented because their absence is a design decision and someone will
otherwise assume them:

- **No Docker.** The runtime is systemd + a virtualenv + `npm start`. If Docker
  is installed on the box it is incidental and nothing depends on it. Do not
  containerise without a present-tense reason.
- **No Postgres.** See [§4](#4-sqlite-in-production).
- **No process manager beyond systemd.** No PM2, no supervisor.
- **No CDN, no Redis, no object storage in the serving path.** (R2 is used by
  the *crawler*, never by production serving.)

---

## 2. Caddy

Caddy is the only process bound to a public port. Its whole configuration:

```caddyfile
usul16.com {
	encode gzip zstd

	handle_path /api/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle {
		reverse_proxy 127.0.0.1:3000
	}
}
```

### What it does

**TLS termination and certificates.** Caddy obtains and renews Let's Encrypt
certificates automatically from the `usul16.com` site block — there is no certbot,
no cron job, no renewal runbook. This is the main reason Caddy was chosen over
nginx: the certificate lifecycle is a non-event.

**Routing.** Two rules, and the order matters:

- `handle_path /api/*` → `127.0.0.1:8000`. `handle_path` **strips the matched
  prefix**, so `https://usul16.com/api/health` arrives at FastAPI as `/health`.
  The API has no idea it is mounted under `/api`.
- `handle` (no matcher) → `127.0.0.1:3000`. Everything else is the Next.js app.

**Compression.** `encode gzip zstd` — meaningful here because Arabic commentary
text compresses extremely well.

### Why the browser never talks to FastAPI directly

Four reasons, each sufficient on its own:

1. **FastAPI is bound to `127.0.0.1`.** It is not reachable from outside the
   host at all. This is deliberate: the API has no authentication (every route
   is public and read-only), so its only protection is that the loopback
   interface is not routable.
2. **One origin, no CORS in the browser path.** Because the API is served from
   the same origin under `/api`, the reader makes same-origin requests.
   `API_ALLOWED_ORIGINS` still exists for local development, where the Next dev
   server sits on a different port.
3. **One certificate, one hostname.** A second public listener would need its
   own TLS.
4. **A failure boundary.** Caddy keeps serving (and returns a clean 502) while
   the API restarts — which `deploy-db.sh` does on every data deployment.

### Request flow

```
GET https://usul16.com/hadith/alkafi-2
  → Caddy :443, TLS terminated
  → no /api prefix → handle → 127.0.0.1:3000
  → Next.js server-renders the page; during render it fetches
      https://usul16.com/api/hadiths/alkafi-2
    → Caddy :443
    → /api/* matches → handle_path strips it → 127.0.0.1:8000/hadiths/alkafi-2
    → FastAPI reads SQLite, returns JSON incl. `commentaries`
  → HTML returns to the browser
  → the reader lazily fetches /api/hadiths/alkafi-2/commentaries when a
    disclosure is opened
```

The commentary **body** is deliberately not in the page payload. The summary
(title, author, printed location, evidence basis) is server-rendered; the text
itself is fetched on open. That is why a hadith carrying two long commentaries
does not inflate every page load.

---

## 3. The two application processes

### FastAPI — `usul16-api`

Serves the read-only JSON API over the corpus: hadiths, chapters, chains,
narrators, topics, search, transmission graph, and commentary.

```ini
[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/app/eshia-research
EnvironmentFile=/home/deploy/app/eshia-research/.env
ExecStart=/home/deploy/app/eshia-research/.venv/bin/uvicorn \
          eshia_research.api.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
```

Three details that matter:

- **`WorkingDirectory` is load-bearing.** `DATABASE_URL` is
  `sqlite:///./eshia_research.db` — *relative*. It resolves against the working
  directory. Change the working directory without changing the URL and the API
  silently opens a different (or empty) database. This is precisely how Bug 1
  would have manifested.
- **`--workers 1`.** One process. SQLite readers are cheap and the box has 2
  vCPU; more workers would multiply memory against a ~3 GB file for no gain at
  current traffic.
- **`EnvironmentFile`** is the same `.env` the CLI reads, so a CLI command run
  by hand in that directory sees the same database as the service.

### Next.js — `usul16-web`

Frontend only. It renders the reader and calls the API; it never opens SQLite
and has no database credentials.

```ini
[Service]
WorkingDirectory=/home/deploy/app/web
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm start
After=network.target usul16-api.service
Requires=usul16-api.service
```

`npm start` serves a **prebuilt** `.next` directory. The build happens during
code deployment, not at boot — so a deploy that fails to build leaves the old
build running rather than starting a broken one.

`web/.env.local` holds `NEXT_PUBLIC_API_BASE_URL=https://usul16.com/api`. It is
`NEXT_PUBLIC_*`, so it is inlined into the client bundle **at build time**;
changing it requires a rebuild, not a restart.

---

## 4. SQLite in production

This is a deliberate choice, revisited more than once, and kept.

### Why SQLite

**The workload is read-only.** Production never writes. It serves a corpus
built offline on a workstation. There are no user accounts, no comments, no
submissions — nothing that mutates state in response to a request. A database
server's core value is concurrent, transactional, multi-writer access; none of
that is needed here.

**It is a file.** Backup is `cp`. Rollback is `cp` back. Verification is
`PRAGMA integrity_check`. Shipping a whole new corpus is a file move plus a
service restart. Compare with Postgres: `pg_dump`/`pg_restore` cycles, role and
permission management, connection tuning, a second daemon to monitor, its own
upgrade path, and its own backup strategy — all to serve data that never
changes at runtime.

**It removes an entire failure class.** There is no connection pool to exhaust,
no listener to misconfigure, no separate service that can be up while the app is
down. If the file is present and readable, the API works.

**Reads are fast enough by a wide margin.** The heavy work (crawling,
extraction, isnad resolution, commentary alignment) happens offline. Production
executes indexed lookups against a static file in the page cache.

### Why "read-only" is a property, not a setting

Nothing enforces read-only at the filesystem level today — the file is writable
by `deploy`. It is read-only because **no production code path writes to it**:
the API layer issues queries only, and editorial write routes exist solely
behind `API_ADMIN_TOKEN`, which is empty in production (disabling them).

Consequences to respect:

- **Never run a heavy writer against the served database.** A crawl or an
  indexing job writing concurrently has already produced `database is locked`
  in this project (`AGENT_HANDOFF.md` §5). Build offline; ship the result.
- `deploy-db.sh` is the *only* sanctioned writer, and it writes in one
  transaction, then restarts the API.

### Why not Postgres

Not "not yet, we're small" — the shape of the problem does not call for it.
Adopting Postgres would mean a second daemon, a migration of ~3 GB of corpus, a
new backup regime, and new failure modes, in exchange for concurrency features
that a read-only workload cannot use. Revisit only on a concrete present-tense
trigger: production writes, multi-server serving, or a dataset that stops
fitting comfortably on disk.

---

## 5. The three deployment layers

The central idea of this system. **Code, schema and data reach production by
three independent paths, on purpose.**

```
Layer 1  CODE     git push → GitHub Actions → deploy-usul16.sh   automatic
Layer 2  SCHEMA   alembic upgrade head                            manual, idempotent
Layer 3  DATA     infra/deploy/deploy-db.sh                       manual, from a workstation
```

They are independent because they differ in blast radius, in reversibility, and
in how long they take. Coupling them would force the safest to move at the pace
of the most dangerous.

### 5.1 Layer 1 — code

`.github/workflows/deploy.yml` triggers on push to `main`, SSHes to the server
as `deploy`, and runs `/home/deploy/deploy-usul16.sh`:

```bash
APP_DIR="/home/deploy/app"
cd "$APP_DIR"
git fetch origin
git reset --hard origin/main          # server is a mirror of main, never a workspace
cd "$APP_DIR/eshia-research" && source .venv/bin/activate && pip install -e .
cd "$APP_DIR/web" && npm ci && npm run build
sudo systemctl restart usul16-api usul16-web
sudo systemctl is-active --quiet usul16-api usul16-web
```

Properties worth understanding:

- **`git reset --hard origin/main`.** The checkout is disposable. Never edit
  files on the server; the next deploy destroys them. The deploy key is
  read-only, so the server cannot push its own state back.
- **Build before restart.** With `set -euo pipefail`, a failing build aborts the
  script *before* the restart, leaving the previous version running. Failure
  mode is "deploy didn't happen", not "site is down".
- **Deploys queue** (`cancel-in-progress: false`) — two merges cannot interleave
  a `git reset` with an `npm run build`.
- **`/home/deploy/deploy-usul16.sh` is a copy** of `infra/deploy/deploy-usul16.sh`,
  not a symlink. Editing the repo copy does not change what CI runs until you
  copy it over. This is a real trap; see the checklist in
  [§15](#15-deployment-checklists).

**Git deploys code and nothing else.** No migrations, no data. A merge to `main`
can add a table-reading feature without the table existing — the code ships, the
schema does not follow automatically.

### 5.2 Layer 2 — schema

Alembic, run manually on the server:

```bash
ssh deploy@<host>
cd /home/deploy/app/eshia-research
source .venv/bin/activate
alembic upgrade head
```

Migrations do structure only: `CREATE TABLE`, `ALTER TABLE`, indexes,
constraints. **Migrations never insert commentary rows.** That separation is
deliberate — a migration is a schema statement that should be replayable on any
copy of the database, including an empty one. Data belongs to Layer 3.

#### Migration `e4c91f7b2d68`

```
revision      = "e4c91f7b2d68"
down_revision = "a6c8d2e4f190"
```

Creates `hadith_commentaries`: the source-preserving ledger of commentary
passages. Columns of note — `source_key` (which sharh), `hadith_id` (nullable:
an extracted passage may exist without being linked to any hadith),
`commentary_raw`/`commentary_normalised`, printed extent (`volume_start`,
`page_start`, …), `match_status`, `match_method`, `match_score`,
`matcher_version`, `match_evidence_json`.

Two unique constraints encode the publication model:

- `(commentary_book_id, source_key, source_sequence)` — one row per printed passage.
- `(source_key, hadith_id)` — **at most one published commentary per hadith per
  source.** Contention between two passages claiming the same hadith must be
  resolved before import, not by the database.

`down_revision = a6c8d2e4f190` chains onto what production already had, so
`alembic upgrade head` is a single forward step and a no-op if already applied.

> **Known landmine.** `AGENT_HANDOFF.md` §6 records Alembic schema drift: nine
> tables (`persons`, `mention_resolutions`, …) exist in production but have no
> migration, having been created by `Base.metadata.create_all()`. Consequence:
> **`alembic upgrade head` against an empty database does not reproduce
> production.** Migrations are safe to apply forward to the *existing*
> production database; they cannot rebuild it from nothing. Baseline before
> authoring new migrations.

### 5.3 Layer 3 — data

`infra/deploy/deploy-db.sh`, run from a workstation.

**Why it exists.** Code deploys itself; the database does not travel through
Git (`*.db` is gitignored, and a 3 GB binary has no business in version
control). Before this script, that half of deployment was a manual procedure
described in prose in `AGENT_HANDOFF.md` §7 and had never been executed.

**Why it is deliberately outside GitHub Actions.** Three reasons:

1. **The source of truth is a workstation, not the repo.** The corpus and its
   commentary index live on the machine that crawled and built them. CI has no
   copy and no way to get one.
2. **Data deployment is not idempotent in the way code is.** Re-running a code
   deploy converges to `origin/main`. Writing data mutates a file that is the
   accumulated output of weeks of work. That deserves a human at the keyboard,
   a dry run, and an explicit decision.
3. **It must be able to refuse.** The import validates against production and
   aborts. An automated pipeline that runs on merge would either bypass the
   judgement or fail builds for reasons unrelated to the code being merged.

---

## 6. Commentary deployment architecture

### Why commentary ships separately from the corpus

The corpus (hadiths, chains, narrators) changes rarely and wholesale. Commentary
changes often and narrowly: a matcher improvement re-links a few thousand rows
while the other ~90,000 hadith rows are untouched. Coupling the two would mean
re-shipping the corpus to correct a matcher bug.

### Why not ship the database file

The served database is **~3 GB**. Shipping it on every commentary change is
unacceptable for reasons that compound:

- **Upload cost.** Multi-hour uploads from a home connection, repeated per
  iteration. During this project the commentary index was rebuilt roughly ten
  times in two days.
- **It overwrites everything.** A full file replaces production's copy wholesale,
  discarding any divergence — including anything applied to production and not to
  the workstation.
- **Waste.** The commentary payload is ~45 MB of text (~19 MB compressed across
  both sources). Shipping 3 GB to deliver 19 MB is a ~160× overhead.
- **The failure window is worse.** A partially transferred multi-gigabyte file is
  a much larger problem than a failed 12 MB upload.

### Delta deployment

Only rows whose **content** differs travel:

1. Production reports a manifest: for every row of that `source_key`, a stable
   key plus a content fingerprint.
2. The workstation compares its rows against that manifest and exports only
   `changed` (plus `removed`), skipping `unchanged`.
3. The delta ships as gzipped JSON.

Measured on the first deployment: Mir'at **14,300 rows → ~11.6 MB**,
Mazandarani **4,315 rows → ~7.6 MB**. On a re-deploy where nothing changed the
delta is empty and the script exits early without touching production.

### Transactionality

The import validates **everything** before writing **anything**, then applies
the whole delta in one transaction. A delta cannot half-apply. If validation
fails the script exits non-zero, production is untouched, and the failure is
reported before any write.

### Backups and rollback

A timestamped copy is taken **before** any write:

```
eshia_research.db.bak-YYYYMMDDTHHMMSSZ
```

Every run prints its exact rollback command — on success, on import failure, and
on failed verification:

```bash
ssh deploy@<host> 'cd /home/deploy/app/eshia-research \
  && cp eshia_research.db.bak-<stamp> eshia_research.db \
  && sudo systemctl restart usul16-api'
```

Rollback is a file copy and a restart because the database is a file. This is
the operational dividend of [§4](#4-sqlite-in-production).

---

## 7. `public_id`, and why `hadith_id` must never travel

**The most important architectural decision in the data pipeline.**

`hadith_commentaries.hadith_id` is a foreign key to `hadiths.id` — a local
autoincrement integer. Production is a **separate copy** of the corpus, built by
its own extraction run. Nothing guarantees that `hadiths.id = 41822` denotes the
same report on both machines. Row ids depend on insertion order, on rebuilds, on
re-extractions, on rejected rows being purged.

If the delta carried `hadith_id`, and the two copies disagreed by even one row,
every commentary after that point would attach to the wrong hadith. And it would
**fail silently** — every foreign key valid, every row present, no error, no
crash. The reader would display al-Majlisi's commentary on report 5 underneath
report 4. For a project whose entire value is source-verifiable attribution,
that is the worst possible failure: confident, plausible, and wrong.

The delta therefore carries **`public_id`** (`alkafi-2372`) — the stable
identifier a hadith keeps across rebuilds, and the same one used in permalinks
and citations. On import, production resolves `public_id → local id` itself.

The import **validates every `public_id` before writing anything**. If any
cannot be resolved, it refuses the entire delta rather than importing the
resolvable subset — a partially applied delta is exactly the silent corruption
this design exists to prevent.

This turns a catastrophic silent failure into a loud refusal at the gate. It is
also cheap: `public_id` is already indexed and already the API's addressing
scheme.

> This class of bug is not hypothetical here. The same identity assumption was
> caught once during local work, by an identity guard comparing `public_id`
> against `id` before copying rows between two local databases.

---

## 8. `deploy-db.sh`, stage by stage

```bash
./infra/deploy/deploy-db.sh <source-key> [--dry-run]
./infra/deploy/deploy-db.sh mirat-al-uqul
./infra/deploy/deploy-db.sh sharh-al-mazandarani --dry-run
```

Run from the **repository root** on a workstation, in an environment with `ssh`,
`scp` and the project venv (Git Bash on Windows is supported explicitly).

Configuration, all overridable by environment variable:

| Variable | Default |
|---|---|
| `USUL16_HOST` | `deploy@91.98.192.21` |
| `USUL16_REMOTE_APP` | `/home/deploy/app/eshia-research` |
| `USUL16_REMOTE_INCOMING` | `/home/deploy/incoming` |
| `DATABASE_FILE` | `eshia-research/eshia_research.db` |
| `PYTHON` | auto-detected (see below) |

**Interpreter resolution.** Tries `.venv/bin/python`, then
`.venv/Scripts/python.exe` (Windows virtualenvs put it there), then `python3`,
then `python` — and then **refuses to run unless the chosen interpreter can
`import eshia_research`**. Without that guard, Git Bash silently falls through
to a system Python without the project installed and fails later with a
confusing error.

The ordering principle: **everything that can fail without touching production
happens first.** Fingerprint, export, upload, migrate, validate — then write.

### Stage 1/8 — read the production manifest

```bash
ssh <host> "cd <app> && .venv/bin/python -m eshia_research.cli \
  commentary-manifest '<source-key>' --output <incoming>/manifest-<key>.json"
scp <host>:<incoming>/manifest-<key>.json → local
```

Asks production what it already has. This is what makes the transfer a delta on
the wire rather than a full dump diffed after arrival. Failure here usually
means the schema is missing — the script says so explicitly ("Is the migration
applied?"), which is how [Bug 3](#bug-3--no-such-table-hadith_commentaries) was
diagnosed in seconds.

### Stage 2/8 — export the delta

```bash
DATABASE_URL="sqlite:///<abs>" python -m eshia_research.cli \
  export-commentary-delta '<key>' --manifest <manifest> --output <delta>.json.gz
```

Compares local rows against the manifest, writes only what differs. Prints
`changed / unchanged / removed`. **If the delta is under 200 bytes the script
exits 0 early** — production already matches, nothing to do.

`DATABASE_URL` is built as an **absolute** path (and converted with `cygpath -m`
under Git Bash) because the CLI runs from the repository root while the database
lives a directory below it; a relative URL resolves to the wrong place.

### Stage 3/8 — upload

`scp` the gzip into `/home/deploy/incoming/`. Staging, never on top of the live
database.

### Stage 4/8 — migrations

```bash
ssh <host> "cd <app> && .venv/bin/alembic upgrade head"
```

Idempotent, so it runs every time. This is what makes a first-ever commentary
deployment work on a database that has never had the table.

### Stage 5/8 — back up before any write

```bash
cp eshia_research.db eshia_research.db.bak-<stamp>
```

The rollback command is composed here and printed on every subsequent failure
path.

### Stage 6/8 — validate, then import in one transaction

```bash
ssh <host> "... import-commentary-delta '<remote-delta>' [--dry-run]"
```

Resolves and validates every `public_id`; refuses the whole delta on any
failure; applies in a single transaction. On failure the script prints
`IMPORT FAILED — production was not modified` plus the rollback command, and
exits 1.

### Stage 7/8 — restart the API

```bash
sudo systemctl restart usul16-api
```

Needed because the process holds an open handle to the database file.

### Stage 8/8 — verify over HTTP

`systemctl is-active` reports a unit that starts and then 500s as healthy, so
verification asserts on real responses: poll `localhost:8000/health` for up to
60 s, then fetch a real data endpoint and check it carries a `commentaries`
field.

**This stage contains a known bug — see [Bug 4](#bug-4--false-deployment-failure-architectural).**

On success it prints the rollback command and lists older backups beyond the
newest three.

---

## 9. Dry run

```bash
./infra/deploy/deploy-db.sh <source-key> --dry-run
```

Performs stages **1–6** and stops:

| Stage | Dry run |
|---|---|
| 1 Manifest | yes — reads production |
| 2 Export | yes |
| 3 Upload | yes — file lands in `incoming/` |
| 4 `alembic upgrade head` | **yes — this does modify schema** |
| 5 Backup | yes |
| 6 Validate + import | validates, then **rolls back** |
| 7 Restart | no |
| 8 Verify | no |

**A dry run is not entirely side-effect-free.** It applies migrations, uploads a
file, and takes a backup. It does not write commentary rows: the import runs
inside a transaction that is rolled back after validation.

What it actually buys you: **every `public_id` in the delta is resolved against
production's corpus before you commit to anything.** If your workstation's
corpus has diverged from production's, this is where you find out — cheaply,
loudly, and without a partially-applied delta. Always dry-run first on a source
you have not deployed before.

---

## 10. First production deployment — timeline

The commentary system's first real deployment. Reconstructed from the verified
end state and the operator's account; bootstrap details are as reported
(see [§0](#0-provenance-of-this-document)).

**Server and access**
1. Hetzner CX23 provisioned, Ubuntu 24.04.
2. SSH key access; `deploy` user created as the owner of the application tree
   and the identity CI authenticates as.
3. Firewall: 22, 80, 443 only. Nothing else is publicly reachable — 8000 and
   3000 bind to loopback.
4. Swap configured (2 GB) — real headroom on a 3.7 GB box during `npm run build`.

**Runtime**
5. Python 3.11 + venv; Node 20 (Next.js 16 requires a current LTS); Caddy from
   its official repository.
6. Docker was installed during bootstrap but **nothing uses it** — see
   [§1](#explicitly-not-used).

**Code**
7. Read-only GitHub deploy key on the server; repository cloned to
   `/home/deploy/app`.
8. `infra/systemd/usul16-{api,web}.service` → `/etc/systemd/system/`, enabled.
9. `infra/caddy/Caddyfile` → `/etc/caddy/Caddyfile`, reloaded; Let's Encrypt
   issued automatically.
10. Backend venv + `pip install -e .`; frontend `npm ci && npm run build`.
11. `/home/deploy/deploy-usul16.sh` installed; GitHub Actions deployment
    verified end to end.

**Database**
12. Baseline corpus transferred and placed at
    `/home/deploy/app/eshia-research/eshia_research.db`; verified with
    `PRAGMA integrity_check` and a row-count floor.
13. `alembic upgrade head` → `e4c91f7b2d68` applied, creating
    `hadith_commentaries` (only after Bug 3 surfaced — see below).

**Commentary**
14. Branch merged to `main` as `21e339e` (PR #4), CI deployed the code —
    required before the CLI subcommands existed on the server (Bug 2).
15. `deploy-db.sh mirat-al-uqul --dry-run`, then for real: **14,300 rows**.
16. `deploy-db.sh sharh-al-mazandarani --dry-run`, then for real: **4,315 rows**.
17. Verified via API and in the browser: hadiths in the Usul carry both
    commentaries; hadiths outside it carry Mir'at only.
18. Redundant `eshia_research.db.bak-*` files removed, newest retained.

---

## 11. Bugs encountered

### Bug 1 — wrong application root

**Symptom (caught before reaching production).** The repository's infrastructure
files disagreed with each other: `deploy-db.sh` targeted
`/home/deploy/usul16/eshia-research` while the systemd units and
`deploy-usul16.sh` targeted `/home/deploy/app`.

**Cause.** `/home/deploy/usul16` was invented during development, when
`deploy-db.sh` was first written, without reading `infra/`. It then propagated
into deployment instructions, was echoed back as if authoritative, and was
"reconciled" in the wrong direction — by rewriting the systemd units and
`deploy-usul16.sh`, the files that *describe live production*, to match the new
invention (commit `25e2e85`).

**Why it was wrong.** `/home/deploy/app` was established in `dcb07ef` when the
infrastructure was first version-controlled, and is what `origin/main` deployed
from. `/home/deploy/usul16` appeared in exactly one commit and had no other
source. Evidence pointed one way; the change went the other.

**What it would have caused.** CI runs the **server's** copy of
`deploy-usul16.sh`, still pointing at `/home/deploy/app` — so deploys would have
kept working while the repository quietly stopped describing production. Worse,
anyone reinstalling the units from the repository would have pointed both
services at a directory that does not exist: both fail to start. An outage
caused by a documentation change.

**Resolution.** Commit `3db7bd1` restored `/home/deploy/app` everywhere and made
`deploy-db.sh` default to `/home/deploy/app/eshia-research`. The three
production files were verified byte-identical to `origin/main`.

**Lesson.** When a version-controlled description of production conflicts with a
newly written tool, the tool is wrong until the *server* says otherwise. Verify
against the machine — `systemctl cat usul16-api | grep WorkingDirectory` — not
against the more recently edited file.

### Bug 2 — `No such command 'commentary-manifest'`

**Symptom.** Stage 1 failed immediately; the CLI on the server did not recognise
the subcommand.

**Cause.** `deploy-db.sh` was run against production before the branch was
merged. The script and the three CLI subcommands it drives
(`commentary-manifest`, `export-commentary-delta`, `import-commentary-delta`)
ship as **code** — Layer 1. Production was still running pre-merge code.

**Resolution.** Merge to `main`, let CI deploy, re-run.

**Lesson.** Layer 3 depends on Layer 1. `deploy-db.sh` is not self-contained: it
is a driver for CLI commands that must already exist on the target. Merge and
deploy the code first.

### Bug 3 — `no such table: hadith_commentaries`

**Symptom.** With the code deployed, stage 1 still failed — now from SQLite,
because the table did not exist.

**Cause.** Merging deployed the code that *reads* the table; nothing created it.
Layer 1 does not run migrations. Production had never had `alembic upgrade head`
applied for `e4c91f7b2d68`.

**Resolution.**
```bash
cd /home/deploy/app/eshia-research && source .venv/bin/activate && alembic upgrade head
```

**Lesson.** The clearest possible demonstration of why the three layers are
distinct — and the reason `deploy-db.sh` now runs `alembic upgrade head` itself
at stage 4, so a first-ever deployment of a new commentary source cannot hit
this again.

### Bug 4 — false deployment failure *(architectural)*

**Symptom.** `deploy-db.sh` reported failure and printed a rollback command —
but the deployment had **succeeded**. The rows were imported, the API returned
commentaries, and the website displayed them correctly.

**Cause.** Stage 8 verification:

```bash
SAMPLE=$(remote "curl -fsS 'localhost:8000/hadiths/alkafi-2' | head -c 4000")
if [[ "$SAMPLE" != *"commentaries"* ]]; then ... exit 1; fi
```

The response was truncated at 4,000 bytes, and `alkafi-2`'s `commentaries` field
begins **after** that boundary — the hadith carries a long isnad, matn,
footnotes and translation first. The check searched truncated text for a
substring and concluded the field was absent.

**Why this is architectural, not cosmetic.** The verification does not verify
what it claims to. Three compounding defects:

1. **Substring search over truncated JSON**, sensitive to field order and
   payload size — a property of the *data*, not of deployment success.
2. **A hardcoded hadith** (`alkafi-2`) with no guarantee of any relationship to
   the source being deployed. Deploying a commentary that never touches
   `alkafi-2` would still "verify" against it.
3. **It does not check the deployed source.** Even reading the whole body, the
   presence of the string `commentaries` says nothing about whether
   `sharh-al-mazandarani` arrived.

A false failure is dangerous beyond noise: it prints a rollback command after a
successful deployment, inviting an operator to reverse work that succeeded.

**Status: not fixed.** Deliberately left in place for this documentation task —
see [§14](#14-todo--known-issues).

**Operational note until fixed.** If stage 8 reports failure, **do not roll back
reflexively.** Verify independently first:

```bash
curl -fsS 'https://usul16.com/api/hadiths/<a-hadith-you-know-is-linked>' \
  | python -m json.tool | grep -A2 source_key
```

---

## 12. Current production state

Verified at the time of writing.

| | rows shipped | linked to a hadith |
|---|---|---|
| `mirat-al-uqul` | 14,300 | 13,590 |
| `sharh-al-mazandarani` | 4,315 | 3,224 |

Rows exist without a link by design: an extracted passage that could not be
attributed with sufficient evidence is retained as internal evidence and is
never published. Only `match_status = 'matched'` reaches the reader.

**Verified live**

- `https://usul16.com/api/health` → `200 {"status":"ok"}`
- `alkafi-2`, `alkafi-6`, `alkafi-54` → 2 commentaries each
  (`mirat-al-uqul`, `sharh-al-mazandarani`)
- `alkafi-3761` → 1 (`mirat-al-uqul`) — correct: outside the Usul, which
  Mazandarani does not cover
- Reader displays both disclosures; commentary bodies load on open
- Redundant backups removed

Coverage context (measured on the workstation; production is a copy of the same
index): of al-Kafi's 15,336 hadiths, **~91.5% carry at least one commentary**.
Within the Usul + Rawda (4,384 hadiths, the only part Mazandarani addresses),
**98.3% carry at least one** and **63.5% carry both**.

---

## 13. Backup policy

**Format.** `eshia_research.db.bak-YYYYMMDDTHHMMSSZ`, beside the live database
in `/home/deploy/app/eshia-research/`.

**Creation.** Automatic, at stage 5 of every `deploy-db.sh` run — including dry
runs.

**Retention: keep the newest three verified backups; delete the rest.**

**Why so few.** Each backup is a **full ~3 GB copy** — the whole corpus, not a
delta. The server has ~22 GB free. Four backups plus the live database is ~15 GB;
a handful more fills the disk. A full disk on a SQLite host is severe: the API
may fail to serve and the next deployment cannot take its safety backup.

Retention is short because these are **deployment rollback points**, not
archives. They protect the minutes-to-hours window in which a bad delta might be
discovered. Long-term durability is a different problem with a different answer:
`AGENT_HANDOFF.md` §6 requires at least one copy **off** the server, and requires
that it actually be opened and queried — a copy never restored is not a backup.

**Cleanup.** `deploy-db.sh` lists candidates beyond the newest three on success.
Removal is manual and deliberate:

```bash
ssh deploy@<host> 'cd /home/deploy/app/eshia-research && ls -1t eshia_research.db.bak-*'
# verify the newest is good, then delete specific files by name
```

Delete by explicit name. Never glob-delete backups.

---

## 14. TODO — known issues

### Fix stage 8 verification *(Bug 4)*

Replace the truncated substring search in `infra/deploy/deploy-db.sh:161`.

**Preferred fix:**

1. **Choose a hadith actually linked to the deployed source** — query the target
   for one `public_id` with a `matched` row for this `source_key`, rather than
   hardcoding `alkafi-2`.
2. **Request that hadith** from the API.
3. **Parse the JSON properly** (`python -m json.tool`, or `jq` if present) — no
   `head -c`, no substring matching.
4. **Assert the deployed `source_key` is present** in the parsed `commentaries`
   array — not merely that the word "commentaries" appears somewhere.

This converts the check from "does a string appear in the first 4 KB" into "did
the thing I just deployed actually reach the reader", which is what the stage
claims to test.

### Alembic baseline

Nine tables have no migration (`AGENT_HANDOFF.md` §6). `alembic upgrade head`
cannot reproduce production from an empty database. Baseline before authoring
new migrations.

### `deploy-usul16.sh` is copied, not linked

The server's `/home/deploy/deploy-usul16.sh` can drift from
`infra/deploy/deploy-usul16.sh`. Consider having CI invoke the repository copy
(`/home/deploy/app/infra/deploy/deploy-usul16.sh`) so there is one file — noting
that the script `git reset --hard`s the tree it lives in, which needs care.

### Code deploy has no HTTP health check

`deploy-usul16.sh` asserts `systemctl is-active` only, which a unit that starts
and then 500s satisfies. `deploy-db.sh` already polls real endpoints; the code
deploy should too (`AGENT_HANDOFF.md` §8 item 1).

---

## 15. Deployment checklists

### Code-only (backend, frontend, or reader UI)

Python, TypeScript, React, styling — anything that does not change schema or data.

```bash
git checkout main && git pull
# merge your branch, then:
git push origin main            # CI does the rest
```
Then watch the Actions run and verify:
```bash
curl -fsS https://usul16.com/api/health
curl -fsSI https://usul16.com/ | head -1
```

Reader UI changes are code-only. Note that changing `NEXT_PUBLIC_*` values needs
a **rebuild**, not a restart.

### Schema

```bash
ssh deploy@<host>
cd /home/deploy/app/eshia-research && source .venv/bin/activate
cp eshia_research.db eshia_research.db.bak-$(date -u +%Y%m%dT%H%M%SZ)   # migrations are not free to reverse
alembic current
alembic upgrade head
alembic current
sudo systemctl restart usul16-api
```

### Commentary data

**Order matters — Layer 1, then 2, then 3.**

1. Merge and deploy the code (the CLI subcommands must exist on the server).
2. Confirm the deploy finished.
3. Dry run:
   ```bash
   ./infra/deploy/deploy-db.sh <source-key> --dry-run
   ```
   Confirm the delta size is plausible and **no `public_id` failed to resolve**.
4. Real run:
   ```bash
   ./infra/deploy/deploy-db.sh <source-key>
   ```
5. Verify independently — **do not trust stage 8 alone** (Bug 4):
   ```bash
   curl -fsS 'https://usul16.com/api/hadiths/<linked-id>' | python -m json.tool | grep source_key
   ```
6. Record the run and prune backups to the newest three.

### Full database refresh (rare)

Only when the corpus itself changes — a re-extraction, new books, rebuilt chains.

1. Compact locally: `VACUUM INTO 'snapshot.db'`.
2. Verify the snapshot: `PRAGMA integrity_check` = `ok`; required tables
   present; `COUNT(*) FROM hadiths` above a sane floor.
3. `rsync -avzP` (resumable; `scp` is not) into `/home/deploy/incoming/`.
4. Verify again **on the server**, before the swap.
5. Back up the live database.
6. `mv -f` into place — same filesystem, so the rename is atomic — then
   `sudo systemctl restart usul16-api`.
7. Verify over HTTPS. Roll back and restart on failure.
8. **Re-run `deploy-db.sh` for every commentary source.** A refreshed corpus may
   renumber `hadiths.id`; commentary must be re-linked by `public_id`.

`journal_mode=delete` means one file with no `-wal`/`-shm` sidecars to ship. If
that ever changes to WAL, the sidecars must travel too.

---

## 16. Lessons learned

**Git deploys code. Alembic deploys schema. `deploy-db.sh` deploys data.**
Three paths, deliberately independent.

Bugs 2 and 3 are the argument for the separation, experienced in sequence: code
arrived without schema, schema arrived without data. Each failed loudly, at its
own boundary, with an obvious remedy — and none of them corrupted anything. A
single "deploy everything" button would have had to get all three right
simultaneously, and its failure modes would have been entangled.

The separation is safer because the three differ in every property that matters:

| | reversibility | speed | source of truth | blast radius |
|---|---|---|---|---|
| Code | trivial (redeploy previous commit) | minutes | Git | whole app, but recoverable |
| Schema | hard (needs a down-migration) | seconds | Git | structural, hard to undo |
| Data | file copy | minutes–hours | a workstation | silent corruption if wrong |

Coupling them would force the safest to move at the pace of the most dangerous,
and would make a data mistake reachable by a merge.

**Other lessons worth keeping:**

- **Identify by stable public keys across machine boundaries.** `public_id`
  instead of `hadith_id` converts a silent, plausible, catastrophic failure into
  a loud refusal. Any transfer between two copies of a corpus must do this.
- **Verify against the machine, not the most recently edited file** (Bug 1).
- **A verification that can pass or fail for reasons unrelated to the thing it
  verifies is not a verification** (Bug 4). Worse, a false failure invites an
  operator to undo work that succeeded.
- **Everything that can fail without touching production should happen first.**
  `deploy-db.sh` fingerprints, exports, uploads, migrates and validates before
  it writes — which is why its failures are non-events.
- **Simple infrastructure is a feature.** SQLite makes backup `cp` and rollback
  `cp`. That is why the rollback story fits in one line.

---

## Related documents

- [`docs/operations.md`](../operations.md) — runtime, database-change,
  backup-retention and verification procedures.
- [`DEPLOY.md`](../../DEPLOY.md) — **superseded.** The original build-out
  narrative; still useful for its reasoning about why a single VPS, but its
  paths (`/home/usul/usul16/…`, user `usul`) describe an earlier layout and
  will break things if copied. It carries a banner saying so.
- [`AGENT_HANDOFF.md`](../../AGENT_HANDOFF.md) — corpus decisions, the commentary
  matching engine, known defects (§6), the original `deploy-db.sh` design (§7),
  and deploy-script improvements (§8).
- `infra/` — systemd units, Caddyfile and deployment scripts. **The source of
  truth for production layout.**
