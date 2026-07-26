# Man La Yahduruhu al-Faqih website reconciliation

Last run: 2026-07-24

## Current decision

The Arabic report corpus is **ready to begin rijal work**, but the public
English release is **not yet production-ready**. Report identities, Arabic
boundaries, local-only records, website continuations, duplicate occurrences,
and active isnad preservation now pass the fail-closed boundary gate. Twenty-one
records still lack a complete publishable website translation.

This distinction is deliberate: translation gaps do not prevent chain
tokenization and narrator research, but they continue to block a public-release
claim. The first rijal queue is the 804 chain-tokenizer results marked for
review, not another hadith-count reconciliation.

## Website inventory

- Thaqalayn website books: `34`, `35`, `36`, and `37`
- Rendered chapter pages: 659
- Rendered content routes: 5,927
- Website rows with no English: 23, including three field-placement anomalies
- Website display anomalies retained in the inventory: 87

The website includes compiler rulings, chapter introductions, supplications,
and guide subdivisions as hadith routes. Ninety-five such routes were reviewed
as non-independent units; they are evidence, not extra narrations.

## Final reconciliation

- Local visible reports: 5,924
- Unique visible public IDs: 5,924
- Arabic-confirmed local reports: 5,829
- Arabic-confirmed website routes: 5,832
- Confirmed relation edges: 5,832
- Reviewed local-edition reports without standalone website routes: 95
- Reviewed website non-independent units: 95
- Missing numbered website reports: 0
- Unclassified local units: 0
- Unclassified website units: 0
- Inventory reconciliation ready: yes
- Arabic boundaries ready for rijal: yes
- Production release ready: no

The opening failures are repaired: reports 9 and 10 are separate records,
compiler material no longer leaks into the displayed Arabic, and incomplete
local boundaries use the rendered website report. The source extraction is
retained in `full_text_raw` as provenance.

The combined source row at report 2119 was split into its numbered report and
its second unnumbered transmitted report, which now has stable ID
`faqih-web-35-3-1-12`. Repeated wording at reports 2296, 2189, 2153, 3402,
and 5765 remains separate because each occurrence has its own source location.
Manual relations and exclusions are bound to local and website Arabic hashes;
the local-only set is additionally locked to its Arabic content evidence.

## Publication gate

- Boundary-blocking records: 0
- Mapped records below 90% website-Arabic coverage: 0
- Non-one-to-one record boundaries: 0
- Unreviewed local-only records: 0
- Approved splits with a detectable source isnad omitted: 0
- Website reports without usable English: 20
- Records without a publishable website translation: 21

The review restored 293 deterministic active isnads that an earlier website
repair had placed inside the matn, manually corrected eleven compiler/heading
overruns, and rebuilt the Faqih chain index. The resulting 3,277 isnad-bearing
rows produce 3,809 chain routes and 8,560 narrator nodes; 804 chains are marked
for parser review and uncertainty handling during rijal work.

## Publication state

- Stored published rendered-website English rows: 5,808
- Website structure rows: 5,904
- Topic assignments: 28,622 across all 5,924 visible reports
- Generated topics: 711, including 67 semantic search topics

English is published only where the website supplies English and the report
relation is safe for publication. Missing website English, partial
continuations, and combined-edition boundaries remain visibly untranslated;
the importer does not invent or misattach text to make the percentage larger.

## Excluded apparatus

Sixteen source rows remain preserved but hidden as proven non-hadith
apparatus: `faqih-1574` and `faqih-5909` through `faqih-5923`. Their status is
`rejected_non_hadith_fragment`; source Arabic and provenance were not deleted.

## Rerun

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m eshia_research.cli audit-thaqalayn-website `
  --corpus faqih `
  --inventory-path scratch_audit\faqih_thaqalayn_website_inventory_20260723.json `
  --audit-path scratch_audit\faqih_thaqalayn_website_audit_20260723.json `
  --markdown-path scratch_audit\faqih_thaqalayn_website_audit_20260723.md `
  --cache-dir scratch_audit\faqih_cache `
  --review-manifest-path data\reconciliation\faqih_thaqalayn_website_20260723.json `
  --reuse-inventory
```

The numbered-gap, structure, English, and topic imports remain separate and
dry-run capable. Take a full database backup before applying any future
reconciliation change.
