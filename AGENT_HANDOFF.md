# Agent Handoff

Shared working note for Codex and Claude. **Read this before making project changes**, then
update it when you change the plan, database, scripts, or UI behaviour.

This file is a *durable reference*, not a diary. The blow-by-blow history of every past
operation (2026-07-06 → 2026-07-27) lives in this file's **git history** — use
`git log -p AGENT_HANDOFF.md` if you need to reconstruct why something was done.

---

## 1. Production (LIVE)

**usul16.com** — Hetzner VPS (Ubuntu 24.04, 2 vCPU, 3.7 GB RAM, 2 GB swap, ~22 GB free).
Caddy → Next.js `:3000` + FastAPI `:8000`, both under systemd. SQLite on local disk.

Infrastructure is version-controlled in **`infra/`** (`deploy/deploy-usul16.sh`,
`systemd/usul16-{api,web}.service`, `caddy/Caddyfile`) — production is reproducible from Git.

### Code changes → automatic
```bash
git pull origin main   # develop from any machine
git add . && git commit -m "..." && git push origin main
```
Push to `main` → `.github/workflows/deploy.yml` → SSH to VPS → `/home/deploy/deploy-usul16.sh`
(`git reset --hard origin/main`, `pip install -e .`, `npm ci`, `npm run build`, restart both
services, check they are active). Deploys **queue** (`cancel-in-progress: false`).

The server's deploy key is **read-only** — it can `fetch`/`pull`, never `push`.
**Never edit files on the server.** All changes go through Git.

### Database changes → manual, separate
**The DB does not travel through Git** (`*.db` is gitignored; the deploy script only touches
code). None of the research work below reaches production by pushing to `main`.
Data ships by its own path: upload a verified snapshot, verify, swap, restart, rollback on
failure — use `infra/deploy/deploy-db.sh` (§7); it ships a public_id-keyed delta of the
commentary rows and never replaces the live database.

### Server-specific, never commit
`eshia-research/.env` · `eshia-research/eshia_research.db` · `eshia-research/.venv` ·
`web/.env.local`. These persist across deploys.

### Deployment philosophy (deliberate)
Usul16 is a content platform, not banking. Deployment is kept **simple on purpose**.
Atomic release directories, artifact publishing, R2 versioning and Postgres were all
considered and **intentionally postponed**. Do not propose enterprise infrastructure
without a concrete, present-tense justification.

---

## 2. Update Protocol

- Keep this file concise. Add durable status, decisions and next steps — not narration.
- Before DB edits: record intended scope + backup filename. After: record what changed,
  counts, and caveats.
- Never mark a corpus/book "clean" unless suspicious cases were audited **and** chain
  indexes rebuilt afterwards.
- If you discover a bad assumption, correct it here so the next agent doesn't repeat it.

---

## 3. Goal & current state of the corpus

Build a **Shia transmission graph and reading platform**, not a text index. Al-Kafi is the
gold-standard pilot; the pipeline learned there is then applied to the other books.

| Book | `source_book_id` | State |
|---|---|---|
| **Al-Kafi** | `11005` | ✅ Gold. 15,3xx hadiths, boundaries audited, chains + rijal resolved, topics, gradings, live English, on the graph. |
| **Man la yahduruhu al-Faqih** | `11021` | 🟡 ~90%. Boundaries passed; Imams 96% resolved; 5,808/5,924 translated (98%). **Gaps:** 116 untranslated, 798 `needs_review` chains, **0 gradings**, Phase D never run, not on the graph. |
| **Tahdhib al-Ahkam** | `10083` | 🔴 Raw. Hadiths+isnads extracted, no finishing work. ~14k — bigger than Al-Kafi. |
| **Al-Istibsar** | `11002` | 🔴 Raw. Same, ~5.5k. |
| **Bihar al-Anwar** | `71860` | 🔴 Crawled, **not hadith-extracted**. |
| Mu'jam Rijal al-Hadith | `14036` | ✅ 15,593 entries — the rijal spine. |

**Faqih/Tahdhib/Istibsar use abbreviated isnads** (al-Saduq's / al-Tusi's *mashyakha* holds
the path to the first narrator). A **mashyakha-expansion engine** is the single unbuilt piece
that unlocks all three. It does not exist yet.

Main DB: `eshia-research/eshia_research.db` (~2.5 GB, 39 tables, 173 indexes,
`journal_mode=delete`). Most of it is **derived and regenerable** (chain nodes, candidates,
resolutions, topics); source text is only ~0.55 GB.

---

## 4. Rijal / Tamyiz engine (person identity)

Three distinct objects: chain-node **mention** → Mu'jam **entry** (evidence) → **person**
(historical individual). `chain_nodes.canonical_narrator_id` means "entry citation";
person identity is a separate claim in `mention_resolutions`, each with a rendered *dalil*.

Phases (all shippable independently): **A** person ontology + name grammar · **B** reference
calculus (أبيه/عنه/بهذا الإسناد, 'iddah rosters) · **C** tabaqat lattice (generation
intervals) · **D** global/context resolution + compiler & kunya priors · **E** tashif/saqt
criticism (annotate only, never edit text).

**Re-run order matters** — changing the grammar/person layer invalidates everything
downstream: `build-person-layer` → `resolve-persons` → `build-tabaqat` → `refine-tabaqat`.

**Al-Kafi measured state:** ~72% resolved, 61.7% Mu'jam corroboration, **0 reliable
generation violations**, bare-form leak 0.

**DONE definition (standing):** every node is either resolved-with-dalil, ranked-ambiguous
with candidates shown, or flagged. The ~72% plateau is the *honest* answer —
**do not chase 100%.**

---

## 5. Standing cautions (hard-won — do not relearn these)

- **Uncertainty is displayed, never hidden.** Ranked candidates with reasons; never force a winner.
- Don't resolve ambiguous names by string match alone; never invent a narrator to fill a gap.
- Don't use page breaks as hadith boundaries; don't treat every `قال`/`في`/`أن` as a safe split;
  don't use "matn contains عن/قال" as a split error (valid matns quote dialogue).
- Rejected footnote/commentary fragments must never render as hadith cards.
- After any split repair, **derived chains/resolver output are stale until rebuilt.**
- **Do not re-run `refine-collective-context` to convergence** — stop when marginal
  corroboration drops below corpus (rounds 2–3 made it worse; only round 1 was kept).
- Only **anchor-derived** generations (`imam_fixed`/`ashab_anchor`/`anchor_and_propagated`)
  are hard chronology evidence; propagated ones are advisory. Fixed-Imam layers are ground
  truth and are never demoted to `conflict`.
- Translations: never join editions by number alone (this corrupted 62 rows once). Public
  English requires positive human-source provenance **or** the clearly-labelled AI tier.
- SQLite: a crawl + an indexing job writing concurrently caused "database is locked"
  (`timeout=60` + chunked commits fixed it). Don't run heavy writers against the served DB.

---

## 6. Known defects / open risks

- **🔴 Alembic schema drift.** `alembic_version` reports head (`a6c8d2e4f190`) but **9 tables
  have no migration** — `persons`, `person_entry_links`, `person_surface_forms`,
  `person_relations`, `collective_rosters`, `mention_resolutions`, `person_generations`,
  `person_resolution_decisions`, `person_resolution_external_reviews`. They were created by
  `Base.metadata.create_all()`. **`alembic upgrade head` on an empty DB does NOT reproduce
  production.** Fix by baselining before authoring any new migration.
- Deploy verifies `systemctl is-active` only — a unit can be "active" while serving 500s.
- Local and production DBs are separate copies; confirm `sha256sum` before shipping either way.
- Backups: keep at least one copy **off** the server, and actually open/query it — a copy
  that has never been restored is not a backup.

---

## 7. `infra/deploy/deploy-db.sh` — SHIPPED (2026-07-31)

Code deploys itself when `main` is pushed; the database does not, and this is the missing
half. **It never replaces the production database** — it ships only the commentary rows that
differ.

```bash
./infra/deploy/deploy-db.sh mirat-al-uqul            # publish
./infra/deploy/deploy-db.sh sharh-al-mazandarani --dry-run
```

**Rows travel keyed by `public_id`, never `hadith_id`.** Production is a *separate copy* of
the corpus and nothing guarantees its `hadiths.id` sequence matches the local one; a row
carrying `hadith_id=19479` would silently attach a commentary to whatever hadith holds that
id there. Rehearsed against the real corpus with production's ids deliberately shifted by
4,000,000: **400 sampled links, 0 mismatches.**

**It is a delta on the wire, not a dump that is diffed on arrival.** Step 1 pulls a
fingerprint manifest back from production, so only changed rows are ever uploaded:

| | |
|---|---|
| full DB | 2.97 GB (research copy is now 6.67 GB after the Mazandarani crawl) |
| first publish of Mir'at | **11.6 MB** — 256× smaller |
| first publish of Mazandarani | 7.6 MB |
| nothing changed | **323 bytes**, and the script exits early |

Eight steps, ordered so everything that can fail without touching production happens first:

1. **Fingerprint production** (`commentary-manifest`) — small, and what makes this a delta.
2. **Export only what differs** (`export-commentary-delta --manifest`), including a list of
   `source_sequence`s that no longer exist so removals propagate.
3. **Upload** to `~/incoming`, never over the live file.
4. **`alembic upgrade head`** — `hadith_commentaries` may not exist there yet; the migration
   `e4c91f7b2d68` chains directly off production's current head `a6c8d2e4f190`.
5. **Back up** the live DB, timestamped, *before* any write.
6. **Validate then import** (`import-commentary-delta`): every `public_id` must resolve
   before a single row is written, then the whole delta applies in **one transaction**. A
   delta built against a different corpus aborts with production untouched.
7. **Restart** the API.
8. **Verify over HTTP** — `/health` *and* a real data endpoint returning a `commentaries`
   field, because `systemctl is-active` reports a unit that starts and then 500s as healthy.

Prints the exact rollback command on success and on every failure path.

The importer also creates the commentary's `books` row from the exported metadata if the
target has never seen that work, so a first deployment is self-contained; and it detaches an
incumbent row when a re-index moves a passage onto a hadith another passage held, which
`uq_hadith_commentaries_source_hadith` would otherwise reject.

Covered by `tests/test_commentary_transfer.py` (11 tests), including the id-mismatch case,
partial-failure atomicity, dry-run, deletions, and idempotence.

**Still true of a full-file swap**, if one is ever needed: `journal_mode=delete` means a
single file with no `-wal`/`-shm` sidecars to ship; copy to the same filesystem and `mv -f`
so the rename is atomic; readers keep the old inode until restart.

---

## 8. Suggested deploy-script improvements (high value, low complexity only)

The current script is already safe in one important way: `set -euo pipefail` with the build
*before* the restart means a failed build aborts and **leaves the old services running**.
Worth adding, in priority order:

1. **HTTP health check instead of `systemctl is-active`** (~6 lines): after restart, poll
   `curl -fsS localhost:8000/health` and `localhost:3000` for ~30 s. This is the single
   highest-value change — it converts "the unit started" into "the site actually works",
   and makes the GitHub Actions run go red when it doesn't.
2. **Echo the deployed SHA** at start and end (1 line) — makes debugging and rollback obvious.
3. **Print the rollback command on failure** rather than auto-rolling-back (auto-rollback
   needs a full rebuild, which can also fail; a loud red deploy + a copy-paste command is
   simpler and safer at this scale).
4. *(Optional)* `flock` on a lockfile so a manual run can't overlap a CI run.
5. *(Optional)* Skip `npm ci` when `web/package-lock.json` is unchanged — saves the slowest step.

Deliberately **not** recommended now: release directories + symlink swaps, artifact
publishing, blue/green, containerisation. They solve problems Usul16 does not have yet.

---

## 9. Open work queue

**Faqih → gold** (in priority order): gradings import (0 today — biggest visible gap) ·
116 untranslated (28 already drafted in the AI-tier style; publication AI lane is built and
tested) · 798 `needs_review` chains (part 1 of 2 reviewed and validated: 399/399 boundaries
verified against source, 397 need mashyakha, 2 clean; **part 2 generated, awaiting review** —
`scratch_audit/faqih_needs_review_part{1_RESOLVED,2}.md`) · run Phase D context ·
union lattice rebuild · flip into `POLISHED_TRANSMISSION_BOOK_IDS` to light it up on the graph.

**Then:** mashyakha-expansion engine → Tahdhib → Istibsar → Bihar.

**Product:** Mir'at al-'Uqul + Sharh al-Mazandarani commentary integration, commentary
rendering, narrator pages, search + OCR improvements, performance.

**Mir'at al-'Uqul ingestion (2026-07-28):** eShia book `71429` is fully crawled
with every source page's HTML retained: 10,914 pages across 26 volumes. Backup before
the local migration/crawl: `eshia-research/eshia_research.before-mirat-al-uqul.20260728.db`
(2,559,860,736 bytes, `quick_check=ok`). Migration `e4c91f7b2d68` is applied locally.

The `hadith_commentaries` ledger, parser and lazy public API/UI are implemented.
The reader disclosure is labelled exactly `شرح مرآة العقول`, sized as apparatus (a step
quieter than the matn, honouring the Arabic text-size control via `.reader-sharh`), and
states its own evidence basis. Only rows with `match_status='matched'` render publicly;
`needs_review`, `unmatched` and `malformed` rows remain internal evidence.

> **Mir'at is parked here (2026-07-29) at 13,561 / 15,336 = 88.4%, ≈97.5% of what the
> source actually contains.** See "Coverage was a parser bug" below for the full account.
> Remaining: 353 duplicate_candidate, 194 section_number_only, 124 text_only, 58 unmatched,
> 10 malformed. Next effort goes to **Sharh al-Mazandarani** instead, because the residual
> Mir'at gap is mostly reports al-Majlisi never commented on — a second sharh reaches them,
> more parser work does not.

Historical v3 index (superseded): 12,302 commentary blocks; 5,240 copied report anchors; 548 verified
public links; 5,235 review-only candidates; 6,509 unlinked; 10 malformed. Focused
`tests/test_mirat_al_uqul.py`: 6 passed (parser, API visibility, duplicate protection,
heading recovery and number-shift realignment). This is **not production-deployed**:
the code is uncommitted/unpushed and the production DB has not been shipped.

For the local reader only, the 12,302 indexed rows were copied from the main research DB
into `eshia-research/eshia_research.local-server.db` after confirming stable book/hadith
IDs. FastAPI is running on `127.0.0.1:8000` against that clone; use the stable Next server
at `http://127.0.0.1:3001` (`:3000` is a frozen dev server). Confirmed examples:
`/hadith/alkafi-6`, `/hadith/alkafi-17`, `/hadith/alkafi-24`, `/hadith/alkafi-28`.

**CORS, not missing data (2026-07-28).** The reader showed `تعذر تحميل الشرح.` for every
hadith while the API returned the passage correctly. Cause: `api_allowed_origins` listed
only port **3000**, but the stable reader is served on **3001**, so the browser dropped the
client-side response. Any panel that fetches from the browser (commentary *and* the
clickable narrator chain) breaks the same way on a non-allowlisted port — server-rendered
text keeps working, which is what makes it look like a data bug. The default in
`config.py` / `.env.example` now allows 3000 **and** 3001. Production is unaffected: it
sets `API_ALLOWED_ORIGINS` explicitly to the HTTPS origin in its systemd unit.

The reader disclosure was also rescaled: it was `text-lg`/`sm:text-xl` inside a 2 px gold
border with a tinted panel, which read nearly as loud as the matn (`text-2xl`). It is now
`text-base`/`sm:text-lg` in a 1 px bordered panel matching the translation disclosure —
commentary is apparatus and must stay a step quieter than the hadith. The label is still
exactly `شرح مرآة العقول`, the printed lead-in (`الحديث السادس`) is picked out in gold,
and there is now an explicit empty state instead of a silently blank panel.

**Coverage was a parser bug, not a threshold problem (2026-07-29, matcher `v4`).**
The 548-link plateau was never about strictness. Four defects in the *extractor* were
starving the matcher of usable evidence; all four are fixed and covered by tests:

1. **Reports were keyed by chapter title alone.** Titles are not unique across 26 volumes —
   «باب نادر» recurs dozens of times — so every recurrence concatenated into one blob.
   One "report" reached **67,601 chars and was shared by 284 passages**. Reports are now
   keyed by *which run* of a title they belong to (`report_key(title, occurrence, number)`).
2. **Most chapter headings were never detected.** eShia typesets a title across several
   centred elements — `<h2>باب</h2>` then `<h2>الجبر والقدر…</h2>` — and neither fragment
   is a chapter title on its own. Volume 2 detected 26 of 89 headings. A *run* of
   consecutive heading elements is now joined into one title before testing.
3. **Later volumes bracket each title line** — `(باب)` `(فضل البنات)`. Volume 21 accepted
   26 of 296. Each fragment is now unwrapped before joining.
4. **A repeated report number inside one run glued two reports together.** That now opens
   a new chapter run (an unmarked chapter change) instead of concatenating.

**The scorer was also measuring typesetting, not identity.** Mir'at spells out honorifics
(«عليه‌السلام») where al-Kafi prints «ع», attaches the conjunction («وعدوه» vs «وَ عَدُوُّهُ»),
and carries the printed report number. Correct matches were scoring 0.61–0.89 purely from
these artefacts. `_comparable_tokens` now strips all three **from both sides**, and a quote
whose opening reproduces the hadith's opening verbatim with ≥97% word coverage counts as
identification however early al-Majlisi stopped copying (`_incipit_aligned`).
**Public thresholds were not relaxed** — 0.94 / 0.985 and the runner-up gap are unchanged.

**Measured result of the first v4 run:** matched **548 → 4,181** (27.3% of al-Kafi's 15,336),
unmatched 6,509 → 1,155, distinct reports 5,240 → 10,269, extracted 12,302 (unchanged —
parser stability). Precision audit over **all 4,181** published links: 96.9% reproduce the
hadith's opening word-for-word with ≥90% coverage, 1.7% incipit-verbatim at lower coverage,
0.6% coverage-only, **0.8% (35 rows) worth human eyes**. Fixes 3 and 4 landed after that run.

**Re-runs are expensive** (~45 min; page parsing dominates). `_hadith_token_cache` removed
the quadratic re-tokenisation — clear it at the start of each run. The indexer commits once
at the end, so a killed run rolls back cleanly (verified: `quick_check=ok` after one).

### The commentary system (2026-07-29)

Built to take one commentary to full coverage and to accept the next one as a
**descriptor plus a crawl, not a second pipeline**.

- **`commentary/sources.py`** — `CommentarySource` descriptors. `MIRAT_AL_UQUL` is live;
  `SHARH_AL_MAZANDARANI` is filled in except for its eShia book id (not yet crawled) and
  carries `covers_whole_target=False`, so a commentary on the Usul alone is never scored
  as having failed on volumes it never addressed.
- **`commentary/alignment.py`** — generic, source-agnostic chapter-sequence alignment.
  Knows nothing about Mir'at, al-Kafi or eShia markup; it aligns two ordered sequences of
  numbered chapter runs given trusted anchor pairs.
- **`commentary/mirat_al_uqul.py`** — the Mir'at extractor plus the two-pass indexer:
  text matching first, then alignment over what text could not reach.

**Why alignment exists.** Al-Majlisi frequently writes «الحديث الرابع» and comments
*without reprinting the report*. Those passages contain no quotable text, so no scoring
will ever place them. What they carry is position, and both works walk the same chapters
in the same order, numbering from one inside each.

**The rule it rests on is measured, not assumed.** Inside an aligned chapter, passage *k*
explains hadith *k*. That was validated against the 7,779 links placed by text alone —
position never consulted — and it holds for **7,705 of 7,779 (99.05%)**.

**The 74 exceptions are the reason it is not naive.** Whole chapters are offset:
al-Kafi's «باب البداء» runs one behind the sharh throughout, so a zero-offset assumption
would land every positional placement on the neighbouring report. Each chapter's
`ordinal_delta` is therefore *learned from its own text-verified anchors*; a chapter whose
anchors disagree (<80% agreement) is left unfilled rather than guessed.

Other guards: anchors must form a monotonic sequence (chapter order is shared, so a
backwards anchor is a mis-anchor, dropped by weighted LIS); interpolated chapters need
title agreement ≥0.6; a hadith is never double-claimed; and where the report *was*
reprinted, an outright text contradiction (<0.35) outranks position and forces review.

**Positional links are labelled, never disguised.** `match_method='chapter_sequence_aligned'`
surfaces as `evidence: "position"` on the API, and the reader states plainly that the
commentator did not reprint the text and the link rests on its place in the chapter.

**The footnote area lags the main text by up to a page** — eShia prints al-Kafi at the head
of the page and the sharh at its foot, so the commentary below a new chapter heading is
still finishing the *previous* chapter. A run therefore reads «التاسع، الأول، الثاني …».
Left alone, that trailing passage is filed under the new chapter, takes the new chapter's
report for its ordinal, and beats the real passage to the claim on iteration order — so
**729 hadiths were showing the previous chapter's sharh** while the correct passage was
discarded as a duplicate. This was a precision bug found only by chasing the coverage
deficit; `_reassign_carryover_passages` hands those passages back to the chapter that
ended. A run whose numbering simply starts late is *not* treated as carry-over (tested).

**Coverage progression** (al-Kafi = 15,336 hadiths): 548 → 4,181 (report keying + heading
runs) → 7,779 (bracketed headings, repeat-number split) → 10,649 (alignment layer) →
12,499 (mid-span header detection) → **13,561 of which 3,532 positional** (carry-over fix).

**Final measured state:** 13,561 / 15,336 = **88.4%** of al-Kafi; 13,561 / 14,300 = 94.8% of
extracted passages placed. Remaining unplaced: 353 duplicate_candidate, 194
section_number_only, 124 text_only, 58 unmatched, 10 malformed. Ordinal rule re-validated
on 10,029 text-verified links: **99.14%** agreement.

**Do not chase 100% — the source does not contain it.** A full scan of all 10,914 pages
split the 2,715 unexplained reports by cause: **1,423 (52.4%) are never mentioned in the
sharh at all** — al-Majlisi passed over them, so no parser change can recover them — and
1,292 were extraction headroom (mostly the carry-over case, now fixed). The honest ceiling
for this source is ≈13,913 (**90.7%**), and 13,561 is **97.5% of what Mir'at actually
contains**. Closing the rest needs a *second* commentary, which is what the source system
is for.

**Extraction, not matching, was the ceiling.** Reports extract at 15,338 — against 15,336
hadiths, effectively exact — but passages stalled at 12,302. Cause: `الحديث ...` headers were
only recognised at a span start or after `.!؟`, and eShia runs the chapter title straight
into the header («…والسبيل فيهم مقيم الحديث الأول : ضعيف»), so those passages were swallowed
as continuations. Headers are now also recognised mid-span when followed by a readable
ordinal **and** a colon — the printed header form — which does not capture al-Majlisi
referring back to «الحديث الأول» in his own prose (both cases tested). Passages: 12,302 → 14,300.

**Mir'at is parked, not finished.** Deferred, in priority order if it is picked up again:
eyeball a sample of positional links; check whether the 353 remaining `duplicate_candidate`
rows are further carry-over at a page boundary I did not model; commit/push code; ship a
separately verified DB snapshot via section 7. Full re-index is ~45 min and dominated by
page parsing, so **batch parser changes before running**. **Do not lower the text
thresholds** — every gain came from making the evidence comparable or adding independent
evidence, never from lowering the bar.

**Local reader:** after an index run the rows must be copied into
`eshia_research.local-server.db` (the served clone) — the research DB is not served. Copy
only after checking that hadith/book ids still denote the same rows in both files.

---

### Sharh al-Mazandarani (current focus, 2026-07-29)

**Identified: eShia book `13033`, 12 volumes, local `books.id=1241`.** Confirmed from its
own title page, not guessed:

> «شرح الكافي الجامع **للمولى محمد صالح المازندراني** المتوفى 1081 ه‌
>  مع تعاليق الميرزا أبو الحسن الشعراني»

Do not confuse it with the neighbours in the catalogue: `12823` is Mulla Sadra's
*Sharh Usul al-Kafi*, `27312` al-Shafi, `27289` al-Kashf al-Wafi. All are commentaries on
the Usul; only `13033` is al-Mazandarani's.

**Two facts from that title page that shape the work:**

1. It covers the **Usul (and Rawda), not the whole Kafi** — hence `covers_whole_target=False`
   on the descriptor. Coverage must be reported against the covered part, or the number
   will look like failure on volumes the work never addressed.
2. The edition **interleaves al-Sha'rani's glosses** («تعاليق») with al-Mazandarani's
   commentary. Extraction must keep the two apart: attributing a Sha'rani gloss to
   al-Mazandarani is a **false attribution**, not a formatting slip. Establish how the
   markup distinguishes them *before* indexing anything.

**State:** catalogued with 2 probe pages only; the 12 volumes are **not yet crawled**.
`crawl-commentary <source-key>` is generic over the descriptor (volume range, raw-HTML
guard, checkpointed and resumable), so no bespoke crawler is needed:

```powershell
python -m eshia_research.cli crawl-commentary sharh-al-mazandarani --start-volume 1 --end-volume 1
```

**Sequence:** crawl one volume → inspect its markup for the Mazandarani/Sha'rani
distinction and the copied-report layer → only then write the extraction profile → crawl
the rest → index. The Mir'at lesson is that **extraction defects, not thresholds, cost the
coverage**, and every one of them was visible in a single volume's HTML.

#### Format (reverse-engineered from volume 2, 362 pages)

**Nothing about the Mir'at extractor applies here — do not try to reuse it.** eShia 13033
has *no* `<p>` or `span.FootNote` structure at all: the content cell holds bare text nodes
separated by `<br>`. This is *sharh mazji*, interwoven commentary, and it has three layers
in one text stream:

```
باب صفة العلم                       ← running page header (repeats the title)
باب صفة العلم وفضله وفضل العلماء    ← the real chapter title
* الأصل: 1 - محمد بن الحسن … قال …  ← al-Kafi base text, numbered within the باب
  الشرح: … (وجاهل مدع للعلم) من المفتريات …   ← al-Mazandarani, quoting lemmata in ()
  … كما في (1) …        1 - كأنه أراد بالعلماء …  ← numbered gloss = al-Sha'rani
```

The decisive find is the literal marker **`الأصل:`** — the base text *is* separated after
all, and each occurrence is followed by `N -` where **N is the hadith's number within its
باب**. That is the same ordinal al-Kafi's `printed_number` carries, so **the existing
`alignment.py` applies unchanged** (chapter runs, learned `ordinal_delta`, monotonic
anchors). Only the extractor is new.

Volume-2 measurements: 2,550 parenthesised lemmata (median 16 chars — lemma-by-lemma, so a
lemma alone is far too short to match a hadith); 73 isnad-shaped lemmata; 23 chapter-heading
lines; **0** lines beginning with a bare number (so Mir'at's `_NUMBERED_REPORT_RE` finds
nothing here).

**The Sha'rani hazard is real, confirmed, and has NO markup delimiter.** Glosses are not
labelled «الشعراني» in the body — that word appears twice in 120 pages. They are numbered
footnotes: `(1)` inside the commentary, resolved by `1 - …` appended at the foot of the page.
Verified on v2 p26: the body breaks off mid-sentence («… كان نورا على نور كما في») and the
gloss follows immediately — **no `<br>`, no `<hr>`, no element boundary**; splitting on `<br>`
returns body+gloss as one 2,068-char blob, and the only `hr` tags on the page are outside the
content cell. So unlike Mir'at's `span.FootNote`, there is **nothing in the markup to trust**.

The only available signal is the convention: a `N -` run at the end of a page whose numbers
match the `(N)` references appearing earlier in that page. That is a heuristic over prose,
not a structural guarantee, so the posture must be:

* detect the gloss run by resolving `(N)` references to `N -` markers **in ascending order,
  searching only after the last reference** (searching from the start finds digit-dash pairs
  inside the body);
* store the gloss text **separately**, never concatenated into `commentary_raw`;
* when references exist but do not resolve in order, treat the unit as **uncertain and
  withhold it from publication** rather than risk printing al-Sha'rani under
  al-Mazandarani's name. A false attribution of religious scholarship is worse than a gap.

**Crawl:** `STORE_RAW_HTML_R2=true` in `.env` (deliberate, for the big library crawl) sends
HTML to R2 instead of the `html_raw` column, and the commentary parser needs the column.
Override per run — do not edit `.env`:
`$env:STORE_RAW_HTML='true'; $env:STORE_RAW_HTML_R2='false'`.

#### Built so far

**Crawl DONE: all 12 volumes, 4,831 pages** (~16 min; vols 336/361/303/297/357/438/425/416/
437/370/489/590). `crawl-commentary sharh-al-mazandarani` is checkpointed and re-runnable.

**`commentary/mazandarani.py`** reads the edition into `(report, commentary, gloss)` units,
with `tests/test_mazandarani.py` (10 tests). Measured on the real volume 2: **178 units, 168
publishable, 22 chapter runs** (matching its ~23 printed headings), commentary median 1,983
chars, report median 247, and **156 KB of al-Sha'rani gloss separated out** rather than
attributed to al-Mazandarani. Ordinals come out as clean per-run sequences (1,2,3…), which
is exactly what `alignment.py` consumes.

**The chapter-detection trap, already paid for once:** «باب» and «كتاب» are ordinary words
in al-Mazandarani's prose («كتاب والسنة، إذ بهما يتوصل …»). Scanning the text for them
invented chapters out of sentences and fragmented volume 2 into **111** runs. A heading is
therefore trusted **only at the head of a page**, which is where this edition prints it —
that alone took 111 → 22. `opening_chapter_title` also drops the truncated running header in
favour of the full title and caps a title at 200 chars.

Known rough edges in the extractor, all tolerable for alignment (which leans on anchors plus
title similarity, not exact titles): one run title bleeds into commentary where a page opens
with a heading and no `الأصل:` marker; occasional merged runs where a heading was missed
(ordinals read `1..6,1..5`); a few units with no readable ordinal.

#### Indexed (first run, 2026-07-30)

`index-sharh-al-mazandarani`: pages 4,831 · units 3,059 · publishable 2,529 ·
**matched 1,999** (1,096 of them by chapter position) · needs_review 996 · unmatched 64 ·
**withheld for attribution 63**. Coverage of the part it addresses: **1,999/4,384 = 45.6%**.

Scope is enforced in code: `MAZANDARANI_TARGET_VOLUMES = (1, 2, 8)` — al-Kafi's Usul is
volumes 1–2 (3,787 hadiths) and the Rawda is volume 8 (597), measured, not assumed. Reporting
against all 15,336 would read as failure on five volumes the work never addresses.

**The shared matching layer now lives in `commentary/matching.py`** (`comparable_tokens`,
`score_report_text`, `best_text_candidate`, the hadith token cache). Both sources import it;
`mirat_al_uqul` keeps private aliases so its call sites and tests are untouched. Thresholds
stay with each caller, which is where they have to be justified.

### Combined coverage — the multi-source thesis, confirmed

| | hadiths | of |
|---|---|---|
| Mir'at al-'Uqul alone | 13,561 | 88.4% of 15,336 |
| **at least one sharh** | **13,998** | **91.3% of 15,336** |
| both sharhs on the same hadith | 1,562 | — |
| Mazandarani adds where Mir'at had none | 437 | — |
| **Usul + Rawda (where both works overlap)** | **4,285 / 4,384** | **97.7%** |

That 97.7% is the point: where two commentaries cover the same ground, coverage is close to
complete. The residual gap is concentrated in the **Furu' (volumes 3–7, 10,952 hadiths)**,
which only Mir'at addresses — so the way to lift the corpus number further is a *third*
commentary on the Furu', not more parser work on the two we have.

#### Multi-source reader — DONE

`_commentary_summary` now reads labels from `COMMENTARY_SOURCES`, so adding a commentary is
a descriptor entry rather than another branch. `CommentaryDisclosure` (renamed from
`MiratAlUqulDisclosure`) renders **every** commentary the API returns, in the order it
returns them, and the label comes from `disclosure_label_ar` on the descriptor —
«شرح مرآة العقول» and «شرح أصول الكافي» — because a full printed title is too long for a
collapsed row. Verified end-to-end on `alkafi-2`, which carries both.

**Watch this when syncing:** the local-server copy script was per-source-key and silently
left Mazandarani out of the reader. Copy **all** of `hadith_commentaries`, not one key.

#### Ordinal fill

Volumes 7, 10 and 12 print «الأصل: - علي بن إبراهيم …» — the dash but **no number** — for
~263 reports. `fill_missing_ordinals` interpolates a gap only when the numbered neighbours
bracket it exactly (between 4 and 6 the missing one is 5); consecutive gaps are left
unnumbered rather than guessed. Honest result: **+12 links (1,999 → 2,011)**, because most
gaps are consecutive and therefore unresolvable this way. Low yield, correctly refused.

#### All 12 volumes now extract — three marker bugs, not three missing volumes

An earlier note here claimed volumes 8 and 9 were unusable. **That was wrong**, and the
error was mine in both cases: the edition varies its punctuation between volumes and the
markers were written too strictly.

| vol | pages | units before | units now |
|---|---|---|---|
| **8** | 417 | **0** | **437** |
| **9** | 438 | **4** | **595** |
| 1–7, 10–12 | 3,976 | 3,055 | 3,283 |
| **total** | 4,831 | 3,059 | **4,315** |

1. **Volume 9 opens a report with a bare number, not «الأصل»** — «… 30 - محمد بن يحيى، عن
   أحمد … * الشرح: قوله …». It marks `الشرح` 608 times and `الأصل` 4 times, which is why
   keying on `الأصل` found 4 units in 438 pages. `unit_starts` is now a three-marker state
   machine: a unit opens at `الأصل`, **or** at a numbered report encountered while already
   inside a commentary. The commentary-state requirement matters — a numbered run inside a
   *report* belongs to that report — and an isnad hint («عن»/«قال» within 90 chars) guards it.
2. **Volume 8 omits the colon entirely** — «* الأصل 1 - علي بن إبراهيم …», «* الشرح قوله …».
   The markers now accept asterisk **or** colon. Not both optional: «الأصل» and «الشرح» are
   ordinary words in his prose («قدم الايمان لأنه الأصل والأهم»), and a bare occurrence must
   never open a unit. Both cases are tested.
   *The earlier claim that volume 8 was OCR-corrupted junk was overstated* — it does carry
   some OCR noise, but it is fully structured and now yields 437 units, 361 publishable.
3. **Chapter titles swallowed commentary.** Where a chapter opens with no `الأصل` on the same
   page, the sharh runs straight on from the heading — «كتاب فرض العلم (ووجوب طلبه) العطف
   للتفسير …». The title now ends at the first parenthesised lemma (cap 120 chars). This is
   worth more than it looks: a title carrying commentary destroys the title agreement the
   alignment layer needs, so fixing it moved **+160 links and +160 positional placements**.

Also: volumes 7/10/12 print «الأصل: - …» with the dash but no number for ~263 reports.
`fill_missing_ordinals` interpolates only where numbered neighbours bracket the gap exactly;
consecutive gaps are left unnumbered rather than guessed. Honest yield: +12 links.

#### Mazandarani progression

| step | matched | of 4,384 |
|---|---|---|
| first index | 1,999 | 45.6% |
| ordinal fill | 2,011 | 45.9% |
| volume 9 state machine | 2,327 | 53.1% |
| volume 8 colon-optional markers | 2,437 | 55.6% |
| chapter-title trimming | **2,597** | **59.2%** |

**Corpus-wide: 14,006 / 15,336 = 91.3%** with at least one sharh; **Usul+Rawda 4,293 / 4,384
= 97.9%**; **2,152** hadiths now carry both commentaries (was 1,562).

#### He comments on groups — do not read those units as missing coverage

A report with no sharh after it is **not** a parser failure. Verified on the raw page
(v7 p133–134), al-Mazandarani prints several reports in a row and then explains once:

```
* الأصل: - محمد بن يحيى …    (report, no sharh)
* الأصل: - محمد بن يحيى …    (report, no sharh)
* الأصل: - محمد، عن أحمد …   (report, no sharh)
* الأصل: - الحسين بن محمد …  (report)
* الشرح: قوله (فمن عرفه كان مؤمنا) …   ← one commentary, after four reports
```

**428 units are reports he passed over** (0 of a 335-unit sample contained «الشرح», and each
ends cleanly at its matn). They are recorded as `no_commentary_in_source`, deliberately
distinct from `withheld_attribution`, because the two mean opposite things: an attribution we
could not establish is a defect to chase; a report the commentator ignored will never yield a
link. Note these stretches also drop the report numbering («* الأصل: - » with no digit), which
is why volume 7 shows so many unreadable ordinals — also not a defect.

**So report two rates, not one:**

* **66.8% (2,597 / 3,887)** — units *carrying commentary* that were placed. This is the
  number that measures the pipeline.
* **59.2% (2,597 / 4,384)** — hadiths of the Usul+Rawda reached. This is bounded by what he
  chose to comment on and can never reach 100%.

#### Source runs must split on an ordinal restart, like the target side

Chapter alignment itself is healthy — **341 of 349 source chapters paired (98%)**, 263
anchored and 78 interpolated — so unpaired chapters were never the problem. The blocker was
that `build_source_runs` grouped by heading **only**, while `build_target_runs` had always
split on "heading changes **or** numbering restarts". Where the edition failed to mark a
heading, two chapters merged into one run reading `1..6,1..5`, and `setdefault` silently
dropped every unit whose ordinal was already taken — **664 units fell out of the runs
entirely**, leaving them with no position at all. Position is the only thing that can place
a report al-Kafi prints more than once, so those were unplaceable by construction.

Making the two sides symmetric was worth **+189 links and +189 positional placements**
(2,597 → 2,786). If a third commentary is added, give its `build_source_runs` the same rule.

#### Mazandarani progression (final for this session)

| step | matched | of units carrying commentary |
|---|---|---|
| first index | 1,999 | — |
| ordinal fill | 2,011 | — |
| volume 9 state machine | 2,327 | — |
| volume 8 colon-optional markers | 2,437 | — |
| chapter-title trimming | 2,597 | 66.8% |
| **source-run splitting** | **2,786** | **71.7%** |

**Corpus-wide: 14,004 / 15,336 = 91.3%** with at least one sharh · **Usul+Rawda 4,291 / 4,384
= 97.9%** · **2,343** hadiths carry both commentaries (was 1,562 at the start of the session).

**Next, in priority order:**

#### Two decisive fixes (2026-07-30) — superseding the numbers above

**1. The tokenizer was deleting narrator names, in *both* commentaries.**
`normalise_arabic_persian` maps Arabic yeh (ي U+064A) → Persian yeh (ی U+06CC) and kaf
(ك U+0643) → Persian kaf (ک U+06A9), but `ARABIC_WORD_RE` was `[ء-ي]`, which **ends at
U+064A**. Every normalised word was cut at its first yeh or kaf — «التوحيد» tokenised as
«التوح», and **«يحيى» and «عيسى» produced no token at all**, two of the commonest names in
an al-Kafi isnad, silently removed from every comparison. It matched anyway because the
damage was symmetric, but on badly degraded signal. Range widened to `[ء-يٮ-ۓٰ]`.
Mir'at 13,561 → **13,590**. (The diacritics theory in the old note above was **wrong** —
diacritics were always stripped correctly. This was the real cause.)

**2. Ordinal corroboration — the biggest single win.** The 0.985 text bar exists to separate
near-ties. Where a **second independent witness** agrees — the identified hadith carries the
same number inside its chapter as the unit does — that ambiguity is absent, so ≥0.90 suffices.
Same two-evidence rule Mir'at already uses for `section_number_and_text`; **not** a relaxed
threshold. New method `text_and_ordinal`. Mazandarani 2,875 → **3,225**, and positional
placements fell 1,454 → 523 as direct text evidence replaced inference.

Also: `publishable` no longer requires a printed number — an ordinal places a unit *by
position*, it is not needed to identify one *by text*. That gate had excluded 263 units that
carried both a commentary and a usable report.

**Volume 1 is NOT under-extracted** (checked): 44 markers for كتاب العقل والجهل's ~34 hadiths
is correct; pages 150/250 are continuous commentary — he simply writes at length.

| | | |
|---|---|---|
| Mazandarani placed | 3,225 / 3,887 units carrying commentary | **83.0%** |
| Usul+Rawda he reaches | 3,225 / 4,384 | 73.6% |
| **both sharhs** | **2,784 / 4,384** | **63.5%** (was 53.6%) |
| at least one sharh | 4,308 / 4,384 | 98.3% |
| corpus-wide | 14,031 / 15,336 | 91.5% |

**Next, in priority order:**

1. **662 units carrying commentary remain unplaced** — the live headroom. The ceiling for
   "both" is ~88.7%, so ~25 points are still available.
2. **Audit `text_and_ordinal` and the 523 positional links by eye.** The corroboration rule
   is new and has never been checked against the printed page. Do this before shipping.
3. Volume 9's isnad-onset splitter (438 pages). Volume 8 needs re-sourcing, not a parser.
4. Nothing is committed or deployed; production has none of this.

**Reader-layer revision (local, 2026-08-09):** English, commentary and footnotes now read as three explicit, progressively disclosed layers. Commentaries use one disclosure with a source selector rather than one near-identical panel per sharh; footnotes have a stronger dotted rule and larger reading size. The printed-page route links to the verified Thaqalayn kitab/chapter context attached to the hadiths actually on that page (possibly more than one), rather than guessing from page numbers. `_attach_reader_extras` now attaches that structure to all reader-list responses; regression coverage is in `tests/test_api_books.py`. This needs the normal code deployment before it reaches production.

**Graph (shipped):** whole confident Al-Kafi network (~2,000 narrators / 5,370 edges,
Barnes–Hut), all 15,593 narrators searchable via the directory, "show uncertain" tier,
and path-finding (`/transmission-graph/paths`). Deferred: reliability dossier, layperson
onboarding mode.

---

## 10. Useful commands

```powershell
# from eshia-research/, venv active; PYTHONIOENCODING=utf-8 for Arabic output
python -m eshia_research.cli --help

# rijal pipeline (ORDER MATTERS)
... build-person-layer
... resolve-persons          --source-book-id 11005
... build-tabaqat            --source-book-id 11005 --source-book-id 11021
... refine-tabaqat           --source-book-id 11005
... refine-imam-priors       --source-book-id 11021   # kunya priors (أبو عبد الله → al-Sadiq)
... refine-collective-context --source-book-id 11005   # round 1 ONLY

# audits / measurement (read-only)
... eval-resolution   --source-book-id 11005
... audit-generations --source-book-id 11005
... audit-hadith-splits --source-book-id 11005 --include-chain-index

# tests
pytest -q        # 413+ passing
```
Frontend: `npm run lint && npm run build` in `web/`.
Local dev: API `127.0.0.1:8000`, web `127.0.0.1:3000` (backend takes ~60–90 s to boot —
it loads the 2.5 GB DB).
