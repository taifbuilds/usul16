# Man La Yahduruhu al-Faqih completeness

Last verified: 2026-08-23

## Current decision

Faqih is ready for transmission-graph publication. Its Arabic boundaries remain
preserved, the chain tokenizer has been rebuilt, unresolved parser noise has been
reduced to three honest review cases, and the person-resolution safety gates pass.

This does not mean every content layer is complete. One report still lacks a safe
English boundary match, 95 reviewed local-edition units have no standalone rendered
website translation, and no attributable per-report grading source has been imported.

## Corpus and publication state

- Source rows: 5,940
- Visible reports: 5,924
- Hidden proven apparatus rows: 16 (`faqih-1574` and `faqih-5909` through
  `faqih-5923`)
- Published rendered-website English rows: 5,828
- Visible reports without published English: 96
- Topic-tagged visible reports: 5,924
- Report-level gradings: 0
- Graph publication: enabled through `POLISHED_TRANSMISSION_BOOK_IDS`

Of the 96 untranslated visible rows, 95 are already reviewed local-edition units
without standalone website routes. The remaining actionable boundary case is
`faqih-5751`. Its local Arabic and the current rendered route overlap strongly but
are not the same report boundary (24,512 versus 32,670 characters; similarity
0.924). The longer English must not be attached to the shorter local record without
an explicit split or boundary ruling.

## Chain rebuild

The 2026-08-23 rebuild parsed 4,168 isnad-bearing reports into:

- 4,399 chain routes
- 9,020 narrator nodes
- 3 `needs_review` chains (99.9% clean)

The three retained reviews are not ordinary tokenizer debris:

- `faqih-1827`: narrative-only construction
- `faqih-3401`: narrative-only / mursal construction
- `faqih-5751`: genuine long multi-route and boundary case

Direct Imam narratives, follow-up questions, letters, raised reports, shared
honorifics, co-narrators, compiler bylines, cross-report mursal pronouns, and common
editorial apparatus now have explicit tokenizer handling and regression tests.

## Person-resolution state

Evaluation over all 9,020 chain nodes:

| status | nodes | share |
|---|---:|---:|
| resolved | 5,921 | 65.6% |
| ambiguous | 2,415 | 26.8% |
| unresolved | 673 | 7.5% |
| missing | 9 | 0.1% |
| latent | 2 | 0.0% |

Safety and evidence gates:

- Bare-form leaks: 0
- Reliable generation violations: 0
- Raw generation warnings: 4
- Mu'jam edge-corroboration floor: 77.5%

The raw warnings are research leads, not reliable-gate failures. Do not convert
ambiguous candidates into resolved people merely to raise the percentage.

## Mashyakha proposal layer

Faqih's abbreviated openings are matched against an independently preserved
Mashyakha witness. Proposals do not rewrite the printed isnad or create graph edges.

Source side:

- 387 source paths
- 378 parsed
- 5 subject-scoped entries
- 4 held for review
- 383 target forms

Report side:

- 2,799 mursal openings
- 3,470 proposal rows
- 1,868 single-witness proposals
- 1,602 ranked candidates requiring review
- 2,426 openings with any witness
- 373 openings with no witness

Match evidence:

| method | openings |
|---|---:|
| exact first narrator | 1,455 |
| canonical first narrator | 94 |
| unique name extension | 301 |
| ism/nisba elision | 24 |
| partial-name candidate | 552 |

There are 1,874 single-candidate matches but only 1,868 proposals because six
openings point to narrators with multiple Mashyakha witnesses. Those remain review
items. `Ibn X` forms, subject-scoped entries, and multiple witnesses continue to
fail closed.

## Rendered-website refresh

The live inventory refreshed on 2026-08-23 contains:

- 660 rendered chapter pages
- 5,928 content routes

The website migrated from global report-number routes to chapter-local report
numbers. The prior reviewed manifest is therefore intentionally rejected against
the new inventory hash. A fresh unreviewed audit found 5,911 local and 5,920 remote
records by exact/indexed Arabic evidence, with 13 local and 8 remote records still
outside that automatic accounting. It is diagnostic only and must not replace the
reviewed reconciliation until its new route identities are reviewed.

Twenty of the former 21 English blockers had unique, exact Arabic matches in the
new inventory and were imported with per-row source hashes and provenance. This
raised the published count from 5,808 to 5,828. `faqih-5751` was deliberately held
back.

## What is actually left

1. Make an editorial split/boundary decision for `faqih-5751`, then import only the
   English belonging to the accepted local unit.
2. Obtain an attributable per-report grading source; the present count is zero.
3. Review the new route-migration audit before replacing the old reconciliation
   manifest.
4. Work through the 1,602 Mashyakha candidate rows when stronger report-context
   evidence exists; do not guess the 373 no-witness openings.
5. Improve the 2,415 ambiguous person mentions through compiler, teacher/student,
   and Mashyakha context rather than looser name matching.

## Verification

The completed 2026-08-23 run passed:

- 569 backend tests
- Next.js production build and TypeScript validation
- SQLite `PRAGMA quick_check` (`ok`)
- zero dangling mention-resolution nodes
- zero orphaned chain nodes

Pre-change backups remain at
`eshia_research.before-faqih-chain-completion.20260823.db` and
`eshia_research.before-tusi-resolution.20260823.db`.
