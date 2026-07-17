# Al-Kafi flagged-chain completion audit — 2026-07-12

## Scope

Completed the source and parser audit for all 1,060 Al-Kafi chains that were
previously marked `needs_review`, spanning 1,030 hadiths. The live database was
not edited until the complete transaction and downstream resolver rebuild had
passed on a disposable copy of the verified backup.

Backup used for both the disposable validation and the live rollback point:

`eshia_research.before-alkafi-flagged-chain-repair.20260712-004051.db`

Pre-apply SHA-256 for both live and backup:

`11C103E1B8E312B7D95C2FBADD05D39D89753233B32729E58D7B507BCE8969BD`

## Repairs

- Corrected 106 source-verified isnad/matn boundaries.
- Restored the source report number and two independent routes for
  `alkafi-4680`, removing the false shared prefix.
- Retokenized every one of the 1,030 affected hadiths under the corrected
  period/parallel-route detector.
- Raised the safe co-narrator expansion ceiling to 32; the observed Al-Kafi
  maximum is 24. No `co_narrator_cap` warning remains in Al-Kafi.
- Kept genuine `جميعاً` convergences raw and reversible, recording them as
  `reviewed_complex` rather than inventing uncertain topology.
- Retained 37 explicitly source-reviewed abbreviated, nested-report, and
  alternative-route exceptions with their warning flags and review notes
  visible as provenance.

## Evidence handling

Chain and node IDs were preserved whenever the narrator token remained the
same. When a token only lost leaked matn, derived machine rows were refreshed
and identity-bearing human evidence was retained only when it still applied.

- Identity-bearing changed nodes preserved: 1
- External reviews migrated from duplicate false routes: 9
- Admin decisions migrated: 1
- Duplicate admin decisions safely collapsed: 8
- Stale parser-artifact external reviews retired: 46
- Stale parser-artifact admin decisions retired: 46
- Remaining external reviews: 9,994
- Remaining promoted admin decisions: 9,967

Every retired external case ID is recorded in its hadith split-review note.
The 9,994 external-review `decision_id` audit pointers were relinked to their
current promoted admin decisions. Final foreign-key errors and evidence
orphans are both zero.

## Final corpus state

- Stored Al-Kafi rows: 15,361
- Rejected audit rows: 26
- Visible genuine printed units: 15,335
- Corrected-parser draft: 15,335
- Source page mismatches: 0
- Chains: 17,299
- Chain nodes: 88,380
- Chain status: 16,122 pending/clean, 248 approved, 892 reviewed-complex,
  37 reviewed-exception, 0 needs-review
- Node-count mismatches: 0
- Duplicate chain numbers: 0
- Duplicate split-review rows: 0

Remaining structural warning flags occur only on reviewed exception/complex
rows. `compressed_isnad` remains a non-blocking diagnostic on 43 clean or
approved rows. No Al-Kafi `co_narrator_cap` or `citation_noise` flag remains.

## Resolution quality

The full Mu'jam, person, tabaqat, source-prior, one-round context, validated
resolution restoration, and machine-review pipeline was rerun.

- Resolved: 63,847 / 88,380 nodes (72.2%)
- Ambiguous: 13,653 (15.4%)
- Unresolved: 10,464 (11.8%)
- Mu'jam edge corroboration floor: 61.9%
- Reliable anchor-derived generation violations: 0 / 185
- Bare-form identity leaks: 0
- Machine review: 56,441 `approve_current`; 31,939
  `needs_external_review`

The validated pre-repair resolution state was restored only for shared node
IDs whose normalized token was byte-identical. Fresh results were retained for
101 changed shared nodes and 692 new nodes.

## Verification and live smoke

- Full backend suite: 322 passed, 1 dependency deprecation warning
- `PRAGMA quick_check`: `ok`
- `PRAGMA foreign_key_check`: 0 rows
- Derived orphan checks: 0 for external reviews, decisions,
  `mention_resolutions`, and `chain_node_candidates`
- Backend `http://127.0.0.1:8000/health`: `ok`
- Frontend `http://127.0.0.1:3000`: HTTP 200
- Live split stats: 15,361 total; 1,284 approved; 26 rejected;
  0 needs-review; 0 suspicious-unreviewed
- Live `alkafi-4680` chain endpoint: 2 chains, 10 nodes

