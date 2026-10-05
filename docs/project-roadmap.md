# Usul16 project roadmap

Last reconciled: 2026-10-05

## Milestone

Publish all Four Books in a responsibly evidenced transmission graph and give each
collection a clear, source-verifiable reading experience. Bihar remains outside this
milestone. Resolution percentages are measurements, not targets: an honestly ambiguous
mention is a valid final result.

## Current baseline

- Production and `origin/main` were both at `8d9b6ee` when the restart audit began.
- Al-Kafi and Faqih are enabled in the public graph. Tahdhib and Istibsar remain gated.
- The live homepage, books, search, hadith, narrator and graph pages returned HTTP 200.
  Their corresponding health, catalogue, hadith, commentary, chain, narrator and graph
  API routes also returned HTTP 200 with non-empty payloads.
- The backend suite passed: **575 tests**, with 10 known warnings and no failures.
- The Next.js 16.2.9 production build passed compilation, TypeScript validation and static
  page generation.
- The compact production snapshot
  `eshia-research/deploy-usul16-838a73c-20260824.db` is the verified local recovery
  artifact: SHA-256
  `BA7CB26E7C77CDE819B6E3ECFE057B6F71B92F37ADA6B76F31A0ED7AFAD9F587`,
  `quick_check=ok`, 90,407 hadiths, 89,536 chains, 18,637 commentary rows, Alembic
  revision `a7c3e5b91d24`. It was opened and queried in read-only mode on 2026-10-05.

## Phase 1 — Secure and reconcile

Status: **complete (2026-10-05)**

| ID | Task | Acceptance evidence |
|---|---|---|
| P1-01 | Preserve the six August rijal studies | Added under `docs/rijal-methodology/cases/`, indexed and checked for complete structure, readable UTF-8 and explicit conclusions/limitations. |
| P1-02 | Preserve the current Faqih route-migration evidence | Added the 2026-08-23 inventory and unreviewed audit. Both JSON files parse successfully; the report remains explicitly labelled unreviewed. |
| P1-03 | Separate generated local artifacts | Added narrow ignore rules for the response cache, rollback SQL, commentary manifest/delta and incidental `uv.lock`; files remain on disk and recoverable. |
| P1-04 | Reconcile durable status | Updated `AGENT_HANDOFF.md` so dated commentary checkpoints no longer contradict the 2026-08-24 production refresh. This roadmap is now the canonical task register. |
| P1-05 | Verify recovery material | Verified the recorded SHA-256, opened the compact snapshot read-only, ran SQLite `quick_check`, queried core row counts and confirmed its schema revision. |
| P1-06 | Verify code and principal user journeys | Backend tests and frontend production build passed; local checkout matched `origin/main`; live reader, search, narrator and graph smoke checks passed. |

Deliverable: a clean, committed restart baseline with preserved research, one current task
register, a queryable recovery artifact and verified local/live health.

## Phase 2 — Repair the evidence foundation

Status: **next**

| ID | Task | Acceptance criterion |
|---|---|---|
| P2-01 | Identify the exact 23 overrun Mu'jam occurrence ledgers and their correct source boundaries | Each ledger has a source citation, old/new boundary and explicit repair rationale. |
| P2-02 | Apply the boundary repairs on a disposable database copy first | A before/after manifest is produced; no unrelated source rows change. |
| P2-03 | Rebuild affected derived evidence in the documented order | Person layer, resolutions and tabaqat outputs are internally consistent with no dangling rows. |
| P2-04 | Re-run the context resolver and measure the effect | Bare-form leaks and reliable-generation violations remain zero; an immediate rerun resolves zero new cases. |
| P2-05 | Publish the repair audit | Reviewable ledger, counts, test results, database integrity result and rollback hash are recorded. |

Deliverable: corrected and reproducible Mu'jam evidence that can safely support the remaining
Four Books resolution work.

## Phase 3 — Complete Four Books transmission coverage

Status: **queued; depends on Phase 2**

| ID | Task | Acceptance criterion |
|---|---|---|
| P3-01 | Generalize the sourced Mashyakha proposal layer to Tahdhib | Literal and reconstructed chains remain separate; every proposal cites its path and scope. |
| P3-02 | Generalize the same layer to Istibsar | Same publication and provenance gates as Tahdhib. |
| P3-03 | Review the 56 suspicious al-Tusi chains | Each is corrected, accepted with explanation, or retained as review-only. |
| P3-04 | Classify the remaining retained multi-route cases | Route multiplicity remains visible and is never collapsed into a fabricated single chain. |
| P3-05 | Rebuild and evaluate person resolution | Collection reports include resolution states, corroboration, generation checks and unresolved-case counts. |
| P3-06 | Enable Tahdhib and Istibsar in the graph separately | Each book passes its own chain, identity and abbreviated-opening publication gates before its ID is added. |

Deliverable: all Four Books available in the public graph with traceable literal and
reconstructed transmission evidence.

## Phase 4 — Complete the reader's core layers

Status: **queued; source acquisition can begin early**

| ID | Task | Acceptance criterion |
|---|---|---|
| P4-01 | Decide the `faqih-5751` Arabic/English boundary | The editorial ruling and any split are explicit; English is attached only to the accepted unit. |
| P4-02 | Review the Faqih route-migration audit | The unreviewed manifest is accepted or corrected through documented human review before replacing the prior reconciliation. |
| P4-03 | Add verified Tahdhib and Istibsar section structure | Contents and citations reproduce the selected editions without inferred false headings. |
| P4-04 | Add topic coverage | Tagging method, coverage and review status are reported per collection. |
| P4-05 | Acquire and align attributable English sources | Rights, attribution, route/boundary matching and missing coverage are recorded; number-only joins are forbidden. |
| P4-06 | Acquire an attributable grading layer | Grading source and methodology remain visible; absent or contested grades stay absent/contested. |

Deliverable: a consistent Four Books reader whose content layers are either sourced and
verified or plainly marked unavailable.

## Phase 5 — Validate and release

Status: **queued; depends on Phases 2–4**

| ID | Task | Acceptance criterion |
|---|---|---|
| P5-01 | Run end-to-end reader, search, narrator and graph checks | Desktop/mobile, keyboard, reduced-motion and representative evidence journeys pass. |
| P5-02 | Validate performance and failure behaviour | Agreed page/API budgets pass and user-facing failures remain intelligible. |
| P5-03 | Close the content-rights register for released layers | Dated permission/licence evidence and required attribution exist for every public material class. |
| P5-04 | Add application-level code-deploy health checks | Deployment verifies real HTTP responses and records the deployed Git SHA. |
| P5-05 | Prepare code/data releases and rollback material | Code and database paths are independently rehearsed; hashes and rollback commands are recorded. |
| P5-06 | Deploy and verify production | Production passes the release checklist and the public methodology/coverage statements match deployed data. |

Deliverable: a verified Four Books release with transparent coverage, recovery material and
documented remaining limitations.

## Preserved and local-only artifacts

Durable research now tracked:

- six rijal methodology case studies;
- the 2026-08-23 Faqih website inventory;
- the corresponding unreviewed JSON audit and readable Markdown summary.

Generated artifacts intentionally kept local:

- `scratch_audit/faqih_cache/` (660 cached responses, about 10 MB);
- `mashyakha_tables_before_v2_20260810T180313Z.sql` (rollback dump);
- the Mazandarani pre-fix manifest and compressed delta;
- `eshia-research/uv.lock`, because the documented environment currently installs with pip.

These files were not deleted. The ignore rules can be reversed if one becomes a deliberate
published artifact.
