# Al-Kafi completeness audit

Last run: 2026-07-23

## Current decision

Do not publish the claim "we have every hadith in Al-Kafi" yet.

The Thaqalayn website inventory is complete, but the bidirectional alignment
between that edition and the local eShia edition still has unresolved report
boundaries. Different row counts are expected when one edition splits a report
that another edition keeps together; row-count equality is not the claim gate.

## Website inventory

- 2,722 rendered Al-Kafi chapter pages were inventoried directly from
  `thaqalayn.net`.
- The website sitemap contains 14,250 Al-Kafi hadith routes.
- Every sitemap route was found in the rendered chapter pages.
- 14,249 routes are rendered reports.
- One route, `/hadith/1/4/87/0`, is explicitly labelled as part of the
  previous chapter and is retained as a non-report placeholder.
- Four website display anomalies are retained in the JSON evidence: one
  combined Arabic/English paragraph and three reports with no rendered Arabic.

This independently explains the website-side count. It does not rely on the
Thaqalayn API.

## Alignment result

- Local visible report units: 15,336
- Website reports: 14,249
- Directly confirmed local units: 13,568
- Directly confirmed website reports: 13,564
- Bounded split/merge candidate blocks: 504
- Candidate coverage: 595 local units and 598 website reports
- Outside those candidate blocks: 1,173 local units and 87 website reports
- Public completeness claim ready: no

The large local-only remainder is concentrated in volume 7 and is evidence of
edition segmentation differences that still need boundary review, not proof of
extra or missing narrations.

## Claim gate

The claim becomes defensible only when every website report has a reviewed
local relation and every local report unit is classified as one of:

1. the same report,
2. a documented split or merge of website reports, or
3. a documented local-only editorial/non-report unit.

The final audit must have zero unclassified reports in both directions. A
matching total row count is neither required nor sufficient.

## Rerun

From `eshia-research` in PowerShell:

```powershell
$root = Join-Path ([System.IO.Path]::GetTempPath()) 'usul16-thaqalayn-website'
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m eshia_research.cli audit-thaqalayn-website `
  --inventory-path "$root\inventory.json" `
  --audit-path "scratch_audit\alkafi_thaqalayn_website_audit_20260723.json" `
  --markdown-path "scratch_audit\alkafi_thaqalayn_website_audit_20260723.md" `
  --cache-dir "$root\cache"
```

The command is read-only with respect to the database. It obeys
`robots.txt`, rate-limits website requests, resumes from a compact cache,
verifies rendered routes against the website sitemap, and then rechecks every
accepted relation against rendered Arabic.

Detailed evidence is in
`scratch_audit/alkafi_thaqalayn_website_audit_20260723.json`; the short result
is in the adjacent Markdown report.

## Website English import

Rendered chapter pages, rather than the Thaqalayn API, are the preferred
public English source. After refreshing the website inventory and audit, run:

```powershell
$root = Join-Path ([System.IO.Path]::GetTempPath()) 'usul16-thaqalayn-website'
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m eshia_research.cli import-thaqalayn-website-english `
  --inventory-path "$root\inventory.json" `
  --audit-path "scratch_audit\alkafi_thaqalayn_website_audit_20260723.json" `
  --dry-run
```

Replace `--dry-run` with `--apply` only after reviewing the totals. The import
creates `thaqalayn_website_v1` rows and does not overwrite historical API
translations. It accepts only one-to-one relations whose Arabic still passes
the audit threshold. Public reads prefer website rows, then API-live rows,
then the earlier source-aligned translation.
