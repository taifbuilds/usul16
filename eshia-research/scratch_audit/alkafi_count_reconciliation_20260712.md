# Al-Kafi count reconciliation — 2026-07-12

## Result

- Stored rows: **15,361**
- Audited non-hadith/editorial rows retained for provenance but hidden: **26**
- Visible, source-aligned printed report units: **15,335**
- Corrected-parser draft: **15,335**
- Page-level count mismatches: **0**
- Visible volume counts: **1,442 / 2,344 / 2,182 / 2,192 / 2,201 / 2,666 / 1,711 / 597**

The database total is deliberately not presented as the one universal historical count. The Dar al-Kutub al-Islamiyya edition introduction reports 15,176 numbered *akhbar*, while other totals (including 16,199) use different rules for repeated routes, variants, or report units. The project's operational count is now explicitly: **one visible row per printed numbered report unit in the crawled edition**, with rejected parser artefacts retained only as an audit trail.

Sources consulted for the count-convention distinction:

- <https://ablibrary.net/book_content/2045/28>
- <https://en.al-shia.org/the-book-of-al-kafi-by-shaykh-kulayni/>

## Parser defects corrected

- Recovered six numbered reports swallowed into the preceding row: new stable IDs `alkafi-192a`, `alkafi-1597a`, `alkafi-3608a`, `alkafi-4835a`, `alkafi-4961a`, and `alkafi-7830a`.
- Rejected three additional numbered editorial notes (`alkafi-580`, `alkafi-2461`, `alkafi-14966`) and restored their genuine following-page continuation to the preceding report.
- Corrected six outer page/verse-number artefacts that obscured the real printed report number (`alkafi-1391`, `alkafi-6111`, `alkafi-8413`, `alkafi-11513`, `alkafi-13381`, `alkafi-14868`).
- Prevented citation page `414` before “في رواية أخرى” from becoming a report.
- Preserved multi-line bottom footnotes without breaking cross-page report continuation.
- Recognized standalone `حديث قوم صالح ع` and ZWNJ-bearing bab labels as headings.
- Added a vocalized `فِي` isnad/matn boundary; this exposed and repaired the previously fused chains in `alkafi-7830`/`alkafi-7830a`.

Four source-edition numbering anomalies remain intentionally unchanged rather than silently “corrected”: volume 1 page 368 (`1,2,3,1,5`), volume 1 page 426 (`71,73,73`), volume 3 page 147 (`2,2,4`), and volume 4 pages 73–74 (duplicate `4`). The stored `printed_number` continues to reflect the source.

## Database and derived-data safeguards

- Backup: `eshia_research.before-alkafi-count-reconciliation.20260711-175031.db`
- Backup and source SHA-256 at copy time: `96767B9B6BC0BD77BBEB0F5A82C0D277B79138B19245A9061A05C5833B21E408`
- Both snapshot and source passed `PRAGMA quick_check`; final database also passed.
- Every pre-existing hadith public ID and genuine chain-node ID was preserved where the underlying narrator token remained valid.
- Ten external reviews and 23 decisions attached solely to the three false commentary rows were removed as invalid evidence. The remaining admin decisions total 10,021 and external review rows total 10,040.
- A full person-resolution rebuild regressed independent Mu'jam corroboration to 58.8%, so it was rejected. Validated resolution rows were restored for unchanged node IDs, while fresh rows were retained for 22 new node IDs.
- Final person resolution: 63,292/87,752 resolved (72.1%), reliable generation violations 0/185, Mu'jam corroboration floor 61.7%.

## Verification

- Split audit: 1,174 approved, 26 rejected, 0 needs-review, `suspicious_unreviewed=0`.
- Chains/nodes: 17,184 / 87,752.
- Orphan checks: zero for chains, nodes, candidates, mention resolutions, decisions, and external reviews.
- Internal sequences: unique and contiguous `1..15,361`; public IDs unique.
- Backend suite: **320 passed**, one upstream deprecation warning.
